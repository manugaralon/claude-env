---
phase: 02-pipeline
plan: "02"
subsystem: pipeline
tags: [anthropic, pydantic, yaml, markdown, llm, input-normalizer]

# Dependency graph
requires:
  - phase: 02-pipeline-01
    provides: ProjectSpec model, pipeline __init__.py, OutputLayer enum
  - phase: 01-foundation
    provides: TemplateRegistry, DomainProfile, project scaffold
provides:
  - InputNormalizer class with from_freeform() and from_spec_file() methods
  - spec_parser module with parse_yaml_spec and parse_markdown_spec
  - Full test suite with mock LLM client (11 tests)
affects: [03-generator, 04-skills, 05-cli]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mock client injection via __init__ param — LLM path testable without API key"
    - "JSON fence stripping with _extract_json helper before json.loads"
    - "isinstance(TextBlock) narrowing for mypy strict on anthropic SDK content"
    - "removeprefix() for bullet list parsing in markdown sections"

key-files:
  created:
    - claude_env/pipeline/spec_parser.py
    - claude_env/pipeline/input_normalizer.py
    - tests/test_input_normalizer.py
  modified: []

key-decisions:
  - "Mock client injected via __init__ constructor (not module-level) — avoids real API calls in tests"
  - "TextBlock constructed directly (not MagicMock(spec=TextBlock)) so isinstance check passes in normalizer"
  - "_extract_json strips both plain and ```json fenced responses before json.loads"

patterns-established:
  - "LLM client injected via constructor, default is anthropic.Anthropic() — testable by design"
  - "Spec file dispatch by suffix (.yaml/.yml -> parse_yaml_spec, .md -> parse_markdown_spec)"

requirements-completed: [PIPE-01, PIPE-02]

# Metrics
duration: 12min
completed: 2026-04-18
---

# Phase 2 Plan 02: Input Normalizer Summary

**InputNormalizer with LLM freeform path (mock-injectable), YAML/Markdown spec parsers, and 11 passing tests — no ANTHROPIC_API_KEY needed for testing**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-04-18T20:15:00Z
- **Completed:** 2026-04-18T20:27:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `parse_yaml_spec` and `parse_markdown_spec` in `spec_parser.py` — fixture-file validated
- `InputNormalizer` class with `from_freeform()` (LLM via injected client) and `from_spec_file()` (extension dispatch)
- `_extract_json()` strips markdown fences before json.loads — handles LLM wrapping pattern
- 11 tests covering both input paths, JSON fence stripping, and unsupported extension error

## Task Commits

Each task was committed atomically:

1. **Task 1: spec_parser (YAML + Markdown) with tests** - `7dcd883` (feat)
2. **Task 2: InputNormalizer with LLM freeform path and dispatch** - `2c27464` (feat)

_Note: Both tasks used TDD (RED->GREEN). Tests written before implementation._

## Files Created/Modified

- `claude_env/pipeline/spec_parser.py` — parse_yaml_spec and parse_markdown_spec functions
- `claude_env/pipeline/input_normalizer.py` — InputNormalizer class, _extract_json helper, _LLM_MODEL constant
- `tests/test_input_normalizer.py` — 11 tests including make_mock_client() helper

## Decisions Made

- Mock client injected via `__init__` (default `anthropic.Anthropic()`) so tests run without API key
- `TextBlock(text=..., type="text")` constructed as real Pydantic model in tests so `isinstance(block, TextBlock)` passes in normalizer code
- `_extract_json` strips both plain ``` and ```json fenced responses before parsing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed ruff E501 in _SYSTEM_PROMPT string**
- **Found during:** Task 2 (post-implementation ruff check)
- **Issue:** System prompt had a line exceeding the 100-char limit (107 chars)
- **Fix:** Added backslash continuation to split the long line in the prompt string
- **Files modified:** claude_env/pipeline/input_normalizer.py
- **Verification:** `uv run ruff check claude_env/pipeline/` exits 0
- **Committed in:** 2c27464 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking/style)
**Impact on plan:** Trivial line-wrap fix. No scope creep.

## Issues Encountered

None — plan executed cleanly. The pytest `-k "yaml or markdown"` selector also matched `test_from_spec_file_yaml` and `test_from_spec_file_markdown` which failed at Task 1 time (expected, as InputNormalizer didn't exist yet). All 6 pure spec_parser tests passed in Task 1's GREEN phase.

## User Setup Required

None - no external service configuration required. LLM path is tested via mock injection.

## Next Phase Readiness

- Both input paths (freeform + spec file) produce `ProjectSpec` — downstream generator can consume either
- `ANTHROPIC_API_KEY` required only at runtime for `from_freeform()` — tests are API-key free
- Phase 03 (generator) can import `InputNormalizer` directly from `claude_env.pipeline.input_normalizer`

---
*Phase: 02-pipeline*
*Completed: 2026-04-18*
