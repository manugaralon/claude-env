# Phase 6: Constitution Generation — Specification

**Created:** 2026-06-09
**Ambiguity score:** 0.11 (gate: ≤ 0.20)
**Requirements:** 5 locked

## Goal

The claude-env generator emits a `.planning/CONSTITUTION.md` (project architectural DNA) into every environment it produces, and the generated `CLAUDE.md` references it — so each generated environment is born with a binding, gateable constitution (the downstream of phase B, where GSD spec/plan/execute already gate against `.planning/CONSTITUTION.md`).

## Background

The generator renders Jinja2 templates (`claude_env/data/*.j2`, e.g. `claude_md_project.j2`, `context_md.j2`, `adr_readme.j2`) into a target environment via a GenerationPlan with an idempotent merge strategy (built in Phase 3). It currently emits CLAUDE.md, skills, subagents, hooks, MCP config — but **no constitution**. Phase B (2026-06-09) patched GSD's spec/plan/execute workflows to read and gate against `.planning/CONSTITUTION.md`, and seeded one for this repo by hand. Phase 6 closes the B→A sequence: make the generator produce that file automatically, so the gating mechanism has an artifact to gate against in every new project. This SPEC was itself produced under the live constitution gate — its requirements comply with this repo's CONSTITUTION.md (P1–P7).

## Requirements

1. **Constitution template**: A Jinja2 template renders a project constitution.
   - Current: No constitution template exists in `claude_env/data/` or `claude_env/templates/`.
   - Target: A `constitution.j2` template renders a `CONSTITUTION.md` with a universal-core set of principles plus principles specific to the detected technical domain (web/CLI/data/infra/…), matching how `claude_md_project.j2` is already domain-adapted.
   - Acceptance: Rendering for a given domain produces a file containing ≥1 universal principle AND ≥1 domain-specific principle for that domain; rendering for two different domains yields different domain-specific sections.

2. **Generator emits to the project layer**: The GenerationPlan includes the constitution output at the project's `.planning/CONSTITUTION.md`.
   - Current: The generator emits CLAUDE.md/skills/etc.; no `.planning/CONSTITUTION.md` is produced.
   - Target: Every generated environment includes `<output>/.planning/CONSTITUTION.md`.
   - Acceptance: Running the generator on a sample input yields `<output>/.planning/CONSTITUTION.md`; the file is NOT written into the global `~/.claude/` layer (P1 — two layers, never blurred).

3. **Generated CLAUDE.md references the constitution**: The rendered `claude_md_project.j2` binds the agent to the constitution.
   - Current: The generated CLAUDE.md contains no reference to any constitution.
   - Target: The generated CLAUDE.md includes a concise (1–2 line) instruction to read and respect `.planning/CONSTITUTION.md` — so even environments that do not use GSD honor it.
   - Acceptance: The rendered CLAUDE.md contains a reference to `.planning/CONSTITUTION.md`; the total rendered CLAUDE.md is ≤ 200 lines (P3).

4. **Write-once, non-destructive**: Re-generation never overwrites an existing constitution.
   - Current: Phase 3 provides idempotent merge for generated files, but no constitution-specific handling.
   - Target: If `.planning/CONSTITUTION.md` already exists in the target, the generator leaves it byte-untouched; it only creates the file when absent (a constitution is user-owned DNA after creation — P4).
   - Acceptance: Edit a generated `CONSTITUTION.md`, re-run the generator → `git diff` on that file is empty.

5. **Zero-config and concise**: The emitted constitution is usable as-is and tight.
   - Current: N/A.
   - Target: The emitted `CONSTITUTION.md` requires no manual editing to be valid and usable (P2 — zero manual config), and is concise (P7) — a bounded set of real principles, not a blank fill-in form.
   - Acceptance: The emitted file is ≤ ~50 lines and contains no placeholder whose absence breaks usage (any optional curation hint is clearly marked optional, not a blocking TODO).

## Boundaries

