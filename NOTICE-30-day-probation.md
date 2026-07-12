# 30-Day Probation Notice — 2026-05-07 batch

The work landed in this batch was reviewed by an LLM Council on 2026-05-07. The verdict was **80% theatre / 20% real value**, with concrete remediation: instrument usage and let data decide what survives.

## What's on probation

- ~/.claude/ skills batch (15 cherry-picks + 7 self-built + 19 GSD frontmatter upgrades) — installed but **unproven in real use**
- "44 strong skills" metric — **self-graded** by an audit script the same agent designed; no external validation
- New bootstrap artifacts (`CONTEXT.md`, `docs/adr/README.md`) — useful only if actually populated by week 1 of new projects
- Subsystem 11/13 skills (`/instinct-*`, `/evolve`, `/evaluate`, `/check-evaluation`, `/find-skill`) — meta-tooling has historically high abandonment in dotfiles repos

## What's measured

`~/.claude/hooks/skill-usage-log.sh` (PostToolUse `Skill` matcher) records every skill invocation to `~/.claude/instrumentation/skill-invocations.log` with format `ISO_timestamp|skill_name|cwd`.

## Probation review on 2026-06-07

```bash
bash ~/.claude/scripts/skill-usage-report.sh
```

**Decision rule:** any skill with <3 invocations in 30 days = candidate for deletion or move to `~/.claude/skills-quarantine/`.

## What survives without probation (defensible)

- `quality-gate-precommit.sh` hook — auto-fires at commit boundary; self-validating (will catch problems whether Manuel notices or not)
- The 5 already-existing own skills upgraded with proper frontmatter (`fix-issue`, `create-pr`, `run-lint`, `quality-gate`, `karpathy-guidelines`) — Manuel was already using these, just better-described
- Cleanup of the dead `templates/` duplicate dir — pure deuda técnica resolved
- ADR-0001 (architectural decision documented)

## Council blind spots caught in peer review

Three things the advisor council itself missed:

1. **The audit metric needs auditing.** The 5/6 rubric was designed in the same session as the score. Closed loop. Before any usage telemetry, an external check (Manuel-graded sample, or blind deletion test) is needed.
2. **Opportunity cost of the session.** Hours spent on scaffolding are hours not spent on real projects.
3. **Per-session carrying cost.** Every skill, frontmatter trigger, and hook inflates Claude's pre-task context, taxing all future sessions whether the skill fires or not.

## Honest framing

This batch is shipped because the alternative (delete-before-measuring) has its own bias. We commit, we instrument, we measure, we cull. Data > intent.

— Reviewed and merged 2026-05-07.

---

## Review executed 2026-07-12 (66 days, window extendida — la review del 06-07 no llegó a correrse)

`skill-usage-report.sh` sobre `skill-invocations.log`: **117 invocaciones, 19 skills únicos** desde 2026-05-07. El log está dominado por GSD (`gsd-plan-phase` 22, `gsd-execute-phase` 18, `gsd-discuss-phase` 17…) y `consciousness-council` (22). El council de 2026-05-07 tenía razón: la capa atómica cherry-pickeada resultó ~100% theatre según el uso real.

**Batch en probation identificado por mtime (2026-05-06/07):** 26 dirs − 5 exentos por este NOTICE = 21 skills.

| Resultado | Skills | Acción |
|---|---|---|
| **Sobrevive** (≥3 invocaciones) | `evolve` (3) | Se queda |
| **Quarantined** (0 invocaciones, sin referencias en CLAUDE.md) | caveman, check-evaluation, evaluate, find-skill, improve-codebase-architecture, llm-council, mcp-builder, receiving-code-review, requesting-code-review, skill-creator, subagent-driven-development, writing-plans, zoom-out (13) | Movidos a `~/.claude/skills-quarantine/` 2026-07-12 |
| **Pendiente decisión Manuel** (0 invocaciones PERO referenciados como capa atómica en `~/.claude/CLAUDE.md` y CLAUDE.md de proyectos) | grill-with-docs, tdd, systematic-debugging, brainstorming, verification-before-completion, instinct-add, instinct-status (7) | Quarantinar exige limpiar las referencias en CLAUDE.md a la vez; se decide junto |

**Caveats de instrumentación:** el hook solo registra invocaciones vía tool `Skill` en sesión principal — metodología seguida sin invocar el skill (p.ej. TDD dentro de gsd-executor) no computa. `consciousness-council` (22 usos) no era parte del batch y confirma su estatus canónico sobre `llm-council` (0 usos).

**Restaurar:** `mv ~/.claude/skills-quarantine/<name> ~/.claude/skills/`. Borrado definitivo de la quarantine: decisión manual futura (sugerido: +30 días sin restauraciones).
