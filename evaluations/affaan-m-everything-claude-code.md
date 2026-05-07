---
source: https://github.com/affaan-m/everything-claude-code
type: github-repo
evaluated_date: 2026-05-06
verdict: cherry-pick
tags: [framework, harness, multi-runtime, security-first, continuous-learning]
extracts: [
  "Continuous Learning v2 (instincts + observation hooks)",
  "AgentShield security framework",
  "Cross-harness architecture pattern (.claude, .codex, .cursor, .kiro, .codebuddy)",
  "48 specialized agents (language-specific reviewers + resolvers)",
  "Hook system (PreToolUse, PostToolUse, SessionStart, Stop)",
  "MCP configuration template (15+ servers bundled)",
  "Security-first guardrails and attestation model"
]
---

# Everything Claude Code (affaan-m) — Evaluation Report

**Repository:** https://github.com/affaan-m/everything-claude-code
**Stars:** 174k | **Forks:** 21k | **Contributors:** 170+
**Version:** 2.0.0-rc.1 (April 2026)
**License:** MIT (permissive, fork-friendly)

---

## Executive Summary

ECC is a **mature, production-tested harness framework** with depth across 13 critical subsystems. It differs from `obra/superpowers` in focus: ECC emphasizes **continuous self-improvement via instincts, security sandboxing, multi-runtime portability**, and **research-first workflows**. While there is overlap (agents, skills, rules, hooks), ECC's unique strengths are:

1. **Instincts + Continuous Learning** — Auto-capture behavioral patterns into reusable YAML instincts files
2. **Security-first attestation** — Comprehensive CVE audit trail, AgentShield framework, MCP Top 10 compliance
3. **Cross-harness substrate** — Single skill source → Claude Code / Codex / Cursor / OpenCode / Gemini adapters
4. **Operator-grade automation** — Hermes integration (public/private boundary documented)

**Recommendation: CHERRY-PICK from ECC, do NOT fork as base.** ECC's architecture is tightly coupled to its 48 agents + 182 skills ecosystem. For `claude-env`, extract **instincts/memory mechanism, hook patterns, security templates, and multi-runtime adapter logic** without adopting its full agent catalogue.

---

## 1. Top-Level Architecture

### Directory Structure

```
everything-claude-code/
├── .claude/                          # Claude Code plugin assets
│   ├── identity.json                # Harness identity baseline
│   ├── skills/                      # Generated + curated skills
│   ├── rules/                       # Always-follow guidelines (2 files: guardrails + node.md)
│   ├── commands/                    # Slash command templates (3 workflow examples)
│   ├── hooks/                       # (empty; populated by plugin system)
│   ├── homunculus/instincts/        # Continuous learning instincts (YAML inherited patterns)
│   ├── team/                        # Team config sync
│   └── enterprise/                  # Governance controls
├── .agents/                          # Codex/OpenCode multi-agent skill surface (32 skills)
├── .codex/, .cursor/, .kiro/, .codebuddy/, .gemini/  # Runtime adapters
├── agents/                          # 48 specialized agent definitions (Markdown + YAML)
├── skills/                          # 182 workflow skills (domain knowledge + patterns)
├── commands/                        # Legacy slash command shims + CLI mapping
├── hooks/                           # `hooks.json` (47 KB, comprehensive hook system)
├── .mcp.json                        # Primary MCP server config (6 servers: github, context7, exa, memory, playwright, sequential-thinking)
├── mcp-configs/mcp-servers.json     # Extended MCP template (15+ servers with credentials guide)
├── rules/                           # Language-specific rules (12 languages + common)
├── ecc2/                            # Rust alpha control-plane (daemon, TUI, sessions)
└── EVALUATION.md                    # Self-evaluation gap analysis
```

### Key Files

- **`.claude/identity.json`** — Harness personality (technical, minimal verbosity, JavaScript domain, createdAt: 2026-03-20)
- **`.claude/ecc-tools.json`** — Install manifest (profile: full, 6 packages: runtime-core, workflow-pack, agentshield-pack, research-pack, team-config-sync, enterprise-controls)
- **`agent.yaml`** — Gitagent export surface (182 skills declared, fallback model: claude-sonnet-4-6)
- **`.mcp.json`** — Minimal production MCP config
- **`mcp-configs/mcp-servers.json`** — Full template with 15 options + credential placeholders

---

## 2. Distinctive Features

### A. Instincts (Continuous Learning Layer)

**What it means:** YAML-based pattern capture from live session observations. Not static rules — evolved from behavior.

