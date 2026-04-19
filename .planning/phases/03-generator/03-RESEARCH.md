# Phase 3: Generator - Research

**Researched:** 2026-04-18
**Domain:** File generation — idempotent disk writer, sentinel merge, template expansion, settings.json production
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GEN-01 | Generator produces `.claude/CLAUDE.md` ≤200 lines with plan→execute→verify, context management, and lessons.md loop | Template expansion via existing `claude_md_project.j2` + enriched context dict; line-count enforced post-render |
| GEN-02 | Generator produces 3–5 domain-appropriate `.claude/skills/<name>/SKILL.md` files with YAML frontmatter and verb-phrase descriptions | `skill_stub.j2` requires richer context: `skill_name`, `description`, `invocation`; context must be supplied from DomainProfile or a skill-catalogue fixture |
| GEN-03 | Generator produces 2–3 `.claude/agents/<name>.md` files with explicit `skills:` field | `agent_stub.j2` already has correct frontmatter shape with `skills:` list; context must supply `agent_name`, `description`, `skills` list |
| GEN-04 | Generator produces `.claude/settings.json` with lint/typecheck hooks using hardcoded paths and exit code 2 | No template exists yet for settings.json — new `settings_json.j2` template needed; `exitCode: 2` is the Claude Code blocking convention |
| GEN-05 | Generator produces/updates global `~/.claude/CLAUDE.md` via merge-safe sentinel pattern | Sentinel pattern: `# BEGIN CLAUDE-ENV MANAGED` / `# END CLAUDE-ENV MANAGED` delimiters; read existing file, locate block, replace, write back |
| GEN-06 | All generation is idempotent — re-running merges safely without overwriting user customizations | Sentinel-protected sections are never overwritten; files written with write-if-changed semantics; user-edited content outside sentinels is preserved |
</phase_requirements>

---

## Summary

