# Stack Research

**Project:** claude-env-2 — Claude environment generator
**Researched:** 2026-04-15
**Mode:** Ecosystem (What's the right stack for this CLI tool?)

---

## Recommended Stack

### CLI Framework

- **Typer** v0.24.1 — primary CLI interface
  - Confidence: HIGH (verified via PyPI, released 2026-02-21)
  - Rationale: Type-hint-driven API eliminates boilerplate. Auto-generates help text, completions, and error messages. Rich integration built-in (`typer.Typer(rich_markup_mode='rich')`). Stack-consistent with Python 3.12+/Pydantic v2 project. CLI surface is small (generate, validate, init wizard) — Typer's opinionated structure prevents scope creep.
  - Alternative considered: Click v8.x — battle-tested and 38.7% ecosystem share as of 2025, but decorator-based syntax is more verbose. No benefit over Typer for a new single-developer tool.
  - Alternative considered: argparse (stdlib) — rejected. No automatic help formatting, no type coercion, significantly more boilerplate for subcommands.

### Terminal Output

- **Rich** v14.x — colored output, panels, progress, tables
  - Confidence: HIGH (verified via readthedocs.io, current stable 14.1.0+)
  - Rationale: Typer integrates with Rich natively. Wizard-style onboarding (the `setup.sh`-style init command) needs visual feedback. File generation confirmation with per-file status is a natural use case for Rich panels. Zero friction — Typer pulls it in.
  - Alternative considered: colorama — primitive (ANSI escape sequences only), no structured output.

### Templating Engine

- **Jinja2** v3.1.6 — generates CLAUDE.md, SKILL.md, agent .md, hooks JSON
  - Confidence: HIGH (verified via PyPI, released 2025-03-05)
  - Rationale: The output artifacts are text files with variable interpolation, conditional sections (e.g., include Python-specific rules only for Python projects), and loops (e.g., emit one subagent block per detected domain). Jinja2 covers all three naturally. Its `Environment` + `FileSystemLoader` pattern fits a `templates/` directory in the project. Used by Ansible, Flask, and similar config-generation tools for exactly this use case.
  - Alternative considered: Python f-strings / string.Template — insufficient. No conditionals, no loops, no template inheritance, no whitespace control. Unmaintainable at 5+ templates.
  - Alternative considered: Mako — more powerful, but Jinja2 is the ecosystem standard and its sandbox mode matters if templates ever become user-supplied.
  - Alternative considered: Cookiecutter — wrong layer. Cookiecutter is a project-scaffolding CLI, not a library. We need programmatic template rendering with runtime context from project analysis; Cookiecutter assumes static interactive prompts.

### Data Modeling and Validation

- **Pydantic** v2.x — project definition schema, generator config, output manifest
  - Confidence: HIGH (stack constraint from PROJECT.md, consistent with Manuel's standard stack)
  - Rationale: The input to the generator (raw idea or structured spec) needs a validated schema. The output manifest (which files were generated, to which paths) benefits from typed models. Pydantic v2's `model_validate()` from dict/JSON/YAML is the standard pattern for this. Field-level validation catches bad inputs early (e.g., project name with invalid characters).
  - Alternative considered: dataclasses — no validation, no serialization helpers, no `.model_dump()` for output.

### YAML / TOML Parsing

- **PyYAML** v6.x — parse structured spec inputs
  - Confidence: MEDIUM (standard library companion, widely used; no version verification done beyond ecosystem knowledge)
  - Rationale: Input specs may arrive as YAML files. SKILL.md and agent frontmatter the generator writes is YAML. PyYAML is the de-facto standard; no alternative needed. For writing YAML output specifically, use `yaml.dump()` with `default_flow_style=False` and `allow_unicode=True`.
  - Note: Python 3.11+ includes `tomllib` (stdlib) for TOML reading if TOML inputs are ever needed — no extra dep.

### Packaging

- **uv** — package manager + build tool
  - Confidence: HIGH (verified via astral.sh docs and ecosystem signals; uv is dominant in 2025/2026 Python tooling)
  - Rationale: `pyproject.toml` as single source of truth. `uv sync` is the only setup step needed. `uv run` allows invocation without global install. The `[project.scripts]` entry point makes the CLI installable as `claude-env`. No `requirements.txt`, no `setup.py`, no `setup.cfg`. `uv_build` as backend for pure-Python project — zero config.
  - Alternative considered: Poetry — slower, heavier, slightly different lockfile semantics. uv supersedes it for new projects in 2025.
  - Alternative considered: pip + setuptools — legacy; requires separate lockfile management.

---

## Claude Code Output Artifacts — Exact Formats

This section documents the exact file formats the generator must produce. This is not a stack choice but a hard constraint from the Claude Code runtime.

### Skills: `.claude/skills/<name>/SKILL.md`

YAML frontmatter + markdown body. Required fields: none (name defaults to directory name, description defaults to first paragraph). Recommended fields:

```yaml
---
name: <slug>                          # lowercase, hyphens, max 64 chars
description: <what it does and when> # max 1024 chars, front-load the use case
disable-model-invocation: true        # for manually-invoked task skills
context: fork                         # to run in isolated subagent context
agent: Explore|Plan|general-purpose   # which subagent type, when context: fork
allowed-tools: Read Grep Bash(git *)  # space-separated or YAML list
effort: low|medium|high|max
---
```

Supporting files live alongside SKILL.md: `scripts/`, `references/`, `assets/`. Reference them from SKILL.md body. Keep SKILL.md body under 500 lines. Use `${CLAUDE_SKILL_DIR}` to reference bundled scripts portably.

Personal skills: `~/.claude/skills/`. Project skills: `.claude/skills/`. Project skills are checked into version control.

### Subagents: `.claude/agents/<name>.md`

Markdown file with YAML frontmatter. Required fields: `name`, `description`. Body becomes the system prompt.

```yaml
---
name: <slug>                          # lowercase, hyphens
description: <when Claude should delegate here>
tools: Read, Grep, Glob, Bash         # allowlist (omit = inherit all)
disallowedTools: Write, Edit          # denylist (alternative to tools)
model: sonnet|opus|haiku|inherit
permissionMode: default|acceptEdits|auto|bypassPermissions
maxTurns: 10
memory: user|project|local
effort: low|medium|high|max
color: red|blue|green|yellow|purple|orange|pink|cyan
---

System prompt markdown body here.
```

Personal subagents: `~/.claude/agents/`. Project subagents: `.claude/agents/`.

### Hooks: `.claude/settings.json`

JSON file at project scope (or `~/.claude/settings.json` for global). Structure:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/script.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "PostToolUse": [...],
    "SessionStart": [...]
  }
}
```

Matcher: exact tool name, `|`-separated list, or JS regex. Hook types: `command`, `http`, `prompt`, `agent`.

### CLAUDE.md: `CLAUDE.md` (project root) or `~/.claude/CLAUDE.md` (global)

Plain markdown. No special format. Quality constraint: must stay under 200 lines.

---

## What NOT to Use

- **Cookiecutter** — wraps the wrong abstraction. It's a user-facing scaffold CLI, not a programmatic rendering library. It would require subprocess calls and can't be controlled from Python code.
- **Copier** — same problem as Cookiecutter. Template updates and migration are useful for framework upgrades, not for a generator that produces a one-shot environment.
- **Mako** — heavier than Jinja2 with no benefit for this use case. Jinja2's sandbox mode is more mature for future extensibility.
- **Click** — redundant with Typer chosen. Typer is built on Click; picking Click directly means writing more code for the same result.
- **argparse** — no type coercion, no auto-help, no subcommand nesting without boilerplate. Not appropriate for a multi-subcommand CLI.
- **TOML for template config** — YAML is already required for SKILL.md and agent frontmatter outputs. Introducing a second config format (TOML) for the generator's own config would be inconsistent with no benefit.
- **setuptools / setup.py / requirements.txt** — legacy. uv + pyproject.toml replaces this entirely.

---

## Installation Baseline

```bash
# Bootstrap
uv init claude-env-2
uv add typer rich jinja2 pydantic pyyaml

