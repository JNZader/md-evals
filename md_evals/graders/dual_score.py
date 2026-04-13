"""Dual-score pattern: score content quality AND rubric quality.

Inspired by jmilinovich/goal-md. Prevents the eval from gaming itself —
if the rubric is weak, the content score is unreliable.

Two scores are produced:
  - **Content score**: Does the output meet the rubric criteria?
  - **Rubric quality score**: Is the rubric well-defined enough to give
    reliable scores?

The combined confidence is ``content_score * rubric_quality``, reflecting
the principle that a high content score is only trustworthy when the
rubric itself is strong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from md_evals.models import EvaluatorResult


# ─── Rubric quality checks ──────────────────────────────────────


@dataclass(frozen=True)
class RubricQualityReport:
    """Assessment of a rubric's quality.

    Attributes:
        score: Overall rubric quality in [0.0, 1.0].
        has_clear_criteria: Whether criteria are explicitly stated.
        has_scoring_levels: Whether discrete scoring levels are defined.
        has_examples: Whether examples of good/bad output are included.
        specificity_score: How specific (vs. vague) the rubric is.
        issues: Human-readable list of rubric weaknesses.
    """

    score: float
    has_clear_criteria: bool
    has_scoring_levels: bool
    has_examples: bool
    specificity_score: float
    issues: list[str] = field(default_factory=list)


def assess_rubric_quality(
    rubric_text: str,
    *,
    criteria_keywords: list[str] | None = None,
    scoring_keywords: list[str] | None = None,
    example_keywords: list[str] | None = None,
    vague_words: list[str] | None = None,
) -> RubricQualityReport:
    """Assess the quality of a rubric text.

    Uses heuristic keyword checks. For a more robust analysis, feed
    the rubric through an LLM-as-judge with a meta-rubric.

    Args:
        rubric_text: The full rubric text to analyze.
        criteria_keywords: Words that indicate criteria are stated.
        scoring_keywords: Words that indicate scoring levels exist.
        example_keywords: Words that indicate examples are present.
        vague_words: Words that indicate vagueness.

    Returns:
        RubricQualityReport with scores and issues.
    """
    if criteria_keywords is None:
        criteria_keywords = [
            "must", "should", "require", "criteria", "criterion",
            "expected", "evaluate", "assess", "check",
        ]
    if scoring_keywords is None:
        scoring_keywords = [
            "score", "rating", "level", "grade", "points",
            "1-5", "1-10", "0-1", "scale", "rubric",
        ]
    if example_keywords is None:
        example_keywords = [
            "example", "e.g.", "for instance", "such as",
            "sample", "good:", "bad:", "ideal:",
        ]
    if vague_words is None:
        vague_words = [
            "good", "nice", "appropriate", "adequate", "reasonable",
            "sufficient", "proper", "suitable",
        ]

    rubric_lower = rubric_text.lower()
    issues: list[str] = []

    # Check for empty / very short rubric
    if len(rubric_text.strip()) < 10:
        return RubricQualityReport(
            score=0.0,
            has_clear_criteria=False,
            has_scoring_levels=False,
            has_examples=False,
            specificity_score=0.0,
            issues=["Rubric is empty or too short to be meaningful"],
        )

    # --- Criteria clarity ---
    criteria_hits = sum(
        1 for kw in criteria_keywords if kw.lower() in rubric_lower
    )
    has_clear_criteria = criteria_hits >= 2
    if not has_clear_criteria:
        issues.append(
            "Rubric lacks explicit criteria language "
            "(e.g., 'must', 'should', 'require')"
        )

    # --- Scoring levels ---
    scoring_hits = sum(
        1 for kw in scoring_keywords if kw.lower() in rubric_lower
    )
    has_scoring_levels = scoring_hits >= 1
    if not has_scoring_levels:
        issues.append(
            "Rubric does not define scoring levels or a scale"
        )

    # --- Examples ---
    example_hits = sum(
        1 for kw in example_keywords if kw.lower() in rubric_lower
    )
    has_examples = example_hits >= 1
    if not has_examples:
        issues.append(
            "Rubric lacks concrete examples of good/bad output"
        )

    # --- Specificity (inverse of vagueness) ---
    word_count = max(len(rubric_text.split()), 1)
    vague_hits = sum(
        1 for kw in vague_words if kw.lower() in rubric_lower
    )
    vagueness_ratio = vague_hits / word_count
    # Higher ratio = more vague = lower specificity
    specificity_score = max(0.0, min(1.0, 1.0 - (vagueness_ratio * 20)))
    if specificity_score < 0.5:
        issues.append(
            f"Rubric uses too many vague terms ({vague_hits} vague words "
            f"in {word_count} total words)"
        )

    # --- Composite score ---
    weights = {
        "criteria": 0.35,
        "scoring": 0.25,
        "examples": 0.20,
        "specificity": 0.20,
    }
    composite = (
        weights["criteria"] * (1.0 if has_clear_criteria else 0.0)
        + weights["scoring"] * (1.0 if has_scoring_levels else 0.0)
        + weights["examples"] * (1.0 if has_examples else 0.0)
        + weights["specificity"] * specificity_score
    )

    return RubricQualityReport(
        score=round(composite, 4),
        has_clear_criteria=has_clear_criteria,
        has_scoring_levels=has_scoring_levels,
        has_examples=has_examples,
        specificity_score=round(specificity_score, 4),
        issues=issues,
    )


# ─── Content scoring ────────────────────────────────────────────


@dataclass(frozen=True)
class ContentScoreReport:
    """Content quality assessment result.

    Attributes:
        score: Content quality in [0.0, 1.0].
        reason: Explanation of the score.
        details: Arbitrary extra data.
    """

    score: float
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


# ─── Dual-score result ──────────────────────────────────────────


@dataclass(frozen=True)
class DualScoreResult:
    """Combined dual-score result.

    Attributes:
        content_score: Content quality in [0.0, 1.0].
        rubric_quality: Rubric quality in [0.0, 1.0].
        combined_confidence: content_score * rubric_quality.
        passed: Whether combined_confidence meets the threshold.
        content_report: Detailed content assessment.
        rubric_report: Detailed rubric assessment.
    """

    content_score: float
    rubric_quality: float
    combined_confidence: float
    passed: bool
    content_report: ContentScoreReport
    rubric_report: RubricQualityReport

    def to_evaluator_result(self, name: str = "dual_score") -> EvaluatorResult:
        """Convert to standard ``EvaluatorResult``."""
        return EvaluatorResult(
            evaluator_name=name,
            passed=self.passed,
            score=self.combined_confidence,
            reason=(
                f"Content={self.content_score:.2f}, "
                f"Rubric={self.rubric_quality:.2f}, "
                f"Combined={self.combined_confidence:.2f}"
            ),
            details={
                "content_score": self.content_score,
                "rubric_quality": self.rubric_quality,
                "combined_confidence": self.combined_confidence,
                "rubric_issues": self.rubric_report.issues,
                "content_reason": self.content_report.reason,
            },
        )


# ─── Dual-score evaluator ───────────────────────────────────────


@dataclass
class DualScoreEvaluator:
    """Dual-score evaluator: score content AND rubric quality.

    The evaluator first assesses the rubric quality, then scores the
    content against that rubric. The combined confidence is the product
    of both scores, ensuring a high content score is only meaningful
    when backed by a strong rubric.

    Args:
        name: Evaluator identifier.
        rubric_text: The rubric text to assess and use.
        pass_threshold: Minimum combined confidence to pass (default 0.5).
        content_scorer: Optional callable that scores content.
            If None, the caller must provide a pre-computed content score.
    """

    name: str
    rubric_text: str
    pass_threshold: float = 0.5
    content_scorer: Any = None  # Callable[[str, str], ContentScoreReport] | None

    def evaluate(
        self,
        output: str,
        *,
        content_score: float | None = None,
        content_reason: str = "",
    ) -> DualScoreResult:
        """Run the dual-score evaluation.

        Args:
            output: The LLM output to evaluate.
            content_score: Pre-computed content score. If the
                ``content_scorer`` callable is set, this is ignored.
            content_reason: Explanation for the content score (used when
                providing a pre-computed score).

        Returns:
            DualScoreResult with both scores and combined confidence.
        """
        # Step 1: Assess rubric quality
        rubric_report = assess_rubric_quality(self.rubric_text)

        # Step 2: Score content
        if self.content_scorer is not None:
            content_report = self.content_scorer(output, self.rubric_text)
        elif content_score is not None:
            content_report = ContentScoreReport(
                score=max(0.0, min(1.0, content_score)),
                reason=content_reason or "Pre-computed content score",
            )
        else:
            content_report = ContentScoreReport(
                score=0.0,
                reason="No content scorer or pre-computed score provided",
            )

        # Step 3: Combined confidence
        combined = content_report.score * rubric_report.score

        return DualScoreResult(
            content_score=content_report.score,
            rubric_quality=rubric_report.score,
            combined_confidence=round(combined, 4),
            passed=combined >= self.pass_threshold,
            content_report=content_report,
            rubric_report=rubric_report,
        )