Phase 3 is the I/O layer that takes the `GenerationPlan` (pure data, no I/O) produced by Phase 2 and writes all artifacts to disk. The primary engineering challenges are (1) implementing the sentinel merge strategy for GEN-05/GEN-06 so re-runs are safe, (2) enriching the artifact contexts that Phase 2 left minimal (skill and agent stubs need content beyond the planner's `slug` + `domain`), and (3) adding a `settings.json` artifact that Phase 2 did not include.

The existing templates (`skill_stub.j2`, `agent_stub.j2`) expect more context variables than the Environment Planner currently injects — the planner only puts `slug` and `domain` into skill/agent context, but the templates also reference `skill_name`, `description`, `invocation`, `agent_name`, and `skills` (list). Phase 3 must either enrich the context at generation time or update the planner to inject richer context. The cleanest path is to define a domain-level **content catalogue** (skill descriptions, agent descriptions, skills-list mapping) and look up values at generation time — this keeps the planner's context minimal and the generator responsible for content expansion.

The sentinel merge strategy for `~/.claude/CLAUDE.md` (GEN-05) must be designed precisely: delimit a managed block with unique markers, read the existing file, locate the block, replace only that block, and write the file atomically. All content outside the managed block is untouched. The same pattern applies to the per-project `.claude/CLAUDE.md` on re-run.

**Primary recommendation:** Implement Generator as a single `Generator` class with `execute(plan, project_root, global_root)`. Add a `content_catalogue.py` module that maps domain + slug to full skill/agent metadata. Implement sentinel merge as a standalone utility function. Write `settings_json.j2` template. Run all tests against real filesystem writes using `tmp_path`.

---

## Standard Stack

### Core (all already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.13.1 | `GenerationPlan`, `Artifact` — already locked | Passed in from Phase 2; no new schema work |
| Jinja2 | 3.1.6 | Template rendering via `TemplateRegistry.render()` | Already wired; `TemplateRegistry` is the only rendering path |
| pathlib | stdlib | All path construction and file I/O | `Path.write_text()`, `Path.mkdir(parents=True, exist_ok=True)` |
| json | stdlib | Write and validate `settings.json` | `json.dumps(data, indent=2)` produces valid JSON; roundtrip validates it |

### No New Dependencies

Phase 3 requires zero new packages. All I/O is stdlib pathlib + json. Jinja2 and Pydantic are already installed.

**Version verification (confirmed 2026-04-18):**
- All deps locked in `uv.lock` — no additions needed.

---

## Architecture Patterns

### Recommended Project Structure (additions for Phase 3)

```
claude_env/
├── generator/
│   ├── __init__.py
│   ├── generator.py          # Generator class — execute(plan, project_root, global_root)
│   ├── sentinel.py           # merge_sentinel_block() utility
│   └── content_catalogue.py  # Domain → skill/agent content lookup
templates/
├── claude_md_project.j2      # Phase 1 stub — needs expansion (GEN-01)
├── skill_stub.j2             # Phase 1 stub — context shape already correct
├── agent_stub.j2             # Phase 1 stub — context shape already correct
└── settings_json.j2          # NEW — Claude Code hooks (GEN-04)
tests/
├── test_generator.py         # GEN-01 through GEN-06 coverage
└── fixtures/
    └── plans/
        └── web_plan.py       # Pre-built GenerationPlan fixture for tests
```

### Pattern 1: Generator Class

**What:** A class that accepts `TemplateRegistry` at construction and exposes `execute()`. Iterates all artifacts in the plan, resolves the target path based on `layer`, creates parent directories, and writes the rendered content.

**When to use:** This is the single execution path — nothing else writes files.

```python
# claude_env/generator/generator.py
from __future__ import annotations

from pathlib import Path

from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer
from claude_env.templates.registry import TemplateRegistry
from claude_env.generator.sentinel import merge_sentinel_block
from claude_env.generator.content_catalogue import enrich_artifact_context


class Generator:
    def __init__(self, registry: TemplateRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        plan: GenerationPlan,
        project_root: Path,    # abs path to target project dir
        global_root: Path,     # abs path to ~/.claude
    ) -> list[Path]:
        """Write all artifacts from plan to disk.

        Returns list of absolute paths that were written.
        Raises ValueError if any path resolves outside its layer root.
        """
        written: list[Path] = []
        for artifact in plan.artifacts:
            target = self._resolve_path(artifact, project_root, global_root)
            context = enrich_artifact_context(artifact, plan)
            content = self._registry.render(artifact.template_id, context)

            if target.exists() and _has_sentinel(target):
                current = target.read_text()
                content = merge_sentinel_block(current, content)

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(target)
        return written

    def _resolve_path(
        self,
        artifact: Artifact,
        project_root: Path,
        global_root: Path,
    ) -> Path:
        layer_root = project_root / ".claude" if artifact.layer == OutputLayer.PROJECT else global_root
        target = (layer_root / artifact.target_path).resolve()
        # Security: ensure target stays within layer root
        if not str(target).startswith(str(layer_root.resolve())):
            raise ValueError(f"Path traversal detected: {artifact.target_path}")
        return target
```

### Pattern 2: Sentinel Merge Strategy (GEN-05, GEN-06)

**What:** The merge strategy that makes re-runs safe. Managed sections are delimited by unique markers. On write: if the file does not exist, write directly. If it exists, locate the managed block, replace only that block, preserve everything else.

**Sentinel format:**

```
# BEGIN CLAUDE-ENV MANAGED — do not edit this block manually
[generated content]
# END CLAUDE-ENV MANAGED
```

**Implementation:**

```python
# claude_env/generator/sentinel.py
from __future__ import annotations

_BEGIN = "# BEGIN CLAUDE-ENV MANAGED"
_END = "# END CLAUDE-ENV MANAGED"

SENTINEL_HEADER = f"{_BEGIN} — do not edit this block manually\n"
SENTINEL_FOOTER = f"{_END}\n"


def wrap_with_sentinel(content: str) -> str:
    """Wrap content in sentinel markers."""
    return f"{SENTINEL_HEADER}{content}\n{SENTINEL_FOOTER}"


def merge_sentinel_block(existing: str, new_managed_content: str) -> str:
    """Replace the managed block in existing with new_managed_content.

    If no managed block exists in existing, appends the new block at the end.
    Content outside the managed block is preserved verbatim.

    Args:
        existing: Current file content.
        new_managed_content: New content to put inside the sentinel block.

    Returns:
        Merged file content with managed block replaced.
    """
    wrapped = wrap_with_sentinel(new_managed_content)

    begin_idx = existing.find(_BEGIN)
    end_idx = existing.find(_END)

    if begin_idx == -1 or end_idx == -1:
        # No existing block — append
        return existing.rstrip("\n") + "\n\n" + wrapped

    end_of_block = end_idx + len(_END)
    # Consume trailing newline after END marker if present
    if end_of_block < len(existing) and existing[end_of_block] == "\n":
        end_of_block += 1

    before = existing[:begin_idx]
    after = existing[end_of_block:]
    return before + wrapped + after


def has_sentinel(content: str) -> bool:
    return _BEGIN in content and _END in content
```

**Key insight:** The sentinel approach is the canonical "merge-safe generated section" pattern used by tools like Terraform, Rails generators, and git-crypt. The delimiters must be on their own lines and unique enough that a human would not accidentally write them. The `# BEGIN CLAUDE-ENV MANAGED` prefix is unlikely to conflict with any real content.

### Pattern 3: Content Catalogue (fills gap between planner and templates)

**What:** The Environment Planner stores minimal context (`slug`, `domain`) in each `Artifact`. The actual templates (`skill_stub.j2`, `agent_stub.j2`) expect richer data: `skill_name`, `description`, `invocation`, `agent_name`, `skills`. The content catalogue holds this mapping.

**When to use:** Called by `Generator.execute()` before rendering, not by the planner.

```python
# claude_env/generator/content_catalogue.py
from __future__ import annotations

from claude_env.models.generation_plan import Artifact, GenerationPlan

# Per-skill metadata: slug → {name, description, invocation}
_SKILL_CATALOGUE: dict[str, dict[str, str]] = {
    "fix-issue": {
        "skill_name": "fix-issue",
        "description": "Diagnose and fix a reported bug or failing test",
        "invocation": "/fix-issue",
    },
    "create-pr": {
        "skill_name": "create-pr",
        "description": "Stage changes, write commit message, and open a pull request",
        "invocation": "/create-pr",
    },
    "run-lint": {
        "skill_name": "run-lint",
        "description": "Run project linter and auto-fix correctable violations",
        "invocation": "/run-lint",
    },
    "update-deps": {
        "skill_name": "update-deps",
        "description": "Update project dependencies to latest compatible versions",
        "invocation": "/update-deps",
    },
    "add-subcommand": {
        "skill_name": "add-subcommand",
        "description": "Scaffold a new CLI subcommand with help text and tests",
        "invocation": "/add-subcommand",
    },
}

# Per-agent metadata: slug → {name, description, skills list}
_AGENT_CATALOGUE: dict[str, dict[str, object]] = {
    "security-reviewer": {
        "agent_name": "security-reviewer",
        "description": "Review code changes for security vulnerabilities and suggest mitigations",
        "skills": ["fix-issue", "create-pr"],
    },
    "accessibility-auditor": {
        "agent_name": "accessibility-auditor",
        "description": "Audit UI components for WCAG compliance and propose fixes",
        "skills": ["fix-issue"],
    },
    "cli-ux-reviewer": {
        "agent_name": "cli-ux-reviewer",
        "description": "Review CLI commands for usability, help text clarity, and ergonomics",
        "skills": ["fix-issue", "add-subcommand"],
    },
}


def enrich_artifact_context(artifact: Artifact, plan: GenerationPlan) -> dict[str, object]:
    """Return a context dict suitable for rendering artifact.template_id.

    Starts from artifact.context and supplements with catalogue data.
    Unknown slugs fall back to slug-derived defaults.
    """
    ctx = dict(artifact.context)

    if artifact.template_id == "skill_stub.j2":
        slug = str(ctx.get("slug", ""))
        catalogue_entry = _SKILL_CATALOGUE.get(slug, {})
        ctx.setdefault("skill_name", catalogue_entry.get("skill_name", slug))
        ctx.setdefault("description", catalogue_entry.get("description", f"Perform {slug} tasks"))
        ctx.setdefault("invocation", catalogue_entry.get("invocation", f"/{slug}"))

    elif artifact.template_id == "agent_stub.j2":
        slug = str(ctx.get("slug", ""))
        catalogue_entry = _AGENT_CATALOGUE.get(slug, {})
        ctx.setdefault("agent_name", catalogue_entry.get("agent_name", slug))
        ctx.setdefault("description", catalogue_entry.get("description", f"{slug} agent"))
        ctx.setdefault("skills", catalogue_entry.get("skills", []))

    return ctx
```

### Pattern 4: settings.json Template (GEN-04)

**What:** A new `settings_json.j2` template that renders valid JSON for `.claude/settings.json`. Uses `| tojson` Jinja2 filter for proper JSON string escaping. Must produce a `hooks` key with `PreToolUse` or `PostToolUse` hooks for lint and typecheck, using `exitCode: 2` to block on failure.

**Claude Code settings.json hook structure (from real `~/.claude/settings.json` inspection):**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<hardcoded path to lint script>",
            "exitCode": 2
          }
        ]
      }
    ]
  }
}
```

**Template (`templates/settings_json.j2`):**

```jinja2
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
{%- for hook in hooks %}
          {
            "type": "command",
            "command": {{ hook.command | tojson }},
            "exitCode": {{ hook.exit_code }}
          }{% if not loop.last %},{% endif %}
{%- endfor %}
        ]
      }
    ]
  }
}
```

**GEN-04 clarification:** "hardcoded paths" means the generator writes the hook command as a resolved absolute path (e.g., `/usr/local/bin/ruff check .`) rather than a relative path or shell alias. This ensures the hook works regardless of shell PATH configuration.

**Artifact context for settings.json:**
```python
Artifact(
    target_path="settings.json",
    template_id="settings_json.j2",
    context={
        "hooks": [
            {"command": "/usr/local/bin/ruff check .", "exit_code": 2},
            {"command": "/usr/local/bin/mypy .", "exit_code": 2},
        ]
    },
    layer=OutputLayer.PROJECT,
)
```

The Environment Planner currently does **not** produce a `settings.json` artifact — this is left to Phase 3 because the planner has no access to the target filesystem (to detect tool paths). The Generator must inject this artifact at execution time, extending the plan with a settings.json entry.

### Pattern 5: Template Expansion for GEN-01

**What:** The existing `claude_md_project.j2` is a stub (12 lines). GEN-01 requires the output to be ≤200 lines and contain three specific sections: plan→execute→verify pattern, context management rules, and lessons.md auto-improvement loop. The template must be expanded substantially.

**Template expansion strategy:**
- Each `claude_md_sections` ID in the profile maps to a template block defined inline in `claude_md_project.j2` using Jinja2 `{% macro %}` or `{% if section_id in sections %}` guards.
- The three required sections (plan→execute→verify, context_management, lessons_loop) map to section IDs already in `web.yaml` and `cli.yaml` profiles.
- Total rendered output must stay ≤200 lines — the template must be written to stay within this budget.

**Section ID → content mapping (inside `claude_md_project.j2`):**

| Section ID | Generates |
|------------|-----------|
| `plan_execute_verify` | "## Workflow: Plan → Execute → Verify" with 3-step pattern |
| `context_management` | "## Context Management" with compact/subagent rules |
| `lessons_loop` | "## Lessons Loop" with `lessons.md` write-back instruction |
| `mobile_first` | "## Mobile-First UI" with 44×44px minimum target note |
| `surgical_changes` | "## Surgical Changes" with minimal-diff rule |

### Anti-Patterns to Avoid

- **Writing `target_path` containing `..` or `~`:** `Artifact.target_path` is always relative to the layer root. The Generator resolves it; never pass resolved paths into the Artifact model.
- **Using `Path.open('w')` without encoding:** Always `write_text(content, encoding="utf-8")`. Default encoding is platform-dependent — breaks on Windows and some Linux locales.
- **Constructing `settings.json` by string concatenation:** Use `json.dumps()` with `indent=2` to validate the data structure before writing, then write the string. A syntax error in a manually constructed JSON string is silent until runtime.
- **Sentinel markers inside code blocks in CLAUDE.md:** If the template outputs markdown code blocks, ensure the sentinel markers are at the top level of the file, not inside a fenced block — otherwise the `has_sentinel()` check would find them and treat code examples as managed content.
- **Creating parent dirs with `mkdir()` alone:** Use `Path.mkdir(parents=True, exist_ok=True)` — the `.claude/skills/fix-issue/` path requires three levels of creation.
- **Not enriching agent `skills:` field:** GEN-03 explicitly requires `skills:` references. The `agent_stub.j2` template already has `{%- for skill in skills %}` — if `skills` is empty (as injected by the planner), the frontmatter `skills:` section will be empty, violating GEN-03. The content catalogue must supply non-empty `skills` lists.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization for settings.json | String concatenation or f-strings | `json.dumps(data, indent=2)` | Escaping, trailing commas, Unicode — all handled by stdlib |
| Atomic file write | `f.write()` + manual temp-file swap | `Path.write_text()` | Python's `write_text()` is atomic on POSIX (writes to temp then renames) — sufficient for this use case |
| Sentinel delimiter search | Regex with lookahead | Simple `str.find()` | Markers are deterministic strings on their own lines; regex adds no value here |
| Directory creation | Manual `os.makedirs()` | `Path.mkdir(parents=True, exist_ok=True)` | Cleaner, idiomatic pathlib, works on all platforms |
| Template variable quoting in settings.json | Manual escaping | Jinja2 `| tojson` filter | Handles embedded quotes, backslashes, Unicode code points correctly |

**Key insight:** Phase 3 is almost entirely stdlib pathlib + existing Jinja2 machinery. The only design work is the sentinel merge algorithm and the content catalogue. Don't add libraries.

---

## Common Pitfalls

### Pitfall 1: Planner context is insufficient for current templates

**What goes wrong:** `Generator.execute()` calls `registry.render("skill_stub.j2", artifact.context)` and gets `jinja2.UndefinedError: 'skill_name' is undefined`. The planner only injects `slug` and `domain`; the template also needs `skill_name`, `description`, and `invocation`.

**Why it happens:** Phase 2 decision: "All Artifacts assigned layer=PROJECT — global layer assignment is a Phase 3 generator concern." The planner deliberately kept context minimal. The Phase 3 generator is expected to enrich it.

**How to avoid:** The `content_catalogue.enrich_artifact_context()` function must be called before every `registry.render()` call. Never call render directly with `artifact.context` alone.

**Warning signs:** Any `UndefinedError` during tests that use real templates against real artifacts from the planner.

### Pitfall 2: settings.json artifact is missing from the plan

**What goes wrong:** `Generator.execute()` completes without writing `.claude/settings.json`. GEN-04 is unmet. The test passes because no test asserts `settings.json` exists if the artifact was never in the plan.

**Why it happens:** The Environment Planner currently does not produce a `settings.json` artifact — this was explicitly deferred: "All Artifacts assigned layer=PROJECT — global layer assignment is a Phase 3 generator concern." But the planner also doesn't add settings.json.

**How to avoid:** Two options: (a) extend the planner to add a `settings.json` artifact using a `settings_json.j2` template (cleanest — keeps the plan complete), or (b) have the Generator inject this artifact at execution time. Option (a) is cleaner — but requires the `settings_json.j2` template to exist before the planner test can validate it. Recommendation: create the template in Wave 0 of Phase 3, then update the planner to include the settings artifact, then implement the generator.

**Warning signs:** After generator runs, listing `.claude/` shows `CLAUDE.md`, `skills/`, `agents/` but no `settings.json`.

### Pitfall 3: Sentinel merge corrupts file on re-run if template adds sentinel markers

**What goes wrong:** The generated `CLAUDE.md` itself contains the string `# BEGIN CLAUDE-ENV MANAGED` (e.g., as an example in a "how this was generated" comment). On re-run, `merge_sentinel_block()` finds the marker inside the content, splits incorrectly, and corrupts the file.

