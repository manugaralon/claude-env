"""Shared pytest fixtures for claude-env tests."""
from __future__ import annotations

from pathlib import Path

import pytest


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
