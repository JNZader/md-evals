"""PipelineRunner — assembles and executes the full evaluation pipeline.

Top-level entry point that wires together:

1. Skill parsing (``SkillParser``)
2. Model routing (``ModelRouter``)
3. Probe instantiation (via ``discover_probes``)
4. Detector instantiation (via ``discover_detectors``)
5. Pipeline stage construction and execution

Callers create a ``PipelineRunner`` with an ``EvalConfig``, a
``RubricConfig``, and a ``PipelineConfig``, then call :meth:`run` (async)
or :meth:`run_sync` (blocking) with a skill path.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from md_evals.pipeline.config import PipelineConfig
from md_evals.pipeline.context import EvalContext
from md_evals.pipeline.model_router import ModelRouter
from md_evals.pipeline.pipeline import Pipeline
from md_evals.pipeline.plugins import discover_probes, discover_detectors
from md_evals.pipeline.probes import DimensionProbe
from md_evals.pipeline.skill_parser import SkillParser
from md_evals.pipeline.stages import PreCheckStage, AuditorStage, TargetStage, JudgeStage
from md_evals.precheck import PreCheckEngine
from md_evals.rubric import RubricConfig
from md_evals.scoring import EvalResult

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Top-level runner that assembles and executes the pipeline.

    Args:
        config: The top-level ``EvalConfig`` (provides ``defaults`` for
            model/provider fallback).
        rubric: Rubric configuration for grading and dimensions.
        pipeline_config: Pipeline-specific configuration (stages, probes,
            detectors, concurrency, etc.).
    """

    def __init__(
        self,
        config: Any,  # EvalConfig — use Any to avoid circular imports
        rubric: RubricConfig,
        pipeline_config: PipelineConfig,
    ):
        self.config = config
        self.rubric = rubric
        self.pipeline_config = pipeline_config

    async def run(self, skill_path: str) -> EvalResult:
        """Run the full pipeline on a SKILL.md file.

        Parses the skill, builds probes/detectors/stages, constructs the
        evaluation context, and executes the pipeline.

        Args:
            skill_path: Filesystem path to the SKILL.md file.

        Returns:
            A fully-populated ``EvalResult`` with overall grade, dimension
            scores, pre-check result, and execution metadata.
        """
        # 1. Parse skill
        skill = SkillParser.parse(skill_path)

        # 2. Create model router
        router = ModelRouter(self.config.defaults, self.pipeline_config)

        # 3. Build probes
        probes = self._build_probes()

        # 4. Build detectors
        detectors = self._build_detectors()

        # 5. Build stages
        precheck_engine = PreCheckEngine(self.rubric)
        stages = [
            PreCheckStage(
                precheck_engine,
                halt_on_error=self.pipeline_config.halt_on_precheck_error,
            ),
            AuditorStage(probes, router),
            TargetStage(
                router,
                max_concurrent=self.pipeline_config.target.max_concurrent,
            ),
            JudgeStage(detectors, router, self.rubric),
        ]

        # 6. Build context
        context = EvalContext(
            skill=skill,
            rubric=self.rubric,
            pipeline_config=self.pipeline_config,
            skill_path=skill_path,
        )

        # 7. Execute pipeline
        pipeline = Pipeline(stages)
        return await pipeline.execute(context)

    def _build_probes(self) -> list:
        """Build probe instances from config.

        For the ``"dimension"`` probe, creates one ``DimensionProbe``
        per rubric dimension.  Other probes are instantiated with
        default arguments.

        Returns:
            List of probe instances.
        """
        available = discover_probes()
        probes: list = []

        for probe_name in self.pipeline_config.probes:
            if probe_name == "dimension":
                # Create one DimensionProbe per rubric dimension
                for dim_name, dim_config in self.rubric.dimensions.items():
                    probes.append(DimensionProbe(
                        dimension=dim_name,
                        description=dim_config.description,
                    ))
            elif probe_name in available:
                probe_class = available[probe_name]
                probes.append(probe_class())
            else:
                logger.warning("Unknown probe '%s', skipping", probe_name)

        return probes

    def _build_detectors(self) -> list:
        """Build detector instances from config.

        For the ``"llm-judge"`` detector, creates one
        ``LLMJudgeDetector`` per rubric dimension.  Other detectors
        are instantiated with default arguments.

        Returns:
            List of detector instances.
        """
        available = discover_detectors()
        detectors: list = []

        for det_name in self.pipeline_config.detectors:
            if det_name in available:
                det_class = available[det_name]
                if det_name == "llm-judge":
                    # Create one per rubric dimension
                    for dim_name in self.rubric.dimensions:
                        detectors.append(det_class(target_dimension=dim_name))
                else:
                    detectors.append(det_class())
            else:
                logger.warning("Unknown detector '%s', skipping", det_name)

        return detectors

    def run_sync(self, skill_path: str) -> EvalResult:
        """Sync wrapper for running the pipeline.

        Convenience method that calls :meth:`run` inside
        ``asyncio.run``.

        Args:
            skill_path: Filesystem path to the SKILL.md file.

        Returns:
            A fully-populated ``EvalResult``.
        """
        return asyncio.run(self.run(skill_path))
