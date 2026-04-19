"""Generator — executes a GenerationPlan by writing all artifacts to disk.

This is the core I/O layer that turns a GenerationPlan (data) into files on
disk. It handles PROJECT-layer files (plain overwrite under project_root/.claude/)
and GLOBAL-layer files (sentinel wrap/merge under global_root/).
"""
from __future__ import annotations

from pathlib import Path

from claude_env.generator.content_catalogue import enrich_artifact_context
from claude_env.generator.sentinel import merge_sentinel_block, wrap_with_sentinel
from claude_env.models.generation_plan import Artifact, GenerationPlan, OutputLayer
from claude_env.templates.registry import TemplateRegistry


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

        for artifact in plan.artifacts:
            target = self._resolve_path(artifact, project_root, global_root)
            context = enrich_artifact_context(artifact, plan)
            rendered_content = self._registry.render(artifact.template_id, context)

            if artifact.layer == OutputLayer.GLOBAL:
                if target.exists():
                    existing = target.read_text(encoding="utf-8")
                    final_content = merge_sentinel_block(existing, rendered_content)
                else:
                    final_content = wrap_with_sentinel(rendered_content)
            else:
                # OutputLayer.PROJECT — plain overwrite, no sentinel
                final_content = rendered_content

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(final_content, encoding="utf-8")
            written.append(target)

        return written

    def _resolve_path(
        self,
        artifact: Artifact,
        project_root: Path,
        global_root: Path,
    ) -> Path:
        """Resolve an artifact's target_path to an absolute filesystem path.

        PROJECT-layer artifacts resolve under ``project_root/.claude/``.
        GLOBAL-layer artifacts resolve under ``global_root/``.

        Args:
            artifact: The artifact whose path to resolve.
            project_root: Project root directory.
            global_root: Global configuration root directory.

        Returns:
            Absolute resolved Path.

        Raises:
            ValueError: if target_path attempts path traversal outside the layer root.
        """
        if artifact.layer == OutputLayer.PROJECT:
            layer_root = project_root / ".claude"
        else:
            layer_root = global_root

        target = (layer_root / artifact.target_path).resolve()

        if not str(target).startswith(str(layer_root.resolve())):
            raise ValueError(f"Path traversal detected: {artifact.target_path}")

        return target
