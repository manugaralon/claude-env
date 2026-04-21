# claude-env

Generate calibrated Claude Code environments from project specs.

`claude-env` writes a `.claude/` layer for any project — CLAUDE.md, skills, agents, and settings — so every Claude Code session starts with the right conventions for your stack.

## Install

```bash
uv tool install git+https://github.com/manugaralon/claude-env
```

## Quick start

**Bootstrap a project** (no API key needed):

```bash
cd your-project
claude-env bootstrap --description "a FastAPI backend for a todo app"
```

**Dry-run first** to preview what will be written:

```bash
claude-env bootstrap --description "a FastAPI backend for a todo app" --dry-run
```

**Use a spec file** for precise control:

```bash
claude-env bootstrap --spec spec.yaml
```

**Global setup** — writes a `~/.claude/` baseline and installs the `/claude-env` skill in Claude Code:

```bash
claude-env setup
```

## From Claude Code

After running `claude-env setup`, type `/claude-env` in any Claude Code session to bootstrap the current project interactively.

## What gets generated

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Project conventions (plan→execute→verify workflow, context management) |
| `.claude/skills/fix-issue/SKILL.md` | `/fix-issue` skill |
| `.claude/skills/create-pr/SKILL.md` | `/create-pr` skill |
| `.claude/skills/run-lint/SKILL.md` | `/run-lint` skill |
| `.claude/agents/code-reviewer.md` | Code review subagent |
| `.claude/agents/security-reviewer.md` | Security review subagent |

## Spec file format

```yaml
name: my-project
description: A Python CLI tool for reviewing code
languages: [python]
tech_stack: [typer, rich, pytest]
```

Or Markdown:

```markdown
# My Project

A Python CLI tool for reviewing code.

**Stack:** Python, Typer, Rich, pytest
```

## CLI reference

```
claude-env setup                          Global onboarding wizard
claude-env bootstrap [DIR]                Generate .claude/ for a project
  --description, -d TEXT                  One-line description (no API key needed)
  --spec, -s PATH                         YAML or Markdown spec file
  --dry-run                               Preview files without writing
claude-env version                        Print version
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- `ANTHROPIC_API_KEY` — only required when using the interactive freeform description prompt (not needed with `--description` or `--spec`)

## License

MIT
