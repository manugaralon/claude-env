# Architecture Research

**Domain:** Developer tooling — Claude Code environment generator  
**Researched:** 2026-04-15  
**Confidence:** HIGH (derived from existing codebase, not speculation)

---

## Components

### 1. Input Normalizer
- **Responsibility:** Accept two input forms (freeform idea text or structured spec document) and produce a normalized `ProjectSpec` object. Freeform ideas are fleshed out via LLM call; structured specs are parsed directly. The output is the same schema regardless of input form.
- **Inputs:** Raw string (freeform) or path to spec file (Markdown/text)
- **Outputs:** `ProjectSpec` — name, description, domain(s), stack hints, constraints, languages, known skills needed
- **Dependencies:** LLM call (Claude) for freeform → structured expansion; nothing else

### 2. Domain Classifier
- **Responsibility:** Determine which technical domain(s) apply (web, mobile, data, infra, CLI, ML, etc.) and select the matching domain profile. A domain profile is a static config file that maps domain → recommended skills, agent types, and CLAUDE.md sections. This is purely deterministic after classification.
- **Inputs:** `ProjectSpec` from Input Normalizer
- **Outputs:** `DomainProfile` — list of domain tags, recommended skill slugs, recommended agent slugs, CLAUDE.md section overrides
- **Dependencies:** Static domain profile registry (YAML/JSON files, one per domain); Input Normalizer must run first

### 3. Environment Planner
- **Responsibility:** Merge `ProjectSpec` + `DomainProfile` into a complete generation plan. Decides what to generate for each output layer (global vs per-project), resolves conflicts between domain recommendations and project-specific constraints, and produces a flat `GenerationPlan` — a list of artifacts to write with their source templates and variable bindings.
- **Inputs:** `ProjectSpec`, `DomainProfile`
- **Outputs:** `GenerationPlan` — ordered list of `Artifact(target_path, template_id, variables, layer: global|project)`
- **Dependencies:** Domain Classifier; template registry (must know which templates exist)

### 4. Template Registry
- **Responsibility:** Hold all templates — CLAUDE.md (global and per-project), skill `.md` files, agent `.md` files, hooks config. Templates use `{{VAR}}` substitution (same pattern as existing claude-env). Provides `render(template_id, variables) → str`.
- **Inputs:** Template ID + variable dict
- **Outputs:** Rendered string content
- **Dependencies:** None (pure file-based registry; loaded at startup)

### 5. Generator
- **Responsibility:** Execute the `GenerationPlan` — render each artifact and write it to its target path. Handles the two-layer output: global `~/.claude/` writes (merge-safe, never full-overwrite) and per-project `.claude/` writes (create or overwrite). Enforces the 200-line constraint on all generated CLAUDE.md files.
- **Inputs:** `GenerationPlan`, Template Registry
- **Outputs:** Files on disk (`~/.claude/` and `<project>/.claude/` trees)
- **Dependencies:** Template Registry; Environment Planner must have run

### 6. Audit Agent
- **Responsibility:** Validate the generated environment before the developer starts. Reads the generated files, checks for: completeness (required sections present), CLAUDE.md line count ≤ 200, no template variables left unreplaced, agent files reference valid skill slugs, hooks config is syntactically valid. Returns a structured report with PASS/WARN/FAIL per check.
- **Inputs:** Generated file tree (paths from Generator output)
- **Outputs:** `AuditReport` — list of checks with status and message; overall PASS/FAIL
- **Dependencies:** Generator must have written files first; runs as a Claude subagent (zero-context launch to avoid confirmation bias)

### 7. CLI Entrypoint (`main.py`)
- **Responsibility:** Two modes. (a) `setup` — global onboarding wizard: interactive Q&A, calls Input Normalizer in freeform mode, runs full pipeline, writes `~/.claude/` layer. (b) `bootstrap` — per-project mode: reads project directory, calls full pipeline, writes `.claude/` layer. Both modes call Audit Agent after generation and surface the report to the user.
- **Inputs:** CLI args (`setup` or `bootstrap [project-path]`), stdin for wizard questions
- **Outputs:** Orchestrates all components; prints generation summary and audit report
- **Dependencies:** All components above

### 8. Claude Code Skill (`commands/claude-env.md`)
- **Responsibility:** Wrap `bootstrap` mode as a Claude Code slash command so it can be invoked from any project directory as `/claude-env:bootstrap`. The skill calls `python3 <path-to-claude-env-2>/main.py bootstrap .` and surfaces the audit report inline. This is a thin wrapper — no logic lives here.
- **Inputs:** Current project directory (implicit from Claude Code context)
- **Outputs:** Runs the CLI, streams output back to the user
- **Dependencies:** CLI Entrypoint must exist and be callable

---

## Data Flow

```
Input (freeform text | spec file)
  └─→ Input Normalizer
        └─→ ProjectSpec
              └─→ Domain Classifier
                    ├─→ DomainProfile
                    │     └─→ Environment Planner
                    │               ├─← Template Registry (reads templates)
                    │               └─→ GenerationPlan
                    │                     └─→ Generator
                    │                           ├─→ ~/.claude/ (global layer)
                    │                           └─→ .claude/ (per-project layer)
                    │                                 └─→ Audit Agent
                    │                                       └─→ AuditReport → user
                    └─→ (domain tags also inform skill/agent selection in Planner)
```

