"""Tests for md_evals.pipeline.stages — concrete stage implementations.

Uses mocks for LLMAdapter and dependencies. Verifies PreCheckStage,
AuditorStage, TargetStage, and JudgeStage behavior.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from md_evals.pipeline.config import PipelineConfig
from md_evals.pipeline.context import EvalContext, Scenario, StageError, StageResult
from md_evals.pipeline.skill_parser import ParsedSkill
from md_evals.pipeline.stages import AuditorStage, JudgeStage, PreCheckStage, TargetStage
from md_evals.scoring import DimensionScore


# ── Helpers ──


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def _make_context(**kwargs):
    """Create a minimal EvalContext."""
    defaults = {
        "skill_path": "/fake/skill.md",
        "skill": ParsedSkill(raw_content="# Test", title="Test"),
    }
    defaults.update(kwargs)
    return EvalContext(**defaults)


def _make_mock_router():
    """Create a mock ModelRouter."""
    router = MagicMock()
    adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "LLM response content"
    adapter.complete = AsyncMock(return_value=mock_response)

    router.get_adapter.return_value = adapter
    router.get_temperature.return_value = 0.7
    router._get_stage_config.return_value = MagicMock(model="test-model", provider="test-provider")
    router.defaults = MagicMock(model="default-model", provider="default-provider")
    return router, adapter


def _make_rubric():
    """Create a mock RubricConfig."""
    from md_evals.rubric import RubricConfig, DimensionConfig

    return RubricConfig(
        dimensions={
            "correctness": DimensionConfig(weight=0.5, description="Accuracy"),
            "format": DimensionConfig(weight=0.5, description="Structure"),
        },
        grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30},
    )


# ============================================================================
# 1. PreCheckStage Tests
# ============================================================================


def test_precheck_stage_name():
    """PreCheckStage.name is 'pre-check'."""
    engine = MagicMock()
    stage = PreCheckStage(engine)
    assert stage.name == "pre-check"


def test_precheck_stage_passes_clean_file():
    """PreCheckStage succeeds when pre-check passes."""
    engine = MagicMock()
    result_mock = MagicMock()
    result_mock.passed = True
    engine.run.return_value = result_mock

    stage = PreCheckStage(engine, halt_on_error=True)
    ctx = _make_context()

    result = _run(stage.execute(ctx))

    assert result.success is True
    assert ctx.pre_check_result is result_mock


def test_precheck_stage_fails_dirty_file_halt_mode():
    """PreCheckStage fails when pre-check finds errors and halt=True."""
    engine = MagicMock()
    result_mock = MagicMock()
    result_mock.passed = False
    engine.run.return_value = result_mock

    stage = PreCheckStage(engine, halt_on_error=True)
    ctx = _make_context()

    result = _run(stage.execute(ctx))

    assert result.success is False
    assert "failed" in result.error.lower()
    assert ctx.pre_check_result is result_mock  # still populated


def test_precheck_stage_continues_dirty_file_non_halt():
    """PreCheckStage succeeds even on pre-check failure when halt=False."""
    engine = MagicMock()
    result_mock = MagicMock()
    result_mock.passed = False
    engine.run.return_value = result_mock

    stage = PreCheckStage(engine, halt_on_error=False)
    ctx = _make_context()

    result = _run(stage.execute(ctx))

    assert result.success is True  # continues despite failures


def test_precheck_stage_engine_exception():
    """PreCheckStage handles engine exceptions gracefully."""
    engine = MagicMock()
    engine.run.side_effect = RuntimeError("Engine crash")

    stage = PreCheckStage(engine, halt_on_error=True)
    ctx = _make_context()

    result = _run(stage.execute(ctx))

    assert result.success is False
    assert "Engine crash" in result.error
    assert len(ctx.errors) == 1
    assert ctx.errors[0].error_type == "RuntimeError"


# ============================================================================
# 2. AuditorStage Tests
# ============================================================================


def test_auditor_stage_name():
    """AuditorStage.name is 'auditor'."""
    router, _ = _make_mock_router()
    stage = AuditorStage(probes=[], model_router=router)
    assert stage.name == "auditor"


def test_auditor_stage_runs_probes():
    """AuditorStage calls each probe and collects scenarios."""
    router, _ = _make_mock_router()

    probe1 = MagicMock()
    probe1.generate_scenarios.return_value = [
        Scenario(probe_name="p1", prompt="s1"),
    ]
    probe2 = MagicMock()
    probe2.generate_scenarios.return_value = [
        Scenario(probe_name="p2", prompt="s2"),
        Scenario(probe_name="p2", prompt="s3"),
    ]

    stage = AuditorStage(probes=[probe1, probe2], model_router=router)
    ctx = _make_context()

    result = _run(stage.execute(ctx))

    assert result.success is True
    assert len(ctx.scenarios) == 3
    assert result.data["scenario_count"] == 3


def test_auditor_stage_stores_adapter_in_metadata():
    """AuditorStage stores auditor_adapter in context.metadata."""
    router, adapter = _make_mock_router()
    stage = AuditorStage(probes=[], model_router=router)
    ctx = _make_context()

    _run(stage.execute(ctx))

    assert ctx.metadata["auditor_adapter"] is adapter


def test_auditor_stage_handles_probe_failure():
    """AuditorStage records probe failure but continues."""
    router, _ = _make_mock_router()

    good_probe = MagicMock()
    good_probe.generate_scenarios.return_value = [
        Scenario(probe_name="good", prompt="ok"),
    ]
    bad_probe = MagicMock()
    bad_probe.name = "bad-probe"
    bad_probe.generate_scenarios.side_effect = ValueError("Probe crashed")

    stage = AuditorStage(probes=[bad_probe, good_probe], model_router=router)
    ctx = _make_context()

    result = _run(stage.execute(ctx))

    assert result.success is True  # stage doesn't fail
    assert len(ctx.scenarios) == 1  # only from good probe
    assert len(ctx.errors) == 1
    assert "bad-probe" in ctx.errors[0].message


# ============================================================================
# 3. TargetStage Tests
# ============================================================================


def test_target_stage_name():
    """TargetStage.name is 'target'."""
    router, _ = _make_mock_router()
    stage = TargetStage(model_router=router)
    assert stage.name == "target"


def test_target_stage_executes_scenarios():
    """TargetStage sends each scenario to the LLM and populates responses."""
    router, adapter = _make_mock_router()
    stage = TargetStage(model_router=router, max_concurrent=2)

    s1 = Scenario(id="s1", probe_name="test", prompt="Hello")
    s2 = Scenario(id="s2", probe_name="test", prompt="World")

    ctx = _make_context()
    ctx.scenarios = [s1, s2]

    result = _run(stage.execute(ctx))

    assert result.success is True
    assert result.data["response_count"] == 2
    assert "s1" in ctx.responses
    assert "s2" in ctx.responses
    assert adapter.complete.call_count == 2


def test_target_stage_empty_scenarios():
    """TargetStage returns immediately with empty scenarios."""
    router, adapter = _make_mock_router()
    stage = TargetStage(model_router=router)
    ctx = _make_context()
    ctx.scenarios = []

    result = _run(stage.execute(ctx))

    assert result.success is True
    assert result.data["response_count"] == 0
    adapter.complete.assert_not_called()


def test_target_stage_handles_llm_failure():
    """TargetStage records empty response on LLM failure."""
    router, adapter = _make_mock_router()
    adapter.complete.side_effect = RuntimeError("API timeout")

    stage = TargetStage(model_router=router)
    s1 = Scenario(id="fail-id", probe_name="test", prompt="Hello")

    ctx = _make_context()
    ctx.scenarios = [s1]

    result = _run(stage.execute(ctx))

    assert result.success is True  # stage doesn't fail
    assert ctx.responses["fail-id"] == ""  # empty response
    assert len(ctx.errors) == 1
    assert "fail-id" in ctx.errors[0].message


# ============================================================================
# 4. JudgeStage Tests
# ============================================================================


def test_judge_stage_name():
    """JudgeStage.name is 'judge'."""
    router, _ = _make_mock_router()
    rubric = _make_rubric()
    stage = JudgeStage(detectors=[], model_router=router, rubric=rubric)
    assert stage.name == "judge"


def test_judge_stage_runs_detectors():
    """JudgeStage runs all detectors on each scenario and produces scores."""
    router, _ = _make_mock_router()
    rubric = _make_rubric()

    detector = MagicMock()
    detector.name = "test-detector"
    detector.score.return_value = DimensionScore(
        dimension="correctness", score=0.9, weight=0.5, grade="A",
    )

    s1 = Scenario(id="s1", probe_name="test", prompt="Hello")
    ctx = _make_context()
    ctx.scenarios = [s1]
    ctx.responses = {"s1": "Good answer"}

    stage = JudgeStage(detectors=[detector], model_router=router, rubric=rubric)
    result = _run(stage.execute(ctx))

    assert result.success is True
    assert len(ctx.scores) > 0  # aggregated scores
    detector.score.assert_called_once()


def test_judge_stage_handles_detector_failure():
    """JudgeStage records detector failure but continues."""
    router, _ = _make_mock_router()
    rubric = _make_rubric()

    bad_detector = MagicMock()
    bad_detector.name = "bad-detector"
    bad_detector.score.side_effect = ValueError("Detector crashed")

    good_detector = MagicMock()
    good_detector.name = "good-detector"
    good_detector.score.return_value = DimensionScore(
        dimension="format", score=0.8, weight=0.5, grade="B",
    )

    s1 = Scenario(id="s1", probe_name="test", prompt="Hello")
    ctx = _make_context()
    ctx.scenarios = [s1]
    ctx.responses = {"s1": "Answer"}

    stage = JudgeStage(
        detectors=[bad_detector, good_detector],
        model_router=router,
        rubric=rubric,
    )
    result = _run(stage.execute(ctx))

    assert result.success is True
    assert len(ctx.errors) == 1
    assert "bad-detector" in ctx.errors[0].message


def test_judge_stage_stores_metadata():
    """JudgeStage stores judge model metadata in context."""
    router, _ = _make_mock_router()
    rubric = _make_rubric()
    stage = JudgeStage(detectors=[], model_router=router, rubric=rubric)
    ctx = _make_context()
    ctx.scenarios = []
    ctx.responses = {}

    _run(stage.execute(ctx))

    assert "judge_adapter" in ctx.metadata
    assert "judge_model" in ctx.metadata
    assert "judge_provider" in ctx.metadata


def test_judge_stage_produces_valid_dimension_scores():
    """JudgeStage produces DimensionScore objects matching rubric dimensions."""
    router, _ = _make_mock_router()
    rubric = _make_rubric()

    detector = MagicMock()
    detector.name = "det"
    detector.score.return_value = DimensionScore(
        dimension="correctness", score=0.85, weight=0.5, grade="A",
    )

    s1 = Scenario(id="s1", probe_name="test", prompt="Hello")
    ctx = _make_context(rubric=rubric)
    ctx.scenarios = [s1]
    ctx.responses = {"s1": "Answer"}

    stage = JudgeStage(detectors=[detector], model_router=router, rubric=rubric)
    _run(stage.execute(ctx))

    # Should have one score per rubric dimension
    assert len(ctx.scores) == 2  # correctness + format
    dims = {s.dimension for s in ctx.scores}
    assert "correctness" in dims
    assert "format" in dims
