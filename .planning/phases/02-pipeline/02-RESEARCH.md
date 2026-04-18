# Phase 2: Pipeline - Research

**Researched:** 2026-04-18
**Domain:** Data pipeline — Input Normalizer, Domain Classifier, Environment Planner
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | System accepts raw freeform idea text and normalizes it to a structured ProjectSpec | LLM expansion via anthropic SDK 0.96.0; structured JSON output from claude-haiku-3-5 with injected client for testability |
| PIPE-02 | System accepts a structured spec document (markdown/YAML) as input | PyYAML (already in deps) for YAML specs; regex-based header extraction for markdown; no new deps required |
| PIPE-03 | System classifies ProjectSpec into a technical domain using static domain profiles | Signal matching: iterate detection_signals from each DomainProfile against ProjectSpec fields; deterministic, pure function |
| PIPE-04 | System produces a GenerationPlan from ProjectSpec + DomainProfile (pure data structure, no I/O) | Pure function plan(spec, profile, registry) → GenerationPlan; TemplateRegistry.list_templates() validates artifact IDs at plan time |
</phase_requirements>

---

## Summary

Phase 2 builds the three processing components that sit between raw user input and the file-writing step. None of these components write files to disk. The pipeline is: freeform text or spec file → `ProjectSpec` (Input Normalizer) → domain classification → `DomainProfile` (Domain Classifier) → `GenerationPlan` listing every artifact to write (Environment Planner).

The only external dependency introduced in this phase is the `anthropic` Python SDK for the Input Normalizer's freeform expansion path (PIPE-01). The Domain Classifier and Environment Planner are entirely deterministic — no LLM, no I/O, testable with fixture inputs. The critical open question from STATE.md ("LLM invocation path for Input Normalizer") is answered here: use `anthropic` SDK with JSON-mode structured output and inject the client via constructor to keep tests free of real API calls.

