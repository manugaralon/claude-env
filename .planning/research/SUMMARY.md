# Research Summary

**Project:** claude-env-2 — Claude Code environment generator  
**Synthesized:** 2026-04-15

---

## Recommended Stack

| Tool | Version | Rationale |
|------|---------|-----------|
| Python | 3.12+ | Stack constraint |
| Typer | 0.24.1 | Type-hint CLI, Rich built-in, zero boilerplate for subcommands |
| Rich | 14.x | Wizard output, per-file status panels — pulled in by Typer automatically |
| Jinja2 | 3.1.6 | Conditionals + loops needed for domain-adaptive templates; f-strings won't scale |
| Pydantic | v2.x | Validated `ProjectSpec` and `GenerationPlan` schemas |
| PyYAML | 6.x | SKILL.md / agent frontmatter is YAML; input specs may be YAML |
| uv | current | `pyproject.toml` only; `uv sync` is the single setup step |

**Dev dependencies:** pytest, ruff, mypy  
**Entry point:** `claude-env = "claude_env.cli:app"` in `[project.scripts]`

---

## Table Stakes Features

All of these must ship in v1. Missing any makes the tool feel incomplete or untrustworthy.

1. **Domain detection from input** — detect technical domain from freeform text or structured spec without requiring user labels
2. **Two-layer output** — produce both `~/.claude/` (global conventions) and `.claude/` (per-project agents, skills, CLAUDE.md, hooks)
3. **CLAUDE.md generation** — ≤200 lines, behavioral rules only, no content Claude can infer from code
4. **Skills generation** — 3–5 domain-appropriate `.claude/skills/<name>/SKILL.md` files with verb-phrase descriptions and correct frontmatter
5. **Subagents generation** — 2–3 domain-appropriate `.claude/agents/<name>.md` files with explicit `skills:` references
6. **Hooks generation** — `.claude/settings.json` with lint/typecheck hooks; hardcoded paths, exit code 2 for blocking
7. **Plan→execute→verify pattern embedded** — encoded in generated CLAUDE.md and skills
8. **Context management rules embedded** — `/clear` protocol, compact instructions, subagent delegation patterns
9. **Auto-improvement loop (lessons.md)** — generated CLAUDE.md includes the lessons.md read-at-session-start pattern
10. **Dry-run mode** — show what would be written without writing it; mandatory before developer trust is established
11. **Idempotent generation** — sentinel-based merge strategy from day one; never overwrite user edits
12. **CLI skill invocability** — tool invocable as `/claude-env:bootstrap` from any project directory inside Claude Code

---

## Architecture

### Components and Build Order

```
1. Template Registry      — pure file I/O, no deps; build and test first
2. Input Normalizer       — ProjectSpec schema + LLM expansion for freeform
3. Domain Classifier      — YAML domain profiles (web/CLI/data/infra); purely deterministic
4. Environment Planner    — merges ProjectSpec + DomainProfile → GenerationPlan (pure data, no I/O)
5. Generator              — executes GenerationPlan; first component with file I/O; enforces 200-line cap
6. Audit Agent            — structural checks (JSON valid, line count, required fields); LLM layer second
7. CLI Entrypoint         — wires setup (global wizard) and bootstrap (per-project) modes
8. Claude Code Skill      — thin wrapper calling CLI; no logic of its own
```

### Key Patterns

- **Single-direction pipeline** — no feedback loops; strictly: Input → Spec → Domain → Plan → Generate → Audit
- **Declarative GenerationPlan as pivot** — planner produces a data structure, generator executes it; testable independently
- **Domain profiles are YAML config files, not code** — adding a domain = adding a file, not touching core logic
- **Merge-safe global writes** — `~/.claude/CLAUDE.md` append-only with sentinel; skills/agents use named subdirectories; hooks JSON merged with dedup
- **200-line constraint enforced at generation time** — templates may be larger; Generator selects/truncates sections
- **Audit Agent zero-context** — launched with no conversation history to avoid confirmation bias from generation step

### Data Flow

```
Input (freeform | spec file)
  → Input Normalizer → ProjectSpec
  → Domain Classifier → DomainProfile
  → Environment Planner → GenerationPlan
  → Generator → files on disk (~/.claude/ + .claude/)
  → Audit Agent → AuditReport → user
```

---

## Watch Out For

