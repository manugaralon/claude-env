---
source: https://github.com/pbakaus/impeccable
type: github-repo
evaluated_date: 2026-06-08
verdict: integrate
tags: [frontend, design, ui, claude-skill, anti-slop]
extracts: [impeccable skill (/impeccable commands), deterministic anti-pattern rules, init → DESIGN.md flow]
revisit_after:
---

# pbakaus/impeccable

**Summary**: Comprehensive frontend-design skill (~36k stars, Apache-2.0) extending Anthropic's base frontend-design skill. 7 domain reference files (typography, OKLCH color, spatial, motion, interaction, responsive, UX writing), 23 `/impeccable` commands, 27 deterministic anti-pattern rules + a 12-rule LLM critique pass. CLI (`npx impeccable`) and optional browser extension run rules without LLM calls. Install: `npx impeccable skills install` (auto-detects Claude Code) or `/plugin marketplace add pbakaus/impeccable`.

## Why this verdict
integrate — most mature of the frontend trio; fills a real design-quality gap. Fits the GSD flow at a different altitude than existing UI tooling: `gsd-ui-phase` = pre-code design contract, **impeccable = implementation polish + deterministic audit**, `gsd-ui-review` = final 6-pillar gate. The `/impeccable live` browser loop and deterministic anti-pattern rules are things gsd-ui-review lacks.

## Specific items extracted
- The skill itself (esp. `audit` / `polish` / `animate` commands).
- The deterministic anti-pattern CLI (runs without LLM/token cost).
- The `/impeccable init → DESIGN.md` persistent design-context flow.

## Caveats / risks
- 23 commands = surface area (likely ~3 used 90% of the time); context-heavy if all 7 refs load — use `/impeccable pin` to scope.
- Apache-2.0, clean; actively developed.
