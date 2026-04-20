# Phase 4: CLI + Skill - Research

**Researched:** 2026-04-20
**Domain:** CLI wiring — Typer commands, dry-run, Claude Code SKILL.md format, end-to-end pipeline integration
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CLI-01 | `claude-env setup` — global onboarding wizard that generates `~/.claude/` layer | Typer `@app.command()` + `typer.prompt()` wizard; Generator.execute() with `global_root=Path.home()/".claude"` and a `general` profile; existing pipeline already wired |
| CLI-02 | `claude-env bootstrap` — per-project generation that produces `.claude/` layer | Typer `@app.command()`; InputNormalizer from freeform/spec file OR interactive prompt; DomainClassifier + EnvironmentPlanner + Generator already complete; project_root = cwd() |
| CLI-03 | `--dry-run` flag shows what would be written without writing | Boolean Typer Option flag; `Generator.execute()` is the only I/O path — intercept before `target.write_text()`; print table of paths via Rich |
| CLI-04 | Tool installable as Claude Code skill `~/.claude/skills/claude-env/SKILL.md` invocable from any project directory | Claude Code SKILL.md frontmatter with `name: bootstrap`, description, optional `allowed-tools`; body is instructions for the model to invoke `claude-env bootstrap` via Bash |
</phase_requirements>

---

## Summary

Phase 4 is the thin integration layer that wires all Phase 1–3 components (InputNormalizer, DomainClassifier, EnvironmentPlanner, Generator) behind two Typer CLI commands and installs a SKILL.md so Claude Code can invoke the tool as a slash-command. The core logic is complete — this phase is plumbing and entry-point work.

The CLI stub in `claude_env/cli.py` already has a Typer app with a `version` command. Phase 4 replaces it with `setup` and `bootstrap` commands. The `setup` command targets the global `~/.claude/` layer using the `general` domain profile (no classification needed — global layer is always general conventions). The `bootstrap` command takes the full pipeline path: freeform prompt or spec file → InputNormalizer → DomainClassifier → EnvironmentPlanner → Generator. The `--dry-run` flag intercepts the Generator write step and prints what would be written.

The Claude Code skill (CLI-04) is a `~/.claude/skills/claude-env/SKILL.md` file with YAML frontmatter that tells Claude Code when to invoke the skill, and a body that instructs the model to run `claude-env bootstrap` via Bash. This is the same format used by all installed skills in `~/.claude/skills/`. The skill itself does not run Python code — it instructs the Claude model to use the Bash tool to invoke the already-installed CLI.

