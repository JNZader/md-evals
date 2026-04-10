"""Evaluate plugin directories following the agentskills.io structure.

A plugin directory contains:

- ``plugin.json`` — Manifest with name, description, version, and
  lists of skill/command paths.
- ``skills/`` — Directory containing SKILL.md files.
- ``commands/`` — Optional directory containing command definitions.

Key types:

- :class:`PluginManifest` — Parsed plugin.json manifest.
- :class:`PluginEvalResult` — Aggregate evaluation result for a plugin.
- :class:`PluginEvaluator` — Discovers skills and coordinates evaluation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_evals.scoring import EvalResult

logger = logging.getLogger(__name__)


# ─── Data Models ───


@dataclass
class PluginManifest:
    """Parsed plugin.json manifest.

    Attributes:
        name: Plugin display name.
        description: Short plugin description.
        version: Semantic version string.
        skills: List of skill file paths (relative to plugin root).
        commands: List of command file paths (relative to plugin root).
    """

    name: str = ""
    description: str = ""
    version: str = ""
    skills: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)


@dataclass
class PluginEvalResult:
    """Result from evaluating a plugin directory.

    Attributes:
        plugin_name: Name from the manifest (or directory name).
        manifest_valid: Whether plugin.json was found and valid.
        skill_results: List of per-skill EvalResult objects.
        aggregate_grade: Overall grade across all skills.
        aggregate_score: Weighted average score across all skills.
    """

    plugin_name: str
    manifest_valid: bool
    skill_results: list[EvalResult] = field(default_factory=list)
    aggregate_grade: str = "F"
    aggregate_score: float = 0.0


# ─── Exceptions ───


class PluginError(Exception):
    """Raised when plugin loading or evaluation fails."""


# ─── Plugin Evaluator ───


class PluginEvaluator:
    """Evaluate a plugin directory.

    Discovers SKILL.md files, loads the manifest, and coordinates
    evaluation of all skills.

    Args:
        config: Top-level EvalConfig (provides model/provider defaults).
        rubric: RubricConfig for grading.
        pipeline_config: Optional PipelineConfig override.
    """

    def __init__(
        self,
        config: Any = None,
        rubric: Any = None,
        pipeline_config: Any = None,
    ):
        self.config = config
        self.rubric = rubric
        self.pipeline_config = pipeline_config

    @classmethod
    def discover_skills(cls, plugin_path: str) -> list[str]:
        """Find all SKILL.md files in a plugin directory.

        Searches in this order:

        1. Paths listed in ``plugin.json`` (if it exists).
        2. ``skills/`` subdirectory — any ``SKILL.md`` or ``*.skill.md``.
        3. ``commands/`` subdirectory — any ``SKILL.md`` files.
        4. Root-level ``SKILL.md``.

        Args:
            plugin_path: Path to the plugin directory.

        Returns:
            List of absolute paths to discovered skill files.
        """
        root = Path(plugin_path).resolve()
        found: list[str] = []
        seen: set[str] = set()

        def _add(p: Path) -> None:
            resolved = str(p.resolve())
            if resolved not in seen and p.is_file():
                seen.add(resolved)
                found.append(resolved)

        # 1. From manifest
        manifest_path = root / "plugin.json"
        if manifest_path.is_file():
            try:
                manifest = cls.load_manifest(plugin_path)
                for skill_rel in manifest.skills:
                    skill_p = root / skill_rel
                    _add(skill_p)
            except PluginError:
                pass  # Fall through to discovery

        # 2. skills/ directory
        skills_dir = root / "skills"
        if skills_dir.is_dir():
            for f in sorted(skills_dir.rglob("SKILL.md")):
                _add(f)
            for f in sorted(skills_dir.rglob("*.skill.md")):
                _add(f)

        # 3. commands/ directory
        commands_dir = root / "commands"
        if commands_dir.is_dir():
            for f in sorted(commands_dir.rglob("SKILL.md")):
                _add(f)

        # 4. Root SKILL.md
        root_skill = root / "SKILL.md"
        _add(root_skill)

        return found

    @classmethod
    def load_manifest(cls, plugin_path: str) -> PluginManifest:
        """Load and parse plugin.json from a plugin directory.

        Args:
            plugin_path: Path to the plugin directory.

        Returns:
            A PluginManifest with parsed fields.

        Raises:
            PluginError: If plugin.json is missing or invalid.
        """
        manifest_path = Path(plugin_path).resolve() / "plugin.json"

        if not manifest_path.is_file():
            raise PluginError(
                f"plugin.json not found in '{plugin_path}'"
            )

        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise PluginError(
                f"Failed to parse plugin.json in '{plugin_path}': {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise PluginError(
                f"plugin.json must be a JSON object, got {type(data).__name__}"
            )

        return PluginManifest(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            version=str(data.get("version", "")),
            skills=[str(s) for s in data.get("skills", [])],
            commands=[str(c) for c in data.get("commands", [])],
        )

    async def evaluate(self, plugin_path: str) -> PluginEvalResult:
        """Evaluate all skills in a plugin directory.

        Discovers skill files, evaluates each using the pipeline,
        and computes an aggregate grade.

        Args:
            plugin_path: Path to the plugin directory.

        Returns:
            A PluginEvalResult with per-skill results and aggregate grade.
        """
        root = Path(plugin_path).resolve()

        # Load manifest
        manifest_valid = False
        plugin_name = root.name
        try:
            manifest = self.load_manifest(plugin_path)
            manifest_valid = True
            plugin_name = manifest.name or root.name
        except PluginError as exc:
            logger.warning("No valid manifest: %s", exc)

        # Discover skills
        skill_paths = self.discover_skills(plugin_path)

        if not skill_paths:
            return PluginEvalResult(
                plugin_name=plugin_name,
                manifest_valid=manifest_valid,
                skill_results=[],
                aggregate_grade="F",
                aggregate_score=0.0,
            )

        # Evaluate each skill
        from md_evals.pipeline.config import PipelineConfig
        from md_evals.pipeline.runner import PipelineRunner
        from md_evals.scoring import EvalMetadata

        pipeline_config = self.pipeline_config or PipelineConfig()
        runner = PipelineRunner(
            config=self.config,
            rubric=self.rubric,
            pipeline_config=pipeline_config,
        )

        results: list[EvalResult] = []
        for skill in skill_paths:
            try:
                result = await runner.run(skill)
                results.append(result)
            except Exception as exc:
                logger.error("Failed to evaluate '%s': %s", skill, exc)
                results.append(
                    EvalResult(
                        skill_path=skill,
                        overall_grade="F",
                        overall_score=0.0,
                        dimensions=[],
                        pre_check=None,
                        metadata=EvalMetadata(model="error", provider="error"),
                    )
                )

        # Aggregate
        agg_score, agg_grade = self._aggregate(results)

        return PluginEvalResult(
            plugin_name=plugin_name,
            manifest_valid=manifest_valid,
            skill_results=results,
            aggregate_grade=agg_grade,
            aggregate_score=agg_score,
        )

    def evaluate_sync(self, plugin_path: str) -> PluginEvalResult:
        """Sync wrapper for :meth:`evaluate`.

        Args:
            plugin_path: Path to the plugin directory.

        Returns:
            A PluginEvalResult.
        """
        return asyncio.run(self.evaluate(plugin_path))

    @staticmethod
    def _aggregate(results: list[EvalResult]) -> tuple[float, str]:
        """Compute aggregate score and grade from skill results.

        Simple mean of overall_scores, then mapped to grade.

        Args:
            results: List of per-skill EvalResult objects.

        Returns:
            Tuple of (avg_score, grade).
        """
        if not results:
            return 0.0, "F"

        avg = sum(r.overall_score for r in results) / len(results)

        # Use simple thresholds matching the default rubric
        thresholds = {"S": 0.95, "A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30}
        from md_evals.scoring import score_to_grade

        grade = score_to_grade(avg, thresholds)
        return round(avg, 4), grade
