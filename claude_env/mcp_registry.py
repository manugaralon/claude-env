"""Registry of well-known MCP servers exposed via `claude-env bootstrap` flags.

Each entry maps a CLI-friendly slug to the stdio command the corresponding
`.mcp.json` entry needs. Project-scoped MCPs are written to a `.mcp.json`
file at the project root — this is the format Claude Code reads for
project-level MCP servers.

Plugins (e.g. claude-mem) are NOT registered here because they use the
Claude Code plugin manager, not the MCP protocol. The CLI surfaces these
as guidance text instead of writing them to disk.
"""
from __future__ import annotations

from typing import TypedDict


class McpServer(TypedDict):
    name: str
    command: str
    args: list[str]


# Slug → (server_name_in_mcp_json, command, args).
# Slugs are the user-facing flag names (--with-<slug>).
MCP_REGISTRY: dict[str, McpServer] = {
    "browser": {
        "name": "playwright",
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
    },
    "context7": {
        "name": "context7",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp@latest"],
    },
    "sequential-thinking": {
        "name": "sequential-thinking",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
    },
}

# Plugins are user-scoped via `claude plugin install`, not project-scoped via
# `.mcp.json`. The CLI prints a one-line install hint when these flags are set.
PLUGIN_HINTS: dict[str, str] = {
    "claude-mem": "Install the claude-mem plugin: claude plugin install claude-mem@thedotmack",
}


def resolve_mcp_servers(slugs: list[str]) -> list[McpServer]:
    """Return the McpServer entries for `slugs` (skips unknown slugs).

    Order is preserved from the input list so the .mcp.json output is
    deterministic for a given flag combination.
    """
    return [MCP_REGISTRY[s] for s in slugs if s in MCP_REGISTRY]


def resolve_plugin_hints(slugs: list[str]) -> list[str]:
    """Return install-hint strings for plugin slugs (claude-mem, etc.)."""
    return [PLUGIN_HINTS[s] for s in slugs if s in PLUGIN_HINTS]
