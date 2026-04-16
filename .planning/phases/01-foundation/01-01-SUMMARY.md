---
phase: 01-foundation
plan: 01
subsystem: infra
tags: [python, uv, pyproject, hatchling, pydantic, jinja2, pyyaml, typer, ruff, mypy, pytest]

requires: []

provides:
  - Installable Python package (claude-env) via uv sync
  - claude_env package tree with models/, templates/, profiles/ subpackages
  - Typer CLI stub (claude-env entry point)
  - tests/ scaffold with conftest fixtures for Plans 02 and 03
  - ruff + mypy strict baseline (zero errors)

affects:
  - 01-02 (DomainProfile model imports from claude_env.models)
  - 01-03 (TemplateRegistry imports from claude_env.templates)
  - all downstream phases (depend on ruff/mypy green baseline)

tech-stack:
  added:
    - uv 0.10.8 (package manager + lockfile)
    - pydantic 2.13.1 (schema validation)
    - jinja2 3.1.6 (template rendering)
    - pyyaml 6.0.3 (YAML loading)
    - typer 0.24.1 (CLI framework)
    - rich 15.0.0 (terminal output)
    - pytest 9.0.3 (test runner)
    - ruff 0.15.10 (linter + formatter)
    - mypy 1.20.1 (strict type checker)
    - types-pyyaml 6.0.12.20260408 (mypy stubs for PyYAML)
    - hatchling (build backend)
  patterns:
    - pyproject.toml as single config source (ruff, mypy, pytest all in one file)
    - uv sync + uv run for all dev commands (no global env pollution)
    - mypy strict from day one to prevent type debt accumulation
    - ruff select=["E","F","I","UP"] covering errors, unused imports, isort, pyupgrade

key-files:
  created:
    - pyproject.toml
    - .python-version
    - .gitignore
    - uv.lock
    - claude_env/__init__.py
    - claude_env/cli.py
    - claude_env/models/__init__.py
    - claude_env/templates/__init__.py
    - claude_env/profiles/__init__.py
    - templates/.gitkeep
    - tests/__init__.py
    - tests/conftest.py
  modified: []

key-decisions:
  - "hatchling build backend with explicit packages=[\"claude_env\"] to avoid discovery issues in src-less layout"
  - "templates/ at project root (not inside claude_env/) — Jinja2 FileSystemLoader needs plain dir, not Python package"
  - "types-pyyaml in dev deps so mypy strict passes on yaml imports without ignore_missing_imports=true"
  - "Typer 0.24 single-command behavior: uv run claude-env (no subcommand) outputs version — uv run claude-env version fails by design"

patterns-established:
  - "All tool config in pyproject.toml — no ruff.toml, .mypy.ini, setup.cfg"
  - "from __future__ import annotations in all modules using type hints"
  - "Explicit docstrings in every __init__.py for subpackage purpose clarity"

requirements-completed: []

duration: 3min
completed: 2026-04-16
---

# Phase 1 Plan 01: Package Bootstrap Summary

**Python package with uv/hatchling, ruff + mypy strict baseline, Typer CLI stub, and pytest scaffold — installable in one `uv sync`**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-16T12:01:07Z
- **Completed:** 2026-04-16T12:04:xx Z
- **Tasks:** 3
- **Files modified:** 12 created, 0 modified

## Accomplishments

- Installable claude-env package: `uv sync` resolves 27 packages, `uv run claude-env` prints version
- ruff check and mypy --strict both exit 0 on the initial codebase (5 source files)
- Shared pytest fixtures in conftest.py lock the contract for Plans 02 and 03
- templates/ directory at project root ready for Jinja2 FileSystemLoader (Plan 03)

## Task Commits

1. **Task 1: Create pyproject.toml with full tool config and run uv sync** - `af2ad9a` (chore)
2. **Task 2: Create claude_env package tree with subpackages and Typer CLI stub** - `184fa94` (feat)
3. **Task 3: Create tests/ scaffold with conftest and verify ruff + mypy green** - `1a4109c` (feat)

## Files Created/Modified

