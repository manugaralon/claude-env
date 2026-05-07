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
        "mandatory_triggers": "'/fix-issue', 'fix this bug', 'debug this', 'this is broken'",
        "strong_triggers": "error stack traces with a help request, test failures, 'X is not working', regression reports",
        "skip_when": "feature requests, exploratory questions, planning discussions, refactors with no broken behavior",
        "allowed_tools": "Bash, Read, Edit, Grep, Glob",
    },
    "create-pr": {
        "skill_name": "create-pr",
        "description": "Stage changes, write commit message, and open a pull request",
        "invocation": "/create-pr",
        "mandatory_triggers": "'/create-pr', 'open a PR', 'submit this PR', 'create pull request'",
        "strong_triggers": "after passing quality gates, 'time to merge', 'ship this', 'I'm done with X'",
        "skip_when": "mid-implementation, tests failing, no commits to PR, when user wants to keep working on the branch",
        "allowed_tools": "Bash, Read",
    },
    "run-lint": {
        "skill_name": "run-lint",
        "description": "Run project linter and auto-fix correctable violations",
        "invocation": "/run-lint",
        "mandatory_triggers": "'/run-lint', 'run the linter', 'lint this', 'check style'",
        "strong_triggers": "'before commit', 'is the style right', 'auto-fix style', 'lint errors'",
        "skip_when": "no code written yet, mid-debug, when not asking about style or formatting",
        "allowed_tools": "Bash, Read",
    },
    "update-deps": {
        "skill_name": "update-deps",
        "description": "Update project dependencies to latest compatible versions",
        "invocation": "/update-deps",
        "mandatory_triggers": "'/update-deps', 'update dependencies', 'upgrade packages', 'bump versions'",
        "strong_triggers": "'security update', 'CVE in dependency', 'is X library outdated', 'audit deps'",
        "skip_when": "regular feature work, no dep-related concern, normal coding tasks",
        "allowed_tools": "Bash, Read, Edit",
    },
    "add-subcommand": {
        "skill_name": "add-subcommand",
        "description": "Scaffold a new CLI subcommand with help text and tests",
        "invocation": "/add-subcommand",
        "mandatory_triggers": "'/add-subcommand', 'add a subcommand', 'new CLI command'",
        "strong_triggers": "extending an existing CLI with a new verb, scaffolding command structure",
        "skip_when": "non-CLI projects, modifying existing subcommand behavior, single-script projects",
        "allowed_tools": "Bash, Read, Edit, Write",
    },
    "quality-gate": {
        "skill_name": "quality-gate",
        "description": "Run all 5 quality gates — lint, type check, build, secrets scan, tests",
        "invocation": "/quality-gate",
        "mandatory_triggers": "'/quality-gate', 'quality gate', 'final check', 'before commit', 'ready to ship'",
        "strong_triggers": "after completing implementation, 'I'm done', 'is this done', 'can I merge'",
        "skip_when": "mid-implementation work, exploration, when there are no actual changes to verify",
        "allowed_tools": "Bash",
    },
    "karpathy-guidelines": {
        "skill_name": "karpathy-guidelines",
        "description": "Apply Karpathy's 4 coding principles: think before coding, simplicity, surgical changes, goal-driven execution",
        "invocation": "/karpathy-guidelines",
        "mandatory_triggers": "'/karpathy-guidelines', 'karpathy principles', 'apply karpathy', 'be more rigorous'",
        "strong_triggers": "starting non-trivial implementation, before significant refactor, when assumptions feel implicit, when complexity is creeping in",
        "skip_when": "trivial 1-line edits, search/explore operations, factual lookups",
        "allowed_tools": "Bash",
    },
    "llm-council": {
        "skill_name": "llm-council",
        "description": "Run a decision through 5 independent AI advisors, peer review, and chairman synthesis — for questions where being wrong is expensive",
        "invocation": "/llm-council",
        "mandatory_triggers": "'council this', 'run the council', 'war room this', 'pressure-test this', 'stress-test this', 'debate this'",
        "strong_triggers": "'should I X or Y', 'which option', 'what would you do', 'is this the right move', 'I can't decide', 'I'm torn between'",
        "skip_when": "simple yes/no questions, factual lookups, casual 'should I' without a meaningful tradeoff",
        "allowed_tools": "Agent, Bash, Read, Glob, Write",
    },
    # Domain-specific stubs — currently render via skill_stub.j2 with no full
    # body. They exist so domain profiles (data, infra) emit named triggers
    # rather than hollow stubs. Promote to a full *.j2 template when the body
    # is authored.
    "run-pipeline": {
        "skill_name": "run-pipeline",
        "description": "Execute a data pipeline (Airflow DAG, dbt run, or scripted ETL) and surface failure context",
        "invocation": "/run-pipeline",
        "mandatory_triggers": "'/run-pipeline', 'run the pipeline', 'kick off the DAG', 'trigger the ETL'",
        "strong_triggers": "'is the pipeline failing', 'why did the run break', dbt/airflow context with a run request",
        "skip_when": "non-data projects, schema-only questions, no executable pipeline present",
        "allowed_tools": "Bash, Read",
    },
    "validate-schema": {
        "skill_name": "validate-schema",
        "description": "Validate dataset schema against an expected contract (Pydantic, dbt schema.yml, JSON Schema)",
        "invocation": "/validate-schema",
        "mandatory_triggers": "'/validate-schema', 'check the schema', 'is this dataset valid'",
        "strong_triggers": "schema mismatch errors, downstream consumer broke, contract drift suspected",
        "skip_when": "no formal schema declared, exploratory data analysis, ad-hoc transforms",
        "allowed_tools": "Bash, Read",
    },
    "profile-data": {
        "skill_name": "profile-data",
        "description": "Profile a dataset for shape, nulls, distributions, and outliers — produces a quality report",
        "invocation": "/profile-data",
        "mandatory_triggers": "'/profile-data', 'profile this dataset', 'data quality report'",
        "strong_triggers": "'what does this data look like', 'are there nulls', 'distribution of column X'",
        "skip_when": "no dataset to profile, schema-only questions, infrastructure work",
        "allowed_tools": "Bash, Read",
    },
    "plan-apply": {
        "skill_name": "plan-apply",
        "description": "Run a plan/diff for infrastructure changes (terraform plan, pulumi preview, cdk diff) and explain the delta",
        "invocation": "/plan-apply",
        "mandatory_triggers": "'/plan-apply', 'terraform plan', 'pulumi preview', 'cdk diff'",
        "strong_triggers": "'what would this change', 'preview the infra changes', 'show me the diff before applying'",
        "skip_when": "non-IaC projects, runtime application logic, no plan-able infra surface",
        "allowed_tools": "Bash, Read",
    },
    "validate-manifest": {
        "skill_name": "validate-manifest",
        "description": "Validate infrastructure manifests (Kubernetes YAML, Helm values, terraform vars) against schemas and policies",
        "invocation": "/validate-manifest",
        "mandatory_triggers": "'/validate-manifest', 'validate the manifest', 'is this YAML valid', 'check the helm values'",
        "strong_triggers": "'kubernetes won't accept this', 'helm template fails', schema-validation errors on manifests",
        "skip_when": "non-IaC projects, runtime config that isn't a manifest, ad-hoc YAML files",
        "allowed_tools": "Bash, Read",
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
    "code-reviewer": {
        "agent_name": "code-reviewer",
        "description": (
            "Review code changes for correctness, clarity, and adherence to project "
            "conventions. Invoked with zero context — only the artifact under review."
        ),
        "skills": ["fix-issue", "create-pr"],
    },
    "advisor": {
        "agent_name": "advisor",
        "description": (
            "Senior advisor for hard decisions — architecture, security, complex refactors. "
            "Invoked by the Worker (Sonnet) when the cost of getting it wrong is high."
        ),
        "skills": [],
    },
    "data-quality-reviewer": {
        "agent_name": "data-quality-reviewer",
        "description": (
            "Review datasets and pipeline outputs for quality issues — nulls, "
            "outliers, schema drift, distribution shifts."
        ),
        "skills": ["profile-data", "validate-schema"],
    },
    "schema-auditor": {
        "agent_name": "schema-auditor",
        "description": (
            "Audit schema definitions against producer/consumer contracts and "
            "flag breaking changes before they ship."
        ),
        "skills": ["validate-schema"],
    },
    "cost-reviewer": {
        "agent_name": "cost-reviewer",
        "description": (
            "Review infrastructure changes for cost impact — flag expensive "
            "resources, suggest cheaper alternatives, surface oversize defaults."
        ),
        "skills": ["plan-apply"],
    },
}


def known_skill_slugs() -> list[str]:
    """Return every skill slug known by the catalogue or the planner template map.

    Source of truth for ``claude-env setup``'s global install — the kitchen
    sink of skills that ship with the package. Lazy-imports the planner's
    template map to avoid a circular import at module load.
    """
    from claude_env.pipeline.environment_planner import _SKILL_TEMPLATE_MAP

    return sorted(set(_SKILL_CATALOGUE.keys()) | set(_SKILL_TEMPLATE_MAP.keys()))


def known_agent_slugs() -> list[str]:
    """Return every agent slug known by the catalogue.

    Source of truth for ``claude-env setup``'s global agent install.
    """
    return sorted(_AGENT_CATALOGUE.keys())


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
            for key, value in entry.items():
                ctx.setdefault(key, value)
        else:
            ctx.setdefault("skill_name", slug)
            ctx.setdefault("description", f"Perform {slug} tasks")
            ctx.setdefault("invocation", f"/{slug}")
        # Always provide defaults for optional frontmatter fields so the
        # template can render with strict-undefined enabled.
        ctx.setdefault("mandatory_triggers", "")
        ctx.setdefault("strong_triggers", "")
        ctx.setdefault("skip_when", "")
        ctx.setdefault("allowed_tools", "")

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
