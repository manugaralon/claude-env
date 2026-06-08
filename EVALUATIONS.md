# Evaluations Registry

Índice consultable de todo lo evaluado para integración en `claude-env`. Cada entrada apunta a un detail file en `evaluations/` (repos) o `notes/` (transcripts, posts).

**Verdict vocabulary**:
- `integrate` — entra como dependencia o fork del stack
- `cherry-pick` — patrón o pieza específica adoptada, la fuente no se sigue
- `skip` — revisado y descartado
- `research-only` — material de estudio, no se mete en el stack
- `reconsider` — guardar para revisar en `revisit_after`
- `queued` — pendiente de evaluar a fondo

---

## Skill collections / agent skills

| Source | Stars | Verdict | Pulled | Notes |
|---|---|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | 129k | cherry-pick | **PULLED**: mcp-builder, skill-creator. Pending: doc-coauthoring, frontend-design, web-artifacts-builder | Reference library, no fork. License split: 7 Apache 2.0 / 11 proprietary. Detail: `evaluations/anthropics-skills.md` |
| [mattpocock/skills](https://github.com/mattpocock/skills) | — | cherry-pick | **PULLED**: grill-with-docs (+ ADR-FORMAT, CONTEXT-FORMAT sidecars), tdd (+ 5 sidecars), caveman, zoom-out, improve-codebase-architecture. **Complete**. | Skills small + opinated. |
| [obra/superpowers](https://github.com/obra/superpowers) | 178k | cherry-pick | **PULLED**: systematic-debugging (+ 3 sidecars), brainstorming, writing-plans, verification-before-completion, tdd-anti-patterns sidecar, requesting-code-review (+ code-reviewer.md), receiving-code-review, subagent-driven-development (+ 3 prompt sidecars). Pending: writing-skills (replaced by anthropics/skill-creator). | NO fork — hard gates incompatibles con GSD. MIT ok. Detail: `evaluations/obra-superpowers.md` |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 174k | cherry-pick | **PULLED (adapted)**: instincts mechanism via subsystem 11 (3-tier learning, simplified vs ECC's full v2.1), hook architecture pattern via #9. Pending: security guardrails (AgentShield), MCP config template. | NO fork — 48 agents + 182 skills domain-specific. Detail: `evaluations/affaan-m-everything-claude-code.md` |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 30k | queued | — | "Production-grade engineering skills." Cherry-pick alongside mattpocock. |
| [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | 94k | queued | — | Colección de subagentes especializados. Material para capa 4 (agentes). |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 19k | cherry-pick | — | 100+ subagentes — catálogo de referencia. |
| [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) | 116k | cherry-pick | CLAUDE.md addendum | Es un solo CLAUDE.md de pitfalls de LLMs según Karpathy. Absorber, no integrar. |

## Methodologies

| Source | Verdict | Notes |
|---|---|---|
| [glittercowboy/get-shit-done](https://github.com/glittercowboy/get-shit-done) (GSD) | integrate | **Methodology primaria** — columna vertebral spec-driven a nivel proyecto/phase. Ya instalada (v1.38.3). |
| [obra/superpowers](https://github.com/obra/superpowers) | cherry-pick | **Methodology secundaria** — patrones a nivel change (grilling, ADRs, CONTEXT.md). |
| Tu CLAUDE.md (`plan→execute→verify`) | integrate | **Methodology default** cuando no hay GSD ni superpowers activos (cambios pequeños). |

## MCPs (capabilities)

### Installed at user scope (2026-05-07)

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| `@modelcontextprotocol/server-sequential-thinking` | — | **integrated** | Razonamiento estructurado largo. Zero-key, npx-only. |
| `@playwright/mcp` | — | **integrated** | Browser automation. Reemplaza vercel-labs/agent-browser inicialmente (más simple, no requiere compilar Rust). |

### Browser alternatives (evaluated)

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | 32k | reconsider | MCP-native, Rust, Vercel-mantained. Defer hasta que Rust compile barrier valga la pena vs playwright. |
| [LvcidPsyche/auto-browser](https://github.com/LvcidPsyche/auto-browser) | 402 | skip | Solo si necesitas Docker+noVNC para sesiones remotas con humano-in-loop. |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 92k | skip | Es librería Python, no MCP. No entra directamente. |

### MCPs evaluados 2026-05-07

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [upstash/context7](https://github.com/upstash/context7) | 54k | **install ya** | Live docs lookup vía Upstash. Setup OAuth automático con `npx -y ctx7 setup --claude`. Soluciona "Claude usa docs desactualizadas". ECC bundles it. |
| [makenotion/notion-mcp-server](https://github.com/makenotion/notion-mcp-server) | 4.3k | conditional | Install si usas Notion como project management — necesita integration token. |
| [supabase-community/supabase-mcp](https://github.com/supabase-community/supabase-mcp) | 2.7k | conditional | Install al arrancar proyecto Supabase — necesita project URL + service key. |
| [docker/mcp-gateway](https://github.com/docker/mcp-gateway) | 1.4k | reconsider | MCP gateway para gestión via Docker. Overkill con 6 MCPs; revisitar si count crece a 15+. |
| [Jpisnice/shadcn-ui-mcp-server](https://github.com/Jpisnice/shadcn-ui-mcp-server) | 2.8k | skip | Probablemente redundante con `vercel:shadcn` skill ya cargado. Install solo si gap concreto. |
| Google MCPs (Maps, BigQuery, Firebase, Cloud) | varies | defer-per-project | Cada uno necesita gcloud auth + project setup. Install per-project, no preemptive. |

### Code-graph & context tooling (evaluados 2026-06-08)

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | 44.5k | cherry-pick | MCP de code-graph **en runtime** (agente), 100% local, MIT. ~47% menos tokens / 58% menos tool-calls. Complementa `/gsd-graphify` (build-time). Caveat: installer `curl\|sh`, pre-1.0, bus-factor. Detail: `evaluations/colbymchenry-codegraph.md` |
| [Lum1104/Understand-Anything](https://github.com/Lum1104/Understand-Anything) | 54.9k | cherry-pick | Plugin de graph **interactivo human-facing** (onboarding/tours/dashboard). Distinto consumidor que codegraph (humano vs agente). MIT. Detail: `evaluations/Lum1104-Understand-Anything.md` |
| [chopratejas/headroom](https://github.com/chopratejas/headroom) | 17.7k | cherry-pick | Compresión de tokens 60-95% vía **MCP server** (solo esa forma). Encaja con token-discipline; cero solape. Lossy — validar fidelidad + fijar versión. Apache-2.0. Detail: `evaluations/chopratejas-headroom.md` |

## Memory / persistence

| Source | Verdict | Notes |
|---|---|---|
| `claude-mem` (plugin) | integrate | Memoria entre sesiones. Ya instalado. |
| Auto-memory hook (CLAUDE.md global) | integrate | Fact-store del usuario. Ya activo. |
| `CONTEXT.md` (mattpocock pattern) | integrate | Ubiquitous language por proyecto. Por implementar en bootstrap. |
| `docs/adr/` (ADR scaffold) | integrate | Decisions log por proyecto. Por implementar en bootstrap. |
| [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) | skip | Redundante con `claude-mem` (ya integrado y activo). Benchmarks retrieval-only auto-medidos, no comparan vs claude-mem; no justifican migrar un sistema de memoria sticky. Detail: `evaluations/rohitg00-agentmemory.md` |

## Research-only (no se shippea)

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) | 40k | research-only | Leaked system prompts — patrones a estudiar, no a shippear. |
| [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) | 137k | research-only | Mega-colección de prompts. Material de estudio. |
| [sansan0/trendradar](https://github.com/sansan0/trendradar) | 57k | research-only | AI-driven trend/news monitor. Categoría distinta a claude-env (no es dev tool). |

## Different category (no entra en claude-env)

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | 40k | skip | Agent orchestration runtime — territorio GSD, no env. |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 135k | skip | Full agent project, no skills/env. |
| [jamesrochabrun/AgentHub](https://github.com/jamesrochabrun/AgentHub) | 371 | skip | App Swift de gestión de sesiones. Tool externo. |
| [ripienaar/free-for-dev](https://github.com/ripienaar/free-for-dev) | 121k | skip | Lista de SaaS gratis. Otro dominio. |

## Skill registries / aggregators

Aglutinadores tipo "marketplace". Ninguno tiene curación de calidad real — la calidad sigue viniendo de los curadores opinionados (Tier 1 arriba). Estos son **Tier 2/3** para el skill `/find-skill`.

| Source | Skills | Verdict | Notes |
|---|---|---|---|
| [agentskill.work](https://agentskill.work) | 995 | integrate (Tier 2) | Scraped de GitHub, tiene OpenAPI/Swagger + llms.txt. Manejable, sirve como search broader cuando Tier 1 no cubre. |
| [clawhub.ai](https://clawhub.ai) | 52.7k | reconsider (Tier 2) | Community-driven, sin proceso de curación claro. Asociado a OpenClaw. Verificar API antes de adoptar. |
| [skillsmp.com](https://skillsmp.com) | 1.24M | reconsider (Tier 3) | Auto-scraped de GitHub con 2-star mínimo. Demasiado ruido; útil solo con flag explícito `--broadest`. |
| [yfge/skill-finder](https://github.com/yfge/skill-finder) | 3⭐ | skip | El skill en sí es tiny (5KB, 3 stars) — solo nos sirvió para descubrir clawhub + agentskill.work. |

## IG / video / blog sources

Ver `notes/` para detail files (frontmatter ya estructurado). Cuando se decida verdict, añadir entry aquí enlazando al note correspondiente.

| Source | Type | Verdict | Date | Notes |
|---|---|---|---|---|
| [@bashi_fuirkashi DWrR5XyTQTq](https://instagram.com/p/DWrR5XyTQTq/) | ig-post | queued | 2026-04-21 | "Upgrade your Claude Code Skills." Transcript en `notes/`. |

---

## Mantenimiento

- **Añadir nueva fuente**: usar skill `/evaluate <url>` — fetcha metadata, pregunta verdict, escribe detail file + actualiza esta tabla.
- **Buscar si algo ya fue evaluado**: `grep <url-or-keyword> EVALUATIONS.md` o usar `/check-evaluation <query>`.
- **Revisitar entries `reconsider`**: revisión periódica (mensual) de entries con `revisit_after` vencido.
- **Cutoff de exploración**: NO existe — la evaluación continua es parte del producto. Lo que sí hay es priorización: P1 entries (anthropics/skills, superpowers, everything-claude-code) bloquean decisiones arquitectónicas; el resto se evalúa en background.
