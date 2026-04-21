"""Tests for SKILL.md installation via claude-env setup."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from claude_env.cli import app

runner = CliRunner()


def _extract_frontmatter(text: str) -> tuple[dict, str]:
    assert text.startswith("---\n"), f"no frontmatter: {text[:40]!r}"
    _, rest = text.split("---\n", 1)
    front, body = rest.split("---\n", 1)
    return yaml.safe_load(front), body


def test_setup_creates_skill_md_at_correct_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    skill_path = tmp_path / ".claude" / "skills" / "claude-env" / "SKILL.md"
    assert skill_path.exists(), f"SKILL.md not found at {skill_path}"


def test_skill_md_has_valid_yaml_frontmatter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    skill_path = tmp_path / ".claude" / "skills" / "claude-env" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    frontmatter, _ = _extract_frontmatter(content)
    assert frontmatter["name"] == "claude-env"
    assert frontmatter["allowed-tools"] == "Bash"
    assert isinstance(frontmatter["description"], str)
    assert len(frontmatter["description"]) > 0


def test_skill_md_description_is_verb_phrase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    skill_path = tmp_path / ".claude" / "skills" / "claude-env" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    frontmatter, _ = _extract_frontmatter(content)
    description = frontmatter["description"]
    first_word = description.split()[0]
    verb_whitelist = {
        "Generate", "Create", "Bootstrap", "Build", "Install", "Set", "Produce", "Write"
    }
    assert first_word in verb_whitelist, f"Description does not start with a verb: {description!r}"


def test_skill_md_body_references_bootstrap_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    skill_path = tmp_path / ".claude" / "skills" / "claude-env" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    _, body = _extract_frontmatter(content)
    assert "claude-env bootstrap" in body, "Body does not reference 'claude-env bootstrap'"


def test_skill_md_body_mentions_dry_run_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output
    skill_path = tmp_path / ".claude" / "skills" / "claude-env" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    _, body = _extract_frontmatter(content)
    assert "--dry-run" in body, "Body does not mention '--dry-run'"


def test_setup_is_idempotent_for_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # First run
    result1 = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result1.exit_code == 0, result1.output
    skill_path = tmp_path / ".claude" / "skills" / "claude-env" / "SKILL.md"
    content_first = skill_path.read_text(encoding="utf-8")

    # Second run
    result2 = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result2.exit_code == 0, result2.output
    content_second = skill_path.read_text(encoding="utf-8")

    # Exactly one SKILL.md — no backup files
    skill_dir = tmp_path / ".claude" / "skills" / "claude-env"
    files_in_dir = [f.name for f in skill_dir.iterdir()]
    assert files_in_dir == ["SKILL.md"], f"Unexpected files in skill dir: {files_in_dir}"

    # Content is identical
    assert content_first == content_second


def test_install_skill_does_not_disturb_other_files_in_skills_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Pre-create an unrelated skill file
    unrelated_dir = tmp_path / ".claude" / "skills" / "unrelated"
    unrelated_dir.mkdir(parents=True)
    unrelated_file = unrelated_dir / "SKILL.md"
    unrelated_file.write_text("unrelated-content", encoding="utf-8")

    result = runner.invoke(app, ["setup"], input="Manuel\n")
    assert result.exit_code == 0, result.output

    # Unrelated file must be untouched
    assert unrelated_file.exists()
    assert unrelated_file.read_text(encoding="utf-8") == "unrelated-content"
