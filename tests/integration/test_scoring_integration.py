"""Integration tests for scoring — real grade calculations, no mocks."""

import pytest

from md_evals.scoring import (
    DimensionScore,
    EvalMetadata,
    EvalResult,
    score_to_grade,
    calculate_overall_grade,
    build_dimension_scores,
    eval_result_to_dict,
)


# ── Standard thresholds from rubric_default.yaml ──
DEFAULT_THRESHOLDS = {"S": 0.95, "A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30}
NO_S_THRESHOLDS = {"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30}


class TestScoreToGrade:
    """Test score_to_grade with known inputs and thresholds."""

    @pytest.mark.parametrize(
        "score, expected",
        [
            (1.0, "S"),
            (0.96, "S"),
            (0.95, "S"),
            (0.94, "A"),
            (0.90, "A"),
            (0.85, "A"),
            (0.84, "B"),
            (0.75, "B"),
            (0.70, "B"),
            (0.69, "C"),
            (0.55, "C"),
            (0.50, "C"),
            (0.49, "D"),
            (0.35, "D"),
            (0.30, "D"),
            (0.29, "F"),
            (0.0, "F"),
        ],
    )
    def test_default_thresholds(self, score, expected):
        assert score_to_grade(score, DEFAULT_THRESHOLDS) == expected

    def test_no_s_grade(self):
        assert score_to_grade(0.99, NO_S_THRESHOLDS) == "A"

    def test_clamp_above_one(self):
        assert score_to_grade(1.5, DEFAULT_THRESHOLDS) == "S"

    def test_clamp_below_zero(self):
        assert score_to_grade(-0.5, DEFAULT_THRESHOLDS) == "F"


class TestCalculateOverallGrade:
    """Test weighted average calculation with real dimension scores."""

    def test_all_perfect(self):
        dims = [
            DimensionScore(dimension="correctness", score=1.0, weight=0.5, grade="S"),
            DimensionScore(dimension="format", score=1.0, weight=0.5, grade="S"),
        ]
        overall, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
        assert overall == pytest.approx(1.0)
        assert grade == "S"

    def test_all_zero(self):
        dims = [
            DimensionScore(dimension="correctness", score=0.0, weight=0.5, grade="F"),
            DimensionScore(dimension="format", score=0.0, weight=0.5, grade="F"),
        ]
        overall, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
        assert overall == pytest.approx(0.0)
        assert grade == "F"

    def test_mixed_scores_weighted(self):
        dims = [
            DimensionScore(dimension="correctness", score=0.90, weight=0.6, grade="A"),
            DimensionScore(dimension="format", score=0.50, weight=0.4, grade="C"),
        ]
        # Expected: (0.90 * 0.6 + 0.50 * 0.4) / 1.0 = 0.74
        overall, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
        assert overall == pytest.approx(0.74)
        assert grade == "B"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            calculate_overall_grade([], DEFAULT_THRESHOLDS)

    def test_zero_weights_return_f(self):
        dims = [
            DimensionScore(dimension="a", score=1.0, weight=0.0, grade="S"),
        ]
        overall, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
        assert overall == 0.0
        assert grade == "F"

    def test_realistic_seven_dimensions(self):
        """Simulate the default 7-dimension rubric with realistic scores."""
        dims = [
            DimensionScore(dimension="correctness", score=0.88, weight=0.25, grade="A"),
            DimensionScore(dimension="completeness", score=0.72, weight=0.20, grade="B"),
            DimensionScore(dimension="format", score=0.90, weight=0.15, grade="A"),
            DimensionScore(dimension="adherence", score=0.65, weight=0.15, grade="C"),
            DimensionScore(dimension="safety", score=0.95, weight=0.10, grade="S"),
            DimensionScore(dimension="efficiency", score=0.80, weight=0.10, grade="B"),
            DimensionScore(dimension="robustness", score=0.60, weight=0.05, grade="C"),
        ]
        overall, grade = calculate_overall_grade(dims, DEFAULT_THRESHOLDS)
        # Manual: 0.88*0.25 + 0.72*0.20 + 0.90*0.15 + 0.65*0.15 + 0.95*0.10 + 0.80*0.10 + 0.60*0.05
        # = 0.22 + 0.144 + 0.135 + 0.0975 + 0.095 + 0.08 + 0.03 = 0.8015
        assert overall == pytest.approx(0.8015, abs=0.001)
        assert grade == "B"


class TestBuildDimensionScores:
    """Test building DimensionScore list from raw data."""

    def test_from_raw_scores(self):
        raw = {"correctness": 0.90, "format": 0.75}
        rubric_dims = {
            "correctness": {"weight": 0.6},
            "format": {"weight": 0.4},
        }
        result = build_dimension_scores(raw, rubric_dims, DEFAULT_THRESHOLDS)
        assert len(result) == 2
        assert result[0].dimension == "correctness"
        assert result[0].score == 0.90
        assert result[0].grade == "A"
        assert result[0].weight == 0.6

    def test_missing_score_defaults_zero(self):
        raw = {"correctness": 0.90}
        rubric_dims = {
            "correctness": {"weight": 0.5},
            "format": {"weight": 0.5},
        }
        result = build_dimension_scores(raw, rubric_dims, DEFAULT_THRESHOLDS)
        format_score = [d for d in result if d.dimension == "format"][0]
        assert format_score.score == 0.0
        assert format_score.grade == "F"

    def test_score_clamped_to_range(self):
        raw = {"x": 1.5}
        rubric_dims = {"x": {"weight": 1.0}}
        result = build_dimension_scores(raw, rubric_dims, DEFAULT_THRESHOLDS)
        assert result[0].score == 1.0

    def test_negative_score_clamped(self):
        raw = {"x": -0.5}
        rubric_dims = {"x": {"weight": 1.0}}
        result = build_dimension_scores(raw, rubric_dims, DEFAULT_THRESHOLDS)
        assert result[0].score == 0.0


class TestEvalResultSerialization:
    """Test full serialization pipeline."""

    def test_eval_result_to_dict_basic(self):
        dims = [
            DimensionScore(dimension="correctness", score=0.90, weight=1.0, grade="A"),
        ]
        metadata = EvalMetadata(model="gpt-4o", provider="openai")
        result = EvalResult(
            skill_path="/test/SKILL.md",
            overall_grade="A",
            overall_score=0.90,
            dimensions=dims,
            pre_check=None,
            metadata=metadata,
        )
        d = eval_result_to_dict(result)
        assert d["skill_path"] == "/test/SKILL.md"
        assert d["overall_grade"] == "A"
        assert d["overall_score"] == 0.9
        assert len(d["dimensions"]) == 1
        assert d["dimensions"][0]["dimension"] == "correctness"
        assert d["pre_check"] is None
        assert "cost_metrics" not in d["metadata"]

    def test_eval_result_to_dict_with_precheck(self):
        from md_evals.precheck import PreCheckResult, PreCheckFinding

        dims = [
            DimensionScore(dimension="x", score=0.5, weight=1.0, grade="C"),
        ]
        metadata = EvalMetadata(model="test", provider="test")
        pre = PreCheckResult(
            passed=True,
            findings=[PreCheckFinding(check="test", message="ok", severity="info")],
            checks_run=1,
            duration_ms=5,
        )
        result = EvalResult(
            skill_path="/test.md",
            overall_grade="C",
            overall_score=0.5,
            dimensions=dims,
            pre_check=pre,
            metadata=metadata,
        )
        d = eval_result_to_dict(result)
        assert d["pre_check"] is not None
        assert d["pre_check"]["passed"] is True
