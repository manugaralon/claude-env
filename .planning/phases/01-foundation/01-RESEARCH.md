# Phase 1: Foundation - Research

**Researched:** 2026-04-16
**Domain:** Python project scaffolding — uv, pyproject.toml, Jinja2 template registry, Pydantic v2 schema, ruff/mypy zero-error baseline
**Confidence:** HIGH

---

## Summary

Phase 1 is pure infrastructure: no domain classification logic, no LLM calls, no file generation for target projects. The deliverables are (1) a working Python package installable via `uv sync`, (2) a Jinja2-based template registry that renders templates by name given a context dict, (3) Pydantic v2 schema for `DomainProfile` loadable from YAML, and (4) ruff + mypy passing clean on the initial codebase.

The critical decision to finalize in this phase is the domain profile YAML schema. STATE.md flags it explicitly: "core data contract, must be finalized in Phase 1." Everything downstream — the Domain Classifier (Phase 2), the Environment Planner (Phase 2), and the Generator (Phase 3) — takes `DomainProfile` as input. If the schema drifts after Phase 1, downstream components break. The schema must be written, validated with Pydantic v2, and frozen before Phase 1 is marked complete.

The prior domain research (STACK.md, ARCHITECTURE.md, SUMMARY.md) is thorough and locks the stack. Phase 1 research focuses on the specifics that research didn't yet nail down: exact pyproject.toml structure for uv, the right Jinja2 initialization pattern for a `templates/` directory, the Pydantic v2 model design for `DomainProfile`, and the minimal ruff + mypy config that satisfies the "zero errors" success criterion without over-constraining later phases.

**Primary recommendation:** Write `DomainProfile` schema first, wire `uv`/`pyproject.toml` second, implement the template registry third, configure ruff/mypy last — in that order, because `DomainProfile` is the highest-risk deliverable with downstream coupling.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12.3 | Runtime | Project constraint; 3.12 gives `tomllib` stdlib, better error messages |
| uv | 0.10.8 | Package manager + build | Replaces pip/Poetry; `uv sync` is single setup step; used in Manuel's stack |
| Pydantic | 2.13.1 | Schema validation for `DomainProfile`, `ProjectSpec` | Stack constraint; v2 `model_validate()` from dict covers YAML-loaded data directly |
| Jinja2 | 3.1.6 | Template rendering | Stack decision locked; `Environment` + `FileSystemLoader` for `templates/` directory |
| PyYAML | 6.0.3 | Load domain profile YAML files | SKILL.md and agent frontmatter are YAML; input specs may be YAML |

### Dev / Quality

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 | Test runner | All tests; `uv run pytest` from project root |
| ruff | 0.15.10 | Linter + formatter | Replaces flake8 + black + isort; single binary, fast |
| mypy | 1.20.1 | Static type checker | Enforced from Phase 1 so later phases don't accumulate type debt |

### Alternatives Already Ruled Out

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 | f-strings / string.Template | No conditionals, no loops — unworkable at 5+ templates |
| uv | Poetry, pip+setuptools | Legacy or heavier; uv is the 2025/2026 standard |
| Pydantic v2 | dataclasses | No field validation, no `model_validate()` from dict |

**Installation:**

```bash
uv init claude-env-2
uv add pydantic pyyaml jinja2
uv add --dev pytest ruff mypy
```

**pyproject.toml entry point (add after `uv init`):**

```toml
[project.scripts]
claude-env = "claude_env.cli:app"
```

**Version verification (confirmed 2026-04-16 via pip index):**
- pydantic: 2.13.1
- jinja2: 3.1.6
- pyyaml: 6.0.3
- ruff: 0.15.10
- mypy: 1.20.1
- pytest: 9.0.3

---

## Architecture Patterns

### Recommended Project Structure

```
claude_env/
├── __init__.py
├── cli.py               # Typer app (stub in Phase 1)
├── models/
│   ├── __init__.py
│   └── domain_profile.py  # DomainProfile Pydantic model
├── templates/
│   ├── __init__.py
│   └── registry.py        # TemplateRegistry class
└── profiles/
    ├── web.yaml
    ├── cli.yaml
    ├── data.yaml
    └── infra.yaml
tests/
├── __init__.py
├── test_domain_profile.py
└── test_template_registry.py
templates/                 # Jinja2 template files (not Python package)
    ├── claude_md_project.j2
    ├── skill_stub.j2
    └── agent_stub.j2
pyproject.toml
```

