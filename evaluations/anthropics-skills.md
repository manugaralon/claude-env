---
source: https://github.com/anthropics/skills
type: github-repo
evaluated_date: 2026-05-06
verdict: cherry-pick
tags: [official, anthropic, skills, canonical, production]
extracts: [claude-api, mcp-builder, doc-coauthoring, skill-creator, docx, pdf, pptx, xlsx, frontend-design, web-artifacts-builder]
---

# Anthropic Skills Repository Evaluation

## Summary

The official Anthropic skills repository at `anthropics/skills` is the canonical source for production-ready skills powering Claude.ai, Claude Code, and the Claude API. It contains 18 carefully curated skills split between document processing (DOCX/PDF/PPTX/XLSX; proprietary license), example skills (creative/technical; Apache 2.0), and a substantial Claude API integration guide. The repository is actively maintained (48 commits, last update 2026-05-03) but takes a **skills-only** approach — no methodology framework (no CLAUDE.md, AGENTS.md, or GSD integration), no superpowers library, no knowledge base. Its value lies in reference implementations of edge-case patterns (e.g., philosophy-first generative art, skill evaluation frameworks, MCP best practices) and production-grade document manipulation. Most of its 11 non-document example skills have overlaps with existing community libraries but sufficient differentiation in approach to warrant selective cherry-picking.

## Structure & Conventions

### Organization
- **`./skills/`** - 18 skill folders, each with a `SKILL.md` file (required), plus supplementary files (reference docs, scripts, examples, themes)
- **`./spec/`** - Points to external agentskills.io specification (not detailed here)
- **`./template/`** - Minimal template for skill creation (name + description only)
- **`./.claude-plugin/marketplace.json`** - Plugin registry defining 3 plugin bundles:
  - `document-skills` — DOCX, PDF, PPTX, XLSX (proprietary)
  - `example-skills` — 11 non-document skills (mostly Apache 2.0)
  - `claude-api` — API integration guide

### Frontmatter Convention
**Minimal, text-driven:**
```yaml
---
name: kebab-case-identifier
description: Plain English trigger text. "Use when user requests X, Y, Z." Also includes SKIP conditions.
license: Apache 2.0 | Proprietary (terms in LICENSE.txt)
---
```

**Key observation:** No `allowed-tools`, `tags`, or machine-parseable metadata. Skill discovery relies entirely on Claude parsing the `description` field for keywords ("when user requests..."). This is the "Claude doesn't invoke my skill" problem — no explicit trigger list or capability tags.

### Supporting Structure
Each skill typically includes:
- **README-style instructions** (philosophy → implementation steps)
- **Reference docs** (e.g., `claude-api/*/claude-api.md` for language-specific examples)
- **Scripts/utilities** (e.g., `mcp-builder/scripts/evaluation.py`, `web-artifacts-builder/scripts/init-artifact.sh`)
- **Themes/examples** (e.g., `theme-factory/themes/`, `internal-comms/examples/`)
- **License file** (Apache 2.0 or proprietary)

## Skill Catalogue

