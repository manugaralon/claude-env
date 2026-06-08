---
source: https://github.com/rohitg00/agentmemory
type: github-repo
evaluated_date: 2026-06-08
verdict: skip
tags: [memory, persistence, claude-plugin, benchmarks]
extracts: []
revisit_after:
---

# rohitg00/agentmemory

**Summary**: Persistent-memory plugin for AI coding agents — auto-captures sessions via lifecycle hooks and serves them back through hybrid (BM25 + vector + knowledge-graph) semantic search, stored locally in SQLite. TypeScript, Apache-2.0, ~21.8k stars. Install: `/plugin marketplace add rohitg00/agentmemory` + `/plugin install agentmemory`. Same integration surface as claude-mem.

## Why this verdict
skip — heavily redundant with `claude-mem`, which is already integrated, active, and loading observations in live sessions. Persistent agent memory is a solved problem in this env. The deltas (4-tier consolidation, hybrid retrieval, cross-agent RBAC, pre-storage secret stripping, session replay) don't solve an unmet need, and switching a sticky memory system is high-cost.

## Caveats / risks
- "Based on real-world benchmarks" is overstated: the headline 95.2% R@5 on LongMemEval-S is retrieval-recall only and self-measured; claude-mem isn't even in their COMPARISON.md; the "real-world" QUALITY.md eval is 240 synthetic observations, not production data.
- Single-maintainer (rohitg00 ~381 commits vs 10 next); GOVERNANCE/ROADMAP read as growth-optics, MAINTAINERS lists one person. Pre-1.0.
- Apache-2.0, local SQLite, no phone-home by default (optional cloud embeddings need API keys).

## Revisit trigger
Only if it posts a head-to-head win vs claude-mem on a neutral benchmark.
