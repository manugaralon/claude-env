# Phase 7: Augment Mode — Specification

**Created:** 2026-06-09
**Ambiguity score:** 0.13 (gate: ≤ 0.20)
**Requirements:** 5 locked

## Goal

`claude-env bootstrap` becomes **safe to run on a project that already has history/bespoke files** — it never clobbers human-authored content. Generated content is applied via per-artifact write strategies (sentinel-managed block / write-once / skip-if-exists / overwrite), so the same command works on greenfield AND mature projects. This is the cross-project "apply to existing repos" path (the 90% case for a solo dev with live projects).

## Background

Today the generator dispatches its write strategy on `artifact.layer` (`generator/generator.py`): GLOBAL → sentinel wrap/merge; PROJECT / PROJECT_ROOT → plain overwrite (plus the `write_once` skip added in Phase 6). That makes `bootstrap` **unsafe on existing projects**: it would overwrite a hand-edited `.claude/CONTEXT.md` or skill, and — worse — write a second `.claude/CLAUDE.md` alongside a bespoke root `./CLAUDE.md` (two files, undefined precedence). The sentinel helpers (`generator/sentinel.py`: `wrap_with_sentinel`, `has_sentinel`, `merge_sentinel_block`) are already **pure string functions over arbitrary content** — not coupled to the GLOBAL layer; the coupling is only in the generator's dispatch. So augment-mode is a small, surgical change, not a new engine. Motivated by Agus/Clibit (mature, bespoke root CLAUDE.md + heavy GSD). This SPEC was produced under claude-env's own constitution gate (P1–P7); P4 (idempotent/non-destructive) is the feature itself.

## Requirements

1. **Per-artifact merge strategy**: write strategy is explicit metadata, not inferred from layer.
   - Current: generator branches on `artifact.layer` (+ the `write_once` bool).
   - Target: add a `MergeStrategy` enum (`overwrite | sentinel | write_once | skip_if_exists`) and a `merge_strategy` field on `Artifact`; the generator dispatches on it. Preserves the Phase-3 invariant "strategy from metadata, never from file content".
   - Acceptance: all existing tests pass unchanged; current artifacts keep identical behavior (GLOBAL→sentinel, PROJECT/PROJECT_ROOT→overwrite, constitution→write_once) whether mapped from layer for back-compat or set explicitly.

2. **Non-destructive CLAUDE.md augment**: never create a second CLAUDE.md; merge a managed block into the existing one.
   - Current: the CLAUDE.md artifact writes `.claude/CLAUDE.md` via plain overwrite.
   - Target: when a CLAUDE.md already exists, resolve the target to it (precedence: root `./CLAUDE.md`, then `.claude/CLAUDE.md`) and sentinel-merge a managed block; if none exists, write `.claude/CLAUDE.md` fresh (sentinel-wrapped). All content outside the managed block is byte-preserved.
   - Acceptance: augment on a project with a bespoke `./CLAUDE.md` leaves every non-managed line byte-identical, adds/updates only the managed block, and creates NO second CLAUDE.md.

3. **Skip-if-exists for bespoke artifacts**: don't clobber user-authored files.
   - Current: PROJECT artifacts (`CONTEXT.md`, `skills/`, `agents/`) plain-overwrite.
   - Target: artifacts likely hand-edited (CONTEXT.md, skills, agents) use `skip_if_exists` — create only when absent, leave existing untouched.
   - Acceptance: augment over an existing `CONTEXT.md` or skill leaves it byte-identical; absent ones are created.

4. **Dry-run shows the real augment delta**: per-artifact action against actual target state, writing nothing.
   - Current: `--dry-run` lists files that would be written.
   - Target: `--dry-run` reports, per artifact, the resolved action (`create` / `merge-managed-block` / `skip-exists` / `overwrite`) computed against the target's current existence, and writes zero bytes.
   - Acceptance: `--dry-run` on a project with mixed existing/absent targets prints the correct action per artifact and writes nothing.

5. **Safe by default on existing projects**: `bootstrap` with no flags never alters human content.
   - Current: bootstrap overwrites PROJECT artifacts — unsafe on mature repos.
   - Target: with the strategies above, plain `bootstrap` on an existing project only updates managed blocks and creates absent files.
   - Acceptance: `bootstrap` (no flags) on a copy of a mature project (bespoke CLAUDE.md + CONTEXT.md + a skill) changes only managed blocks + creates only absent files; `git diff` shows no human-authored content altered.

