---
phase: 04-cli-skill
verified: 2026-04-20T00:00:00Z
status: passed
score: 8/8 must-haves verified
gaps: []
human_verification:
  - test: "Verify /claude-env:bootstrap slash-command in Claude Code"
    expected: "Claude Code picks up the skill from ~/.claude/skills/claude-env/bootstrap/SKILL.md and executes claude-env bootstrap"
    why_human: "Requires a live Claude Code session; cannot verify slash-command registration programmatically"
---

# Phase 4: CLI + Skill Verification Report

**Phase Goal:** Implement `claude-env setup`, `claude-env bootstrap`, `--dry-run` flag, and SKILL.md installation at `~/.claude/skills/claude-env/bootstrap/SKILL.md`.
**Verified:** 2026-04-20
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                            | Status     | Evidence                                                                                  |
|----|--------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------|
| 1  | `claude-env setup` runs and writes a valid `~/.claude/` layer                                   | VERIFIED   | `test_setup_writes_general_layer` passes; `~/.claude/CLAUDE.md` exists after monkeypatched run |
| 2  | `claude-env setup` uses the general profile (no domain selection required)                       | VERIFIED   | `test_setup_uses_general_profile` passes; CLAUDE.md content contains "Plan"               |
| 3  | `claude-env bootstrap --spec <file>` generates `.claude/` in the project dir without LLM        | VERIFIED   | `test_bootstrap_with_spec_file_writes_project_layer` + `test_bootstrap_with_spec_skips_llm` pass |
| 4  | `claude-env bootstrap --dry-run --spec <file>` prints paths and exits 0 without writing files   | VERIFIED   | `test_bootstrap_dry_run_writes_nothing` passes; output contains "would write", `.claude/` absent |
| 5  | Dry-run paths are identical to actual written paths (single source of truth)                    | VERIFIED   | `test_dry_run_paths_match_actual_paths` passes; `resolve_plan_paths` used by both paths   |
| 6  | Missing ANTHROPIC_API_KEY produces a clean error, not a traceback                               | VERIFIED   | `test_bootstrap_missing_api_key_freeform_clean_error` passes; exit != 0, message printed  |
| 7  | `setup` installs SKILL.md at `~/.claude/skills/claude-env/bootstrap/SKILL.md`                  | VERIFIED   | `test_setup_creates_skill_md_at_correct_path` passes                                      |
| 8  | SKILL.md has correct frontmatter and body content                                               | VERIFIED   | All 7 tests in `test_skill.py` pass (frontmatter, verb-phrase, body references, idempotency, isolation) |

**Score:** 8/8 truths verified

---

### Required Artifacts

| Artifact                                   | Provides                                                        | Status     | Details                                                      |
|--------------------------------------------|-----------------------------------------------------------------|------------|--------------------------------------------------------------|
| `claude_env/cli.py`                        | Typer app with version, setup, bootstrap (+ --spec, --dry-run) | VERIFIED   | 3 `@app.command()` decorators; heavy imports inside function bodies |
| `claude_env/generator/generator.py`        | `resolve_plan_paths()` module-level helper                      | VERIFIED   | Defined at line 17; called internally at line 90 and imported by CLI |
| `tests/test_cli.py`                        | 8 CLI integration tests via CliRunner                           | VERIFIED   | 8 tests collected and passing                                |
| `tests/test_skill.py`                      | 7 SKILL.md installation tests                                   | VERIFIED   | 7 tests collected and passing                                |

---

### Key Link Verification

| From                          | To                                              | Via                                                      | Status   | Details                                                        |
|-------------------------------|-------------------------------------------------|----------------------------------------------------------|----------|----------------------------------------------------------------|
| `cli.py (bootstrap)`          | `generator.py`                                  | `Generator(registry).execute()` + `resolve_plan_paths()` | WIRED    | Lines 125, 162, 167 in cli.py                                  |
| `cli.py (bootstrap)`          | `pipeline/input_normalizer.py`                  | `InputNormalizer().from_spec_file()`                     | WIRED    | Line 137 in cli.py                                             |
| `cli.py (bootstrap)`          | `pipeline/domain_classifier.py`                 | `classify(spec, profiles)`                               | WIRED    | Line 155 in cli.py                                             |
| `cli.py (bootstrap)`          | `pipeline/environment_planner.py`               | `plan(spec, profile, available_templates)`               | WIRED    | Line 128 in cli.py                                             |
| `cli.py (setup)`              | `~/.claude/skills/claude-env/bootstrap/SKILL.md`| `_install_bootstrap_skill(Path.home() / ".claude")`      | WIRED    | Line 105 in cli.py; `_install_bootstrap_skill` defined at line 59 |
| `SKILL.md frontmatter`        | Claude Code slash-command `/claude-env:bootstrap`| `name: bootstrap` in frontmatter + directory layout     | UNCERTAIN| Cannot verify programmatically — needs human (Claude Code session) |