The flow is strictly linear with no back-edges. Each component depends only on the output of the preceding stage. The only external call is the LLM invocation in Input Normalizer (for freeform expansion) and the Audit Agent (Claude subagent). All other components are deterministic.

---

## Build Order

1. **Template Registry** — No dependencies. Define the schema for templates and write initial templates (global CLAUDE.md, per-project CLAUDE.md, skill stub, agent stub, hooks config). This is the foundation everything else renders from. Can be built and tested in isolation by calling `render()` directly.

2. **Input Normalizer** — Depends only on the LLM and the `ProjectSpec` schema. Build the schema first, then the freeform→structured expansion, then the spec file parser. Testable with fixture inputs without touching templates or generation.

3. **Domain Classifier** — Depends on `ProjectSpec` and the domain profile registry. Build the domain profiles (YAML/JSON) before the classifier logic. Start with 3-4 domains (web, CLI, data, infra) and expand. Testable in isolation: given a `ProjectSpec`, assert correct domain tags.

4. **Environment Planner** — Depends on `ProjectSpec` + `DomainProfile` + Template Registry (must know what exists). The planner's output (`GenerationPlan`) is a pure data structure — no file I/O yet. Test by asserting correct artifact list for known domain profiles.

5. **Generator** — Depends on `GenerationPlan` + Template Registry. This is the first component with file I/O. Test with a temp directory. Enforce 200-line constraint here, not in templates. Implement merge-safe global layer writes (append new sections, never overwrite existing user customizations).

6. **Audit Agent** — Depends on generated file tree. Implement as a set of deterministic checks first (line count, unreplaced vars, required sections). The Claude subagent wrapper comes after the checks are solid — don't couple the check logic to the agent invocation.

7. **CLI Entrypoint** — Depends on all components. Wire up `setup` and `bootstrap` modes. Interactive wizard for `setup`. At this point the full pipeline is testable end-to-end with real inputs.

8. **Claude Code Skill** — Depends on CLI Entrypoint being stable. Write the `.md` command file last — it is one page and wraps the CLI. Install it into `~/.claude/commands/` as part of `setup`.

---

## Key Architectural Decisions

**Single-direction pipeline, no feedback loops** — The flow from input to generation is strictly forward. The Audit Agent runs after, not during, generation. This keeps each component independently testable and avoids the complexity of regeneration loops. If the audit fails, the user re-runs with corrected input.

**Declarative `GenerationPlan` as the pivot** — The Environment Planner produces a data structure (list of artifacts), not side effects. The Generator executes it. This separation means the planner can be tested without file I/O and the generator can be swapped without touching domain logic.

**Domain profiles are static config files, not code** — Each domain (web, CLI, data, etc.) is a YAML/JSON file listing which skills, agents, and CLAUDE.md sections apply. Adding a new domain requires adding a file, not changing code. This follows the open/closed principle and makes the domain registry extensible without touching core logic.

**Merge-safe global layer writes** — The `~/.claude/` layer is the user's live environment. Generator must never full-overwrite it. Strategy: for CLAUDE.md, append a clearly-delimited section. For skills and agents, write to named subdirectories. For hooks config, merge JSON. This prevents the tool from destroying manual customizations on repeat runs.

**200-line constraint enforced at generation time, not at template time** — Templates can be longer than 200 lines (they include comments, optional sections). The Generator truncates/selects sections to stay under the limit for the final output. This keeps templates expressive while enforcing the quality constraint on output.

**Audit Agent as zero-context subagent** — Following the existing claude-env reviewer pattern, the Audit Agent is launched with zero conversation history. This prevents it from inheriting the confirmation bias of the generation step. It reads only the generated files and applies checks independently.

**CLI-first, skill as thin wrapper** — All logic lives in `main.py`. The Claude Code skill (`/claude-env:bootstrap`) is a one-page command file that calls the CLI. This means the tool is testable and usable without Claude Code, and the skill adds no logic of its own.

**Two-layer output with explicit layer tagging** — Every artifact in `GenerationPlan` is tagged `global` or `project`. The Generator routes each to the correct destination. This explicit tagging prevents accidental cross-layer writes and makes the generation plan human-readable (auditable before execution).

---

## What the Existing claude-env Does Not Have (Gap Analysis)

The current `claude-env` covers: global CLAUDE.md generation via setup.sh wizard, lessons.md and memory.md templates, Trace2Skill analyst agents, content transcription pipeline.

It does not cover: domain classification, per-project `.claude/` layer generation, skills/agents generation, hooks config generation, audit agent, Claude Code skill for per-project invocation. These are all new components in claude-env-2.

The template system and wizard interaction pattern are directly reusable. The `{{VAR}}` substitution pattern from `setup.sh` should be kept as-is (proven, simple).
