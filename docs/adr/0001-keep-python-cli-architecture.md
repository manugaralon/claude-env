# 0001 — Keep Python + Jinja2 architecture for claude-env CLI

**Status**: accepted
**Date**: 2026-05-07

## Context

claude-env was originally built as a Python CLI (Typer) with Pydantic models, Jinja2 templates, and a layered pipeline (input normalizer → domain classifier → environment planner → generator). After ~3500 LOC accumulated (1,444 in `claude_env/`, 1,464 in tests, 581 in `.j2` templates), we evaluated whether to simplify to a bash + YAML manifest alternative.

The motivating concern: Python brings distribution friction (users need `uv tool install` or pip), startup latency, and cognitive overhead vs a bash script + plain YAML manifest that any unix-literate person can read.

## Decision

**Keep the Python + Jinja2 architecture as-is.**

## Reasoning

### What we'd lose if we rewrote in bash

1. **Pydantic schema validation** (`ProjectSpec`, `DomainProfile`, `GenerationPlan`) catches errors at deserialization time. Bash YAML loading via `yq` or `python -c` is stringly-typed and error-prone.
2. **Jinja2 StrictUndefined** crashes immediately on missing template variables — a deliberate safety mechanism. Bash equivalents (envsubst, sed) silently produce empty strings.
3. **Conditional template logic** (`{% if mandatory_triggers %}…{% endif %}` in `skill_stub.j2`) — bash can do this with case/awk but it's fragile, especially with multi-line strings.
4. **107 pytest tests** — re-implementing in bats or shellspec would be painful and tests of bash logic are themselves notoriously brittle.
5. **Idempotent re-runs via sentinel headers** — Generator's `has_sentinel()` logic is non-trivial in bash.

### What a bash rewrite would actually cost

Rough LOC estimate for equivalent bash:
- Profile detection (filesystem signals): ~50 lines
- YAML loading via `yq` or python shell-out: ~30 lines
- Template rendering with conditionals: ~80–150 lines (or shell out to python anyway, defeating the purpose)
- Sentinel writing + idempotent re-runs: ~80 lines
- CLI args parsing: ~50 lines
- Total: 300–500 lines of bash, but **more fragile and less testable**

### What the Python version actually costs

- 11 dependencies (8 main + 3 dev). Main deps (pydantic, pyyaml, jinja2, typer, rich, anthropic, groq) are stable, mainstream, and provide concrete value.
- 1,444 LOC well-organized into 4 clear layers (models, pipeline, generator, templates).
- 1:1 LOC ratio between code and tests — high test coverage is paying off.
- `uv tool install` distribution is mature and one-command for users.

### Use case fit

claude-env is currently a **personal tool** for Manuel, not a public distribution. Future distribution via GitHub is possible but not the priority. Even if distribution becomes priority, the right target is likely an npm package wrapper (matching the Claude Code ecosystem norm) rather than bash — and the npm wrapper would itself be a thin shim over the existing Python CLI.

## Consequences

- **Continued reliance on Python 3.12+** — users without Python need to install it (or use `uv tool install` which bundles Python).
- **Maintained pyproject.toml + pytest harness** — already standard practice; not new burden.
- **Complexity stays managed via tests** — adding new templates/profiles requires updating tests in lockstep (current discipline is strong).
- **No rewrite work** — saves ~1–2 weeks of re-implementation + test rewriting that wouldn't deliver new functionality.

## Considered alternatives

- **Bash + YAML manifest** (rejected): more fragile, similar LOC, loses validation/typing/testing maturity.
- **TypeScript/Node CLI** (not seriously considered): would require similar rewrite cost; no distribution advantage over Python for this use case.
- **Refactor Python heavily** (rejected): code is already clean (4 clear layers, strict typing, comprehensive tests). No high-value refactor identified.

## Follow-ups (not blocking this decision)

- Continue the existing discipline of 1:1 test-to-code ratio.
- If future distribution targets non-Python users, build an npm wrapper around the Python CLI rather than rewriting.
- Periodically re-evaluate `anthropic` and `groq` SDK dependencies — they are used (input_normalizer, analyzer, cli, capture) but heavy. If LLM integration becomes optional, splitting them into an extras group (`pip install claude-env[llm]`) is worth considering.
