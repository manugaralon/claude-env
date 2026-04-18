---
phase: 02-pipeline
plan: 03
subsystem: pipeline
tags: [classifier, signal-matching, generation-plan, pydantic, tdd]

# Dependency graph
requires:
  - phase: 02-pipeline/02-01
    provides: Data contract models (DomainProfile, ProjectSpec, GenerationPlan, Artifact, OutputLayer)
  - phase: 01-foundation
    provides: DomainProfile YAML files (web, cli, data, infra, general) and TemplateRegistry

provides:
  - classify() function: assigns best-matching DomainProfile to ProjectSpec via signal scoring
  - load_all_profiles() function: loads all .yaml profiles from a directory
  - plan() function: transforms ProjectSpec+DomainProfile into GenerationPlan with typed Artifacts
  - 13 passing tests covering all classifier and planner behaviors

affects: [02-04, 03-generator, phase 3 generator integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure function pipeline stages — no I/O, no LLM, fully unit-testable with fixtures"
    - "TDD: RED commit (failing tests), then GREEN commit (implementation)"
    - "Inline DomainProfile construction for unit test fixtures — no disk I/O in tests"
    - "Template ID validation at plan() time, not at generation time"

key-files:
  created:
    - claude_env/pipeline/domain_classifier.py
    - claude_env/pipeline/environment_planner.py
    - tests/test_domain_classifier.py
    - tests/test_environment_planner.py
  modified: []

key-decisions:
  - "Signal matching uses tech_stack+languages token set (case-insensitive) against detection_signals — real profiles use file path signals, tests use named tech signals via fixture profiles"
  - "Template ID validation occurs inside plan() before returning GenerationPlan, not deferred to generator phase"
  - "All Artifacts assigned layer=PROJECT — global layer assignment is a Phase 3 generator concern"

patterns-established:
  - "classify() scores profiles by signal count, ties broken by sort order, falls back to general on zero-match"
  - "plan() builds CLAUDE.md + N skill + M agent artifacts from profile.skill_slugs / profile.agent_slugs"

requirements-completed: [PIPE-03, PIPE-04]

# Metrics
duration: 2min
completed: 2026-04-18
---

# Phase 02 Plan 03: Domain Classifier and Environment Planner Summary

**Signal-matching DomainClassifier and pure-data EnvironmentPlanner producing typed GenerationPlan with template validation**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-18T20:34:06Z
- **Completed:** 2026-04-18T20:36:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- DomainClassifier with case-insensitive signal scoring, general fallback, and ValueError on missing fallback
- EnvironmentPlanner producing Artifact entries for CLAUDE.md, N skills, and M agents — all layer=PROJECT
- Template ID validation at plan-time (not deferred to generator)
- 13 tests passing with inline fixtures — no disk I/O in unit tests; real profile integration tests in both modules

## Task Commits

1. **Task 1 RED: Failing tests for DomainClassifier** - `ed036e6` (test)
2. **Task 1 GREEN: Implement DomainClassifier** - `124713e` (feat)
3. **Task 2 RED: Failing tests for EnvironmentPlanner** - `cb69e55` (test)
4. **Task 2 GREEN: Implement EnvironmentPlanner** - `01066f1` (feat)

**Plan metadata:** (docs commit — pending)

_Note: TDD tasks have two commits each (test RED → feat GREEN)_

## Files Created/Modified

- `claude_env/pipeline/domain_classifier.py` — classify() and load_all_profiles() pure functions
- `claude_env/pipeline/environment_planner.py` — plan() producing GenerationPlan with Artifact list
- `tests/test_domain_classifier.py` — 6 tests: web/cli signal match, fallback, case-insensitive, ValueError, load integration
- `tests/test_environment_planner.py` — 7 tests: CLAUDE.md artifact, skill/agent counts, layers, context keys, invalid template, real web.yaml

## Decisions Made

- Signal matching operates on `spec.tech_stack + spec.languages` token set — real profiles use file path signals (package.json, pyproject.toml), but the classifier is agnostic to signal semantics; test fixtures use named technology signals
- Template validation happens inside `plan()` before returning the `GenerationPlan` — early failure, not deferred to Phase 3 generator
- All artifacts are `layer=PROJECT`; the global vs project distinction is a Phase 3 concern

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

Pre-existing `ruff` E501 lint error in `claude_env/pipeline/input_normalizer.py` (line 17, 107 chars) — out of scope for this plan, not introduced by these changes. Verified our two new files are ruff-clean.

## Next Phase Readiness

- Domain Classifier and Environment Planner complete — Phase 3 generator can consume GenerationPlan directly
- TemplateRegistry (Phase 1) renders artifacts; plan() produces the Artifact list it needs
- Remaining Phase 2 plan (if any) can integrate classify() + plan() into the full pipeline

---
*Phase: 02-pipeline*
*Completed: 2026-04-18*