**Why it happens:** `str.find()` finds the first occurrence of the marker, but if it's inside rendered content rather than at the top-level management boundary, the split point is wrong.

**How to avoid:** The `claude_md_project.j2` template must never emit the sentinel marker strings. Verify by rendering the template and asserting the output does not contain `_BEGIN` or `_END` before implementing the merge function. Add this assertion to the test suite.

**Warning signs:** Idempotency test fails on second run — file content changes between run 1 and run 2.

### Pitfall 4: Path traversal via crafted `target_path`

**What goes wrong:** An `Artifact` with `target_path = "../../etc/passwd"` causes the generator to write outside the project root.

**Why it happens:** `(layer_root / artifact.target_path).resolve()` resolves `..` segments. If not checked, arbitrary paths are writable.

**How to avoid:** After resolving the absolute path, assert it starts with `str(layer_root.resolve())`. Raise `ValueError` if not. This is implemented in the `_resolve_path()` example above. Add a test with a path-traversal artifact.

**Warning signs:** Generator test with malicious `target_path` writes to a location outside `tmp_path`.

### Pitfall 5: Global root ~/.claude write without existence check

**What goes wrong:** `Generator.execute()` tries to write to `~/.claude/CLAUDE.md` but `~/.claude/` does not exist on a fresh machine. `Path.parent.mkdir(parents=True, exist_ok=True)` handles this, but only if called on the target file's parent — not on the global root itself.