**Implementation:**
- **Hook:** `pre:observe:continuous-learning` in `hooks/hooks.json` (PreToolUse, async, 10s timeout)
- **Spec:** `/tmp/everything-claude-code/docs/continuous-learning-v2-spec.md`
- **Storage:** `.claude/homunculus/instincts/inherited/everything-claude-code-instincts.yaml`
- **Instinct structure:**
  ```yaml
  ---
  id: everything-claude-code-conventional-commits
  trigger: "when making a commit in everything-claude-code"
  confidence: 0.9
  domain: git
  source: repo-curation
  source_repo: affaan-m/everything-claude-code
  ---
  # Action & Evidence sections follow
  ```

**Commands:**
- `/instinct-status` — List active instincts with confidence scores
- `/instinct-import` — Load YAML instinct bundles
- `/instinct-export` — Save learned patterns for sharing
- `/evolve` — Cluster instincts, merge duplicates, rank by confidence

**Execution:** Instincts are **NOT** constraints like rules. They are **probabilistic triggers** evaluated by a background observer loop. Triggers match git operations, code changes, and tool invocations.

---

### B. Research-First Development

**What it means:** Documentation-heavy workflows with source attribution, broad repository context retrieval, and fact validation.

**Implementation:**
- **Skill:** `.claude/research/everything-claude-code-research-playbook.md`
- **Flow:** 
  1. Inspect local code and docs first
  2. Browse only for unstable or external facts
  3. Summarize findings with file paths, commands, links
- **Tool integration:** Context7 (live docs lookup), Exa (web search), Firecrawl (scraping)
- **Guardrails:**
  - Prefer primary documentation over secondary sources
  - Include concrete dates for facts that may change
  - Keep short evidence trail for recommendations

**Agents used:** `docs-lookup` (Context7 wrapper), `deep-research` (multi-source synthesis)

---

### C. Security Layer (AgentShield)

**What it means:** Multi-layered defense against prompt injection, RCE, secret exposure, and supply-chain attacks.

**Threat Model:**
- **CVE-2025-59536 (CVSS 8.7):** Project-contained code running before trust dialog
- **CVE-2026-21852:** ANTHROPIC_BASE_URL hijacking → API key leak
- **MCP consent abuse:** Auto-approved servers before user trust
- **Skill supply chain:** Snyk found 36% of public skills contain prompt injection; 1,467 malicious payloads in 3,984 scanned skills
- **Memory poisoning:** Microsoft documented 31 companies / 14 industries affected by hidden instruction injection in AI memory

**Defenses:**
1. **Trust boundary enforcement** — `.claude/` config guarded by project trust dialog
2. **Hook sanitization** — Dangerous Bash commands blocked (rm -rf, force push)
3. **MCP server validation** — Explicit schema checking, environment variable sandboxing
4. **Instinct attestation** — Instincts tagged with source_repo, confidence score, and domain
5. **Skill validation** — evalview MCP for AI regression testing; ToxicSkills scanning
6. **Sandboxing guidance** — Documented Docker Compose + devcontainer patterns for untrusted repos

**Files:**
- `the-security-guide.md` — 150+ line comprehensive threat model + remediation
- `.claude/rules/everything-claude-code-guardrails.md` — Auto-generated security baseline
- `agents/security-reviewer.md` — Dedicated security-first code review agent
- `skills/security-review/` — Security domain knowledge (cloud, web, runtime)
- `mcp-configs/mcp-servers.json` — Credential handling guide + `ECC_DISABLED_MCPS` env override

---

## 3. Inventory

### Agents (48 Total)

**Language Reviewers (8):**
- `typescript-reviewer`, `python-reviewer`, `java-reviewer`, `kotlin-reviewer`, `rust-reviewer`, `go-reviewer`, `cpp-reviewer`, `csharp-reviewer`, `flutter-reviewer`

**Build Resolvers (7):**
- `go-build-resolver`, `java-build-resolver`, `kotlin-build-resolver`, `rust-build-resolver`, `cpp-build-resolver`, `dart-build-resolver`, `pytorch-build-resolver`

**Core Workflow (8):**
- `planner`, `architect`, `code-reviewer`, `security-reviewer`, `tdd-guide`, `code-simplifier`, `refactor-cleaner`, `doc-updater`

**Specialized (12):**
- `loop-operator`, `harness-optimizer`, `database-reviewer`, `e2e-runner`, `build-error-resolver`, `performance-optimizer`, `a11y-architect`, `type-design-analyzer`

