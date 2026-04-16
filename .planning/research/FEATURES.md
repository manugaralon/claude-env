# Features Research

**Domain:** Claude Code environment generator
**Researched:** 2026-04-15
**Confidence:** HIGH (Claude Code official docs) / MEDIUM (scaffolding comparison) / HIGH (project spec)

---

## Table Stakes

Features users expect. Missing = tool feels incomplete or untrustworthy.

- **Domain detection from input** — Parse freeform text or structured spec and identify the technical domain (web, mobile, data, infra, CLI, etc.) without user having to label it.
  - Complexity: medium
  - Dependencies: none
  - Rationale: Every scaffolding tool (Yeoman, Copier, Cookiecutter) uses detection or Q&A to drive template selection. Without it, output is generic and useless.

- **Two-layer output (global + per-project)** — Generate both `~/.claude/` (cross-project conventions, shared skills) and `.claude/` (domain-specific agents, project CLAUDE.md, project skills).
  - Complexity: medium
  - Dependencies: domain detection
  - Rationale: Official Claude Code architecture distinguishes these two scopes. Flattening both into one layer produces conflicts and configuration drift.

- **CLAUDE.md generation** — Produce a project CLAUDE.md that passes the 200-line constraint. Must include only what Claude cannot infer from code: non-obvious bash commands, project-specific conventions, workflow rules, architecture decisions.
  - Complexity: medium
  - Dependencies: domain detection
  - Rationale: CLAUDE.md is the entry point for every session. Bloated or absent CLAUDE.md is the single most common cause of degraded Claude performance (official docs: "if your CLAUDE.md is too long, Claude ignores half of it").

- **Skills generation** — Produce `.claude/skills/` directory with domain-appropriate SKILL.md files. Skills encode reusable workflows (fix-issue, create-pr, run-migrations) that are auto-triggered or manually invoked.
  - Complexity: medium
  - Dependencies: domain detection, CLAUDE.md generation
  - Rationale: Skills are the primary extensibility mechanism in Claude Code. Environments without skills require manual prompting for every workflow.

- **Subagents generation** — Produce `.claude/agents/` with domain-appropriate agents (e.g., security-reviewer, test-writer, db-migration-reviewer). Each agent gets its own context, tools list, and model assignment.
  - Complexity: medium
  - Dependencies: domain detection
  - Rationale: Subagents are how Claude Code keeps the main context clean during investigation. Without project-tuned subagents, users either pollute main context or never use them.

- **Hooks generation** — Produce `.claude/settings.json` with hooks for deterministic enforcement: lint-after-edit, block-writes-to-migrations, run-typecheck. Hooks are the guarantee layer — unlike CLAUDE.md instructions (advisory), hooks are enforced.
  - Complexity: medium
  - Dependencies: domain detection
  - Rationale: Official Claude Code docs explicitly distinguish hooks (deterministic) from CLAUDE.md (advisory). Environments without hooks rely on Claude following instructions every time — which it does not.

- **Plan→execute→verify pattern embedded** — Generated CLAUDE.md and skills must encode the explore→plan→implement→commit workflow. This is the single highest-leverage behavior change per official Claude Code docs.
  - Complexity: low
  - Dependencies: CLAUDE.md generation
  - Rationale: Without explicit embedding, developers revert to chatbot-style usage and lose most of the value.

- **Context management rules embedded** — Generated CLAUDE.md includes `/clear` protocol, compact instructions ("when compacting, preserve X"), and subagent delegation patterns for investigation tasks.
  - Complexity: low
  - Dependencies: CLAUDE.md generation
  - Rationale: Context window degradation is the primary failure mode in Claude Code sessions. Every environment must address this.

- **CLI invocability as a Claude Code skill** — The tool itself must be invocable as `/skill-name` from any project directory inside Claude Code, not just as a standalone script.
  - Complexity: medium
  - Dependencies: none
  - Rationale: Stated requirement in PROJECT.md. Without this, every bootstrapping requires leaving the Claude Code workflow.

