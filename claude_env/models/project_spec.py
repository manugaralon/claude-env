"""ProjectSpec Pydantic v2 model — input contract for the generation pipeline."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProjectSpec(BaseModel):
    """Structured representation of a project definition provided by the developer."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    domain_hint: str = "general"
    languages: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    known_skills: list[str] = Field(default_factory=list)
