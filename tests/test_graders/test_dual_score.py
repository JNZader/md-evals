"""Tests for dual-score pattern: content quality + rubric quality."""

import pytest

from md_evals.graders.dual_score import (
    DualScoreEvaluator,
    DualScoreResult,
    ContentScoreReport,
    RubricQualityReport,
    assess_rubric_quality,
)


# ============================================================================
# assess_rubric_quality
# ============================================================================


class TestAssessRubricQuality:
    """Tests for the rubric quality assessor."""

    def test_empty_rubric_scores_zero(self):
        report = assess_rubric_quality("")
        assert report.score == 0.0
        assert report.has_clear_criteria is False
        assert len(report.issues) >= 1

    def test_very_short_rubric_scores_zero(self):
        report = assess_rubric_quality("Be good")
        assert report.score == 0.0

    def test_strong_rubric_scores_high(self):
        rubric = (
            "The output must include all required sections. "
            "Each section should contain at least 3 sentences. "
            "Score on a scale of 1-5 where 5 is excellent. "
            "For example, a good response includes specific data points. "
            "The criteria require factual accuracy and completeness."
        )
        report = assess_rubric_quality(rubric)
        assert report.score > 0.7
        assert report.has_clear_criteria is True
        assert report.has_scoring_levels is True
        assert report.has_examples is True

    def test_rubric_without_scoring_levels(self):
        rubric = (
            "The output must be correct and should include all required details. "
            "Evaluate whether the response addresses the criteria."
        )
        report = assess_rubric_quality(rubric)
        assert report.has_scoring_levels is False
        assert any("scoring levels" in issue for issue in report.issues)

    def test_rubric_without_examples(self):
        rubric = (
            "The output must be correct. Score on a scale of 1-5. "
            "The response should meet all criteria and requirements."
        )
        report = assess_rubric_quality(rubric)
        assert report.has_examples is False
        assert any("examples" in issue.lower() for issue in report.issues)

    def test_vague_rubric_low_specificity(self):
        rubric = (
            "The output should be good and appropriate. "
            "It should be adequate and reasonable. "
            "A proper and suitable response is nice."
        )
        report = assess_rubric_quality(rubric)
        assert report.specificity_score < 0.8

    def test_specific_rubric_high_specificity(self):
        rubric = (
            "The output must contain exactly 3 code blocks. "
            "Each function must have type annotations. "
            "Score 1-5 based on test coverage percentage. "
            "For example, 90% coverage = 5 points."
        )
        report = assess_rubric_quality(rubric)
        assert report.specificity_score >= 0.8

    def test_custom_keywords(self):
        rubric = "OBLIGATORIO: incluir datos. PUNTAJE: 1 a 10."
        report = assess_rubric_quality(
            rubric,
            criteria_keywords=["obligatorio", "incluir"],
            scoring_keywords=["puntaje"],
        )
        assert report.has_clear_criteria is True
        assert report.has_scoring_levels is True


# ============================================================================
# DualScoreEvaluator
# ============================================================================


class TestDualScoreEvaluator:
    """Tests for the dual-score evaluator."""

    STRONG_RUBRIC = (
        "The output must include all required sections and should be comprehensive. "
        "Score on a scale of 1-5 based on criteria completeness. "
        "For example, a 5-point response covers every requirement with evidence."
    )

    WEAK_RUBRIC = "Be good."

    def test_high_content_strong_rubric_passes(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
            pass_threshold=0.5,
        )
        result = evaluator.evaluate(
            "Great output", content_score=0.9, content_reason="Excellent"
        )
        assert result.content_score == 0.9
        assert result.rubric_quality > 0.7
        assert result.combined_confidence > 0.5
        assert result.passed is True

    def test_high_content_weak_rubric_fails(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.WEAK_RUBRIC,
            pass_threshold=0.5,
        )
        result = evaluator.evaluate(
            "Great output", content_score=0.9, content_reason="Excellent"
        )
        assert result.content_score == 0.9
        assert result.rubric_quality == 0.0  # Weak rubric
        assert result.combined_confidence == 0.0
        assert result.passed is False

    def test_low_content_strong_rubric_fails(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
            pass_threshold=0.5,
        )
        result = evaluator.evaluate(
            "Bad output", content_score=0.2, content_reason="Poor"
        )
        assert result.content_score == 0.2
        assert result.combined_confidence < 0.5
        assert result.passed is False

    def test_combined_confidence_is_product(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
            pass_threshold=0.0,
        )
        result = evaluator.evaluate("output", content_score=0.8)
        expected = round(0.8 * result.rubric_quality, 4)
        assert result.combined_confidence == expected

    def test_no_content_score_or_scorer(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
        )
        result = evaluator.evaluate("output")
        assert result.content_score == 0.0
        assert result.combined_confidence == 0.0

    def test_custom_content_scorer(self):
        def scorer(output: str, rubric: str) -> ContentScoreReport:
            # Simple scorer: score based on length
            score = min(1.0, len(output) / 100)
            return ContentScoreReport(
                score=score, reason=f"Length-based: {len(output)} chars"
            )

        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
            content_scorer=scorer,
            pass_threshold=0.0,
        )
        result = evaluator.evaluate("A" * 80)
        assert result.content_score == 0.8
        assert "Length-based" in result.content_report.reason

    def test_content_score_clamped_to_0_1(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
            pass_threshold=0.0,
        )
        result = evaluator.evaluate("output", content_score=1.5)
        assert result.content_score == 1.0

        result2 = evaluator.evaluate("output", content_score=-0.5)
        assert result2.content_score == 0.0

    def test_to_evaluator_result(self):
        evaluator = DualScoreEvaluator(
            name="dual_test",
            rubric_text=self.STRONG_RUBRIC,
            pass_threshold=0.0,
        )
        result = evaluator.evaluate("output", content_score=0.7)
        eval_result = result.to_evaluator_result(name="my_dual")
        assert eval_result.evaluator_name == "my_dual"
        assert eval_result.score == result.combined_confidence
        assert "Content=" in eval_result.reason
        assert "Rubric=" in eval_result.reason
        assert "rubric_issues" in eval_result.details

    def test_pass_threshold_boundary(self):
        evaluator = DualScoreEvaluator(
            name="test",
            rubric_text=self.STRONG_RUBRIC,
            pass_threshold=0.5,
        )
        # Find rubric quality to calculate needed content score
        rubric_report = assess_rubric_quality(self.STRONG_RUBRIC)
        # Set content score so combined is exactly at threshold
        needed = 0.5 / rubric_report.score
        result = evaluator.evaluate("output", content_score=needed)
        assert result.passed is True

        # Just below threshold
        result2 = evaluator.evaluate("output", content_score=needed - 0.1)
        assert result2.passed is False


# ============================================================================
# DualScoreResult frozen
# ============================================================================


class TestDualScoreResult:
    """Tests for DualScoreResult dataclass."""

    def test_is_frozen(self):
        result = DualScoreResult(
            content_score=0.8,
            rubric_quality=0.9,
            combined_confidence=0.72,
            passed=True,
            content_report=ContentScoreReport(score=0.8, reason="Good"),
            rubric_report=RubricQualityReport(
                score=0.9,
                has_clear_criteria=True,
                has_scoring_levels=True,
                has_examples=True,
                specificity_score=0.9,
            ),
        )
        with pytest.raises(AttributeError):
            result.content_score = 0.5  # type: ignore[misc]
