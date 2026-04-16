---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ && uv run ruff check . && uv run mypy src/` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ && uv run ruff check . && uv run mypy src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | INFRA | unit | `uv sync && uv run python -c "import claude_env"` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA | lint | `uv run ruff check . && uv run mypy src/` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | DOMAIN | unit | `uv run pytest tests/test_domain_profiles.py -x -q` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | REGISTRY | unit | `uv run pytest tests/test_template_registry.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — empty, marks tests as package
- [ ] `tests/test_domain_profiles.py` — stubs for profile load/schema-valid tests
- [ ] `tests/test_template_registry.py` — stubs for registry resolve/render tests
- [ ] `tests/conftest.py` — shared fixtures (tmp_path, sample yaml data)

*Wave 0 creates the test stubs before production code is written.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `uv sync` installs cleanly on fresh venv | INFRA | Requires clean environment | `rm -rf .venv && uv sync` in fresh shell, verify no errors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
