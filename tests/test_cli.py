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


def test_setup_uses_general_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    content = (tmp_path / ".claude" / "CLAUDE.md").read_text()
    assert "Plan" in content  # claude_md_project.j2 plan_execute_verify section


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
