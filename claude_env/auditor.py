"""Auditor — structural validation of a generated `.claude/` environment.

Implements QA-01: catches regressions in generated content before the
developer starts a session. Each check is pure (just file inspection),
returns a `Finding` with severity and a precise file+rule reference, and
contributes to a top-level `AuditReport` that decides PASS/FAIL.

Design constraints (from .planning/REQUIREMENTS.md):
- v1 = structural audit only (no LLM judgment)
- Findings must name the exact file and the exact rule violated, so a
  human or a follow-up agent can act without re-reading the source.
- Exit code at the bootstrap call site reflects PASS/FAIL.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warn"]

# CLAUDE.md hard line cap from GEN-01.
_CLAUDE_MD_MAX_LINES = 200

# Verbs we accept as the leading word of a skill description. Pulled from the
# project's voice — descriptions read as "<verb> the thing" so reviewers can
# scan a directory of SKILL.md files and grasp the action surface fast.
_DESCRIPTION_VERBS = frozenset({
    "add", "audit", "apply", "build", "capture", "check", "clean", "create",
    "diagnose", "emit", "execute", "explore", "extract", "find", "fix",
    "generate", "install", "list", "load", "merge", "perform", "plan",
    "preview", "produce", "profile", "register", "render", "report", "review",
    "run", "scaffold", "scan", "schedule", "stage", "summarise", "summarize",
    "synthesize", "test", "trigger", "turn", "update", "validate", "verify",
    "write",
    # Adjective- or noun-led descriptions from cherry-picked skills (mattpocock,
    # superpowers). Their voice is intentional — keep them as valid first
    # words rather than rewriting upstream content.
    "disciplined", "grilling", "iron", "test-driven",
})


@dataclass
class Finding:
    """One audit observation tied to a specific file and rule."""

    severity: Severity
    rule: str           # short ID like "CLAUDE_MD_LINE_COUNT"
    file: str           # path relative to project root
    message: str        # human-readable explanation

    def render(self) -> str:
        prefix = "ERROR" if self.severity == "error" else "WARN"
        return f"[{prefix}] {self.rule} {self.file}: {self.message}"


@dataclass
class AuditReport:
    """Result of running every check against a project's `.claude/` tree."""

    project_root: Path
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Audit fails only on `error`-severity findings; warnings don't fail."""
        return not any(f.severity == "error" for f in self.findings)

    def render(self) -> str:
        if not self.findings:
            return "audit: PASS — no issues"
        lines = ["audit: " + ("PASS" if self.passed else "FAIL")]
        lines.extend(f.render() for f in self.findings)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual checks — each returns a list of Findings (empty = clean)
# ---------------------------------------------------------------------------


def _check_claude_md_line_count(project_root: Path) -> list[Finding]:
    target = project_root / ".claude" / "CLAUDE.md"
    if not target.exists():
        return [Finding(
            severity="error",
            rule="CLAUDE_MD_MISSING",
            file=str(target.relative_to(project_root)),
            message="CLAUDE.md not found under .claude/",
        )]
    line_count = len(target.read_text(encoding="utf-8").splitlines())
    if line_count > _CLAUDE_MD_MAX_LINES:
        return [Finding(
            severity="error",
            rule="CLAUDE_MD_LINE_COUNT",
            file=str(target.relative_to(project_root)),
            message=(
                f"{line_count} lines exceeds the {_CLAUDE_MD_MAX_LINES}-line cap "
                "from GEN-01 (every line must change behavior)."
            ),
        )]
    return []


def _check_settings_json_valid(project_root: Path) -> list[Finding]:
    target = project_root / ".claude" / "settings.json"
    if not target.exists():
        # settings.json is optional — generator only emits it when hooks are
        # configured. Missing is not a failure.
        return []
    try:
        json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Finding(
            severity="error",
            rule="SETTINGS_JSON_INVALID",
            file=str(target.relative_to(project_root)),
            message=f"not valid JSON ({exc.msg} at line {exc.lineno} col {exc.colno})",
        )]
    return []