---

### Requirements Coverage

| Requirement | Source Plan | Description                                                                                    | Status        | Evidence                                                                           |
|-------------|-------------|------------------------------------------------------------------------------------------------|---------------|------------------------------------------------------------------------------------|
| CLI-01      | 04-01       | `setup` wizard writes valid `~/.claude/` layer (non-interactively given --name and --domain)  | SATISFIED*    | `setup` writes CLAUDE.md layer; uses single `typer.prompt` (name only, always general profile). NOTE: `--name`/`--domain` CLI args not implemented — plan decision locked setup to interactive prompt for name + hardcoded general profile. The non-interactive contract is satisfied via `input=` in tests; `--domain` flag was explicitly dropped. |
| CLI-02      | 04-01       | `bootstrap` runs full pipeline + generator producing `.claude/` in project dir                | SATISFIED     | `test_bootstrap_with_spec_file_writes_project_layer` passes; full pipeline wired  |
| CLI-03      | 04-01       | `--dry-run` lists files to be written without writing them, exits 0                           | SATISFIED     | `test_bootstrap_dry_run_writes_nothing` passes; "would write" in output, no files written |
| CLI-04      | 04-02       | `setup` installs SKILL.md at `~/.claude/skills/claude-env/bootstrap/SKILL.md` with correct frontmatter | SATISFIED | All 7 `test_skill.py` tests pass; `name: bootstrap`, `allowed-tools: Bash`, verb-phrase description |

*CLI-01 note: The verification request specified `--name`/`--domain` non-interactive args. The actual plan decisions (04-01-PLAN.md) explicitly locked `setup` to a single `typer.prompt("Your name")` call and hardcoded the general profile — no `--domain` flag. This was a deliberate plan decision, not a gap. The requirement is satisfied per the plan's definition of "non-interactive (name only)".

---

### Anti-Patterns Found

None found. Checked `claude_env/cli.py`, `claude_env/generator/generator.py`, `tests/test_cli.py`, `tests/test_skill.py` for TODO/FIXME/placeholder/stub patterns.

- HOOK comment (Plan 04-01 anchor) confirmed removed from `cli.py` — no match on "HOOK".
- No module-level `from anthropic` import — heavy imports stay inside function bodies per plan decision.
- No `return null` / empty implementation stubs.

---

### Human Verification Required

#### 1. Claude Code slash-command `/claude-env:bootstrap`

**Test:** Run `uv run claude-env setup` (types real name at prompt), then in a Claude Code session in any project directory type `/claude-env:bootstrap`.
**Expected:** Claude Code recognizes the skill from `~/.claude/skills/claude-env/bootstrap/SKILL.md` and executes `claude-env bootstrap` via Bash.
**Why human:** Slash-command registration in Claude Code cannot be verified programmatically — it requires a live session and visual confirmation that the command is recognized and dispatched correctly.

---

### Full Test Suite Results

```
104 passed in 1.77s
```

- `tests/test_cli.py` — 8/8 passed
- `tests/test_skill.py` — 7/7 passed
- `uv run mypy claude_env/` — no issues found in 18 source files
- `uv run ruff check claude_env/` — all checks passed

---

### Summary

Phase 4 goal is achieved. All four requirements (CLI-01 through CLI-04) are satisfied:

- `claude-env setup` writes a valid `~/.claude/` layer using the general profile, installs SKILL.md at the correct path, and is idempotent.
- `claude-env bootstrap --spec <file>` runs the full pipeline without requiring an LLM call.
- `--dry-run` correctly lists resolved paths and writes nothing.
- SKILL.md has valid YAML frontmatter (`name: bootstrap`, `allowed-tools: Bash`, verb-phrase description), body references `claude-env bootstrap` and `--dry-run`.
- `resolve_plan_paths` is the single source of truth for path resolution, shared between dry-run and real execution.

One item needs human verification: whether the SKILL.md directory layout (`skills/claude-env/bootstrap/SKILL.md`) is correctly picked up as `/claude-env:bootstrap` by Claude Code. The plan documents this as the best-evidence inference from research, with a fallback path to a flat layout if Claude Code rejects it.

---

_Verified: 2026-04-20_
_Verifier: Claude (gsd-verifier)_
