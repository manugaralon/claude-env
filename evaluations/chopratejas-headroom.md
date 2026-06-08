---
source: https://github.com/chopratejas/headroom
type: github-repo
evaluated_date: 2026-06-08
verdict: cherry-pick
tags: [token-optimization, compression, mcp, context-engineering, rag]
extracts: [headroom MCP server — headroom_compress / retrieve / stats]
revisit_after:
---

# chopratejas/headroom

**Summary**: Context-compression engine that shrinks tool outputs, logs, files, RAG chunks and conversation history by 60-95% before they hit the LLM. Ships as a Python/TS library, an OpenAI-compatible proxy, AND an MCP server. Python, Apache-2.0, ~17.7k stars, active (monthly releases, pre-1.0). MCP form: `pip install "headroom-ai[mcp]"` + `headroom mcp install` (auto-registers). Exposes `headroom_compress`, `headroom_retrieve` (rehydrate via hash, 1h TTL), `headroom_stats` — a tool, not a proxy.

## Why this verdict
cherry-pick — adopt the MCP-server form ONLY (skip the proxy/library forms). On-target for token discipline; the env currently has no compression layer. Low-cost trial, strong conceptual fit with the Sonnet-default / subagent-delegation / `/compact` mandate.

## Specific items extracted
- The MCP server (compress/retrieve/stats tools) as an on-demand compression layer for large tool outputs.

## Caveats / risks
- Compression is inherently lossy. "Same answers" is benchmark-backed (GSM8K 0.870→0.870, BFCL 97% tools, SQuAD 97%) but fidelity on *your* content is unproven — pin a version and validate before trusting on critical outputs.
- Proxy mode would route data; the MCP/tool mode keeps data local — use MCP mode.
- Pre-1.0, fast-moving API; moderate bus-factor (owner ~957 of ~1400 commits).
