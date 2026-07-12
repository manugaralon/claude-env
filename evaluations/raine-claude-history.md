---
source: https://github.com/raine/claude-history
type: github-repo
evaluated_date: 2026-07-12
verdict: integrate
tags: [transcript, search, session-resume, jsonl, cli, rust, terminal-native]
extracts: [claude-history CLI — búsqueda de historial + resume/fork de sesiones]
revisit_after:
---

# raine/claude-history

**Summary**: CLI companion de Claude Code escrito en Rust (~389 stars, MIT, v0.1.70 del 5-jul-2026, activo, 1 maintainer dominante). Lee directamente los JSONL de `~/.claude/projects/`. Búsqueda **fuzzy** con scoring por campo + indexado de tool-outputs, y opción de búsqueda **semántica** que rankea por significado. TUI terminal: visor de conversación con navegación estilo vim, búsqueda in-viewer, render Markdown, toggle de thinking-blocks, ciclado de tool-calls (summary/truncated/full). **Resume/fork** de conversaciones desde la propia UI (keybindings configurables), **fork cross-project** (trabajo entre git worktrees), export + clipboard de una conversación o de un mensaje suelto. Install: `curl -fsSL .../install.sh | bash` (binario prebuilt), `brew install raine/claude-history/claude-history`, o `cargo install claude-history`.

## Why this verdict
integrate — es la **única de las 4 que aporta capacidad net-new real** que el env no cubre: grep/búsqueda sobre el transcript JSONL **crudo** (incluidos tool-outputs) + **resurrección/fork de sesiones antiguas** desde el terminal. claude-mem busca sobre observaciones destiladas, no sobre el transcript crudo, y no puede reabrir ni forkar una sesión; codeburn es analítica de tokens; GSD trackea su propio estado. Es exactamente el par de casos net-new que el brief nombraba (grep sobre JSONL + resucitar sesiones) — y esta herramienta cumple los dos sola. Terminal-native y zero-config, encaja con el flujo de Manuel. La candidata a instalar ya.

## Specific items extracted
- El binario `claude-history` como capa de búsqueda-de-historial + resume/fork/resurrección de sesiones.

## Caveats / risks
- Muy pre-1.0 (v0.1.x) + 1 maintainer dominante → bus-factor. Superficie de cambio de API alta.
- El install ofrece `curl | bash`: preferir el binario de Homebrew o `cargo install`, o revisar el script antes (mismo patrón ya flagged en codegraph).
- Rust no está en el stack declarado de Manuel (Python/uv + Node). Sin toolchain Rust, la vía real es el binario prebuilt (brew o el script revisado), no `cargo install`.
- Verificar el backend de la búsqueda semántica (embeddings local vs key/descarga) antes de depender de ese modo; la fuzzy no lo necesita.