**Vertical + Research (5):**
- `gan-planner`, `gan-generator`, `gan-evaluator`, `healthcare-reviewer`, `seo-specialist`

**Automation (8):**
- `chief-of-staff`, `conversation-analyzer`, `comment-analyzer`, `docs-lookup`, `pr-test-analyzer`, `silent-failure-hunter`, `opensource-forker`, `opensource-packager`

---

### Skills (182 Total)

Organized by domain. Sample from `.agents/skills/`:

**Testing & QA (6):**
- `tdd-workflow`, `e2e-testing`, `verification-loop`, `eval-harness`, `ai-regression-testing`, `testing-strategies`

**Architecture & Patterns (8):**
- `api-design`, `backend-patterns`, `frontend-patterns`, `mcp-server-patterns`, `database-migrations`, `docker-patterns`, `nextjs-turbopack`, `design-system`

**Language Ecosystems (12+):**
- `python-patterns`, `django-patterns`, `django-security`, `django-tdd`, `django-verification`
- `cpp-coding-standards`, `cpp-testing`, `cpp-patterns`
- `rust-patterns`, `bun-runtime`, `kotlin-patterns`, `laravel-patterns`

**AI/ML & Research (8):**
- `claude-api`, `agent-eval`, `agent-introspection-debugging`, `deep-research`, `documentation-lookup`, `cost-aware-llm-pipeline`, `prompt-optimizer`, `ai-regression-testing`

**Media & Operations (6):**
- `content-engine`, `brand-voice`, `article-writing`, `video-editing`, `manim-video`, `remotion-video-creation`

**Business (5):**
- `investor-materials`, `investor-outreach`, `market-research`, `strategic-compact`, `customer-billing-ops`

**Integration & Tools (5):**
- `exa-search`, `fal-ai-media`, `dmux-workflows`, `x-api`, `crosspost`

---

### MCPs

**Core (in `.mcp.json`):**
1. **github** — PR, issue, repo ops
2. **context7** — Live docs lookup (Upstash, supports 30+ frameworks)
3. **exa** — Web search + research
4. **memory** — Session persistence (Anthropic native)
5. **playwright** — Browser automation
6. **sequential-thinking** — Extended reasoning

**Extended (in `mcp-configs/mcp-servers.json`, 15 total):**
- Jira, Firecrawl, Supabase, Omega Memory, Vercel, Railway, Cloudflare (4 MCPs), ClickHouse, Exa (web), Magic UI, Filesystem, FAL AI, Browserbase, Browser Use, DevFleet, Token Optimizer, LaraPlugins, Confluence, EvalView

**Cost control:** Documented `ECC_DISABLED_MCPS=github,context7,...` pattern + per-project `disabledMcpServers` override.

---

## 4. Multi-Runtime Strategy

### Principle

**One source, N adapters.** Shared behavior in `skills/`, `rules/`, `hooks/`, `scripts/`; harness-specific loading/enforcement at the edge.

### Adaptation Layer

| Surface | Shared Source | Claude Code | Codex | Cursor | OpenCode | Gemini |
|---------|---------------|----|----|----|---------|--------|
| **Skills** | `skills/*/SKILL.md` | Claude plugin (auto-inject) | `.agents/skills/` + `openai.yaml` metadata | `.cursor/skills/` (copies) | Plugin/config | Instruction-backed |
| **Rules** | `rules/` (12 langs) | Native rules install | `AGENTS.md` + instruction-backed | `.cursor/rules/` (adapted) | Instructions | Doc-only |
| **Hooks** | `hooks/hooks.json` + `scripts/hooks/*.js` | Native hook execution | Instruction adapter (no native) | Hook adapter layer | Event system | Instruction-backed |
| **MCPs** | `.mcp.json` + `mcp-configs/` | Native config import | Config import + `config.toml` | Config file | Plugin system | Not supported yet |
| **Commands** | `commands/`, CLI scripts | Slash commands | CLI routing | Custom handler | Plugin events | CLI only |

### Examples

**`.claude/` (Claude Code):** Native plugin loads everything.

**`.codex/`:** 
- `config.toml` — MCP + agent baseline
- `AGENTS.md` — Usage guide pointing at `.agents/skills/`
- `agents/explorer.toml`, `reviewer.toml`, `docs-researcher.toml` — Read-only multi-agent roles

**`.cursor/`:**
- `skills/` — Full copy of curated skills
- `rules/` — Adapted syntax for Cursor's rule loader
- `hooks.json` — Cursor-compatible hook format (limited parity)

