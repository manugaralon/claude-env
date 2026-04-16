"""Template rendering registry — the single path for all generated artifacts.

Wraps jinja2.Environment with:
- StrictUndefined: missing context vars raise immediately (closes research Pitfall #5)
- autoescape=False: output is markdown/text, not HTML
- keep_trailing_newline=True: preserves final newline of template files
- Absolute path guard: prevents cwd-dependent lookup failures (Pitfall #2)
"""
from __future__ import annotations

from pathlib import Path

import jinja2


class TemplateRegistry:
    """Render-by-name facade over jinja2.Environment."""

    def __init__(self, templates_dir: Path) -> None:
        """Initialize the registry rooted at `templates_dir`.

        Args:
            templates_dir: Absolute path to the directory containing `.j2` files.

        Raises:
            ValueError: if `templates_dir` is not absolute.
        """
        if not templates_dir.is_absolute():
            raise ValueError(
                f"templates_dir must be absolute, got: {templates_dir}"
            )
        self._templates_dir = templates_dir
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            autoescape=False,
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )

    def render(self, template_id: str, context: dict[str, object]) -> str:
        """Render template `template_id` with `context`.

        Args:
            template_id: Filename of the template (e.g., `"claude_md_project.j2"`).
            context: Variables available inside the template.

        Returns:
            Rendered string.

        Raises:
            jinja2.TemplateNotFound: if `template_id` does not exist.
            jinja2.UndefinedError: if a referenced variable is missing from context.
        """
        template = self._env.get_template(template_id)
        return template.render(**context)

    def list_templates(self) -> list[str]:
        """Return all template filenames discoverable from `templates_dir`."""
        return self._env.list_templates()
