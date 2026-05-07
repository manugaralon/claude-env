"""Tests for InputNormalizer and spec_parser functions."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Skip the entire file if the anthropic SDK is not installed — these tests
# exercise the LLM-mediated freeform path, which has no meaningful behavior
# without the SDK present.
pytest.importorskip("anthropic")

from anthropic.types import TextBlock  # noqa: E402

from claude_env.models.project_spec import ProjectSpec  # noqa: E402
from claude_env.pipeline.spec_parser import parse_markdown_spec, parse_yaml_spec  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "specs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_client(response_json: str) -> MagicMock:
    mock = MagicMock()
    text_block = TextBlock(text=response_json, type="text")
    mock_message = MagicMock()
    mock_message.content = [text_block]
    mock.messages.create.return_value = mock_message
    return mock


# ---------------------------------------------------------------------------
# parse_yaml_spec
# ---------------------------------------------------------------------------


def test_parse_yaml_spec_simple_web() -> None:
    spec = parse_yaml_spec(FIXTURES / "simple_web.yaml")
    assert isinstance(spec, ProjectSpec)
    assert spec.name == "habit-tracker"
    assert spec.domain_hint == "web"
    assert "react" in spec.tech_stack
    assert "fastapi" in spec.tech_stack
    assert "postgres" in spec.tech_stack


def test_parse_yaml_spec_cli_tool() -> None:
    spec = parse_yaml_spec(FIXTURES / "cli_tool.yaml")
    assert isinstance(spec, ProjectSpec)
    assert spec.name == "file-organizer"
    assert spec.domain_hint == "cli"


def test_parse_yaml_spec_extra_keys_raises(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        "name: test\ndescription: test\nunknown_field: oops\n"
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        parse_yaml_spec(bad_yaml)


# ---------------------------------------------------------------------------
# parse_markdown_spec
# ---------------------------------------------------------------------------


def test_parse_markdown_spec_simple_web() -> None:
    spec = parse_markdown_spec(FIXTURES / "simple_web.md")
    assert isinstance(spec, ProjectSpec)
    assert spec.name == "habit-tracker"
    assert "react" in spec.tech_stack


def test_parse_markdown_spec_tech_stack_complete() -> None:
    spec = parse_markdown_spec(FIXTURES / "simple_web.md")
    assert "fastapi" in spec.tech_stack
    assert "postgres" in spec.tech_stack


def test_parse_markdown_spec_description() -> None:
    spec = parse_markdown_spec(FIXTURES / "simple_web.md")
    assert "habits" in spec.description.lower()


# ---------------------------------------------------------------------------
# InputNormalizer — freeform path
# ---------------------------------------------------------------------------


def test_from_freeform_returns_project_spec() -> None:
    from claude_env.pipeline.input_normalizer import InputNormalizer

    response_json = (
        '{"name": "habit-tracker", "description": "A web app for tracking habits",'
        ' "domain_hint": "web", "languages": ["python"], "tech_stack": ["react"],'
        ' "constraints": [], "known_skills": []}'
    )
    client = make_mock_client(response_json)
    spec = InputNormalizer(client=client).from_freeform(
        "a web app for tracking habits"
    )
    assert isinstance(spec, ProjectSpec)
    assert spec.name == "habit-tracker"
    assert spec.domain_hint == "web"


def test_from_freeform_strips_json_fences() -> None:
    from claude_env.pipeline.input_normalizer import InputNormalizer

    fenced = (
        "```json\n"
        '{"name": "habit-tracker", "description": "desc", "domain_hint": "web",'
        ' "languages": [], "tech_stack": [], "constraints": [], "known_skills": []}\n'
        "```"
    )
    client = make_mock_client(fenced)
    spec = InputNormalizer(client=client).from_freeform("track my habits")
    assert spec.name == "habit-tracker"


# ---------------------------------------------------------------------------
# InputNormalizer — from_spec_file dispatch
# ---------------------------------------------------------------------------


def test_from_spec_file_yaml() -> None:
    from claude_env.pipeline.input_normalizer import InputNormalizer

    spec = InputNormalizer().from_spec_file(FIXTURES / "simple_web.yaml")
    assert isinstance(spec, ProjectSpec)
    assert spec.name == "habit-tracker"


def test_from_spec_file_markdown() -> None:
    from claude_env.pipeline.input_normalizer import InputNormalizer

    spec = InputNormalizer().from_spec_file(FIXTURES / "simple_web.md")
    assert isinstance(spec, ProjectSpec)
    assert spec.name == "habit-tracker"


def test_from_spec_file_unsupported_extension(tmp_path: Path) -> None:
    from claude_env.pipeline.input_normalizer import InputNormalizer

    txt = tmp_path / "spec.txt"
    txt.write_text("name: test")
    with pytest.raises(ValueError, match="Unsupported"):
        InputNormalizer().from_spec_file(txt)
