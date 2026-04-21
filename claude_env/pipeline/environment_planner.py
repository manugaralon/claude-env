"""Environment Planner — pure data transformation, no I/O, no LLM."""
from __future__ import annotations

from claude_env.models.domain_profile import DomainProfile
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer
from claude_env.models.project_spec import ProjectSpec

_SKILL_TEMPLATE_MAP: dict[str, str] = {
    "quality-gate": "quality_gate_skill.j2",
}

_AGENT_TEMPLATE_MAP: dict[str, str] = {
    "advisor": "advisor_agent.j2",
}


def plan(
    spec: ProjectSpec,
    profile: DomainProfile,
    available_templates: list[str],
) -> GenerationPlan:
    """Produce a GenerationPlan from spec + profile.

    Rules:
    - One Artifact for per-project CLAUDE.md (template: claude_md_project.j2)
    - One Artifact per skill slug in profile.skill_slugs (template: skill_stub.j2)
    - One Artifact per agent slug in profile.agent_slugs (template: agent_stub.j2)
    - All artifacts are layer=PROJECT (global layer is Phase 3 concern)
    - All template_ids must exist in available_templates

    No file I/O occurs here. Generator (Phase 3) executes the plan.

    Raises:
        ValueError: if any artifact references a template_id not in available_templates.
    """
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

    # Skills
    for slug in profile.skill_slugs:
        artifacts.append(
            Artifact(
                target_path=f"skills/{slug}/SKILL.md",
                template_id=_SKILL_TEMPLATE_MAP.get(slug, "skill_stub.j2"),
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