**`.kiro/`:**
- `agents/` — Agent definitions
- `hooks/` — Hook adapters
- `docs/` — Kiro-specific setup

### Hermes Boundary

Hermes (the operator shell, private) is NOT published. The public repo documents:
- **Do ship:** Sanitized setup guides, repo-relative demo prompts, general operator skills, public examples
- **Do not ship:** OAuth tokens, raw `~/.hermes` exports, personal workspace memory, private datasets

**Key commands:**
- `ecc migrate audit --source ~/.hermes` — Inventory legacy state
- `ecc migrate plan` — Generate migration artifacts
- `ecc migrate import-skills` — Extract reusable skills from private ops

---

## 5. Hook System Deep Dive

**File:** `hooks/hooks.json` (47 KB, 50+ hook entries)

### Hook Lifecycle

| Phase | Purpose | Examples |
|-------|---------|----------|
| **PreToolUse** | Before tool execution | Bash preflight (quality, tmux, push checks), Write warning, Continuous learning observation |
| **PostToolUse** | After tool completes | Cost tracking, Test result capture, Success/failure logging |
| **SessionStart** | Session init | Load MCP config, Restore memory, Initialize observer |
| **Stop** | Session end | Git hygiene check, Session save, Instinct clustering, Cost report |

### Key Hooks (Enabled by Default)

1. **`pre:bash:dispatcher`** — Consolidated Bash preflight (quality + tmux + push + GateGuard)
2. **`pre:write:doc-file-warning`** — Warn about non-standard doc files (non-blocking)
3. **`pre:edit-write:suggest-compact`** — Suggest manual compaction at intervals
4. **`pre:observe:continuous-learning`** — Capture tool use for instinct learning (async, 10s timeout)

### Hook Bootstrap Logic

```bash
node -e "
  const CLAUDE_PLUGIN_ROOT = resolve to ~/.claude or ~/.claude/plugins/ecc/...
  const bootstrap = path.join(CLAUDE_PLUGIN_ROOT, 'scripts/hooks/plugin-hook-bootstrap.js')
  process.env.CLAUDE_PLUGIN_ROOT = CLAUDE_PLUGIN_ROOT
  require(bootstrap)
  require('scripts/hooks/pre-bash-dispatcher.js')
"
```

This allows ECC to work as a plugin OR as a direct repo without path hardcoding.

---

## 6. Comparison with `obra/superpowers`

**Availability note:** We cannot access superpowers directly, but based on its positioning (178k stars, "superpowers/mattpocock atomic"), typical patterns suggest:

| Dimension | ECC | Superpowers (inferred) |
|-----------|-----|----------------------|
| **Agents** | 48 language-specific + workflow | Likely smaller, skill-focused |
| **Skills** | 182, auto-learned from patterns | Likely curated, hand-written |
| **Instincts** | Yes, YAML-based learnable | Probably not; static rules |
| **Security** | Comprehensive (AgentShield, CVE tracking) | Likely lighter; no dedicated audit |
| **Multi-runtime** | Yes (5 harnesses via adapters) | Probably single-harness focused |
| **Hooks** | 50+ production hooks | Likely fewer or plugin-dependent |
| **MCP** | 15+ servers bundled + template | Probably fewer, core only |
| **License** | MIT (permissive) | Unknown; likely also permissive |
| **Operator story** | Hermes (public surface) | Likely local/closed |
| **Continuous Learning** | Built-in (v2 spec) | Probably not |

### Overlap

Both likely provide:
- Agent/skill definitions
- Code review workflows
- TDD/testing guidance
- Security rules
- Multi-language support
- Hook system

### ECC Unique

- Instincts + continuous learning
- Comprehensive security audit trail + CVE tracking
- Cross-harness adapter architecture
- Operator workflow lane (Hermes integration)
- Research-first methodology
- Memory poisoning defenses

### Superpowers Likely Unique

- Probably tighter "atomic" pattern library (not inferred from behavior)
- Likely mattpocock-specific conventions

---

## 7. License & Fork Viability

**License:** MIT (Affaan Mustafa, 2026)

