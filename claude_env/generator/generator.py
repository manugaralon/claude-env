"""Generator — executes a GenerationPlan by writing all artifacts to disk.

This is the core I/O layer that turns a GenerationPlan (data) into files on
disk. Each artifact carries a write strategy (``merge_strategy``); the
generator dispatches on it — sentinel-managed block, write-once,
skip-if-exists, or plain overwrite. The strategy is always artifact metadata,
never inferred from file contents (Phase-3 invariant).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from claude_env.generator.content_catalogue import enrich_artifact_context
from claude_env.generator.sentinel import merge_sentinel_block, wrap_with_sentinel
from claude_env.models.generation_plan import (
    Artifact,
    GenerationPlan,
    MergeStrategy,
    OutputLayer,
)
from claude_env.templates.registry import TemplateRegistry

# The per-artifact action a run would take against the real target state.
Action = Literal["create", "merge-managed-block", "skip-exists", "overwrite"]


def effective_merge_strategy(artifact: Artifact) -> MergeStrategy:
    """Resolve the write strategy for *artifact*.

    Explicit ``merge_strategy`` wins. When unset, map from ``write_once`` and
    ``layer`` so artifacts authored before Phase 7 keep identical behavior:
    GLOBAL → sentinel, write_once → write-once, everything else → overwrite.
    """
    if artifact.merge_strategy is not None:
        return artifact.merge_strategy
    if artifact.write_once:
        return MergeStrategy.WRITE_ONCE
    if artifact.layer == OutputLayer.GLOBAL:
        return MergeStrategy.SENTINEL
    return MergeStrategy.OVERWRITE


@dataclass(frozen=True)
class ResolvedArtifact:
    """An artifact resolved against the real filesystem: target + action."""

    artifact: Artifact
    target: Path
    action: Action


def _layer_root(artifact: Artifact, project_root: Path, global_root: Path) -> Path:
    if artifact.layer == OutputLayer.PROJECT:
        return project_root / ".claude"
    if artifact.layer == OutputLayer.PROJECT_ROOT:
        return project_root
    return global_root


def _resolve_target(
    artifact: Artifact,
    strategy: MergeStrategy,
    project_root: Path,
    global_root: Path,
) -> Path:
    """Resolve an artifact to its absolute target Path (no writing).

    A sentinel-strategy CLAUDE.md is special: augment mode merges the managed
    block into a project's EXISTING CLAUDE.md rather than creating a second
    one. Precedence: a bespoke root ``./CLAUDE.md`` first, then
    ``.claude/CLAUDE.md``; if neither exists, a fresh ``.claude/CLAUDE.md``.

    Raises:
        ValueError: if the artifact's target_path attempts path traversal.
    """
    if (
        strategy == MergeStrategy.SENTINEL
        and artifact.layer in (OutputLayer.PROJECT, OutputLayer.PROJECT_ROOT)
        and artifact.target_path == "CLAUDE.md"
    ):
        root_claude = project_root / "CLAUDE.md"
        dot_claude = project_root / ".claude" / "CLAUDE.md"
        return (root_claude if root_claude.exists() else dot_claude).resolve()

    layer_root = _layer_root(artifact, project_root, global_root)
    target = (layer_root / artifact.target_path).resolve()
    if not str(target).startswith(str(layer_root.resolve())):
        raise ValueError(f"Path traversal detected: {artifact.target_path}")
    return target


def _action_for(strategy: MergeStrategy, target: Path) -> Action:
    exists = target.exists()
    if strategy in (MergeStrategy.WRITE_ONCE, MergeStrategy.SKIP_IF_EXISTS):
        return "skip-exists" if exists else "create"
    if strategy == MergeStrategy.SENTINEL:
        return "merge-managed-block" if exists else "create"
    return "overwrite" if exists else "create"


def resolve_plan(
    plan: GenerationPlan,
    project_root: Path,
    global_root: Path,
) -> list[ResolvedArtifact]:
    """Resolve every artifact to its target Path and the action a run would take.

    Single source of truth shared by ``Generator.execute()`` and the CLI's
    ``--dry-run``. Filesystem is read (existence checks) but never written.

    Raises:
        ValueError: if any artifact's target_path attempts path traversal.
    """
    resolved: list[ResolvedArtifact] = []
    for artifact in plan.artifacts:
        strategy = effective_merge_strategy(artifact)
        target = _resolve_target(artifact, strategy, project_root, global_root)
        resolved.append(ResolvedArtifact(artifact, target, _action_for(strategy, target)))
    return resolved


def resolve_plan_paths(
    plan: GenerationPlan,
    project_root: Path,
    global_root: Path,
) -> list[Path]:
    """Resolve every artifact in *plan* to its absolute target Path.

    Backward-compatible thin wrapper over :func:`resolve_plan`.

    Raises:
        ValueError: if any artifact's target_path attempts path traversal.
    """
    return [r.target for r in resolve_plan(plan, project_root, global_root)]


class Generator:
    """Executes a GenerationPlan by writing artifact files to disk.

    Each artifact's ``merge_strategy`` (explicit, or mapped from layer for
    back-compat) decides how it is written:

    - ``overwrite`` — replace unconditionally (generated machine config).
    - ``sentinel`` — create sentinel-wrapped when absent; otherwise merge the
      managed block in-place, byte-preserving all surrounding user content.
    - ``write_once`` — create when absent; never touch an existing target.
    - ``skip_if_exists`` — create when absent; leave existing files untouched.

    The strategy is derived solely from artifact metadata — the generator
    never inspects file contents to decide behavior.
    """

    def __init__(self, registry: TemplateRegistry) -> None:
        """Store the TemplateRegistry used for all template rendering.

        Args:
            registry: A configured TemplateRegistry instance.
        """
        self._registry = registry

    def execute(
        self,
        plan: GenerationPlan,
        project_root: Path,
        global_root: Path,
    ) -> list[Path]:
        """Write all artifacts in *plan* to disk and return the list of written paths.

        Skipped artifacts (``skip_if_exists``/``write_once`` whose target
        already exists) are not written and not included in the result.

        Args:
            plan: The GenerationPlan describing all artifacts to write.
            project_root: Root directory of the project. PROJECT-layer artifacts
                are written to ``project_root/.claude/``.
            global_root: Root directory for global Claude configuration. GLOBAL-layer
                artifacts are written here.

        Returns:
            List of absolute Paths that were written.

        Raises:
            ValueError: if any artifact's target_path attempts path traversal (contains ..).
        """
        written: list[Path] = []

        for resolved in resolve_plan(plan, project_root, global_root):
            # Existence-gated strategies short-circuit before any render/merge.
            if resolved.action == "skip-exists":
                continue

            artifact, target = resolved.artifact, resolved.target
            strategy = effective_merge_strategy(artifact)
            context = enrich_artifact_context(artifact, plan)
            rendered_content = self._registry.render(artifact.template_id, context)

            if strategy == MergeStrategy.SENTINEL:
                if target.exists():
                    existing = target.read_text(encoding="utf-8")
                    final_content = merge_sentinel_block(existing, rendered_content)
                else:
                    final_content = wrap_with_sentinel(rendered_content)
            else:
                final_content = rendered_content

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(final_content, encoding="utf-8")
            written.append(target)

        return written
