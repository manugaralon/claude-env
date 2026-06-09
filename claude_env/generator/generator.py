"""Generator — executes a GenerationPlan by writing all artifacts to disk.

This is the core I/O layer that turns a GenerationPlan (data) into files on
disk. It handles PROJECT-layer files (plain overwrite under project_root/.claude/)
and GLOBAL-layer files (sentinel wrap/merge under global_root/).
"""
from __future__ import annotations

from pathlib import Path

from claude_env.generator.content_catalogue import enrich_artifact_context
from claude_env.generator.sentinel import merge_sentinel_block, wrap_with_sentinel
from claude_env.models.generation_plan import GenerationPlan, OutputLayer
from claude_env.templates.registry import TemplateRegistry


def resolve_plan_paths(
    plan: GenerationPlan,
    project_root: Path,
    global_root: Path,
) -> list[Path]:
    """Resolve every artifact in *plan* to its absolute target Path without writing.

    Single source of truth for path resolution — used by Generator.execute()
    and by the CLI's --dry-run mode.

    Raises:
        ValueError: if any artifact's target_path attempts path traversal.
    """
    paths: list[Path] = []
    for artifact in plan.artifacts:
        if artifact.layer == OutputLayer.PROJECT:
            layer_root = project_root / ".claude"
        elif artifact.layer == OutputLayer.PROJECT_ROOT:
            layer_root = project_root
        else:
            layer_root = global_root
        target = (layer_root / artifact.target_path).resolve()
        if not str(target).startswith(str(layer_root.resolve())):
            raise ValueError(f"Path traversal detected: {artifact.target_path}")
        paths.append(target)
    return paths


class Generator:
    """Executes a GenerationPlan by writing artifact files to disk.

    PROJECT-layer artifacts are written under ``project_root/.claude/`` and
    always overwritten unconditionally (no sentinel involvement).

    GLOBAL-layer artifacts are written under ``global_root/`` with sentinel
    management: new files are created via ``wrap_with_sentinel`` so that the
    managed block is present from the very first write; existing files are
    updated via ``merge_sentinel_block`` which replaces the managed block
    in-place and preserves surrounding user content.

    The layer decision is based solely on ``artifact.layer`` — the generator
    never inspects file contents to determine behavior.
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

        resolved = resolve_plan_paths(plan, project_root, global_root)
        for artifact, target in zip(plan.artifacts, resolved, strict=True):
            # Write-once: existence check FIRST, before any render/merge/sentinel.
            # If the artifact opts in and the target exists, leave it untouched
            # (user-owned content, e.g. CONSTITUTION.md). Not added to `written`.
            if artifact.write_once and target.exists():
                continue
            context = enrich_artifact_context(artifact, plan)
            rendered_content = self._registry.render(artifact.template_id, context)

            if artifact.layer == OutputLayer.GLOBAL:
                if target.exists():
                    existing = target.read_text(encoding="utf-8")
                    final_content = merge_sentinel_block(existing, rendered_content)
                else:
                    final_content = wrap_with_sentinel(rendered_content)
            else:
                # PROJECT or PROJECT_ROOT — plain overwrite, no sentinel
                final_content = rendered_content

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(final_content, encoding="utf-8")
            written.append(target)

        return written
