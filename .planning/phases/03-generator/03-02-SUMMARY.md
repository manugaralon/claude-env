---
phase: 03-generator
plan: "02"
subsystem: generator
tags: [generator, sentinel, tdd, artifact-writing, path-traversal]
dependency_graph:
  requires: [03-01]
  provides: [Generator class, GEN-01 through GEN-06 test coverage]
  affects: [CLI phase, integration tests]
tech_stack:
  added: []
  patterns: [TDD red-green, sentinel-aware file writing, layer-based dispatch]
key_files:
  created:
    - claude_env/generator/generator.py
    - tests/test_generator.py
  modified:
    - tests/conftest.py
decisions:
  - Generator dispatches on artifact.layer (not has_sentinel()) — file content never determines write strategy
  - GLOBAL-layer first write uses wrap_with_sentinel so sentinel markers exist from day one
  - PROJECT-layer always overwrites unconditionally — no sentinel involvement
  - merge_sentinel_block handles both pre-existing sentinel and sentinel-free files internally
metrics:
  duration: "~3 min"
  completed: "2026-04-19"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 03 Plan 02: Generator Class Summary

**One-liner:** Generator class with layer-aware sentinel dispatch (wrap_with_sentinel for new GLOBAL files, merge_sentinel_block for existing) and 16-test suite covering GEN-01 through GEN-06.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Failing test suite for Generator | a8f9e9c | tests/test_generator.py, tests/conftest.py |
| 1 (GREEN) | Generator class implementation | d0aa26e | claude_env/generator/generator.py |

## What Was Built

### Generator class (`claude_env/generator/generator.py`)

- `Generator(registry).execute(plan, project_root, global_root) -> list[Path]`
- PROJECT-layer: writes to `project_root/.claude/<target_path>`, plain overwrite
- GLOBAL-layer: writes to `global_root/<target_path>`:
  - File absent → `wrap_with_sentinel(rendered)` (sentinel markers from first write)
  - File exists → `merge_sentinel_block(existing, rendered)` (preserves user content)
- `_resolve_path()`: raises `ValueError("Path traversal detected: ...")` for `..` escapes
- All writes: `mkdir(parents=True, exist_ok=True)` + `encoding="utf-8"`
- CRITICAL: `has_sentinel` is never imported or called — layer field is the only dispatch signal

### Test suite (`tests/test_generator.py`)

16 tests covering all 6 GEN requirements:

- GEN-01: CLAUDE.md ≤200 lines, contains Plan/Execute/Verify/Context/lessons.md
- GEN-02: 4 skill SKILL.md files with YAML frontmatter and verb-phrase descriptions
- GEN-03: 2 agent files with non-empty `skills:` list in frontmatter
- GEN-04: settings.json valid JSON with `hooks.PostToolUse[0].hooks[0].exitCode == 2`
- GEN-05: First write of GLOBAL artifact is sentinel-wrapped; existing user content preserved on merge
- GEN-06: Idempotency tested independently for PROJECT artifacts, settings.json, and GLOBAL artifacts; user edits outside sentinel block survive re-run

### conftest.py additions

- `real_registry` fixture: TemplateRegistry backed by real `templates/` directory
- `web_plan` fixture: GenerationPlan from web.yaml profile via `environment_planner.plan()`

## Verification

- `uv run pytest tests/test_generator.py -v`: 16/16 passed
- `uv run pytest tests/ -v`: 89/89 passed (no regressions)
- `uv run ruff check claude_env/generator/generator.py tests/test_generator.py`: clean
- `uv run mypy claude_env/generator/generator.py`: clean

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `claude_env/generator/generator.py`: FOUND
- `tests/test_generator.py`: FOUND (16 test functions)
- `tests/conftest.py`: FOUND (real_registry + web_plan fixtures)
- Commit a8f9e9c (RED tests): FOUND
- Commit d0aa26e (GREEN implementation): FOUND
- `grep "has_sentinel" claude_env/generator/generator.py`: 0 matches — CORRECT
