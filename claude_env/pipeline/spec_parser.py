"""YAML and Markdown spec file parsers that produce ProjectSpec instances."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from claude_env.models.project_spec import ProjectSpec


def parse_yaml_spec(path: Path) -> ProjectSpec:
    """Parse a YAML spec file directly into ProjectSpec.

    The YAML file must have keys matching ProjectSpec fields.
    Extra keys are rejected by model_config extra='forbid'.
    """
    raw = yaml.safe_load(path.read_text())
    return ProjectSpec.model_validate(raw)


def parse_markdown_spec(path: Path) -> ProjectSpec:
    """Extract ProjectSpec fields from a structured markdown spec.

    Expected format:
    - H1 (# Title) becomes name (lowercased, spaces->hyphens)
    - ## Description section becomes description
    - ## Stack or ## Tech Stack section: bullet list becomes tech_stack
    """
    text = path.read_text()

    name_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    name = name_match.group(1).strip().lower().replace(" ", "-") if name_match else "unknown"

    desc_match = re.search(
        r"^## Description\s*\n(.+?)(?=\n##|\Z)", text, re.MULTILINE | re.DOTALL
    )
    description = desc_match.group(1).strip() if desc_match else ""

    stack_match = re.search(
        r"^## (?:Stack|Tech Stack)\s*\n(.+?)(?=\n##|\Z)", text, re.MULTILINE | re.DOTALL
    )
    tech_stack: list[str] = []
    if stack_match:
        tech_stack = [
            line.strip().removeprefix("- ").strip()
            for line in stack_match.group(1).splitlines()
            if line.strip()
        ]

    return ProjectSpec(name=name, description=description, tech_stack=tech_stack)
