# Roadmap: claude-env-2

## Overview

Build a pipeline that turns a raw project idea or structured spec into a fully configured Claude Code environment. Five phases follow the natural build order: scaffold the project, build the data pipeline (input → spec → domain → plan), execute generation (all output files), wire the CLI and skill entry points, then validate everything with the audit step.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Project scaffold, dependencies, template registry, domain profile YAML files
- [ ] **Phase 2: Pipeline** - Input normalizer, domain classifier, environment planner — pure data, no I/O
- [ ] **Phase 3: Generator** - Executes GenerationPlan: all output files with idempotent merge strategy
- [ ] **Phase 4: CLI + Skill** - Typer entrypoint (setup, bootstrap, --dry-run), Claude Code skill wrapper
- [ ] **Phase 5: Audit** - Structural validation of generated environment before developer starts

## Phase Details

### Phase 1: Foundation
**Goal**: Project infrastructure exists and domain profiles are defined — the skeleton every other component builds on
**Depends on**: Nothing (first phase)
**Requirements**: (no direct v1 requirements — foundational infrastructure)
**Success Criteria** (what must be TRUE):
  1. `uv sync` installs all dependencies cleanly from pyproject.toml with no manual steps
  2. Template registry can resolve and render any template by name given a context dict
  3. Domain profile YAML files for web, CLI, data, and infra are loadable and schema-valid
  4. `ruff` and `mypy` pass on the initial codebase with zero errors
**Plans:** 1/3 plans executed
Plans:
- [ ] 01-01-PLAN.md — Bootstrap: pyproject.toml with ruff/mypy/pytest config, package tree with subpackages, Typer CLI stub, tests scaffold with conftest
- [ ] 01-02-PLAN.md — DomainProfile Pydantic v2 model with `extra="forbid"` + 5 YAML profiles (web, cli, data, infra, general) + schema-drift tests
- [ ] 01-03-PLAN.md — TemplateRegistry (Jinja2 + StrictUndefined + absolute-path guard) + 3 stub templates + unit/integration tests

### Phase 2: Pipeline
**Goal**: A freeform idea or structured spec file flows through to a validated GenerationPlan data structure — no files written yet
**Depends on**: Phase 1
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04
**Success Criteria** (what must be TRUE):
  1. Given a freeform text idea, Input Normalizer returns a valid ProjectSpec with domain hint populated
  2. Given a markdown/YAML spec file, Input Normalizer returns an equivalent ProjectSpec
  3. Domain Classifier assigns one of {web, CLI, data, infra, general} to any ProjectSpec without requiring user input
  4. Environment Planner produces a GenerationPlan that lists every file to be written, testable with no I/O
**Plans**: TBD

### Phase 3: Generator
**Goal**: Given a GenerationPlan, all target files are written to disk correctly — per-project and global layers, within quality constraints, safely on re-run
**Depends on**: Phase 2
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06
**Success Criteria** (what must be TRUE):
  1. Generated `.claude/CLAUDE.md` is ≤200 lines and contains plan→execute→verify pattern, context management rules, and lessons.md auto-improvement loop
  2. Generated `.claude/skills/` contains 3–5 SKILL.md files with verb-phrase descriptions and correct YAML frontmatter
  3. Generated `.claude/agents/` contains 2–3 agent files with explicit `skills:` references to generated skills
  4. Generated `.claude/settings.json` is valid JSON with lint/typecheck hooks using hardcoded paths and exit code 2
  5. Re-running generator on an already-generated project merges safely — existing user edits in sentinel-protected sections are preserved
**Plans**: TBD

### Phase 4: CLI + Skill
**Goal**: The tool is invocable from the terminal and from inside Claude Code — global onboarding and per-project bootstrapping both work end-to-end
**Depends on**: Phase 3
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):
  1. `claude-env setup` runs the global wizard and writes a valid `~/.claude/` layer without prompting for technical choices
  2. `claude-env bootstrap` run from a project directory generates a complete `.claude/` layer for that project
  3. `claude-env bootstrap --dry-run` prints every file that would be written without touching disk
  4. `/claude-env:bootstrap` is invocable as a Claude Code skill from any project directory and produces the same output as the CLI
**Plans**: TBD

### Phase 5: Audit
**Goal**: A generated environment is structurally validated before the developer starts — problems are caught immediately, not discovered mid-session
**Depends on**: Phase 4
**Requirements**: QA-01
**Success Criteria** (what must be TRUE):
  1. Audit step reports PASS or FAIL with specific failure reasons for: CLAUDE.md line count, settings.json JSON validity, agent files missing `skills:` field, skill descriptions that are not verb-phrases
  2. A deliberately broken generated environment (e.g., settings.json with trailing comma) produces a FAIL report identifying the exact file and rule violated
  3. Audit runs automatically at the end of `claude-env bootstrap` and its exit code reflects pass/fail
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/3 | In Progress|  |
| 2. Pipeline | 0/TBD | Not started | - |
| 3. Generator | 0/TBD | Not started | - |
| 4. CLI + Skill | 0/TBD | Not started | - |
| 5. Audit | 0/TBD | Not started | - |