### Pattern 1: Jinja2 Template Registry

**What:** A class that wraps `jinja2.Environment` with `FileSystemLoader` pointing at the `templates/` directory. Exposes `render(template_id: str, context: dict) -> str`.

**When to use:** Any time a template name and context dict must produce a rendered string. This is the only rendering path — nothing else calls Jinja2 directly.

**Example:**

```python
# Source: Jinja2 official docs — Environment + FileSystemLoader
from pathlib import Path
import jinja2

class TemplateRegistry:
    def __init__(self, templates_dir: Path) -> None:
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            autoescape=False,          # Output is markdown/text, not HTML
            undefined=jinja2.StrictUndefined,  # Fail fast on missing vars
            keep_trailing_newline=True,
        )

    def render(self, template_id: str, context: dict) -> str:
        template = self._env.get_template(template_id)
        return template.render(**context)
```

Key setting: `StrictUndefined` causes rendering to raise `UndefinedError` immediately if a context variable is missing. Default `Undefined` silently produces empty strings — this hides bugs in template/context mismatches.

### Pattern 2: DomainProfile Pydantic v2 Model

**What:** A Pydantic v2 `BaseModel` that validates a domain profile YAML file. `model_validate()` is called with the dict produced by `yaml.safe_load()`.

**When to use:** Loading any `.yaml` profile from `claude_env/profiles/`. Validation runs at load time, not at use time.

**DomainProfile schema (to finalize in Phase 1):**

```python
# Source: Pydantic v2 docs — model_validate from dict
from pydantic import BaseModel, Field

class DomainProfile(BaseModel):
    domain: str                          # Canonical name: "web", "cli", "data", "infra"
    display_name: str                    # Human label: "Web Application"
    description: str                     # One-line description for generated comments
    skill_slugs: list[str]               # 3-5 skill names to generate
    agent_slugs: list[str]               # 2-3 agent names to generate
    claude_md_sections: list[str]        # Section IDs to include in generated CLAUDE.md
    hook_templates: list[str]            # Hook template IDs for settings.json
    detection_signals: list[str]         # File/pattern signals for domain auto-detection
```

**Loading pattern:**

```python
import yaml
from pathlib import Path
from claude_env.models.domain_profile import DomainProfile

def load_profile(path: Path) -> DomainProfile:
    raw = yaml.safe_load(path.read_text())
    return DomainProfile.model_validate(raw)
```

**Example profile YAML (web.yaml):**

```yaml
domain: web
display_name: Web Application
description: Frontend or fullstack web project with browser-facing UI
skill_slugs:
  - fix-issue
  - create-pr
  - run-lint
  - update-deps
agent_slugs:
  - security-reviewer
  - accessibility-auditor
claude_md_sections:
  - mobile_first
  - plan_execute_verify
  - context_management
  - lessons_loop
hook_templates:
  - lint_after_edit
  - typecheck_after_edit
detection_signals:
  - package.json
  - index.html
  - src/App.tsx
  - src/main.tsx
```

### Pattern 3: pyproject.toml for uv

**What:** Complete pyproject.toml that `uv sync` resolves cleanly with no manual steps.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claude-env"
version = "0.1.0"
description = "Generate calibrated Claude Code environments from project specs"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.13",
    "pyyaml>=6.0",
    "jinja2>=3.1",
    "typer>=0.24",
    "rich>=14.0",
]

[project.scripts]
claude-env = "claude_env.cli:app"

