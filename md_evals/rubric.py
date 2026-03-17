"""Rubric system for structured skill scoring.

Provides Pydantic models for rubric configuration, validation logic,
and a loader with a resolution chain (CLI → CWD → home → built-in).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

# ============== Constants ==============

BUILTIN_DIMENSIONS: set[str] = frozenset(
    {"correctness", "completeness", "format", "adherence", "safety", "efficiency", "robustness"}
)

REQUIRED_GRADES: set[str] = {"A", "B", "C", "D"}
OPTIONAL_GRADES: set[str] = {"S"}
ALL_GRADES: list[str] = ["S", "A", "B", "C", "D"]

_WEIGHT_TOLERANCE: float = 0.001


# ============== Exceptions ==============


class RubricError(Exception):
    """Base exception for rubric operations."""


class RubricValidationError(RubricError):
    """Raised when rubric validation fails."""


class RubricNotFoundError(RubricError):
    """Raised when rubric file is not found."""


# ============== Pydantic Models ==============


class SecurityPattern(BaseModel):
    """A regex pattern used for pre-check security scanning.

    Attributes:
        pattern: A valid regular expression to match against file content.
        message: Human-readable description shown when the pattern matches.
        severity: Impact level — ``"error"``, ``"warning"``, or ``"info"``.
    """

    pattern: str
    message: str
    severity: str = "warning"


class PreCheckConfig(BaseModel):
    """Configuration for lightweight structural checks run before LLM scoring.

    Attributes:
        required_sections: Markdown headings that must be present.
        max_lines: Maximum allowed line count for the evaluated file.
        security_patterns: Regex patterns scanned against file content.
    """

    required_sections: list[str] = Field(
        default_factory=lambda: ["Description", "Rules", "Examples"],
    )
    max_lines: int = 400
    security_patterns: list[SecurityPattern] = Field(default_factory=list)


class DimensionConfig(BaseModel):
    """Configuration for a single scoring dimension.

    Attributes:
        weight: Relative weight in ``[0.0, 1.0]``.  All dimension weights
            must sum to 1.0 (±0.001 tolerance) across the rubric.
        description: Human-readable explanation of what the dimension measures.
    """

    weight: float
    description: str = ""


class RubricConfig(BaseModel):
    """Top-level rubric configuration.

    Validates structural invariants via a Pydantic ``model_validator``:

    * Dimension weights sum to 1.0 (±0.001).
    * Grade thresholds are strictly monotonically decreasing (S > A > B > C > D).
    * Each threshold is in the range (0.0, 1.0].
    * Grades A, B, C, D are required; S is optional.
    * Security patterns compile as valid regex.
    * At least one dimension is defined.
    * Version must be ``"1.0"``.
    * Custom dimensions with empty descriptions emit a warning.

    Attributes:
        version: Schema version — currently only ``"1.0"`` is supported.
        dimensions: Mapping of dimension name → :class:`DimensionConfig`.
        grade_thresholds: Mapping of grade letter → minimum score threshold.
        pre_check: Pre-check configuration for structural validation.
    """

    version: str = "1.0"
    dimensions: dict[str, DimensionConfig]
    grade_thresholds: dict[str, float]
    pre_check: PreCheckConfig = Field(default_factory=PreCheckConfig)

    @model_validator(mode="after")
    def _validate_rubric(self) -> "RubricConfig":
        """Enforce all rubric invariants after model construction."""
        self._check_version()
        self._check_dimensions()
        self._check_weights()
        self._check_grade_thresholds()
        self._check_security_patterns()
        self._warn_empty_custom_descriptions()
        return self

    # ── Private validation helpers ────────────────────────────────

    def _check_version(self) -> None:
        if self.version != "1.0":
            raise RubricValidationError(
                f"Unsupported rubric version '{self.version}' — only '1.0' is supported"
            )

    def _check_dimensions(self) -> None:
        if not self.dimensions:
            raise RubricValidationError("Rubric must define at least one dimension")

    def _check_weights(self) -> None:
        total = sum(d.weight for d in self.dimensions.values())
        if abs(total - 1.0) > _WEIGHT_TOLERANCE:
            raise RubricValidationError(
                f"Dimension weights must sum to 1.0 (got {total:.4f})"
            )

    def _check_grade_thresholds(self) -> None:
        keys = set(self.grade_thresholds.keys())

        # Required grades
        missing = REQUIRED_GRADES - keys
        if missing:
            raise RubricValidationError(
                f"Missing required grade thresholds: {', '.join(sorted(missing))}"
            )

        # Only valid grade letters allowed
        unknown = keys - REQUIRED_GRADES - OPTIONAL_GRADES
        if unknown:
            raise RubricValidationError(
                f"Unknown grade thresholds: {', '.join(sorted(unknown))}"
            )

        # Each threshold in (0.0, 1.0]
        for grade, value in self.grade_thresholds.items():
            if not (0.0 < value <= 1.0):
                raise RubricValidationError(
                    f"Grade threshold '{grade}' must be in (0.0, 1.0] (got {value})"
                )

        # Strict monotonic decrease following the canonical order S > A > B > C > D
        present = [g for g in ALL_GRADES if g in self.grade_thresholds]
        for i in range(len(present) - 1):
            higher = present[i]
            lower = present[i + 1]
            if self.grade_thresholds[higher] <= self.grade_thresholds[lower]:
                raise RubricValidationError(
                    f"Grade thresholds must be strictly decreasing: "
                    f"{higher}={self.grade_thresholds[higher]} "
                    f"must be > {lower}={self.grade_thresholds[lower]}"
                )

    def _check_security_patterns(self) -> None:
        for sp in self.pre_check.security_patterns:
            try:
                re.compile(sp.pattern)
            except re.error as exc:
                raise RubricValidationError(
                    f"Invalid regex in security pattern: '{sp.pattern}' — {exc}"
                ) from exc

    def _warn_empty_custom_descriptions(self) -> None:
        for name, dim in self.dimensions.items():
            if name not in BUILTIN_DIMENSIONS and not dim.description:
                logger.warning(
                    "Custom dimension '%s' has an empty description — "
                    "consider adding one for clarity",
                    name,
                )


# ============== Rubric Loader ==============


class RubricLoader:
    """Loads and resolves rubric configuration from YAML files.

    Resolution chain (first match wins):

    1. Explicit CLI path (``--rubric path/to/rubric.yaml``)
    2. ``rubric.yaml`` in the current working directory
    3. ``~/.md-evals/rubric.yaml`` (user-level default)
    4. Built-in default bundled with the package
    """

    BUILTIN_PATH: Path = Path(__file__).parent / "rubric_default.yaml"
    HOME_PATH: Path = Path.home() / ".md-evals" / "rubric.yaml"

    @classmethod
    def resolve(cls, cli_rubric: str | None = None) -> RubricConfig:
        """Resolve a rubric configuration using the resolution chain.

        Args:
            cli_rubric: Optional explicit path provided via CLI flag.

        Returns:
            A validated :class:`RubricConfig` instance.

        Raises:
            RubricNotFoundError: If the explicit CLI path does not exist.
            RubricValidationError: If the resolved file fails validation.
        """
        # 1. Explicit CLI path
        if cli_rubric is not None:
            logger.debug("Loading rubric from CLI flag: %s", cli_rubric)
            return cls.load(cli_rubric)

        # 2. CWD rubric.yaml
        cwd_path = Path.cwd() / "rubric.yaml"
        if cwd_path.is_file():
            logger.debug("Loading rubric from CWD: %s", cwd_path)
            return cls.load(str(cwd_path))

        # 3. Home directory
        if cls.HOME_PATH.is_file():
            logger.debug("Loading rubric from home: %s", cls.HOME_PATH)
            return cls.load(str(cls.HOME_PATH))

        # 4. Built-in default
        logger.debug("Loading built-in default rubric")
        return cls.load_default()

    @classmethod
    def load(cls, path: str) -> RubricConfig:
        """Load and validate a rubric from a YAML file.

        Args:
            path: Filesystem path to the rubric YAML file.

        Returns:
            A validated :class:`RubricConfig` instance.

        Raises:
            RubricNotFoundError: If *path* does not exist.
            RubricValidationError: If the file is empty, contains invalid
                YAML, or fails rubric validation rules.
        """
        file_path = Path(path)

        if not file_path.exists():
            raise RubricNotFoundError(f"Rubric file not found: {path}")

        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise RubricValidationError(
                f"Invalid YAML in rubric file '{path}': {exc}"
            ) from exc

        if data is None:
            raise RubricValidationError(f"Rubric file is empty: {path}")

        try:
            config = RubricConfig(**data)
        except RubricValidationError:
            # Re-raise our own validation errors directly
            raise
        except Exception as exc:
            raise RubricValidationError(
                f"Invalid rubric configuration in '{path}': {exc}"
            ) from exc

        return config

    @classmethod
    def load_default(cls) -> RubricConfig:
        """Load the built-in default rubric bundled with the package.

        Returns:
            A validated :class:`RubricConfig` with the default 7 dimensions.

        Raises:
            RubricNotFoundError: If the bundled default file is missing.
            RubricValidationError: If the bundled default fails validation
                (should never happen — indicates a packaging bug).
        """
        return cls.load(str(cls.BUILTIN_PATH))
