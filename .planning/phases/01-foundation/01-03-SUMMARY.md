---
phase: 01-foundation
plan: "03"
subsystem: templating
tags: [jinja2, templates, registry, strict-undefined, tdd]

requires:
  - phase: 01-01
    provides: package layout, pyproject.toml, uv/pytest/mypy/ruff setup

provides:
  - TemplateRegistry class (single rendering path for all generated artifacts)
  - 3 stub Jinja2 templates (claude_md_project.j2, skill_stub.j2, agent_stub.j2)
  - Unit tests (7) + integration tests (5) covering the full rendering contract

affects:
  - Phase 3 generators (CLAUDE.md, SKILL.md, agent stubs) — must use TemplateRegistry.render()

tech-stack:
  added: [jinja2 (already in deps), no new packages required]
  patterns:
    - "TemplateRegistry as single rendering path — all generated artifacts go through render()"
    - "StrictUndefined to surface missing context variables at render time, not silently"
    - "Absolute path guard on constructor to prevent cwd-relative lookup bugs"
    - "TDD: RED commit (failing tests) then GREEN commit (implementation)"

key-files:
  created:
    - claude_env/templates/registry.py
    - templates/claude_md_project.j2
    - templates/skill_stub.j2
    - templates/agent_stub.j2
    - tests/test_template_registry.py
  modified: []

key-decisions:
  - "TemplateRegistry uses StrictUndefined — missing context vars raise jinja2.UndefinedError immediately (closes Pitfall #5)"
  - "autoescape=False — output is markdown/text, HTML escaping would mangle angle brackets in code blocks"
  - "keep_trailing_newline=True — preserves file trailing newlines for concatenation-friendly generated files"
  - "Absolute path guard raises ValueError — prevents cwd-dependent test/runtime failures (closes Pitfall #2)"
  - "templates/ lives at project root, not inside claude_env/ — FileSystemLoader reads plain directories, not Python packages"
  - "Whitespace control via {%- for %} in stub templates — prevents stray blank lines in YAML frontmatter (closes Pitfall #5)"

patterns-established:
  - "All artifact rendering goes through TemplateRegistry.render(template_id, context) — never raw jinja2 directly"
  - "Integration tests use Path(__file__).parent.parent / 'templates' .resolve() for deterministic absolute path"

requirements-completed: []

duration: 8min
completed: 2026-04-16
---

# Phase 1 Plan 03: Template Registry Summary

**Jinja2 TemplateRegistry with StrictUndefined, absolute-path guard, and 3 stub templates locking the rendering contract for Phase 3 generators**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-16T12:09:58Z
- **Completed:** 2026-04-16T12:18:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- `TemplateRegistry` class ships with StrictUndefined, autoescape=False, keep_trailing_newline=True, and absolute-path guard
- 3 stub Jinja2 templates at project root: `claude_md_project.j2`, `skill_stub.j2`, `agent_stub.j2`
- 12 passing tests (7 unit + 5 integration) covering the full rendering contract
- ruff + mypy strict green on all new code
- Research Pitfalls #2 and #5 closed by constructor invariants and template whitespace control

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TemplateRegistry class with tests (RED)** - `2695521` (test)
2. **Task 1: Create TemplateRegistry class with tests (GREEN)** - `7fedae4` (feat)
3. **Task 2: Create 3 stub templates and integration tests** - `de0ef3b` (feat)

_Note: TDD task had two commits (test RED → feat GREEN). No REFACTOR step needed._

## Files Created/Modified
- `claude_env/templates/registry.py` - TemplateRegistry class: render-by-name facade over jinja2.Environment
- `templates/claude_md_project.j2` - Stub template for generated per-project CLAUDE.md (context: project_name, domain, sections)
- `templates/skill_stub.j2` - Stub template for generated SKILL.md files (context: skill_name, description, invocation)
- `templates/agent_stub.j2` - Stub template for generated agent .md files (context: agent_name, description, skills)
- `tests/test_template_registry.py` - Unit tests (7) + integration tests (5) for the full registry contract

## Public API

```python
class TemplateRegistry:
    def __init__(self, templates_dir: Path) -> None:
        # Raises ValueError if templates_dir is not absolute

    def render(self, template_id: str, context: dict[str, object]) -> str:
        # Raises jinja2.UndefinedError on missing context vars (StrictUndefined)
        # Raises jinja2.TemplateNotFound if template_id doesn't exist

    def list_templates(self) -> list[str]:
        # Returns list of template filenames available in templates_dir
```

## Stub Template Contracts (for Phase 3)

| Template | Context variables |
|---|---|
| `claude_md_project.j2` | `project_name: str`, `domain: str`, `sections: list[str]` |
| `skill_stub.j2` | `skill_name: str`, `description: str`, `invocation: str` |
| `agent_stub.j2` | `agent_name: str`, `description: str`, `skills: list[str]` |

## Decisions Made
- StrictUndefined chosen over default Undefined — default silently produces empty strings, masking bugs in generated output
- autoescape=False because all output is Markdown/text; HTML escaping would corrupt angle brackets in code blocks
- templates/ at project root (confirmed from prior decisions) — Jinja2 FileSystemLoader reads a plain directory, not a Python package
- Whitespace control `{%- for ... %}` / `{%- endfor %}` used in stub templates to prevent stray blank lines in YAML frontmatter blocks

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `TemplateRegistry` is the locked single rendering path; Phase 3 generators must import and use it
- Stub templates are concrete starting points — Phase 3 fleshes them out with full content sections
- No blockers for Phase 2 (Input Normalizer / CLI) — registry is independent

---
*Phase: 01-foundation*
*Completed: 2026-04-16*
