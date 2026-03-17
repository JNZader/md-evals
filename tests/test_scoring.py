"""Comprehensive unit tests for md_evals.scoring module.

Tests cover all public types and functions:
  - DimensionScore, EvalMetadata, EvalResult (dataclass contracts)
  - score_to_grade (boundary values, clamping, S-grade omission)
  - calculate_overall_grade (weighted average, edge cases)
  - build_dimension_scores (raw → typed, defaults, clamping)
  - eval_result_to_dict (serialization, None handling)
  - Property-based tests via Hypothesis
  - Thread-safety smoke test
"""

from __future__ import annotations

import dataclasses
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st

from md_evals.metrics import CostMetrics, ContextMetrics
from md_evals.precheck import PreCheckResult
from md_evals.scoring import (
    BUILTIN_DIMENSIONS,
    GRADE_ORDER,
    DimensionScore,
    EvalMetadata,
    EvalResult,
    build_dimension_scores,
    calculate_overall_grade,
    eval_result_to_dict,
    score_to_grade,
)


# ============================================================================
# Constants: shared thresholds used across many tests
# ============================================================================

DEFAULT_THRESHOLDS: dict[str, float] = {
    "S": 0.95,
    "A": 0.85,
    "B": 0.70,
    "C": 0.50,
    "D": 0.30,
}

NO_S_THRESHOLDS: dict[str, float] = {
    "A": 0.85,
    "B": 0.70,
    "C": 0.50,
    "D": 0.30,
}


# ============================================================================
# 1. DimensionScore dataclass tests
# ============================================================================


def test_dimension_score_construction():
    """DimensionScore can be created with all required fields."""
    ds = DimensionScore(
        dimension="correctness",
        score=0.90,
        weight=0.25,
        grade="A",
        evidence=["Good answer"],
    )
    assert ds.dimension == "correctness"
    assert ds.score == 0.90
    assert ds.weight == 0.25
    assert ds.grade == "A"
    assert ds.evidence == ["Good answer"]


def test_dimension_score_evidence_defaults_to_empty_list():
    """Evidence defaults to an empty list, not None."""
    ds = DimensionScore(dimension="safety", score=1.0, weight=0.10, grade="S")
    assert ds.evidence == []
    assert isinstance(ds.evidence, list)


def test_dimension_score_frozen_immutability():
    """Setting a field on a frozen DimensionScore raises an error."""
    ds = DimensionScore(dimension="format", score=0.80, weight=0.15, grade="B")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        ds.score = 0.99  # type: ignore[misc]


def test_dimension_score_is_stdlib_dataclass():
    """DimensionScore is a stdlib dataclass, NOT Pydantic (ADR-03)."""
    assert dataclasses.is_dataclass(DimensionScore)
    # Must not have Pydantic's model_fields
    assert not hasattr(DimensionScore, "model_fields")
    assert not hasattr(DimensionScore, "__pydantic_model__")


# ============================================================================
# 2. EvalMetadata tests
# ============================================================================


def test_eval_metadata_construction_defaults():
    """EvalMetadata can be created with only required fields; defaults are sane."""
    meta = EvalMetadata(model="gpt-4o", provider="openai")
    assert meta.model == "gpt-4o"
    assert meta.provider == "openai"
    assert meta.cost_metrics is None
    assert meta.context_metrics is None
    assert meta.total_duration_ms == 0
    assert meta.pre_check_duration_ms == 0
    assert meta.llm_duration_ms == 0
    assert meta.timestamp == ""


def test_eval_metadata_with_metrics():
    """EvalMetadata correctly references CostMetrics and ContextMetrics."""
    cost = CostMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    ctx = ContextMetrics(prompt_tokens_used=100)
    meta = EvalMetadata(
        model="claude-3-sonnet",
        provider="anthropic",
        cost_metrics=cost,
        context_metrics=ctx,
        total_duration_ms=5000,
        timestamp="2026-03-17T10:00:00Z",
    )
    assert meta.cost_metrics is cost
    assert meta.context_metrics is ctx
    assert meta.total_duration_ms == 5000


def test_eval_metadata_is_mutable():
    """EvalMetadata is mutable (not frozen) for incremental field setting."""
    meta = EvalMetadata(model="gpt-4o", provider="openai")
    meta.total_duration_ms = 9999
    assert meta.total_duration_ms == 9999


