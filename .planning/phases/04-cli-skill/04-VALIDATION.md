---
phase: 4
slug: cli-skill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 04-01 | 1 | CLI-01, CLI-02 | unit | `uv run pytest tests/test_cli.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 04-01 | 1 | CLI-03 | unit | `uv run pytest tests/test_cli.py -k "dry_run" -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 04-02 | 2 | CLI-04 | unit | `uv run pytest tests/test_skill.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cli.py` — stubs for CLI-01 (setup), CLI-02 (bootstrap), CLI-03 (dry-run)
- [ ] `tests/test_skill.py` — stubs for CLI-04 (SKILL.md installation and invocability)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `claude-env setup` wizard UX | CLI-01 | Interactive prompts require human | Run `claude-env setup` in terminal, verify it prompts for name/domain, completes without error |
| `/claude-env:bootstrap` in Claude Code | CLI-04 | Claude Code skill invocation requires live session | Open a project in Claude Code, type `/claude-env:bootstrap`, verify it runs and produces `.claude/` layer |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
