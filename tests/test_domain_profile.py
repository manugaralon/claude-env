"""Tests for DomainProfile model and load_profile()."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from claude_env.models.domain_profile import DomainProfile, load_profile

PROFILES_DIR = Path(__file__).parent.parent / "claude_env" / "profiles"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "profiles"
ALL_DOMAINS = ["web", "cli", "data", "infra", "general"]


def test_valid_yaml_loads_via_load_profile(
    tmp_path: Path, sample_profile_yaml: str
) -> None:
    p = tmp_path / "web.yaml"
    p.write_text(sample_profile_yaml)
    profile = load_profile(p)
    assert isinstance(profile, DomainProfile)
    assert profile.domain == "web"
    assert len(profile.skill_slugs) == 3


def test_model_validate_from_dict(sample_profile_yaml: str) -> None:
    data = yaml.safe_load(sample_profile_yaml)
    profile = DomainProfile.model_validate(data)
    assert profile.domain == "web"


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError) as exc_info:
        load_profile(FIXTURES_DIR / "invalid_missing_field.yaml")
    assert "domain" in str(exc_info.value)


def test_extra_field_raises() -> None:
    with pytest.raises(ValidationError) as exc_info:
        load_profile(FIXTURES_DIR / "invalid_extra_field.yaml")
    assert "foo" in str(exc_info.value) or "extra" in str(exc_info.value).lower()


def test_wrong_type_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "domain: web\n"
        "display_name: X\n"
        "description: Y\n"
        "skill_slugs: not-a-list\n"
        "agent_slugs: [a]\n"
        "claude_md_sections: [s]\n"
        "hook_templates: [h]\n"
        "detection_signals: [d]\n"
    )
    with pytest.raises(ValidationError):
        load_profile(bad)


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_real_profile_loads(domain: str) -> None:
    path = PROFILES_DIR / f"{domain}.yaml"
    profile = load_profile(path)
    assert profile.domain == domain
    assert len(profile.skill_slugs) >= 1
    assert len(profile.agent_slugs) >= 1
