---
source: https://github.com/browser-use/browser-harness
type: github-repo
evaluated_date: 2026-06-08
verdict: cherry-pick
tags: [browser-automation, playwright, self-improving, claude-skill]
extracts: [interaction-skills/ library (iframes, shadow DOM, downloads)]
revisit_after:
---

# browser-use/browser-harness

**Summary**: CDP-based browser-automation harness from the browser-use org (~14.5k stars, MIT, Python). Wraps Playwright-level primitives behind a heredoc Python interface + a `SKILL.md` Claude reads as a slash-command. Self-improving "mini Ralph loop": writes Markdown playbooks into `agent-workspace/domain-skills/` as it learns a site's quirks, re-read on later runs (`BH_DOMAIN_SKILLS=1`). Also ships remote cloud-browser w/ profile sync, parallel sub-agent isolation, and a structured `interaction-skills/` library.

## Why this verdict
cherry-pick — DON'T install as primary browser automation (the `playwright` MCP covers the base case, ~80% overlap). Cherry-pick the `interaction-skills/` Markdowns (iframes, shadow DOM, cross-origin, downloads) as a reference overlay for when the playwright MCP hits edge cases. The domain-skills accumulation loop is only worth enabling if repeated same-site automation becomes a real workload.

## Specific items extracted
- The `interaction-skills/` library, dropped into `.claude/skills/browser/` as a reference overlay.

## Caveats / risks
- Young repo (Apr 2026), no tagged releases (HEAD is the artifact), 118 open issues.
- Bad auto-written playbooks can poison future runs → manual pruning needed.
- Remote mode needs `BROWSER_USE_API_KEY` (vendor lock-in/billing).
- "Self-improvement" is file-based knowledge accumulation, not weights/reflection.