**Why it happens:** `global_root = Path.home() / ".claude"` may not exist. `target.parent.mkdir(parents=True, exist_ok=True)` where `target = global_root / "CLAUDE.md"` will create `~/.claude/` as needed — this is fine. The pitfall is forgetting to call `mkdir` and using `target.write_text()` directly.

**How to avoid:** The `execute()` loop must always call `target.parent.mkdir(parents=True, exist_ok=True)` before `target.write_text()`. This is already in the proposed pattern above — verify it's never skipped.

### Pitfall 6: Line count for GEN-01 exceeds 200

**What goes wrong:** The expanded `claude_md_project.j2` template, when rendered with a profile that has 4 sections, produces 220+ lines. GEN-01 fails.

**Why it happens:** Each section adds ~20-30 lines; with 4 sections and a header, it's easy to exceed 200 lines.

**How to avoid:** Write the template, render it with the most verbose profile (web.yaml has 4 sections: mobile_first, plan_execute_verify, context_management, lessons_loop), count the lines programmatically, and assert ≤200 in a test. Trim section content until the assertion passes. Write the test first.

**Warning signs:** `assert len(rendered.splitlines()) <= 200` fails in template rendering tests.

---

## Code Examples

### Generator execute loop

```python
# claude_env/generator/generator.py
def execute(self, plan: GenerationPlan, project_root: Path, global_root: Path) -> list[Path]:
    written: list[Path] = []
    for artifact in plan.artifacts:
        target = self._resolve_path(artifact, project_root, global_root)
        context = enrich_artifact_context(artifact, plan)
        content = self._registry.render(artifact.template_id, context)

        if target.exists() and has_sentinel(target.read_text()):
            existing = target.read_text(encoding="utf-8")
            content = merge_sentinel_block(existing, content)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(target)
    return written
```

