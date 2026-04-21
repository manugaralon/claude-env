"""Content catalogue — enriches minimal planner context into full template context.

The planner emits minimal artifact contexts (slug + domain). This module maps
known slugs to rich descriptions so templates can render without hardcoding
content in the planner.
"""
from __future__ import annotations

from claude_env.models.generation_plan import Artifact, GenerationPlan

_SKILL_CATALOGUE: dict[str, dict[str, str]] = {
    "fix-issue": {
        "skill_name": "fix-issue",
        "description": "Diagnose and fix a reported bug or failing test",
        "invocation": "/fix-issue",
    },
    "create-pr": {
        "skill_name": "create-pr",
        "description": "Stage changes, write commit message, and open a pull request",
        "invocation": "/create-pr",
    },
    "run-lint": {
        "skill_name": "run-lint",
        "description": "Run project linter and auto-fix correctable violations",
        "invocation": "/run-lint",
    },
    "update-deps": {
        "skill_name": "update-deps",
        "description": "Update project dependencies to latest compatible versions",
        "invocation": "/update-deps",
    },
    "add-subcommand": {
        "skill_name": "add-subcommand",
        "description": "Scaffold a new CLI subcommand with help text and tests",
        "invocation": "/add-subcommand",
    },
    "quality-gate": {
        "skill_name": "quality-gate",
        "description": "Run all 5 quality gates — lint, type check, build, secrets scan, tests",
        "invocation": "/quality-gate",
    },
    "karpathy-guidelines": {
        "skill_name": "karpathy-guidelines",
        "description": "Apply Karpathy's 4 coding principles: think before coding, simplicity, surgical changes, goal-driven execution",
        "invocation": "/karpathy-guidelines",
    },
}

_AGENT_CATALOGUE: dict[str, dict[str, object]] = {
    "security-reviewer": {
        "agent_name": "security-reviewer",
        "description": "Review code changes for security vulnerabilities and suggest mitigations",
        "skills": ["fix-issue", "create-pr"],
    },
    "accessibility-auditor": {
        "agent_name": "accessibility-auditor",
        "description": "Audit UI components for WCAG compliance and propose fixes",
        "skills": ["fix-issue"],
    },
    "cli-ux-reviewer": {
        "agent_name": "cli-ux-reviewer",
        "description": "Review CLI commands for usability, help text clarity, and ergonomics",
        "skills": ["fix-issue", "add-subcommand"],
    },
    "advisor": {
        "agent_name": "advisor",
        "description": (
            "Senior advisor for hard decisions — architecture, security, complex refactors. "
            "Invoked by the Worker (Sonnet) when the cost of getting it wrong is high."
        ),
        "skills": [],
    },
}


def enrich_artifact_context(artifact: Artifact, plan: GenerationPlan) -> dict[str, object]:
    """Return an enriched context dict for *artifact*.

    For skill_stub.j2 and agent_stub.j2, known slugs are looked up in the
    catalogues and merged into the context via setdefault (caller-supplied
    values always win). Unknown slugs get slug-derived defaults.

    All other template_ids are returned unchanged.
    """
    ctx: dict[str, object] = dict(artifact.context)
    slug = str(ctx.get("slug", ""))

    if artifact.template_id == "skill_stub.j2":
        entry = _SKILL_CATALOGUE.get(slug)
        if entry:
            ctx.setdefault("skill_name", entry["skill_name"])
            ctx.setdefault("description", entry["description"])
            ctx.setdefault("invocation", entry["invocation"])
        else:
            ctx.setdefault("skill_name", slug)
            ctx.setdefault("description", f"Perform {slug} tasks")
            ctx.setdefault("invocation", f"/{slug}")

    elif artifact.template_id == "agent_stub.j2":
        agent_entry = _AGENT_CATALOGUE.get(slug)
        if agent_entry:
            ctx.setdefault("agent_name", agent_entry["agent_name"])
            ctx.setdefault("description", agent_entry["description"])
            ctx.setdefault("skills", agent_entry["skills"])
        else:
            ctx.setdefault("agent_name", slug)
            ctx.setdefault("description", f"Perform {slug} tasks")
            ctx.setdefault("skills", [])

    return ctx
