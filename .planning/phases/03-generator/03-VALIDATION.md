---
phase: 3
slug: generator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 3 — Validation Strategy

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
| 3-01-01 | 03-01 | 0 | GEN-01, GEN-02, GEN-03 | unit | `uv run pytest tests/test_content_catalogue.py -x -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 03-01 | 0 | GEN-04 | unit | `uv run pytest tests/test_generator.py -x -q` | ❌ W0 | ⬜ pending |
| 3-02-01 | 03-02 | 1 | GEN-01, GEN-02, GEN-03 | unit | `uv run pytest tests/test_generator.py -x -q` | ❌ W0 | ⬜ pending |
| 3-02-02 | 03-02 | 1 | GEN-04 | unit | `uv run pytest tests/test_generator.py -k "settings" -x -q` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03-03 | 2 | GEN-05, GEN-06 | unit | `uv run pytest tests/test_merge.py -x -q` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03-03 | 2 | GEN-05, GEN-06 | integration | `uv run pytest tests/test_generator.py -k "rerun or idempotent" -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_content_catalogue.py` — stubs for GEN-01, GEN-02, GEN-03 (context enrichment)
- [ ] `tests/test_generator.py` — stubs for GEN-04 (file writing), GEN-05, GEN-06 (sentinel merge)
- [ ] `tests/test_merge.py` — stubs for GEN-05, GEN-06 (sentinel merge logic)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Generated CLAUDE.md quality | GEN-01 | Content quality is subjective | Run generator on a sample spec, read output `.claude/CLAUDE.md`, verify plan→execute→verify pattern and lessons.md loop are present and meaningful |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