## Boundaries

**In scope:**
- `MergeStrategy` enum + `merge_strategy` field on `Artifact`; generator dispatch on strategy.
- CLAUDE.md existing-target detection (root vs `.claude/`) + sentinel-merge of a managed block.
- `skip_if_exists` for CONTEXT.md / skills / agents.
- `--dry-run` per-artifact action reporting against real target state.
- Back-compat: current behavior + all existing tests preserved.

**Out of scope:**
- A separate `augment` command — `bootstrap` handles both greenfield and existing (P6 simplicity; one entry point).
- A sync engine across repos — explicitly rejected (advisor); idempotent managed-block merge IS the "re-run to refresh".
- Auto-editing / migrating bespoke human content; interactive conflict-resolution UI.
- Touching GSD's own files, or anything outside the env layer.

## Constraints

Bound by claude-env's `.planning/CONSTITUTION.md` (SPEC produced under its gate):
- **P4** — idempotent, non-destructive: the defining property; never clobber human content.
- **P6** — simplicity / surgical: reuse the existing path-agnostic sentinel helpers; add one enum + one field + a dispatch change; no new command, no new engine.
- **P1** — two layers respected; CLAUDE.md target resolution must not blur project vs global.
- **P3** — any managed block injected into a CLAUDE.md must respect the ≤200-line spirit (managed content stays tight).
- Phase-3 invariant: write strategy from artifact metadata, never from file content.
- Backward compatibility: the existing 167 tests pass unchanged.

## Acceptance Criteria

- [x] `Artifact` has a `merge_strategy` field; the generator dispatches on it; all existing tests pass unchanged.
- [x] On a project with a bespoke `./CLAUDE.md`, augment injects a managed block into it (no second CLAUDE.md); non-managed lines are byte-identical.
- [x] An existing `CONSTITUTION.md` is never overwritten (write_once preserved); existing `CONTEXT.md` / skills are skipped, not clobbered.
- [x] `--dry-run` reports the correct per-artifact action against real target state and writes zero bytes.
- [x] `bootstrap` with no flags on a mature-project copy alters zero human-authored content (only managed blocks + absent files).

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                                                    |
|--------------------|-------|------|--------|----------------------------------------------------------|
| Goal Clarity       | 0.88  | 0.75 | ✓      | "bootstrap safe on existing repos via per-artifact strategy" |
| Boundary Clarity   | 0.92  | 0.70 | ✓      | Explicit out-of-scope (no new cmd, no sync engine)       |
| Constraint Clarity | 0.90  | 0.65 | ✓      | Constitution P1/P3/P4/P6 + Phase-3 invariant + back-compat |
| Acceptance Criteria| 0.85  | 0.70 | ✓      | 5 falsifiable checkboxes                                  |
| **Ambiguity**      | 0.13  | ≤0.20| ✓      | Gate passed (architecture de-risked by council/advisor)  |

Status: ✓ = met minimum, ⚠ = below minimum (planner treats as assumption)

## Interview Log

Interview auto-resolved per user delegation ("decide tú"); decisions grounded in the council+advisor deliberation (this session), the de-risked ROADMAP design, and claude-env's CONSTITUTION.md (the live gate fired during this spec — P4 is the feature).

| Round | Perspective     | Question summary                              | Decision locked                                                      |
|-------|-----------------|-----------------------------------------------|---------------------------------------------------------------------|
| 1     | Researcher      | How is write strategy chosen today?           | Generator dispatches on `layer` + `write_once`; sentinel helpers are already path-agnostic |
| 2     | Simplifier      | Minimum viable augment?                        | One `MergeStrategy` enum + field + dispatch change; reuse sentinel; NO new command |
| 3     | Boundary Keeper | New `augment` command or extend `bootstrap`?   | Extend bootstrap — safe-by-default via per-artifact strategy (P6)    |
| 3     | Boundary Keeper | CLAUDE.md: 2nd file or merge into existing?     | Merge a managed block into the existing CLAUDE.md (root preferred); NEVER a 2nd file |
| 4     | Constitution    | Does the SPEC comply with CONSTITUTION.md?      | Yes — P4 (non-destructive) is the feature; P6 (reuse sentinel); back-compat preserved |

---

*Phase: 07-augment-mode*
*Spec created: 2026-06-09*
*Next step: /gsd-discuss-phase 7 — implementation decisions (MergeStrategy mapping, CLAUDE.md target resolution, dry-run reporting format)*
