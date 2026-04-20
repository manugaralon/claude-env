---
phase: "04-cli-skill"
plan: "02"
subsystem: cli
tags: [cli, skill, claude-code, setup]
dependency_graph:
  requires: [04-01]
  provides: [claude-env-bootstrap-skill]
  affects: [claude-code-slash-commands]
tech_stack:
  added: [pyyaml-for-tests]
  patterns: [fixed-string-constant, idempotent-file-write]
key_files:
  created: [tests/test_skill.py]
  modified: [claude_env/cli.py]
decisions:
  - "SKILL.md content is a Python string constant _SKILL_MD_CONTENT — not a Jinja template, no user-dependent fields"
  - "YAML >- folded scalar used for description to stay within 100-char line limit while keeping first word as verb"
  - "_install_bootstrap_skill() always overwrites — idempotency guaranteed by fixed content"
  - "Skill is installed from setup() only, not bootstrap() — it is global infrastructure"
metrics:
  duration: "~10 min"
  completed: "2026-04-20"
  tasks_completed: 2
  files_changed: 2
---

# Phase 4 Plan 2: SKILL.md Installation Summary

**One-liner:** `claude-env setup` now installs `~/.claude/skills/claude-env/bootstrap/SKILL.md` with valid YAML frontmatter (name: bootstrap, allowed-tools: Bash) and a body documenting `claude-env bootstrap` and `--dry-run`.

## What Was Built

- `_SKILL_MD_CONTENT` — module-level string constant in `cli.py` with YAML frontmatter + Markdown body
- `_install_bootstrap_skill(global_root: Path) -> Path` — writes SKILL.md, always overwrites, idempotent
- `setup()` — HOOK comment replaced with call to `_install_bootstrap_skill(Path.home() / ".claude")`
- `tests/test_skill.py` — 7 tests covering path, frontmatter validity, verb-phrase description, body content, idempotency, and non-disturbance of other skill files

## SKILL.md Location

`~/.claude/skills/claude-env/bootstrap/SKILL.md`

- Invocable via `/claude-env:bootstrap` in Claude Code
- Frontmatter: `name: bootstrap`, `allowed-tools: Bash`, verb-phrase description
- Body: instructs Claude to run `claude-env bootstrap` (with --spec and --dry-run variants)

## Deviations from Plan

**[Rule 1 - Bug] YAML block scalar for long description line**
- **Found during:** Task 2 (ruff E501 check)
- **Issue:** `description: <long string>` exceeded 100-char line limit inside Python string constant
- **Fix:** Used YAML `>-` folded scalar — description parses correctly, first word remains "Generate"
- **Files modified:** `claude_env/cli.py`
- **Commit:** `f8c853a`

## Self-Check: PASSED

- `claude_env/cli.py`: `_SKILL_MD_CONTENT` defined + used (2 matches), `_install_bootstrap_skill` at module level, called from `setup()`, HOOK comment removed
- `tests/test_skill.py`: 7 tests, all passing
- All commits present: `7559646` (test RED), `f8c853a` (feat GREEN)
- Full suite: 104 tests passed, mypy clean, ruff clean
