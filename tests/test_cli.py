"""CLI integration tests via typer.testing.CliRunner."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from claude_env.cli import app

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures" / "specs"


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "claude-env" in result.output


def test_setup_writes_general_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    assert (tmp_path / ".claude" / "CLAUDE.md").exists()


def test_setup_uses_global_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    content = (tmp_path / ".claude" / "CLAUDE.md").read_text()
    assert "Plan" in content  # claude_md_project.j2 plan_execute_verify section


def test_setup_installs_full_skill_catalogue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """setup must install every catalogued skill globally — not a subset."""
    from claude_env.generator.content_catalogue import known_skill_slugs

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    skills_dir = tmp_path / ".claude" / "skills"
    for slug in known_skill_slugs():
        assert (skills_dir / slug / "SKILL.md").exists(), f"Missing global skill: {slug}"


def test_setup_installs_all_catalogued_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from claude_env.generator.content_catalogue import known_agent_slugs

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    agents_dir = tmp_path / ".claude" / "agents"
    for slug in known_agent_slugs():
        assert (agents_dir / f"{slug}.md").exists(), f"Missing global agent: {slug}"


def test_setup_installs_skill_sidecars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """tdd and grill-with-docs sidecars must land alongside SKILL.md globally."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    tdd = tmp_path / ".claude/skills/tdd"
    for s in ("tests.md", "mocking.md", "deep-modules.md",
              "interface-design.md", "refactoring.md"):
        assert (tdd / s).exists(), f"Missing tdd sidecar: {s}"
    grill = tmp_path / ".claude/skills/grill-with-docs"
    assert (grill / "CONTEXT-FORMAT.md").exists()
    assert (grill / "ADR-FORMAT.md").exists()


def test_build_global_profile_kitchen_sink() -> None:
    """The helper that drives setup must return every catalogued slug."""
    from claude_env.cli import _build_global_profile
    from claude_env.generator.content_catalogue import (
        known_agent_slugs,
        known_skill_slugs,
    )

    profile = _build_global_profile()
    assert profile.skill_slugs == known_skill_slugs()
    assert profile.agent_slugs == known_agent_slugs()
    assert profile.detection_signals == []  # never picked by classifier


def test_bootstrap_with_browser_flag_writes_mcp_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--spec", str(spec), "--with-browser"]
    )
    assert result.exit_code == 0, result.output
    mcp = project_dir / ".mcp.json"
    assert mcp.exists()
    assert not (project_dir / ".claude" / ".mcp.json").exists()
    data = json.loads(mcp.read_text())
    assert "playwright" in data["mcpServers"]


def test_bootstrap_combines_multiple_mcp_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app,
        ["bootstrap", str(project_dir), "--spec", str(spec),
         "--with-browser", "--with-context7", "--with-sequential-thinking"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads((project_dir / ".mcp.json").read_text())
    assert set(data["mcpServers"].keys()) == {
        "playwright", "context7", "sequential-thinking"
    }


def test_bootstrap_no_mcp_flags_no_mcp_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--spec", str(spec)]
    )
    assert result.exit_code == 0, result.output
    assert not (project_dir / ".mcp.json").exists()


def test_bootstrap_with_claude_mem_emits_plugin_hint_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """claude-mem is a plugin, not an MCP — surfaces guidance, no .mcp.json."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--spec", str(spec), "--with-claude-mem"]
    )
    assert result.exit_code == 0, result.output
    assert "claude-mem" in result.output
    assert "plugin" in result.output.lower()
    assert not (project_dir / ".mcp.json").exists()


def test_bootstrap_with_spec_file_writes_project_layer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--spec", str(spec)]
    )
    assert result.exit_code == 0, result.output
    assert (project_dir / ".claude" / "CLAUDE.md").exists()


def test_bootstrap_with_spec_skips_llm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--spec", str(spec)]
    )
    assert result.exit_code == 0, result.output


def test_bootstrap_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--spec", str(spec), "--dry-run"]
    )
    assert result.exit_code == 0, result.output
    assert "would write" in result.output
    assert not (project_dir / ".claude").exists()


def test_dry_run_paths_match_actual_paths(
    tmp_path: Path, web_plan, real_registry
) -> None:
    from claude_env.generator.generator import Generator, resolve_plan_paths

    project_root = tmp_path / "proj"
    global_root = tmp_path / "global"
    project_root.mkdir()
    global_root.mkdir()
    expected = resolve_plan_paths(web_plan, project_root, global_root)
    actual = Generator(real_registry).execute(web_plan, project_root, global_root)
    assert expected == actual


def test_bootstrap_with_description_flag_skips_interactive_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    # With --description, no interactive prompt is attempted — but LLM call
    # still fails cleanly without a key (expected non-zero exit)
    result = runner.invoke(
        app, ["bootstrap", str(project_dir), "--description", "a CLI tool in Python", "--dry-run"]
    )
    # Either succeeds (key present in env) or exits cleanly with API key message
    assert result.exit_code in (0, 1)
    if result.exit_code == 1:
        assert "ANTHROPIC_API_KEY" in result.output or "api_key" in result.output.lower()


def test_bootstrap_missing_api_key_freeform_clean_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    result = runner.invoke(
        app, ["bootstrap", str(project_dir)], input="a web app\n"
    )
    # Either clean exit-1 with guidance, or the message surfaces in output
    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output or "api_key" in result.output.lower()
