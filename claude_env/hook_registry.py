"""Registry of hook templates referenced by domain profile YAML.

Profile YAML lists `hook_templates: [lint_after_edit, typecheck_after_edit]`.
The planner converts those slugs into concrete command + exit_code entries
that get rendered into `.claude/settings.json` by the generator.

Language-aware: a hook slug expands to the right tool for the project's
languages (ruff for python, eslint for typescript/javascript, etc.).
When no language is detected the slug expands to a documented placeholder
the user can edit.

`exitCode = 2` blocks the tool call until the failure is addressed; this
matches the GEN-04 contract from REQUIREMENTS.md.
"""
from __future__ import annotations

from typing import TypedDict


class Hook(TypedDict):
    command: str
    exit_code: int


# Language → command for `lint_after_edit`. The first matching language wins.
_LINT_BY_LANGUAGE: dict[str, str] = {
    "python": "ruff check .",
    "typescript": "npx --no-install eslint .",
    "javascript": "npx --no-install eslint .",
    "rust": "cargo clippy --quiet",
    "go": "go vet ./...",
}

_TYPECHECK_BY_LANGUAGE: dict[str, str] = {
    "python": "mypy --strict .",
    "typescript": "npx --no-install tsc --noEmit",
    # JavaScript has no built-in typecheck — falls through to placeholder
    "rust": "cargo check --quiet",
    "go": "go vet ./...",
}

_PLACEHOLDER = (
    "echo 'configure this hook for your stack: see .claude/settings.json'"
)


def _resolve_command(table: dict[str, str], languages: list[str]) -> str:
    """Pick the first table entry matching one of the project's languages.

    Case-insensitive lookup so spec data like "TypeScript" or "Python"
    matches the table keys.
    """
    for lang in languages:
        cmd = table.get(lang.lower())
        if cmd:
            return cmd
    return _PLACEHOLDER


def resolve_hooks(slugs: list[str], languages: list[str]) -> list[Hook]:
    """Map profile.hook_templates slugs to concrete hook entries.

    Unknown slugs are skipped silently — adding a new slug to a profile
    without registering it here is a no-op rather than an error, so
    profile authors can stage YAML changes ahead of registry updates.
    """
    out: list[Hook] = []
    for slug in slugs:
        if slug == "lint_after_edit":
            out.append({
                "command": _resolve_command(_LINT_BY_LANGUAGE, languages),
                "exit_code": 2,
            })
        elif slug == "typecheck_after_edit":
            out.append({
                "command": _resolve_command(_TYPECHECK_BY_LANGUAGE, languages),
                "exit_code": 2,
            })
        # else: unknown slug — silently ignored for forward compatibility
    return out
