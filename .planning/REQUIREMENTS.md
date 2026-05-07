# Requirements

## v1 Requirements

### Core Pipeline

- [x] **PIPE-01**: System accepts raw freeform idea text as input and normalizes it to a structured ProjectSpec
- [x] **PIPE-02**: System accepts a structured spec document (markdown/YAML) as input
- [x] **PIPE-03**: System classifies ProjectSpec into a technical domain using static domain profiles (web, CLI, data, infra, general)
- [x] **PIPE-04**: System produces a GenerationPlan from ProjectSpec + DomainProfile (pure data structure, no I/O)

### Generation

- [x] **GEN-01**: Generator produces per-project `.claude/CLAUDE.md` ≤200 lines with behavioral rules, plan→execute→verify pattern, context management rules, and auto-improvement loop (lessons.md)
- [x] **GEN-02**: Generator produces 3–5 domain-appropriate `.claude/skills/<name>/SKILL.md` files with correct frontmatter and verb-phrase descriptions
- [x] **GEN-03**: Generator produces 2–3 domain-appropriate `.claude/agents/<name>.md` files with explicit `skills:` references
- [x] **GEN-04**: Generator produces `.claude/settings.json` with lint/typecheck hooks using hardcoded paths and exit code 2 for blocking
- [x] **GEN-05**: Generator produces/updates global `~/.claude/CLAUDE.md` with cross-project conventions via merge-safe sentinel pattern
- [x] **GEN-06**: All generation is idempotent — re-running merges safely without overwriting user customizations

### CLI

- [x] **CLI-01**: `claude-env setup` — global onboarding wizard that generates `~/.claude/` layer
- [x] **CLI-02**: `claude-env bootstrap` — per-project generation that produces `.claude/` layer
- [x] **CLI-03**: `--dry-run` flag shows what would be written without writing
- [x] **CLI-04**: Tool is installable as Claude Code skill `~/.claude/skills/claude-env/SKILL.md` invocable from any project

### Quality

- [x] **QA-01**: Audit step validates generated environment: CLAUDE.md line count, hooks JSON validity, subagent `skills:` field presence, skill description quality

## v2 Requirements (deferred)

- Trace2Skill integration — requires real execution traces from v1 usage
- SECONDBRAIN KB live query at generation time — depends on process.py stability
- Expert LLM audit agent — structural checks sufficient for v1; LLM judgment is v2
- Mobile and ML domain profiles — expand after core domains are validated

## Out of Scope

- GUI/web interface — CLI + skill is sufficient for the target user
- Multi-user/team sync — single developer focus for v1
- File watcher / auto-update on code changes — initial generation only
- Template marketplace / plugin registry — scope creep
- IDE plugins — Claude Code CLI is the runtime

## Traceability

| REQ-ID | Phase |
|--------|-------|
| PIPE-01 | Phase 2 |
| PIPE-02 | Phase 2 |
| PIPE-03 | Phase 2 |
| PIPE-04 | Phase 2 |
| GEN-01 | Phase 3 |
| GEN-02 | Phase 3 |
| GEN-03 | Phase 3 |
| GEN-04 | Phase 3 |
| GEN-05 | Phase 3 |
| GEN-06 | Phase 3 |
| CLI-01 | Phase 4 |
| CLI-02 | Phase 4 |
| CLI-03 | Phase 4 |
| CLI-04 | Phase 4 |
| QA-01 | Phase 5 |
