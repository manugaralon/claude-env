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
