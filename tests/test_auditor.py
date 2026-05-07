"""Tests for the auditor module — QA-01 structural validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from claude_env.auditor import (
    AuditReport,
    Finding,
    audit,
)
from claude_env.generator.generator import Generator
from claude_env.models.generation_plan import GenerationPlan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bootstrap_for_audit(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> Path:
    """Run a real bootstrap so we audit a realistic environment."""
    Generator(real_registry).execute(web_plan, tmp_path, tmp_path / "global")
    return tmp_path


# ---------------------------------------------------------------------------
# Pass cases
# ---------------------------------------------------------------------------


def test_audit_passes_on_freshly_bootstrapped_project(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    project = _bootstrap_for_audit(tmp_path, real_registry, web_plan)
    report = audit(project)
    # Allow non-error findings (warns are OK); fail only on errors.
    assert report.passed, report.render()


def test_audit_returns_no_findings_on_clean_environment(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    """A correctly generated environment should be silent — no warns either."""
    project = _bootstrap_for_audit(tmp_path, real_registry, web_plan)
    report = audit(project)
    assert report.findings == [], "\n".join(f.render() for f in report.findings)


# ---------------------------------------------------------------------------
# Fail cases — each deliberately breaks one rule
# ---------------------------------------------------------------------------


def test_audit_fails_when_claude_md_missing(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    report = audit(tmp_path)
    assert not report.passed
    rules = {f.rule for f in report.findings}
    assert "CLAUDE_MD_MISSING" in rules


def test_audit_fails_when_claude_md_too_long(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    project = _bootstrap_for_audit(tmp_path, real_registry, web_plan)
    target = project / ".claude" / "CLAUDE.md"
    # Append 250 filler lines to bust the 200-line cap
    target.write_text(target.read_text() + "\n" + "\n".join("# filler" for _ in range(250)))
    report = audit(project)
    assert not report.passed
    finding = next(f for f in report.findings if f.rule == "CLAUDE_MD_LINE_COUNT")
    assert "exceeds" in finding.message
    assert finding.file == ".claude/CLAUDE.md"


def test_audit_fails_when_settings_json_has_trailing_comma(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    project = _bootstrap_for_audit(tmp_path, real_registry, web_plan)
    settings = project / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text('{"hooks": [{},]}\n', encoding="utf-8")
    report = audit(project)
    assert not report.passed
    finding = next(f for f in report.findings if f.rule == "SETTINGS_JSON_INVALID")
    assert finding.file == ".claude/settings.json"
    assert "valid JSON" in finding.message


def test_audit_fails_when_agent_missing_skills_field(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    project = _bootstrap_for_audit(tmp_path, real_registry, web_plan)
    agent = project / ".claude" / "agents" / "broken.md"
    agent.write_text(
        "---\nname: broken\ndescription: A test agent\n---\n\n# Body\n",
        encoding="utf-8",
    )
    report = audit(project)
    assert not report.passed
    finding = next(
        f for f in report.findings
        if f.rule == "AGENT_MISSING_SKILLS_FIELD" and "broken.md" in f.file
    )
    assert "skills:" in finding.message


def test_audit_warns_on_non_verb_skill_description(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    project = _bootstrap_for_audit(tmp_path, real_registry, web_plan)
    skill_dir = project / ".claude" / "skills" / "weird"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: weird\ndescription: Banana flavored skill description\n---\n\n# Weird\n",
        encoding="utf-8",
    )
    report = audit(project)
    # Warn-only — audit still passes overall
    assert report.passed
    finding = next(
        f for f in report.findings
        if f.rule == "SKILL_DESCRIPTION_NOT_VERB_PHRASE" and "weird" in f.file
    )
    assert finding.severity == "warn"


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def test_audit_report_render_passes_clean() -> None:
    report = AuditReport(project_root=Path("/x"))
    assert "PASS" in report.render()


def test_audit_report_render_includes_findings() -> None:
    report = AuditReport(
        project_root=Path("/x"),
        findings=[Finding(severity="error", rule="X", file="f", message="m")],
    )
    rendered = report.render()
    assert "FAIL" in rendered
    assert "X" in rendered and "m" in rendered


def test_audit_report_passed_ignores_warnings() -> None:
    """Warnings don't fail the audit — only errors do."""
    report = AuditReport(
        project_root=Path("/x"),
        findings=[Finding(severity="warn", rule="W", file="f", message="m")],
    )
    assert report.passed
