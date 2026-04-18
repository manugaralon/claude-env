---
phase: 02-pipeline
plan: "01"
subsystem: models
tags: [pydantic, anthropic, pipeline, fixtures, contracts]

requires:
  - phase: 01-foundation
    provides: DomainProfile model and TemplateRegistry patterns used as design reference

provides:
  - ProjectSpec Pydantic v2 model (extra=forbid) as pipeline input contract
  - GenerationPlan, Artifact, OutputLayer models as pipeline output contract
  - claude_env/pipeline package init (ready for component modules)
  - anthropic>=0.96 SDK installed and importable
  - YAML and Markdown test fixtures for InputNormalizer/DomainClassifier plans

affects: [02-02, 02-03, 02-04]

tech-stack:
  added: [anthropic>=0.96]
  patterns:
    - "StrEnum for OutputLayer (UP042-compliant) instead of (str, Enum)"
    - "extra=forbid on all Pydantic models to catch schema drift at validation time"
    - "Field(default_factory=list) for all list fields to avoid mutable default"

key-files:
  created:
    - claude_env/models/project_spec.py
    - claude_env/models/generation_plan.py
    - claude_env/pipeline/__init__.py
    - tests/fixtures/specs/simple_web.yaml
    - tests/fixtures/specs/cli_tool.yaml
    - tests/fixtures/specs/simple_web.md
    - tests/test_models.py
  modified:
    - pyproject.toml
    - uv.lock

key-decisions:
  - "OutputLayer uses StrEnum (not str+Enum) per ruff UP042 — cleaner, Python 3.11+ idiomatic"
  - "anthropic pinned to >=0.96 matching the version available in uv resolution (0.96.0)"

patterns-established:
  - "TDD RED-GREEN cycle: test commit before implementation commit"
  - "StrEnum for string enums across all future pipeline models"

requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]

duration: 2min
completed: 2026-04-18
---

# Phase 2 Plan 01: Data Contracts and Pipeline Package Summary

**ProjectSpec and GenerationPlan Pydantic v2 models with extra=forbid, anthropic SDK installed, and YAML/Markdown spec fixtures ready for pipeline plan 02**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-18T20:09:46Z
- **Completed:** 2026-04-18T20:11:52Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- ProjectSpec model with all optional fields defaulted (domain_hint="general", languages/tech_stack/constraints/known_skills=[])
- GenerationPlan + Artifact + OutputLayer (StrEnum) all with extra="forbid" — schema drift caught at validation time
- 9 passing tests covering defaults, round-trips, extra-field rejection, and enum values
- anthropic 0.96.0 installed; claude_env.pipeline importable; 3 fixture files ready for plan 02

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for models** - `f90aeaa` (test)
2. **Task 1 GREEN: ProjectSpec and GenerationPlan models** - `9cce2d2` (feat)
3. **Task 2: anthropic dep, pipeline package, spec fixtures** - `dcf216d` (feat)
4. **Deviation fix: StrEnum for OutputLayer** - `54ae826` (fix)

**Plan metadata:** (docs commit, see below)

_Note: TDD tasks have separate test and implementation commits_

## Files Created/Modified

- `claude_env/models/project_spec.py` - ProjectSpec Pydantic v2 model, input contract
- `claude_env/models/generation_plan.py` - GenerationPlan, Artifact, OutputLayer, output contract
- `claude_env/pipeline/__init__.py` - Empty pipeline package init
- `tests/test_models.py` - 9 tests covering all model behaviors
- `tests/fixtures/specs/simple_web.yaml` - habit-tracker web app spec fixture
- `tests/fixtures/specs/cli_tool.yaml` - file-organizer CLI tool spec fixture
- `tests/fixtures/specs/simple_web.md` - Markdown version of web spec fixture
- `pyproject.toml` - Added anthropic>=0.96 dependency
- `uv.lock` - Updated lock file with anthropic 0.96.0 and transitive deps

## Decisions Made

- **StrEnum for OutputLayer:** ruff UP042 flags `(str, Enum)` — switched to `StrEnum` (Python 3.11+, already required). Cleaner and idiomatic.
- **anthropic pinned to >=0.96:** matches available version (0.96.0) in uv resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff UP042: OutputLayer inheriting from both str and Enum**
- **Found during:** Task 2 verification (full verification suite)
- **Issue:** `class OutputLayer(str, Enum)` triggers ruff UP042 — should use `StrEnum`
- **Fix:** Changed inheritance to `StrEnum` and import to `from enum import StrEnum`
- **Files modified:** `claude_env/models/generation_plan.py`
- **Verification:** `uv run ruff check claude_env/models/ claude_env/pipeline/` exits 0; all 9 tests still pass
- **Committed in:** `54ae826` (separate fix commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - style/correctness)
**Impact on plan:** Necessary for ruff clean. No behavior change — StrEnum values are identical.

## Issues Encountered

None — tasks proceeded smoothly. The ruff UP042 flag was caught during the final verification sweep and fixed inline.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All pipeline data contracts locked: ProjectSpec (input), GenerationPlan/Artifact/OutputLayer (output)
- anthropic SDK ready for Plan 02 (InputNormalizer LLM calls)
- claude_env.pipeline package ready for component modules (02, 03, 04)
- Spec fixtures ready for InputNormalizer parsing tests (Plan 02)
- mypy strict and ruff clean on all new files

---
*Phase: 02-pipeline*
*Completed: 2026-04-18*
