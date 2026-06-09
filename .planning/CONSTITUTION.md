# Constitution — claude-env

**Project DNA.** These are binding architectural principles, not preferences. Every SPEC, PLAN, and implementation in this project MUST comply. A conflict with a principle is a blocker — resolve it by complying, or amend this constitution explicitly (see Amendment).

GSD `spec-phase`, `plan-phase`, and `execute-phase` read this file and gate against it.

---

## Principles

### P1 — Two layers, never blurred
Output targets exactly two layers: per-project `.claude/` and global `~/.claude/`. Project-specific content never leaks into the global layer, and global conventions never get duplicated into a project. If a change touches both, say which goes where and why.

### P2 — Zero manual config is the bar
The core value is "start building immediately, zero manual configuration." Generated output must be runnable as-is. No "now go edit X / set Y by hand" steps in the happy path. If a manual step is unavoidable, it is a defect to be designed out, not documented around.

### P3 — Generated CLAUDE.md ≤ 200 lines, every line earns its place
Hard quality constraint (REQUIREMENTS). No generic boilerplate — each line must change agent behavior (per L002). A longer file is not a richer environment; it is context tax paid every session.

### P4 — Idempotent, non-destructive generation
Re-running the generator merges; it never clobbers user edits. Output is deterministic given the same input. No surprise overwrites — preserve hand-tuned content across re-runs.

### P5 — Domain-adaptive, not one-size-fits-all
Output is calibrated to the detected technical domain (web/CLI/data/infra/…). Generic dumps that ignore the domain violate the project's reason to exist.

### P6 — Simplicity first, surgical changes
Minimum code that solves the problem. No speculative features, no abstractions for single-use code, no error handling for impossible states. Touch only what the task requires; match existing style. Root causes, never patches (`--no-verify`, silenced warnings, skipped tests are forbidden).

### P7 — Token-discipline is a product value
The environments this project produces — and this project's own work — minimize context/token waste. Measure before adding (the env's health is auditable, e.g. `codeburn`), prune ghost weight, prefer modularity over monolith. Adding a tool/skill/file must justify its per-session context cost.

---

## Amendment

This constitution changes only by an explicit, deliberate decision recorded here — not silently mid-task. To amend: state the principle changed, the reason, and the date. Implementation pressure is never a valid reason to quietly violate a principle; surface the conflict instead.

*Established 2026-06-09 — derived from PROJECT.md core value + global engineering conventions (CLAUDE.md). Seeded by the spec-kit "Constitution" pattern (EVALUATIONS: github/spec-kit, cherry-pick).*