# ============================================================================
# 3. EvalResult tests
# ============================================================================


def test_eval_result_construction():
    """EvalResult can be created with all fields."""
    dims = [
        DimensionScore(dimension="correctness", score=0.9, weight=0.5, grade="A"),
        DimensionScore(dimension="completeness", score=0.8, weight=0.5, grade="B"),
    ]
    meta = EvalMetadata(model="gpt-4o", provider="openai")
    pre = PreCheckResult(passed=True, checks_run=5, duration_ms=120)

    result = EvalResult(
        skill_path="/path/to/skill.md",
        overall_grade="A",
        overall_score=0.85,
        dimensions=dims,
        pre_check=pre,
        metadata=meta,
    )
    assert result.skill_path == "/path/to/skill.md"
    assert result.overall_grade == "A"
    assert result.overall_score == 0.85
    assert len(result.dimensions) == 2
    assert result.pre_check is pre
    assert result.metadata is meta


def test_eval_result_execution_results_defaults_to_none():
    """execution_results defaults to None when not provided."""
    meta = EvalMetadata(model="gpt-4o", provider="openai")
    result = EvalResult(
        skill_path="s.md",
        overall_grade="B",
        overall_score=0.75,
        dimensions=[],
        pre_check=None,
        metadata=meta,
    )
    assert result.execution_results is None


def test_eval_result_pre_check_can_be_none():
    """pre_check can be explicitly set to None (skipped)."""
    meta = EvalMetadata(model="gpt-4o", provider="openai")
    result = EvalResult(
        skill_path="s.md",
        overall_grade="F",
        overall_score=0.0,
        dimensions=[],
        pre_check=None,
        metadata=meta,
    )
    assert result.pre_check is None


# ============================================================================
# 4. score_to_grade tests — ALL 12 boundary values
# ============================================================================


@pytest.mark.parametrize(
    "score, expected_grade",
    [
        # F range: [0.0, 0.30)
        (0.0, "F"),
        (0.29, "F"),
        # D range: [0.30, 0.50)
        (0.30, "D"),
        (0.49, "D"),
        # C range: [0.50, 0.70)
        (0.50, "C"),
        (0.69, "C"),
        # B range: [0.70, 0.85)
        (0.70, "B"),
        (0.84, "B"),
        # A range: [0.85, 0.95)
        (0.85, "A"),
        (0.94, "A"),
        # S range: [0.95, 1.0]
        (0.95, "S"),
        (1.0, "S"),
    ],
    ids=[
        "0.00→F", "0.29→F",
        "0.30→D", "0.49→D",
        "0.50→C", "0.69→C",
        "0.70→B", "0.84→B",
        "0.85→A", "0.94→A",
        "0.95→S", "1.00→S",
    ],
)
def test_score_to_grade_boundary(score: float, expected_grade: str):
    """Verify all 12 boundary values for score → grade mapping."""
    assert score_to_grade(score, DEFAULT_THRESHOLDS) == expected_grade


def test_score_to_grade_clamping_below_zero():
    """Scores below 0.0 are clamped — negative score yields F."""
    assert score_to_grade(-0.1, DEFAULT_THRESHOLDS) == "F"


def test_score_to_grade_clamping_above_one():
    """Scores above 1.0 are clamped — 1.5 still hits S threshold."""
    assert score_to_grade(1.5, DEFAULT_THRESHOLDS) == "S"


def test_score_to_grade_no_s_threshold():
    """When S is not in thresholds, high scores get A instead."""
    assert score_to_grade(0.99, NO_S_THRESHOLDS) == "A"


def test_score_to_grade_exact_threshold_boundaries():
    """Scores exactly at threshold boundaries belong to the higher grade."""
    # At exactly 0.95 → S (not A)
    assert score_to_grade(0.95, DEFAULT_THRESHOLDS) == "S"
    # At exactly 0.85 → A (not B)
    assert score_to_grade(0.85, DEFAULT_THRESHOLDS) == "A"
    # At exactly 0.70 → B (not C)
    assert score_to_grade(0.70, DEFAULT_THRESHOLDS) == "B"


# ============================================================================
# 5. calculate_overall_grade tests
# ============================================================================