[dependency-groups]
dev = [
    "pytest>=9.0",
    "ruff>=0.15",
    "mypy>=1.20",
    "types-pyyaml",   # mypy stubs for PyYAML
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]   # pycodestyle, pyflakes, isort, pyupgrade

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = false
```

Note: `types-pyyaml` is the mypy stub package for PyYAML. Without it, `mypy --strict` fails on `import yaml`. Jinja2 ships its own stubs. Pydantic v2 ships its own stubs. These require no extra packages.

Note: `hatchling` is uv's default build backend for pure Python projects — no configuration needed beyond `[build-system]`.

### Pattern 4: ruff + mypy zero-error baseline

**What:** Config that passes clean on an initial codebase without blocking legitimate patterns used later.

**Ruff:** `select = ["E", "F", "I", "UP"]` covers errors (E), undefined names / unused imports (F), import ordering (I), and Python version upgrade hints (UP). Avoids `ANN` (annotation rules) which would enforce docstring annotations — those are covered by mypy strict mode instead.

**mypy:** `strict = true` enables: `--disallow-untyped-defs`, `--disallow-any-generics`, `--warn-return-any`, `--warn-unused-ignores`, and more. For Phase 1 this is achievable because the codebase is small and clean. The payoff is that later phases cannot introduce untyped functions without mypy catching it.

**CI check commands:**

```bash
uv run ruff check claude_env/ tests/
uv run mypy claude_env/
```

### Anti-Patterns to Avoid

- **Jinja2 with `Undefined` (default):** Missing template variables render as empty strings silently. Use `StrictUndefined`.
- **`yaml.load()` without Loader:** `yaml.safe_load()` only. `yaml.load()` executes arbitrary Python and will trigger a security warning from PyYAML.
- **Putting templates inside the Python package directory:** Jinja2 `FileSystemLoader` needs a plain directory path, not a Python package. Keep `templates/` at project root, separate from `claude_env/`.
- **mypy `ignore_missing_imports = true`:** Hides real missing stub issues. Add `types-pyyaml` instead so stubs are present.
- **Skipping `__init__.py` in `models/` and `templates/`:** mypy strict mode needs proper package structure to resolve imports. All directories that are Python packages need `__init__.py`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing and validation | Custom YAML parser + manual field checks | `yaml.safe_load()` + Pydantic `model_validate()` | Edge cases: type coercion, missing fields, extra fields, nested structures |
| Template variable injection | f-strings or `str.replace()` | Jinja2 | No conditionals, no loops, no whitespace control in f-strings |
| Python packaging config | `setup.py` + `requirements.txt` | `pyproject.toml` + uv | Legacy toolchain; uv makes lockfile management automatic |
| Type checking | Runtime `isinstance()` guards | mypy + Pydantic | Static analysis catches errors before runtime |
| Import sorting | Manual import ordering | ruff `I` ruleset | Diff noise, merge conflicts, inconsistency — automated is the only sustainable approach |

**Key insight:** Every item in this list looks simple to hand-roll for the first use case. Each one has edge cases that compound as the codebase grows. The libraries exist precisely because the naive implementation breaks in production.

---

## Common Pitfalls

### Pitfall 1: DomainProfile Schema Drift

**What goes wrong:** Phase 1 defines a minimal `DomainProfile`. Phase 2 (Domain Classifier) and Phase 3 (Generator) add fields directly without updating the Pydantic model. Model validation stops catching malformed profiles. Downstream code does `.get()` on raw dicts instead of using typed attributes.

**Why it happens:** It's faster to add a field to a YAML file than to update the Pydantic model. The gap opens gradually.

**How to avoid:** `DomainProfile` is frozen after Phase 1. Any field added in later phases requires a model update first, not a raw dict access. Pydantic v2 `model_config = ConfigDict(extra="forbid")` makes extra YAML fields a validation error — catches drift immediately.

**Warning signs:** Code using `profile.get("field")` or `profile["field"]` instead of `profile.field`. YAML files with fields not in the Pydantic model.

### Pitfall 2: Template File Not Found at Runtime

**What goes wrong:** `TemplateRegistry.render("claude_md_project.j2", ctx)` raises `TemplateNotFound`. The template file exists but the `FileSystemLoader` path is wrong — relative path resolved from the wrong working directory.

**Why it happens:** `FileSystemLoader(str(templates_dir))` uses whatever `templates_dir` is at construction time. If constructed with a relative path (e.g., `Path("templates")`), resolution depends on `cwd()` at invocation time.

**How to avoid:** Always construct the `TemplateRegistry` with an absolute path. Derive it from `__file__` of the registry module or accept it as a constructor argument and assert `templates_dir.is_absolute()`.

```python
# Safe: derive absolute path from module location
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
```

**Warning signs:** Tests pass when run from project root, fail when run from a different directory.

### Pitfall 3: mypy strict fails on PyYAML imports

**What goes wrong:** `mypy --strict` reports `error: Skipping analyzing "yaml": module is installed, but missing library stubs or py.typed marker`. All YAML-loading code is flagged.

**Why it happens:** PyYAML does not ship mypy stubs. `mypy --strict` with `ignore_missing_imports = false` treats this as an error.

**How to avoid:** Add `types-pyyaml` to dev dependencies. One package, zero config, resolves all yaml stubs.

**Warning signs:** Running `uv run mypy claude_env/` produces stub-related errors only for yaml imports.

### Pitfall 4: ruff and mypy config in wrong file

**What goes wrong:** `ruff check` ignores config because `[tool.ruff]` is in a separate `ruff.toml` file rather than `pyproject.toml`, or vice versa. Config appears to be set but doesn't apply.

**Why it happens:** Both ruff and mypy support multiple config file locations with precedence rules. When multiple files exist, the wrong one wins.

**How to avoid:** Put all tool config in `pyproject.toml`. No `ruff.toml`, no `.mypy.ini`, no `setup.cfg`. One file is the source of truth.

### Pitfall 5: Jinja2 template whitespace producing malformed YAML output

**What goes wrong:** Templates for SKILL.md frontmatter (which is YAML) contain Jinja2 block tags (`{% if %}`, `{% for %}`) that introduce extra blank lines. The rendered output is structurally invalid YAML.

**Why it happens:** Jinja2's default whitespace behavior preserves newlines around block tags. A `{% for %}` loop produces a blank line for the tag itself plus the loop content.

**How to avoid:** Use Jinja2 whitespace control: `{%- if condition %}` (dash strips preceding whitespace) and `{% endif -%}` (dash strips trailing whitespace). Address this in template authoring, not in post-processing.

---

## Code Examples

### Template Registry (complete, Phase 1 deliverable)

```python
# claude_env/templates/registry.py
from pathlib import Path
import jinja2

