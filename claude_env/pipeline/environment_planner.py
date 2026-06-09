"""Environment Planner — pure data transformation, no I/O, no LLM."""
from __future__ import annotations

from claude_env.models.domain_profile import DomainProfile
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer
from claude_env.models.project_spec import ProjectSpec

_SKILL_TEMPLATE_MAP: dict[str, str] = {
    "quality-gate": "quality_gate_skill.j2",
    "karpathy-guidelines": "karpathy_guidelines_skill.j2",
    "llm-council": "llm_council_skill.j2",
    # Cherry-picked atomic skills (mattpocock + obra/superpowers, 2026-05-07)
    "grill-with-docs": "grill_with_docs_skill.j2",
    "tdd": "tdd_skill.j2",
    "systematic-debugging": "systematic_debugging_skill.j2",
    "brainstorming": "brainstorming_skill.j2",
    "verification-before-completion": "verification_before_completion_skill.j2",
    "writing-plans": "writing_plans_skill.j2",
    "improve-codebase-architecture": "improve_codebase_architecture_skill.j2",
}

_AGENT_TEMPLATE_MAP: dict[str, str] = {
    "advisor": "advisor_agent.j2",
}

# Skills that ship sidecar files alongside SKILL.md.
# Each entry maps the skill slug to a list of (sidecar_filename, template_id)
# tuples. The sidecar is rendered into skills/<slug>/<sidecar_filename>.
# Sidecars exist because cherry-picked atomic skills (mattpocock, superpowers)
# split their content across multiple files; without these, the SKILL.md
# bodies link to files that never get emitted.
_SKILL_SIDECARS: dict[str, list[tuple[str, str]]] = {
    "tdd": [
        ("tests.md", "tdd_tests_sidecar.j2"),
        ("mocking.md", "tdd_mocking_sidecar.j2"),
        ("refactoring.md", "tdd_refactoring_sidecar.j2"),
        ("deep-modules.md", "tdd_deep_modules_sidecar.j2"),
        ("interface-design.md", "tdd_interface_design_sidecar.j2"),
    ],
    "grill-with-docs": [
        ("CONTEXT-FORMAT.md", "grill_context_format_sidecar.j2"),
        ("ADR-FORMAT.md", "grill_adr_format_sidecar.j2"),
    ],
}

# Domain-specific constitution principles appended to the universal core in the
# generated .planning/CONSTITUTION.md. Domains absent here get only the universal
# core (template renders no domain section). Keep each list tight (P7).
_DOMAIN_CONSTITUTION_PRINCIPLES: dict[str, list[str]] = {
    "web": [
        "Mobile-first: design at 375px, 44px minimum tap targets, no horizontal scroll.",
        "Accessibility is non-negotiable: semantic HTML, keyboard nav, WCAG AA contrast.",
        "No layout shift: reserve space for async content before it loads.",
    ],
    "cli": [
        "Composability: read stdin, write stdout, exit codes are the contract.",
        "Fail loud with actionable messages to stderr; never leave silent partial state.",
        "Sane defaults: the happy path requires zero flags.",
    ],
    "data": [
        "Reproducibility: deterministic pipelines, pinned dependencies, versioned inputs.",
        "Validate at boundaries: schema-check data on ingest, fail fast on drift.",
        "No silent data loss: every transform is auditable and recoverable.",
    ],
    "infra": [
        "Idempotent and declarative: applying twice equals applying once.",
        "Least privilege by default; secrets never live in code or logs.",
        "Every change is reversible: plan/diff before apply.",
    ],
}


