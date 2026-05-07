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


def plan(
    spec: ProjectSpec,
    profile: DomainProfile,
    available_templates: list[str],
    mcp_slugs: list[str] | None = None,
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
