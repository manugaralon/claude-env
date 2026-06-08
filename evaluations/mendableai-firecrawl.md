---
source: https://github.com/mendableai/firecrawl
type: github-repo
evaluated_date: 2026-06-08
verdict: cherry-pick
tags: [scraping, crawling, mcp, web, extraction]
extracts: [firecrawl-mcp-server (self-hosted OSS)]
revisit_after:
---

# mendableai/firecrawl

**Summary**: Full-stack web scraping/crawling API (~130k stars, AGPL-3.0). Clean markdown+JSON output, JS rendering, rotating proxies, PDF/DOCX parsing, structured extraction, autonomous agent mode (searches+navigates without a URL), interactive automation. Ships an official `firecrawl-mcp-server`. Self-hostable (AGPL OSS, no key) or cloud (`FIRECRAWL_API_KEY`, freemium).

## Why this verdict
cherry-pick — adds bulk/structured extraction + autonomous crawling that the `playwright` MCP (session-oriented, you drive it) and the research skills (`parallel-web`, `perplexity-search`) don't cover cleanly. Self-host the OSS to avoid a key dependency. Worth it ONLY if bulk scraping / structured multi-page extraction becomes a recurring need; if web research stays ad-hoc, defer.

## Specific items extracted
- The MCP server, self-hosted.

## Caveats / risks
- AGPL-3.0 (copyleft) — fine for self-host/internal use; note it for any redistribution.
- Cloud version is freemium/paid. Heavier than playwright for simple one-off fetches.