def plan(
    spec: ProjectSpec,
    profile: DomainProfile,
    available_templates: list[str],
    mcp_slugs: list[str] | None = None,
    with_quality_gate_precommit: bool = False,
) -> GenerationPlan:
    """Produce a GenerationPlan from spec + profile.

    Rules:
    - One Artifact for per-project CLAUDE.md (template: claude_md_project.j2)
    - One Artifact per skill slug in profile.skill_slugs (template: skill_stub.j2)
    - One Artifact per agent slug in profile.agent_slugs (template: agent_stub.j2)
    - Most artifacts are layer=PROJECT, written under <project>/.claude/.
    - When `mcp_slugs` resolves to one or more MCP servers, an additional
      `.mcp.json` artifact is emitted at layer=PROJECT_ROOT (project root,
      since Claude Code reads MCPs from there, not from .claude/).
    - All template_ids must exist in available_templates.

    No file I/O occurs here. Generator (Phase 3) executes the plan.

    Raises:
        ValueError: if any artifact references a template_id not in available_templates.
    """
    from claude_env.hook_registry import resolve_hooks
    from claude_env.mcp_registry import resolve_mcp_servers

    artifacts: list[Artifact] = []

    # Per-project CLAUDE.md
    artifacts.append(
        Artifact(
            target_path="CLAUDE.md",
            template_id="claude_md_project.j2",
            context={
                "project_name": spec.name,
                "domain": profile.domain,
                "sections": profile.claude_md_sections,
            },
            layer=OutputLayer.PROJECT,
        )
    )

    # Domain context (mattpocock CONTEXT.md pattern — ubiquitous language scaffold)
    artifacts.append(
        Artifact(
            target_path="CONTEXT.md",
            template_id="context_md.j2",
            context={
                "project_name": spec.name,
                "description": spec.description,
            },
            layer=OutputLayer.PROJECT,
        )
    )

    # ADR scaffold (docs/adr/README.md — format guide; numbered ADRs created lazily)
    artifacts.append(
        Artifact(
            target_path="docs/adr/README.md",
            template_id="adr_readme.j2",
            context={
                "project_name": spec.name,
            },
            layer=OutputLayer.PROJECT,
        )
    )

    # Project constitution (spec-kit cherry-pick): architectural DNA at
    # .planning/CONSTITUTION.md — universal core + domain-specific principles.
    # PROJECT_ROOT because .planning/ lives at the repo root, not under .claude/.
    # write_once: a constitution is user-owned after creation — re-generation
    # must never clobber the dev's edits.
    artifacts.append(
        Artifact(
            target_path=".planning/CONSTITUTION.md",
            template_id="constitution.j2",
            context={
                "project_name": spec.name,
                "domain": profile.domain,
                "principles": _DOMAIN_CONSTITUTION_PRINCIPLES.get(profile.domain, []),
            },
            layer=OutputLayer.PROJECT_ROOT,
            write_once=True,
        )
    )

    # Skills (and any sidecars they ship with)
    for slug in profile.skill_slugs:
        artifacts.append(
            Artifact(
                target_path=f"skills/{slug}/SKILL.md",
                template_id=_SKILL_TEMPLATE_MAP.get(slug, "skill_stub.j2"),
                context={"slug": slug, "domain": profile.domain},
                layer=OutputLayer.PROJECT,
            )
        )
        for sidecar_name, sidecar_template in _SKILL_SIDECARS.get(slug, []):
            artifacts.append(
                Artifact(
                    target_path=f"skills/{slug}/{sidecar_name}",
                    template_id=sidecar_template,
                    context={"slug": slug, "domain": profile.domain},
                    layer=OutputLayer.PROJECT,
                )
            )

    # Agents
    for slug in profile.agent_slugs:
        artifacts.append(
            Artifact(
                target_path=f"agents/{slug}.md",
                template_id=_AGENT_TEMPLATE_MAP.get(slug, "agent_stub.j2"),
                context={"slug": slug, "domain": profile.domain},
                layer=OutputLayer.PROJECT,
            )
        )

    # Hooks → .claude/settings.json (GEN-04). Emitted only when the profile
    # declares at least one known hook slug; otherwise no settings file is
    # written and the user gets a clean `.claude/` without empty config.
    hooks = resolve_hooks(profile.hook_templates, spec.languages)
    if hooks:
        artifacts.append(
            Artifact(
                target_path="settings.json",
                template_id="settings_json.j2",
                context={"hooks": list(hooks)},
                layer=OutputLayer.PROJECT,
            )
        )

    # MCP servers (project-scoped, written to .mcp.json at project root)
    mcp_servers = resolve_mcp_servers(mcp_slugs or [])
    if mcp_servers:
        artifacts.append(
            Artifact(
                target_path=".mcp.json",
                template_id="mcp_json.j2",
                context={"servers": list(mcp_servers)},
                layer=OutputLayer.PROJECT_ROOT,
            )
        )

    # Quality-gate-precommit hook opt-in marker
    if with_quality_gate_precommit:
        artifacts.append(
            Artifact(
                target_path="quality-gate-precommit",
                template_id="quality_gate_marker.j2",
                context={"project_name": spec.name},
                layer=OutputLayer.PROJECT,
            )
        )

    # Validate all template IDs exist
    for artifact in artifacts:
        if artifact.template_id not in available_templates:
            raise ValueError(
                f"Template '{artifact.template_id}' not found. "
                f"Available: {available_templates}"
            )

    return GenerationPlan(
        project_name=spec.name,
        domain=profile.domain,
        artifacts=artifacts,
    )