def test_calculate_overall_grade_spec_example():
    """Weighted average from spec: 0.8275 → B.

    correctness=0.90(25%), completeness=0.85(20%), format=0.80(15%),
    adherence=0.75(15%), safety=0.95(10%), efficiency=0.70(10%),
    robustness=0.60(5%)

    Weighted sum = 0.90*0.25 + 0.85*0.20 + 0.80*0.15 + 0.75*0.15
                 + 0.95*0.10 + 0.70*0.10 + 0.60*0.05
                 = 0.225 + 0.170 + 0.120 + 0.1125 + 0.095 + 0.070 + 0.030
                 = 0.8225
    """
    dims = [
        DimensionScore(dimension="correctness", score=0.90, weight=0.25, grade="A"),
        DimensionScore(dimension="completeness", score=0.85, weight=0.20, grade="A"),
        DimensionScore(dimension="format", score=0.80, weight=0.15, grade="B"),
        DimensionScore(dimension="adherence", score=0.75, weight=0.15, grade="B"),
        DimensionScore(dimension="safety", score=0.95, weight=0.10, grade="S"),
        DimensionScore(dimension="efficiency", score=0.70, weight=0.10, grade="B"),
        DimensionScore(dimension="robustness", score=0.60, weight=0.05, grade="C"),
    ]
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)

    # Weighted average: (0.225+0.170+0.120+0.1125+0.095+0.070+0.030) / 1.0
    assert overall_score == pytest.approx(0.8225, abs=1e-4)
    assert grade == "B"


def test_calculate_overall_grade_all_zeros():
    """All scores zero → overall 0.0 → F."""
    dims = [
        DimensionScore(dimension="a", score=0.0, weight=0.50, grade="F"),
        DimensionScore(dimension="b", score=0.0, weight=0.50, grade="F"),
    ]
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
    assert overall_score == pytest.approx(0.0)
    assert grade == "F"


def test_calculate_overall_grade_all_ones():
    """All scores 1.0 → overall 1.0 → S."""
    dims = [
        DimensionScore(dimension="a", score=1.0, weight=0.50, grade="S"),
        DimensionScore(dimension="b", score=1.0, weight=0.50, grade="S"),
    ]
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
    assert overall_score == pytest.approx(1.0)
    assert grade == "S"


def test_calculate_overall_grade_empty_raises():
    """Empty dimensions list raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        calculate_overall_grade([], DEFAULT_THRESHOLDS)


def test_calculate_overall_grade_single_dimension():
    """Single dimension: overall score equals that dimension's score."""
    dims = [
        DimensionScore(dimension="only", score=0.72, weight=1.0, grade="B"),
    ]
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
    assert overall_score == pytest.approx(0.72)
    assert grade == "B"


def test_calculate_overall_grade_zero_weights():
    """All weights zero → degenerate case, returns (0.0, F)."""
    dims = [
        DimensionScore(dimension="a", score=0.90, weight=0.0, grade="A"),
        DimensionScore(dimension="b", score=0.95, weight=0.0, grade="S"),
    ]
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
    assert overall_score == 0.0
    assert grade == "F"


def test_calculate_overall_grade_unnormalized_weights():
    """Weights that don't sum to 1.0 are normalized by total_weight."""
    dims = [
        DimensionScore(dimension="a", score=0.80, weight=2.0, grade="B"),
        DimensionScore(dimension="b", score=0.60, weight=2.0, grade="C"),
    ]
    # weighted avg = (0.80*2 + 0.60*2) / 4 = 2.80 / 4 = 0.70
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
    assert overall_score == pytest.approx(0.70)
    assert grade == "B"


# ============================================================================
# 6. build_dimension_scores tests
# ============================================================================


def test_build_dimension_scores_basic():
    """Creates correct DimensionScore objects from raw scores and rubric config."""
    rubric = {
        "correctness": {"weight": 0.50},
        "completeness": {"weight": 0.50},
    }
    scores = {"correctness": 0.90, "completeness": 0.70}

    result = build_dimension_scores(scores, rubric, DEFAULT_THRESHOLDS)

    assert len(result) == 2
    assert result[0].dimension == "correctness"
    assert result[0].score == 0.90
    assert result[0].weight == 0.50
    assert result[0].grade == "A"
    assert result[1].dimension == "completeness"
    assert result[1].score == 0.70
    assert result[1].grade == "B"


def test_build_dimension_scores_missing_scores_default_to_zero():
    """Missing scores default to 0.0."""
    rubric = {"correctness": {"weight": 1.0}}
    scores: dict[str, float] = {}  # no score provided

    result = build_dimension_scores(scores, rubric, DEFAULT_THRESHOLDS)

    assert result[0].score == 0.0
    assert result[0].grade == "F"