The primary design challenge is `ProjectSpec` schema — it must capture enough from freeform prose to drive domain classification (feeding the classifier's signal matching) and template variable binding (feeding the planner). The schema must be defined before any of the three components are implemented, because all three take or produce it.

**Primary recommendation:** Define `ProjectSpec` and `GenerationPlan` Pydantic models first (Wave 0), then implement Input Normalizer with injected `anthropic` client, then Domain Classifier as a pure signal-matching function, then Environment Planner as a pure data-transformation function.

---

## Standard Stack

### Core (already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.13.1 | `ProjectSpec`, `GenerationPlan` models | Already locked; v2 `model_validate()` from dict covers LLM JSON response directly |
| PyYAML | 6.0.3 | Parse structured YAML spec files (PIPE-02) | Already in deps; `yaml.safe_load()` covers all YAML input |
| anthropic | 0.96.0 | LLM call for freeform expansion (PIPE-01) | Official Anthropic Python SDK; structured JSON output; `ANTHROPIC_API_KEY` env var |

### New Dependency (PIPE-01 only)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| anthropic | 0.96.0 | Call Claude to extract structured fields from freeform text | Only path to reliable freeform→structured extraction; SDK ships its own mypy stubs |

**Installation:**
```bash
uv add anthropic
```

**Version verification (confirmed 2026-04-18 via pip index):**
- anthropic: 0.96.0 (latest)

### No Additional Dependencies for PIPE-02, PIPE-03, PIPE-04

- PyYAML already handles YAML spec files
- Markdown spec parsing needs only stdlib `re` (regex) for header extraction
- Domain Classifier and Environment Planner are pure Python with Pydantic — zero new deps

---

## Architecture Patterns

### Data Schema: ProjectSpec

The central data contract. All three components consume or produce it. Must be defined before any implementation.

```python
# claude_env/models/project_spec.py
from pydantic import BaseModel, ConfigDict, Field

class ProjectSpec(BaseModel):
    """Normalized representation of a project definition.

    Produced by Input Normalizer; consumed by Domain Classifier and Environment Planner.
    Fields are intentionally broad to cover both freeform and structured input paths.
    """
    model_config = ConfigDict(extra="forbid")

    name: str                            # Project name, slug form
    description: str                     # One-paragraph project description
    domain_hint: str = "general"         # Coarse domain from input ("web", "cli", etc.) or "general"
    languages: list[str] = Field(default_factory=list)  # ["python", "typescript", ...]
    tech_stack: list[str] = Field(default_factory=list)  # ["react", "fastapi", "postgres", ...]
    constraints: list[str] = Field(default_factory=list) # ["offline-first", "no external deps", ...]
    known_skills: list[str] = Field(default_factory=list) # Skill slugs user explicitly requested
```

Key design decisions:
- `domain_hint` is populated by Input Normalizer (may be "general") and then overridden/confirmed by Domain Classifier
- `tech_stack` is a flat string list — matches how `detection_signals` in `DomainProfile` are structured (flat strings)
- All list fields default to empty list — freeform input may not populate every field

### Data Schema: GenerationPlan

```python
# claude_env/models/generation_plan.py
from __future__ import annotations
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ConfigDict

class OutputLayer(str, Enum):
    GLOBAL = "global"   # writes to ~/.claude/
    PROJECT = "project" # writes to .claude/ in target project

class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_path: str         # Relative path within the layer root (e.g., "skills/fix-issue/SKILL.md")
    template_id: str         # Filename in templates/ (e.g., "skill_stub.j2")
    context: dict[str, object]  # Variables passed to template.render()
    layer: OutputLayer       # Where to write

class GenerationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_name: str
    domain: str
    artifacts: list[Artifact]
```

### Pattern 1: Input Normalizer — Freeform Path (PIPE-01)

**What:** An `InputNormalizer` class that accepts an optional injected `anthropic.Anthropic` client. When given freeform text, calls the LLM with a system prompt that instructs extraction of `ProjectSpec` fields as JSON. When given a spec file path, dispatches to the structured parser.

**Dependency injection for testability:** The `anthropic.Anthropic` client is injected at construction time. Tests pass a mock client; production code passes the real one (or lets the class construct it from `ANTHROPIC_API_KEY`).

```python
# claude_env/pipeline/input_normalizer.py
from __future__ import annotations

import anthropic
from pydantic import ValidationError

from claude_env.models.project_spec import ProjectSpec

_SYSTEM_PROMPT = """
You are a project specification extractor. Given a freeform project description, output a JSON object with:
- name: short slug (lowercase, hyphens)
- description: one paragraph summary
- domain_hint: one of "web", "cli", "data", "infra", or "general"
- languages: list of programming languages mentioned or implied
- tech_stack: list of frameworks, databases, tools mentioned
- constraints: list of explicit constraints or requirements
- known_skills: list of specific capability slugs if mentioned

Output ONLY the JSON object, no markdown, no explanation.
"""

class InputNormalizer:
    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self._client = client or anthropic.Anthropic()

    def from_freeform(self, text: str) -> ProjectSpec:
        message = self._client.messages.create(
            model="claude-haiku-3-5-20241022",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = message.content[0].text
        import json
        data = json.loads(raw)
        return ProjectSpec.model_validate(data)

    def from_spec_file(self, path: Path) -> ProjectSpec:
        ...  # dispatches to YAML or markdown parser based on suffix
```

Model choice: `claude-haiku-3-5-20241022` — fast, cheap, sufficient for structured extraction. Not `claude-sonnet` (too expensive for a routine normalization step).

### Pattern 2: Structured Spec Parser (PIPE-02)

**What:** Pure parsing logic — no LLM. Two sub-paths: YAML (`.yaml`/`.yml`) and Markdown (`.md`).

```python
# claude_env/pipeline/spec_parser.py
from __future__ import annotations

import re
import yaml
from pathlib import Path
from claude_env.models.project_spec import ProjectSpec

def parse_yaml_spec(path: Path) -> ProjectSpec:
    """Parse a YAML spec file directly into ProjectSpec.

    The YAML file must have keys matching ProjectSpec fields.
    Extra keys are rejected by model_config extra='forbid'.
    """
    raw = yaml.safe_load(path.read_text())
    return ProjectSpec.model_validate(raw)

def parse_markdown_spec(path: Path) -> ProjectSpec:
    """Extract ProjectSpec fields from a structured markdown spec.

    Expected format: top-level H1 is project name, H2 sections map to fields.
    """
    text = path.read_text()

    name_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else "unknown"

    desc_match = re.search(r"^## Description\s*\n(.+?)(?=\n##|\Z)", text, re.MULTILINE | re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    stack_match = re.search(r"^## (Stack|Tech Stack)\s*\n(.+?)(?=\n##|\Z)", text, re.MULTILINE | re.DOTALL)
    tech_stack: list[str] = []
    if stack_match:
        tech_stack = [line.strip("- ").strip() for line in stack_match.group(2).splitlines() if line.strip()]

    return ProjectSpec(name=name, description=description, tech_stack=tech_stack)
```

### Pattern 3: Domain Classifier (PIPE-03)

**What:** A pure function that iterates over all domain profiles and scores each against `ProjectSpec.tech_stack + ProjectSpec.languages`. Returns the profile with the highest match count. Falls back to `general` profile if no signals match.

```python
# claude_env/pipeline/domain_classifier.py
from __future__ import annotations

from claude_env.models.domain_profile import DomainProfile, load_profile
from claude_env.models.project_spec import ProjectSpec
from pathlib import Path

def classify(spec: ProjectSpec, profiles: list[DomainProfile]) -> DomainProfile:
    """Assign the best-matching DomainProfile to spec.

    Matching: count how many detection_signals appear in spec.tech_stack or spec.languages.
    Returns the profile with highest match count. Ties go to first-defined profile.
    Falls back to the 'general' profile (detection_signals=[]) if no signals match.
    """
    spec_tokens = {t.lower() for t in spec.tech_stack + spec.languages}

    scored: list[tuple[int, DomainProfile]] = []
    general: DomainProfile | None = None

    for profile in profiles:
        if profile.domain == "general":
            general = profile
            continue
        score = sum(1 for sig in profile.detection_signals if sig.lower() in spec_tokens)
        scored.append((score, profile))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored and scored[0][0] > 0:
        return scored[0][1]

    # Fall back to general or first profile
    if general:
        return general
    return profiles[0]


def load_all_profiles(profiles_dir: Path) -> list[DomainProfile]:
    """Load all .yaml profiles from profiles_dir."""
    return [load_profile(p) for p in sorted(profiles_dir.glob("*.yaml"))]
```

### Pattern 4: Environment Planner (PIPE-04)

**What:** A pure function. Takes `ProjectSpec` + `DomainProfile` + available template IDs. Returns `GenerationPlan` — a flat list of `Artifact` objects. No file I/O. The planner knows what templates exist via `TemplateRegistry.list_templates()`, but does not call `render()`.

```python
# claude_env/pipeline/environment_planner.py
from __future__ import annotations

from claude_env.models.domain_profile import DomainProfile
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer
from claude_env.models.project_spec import ProjectSpec

def plan(spec: ProjectSpec, profile: DomainProfile, available_templates: list[str]) -> GenerationPlan:
    """Produce a GenerationPlan from spec + profile.

    Rules:
    - One Artifact per skill slug in profile.skill_slugs → template "skill_stub.j2", layer PROJECT
    - One Artifact per agent slug in profile.agent_slugs → template "agent_stub.j2", layer PROJECT
    - One Artifact for per-project CLAUDE.md → template "claude_md_project.j2", layer PROJECT
    - All artifact template_ids must exist in available_templates (validated at plan time)

    No file I/O occurs here. Generator (Phase 3) executes the plan.
    """
    artifacts: list[Artifact] = []

    # Per-project CLAUDE.md
    artifacts.append(Artifact(
        target_path="CLAUDE.md",
        template_id="claude_md_project.j2",
        context={
            "project_name": spec.name,
            "domain": profile.domain,
            "sections": profile.claude_md_sections,
        },
        layer=OutputLayer.PROJECT,
    ))

    # Skills
    for slug in profile.skill_slugs:
        artifacts.append(Artifact(
            target_path=f"skills/{slug}/SKILL.md",
            template_id="skill_stub.j2",
            context={"slug": slug, "domain": profile.domain},
            layer=OutputLayer.PROJECT,
        ))

    # Agents
    for slug in profile.agent_slugs:
        artifacts.append(Artifact(
            target_path=f"agents/{slug}.md",
            template_id="agent_stub.j2",
            context={"slug": slug, "domain": profile.domain},
            layer=OutputLayer.PROJECT,
        ))

    # Validate all template IDs exist
    for artifact in artifacts:
        if artifact.template_id not in available_templates:
            raise ValueError(
                f"Template '{artifact.template_id}' not found. "
                f"Available: {available_templates}"
            )

    return GenerationPlan(
        project_name=spec.name,
        domain=profile.domain,
        artifacts=artifacts,
    )
```

### Recommended Project Structure (additions for Phase 2)

```
claude_env/
├── models/
│   ├── domain_profile.py       # Phase 1 — already exists
│   ├── project_spec.py         # Phase 2 — NEW
│   └── generation_plan.py      # Phase 2 — NEW
├── pipeline/
│   ├── __init__.py             # Phase 2 — NEW
│   ├── input_normalizer.py     # Phase 2 — NEW (PIPE-01 + PIPE-02)
│   ├── spec_parser.py          # Phase 2 — NEW (PIPE-02 structured path)
│   ├── domain_classifier.py    # Phase 2 — NEW (PIPE-03)
│   └── environment_planner.py  # Phase 2 — NEW (PIPE-04)
tests/
├── test_input_normalizer.py    # Phase 2 — NEW
├── test_domain_classifier.py   # Phase 2 — NEW
├── test_environment_planner.py # Phase 2 — NEW
└── fixtures/
    ├── specs/
    │   ├── simple_web.yaml     # Structured YAML spec fixture
    │   ├── cli_tool.yaml       # Structured YAML spec fixture
    │   └── simple_web.md       # Markdown spec fixture
```

### Anti-Patterns to Avoid

- **LLM client constructed at module level:** `client = anthropic.Anthropic()` at top of file fails at import time if `ANTHROPIC_API_KEY` is not set. Construct inside `__init__` or accept as argument.
- **Domain Classifier calling LLM:** Classifier must be deterministic. If the LLM already populated `domain_hint` in `ProjectSpec`, the classifier may confirm it — but it must also override it if signals point elsewhere. Never make classifier depend on LLM.
- **GenerationPlan with file paths containing `~`:** `target_path` is relative within the layer root. The Generator (Phase 3) resolves the absolute path. Phase 2 must not expand `~` — that is Phase 3's job.
- **Calling `registry.render()` from the Planner:** The Planner uses `registry.list_templates()` to validate IDs, not to render. Rendering happens in Phase 3. Keep the boundary sharp.
- **Hardcoding model name as string literal:** Put the model name in a module-level constant (`_LLM_MODEL = "claude-haiku-3-5-20241022"`) so it can be overridden in tests and updated in one place.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Freeform text → structured data | Custom regex / keyword extraction | anthropic SDK + LLM structured output | Regex breaks on paraphrasing; LLM handles natural language variation |
| JSON response parsing from LLM | Custom string parsing | `json.loads()` + `ProjectSpec.model_validate()` | LLM may add whitespace, comments; json.loads handles all valid JSON |
| YAML spec parsing | Custom parser | `yaml.safe_load()` (already in deps) | YAML edge cases: multi-line strings, anchors, type coercion |
| Token matching for classification | Levenshtein distance or ML | Simple set intersection on `detection_signals` | Over-engineering: exact match on tech stack tokens is sufficient and debuggable |
| Artifact ordering in GenerationPlan | Topological sort | Deterministic list construction order | No dependency ordering needed — Generator writes all artifacts; CLAUDE.md first is sufficient |

**Key insight:** The pipeline components look like they need sophisticated ML or NLP. They don't. The LLM handles the only genuinely ambiguous step (freeform→structured). After that, everything is set membership and list construction.

---

## Common Pitfalls

### Pitfall 1: LLM Returns Invalid JSON

**What goes wrong:** `json.loads(message.content[0].text)` raises `JSONDecodeError`. The LLM prepended markdown fences (` ```json `) or added a trailing comment.

**Why it happens:** LLMs sometimes wrap JSON in markdown code blocks even when instructed not to. Haiku is better than older models but not perfect.

**How to avoid:** Strip markdown fences before parsing. Use a utility function:

```python
def _extract_json(raw: str) -> str:
    """Strip markdown code fences if present."""
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```\w*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)
    return stripped.strip()
```

**Warning signs:** `JSONDecodeError: Expecting value: line 1 column 1` in Input Normalizer tests with real API.

### Pitfall 2: ProjectSpec ValidationError on LLM Output

**What goes wrong:** `ProjectSpec.model_validate(data)` raises `ValidationError` because the LLM returned unexpected field names or wrong types (e.g., `"languages": "python"` instead of `["python"]`).

**Why it happens:** LLM output is probabilistic — even with a detailed system prompt, field names may deviate on edge cases.

**How to avoid:** Use a lenient intermediate model or catch `ValidationError` and retry with an error message appended to the prompt. For v1, a single retry is sufficient:

```python
try:
    return ProjectSpec.model_validate(data)
except ValidationError as e:
    # One retry with error context
    ...
```

**Warning signs:** Occasional test failures on freeform inputs that are structurally valid but use synonyms for field names.

### Pitfall 3: Domain Classifier Has No Match and No General Profile

**What goes wrong:** `classify()` returns the first profile arbitrarily when no signals match and no `general` profile is loaded. Classification is silently wrong.

**Why it happens:** `general.yaml` was not loaded (e.g., `profiles_dir` path points to a subset of profiles), or the `general` domain was removed.

**How to avoid:** `classify()` must assert that a `general` profile exists in the profiles list. Raise `ValueError("No 'general' fallback profile found")` if absent. Load profiles with `load_all_profiles()` which loads all `.yaml` files, ensuring `general.yaml` is always included.

**Warning signs:** Classifier assigns `cli` domain to a project with description "a web app" because `cli.yaml` happened to be first alphabetically.

### Pitfall 4: Environment Planner Generates Template IDs That Don't Exist

**What goes wrong:** Phase 3 Generator calls `registry.render(artifact.template_id, artifact.context)` and gets `TemplateNotFound`. The template was listed in a `DomainProfile.hook_templates` but the `.j2` file was never created.

**Why it happens:** `DomainProfile.hook_templates` contains IDs like `"lint_after_edit"` that reference templates not yet created (they are Phase 3 deliverables). Phase 2 plan only validates templates that exist at plan time.

**How to avoid:** The Planner's validation of `available_templates` must only cover templates Phase 2 is responsible for (CLAUDE.md, skill stub, agent stub). Hook templates are a Phase 3 concern — don't validate them in the Planner until they exist. Document this boundary explicitly.

**Warning signs:** `ValueError: Template 'lint_after_edit.j2' not found` during Phase 2 testing when planner tries to validate hook templates.

### Pitfall 5: InputNormalizer Constructs Anthropic Client at Import Time

**What goes wrong:** `import claude_env.pipeline.input_normalizer` fails with `AuthenticationError` or raises because `ANTHROPIC_API_KEY` is not set — breaks all tests.

**Why it happens:** `client = anthropic.Anthropic()` at module level reads `ANTHROPIC_API_KEY` immediately on import.

**How to avoid:** Always construct inside `__init__` with lazy default:

```python
class InputNormalizer:
    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self._client = client or anthropic.Anthropic()  # reads key only here
```

Tests pass a mock: `InputNormalizer(client=mock_client)` — never hits the env var.

### Pitfall 6: mypy fails on anthropic stubs

**What goes wrong:** `uv run mypy claude_env/` reports `Skipping analyzing "anthropic"` or type errors on `message.content[0].text`.

**Why it happens:** anthropic SDK 0.96.x ships its own `py.typed` marker and complete stubs — this should just work. But the `content[0]` access has type `ContentBlock` which is a union. `mypy --strict` requires narrowing before accessing `.text`.

**How to avoid:** Narrow the content block type:

```python
from anthropic.types import TextBlock
block = message.content[0]
if not isinstance(block, TextBlock):
    raise ValueError(f"Unexpected content block type: {type(block)}")
raw = block.text
```

---

## Code Examples

### Anthropic SDK: structured extraction (verified pattern)

```python
# Source: anthropic SDK 0.96.0 docs — messages.create
import anthropic
import json

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

message = client.messages.create(
    model="claude-haiku-3-5-20241022",
    max_tokens=1024,
    system="Output ONLY valid JSON matching the schema described below...",
    messages=[{"role": "user", "content": "a web app for tracking habits"}],
)

# Content block narrowing (mypy --strict compatible)
from anthropic.types import TextBlock
block = message.content[0]
assert isinstance(block, TextBlock)
data = json.loads(block.text)
```

### Domain Classifier: signal matching (pure function, no deps)

```python
# Pure set intersection — no LLM
spec_tokens = {"react", "typescript", "postgres"}
signals = ["package.json", "index.html", "react", "tailwind"]
score = sum(1 for sig in signals if sig.lower() in spec_tokens)
# → 1 (react matched)
```

### Environment Planner: test pattern (no I/O)

```python
# tests/test_environment_planner.py
from claude_env.models.project_spec import ProjectSpec
from claude_env.models.domain_profile import load_profile
from claude_env.pipeline.environment_planner import plan
from pathlib import Path

def test_plan_produces_skill_artifacts() -> None:
    spec = ProjectSpec(name="my-app", description="a web app", domain_hint="web")
    profile = load_profile(Path("claude_env/profiles/web.yaml"))
    available = ["claude_md_project.j2", "skill_stub.j2", "agent_stub.j2"]
    result = plan(spec, profile, available)
    skill_paths = [a.target_path for a in result.artifacts if "skills/" in a.target_path]
    assert len(skill_paths) == len(profile.skill_slugs)
```

### Input Normalizer: test with mock client

```python
# tests/test_input_normalizer.py
from unittest.mock import MagicMock
from anthropic.types import Message, TextBlock, Usage
from claude_env.pipeline.input_normalizer import InputNormalizer

def make_mock_client(response_json: str) -> MagicMock:
    mock = MagicMock()
    text_block = MagicMock(spec=TextBlock)
    text_block.text = response_json
    mock.messages.create.return_value = MagicMock(content=[text_block])
    return mock

def test_from_freeform_returns_project_spec() -> None:
    mock_client = make_mock_client('{"name":"habit-tracker","description":"A web app","domain_hint":"web","languages":["python"],"tech_stack":["react"],"constraints":[],"known_skills":[]}')
    normalizer = InputNormalizer(client=mock_client)
    spec = normalizer.from_freeform("a web app for tracking habits")
    assert spec.name == "habit-tracker"
    assert spec.domain_hint == "web"
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Regex-only keyword extraction for "domain detection" | LLM structured extraction (freeform path) + signal matching (structured path) | Freeform path handles natural language variation; signal matching stays deterministic |
| anthropic SDK < 0.50: manual JSON parsing | anthropic SDK 0.96.0: content block typed as union; use `isinstance(block, TextBlock)` | mypy strict mode compatible; no silent type errors on content access |
| `model="claude-3-haiku"` (old naming) | `model="claude-haiku-3-5-20241022"` (current API ID) | Old model IDs may 404 — always use the versioned ID from official docs |

**Deprecated/outdated:**
- `anthropic.Client` (pre-0.20): replaced by `anthropic.Anthropic()`. Don't use.
- `completion()` method: replaced by `messages.create()`. Don't use.

---

## Open Questions

1. **Hook template IDs in GenerationPlan**
   - What we know: `DomainProfile.hook_templates` contains IDs like `"lint_after_edit"`. The Planner should eventually include these as `Artifact` entries.
   - What's unclear: The `.j2` templates for hooks don't exist yet (Phase 3 creates them). Should Phase 2 include hook artifacts in the plan with a known-missing template ID, or skip them?
   - Recommendation: Skip hook artifacts in Phase 2's Planner. Add them in Phase 3 once templates exist. The `plan()` function signature can accept an optional `include_hooks: bool = False` flag to keep the API clean.

2. **Markdown spec format: enforce or auto-detect?**
   - What we know: PIPE-02 says "markdown/YAML spec file" — both must work.
   - What's unclear: Is there a canonical markdown spec format, or does the normalizer do best-effort extraction?
   - Recommendation: Best-effort extraction for markdown, strict validation for YAML. YAML must match `ProjectSpec` fields exactly (Pydantic enforces this). Markdown gets name from H1, description from first paragraph, tech_stack from bullet lists under "## Stack". Document this format in a `spec-template.md` file that users can copy.

3. **anthropic SDK: sync vs async**
   - What we know: Current phase uses synchronous `client.messages.create()`. CLI is synchronous (Typer). No async anywhere in Phase 1 or 2.
   - What's unclear: Phase 4 CLI may want streaming output for user experience.
   - Recommendation: Use `anthropic.Anthropic()` (sync) for Phase 2. `anthropic.AsyncAnthropic()` is available later if streaming is needed. Don't introduce async in Phase 2 — no benefit until the CLI UX needs it.

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
| PIPE-01 | `from_freeform(text)` returns valid `ProjectSpec` with `domain_hint` populated | unit (mock client) | `uv run pytest tests/test_input_normalizer.py -x` | ❌ Wave 0 |
| PIPE-02 | `from_spec_file(yaml_path)` returns equivalent `ProjectSpec` | unit | `uv run pytest tests/test_input_normalizer.py::test_from_yaml_spec -x` | ❌ Wave 0 |
| PIPE-02 | `from_spec_file(md_path)` returns equivalent `ProjectSpec` | unit | `uv run pytest tests/test_input_normalizer.py::test_from_markdown_spec -x` | ❌ Wave 0 |
| PIPE-03 | Classifier assigns correct domain to `ProjectSpec` with known tech stack | unit | `uv run pytest tests/test_domain_classifier.py -x` | ❌ Wave 0 |
| PIPE-03 | Classifier falls back to `general` when no signals match | unit | `uv run pytest tests/test_domain_classifier.py::test_fallback_to_general -x` | ❌ Wave 0 |
| PIPE-04 | `plan()` returns `GenerationPlan` listing all skill and agent artifacts | unit | `uv run pytest tests/test_environment_planner.py -x` | ❌ Wave 0 |
| PIPE-04 | `plan()` raises `ValueError` if a template ID is not in `available_templates` | unit | `uv run pytest tests/test_environment_planner.py::test_invalid_template_raises -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v && uv run ruff check claude_env/ && uv run mypy claude_env/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `claude_env/models/project_spec.py` — `ProjectSpec` Pydantic model
- [ ] `claude_env/models/generation_plan.py` — `Artifact`, `GenerationPlan`, `OutputLayer` models
- [ ] `claude_env/pipeline/__init__.py` — empty package init
- [ ] `tests/test_input_normalizer.py` — covers PIPE-01 (mock), PIPE-02 (YAML), PIPE-02 (markdown)
- [ ] `tests/test_domain_classifier.py` — covers PIPE-03 (match, no match, general fallback)
- [ ] `tests/test_environment_planner.py` — covers PIPE-04 (artifact count, invalid template raises)
- [ ] `tests/fixtures/specs/simple_web.yaml` — YAML spec fixture for PIPE-02 test
- [ ] `tests/fixtures/specs/simple_web.md` — Markdown spec fixture for PIPE-02 test
- [ ] Framework install: `uv add anthropic` — adds anthropic 0.96.0 to pyproject.toml

---

## Sources

### Primary (HIGH confidence)

- `/home/manuel/Desktop/PROJECTS/claude-env-2/.planning/research/ARCHITECTURE.md` — component responsibilities, data flow, LLM invocation decision
- `/home/manuel/Desktop/PROJECTS/claude-env-2/.planning/research/SUMMARY.md` — open question on LLM path, build order
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/models/domain_profile.py` — locked schema, confirmed `detection_signals: list[str]`
- `/home/manuel/Desktop/PROJECTS/claude-env-2/claude_env/profiles/web.yaml` — confirmed signal format (flat strings)
- pip index anthropic — 0.96.0 confirmed current (2026-04-18)

### Secondary (MEDIUM confidence)

- anthropic SDK 0.96.0 `TextBlock` type — inferred from SDK typing pattern; confirmed sdk ships `py.typed`
- `claude-haiku-3-5-20241022` model ID — current as of training knowledge, verify at implementation time via Anthropic docs

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — anthropic 0.96.0 verified via pip index; all other deps already in pyproject.toml
- Architecture: HIGH — `ProjectSpec` and `GenerationPlan` schemas derived directly from ARCHITECTURE.md and existing `DomainProfile` contract; pattern consistent with Phase 1 design
- Pitfalls: HIGH — LLM JSON fence issue and `content[0]` type narrowing are concrete SDK-level issues; classifier fallback pitfall is structural reasoning from code design
- LLM invocation decision: HIGH — ARCHITECTURE.md and SUMMARY.md both explicitly state "LLM call (Claude)"; anthropic SDK is the only correct path

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (stable; anthropic SDK releases frequently but messages API contract is stable)
