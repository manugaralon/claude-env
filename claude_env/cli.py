"""CLI entrypoint — setup (global), bootstrap (per-project), version."""
from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Generate calibrated Claude Code environments.")
console = Console()

_TEMPLATES_DIR = Path(__file__).parent / "data"
_PROFILES_DIR = Path(__file__).parent / "profiles"

_SKILL_MD_CONTENT = """\
---
name: claude-env
description: >-
  Generate a complete .claude/ environment layer for the current project using claude-env.
  Use when bootstrapping a new project, re-running environment generation, or installing
  Claude Code conventions. Run with --dry-run to preview without writing files.
allowed-tools: Bash
---

# Claude Env Bootstrap

Generate the project's `.claude/` environment layer by running the claude-env CLI.

## Steps

1. Confirm `claude-env` is installed:

   ```bash
   claude-env version
   ```

2. Ask the user: "What is this project? Give me a one-line description."

3. Run bootstrap with the description (non-interactive, no LLM call needed
   if a spec file exists — use `--spec` instead of `--description` when one is present):

   Dry-run first to preview:

   ```bash
   claude-env bootstrap --description "DESCRIPTION" --dry-run
   ```

   Then write for real:

   ```bash
   claude-env bootstrap --description "DESCRIPTION"
   ```

   Or with a spec file (skips the LLM entirely):

   ```bash
   claude-env bootstrap --spec ./spec.yaml
   ```

4. Report which files were written and confirm the `.claude/` layer exists.

## Opt-in integration flags

Ask the user whether to enable any of these. None are required — only add flags
the user explicitly opts into.

- `--with-browser` — playwright MCP (browser automation) at project scope (writes `.mcp.json`)
- `--with-context7` — upstash/context7 MCP (live docs lookup) at project scope
- `--with-sequential-thinking` — sequential-thinking MCP at project scope
- `--with-claude-mem` — prints the install hint for the claude-mem plugin (it's a
  user-scoped plugin, not an MCP — no file is written)
- `--with-quality-gate-precommit` — emits `.claude/quality-gate-precommit` marker
  that opts the project into the global lint+secrets pre-commit hook

Combine flags freely:

```bash
claude-env bootstrap --spec ./spec.yaml --with-browser --with-context7 \\
    --with-quality-gate-precommit
```

## Notes

- Never run `claude-env bootstrap` without `--description` or `--spec` — it will
  block on an interactive prompt that cannot complete inside a Bash tool call.
- `--description` triggers an LLM call (requires ANTHROPIC_API_KEY). If the key
  is missing, fall back to `--spec` with a minimal YAML spec you generate yourself.
- The `--with-*` flags are independent and can be combined. Re-running bootstrap
  with different flags is safe — generation is idempotent.
"""


def _install_bootstrap_skill(global_root: Path) -> Path:
    """Write the claude-env SKILL.md to <global_root>/skills/claude-env/bootstrap/SKILL.md.

    Always overwrites. Returns the absolute path written.
    """
    target = global_root / "skills" / "claude-env" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_SKILL_MD_CONTENT, encoding="utf-8")
    return target


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo("claude-env 0.1.0")


def _build_global_profile() -> "DomainProfile":  # noqa: F821
    """Construct the kitchen-sink DomainProfile used by `claude-env setup`.

    Drives the global ~/.claude/ install — every skill in the catalogue
    plus every catalogued agent. Empty `detection_signals` keeps this
    profile out of project-level domain classification.
    """
    from claude_env.generator.content_catalogue import (
        known_agent_slugs,
        known_skill_slugs,
    )
    from claude_env.models.domain_profile import DomainProfile

    return DomainProfile(
        domain="global",
        display_name="Global Claude Conventions",
        description="Kitchen-sink install — every catalogued skill and agent for ~/.claude/",
        skill_slugs=known_skill_slugs(),
        agent_slugs=known_agent_slugs(),
        claude_md_sections=[
            "think_before_coding",
            "plan_execute_verify",
            "context_management",
            "lessons_loop",
            "delegate_prompting",
            "demand_elegance",
            "autonomous_bug_fixing",
            "core_principles",
        ],
        hook_templates=[],
        detection_signals=[],
    )


@app.command()
def setup() -> None:
    """Run global onboarding wizard — writes ~/.claude/ layer."""
    from claude_env.generator.generator import Generator
    from claude_env.models.project_spec import ProjectSpec
    from claude_env.pipeline.environment_planner import plan as make_plan
    from claude_env.templates.registry import TemplateRegistry

    console.print("[bold]claude-env setup[/bold]")
    user_name = typer.prompt("Your name")

    spec = ProjectSpec(
        name="global",
        description=f"Global Claude Code conventions for {user_name}",
    )
    registry = TemplateRegistry(_TEMPLATES_DIR.resolve())
    profile = _build_global_profile()
    generation_plan = make_plan(spec, profile, registry.list_templates())

    gen = Generator(registry)
    # Pitfall #4: project_root=Path.home() so PROJECT-layer → ~/.claude/
    written = gen.execute(
        generation_plan,
        project_root=Path.home(),
        global_root=Path.home() / ".claude",
    )

    skill_path = _install_bootstrap_skill(Path.home() / ".claude")

    console.print(
        f"[green]Setup complete.[/green] Wrote {len(written)} files + skill at {skill_path}."
    )
    console.print(
        f"  Installed {len(profile.skill_slugs)} skills, {len(profile.agent_slugs)} agents."
    )


