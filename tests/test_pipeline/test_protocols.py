"""Tests for md_evals.pipeline.protocols — structural interfaces.

Verifies that runtime_checkable Protocol classes work correctly with
duck-typing: classes with the right shape satisfy the protocol, and
classes missing required methods do not.
"""

from __future__ import annotations

import asyncio

import pytest

from md_evals.pipeline.context import EvalContext, Scenario, StageResult
from md_evals.pipeline.protocols import Detector, PipelineStage, Probe
from md_evals.scoring import DimensionScore


# ── Concrete duck-typed implementations ──


class FakeStage:
    """Duck-typed PipelineStage (satisfies protocol without inheriting)."""

    @property
    def name(self) -> str:
        return "fake-stage"

    async def execute(self, context: EvalContext) -> StageResult:
        return StageResult(success=True, duration_ms=1)


class FakeProbe:
    """Duck-typed Probe."""

    @property
    def name(self) -> str:
        return "fake-probe"

    def generate_scenarios(self, skill, context) -> list[Scenario]:
        return [Scenario(probe_name="fake-probe", prompt="test")]


class FakeDetector:
    """Duck-typed Detector."""

    @property
    def name(self) -> str:
        return "fake-detector"

    @property
    def dimension(self) -> str:
        return "test-dim"

    def score(self, scenario, response, skill, context) -> DimensionScore:
        return DimensionScore(dimension="test-dim", score=0.8, weight=0.5, grade="B")


# ── Classes that break the protocol ──


class MissingExecuteStage:
    """Has name but no execute method."""

    @property
    def name(self) -> str:
        return "broken"


class MissingNameStage:
    """Has execute but no name property."""

    async def execute(self, context):
        return StageResult()


class MissingGenerateProbe:
    """Has name but no generate_scenarios method."""

    @property
    def name(self) -> str:
        return "broken"


class MissingScoreDetector:
    """Has name and dimension but no score method."""

    @property
    def name(self) -> str:
        return "broken"

    @property
    def dimension(self) -> str:
        return "broken"


class MissingDimensionDetector:
    """Has name and score but no dimension property."""

    @property
    def name(self) -> str:
        return "broken"

    def score(self, scenario, response, skill, context):
        return DimensionScore(dimension="x", score=0.0, weight=0.0, grade="F")


# ============================================================================
# PipelineStage Protocol Tests
# ============================================================================


def test_pipeline_stage_isinstance_valid():
    """A class with name+execute satisfies PipelineStage protocol."""
    stage = FakeStage()
    assert isinstance(stage, PipelineStage)


def test_pipeline_stage_isinstance_missing_execute():
    """A class missing execute() does NOT satisfy PipelineStage."""
    obj = MissingExecuteStage()
    assert not isinstance(obj, PipelineStage)


def test_pipeline_stage_isinstance_missing_name():
    """A class missing name property does NOT satisfy PipelineStage."""
    obj = MissingNameStage()
    assert not isinstance(obj, PipelineStage)


def test_pipeline_stage_execute_returns_stage_result():
    """Duck-typed stage execute returns a StageResult."""
    stage = FakeStage()
    result = asyncio.run(stage.execute(EvalContext()))
    assert isinstance(result, StageResult)
    assert result.success is True


def test_pipeline_stage_name_property():
    """Stage name is accessible as a property."""
    stage = FakeStage()
    assert stage.name == "fake-stage"


# ============================================================================
# Probe Protocol Tests
# ============================================================================


def test_probe_isinstance_valid():
    """A class with name+generate_scenarios satisfies Probe protocol."""
    probe = FakeProbe()
    assert isinstance(probe, Probe)


def test_probe_isinstance_missing_generate():
    """A class missing generate_scenarios does NOT satisfy Probe."""
    obj = MissingGenerateProbe()
    assert not isinstance(obj, Probe)


def test_probe_generate_scenarios_returns_list():
    """Duck-typed probe returns a list of Scenarios."""
    probe = FakeProbe()
    scenarios = probe.generate_scenarios(None, EvalContext())
    assert isinstance(scenarios, list)
    assert len(scenarios) == 1
    assert scenarios[0].probe_name == "fake-probe"


def test_probe_name_property():
    """Probe name is accessible as a property."""
    probe = FakeProbe()
    assert probe.name == "fake-probe"


# ============================================================================
# Detector Protocol Tests
# ============================================================================


def test_detector_isinstance_valid():
    """A class with name+dimension+score satisfies Detector protocol."""
    detector = FakeDetector()
    assert isinstance(detector, Detector)


def test_detector_isinstance_missing_score():
    """A class missing score() does NOT satisfy Detector."""
    obj = MissingScoreDetector()
    assert not isinstance(obj, Detector)


def test_detector_isinstance_missing_dimension():
    """A class missing dimension property does NOT satisfy Detector."""
    obj = MissingDimensionDetector()
    assert not isinstance(obj, Detector)


def test_detector_score_returns_dimension_score():
    """Duck-typed detector returns a DimensionScore."""
    detector = FakeDetector()
    scenario = Scenario(probe_name="test", prompt="test")
    ds = detector.score(scenario, "response", None, EvalContext())
    assert isinstance(ds, DimensionScore)
    assert ds.dimension == "test-dim"
    assert ds.score == 0.8


def test_detector_name_and_dimension_properties():
    """Detector name and dimension are accessible as properties."""
    detector = FakeDetector()
    assert detector.name == "fake-detector"
    assert detector.dimension == "test-dim"


# ============================================================================
# Edge Cases
# ============================================================================


def test_plain_dict_does_not_satisfy_any_protocol():
    """A plain dict does not satisfy any protocol."""
    obj = {"name": "foo", "execute": lambda ctx: None}
    assert not isinstance(obj, PipelineStage)
    assert not isinstance(obj, Probe)
    assert not isinstance(obj, Detector)