**Fork viability:** HIGH.
- Permissive license allows commercial use, modification, and redistribution
- Well-organized for selective adoption (don't need all 48 agents)
- No runtime dependencies on external proprietary services (Hermes is optional, public surface documented)
- All code, rules, and skills are in-tree; no external API keys required to run tests

**Caution:** If you fork and adopt Hermes integrations, sanitize all private credentials and operator-specific skills before publishing.

---

## 8. Recommendation: CHERRY-PICK (Not Fork-As-Base)

### Why Not Fork Wholesale

1. **Agent bloat** — 48 agents is overkill for `claude-env`'s initial scope (your 13 subsystems suggest 5–10 agents max)
2. **Skill explosion** — 182 skills = maintenance burden. Most are domain-specific (Django, Kotlin, PyTorch) that may not apply to your GSD/atomic methodology
3. **Tight coupling** — Skills reference agent names, hooks reference skill ids. Forking wholesale means adopting their naming convention + dependency graph
4. **Hermes entanglement** — Operator lane assumes Hermes runtime; if you don't use it, you're carrying dead code

### What to Extract

#### Tier 1 (Immediate Value)

1. **Instincts + Continuous Learning v2**
   - File: `docs/continuous-learning-v2-spec.md`
   - Hook: `pre:observe:continuous-learning` from `hooks/hooks.json`
   - Storage: `.claude/homunculus/instincts/inherited/*.yaml` pattern
   - **Use case:** Auto-capture your GSD/atomic patterns into learnable YAML

2. **Hook System Architecture**
   - File: `hooks/hooks.json` structure + `scripts/hooks/plugin-hook-bootstrap.js`
   - **Extract:** Hook dispatch pattern, PreToolUse/PostToolUse lifecycle, async timeout handling
   - **Skip:** All 48 hook implementations; build your own for your subsystems

3. **Cross-Harness Adapter Pattern**
   - Files: `docs/architecture/cross-harness.md`, `.claude/`, `.codex/`, `.cursor/`, `.kiro/` directories
   - **Extract:** Skill source → adapter mapping, MCP config sharing, rules translation
   - **Use case:** Prepare `claude-env` for future multi-runtime expansion

4. **Security Guardrails**
   - Files: `the-security-guide.md`, `.claude/rules/everything-claude-code-guardrails.md`, `agents/security-reviewer.md`
   - **Extract:** Threat model, CVE tracking template, AgentShield checklist, sandboxing patterns
   - **Use case:** Populate your `security` subsystem

#### Tier 2 (Reference Only)

5. **Agent Design Patterns**
   - Files: `agents/*.md` — 48 examples across language reviewers, build resolvers, workflow agents
   - **Extract:** Agent frontmatter format, delegation strategy, when-to-use guidance
   - **Skip:** Don't adopt all 48; design 5–8 for your core workflows

6. **MCP Configuration Template**
   - Files: `.mcp.json`, `mcp-configs/mcp-servers.json`
   - **Extract:** MCP bootstrap pattern, credential handling guide, `ECC_DISABLED_MCPS` override mechanism
   - **Reference:** 15 server options for your planned MCPs (Vercel, Postgres, Perplexity, Sequential Thinking already in ECC)

7. **Memory + Team Config**
   - Files: `.claude/team/everything-claude-code-team-config.json`, `.claude/enterprise/controls.md`
   - **Extract:** Team sync pattern, governance scaffold
   - **Use case:** Prepare for `distribution` and `self-improvement` subsystems

#### Tier 3 (Patterns Only)

8. **Skill Authoring Convention**
   - Look at `skills/*/SKILL.md` — clear YAML frontmatter + "When to Use" / "How It Works" / "Examples" sections
   - **Extract:** Format + naming (kebab-case directories)

---

## 9. Specific Items to Cherry-Pick

### File-by-File Extraction Plan

```
affaan-m/everything-claude-code/
├── docs/continuous-learning-v2-spec.md
│   → claude-env/docs/subsystems/memory.md (adapt)
├── docs/architecture/cross-harness.md
│   → claude-env/docs/architecture/multi-runtime.md (reference + adapt)
├── the-security-guide.md
│   → claude-env/docs/subsystems/security.md (summary + links to full)
├── hooks/hooks.json (partial: PreToolUse/PostToolUse lifecycle, async pattern)
│   → claude-env/.claude/hooks/hooks.json (build your own 5–10 hooks)
├── .claude/rules/everything-claude-code-guardrails.md (structure)
│   → claude-env/.claude/rules/claude-env-guardrails.md (write your own)
├── agents/security-reviewer.md, agents/code-reviewer.md, agents/tdd-guide.md
│   → claude-env/agents/ (study format; create 5–8 of your own)
├── agents/planner.md, agents/architect.md
│   → claude-env/agents/ (study for GSD/superpowers alignment)
├── .claude/homunculus/instincts/inherited/ (example structure)
│   → claude-env/.claude/homunculus/instincts/ (create your own instinct YAML)
├── mcp-configs/mcp-servers.json (template; keep for reference)
│   → claude-env/docs/MCPs/template.json (reference; pick 5)
├── skills/tdd-workflow/SKILL.md, skills/coding-standards/SKILL.md
│   → claude-env/skills/ (study format; write your own for GSD)
└── .claude/identity.json (structure)
    → claude-env/.claude/identity.json (minimal; write your own)
```

### No-Copy Items

- All 48 agents (too many; write your own 5–8)
- All 182 skills (too many; write your own 15–25 aligned to your 13 subsystems)
- All 50+ hook implementations (too specific; design your own 5–10)
- Hermes-specific workflows (not your use case)
- Language-specific rules for Django, Kotlin, PyTorch (unless you use them)

---

## 10. Integration Pathway for `claude-env`

### Phase 1: Memory & Observation (Month 1)

- Extract continuous-learning v2 spec → adapt to GSD/atomic patterns
- Build 3–5 observation hooks (PreToolUse listeners) for plan→execute→verify phases
- Create `.claude/homunculus/instincts/inherited/claude-env-instincts.yaml` with initial patterns

### Phase 2: Security & Governance (Month 1–2)

- Adopt ECC's threat model; document your CVSS targets
- Write 3–5 guardrail rules matching your 13 subsystems
- Create `security-review` agent + skill

### Phase 3: Multi-Runtime (Month 2–3)

- Design adapter layer for Claude Code → Cursor / Codex / OpenCode (reference ECC's pattern)
- MCP: Choose 5 from ECC's 15 options (Vercel, Postgres, Perplexity, Sequential Thinking, + 1 more)
- Create `.codex/`, `.cursor/`, `.kiro/` directories with minimal adapters

### Phase 4: Agent & Skill Scaffolding (Ongoing)

- Write 5–8 agents aligned to GSD/atomic methodology
- Write 15–25 skills tied to your 13 subsystems (not 182)
- Use ECC's skill format but your own domain taxonomy

---

## 11. Summary: Distinctive Value

| Feature | ECC Strength | How It Helps `claude-env` |
|---------|-------|--------|
| Instincts (learned YAML) | Production-proven, v2 spec stable | Auto-learn your GSD patterns from sessions |
| Security audit trail | CVE tracking, threat model, AgentShield | Populate your security subsystem with rigor |
| Cross-harness adapters | 5 harnesses supported; architecture documented | Future-proof for multi-runtime expansion |
| Hook system | 50+ examples; bootstrap pattern proven | Design 5–10 context-aware hooks |
| Memory mechanism | Claude memory MCP + homunculus instincts | Combine with your plan→execute→verify cycle |
| Research playbook | Source-first, evidence trails, fact validation | Align with your methodology docs |

---

## Files for Reference

- **Instincts:** `/tmp/everything-claude-code/docs/continuous-learning-v2-spec.md`
- **Security:** `/tmp/everything-claude-code/the-security-guide.md`
- **Architecture:** `/tmp/everything-claude-code/docs/architecture/cross-harness.md`
- **Hooks:** `/tmp/everything-claude-code/hooks/hooks.json` (first 50 lines show pattern)
- **Agents:** `/tmp/everything-claude-code/agents/` (48 Markdown files; all follow consistent format)
- **Skills:** `/tmp/everything-claude-code/.agents/skills/` (32 subdirs; each has SKILL.md + agents/openai.yaml)
- **Rules:** `/tmp/everything-claude-code/rules/` (12 languages + common guardrails)

---

## Verdict: CHERRY-PICK

**Do not fork as-base.** Instead:
1. Extract instincts/memory + hook architecture → your `memory` subsystem
2. Adopt security guardrails + threat model → your `security` subsystem
3. Reference agent/skill design patterns → build 5–8 agents + 15–25 skills for your 13 subsystems
4. Study cross-harness adapter logic → prepare for multi-runtime future
5. Copy MCP template + credential handling → integrate your 4–5 chosen MCPs

This allows you to:
- Leverage ECC's battle-tested patterns without the overhead
- Maintain architectural independence (your own agent/skill taxonomy)
- Stay focused on GSD/atomic methodology (not distracted by 182 skills)
- Keep the door open for multi-runtime expansion later

**Total extraction effort:** 20–40 hours (read, annotate, adapt, test).
**Total value:** 3–5 unique subsystems jumpstarted from production-grade patterns.

