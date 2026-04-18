"""Tests for the Domain Classifier pipeline stage."""
from __future__ import annotations

import pytest

from claude_env.models.domain_profile import DomainProfile
from claude_env.models.project_spec import ProjectSpec
from claude_env.pipeline.domain_classifier import classify, load_all_profiles
from pathlib import Path


def _make_profile(domain: str, signals: list[str], **kwargs) -> DomainProfile:
    return DomainProfile(
        domain=domain,
        display_name=domain.title(),
        description=f"Test {domain} profile",
        skill_slugs=kwargs.get("skill_slugs", ["test-skill"]),
        agent_slugs=kwargs.get("agent_slugs", ["test-agent"]),
        claude_md_sections=["rules"],
        hook_templates=[],
        detection_signals=signals,
    )


def _make_spec(**kwargs) -> ProjectSpec:
    return ProjectSpec(
        name=kwargs.get("name", "test-project"),
        description=kwargs.get("description", "A test project"),
        tech_stack=kwargs.get("tech_stack", []),
        languages=kwargs.get("languages", []),
    )


_WEB = _make_profile("web", ["react", "next.js"])
_CLI = _make_profile("cli", ["typer", "click"])
_GENERAL = _make_profile("general", [])
_ALL_PROFILES = [_WEB, _CLI, _GENERAL]


def test_classify_web_signals():
    spec = _make_spec(tech_stack=["react", "postgres"])
    result = classify(spec, _ALL_PROFILES)
    assert result.domain == "web"


def test_classify_cli_signals():
    spec = _make_spec(tech_stack=["typer"])
    result = classify(spec, _ALL_PROFILES)
    assert result.domain == "cli"


def test_fallback_to_general():
    spec = _make_spec(tech_stack=["obscure-lib"])
    result = classify(spec, _ALL_PROFILES)
    assert result.domain == "general"


def test_classify_case_insensitive():
    spec = _make_spec(tech_stack=["React"])
    result = classify(spec, _ALL_PROFILES)
    assert result.domain == "web"


def test_missing_general_raises():
    spec = _make_spec(tech_stack=["obscure-lib"])
    with pytest.raises(ValueError, match="No 'general' fallback profile found"):
        classify(spec, [_WEB, _CLI])


def test_load_all_profiles():
    profiles_dir = Path(__file__).parent.parent / "claude_env" / "profiles"
    profiles = load_all_profiles(profiles_dir)
    domains = {p.domain for p in profiles}
    assert len(profiles) == 5
    assert "general" in domains
    assert "web" in domains