class TemplateRegistry:
    def __init__(self, templates_dir: Path) -> None:
        if not templates_dir.is_absolute():
            raise ValueError(f"templates_dir must be absolute, got: {templates_dir}")
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            autoescape=False,
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )

    def render(self, template_id: str, context: dict[str, object]) -> str:
        template = self._env.get_template(template_id)
        return template.render(**context)

    def list_templates(self) -> list[str]:
        return self._env.list_templates()
```

### DomainProfile model (complete, Phase 1 deliverable)

```python
# claude_env/models/domain_profile.py
from pathlib import Path
import yaml
from pydantic import BaseModel, ConfigDict

class DomainProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: str
    display_name: str
    description: str
    skill_slugs: list[str]
    agent_slugs: list[str]
    claude_md_sections: list[str]
    hook_templates: list[str]
    detection_signals: list[str]

def load_profile(path: Path) -> DomainProfile:
    raw = yaml.safe_load(path.read_text())
    return DomainProfile.model_validate(raw)
```

### Minimal test for template registry

```python
# tests/test_template_registry.py
from pathlib import Path
import pytest
from claude_env.templates.registry import TemplateRegistry

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "templates"

def test_render_resolves_by_name(tmp_path: Path) -> None:
    (tmp_path / "hello.j2").write_text("Hello {{ name }}!")
    registry = TemplateRegistry(templates_dir=tmp_path)
    result = registry.render("hello.j2", {"name": "world"})
    assert result == "Hello world!"

def test_render_raises_on_missing_variable(tmp_path: Path) -> None:
    (tmp_path / "greet.j2").write_text("Hi {{ missing_var }}")
    registry = TemplateRegistry(templates_dir=tmp_path)
    with pytest.raises(Exception):  # jinja2.UndefinedError
        registry.render("greet.j2", {})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + `requirements.txt` | `pyproject.toml` + uv | 2023-2024 (PEP 517/518 + uv release) | Single source of truth; `uv sync` replaces manual pip steps |
| `pip install -e .` for dev | `uv sync` + `uv run` | 2024-2025 | No global environment pollution; lockfile is automatic |
| flake8 + black + isort (3 tools) | ruff (1 tool) | 2023+ | Same rules, 10-100x faster, single config section |
| mypy `ignore_missing_imports = true` | `types-*` stub packages | Ongoing | Stubs available for most major packages; `ignore_missing_imports` is now a crutch |
| Jinja2 `Undefined` (default) | `StrictUndefined` | Always available, underused | Strict mode is unambiguously correct for config/template generation |

**Deprecated/outdated:**

- `setup.cfg`: Replaced by `pyproject.toml`. Don't create it.
- `.flake8` config file: Replaced by `[tool.ruff]` in `pyproject.toml`.
- `Pipfile` / `Pipfile.lock`: Replaced by uv lockfile. Don't create it.