### Sentinel merge — core logic

```python
# claude_env/generator/sentinel.py
def merge_sentinel_block(existing: str, new_managed_content: str) -> str:
    wrapped = wrap_with_sentinel(new_managed_content)
    begin_idx = existing.find(_BEGIN)
    end_idx = existing.find(_END)

    if begin_idx == -1 or end_idx == -1:
        return existing.rstrip("\n") + "\n\n" + wrapped

    end_of_block = existing.find("\n", end_idx) + 1  # consume line including newline
    before = existing[:begin_idx]
    after = existing[end_of_block:]
    return before + wrapped + after
```

### settings.json production via json.dumps (no template needed for simple case)

```python
# Alternative to template for settings.json — pure Python dict → JSON string
import json

def _build_settings_json(hook_commands: list[str]) -> str:
    data = {
        "hooks": {
            "PostToolUse": [
                {
                    "hooks": [
                        {"type": "command", "command": cmd, "exitCode": 2}
                        for cmd in hook_commands
                    ]
                }
            ]
        }
    }
    return json.dumps(data, indent=2) + "\n"
```

Note: Using `json.dumps` directly (instead of a Jinja2 template) for settings.json is simpler and eliminates JSON-in-Jinja2 escaping complexity. The tradeoff is it bypasses the TemplateRegistry. Both approaches are valid; the pure-Python approach is recommended for settings.json specifically because the structure is well-defined and not user-customizable per domain.

