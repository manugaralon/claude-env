---
source: https://github.com/Manavarya09/design-extract
type: github-repo
evaluated_date: 2026-06-08
verdict: integrate
tags: [design, frontend, design-tokens, mcp, scraping]
extracts: [designlang CLI, design-extract MCP server]
revisit_after:
---

# Manavarya09/design-extract

**Summary**: Headless-Chromium (Playwright) CLI (~3.1k stars, MIT) that reads any live URL's rendered DOM and emits a full design system: DTCG tokens (primitive/semantic/composite), Tailwind v4 config, shadcn/ui theme, Figma variables, motion tokens, brand voice, WCAG audit, CSS health report, native iOS/Android/Flutter emitters. Ships an MCP server wired to Claude Code. Install: `npx designlang <url>` → outputs to `.claude/` or a tokens dir.

## Why this verdict
integrate — fills the *inward* gap nothing in the stack covers. impeccable generates **outward** (prompt → design); design-extract extracts **inward** (URL → tokens). Complementary pipeline stages, not duplicates. Enables the "clone/match this site's design" workflow and can feed `gsd-ui-phase` with real tokens.

## Specific items extracted
- The `designlang` CLI and its MCP server.

## Caveats / risks
- MIT, MCP-native, actively updated. Headless-Chromium/Playwright dependency at runtime.
