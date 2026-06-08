---
source: https://github.com/getagentseal/codeburn
type: github-repo
evaluated_date: 2026-06-08
verdict: integrate
tags: [token-tracking, observability, cli, cost, token-discipline]
extracts: [codeburn CLI/TUI, codeburn optimize]
revisit_after:
---

# getagentseal/codeburn

**Summary**: Zero-config local TUI+CLI dashboard (~7.7k stars, MIT) that reads session files from disk across 25+ AI coding tools (Claude Code, Codex, Cursor…). Tracks token spend by project / model / activity type (13 categories incl. Planning, Delegation, Git Ops, MCP), per-MCP overhead, one-shot vs retry rate, cache hit rate, git yield. `codeburn optimize` scans `~/.claude/` for waste: bloated CLAUDE.md, ghost skills/agents never invoked, unused MCP servers, uncapped bash output. Install: `npm i -g codeburn` (or brew). No key, no proxy, no MCP.

## Why this verdict
integrate — directly on-theme for token-discipline, zero-config, reads existing Claude Code data. Complements `gsd-session-report` (per-phase estimate) and `gsd-stats` with cross-session aggregation, automatic activity classification, and waste detection. `codeburn optimize` is immediately useful to audit THIS repo's own `~/.claude/` health.

## Specific items extracted
- codeburn CLI/TUI; run `codeburn optimize` as a first check post-install.

## Caveats / risks
- MIT, local-only (reads `~/.claude/` session data — no key/proxy). Young-ish (44 open issues), actively maintained.
