---
source: https://github.com/obra/superpowers
type: github-repo
evaluated_date: 2026-05-06
verdict: cherry-pick
tags: [framework, methodology, multi-runtime, skills-framework]
extracts: [brainstorming-technique, test-driven-development, systematic-debugging, subagent-driven-development, writing-plans-task-decomposition, code-review-patterns, git-worktrees-isolation, skill-composition-pattern, multi-runtime-abstraction, using-superpowers-bootstrap]
---

# Obra/Superpowers Deep Evaluation

## Executive Summary

**Superpowers is a mature, production-grade methodology framework for multi-runtime AI agents** — 14 skills + enforcement hooks spanning TDD, debugging, brainstorming, planning, code review, and subagent orchestration. It ships across 8 platforms (Claude Code, Codex, Cursor, OpenCode, Gemini CLI, Factory Droid, Copilot CLI, GitHub CLI) via unified skill definitions and runtime-agnostic frontmatter.

**Recommendation: CHERRY-PICK, not fork-as-base.** Superpowers excels at *atomic workflow patterns* (brainstorming, TDD, systematic debugging) but encodes strong opinions about *session structure* (hard gates, "human partner" terminology, rigid skill priority trees) that conflict with GSD's phase-driven methodology and claude-env's profile-driven customization. You can absorb ~6-8 high-value skills without adopting its entire framework. Integration would require ripping out its mandatory skill invoking system and replacing it with GSD-aware conditional triggering.

**Unique value over mattpocock/anthropics-skills:**
- Multi-runtime abstraction layer (hooks.json, platform detection, bootstrap injection)
- Enforcement model (hard gates that block action until preconditions met)
- Subagent-driven-development pattern with two-stage review (spec compliance + code quality)
- Adversarial skill testing methodology (pressure testing with subagents)
- Mature codebase stability (v5.1.0, 94% PR rejection rate = high standards)

---

## 1. Methodology Structure

### Core Flow (Mandatory Sequence)

Superpowers enforces a rigid, linear workflow at session bootstrap (injected by `hooks/session-start`):

```
1. using-superpowers (bootstrap)
   ↓ [HARD-GATE: Must invoke Skill tool before any response]
2. brainstorming (if creative work)
   ↓ [Hard-gate: Design approval REQUIRED before touching code]
3. using-git-worktrees (isolation)
   ↓
4. writing-plans (task decomposition)
   ↓
5. subagent-driven-development OR executing-plans (execution)
   ↓
6. requesting-code-review (spec compliance review)
   ↓
7. finishing-a-development-branch (merge decision)
```

**vs. GSD phases:**

| GSD | Superpowers | Alignment |
|-----|-------------|-----------|
| **VERTEBRAL** (discover, design, plan) | brainstorming → writing-plans | High — both front-load requirements clarity |
| **EXECUTION** (implement, verify, iterate) | subagent-driven-development, TDD | High — both use test-first approach |
| **INTEGRATION** (review, ship, document) | requesting-code-review, finishing-a-development-branch | Medium — superpowers is more rigid |
| **Phase documentation** | —No built-in phase artifact pattern— | Gap — superpowers has no PHASE.md equivalent |

**Key difference:** GSD is *phase-oriented* (each phase produces artifacts: REQUIREMENTS.md, PLAN.md, PHASE_ARTIFACTS/). Superpowers is *skill-oriented* (skills auto-trigger based on conversation context, not explicit phase state). They can coexist if you:
- Keep GSD as project-level backbone (PROJECT.md, phases)
- Use superpowers skills within the EXECUTE phase (TDD, debugging, code review)
- Suppress automatic skill triggering outside EXECUTE phase

### Instruction Priority

From `using-superpowers/SKILL.md`:
```
1. User's explicit instructions (CLAUDE.md, GEMINI.md, AGENTS.md, direct requests)
2. Superpowers skills (override default system behavior)
3. Default system prompt
```

This is **compatible with claude-env** if you define GSD + superpowers rules in `.claude/CLAUDE.md`:
```
When in VERTEBRAL phase: skip brainstorming/writing-plans; use GSD:spike instead
When in EXECUTE phase: mandatory TDD, code-review, systematic-debugging
```

---

## 2. Multi-Runtime Mechanism

Superpowers uses **three-layer abstraction:**

### Layer 1: Plugin Manifests (Harness-Specific Metadata)

