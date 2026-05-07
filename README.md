# claude-env

Genera entornos calibrados de Claude Code a partir de specs de proyecto.

`claude-env` escribe una capa `.claude/` para cualquier proyecto — CLAUDE.md, skills, agents, settings, más un scaffold de `CONTEXT.md` y `docs/adr/` — para que cada sesión de Claude Code arranque con las convenciones correctas para tu stack.

> Versión en inglés: [README-en.md](./README-en.md)

---

## Onboarding

### Qué obtienes

Cuando ejecutas `claude-env bootstrap` en un proyecto, obtienes una capa `.claude/` configurada más artefactos a nivel raíz:

| Artefacto | Para qué sirve |
|---|---|
| `.claude/CLAUDE.md` | Convenciones del proyecto según perfil (think→plan→execute→verify, gestión de contexto, los 4 principios de Karpathy) |
| `.claude/skills/<name>/SKILL.md` | Skills apropiadas al perfil con frontmatter explícito `MANDATORY TRIGGERS / STRONG TRIGGERS / SKIP` para que Claude las auto-invoque cuando corresponde |
| `.claude/agents/<name>.md` | Subagentes (security-reviewer, advisor, reviewers específicos al perfil) |
| `CONTEXT.md` | Scaffold de glosario de dominio — define el lenguaje ubicuo del proyecto. Se rellena con la skill `grill-with-docs` a medida que las decisiones cristalizan. |
| `docs/adr/README.md` | Referencia del formato de ADR (Architecture Decision Record) + reglas de cuándo usarlo. Los ADRs numerados (`0001-slug.md`, `0002-slug.md`) se crean lazy, según aparecen las decisiones. |

### Detección automática de perfil

Señales del filesystem deciden qué perfil aplica:

| Perfil | Señales |
|---|---|
| `web` | `package.json`, `index.html`, `tailwind.config.js`, entry files de React/Vite/Next |
| `cli` | `pyproject.toml` + `cli.py` / `main.py` / `bin/` |
| `data` | Notebooks, parquet, config de ML |
| `infra` | `terraform/`, manifests de k8s |
| `general` | Fallback cuando ninguna señal matchea |

Se puede sobrescribir con `--domain-hint web` si la detección falla.

### Cómo se usa

```bash
# Instalar
uv tool install git+https://github.com/manugaralon/claude-env

# Bootstrap de un proyecto nuevo — primero dry-run para previsualizar
cd your-project
claude-env bootstrap --description "FastAPI todo backend" --dry-run
claude-env bootstrap --description "FastAPI todo backend"

# O con un spec YAML (sin llamada a LLM, determinista)
claude-env bootstrap --spec spec.yaml

# Setup global — escribe la baseline de ~/.claude/ e instala la skill /claude-env
claude-env setup
```

### Desde Claude Code

Después de correr `claude-env setup`, escribe `/claude-env` en cualquier sesión de Claude Code para hacer bootstrap del proyecto actual interactivamente.

### Formato del spec file

```yaml
name: my-project
description: A Python CLI tool for reviewing code
languages: [python]
tech_stack: [typer, rich, pytest]
```

También funciona Markdown — `name` desde el H1, `description` desde el primer párrafo, `tech_stack` parseado de una línea `**Stack:**`.

### Referencia CLI

```
claude-env setup                          Wizard de onboarding global
claude-env bootstrap [DIR]                Genera .claude/ para un proyecto
  --description, -d TEXT                  Descripción de una línea (sin API key)
  --spec, -s PATH                         Spec file YAML o Markdown
  --dry-run                               Previsualiza archivos sin escribir
claude-env version                        Imprime la versión
```

---

## Stack interno

### Pipeline

`claude-env` es un CLI Python 3.12+ construido sobre Pydantic v2 + Jinja2 + Typer. El pipeline de bootstrap es transformación de datos pura, con la I/O aislada al stage final:

```
ProjectSpec (input)                      models/project_spec.py
   │
   ▼ pipeline/input_normalizer.py        (descripción raw → ProjectSpec; LLM solo si no hay --description / --spec)
   │
DomainProfile                            profiles/<domain>.yaml + classifier.py
   │
   ▼ pipeline/environment_planner.py     (puro: ProjectSpec + DomainProfile → GenerationPlan)
   │
GenerationPlan (lista de Artifacts)
   │
   ▼ generator/generator.py              (escribe archivos, sentinel-protected, idempotente)
   │
.claude/ layer + CONTEXT.md + docs/adr/README.md
```

