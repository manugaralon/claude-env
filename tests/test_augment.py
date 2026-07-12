"""Phase 7 — Augment Mode acceptance tests.

Covers the five locked acceptance criteria in
``.planning/phases/07-augment-mode/07-SPEC.md``:

  AC1  Artifact has merge_strategy; generator dispatches on it (back-compat).
  AC2  Non-destructive CLAUDE.md augment: managed block into the existing
       CLAUDE.md, never a second one; non-managed lines byte-identical.
  AC3  write_once constitution never overwritten; existing CONTEXT.md / skills
       skipped, not clobbered.
  AC4  --dry-run reports the resolved per-artifact action and writes zero bytes.
  AC5  Plain bootstrap on a mature project alters zero human-authored content.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from claude_env.cli import app
from claude_env.generator.generator import (
    Generator,
    ResolvedArtifact,
    effective_merge_strategy,
    resolve_plan,
)
from claude_env.generator.sentinel import (
    SENTINEL_HEADER,
    has_sentinel,
)
from claude_env.models.generation_plan import (
    Artifact,
    GenerationPlan,
    MergeStrategy,
    OutputLayer,
)

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures" / "specs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _claude_md_artifact(strategy: MergeStrategy = MergeStrategy.SENTINEL) -> Artifact:
    return Artifact(
        target_path="CLAUDE.md",
        template_id="claude_md_project.j2",
        context={"project_name": "p", "domain": "web", "sections": ["plan_execute_verify"]},
        layer=OutputLayer.PROJECT,
        merge_strategy=strategy,
    )


def _plan(*artifacts: Artifact) -> GenerationPlan:
    return GenerationPlan(project_name="p", domain="web", artifacts=list(artifacts))


def _all_files(root: Path) -> set[Path]:
    return {p for p in root.rglob("*") if p.is_file()}


# ---------------------------------------------------------------------------
# AC1 — merge_strategy field + strategy dispatch (not layer inference)
# ---------------------------------------------------------------------------


def test_effective_strategy_back_compat_mapping() -> None:
    """Unset merge_strategy maps from layer/write_once identically to pre-Phase-7."""
    global_art = Artifact(
        target_path="CLAUDE.md", template_id="t", context={}, layer=OutputLayer.GLOBAL
    )
    project_art = Artifact(
        target_path="settings.json", template_id="t", context={}, layer=OutputLayer.PROJECT
    )
    project_root_art = Artifact(
        target_path=".mcp.json", template_id="t", context={}, layer=OutputLayer.PROJECT_ROOT
    )
    write_once_art = Artifact(
        target_path=".planning/CONSTITUTION.md", template_id="t", context={},
        layer=OutputLayer.PROJECT_ROOT, write_once=True,
    )
    assert effective_merge_strategy(global_art) == MergeStrategy.SENTINEL
    assert effective_merge_strategy(project_art) == MergeStrategy.OVERWRITE
    assert effective_merge_strategy(project_root_art) == MergeStrategy.OVERWRITE
    assert effective_merge_strategy(write_once_art) == MergeStrategy.WRITE_ONCE


def test_explicit_strategy_overrides_layer_mapping() -> None:
    """An explicit merge_strategy wins over the layer-derived default."""
    art = _claude_md_artifact(MergeStrategy.SENTINEL)  # PROJECT layer + SENTINEL
    assert art.layer == OutputLayer.PROJECT
    assert effective_merge_strategy(art) == MergeStrategy.SENTINEL


def test_dispatch_is_on_strategy_not_layer(tmp_path: Path, real_registry) -> None:
    """A PROJECT-layer artifact with SENTINEL strategy is sentinel-wrapped.

    Proves the generator dispatches on merge_strategy, not on layer (a PROJECT
    artifact used to be a plain overwrite).
    """
    Generator(real_registry).execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")
    content = (tmp_path / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
    assert content.startswith(SENTINEL_HEADER)
    assert has_sentinel(content)


# ---------------------------------------------------------------------------
# AC2 — non-destructive CLAUDE.md augment
# ---------------------------------------------------------------------------


def test_augment_merges_into_bespoke_root_claude_md(tmp_path: Path, real_registry) -> None:
    bespoke = "# Clibit\n\nHand-written founder rules.\n\n## Section\n\nMore human content.\n"
    (tmp_path / "CLAUDE.md").write_text(bespoke, encoding="utf-8")

    Generator(real_registry).execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")

    result = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    # Managed block injected...
    assert has_sentinel(result)
    # ...and every byte of the human content before the block is preserved.
    assert result.startswith(bespoke.rstrip("\n"))
    for line in bespoke.splitlines():
        assert line in result


def test_augment_never_creates_second_claude_md(tmp_path: Path, real_registry) -> None:
    (tmp_path / "CLAUDE.md").write_text("# bespoke root\n", encoding="utf-8")
    Generator(real_registry).execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")
    # The managed block went into the ROOT file — NOT a second .claude/CLAUDE.md.
    assert not (tmp_path / ".claude" / "CLAUDE.md").exists()


def test_augment_prefers_root_over_dotclaude(tmp_path: Path, real_registry) -> None:
    (tmp_path / "CLAUDE.md").write_text("# root bespoke\n", encoding="utf-8")
    dot = tmp_path / ".claude" / "CLAUDE.md"
    dot.parent.mkdir(parents=True)
    dot.write_text("# dot bespoke\n", encoding="utf-8")

    Generator(real_registry).execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")

    # Root gets the managed block (precedence); .claude/CLAUDE.md is untouched.
    assert has_sentinel((tmp_path / "CLAUDE.md").read_text(encoding="utf-8"))
    assert dot.read_text(encoding="utf-8") == "# dot bespoke\n"


def test_augment_merges_into_existing_dotclaude_when_no_root(
    tmp_path: Path, real_registry
) -> None:
    dot = tmp_path / ".claude" / "CLAUDE.md"
    dot.parent.mkdir(parents=True)
    dot.write_text("# dot bespoke\n\nkeep me\n", encoding="utf-8")

    Generator(real_registry).execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")

    result = dot.read_text(encoding="utf-8")
    assert has_sentinel(result)
    assert "keep me" in result
    assert not (tmp_path / "CLAUDE.md").exists()  # no bespoke root invented


def test_augment_greenfield_writes_fresh_dotclaude(tmp_path: Path, real_registry) -> None:
    Generator(real_registry).execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")
    dot = tmp_path / ".claude" / "CLAUDE.md"
    assert dot.exists()
    assert has_sentinel(dot.read_text(encoding="utf-8"))
    assert not (tmp_path / "CLAUDE.md").exists()


def test_augment_is_idempotent_on_bespoke_root(tmp_path: Path, real_registry) -> None:
    bespoke = "# founder\n\nsovereign content\n"
    (tmp_path / "CLAUDE.md").write_text(bespoke, encoding="utf-8")
    gen = Generator(real_registry)

    gen.execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")
    first = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    gen.execute(_plan(_claude_md_artifact()), tmp_path, tmp_path / "g")
    second = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")

    assert first == second  # re-run only refreshes the managed block in place
    assert first.startswith(bespoke.rstrip("\n"))


# ---------------------------------------------------------------------------
# AC3 — write_once + skip_if_exists never clobber bespoke content
# ---------------------------------------------------------------------------


def test_skip_if_exists_preserves_existing_context_md(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    ctx = tmp_path / ".claude" / "CONTEXT.md"
    ctx.parent.mkdir(parents=True)
    bespoke = "# Ubiquitous language\n\nPatient, Appointment, DPA gate.\n"
    ctx.write_text(bespoke, encoding="utf-8")

    Generator(real_registry).execute(web_plan, tmp_path, tmp_path / "g")

    assert ctx.read_text(encoding="utf-8") == bespoke  # byte-identical


def test_skip_if_exists_preserves_existing_skill(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    skill = tmp_path / ".claude" / "skills" / "fix-issue" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    bespoke = "---\nname: fix-issue\ndescription: Fix my way\n---\n\nCustom body.\n"
    skill.write_text(bespoke, encoding="utf-8")

    Generator(real_registry).execute(web_plan, tmp_path, tmp_path / "g")

    assert skill.read_text(encoding="utf-8") == bespoke  # untouched


def test_skip_if_exists_creates_absent_context_md(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    Generator(real_registry).execute(web_plan, tmp_path, tmp_path / "g")
    assert (tmp_path / ".claude" / "CONTEXT.md").exists()  # absent -> created


def test_write_once_constitution_never_overwritten(
    tmp_path: Path, real_registry, web_plan: GenerationPlan
) -> None:
    gen = Generator(real_registry)
    gen.execute(web_plan, tmp_path, tmp_path / "g")
    const = tmp_path / ".planning" / "CONSTITUTION.md"
    const.write_text("HAND-EDITED", encoding="utf-8")
    gen.execute(web_plan, tmp_path, tmp_path / "g")
    assert const.read_text(encoding="utf-8") == "HAND-EDITED"


# ---------------------------------------------------------------------------
# AC4 — dry-run reports resolved action per artifact, writes zero bytes
# ---------------------------------------------------------------------------


def _find(resolved: list[ResolvedArtifact], suffix: str) -> ResolvedArtifact:
    return next(r for r in resolved if str(r.target).endswith(suffix))


def test_resolve_plan_reports_actions_against_real_state(
    tmp_path: Path, web_plan: GenerationPlan
) -> None:
    # Seed a mixed target state.
    (tmp_path / "CLAUDE.md").write_text("# bespoke\n", encoding="utf-8")          # -> merge
    ctx = tmp_path / ".claude" / "CONTEXT.md"
    ctx.parent.mkdir(parents=True)
    ctx.write_text("# ctx\n", encoding="utf-8")                                   # -> skip
    settings = tmp_path / ".claude" / "settings.json"
    settings.write_text("{}\n", encoding="utf-8")                                 # -> overwrite
    (tmp_path / ".planning").mkdir()
    (tmp_path / ".planning" / "CONSTITUTION.md").write_text("c\n", encoding="utf-8")  # -> skip

    before = _all_files(tmp_path)
    resolved = resolve_plan(web_plan, tmp_path, tmp_path / "g")
    after = _all_files(tmp_path)

    assert before == after  # resolve_plan writes nothing

    assert _find(resolved, "/CLAUDE.md").action == "merge-managed-block"
    # bespoke root CLAUDE.md is the resolved target — no .claude/CLAUDE.md invented
    assert _find(resolved, "/CLAUDE.md").target == (tmp_path / "CLAUDE.md").resolve()
    assert _find(resolved, ".claude/CONTEXT.md").action == "skip-exists"
    assert _find(resolved, "settings.json").action == "overwrite"
    assert _find(resolved, "CONSTITUTION.md").action == "skip-exists"
    # an absent skill resolves to a create
    assert any(r.action == "create" and str(r.target).endswith("SKILL.md") for r in resolved)


def test_cli_dry_run_reports_actions_and_writes_nothing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)
    project = tmp_path / "proj"
    project.mkdir()
    root_claude = project / "CLAUDE.md"
    root_claude.write_text("# bespoke\n", encoding="utf-8")
    ctx = project / ".claude" / "CONTEXT.md"
    ctx.parent.mkdir(parents=True)
    ctx.write_text("# ctx\n", encoding="utf-8")

    before = _all_files(project)
    result = runner.invoke(app, ["bootstrap", str(project), "--spec", str(spec), "--dry-run"])
    after = _all_files(project)

    assert result.exit_code == 0, result.output
    # Resolved actions surfaced
    assert "merge-managed-block" in result.output
    assert "skip-exists" in result.output
    assert "create" in result.output
    # Nothing written — every pre-existing file byte-identical, no new files
    assert before == after
    assert root_claude.read_text(encoding="utf-8") == "# bespoke\n"
    assert ctx.read_text(encoding="utf-8") == "# ctx\n"


# ---------------------------------------------------------------------------
# AC5 — plain bootstrap is safe by default on a mature project
# ---------------------------------------------------------------------------


def test_bootstrap_no_flags_safe_on_mature_project(tmp_path, monkeypatch) -> None:
    """bootstrap (no flags) on a mature project alters zero human-authored bytes."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    spec = tmp_path / "spec.yaml"
    shutil.copy(FIXTURES / "simple_web.yaml", spec)

    project = tmp_path / "mature"
    project.mkdir()
    # Bespoke, hand-authored artifacts a mature repo would already have.
    bespoke_claude = (
        "# Clibit — founder rules\n\n"
        "Multi-tenant from day one. RLS always FORCE.\n\n"
        "## Non-negotiables\n\nNotes editable only day-of-creation.\n"
    )
    (project / "CLAUDE.md").write_text(bespoke_claude, encoding="utf-8")
    bespoke_ctx = "# Domain language\n\nPatient, Appointment, DPA gate.\n"
    ctx = project / ".claude" / "CONTEXT.md"
    ctx.parent.mkdir(parents=True)
    ctx.write_text(bespoke_ctx, encoding="utf-8")
    bespoke_skill = (
        "---\nname: fix-issue\ndescription: Fix the reported bug fast\n---\n\n"
        "Bespoke skill body — do not touch.\n"
    )
    skill = project / ".claude" / "skills" / "fix-issue" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(bespoke_skill, encoding="utf-8")

    result = runner.invoke(app, ["bootstrap", str(project), "--spec", str(spec)])
    assert result.exit_code == 0, result.output

    # Human-authored content: byte-identical outside the managed block.
    claude_after = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_after.startswith(bespoke_claude.rstrip("\n"))
    assert has_sentinel(claude_after)  # managed block added
    assert ctx.read_text(encoding="utf-8") == bespoke_ctx  # untouched
    assert skill.read_text(encoding="utf-8") == bespoke_skill  # untouched

    # Never a second CLAUDE.md.
    assert not (project / ".claude" / "CLAUDE.md").exists()

    # Additive only: absent files were created (e.g. an agent, another skill).
    assert (project / ".claude" / "agents").is_dir()
    assert (project / ".planning" / "CONSTITUTION.md").exists()
