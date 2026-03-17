"""Scoring engine for md-evals: data foundation and grade calculation.

Phase A — Data Foundation:
  Defines the core dataclasses for evaluation results: DimensionScore,
  EvalMetadata, and EvalResult. These are the canonical output types that
  flow from the scoring pipeline to the reporter and JSON serializer.

Phase D — Grade Calculation:
  Pure functions for mapping numeric scores (0.0–1.0) to letter grades
  (S/A/B/C/D/F), computing weighted averages across rubric dimensions,
  and building typed DimensionScore lists from raw LLM output.

All dataclasses use stdlib @dataclass (not Pydantic) per ADR-03,
since these are internal computation objects, not API models.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from md_evals.metrics import CostMetrics, ContextMetrics

if TYPE_CHECKING:
    from md_evals.precheck import PreCheckResult


# ─── Constants ───


BUILTIN_DIMENSIONS: frozenset[str] = frozenset({
    "correctness",
    "completeness",
    "format",
    "adherence",
    "safety",
    "efficiency",
    "robustness",
})
"""Built-in rubric dimensions recognized by the scoring engine.

Rubrics may use any subset of these, plus custom dimensions. The set is
used for validation and documentation, not as a hard constraint.
"""

GRADE_ORDER: tuple[str, ...] = ("S", "A", "B", "C", "D", "F")
"""Letter grades in descending order of quality.