Que el planning sea data pura significa que los tests no necesitan filesystem para validar correctitud — `test_environment_planner.py` ejercita `plan()` contra los YAML de perfiles directamente.

### Layout

```
claude_env/
├── models/          # Schemas Pydantic v2 (extra="forbid", strict types)
│   ├── project_spec.py
│   ├── domain_profile.py
│   └── generation_plan.py
├── pipeline/        # Transformación pura, sin I/O
│   ├── input_normalizer.py    # raw → ProjectSpec
│   ├── domain_classifier.py   # señales filesystem → DomainProfile
│   ├── environment_planner.py # → GenerationPlan
│   └── spec_parser.py
├── generator/       # I/O + idempotencia
│   ├── generator.py           # escribe artifacts con sentinel headers
│   ├── content_catalogue.py   # _SKILL_CATALOGUE: metadata + triggers por skill
│   └── sentinel.py            # protege archivos editados por el usuario de re-writes
├── templates/       # Facade Jinja2
│   └── registry.py            # StrictUndefined + autoescape=False
├── data/            # *.j2 templates (directorio canónico)
└── profiles/        # *.yaml perfiles de dominio
```

### Contrato del frontmatter de skills

Cada SKILL.md generada sigue este patrón:

```yaml
---
name: skill-slug
description: >-
  Resumen de una línea de qué hace la skill.
  MANDATORY TRIGGERS: '/skill-slug', 'frase natural', 'otra frase natural'.
  STRONG TRIGGERS: situaciones contextuales donde la skill debería auto-disparar.
  SKIP: do NOT trigger on casos que parecen similares pero no lo son.
allowed-tools: Bash, Read, Edit, Write
---
```

El patrón `TRIGGER` / `SKIP` es el antídoto a "la skill existe pero Claude no la invoca". `_SKILL_CATALOGUE` en `generator/content_catalogue.py` declara los triggers por skill; `data/skill_stub.j2` los renderiza vía conditionals de Jinja2.

### Re-runs idempotentes

El generator escribe un comentario sentinela en cada archivo gestionado. Re-correr `claude-env bootstrap` actualiza archivos gestionados sin pisar las ediciones del usuario en archivos no-gestionados. Ver `generator/sentinel.py`.

### Probation y telemetría (post-batch 2026-05-07)

El batch del 2026-05-07 (5 commits) trajo infraestructura nueva sustancial (extensión del catálogo de skills, registry de evaluaciones, audit script, ADR-0001) en **probation de 30 días** — ver `NOTICE-30-day-probation.md`. Las invocaciones de skills se loguean por `~/.claude/hooks/skill-usage-log.sh` (PostToolUse con matcher `Skill`). Items con <3 invocaciones tras 30 días son candidatos a borrado o cuarentena. **Data > intención.**

Correr el 2026-06-07:

```bash
bash ~/.claude/scripts/skill-usage-report.sh
```

### Decisiones arquitectónicas

Ver `docs/adr/`:

- **ADR-0001** (`0001-keep-python-cli-architecture.md`) — se mantuvo Python+Jinja2+Pydantic+Typer; rechazada la alternativa bash+YAML manifest. Razonamiento: madurez de validación, infraestructura de tests, lógica condicional de templates y re-runs idempotentes están bien servidos por Python; el equivalente bash sería más frágil con LOC similar.

### Tests

```bash
pytest tests/   # 107/107 esperado
```

Los tests viven al lado del código en ratio ~1:1 LOC. La fixture `real_registry` de `conftest.py` usa `claude_env/data/` como directorio canónico de templates. `test_skill_frontmatter` maneja tanto descripciones inline como folded-scalar (`>-`) para el patrón multi-línea de triggers.

### Registry de evaluaciones (subsistema 13)

`EVALUATIONS.md` en la raíz del repo trackea cada fuente externa considerada para integración (repos, MCPs, posts, videos) con vocabulario de veredicto: `integrate`, `cherry-pick`, `skip`, `research-only`, `reconsider`, `queued`. Las evaluaciones profundas de frameworks estudiados durante la integración viven en `evaluations/`:

- `evaluations/anthropics-skills.md` — repo oficial de skills de Anthropic (288 líneas)
- `evaluations/obra-superpowers.md` — superpowers de Jesse Vincent (740 líneas)
- `evaluations/affaan-m-everything-claude-code.md` — harness ECC (539 líneas)

---

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip
- `ANTHROPIC_API_KEY` — solo necesaria con el prompt freeform interactivo (no necesaria con `--description` o `--spec`)

## Licencia

MIT