def test_build_dimension_scores_clamping():
    """Scores outside [0.0, 1.0] are clamped."""
    rubric = {
        "too_high": {"weight": 0.5},
        "too_low": {"weight": 0.5},
    }
    scores = {"too_high": 1.5, "too_low": -0.3}

    result = build_dimension_scores(scores, rubric, DEFAULT_THRESHOLDS)

    assert result[0].score == 1.0  # clamped from 1.5
    assert result[1].score == 0.0  # clamped from -0.3


def test_build_dimension_scores_with_object_config():
    """Supports rubric config with attribute access (object, not dict)."""

    class DimConfig:
        def __init__(self, weight: float):
            self.weight = weight

    rubric = {
        "safety": DimConfig(0.30),
        "format": DimConfig(0.70),
    }
    scores = {"safety": 0.95, "format": 0.80}

    result = build_dimension_scores(scores, rubric, DEFAULT_THRESHOLDS)

    assert result[0].dimension == "safety"
    assert result[0].weight == pytest.approx(0.30)
    assert result[1].dimension == "format"
    assert result[1].weight == pytest.approx(0.70)


def test_build_dimension_scores_empty_rubric():
    """Empty rubric produces empty list (no crash)."""
    result = build_dimension_scores({}, {}, DEFAULT_THRESHOLDS)
    assert result == []


# ============================================================================
# 7. Hypothesis property-based tests
# ============================================================================


@given(score=st.floats(min_value=0.0, max_value=1.0))
@settings(max_examples=200)
def test_score_to_grade_always_valid(score: float):
    """For any valid score, grade is always one of S/A/B/C/D/F."""
    grade = score_to_grade(score, DEFAULT_THRESHOLDS)
    assert grade in {"S", "A", "B", "C", "D", "F"}


@given(
    score_a=st.floats(min_value=0.0, max_value=1.0),
    score_b=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=200)
def test_score_to_grade_monotonic(score_a: float, score_b: float):
    """Higher scores always get equal or better grades (monotonicity)."""
    grade_a = score_to_grade(score_a, DEFAULT_THRESHOLDS)
    grade_b = score_to_grade(score_b, DEFAULT_THRESHOLDS)
    rank = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
    if score_a > score_b:
        assert rank[grade_a] >= rank[grade_b]


@given(score=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_score_to_grade_never_crashes(score: float):
    """score_to_grade never raises for any finite float input."""
    grade = score_to_grade(score, DEFAULT_THRESHOLDS)
    assert grade in {"S", "A", "B", "C", "D", "F"}


@given(
    scores=st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=1.0),
            st.floats(min_value=0.01, max_value=1.0),
        ),
        min_size=1,
        max_size=10,
    )
)
@settings(max_examples=100)
def test_calculate_overall_grade_always_valid(
    scores: list[tuple[float, float]],
):
    """calculate_overall_grade always returns a valid grade for non-empty input."""
    dims = [
        DimensionScore(dimension=f"dim_{i}", score=s, weight=w, grade="F")
        for i, (s, w) in enumerate(scores)
    ]
    overall_score, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
    assert 0.0 <= overall_score <= 1.0
    assert grade in {"S", "A", "B", "C", "D", "F"}


# ============================================================================
# 8. Concurrency test
# ============================================================================


def test_grade_calculation_thread_safe():
    """Grade calculation works correctly from multiple threads."""
    expected = {
        0.0: "F",
        0.30: "D",
        0.50: "C",
        0.70: "B",
        0.85: "A",
        0.95: "S",
    }

    def _check(score: float) -> tuple[float, str]:
        grade = score_to_grade(score, DEFAULT_THRESHOLDS)
        return score, grade

    with ThreadPoolExecutor(max_workers=8) as pool:
        # Submit 100 tasks across 6 score values
        futures = [
            pool.submit(_check, score)
            for score in list(expected.keys()) * 20  # 120 calls total
        ]
        for fut in as_completed(futures):
            score, grade = fut.result()
            assert grade == expected[score], (
                f"Thread-safety violation: score={score} returned {grade}, "
                f"expected {expected[score]}"
            )


# ============================================================================
# 9. eval_result_to_dict tests
# ============================================================================