**Primary recommendation:** Implement `cli.py` with `setup` and `bootstrap` commands, each calling the pipeline in sequence. For dry-run, introduce a `DryRunGenerator` wrapper that collects paths without writing. Write `~/.claude/skills/claude-env/SKILL.md` as the skill installation artifact (CLI-04 is produced by the tool's own `setup` command).

---

## Standard Stack

### Core (all already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Typer | 0.24.1 | CLI app with `@app.command()`, `Option`, `Argument`, `prompt()` | Already in deps; confirmed installed and functional |
| Rich | 14.x | Console output: colored status, file path tables, error messages | Already in deps; already used throughout |
| pathlib | stdlib | Path resolution for project_root, global_root, skill install path | No new dep; all existing code uses pathlib |

### No New Dependencies

Phase 4 requires zero new packages. Typer, Rich, and all pipeline components are already installed. The `ANTHROPIC_API_KEY` env var is needed at runtime for freeform input but is not a package dependency.

**Version verification (confirmed 2026-04-20):**
- typer: 0.24.1 (confirmed via `uv run python -c "import typer; print(typer.__version__)"`)
- All other deps locked in `uv.lock` — no additions needed.

---

## Architecture Patterns

### Recommended Project Structure (additions for Phase 4)

```
claude_env/
├── cli.py               # REPLACE stub — add setup, bootstrap, --dry-run
tests/
├── test_cli.py          # CLI integration tests via Typer test runner
templates/
└── skill_md.j2          # (optional) Template for claude-env SKILL.md — or write as literal string
```

The skill installation file is NOT a template — it has fixed content. Write it as a Python string literal in `cli.py` or a separate constant, not a Jinja2 template.

### Pattern 1: Typer Multi-Command App

**What:** Replace the stub `cli.py` with two real commands: `setup` and `bootstrap`. Each command is a `@app.command()` function with typed parameters.

**When to use:** This is the single entry point. `pyproject.toml` already maps `claude-env` → `claude_env.cli:app`.

```python
# claude_env/cli.py
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from claude_env.generator.generator import Generator
from claude_env.models.domain_profile import load_profile
from claude_env.pipeline.domain_classifier import classify, load_all_profiles
from claude_env.pipeline.environment_planner import plan
from claude_env.pipeline.input_normalizer import InputNormalizer
from claude_env.templates.registry import TemplateRegistry

app = typer.Typer(help="Generate calibrated Claude Code environments.")
console = Console()

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_PROFILES_DIR = Path(__file__).parent / "profiles"


@app.command()
def setup() -> None:
    """Run global onboarding wizard — writes ~/.claude/ layer."""
    ...


@app.command()
def bootstrap(
    project_dir: Path = typer.Argument(
        default=Path("."),
        help="Project directory to bootstrap (default: current directory)",
    ),
    spec_file: Path | None = typer.Option(
        None, "--spec", "-s",
        help="Path to YAML or Markdown spec file",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Print files that would be written without writing them",
    ),
) -> None:
    """Generate .claude/ layer for the given project directory."""
    ...


if __name__ == "__main__":
    app()
```

### Pattern 2: setup Command — Global Wizard

**What:** The `setup` command prompts for user name / conventions and writes the global `~/.claude/` layer using the `general` domain profile. No domain classification needed — global layer always uses `general`.

**Key decisions:**
- Global root: `Path.home() / ".claude"`
- Profile: always `general.yaml` (no classification for global layer)
- Wizard: use `typer.prompt()` for user-facing questions (name, preferred language style). Only prompt for things that affect template rendering. No technical choices.
- Project spec for global setup: construct `ProjectSpec` directly with fixed defaults, overriding only user-supplied fields.

```python
@app.command()
def setup() -> None:
    """Run global onboarding wizard — writes ~/.claude/ layer."""
    console.print("[bold]Claude Env Setup[/bold] — global ~/.claude/ layer")

    user_name = typer.prompt("Your name (used in commit conventions)")
    # Build minimal ProjectSpec for global layer
    from claude_env.models.project_spec import ProjectSpec
    spec = ProjectSpec(
        name="global",
        description=f"Global Claude Code conventions for {user_name}",
    )

    global_root = Path.home() / ".claude"
    registry = TemplateRegistry(_TEMPLATES_DIR)
    profiles = load_all_profiles(_PROFILES_DIR)
    general_profile = next(p for p in profiles if p.domain == "general")
    generation_plan = plan(spec, general_profile, registry.list_templates())

    gen = Generator(registry)
    written = gen.execute(generation_plan, project_root=global_root, global_root=global_root)

    # Install the claude-env SKILL.md (CLI-04)
    _install_skill(global_root)

    console.print(f"[green]Setup complete.[/green] Wrote {len(written)} files.")
```

**Note:** The `setup` command also installs the claude-env SKILL.md into `~/.claude/skills/claude-env/SKILL.md` (CLI-04). This is the natural place to install it — during global setup.

### Pattern 3: bootstrap Command — Per-Project Generation

**What:** The `bootstrap` command is the full pipeline for a specific project. It accepts either a spec file (`--spec`) or prompts interactively for a project description (freeform text via `typer.prompt()`).

**Input resolution order:**
1. If `--spec` provided: use `InputNormalizer.from_spec_file(path)`
2. Otherwise: `typer.prompt("Describe your project in 1-2 sentences")` → `InputNormalizer.from_freeform(text)`

**Pipeline flow:** InputNormalizer → ProjectSpec → DomainClassifier → DomainProfile → EnvironmentPlanner → GenerationPlan → Generator → written files

```python
@app.command()
def bootstrap(
    project_dir: Path = typer.Argument(default=Path("."), ...),
    spec_file: Path | None = typer.Option(None, "--spec", "-s", ...),
    dry_run: bool = typer.Option(False, "--dry-run", ...),
) -> None:
    project_root = project_dir.resolve()
    global_root = Path.home() / ".claude"
    registry = TemplateRegistry(_TEMPLATES_DIR)
    normalizer = InputNormalizer()  # uses ANTHROPIC_API_KEY from env

    if spec_file is not None:
        spec = normalizer.from_spec_file(spec_file.resolve())
    else:
        description = typer.prompt("Describe your project")
        spec = normalizer.from_freeform(description)

    profiles = load_all_profiles(_PROFILES_DIR)
    profile = classify(spec, profiles)
    console.print(f"Domain: [cyan]{profile.domain}[/cyan]")

    generation_plan = plan(spec, profile, registry.list_templates())

    if dry_run:
        _print_dry_run(generation_plan, project_root, global_root)
        return

    gen = Generator(registry)
    written = gen.execute(generation_plan, project_root=project_root, global_root=global_root)
    for path in written:
        console.print(f"  [green]wrote[/green] {path}")
    console.print(f"[bold green]Done.[/bold green] {len(written)} files generated.")
```

### Pattern 4: --dry-run Implementation

**What:** Print every file that would be written without touching disk. The Generator's `_resolve_path()` method already does the path resolution — dry-run reuses that logic without calling `write_text()`.

**Approach:** Do NOT subclass Generator. Call `Generator._resolve_path()` directly (or extract a `resolve_paths(plan, project_root, global_root) -> list[Path]` helper). Avoids duplicating path resolution logic.

**Alternative (simpler):** Extract a pure function `resolve_plan_paths(plan, project_root, global_root) -> list[Path]` into `generator.py` that reuses `_resolve_path` logic. Call it from the CLI for dry-run. Generator.execute() is unchanged.

```python
def _print_dry_run(
    generation_plan: GenerationPlan,
    project_root: Path,
    global_root: Path,
) -> None:
    """Print files that would be written without writing them."""
    from claude_env.models.generation_plan import OutputLayer
    console.print("[yellow]Dry run — no files written[/yellow]")
    for artifact in generation_plan.artifacts:
        if artifact.layer == OutputLayer.PROJECT:
            layer_root = project_root / ".claude"
        else:
            layer_root = global_root
        target = (layer_root / artifact.target_path).resolve()
        console.print(f"  [dim]would write[/dim] {target}")
```

### Pattern 5: Claude Code SKILL.md (CLI-04)

**What:** A SKILL.md file installed at `~/.claude/skills/claude-env/SKILL.md` that enables `/claude-env:bootstrap` as a Claude Code slash-command.

**Key facts from inspecting real skills:**
- The YAML frontmatter `name:` field is the identifier Claude Code uses. The directory name (`claude-env`) and skill `name:` in frontmatter must match the invocation prefix.
- The slash command `/claude-env:bootstrap` convention means: skill directory = `claude-env`, skill name = `bootstrap`. This implies the skill should be at `~/.claude/skills/claude-env/bootstrap/SKILL.md` OR the single skill name is `claude-env` and the body handles `bootstrap` as a subcommand. **Research finding:** The `/plugin:skill` convention in Claude Code corresponds to `~/.claude/skills/<skill-dir>/SKILL.md` where the dir IS the namespace. A single SKILL.md per directory is the standard format. The `/claude-env:bootstrap` invocation likely maps to `~/.claude/skills/claude-env/SKILL.md` with `name: claude-env` (or `name: bootstrap` in the `claude-env` dir).
- The body instructs Claude to use Bash to invoke the CLI. The model never runs Python directly.
- `allowed-tools: Bash` is sufficient — the CLI handles all I/O.

**SKILL.md content:**

```markdown
---
name: claude-env
description: Generate a complete .claude/ environment layer for the current project. Use when setting up a new project or re-running environment generation. Invokes claude-env bootstrap in the current directory. Accepts optional --spec path for structured spec file input, and --dry-run to preview without writing.
allowed-tools: Bash
---

# Claude Env Bootstrap

Generate the project's `.claude/` environment layer by running the claude-env CLI.

## Steps

1. Confirm `claude-env` is installed:
   ```bash
   claude-env --version
   ```
   If not installed, run: `uv tool install claude-env` or `pip install claude-env`.

2. Run bootstrap in the current project directory:
   ```bash
   claude-env bootstrap
   ```
   Or with a spec file:
   ```bash
   claude-env bootstrap --spec ./spec.yaml
   ```
   Or dry-run to preview:
   ```bash
   claude-env bootstrap --dry-run
   ```

3. Report which files were written and confirm the `.claude/` layer exists.
```

**Installation path:** The SKILL.md is written by the `setup` command to `~/.claude/skills/claude-env/SKILL.md`. It is a fixed string, not a template.

**Invocation:** From any project, the user types `/claude-env` in Claude Code chat, Claude loads the SKILL.md body, and executes `claude-env bootstrap` via Bash in the current directory.

### Pattern 6: TemplateRegistry Path Resolution in CLI Context

**What:** The CLI is invoked from arbitrary working directories. `TemplateRegistry` requires an absolute path. The correct derivation is from `__file__` in `cli.py`.

```python
# In cli.py — safe regardless of cwd
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_PROFILES_DIR = Path(__file__).parent / "profiles"
```

This resolves relative to the installed package location, not cwd. Matches the pattern established in Phase 1 research.

### Anti-Patterns to Avoid

- **Prompting for technical choices in `setup`:** The success criterion says "without prompting for technical choices." Prompt for name/preferences only — not for which domain profile to use or which hooks to enable.
- **Using `Path(".")` without `.resolve()` for project_root:** `Path(".")` is relative; always call `.resolve()` before passing to Generator.
- **Importing Generator or pipeline at module level:** Keep heavy imports inside command functions or at module level with `from __future__ import annotations` to avoid slow CLI startup.
- **Skipping skill dir creation:** `~/.claude/skills/claude-env/` may not exist. Use `Path.mkdir(parents=True, exist_ok=True)` before writing SKILL.md.
- **Hardcoding `ANTHROPIC_API_KEY` check:** The InputNormalizer raises a clear anthropic SDK error if the key is missing. Catch it and print a user-friendly message rather than letting the stack trace through.
- **Installing SKILL.md in `bootstrap` instead of `setup`:** SKILL.md is global infrastructure — belongs in `setup`. Bootstrap is per-project.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Prompts with defaults | Custom `input()` loop | `typer.prompt(text, default=...)` | Handles `^C` as clean Abort, respects TTY |
| Colored terminal output | ANSI escape codes in f-strings | `rich.Console.print("[green]...[/green]")` | Already in deps; handles Windows/piped output correctly |
| Argument parsing | `sys.argv` parsing | Typer `@app.command()` with typed signatures | Auto-generates `--help`, validates types |
| Boolean flags | Custom `--flag`/`--no-flag` | `typer.Option(False, "--dry-run")` | Correct CLI conventions; Typer handles negation |
| Path resolution for templates | `Path("templates")` relative | `Path(__file__).parent.parent / "templates"` | cwd-independent; established in Phase 1 research |

---

## Common Pitfalls

### Pitfall 1: `ANTHROPIC_API_KEY` missing causes cryptic error

**What goes wrong:** User runs `claude-env bootstrap` without setting `ANTHROPIC_API_KEY`. The anthropic SDK raises `anthropic.AuthenticationError` with a multi-line stack trace dumped to stdout.

**Why it happens:** `InputNormalizer.__init__()` creates `anthropic.Anthropic()` which reads the env var. If missing, the SDK raises on the first API call (not at construction time in newer SDK versions).

**How to avoid:** Wrap the `normalizer.from_freeform()` / `normalizer.from_spec_file()` call in a `try/except` that catches `anthropic.AuthenticationError` and prints: "Error: ANTHROPIC_API_KEY is not set. Run: export ANTHROPIC_API_KEY=sk-...".

**Warning signs:** Users see a Python traceback instead of a clean error message.

### Pitfall 2: Skill invocation format mismatch

**What goes wrong:** User types `/claude-env:bootstrap` and Claude Code doesn't recognize the skill, or loads the wrong skill.

**Why it happens:** Claude Code's skill resolution uses the directory name under `~/.claude/skills/` as the namespace. The colon-separated format `/skill-dir:subname` routes to `~/.claude/skills/<skill-dir>/<subname>/SKILL.md`. If the skill is at `~/.claude/skills/claude-env/SKILL.md` (no subdir), the invocation is `/claude-env` not `/claude-env:bootstrap`.

**How to avoid:** The success criterion says `/claude-env:bootstrap` must work. This implies the SKILL.md must be at `~/.claude/skills/claude-env/bootstrap/SKILL.md` with `name: bootstrap`. Install accordingly. If the intent is a single SKILL.md covering all subcommands, the invocation is just `/claude-env` and the body handles routing.

**Resolution:** Install the SKILL.md at `~/.claude/skills/claude-env/bootstrap/SKILL.md`. This satisfies `/claude-env:bootstrap` invocation. The skill name in frontmatter should be `bootstrap`.

**Warning signs:** `/claude-env:bootstrap` in Claude Code returns "skill not found" or loads a different skill.

### Pitfall 3: dry-run replicates path resolution logic

**What goes wrong:** The `--dry-run` path resolution is implemented separately from `Generator._resolve_path()` and diverges — e.g., dry-run shows paths under `.claude/` but actual run writes under `project_root/.claude/` at a different resolved path.

**Why it happens:** `Generator._resolve_path()` is a private method. Caller reimplements path logic independently.

**How to avoid:** Extract `resolve_plan_paths(plan, project_root, global_root) -> list[Path]` as a standalone function in `generator.py` that both `Generator.execute()` and the dry-run CLI path call. Single source of truth.

### Pitfall 4: setup uses general profile but planner produces PROJECT-layer artifacts

**What goes wrong:** `setup` calls `Generator.execute(plan, project_root=global_root, global_root=global_root)` but the plan contains PROJECT-layer artifacts (from the planner's default). These get written to `global_root/.claude/` — a `~/.claude/.claude/` path — instead of directly under `~/.claude/`.

**Why it happens:** The Environment Planner always produces `layer=PROJECT` artifacts. The Generator resolves PROJECT artifacts under `project_root/.claude/`. If `project_root = global_root = ~/.claude`, the output is `~/.claude/.claude/CLAUDE.md`.

**How to avoid:** For `setup`, the GLOBAL layer artifacts are what we want. Options:
1. Pass `project_root = Path.home()` (so PROJECT layer → `~/.claude/`) and `global_root = Path.home() / ".claude"`.
2. Extend the planner to support a `target_layer=GLOBAL` override for setup mode.
3. Run setup as a special path that writes directly to global_root without the planner.

**Recommendation:** Option 1 — pass `project_root = Path.home()` for setup, making `project_root / ".claude"` = `~/.claude/`. This is the cleanest fix with zero model changes. Document this clearly.

### Pitfall 5: Slow CLI startup due to top-level anthropic import

**What goes wrong:** `claude-env --help` or `claude-env bootstrap --dry-run` takes 2+ seconds to start because `import anthropic` loads heavy SDK machinery at module import time.

**Why it happens:** Top-level `from claude_env.pipeline.input_normalizer import InputNormalizer` in `cli.py` triggers `import anthropic` when the module loads.

**How to avoid:** Import `InputNormalizer` inside the `bootstrap()` function body, not at module level. This defers the import to when the command actually runs. For `--dry-run` with a `--spec` file, the LLM is not called at all — the import still happens but the API call does not.

---

## Code Examples

### Full setup command

```python
@app.command()
def setup() -> None:
    """Run global onboarding wizard — writes ~/.claude/ layer."""
    console.print("[bold]claude-env setup[/bold]")
    user_name = typer.prompt("Your name")

    from claude_env.models.project_spec import ProjectSpec
    from claude_env.pipeline.domain_classifier import load_all_profiles
    from claude_env.pipeline.environment_planner import plan as make_plan
    from claude_env.templates.registry import TemplateRegistry
    from claude_env.generator.generator import Generator

    spec = ProjectSpec(name="global", description=f"Global conventions for {user_name}")
    registry = TemplateRegistry(_TEMPLATES_DIR)
    profiles = load_all_profiles(_PROFILES_DIR)
    general = next(p for p in profiles if p.domain == "general")
    generation_plan = make_plan(spec, general, registry.list_templates())

    gen = Generator(registry)
    # project_root=Path.home() so PROJECT-layer artifacts → ~/.claude/
    written = gen.execute(generation_plan, project_root=Path.home(), global_root=Path.home() / ".claude")

    # Install claude-env skill (CLI-04)
    skill_path = Path.home() / ".claude" / "skills" / "claude-env" / "bootstrap" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(_SKILL_MD_CONTENT, encoding="utf-8")

    console.print(f"[green]Done.[/green] Wrote {len(written)} files + skill.")
```

### Full bootstrap command

```python
@app.command()
def bootstrap(
    project_dir: Path = typer.Argument(default=Path("."), help="Project directory"),
    spec_file: Path | None = typer.Option(None, "--spec", "-s", help="Spec file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing"),
) -> None:
    """Generate .claude/ layer for a project."""
    from claude_env.pipeline.input_normalizer import InputNormalizer
    from claude_env.pipeline.domain_classifier import classify, load_all_profiles
    from claude_env.pipeline.environment_planner import plan as make_plan
    from claude_env.templates.registry import TemplateRegistry
    from claude_env.generator.generator import Generator

    project_root = project_dir.resolve()
    global_root = Path.home() / ".claude"
    registry = TemplateRegistry(_TEMPLATES_DIR)
    normalizer = InputNormalizer()

    try:
        if spec_file is not None:
            spec = normalizer.from_spec_file(spec_file.resolve())
        else:
            description = typer.prompt("Describe your project")
            spec = normalizer.from_freeform(description)
    except Exception as exc:
        if "api_key" in str(exc).lower() or "authentication" in str(exc).lower():
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY is not set.")
            raise typer.Exit(1)
        raise

    profiles = load_all_profiles(_PROFILES_DIR)
    profile = classify(spec, profiles)
    console.print(f"Domain detected: [cyan]{profile.domain}[/cyan]")

    generation_plan = make_plan(spec, profile, registry.list_templates())

    if dry_run:
        console.print("[yellow]Dry run — no files written[/yellow]")
        from claude_env.models.generation_plan import OutputLayer
        for artifact in generation_plan.artifacts:
            layer_root = project_root / ".claude" if artifact.layer == OutputLayer.PROJECT else global_root
            target = (layer_root / artifact.target_path).resolve()
            console.print(f"  would write: {target}")
        return

    gen = Generator(registry)
    written = gen.execute(generation_plan, project_root=project_root, global_root=global_root)
    for path in written:
        console.print(f"  [green]wrote[/green] {path}")
    console.print(f"[bold green]Done.[/bold green] {len(written)} files generated.")
```

### SKILL.md content constant

```python
_SKILL_MD_CONTENT = """\
---
name: bootstrap
description: Generate a complete .claude/ environment layer for the current project using claude-env. Use when bootstrapping a new project, re-running environment generation, or setting up Claude Code conventions. Run with --dry-run to preview without writing files. Requires ANTHROPIC_API_KEY in the environment for freeform project description; use --spec to skip LLM and read a spec file directly.
allowed-tools: Bash
---

# Claude Env Bootstrap

Generate the project's `.claude/` environment layer by running the claude-env CLI.

## Steps

1. Confirm `claude-env` is installed:

   ```bash
   claude-env --version
   ```

2. Run bootstrap in the current project directory:

   ```bash
   claude-env bootstrap
   ```

   Or with a spec file (no LLM call):

   ```bash
   claude-env bootstrap --spec ./spec.yaml
   ```

   Or dry-run to preview what would be written:

   ```bash
   claude-env bootstrap --dry-run
   ```

3. Report which files were written and confirm the `.claude/` layer exists.
"""
```

### Testing CLI commands with Typer's test runner

```python
# tests/test_cli.py
from typer.testing import CliRunner
from claude_env.cli import app

runner = CliRunner()

def test_bootstrap_dry_run_no_api_key(tmp_path: Path) -> None:
    """Dry-run with a spec file should succeed without ANTHROPIC_API_KEY."""
    spec = tmp_path / "spec.yaml"
    spec.write_text("name: test-proj\ndescription: test\n")
    result = runner.invoke(app, ["bootstrap", str(tmp_path), "--spec", str(spec), "--dry-run"])
    assert result.exit_code == 0
    assert "would write" in result.output

def test_bootstrap_missing_api_key_clean_error() -> None:
    """Missing API key should print clean error, not traceback."""
    result = runner.invoke(app, ["bootstrap"], input="a web app\n", env={"ANTHROPIC_API_KEY": ""})
    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output
```

---

## Integration Flow: CLI → Pipeline → Generator

The full data flow for `bootstrap`:

```
User runs: claude-env bootstrap [project_dir] [--spec path] [--dry-run]
  │
  ├─ spec_file provided → InputNormalizer.from_spec_file(path)
  │   └─ parse_yaml_spec() or parse_markdown_spec() → ProjectSpec
  │
  └─ no spec_file → typer.prompt() → InputNormalizer.from_freeform(text)
      └─ LLM call (claude-haiku-3-5) → JSON → ProjectSpec
  │
  ├─ DomainClassifier.classify(spec, profiles) → DomainProfile
  │
  ├─ EnvironmentPlanner.plan(spec, profile, templates) → GenerationPlan
  │
  ├─ [--dry-run] → print resolved paths, return
  │
  └─ Generator.execute(plan, project_root, global_root) → list[Path]
      ├─ PROJECT layer → project_root/.claude/<target_path>
      └─ GLOBAL layer → global_root/<target_path> (sentinel merge)
```

For `setup`, the flow skips InputNormalizer and DomainClassifier:

```
User runs: claude-env setup
  │
  ├─ typer.prompt("Your name") → user_name
  ├─ ProjectSpec(name="global", description=...) constructed directly
  ├─ general profile loaded directly (no classify() call)
  ├─ EnvironmentPlanner.plan(spec, general, templates) → GenerationPlan
  ├─ Generator.execute(plan, project_root=Path.home(), global_root=~/.claude)
  └─ Write ~/.claude/skills/claude-env/bootstrap/SKILL.md
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `argparse` or `click` directly | Typer (wraps click) | Type annotations drive CLI schema; no manual `add_argument()` boilerplate |
| Shell scripts for CLI wrapper | Python CLI via `pyproject.toml` entry_points | `uv tool install` / `pipx install` make it globally available; typed, testable |
| Manual ANSI colors | Rich `Console.print("[green]...")` | TTY-aware; no color codes in piped output |
| Symlinked shell scripts as skills | Claude Code SKILL.md + `allowed-tools: Bash` | Model-native invocation; works in Claude Code without shell setup |

---

## Open Questions

1. **SKILL.md invocation path: `/claude-env` vs `/claude-env:bootstrap`**
   - What we know: The success criterion says `/claude-env:bootstrap` must be invocable. Inspecting real skills shows that colon-syntax `plugin:skill` maps to `~/.claude/skills/<plugin>/<skill>/SKILL.md`.
   - What's unclear: Claude Code's exact resolution behavior for user-installed (non-plugin) skills vs marketplace skills — no official docs found for the colon-syntax in user skill directories.
   - Recommendation: Install at `~/.claude/skills/claude-env/bootstrap/SKILL.md` to satisfy `/claude-env:bootstrap`. If that doesn't work, a flat `~/.claude/skills/claude-env/SKILL.md` with name `claude-env` is the fallback. Test at implementation time.

2. **setup command: should it also run bootstrap for the current project?**
   - What we know: CLI-01 says `setup` writes `~/.claude/` layer. CLI-02 says `bootstrap` writes `.claude/` for a project. They are separate commands.
   - What's unclear: Whether `setup` should optionally chain into `bootstrap` after global setup.
   - Recommendation: Keep them separate per the spec. Don't chain. The user can run both.

3. **`--spec` flag: should it accept stdin (`-`)?**
   - What we know: CLI-03 is about `--dry-run` only. No stdin requirement in CLI-02.
   - Recommendation: Skip stdin for v1. File path only. Simpler and sufficient.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (already installed) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (exists from Phase 1) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v && uv run ruff check claude_env/ && uv run mypy claude_env/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `setup` writes files to a temp global_root without error | integration (tmp_path + mock) | `uv run pytest tests/test_cli.py::test_setup_writes_global_layer -x` | ❌ Wave 0 |
| CLI-01 | `setup` installs SKILL.md at correct path | unit | `uv run pytest tests/test_cli.py::test_setup_installs_skill -x` | ❌ Wave 0 |
| CLI-02 | `bootstrap --spec yaml_file` generates `.claude/` layer in tmp project | integration (tmp_path) | `uv run pytest tests/test_cli.py::test_bootstrap_with_spec -x` | ❌ Wave 0 |
| CLI-02 | `bootstrap` without LLM (spec file path) exits 0 and writes files | integration | `uv run pytest tests/test_cli.py::test_bootstrap_no_api_key_with_spec -x` | ❌ Wave 0 |
| CLI-03 | `bootstrap --dry-run --spec file` prints paths, writes nothing | unit | `uv run pytest tests/test_cli.py::test_bootstrap_dry_run_no_api_key -x` | ❌ Wave 0 |
| CLI-03 | Dry-run path list matches actual written paths | integration | `uv run pytest tests/test_cli.py::test_dry_run_paths_match_actual -x` | ❌ Wave 0 |
| CLI-04 | SKILL.md written with correct frontmatter (name: bootstrap, allowed-tools: Bash) | unit | `uv run pytest tests/test_cli.py::test_skill_md_frontmatter -x` | ❌ Wave 0 |

**Testing approach:** Use `typer.testing.CliRunner` (ships with Typer, no extra dep). For CLI-02, avoid real LLM calls by always using `--spec` in tests. Mock `InputNormalizer.from_freeform` only if testing the interactive prompt path.

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v && uv run ruff check claude_env/ && uv run mypy claude_env/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_cli.py` — covers CLI-01 through CLI-04 (7 test functions above)
- [ ] `claude_env/cli.py` — replace stub with `setup` + `bootstrap` commands (existing file, needs full rewrite)

*(No new test framework or config needed — existing pytest setup covers this)*

---

## Sources

### Primary (HIGH confidence)

- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/cli.py` — confirmed stub structure, Typer app, entry point
- `/home/manuel/Desktop/PROJECTS/claude-env-2/pyproject.toml` — confirmed `claude-env = "claude_env.cli:app"` entry point, typer>=0.24 in deps
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/generator/generator.py` — confirmed `execute()` signature, `_resolve_path()` logic
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/pipeline/` — confirmed all pipeline components are importable and functional (89 tests pass)
- `~/.claude/skills/adaptyv/SKILL.md`, `~/.claude/skills/perplexity-search/SKILL.md` — real SKILL.md format: YAML frontmatter with `name`, `description`, `allowed-tools`
- `/home/manuel/.claude/plugins/cache/claude-plugins-official/vercel/0.40.0/skills/bootstrap/SKILL.md` — confirmed `name: bootstrap`, plugin skill directory structure
- `/home/manuel/.claude/plugins/marketplaces/thedotmack/plugin/skills/do/SKILL.md` — confirmed slash-command skill format with `allowed-tools`
- `uv run python -c "import typer; print(typer.__version__)"` — typer 0.24.1 confirmed installed

### Secondary (MEDIUM confidence)

- Typer official docs (`help(typer.prompt)` via Python REPL) — prompt API confirmed: wraps click.prompt with same signature
- Claude Code skill resolution behavior (inferred from directory structure `~/.claude/skills/<dir>/<subdir>/SKILL.md` → `/dir:subdir` invocation) — MEDIUM because no official documentation found for user-installed skill colon-syntax

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps; all confirmed installed and functional
- CLI architecture: HIGH — derived from actual Typer API, existing pipeline code, confirmed entry point
- SKILL.md format: HIGH — verified from multiple real installed skills
- SKILL.md invocation path (`/claude-env:bootstrap`): MEDIUM — colon-syntax behavior inferred from plugin structure, not confirmed in official docs
- Pitfalls: HIGH — derived from concrete code analysis and known integration points

**Research date:** 2026-04-20
**Valid until:** 2026-05-20 (stable ecosystem; Claude Code SKILL.md format may change — verify at implementation time)
