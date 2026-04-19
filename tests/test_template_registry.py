"""Tests for TemplateRegistry."""
from __future__ import annotations

from pathlib import Path

import jinja2
import pytest

from claude_env.templates.registry import TemplateRegistry


def test_render_resolves_by_name(templates_dir: Path) -> None:
    (templates_dir / "hello.j2").write_text("Hello {{ name }}!")
    registry = TemplateRegistry(templates_dir=templates_dir)
    assert registry.render("hello.j2", {"name": "world"}) == "Hello world!"


def test_render_raises_on_missing_variable(templates_dir: Path) -> None:
    (templates_dir / "greet.j2").write_text("Hi {{ missing_var }}")
    registry = TemplateRegistry(templates_dir=templates_dir)
    with pytest.raises(jinja2.UndefinedError):
        registry.render("greet.j2", {})


def test_relative_path_rejected() -> None:
    with pytest.raises(ValueError, match="absolute"):
        TemplateRegistry(templates_dir=Path("templates"))


def test_template_not_found_raises(templates_dir: Path) -> None:
    registry = TemplateRegistry(templates_dir=templates_dir)
    with pytest.raises(jinja2.TemplateNotFound):
        registry.render("nope.j2", {})


def test_list_templates_returns_j2_files(templates_dir: Path) -> None:
    (templates_dir / "a.j2").write_text("A")
    (templates_dir / "b.j2").write_text("B")
    registry = TemplateRegistry(templates_dir=templates_dir)
    listed = registry.list_templates()
    assert "a.j2" in listed
    assert "b.j2" in listed


def test_autoescape_disabled(templates_dir: Path) -> None:
    (templates_dir / "raw.j2").write_text("{{ val }}")
    registry = TemplateRegistry(templates_dir=templates_dir)
    # Output is markdown/text — no HTML escaping
    assert registry.render("raw.j2", {"val": "<script>"}) == "<script>"


def test_keep_trailing_newline(templates_dir: Path) -> None:
    (templates_dir / "nl.j2").write_text("line\n")
    registry = TemplateRegistry(templates_dir=templates_dir)
    assert registry.render("nl.j2", {}).endswith("\n")


# ---- Integration tests against real project-root templates/ directory ----

REAL_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def test_real_templates_directory_exists() -> None:
    assert REAL_TEMPLATES_DIR.is_dir()


def test_claude_md_project_renders() -> None:
    registry = TemplateRegistry(templates_dir=REAL_TEMPLATES_DIR.resolve())
    out = registry.render(
        "claude_md_project.j2",
        {
            "project_name": "TestProj",
            "domain": "web",
            "sections": ["plan_execute_verify", "context_management"],
        },
    )
    assert "TestProj" in out
    assert "web" in out
    # Template now renders section content, not section IDs
    assert "Plan" in out  # plan_execute_verify section heading
    assert "context" in out.lower()  # context_management section


def test_skill_stub_renders() -> None:
    registry = TemplateRegistry(templates_dir=REAL_TEMPLATES_DIR.resolve())
    out = registry.render(
        "skill_stub.j2",
        {
            "skill_name": "fix-issue",
            "description": "Fix a reported issue with minimal changes.",
            "invocation": "/fix-issue",
        },
    )
    assert "fix-issue" in out
    assert "/fix-issue" in out
    assert out.startswith("---")  # YAML frontmatter


def test_agent_stub_renders() -> None:
    registry = TemplateRegistry(templates_dir=REAL_TEMPLATES_DIR.resolve())
    out = registry.render(
        "agent_stub.j2",
        {
            "agent_name": "security-reviewer",
            "description": "Reviews code for security issues.",
            "skills": ["fix-issue", "run-lint"],
        },
    )
    assert "security-reviewer" in out
    assert "- fix-issue" in out
    assert "- run-lint" in out


def test_list_templates_finds_all_stubs() -> None:
    registry = TemplateRegistry(templates_dir=REAL_TEMPLATES_DIR.resolve())
    listed = registry.list_templates()
    assert "claude_md_project.j2" in listed
    assert "skill_stub.j2" in listed
    assert "agent_stub.j2" in listed