```
.claude-plugin/plugin.json        (Claude Code)
.codex-plugin/plugin.json         (OpenAI Codex)
.cursor-plugin/plugin.json        (Cursor IDE)
.opencode/plugins/superpowers.js  (OpenCode)
GEMINI.md                         (Gemini CLI)
```

Each manifest is **identical in content** but differs in **metadata structure** to match harness APIs. All point to the same `skills/` directory.

### Layer 2: SessionStart Hook (Bootstrap Injection)

`hooks/session-start` (bash script, ~60 lines):

1. Detects harness via environment variables:
   - `CLAUDE_PLUGIN_ROOT` → Claude Code
   - `CURSOR_PLUGIN_ROOT` → Cursor (may also set CLAUDE_PLUGIN_ROOT)
   - `COPILOT_CLI` → GitHub Copilot CLI
   - Default → OpenCode/generic

2. Reads `skills/using-superpowers/SKILL.md` at runtime

3. **Escapes for JSON** and wraps in platform-specific envelope:
   ```bash
   if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
     printf '{"additional_context": "%s"}\n' "$escaped_content"
   elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
     printf '{"hookSpecificOutput": {"additionalContext": "%s"}}\n' "$escaped_content"
   else
     printf '{"additionalContext": "%s"}\n' "$escaped_content"
   fi
   ```

4. Injects into session context (not system prompt) to avoid token bloat

### Layer 3: Tool Mapping (Runtime Tool Equivalences)

Skill frontmatter uses **Claude Code tool names**:
```markdown
- Read (file reading)
- Write (file creation)
- Edit (file editing)
- Bash (run commands)
- Skill (invoke a skill)
- Task (dispatch subagent)
```

Platform-specific mappings live in `skills/using-superpowers/references/`:

**`gemini-tools.md`:**
```
Read       → read_file
Write      → write_file
Edit       → replace
Bash       → run_shell_command
Skill      → activate_skill
Task       → @agent-name or @generalist
```

**`codex-tools.md` / `copilot-tools.md`:** Similar mappings for OpenAI/Microsoft ecosystems.

### Why This Matters for claude-env

**Superpowers' abstraction is read-only.** It doesn't:
- Modify platform settings or config
- Create new tools
- Abstract tool creation

You can **consume** superpowers' multi-runtime abstraction as a model for how to distribute skills, but can't directly fork it because:
1. The hook mechanism is tightly coupled to skill content (SKILL.md reading at runtime)
2. Platform manifests are generated/synced via private scripts (`sync-to-codex-plugin`)
3. No generic "plugin manifest generator" — each platform has manual tuning

**For claude-env:** You could create a plugin manifest generator that points to your generated skills, using superpowers' structure as a template.

---

## 3. Skills Inventory & Descriptions

**14 Core Skills** (skill frontmatter: `name` + `description`):

| Name | Trigger | Purpose | Type |
|------|---------|---------|------|
| **using-superpowers** | Session start (bootstrap) | Teach agent how to find/invoke skills; hard-gate on Skill tool | Rigid |
| **brainstorming** | "build X", "add feature" | Socratic design refinement; hard-gate on design approval before code | Rigid |
| **writing-plans** | After design approval | Decompose spec into bite-sized tasks (2-5 min each); explicit file→task mapping | Rigid |
| **test-driven-development** | During implementation | RED-GREEN-REFACTOR cycle; hard-gate: code written before test = delete it | Rigid |
| **systematic-debugging** | Any bug/test failure | 4-phase root cause process before fixes allowed | Rigid |
| **verification-before-completion** | Before claiming success | Run verification commands; evidence before assertions | Rigid |
| **requesting-code-review** | After task/feature completion | Pre-review checklist; dispatch spec-compliance + code-quality reviewers | Flexible |
| **receiving-code-review** | Getting feedback | Verify feedback rigor before implementing suggestions | Flexible |
| **using-git-worktrees** | Before feature work | Create isolated workspace; native tool preference + git fallback | Flexible |
| **finishing-a-development-branch** | Work complete, tests pass | Merge/PR/keep/discard decision; provenance-aware cleanup | Flexible |
| **subagent-driven-development** | With implementation plan, same session | Dispatch fresh agent per task; two-stage review (spec, then quality); continuous execution | Rigid |
| **dispatching-parallel-agents** | 2+ independent failures/tasks | Parallel subagent dispatch with focused scopes; non-blocking parallelization | Flexible |
| **executing-plans** | With plan, separate session | Batch execution with human checkpoints between batches | Flexible |
| **writing-skills** | Creating/editing skills | TDD for documentation; pressure testing with subagents | Rigid (meta) |

