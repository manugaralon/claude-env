---
phase: 03-generator
plan: "01"
subsystem: generator
tags: [jinja2, sentinel, templates, content-catalogue, tdd]

requires:
  - phase: 02-pipeline
    provides: Artifact and GenerationPlan models consumed by enrich_artifact_context
  - phase: 01-foundation
    provides: TemplateRegistry used in template rendering tests

provides:
  - sentinel merge module (wrap_with_sentinel, has_sentinel, merge_sentinel_block)
  - content catalogue (enrich_artifact_context for 5 skills + 3 agents)
  - expanded claude_md_project.j2 with 5 guarded sections
  - settings_json.j2 with PostToolUse hooks and tojson escaping

affects: [03-02-generator-class]

tech-stack:
  added: []
  patterns:
    - "Sentinel markers delimit managed blocks; replace in-place or append, preserving user content"
    - "Content catalogue uses setdefault so caller-supplied context values always win over catalogue defaults"
    - "Template sections are guarded with {% if 'section_id' in sections %} flags"

key-files:
  created:
    - claude_env/generator/__init__.py
    - claude_env/generator/sentinel.py
    - claude_env/generator/content_catalogue.py
    - templates/settings_json.j2
    - tests/test_sentinel.py
    - tests/test_content_catalogue.py
  modified:
    - templates/claude_md_project.j2
    - tests/test_template_registry.py

key-decisions:
  - "Sentinel uses _BEGIN/_END module constants (not exported) to avoid marker strings leaking into template output"
  - "content_catalogue uses separate local variable names for skill vs agent catalogue lookups to satisfy mypy strict typing"
  - "test_template_registry.py updated: old assertion checked for literal section IDs which the expanded template no longer emits; new assertion checks rendered section content"

patterns-established:
  - "TDD RED-GREEN executed strictly: tests committed first, then implementation"
  - "Deviation Rule 1 applied: pre-existing test updated to match expanded template behavior"

requirements-completed: [GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06]

duration: 3min
completed: 2026-04-19
---

# Phase 3 Plan 01: Sentinel Merge + Content Catalogue + Templates Summary

**Idempotent sentinel merge module and content catalogue enriching 5 skill slugs and 3 agent slugs, with expanded claude_md_project.j2 (5 guarded sections, <=200 lines) and new settings_json.j2 with PostToolUse hooks**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-19T11:45:09Z
- **Completed:** 2026-04-19T11:48:31Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Sentinel merge module handles replace, append, idempotency, and user-edit preservation outside managed block
- Content catalogue maps all 5 skill slugs (fix-issue, create-pr, run-lint, update-deps, add-subcommand) and 3 agent slugs (security-reviewer, accessibility-auditor, cli-ux-reviewer) to rich context
- claude_md_project.j2 expanded from 12-line stub to full template with 5 conditional sections; renders 40 lines for web.yaml (well under 200 limit)
- settings_json.j2 generates valid JSON with PostToolUse hooks and tojson escaping for special chars
- 18 tests pass across test_sentinel.py (8) and test_content_catalogue.py (10); ruff and mypy clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Sentinel merge module + tests** - `dd14f3d` (feat)
2. **Task 2: Content catalogue + expanded templates + tests** - `d2daa4d` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `claude_env/generator/__init__.py` - Package init with docstring
- `claude_env/generator/sentinel.py` - wrap_with_sentinel, has_sentinel, merge_sentinel_block
- `claude_env/generator/content_catalogue.py` - enrich_artifact_context with _SKILL_CATALOGUE and _AGENT_CATALOGUE
- `templates/claude_md_project.j2` - Expanded from stub to 5-section conditional template
- `templates/settings_json.j2` - New: PostToolUse hooks JSON template with tojson filter
- `tests/test_sentinel.py` - 8 tests covering all sentinel behaviors
- `tests/test_content_catalogue.py` - 10 tests covering catalogue enrichment and template rendering
- `tests/test_template_registry.py` - Updated assertion to check rendered content, not section IDs

## Decisions Made
- Sentinel module uses `_BEGIN`/`_END` as module-level private constants so the marker strings live only in sentinel.py and never contaminate template output (CRITICAL requirement in plan satisfied)
- Used separate variable names (`entry` vs `agent_entry`) in `enrich_artifact_context` to satisfy mypy strict typing on the two catalogue dict types
- `setdefault` used for all catalogue enrichment so caller-supplied context always wins over catalogue defaults

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated pre-existing test_template_registry.py assertion**
- **Found during:** Task 2 (full test suite run)
- **Issue:** `test_claude_md_project_renders` asserted `"plan_execute_verify" in out` — valid with old stub that listed section names literally; invalid with new template that renders section content via if-guards
- **Fix:** Changed assertions to check for rendered content (`"Plan" in out`, `"context" in out.lower()`) instead of section ID strings
- **Files modified:** tests/test_template_registry.py
- **Verification:** Full test suite passes (73 tests, 0 failures)
- **Committed in:** d2daa4d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - existing test reflecting stale template behavior)
**Impact on plan:** Necessary update; no scope creep.

## Issues Encountered
- mypy flagged incompatible type assignment when reusing `entry` variable for both `dict[str, str]` (skill) and `dict[str, object]` (agent) lookups in the same function. Fixed by using `agent_entry` as a distinct local variable for the agent branch.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- sentinel.py, content_catalogue.py, claude_md_project.j2, and settings_json.j2 are all ready for Plan 02's Generator class to consume
- Generator class (03-02) can import and call enrich_artifact_context before rendering, and merge_sentinel_block when writing files

---
*Phase: 03-generator*
*Completed: 2026-04-19*
