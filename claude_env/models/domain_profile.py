"""DomainProfile Pydantic v2 model — locked schema for domain profile YAMLs.

STATE.md flags this as "core data contract, must be finalized in Phase 1."
Do not add fields in later phases without updating this model first.
`extra="forbid"` guarantees drift is caught at validation time.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class DomainProfile(BaseModel):
    """Static profile describing how to generate a Claude env for a given domain."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    display_name: str
    description: str
    skill_slugs: list[str]
    agent_slugs: list[str]
    claude_md_sections: list[str]
    hook_templates: list[str]
    detection_signals: list[str]


def load_profile(path: Path) -> DomainProfile:
    """Load and validate a DomainProfile YAML from disk.

    Raises:
        pydantic.ValidationError: if YAML is missing required fields, has extra fields,
            or has wrong types.
        yaml.YAMLError: if YAML is syntactically invalid.
        FileNotFoundError: if `path` does not exist.
    """
    raw = yaml.safe_load(path.read_text())
    return DomainProfile.model_validate(raw)
