"""Tests for ProjectSpec and GenerationPlan Pydantic v2 models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from claude_env.models.project_spec import ProjectSpec
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer


# ---------------------------------------------------------------------------
# ProjectSpec tests
# ---------------------------------------------------------------------------


def test_project_spec_defaults() -> None:
    spec = ProjectSpec(name="x", description="y")
    assert spec.domain_hint == "general"
    assert spec.languages == []
    assert spec.tech_stack == []
    assert spec.constraints == []
    assert spec.known_skills == []


def test_project_spec_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        ProjectSpec(name="x", description="y", unknown_field="bad")  # type: ignore[call-arg]


def test_project_spec_round_trip() -> None:
    spec = ProjectSpec(
        name="x",
        description="y",
        domain_hint="web",
        languages=["python"],
        tech_stack=["react"],
    )
    restored = ProjectSpec.model_validate(spec.model_dump())
    assert restored == spec


# ---------------------------------------------------------------------------
# OutputLayer tests
# ---------------------------------------------------------------------------


def test_output_layer_values() -> None:
    assert OutputLayer.GLOBAL == "global"
    assert OutputLayer.PROJECT == "project"


# ---------------------------------------------------------------------------
# Artifact tests
# ---------------------------------------------------------------------------


def test_artifact_creates_valid_instance() -> None:
    artifact = Artifact(
        target_path="CLAUDE.md",
        template_id="claude_md",
        context={"project_name": "x"},
        layer=OutputLayer.GLOBAL,
    )
    assert artifact.target_path == "CLAUDE.md"
    assert artifact.template_id == "claude_md"
    assert artifact.layer == OutputLayer.GLOBAL


def test_artifact_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Artifact(
            target_path="CLAUDE.md",
            template_id="claude_md",
            context={},
            layer=OutputLayer.GLOBAL,
            extra="bad",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# GenerationPlan tests
# ---------------------------------------------------------------------------


def test_generation_plan_empty_artifacts() -> None:
    plan = GenerationPlan(project_name="x", domain="web", artifacts=[])
    assert plan.project_name == "x"
    assert plan.domain == "web"
    assert plan.artifacts == []


def test_generation_plan_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        GenerationPlan(project_name="x", domain="web", artifacts=[], extra="bad")  # type: ignore[call-arg]


def test_generation_plan_with_artifacts() -> None:
    artifact = Artifact(
        target_path="CLAUDE.md",
        template_id="claude_md",
        context={"key": "val"},
        layer=OutputLayer.PROJECT,
    )
    plan = GenerationPlan(project_name="my-project", domain="cli", artifacts=[artifact])
    assert len(plan.artifacts) == 1
    assert plan.artifacts[0].layer == OutputLayer.PROJECT
