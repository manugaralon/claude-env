---
source: https://github.com/daaain/claude-code-log
type: github-repo
evaluated_date: 2026-07-12
verdict: cherry-pick
tags: [transcript, html-export, markdown, tui, token-tracking, jsonl, cli, python]
extracts: [export Markdown con detail-levels — destilador de sesión a texto pegable]
revisit_after:
---

# daaain/claude-code-log

**Summary**: CLI Python (~1.1k stars, MIT, v1.5.0 del 9-jul-2026, 18 releases, muy activo). Install `pip install claude-code-log` o `uvx claude-code-log@latest`. Convierte los JSONL de `~/.claude/projects/` en HTML/Markdown legible. TUI interactivo para navegar sesiones con summaries en tiempo real + quick-actions, procesado de la jerarquía de proyectos completa, **token-usage tracking** por mensaje/sesión, timeline interactivo, filtrado por rango de fechas en lenguaje natural, filtrado runtime vía JS, **detail-levels** (`full|high|low|minimal|user-only`), y **export Markdown** on-demand desde la TUI.

## Why this verdict
cherry-pick — la más pulida y mejor-starred de las 4, pero sus dos features estrella ya están cubiertas por el stack: el **HTML-export** lo gana simonw/claude-code-transcripts (que además comparte vía Gist), y el **token-tracking** lo hace mejor codeburn (cross-tool + `optimize`). El delta genuinamente no cubierto es el **export Markdown con detail-levels** — destilar una sesión a `low`/`minimal` para pegarla en un doc, issue o PR — que ni simonw (solo HTML/Gist) ni codeburn ni claude-mem ofrecen. No es la herramienta primaria de transcript; instalar solo si aparece esa necesidad concreta de "destilar sesión → Markdown pegable". La redundancia, no la calidad, es lo que la baja de integrate.

## Specific items extracted
- Export Markdown con detail-levels (`full|high|low|minimal|user-only`) como destilador de sesión a texto pegable en docs/issues/PRs.

## Caveats / risks
- MIT, zero-config vía `uvx`, muy activo (18 releases) → riesgo técnico bajo. El motivo de no-integrate es solape, no madurez.
- Si por algún motivo se descartara simonw, daaain es el reemplazo natural para el HTML-export local (subiría a integrate).