**In scope:**
- A `constitution.j2` template (universal core + domain-adapted principles).
- A GenerationPlan entry emitting `.planning/CONSTITUTION.md` into the generated env.
- Domain-adapted principle selection driven by the existing domain classifier.
- A concise reference to the constitution in the generated `CLAUDE.md`.
- Write-once handling so re-generation never clobbers an edited constitution.

**Out of scope:**
- Modifying GSD's own workflows to gate against the constitution — that was **phase B**, already done outside this project (in `~/.claude/get-shit-done/`).
- Retrofitting `CONSTITUTION.md` into already-generated environments — the generator only affects newly generated/regenerated envs.
- Any editor/wizard/TUI for authoring or amending the constitution — out (a plain file the dev edits).
- Runtime enforcement beyond the generated CLAUDE.md reference — non-GSD envs rely on that reference; GSD envs rely on the phase-B gates. No new enforcement layer here.

## Constraints

Bound by this repo's own `.planning/CONSTITUTION.md` (the SPEC was generated under its gate):
- **P1** — output goes to the project layer only, never the global `~/.claude/`.
- **P2** — emitted constitution usable with zero manual config.
- **P3** — the reference added to the generated CLAUDE.md must keep it ≤ 200 lines.
- **P4** — idempotent / write-once; never clobber an edited constitution.
- **P5** — domain-adapted content, not a generic dump.
- **P6** — minimal implementation: one template + one plan entry + one reference line; no new abstraction.
- **P7** — the emitted constitution stays tight (context cost is paid every session in the generated env).

## Acceptance Criteria

- [ ] Generating an env produces `<output>/.planning/CONSTITUTION.md`.
- [ ] The constitution is written only to the project layer, never to global `~/.claude/`.
- [ ] The emitted constitution contains universal-core principles AND ≥1 domain-specific principle for the detected domain.
- [ ] The generated `CLAUDE.md` references `.planning/CONSTITUTION.md` and remains ≤ 200 lines.
- [ ] Re-running the generator over an env with an existing, edited `CONSTITUTION.md` leaves it byte-identical (empty diff).
- [ ] The emitted constitution is usable with zero manual edits and is ≤ ~50 lines.

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                                             |
|--------------------|-------|------|--------|---------------------------------------------------|
| Goal Clarity       | 0.90  | 0.75 | ✓      | Specific outcome: generator emits + CLAUDE.md refs |
| Boundary Clarity   | 0.92  | 0.70 | ✓      | Explicit out-of-scope (B, retrofit, editor)       |
| Constraint Clarity | 0.88  | 0.65 | ✓      | Constitution P1–P7 bind the design                |
| Acceptance Criteria| 0.85  | 0.70 | ✓      | 6 falsifiable checkboxes                           |
| **Ambiguity**      | 0.11  | ≤0.20| ✓      | Gate passed                                        |

Status: ✓ = met minimum, ⚠ = below minimum (planner treats as assumption)

## Interview Log

Interview auto-resolved per user delegation ("decide tú"); decisions grounded in this repo's CONSTITUTION.md (the live constitution gate fired during this spec — first end-to-end validation of phase B).

| Round | Perspective     | Question summary                          | Decision locked                                                        |
|-------|-----------------|-------------------------------------------|-----------------------------------------------------------------------|
| 1     | Researcher      | How does the generator emit files today?  | Jinja2 templates + GenerationPlan + idempotent merge (Phase 3)        |
| 2     | Simplifier      | Minimum viable A?                          | 1 template + 1 plan entry + 1 CLAUDE.md ref line — no new abstraction |
| 3     | Boundary Keeper | Content: generic vs domain-adapted?       | Hybrid: universal core + domain-specific principles (P5)              |
| 3     | Boundary Keeper | Re-gen behavior on an edited constitution?| Write-once — never overwrite (P4); create only if absent             |
| 4     | Constitution    | Does the SPEC comply with CONSTITUTION.md?| Yes — P1–P7 mapped into Constraints; gate passed                      |

---

*Phase: 06-constitution-generation*
*Spec created: 2026-06-09*
*Next step: /gsd-discuss-phase 6 — implementation decisions (template structure, domain-principle source, write-once mechanism)*
