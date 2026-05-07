# claude-env

Generate calibrated Claude Code environments from project specs.

`claude-env` writes a `.claude/` layer for any project — CLAUDE.md, skills, agents, settings, plus a `CONTEXT.md` and `docs/adr/` scaffold — so every Claude Code session starts with the right conventions for your stack.

---

## Onboarding

### What you get

When you run `claude-env bootstrap` in a project, you get a configured `.claude/` layer plus root-level domain artifacts:

| Artifact | Purpose |
|---|---|
| `.claude/CLAUDE.md` | Project conventions per profile (think→plan→execute→verify, context management, Karpathy's 4 principles) |
| `.claude/skills/<name>/SKILL.md` | Profile-appropriate skills with explicit `MANDATORY TRIGGERS / STRONG TRIGGERS / SKIP` frontmatter so they auto-fire when relevant |
| `.claude/agents/<name>.md` | Subagents (security-reviewer, advisor, profile-specific reviewers) |
| `CONTEXT.md` | Domain glossary scaffold — defines the project's ubiquitous language. Populate via the `grill-with-docs` skill as decisions crystallize. |
| `docs/adr/README.md` | Architecture Decision Record format reference + when-to-use rules. Numbered ADRs (`0001-slug.md`, `0002-slug.md`) created lazily as decisions arise. |

### Profiles auto-detected

Filesystem signals decide which profile applies:

| Profile | Signals |
|---|---|
| `web` | `package.json`, `index.html`, `tailwind.config.js`, React/Vite/Next entry files |
| `cli` | `pyproject.toml` + `cli.py` / `main.py` / `bin/` |
| `data` | Notebooks, parquet, ML config |
| `infra` | `terraform/`, k8s manifests |
| `general` | Fallback when no signal matches |

Override with `--domain-hint web` if detection misses.

### How to use it

```bash
# Install
uv tool install git+https://github.com/manugaralon/claude-env

# Bootstrap a new project — dry-run first to preview
cd your-project
claude-env bootstrap --description "FastAPI todo backend" --dry-run
claude-env bootstrap --description "FastAPI todo backend"

# Or with a YAML spec (no LLM call needed, deterministic)
claude-env bootstrap --spec spec.yaml

# Global setup — writes ~/.claude/ baseline and installs the /claude-env skill
claude-env setup
```

### Opt-in integrations (bootstrap flags)

```bash
# Project-scoped MCPs — write .mcp.json at the project root
claude-env bootstrap --spec spec.yaml \
  --with-browser              `# playwright MCP` \
  --with-context7             `# upstash/context7 MCP` \
  --with-sequential-thinking  `# sequential-thinking MCP`

# Plugins (not MCPs) — print install hint, no file written
claude-env bootstrap --spec spec.yaml --with-claude-mem

# Quality-gate-precommit hook — emits the .claude/quality-gate-precommit
# marker that opts this project into the global hook at
# ~/.claude/hooks/quality-gate-precommit.sh (lint + secrets on every commit)
claude-env bootstrap --spec spec.yaml --with-quality-gate-precommit
```

### From Claude Code

After running `claude-env setup`, type `/claude-env` in any Claude Code session to bootstrap the current project interactively.

### Spec file format

```yaml
name: my-project
description: A Python CLI tool for reviewing code
languages: [python]
tech_stack: [typer, rich, pytest]
```

Markdown specs also work — `name` from the H1, `description` from the first paragraph, `tech_stack` parsed from a `**Stack:**` line.

### CLI reference

```
claude-env setup                          Global onboarding wizard
claude-env bootstrap [DIR]                Generate .claude/ for a project
  --description, -d TEXT                  One-line description (no API key needed)
  --spec, -s PATH                         YAML or Markdown spec file
  --dry-run                               Preview files without writing
  --with-browser                          Add playwright MCP to .mcp.json
  --with-context7                         Add context7 MCP to .mcp.json
  --with-sequential-thinking              Add sequential-thinking MCP to .mcp.json
  --with-claude-mem                       Print install hint for the plugin
  --with-quality-gate-precommit           Enable lint+secrets pre-commit hook
claude-env audit [DIR]                    Audit a generated .claude/ (exit 1 on FAIL)
claude-env version                        Print version
```

---

## Internal stack

### Pipeline

`claude-env` is a Python 3.12+ CLI built on Pydantic v2 + Jinja2 + Typer. The bootstrap pipeline is pure data transformation with file I/O isolated to the final stage:

```
ProjectSpec (input)                      models/project_spec.py
   │
   ▼ pipeline/input_normalizer.py        (raw description → ProjectSpec; LLM only when no --description / --spec)
   │
DomainProfile                            profiles/<domain>.yaml + classifier.py
   │
   ▼ pipeline/environment_planner.py     (pure: ProjectSpec + DomainProfile → GenerationPlan)
   │
GenerationPlan (list of Artifacts)
   │
   ▼ generator/generator.py              (writes files, sentinel-protected, idempotent)
   │
.claude/ layer + CONTEXT.md + docs/adr/README.md
```

Pure-data planning means tests don't need a filesystem to validate plan correctness — `test_environment_planner.py` exercises `plan()` against profile YAMLs directly.

### Layout

```
claude_env/
├── models/          # Pydantic v2 schemas (extra="forbid", strict types)
│   ├── project_spec.py
│   ├── domain_profile.py
│   └── generation_plan.py
├── pipeline/        # Pure transformation, no I/O
│   ├── input_normalizer.py    # raw → ProjectSpec
│   ├── domain_classifier.py   # filesystem signals → DomainProfile
│   ├── environment_planner.py # → GenerationPlan
│   └── spec_parser.py
├── generator/       # File I/O + idempotency
│   ├── generator.py           # writes artifacts with sentinel headers
│   ├── content_catalogue.py   # _SKILL_CATALOGUE: per-skill metadata + triggers
│   └── sentinel.py            # protects user-edited files from re-writes
├── templates/       # Jinja2 facade
│   └── registry.py            # StrictUndefined + autoescape=False
├── data/            # *.j2 templates (the canonical templates dir)
└── profiles/        # *.yaml domain profiles
```

### Skill frontmatter contract

Every generated SKILL.md follows this pattern:

```yaml
---
name: skill-slug
description: >-
  One-line summary of what the skill does.
  MANDATORY TRIGGERS: '/skill-slug', 'natural phrase', 'another natural phrase'.
  STRONG TRIGGERS: contextual situations where the skill should auto-fire.
  SKIP: do NOT trigger on cases that look similar but aren't.
allowed-tools: Bash, Read, Edit, Write
---
```

The `TRIGGER` / `SKIP` pattern is the antidote to "the skill exists but Claude doesn't invoke it." `_SKILL_CATALOGUE` in `generator/content_catalogue.py` declares triggers per skill; `data/skill_stub.j2` renders them via Jinja2 conditionals.

### Idempotent re-runs

The generator writes a sentinel comment on each managed file. Re-running `claude-env bootstrap` updates managed files without clobbering user edits to non-managed files. See `generator/sentinel.py`.

### Probation & telemetry (post-2026-05-07 batch)

The 2026-05-07 batch (5 commits) shipped substantial new infrastructure (skill catalogue extension, evaluation registry, audit script, ADR-0001) on **30-day probation** — see `NOTICE-30-day-probation.md`. Skill invocations are logged by `~/.claude/hooks/skill-usage-log.sh` (PostToolUse with `Skill` matcher). Items with <3 invocations after 30 days are candidates for deletion or quarantine. **Data > intent.**

Run on 2026-06-07:

```bash
bash ~/.claude/scripts/skill-usage-report.sh
```

### Architectural decisions

See `docs/adr/`:

- **ADR-0001** (`0001-keep-python-cli-architecture.md`) — kept Python+Jinja2+Pydantic+Typer; rejected the bash+YAML manifest alternative. Rationale: validation maturity, test infrastructure, conditional template logic, idempotent re-runs are well-served by Python; bash equivalent would be more fragile at similar LOC.

### Tests

```bash
pytest tests/   # 107/107 expected
```

Tests live next to code at ~1:1 LOC ratio. `conftest.py` `real_registry` fixture uses `claude_env/data/` as canonical templates dir. `test_skill_frontmatter` handles both inline and folded-scalar (`>-`) YAML descriptions for the multi-line trigger pattern.

### Evaluations registry (subsystem 13)

`EVALUATIONS.md` at the repo root tracks every external source considered for integration (repos, MCPs, posts, videos) with verdict vocabulary: `integrate`, `cherry-pick`, `skip`, `research-only`, `reconsider`, `queued`. Deep evaluations of frameworks studied during integration live in `evaluations/`:

- `evaluations/anthropics-skills.md` — Anthropic's official skills repo (288 lines)
- `evaluations/obra-superpowers.md` — Jesse Vincent's superpowers (740 lines)
- `evaluations/affaan-m-everything-claude-code.md` — ECC harness (539 lines)

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- `ANTHROPIC_API_KEY` — only required when using the interactive freeform description prompt (not needed with `--description` or `--spec`)

## License

MIT
