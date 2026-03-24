"""Integration tests for pipeline runner — real code paths, mock only LLM calls.

This is the MOST IMPORTANT test file. pipeline/runner.py is at 30% coverage.
We test:
  - PipelineRunner construction
  - _build_probes / _build_detectors
  - Pipeline stage initialization and ordering
  - Pipeline.execute with real stages (PreCheckStage using real PreCheckEngine)
  - Pipeline._build_eval_result
  - Error handling and graceful degradation
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from md_evals.pipeline.config import PipelineConfig, AuditorConfig, TargetConfig, JudgeConfig
from md_evals.pipeline.context import EvalContext, Scenario, StageResult, StageError
from md_evals.pipeline.pipeline import Pipeline
from md_evals.pipeline.stages import PreCheckStage, AuditorStage, TargetStage, JudgeStage
from md_evals.precheck import PreCheckEngine
from md_evals.rubric import RubricConfig, DimensionConfig, RubricLoader
from md_evals.scoring import DimensionScore, EvalMetadata, EvalResult, calculate_overall_grade


FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_rubric() -> RubricConfig:
    return RubricConfig(
        version="1.0",
        dimensions={
            "correctness": DimensionConfig(weight=0.5, description="accuracy"),
            "format": DimensionConfig(weight=0.5, description="formatting"),
        },
        grade_thresholds={"S": 0.95, "A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30},
    )


def _make_pipeline_config(**overrides) -> PipelineConfig:
    defaults = dict(
        enabled=True,
        probes=["dimension"],
        detectors=["llm-judge"],
    )
    defaults.update(overrides)
    return PipelineConfig(**defaults)


def _make_eval_config():
    """Minimal mock EvalConfig with defaults attribute."""
    from md_evals.models import Defaults

    config = MagicMock()
    config.defaults = Defaults(model="gpt-4o", provider="openai")
    return config


class TestPipelineRunnerConstruction:
    """Test PipelineRunner can be constructed with valid configs."""

    def test_construction(self):
        from md_evals.pipeline.runner import PipelineRunner

        config = _make_eval_config()
        rubric = _make_rubric()
        pipeline_config = _make_pipeline_config()

        runner = PipelineRunner(config, rubric, pipeline_config)
        assert runner.config is config
        assert runner.rubric is rubric
        assert runner.pipeline_config is pipeline_config


class TestBuildProbes:
    """Test _build_probes method with real plugin discovery."""

    def test_build_dimension_probes(self):
        from md_evals.pipeline.runner import PipelineRunner

        rubric = _make_rubric()
        config = _make_eval_config()
        pipeline_config = _make_pipeline_config(probes=["dimension"])

        runner = PipelineRunner(config, rubric, pipeline_config)
        probes = runner._build_probes()
        # Should create one DimensionProbe per rubric dimension
        assert len(probes) == 2
        dims = {p._dimension for p in probes}
        assert dims == {"correctness", "format"}

    def test_build_probes_unknown_skipped(self):
        from md_evals.pipeline.runner import PipelineRunner

        rubric = _make_rubric()
        config = _make_eval_config()
        pipeline_config = _make_pipeline_config(probes=["nonexistent_probe"])

        runner = PipelineRunner(config, rubric, pipeline_config)
        probes = runner._build_probes()
        assert len(probes) == 0  # Unknown probes are skipped with warning

    def test_build_probes_empty_list(self):
        from md_evals.pipeline.runner import PipelineRunner

        rubric = _make_rubric()
        config = _make_eval_config()
        pipeline_config = _make_pipeline_config(probes=[])

        runner = PipelineRunner(config, rubric, pipeline_config)
        probes = runner._build_probes()
        assert len(probes) == 0


class TestBuildDetectors:
    """Test _build_detectors method with real plugin discovery."""

    def test_build_llm_judge_detectors(self):
        from md_evals.pipeline.runner import PipelineRunner

        rubric = _make_rubric()
        config = _make_eval_config()
        pipeline_config = _make_pipeline_config(detectors=["llm-judge"])

        runner = PipelineRunner(config, rubric, pipeline_config)
        detectors = runner._build_detectors()
        # Should create one LLMJudgeDetector per rubric dimension
        assert len(detectors) == 2

    def test_build_detectors_unknown_skipped(self):
        from md_evals.pipeline.runner import PipelineRunner

        rubric = _make_rubric()
        config = _make_eval_config()
        pipeline_config = _make_pipeline_config(detectors=["nonexistent_detector"])

        runner = PipelineRunner(config, rubric, pipeline_config)
        detectors = runner._build_detectors()
        assert len(detectors) == 0

    def test_build_detectors_empty_list(self):
        from md_evals.pipeline.runner import PipelineRunner

        rubric = _make_rubric()
        config = _make_eval_config()
        pipeline_config = _make_pipeline_config(detectors=[])

        runner = PipelineRunner(config, rubric, pipeline_config)
        detectors = runner._build_detectors()
        assert len(detectors) == 0


class TestPreCheckStageIntegration:
    """Test PreCheckStage with real PreCheckEngine and real files."""

    def test_precheck_valid_file(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        stage = PreCheckStage(engine, halt_on_error=True)

        context = EvalContext(skill_path=str(FIXTURES / "skill_valid.md"))
        result = asyncio.run(stage.execute(context))

        assert result.success is True
        assert context.pre_check_result is not None
        assert context.pre_check_result.passed is True

    def test_precheck_empty_file_halts(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        stage = PreCheckStage(engine, halt_on_error=True)

        context = EvalContext(skill_path=str(FIXTURES / "skill_invalid_empty.md"))
        result = asyncio.run(stage.execute(context))

        assert result.success is False
        assert context.pre_check_result is not None
        assert context.pre_check_result.passed is False

    def test_precheck_no_halt(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        stage = PreCheckStage(engine, halt_on_error=False)

        context = EvalContext(skill_path=str(FIXTURES / "skill_invalid_empty.md"))
        result = asyncio.run(stage.execute(context))

        assert result.success is True  # Don't halt even on failure

    def test_precheck_missing_file(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        stage = PreCheckStage(engine, halt_on_error=True)

        context = EvalContext(skill_path="/nonexistent/SKILL.md")
        result = asyncio.run(stage.execute(context))

        assert result.success is False


class TestPipelineExecuteIntegration:
    """Test Pipeline.execute with real stage wiring."""

    def test_pipeline_with_only_precheck(self):
        """Minimal pipeline: only precheck stage, real file."""
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        stages = [PreCheckStage(engine)]

        context = EvalContext(
            skill_path=str(FIXTURES / "skill_valid.md"),
            rubric=rubric,
        )
        pipeline = Pipeline(stages)
        result = asyncio.run(pipeline.execute(context))

        assert isinstance(result, EvalResult)
        assert result.skill_path == str(FIXTURES / "skill_valid.md")
        # No scores -> grade F (default when no judge runs)
        assert result.overall_grade == "F"
        assert result.overall_score == 0.0
        assert result.metadata.total_duration_ms >= 0

    def test_pipeline_graceful_degradation(self):
        """Stage that raises exception doesn't crash the pipeline."""

        class FailingStage:
            name = "failing"

            async def execute(self, context):
                raise RuntimeError("Stage exploded!")

        rubric = RubricLoader.load_default()
        context = EvalContext(
            skill_path=str(FIXTURES / "skill_valid.md"),
            rubric=rubric,
        )
        pipeline = Pipeline([FailingStage()])
        result = asyncio.run(pipeline.execute(context))

        assert isinstance(result, EvalResult)
        assert result.overall_grade == "F"
        assert len(context.errors) == 1
        assert context.errors[0].error_type == "RuntimeError"

    def test_pipeline_timeout_handling(self):
        """Stage that hangs gets timed out."""

        class HangingStage:
            name = "hanging"

            async def execute(self, context):
                await asyncio.sleep(10)
                return StageResult(success=True)

        rubric = RubricLoader.load_default()
        context = EvalContext(
            skill_path=str(FIXTURES / "skill_valid.md"),
            rubric=rubric,
        )
        pipeline = Pipeline([HangingStage()], timeout_per_stage=1)
        result = asyncio.run(pipeline.execute(context))

        assert isinstance(result, EvalResult)
        assert len(context.errors) == 1
        assert context.errors[0].error_type == "timeout"

    def test_pipeline_with_scores(self):
        """Pipeline with manually-set scores produces correct grades."""

        class ScoreInjector:
            name = "score-injector"

            async def execute(self, context):
                context.scores = [
                    DimensionScore(dimension="correctness", score=0.90, weight=0.5, grade="A"),
                    DimensionScore(dimension="format", score=0.80, weight=0.5, grade="B"),
                ]
                return StageResult(success=True)

        rubric = _make_rubric()
        context = EvalContext(
            skill_path="/test/SKILL.md",
            rubric=rubric,
        )
        pipeline = Pipeline([ScoreInjector()])
        result = asyncio.run(pipeline.execute(context))

        assert result.overall_score == pytest.approx(0.85)
        assert result.overall_grade == "A"

    def test_pipeline_multiple_stages_sequential(self):
        """Verify stages execute in order."""
        execution_order = []

        class OrderedStage:
            def __init__(self, stage_name):
                self.name = stage_name

            async def execute(self, context):
                execution_order.append(self.name)
                return StageResult(success=True)

        rubric = _make_rubric()
        context = EvalContext(skill_path="/test.md", rubric=rubric)
        stages = [OrderedStage("first"), OrderedStage("second"), OrderedStage("third")]
        pipeline = Pipeline(stages)
        asyncio.run(pipeline.execute(context))

        assert execution_order == ["first", "second", "third"]

    def test_pipeline_continues_after_stage_failure(self):
        """Verify pipeline continues to subsequent stages after one fails."""
        executed = []

        class PassStage:
            def __init__(self, n):
                self.name = f"pass-{n}"

            async def execute(self, context):
                executed.append(self.name)
                return StageResult(success=True)

        class FailStage:
            name = "fail"

            async def execute(self, context):
                executed.append(self.name)
                return StageResult(success=False, error="intentional failure")

        rubric = _make_rubric()
        context = EvalContext(skill_path="/test.md", rubric=rubric)
        pipeline = Pipeline([PassStage(1), FailStage(), PassStage(2)])
        asyncio.run(pipeline.execute(context))

        assert executed == ["pass-1", "fail", "pass-2"]
        assert len(context.errors) == 1