### 1. CLAUDE.md bloat silently breaks everything — SEVERITY: HIGH
Generated CLAUDE.md exceeds 200 lines or includes content Claude infers anyway. Claude ignores bloated files.  
**Prevention:** Hard-cap at 200 lines as a CI assertion. Apply "would removing this cause Claude to make a mistake?" filter per line. Use `@path` imports to offload supplementary content.

### 2. Generated skills are never invoked — SEVERITY: HIGH
Vague skill `description` fields mean Claude never autodiscovers them. Overlapping descriptions cause confusion.  
**Prevention:** Generate descriptions as precise verb-phrases ("Fix a GitHub issue end-to-end"). Set `disable-model-invocation: true` for side-effect workflows. List available skills explicitly in generated CLAUDE.md.

### 3. Hooks fail silently — SEVERITY: HIGH
Malformed `settings.json` (trailing comma, shell variables in paths, wrong exit code) results in hooks that appear configured but never run.  
**Prevention:** Hardcode absolute paths — never shell variables. Validate JSON with `python3 -m json.tool` before writing. Document that exit code `2` blocks, exit code `1` does not. Audit Agent must parse settings.json structurally.

### 4. Non-idempotent generation destroys manual edits — SEVERITY: HIGH
Re-running generator overwrites developer customizations. Developer stops using the tool.  
**Prevention:** Sentinel-based merge strategy from day one (`# USER SECTION — DO NOT REGENERATE BELOW`). Hooks JSON merged with deduplication. Cannot be retrofitted — design it in at the start.

### 5. Two-layer global/project collision — SEVERITY: HIGH
Rules in `~/.claude/CLAUDE.md` contradict `.claude/CLAUDE.md`. Same skill slug exists at both layers with different behavior. Hooks execute twice.  
**Prevention:** Scope contract: global owns cross-project conventions, project layer owns domain behavior. Check for name collision before writing. Comment block at top of each CLAUDE.md stating its scope.

### 6. Subagents can't access project skills — SEVERITY: HIGH
Skills are not automatically injected into spawned subagent contexts. Subagents silently fall back to global skills.  
**Prevention:** Generate agent `.md` files with explicit `skills:` references. Audit Agent validates this cross-reference. Document the boundary in the generated environment.

---

## Key Decisions Already Made

These are locked in by research — do not revisit without strong reason.

1. **Typer over Click or argparse** — correct choice for a new multi-subcommand CLI with Rich output. Closed.
2. **Jinja2 over f-strings/string.Template** — templates need conditionals and loops; f-strings don't scale past 5 templates. Closed.
3. **uv over Poetry or pip+setuptools** — 2025/2026 standard; `pyproject.toml` as single source of truth. Closed.
4. **Skills over Commands** — Claude Code merged `.claude/commands/` into `.claude/skills/`. Generator produces skills. Closed.
5. **Merge-safe global writes, never full-overwrite** — `~/.claude/` is the user's live environment. Sentinel merge is mandatory.
6. **Structural checks before LLM judgment in Audit Agent** — Audit correctness requires concrete assertions, not LLM opinion.
7. **Trace2Skill deferred to v2** — Requires real execution traces. Premature in v1.
8. **KB-backed generation deferred to v2** — Depends on SECONDBRAIN query path stability. Core generation must work first.
9. **Expert Audit Agent deferred to v2** — Requires all generation steps to exist before it's useful.
10. **No GUI, no team sync, no file watcher, no template registry** — explicit anti-features for v1.

---

## Open Questions

1. **LLM invocation path for Input Normalizer** — Freeform idea expansion requires an LLM call. Is this a direct Claude API call from the generator, or does it run inside the Claude Code context? Affects cost, latency, and offline-use design.
2. **How many domain profiles for v1?** — Research suggests 3–4 (web, CLI, data, infra). Is that enough to demonstrate value, or does the tool feel limited without mobile/ML/backend?
3. **Skill installation path** — The Claude Code skill calls `python3 <path>/main.py bootstrap .` but the path varies by machine. How does the installed skill locate the CLI? `uv run` from a pinned path? Global install?
4. **Exact sentinel and merge contract** — Which sections of generated files are generator-owned vs. user-territory? Needs a concrete decision before implementation to avoid ambiguity in the merge logic.
5. **Domain profile YAML schema** — The Environment Planner maps `DomainProfile` fields to template variables. The exact schema for domain profile files is the core data contract and must be specified before building the planner.
