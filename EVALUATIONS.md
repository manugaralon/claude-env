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

## Individual skills (frontend & media)

Surgidos de la 2ª capa de los IG (2026-06-08).

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | 36k | integrate | Skill de diseño frontend (23 cmds, anti-pattern rules deterministas sin coste de tokens, `/impeccable live` browser loop). Encaja en flujo GSD: `gsd-ui-phase` (pre-code) → impeccable (polish) → `gsd-ui-review` (gate). Apache-2.0. Detail: `evaluations/pbakaus-impeccable.md` |
| [emilkowalski/skill](https://github.com/emilkowalski/skill) | 2.1k | cherry-pick | Skill de animación de Emil Kowalski. Redundante si tienes impeccable; absorber solo la heurística "frecuencia → animar o no" en un `DESIGN.md`. Sin licencia declarada. |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | 38k | skip | Presets de estilo (soft/minimalist/brutalist). Redundante con impeccable; absorber los 3 presets como anclas en `DESIGN.md`. MIT, v2 experimental. |
| [bradautomates/claude-video](https://github.com/bradautomates/claude-video) | 1.9k | cherry-pick | Skill `/watch`: análisis **visual** de frames (ffmpeg) + audio — el delta que tu `capture.py` (solo audio) no cubre. Plugin; reusa `GROQ_API_KEY`. MIT. Detail: `evaluations/bradautomates-claude-video.md` |
| [Manavarya09/design-extract](https://github.com/Manavarya09/design-extract) | 3.1k | integrate | Extrae el design-system de cualquier URL → tokens DTCG/Tailwind/shadcn/Figma (capa *inward*, complementa impeccable que genera *outward*). MCP-native. MIT. Detail: `evaluations/Manavarya09-design-extract.md` |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 49.4k | research-only | Vídeo programático en React. Net-new (nada genera vídeo) pero React-heavy + licencia comercial no-estándar, sin caso de uso recurrente. Revisit si surge necesidad (changelogs animados, demos). Detail: `evaluations/remotion-dev-remotion.md` |

## Methodologies

| Source | Verdict | Notes |
|---|---|---|
| [glittercowboy/get-shit-done](https://github.com/glittercowboy/get-shit-done) (GSD) | integrate | **Methodology primaria** — columna vertebral spec-driven a nivel proyecto/phase. Ya instalada (v1.38.3). |
| [obra/superpowers](https://github.com/obra/superpowers) | cherry-pick | **Methodology secundaria** — patrones a nivel change (grilling, ADRs, CONTEXT.md). |
| Tu CLAUDE.md (`plan→execute→verify`) | integrate | **Methodology default** cuando no hay GSD ni superpowers activos (cambios pequeños). |
| [github/spec-kit](https://github.com/github/spec-kit) | cherry-pick | SDD de GitHub (110k⭐, MIT). **NO switch** — GSD gana en lifecycle scope; spec-kit es feature-scoped. Robar: Constitution file (`.planning/CONSTITUTION.md`), cross-artifact check (`/gsd-analyze`), markers `[P]`. No council-worthy. Detail: `evaluations/github-spec-kit.md` |

## Dev tooling / observability

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [getagentseal/codeburn](https://github.com/getagentseal/codeburn) | 7.7k | integrate | TUI/CLI zero-config que lee `~/.claude/` y clasifica gasto de tokens por actividad/MCP/proyecto. `codeburn optimize` detecta ghost skills, MCPs sin usar, CLAUDE.md inflado. Complementa gsd-session-report (cross-session vs per-phase). MIT. Detail: `evaluations/getagentseal-codeburn.md` |

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
| [browser-use/browser-harness](https://github.com/browser-use/browser-harness) | 14.5k | cherry-pick | Harness CDP con loop de domain-skills auto-escritos. NO como browser primario (playwright MCP cubre el caso base, ~80% solape); cherry-pick su `interaction-skills/` (iframes, shadow DOM) como overlay de referencia. MIT, joven. Detail: `evaluations/browser-use-browser-harness.md` |

### MCPs evaluados 2026-05-07

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [upstash/context7](https://github.com/upstash/context7) | 54k | **integrated** (2026-07-12) | Instalado user-scope: `claude mcp add -s user context7 -- npx -y @upstash/context7-mcp`, conectado ✓. Live docs lookup vía Upstash. Setup OAuth automático con `npx -y ctx7 setup --claude`. Soluciona "Claude usa docs desactualizadas". ECC bundles it. |
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
| [safishamsi/graphify](https://github.com/safishamsi/graphify) | 63k | skip | 4º tool de code-graph — redundante con `/gsd-graphify` + codegraph + understand-anything. Único diferenciador: ingesta multi-modal (PDFs/vídeo/screenshots vía Whisper), sin necesidad real aquí. MIT. |

### Evaluados 2026-06-08 — round 2 (surgido de IG)

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [mendableai/firecrawl](https://github.com/mendableai/firecrawl) | 130k | cherry-pick | Scraping/crawling a escala + extracción estructurada vía MCP. Self-host OSS (AGPL-3.0) para evitar key. Solo si necesitas bulk scraping; playwright + research skills cubren lo ad-hoc. Detail: `evaluations/mendableai-firecrawl.md` |
| [ComposioHQ/composio](https://github.com/ComposioHQ/composio) | 28.7k | skip | Hub de integraciones (500+ apps) vía MCP. Cloud-only + API key. Net-new pero sin caso de uso para solo dev token-disciplined. Revisit si surge automatización cross-app. |
| [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory) | 26.1k | skip | Memory API cloud. Solape directo con claude-mem (mismo motivo que agentmemory). Cloud lock-in sin ganancia neta. |
| [czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp) | 21.6k | skip | MCP de n8n (1851 nodes, validación de workflows). Fuera de scope — no usas n8n. Revisit si n8n entra al stack. MIT. |

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
| [nexu-io/open-design](https://github.com/nexu-io/open-design) | 61.5k | skip | App desktop GUI (clon open-source de Claude Design, 259 skills). Solapa con impeccable+generate-image+infographics; GUI choca con workflow terminal-native. Apache-2.0. |
| [santifer/career-ops](https://github.com/santifer/career-ops) | 48k | skip | Job-search command center (Playwright portales, fit-scoring CV). Sin workflow de búsqueda de empleo. Revisit si cambia. MIT. |
| [Upload-Post/upload-post-skill](https://github.com/Upload-Post/upload-post-skill) | — | skip | Skill que envuelve el SaaS Upload-Post (publicar a redes). Sin workflow de contenido. Key + coste mensual. |
| typefully (SaaS) | — | skip | Wrapper de SaaS para schedule de threads X/LinkedIn. Sin workflow de contenido; sin repo canónico. |

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
| [@speedy_devv DY5w_nQDNw7](https://instagram.com/p/DY5w_nQDNw7/) | ig-post | skip | 2026-06-08 | Opus 4.8 cheatsheet (marketing "comment OPUS"). Detail: `notes/claude-env-ideas_20260608_143301.md` |
| [AI With Mariah DYcTfiiFtXD](https://instagram.com/p/DYcTfiiFtXD/) | ig-post | research-only | 2026-06-08 | 10 Substack reads sobre AI agéntica; surfaces OpenClaw + Chief-of-Staff pattern. Detail: `notes/claude-env-ideas_20260608_143446.md` |
| [@chase.ai DX5m_9LnDA8](https://instagram.com/p/DX5m_9LnDA8/) | ig-post | cherry-pick | 2026-06-08 | Top-10 OSS repos May — surfaces impeccable, claude-video, codeburn, n8n-mcp, design-extract, open-design. Detail: `notes/claude-env-ideas_20260608_143642.md` |
| [Claude finance news DYFPjHBkwLw](https://instagram.com/p/DYFPjHBkwLw/) | ig-post | skip | 2026-06-08 | News/meme: Anthropic finance agents. Sin sustancia accionable. Detail: `notes/claude-env-ideas_20260608_143705.md` |
| [/memory pattern DX9TVLojYTa](https://instagram.com/p/DX9TVLojYTa/) | ig-post | skip | 2026-06-08 | `/memory` multi-tier CLAUDE.md — ya es patrón core. Detail: `notes/claude-env-ideas_20260608_143746.md` |
| [best-skills pyramid DXYtOdgCoEO](https://instagram.com/p/DXYtOdgCoEO/) | ig-post | cherry-pick | 2026-06-08 | "Best skills 2026" — surfaces firecrawl, composio, supermemory, remotion. Detail: `notes/claude-env-ideas_20260608_143753.md` |
| [Enrique Rocha DW-0kCiAsLn](https://instagram.com/p/DW-0kCiAsLn/) | ig-post | skip | 2026-06-08 | Ultraplan — ya cubierto por `gsd-ultraplan-phase`. Detail: `notes/claude-env-ideas_DW-0kCiAsLn.md` |
| [PabloInPublic DY7ocxjOu-6](https://instagram.com/p/DY7ocxjOu-6/) | ig-post | research-only | 2026-06-08 | Dynamic workflows nativos (Claude escribe su orquestación). Comparar vs GSD. Detail: `notes/claude-env-ideas_DY7ocxjOu-6.md` |
| [Girsta AI DYCVxTstJdE](https://instagram.com/p/DYCVxTstJdE/) | ig-post | skip | 2026-06-08 | "Find Skills" plugin — ya tienes `find-skill`. Detail: `notes/claude-env-ideas_DYCVxTstJdE.md` |
| [Vicente Burgos DYCzXW0tgav](https://instagram.com/p/DYCzXW0tgav/) | ig-post | skip | 2026-06-08 | Finance agents (news/marketing). Detail: `notes/claude-env-ideas_DYCzXW0tgav.md` |
| [James Goldbach DYk9qkGE7Sv](https://instagram.com/p/DYk9qkGE7Sv/) | ig-post | research-only | 2026-06-08 | Stack /goal /agents /ultrareview /ultraplan encadenados. Detail: `notes/claude-env-ideas_DYk9qkGE7Sv.md` |
| [nicnonac DYKKzzGSbtA](https://instagram.com/p/DYKKzzGSbtA/) | ig-post | research-only | 2026-06-08 | github/spec-kit — competidor directo de GSD. Head-to-head pendiente. Detail: `notes/claude-env-ideas_DYKKzzGSbtA.md` |
| [Javi Niguez DYo7vfqKa02](https://instagram.com/p/DYo7vfqKa02/) | ig-post | skip | 2026-06-08 | Spec Kit otra vez (dup de DYKKzzGSbtA). Detail: `notes/claude-env-ideas_DYo7vfqKa02.md` |
| [Bashiri DYsMnzehGwH](https://instagram.com/p/DYsMnzehGwH/) | ig-post | skip | 2026-06-08 | AI-engineer mistakes (career-bait; conceptos RAG/LangGraph). Detail: `notes/claude-env-ideas_DYsMnzehGwH.md` |
| [PabloInPublic DYXpWy8uu_b](https://instagram.com/p/DYXpWy8uu_b/) | ig-post | cherry-pick | 2026-06-08 | 3 frontend-design skills: impeccable, Emil Kowalski motion, Taste. Detail: `notes/claude-env-ideas_DYXpWy8uu_b.md` |
| [Enrique Rocha DarnXyuCs5o](https://instagram.com/p/DarnXyuCs5o/) | ig-post | skip | 2026-07-12 | Fin de promo verano Fable/límites + "hazte tu sistema multi-modelo". Marketing de urgencia, sin sustancia accionable. Detail: `notes/claude-env-ideas_DarnXyuCs5o.md` |
| [PabloInPublic DaiolqmMMK7](https://instagram.com/p/DaiolqmMMK7/) | ig-post | skip | 2026-07-12 | "Fable de jefe, Sonnet a currar" (beta API orquestación). El patrón YA es la política de tiers + `model_overrides` GSD. Único delta: la beta API de mid-task consultation — vigilar cuando salga de beta. Detail: `notes/claude-env-ideas_DaiolqmMMK7.md` |
| [forneess DaaEtDDgKuG](https://instagram.com/p/DaaEtDDgKuG/) | ig-post | research-only | 2026-07-12 | Skill "Noodles": diagrama interactivo de call-graph del repo (zoom + drill-down). Repo por identificar (lead-magnet "comenta NOODLE"). Comparar vs `gsd-map-codebase`/`gsd-graphify` antes de verdict final. Detail: `notes/claude-env-ideas_DaaEtDDgKuG.md` |
| [Don Pablo AI DaOVMQrsxLa](https://instagram.com/p/DaOVMQrsxLa/) | ig-post | skip | 2026-07-12 | Explainer "harness > cerebro IA" + curso lead-magnet. El concepto ya es el core de este env. Detail: `notes/claude-env-ideas_DaOVMQrsxLa.md` |
| [nicoazero DaJB1AfMALF](https://instagram.com/p/DaJB1AfMALF/) | ig-post | skip | 2026-07-12 | Buscador de skills en marketplace con auto-install. Redundante con este registro (curación manual > instalar por nº descargas) y `find-skill` acaba de caer en quarantine por 0 uso. Riesgo supply-chain. Detail: `notes/claude-env-ideas_DaJB1AfMALF.md` |
| [meme SQL DZ72UznJjYr](https://instagram.com/p/DZ72UznJjYr/) | ig-post | skip | 2026-07-12 | Meme ("SQL injection"). Sin transcripción útil. Detail: `notes/claude-env-ideas_DZ72UznJjYr.md` |
| [errores vibe-coding DZ05opyO850](https://instagram.com/p/DZ05opyO850/) | ig-post | skip | 2026-07-12 | RLS off / CORS / race conditions + doc 27 criterios (lead-magnet). Básicos ya cubiertos: RLS FORCE es regla día-1 en Clibit. Detail: `notes/claude-env-ideas_DZ05opyO850.md` |
| [5 MCPs DZveeKYvc1h](https://instagram.com/p/DZveeKYvc1h/) | ig-post | cherry-pick | 2026-07-12 | 5 MCPs: playwright ✓, sequential-thinking ✓, Knowledge Graph Memory (redundante con claude-mem), plugin Codex (adversarial cross-vendor — el council/reviewers ya cubren), **context7 — sigue "install ya" desde 2026-05-07 y sin instalar → action item**. Detail: `notes/claude-env-ideas_DZveeKYvc1h.md` |
| [canary CLAUDE.md DZcdGxvTLno](https://instagram.com/p/DZcdGxvTLno/) | ig-post | skip | 2026-07-12 | Canario "empieza cada respuesta con mi nombre" para detectar drift. Línea permanente por señal débil — contradice L002; el drift se gestiona con /compact disciplinado (L014). Detail: `notes/claude-env-ideas_DZcdGxvTLno.md` |
| [Loop Engineering DZZzd9msHJY](https://instagram.com/p/DZZzd9msHJY/) | ig-post | research-only | 2026-07-12 | Steinberger/Cherny: "no promptees agentes, diseña loops que los prompteen". 5 bloques: automations (heartbeat) / worktrees / skills / verification / memory. GSD ya cubre 4; **delta real = automations programadas (crons, wakeups, /loop)** — conecta con `gsd-autonomous`. Candidato a spike. Detail: `notes/claude-env-ideas_DZZzd9msHJY.md` |
| [DaPwq_hk_Yl](https://instagram.com/p/DaPwq_hk_Yl/) | ig-post | queued | 2026-07-12 | Login-gated — captura falló incluso con yt-dlp 2026.07.04. Pendiente `claude_env/cookies.txt`. |
| [DY4gcNRkseO](https://instagram.com/p/DY4gcNRkseO/) | ig-post | queued | 2026-07-12 | Login-gated — pendiente `claude_env/cookies.txt`. |
| [DY1tRvLEqXU](https://instagram.com/p/DY1tRvLEqXU/) | ig-post | queued | 2026-07-12 | Login-gated — pendiente `claude_env/cookies.txt`. |

## Transcript tooling (2026-07-12)

4 herramientas del mismo tema (ver/exportar/buscar transcripts de sesión de Claude Code), evaluadas **comparativamente**: gana como mucho una por caso de uso; las redundantes → skip. El env ya tiene claude-mem (memoria + búsqueda cross-session sobre observaciones destiladas), codeburn (analítica de tokens sobre `~/.claude/`) y GSD (su propio state/session tracking) — una herramienta de transcript solo supera skip si añade algo que esos no cubren. Dos casos net-new emergen: **compartir una sesión (HTML/Gist)** → simonw; **buscar el JSONL crudo + resucitar/forkar sesiones** → raine.

| Source | Stars | Verdict | Notes |
|---|---|---|---|
| [raine/claude-history](https://github.com/raine/claude-history) | 389 | **integrated** (2026-07-12) | Instalado v0.1.70 binario linux-amd64 checksum-verificado → `~/.local/opt/claude-history/` + symlink en `~/.local/bin`. **La única con capacidad net-new real.** Búsqueda fuzzy+semántica sobre el JSONL crudo (incl. tool-outputs) en TUI terminal + **resume/fork/resurrección** de sesiones (cross-project vía git worktrees). Rust, MIT, activo. Cubre solo los 2 ejemplos net-new del brief (grep JSONL + resucitar sesiones). Caveats: muy pre-1.0 (v0.1.x), 1 maintainer, install `curl\|bash` (usar binario brew, no el pipe); sin toolchain Rust → binario prebuilt. Detail: `evaluations/raine-claude-history.md` |
| [simonw/claude-code-transcripts](https://github.com/simonw/claude-code-transcripts) | 1.6k | integrate | Gana el caso **"compartir una sesión"**: export HTML mobile-friendly + **publish a GitHub Gist** (link shareable sin auto-hostear) + batch-archive de todo el historial. `uv tool install`, zero-config, Apache-2.0. Simon Willison → mantenimiento fiable (pesar realidad, no solo stars). Caso distinto a raine → ambos integrate sin solaparse. On-demand (compartir es ocasional para solo dev). Detail: `evaluations/simonw-claude-code-transcripts.md` |
| [daaain/claude-code-log](https://github.com/daaain/claude-code-log) | 1.1k | cherry-pick | La más pulida (uvx/pip, MIT, v1.5.0, 18 releases) pero redundante: su HTML-export lo gana simonw (con Gist) y su token-tracking lo hace mejor codeburn. Delta no cubierto = **export Markdown con detail-levels** (`full\|high\|low\|minimal\|user-only`) para destilar una sesión y pegarla en doc/issue/PR. Instalar solo si aparece esa necesidad. Detail: `evaluations/daaain-claude-code-log.md` |
| [varunr89/claude-transcript-viewer](https://github.com/varunr89/claude-transcript-viewer) | 1 | skip | Wrapper downstream de simonw/claude-code-transcripts (lo usa para generar el HTML, luego re-indexa en SQLite + FTS5 + vectores). Web-app en localhost:3000 (choca con terminal-native), sesgo Apple-Silicon (embeddings MLX), 1⭐ / 14 commits / sin actividad reciente. Su búsqueda semántica es redundante con claude-mem + raine. |

---

## Mantenimiento

- **Añadir nueva fuente**: usar skill `/evaluate <url>` — fetcha metadata, pregunta verdict, escribe detail file + actualiza esta tabla.
- **Buscar si algo ya fue evaluado**: `grep <url-or-keyword> EVALUATIONS.md` o usar `/check-evaluation <query>`.
- **Revisitar entries `reconsider`**: revisión periódica (mensual) de entries con `revisit_after` vencido.
- **Cutoff de exploración**: NO existe — la evaluación continua es parte del producto. Lo que sí hay es priorización: P1 entries (anthropics/skills, superpowers, everything-claude-code) bloquean decisiones arquitectónicas; el resto se evalúa en background.
