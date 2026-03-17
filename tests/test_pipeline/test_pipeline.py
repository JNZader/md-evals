"""Tests for md_evals.pipeline.pipeline — Pipeline orchestrator.

Verifies sequential stage execution, graceful degradation, timeout
handling, error recording, and EvalResult assembly.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from md_evals.pipeline.context import EvalContext, StageResult
from md_evals.pipeline.pipeline import Pipeline
from md_evals.scoring import DimensionScore, EvalResult


# ── Helpers ──


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


class MockStage:
    """A configurable mock stage."""

    def __init__(
        self,
        name: str = "mock-stage",
        success: bool = True,
        error: str | None = None,
        delay: float = 0.0,
        raise_exc: Exception | None = None,
    ):
        self._name = name
        self._success = success
        self._error = error
        self._delay = delay
        self._raise_exc = raise_exc

    @property
    def name(self) -> str:
        return self._name

    async def execute(self, context: EvalContext) -> StageResult:
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._raise_exc:
            raise self._raise_exc
        return StageResult(
            success=self._success,
            duration_ms=int(self._delay * 1000),
            error=self._error,
        )


class ScorePopulatingStage:
    """Stage that populates context.scores (simulates JudgeStage)."""

    @property
    def name(self) -> str:
        return "score-populator"

    async def execute(self, context: EvalContext) -> StageResult:
        context.scores = [
            DimensionScore(dimension="correctness", score=0.85, weight=0.5, grade="A"),
            DimensionScore(dimension="format", score=0.75, weight=0.5, grade="B"),
        ]
        return StageResult(success=True)


# ============================================================================
# 1. Happy Path
# ============================================================================


def test_pipeline_happy_path():
    """Pipeline with all-success stages produces valid EvalResult."""
    from md_evals.rubric import RubricConfig, DimensionConfig

    rubric = RubricConfig(
        dimensions={
            "correctness": DimensionConfig(weight=0.5, description="Accuracy"),
            "format": DimensionConfig(weight=0.5, description="Structure"),
        },
        grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30},
    )

    stages = [
        MockStage("stage-1"),
        MockStage("stage-2"),
        ScorePopulatingStage(),
    ]
    pipeline = Pipeline(stages)
    ctx = EvalContext(skill_path="/test/skill.md", rubric=rubric)

    result = _run(pipeline.execute(ctx))

    assert isinstance(result, EvalResult)
    assert result.skill_path == "/test/skill.md"
    assert result.overall_score > 0.0
    assert result.overall_grade != "F"
    assert len(result.dimensions) == 2


def test_pipeline_records_no_errors_on_success():
    """Successful pipeline records no errors in context."""
    stages = [MockStage("ok-stage")]
    pipeline = Pipeline(stages)
    ctx = EvalContext(skill_path="/test/skill.md")

    _run(pipeline.execute(ctx))

    assert len(ctx.errors) == 0


# ============================================================================
# 2. Failing Stages
# ============================================================================


def test_pipeline_continues_after_stage_failure():
    """Pipeline continues to next stage after a stage returns failure."""
    stages = [
        MockStage("fail", success=False, error="Something broke"),
        ScorePopulatingStage(),
    ]
    pipeline = Pipeline(stages)
    ctx = EvalContext(skill_path="/test/skill.md")

    result = _run(pipeline.execute(ctx))

    # Should still have scores from ScorePopulatingStage
    assert len(result.dimensions) == 2
    assert result.overall_score > 0.0
    # Error should be recorded
    assert len(ctx.errors) == 1
    assert ctx.errors[0].error_type == "stage_failure"


def test_pipeline_continues_after_stage_exception():
    """Pipeline continues after an unhandled exception in a stage."""
    stages = [
        MockStage("crash", raise_exc=RuntimeError("Boom")),
        ScorePopulatingStage(),
    ]
    pipeline = Pipeline(stages)
    ctx = EvalContext(skill_path="/test/skill.md")

    result = _run(pipeline.execute(ctx))

    assert len(result.dimensions) == 2
    assert len(ctx.errors) == 1
    assert ctx.errors[0].error_type == "RuntimeError"
    assert "Boom" in ctx.errors[0].message


def test_pipeline_with_timeout():
    """Pipeline records timeout error when stage exceeds timeout."""
    stages = [
        MockStage("slow", delay=5.0),  # Will timeout
    ]
    pipeline = Pipeline(stages, timeout_per_stage=1)
    ctx = EvalContext(skill_path="/test/skill.md")

    result = _run(pipeline.execute(ctx))

    assert len(ctx.errors) == 1
    assert ctx.errors[0].error_type == "timeout"
    assert "timed out" in ctx.errors[0].message.lower()


# ============================================================================
# 3. Edge Cases
# ============================================================================


def test_pipeline_empty_stages_returns_grade_f():
    """Pipeline with no stages produces EvalResult with grade F."""
    pipeline = Pipeline(stages=[])
    ctx = EvalContext(skill_path="/test/skill.md")

    result = _run(pipeline.execute(ctx))

    assert isinstance(result, EvalResult)
    assert result.overall_grade == "F"
    assert result.overall_score == 0.0
    assert result.dimensions == []


def test_pipeline_all_stages_fail_returns_grade_f():
    """Pipeline where all stages fail returns grade F."""
    stages = [
        MockStage("fail1", success=False, error="Error 1"),
        MockStage("fail2", success=False, error="Error 2"),
    ]
    pipeline = Pipeline(stages)
    ctx = EvalContext(skill_path="/test/skill.md")

    result = _run(pipeline.execute(ctx))

    assert result.overall_grade == "F"
    assert result.overall_score == 0.0
    assert len(ctx.errors) == 2


def test_pipeline_records_all_errors():
    """Pipeline records errors from every failing stage."""
    stages = [
        MockStage("fail", success=False, error="First fail"),
        MockStage("crash", raise_exc=ValueError("Crash")),
        MockStage("ok"),
    ]
    pipeline = Pipeline(stages)
    ctx = EvalContext(skill_path="/test/skill.md")

    _run(pipeline.execute(ctx))

    assert len(ctx.errors) == 2
    error_types = [e.error_type for e in ctx.errors]
    assert "stage_failure" in error_types
    assert "ValueError" in error_types


def test_pipeline_result_includes_metadata():
    """Pipeline EvalResult includes metadata with model info."""
    pipeline = Pipeline(stages=[])
    ctx = EvalContext(skill_path="/test/skill.md")
    ctx.metadata["judge_model"] = "gpt-4o"
    ctx.metadata["judge_provider"] = "openai"

    result = _run(pipeline.execute(ctx))

    assert result.metadata.model == "gpt-4o"
    assert result.metadata.provider == "openai"


def test_pipeline_result_includes_precheck():
    """Pipeline EvalResult includes pre_check_result from context."""
    mock_precheck = MagicMock()
    pipeline = Pipeline(stages=[])
    ctx = EvalContext(skill_path="/test/skill.md")
    ctx.pre_check_result = mock_precheck

    result = _run(pipeline.execute(ctx))

    assert result.pre_check is mock_precheck
