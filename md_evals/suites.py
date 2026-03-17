"""Eval suite runner for batch skill evaluation with CI integration.

Provides named groups of skills with per-skill grade thresholds. Suites
are defined in YAML and can be run from the CLI or CI pipelines with
meaningful exit codes:

- 0: All skills meet their grade thresholds
- 1: Configuration error (missing file, invalid YAML)
- 2: One or more skills failed to meet their threshold

Key types:

- :class:`SkillEntry` — A skill path with a minimum acceptable grade.
- :class:`SuiteConfig` — Named group of skills with shared settings.
- :class:`SuiteResult` — Aggregated pass/fail result from running a suite.
- :class:`SuiteLoader` — Parses and validates suite YAML files.
- :class:`SuiteRunner` — Executes a suite and checks thresholds.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from md_evals.scoring import GRADE_ORDER, EvalResult

logger = logging.getLogger(__name__)


# ─── Data Models ───


@dataclass
class SkillEntry:
    """A skill in an eval suite.

    Attributes:
        path: Filesystem path to the SKILL.md file.
        min_grade: Minimum acceptable grade (default "C").
    """

    path: str
    min_grade: str = "C"


@dataclass
class SuiteConfig:
    """Configuration for an eval suite.

    Attributes:
        name: Human-readable suite name.
        skills: List of skills to evaluate.
        pre_check: Pre-check policy — "required", "optional", or "skip".
        rubric: Optional rubric override path.
    """

    name: str = ""
    skills: list[SkillEntry] = field(default_factory=list)
    pre_check: str = "required"
    rubric: str | None = None


@dataclass
class SuiteResult:
    """Result from running an eval suite.

    Attributes:
        name: Suite name.
        passed: True if all skills met their thresholds.
        results: List of (path, EvalResult, meets_threshold) tuples.
        total_skills: Number of skills in the suite.
        passed_skills: Number that met their threshold.
        failed_skills: Number that failed their threshold.
    """

    name: str
    passed: bool
    results: list[tuple[str, EvalResult, bool]] = field(default_factory=list)
    total_skills: int = 0
    passed_skills: int = 0
    failed_skills: int = 0


# ─── Grade Comparison ───


def grade_meets_threshold(actual: str, minimum: str) -> bool:
    """Check if an actual grade meets or exceeds a minimum grade.

    Uses ``GRADE_ORDER`` (S, A, B, C, D, F) — lower index = better grade.

    Args:
        actual: The grade received (e.g. "B").
        minimum: The minimum acceptable grade (e.g. "C").

    Returns:
        True if actual is at least as good as minimum.
    """
    try:
        actual_idx = GRADE_ORDER.index(actual)
        min_idx = GRADE_ORDER.index(minimum)
    except ValueError:
        # Unknown grade — treat as failure
        return False
    return actual_idx <= min_idx


# ─── Suite Loader ───


class SuiteLoadError(Exception):
    """Raised when suite loading or validation fails."""


class SuiteLoader:
    """Load eval suite configurations from YAML files."""

    @classmethod
    def load(cls, path: str) -> SuiteConfig:
        """Load suite config from a YAML file.

        Args:
            path: Filesystem path to the suite YAML file.

        Returns:
            A validated SuiteConfig.

        Raises:
            SuiteLoadError: If the file is missing, invalid, or empty.
        """
        file_path = Path(path)

        if not file_path.exists():
            raise SuiteLoadError(f"Suite file not found: {path}")

        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise SuiteLoadError(
                f"Invalid YAML in suite file '{path}': {exc}"
            ) from exc

        if data is None:
            raise SuiteLoadError(f"Suite file is empty: {path}")

        return cls._parse(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SuiteConfig:
        """Build SuiteConfig from a raw dictionary.

        Args:
            data: Suite configuration dictionary.

        Returns:
            A validated SuiteConfig.

        Raises:
            SuiteLoadError: If the data is invalid.
        """
        return cls._parse(data)

    @classmethod
    def _parse(cls, data: dict[str, Any]) -> SuiteConfig:
        """Parse and validate suite configuration data.

        Args:
            data: Raw configuration dictionary.

        Returns:
            A validated SuiteConfig.

        Raises:
            SuiteLoadError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise SuiteLoadError("Suite config must be a YAML mapping")

        name = data.get("name", "")
        pre_check = data.get("pre_check", "required")
        rubric = data.get("rubric")

        if pre_check not in ("required", "optional", "skip"):
            raise SuiteLoadError(
                f"Invalid pre_check value: '{pre_check}'. "
                "Must be 'required', 'optional', or 'skip'."
            )

        raw_skills = data.get("skills", [])
        if not isinstance(raw_skills, list):
            raise SuiteLoadError("'skills' must be a list")

        skills: list[SkillEntry] = []
        for i, item in enumerate(raw_skills):
            if isinstance(item, str):
                skills.append(SkillEntry(path=item))
            elif isinstance(item, dict):
                path = item.get("path")
                if not path:
                    raise SuiteLoadError(
                        f"Skill entry {i} missing 'path' field"
                    )
                min_grade = item.get("min_grade", "C")
                if min_grade not in GRADE_ORDER:
                    raise SuiteLoadError(
                        f"Invalid min_grade '{min_grade}' for skill '{path}'. "
                        f"Must be one of: {', '.join(GRADE_ORDER)}"
                    )
                skills.append(SkillEntry(path=str(path), min_grade=str(min_grade)))
            else:
                raise SuiteLoadError(
                    f"Skill entry {i} must be a string or mapping, got {type(item).__name__}"
                )

        return SuiteConfig(
            name=name,
            skills=skills,
            pre_check=pre_check,
            rubric=rubric,
        )


