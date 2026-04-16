"""CLI entrypoint (stub — extended in Phase 4)."""
from __future__ import annotations

import typer

app = typer.Typer(help="Generate calibrated Claude Code environments.")


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo("claude-env 0.1.0")


if __name__ == "__main__":
    app()
