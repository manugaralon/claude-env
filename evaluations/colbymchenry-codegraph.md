---
source: https://github.com/colbymchenry/codegraph
type: github-repo
evaluated_date: 2026-06-08
verdict: cherry-pick
tags: [code-graph, mcp, context-engineering, token-optimization, claude-code]
extracts: [codegraph MCP server — trial as runtime code-graph layer]
revisit_after:
---

# colbymchenry/codegraph

**Summary**: 100%-local MCP server that pre-indexes a codebase into an SQLite-backed knowledge graph (symbols, call edges, dependencies) so agents query structure instead of repeatedly grepping/reading files. TypeScript, MIT, ~44.5k stars, actively maintained (weekly releases, pre-1.0). Install via `npm i -g @colbymchenry/codegraph` + `codegraph install` (auto-wires the Claude Code MCP connection). Exposes `codegraph_explore` / `_search` / `_callers` / `_callees` / `_impact`.

## Why this verdict
cherry-pick — strong standalone MCP worth trialing as the live, agent-callable code-graph layer that GSD's build-time `/gsd-graphify` doesn't cover. Different layer (runtime retrieval vs planning artifact), so complementary rather than redundant. Claimed ~47% fewer tokens / 58% fewer tool calls on its benchmarks.

## Specific items extracted
- The `codegraph` MCP server itself — trial as runtime code-graph indexer on one real project, measure token savings before committing further.

## Caveats / risks
- Pre-1.0; bus-factor risk (one maintainer dominates commits ~355 vs 16 next).
- Install offers a `curl | sh` one-liner — prefer the npm path or review the script first.
- "100% local, no data leaves machine" claim consistent with architecture but unverified.
- Beats Understand-Anything for *agent* consumption; pick one if you don't want two graph layers (see code-graph tension).