def _make_eval_result(
    *,
    pre_check: PreCheckResult | None = None,
    cost_metrics: CostMetrics | None = None,
    context_metrics: ContextMetrics | None = None,
    execution_results: list[Any] | None = None,
) -> EvalResult:
    """Helper to build a minimal EvalResult for serialization tests."""
    dims = [
        DimensionScore(dimension="correctness", score=0.90, weight=0.60, grade="A"),
        DimensionScore(dimension="format", score=0.80, weight=0.40, grade="B"),
    ]
    meta = EvalMetadata(
        model="gpt-4o",
        provider="openai",
        cost_metrics=cost_metrics,
        context_metrics=context_metrics,
        total_duration_ms=4500,
        timestamp="2026-03-17T12:00:00Z",
    )
    return EvalResult(
        skill_path="/skills/test.md",
        overall_grade="A",
        overall_score=0.86,
        dimensions=dims,
        pre_check=pre_check,
        metadata=meta,
        execution_results=execution_results,
    )


def test_eval_result_to_dict_basic_serialization():
    """eval_result_to_dict produces a dict with expected top-level keys."""
    pre = PreCheckResult(passed=True, checks_run=3, duration_ms=50)
    result = _make_eval_result(pre_check=pre)

    d = eval_result_to_dict(result)

    assert d["skill_path"] == "/skills/test.md"
    assert d["overall_grade"] == "A"
    assert d["overall_score"] == 0.86
    assert len(d["dimensions"]) == 2
    assert d["dimensions"][0]["dimension"] == "correctness"
    assert d["pre_check"] is not None
    assert d["pre_check"]["passed"] is True
    assert d["metadata"]["model"] == "gpt-4o"


def test_eval_result_to_dict_none_pre_check():
    """pre_check=None is serialized as None in the dict."""
    result = _make_eval_result(pre_check=None)
    d = eval_result_to_dict(result)
    assert d["pre_check"] is None


def test_eval_result_to_dict_none_cost_metrics():
    """None cost_metrics are excluded from metadata dict for cleaner JSON."""
    result = _make_eval_result(cost_metrics=None)
    d = eval_result_to_dict(result)
    assert "cost_metrics" not in d["metadata"]


def test_eval_result_to_dict_none_context_metrics():
    """None context_metrics are excluded from metadata dict."""
    result = _make_eval_result(context_metrics=None)
    d = eval_result_to_dict(result)
    assert "context_metrics" not in d["metadata"]


def test_eval_result_to_dict_with_cost_and_context():
    """When cost/context metrics exist, they are included in metadata."""
    cost = CostMetrics(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    ctx = ContextMetrics(prompt_tokens_used=100)
    result = _make_eval_result(cost_metrics=cost, context_metrics=ctx)

    d = eval_result_to_dict(result)

    assert "cost_metrics" in d["metadata"]
    assert d["metadata"]["cost_metrics"]["prompt_tokens"] == 100
    assert "context_metrics" in d["metadata"]
    assert d["metadata"]["context_metrics"]["prompt_tokens_used"] == 100


def test_eval_result_to_dict_excludes_execution_results():
    """execution_results is NOT included in the serialized dict (for clean JSON)."""
    result = _make_eval_result(execution_results=["raw_data_1", "raw_data_2"])
    d = eval_result_to_dict(result)
    # The dict should not expose execution_results (internal debugging field)
    assert "execution_results" not in d


def test_eval_result_to_dict_overall_score_rounded():
    """overall_score is rounded to 4 decimal places."""
    meta = EvalMetadata(model="gpt-4o", provider="openai")
    result = EvalResult(
        skill_path="s.md",
        overall_grade="B",
        overall_score=0.82256789,
        dimensions=[],
        pre_check=None,
        metadata=meta,
    )
    d = eval_result_to_dict(result)
    assert d["overall_score"] == 0.8226


# ============================================================================
# 10. Module-level constants sanity checks
# ============================================================================


def test_builtin_dimensions_content():
    """BUILTIN_DIMENSIONS contains the 7 known dimensions."""
    expected = {
        "correctness", "completeness", "format",
        "adherence", "safety", "efficiency", "robustness",
    }
    assert BUILTIN_DIMENSIONS == expected


def test_grade_order_descending():
    """GRADE_ORDER is in descending quality: S, A, B, C, D, F."""
    assert GRADE_ORDER == ("S", "A", "B", "C", "D", "F")
