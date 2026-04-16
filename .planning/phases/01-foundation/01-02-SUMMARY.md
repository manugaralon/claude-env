---
phase: 01-foundation
plan: 02
subsystem: data-model
tags: [pydantic, pydantic-v2, yaml, domain-profile, schema]

# Dependency graph
requires:
  - phase: 01-foundation/01-01
    provides: claude_env package tree, pyproject.toml with pydantic + pyyaml deps, tests/ scaffold with conftest

provides:
  - DomainProfile Pydantic v2 model with locked schema (extra="forbid")
  - load_profile(Path) helper: yaml.safe_load + model_validate
  - 5 concrete YAML profiles: web, cli, data, infra, general
  - Unit test suite covering valid load, missing field, extra field, wrong type, all 5 real profiles
  - Fixture YAMLs for invalid inputs

affects:
  - 02-domain-classifier (takes DomainProfile as output type)
  - 02-environment-planner (takes DomainProfile as input)
  - 03-generator (reads profiles from disk via load_profile)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ConfigDict(extra='forbid') on all schema models to prevent silent drift"
    - "yaml.safe_load (never yaml.load) for security"
    - "TDD: failing test commit -> implementation commit"

key-files:
  created:
    - claude_env/models/domain_profile.py
    - claude_env/profiles/web.yaml
    - claude_env/profiles/cli.yaml
    - claude_env/profiles/data.yaml
    - claude_env/profiles/infra.yaml
    - claude_env/profiles/general.yaml
    - tests/test_domain_profile.py
    - tests/fixtures/profiles/invalid_missing_field.yaml
    - tests/fixtures/profiles/invalid_extra_field.yaml
  modified: []

key-decisions:
  - "detection_signals are flat strings (e.g., 'src/App.tsx') — resolves Open Q1 from research"
  - "general.yaml uses detection_signals: [] as intentional fallback — resolves Open Q3 from research"
  - "extra='forbid' on DomainProfile — any new field in Phase 2+ must update the model first"

patterns-established:
  - "load_profile(Path) is the canonical way to deserialize any domain profile YAML"
  - "Schema frozen at 8 fields: domain, display_name, description, skill_slugs, agent_slugs, claude_md_sections, hook_templates, detection_signals"

requirements-completed: []

# Metrics
duration: 8min
completed: 2026-04-16
---

# Phase 1 Plan 02: DomainProfile Schema and Domain Profiles Summary

**DomainProfile Pydantic v2 model with extra='forbid' locking 8-field schema, plus 5 concrete YAML profiles (web, cli, data, infra, general) validated by 10-test suite**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-16T12:06:45Z
- **Completed:** 2026-04-16T12:14:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- DomainProfile Pydantic v2 model with `extra="forbid"` — schema drift will be caught at validation time, not silently ignored
- `load_profile(Path)` helper using `yaml.safe_load` + `model_validate` — single entry point for all profile deserialization
- 5 domain profile YAMLs covering all project types the classifier will resolve to
- 10 tests: valid load via helper, model_validate direct, missing field, extra field, wrong type, parametrized over all 5 real profiles

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `e7ae214` (test)
2. **Task 1 GREEN: DomainProfile model + load_profile** - `06b85ea` (feat)
3. **Task 2: 5 domain profile YAMLs** - `eb36b65` (feat)

_Note: TDD task has separate test and implementation commits._

## Files Created/Modified

- `claude_env/models/domain_profile.py` - DomainProfile Pydantic model + load_profile() helper
- `claude_env/profiles/web.yaml` - Web/frontend domain profile
- `claude_env/profiles/cli.yaml` - CLI tool domain profile
- `claude_env/profiles/data.yaml` - Data pipeline/ETL domain profile
- `claude_env/profiles/infra.yaml` - Infrastructure as Code domain profile
- `claude_env/profiles/general.yaml` - Fallback profile (detection_signals: [])
- `tests/test_domain_profile.py` - 10 tests covering all contract scenarios
- `tests/fixtures/profiles/invalid_missing_field.yaml` - Missing `domain` key fixture
- `tests/fixtures/profiles/invalid_extra_field.yaml` - Unknown `foo: bar` key fixture

## DomainProfile Schema Contract (for Phase 2 reference)

```python
class DomainProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str                    # Canonical: "web", "cli", "data", "infra", "general"
    display_name: str              # Human label
    description: str               # One-line description
    skill_slugs: list[str]         # 3-5 skill names
    agent_slugs: list[str]         # 2-3 agent names
    claude_md_sections: list[str]  # Section/template IDs
    hook_templates: list[str]      # Hook template IDs for settings.json
    detection_signals: list[str]   # Flat file/pattern strings (e.g., "src/App.tsx")
```

## Open Research Questions Resolved

- **Open Q1 (detection_signals format):** Flat strings (e.g., `"src/App.tsx"`, `"package.json"`) — not structured objects. Simple and sufficient for classifier file-presence checks.
- **Open Q3 (fallback domain):** `general.yaml` exists with `detection_signals: []` — classifier uses it when no other domain signals match.

## Decisions Made

- `detection_signals` are flat strings resolving Open Q1 from research
- `general.yaml` with empty `detection_signals` resolves Open Q3 — explicit fallback, never auto-detected
- `extra="forbid"` on `DomainProfile` ensures Phase 2+ changes require explicit model update first

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `DomainProfile` schema is frozen and tested — Domain Classifier (Phase 2) can take it as output type
- `load_profile(Path)` is the canonical deserialization entry point — Environment Planner and Generator can import directly
- Blocker "Domain profile YAML schema — core data contract, must be finalized in Phase 1" is now resolved
- ruff + mypy strict pass on all new code

---
*Phase: 01-foundation*
*Completed: 2026-04-16*
