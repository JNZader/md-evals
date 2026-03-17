"""Model router — per-stage LLM adapter factory and cache.

The :class:`ModelRouter` creates and caches :class:`LLMAdapter` instances
for each pipeline stage (auditor, target, judge).  When a stage has no
explicit model/provider configured, the router falls back to the global
defaults from ``eval.yaml``.

Design notes
------------
* **Adapter caching** (ADR-04): adapters are cached by ``(model, provider)``
  tuple.  If all three stages use the same model, only one adapter instance
  is created.
* **No runtime validation**: model availability is *not* checked at config
  time (would require API calls).  Validation happens at execution time
  with clear error messages containing the model name.
* **Reuses existing LLMAdapter**: no modifications to ``md_evals/llm.py``.
"""

from __future__ import annotations

import logging
from typing import Any

from md_evals.llm import LLMAdapter
from md_evals.pipeline.config import PipelineConfig, StageConfig

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes LLM requests to per-stage model configurations.

    Creates and caches :class:`LLMAdapter` instances keyed by
    ``(model, provider)``.  Each stage gets the adapter matching its
    configuration, or the global default if no stage-specific model is
    set.

    Args:
        defaults: Global defaults from ``eval.yaml`` (provides fallback
            ``model``, ``provider``, ``temperature``, etc.).
        pipeline_config: Pipeline configuration containing per-stage
            model/provider/temperature settings.

    Example
    -------
    >>> router = ModelRouter(defaults, pipeline_config)
    >>> auditor_llm = router.get_adapter("auditor")
    >>> judge_llm = router.get_adapter("judge")
    >>> auditor_llm is judge_llm  # True if same model/provider configured
    """

    def __init__(
        self,
        defaults: Any,
        pipeline_config: PipelineConfig,
    ) -> None:
        self.defaults = defaults
        self.pipeline_config = pipeline_config
        self._cache: dict[tuple[str, str], LLMAdapter] = {}

    def get_adapter(self, stage: str) -> LLMAdapter:
        """Get or create an :class:`LLMAdapter` for a pipeline stage.

        Resolves the model and provider from the stage config, falling
        back to global defaults.  Returns a cached instance if one
        exists for the same ``(model, provider)`` pair.

        Args:
            stage: Stage name — one of ``"auditor"``, ``"target"``,
                ``"judge"``.  Unknown stage names fall back to a bare
                ``StageConfig()`` (global defaults only).

        Returns:
            An :class:`LLMAdapter` configured for the requested stage.
        """
        stage_config = self._get_stage_config(stage)
        model = stage_config.model or self.defaults.model
        provider = stage_config.provider or self.defaults.provider

        cache_key = (model, provider)
        if cache_key not in self._cache:
            logger.debug(
                "ModelRouter: creating adapter for stage '%s' → %s/%s",
                stage,
                provider,
                model,
            )
            self._cache[cache_key] = LLMAdapter(
                model=model,
                provider=provider,
                defaults=self.defaults,
            )

        return self._cache[cache_key]

    def get_temperature(self, stage: str) -> float:
        """Get the sampling temperature for a pipeline stage.

        Returns the stage-specific temperature if configured, otherwise
        falls back to the global default temperature.

        Args:
            stage: Stage name — ``"auditor"``, ``"target"``, or ``"judge"``.

        Returns:
            Sampling temperature as a float.
        """
        stage_config = self._get_stage_config(stage)
        if stage_config.temperature is not None:
            return stage_config.temperature
        return getattr(self.defaults, "temperature", 0.7)

    def _get_stage_config(self, stage: str) -> StageConfig:
        """Look up the configuration for a specific stage.

        Args:
            stage: Stage name (case-sensitive).

        Returns:
            The stage-specific config, or a bare ``StageConfig`` with
            all defaults if the stage name is not recognised.
        """
        stage_map: dict[str, StageConfig] = {
            "auditor": self.pipeline_config.auditor,
            "target": self.pipeline_config.target,
            "judge": self.pipeline_config.judge,
        }
        return stage_map.get(stage, StageConfig())
