"""Tests for md_evals.pipeline.context — value objects and mutable context.

Verifies Scenario (frozen), StageResult (frozen), StageError (frozen),
and EvalContext (mutable) dataclass contracts.
"""

from __future__ import annotations

import uuid
from dataclasses import FrozenInstanceError

import pytest

from md_evals.pipeline.context import EvalContext, Scenario, StageError, StageResult


# ============================================================================
# 1. Scenario Tests
# ============================================================================


def test_scenario_construction_with_defaults():
    """Scenario can be created with all defaults."""
    s = Scenario()
    assert s.probe_name == ""
    assert s.prompt == ""
    assert s.expected_behavior == ""
    assert s.dimension == ""
    assert s.metadata == {}
    assert s.id != ""  # UUID generated


def test_scenario_uuid_generation():
    """Each Scenario gets a unique UUID by default."""
    s1 = Scenario()
    s2 = Scenario()
    assert s1.id != s2.id
    # Verify it's a valid UUID
    uuid.UUID(s1.id)  # raises ValueError if invalid


def test_scenario_frozen_immutability():
    """Scenario fields cannot be reassigned."""
    s = Scenario(probe_name="test", prompt="hello")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        s.prompt = "changed"  # type: ignore[misc]


def test_scenario_with_all_fields():
    """Scenario can be constructed with all fields."""
    s = Scenario(
        id="custom-id",
        probe_name="dimension",
        prompt="What is 2+2?",
        expected_behavior="Answer 4",
        dimension="correctness",
        metadata={"source": "llm"},
    )
    assert s.id == "custom-id"
    assert s.probe_name == "dimension"
    assert s.prompt == "What is 2+2?"
    assert s.expected_behavior == "Answer 4"
    assert s.dimension == "correctness"
    assert s.metadata == {"source": "llm"}


# ============================================================================
# 2. StageResult Tests
# ============================================================================


def test_stage_result_defaults():
    """StageResult defaults to success=True, duration_ms=0, no error."""
    r = StageResult()
    assert r.success is True
    assert r.duration_ms == 0
    assert r.error is None
    assert r.data == {}


def test_stage_result_with_error():
    """StageResult can carry failure information."""
    r = StageResult(success=False, duration_ms=500, error="Something broke")
    assert r.success is False
    assert r.duration_ms == 500
    assert r.error == "Something broke"


def test_stage_result_frozen():
    """StageResult is frozen and cannot be mutated."""
    r = StageResult(success=True)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        r.success = False  # type: ignore[misc]


def test_stage_result_with_data():
    """StageResult.data carries stage-specific output."""
    r = StageResult(success=True, data={"scenario_count": 5})
    assert r.data["scenario_count"] == 5


# ============================================================================
# 3. StageError Tests
# ============================================================================


def test_stage_error_construction():
    """StageError can be created with all fields."""
    err = StageError(
        stage_name="auditor",
        error_type="probe_failure",
        message="Probe 'X' failed",
        timestamp="2026-03-17T10:00:00Z",
    )
    assert err.stage_name == "auditor"
    assert err.error_type == "probe_failure"
    assert err.message == "Probe 'X' failed"
    assert err.timestamp == "2026-03-17T10:00:00Z"


def test_stage_error_defaults():
    """StageError defaults to empty strings."""
    err = StageError()
    assert err.stage_name == ""
    assert err.error_type == ""
    assert err.message == ""
    assert err.timestamp == ""


def test_stage_error_frozen():
    """StageError is frozen and cannot be mutated."""
    err = StageError(stage_name="test")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        err.stage_name = "changed"  # type: ignore[misc]


# ============================================================================
# 4. EvalContext Tests
# ============================================================================


def test_eval_context_default_construction():
    """EvalContext is created with None inputs and empty collections."""
    ctx = EvalContext()
    assert ctx.skill is None
    assert ctx.rubric is None
    assert ctx.pipeline_config is None
    assert ctx.skill_path == ""
    assert ctx.pre_check_result is None
    assert ctx.scenarios == []
    assert ctx.responses == {}
    assert ctx.scores == []
    assert ctx.metadata == {}
    assert ctx.errors == []


def test_eval_context_add_scenarios():
    """EvalContext.scenarios can be mutated — list append works."""
    ctx = EvalContext()
    s1 = Scenario(probe_name="test", prompt="p1")
    s2 = Scenario(probe_name="test", prompt="p2")
    ctx.scenarios.append(s1)
    ctx.scenarios.append(s2)
    assert len(ctx.scenarios) == 2
    assert ctx.scenarios[0].prompt == "p1"


def test_eval_context_add_responses():
    """EvalContext.responses can be mutated — dict assignment works."""
    ctx = EvalContext()
    ctx.responses["scenario-1"] = "Hello world"
    ctx.responses["scenario-2"] = "Goodbye"
    assert len(ctx.responses) == 2
    assert ctx.responses["scenario-1"] == "Hello world"


def test_eval_context_add_errors():
    """EvalContext.errors can be appended."""
    ctx = EvalContext()
    err = StageError(stage_name="target", error_type="timeout", message="Timed out")
    ctx.errors.append(err)
    assert len(ctx.errors) == 1
    assert ctx.errors[0].stage_name == "target"


def test_eval_context_replace_scores():
    """EvalContext.scores can be replaced wholesale."""
    from md_evals.scoring import DimensionScore

    ctx = EvalContext()
    new_scores = [
        DimensionScore(dimension="format", score=0.9, weight=0.2, grade="A"),
    ]
    ctx.scores = new_scores
    assert len(ctx.scores) == 1
    assert ctx.scores[0].dimension == "format"


def test_eval_context_set_pre_check_result():
    """EvalContext.pre_check_result can be set after construction."""
    ctx = EvalContext()
    assert ctx.pre_check_result is None
    ctx.pre_check_result = {"passed": True}
    assert ctx.pre_check_result == {"passed": True}


def test_eval_context_is_mutable():
    """EvalContext is NOT frozen — all fields can be reassigned."""
    ctx = EvalContext()
    ctx.skill_path = "/new/path.md"
    ctx.metadata["key"] = "value"
    assert ctx.skill_path == "/new/path.md"
    assert ctx.metadata["key"] == "value"
