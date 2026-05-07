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


_TEMPLATES = [
    "claude_md_project.j2", "skill_stub.j2", "agent_stub.j2",
    "quality_gate_skill.j2", "advisor_agent.j2", "karpathy_guidelines_skill.j2",
    "llm_council_skill.j2", "context_md.j2", "adr_readme.j2",
    "settings_json.j2",
    # Cherry-picked atomic skills (2026-05-07)
    "grill_with_docs_skill.j2", "tdd_skill.j2", "systematic_debugging_skill.j2",
    "brainstorming_skill.j2", "verification_before_completion_skill.j2",
    "writing_plans_skill.j2", "improve_codebase_architecture_skill.j2",
    # Sidecars shipped with cherry-picked skills
    "tdd_tests_sidecar.j2", "tdd_mocking_sidecar.j2", "tdd_refactoring_sidecar.j2",
    "tdd_deep_modules_sidecar.j2", "tdd_interface_design_sidecar.j2",
    "grill_context_format_sidecar.j2", "grill_adr_format_sidecar.j2",
]
_PROFILE = _make_profile("web", ["fix-issue", "create-pr"], ["security-reviewer"])


def test_plan_produces_claude_md_artifact():
    result = plan(_make_spec(), _PROFILE, _TEMPLATES)
    claude_md = next(a for a in result.artifacts if a.target_path == "CLAUDE.md")
    assert claude_md.template_id == "claude_md_project.j2"
    assert claude_md.layer == OutputLayer.PROJECT


def test_plan_produces_skill_artifacts():
    result = plan(_make_spec(), _PROFILE, _TEMPLATES)
    skill_artifacts = [a for a in result.artifacts if a.target_path.startswith("skills/")]
    # _PROFILE has fix-issue and create-pr — neither has sidecars, so 1 SKILL.md each
    assert len(skill_artifacts) == len(_PROFILE.skill_slugs)
    for artifact in skill_artifacts:
        assert artifact.template_id == "skill_stub.j2"
        assert "/SKILL.md" in artifact.target_path


def test_plan_emits_tdd_sidecars():
    profile = _make_profile("web", ["tdd"], [])
    result = plan(_make_spec(), profile, _TEMPLATES)
    paths = {a.target_path for a in result.artifacts if a.target_path.startswith("skills/tdd/")}
    assert paths == {
        "skills/tdd/SKILL.md",
        "skills/tdd/tests.md",
        "skills/tdd/mocking.md",
        "skills/tdd/refactoring.md",
        "skills/tdd/deep-modules.md",
        "skills/tdd/interface-design.md",
    }


def test_plan_emits_grill_sidecars():
    profile = _make_profile("web", ["grill-with-docs"], [])
    result = plan(_make_spec(), profile, _TEMPLATES)
    paths = {
        a.target_path for a in result.artifacts
        if a.target_path.startswith("skills/grill-with-docs/")
    }
    assert paths == {
        "skills/grill-with-docs/SKILL.md",
        "skills/grill-with-docs/CONTEXT-FORMAT.md",
        "skills/grill-with-docs/ADR-FORMAT.md",
    }


def test_plan_no_sidecars_for_simple_skills():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(_make_spec(), profile, _TEMPLATES)
    paths = [a.target_path for a in result.artifacts if a.target_path.startswith("skills/")]
    assert paths == ["skills/fix-issue/SKILL.md"]


# ---------------------------------------------------------------------------
# MCP server emission
# ---------------------------------------------------------------------------


def _mcp_templates() -> list[str]:
    return _TEMPLATES + ["mcp_json.j2"]


def test_plan_no_mcp_artifact_when_no_slugs():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(_make_spec(), profile, _mcp_templates(), mcp_slugs=None)
    assert not any(a.target_path == ".mcp.json" for a in result.artifacts)


def test_plan_no_mcp_artifact_when_only_unknown_slugs():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(_make_spec(), profile, _mcp_templates(), mcp_slugs=["nonexistent"])
    assert not any(a.target_path == ".mcp.json" for a in result.artifacts)


def test_plan_emits_mcp_artifact_at_project_root():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(_make_spec(), profile, _mcp_templates(), mcp_slugs=["browser"])
    mcp_artifact = next(a for a in result.artifacts if a.target_path == ".mcp.json")
    assert mcp_artifact.layer == OutputLayer.PROJECT_ROOT
    assert mcp_artifact.template_id == "mcp_json.j2"
    servers = mcp_artifact.context["servers"]
    assert isinstance(servers, list) and len(servers) == 1
    assert servers[0]["name"] == "playwright"


def test_plan_mcp_preserves_slug_order():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(
        _make_spec(), profile, _mcp_templates(),
        mcp_slugs=["context7", "browser"],
    )
    mcp_artifact = next(a for a in result.artifacts if a.target_path == ".mcp.json")
    server_names = [s["name"] for s in mcp_artifact.context["servers"]]
    assert server_names == ["context7", "playwright"]


# ---------------------------------------------------------------------------
# Quality-gate-precommit marker
# ---------------------------------------------------------------------------


def _qg_templates() -> list[str]:
    return _TEMPLATES + ["quality_gate_marker.j2"]


