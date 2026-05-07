"""Tests for the Environment Planner pipeline stage."""
from __future__ import annotations

import pytest
from pathlib import Path

from claude_env.models.domain_profile import DomainProfile, load_profile
from claude_env.models.generation_plan import OutputLayer
from claude_env.models.project_spec import ProjectSpec
from claude_env.pipeline.environment_planner import plan


def _make_profile(domain: str, skill_slugs: list[str], agent_slugs: list[str]) -> DomainProfile:
    return DomainProfile(
        domain=domain,
        display_name=domain.title(),
        description=f"Test {domain} profile",
        skill_slugs=skill_slugs,
        agent_slugs=agent_slugs,
        claude_md_sections=["plan_execute_verify", "context_management"],
        hook_templates=[],
        detection_signals=[],
    )


def _make_spec(name: str = "my-project") -> ProjectSpec:
    return ProjectSpec(name=name, description="A test project")


_TEMPLATES = ["claude_md_project.j2", "skill_stub.j2", "agent_stub.j2", "quality_gate_skill.j2", "advisor_agent.j2", "karpathy_guidelines_skill.j2", "llm_council_skill.j2", "context_md.j2", "adr_readme.j2"]
_PROFILE = _make_profile("web", ["fix-issue", "create-pr"], ["security-reviewer"])


def test_plan_produces_claude_md_artifact():
    result = plan(_make_spec(), _PROFILE, _TEMPLATES)
    claude_md = next(a for a in result.artifacts if a.target_path == "CLAUDE.md")
    assert claude_md.template_id == "claude_md_project.j2"
    assert claude_md.layer == OutputLayer.PROJECT


def test_plan_produces_skill_artifacts():
    result = plan(_make_spec(), _PROFILE, _TEMPLATES)
    skill_artifacts = [a for a in result.artifacts if a.target_path.startswith("skills/")]
    assert len(skill_artifacts) == len(_PROFILE.skill_slugs)
    for artifact in skill_artifacts:
        assert artifact.template_id == "skill_stub.j2"
        assert "/SKILL.md" in artifact.target_path


def test_plan_produces_agent_artifacts():
    result = plan(_make_spec(), _PROFILE, _TEMPLATES)
    agent_artifacts = [a for a in result.artifacts if a.target_path.startswith("agents/")]
    assert len(agent_artifacts) == len(_PROFILE.agent_slugs)
    for artifact in agent_artifacts:
        assert artifact.template_id == "agent_stub.j2"
        assert artifact.target_path.endswith(".md")


def test_plan_all_artifacts_project_layer():
    result = plan(_make_spec(), _PROFILE, _TEMPLATES)
    for artifact in result.artifacts:
        assert artifact.layer == OutputLayer.PROJECT


def test_plan_artifact_context_keys():
    result = plan(_make_spec("proj-x"), _PROFILE, _TEMPLATES)
    claude_md = next(a for a in result.artifacts if a.target_path == "CLAUDE.md")
    assert "project_name" in claude_md.context
    assert "domain" in claude_md.context
    assert "sections" in claude_md.context

    skill = next(a for a in result.artifacts if a.target_path.startswith("skills/"))
    assert "slug" in skill.context
    assert "domain" in skill.context

    agent = next(a for a in result.artifacts if a.target_path.startswith("agents/"))
    assert "slug" in agent.context
    assert "domain" in agent.context


def test_invalid_template_raises():
    # skill_stub.j2 missing from available templates
    # (include context_md/adr_readme so validation gets past the fixed artifacts and hits the skill artifacts first)
    partial_templates = ["claude_md_project.j2", "agent_stub.j2", "context_md.j2", "adr_readme.j2"]
    with pytest.raises(ValueError, match="skill_stub.j2"):
        plan(_make_spec(), _PROFILE, partial_templates)


def test_plan_with_real_web_profile():
    profiles_dir = Path(__file__).parent.parent / "claude_env" / "profiles"
    web_profile = load_profile(profiles_dir / "web.yaml")
    result = plan(_make_spec("real-project"), web_profile, _TEMPLATES)
    # 3 fixed (CLAUDE.md, CONTEXT.md, docs/adr/README.md) + per-skill + per-agent
    expected_count = 3 + len(web_profile.skill_slugs) + len(web_profile.agent_slugs)
    assert len(result.artifacts) == expected_count
    assert result.project_name == "real-project"
    assert result.domain == "web"


def test_plan_produces_context_md_artifact():
    result = plan(_make_spec("proj-y"), _PROFILE, _TEMPLATES)
    context_md = next(a for a in result.artifacts if a.target_path == "CONTEXT.md")
    assert context_md.template_id == "context_md.j2"
    assert context_md.layer == OutputLayer.PROJECT
    assert context_md.context["project_name"] == "proj-y"
    assert "description" in context_md.context


def test_plan_produces_adr_readme_artifact():
    result = plan(_make_spec("proj-z"), _PROFILE, _TEMPLATES)
    adr_readme = next(a for a in result.artifacts if a.target_path == "docs/adr/README.md")
    assert adr_readme.template_id == "adr_readme.j2"
    assert adr_readme.layer == OutputLayer.PROJECT
    assert adr_readme.context["project_name"] == "proj-z"