### Idempotency test pattern

```python
# tests/test_generator.py
def test_generator_is_idempotent(tmp_path: Path, registry: TemplateRegistry) -> None:
    gen = Generator(registry)
    plan = make_web_plan()  # fixture

    gen.execute(plan, tmp_path, tmp_path / "global")
    first_run = (tmp_path / ".claude" / "CLAUDE.md").read_text()

    gen.execute(plan, tmp_path, tmp_path / "global")
    second_run = (tmp_path / ".claude" / "CLAUDE.md").read_text()

    assert first_run == second_run, "Second run must not change output"
```

### Line count assertion for GEN-01

```python
def test_claude_md_line_count(tmp_path: Path, registry: TemplateRegistry) -> None:
    gen = Generator(registry)
    plan = make_web_plan()  # web profile has 4 sections — most verbose
    gen.execute(plan, tmp_path, tmp_path / "global")
    content = (tmp_path / ".claude" / "CLAUDE.md").read_text()
    line_count = len(content.splitlines())
    assert line_count <= 200, f"CLAUDE.md is {line_count} lines — must be ≤200"
```

---

## Context Shape Gap Analysis

This table maps the Phase 2 planner's output context against what each template actually requires:

| Template | Planner injects | Template also needs | Source |
|----------|----------------|---------------------|--------|
| `claude_md_project.j2` | `project_name`, `domain`, `sections` | Nothing else (stub is minimal, needs expansion) | Template expansion in Phase 3 |
| `skill_stub.j2` | `slug`, `domain` | `skill_name`, `description`, `invocation` | `content_catalogue.py` |
| `agent_stub.j2` | `slug`, `domain` | `agent_name`, `description`, `skills` (list) | `content_catalogue.py` |
| `settings_json.j2` (new) | — (not in plan) | `hooks` list | Generator injects artifact |

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Overwrite-on-run | Sentinel-delimited merge | User edits survive re-runs |
| `open(path, 'w')` + `os.makedirs()` | `Path.write_text()` + `Path.mkdir(parents=True, exist_ok=True)` | Idiomatic pathlib; no import of `os` needed |
| Separate tool for JSON validation | `json.dumps()` roundtrip in the generator | One stdlib call validates and serializes |
| Template context assembled at plan time | Planner context + catalogue enrichment at generate time | Planner stays pure/data; generator handles content |

