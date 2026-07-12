---
source: https://github.com/simonw/claude-code-transcripts
type: github-repo
evaluated_date: 2026-07-12
verdict: integrate
tags: [transcript, html-export, sharing, gist, jsonl, cli, python, uv]
extracts: [claude-code-transcripts CLI — export HTML shareable + publish a Gist + batch-archive]
revisit_after:
---

# simonw/claude-code-transcripts

**Summary**: CLI Python de Simon Willison (~1.6k stars, Apache-2.0, v0.6 del 25-ene-2026). Install `uv tool install claude-code-transcripts`. Convierte session files (JSON/JSONL) de `~/.claude/projects/` — o sesiones traídas vía la Claude API — en HTML limpio mobile-friendly con paginación e índice/timeline. Session-picker interactivo de sesiones recientes, **publish directo a GitHub Gist**, **batch-convert** de todo el historial a un archivo navegable, auto-nombrado de dirs por session ID, generación de links a commits (si se le pasa el repo), y opción de incluir el JSON/JSONL original en el output.

## Why this verdict
integrate — gana el caso de uso **"export shareable de una sesión"**: el publish a Gist es el único de las 4 herramientas que produce un enlace compartible sin auto-hostear nada. Net-new — nada en el env exporta ni comparte una sesión (claude-mem es memoria, codeburn tokens, GSD estado). Mantenimiento fiable: es un tool pequeño de Simon Willison (pesar realidad de mantenimiento, no solo stars — su track-record de tools pequeños es sólido). Zero-config vía `uv`, que Manuel ya usa a diario. Caso de uso **distinto** al de raine (compartir/archivar vs buscar/resucitar), así que ambos pueden ser integrate sin solaparse.

## Specific items extracted
- El CLI `claude-code-transcripts`, en particular `publish` (Gist) y el batch-archive de todo el historial.

## Caveats / risks
- Apache-2.0, limpio, sin lock-in.
- El batch-archive de todo el historial puede ser pesado — correr on-demand, no como cron.
- Solapa con daaain/claude-code-log en el HTML-export puro, pero gana por el share vía Gist + el track-record del mantenedor. Si se prefiriera un browser local más completo (Markdown, TUI, detail-levels), ver daaain.
