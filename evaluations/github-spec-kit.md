---
source: https://github.com/github/spec-kit
type: github-repo
evaluated_date: 2026-06-08
verdict: cherry-pick
tags: [methodology, spec-driven, sdd, gsd-comparison]
extracts: [constitution concept, cross-artifact consistency check, parallelization [P] markers]
revisit_after:
---

# github/spec-kit

**Summary**: GitHub's open-source Spec-Driven Development (SDD) toolkit (~110k stars, MIT, GitHub/Microsoft-backed, very active). `specify` CLI + agent-agnostic slash workflow: `/speckit.constitution` → `specify` → `clarify` → `plan` → `tasks` → `analyze` → `implement` → `checklist`. State in `.specify/`. 35+ agent integrations (Claude, Copilot, Gemini, Codex, Cursor…).

## Why this verdict
cherry-pick — **NOT a switch**. GSD (Manuel's backbone) governs the full project lifecycle (milestones, phase types, hooks, code-review/verify/reflection); spec-kit is feature-scoped with no roadmap/milestone/retrospective layer. They operate at different altitudes — switching, or running both as parallel flow-controllers, is high-cost and conflicts with the CLAUDE.md methodology hierarchy. Steal specific ideas instead.

## Specific items extracted (priority order)
1. **Constitution file** — add `.planning/CONSTITUTION.md` (project architectural DNA) that `gsd-spec-phase` / `gsd-plan-phase` / `gsd-execute-phase` read and gate against. Highest value, lowest disruption.
2. **Cross-artifact consistency check** — add a `/gsd-analyze` (or expand `gsd-validate-phase`) for an explicit spec↔plan↔tasks coherence pass.
3. **Parallelization markers** — add a `[P]` convention to `gsd-plan-phase` task output.
- Note: `/speckit.taskstoissues` (tasks → GitHub Issues via MCP) if Manuel ever adopts Issues as a tracker.

## Caveats / risks
- MIT, clean. Agent-agnostic portability is a real asymmetry vs GSD but not a current pain point.
- Escalation: NOT council-worthy — clear-cut; the cherry-picks are additive modifications to GSD, not architectural tensions.
