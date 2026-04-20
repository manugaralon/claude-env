"""CLI entrypoint — setup (global), bootstrap (per-project), version."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Generate calibrated Claude Code environments.")
console = Console()

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_PROFILES_DIR = Path(__file__).parent / "profiles"


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo("claude-env 0.1.0")


@app.command()
def setup() -> None:
    """Run global onboarding wizard — writes ~/.claude/ layer."""
    from claude_env.generator.generator import Generator
    from claude_env.models.project_spec import ProjectSpec
    from claude_env.pipeline.domain_classifier import load_all_profiles
    from claude_env.pipeline.environment_planner import plan as make_plan
    from claude_env.templates.registry import TemplateRegistry

    console.print("[bold]claude-env setup[/bold]")
    user_name = typer.prompt("Your name")

    spec = ProjectSpec(
        name="global",
        description=f"Global Claude Code conventions for {user_name}",
    )
    registry = TemplateRegistry(_TEMPLATES_DIR.resolve())
    profiles = load_all_profiles(_PROFILES_DIR)
    general = next(p for p in profiles if p.domain == "general")
    generation_plan = make_plan(spec, general, registry.list_templates())

    gen = Generator(registry)
    # Pitfall #4: project_root=Path.home() so PROJECT-layer → ~/.claude/
    written = gen.execute(
        generation_plan,
        project_root=Path.home(),
        global_root=Path.home() / ".claude",
    )

    # HOOK: Plan 04-02 will install the claude-env SKILL.md here.

    console.print(f"[green]Setup complete.[/green] Wrote {len(written)} files.")


@app.command()
def bootstrap(
    project_dir: Path = typer.Argument(
        Path("."), help="Project directory to bootstrap (default: current directory)"
    ),
    spec_file: Path | None = typer.Option(
        None, "--spec", "-s", help="Path to YAML or Markdown spec file (skips LLM)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print files that would be written without writing"
    ),
) -> None:
    """Generate .claude/ layer for the given project directory."""
    from claude_env.generator.generator import Generator, resolve_plan_paths
    from claude_env.pipeline.domain_classifier import classify, load_all_profiles
    from claude_env.pipeline.environment_planner import plan as make_plan
    from claude_env.pipeline.input_normalizer import InputNormalizer
    from claude_env.templates.registry import TemplateRegistry

    project_root = project_dir.resolve()
    global_root = Path.home() / ".claude"
    registry = TemplateRegistry(_TEMPLATES_DIR.resolve())

    try:
        if spec_file is not None:
            normalizer = InputNormalizer()
            spec = normalizer.from_spec_file(spec_file.resolve())
        else:
            description = typer.prompt("Describe your project")
            normalizer = InputNormalizer()  # constructs anthropic.Anthropic() — needs key
            spec = normalizer.from_freeform(description)
    except Exception as exc:
        msg = str(exc).lower()
        if "api_key" in msg or "authentication" in msg or "anthropic_api_key" in msg:
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY is not set.")
            console.print(
                "Set it with: [cyan]export ANTHROPIC_API_KEY=sk-...[/cyan], "
                "or pass [cyan]--spec path/to/spec.yaml[/cyan] to skip the LLM."
            )
            raise typer.Exit(1) from exc
        raise

    profiles = load_all_profiles(_PROFILES_DIR)
    profile = classify(spec, profiles)
    console.print(f"Domain detected: [cyan]{profile.domain}[/cyan]")

    generation_plan = make_plan(spec, profile, registry.list_templates())

    if dry_run:
        console.print("[yellow]Dry run — no files written[/yellow]")
        for path in resolve_plan_paths(generation_plan, project_root, global_root):
            console.print(f"  [dim]would write[/dim] {path}")
        return

    gen = Generator(registry)
    written = gen.execute(
        generation_plan, project_root=project_root, global_root=global_root
    )
    for path in written:
        console.print(f"  [green]wrote[/green] {path}")
    console.print(f"[bold green]Done.[/bold green] {len(written)} files generated.")


if __name__ == "__main__":
    app()