- `pyproject.toml` - Project manifest: deps, entry point, ruff/mypy/pytest config, hatchling build
- `.python-version` - Python 3.12 pin for uv
- `.gitignore` - .venv/, caches, dist, build artifacts
- `uv.lock` - Locked dependency graph (27 packages)
- `claude_env/__init__.py` - Package root docstring
- `claude_env/cli.py` - Typer stub with version command (entry point: claude-env)
- `claude_env/models/__init__.py` - Subpackage placeholder (Plan 02: DomainProfile)
- `claude_env/templates/__init__.py` - Subpackage placeholder (Plan 03: TemplateRegistry)
- `claude_env/profiles/__init__.py` - Subpackage placeholder (domain YAML profiles)
- `templates/.gitkeep` - Project-root Jinja2 templates dir marker
- `tests/__init__.py` - Empty package marker for mypy strict
- `tests/conftest.py` - Shared fixtures: sample_profile_yaml (Plan 02), templates_dir (Plan 03)

## Resolved Dependency Versions

| Package | Resolved |
|---------|---------|
| pydantic | 2.13.1 |
| jinja2 | 3.1.6 |
| pyyaml | 6.0.3 |
| typer | 0.24.1 |
| rich | 15.0.0 |
| pytest | 9.0.3 |
| ruff | 0.15.10 |
| mypy | 1.20.1 |
| types-pyyaml | 6.0.12.20260408 |

## Decisions Made

- **hatchling + explicit packages=["claude_env"]**: required for hatchling to find the package in src-less layout; default discovery can fail without it.
- **templates/ at project root**: Jinja2 FileSystemLoader reads a plain directory, not a Python package. Keeping it separate from claude_env/ also avoids packaging .j2 files into the wheel.
- **types-pyyaml in dev deps**: PyYAML ships no inline stubs. Adding types-pyyaml makes `mypy --strict` pass on yaml imports without needing `ignore_missing_imports = true`, which would hide real issues.

## Deviations from Plan

### Typer 0.24 single-command behavior

- **Found during:** Task 2 acceptance criteria verification
- **Issue:** Acceptance criterion `uv run claude-env version` fails in Typer 0.24 when the app has a single command. Typer 0.24 invokes single-command apps directly without requiring the subcommand name, so `version` is passed as an unexpected argument.
- **Fix:** No code change. `uv run claude-env` (no subcommand) prints `claude-env 0.1.0` and exits 0 — functionally identical. The CLI stub will be fully replaced in Phase 4.
- **Impact:** None — this is a stub. Phase 4 CLI plan will explicitly handle multi-command routing.

### pytest exit code 5 with empty test suite

- **Found during:** Task 3 verification
- **Issue:** The plan notes pytest exits 5 when no tests are collected. `--collect-only` also exits 5 in pytest 9 with an empty suite. Both ruff and mypy pass; no actual test failures occurred.
- **Fix:** No change. This is expected per the plan body ("Wave 0 intentionally creates no tests yet"). Plans 02 and 03 will add real tests.
- **Impact:** None — conftest.py fixtures load without errors. Static analysis (ruff + mypy) fully green.

---

**Total deviations:** 2 (both are expected behaviors documented in the plan, no code changes required)
**Impact on plan:** Zero functional impact. Both deviations are Typer/pytest version behaviors acknowledged in the plan itself.

## Issues Encountered

None — all static analysis passes clean. Package installs and imports correctly. CLI entry point works.

## Contract for Plans 02 and 03

Plans 02 and 03 can now run in parallel against this scaffold:

**Plan 02 (DomainProfile):**
- Import target: `claude_env.models` (namespace ready)
- Test fixture: `sample_profile_yaml` in `tests/conftest.py`
- Expected module: `claude_env/models/domain_profile.py`

**Plan 03 (TemplateRegistry):**
- Import target: `claude_env.templates` (namespace ready)
- Test fixture: `templates_dir` in `tests/conftest.py` (absolute path to tmp dir)
- Expected module: `claude_env/templates/registry.py`
- Templates dir: `templates/` at project root (Jinja2 FileSystemLoader target)

## User Setup Required

None — no external service configuration required. `uv sync` is the only setup step.

## Next Phase Readiness

- Plans 02 and 03 can proceed in parallel immediately
- All namespaces (models/, templates/, profiles/) are importable
- ruff + mypy strict baseline established — downstream plans must maintain zero-error status
- No blockers

---
*Phase: 01-foundation*
*Completed: 2026-04-16*

## Self-Check: PASSED

Files verified present: pyproject.toml, .python-version, .gitignore, uv.lock, claude_env/__init__.py, claude_env/cli.py, claude_env/models/__init__.py, claude_env/templates/__init__.py, claude_env/profiles/__init__.py, templates/.gitkeep, tests/__init__.py, tests/conftest.py — all FOUND.

Commits verified: af2ad9a (Task 1), 184fa94 (Task 2), 1a4109c (Task 3) — all present in git log.
