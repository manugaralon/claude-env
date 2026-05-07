#!/usr/bin/env python3
"""Audit Claude Code skills by frontmatter quality.

Scores each SKILL.md based on five signals:
  +2  Explicit TRIGGER keyword in frontmatter
  +1  Explicit SKIP keyword
  +1  allowed-tools field present
  +1  Examples present
  +1  Description has concrete use-case keywords (when/use this/invoke/fires/applies)
       AND is longer than 80 chars

Max score: 6/6.

Run:
    python3 audit-skill-frontmatter.py [skills_dir]

Default skills_dir: ~/.claude/skills

Output:
    Sorted table (worst first) with score, skill name, flags (TSAED).
    Summary line counting weak (≤2) vs strong (≥5).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"
MAX_SCORE = 6


@dataclass
class SkillScore:
    path: Path
    name: str
    score: int = 0
    flags: dict[str, bool] = field(default_factory=dict)
    error: str | None = None


def parse_frontmatter(content: str) -> tuple[str, str]:
    """Return (frontmatter_text, body). Empty frontmatter if missing."""
    if not content.startswith("---"):
        return "", content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return "", content
    return parts[1], parts[2]


def score_skill(path: Path) -> SkillScore:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return SkillScore(path=path, name=path.parent.name, error=str(e))

    fm, _body = parse_frontmatter(content)
    fm_lower = fm.lower()

    flags: dict[str, bool] = {
        "trigger": False,
        "skip": False,
        "tools": False,
        "examples": False,
        "specific": False,
    }
    score = 0

    trigger_patterns = (
        r"trigger\s*when[:\s]"
        r"|^trigger\s*:"
        r"|when this fires"
        r"|when to use"
        r"|mandatory\s+triggers?\b"
        r"|strong\s+triggers?\b"
    )
    if re.search(trigger_patterns, fm_lower, re.MULTILINE):
        score += 2
        flags["trigger"] = True

    if re.search(r"\bskip\s*:|skip when|do not use|don't use when", fm_lower):
        score += 1
        flags["skip"] = True

    if re.search(r"^allowed[-_]tools\s*:", fm, re.MULTILINE):
        score += 1
        flags["tools"] = True

    if re.search(r"^\s*example[s]?\s*:", fm_lower, re.MULTILINE):
        score += 1
        flags["examples"] = True

    desc_match = re.search(
        r"^description\s*:\s*(.+?)(?=\n[a-z_-]+\s*:|\Z)",
        fm,
        re.MULTILINE | re.DOTALL,
    )
    if desc_match:
        desc = desc_match.group(1).strip()
        has_keywords = bool(re.search(r"\b(when|use this|invoke|trigger|fires|applies)\b", desc.lower()))
        if len(desc) > 80 and has_keywords:
            score += 1
            flags["specific"] = True

    skill_name = path.parent.name if path.parent.name not in ("skills", "") else path.stem
    return SkillScore(path=path, name=skill_name, score=score, flags=flags)


def flag_string(flags: dict[str, bool]) -> str:
    return "".join(
        letter if flags.get(key, False) else "-"
        for key, letter in [
            ("trigger", "T"),
            ("skip", "S"),
            ("tools", "A"),
            ("examples", "E"),
            ("specific", "D"),
        ]
    )


def main() -> int:
    skills_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SKILLS_DIR
    if not skills_dir.exists():
        print(f"Error: {skills_dir} not found", file=sys.stderr)
        return 1

    skill_files = sorted(skills_dir.glob("**/SKILL.md"))
    if not skill_files:
        print(f"No SKILL.md files found under {skills_dir}", file=sys.stderr)
        return 1

    results = [score_skill(p) for p in skill_files]
    results.sort(key=lambda r: (r.score, r.name))

    print(f"{'SCORE':<8}{'SKILL':<45}{'FLAGS':<10}")
    print(f"{'-' * 8}{'-' * 45}{'-' * 10}")
    for r in results:
        if r.error:
            print(f"{'ERR':<8}{r.name:<45}{r.error}")
            continue
        flag_str = flag_string(r.flags)
        print(f"{r.score}/{MAX_SCORE:<6}{r.name:<45}{flag_str:<10}")

    weak = sum(1 for r in results if r.error is None and r.score <= 2)
    strong = sum(1 for r in results if r.error is None and r.score >= 5)
    total = sum(1 for r in results if r.error is None)
    errors = sum(1 for r in results if r.error)

    print()
    print(f"Total skills: {total}{f' ({errors} read errors)' if errors else ''}")
    print(f"Weak   (≤2/6): {weak}")
    print(f"Strong (≥5/6): {strong}")
    print()
    print("Flags legend: T=trigger  S=skip  A=allowed-tools  E=examples  D=specific-description")
    return 0


if __name__ == "__main__":
    sys.exit(main())