**Key observations:**
- 7 **Rigid** skills (hard gates, non-negotiable structure)
- 7 **Flexible** skills (patterns, adapt to context)
- All assume fresh subagent dispatch via `Task()` tool (scalable but verbose)

---

## 4. Frontmatter Conventions

### Triggering Model

Superpowers uses **YAML frontmatter + auto-triggering heuristic**:

```yaml
---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---
```

**Rule:** If description matches user intent ("implementing feature", "bugfix"), agent should invoke the skill.

Compare to mattpocock/anthropics-skills:
- **Anthropic**: Simple YAML, emphasis on when NOT to use (exceptions)
- **mattpocock**: Opinionated narrative preambles, contextual decisions
- **Superpowers**: Focus on *preconditions* and *hard gates* — describes **entry conditions** not just use cases

### Hard-Gate Pattern

Unique to superpowers — skills contain `<HARD-GATE>` blocks that define **blocking conditions**:

```markdown
<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, 
or take any implementation action until you have presented a design and the user 
has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>
```

This is **not a guideline** — it's a behavioral instruction. The skill itself becomes enforcement code. Violation examples:
- brainstorming: hard-gate blocks code until design approval
- test-driven-development: hard-gate blocks production code until failing test
- systematic-debugging: hard-gate blocks fixes until root cause found

---

## 5. Agents & Subagent Architecture

### Subagent Types

Superpowers doesn't use *named agents*. Instead, it uses **role-based dispatch with inline prompt templates**:

```markdown
Dispatch: Task (general-purpose)
With prompt template: skills/subagent-driven-development/implementer-prompt.md
```

The system supports three **conceptual roles** (not separate agents):

| Role | Purpose | Template |
|------|---------|----------|
| **Implementer** | Write code for one task | `implementer-prompt.md` |
| **Spec Reviewer** | Verify code matches spec | `spec-reviewer-prompt.md` |
| **Code Quality Reviewer** | Check for bugs, style, patterns | `code-quality-reviewer-prompt.md` |

**Subagent-driven-development workflow:**

```
For each task:
  1. Dispatch implementer subagent (full task spec + code context)
  2. If implementer asks questions → answer in same session, re-dispatch
  3. Dispatch spec-compliance reviewer
  4. If not approved → implementer fixes, re-review
  5. Dispatch code-quality reviewer
  6. If not approved → implementer fixes, re-review
  7. Mark task complete
After all tasks:
  8. Dispatch final code reviewer for entire implementation
  9. Invoke finishing-a-development-branch
```

**Council/delegation pattern:**
- No "council" per se, but **parallel-agents** skill enables concurrent dispatch for unrelated failures
- Each agent is isolated (fresh subagent per task, zero context inheritance)
- Two-stage review enforces *specification correctness* before *code quality* — ordering matters

### Why This Matters

Superpowers' subagent model is **orthogonal to GSD**:
- GSD phase artifacts (REQUIREMENTS.md, PLAN.md) provide context
- Superpowers subagents receive minimal context (just the task spec + code snippets)
- They're compatible if you pass GSD artifacts as context to subagents

---

## 6. Hooks & Enforcement