def _check_agents_have_skills_field(project_root: Path) -> list[Finding]:
    agents_dir = project_root / ".claude" / "agents"
    if not agents_dir.is_dir():
        return []
    findings: list[Finding] = []
    for agent in sorted(agents_dir.glob("*.md")):
        body = agent.read_text(encoding="utf-8")
        # Frontmatter is delimited by --- ... --- at the top
        if not body.startswith("---"):
            findings.append(Finding(
                severity="error",
                rule="AGENT_NO_FRONTMATTER",
                file=str(agent.relative_to(project_root)),
                message="agent file is missing the YAML frontmatter block",
            ))
            continue
        end = body.find("\n---", 3)
        if end < 0:
            findings.append(Finding(
                severity="error",
                rule="AGENT_FRONTMATTER_UNCLOSED",
                file=str(agent.relative_to(project_root)),
                message="frontmatter block never closes",
            ))
            continue
        frontmatter = body[3:end]
        if "skills:" not in frontmatter:
            findings.append(Finding(
                severity="error",
                rule="AGENT_MISSING_SKILLS_FIELD",
                file=str(agent.relative_to(project_root)),
                message=(
                    "agent must declare a `skills:` field (even if empty list) "
                    "so the runtime knows what tooling it can invoke."
                ),
            ))
    return findings


def _extract_description(frontmatter: str) -> str | None:
    """Pull the description value, supporting inline and folded scalars.

    The skill_stub template emits descriptions inline; cherry-picked atomic
    skills use a `>-` folded scalar. Both forms must validate.
    """
    lines = frontmatter.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("description:"):
            inline = line.split(":", 1)[1].strip()
            if inline in (">-", ">", "|-", "|"):
                # Folded/literal scalar — first non-empty continuation line
                for cont in lines[i + 1:]:
                    if cont.strip():
                        return cont.strip()
                return None
            return inline if inline else None
    return None


def _check_skill_descriptions_verb_phrase(project_root: Path) -> list[Finding]:
    skills_dir = project_root / ".claude" / "skills"
    if not skills_dir.is_dir():
        return []
    findings: list[Finding] = []
    for skill in sorted(skills_dir.glob("*/SKILL.md")):
        body = skill.read_text(encoding="utf-8")
        if not body.startswith("---"):
            findings.append(Finding(
                severity="error",
                rule="SKILL_NO_FRONTMATTER",
                file=str(skill.relative_to(project_root)),
                message="SKILL.md is missing the YAML frontmatter block",
            ))
            continue
        end = body.find("\n---", 3)
        if end < 0:
            findings.append(Finding(
                severity="error",
                rule="SKILL_FRONTMATTER_UNCLOSED",
                file=str(skill.relative_to(project_root)),
                message="frontmatter block never closes",
            ))
            continue
        description = _extract_description(body[3:end])
        if not description:
            findings.append(Finding(
                severity="error",
                rule="SKILL_DESCRIPTION_MISSING",
                file=str(skill.relative_to(project_root)),
                message="description field is empty or absent",
            ))
            continue
        first_word = description.split()[0].rstrip(",.;").lower()
        if first_word not in _DESCRIPTION_VERBS:
            findings.append(Finding(
                severity="warn",
                rule="SKILL_DESCRIPTION_NOT_VERB_PHRASE",
                file=str(skill.relative_to(project_root)),
                message=(
                    f"description starts with {first_word!r}; expected a verb "
                    "from the project's action vocabulary."
                ),
            ))
    return findings


_CHECKS = (
    _check_claude_md_line_count,
    _check_settings_json_valid,
    _check_agents_have_skills_field,
    _check_skill_descriptions_verb_phrase,
)


def audit(project_root: Path) -> AuditReport:
    """Run every structural check against `project_root` and return the report."""
    report = AuditReport(project_root=project_root)
    for check in _CHECKS:
        report.findings.extend(check(project_root))
    return report