class TestPipelineConfig:
    """Test PipelineConfig defaults and construction."""

    def test_default_config(self):
        config = PipelineConfig()
        assert config.enabled is False
        assert config.halt_on_precheck_error is True
        assert "dimension" in config.probes
        assert "llm-judge" in config.detectors

    def test_auditor_defaults(self):
        config = PipelineConfig()
        assert config.auditor.temperature == 0.8
        assert config.auditor.scenarios_per_probe == 3

    def test_judge_defaults(self):
        config = PipelineConfig()
        assert config.judge.temperature == 0.0

    def test_target_defaults(self):
        config = PipelineConfig()
        assert config.target.max_concurrent == 5

    def test_custom_config(self):
        config = PipelineConfig(
            enabled=True,
            probes=["dimension"],
            detectors=["format"],
            target=TargetConfig(max_concurrent=10),
        )
        assert config.enabled is True
        assert config.target.max_concurrent == 10


class TestEvalContextConstruction:
    """Test EvalContext wiring."""

    def test_default_context(self):
        ctx = EvalContext()
        assert ctx.skill is None
        assert ctx.rubric is None
        assert ctx.scenarios == []
        assert ctx.responses == {}
        assert ctx.scores == []
        assert ctx.errors == []

    def test_context_with_skill_path(self):
        ctx = EvalContext(skill_path="/test/SKILL.md")
        assert ctx.skill_path == "/test/SKILL.md"

    def test_context_mutable(self):
        ctx = EvalContext()
        ctx.scenarios.append(Scenario(prompt="test"))
        ctx.responses["abc"] = "response"
        ctx.errors.append(StageError(stage_name="test", message="err"))
        assert len(ctx.scenarios) == 1
        assert len(ctx.responses) == 1
        assert len(ctx.errors) == 1


class TestSkillParser:
    """Test SkillParser with real fixture files."""

    def test_parse_valid_skill(self):
        from md_evals.pipeline.skill_parser import SkillParser

        skill = SkillParser.parse(str(FIXTURES / "skill_valid.md"))
        assert skill.title == "My Valid Skill"
        assert "valid skill" in skill.description.lower()
        assert len(skill.rules) >= 3
        assert len(skill.examples) >= 1

    def test_parse_short_skill(self):
        from md_evals.pipeline.skill_parser import SkillParser

        skill = SkillParser.parse(str(FIXTURES / "skill_short.md"))
        assert skill.title == "Example Skill"
        assert len(skill.rules) >= 1

    def test_parse_missing_file_raises(self):
        from md_evals.pipeline.skill_parser import SkillParser

        with pytest.raises(FileNotFoundError):
            SkillParser.parse("/nonexistent/SKILL.md")
