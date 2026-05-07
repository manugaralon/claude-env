"""Tests for content catalogue and expanded templates."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_env.generator.content_catalogue import enrich_artifact_context
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer
from claude_env.templates.registry import TemplateRegistry

TEMPLATES_DIR = Path(__file__).parent.parent / "claude_env" / "data"


def _make_artifact(template_id: str, context: dict[str, object]) -> Artifact:
    return Artifact(
        target_path="dummy",
        template_id=template_id,
        context=context,
        layer=OutputLayer.PROJECT,
    )


def _make_plan() -> GenerationPlan:
    return GenerationPlan(project_name="test-project", domain="web", artifacts=[])


def test_enrich_known_skill() -> None:
    artifact = _make_artifact("skill_stub.j2", {"slug": "fix-issue", "domain": "web"})
    ctx = enrich_artifact_context(artifact, _make_plan())
    assert ctx["skill_name"] == "fix-issue"
    assert str(ctx["description"]).startswith("Diagnose")
    assert ctx["invocation"] == "/fix-issue"


def test_enrich_unknown_skill_fallback() -> None:
    artifact = _make_artifact("skill_stub.j2", {"slug": "unknown-thing", "domain": "web"})
    ctx = enrich_artifact_context(artifact, _make_plan())
    assert ctx["skill_name"] == "unknown-thing"
    assert ctx["description"] == "Perform unknown-thing tasks"
    assert ctx["invocation"] == "/unknown-thing"


def test_enrich_known_agent() -> None:
    artifact = _make_artifact("agent_stub.j2", {"slug": "security-reviewer", "domain": "web"})
    ctx = enrich_artifact_context(artifact, _make_plan())
    assert ctx["agent_name"] == "security-reviewer"
    skills = ctx["skills"]
    assert isinstance(skills, list)
    assert len(skills) > 0
    assert "fix-issue" in skills


def test_enrich_unknown_agent_fallback() -> None:
    artifact = _make_artifact("agent_stub.j2", {"slug": "mystery-agent", "domain": "web"})
    ctx = enrich_artifact_context(artifact, _make_plan())
    assert ctx["agent_name"] == "mystery-agent"
    assert ctx["skills"] == []


def test_enrich_passthrough_other_template() -> None:
    context: dict[str, object] = {
        "project_name": "my-app",
        "domain": "web",
        "sections": ["plan_execute_verify"],
    }
    artifact = _make_artifact("claude_md_project.j2", context)
    ctx = enrich_artifact_context(artifact, _make_plan())
    assert ctx == context


def test_claude_md_template_line_count() -> None:
    registry = TemplateRegistry(TEMPLATES_DIR)
    sections = ["mobile_first", "plan_execute_verify", "context_management", "lessons_loop"]
    rendered = registry.render(
        "claude_md_project.j2",
        {"project_name": "my-app", "domain": "web", "sections": sections},
    )
    lines = rendered.splitlines()
    assert len(lines) <= 200, f"Template rendered {len(lines)} lines, expected <=200"


def test_claude_md_contains_required_sections() -> None:
    registry = TemplateRegistry(TEMPLATES_DIR)
    rendered = registry.render(
        "claude_md_project.j2",
        {
            "project_name": "my-app",
            "domain": "web",
            "sections": ["plan_execute_verify", "context_management", "lessons_loop"],
        },
    )
    assert "Plan" in rendered
    assert "Execute" in rendered
    assert "Verify" in rendered
    assert "context" in rendered.lower()
    assert "lessons.md" in rendered


def test_claude_md_no_sentinel_markers() -> None:
    registry = TemplateRegistry(TEMPLATES_DIR)
    rendered = registry.render(
        "claude_md_project.j2",
        {
            "project_name": "my-app",
            "domain": "web",
            "sections": ["mobile_first", "plan_execute_verify", "context_management", "lessons_loop"],
        },
    )
    assert "BEGIN CLAUDE-ENV MANAGED" not in rendered
    assert "END CLAUDE-ENV MANAGED" not in rendered


def test_settings_json_valid() -> None:
    registry = TemplateRegistry(TEMPLATES_DIR)
    rendered = registry.render(
        "settings_json.j2",
        {"hooks": [{"command": "/usr/bin/ruff check .", "exit_code": 2}]},
    )
    data = json.loads(rendered)
    hook_entry = data["hooks"]["PostToolUse"][0]["hooks"][0]
    assert hook_entry["exitCode"] == 2


def test_settings_json_escapes_paths() -> None:
    registry = TemplateRegistry(TEMPLATES_DIR)
    rendered = registry.render(
        "settings_json.j2",
        {"hooks": [{"command": "ruff check . --fix && echo done", "exit_code": 1}]},
    )
    data = json.loads(rendered)
    cmd = data["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert "ruff check" in cmd
