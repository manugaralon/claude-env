# Pitfalls Research

**Domain:** Claude environment generation / scaffolding tools
**Researched:** 2026-04-15

---

## Generated CLAUDE.md Exceeds the Instruction Budget

- **Warning signs**: Generated file exceeds 150–200 lines; multiple sections covering "standard conventions" Claude already follows by default; includes long prose explanations rather than terse rules; includes API docs inline rather than linking to them.
- **Prevention**: Hard-cap generator output at 200 lines (matches project requirement). Apply a "would removing this cause Claude to make a mistake?" filter for every generated line before writing. Prefer `@path/to/import` references to off-load supplementary content. Use skills for domain knowledge that is only relevant sometimes — CLAUDE.md is for what applies every session.
- **Phase**: Core generation engine (first phase producing CLAUDE.md output). The 200-line test should be a CI assertion, not a manual check.
- **Severity**: high

Official source: [Claude Code best practices — CLAUDE.md](https://code.claude.com/docs/en/best-practices) — "Bloated CLAUDE.md files cause Claude to ignore your actual instructions."

---

## Generated Skills Are Never Invoked (Autodiscovery Failure)

- **Warning signs**: Skills exist in `.claude/skills/` but Claude never references or invokes them without explicit prompting; generated skill descriptions are vague or overlap with CLAUDE.md content; skill `description` frontmatter doesn't contain action-triggering language Claude can match against.
- **Prevention**: The `description` field in `SKILL.md` frontmatter is the primary autodiscovery signal — generate it as a precise verb-phrase that matches common invocation triggers (e.g. "Fix a GitHub issue end-to-end" not "GitHub helper"). For workflow skills with side effects, set `disable-model-invocation: true` so they are only triggered explicitly. Include a mention of available skills and when to use them in the generated CLAUDE.md so Claude has the list at session start.
- **Phase**: Skills generation. Additionally, the expert audit agent should verify that each skill's description is distinct and non-overlapping.
- **Severity**: high

Source: [GitHub issue #24110](https://github.com/anthropics/claude-code/issues/24110) — documented pattern of Claude ignoring project-level skills without strong CLAUDE.md cues.

---

## Subagents Don't Inherit Project Skills (Scope Boundary Confusion)

- **Warning signs**: Subagent is generated to use a project skill, but at runtime the skill is unavailable or the subagent loads a global version instead; tool calls from subagents behave as if no project context exists.
- **Prevention**: Skills are not automatically injected into spawned subagent contexts — they must be explicitly listed in the `tools` or `skills` field of the agent definition file, or the agent must be given filesystem access and instructed to read `.claude/skills/`. Generate agent `.md` files with explicit `skills:` references to any project-level skills they depend on. Document this in the generated environment so future developers don't add skills and wonder why agents miss them.
- **Phase**: Subagent generation. Test this in the expert audit agent which validates the environment before handoff.
- **Severity**: high

Source: [GitHub issue #10061](https://github.com/anthropics/claude-code/issues/10061) — subagents loading global instead of project skills; [issue #32910](https://github.com/anthropics/claude-code/issues/32910) — undocumented filesystem discovery vs. injected skills discrepancy.

---

## hooks in settings.json Fail Silently

- **Warning signs**: Generated `settings.json` has hooks defined but `/hooks` inside Claude Code shows "No hooks configured yet"; hooks contain `$HOME` or other shell variables that are not expanded in JSON; hook scripts exit with code 1 when they should exit 2 to block execution; JSON has a trailing comma.
- **Prevention**: Generate hooks with hardcoded absolute paths — never shell variables. Generate a validation step in setup.sh that runs `/hooks` equivalent check (or `cat .claude/settings.json | python3 -m json.tool`). Document that only exit code `2` blocks a PreToolUse hook; exit 1 is treated as a non-blocking error. Use `jq` to validate the settings JSON before writing. Add a verification task in the generated environment that confirms hooks are loaded.
- **Phase**: Hooks generation and the CLI wizard / setup.sh phase. The expert audit agent should parse settings.json with a JSON validator, not just check file existence.
- **Severity**: high

Sources: [GitHub issue #2835](https://github.com/anthropics/claude-code/issues/2835) — silent failure on malformed JSON; [issue #11544](https://github.com/anthropics/claude-code/issues/11544) — hooks not loading without any error; [DEV article: 5 hook mistakes](https://dev.to/yurukusa/5-claude-code-hook-mistakes-that-silently-break-your-safety-net-58l3).

---

## Two-Layer Conflict: Global and Per-Project Settings Collide

- **Warning signs**: A rule in `~/.claude/CLAUDE.md` contradicts a rule in `.claude/CLAUDE.md`; hooks defined globally overlap with project-level hooks causing double execution; a skill name exists in both `~/.claude/skills/` and `.claude/skills/` with different behavior.
- **Prevention**: Design the generator to be explicit about the layering contract: global layer owns cross-project conventions; project layer owns domain-specific behavior. Generate a comment block at the top of each CLAUDE.md stating its scope and what the other layer is responsible for. For skills and agents, use distinct names across layers — never the same slug at both levels. In the generator, check if a global skill with the same name already exists before writing a project-level one, and warn (or refuse) on collision.
- **Phase**: Two-layer output design phase (global + per-project generation). Also relevant to the CLI wizard global onboarding.
- **Severity**: high

---

## Re-running the Generator Overwrites Manual Edits (Non-Idempotent Output)

- **Warning signs**: Developer has added rules to the generated CLAUDE.md; re-running the generator on the same project overwrites them; hooks added manually to settings.json are lost; developer stops re-running generator because they fear data loss.
- **Prevention**: Generated files must be clearly marked with a header section owned by the generator and a user section that is never touched on re-run. Use a merge strategy: parse existing file, preserve user-added sections below a sentinel comment (e.g. `# USER SECTION — DO NOT REGENERATE BELOW`), regenerate only the header block. For settings.json hooks, append rather than overwrite — merge the hooks array with de-duplication by hook name/matcher. Document regeneration behavior explicitly in the generated environment.
- **Phase**: Core generation engine. This constraint should be designed in at the start, not retrofitted — retrofitting merge logic is significantly harder.
- **Severity**: high

---

## Domain Detection Produces Overfitted or Generic Environments

- **Warning signs**: A Python data project gets a web backend environment; a monorepo gets a single-project environment; the generated environment looks identical for all projects (template was not adapted); generated subagents reference technologies not in the project.
- **Prevention**: Domain detection should be evidence-based: scan actual files (`package.json`, `pyproject.toml`, `go.mod`, directory structure, import patterns) rather than relying on user description alone. If input is a raw idea with no codebase yet, detect intent from terminology and generate a provisional environment that includes a note flagging the detected domain for user confirmation. Build domain detection as a separate, testable module — not inline with template rendering — so it can be validated independently.
- **Phase**: Domain detection module (early phase). The expert audit agent should flag environments where detected domain and generated artifacts don't match.
- **Severity**: medium

---

## Generated CLAUDE.md Embeds Knowledge That Becomes Stale

- **Warning signs**: Generated CLAUDE.md contains specific version numbers, API endpoints, or dependency names inline; six months after generation, the rules reference deprecated patterns; developer doesn't know which rules came from the generator vs. which they added.
- **Prevention**: Generated rules should be behavioral constraints ("use Pydantic v2 models, not dataclasses") not version-pinned facts ("use Pydantic 2.7.4"). For things that do change (framework conventions, API shapes), prefer `@docs/link` or a skill that instructs Claude to check current docs rather than hardcoding. Mark the generation timestamp in the file header so staleness is visible.
- **Phase**: Template design for all generated artifacts.
- **Severity**: medium

---

## Trace2Skill Integration Extracts Fragile or Non-Transferable Rules

- **Warning signs**: Extracted skill rules work only for the specific project they were extracted from; rules reference project-specific file paths or variable names; extracted skills conflict with each other (parallel extraction without conflict resolution); skills that worked for one model stop working after a Claude upgrade.
- **Prevention**: Trace2Skill requires a diverse pool of execution traces — not just one or two runs. Implement the full parallel fleet + hierarchical consolidation pattern from the paper rather than a simplified sequential extraction. During extraction, strip project-specific identifiers (paths, names) and replace with abstract patterns. Run extracted skills through a conflict-detection pass before writing. Accept that the first version of embedded best practices will be hand-authored; Trace2Skill integration should come in a later phase once the system has real runs to extract from.
- **Phase**: Trace2Skill integration (explicitly a later phase — do not block v1 on it).
- **Severity**: medium

Source: [Trace2Skill paper](https://arxiv.org/abs/2603.25158) — "synthesizing skills relying solely on parametric knowledge yields limited benefits"; sequential overfitting to non-generalizable trajectory-local lessons is a documented failure mode.

---

## Expert Audit Agent Has No Ground Truth to Validate Against

- **Warning signs**: Audit agent reports "looks good" for a generated environment that has misconfigured hooks, wrong skill descriptions, or domain mismatch; audit is subjective — no concrete assertions; audit results are not surfaced to the developer in an actionable form.
- **Prevention**: The audit agent should run concrete checks, not just LLM judgment: JSON validity of settings.json, line count of CLAUDE.md, presence of required frontmatter fields in skill and agent files, absence of duplicate skill names across global and project layers, exit code semantics in hook scripts. LLM judgment is a secondary layer on top of structural checks, not a substitute. Audit output must be in a structured format (pass/fail per check with fix instructions), not prose.
- **Phase**: Expert audit agent design. Define the checklist before implementing the agent.
- **Severity**: medium

---

## Generated Environment Is Invocable as a Skill But Has No Isolation

- **Warning signs**: Skill invoked from Project A accidentally writes to `~/.claude/` in a destructive way (overwrites global CLAUDE.md instead of extending it); generator invoked without a project root context writes files to unexpected locations; re-entrant invocation (skill calling itself) causes partial state.
- **Prevention**: The generator skill must detect its working directory and explicitly scope writes: per-project artifacts go to `$(pwd)/.claude/`, global artifacts go to `~/.claude/` only with explicit user confirmation. Never overwrite `~/.claude/CLAUDE.md` — only append or merge. Add a dry-run mode that prints what would be written before writing anything. Make the global onboarding step (CLI wizard) separate from the per-project skill invocation so they can't be confused.
- **Phase**: Skill invocation design and CLI wizard. The isolation boundary between global and per-project must be enforced in code, not just documented.
- **Severity**: high

---

## Phase-Specific Summary

| Phase topic | Likely pitfall | Mitigation |
|---|---|---|
| CLAUDE.md generation | Template bloat exceeds instruction budget | Hard-cap at 200 lines; run assertion |
| Skills generation | Vague descriptions prevent autodiscovery | Verb-phrase descriptions; mention skills in CLAUDE.md |
| Subagent generation | Skills not injected into spawned contexts | Explicit `skills:` field in agent definitions |
| Hooks generation | Silent JSON/exit-code failures | JSON validation; hardcoded paths; exit 2 documentation |
| Two-layer output | Global/project rule collision | Scope contract; name collision detection |
| Re-run behavior | Overwrites user edits | Sentinel-based merge strategy from day one |
| Domain detection | Overfitting or generic output | File-scan evidence; separate testable module |
| Trace2Skill integration | Fragile single-trace extraction | Diverse pool + hierarchical consolidation; defer to later phase |
| Expert audit agent | No concrete assertions | Structural checks first; LLM judgment second |
| Skill invocation isolation | Destructive writes to global layer | Working-directory scoping; dry-run mode |
