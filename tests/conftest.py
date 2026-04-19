"""Shared pytest fixtures for claude-env tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from claude_env.models.domain_profile import load_profile
from claude_env.models.generation_plan import GenerationPlan
from claude_env.models.project_spec import ProjectSpec
from claude_env.pipeline.environment_planner import plan
from claude_env.templates.registry import TemplateRegistry


@pytest.fixture
def sample_profile_yaml() -> str:
    """Minimal valid DomainProfile YAML (used by Plan 02 tests)."""
    return (
        "domain: web\n"
        "display_name: Web Application\n"
        "description: Frontend or fullstack web project\n"
        "skill_slugs: [fix-issue, create-pr, run-lint]\n"
        "agent_slugs: [security-reviewer, accessibility-auditor]\n"
        "claude_md_sections: [mobile_first, plan_execute_verify]\n"
        "hook_templates: [lint_after_edit]\n"
        "detection_signals: [package.json, index.html]\n"
    )


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    """Absolute path to a scratch templates directory (used by Plan 03 tests)."""
    d = tmp_path / "templates"
    d.mkdir()
    return d


@pytest.fixture
def real_registry() -> TemplateRegistry:
    """TemplateRegistry backed by the real templates/ directory at project root."""
    templates_path = Path(__file__).parent.parent / "templates"
    return TemplateRegistry(templates_path.resolve())


@pytest.fixture
def web_plan(real_registry: TemplateRegistry) -> GenerationPlan:
    """GenerationPlan built from the real web.yaml profile using environment_planner.plan()."""
    profiles_dir = Path(__file__).parent.parent / "claude_env" / "profiles"
    profile = load_profile(profiles_dir / "web.yaml")
    spec = ProjectSpec(
        name="test-web-project",
        description="A frontend web project for testing",
        domain_hint="web",
        languages=["typescript"],
        tech_stack=["react", "vite"],
    )
    available = real_registry.list_templates()
    return plan(spec, profile, available)