- **Auto-improvement loop embedded (lessons.md pattern)** — Generated environments include the lessons.md pattern: after corrections, write the failure pattern and prevention to a file that is read at session start.
  - Complexity: low
  - Dependencies: CLAUDE.md generation
  - Rationale: This is the only mechanism that improves Claude behavior with use. Without it, every session starts from zero.

- **Idempotent generation** — Running the generator twice on the same project does not duplicate entries, overwrite manual customizations, or corrupt existing `.claude/` structure.
  - Complexity: medium
  - Dependencies: all generation steps
  - Rationale: Standard expectation from any scaffolding tool. Copier and Cookiecutter both address this. Missing it makes the tool unsafe to re-run.

- **Dry-run mode** — Show what would be generated without writing files. Mandatory for any tool that touches project configuration.
  - Complexity: low
  - Dependencies: none
  - Rationale: Developers will not trust a tool that writes files without preview. Yeoman and Copier both include this.

---

## Differentiators

Features that set this tool apart. Not universally expected, but high value when present.

- **Trace2Skill integration** — After an initial generation, provide a workflow skill that runs the Trace2Skill pipeline: collects execution traces from real Claude sessions, dispatches analyst subagents to extract lessons, and merges them back into the project skills. Skills evolved from real traces outperform hand-written ones by up to 57 percentage points on benchmark tasks (Trace2Skill paper, arXiv 2603.25158).
  - Why differentiating: No existing Claude environment generator implements self-improving skills. This turns the environment from a static artifact into a compounding asset.
  - Complexity: high
  - Dependencies: skills generation, subagents generation

- **Expert audit agent embedded** — Generated environment includes an audit subagent that validates the generated CLAUDE.md, skills, and hooks before the developer starts work. Catches: CLAUDE.md over 200 lines, skills without `disable-model-invocation` on side-effect workflows, missing hooks for deterministic rules, contradictions between CLAUDE.md and hook configuration.
  - Why differentiating: Prevents environment misconfiguration silently corrupting weeks of work. No scaffolding tool in the surveyed ecosystem has a post-generation validator with domain knowledge.
  - Complexity: medium
  - Dependencies: all generation steps

- **Input duality: raw idea vs structured spec** — Accept both a freeform idea paragraph and a structured technical spec document. Route each through a different analysis path before domain detection.
  - Why differentiating: Cookiecutter and Copier expect structured template variables. Accepting a raw idea and doing the interpretation is a step above.
  - Complexity: medium
  - Dependencies: domain detection

- **KB-backed generation (SECONDBRAIN integration)** — Generation engine queries the SECONDBRAIN KB (15+ entries on Claude Code best practices) to produce environment content that reflects accumulated real-world knowledge, not just template defaults.
  - Why differentiating: The environment generator encodes compounding knowledge from real usage. Every new KB entry improves all future generated environments.
  - Complexity: medium
  - Dependencies: SECONDBRAIN query protocol, domain detection

- **Separation of global onboarding from per-project bootstrapping** — CLI wizard for one-time global `~/.claude/` setup (identity, cross-project conventions, global skills). Separate skill invocation for per-project bootstrapping. These are different interactions with different frequencies.
  - Why differentiating: Existing tools treat both as the same operation. The separation respects that global setup happens once but project bootstrapping happens repeatedly.
  - Complexity: low
  - Dependencies: two-layer output

- **Generated CLAUDE.md quality enforcer** — Built-in linter that rejects any generated CLAUDE.md over 200 lines, flags lines Claude can infer from code, detects self-evident platitudes ("write clean code"), and enforces import syntax for cross-referencing additional files with `@path` syntax.
  - Why differentiating: The 200-line constraint is well-known in the Claude Code community but no generator enforces it programmatically.
  - Complexity: low
  - Dependencies: CLAUDE.md generation

---

## Anti-Features (deliberately NOT build)

Things to explicitly exclude. Building these would dilute focus or create maintenance burden without proportional value.

- **GUI / web interface** — Out of scope per PROJECT.md. Target user is a developer in a terminal. A GUI adds frontend development overhead and maintenance surface without reaching a different user.
  - What to do instead: Clear CLI UX with dry-run, verbose mode, and human-readable output.