# Dev
uv add --dev pytest ruff mypy

# Run
uv run claude-env generate my-project.yaml
# or after install:
claude-env generate my-project.yaml
```

`pyproject.toml` entry point:
```toml
[project.scripts]
claude-env = "claude_env.cli:app"
```

---

## Key Findings

- Typer 0.24.1 (2026-02-21) is the current release; Rich integration is native via `rich_markup_mode='rich'`
- Jinja2 3.1.6 (2025-03-05) is current stable; `FileSystemLoader` + `Environment` is the right pattern for a `templates/` directory
- Claude Code merged `.claude/commands/` into `.claude/skills/` — both work, but skills are the forward path and should be what the generator produces
- Skill frontmatter has 13+ fields; `disable-model-invocation`, `context: fork`, and `allowed-tools` are the most impactful for the generated audit/expert agents
- Subagent `.md` files require only `name` + `description`; the markdown body becomes the system prompt directly
- Hooks live in `.claude/settings.json` (not a separate hooks file) at project scope; they use a three-level nesting: `hooks > EVENT > [{matcher, hooks: [...]}]`
- `uv` is the clear 2025/2026 standard for Python packaging; `uv_build` as backend, `pyproject.toml` as single source of truth
- No external services required — all generation is local file I/O with template rendering; fits the "no external services" constraint perfectly

---

## Sources

- [Typer PyPI](https://pypi.org/project/typer/) — version 0.24.1 confirmed
- [Jinja2 PyPI](https://pypi.org/project/Jinja2/) — version 3.1.6 confirmed
- [Claude Code Skills docs](https://code.claude.com/docs/en/skills) — SKILL.md format, frontmatter fields, directory structure
- [Claude Code Subagents docs](https://code.claude.com/docs/en/sub-agents) — agent .md format, frontmatter fields
- [Claude Code Hooks docs](https://code.claude.com/docs/en/hooks) — settings.json hook schema
- [uv docs](https://docs.astral.sh/uv/) — packaging patterns
- [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — pyproject.toml standard
