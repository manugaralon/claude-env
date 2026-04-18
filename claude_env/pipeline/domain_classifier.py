"""Domain Classifier — pure signal matching, no I/O, no LLM."""
from __future__ import annotations

from pathlib import Path

from claude_env.models.domain_profile import DomainProfile, load_profile
from claude_env.models.project_spec import ProjectSpec


def classify(spec: ProjectSpec, profiles: list[DomainProfile]) -> DomainProfile:
    """Assign the best-matching DomainProfile to a ProjectSpec.

    Matching: count how many detection_signals appear in
    spec.tech_stack + spec.languages (case-insensitive).

    Returns the profile with highest match count.
    Falls back to 'general' profile if no signals match.
    Raises ValueError if no 'general' profile is in the list.
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

    if general is not None:
        return general

    raise ValueError("No 'general' fallback profile found in profiles list")


def load_all_profiles(profiles_dir: Path) -> list[DomainProfile]:
    """Load all .yaml profiles from profiles_dir, sorted by filename."""
    return [load_profile(p) for p in sorted(profiles_dir.glob("*.yaml"))]
