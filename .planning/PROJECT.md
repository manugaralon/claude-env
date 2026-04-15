# claude-env-2

## What This Is

An intermediary layer between a project definition and its Claude environment preparation. Given a raw idea or a technical spec as input, it generates a fully adapted Claude environment — CLAUDE.md, skills, hooks, subagents — calibrated to the project's technical domain, expert agents needed, and best practices. The system also embeds expert agents that perform an initial audit of the generated environment and remain available during development.

## Core Value

Given a project definition, produce a Claude environment so adapted and complete that the developer can start building immediately with maximum leverage — zero manual configuration.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Accept two input forms: raw idea (freeform text) or technical spec (structured document)
- [ ] Detect and adapt to technical domain (web, mobile, data, infra, etc.)
- [ ] Generate per-project `.claude/` layer: CLAUDE.md, skills, subagents
- [ ] Generate or extend global `~/.claude/` layer: global CLAUDE.md, cross-project conventions
- [ ] Expert agent audit: validates generated environment before developer starts, available during dev
- [ ] Embed best practices: Trace2Skill, context management, auto-improvement loop, plan→execute→verify
- [ ] CLI wizard (setup.sh style) for initial global onboarding
- [ ] Claude Code skill for per-project bootstrapping (invocable from any project)
- [ ] Output includes expert subagents specialized to the project's domain
- [ ] Generated CLAUDE.md stays under 200 lines (quality constraint)

### Out of Scope

- GUI/web interface — CLI + skill is sufficient for the target user
- Multi-user or team synchronization — single-developer focus for v1
- Automated environment updates on code changes — initial generation only
- IDE plugins — Claude Code CLI is the runtime

## Context

- Manuel is the primary user; the tool is built for his own workflow first, extractable later
- Existing claude-env project exists but lacks: skills/hooks/subagents generation, project-adapter concept, Trace2Skill integration
- The SECONDBRAIN KB now has 15+ entries on Claude Code best practices (context management, hooks, CLAUDE.md structure, skills vs subagents, MCP, verification patterns) — this is the knowledge base the system should encode into generated environments
- Trace2Skill (Alibaba paper): extract skills from real execution traces using 4 analyst agents — rules extracted from real runs outperform hand-written rules
- Two-layer output architecture: global ~/.claude/ (shared conventions, cross-project skills) + per-project .claude/ (domain-specific agents, project skills, project CLAUDE.md)
- The system itself should be a Claude Code skill so it can be invoked from any project directory

## Constraints

- **Tech stack**: Python 3.12+ (consistent with SECONDBRAIN stack) — templating, file generation, CLI
- **Claude Code**: Must be usable as a skill invocable from claude code CLI
- **Output quality**: Generated CLAUDE.md must pass the "200-line test" — concise enough to be read every session
- **No external services**: All generation happens locally; no API calls to external registries
- **Self-contained**: Generated environments must work standalone, without requiring claude-env-2 to be present in the target project

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-layer output (global + per-project) | Both layers serve different needs: global for cross-project conventions, per-project for domain specifics | — Pending |
| Expert agents: initial audit + available during dev | Audit catches misconfiguration before work starts; availability during dev catches gaps as they surface | — Pending |
| CLI wizard + skill (both mechanisms) | CLI wizard for one-time global onboarding; skill for repeatable per-project bootstrapping | — Pending |
| Embed all 4 best practices by default | Trace2Skill, context management, auto-improvement, plan→execute→verify are non-negotiable — not optional flags | — Pending |
| Python for generation engine | Consistent with Manuel's stack; file generation and templating is a natural fit | — Pending |

---
*Last updated: 2026-04-15 after initialization*