@app.command()
def bootstrap(
    project_dir: Path = typer.Argument(
        Path("."), help="Project directory to bootstrap (default: current directory)"
    ),
    spec_file: Path | None = typer.Option(
        None, "--spec", "-s", help="Path to YAML or Markdown spec file (skips LLM)"
    ),
    description: str | None = typer.Option(
        None, "--description", "-d", help="One-line project description (skips interactive prompt)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print files that would be written without writing"
    ),
    with_browser: bool = typer.Option(
        False, "--with-browser", help="Add the playwright MCP server to .mcp.json"
    ),
    with_context7: bool = typer.Option(
        False, "--with-context7", help="Add the context7 MCP server to .mcp.json"
    ),
    with_sequential_thinking: bool = typer.Option(
        False, "--with-sequential-thinking",
        help="Add the sequential-thinking MCP server to .mcp.json"
    ),
    with_claude_mem: bool = typer.Option(
        False, "--with-claude-mem",
        help="Print install hint for the claude-mem plugin (plugin, not MCP — user-scoped)"
    ),
    with_quality_gate_precommit: bool = typer.Option(
        False, "--with-quality-gate-precommit",
        help=(
            "Emit .claude/quality-gate-precommit marker that opts this project "
            "into the global quality-gate-precommit hook (lint + secrets on git commit)"
        ),
    ),
) -> None:
    """Generate .claude/ layer for the given project directory."""
    from claude_env.generator.generator import Generator, resolve_plan_paths
    from claude_env.mcp_registry import resolve_plugin_hints
    from claude_env.pipeline.domain_classifier import classify, load_all_profiles
    from claude_env.pipeline.environment_planner import plan as make_plan
    from claude_env.pipeline.input_normalizer import InputNormalizer
    from claude_env.templates.registry import TemplateRegistry

    mcp_slugs: list[str] = []
    if with_browser:
        mcp_slugs.append("browser")
    if with_context7:
        mcp_slugs.append("context7")
    if with_sequential_thinking:
        mcp_slugs.append("sequential-thinking")
    plugin_slugs: list[str] = []
    if with_claude_mem:
        plugin_slugs.append("claude-mem")

    project_root = project_dir.resolve()
    global_root = Path.home() / ".claude"
    registry = TemplateRegistry(_TEMPLATES_DIR.resolve())

    try:
        if spec_file is not None:
            normalizer = InputNormalizer()
            spec = normalizer.from_spec_file(spec_file.resolve())
        elif description is not None:
            # Build ProjectSpec directly — no LLM call, no API key needed.
            from claude_env.models.project_spec import ProjectSpec
            spec = ProjectSpec(name=project_root.name or "project", description=description)
        else:
            desc = typer.prompt("Describe your project")
            normalizer = InputNormalizer()  # constructs anthropic.Anthropic() — needs key
            spec = normalizer.from_freeform(desc)
    except Exception as exc:
        msg = str(exc).lower()
        if "api_key" in msg or "authentication" in msg or "anthropic_api_key" in msg:
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY is not set.")
            console.print(
                "Set it with: [cyan]export ANTHROPIC_API_KEY=sk-...[/cyan], "
                "or pass [cyan]--spec path/to/spec.yaml[/cyan] to skip the LLM."
            )
            raise typer.Exit(1) from exc
        if isinstance(exc, ModuleNotFoundError) and "anthropic" in msg:
            console.print(
                "[red]Error:[/red] the anthropic SDK is not installed "
                "(needed for the freeform LLM path)."
            )
            console.print(
                "Install with [cyan]pip install anthropic[/cyan] and set "
                "[cyan]ANTHROPIC_API_KEY[/cyan], or pass "
                "[cyan]--spec path/to/spec.yaml[/cyan] to skip the LLM."
            )
            raise typer.Exit(1) from exc
        raise

    profiles = load_all_profiles(_PROFILES_DIR)
    profile = classify(spec, profiles)
    console.print(f"Domain detected: [cyan]{profile.domain}[/cyan]")

    generation_plan = make_plan(
        spec, profile, registry.list_templates(),
        mcp_slugs=mcp_slugs,
        with_quality_gate_precommit=with_quality_gate_precommit,
    )

    if dry_run:
        console.print("[yellow]Dry run — no files written[/yellow]")
        for path in resolve_plan_paths(generation_plan, project_root, global_root):
            console.print(f"  [dim]would write[/dim] {path}")
        for hint in resolve_plugin_hints(plugin_slugs):
            console.print(f"  [dim]plugin[/dim] {hint}")
        return

    gen = Generator(registry)
    written = gen.execute(
        generation_plan, project_root=project_root, global_root=global_root
    )
    for path in written:
        console.print(f"  [green]wrote[/green] {path}")
    for hint in resolve_plugin_hints(plugin_slugs):
        console.print(f"  [yellow]plugin →[/yellow] {hint}")
    console.print(f"[bold green]Done.[/bold green] {len(written)} files generated.")

    # QA-01: structural audit before the developer starts a session.
    from claude_env.auditor import audit as run_audit

    report = run_audit(project_root)
    if report.passed and not report.findings:
        console.print("[green]audit:[/green] PASS")
    else:
        verdict = "[green]PASS[/green]" if report.passed else "[red]FAIL[/red]"
        console.print(f"[bold]audit:[/bold] {verdict}")
        for finding in report.findings:
            color = "red" if finding.severity == "error" else "yellow"
            console.print(
                f"  [{color}]{finding.severity}[/{color}] "
                f"{finding.rule} [dim]{finding.file}[/dim]: {finding.message}"
            )
        if not report.passed:
            raise typer.Exit(1)