---

## Open Questions

1. **Should settings.json artifact be added to the planner or injected by the generator?**
   - What we know: Phase 2 planner produces no `settings.json` artifact. Phase 2 decision log says "global layer assignment is Phase 3 concern" — but settings.json is PROJECT layer, not global.
   - What's unclear: Adding it to the planner requires `settings_json.j2` to exist during planner tests, or the template validation must be skipped for this artifact.
   - Recommendation: Create `settings_json.j2` (or a pure-Python settings builder) in Wave 0 of Phase 3, then add the artifact to the planner in the same wave. This keeps the plan complete and the generator simple.

2. **Sentinel scope: full file or section-per-artifact?**
   - What we know: GEN-05 says global `~/.claude/CLAUDE.md` uses sentinel merge. GEN-06 says re-runs are safe.
   - What's unclear: For the per-project CLAUDE.md, should the entire file be sentinel-wrapped (one block) or should each generated section have its own sentinel?
   - Recommendation: One sentinel block per file, wrapping the entire generated content. This is simpler to implement and test. User additions go outside the block (before or after). This covers GEN-06 fully.

3. **Hook command paths: detect at generation time or use configurable paths?**
   - What we know: GEN-04 says "hardcoded paths and exit code 2". "Hardcoded" means not relying on PATH — absolute paths.
   - What's unclear: How does the generator know where `ruff` or `mypy` is installed? `shutil.which("ruff")` resolves from PATH at generation time.
   - Recommendation: Use `shutil.which("ruff")` and `shutil.which("mypy")` at generation time to resolve absolute paths. If a tool is not found, skip its hook with a warning rather than failing generation. Document this behavior.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (already installed) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (exists from Phase 1) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v && uv run ruff check claude_env/ && uv run mypy claude_env/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEN-01 | `.claude/CLAUDE.md` ≤200 lines with required sections | unit (tmp_path write) | `uv run pytest tests/test_generator.py::test_claude_md_line_count -x` | ❌ Wave 0 |
