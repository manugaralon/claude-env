"""analyzer.py — evaluate captured notes for claude-env applicability."""
from __future__ import annotations

from pathlib import Path

import anthropic

ANALYSIS_MARKER = "## Análisis claude-env"

_PROJECT_CONTEXT = """\
claude-env is a Python CLI tool (Typer) that generates calibrated Claude Code environments
from project specs. Given a project description it:

1. Classifies the project by domain (web, data, cli, infra, general) using YAML profiles
2. Plans which files to generate (GenerationPlan)
3. Renders Jinja2 templates and writes:
   - .claude/CLAUDE.md  — project conventions: plan→execute→verify workflow, context
     management, Karpathy's 4 principles (read code not docs, copy don't abstract,
     TODOs not stubs, code not words)
   - .claude/skills/    — slash commands: fix-issue, create-pr, run-lint,
     quality-gate, karpathy-guidelines
   - .claude/agents/    — subagents: code-reviewer, security-reviewer, advisor
   - .claude/settings.json — tool permissions and hooks

Pipeline stages:
  input_normalizer  → ProjectSpec (from freeform text, YAML, or --description flag)
  domain_classifier → DomainProfile
  environment_planner → GenerationPlan (selects templates per domain)
  generator         → written files (Jinja2 render)

Current CLI commands: setup (global ~/.claude/), bootstrap (per-project .claude/),
capture (Instagram/video → .md), analyze (this command).

Open improvement areas:
- Richer domain profiles and smarter stack detection
- More opinionated CLAUDE.md templates (more conventions, better defaults)
- New skills and agents worth generating automatically
- Better CLI UX and onboarding flow
- Hook templates and settings patterns\
"""

_SYSTEM = """\
You evaluate captured content (social media posts, articles, videos) to identify
concrete, actionable ideas for improving claude-env. Be specific. Vague suggestions
like "improve the templates" are not useful. Name the exact file, template, pipeline
stage, or CLI command where an idea would land.\
"""


def _build_prompt(content: str) -> str:
    return (
        "## What claude-env is\n\n"
        + _PROJECT_CONTEXT
        + "\n\n## Captured content to evaluate\n\n"
        + content[:6000]
        + "\n\n## Your task\n\n"
        "Evaluate this content and respond in exactly this format:\n\n"
        "**Relevancia:** [alta / media / baja / ninguna]\n\n"
        "**Ideas aplicables:**\n"
        "- [idea concreta] → [dónde: template name / pipeline stage / CLI command / file] "
        "→ [cómo en 1-2 frases]\n"
        "(one bullet per idea, or write `ninguna` if none apply)\n\n"
        "**Descartado:** [what is noise, marketing, or irrelevant — 1 sentence]\n\n"
        "If no ideas apply, say so directly. Do not pad the output."
    )


def _strip_analysis(text: str) -> str:
    idx = text.find(ANALYSIS_MARKER)
    return text[:idx].rstrip() if idx != -1 else text


def _already_analyzed(text: str) -> bool:
    return ANALYSIS_MARKER in text


def _extract_body(md_text: str) -> str:
    if md_text.startswith("---"):
        end = md_text.find("---", 3)
        if end != -1:
            return md_text[end + 3:].strip()
    return md_text.strip()


def analyze_file(path: Path, client: anthropic.Anthropic, force: bool = False) -> bool:
    """Append an analysis section to a captured .md file. Returns True if written."""
    text = path.read_text(encoding="utf-8")

    if _already_analyzed(text) and not force:
        return False

    body = _extract_body(_strip_analysis(text))
    prompt = _build_prompt(body)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    analysis = message.content[0].text  # type: ignore[union-attr]

    base = _strip_analysis(text)
    updated = f"{base}\n\n{ANALYSIS_MARKER}\n\n{analysis}\n"
    path.write_text(updated, encoding="utf-8")
    return True
