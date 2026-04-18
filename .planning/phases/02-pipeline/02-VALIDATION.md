---
phase: 2
slug: pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 2 — Validation Strategy

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
| 2-01-01 | 01 | 1 | PIPE-01 | unit | `uv run pytest tests/test_input_normalizer.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | PIPE-01 | unit | `uv run pytest tests/test_input_normalizer.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | PIPE-02 | unit | `uv run pytest tests/test_domain_classifier.py -x -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 2 | PIPE-03 | unit | `uv run pytest tests/test_environment_planner.py -x -q` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 2 | PIPE-04 | integration | `uv run pytest tests/test_pipeline_integration.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_input_normalizer.py` — stubs for PIPE-01
- [ ] `tests/test_domain_classifier.py` — stubs for PIPE-02
- [ ] `tests/test_environment_planner.py` — stubs for PIPE-03
- [ ] `tests/test_pipeline_integration.py` — stubs for PIPE-04 (end-to-end pipeline flow)
- [ ] `tests/conftest.py` — shared fixtures (already exists, may need updates)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM normalizer quality | PIPE-01 | Claude output is non-deterministic; quality check on real API call | Run `uv run python -c "from claude_env.pipeline.input_normalizer import InputNormalizer; n=InputNormalizer(); print(n.normalize('a web app for tracking books'))"` and verify ProjectSpec has domain_hint populated |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