S (Superior) is optional and only awarded when thresholds include an "S" key.
F is the implicit floor — scores below the D threshold receive F.
"""


# ─── Phase A: Data Foundation ───


@dataclass(frozen=True)
class DimensionScore:
    """Score for a single rubric dimension.

    Immutable value object produced by the scoring pipeline. Each dimension
    carries its own weight (from the rubric) and individual letter grade.

    Attributes:
        dimension: Dimension name (e.g. "correctness", "completeness").
        score: Numeric score in [0.0, 1.0].
        weight: Rubric weight for this dimension; all weights sum to 1.0.
        grade: Letter grade (S/A/B/C/D/F) derived from score + thresholds.
        evidence: Supporting evidence strings (populated in Phase 3).
    """

    dimension: str
    score: float
    weight: float
    grade: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class EvalMetadata:
    """Execution metadata for an evaluation run.

    Mutable because timing fields are set incrementally as the pipeline
    executes (pre-check, LLM call, post-processing).

    Attributes:
        model: Model identifier (e.g. "gpt-4o", "claude-3-sonnet").
        provider: Provider name (e.g. "github-models", "openai").
        cost_metrics: Token cost data, or None if unavailable.
        context_metrics: Context window utilization, or None if unavailable.
        total_duration_ms: Wall-clock time for the full evaluation.
        pre_check_duration_ms: Time spent in pre-check validation.
        llm_duration_ms: Time spent waiting for LLM responses.
        timestamp: ISO 8601 timestamp of evaluation start.
    """

    model: str
    provider: str
    cost_metrics: CostMetrics | None = None
    context_metrics: ContextMetrics | None = None
    total_duration_ms: int = 0
    pre_check_duration_ms: int = 0
    llm_duration_ms: int = 0
    timestamp: str = ""


@dataclass
class EvalResult:
    """Complete result of evaluating a skill file.

    Top-level container that flows from the scoring engine to the reporter.
    Mutable because fields like ``execution_results`` may be attached after
    initial construction.

    Attributes:
        skill_path: Path to the evaluated skill/markdown file.
        overall_grade: Aggregate letter grade (S/A/B/C/D/F).
        overall_score: Weighted average score in [0.0, 1.0].
        dimensions: Per-dimension scores with grades and weights.
        pre_check: Pre-check validation result, or None if skipped.
        metadata: Execution metadata (model, timing, costs).
        execution_results: Raw LLM execution results (optional, for debugging).
    """

    skill_path: str
    overall_grade: str
    overall_score: float
    dimensions: list[DimensionScore]
    pre_check: PreCheckResult | None
    metadata: EvalMetadata
    execution_results: list[Any] | None = None


# ─── Phase D: Grade Calculation ───


def score_to_grade(score: float, thresholds: dict[str, float]) -> str:
    """Map a numeric score to a letter grade using configurable thresholds.

    Pure function with no side effects. The score is clamped to [0.0, 1.0]
    before comparison. Thresholds are checked in descending order of quality:
    S (if present), then A, B, C, D. Any score below the D threshold yields F.

    Example thresholds::

        {"S": 0.97, "A": 0.90, "B": 0.75, "C": 0.60, "D": 0.40}

    Args:
        score: Numeric score, ideally in [0.0, 1.0]. Values outside this
               range are clamped.
        thresholds: Mapping of grade letter to minimum score required.
                    Must contain at least "A", "B", "C", "D". "S" is optional.

    Returns:
        Letter grade string: one of "S", "A", "B", "C", "D", or "F".
    """
    clamped = max(0.0, min(1.0, score))

    # Check grades in descending quality order
    for grade in GRADE_ORDER[:-1]:  # S, A, B, C, D (skip F — it's the floor)
        if grade in thresholds and clamped >= thresholds[grade]:
            return grade

    return "F"


def calculate_overall_grade(
    dimensions: list[DimensionScore],
    thresholds: dict[str, float],
) -> tuple[float, str]:
    """Compute a weighted average score and overall letter grade.

    Pure function with no I/O. Weights are taken from each DimensionScore
    (sourced from the rubric). The weighted average is mapped to a letter
    grade via ``score_to_grade``.

    Args:
        dimensions: Non-empty list of scored dimensions with weights.
        thresholds: Grade threshold mapping (see ``score_to_grade``).

    Returns:
        Tuple of (overall_score, grade) where overall_score is in [0.0, 1.0].

    Raises:
        ValueError: If ``dimensions`` is empty.
    """
    if not dimensions:
        raise ValueError(
            "Cannot calculate overall grade from an empty dimensions list."
        )

    total_weight = sum(d.weight for d in dimensions)

    if total_weight == 0.0:
        # All weights are zero — degenerate case, return F
        return 0.0, "F"

    overall_score = sum(d.score * d.weight for d in dimensions) / total_weight
    grade = score_to_grade(overall_score, thresholds)

    return overall_score, grade


def build_dimension_scores(
    scores: dict[str, float],
    rubric_dimensions: dict[str, Any],
    thresholds: dict[str, float],
) -> list[DimensionScore]:
    """Build a list of DimensionScore from raw scores and rubric configuration.

    For each dimension defined in ``rubric_dimensions``, looks up the
    corresponding raw score, clamps it to [0.0, 1.0], computes an individual
    letter grade, and produces a frozen DimensionScore.

    Missing scores default to 0.0 (the LLM failed to produce a value for
    that dimension).

    The ``rubric_dimensions`` values must be objects (or dicts) with a
    ``weight`` attribute or key.

    Args:
        scores: Raw dimension scores from the LLM, keyed by dimension name.
        rubric_dimensions: Rubric configuration keyed by dimension name.
                           Each value must expose a ``weight`` (float).
        thresholds: Grade threshold mapping (see ``score_to_grade``).

    Returns:
        List of DimensionScore, one per rubric dimension, in iteration order.
    """
    result: list[DimensionScore] = []

    for dim_name, dim_config in rubric_dimensions.items():
        # Extract weight — support both object attribute and dict key
        if isinstance(dim_config, dict):
            weight = float(dim_config.get("weight", 0.0))
        else:
            weight = float(getattr(dim_config, "weight", 0.0))

        raw_score = scores.get(dim_name, 0.0)
        clamped_score = max(0.0, min(1.0, float(raw_score)))
        grade = score_to_grade(clamped_score, thresholds)

        result.append(
            DimensionScore(
                dimension=dim_name,
                score=clamped_score,
                weight=weight,
                grade=grade,
            )
        )

    return result


# ─── Serialization ───


def eval_result_to_dict(result: EvalResult) -> dict[str, Any]:
    """Serialize an EvalResult to a plain dict suitable for JSON output.

    Recursively converts dataclasses via ``dataclasses.asdict``, handling
    the optional ``pre_check`` and ``execution_results`` fields gracefully.

    Args:
        result: The EvalResult to serialize.

    Returns:
        Dict with string keys, JSON-serializable values.
    """
    dimensions_list = [asdict(d) for d in result.dimensions]

    metadata_dict = asdict(result.metadata)
    # Remove None metric blocks for cleaner JSON output
    if result.metadata.cost_metrics is None:
        metadata_dict.pop("cost_metrics", None)
    if result.metadata.context_metrics is None:
        metadata_dict.pop("context_metrics", None)

    pre_check_dict: dict[str, Any] | None = None
    if result.pre_check is not None:
        try:
            pre_check_dict = asdict(result.pre_check)
        except TypeError:
            # PreCheckResult may not be a dataclass in all cases
            pre_check_dict = (
                result.pre_check.__dict__
                if hasattr(result.pre_check, "__dict__")
                else None
            )

    return {
        "skill_path": result.skill_path,
        "overall_grade": result.overall_grade,
        "overall_score": round(result.overall_score, 4),
        "dimensions": dimensions_list,
        "pre_check": pre_check_dict,
        "metadata": metadata_dict,
    }
