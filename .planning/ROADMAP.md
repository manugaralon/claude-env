# Roadmap: claude-env-2

## Overview

Build a pipeline that turns a raw project idea or structured spec into a fully configured Claude Code environment. Five phases follow the natural build order: scaffold the project, build the data pipeline (input → spec → domain → plan), execute generation (all output files), wire the CLI and skill entry points, then validate everything with the audit step.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, dependencies, template registry, domain profile YAML files (completed 2026-04-16)
- [x] **Phase 2: Pipeline** - Input normalizer, domain classifier, environment planner — pure data, no I/O (completed 2026-04-18)
- [x] **Phase 3: Generator** - Executes GenerationPlan: all output files with idempotent merge strategy (completed 2026-04-19)
- [x] **Phase 4: CLI + Skill** - Typer entrypoint (setup, bootstrap, --dry-run), Claude Code skill wrapper (completed 2026-04-20)
- [x] **Phase 5: Audit** - Structural validation of generated environment before developer starts (completed 2026-05-07)
- [x] **Phase 6: Constitution Generation** - Generator emits `.planning/CONSTITUTION.md` (universal + domain principles, write-once); generated CLAUDE.md references it (implemented via /gsd-quick 2026-06-09)
- [ ] **Phase 7: Augment Mode** - Apply the env layer to existing/mature projects without clobbering bespoke setup (sentinel managed-block merge for an existing CLAUDE.md, write-once constitution, skip-if-exists, dry-run-able). De-risked 2026-06-09, not yet built.

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
**Plans:** 3/3 plans complete
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
**Plans**: 3 plans
Plans:
- [ ] 02-01-PLAN.md — Data contracts (ProjectSpec, GenerationPlan models), anthropic dep, test fixtures
- [ ] 02-02-PLAN.md — InputNormalizer: freeform LLM extraction + YAML/Markdown spec parsing
- [ ] 02-03-PLAN.md — DomainClassifier (signal matching) + EnvironmentPlanner (GenerationPlan builder)

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
**Plans:** 2/2 plans complete
Plans:
- [ ] 03-01-PLAN.md — Sentinel merge module, content catalogue, expanded CLAUDE.md template, settings.json template + tests
- [ ] 03-02-PLAN.md — Generator class (execute GenerationPlan to disk) + comprehensive GEN-01 through GEN-06 test suite

### Phase 4: CLI + Skill
**Goal**: The tool is invocable from the terminal and from inside Claude Code — global onboarding and per-project bootstrapping both work end-to-end
**Depends on**: Phase 3
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):
  1. `claude-env setup` runs the global wizard and writes a valid `~/.claude/` layer without prompting for technical choices
  2. `claude-env bootstrap` run from a project directory generates a complete `.claude/` layer for that project
  3. `claude-env bootstrap --dry-run` prints every file that would be written without touching disk
  4. `/claude-env:bootstrap` is invocable as a Claude Code skill from any project directory and produces the same output as the CLI
**Plans**: [To be planned]

### Phase 5: Audit
**Goal**: A generated environment is structurally validated before the developer starts — problems are caught immediately, not discovered mid-session
**Depends on**: Phase 4
**Requirements**: QA-01
**Success Criteria** (what must be TRUE):
  1. Audit step reports PASS or FAIL with specific failure reasons for: CLAUDE.md line count, settings.json JSON validity, agent files missing `skills:` field, skill descriptions that are not verb-phrases
  2. A deliberately broken generated environment (e.g., settings.json with trailing comma) produces a FAIL report identifying the exact file and rule violated
  3. Audit runs automatically at the end of `claude-env bootstrap` and its exit code reflects pass/fail
**Plans**: [To be planned]

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete    | 2026-04-18 |
| 2. Pipeline | 3/3 | Complete    | 2026-04-18 |
| 3. Generator | 2/2 | Complete    | 2026-04-19 |
| 4. CLI + Skill | 2/2 | Complete   | 2026-04-20 |
| 5. Audit | 0/TBD | Not started | - |

### Phase 6: Constitution Generation
**Goal**: The generator emits a `.planning/CONSTITUTION.md` (project architectural DNA — universal core + domain-specific principles) into every generated environment, and the generated CLAUDE.md references it. Closes the spec-kit "Constitution" cherry-pick (B→A: B patched GSD to gate against it; A makes the generator produce it).
**Depends on**: Phase 3 (Generator)
**Requirements**: See `phases/06-constitution-generation/06-SPEC.md` (5 locked, ambiguity 0.11)
**Success Criteria** (what must be TRUE):
  1. Generating an env produces `.planning/CONSTITUTION.md` at the project root (not under `.claude/`)
  2. The constitution is domain-adapted (universal core + ≥1 domain-specific principle) and stays ≤ ~50 lines
  3. The generated CLAUDE.md references the constitution and stays ≤ 200 lines
  4. Re-generation never overwrites an existing CONSTITUTION.md (write-once)

**Status**: Implemented via /gsd-quick 2026-06-09 (commit d879f51). 167 tests + end-to-end smoke verified.

### Phase 7: Augment Mode
**Goal**: Apply claude-env's env layer to a project that ALREADY has history/bespoke files — without ever clobbering hand-written content. This is the cross-project "apply to existing repos" path (the 90% case for a solo dev with live projects), complementing greenfield `bootstrap`. Motivated by Agus/Clibit (mature, bespoke CLAUDE.md).
**Depends on**: Phase 3 (Generator) + Phase 6 (write-once)
**Requirements**: TBD (run /gsd-spec-phase 7)
**Design (de-risked 2026-06-09)**:
  - `sentinel.py` (`wrap`/`merge`/`has_sentinel`) are ALREADY pure string fns on arbitrary content — not coupled to the GLOBAL layer. The GLOBAL coupling lives only in the generator's layer-based dispatch.
  - Implementation = add a `merge_strategy` field to `Artifact` (`overwrite` | `sentinel` | `write_once` | `skip_if_exists`) and dispatch on strategy, not layer. Consistent with the Phase-3 rule "strategy from metadata, not content".
  - Existing CLAUDE.md → `sentinel` (managed block appended; human content sovereign, NEVER a 2nd CLAUDE.md). CONSTITUTION.md → `write_once`. Other bespoke artifacts → `skip_if_exists`. Always `--dry-run`-able; if it can't merge safely, skip + report.
**Success Criteria** (what must be TRUE):
  1. Running augment on a project with a bespoke root CLAUDE.md leaves the human content byte-identical and only updates the managed block
  2. No second CLAUDE.md is ever created
  3. An existing CONSTITUTION.md is never overwritten; bespoke artifacts are skipped, not clobbered
  4. `--dry-run` shows the exact delta and writes nothing

**Status**: Planned + de-risked, NOT built. Build in a focused session (spec → plan → execute, or /gsd-quick — it's ~A-sized).
