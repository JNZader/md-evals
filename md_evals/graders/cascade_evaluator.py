"""Cascade evaluator: cheap checks first, expensive LLM-judge only if needed.

Inspired by open-compass/opencompass cascade evaluation strategy. Chains
multiple evaluation strategies in sequence — fast/cheap evaluators run first
(regex, keyword matching), and the expensive LLM-as-judge only fires when
cheaper evaluators return ``uncertain``.

This saves cost by short-circuiting evaluation when cheap checks are
sufficient to determine pass/fail.

Each evaluator in the cascade returns one of three verdicts:
  - ``pass``  → stop, the output passes
  - ``fail``  → stop, the output fails
  - ``uncertain`` → continue to the next evaluator in the chain

If all evaluators return uncertain, the cascade returns a configurable
default result (fail by default).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from md_evals.models import EvaluatorResult


class CascadeVerdict(str, Enum):
    """Verdict from a single cascade step."""

    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class CascadeStepResult:
    """Result from a single step in the cascade.

    Attributes:
        verdict: pass / fail / uncertain.
        score: Numeric score in [0.0, 1.0].
        reason: Human-readable explanation.
        evaluator_name: Which evaluator produced this result.
    """

    verdict: CascadeVerdict
    score: float
    reason: str
    evaluator_name: str


# ─── Step protocols ─────────────────────────────────────────────


@runtime_checkable
class CascadeStep(Protocol):
    """Protocol for a single step in the cascade."""

    name: str

    def evaluate(self, output: str, **context: Any) -> CascadeStepResult:
        """Evaluate the output and return a verdict."""
        ...


# ─── Built-in steps ─────────────────────────────────────────────


@dataclass
class RegexStep:
    """Regex-based cascade step.

    Returns ``pass`` if pattern matches (or ``fail`` if ``pass_on_match``
    is False). Returns ``uncertain`` when the pattern neither confirms
    nor denies the quality.

    Args:
        name: Step identifier.
        pattern: Regex pattern to match.
        pass_on_match: If True, a match means pass; otherwise match means fail.
        uncertain_on_no_match: If True, no-match returns uncertain instead of
            the opposite verdict. Defaults to True so the cascade continues.
    """

    name: str
    pattern: str
    pass_on_match: bool = True
    uncertain_on_no_match: bool = True

    def evaluate(self, output: str, **context: Any) -> CascadeStepResult:
        try:
            compiled = re.compile(self.pattern, re.MULTILINE | re.IGNORECASE)
            match = compiled.search(output)
        except re.error as exc:
            return CascadeStepResult(
                verdict=CascadeVerdict.UNCERTAIN,
                score=0.0,
                reason=f"Invalid regex: {exc}",
                evaluator_name=self.name,
            )

        if match:
            if self.pass_on_match:
                return CascadeStepResult(
                    verdict=CascadeVerdict.PASS,
                    score=1.0,
                    reason=f"Regex matched: {match.group()!r}",
                    evaluator_name=self.name,
                )
            return CascadeStepResult(
                verdict=CascadeVerdict.FAIL,
                score=0.0,
                reason=f"Regex matched (fail-on-match): {match.group()!r}",
                evaluator_name=self.name,
            )

        # No match
        if self.uncertain_on_no_match:
            return CascadeStepResult(
                verdict=CascadeVerdict.UNCERTAIN,
                score=0.5,
                reason="Regex did not match — uncertain",
                evaluator_name=self.name,
            )

        # Definitive opposite verdict
        verdict = CascadeVerdict.FAIL if self.pass_on_match else CascadeVerdict.PASS
        score = 0.0 if self.pass_on_match else 1.0
        return CascadeStepResult(
            verdict=verdict,
            score=score,
            reason="Regex did not match",
            evaluator_name=self.name,
        )


@dataclass
class KeywordStep:
    """Keyword-matching cascade step.

    Checks whether required keywords appear in the output. Returns
    ``pass`` if coverage meets the threshold, ``fail`` if coverage is
    below the fail threshold, and ``uncertain`` otherwise.

    Args:
        name: Step identifier.
        keywords: List of keywords to search for (case-insensitive).
        pass_threshold: Coverage ratio to pass (default 0.8).
        fail_threshold: Coverage ratio below which to fail (default 0.2).
            Between fail and pass thresholds, the verdict is uncertain.
    """

    name: str
    keywords: list[str] = field(default_factory=list)
    pass_threshold: float = 0.8
    fail_threshold: float = 0.2

    def evaluate(self, output: str, **context: Any) -> CascadeStepResult:
        if not self.keywords:
            return CascadeStepResult(
                verdict=CascadeVerdict.UNCERTAIN,
                score=0.5,
                reason="No keywords configured",
                evaluator_name=self.name,
            )

        output_lower = output.lower()
        found = [kw for kw in self.keywords if kw.lower() in output_lower]
        coverage = len(found) / len(self.keywords)

        if coverage >= self.pass_threshold:
            return CascadeStepResult(
                verdict=CascadeVerdict.PASS,
                score=coverage,
                reason=f"Keyword coverage {coverage:.0%} >= {self.pass_threshold:.0%}",
                evaluator_name=self.name,
            )

        if coverage < self.fail_threshold:
            missing = [kw for kw in self.keywords if kw.lower() not in output_lower]
            return CascadeStepResult(
                verdict=CascadeVerdict.FAIL,
                score=coverage,
                reason=(
                    f"Keyword coverage {coverage:.0%} < {self.fail_threshold:.0%}. "
                    f"Missing: {missing}"
                ),
                evaluator_name=self.name,
            )

        # Between thresholds → uncertain
        return CascadeStepResult(
            verdict=CascadeVerdict.UNCERTAIN,
            score=coverage,
            reason=(
                f"Keyword coverage {coverage:.0%} between "
                f"{self.fail_threshold:.0%} and {self.pass_threshold:.0%}"
            ),
            evaluator_name=self.name,
        )


@dataclass
class LLMJudgeStep:
    """LLM-as-judge cascade step — the expensive fallback.

    Wraps an async LLM call into the synchronous cascade protocol.
    In production, the caller should use ``CascadeEvaluator.evaluate_async``
    for proper async handling. The sync ``evaluate`` stores a deferred
    marker so the cascade orchestrator can handle it.

    Args:
        name: Step identifier.
        criteria: Evaluation criteria for the judge.
        pass_threshold: Score threshold for pass (default 0.7).
        fail_threshold: Score threshold for fail (default 0.3).
    """

    name: str
    criteria: str = ""
    pass_threshold: float = 0.7
    fail_threshold: float = 0.3

    def evaluate(self, output: str, **context: Any) -> CascadeStepResult:
        """Sync evaluation — uses pre-supplied ``llm_score`` from context.

        The ``CascadeEvaluator`` injects ``llm_score`` into context after
        running the async LLM call. If no score is available, returns
        uncertain.
        """
        llm_score: float | None = context.get("llm_score")
        llm_reason: str = context.get("llm_reason", "")

        if llm_score is None:
            return CascadeStepResult(
                verdict=CascadeVerdict.UNCERTAIN,
                score=0.0,
                reason="LLM judge not invoked (no llm_score in context)",
                evaluator_name=self.name,
            )

        if llm_score >= self.pass_threshold:
            verdict = CascadeVerdict.PASS
        elif llm_score < self.fail_threshold:
            verdict = CascadeVerdict.FAIL
        else:
            verdict = CascadeVerdict.UNCERTAIN

        return CascadeStepResult(
            verdict=verdict,
            score=llm_score,
            reason=llm_reason or f"LLM judge score: {llm_score:.2f}",
            evaluator_name=self.name,
        )


# ─── Cascade orchestrator ───────────────────────────────────────


@dataclass
class CascadeResult:
    """Final result of the cascade evaluation.

    Attributes:
        passed: Whether the output passed.
        score: Final score (from the decisive step).
        reason: Explanation of the final verdict.
        decisive_step: Name of the step that made the final decision.
        steps_executed: Number of steps that actually ran.
        total_steps: Total steps in the cascade.
        step_results: All step results in execution order.
    """

    passed: bool
    score: float
    reason: str
    decisive_step: str
    steps_executed: int
    total_steps: int
    step_results: list[CascadeStepResult] = field(default_factory=list)

    def to_evaluator_result(self, name: str = "cascade") -> EvaluatorResult:
        """Convert to standard ``EvaluatorResult``."""
        return EvaluatorResult(
            evaluator_name=name,
            passed=self.passed,
            score=self.score,
            reason=self.reason,
            details={
                "decisive_step": self.decisive_step,
                "steps_executed": self.steps_executed,
                "total_steps": self.total_steps,
                "step_results": [
                    {
                        "evaluator_name": sr.evaluator_name,
                        "verdict": sr.verdict.value,
                        "score": sr.score,
                        "reason": sr.reason,
                    }
                    for sr in self.step_results
                ],
            },
        )


@dataclass
class CascadeEvaluator:
    """Cascade evaluator: cheap checks first, expensive LLM-judge last.

    Chains steps in order. Each step returns pass/fail/uncertain.
    On pass or fail the cascade short-circuits. On uncertain it
    continues to the next step.

    Args:
        name: Evaluator identifier.
        steps: Ordered list of cascade steps.
        default_pass: If all steps return uncertain, the default verdict.
    """

    name: str
    steps: list[CascadeStep] = field(default_factory=list)
    default_pass: bool = False

    def evaluate(self, output: str, **context: Any) -> CascadeResult:
        """Run the cascade synchronously.

        For LLM-judge steps, the caller must pre-supply ``llm_score``
        and ``llm_reason`` in the context dict.
        """
        step_results: list[CascadeStepResult] = []

        for step in self.steps:
            result = step.evaluate(output, **context)
            step_results.append(result)

            if result.verdict == CascadeVerdict.PASS:
                return CascadeResult(
                    passed=True,
                    score=result.score,
                    reason=result.reason,
                    decisive_step=result.evaluator_name,
                    steps_executed=len(step_results),
                    total_steps=len(self.steps),
                    step_results=step_results,
                )

            if result.verdict == CascadeVerdict.FAIL:
                return CascadeResult(
                    passed=False,
                    score=result.score,
                    reason=result.reason,
                    decisive_step=result.evaluator_name,
                    steps_executed=len(step_results),
                    total_steps=len(self.steps),
                    step_results=step_results,
                )

        # All uncertain — use default
        return CascadeResult(
            passed=self.default_pass,
            score=0.5,
            reason="All cascade steps returned uncertain — using default verdict",
            decisive_step="default",
            steps_executed=len(step_results),
            total_steps=len(self.steps),
            step_results=step_results,
        )