def test_plan_no_qg_marker_by_default():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(_make_spec(), profile, _qg_templates())
    assert not any(a.target_path == "quality-gate-precommit" for a in result.artifacts)


def test_plan_emits_qg_marker_when_requested():
    profile = _make_profile("web", ["fix-issue"], [])
    result = plan(
        _make_spec(), profile, _qg_templates(),
        with_quality_gate_precommit=True,
    )
    marker = next(a for a in result.artifacts if a.target_path == "quality-gate-precommit")
    assert marker.layer == OutputLayer.PROJECT
    assert marker.template_id == "quality_gate_marker.j2"


# ---------------------------------------------------------------------------
# Hook templates → settings.json
# ---------------------------------------------------------------------------


def test_plan_emits_settings_json_when_profile_has_hooks():
    profile = DomainProfile(
        domain="web",
        display_name="Web",
        description="Test",
        skill_slugs=["fix-issue"],
        agent_slugs=[],
        claude_md_sections=["plan_execute_verify"],
        hook_templates=["lint_after_edit"],
        detection_signals=[],
    )
    spec = ProjectSpec(name="x", description="x", languages=["python"])
    result = plan(spec, profile, _TEMPLATES)
    settings = next(a for a in result.artifacts if a.target_path == "settings.json")
    assert settings.template_id == "settings_json.j2"
    assert settings.layer == OutputLayer.PROJECT
    hooks = settings.context["hooks"]
    assert hooks == [{"command": "ruff check .", "exit_code": 2}]


def test_plan_omits_settings_json_when_no_hooks():
    profile = _make_profile("web", ["fix-issue"], [])
    # _make_profile returns hook_templates=[]
    result = plan(_make_spec(), profile, _TEMPLATES)
    assert not any(a.target_path == "settings.json" for a in result.artifacts)


def test_plan_settings_json_typescript_uses_eslint():
    profile = DomainProfile(
        domain="web",
        display_name="Web",
        description="Test",
        skill_slugs=["fix-issue"],
        agent_slugs=[],
        claude_md_sections=["plan_execute_verify"],
        hook_templates=["lint_after_edit", "typecheck_after_edit"],
        detection_signals=[],
    )
    spec = ProjectSpec(name="x", description="x", languages=["typescript"])
    result = plan(spec, profile, _TEMPLATES)
    settings = next(a for a in result.artifacts if a.target_path == "settings.json")
    commands = [h["command"] for h in settings.context["hooks"]]
    assert "eslint" in commands[0]
    assert "tsc" in commands[1]


def test_plan_settings_json_unknown_language_uses_placeholder():
    profile = DomainProfile(
        domain="general",
        display_name="General",
        description="Test",
        skill_slugs=["fix-issue"],
        agent_slugs=[],
        claude_md_sections=["plan_execute_verify"],
        hook_templates=["lint_after_edit"],
        detection_signals=[],
    )
    spec = ProjectSpec(name="x", description="x", languages=["esoteric-lang"])
    result = plan(spec, profile, _TEMPLATES)
    settings = next(a for a in result.artifacts if a.target_path == "settings.json")
    cmd = settings.context["hooks"][0]["command"]
    assert "configure this hook" in cmd


# ---------------------------------------------------------------------------
# Profile / catalogue consistency — regression guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "profile_filename",
    ["cli.yaml", "data.yaml", "general.yaml", "infra.yaml", "web.yaml"],
)
def test_profile_slugs_all_in_catalogue(profile_filename: str):
    """Every skill/agent slug a profile declares must exist in the catalogue.

    Otherwise the planner emits hollow `Perform <slug> tasks` stubs that
    pollute the user's .claude/skills/ with unhelpful placeholders. If a
    domain wants a new skill, author its catalogue entry first.
    """
    from claude_env.generator.content_catalogue import (
        known_agent_slugs,
        known_skill_slugs,
    )
    from claude_env.models.domain_profile import load_profile

    profiles_dir = Path(__file__).parent.parent / "claude_env" / "profiles"
    profile = load_profile(profiles_dir / profile_filename)
    cat_skills = set(known_skill_slugs())
    cat_agents = set(known_agent_slugs())

    orphan_skills = set(profile.skill_slugs) - cat_skills
    orphan_agents = set(profile.agent_slugs) - cat_agents

    assert not orphan_skills, (
        f"{profile_filename} declares skill slugs not in the catalogue: "
        f"{sorted(orphan_skills)}"
    )
    assert not orphan_agents, (
        f"{profile_filename} declares agent slugs not in the catalogue: "
        f"{sorted(orphan_agents)}"
    )


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
    # 3 fixed (CLAUDE.md, CONTEXT.md, docs/adr/README.md) + per-skill + per-agent +
    # sidecars + settings.json (web profile declares hook_templates).
    # Web profile ships tdd (5 sidecars) and grill-with-docs (2 sidecars).
    sidecar_count = (5 if "tdd" in web_profile.skill_slugs else 0) + (
        2 if "grill-with-docs" in web_profile.skill_slugs else 0
    )
    settings_count = 1 if web_profile.hook_templates else 0
    expected_count = (
        3
        + len(web_profile.skill_slugs)
        + len(web_profile.agent_slugs)
        + sidecar_count
        + settings_count
    )
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
