---
phase: "04-cli-skill"
plan: "01"
subsystem: cli
tags: [cli, typer, generator, dry-run, path-resolution]
dependency_graph:
  requires: [03-generator]
  provides: [cli-setup, cli-bootstrap, resolve-plan-paths]
  affects: [cli-skill-installation]
tech_stack:
  added: [typer, rich]
  patterns: [lazy-imports-in-commands, module-level-path-constants]
key_files:
  created: [tests/test_cli.py]
  modified: [claude_env/cli.py, claude_env/generator/generator.py]
decisions:
  - "resolve_plan_paths() extracted as module-level function in generator.py; Generator.execute() calls it internally — single source of truth for path resolution"
  - "Heavy imports (Generator, InputNormalizer, pipeline) kept inside command bodies to avoid loading anthropic at CLI startup"
  - "setup uses project_root=Path.home() so PROJECT-layer writes to ~/.claude/ (Pitfall #4 fix)"
  - "API key error detected via substring match on exception message — avoids importing anthropic at module level"
  - "HOOK comment left in setup() as anchor for Plan 04-02 SKILL.md installation"
metrics:
  duration: "~15 min"
  completed: "2026-04-20"
  tasks_completed: 2
  files_changed: 3
---

# Phase 4 Plan 1: CLI Setup and Bootstrap Commands Summary

**One-liner:** Typer CLI with `setup` (global ~/.claude/ layer) and `bootstrap` (per-project .claude/ with --spec and --dry-run), wired to full pipeline via lazy imports and `resolve_plan_paths()` as single path-resolution source of truth.

## What Was Built

- `claude_env/cli.py` — Replaced stub with three commands: `version`, `setup`, `bootstrap`
- `claude_env/generator/generator.py` — Extracted `resolve_plan_paths()` as module-level function; `Generator.execute()` delegates to it; `_resolve_path()` removed
- `tests/test_cli.py` — 8 integration tests covering version, setup, bootstrap, dry-run, LLM skip with --spec, and API key error

## Commands Implemented

**`claude-env setup`**
- Prompts for user name (single interactive input)
- Builds a `general` profile GenerationPlan
- Writes `~/.claude/` layer (PROJECT-layer → Path.home()/.claude/)
- HOOK anchor ready for Plan 04-02 SKILL.md installation

**`claude-env bootstrap [project_dir] [--spec file] [--dry-run]`**
- `--spec`: reads YAML/MD spec via `InputNormalizer.from_spec_file()` — no LLM
- Freeform: prompts for description, uses `InputNormalizer.from_freeform()` with LLM
- `--dry-run`: calls `resolve_plan_paths()`, prints paths, writes nothing
- Clean error message for missing `ANTHROPIC_API_KEY`

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `claude_env/cli.py`: exists, 3 `@app.command()` decorators, `setup`, `bootstrap`, `version` defined
- `claude_env/generator/generator.py`: `resolve_plan_paths` defined at module level, called from `Generator.execute()`
- `tests/test_cli.py`: 8 tests, all passing
- All commits present: `cf5d4a8` (test RED), `3006c2b` (feat GREEN)
- Full suite: 97 tests passed, mypy clean, ruff clean