- **Multi-user / team sync** — Sharing environments across a team introduces merge conflicts, permissions questions, and versioning complexity. v1 is single-developer.
  - What to do instead: Generate a `.gitignore`-annotated `CLAUDE.local.md` for personal overrides alongside a team-shareable `CLAUDE.md`.

- **Automated environment updates on code changes** — File watcher that regenerates skills or CLAUDE.md when source code changes would produce noisy, low-quality regenerations. Environment evolution should be intentional.
  - What to do instead: Provide an explicit `/update-env` skill that the developer invokes when they want a re-evaluation.

- **IDE plugins (VS Code extension, etc.)** — Claude Code CLI is the runtime. IDE integration duplicates Claude Code's existing IDE integration without adding value.
  - What to do instead: Ensure the skill is invocable from within Claude Code's terminal, which works inside any IDE.

- **Template registry / marketplace** — A public registry of environment templates for different stacks adds governance, versioning, and curation burden. The target is opinionated generation for a known user profile.
  - What to do instead: Local template library with clear extension points. If a registry becomes necessary, it can be layered on top later.

- **Interactive wizard for every option** — Yeoman's long Q&A flows are cited as friction in the ecosystem. If domain detection is good, most choices should be inferred, not asked.
  - What to do instead: Ask only when ambiguous. One-question max per domain. Pre-fill defaults with confidence level shown.

- **Automatic version pinning in generated environments** — Pinning specific Claude model versions or skill format versions in generated files creates maintenance debt. The environment should work with current Claude Code without version coupling.
  - What to do instead: Generate environments that work with current Claude Code conventions; document the convention version used in a comment, not as a hard pin.

---

## Feature Dependencies

```
Input parsing (raw idea / structured spec)
  └── Domain detection
        ├── CLAUDE.md generation
        │     ├── Plan→execute→verify embedding
        │     ├── Context management rules embedding
        │     └── Auto-improvement loop (lessons.md)
        ├── Skills generation
        │     └── Trace2Skill workflow skill (post-generation, optional)
        ├── Subagents generation
        │     └── Expert audit agent
        └── Hooks generation
              └── Idempotent generation (applies to all file outputs)

Two-layer output (global + per-project)
  └── Separation of global onboarding CLI wizard vs per-project skill

All generation steps
  └── Dry-run mode (wraps all file writes)
  └── CLAUDE.md quality enforcer (lints CLAUDE.md output)
  └── KB-backed generation (reads SECONDBRAIN before generating)
```

---

## MVP Recommendation

Prioritize for v1:

1. Domain detection from input (both input forms)
2. Two-layer output structure (global + per-project)
3. CLAUDE.md generation with 200-line enforcer
4. Skills generation (3-5 domain-appropriate skills)
5. Subagents generation (2-3 domain-appropriate agents)
6. Hooks generation (lint + typecheck by default)
7. Plan→execute→verify + context management embedded
8. Auto-improvement loop (lessons.md pattern)
9. Dry-run mode
10. CLI skill invocability

Defer to v2:

- Trace2Skill integration — High value but high complexity; requires real execution traces to be useful, meaning it needs v1 deployed and in use first.
- KB-backed generation — Useful but requires SECONDBRAIN query path to be stable; can be added as an enhancement after core generation works.
- Expert audit agent — Valuable, but requires all generation steps to exist before an auditor can validate them. Phase 2 after generation is stable.

---

## Sources

- [Claude Code Best Practices — Official Docs](https://code.claude.com/docs/en/best-practices) — HIGH confidence
- [Claude Code Customization Guide: CLAUDE.md, Skills, Subagents](https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/) — MEDIUM confidence
- [Awesome Claude Code — Community Ecosystem](https://github.com/hesreallyhim/awesome-claude-code) — MEDIUM confidence
- [Trace2Skill Paper — arXiv 2603.25158](https://arxiv.org/abs/2603.25158) — HIGH confidence
- [Copier: template lifecycle management](https://copier.readthedocs.io/en/stable/comparisons/) — MEDIUM confidence
- [Cookiecutter vs Yeoman comparison](https://www.opslevel.com/resources/cookiecutter-vs-yeoman-choosing-the-right-scaffolder-for-your-service) — MEDIUM confidence
