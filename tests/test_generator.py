"""Tests for Generator class — GEN-01 through GEN-06."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_env.generator.generator import Generator
from claude_env.generator.sentinel import SENTINEL_HEADER, has_sentinel, wrap_with_sentinel
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer


# ---------------------------------------------------------------------------
# GEN-01: Per-project CLAUDE.md content
# ---------------------------------------------------------------------------


def test_claude_md_line_count(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    content = (tmp_path / ".claude/CLAUDE.md").read_text(encoding="utf-8")
    assert len(content.splitlines()) <= 200


def test_claude_md_required_sections(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    content = (tmp_path / ".claude/CLAUDE.md").read_text(encoding="utf-8").lower()
    assert "plan" in content
    assert "execute" in content
    assert "verify" in content
    assert "context" in content
    assert "lessons.md" in content


# ---------------------------------------------------------------------------
# GEN-02: Skill files
# ---------------------------------------------------------------------------


def test_skill_files_created(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    for slug in ["fix-issue", "create-pr", "run-lint", "update-deps"]:
        assert (tmp_path / f".claude/skills/{slug}/SKILL.md").exists(), f"Missing skill: {slug}"


def test_skill_frontmatter(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    content = (tmp_path / ".claude/skills/fix-issue/SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "name:" in content
    assert "description:" in content
    # Extract description line and check it starts with a verb (action word)
    for line in content.splitlines():
        if line.startswith("description:"):
            description_value = line.split(":", 1)[1].strip()
            # First word should be a verb (action word — capitalize check)
            first_word = description_value.split()[0].rstrip(",")
            assert first_word[0].isupper() or first_word[0].islower()
            # Description should start with a verb: common verbs in catalogue
            assert any(description_value.lower().startswith(v) for v in [
                "diagnose", "stage", "run", "update", "scaffold", "perform"
            ]), f"Description does not start with a verb: {description_value}"
            break


# ---------------------------------------------------------------------------
# GEN-03: Agent files
# ---------------------------------------------------------------------------


def test_agent_files_created(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    assert (tmp_path / ".claude/agents/security-reviewer.md").exists()
    assert (tmp_path / ".claude/agents/accessibility-auditor.md").exists()


def test_agent_skills_field(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    content = (tmp_path / ".claude/agents/security-reviewer.md").read_text(encoding="utf-8")
    assert "skills:" in content
    assert "  - " in content  # at least one skill listed


# ---------------------------------------------------------------------------
# GEN-04: settings.json
# ---------------------------------------------------------------------------


def _settings_plan() -> GenerationPlan:
    return GenerationPlan(
        project_name="test-proj",
        domain="web",
        artifacts=[
            Artifact(
                target_path="settings.json",
                template_id="settings_json.j2",
                context={"hooks": [{"command": "/usr/bin/ruff check .", "exit_code": 2}]},
                layer=OutputLayer.PROJECT,
            )
        ],
    )


def test_settings_json(tmp_path: Path, real_registry) -> None:
    gen = Generator(real_registry)
    gen.execute(_settings_plan(), tmp_path, tmp_path / "global")
    content = (tmp_path / ".claude/settings.json").read_text(encoding="utf-8")
    data = json.loads(content)
    hook = data["hooks"]["PostToolUse"][0]["hooks"][0]
    assert hook["exitCode"] == 2
    assert hook["command"] == "/usr/bin/ruff check ."


# ---------------------------------------------------------------------------
# GEN-05: Global CLAUDE.md sentinel
# ---------------------------------------------------------------------------


def _global_claude_md_plan() -> GenerationPlan:
    return GenerationPlan(
        project_name="test-global",
        domain="web",
        artifacts=[
            Artifact(
                target_path="CLAUDE.md",
                template_id="claude_md_project.j2",
                context={
                    "project_name": "test-global",
                    "domain": "web",
                    "sections": ["plan_execute_verify", "context_management", "lessons_loop"],
                },
                layer=OutputLayer.GLOBAL,
            )
        ],
    )


def test_global_claude_md_first_write(tmp_path: Path, real_registry) -> None:
    global_root = tmp_path / "global"
    gen = Generator(real_registry)
    gen.execute(_global_claude_md_plan(), tmp_path, global_root)
    target = global_root / "CLAUDE.md"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert content.startswith(SENTINEL_HEADER)
    assert has_sentinel(content)


def test_global_claude_md_preserves_existing(tmp_path: Path, real_registry) -> None:
    global_root = tmp_path / "global"
    global_root.mkdir()
    # Pre-create file with user content but no sentinel markers
    existing_file = global_root / "CLAUDE.md"
    existing_file.write_text("# My global config\n", encoding="utf-8")

    gen = Generator(real_registry)
    gen.execute(_global_claude_md_plan(), tmp_path, global_root)

    content = existing_file.read_text(encoding="utf-8")
    assert "My global config" in content  # user content preserved
    assert has_sentinel(content)  # managed block appended


# ---------------------------------------------------------------------------
# GEN-06: Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_rerun(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    global_root = tmp_path / "global"
    gen.execute(web_plan, tmp_path, global_root)

    # Collect all PROJECT-layer paths and their content
    first_run: dict[str, str] = {}
    for artifact in web_plan.artifacts:
        file_path = tmp_path / ".claude" / artifact.target_path
        if file_path.exists():
            first_run[artifact.target_path] = file_path.read_text(encoding="utf-8")

    gen.execute(web_plan, tmp_path, global_root)

    for target_path, first_content in first_run.items():
        second_content = (tmp_path / ".claude" / target_path).read_text(encoding="utf-8")
        assert first_content == second_content, f"Content changed on re-run: {target_path}"


def test_idempotent_rerun_settings_json(tmp_path: Path, real_registry) -> None:
    gen = Generator(real_registry)
    plan = _settings_plan()
    global_root = tmp_path / "global"

    gen.execute(plan, tmp_path, global_root)
    first = (tmp_path / ".claude/settings.json").read_text(encoding="utf-8")

    gen.execute(plan, tmp_path, global_root)
    second = (tmp_path / ".claude/settings.json").read_text(encoding="utf-8")

    assert first == second


def test_idempotent_rerun_global(tmp_path: Path, real_registry) -> None:
    global_root = tmp_path / "global"
    gen = Generator(real_registry)
    plan = _global_claude_md_plan()

    gen.execute(plan, tmp_path, global_root)
    first = (global_root / "CLAUDE.md").read_text(encoding="utf-8")

    gen.execute(plan, tmp_path, global_root)
    second = (global_root / "CLAUDE.md").read_text(encoding="utf-8")

    assert first == second


def test_user_edits_preserved_on_rerun(tmp_path: Path, real_registry) -> None:
    global_root = tmp_path / "global"
    gen = Generator(real_registry)
    plan = _global_claude_md_plan()

    # First run — creates sentinel-wrapped file
    gen.execute(plan, tmp_path, global_root)
    target = global_root / "CLAUDE.md"
    content = target.read_text(encoding="utf-8")
    assert has_sentinel(content)

    # Append user edit after the sentinel block
    target.write_text(content + "\n# USER EDIT\n", encoding="utf-8")

    # Second run — managed block updated, user edit must survive
    gen.execute(plan, tmp_path, global_root)
    result = target.read_text(encoding="utf-8")
    assert "# USER EDIT" in result
    assert has_sentinel(result)


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------


def test_path_traversal_rejected(tmp_path: Path, real_registry) -> None:
    plan = GenerationPlan(
        project_name="evil",
        domain="web",
        artifacts=[
            Artifact(
                target_path="../../etc/evil",
                template_id="claude_md_project.j2",
                context={
                    "project_name": "evil",
                    "domain": "web",
                    "sections": [],
                },
                layer=OutputLayer.PROJECT,
            )
        ],
    )
    gen = Generator(real_registry)
    with pytest.raises(ValueError, match="Path traversal"):
        gen.execute(plan, tmp_path, tmp_path / "global")


# ---------------------------------------------------------------------------
# Basic
# ---------------------------------------------------------------------------


def test_execute_returns_written_paths(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    written = gen.execute(web_plan, tmp_path, tmp_path / "global")
    assert isinstance(written, list)
    assert all(isinstance(p, Path) for p in written)
    assert len(written) == len(web_plan.artifacts)


def test_creates_parent_dirs(tmp_path: Path, real_registry, web_plan: GenerationPlan) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "global")
    assert (tmp_path / ".claude/skills/fix-issue").is_dir()