# ─── Suite Runner ───


class SuiteRunner:
    """Run an eval suite and check grade thresholds.

    Args:
        config: Top-level EvalConfig (provides model/provider defaults).
        rubric: RubricConfig for grading.
        pipeline_config: Optional PipelineConfig override.
    """

    def __init__(
        self,
        config: Any,
        rubric: Any,
        pipeline_config: Any | None = None,
    ):
        self.config = config
        self.rubric = rubric
        self.pipeline_config = pipeline_config

    async def run(self, suite: SuiteConfig) -> SuiteResult:
        """Run all skills in the suite and check against thresholds.

        For each skill, runs the pipeline to get an EvalResult, then
        checks whether the overall grade meets the minimum threshold.

        Args:
            suite: The suite configuration to execute.

        Returns:
            A SuiteResult with pass/fail status for each skill.
        """
        from md_evals.pipeline.config import PipelineConfig
        from md_evals.pipeline.runner import PipelineRunner

        pipeline_config = self.pipeline_config or PipelineConfig()
        runner = PipelineRunner(
            config=self.config,
            rubric=self.rubric,
            pipeline_config=pipeline_config,
        )

        results: list[tuple[str, EvalResult, bool]] = []
        passed_count = 0
        failed_count = 0

        for skill in suite.skills:
            try:
                eval_result = await runner.run(skill.path)
                meets = grade_meets_threshold(
                    eval_result.overall_grade, skill.min_grade
                )
            except Exception as exc:
                logger.error(
                    "Failed to evaluate skill '%s': %s", skill.path, exc
                )
                # Create a failing result
                from md_evals.scoring import EvalMetadata

                eval_result = EvalResult(
                    skill_path=skill.path,
                    overall_grade="F",
                    overall_score=0.0,
                    dimensions=[],
                    pre_check=None,
                    metadata=EvalMetadata(model="error", provider="error"),
                )
                meets = False

            results.append((skill.path, eval_result, meets))
            if meets:
                passed_count += 1
            else:
                failed_count += 1

        all_passed = failed_count == 0

        return SuiteResult(
            name=suite.name,
            passed=all_passed,
            results=results,
            total_skills=len(suite.skills),
            passed_skills=passed_count,
            failed_skills=failed_count,
        )

    def run_sync(self, suite: SuiteConfig) -> SuiteResult:
        """Sync wrapper for :meth:`run`.

        Args:
            suite: The suite configuration to execute.

        Returns:
            A SuiteResult with pass/fail status for each skill.
        """
        return asyncio.run(self.run(suite))