| Skill | Category | Lines | License | Unique Aspects |
|-------|----------|-------|---------|-----------------|
| **claude-api** | Development | 324 | Proprietary | Multi-language SDK guide (Python/TS/Go/Java/Ruby/C#/cURL); prompt caching; managed agents; model migration (4.5→4.6→4.7) |
| **mcp-builder** | Development | 236 | Apache 2.0 | MCP server design patterns; Python (FastMCP) + Node/TS; tool discoverability guidance; evaluation framework (XML-based) |
| **doc-coauthoring** | Workflow | 375 | Apache 2.0 | Three-stage structured workflow (context → refinement → reader testing); reader-blind testing pattern |
| **skill-creator** | Meta | 485 | Apache 2.0 | Skill generation + evaluation + optimization loop; uses skill description optimizer; quantitative benchmarking |
| **docx** | Document | 590 | Proprietary | ZIP-XML manipulation; pandoc fallback; tracked changes; letterheads; TOC generation |
| **pdf** | Document | 314 | Proprietary | pypdf-based; form filling (separate FORMS.md); OCR; encryption |
| **pptx** | Document | 232 | Proprietary | pptxgenjs for creation; markitdown for parsing; templates & speaker notes |
| **xlsx** | Document | 291 | Proprietary | openpyxl/formulas; color-coded financial models (blue=input, black=formula, green=link); zero-error requirement |
| **frontend-design** | Creative | ?* | Apache 2.0 | Bold aesthetic direction first; rejects generic "AI slop"; typography emphasis; production-grade React/HTML/CSS |
| **web-artifacts-builder** | Creative | 73 | Apache 2.0 | React 18 + Tailwind + shadcn/ui + Vite + Parcel bundler; multi-file artifact support; init/bundle scripts |
| **algorithmic-art** | Creative | 404 | Apache 2.0 | Philosophy → implementation (p5.js + seeded randomness); generative systems (particles, flows, fields) |
| **canvas-design** | Creative | 129 | Apache 2.0 | Philosophy → visual (PDF/PNG output); manifesto-driven approach |
| **theme-factory** | Creative | ?* | Apache 2.0 | 10 pre-configured themes (colors + font pairs); theme showcase PDF; swappable styling |
| **brand-guidelines** | Creative | 73 | Apache 2.0 | Anthropic brand colors/typography; post-processing styling |
| **internal-comms** | Enterprise | ?* | Apache 2.0 | 3P updates, newsletters, FAQs, incident reports; format templates in examples/ |
| **slack-gif-creator** | Creative | 254 | Apache 2.0 | GIF constraints (128x128 emoji, 480x480 message, FPS/duration/colors); PIL-based builder |
| **webapp-testing** | Testing | 95 | Apache 2.0 | Playwright testing; server lifecycle helpers; screenshot/DOM inspection |

*Note: Some skills' total line count includes subfolders; frontmatter-only count would be lower.*

### Unique Patterns

1. **Philosophy-first design** (algorithmic-art, canvas-design) — Aesthetic manifesto → code/visual, not templates
2. **Workflow guidance** (doc-coauthoring) — Structured user interview + reader testing
3. **Skill evaluation framework** (skill-creator) — XML-based eval runner with quantitative metrics
4. **Multi-language SDK parity** (claude-api) — 6 languages, live-source pointers to official docs
5. **Proprietary document internals** (docx/pdf/pptx/xlsx) — Reference implementations for production Office/PDF handling

## Unique Value vs Alternatives

### vs mattpocock/superpowers
- **Superpowers:** Focused on JavaScript/Node ecosystem; 50+ skills covering common dev patterns (linting, Docker, Git, etc.). **Anthropic skills:** Broader surface (documents, MCPs, creative, enterprise); production document internals.
- **Overlap:** Frontend design (both have this), web artifacts (both have artifact-building approaches), testing (both cover it).
- **Unique to Anthropic:** Document internals (proprietary), MCP builder (detailed reference), Claude API guide (no equivalent), philosophy-first creativity, Slack GIF optimization.

### vs addyosmani/etc
- **addyosmani patterns:** Smaller, focused libraries (state management, performance, etc.). **Anthropic:** End-to-end workflows and enterprise patterns.
- **Unique to Anthropic:** Proprietary document processing, official API guide, internal comms templates, skill-creation metaskill.

### vs GSD/my-env
- **GSD:** Project-level methodology (milestones, phases, workstreams, artifacts). **Anthropic skills:** Task-level execution tools, no methodology layer.
- **My env (claude-env):** Integrating GSD + superpowers + methodology. **Anthropic:** Orthogonal — provides reusable task executors, not process frameworks.

## Recommendation: Cherry-Pick Specific Items

**Decision: NOT fork-as-base. Reason:** The Anthropic repo is a reference library without methodology scaffolding. It's designed to be selectively installed (via marketplace plugins) rather than forked holistically. Forking would bloat your environment with 11 example skills that you may not immediately need, plus it obscures the canonical upstream source.

**Better approach:** Maintain this repo as a dependency/reference and cherry-pick skills into your `claude-env` as you need them. Use the plugin system to install bundles (e.g., `document-skills` for all doc processing) when needed.

### Specific Items to Cherry-Pick

1. **`skills/claude-api/`** — Full directory
   - **Why:** Canonical multi-language SDK guide; models migration guidance; prompt caching reference
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/claude-api/`
   - **Integration:** Reference via EVALUATIONS.md; consider soft-linking or git-subtree

2. **`skills/mcp-builder/`** — Full directory
   - **Why:** Tool design patterns; evaluation framework; Python (FastMCP) + TS examples
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/mcp-builder/`
   - **Integration:** Critical for building MCPs; keep reference docs

3. **`skills/doc-coauthoring/`** — Full directory
   - **Why:** Structured workflow (context → refine → test); reusable for any writing task
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/doc-coauthoring/`
   - **Integration:** Pairs well with GSD phase workflows

4. **`skills/skill-creator/`** — Full directory (agents/ subfolder especially)
   - **Why:** Skill evaluation loop; quantitative benchmarking; description optimizer
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/skill-creator/`
   - **Integration:** Meta-skill for your own skill development

5. **`skills/frontend-design/`** — SKILL.md + guidelines
   - **Why:** "No AI slop" aesthetic philosophy; bold design direction first
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/frontend-design/`
   - **Integration:** Complements web-artifacts-builder

6. **`skills/web-artifacts-builder/`** — Full directory
   - **Why:** React + Tailwind + shadcn/ui setup; bundling scripts; multi-file artifact support
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/web-artifacts-builder/`
   - **Integration:** Use scripts as templates

7. **`skills/algorithmic-art/` and `canvas-design/`** — Both full
   - **Why:** Philosophy-first creative pattern; generative systems approach
   - **Path:** `/home/manuel/Desktop/PROJECTS/claude-env/skills/{algorithmic-art,canvas-design}/`
   - **Integration:** Template for creative superpowers

8. **Document skills (`docx/`, `pdf/`, `pptx/`, `xlsx/`)** — As-reference only (proprietary)
   - **Why:** Production-grade implementations; too tightly coupled to Claude.ai internals for direct reuse
   - **How:** Read SKILL.md for patterns; don't fork the full directory
   - **Action:** Document patterns in EVALUATIONS.md; link to upstream

### Items to Skip

- **`internal-comms`** — Specific to Anthropic company templates; low transferability
- **`theme-factory`** — Pre-set themes for slides; useful but not critical; reference via plugin system
- **`brand-guidelines`** — Anthropic-specific; your env won't use Anthropic colors
- **`slack-gif-creator`** — Niche; add if needed later
- **`webapp-testing`** — Playwright + helper scripts; standard practice; not unique enough for fork

## Risks & Caveats

### License Risk
- **Document skills (docx/pdf/pptx/xlsx):** Proprietary, NOT open source. Cannot fork, modify, or redistribute. Read for educational value only. If you need to extend document handling, build your own or use community libraries (pypdf, python-pptx, openpyxl).
- **Example skills:** Apache 2.0 — safe to fork, modify, redistribute with attribution.
- **Implication:** Don't create a combined repo that includes proprietary skills alongside open-source ones; separate them or use plugin system.

### Maintenance & Vendor Lock-in
- Repository is actively maintained (48 commits, last 3 days) but updates are primarily for the Claude API integration guide (monthly auto-syncs).
- Skills themselves are relatively stable; new skills are added infrequently.
- **Risk:** If you fork, you'll need to pull upstream changes periodically (especially for claude-api).

### No Methodology Layer
- Anthropic skills assume Claude is already in a task context (user said "build a thing").
- No integration with GSD, project planning, or your plan→execute→verify loop.
- **Implication:** You'll need to write glue code in CLAUDE.md to trigger skills based on project phase (e.g., "in spec-phase, use doc-coauthoring; in code-phase, use claude-api").

### Discoverability Problem
- Skills rely on Claude parsing English descriptions to determine when to invoke.
- No explicit trigger metadata, tags, or `allowed-tools` lists.
- **Solution already in-progress:** OpenAI's Agent Skills spec (agentskills.io) defines extensions; Anthropic may adopt these. For now, rely on skill descriptions.

### Multi-Runtime Support
- Skills are Claude-specific. No mention of Gemini, Codex, or other runtimes.
- Document skills (docx/pdf/pptx/xlsx) are tightly integrated with Claude.ai/Code infrastructure.
- **Implication:** Skills won't transfer to other LLM platforms; OK for personal env, limitation for multi-vendor setups.

## Frontmatter Metadata Gaps

**Finding:** Anthropic's skill frontmatter is minimal (`name` + `description` only). Compared to your needs:

| Metadata | Anthropic | mattpocock | Your Needs |
|----------|-----------|-----------|-----------|
| Name | Yes | Yes | Yes |
| Description | Yes | Yes | Yes |
| Trigger keywords | Embedded in description | Yes | **Need** |
| Allowed tools | No | Yes | **Need** |
| Dependencies | No | No | **Need** |
| Version | No | No | **Need** |
| Tags/categories | No | Implicit | **Need** |
| Methodology hooks (GSD phase) | No | No | **Need** |

**Recommendation:** Extend Anthropic's SKILL.md frontmatter when you cherry-pick. Example:

```yaml
---
name: claude-api
description: "Build, debug, and optimize Claude API / Anthropic SDK apps..."
license: Proprietary
version: 2.0 (as of 2026-05-06)
tags: [sdk, anthropic, production]
triggers: ["code imports anthropic", "user asks for Claude API", "prompt caching"]
allowed_tools: [Bash, WebFetch, Read]
depends_on: []
gsd_phases: [code, research]
---
```

## Update Cadence & Health

- **Repository age:** ~2 years (48 commits)
- **Last 10 commits:** Primarily claude-api updates (auto-synced monthly), occasional bugfixes (skill YAML rendering), one major feature (Managed Agents)
- **New skills:** Rare (last 6 months: 0 new skills; last 12 months: 1 new skill `doc-coauthoring`)
- **Stability:** High. Document skills and example skills are production-ready; unlikely to break.
- **Activity level:** Low-to-moderate. Updated when Claude API changes or bugs are found; not rapid iteration.

## Final Verdict

**cherry-pick** — Establish this repo as your upstream reference. Use the plugin system to install bundles as needed. For your `claude-env`:

1. **Soft-link or git-subtree** `claude-api/` and `mcp-builder/` (critical)
2. **Copy full directories** `doc-coauthoring/`, `skill-creator/`, `frontend-design/`, `web-artifacts-builder/`, creative skills
3. **Reference-only (don't fork)** document skills; read patterns but build your own or use community libraries
4. **Skip** Anthropic-specific skills (brand-guidelines, internal-comms, theme-factory for now)
5. **Extend** all frontmatter with tags, trigger keywords, GSD phase hooks, and tool allowlists
6. **Monitor** upstream monthly for claude-api updates

---

## Extracted Skill Descriptions (for EVALUATIONS.md registry)

```yaml
anthropic-skills/claude-api:
  source: https://github.com/anthropics/skills/tree/main/skills/claude-api
  license: Proprietary
  description: Multi-language SDK guide (Python/TS/Go/Java/Ruby/C#/cURL) for building Claude API apps; covers prompt caching, managed agents, model migration
  status: production
  priority: critical

anthropic-skills/mcp-builder:
  source: https://github.com/anthropics/skills/tree/main/skills/mcp-builder
  license: Apache 2.0
  description: MCP server design patterns, Python FastMCP + TS SDK, tool discoverability, XML-based evaluation framework
  status: production
  priority: critical

anthropic-skills/doc-coauthoring:
  source: https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring
  license: Apache 2.0
  description: Three-stage workflow for co-authoring docs; context gathering → refinement → reader testing
  status: production
  priority: high

anthropic-skills/skill-creator:
  source: https://github.com/anthropics/skills/tree/main/skills/skill-creator
  license: Apache 2.0
  description: Metaskill for creating, evaluating, and optimizing skills; quantitative benchmarking
  status: production
  priority: high

anthropic-skills/frontend-design:
  source: https://github.com/anthropics/skills/tree/main/skills/frontend-design
  license: Apache 2.0
  description: Bold aesthetic-first frontend design; rejects generic AI patterns; production React/CSS
  status: production
  priority: medium

anthropic-skills/web-artifacts-builder:
  source: https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder
  license: Apache 2.0
  description: React 18 + Tailwind + shadcn/ui setup; multi-file artifact bundling; init/bundle scripts
  status: production
  priority: medium

anthropic-skills/algorithmic-art:
  source: https://github.com/anthropics/skills/tree/main/skills/algorithmic-art
  license: Apache 2.0
  description: Philosophy-first p5.js generative art; seeded randomness, particle systems, flow fields
  status: production
  priority: low

anthropic-skills/canvas-design:
  source: https://github.com/anthropics/skills/tree/main/skills/canvas-design
  license: Apache 2.0
  description: Philosophy-first visual design; manifesto → PDF/PNG output
  status: production
  priority: low
```