### Hook System

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start",
            "async": false
          }
        ]
      }
    ]
  }
}
```

**Execution:**
- `SessionStart` event fires on new session, clear, compact
- Matcher pattern: `startup|clear|compact` (any of these triggers)
- Runs `hooks/session-start` bash script synchronously
- Injects bootstrap content into session context

**Windows compatibility:** `hooks/run-hook.cmd` wraps the bash script for cmd.exe.

### Enforcement Mechanisms

1. **Bootstrap injection** (session-start hook)
   - Injects `using-superpowers/SKILL.md` into every session
   - Makes skill discovery immediate

2. **Hard-gates in skill content** (documented instructions)
   - Not automatically enforced — rely on agent discipline
   - E.g., "If you didn't watch the test fail, you don't know if it tests the right thing"

3. **No runtime validation** 
   - No config/schema validation
   - No tool blocking or permission gates
   - Enforcement is behavioral (the skill document teaches discipline)

### Legacy Cleanup

v5.1.0 removed:
- Deprecated slash commands (`/brainstorm`, `/execute-plan`, `/write-plan`)
- Named agent (`superpowers:code-reviewer`) → merged into prompt templates
- Integration sections in skills (legacy from pre-native-skills era)

---

## 7. License & Fork Viability

**MIT License** (Copyright 2025 Jesse Vincent)

**Fork is permissible, but:**

1. **Maintainer responsiveness:** High bar
   - Closing PRs within hours with detailed rejection reasons
   - 94% PR rejection rate (statistically rigorous)
   - Clear contribution guidelines (CLAUDE.md/AGENTS.md)

2. **Not accepting fork-specific changes upstream**
   - PR section explicitly forbids "rebrand the project, add fork-specific features, or merge fork branches"
   - If you fork, don't try to sync upstream

3. **Skill content philosophy diverges from Anthropic**
   - "Our internal skill philosophy differs from Anthropic's published guidance"
   - Won't accept "compliance" restructures of skills without eval evidence
   - They've "extensively tested and tuned our skill content for real-world agent behavior"

**Practical fork scenarios:**

If you fork superpowers as-is, you'd inherit:
- Hard gates as-is (not GSD-aware)
- Mandatory skill triggering on context match
- Subagent dispatch boilerplate (verbose, requires inline prompt templates)

You'd have to rip out:
- `hooks/session-start` → replace with GSD-aware conditional hooks
- `using-superpowers` → replace with `claude-env:skills-discovery`
- Hard gates → make optional based on GSD phase
- Subagent templates → integrate with `~/.claude/agents/` pipeline

**Not recommended.** Cherry-picking is simpler.

---

## 8. GSD Compatibility Analysis

### Specific Conflict Points

**File-level conflicts:**

| File | GSD Equivalent | Conflict? | Resolution |
|------|---|---|---|
| `skills/writing-plans/SKILL.md` | `gsd-plan-phase` | Medium | Superpowers assumes brainstorming happened; GSD assumes REQUIREMENTS.md exists. Can coexist if superpowers docs point to GSD artifacts. |
| `skills/brainstorming/SKILL.md` | `gsd-discuss-phase` | Medium | Different dialogue depth (superpowers: 1-at-a-time questions; GSD: bulk question generation). Use one or the other per project. |
| `hooks/session-start` | Global GSD hook (doesn't exist yet) | High | Superpowers' bootstrap is unconditional; GSD would want phase-aware conditional injection. |
| `skills/*/SKILL.md` | `~/.claude/skills/` | None | Both use same location; can coexist. Namespace collision only if both define `test-driven-development`. |

**Directory conflicts:** None. GSD lives in `.planning/` + `~/.claude/`; superpowers in `~/.claude/skills/`.

**Terminology conflicts:**
- Superpowers: "your human partner" (deliberate, non-negotiable)
- GSD: "the user", "stakeholder"
- No functional conflict, but tonal inconsistency

### Integration Strategy

To run both without friction:

1. **In `.claude/CLAUDE.md` (project-level):**
   ```markdown
   ## Skill Invocation Rules
   
   - **VERTEBRAL phase (discovery):** Use GSD:discuss-phase, NOT superpowers:brainstorming
   - **PLANNING phase:** Use GSD:plan-phase OR superpowers:writing-plans (choose one per project)
   - **EXECUTE phase:** Use superpowers:TDD, systematic-debugging, code-review (mandatory)
   - **INTEGRATION phase:** Use superpowers:requesting-code-review, finishing-a-development-branch
   ```

2. **Disable superpowers' bootstrap** if running GSD:
   ```bash
   # In ~/.claude/settings.local.json
   {
     "plugins": {
       "superpowers": {
         "auto-bootstrap": false  // If this flag exists (unlikely)
       }
     }
   }
   ```
   (Superpowers doesn't have this flag currently; you'd have to fork/patch the hook)

3. **OR: Run superpowers without bootstrap:**
   - Don't install superpowers plugin
   - Copy specific skill files to `~/.claude/skills/`
   - Invoke them manually with `/skill test-driven-development`

**Verdict:** Technically compatible with GSD if you manage phase-aware skill routing in CLAUDE.md. Not seamless without patching superpowers' hooks.

---

## 9. Unique Value (vs. mattpocock, anthropics-skills, addyosmani)

### Superpowers-Only Features

| Feature | Source | Maturity |
|---------|--------|----------|
| **Hard gates** (blocking gates in skill content) | Superpowers | Mature |
| **Multi-runtime single-codebase** (8 platforms, one skill dir) | Superpowers | Mature |
| **Subagent-driven-development** (two-stage review pattern) | Superpowers | Mature (v5.0.6+) |
| **Systematic debugging 4-phase** (detailed root-cause process) | Superpowers | Mature |
| **Skill TDD** (RED-GREEN-REFACTOR for documentation) | Superpowers | Mature (v5.0+) |
| **`using-git-worktrees` + environment detection** | Superpowers | Mature (v5.1.0: native tool preference) |
| **Inline self-review** (vs. subagent review loops) | Superpowers | Recent (v5.0.6: 25min → 30s) |
| **Pressure-testing subagents** | Superpowers | Mature (test methodology in skills) |

### Comparison Matrix

| Dimension | Superpowers | mattpocock | anthropics | addyosmani |
|-----------|---|---|---|---|
| **Skill count** | 14 core | ~8-10 | ~20+ (growing) | ~12 |
| **TDD rigor** | Hard gate | Recommended | Suggested | Documented |
| **Subagent patterns** | 2-stage review + dispatching | Single dispatch | Work in progress | Mentioned |
| **Multi-runtime** | 8 platforms, native | Claude Code only | Claude Code only | Claude Code only |
| **Enforcement hooks** | SessionStart bootstrap | Project hooks | Internal | Internal |
| **License** | MIT | MIT | Apache 2.0 | MIT |
| **Maintenance** | Active, opinionated | Active | Active | Moderate |
| **Skill philosophy** | Tested vs. Anthropic guidance | Opinionated | Anthropic-aligned | General |

---

## 10. Specific Items to Cherry-Pick

### High-Priority Extracts

**1. Brainstorming technique** (skills/brainstorming/SKILL.md)
```
What to take:
  - Visual companion optional offering
  - 2-3 approaches with trade-offs
  - Section-by-section design presentation
  - Design doc + user review loop
  
Keep:
  - Hard gate (optional for claude-env)
  - 8-step checklist
  
Modify:
  - Replace "writing-plans skill invoke" with "gsd-plan-phase invoke"
  - Add GSD REQUIREMENTS.md as output instead of design-doc
```

**2. Test-driven development** (skills/test-driven-development/SKILL.md)
```
What to take:
  - RED-GREEN-REFACTOR cycle visualization
  - "No production code without failing test" principle
  - Testing anti-patterns reference section
  - Exception-handling (throw-away prototypes, generated code)

Keep:
  - Hard gate structure
  - Iron Law enforcement language

Add:
  - GSD phase context (when in EXECUTE, TDD is mandatory)
```

**3. Systematic debugging** (skills/systematic-debugging/SKILL.md)
```
What to take:
  - 4-phase root cause investigation (Evidence gathering, Hypothesis, Instrumentation, Verification)
  - "No fixes without root cause first" principle
  - Defense-in-depth technique
  - Condition-based-waiting pattern (useful for flaky tests)
  - Multi-component system instrumentation pattern

Keep:
  - All of it — this skill is universally applicable

Supporting files:
  - defense-in-depth.md
  - test-pressure-*.md (reference scenarios)
```

**4. Subagent-driven-development** (skills/subagent-driven-development/SKILL.md)
```
What to take:
  - Two-stage review pattern (spec compliance → code quality)
  - Implementer/spec-reviewer/code-quality-reviewer roles
  - Per-task subagent dispatch (not context inheritance)
  - Continuous execution directive

Adapt for claude-env:
  - Replace Task() dispatch with ~/.claude/agents/ pipeline
  - Make GSD PLAN.md the task spec source
  - Add final integration review step

Keep as-is:
  - The review stage ordering (critical insight)
```

**5. Writing-plans task decomposition** (skills/writing-plans/SKILL.md)
```
What to take:
  - Bite-sized task granularity (2-5 min steps)
  - Explicit file→task mapping
  - Checkbox-tracked steps (- [ ])
  - Step structure: failing test → run → code → verify → commit

Adapt:
  - Point to GSD PLAN.md format instead of standalone
  - Make the plan a phase artifact (PHASE.md)
  
Keep:
  - All the task structure examples
```

**6. Code review patterns** (skills/requesting-code-review/, receiving-code-review/)
```
What to take:
  - Pre-review checklist (functionality, edge cases, tests)
  - Two-stage dispatch (spec → quality)
  - spec-reviewer-prompt.md, code-quality-reviewer-prompt.md templates
  - Receiving-code-review's "verify rigor before implementing" principle

Adapt:
  - Fold into ~/.claude/agents/code-reviewer.md
  - Point to GSD integration phase
```

**7. Using-git-worktrees + finishing-a-development-branch**
```
What to take:
  - Environment detection (GIT_DIR != GIT_COMMON for pre-existing worktrees)
  - Native tool preference (use harness worktree tool before git fallback)
  - Provenance-based cleanup (only remove worktrees created by script)
  - Merge/PR/keep/discard decision menu

Adapt:
  - Point to GSD milestone completion phase
  - Add documentation integration step
```

**8. Writing-skills meta-skill** (skills/writing-skills/SKILL.md)
```
What to take:
  - TDD for documentation (RED = subagent fails, GREEN = skill present, REFACTOR = close loopholes)
  - Pressure-testing methodology (adversarial scenarios)
  - Skill types taxonomy (Technique, Pattern, Reference)
  - SKILL.md frontmatter structure

Keep:
  - All of it — excellent meta-documentation
```

### Medium-Priority Extracts

**9. Dispatching-parallel-agents** (skills/dispatching-parallel-agents/SKILL.md)
```
Use when:
  - Multiple independent test failures
  - Parallel debugging sessions

Note: Superpowers' task dispatch is verbose. Consider if you can integrate
with a higher-level parallel execution framework (Claude mem, batch API).
```

**10. Verification-before-completion** (skills/verification-before-completion/SKILL.md)
```
Single-page skill: "Run verification commands; evidence before assertions"
Integrates well with GSD:verify-work phase.
Keep as-is, reference in CLAUDE.md.
```

### Low-Priority Extracts

**11. Executing-plans** (vs. subagent-driven-development)
```
Difference from SDD: Batch execution with human checkpoints between batches.
Only useful if you want synchronous, human-supervised execution.
For claude-env: superpowers:SDD is better abstraction.
```

**12. Receiving-code-review** (skills/receiving-code-review/SKILL.md)
```
"Verify feedback rigor before implementing suggestions"
Useful pattern but lightweight. Reference, don't extract.
```

---

## 11. Recommendation: CHERRY-PICK

### Why NOT Fork-as-Base

1. **Hard gates are non-negotiable in superpowers**
   - GSD phases need conditional triggering (VERTEBRAL vs EXECUTE vs INTEGRATION)
   - Forking would require ripping out 40% of skill content and rewriting

2. **Bootstrap mechanism is rigid**
   - `hooks/session-start` injects unconditionally
   - GSD wants phase-aware, optional injection
   - Fork would need custom hook system

3. **Subagent dispatch is verbose**
   - Requires inline prompt templates (spec-reviewer-prompt.md, etc.)
   - Claude-env wants centralized agent pipeline in `~/.claude/agents/`
   - Fork would need abstraction layer

4. **Skill philosophy conflicts**
   - Superpowers: "tested vs. Anthropic guidance"
   - Claude-env: "integrate with Anthropic patterns"
   - Fork would require mediation layer

### Why CHERRY-PICK Works

1. **Skills are independent modules**
   - You can copy `skills/test-driven-development/SKILL.md` → `~/.claude/skills/`
   - No inter-skill dependencies (skill invocation is explicit)
   - Each skill is self-contained reference

2. **No runtime coupling**
   - Skills don't require superpowers' plugin framework to work
   - You call them with `/skill test-driven-development` in Claude Code
   - Or invoke via Claude mem / GSD integration

3. **Clear adaptation patterns**
   - Superpowers → GSD mapping is straightforward (shown in §8)
   - Rewriting hard-gates to conditional triggers is mechanical
   - Adding GSD context (PHASE.md, REQUIREMENTS.md) is additive

4. **Licensing is permissive**
   - MIT allows redistribution
   - No attribution clauses block modification

### Implementation Checklist

```
Phase 1: Extract & Adapt
  [ ] Copy skills/brainstorming/SKILL.md → ~/.claude/skills/brainstorming/
      - Replace hard-gate with "optional if no GSD phase active"
      - Rewrite final step to point to GSD:plan-phase not writing-plans
  
  [ ] Copy skills/test-driven-development/SKILL.md → ~/.claude/skills/
      - Keep as-is, just reference in EXECUTE phase CLAUDE.md
  
  [ ] Copy skills/systematic-debugging/SKILL.md → ~/.claude/skills/
      - Keep supporting files (defense-in-depth.md, test-pressure-*.md)
  
  [ ] Copy skills/subagent-driven-development/SKILL.md → ~/.claude/skills/
      - Replace Task() dispatch with ~/.claude/agents/ pipeline
      - Make task source GSD PLAN.md (not spec doc)
  
  [ ] Copy skills/writing-plans/SKILL.md → ~/.claude/skills/
      - Redirect to GSD:plan-phase or gsd-plan-phase task
  
  [ ] Copy skills/requesting-code-review/code-reviewer.md → ~/.claude/agents/code-reviewer.md
      - Integrate with GSD INTEGRATION phase
  
  [ ] Copy skills/writing-skills/SKILL.md → ~/.claude/skills/
      - Keep unchanged (meta-skill, universally useful)

Phase 2: Integration
  [ ] Update ~/.claude/CLAUDE.md with skill routing rules (see §8)
  [ ] Add GSD phase context to each skill (via CLAUDE.md, not skill edits)
  [ ] Test: invoke /skill test-driven-development in Claude Code
  [ ] Test: run GSD phase + superpowers skill concurrently

Phase 3: Non-Extraction (What to skip)
  [ ] Don't copy hooks/ (too tightly coupled to superpowers' plugin system)
  [ ] Don't copy using-superpowers/SKILL.md (too superpowers-specific)
  [ ] Don't copy dispatch-parallel-agents yet (lower priority)
  [ ] Don't adopt using-git-worktrees as-is (GSD has git-worktree support)
```

---

## 12. Summary Table

| Aspect | Finding | Action |
|--------|---------|--------|
| **Methodology fit** | Hard gates ⊥ GSD phases | Cherry-pick skills, manage routing in CLAUDE.md |
| **Multi-runtime abstraction** | Excellent but read-only | Reference for plugin manifest design, don't fork |
| **Skill quality** | Mature, well-tested, enforced | Extract 6-8 high-value skills |
| **Subagent model** | Innovative two-stage review | Adapt for GSD artifact-driven dispatch |
| **Code review patterns** | Best-in-class | Adopt spec-reviewer + code-quality-reviewer split |
| **TDD + debugging** | Comprehensive, hard-gated | Use as-is in EXECUTE phase |
| **License** | MIT, permissive | Extract with attribution |
| **Maintainer** | Opinionated, high standards | Respect fork policy (don't sync upstream) |
| **GSD compatibility** | Medium (phase-aware routing needed) | Define rules in CLAUDE.md, condition on phase |
| **Integration effort** | Moderate (rewrite hard-gates) | 2-3 days to fully integrate 6-8 skills |

---

## Conclusion

**Superpowers is a mature, production-grade skills framework optimized for multi-runtime deployment and agentic behavior shaping.** Its hard-gate enforcement model, subagent-driven-development pattern, and multi-runtime abstraction are uniquely valuable. However, forking it as the base of claude-env would require ripping out its core mechanisms (bootstrap, hard gates, skill triggering) to make room for GSD's phase-driven model.

**Cherry-picking 6-8 skills is the pragmatic path:** You get the best techniques (TDD, systematic debugging, code review patterns, brainstorming) without inheriting opinionated session structure that conflicts with GSD. The work is mechanical (copy files, rewrite hard-gates to conditionals, integrate with CLAUDE.md) and the result is architecturally cleaner.

**Extracts to prioritize (in order):**
1. systematic-debugging (universally applicable)
2. test-driven-development (non-negotiable for EXECUTE phase)
3. brainstorming (adapt for GSD discovery)
4. code-review patterns (two-stage dispatch)
5. subagent-driven-development (orchestration template)
6. writing-plans (task decomposition structure)
7. writing-skills (meta-skill for claude-env itself)
8. (Optional) verification-before-completion, using-git-worktrees

**Not recommended to fork. Recommended to cherry-pick with GSD integration layer.**

