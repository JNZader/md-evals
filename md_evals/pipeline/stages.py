"""Pipeline stages — concrete implementations of :class:`PipelineStage`.

Provides four stages that compose the md-evals evaluation pipeline:

* :class:`PreCheckStage` — deterministic structural validation via
  :class:`~md_evals.precheck.PreCheckEngine`.
* :class:`AuditorStage` — scenario generation via probes.
* :class:`TargetStage` — concurrent LLM execution of scenarios.
* :class:`JudgeStage` — response scoring via detectors.

Each stage satisfies the :class:`~md_evals.pipeline.protocols.PipelineStage`
protocol (``name`` property + ``async execute(context)`` method) and follows
the design principle of never raising uncaught exceptions — errors are
captured in :class:`~md_evals.pipeline.context.StageResult` or appended
to ``EvalContext.errors``.

Design notes
------------
* Stages communicate exclusively through the mutable ``EvalContext``.
* ``TargetStage`` uses a bounded semaphore for concurrency control.
* ``JudgeStage`` aggregates per-detector scores into per-dimension scores
  by averaging within each dimension.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import TYPE_CHECKING

from md_evals.pipeline.context import EvalContext, Scenario, StageError, StageResult

if TYPE_CHECKING:
    from md_evals.pipeline.model_router import ModelRouter
    from md_evals.pipeline.protocols import Detector, Probe
    from md_evals.precheck import PreCheckEngine
    from md_evals.rubric import RubricConfig
    from md_evals.scoring import DimensionScore

logger = logging.getLogger(__name__)


# ─── PreCheckStage ───


class PreCheckStage:
    """Wraps existing :class:`PreCheckEngine` as a pipeline stage.

    Runs deterministic structural validation on the SKILL.md file and
    populates ``context.pre_check_result``.  When ``halt_on_error`` is
    ``True`` (the default), returns a failed :class:`StageResult` if the
    pre-check finds error-level findings, signalling the pipeline to skip
    subsequent stages.

    Args:
        precheck_engine: The pre-check engine instance to delegate to.
        halt_on_error: If ``True``, fail the stage when pre-check finds
            error-severity findings.
    """

    def __init__(
        self,
        precheck_engine: PreCheckEngine,
        halt_on_error: bool = True,
    ) -> None:
        self._engine = precheck_engine
        self._halt = halt_on_error

    @property
    def name(self) -> str:
        """Human-readable stage identifier."""
        return "pre-check"

    async def execute(self, context: EvalContext) -> StageResult:
        """Run pre-check.  Populates ``context.pre_check_result``.

        Args:
            context: The mutable evaluation context.

        Returns:
            A :class:`StageResult` — failed if pre-check found errors
            and ``halt_on_error`` is ``True``.
        """
        start = time.monotonic()

        try:
            result = self._engine.run(context.skill_path)
            context.pre_check_result = result
        except Exception as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            logger.error("PreCheckStage crashed: %s", exc)
            context.errors.append(
                StageError(
                    stage_name="pre-check",
                    error_type=type(exc).__name__,
                    message=f"Pre-check engine error: {exc}",
                )
            )
            return StageResult(
                success=False,
                duration_ms=elapsed,
                error=f"Pre-check engine error: {exc}",
            )

        elapsed = int((time.monotonic() - start) * 1000)

        if not result.passed and self._halt:
            return StageResult(
                success=False,
                duration_ms=elapsed,
                error="Pre-check failed with errors",
            )

        return StageResult(success=True, duration_ms=elapsed)


# ─── AuditorStage ───


class AuditorStage:
    """Runs probes to generate test scenarios.

    Iterates over the configured probes, calling each to produce
    :class:`Scenario` objects.  Failed probes are logged and recorded
    in ``context.errors`` but do not fail the stage.

    Populates ``context.scenarios`` and stores the auditor adapter
    and temperature in ``context.metadata`` for probes that need LLM
    access.

    Args:
        probes: List of :class:`Probe` implementations to run.
        model_router: Router for obtaining the auditor LLM adapter.
    """

    def __init__(
        self,
        probes: list[Probe],
        model_router: ModelRouter,
    ) -> None:
        self._probes = probes
        self._router = model_router

    @property
    def name(self) -> str:
        """Human-readable stage identifier."""
        return "auditor"

    async def execute(self, context: EvalContext) -> StageResult:
        """Generate scenarios via probes.  Populates ``context.scenarios``.

        Args:
            context: The mutable evaluation context.

        Returns:
            A :class:`StageResult` with ``scenario_count`` in ``data``.
        """
        start = time.monotonic()

        adapter = self._router.get_adapter("auditor")
        temp = self._router.get_temperature("auditor")

        # Store adapter in context so probes can use it for LLM calls
        context.metadata["auditor_adapter"] = adapter
        context.metadata["auditor_temperature"] = temp

        all_scenarios: list[Scenario] = []

        for probe in self._probes:
            try:
                scenarios = probe.generate_scenarios(context.skill, context)
                all_scenarios.extend(scenarios)
            except Exception as exc:
                probe_name = getattr(probe, "name", type(probe).__name__)
                logger.warning("Probe '%s' failed: %s", probe_name, exc)
                context.errors.append(
                    StageError(
                        stage_name="auditor",
                        error_type="probe_failure",
                        message=f"Probe '{probe_name}' failed: {exc}",
                    )
                )

        context.scenarios = all_scenarios
        elapsed = int((time.monotonic() - start) * 1000)

        return StageResult(
            success=True,
            duration_ms=elapsed,
            data={"scenario_count": len(all_scenarios)},
        )


# ─── TargetStage ───


class TargetStage:
    """Executes scenarios against the target LLM with skill as system prompt.

    Runs all scenarios concurrently (bounded by ``max_concurrent``) using
    :meth:`LLMAdapter.complete`.  The skill's raw content is injected as
    a system prompt.

    Populates ``context.responses`` — a mapping of scenario ID → response
    text.

    Args:
        model_router: Router for obtaining the target LLM adapter.
        max_concurrent: Maximum number of concurrent LLM calls.
    """

    def __init__(
        self,
        model_router: ModelRouter,
        max_concurrent: int = 5,
    ) -> None:
        self._router = model_router
        self._max_concurrent = max_concurrent

    @property
    def name(self) -> str:
        """Human-readable stage identifier."""
        return "target"

    async def execute(self, context: EvalContext) -> StageResult:
        """Run all scenarios.  Populates ``context.responses``.

        Args:
            context: The mutable evaluation context.

        Returns:
            A :class:`StageResult` with ``response_count`` in ``data``.
        """
        start = time.monotonic()

        if not context.scenarios:
            return StageResult(
                success=True,
                duration_ms=0,
                data={"response_count": 0},
            )

        adapter = self._router.get_adapter("target")
        temp = self._router.get_temperature("target")

        # Use skill raw content as system prompt
        skill_content = ""
        if context.skill is not None:
            skill_content = getattr(context.skill, "raw_content", "")

        system_prompt = (
            f"You are a helpful AI assistant.\n\n"
            f"Below is a skill that provides guidelines for your responses:\n"
            f"---\n{skill_content}\n---\n\n"
            f"Follow the skill guidelines above when responding to the user."
        ) if skill_content else None

        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def run_scenario(scenario: Scenario) -> None:
            async with semaphore:
                try:
                    response = await adapter.complete(
                        prompt=scenario.prompt,
                        system_prompt=system_prompt,
                        temperature=temp,
                        stage_type="target",
                    )
                    context.responses[scenario.id] = response.content
                except Exception as exc:
                    short_id = scenario.id[:8]
                    logger.warning(
                        "Scenario %s failed: %s", short_id, exc,
                    )
                    context.responses[scenario.id] = ""
                    context.errors.append(
                        StageError(
                            stage_name="target",
                            error_type="scenario_failure",
                            message=f"Scenario '{short_id}' failed: {exc}",
                        )
                    )

        tasks = [run_scenario(s) for s in context.scenarios]
        await asyncio.gather(*tasks)

        elapsed = int((time.monotonic() - start) * 1000)
        return StageResult(
            success=True,
            duration_ms=elapsed,
            data={"response_count": len(context.responses)},
        )


# ─── JudgeStage ───


class JudgeStage:
    """Runs detectors on (scenario, response) pairs and produces final scores.

    For each scenario, every detector is invoked to produce a
    :class:`DimensionScore`.  Individual detector failures are logged
    and recorded in ``context.errors`` but do not fail the stage.

    After scoring, results are aggregated per dimension by averaging
    scores within the same dimension, then stored in ``context.scores``.

    Args:
        detectors: List of :class:`Detector` implementations to run.
        model_router: Router for obtaining the judge LLM adapter.
        rubric: Rubric configuration for grade thresholds and dimensions.
    """

    def __init__(
        self,
        detectors: list[Detector],
        model_router: ModelRouter,
        rubric: RubricConfig,
    ) -> None:
        self._detectors = detectors
        self._router = model_router
        self._rubric = rubric

    @property
    def name(self) -> str:
        """Human-readable stage identifier."""
        return "judge"

    async def execute(self, context: EvalContext) -> StageResult:
        """Score responses.  Populates ``context.scores``.

        Runs all detectors on each (scenario, response) pair, aggregates
        scores per dimension, and stores judge model metadata in
        ``context.metadata``.

        Args:
            context: The mutable evaluation context.

        Returns:
            A :class:`StageResult` with timing information.
        """
        start = time.monotonic()

        adapter = self._router.get_adapter("judge")
        temp = self._router.get_temperature("judge")

        # Store judge adapter and temperature for detectors that need LLM
        context.metadata["judge_adapter"] = adapter
        context.metadata["judge_temperature"] = temp

        # Store judge model metadata
        judge_config = self._router._get_stage_config("judge")
        context.metadata["judge_model"] = (
            judge_config.model or getattr(self._router.defaults, "model", "default")
        )
        context.metadata["judge_provider"] = (
            judge_config.provider or getattr(self._router.defaults, "provider", "default")
        )

        # Collect all raw scores from detectors
        all_scores: list[DimensionScore] = []

        for scenario in context.scenarios:
            response = context.responses.get(scenario.id, "")

            for detector in self._detectors:
                try:
                    score = detector.score(
                        scenario=scenario,
                        response=response,
                        skill=context.skill,
                        context=context,
                    )
                    all_scores.append(score)
                except Exception as exc:
                    det_name = getattr(detector, "name", type(detector).__name__)
                    short_id = scenario.id[:8]
                    logger.warning(
                        "Detector '%s' failed on scenario %s: %s",
                        det_name,
                        short_id,
                        exc,
                    )
                    context.errors.append(
                        StageError(
                            stage_name="judge",
                            error_type="detector_failure",
                            message=(
                                f"Detector '{det_name}' failed on "
                                f"scenario '{short_id}': {exc}"
                            ),
                        )
                    )

        # Aggregate scores per dimension (average within each dimension)
        context.scores = _aggregate_dimension_scores(
            all_scores, self._rubric,
        )

        elapsed = int((time.monotonic() - start) * 1000)
        return StageResult(success=True, duration_ms=elapsed)


# ─── Helpers ───


def _aggregate_dimension_scores(
    raw_scores: list[DimensionScore],
    rubric: RubricConfig,
) -> list[DimensionScore]:
    """Aggregate per-detector scores into per-dimension averages.

    Groups scores by ``dimension``, computes the mean score for each
    group, looks up the rubric weight, and maps the average to a letter
    grade using the rubric thresholds.

    Dimensions present in the rubric but absent from ``raw_scores``
    receive a score of ``0.0``.

    Args:
        raw_scores: Flat list of scores from all detectors × scenarios.
        rubric: Rubric configuration for weights and thresholds.

    Returns:
        One :class:`DimensionScore` per rubric dimension, sorted by
        rubric iteration order.
    """
    from md_evals.scoring import DimensionScore, score_to_grade

    # Group raw scores by dimension
    by_dimension: dict[str, list[float]] = defaultdict(list)
    for s in raw_scores:
        by_dimension[s.dimension].append(s.score)

    aggregated: list[DimensionScore] = []

    for dim_name, dim_config in rubric.dimensions.items():
        scores = by_dimension.get(dim_name, [])
        avg_score = sum(scores) / len(scores) if scores else 0.0
        clamped = max(0.0, min(1.0, avg_score))
        grade = score_to_grade(clamped, rubric.grade_thresholds)

        aggregated.append(
            DimensionScore(
                dimension=dim_name,
                score=clamped,
                weight=dim_config.weight,
                grade=grade,
            )
        )

    return aggregated
