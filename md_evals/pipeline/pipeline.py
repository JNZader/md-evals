"""Pipeline orchestrator — sequential stage execution with graceful degradation.

The :class:`Pipeline` executor runs a list of stages sequentially,
threading a shared :class:`EvalContext` through each one.  It enforces
per-stage timeouts, catches exceptions, records errors, and always
produces a valid :class:`EvalResult` — even when every stage fails
(grade ``"F"`` with all errors recorded).

Design notes
------------
* **Degrade, don't crash** (design.md §7): a stage failure logs the
  error, appends a ``StageError``, and continues to the next stage.
* **Async with sequential stages** (ADR-03): stages execute one at a
  time because they have data dependencies.  Intra-stage parallelism
  (e.g. concurrent LLM calls inside ``TargetStage``) is the
  responsibility of each stage.
* **Timeout enforcement**: ``asyncio.wait_for`` wraps each stage with a
  configurable per-stage timeout.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from md_evals.pipeline.context import EvalContext, StageError
from md_evals.scoring import (
    DimensionScore,
    EvalMetadata,
    EvalResult,
    calculate_overall_grade,
)

logger = logging.getLogger(__name__)


class Pipeline:
    """Sequential pipeline executor.

    Runs an ordered list of stages against a shared ``EvalContext`` and
    assembles the final ``EvalResult``.

    Args:
        stages: Ordered list of objects satisfying the
            :class:`~md_evals.pipeline.protocols.PipelineStage` protocol.
        timeout_per_stage: Default timeout in seconds applied to each stage
            via ``asyncio.wait_for``.  Individual stages may override this
            via their own config.

    Example
    -------
    >>> pipeline = Pipeline(stages=[precheck, auditor, target, judge])
    >>> result = await pipeline.execute(context)
    >>> print(result.overall_grade)
    """

    def __init__(
        self,
        stages: list[Any],
        timeout_per_stage: int = 300,
    ) -> None:
        self.stages = stages
        self.timeout_per_stage = timeout_per_stage

    async def execute(self, context: EvalContext) -> EvalResult:
        """Run all stages sequentially, returning an ``EvalResult``.

        Each stage is wrapped with:

        1. **Timeout** — ``asyncio.wait_for`` with ``timeout_per_stage`` seconds.
        2. **Exception guard** — any unhandled exception is caught, logged,
           and recorded as a ``StageError`` on the context.
        3. **Failure recording** — if the stage returns
           ``StageResult(success=False)``, the error is recorded but
           execution continues to the next stage.

        Args:
            context: The mutable evaluation context.  Must have ``skill_path``
                set; other fields are populated by stages.

        Returns:
            A fully-populated ``EvalResult`` with overall grade, dimension
            scores, pre-check result, and execution metadata.
        """
        total_start = time.monotonic()

        for stage in self.stages:
            stage_name = getattr(stage, "name", type(stage).__name__)
            logger.debug("Pipeline: starting stage '%s'", stage_name)
            stage_start = time.monotonic()

            try:
                result = await asyncio.wait_for(
                    stage.execute(context),
                    timeout=self.timeout_per_stage,
                )

                stage_ms = int((time.monotonic() - stage_start) * 1000)
                logger.debug(
                    "Pipeline: stage '%s' completed in %dms (success=%s)",
                    stage_name,
                    stage_ms,
                    result.success,
                )

                if not result.success:
                    logger.warning(
                        "Pipeline: stage '%s' failed: %s",
                        stage_name,
                        result.error,
                    )
                    context.errors.append(
                        StageError(
                            stage_name=stage_name,
                            error_type="stage_failure",
                            message=result.error or "Unknown error",
                        )
                    )
                    # Continue to next stage — graceful degradation

            except asyncio.TimeoutError:
                stage_ms = int((time.monotonic() - stage_start) * 1000)
                logger.error(
                    "Pipeline: stage '%s' timed out after %ds (%dms elapsed)",
                    stage_name,
                    self.timeout_per_stage,
                    stage_ms,
                )
                context.errors.append(
                    StageError(
                        stage_name=stage_name,
                        error_type="timeout",
                        message=f"Stage timed out after {self.timeout_per_stage}s",
                    )
                )

            except Exception as exc:
                stage_ms = int((time.monotonic() - stage_start) * 1000)
                logger.error(
                    "Pipeline: stage '%s' raised %s: %s (%dms elapsed)",
                    stage_name,
                    type(exc).__name__,
                    exc,
                    stage_ms,
                )
                context.errors.append(
                    StageError(
                        stage_name=stage_name,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        total_ms = int((time.monotonic() - total_start) * 1000)
        return self._build_eval_result(context, total_ms)

    # ── Private helpers ──

    def _build_eval_result(
        self,
        context: EvalContext,
        total_ms: int,
    ) -> EvalResult:
        """Assemble an ``EvalResult`` from the pipeline context.

        If dimension scores are available, computes the weighted-average
        overall score and maps it to a letter grade using rubric thresholds.
        If no scores exist (e.g. all stages failed), defaults to score 0.0
        and grade ``"F"``.

        Args:
            context: The evaluated pipeline context.
            total_ms: Total wall-clock execution time in milliseconds.

        Returns:
            A fully-populated ``EvalResult``.
        """
        dimensions: list[DimensionScore] = (
            context.scores if context.scores else []
        )

        if dimensions:
            thresholds: dict[str, float] = {}
            if context.rubric is not None:
                thresholds = context.rubric.grade_thresholds
            overall_score, overall_grade = calculate_overall_grade(
                dimensions, thresholds
            )
        else:
            overall_score = 0.0
            overall_grade = "F"

        metadata = EvalMetadata(
            model=context.metadata.get("judge_model", "unknown"),
            provider=context.metadata.get("judge_provider", "unknown"),
            total_duration_ms=total_ms,
        )

        return EvalResult(
            skill_path=context.skill_path,
            overall_grade=overall_grade,
            overall_score=overall_score,
            dimensions=dimensions,
            pre_check=context.pre_check_result,
            metadata=metadata,
        )
