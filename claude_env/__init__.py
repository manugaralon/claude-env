"""claude-env: generate calibrated Claude Code environments."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _version


def get_version() -> str:
    """Return the installed package version, or 'dev' when running from source.

    Reads from package metadata so the version stays in sync with
    pyproject.toml without a hardcoded duplicate. Falls back to 'dev'
    when the package isn't installed (running tests via uv from a fresh
    checkout, etc.).
    """
    try:
        return _version("claude-env")
    except PackageNotFoundError:
        return "dev"


__version__ = get_version()
