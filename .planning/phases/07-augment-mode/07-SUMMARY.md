# Phase 7: Augment Mode — Summary

**Shipped:** 2026-07-12
**Status:** ✅ Complete — all 5 acceptance criteria met.

## What was built

`claude-env bootstrap` is now safe to run on a project that already has
history/bespoke files. The write strategy is explicit per-artifact metadata and
the generator dispatches on it, so one command serves greenfield AND mature
projects without ever clobbering hand-authored content.

### 1. `MergeStrategy` enum + `merge_strategy` field (models)
- Added `MergeStrategy(StrEnum)` = `overwrite | sentinel | write_once | skip_if_exists`.
- Added `merge_strategy: MergeStrategy | None = None` on `Artifact`. `write_once`
  is retained for back-compat (equivalent to `WRITE_ONCE`).

### 2. Strategy dispatch (generator)
- `effective_merge_strategy(artifact)` resolves the strategy: explicit
  `merge_strategy` wins; when unset it maps from `layer`/`write_once`
  (`GLOBAL → sentinel`, `write_once → write_once`, else `overwrite`) — so every
  pre-Phase-7 artifact keeps byte-identical behavior. Preserves the Phase-3
  invariant (strategy from metadata, never file content).
- `resolve_plan()` is the single source of truth: returns a `ResolvedArtifact`
  (artifact + absolute target + action) per artifact against the real
  filesystem. `resolve_plan_paths()` kept as a thin wrapper.
- `Generator.execute()` dispatches on the resolved strategy; skip-exists
  artifacts short-circuit before any render/merge.

### 3. Non-destructive CLAUDE.md target resolution
- A `sentinel`-strategy CLAUDE.md merges its managed block into a project's
  EXISTING CLAUDE.md — precedence: root `./CLAUDE.md`, then `.claude/CLAUDE.md`.
  Never a second file. Greenfield → fresh sentinel-wrapped `.claude/CLAUDE.md`.
  Reuses the path-agnostic `sentinel.py` helpers unchanged.

### 4. skip_if_exists for bespoke artifacts (planner)
- `CONTEXT.md`, `docs/adr/README.md`, `skills/*`, `agents/*` → `skip_if_exists`
  (create only when absent). `CLAUDE.md` → `sentinel`. `CONSTITUTION.md` stays
  `write_once`. `settings.json` / `.mcp.json` / marker stay `overwrite`
  (generated machine config).

### 5. `--dry-run` per-artifact action reporting (cli)
- Reports the resolved action (`create` / `merge-managed-block` / `skip-exists`
  / `overwrite`) against real target state; writes zero bytes. Keeps the
  `would write` wording for non-skip lines (existing contract).

### 6. Auditor tolerance (necessary corollary)
- `_check_claude_md_line_count` no longer flags `CLAUDE_MD_MISSING` when the
  managed block lives in a bespoke root `./CLAUDE.md` (only when
  `.claude/CLAUDE.md` is absent). Additive — the branch is dead code for every
  pre-existing test (none create a root CLAUDE.md), so all prior audit tests are
  unchanged. Without this, plain `bootstrap` on a mature repo would exit 1 on
  the audit, undermining the feature.

## Files touched

| File | Change |
|------|--------|
| `claude_env/models/generation_plan.py` | `MergeStrategy` enum + `merge_strategy` field |
| `claude_env/generator/generator.py` | strategy dispatch, `resolve_plan`/`ResolvedArtifact`, `effective_merge_strategy`, CLAUDE.md target resolution, action computation |
| `claude_env/pipeline/environment_planner.py` | explicit strategies per artifact |
| `claude_env/cli.py` | `--dry-run` action reporting via `resolve_plan` |
| `claude_env/auditor.py` | bespoke-root CLAUDE.md tolerance |
| `tests/test_augment.py` | 16 new tests across the 5 acceptance criteria |
| `.planning/ROADMAP.md`, `07-SPEC.md` | status + checkboxes |

## Tests

- **Before:** 156 passed, 1 skipped.
- **After:** 172 passed, 1 skipped (all 156 prior pass **unchanged** + 16 new).
- New coverage: back-compat strategy mapping, strategy-not-layer dispatch,
  CLAUDE.md merge into bespoke root / `.claude` / greenfield, root-over-`.claude`
  precedence, no-second-file, idempotent re-merge, skip_if_exists byte-preservation
  (CONTEXT.md + skill), write_once constitution, `resolve_plan` action reporting +
  zero-write, CLI dry-run actions + zero-write, and the AC5 capstone
  (mature-project `bootstrap` alters zero human bytes, exit 0).

## Constitution compliance

- **P4** (idempotent/non-destructive) — the feature itself; managed-block merge
  + skip_if_exists + write_once guarantee no human content is clobbered.
- **P6** (simplicity/surgical) — one enum + one field + a dispatch change +
  CLAUDE.md target resolution; reuses existing `sentinel.py`; **no new command,
  no sync engine**.
- **P1** (two layers) — CLAUDE.md resolution stays project-side; global setup
  unaffected in the tested paths.
- **P3** — the injected managed block is the template-bounded 104-line body
  (< 200), well within the cap.
- **Phase-3 invariant** — write strategy is artifact metadata, never file content.

## Deviations from the SPEC

1. **Auditor change (not in SPEC scope list).** The SPEC's in-scope list did not
   mention the auditor, but the generator can now legitimately produce a state
   (managed block in a root `./CLAUDE.md`, no `.claude/CLAUDE.md`) that the
   auditor previously hard-failed. The tolerance is a minimal, additive
   corollary required for plain `bootstrap` on a mature project (AC5) to exit
   clean. It touches nothing outside claude-env's own env layer.
2. **`docs/adr/README.md` → `skip_if_exists`.** The SPEC enumerated CONTEXT.md /
   skills / agents for skip_if_exists; the ADR scaffold README is treated the
   same way (a mature repo may maintain its own ADRs) — same non-destructive
   intent, no behavior change on greenfield.

No other deviations. Out-of-scope items (separate `augment` command, cross-repo
sync engine, auto-editing bespoke content, interactive conflict UI) were not
built.