@app.command()
def audit(
    project_dir: Path = typer.Argument(
        Path("."), help="Project directory to audit (default: current directory)"
    ),
) -> None:
    """Audit a generated `.claude/` environment without re-running bootstrap.

    Returns exit code 0 on PASS, 1 on FAIL. Useful for pre-merge checks
    or for re-validating after manual edits to a generated environment.
    """
    from claude_env.auditor import audit as run_audit

    report = run_audit(project_dir.resolve())
    if not report.findings:
        console.print(f"[green]audit:[/green] PASS — {project_dir.resolve()}")
        return
    verdict = "[green]PASS[/green]" if report.passed else "[red]FAIL[/red]"
    console.print(f"[bold]audit:[/bold] {verdict} — {project_dir.resolve()}")
    for finding in report.findings:
        color = "red" if finding.severity == "error" else "yellow"
        console.print(
            f"  [{color}]{finding.severity}[/{color}] "
            f"{finding.rule} [dim]{finding.file}[/dim]: {finding.message}"
        )
    if not report.passed:
        raise typer.Exit(1)


@app.command()
def capture(
    url: str | None = typer.Option(None, "--url", "-u", help="Single URL to capture"),
    urls_file: Path | None = typer.Option(None, "--urls", help="File with one URL per line"),
    topic: str = typer.Option("general", "--topic", "-t", help="Tag for output files"),
    output: Path = typer.Option(Path("./notes"), "--output", "-o", help="Output directory"),
    language: str = typer.Option("es", "--language", "-l", help="Audio language: es, en, auto"),
) -> None:
    """Download an Instagram/video post and extract its content to a .md file."""
    import subprocess

    from groq import Groq

    from claude_env.capture import process_url

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        console.print("[red]Error:[/red] GROQ_API_KEY is not set.")
        raise typer.Exit(1)

    if subprocess.run(["ffmpeg", "-version"], capture_output=True).returncode != 0:
        console.print("[red]Error:[/red] ffmpeg not installed. Run: sudo apt-get install ffmpeg")
        raise typer.Exit(1)

    if url is None and urls_file is None:
        console.print("[red]Error:[/red] provide --url or --urls")
        raise typer.Exit(1)

    if url:
        urls = [url]
    else:
        assert urls_file is not None
        if not urls_file.exists():
            console.print(f"[red]Error:[/red] {urls_file} not found")
            raise typer.Exit(1)
        urls = [u.strip() for u in urls_file.read_text().splitlines() if u.strip() and not u.startswith("#")]

    output.mkdir(parents=True, exist_ok=True)
    client = Groq(api_key=groq_key)

    console.print(f"Capturing {len(urls)} URL(s) → [cyan]{output}[/cyan] [topic: {topic}]")
    success, failed = 0, 0
    for u in urls:
        if process_url(u, topic, output, client, language):
            success += 1
        else:
            failed += 1

    console.print(f"\n[bold]Done.[/bold] {success} OK, {failed} failed. Files in: {output.resolve()}")


@app.command()
def analyze(
    target: Path = typer.Argument(Path("./notes"), help="Directory or single .md file to analyze"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-analyze already analyzed files"),
) -> None:
    """Evaluate captured notes for ideas applicable to claude-env."""
    import anthropic as _anthropic

    from claude_env.analyzer import analyze_file

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        console.print("[red]Error:[/red] ANTHROPIC_API_KEY is not set.")
        raise typer.Exit(1)

    client = _anthropic.Anthropic(api_key=api_key)

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("*.md"))
    else:
        console.print(f"[red]Error:[/red] {target} not found")
        raise typer.Exit(1)

    if not files:
        console.print(f"No .md files found in {target}")
        raise typer.Exit(0)

    analyzed, skipped = 0, 0
    for f in files:
        if analyze_file(f, client, force=force):
            console.print(f"  [green]analyzed[/green] {f.name}")
            analyzed += 1
        else:
            console.print(f"  [dim]skipped[/dim] {f.name} (already analyzed, use --force to redo)")
            skipped += 1

    console.print(f"\n[bold]Done.[/bold] {analyzed} analyzed, {skipped} skipped.")


if __name__ == "__main__":
    app()
