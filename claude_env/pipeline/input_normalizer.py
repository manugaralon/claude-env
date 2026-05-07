"""InputNormalizer — entry point that converts freeform text or spec files into ProjectSpec."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from claude_env.models.project_spec import ProjectSpec
from claude_env.pipeline.spec_parser import parse_markdown_spec, parse_yaml_spec

# anthropic is only required for from_freeform() (the LLM path). Importing
# it at module load would force every consumer (including --spec callers
# that bypass the LLM) to install anthropic. Defer to method call sites.
if TYPE_CHECKING:
    import anthropic

_LLM_MODEL = "claude-haiku-3-5-20241022"

_SYSTEM_PROMPT = """\
You are a project specification extractor. Given a freeform project description, \
output a JSON object with:
- name: short slug (lowercase, hyphens)
- description: one paragraph summary
- domain_hint: one of "web", "cli", "data", "infra", or "general"
- languages: list of programming languages mentioned or implied
- tech_stack: list of frameworks, databases, tools mentioned
- constraints: list of explicit constraints or requirements
- known_skills: list of specific capability slugs if mentioned

Output ONLY the JSON object, no markdown, no explanation."""


def _extract_json(raw: str) -> str:
    """Strip markdown code fences if present."""
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```\w*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)
    return stripped.strip()


class InputNormalizer:
    """Normalize project input (freeform text or spec file) into ProjectSpec."""

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        # Defer anthropic.Anthropic() construction until from_freeform() is
        # actually called — from_spec_file() does not need an LLM client,
        # and forcing the dep at __init__ time means --spec callers can't
        # use the CLI without anthropic installed and configured.
        self._client = client

    def from_freeform(self, text: str) -> ProjectSpec:
        """Extract ProjectSpec from freeform natural language text via LLM."""
        from anthropic.types import TextBlock

        if self._client is None:
            import anthropic as _anthropic
            self._client = _anthropic.Anthropic()
        message = self._client.messages.create(
            model=_LLM_MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        block = message.content[0]
        if not isinstance(block, TextBlock):
            raise ValueError(f"Unexpected content block type: {type(block)}")
        raw_json = _extract_json(block.text)
        data = json.loads(raw_json)
        return ProjectSpec.model_validate(data)

    def from_spec_file(self, path: Path) -> ProjectSpec:
        """Parse a structured spec file into ProjectSpec.

        Dispatches to YAML or Markdown parser based on file extension.

        Raises:
            ValueError: if file extension is not .yaml, .yml, or .md
        """
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            return parse_yaml_spec(path)
        if suffix == ".md":
            return parse_markdown_spec(path)
        raise ValueError(f"Unsupported spec file format: {suffix}")