---

## Open Questions

1. **DomainProfile: `detection_signals` field scope**
   - What we know: Domain Classifier (Phase 2) uses signals to map a project to a domain. Phase 1 only needs the schema valid and loadable.
   - What's unclear: Signals are file patterns — should they be glob strings (`"src/App.tsx"`), or more structured (`{type: "file", pattern: "*.tsx"}`)?
   - Recommendation: Use flat strings in Phase 1. The Classifier can interpret them. Avoid premature structure.

2. **`claude_md_sections` field: IDs or full content?**
   - What we know: The Generator (Phase 3) uses these to select which CLAUDE.md sections to include in output.
   - What's unclear: Are these IDs referencing Jinja2 template blocks, or standalone `.j2` files?
   - Recommendation: Treat them as Jinja2 template IDs (filenames in `templates/`) from Phase 1. The Generator will resolve them. Document this contract in a comment in the model.

3. **Number of v1 domain profiles**
   - What we know: Roadmap says "web, CLI, data, and infra" — four profiles.
   - What's unclear: "General" was mentioned in REQUIREMENTS.md as a fifth domain. Is it a real profile or a fallback?
   - Recommendation: Create four concrete profiles (web, cli, data, infra) and a `general.yaml` fallback profile with minimal content. The classifier falls back to `general` when no domain is detected.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — created in Wave 0 |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map

Phase 1 has no direct v1 requirement IDs. Success criteria map to tests as follows:

| Success Criterion | Behavior | Test Type | Automated Command | File Exists? |
|------------------|----------|-----------|-------------------|--------------|
| SC-1: `uv sync` installs cleanly | `uv sync` exits 0 | smoke | `uv sync` | ❌ Wave 0 (manual verification) |
| SC-2: Template registry resolves and renders | `render("x.j2", ctx)` returns rendered string | unit | `uv run pytest tests/test_template_registry.py -x` | ❌ Wave 0 |
| SC-3: Domain profiles loadable and schema-valid | `load_profile(path)` returns `DomainProfile` without error | unit | `uv run pytest tests/test_domain_profile.py -x` | ❌ Wave 0 |
| SC-4: ruff and mypy pass with zero errors | Both tools exit 0 | static | `uv run ruff check claude_env/ && uv run mypy claude_env/` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v && uv run ruff check claude_env/ && uv run mypy claude_env/`
- **Phase gate:** Full suite + ruff + mypy all green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_template_registry.py` — covers SC-2 (render by name, missing variable raises)
- [ ] `tests/test_domain_profile.py` — covers SC-3 (valid YAML loads, invalid YAML raises, extra fields raise)
- [ ] `tests/fixtures/` — sample `.j2` templates and YAML profiles for test fixtures
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` section — testpaths, addopts
- [ ] `pyproject.toml` `[tool.mypy]` section with `strict = true`
- [ ] `pyproject.toml` `[tool.ruff]` section
- [ ] Framework install: `uv add --dev pytest ruff mypy types-pyyaml`

---

## Sources

### Primary (HIGH confidence)

- Jinja2 official docs — `Environment`, `FileSystemLoader`, `StrictUndefined`, whitespace control
- Pydantic v2 docs — `model_validate()`, `ConfigDict(extra="forbid")`
- uv official docs (astral.sh) — `uv sync`, `pyproject.toml`, `hatchling` backend, `dependency-groups`
- Project prior research: `.planning/research/STACK.md` (verified stack, versions, rationale)
- Project prior research: `.planning/research/ARCHITECTURE.md` (component design, build order)

### Secondary (MEDIUM confidence)

- pip index (verified 2026-04-16): ruff 0.15.10, mypy 1.20.1, pydantic 2.13.1, jinja2 3.1.6, pyyaml 6.0.3, pytest 9.0.3

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all versions verified via pip index on 2026-04-16; prior research verified via PyPI
- Architecture: HIGH — `DomainProfile` schema, `TemplateRegistry` pattern, pyproject.toml structure all derived from official docs
- Pitfalls: HIGH — `StrictUndefined`, `extra="forbid"`, `types-pyyaml` are concrete and verifiable; schema drift pitfall is structural reasoning from component coupling

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (stable ecosystem; uv versions update frequently but pyproject.toml format is stable)