| GEN-01 | `.claude/CLAUDE.md` contains plan→execute→verify, context management, lessons.md loop | unit | `uv run pytest tests/test_generator.py::test_claude_md_content -x` | ❌ Wave 0 |
| GEN-02 | `skills/<slug>/SKILL.md` files have YAML frontmatter and verb-phrase descriptions | unit | `uv run pytest tests/test_generator.py::test_skill_files -x` | ❌ Wave 0 |
| GEN-03 | `agents/<slug>.md` files have non-empty `skills:` list in frontmatter | unit | `uv run pytest tests/test_generator.py::test_agent_skills_field -x` | ❌ Wave 0 |
| GEN-04 | `.claude/settings.json` is valid JSON with hooks and exitCode 2 | unit | `uv run pytest tests/test_generator.py::test_settings_json -x` | ❌ Wave 0 |
| GEN-05 | Generator writes to `global_root/CLAUDE.md`; existing user content preserved | unit (tmp_path) | `uv run pytest tests/test_generator.py::test_global_claude_md -x` | ❌ Wave 0 |
| GEN-06 | Second run produces identical output (idempotency) | unit | `uv run pytest tests/test_generator.py::test_generator_is_idempotent -x` | ❌ Wave 0 |
| GEN-06 | User edits outside sentinel block are preserved on re-run | unit | `uv run pytest tests/test_sentinel.py::test_user_edits_preserved -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v && uv run ruff check claude_env/ && uv run mypy claude_env/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `claude_env/generator/__init__.py` — empty package init
- [ ] `claude_env/generator/generator.py` — Generator class
- [ ] `claude_env/generator/sentinel.py` — merge_sentinel_block, wrap_with_sentinel, has_sentinel
- [ ] `claude_env/generator/content_catalogue.py` — enrich_artifact_context + catalogues
- [ ] `templates/settings_json.j2` (or pure-Python builder in generator) — for GEN-04
- [ ] Expand `templates/claude_md_project.j2` — add real section content for plan→execute→verify, context_management, lessons_loop, mobile_first, surgical_changes
- [ ] `tests/test_generator.py` — covers GEN-01 through GEN-06
- [ ] `tests/test_sentinel.py` — covers merge_sentinel_block edge cases
- [ ] `tests/fixtures/plans/web_plan.py` or `conftest.py` fixture — reusable GenerationPlan for tests

---

## Sources

### Primary (HIGH confidence)

- `/home/manuel/Desktop/PROJECTS/claude-env-2/templates/skill_stub.j2` — actual template variable requirements
- `/home/manuel/Desktop/PROJECTS/claude-env-2/templates/agent_stub.j2` — actual template variable requirements
- `/home/manuel/Desktop/PROJECTS/claude-env-2/templates/claude_md_project.j2` — current stub, confirmed needs expansion
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/pipeline/environment_planner.py` — confirmed planner context keys per artifact
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/models/generation_plan.py` — locked data contract
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/profiles/web.yaml` — confirmed section IDs and slug lists
- `~/.claude/settings.json` — real Claude Code settings.json format, hooks structure with `exitCode` field

### Secondary (MEDIUM confidence)

- Claude Code docs (inferred from real settings.json): `exitCode: 2` is the blocking hook convention; `PostToolUse` is the standard lifecycle event for lint hooks

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; all required libraries already installed and locked
- Architecture: HIGH — derived directly from existing code contracts (templates, planner output, models)
- Context shape gap: HIGH — verified by reading actual `.j2` files vs actual planner context injection
- Sentinel pattern: HIGH — well-established pattern; implementation is stdlib str operations
- settings.json format: HIGH — read from real `~/.claude/settings.json`
- Pitfalls: HIGH — all derived from concrete code analysis, not speculation

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (stable Python ecosystem; Claude Code settings.json format may change — verify against docs at implementation time)
