"""Pipeline configuration — Pydantic models for YAML-driven pipeline setup.

Defines the ``pipeline:`` section of ``eval.yaml`` as a hierarchy of
Pydantic ``BaseModel`` classes:

* :class:`StageConfig` — base config shared by all stages.
* :class:`AuditorConfig` — auditor-specific settings (creative temperature,
  scenarios per probe).
* :class:`TargetConfig` — target-specific settings (concurrency limit).
* :class:`JudgeConfig` — judge-specific settings (deterministic temperature).
* :class:`PipelineConfig` — top-level container with enable flag, halt
  behaviour, stage configs, and active probe/detector lists.

Default values
--------------
When the pipeline is enabled but stage-specific fields are omitted,
sensible defaults apply:

* Auditor temperature defaults to ``0.8`` (creative scenario generation).
* Judge temperature defaults to ``0.0`` (deterministic scoring).
* Target max_concurrent defaults to ``5``.
* Probes default to ``["dimension", "edge-case", "compliance"]``.
* Detectors default to ``["llm-judge", "format", "security"]``.

Model/provider fields that are ``None`` fall back to ``defaults.model``
and ``defaults.provider`` from ``eval.yaml`` at runtime (resolved by
:class:`~md_evals.pipeline.model_router.ModelRouter`).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StageConfig(BaseModel):
    """Base configuration for a pipeline stage.

    Provides model routing fields shared by all stages.  A ``None`` value
    for ``model`` or ``provider`` means "use the global defaults from
    ``eval.yaml``".

    Attributes:
        model: LLM model identifier, or ``None`` to use global default.
        provider: LLM provider name, or ``None`` to use global default.
        temperature: Sampling temperature override, or ``None`` for
            stage-specific default.
        timeout: Maximum execution time in seconds for this stage.
    """

    model: str | None = None
    provider: str | None = None
    temperature: float | None = None
    timeout: int = 300


class AuditorConfig(StageConfig):
    """Configuration for the auditor stage.

    The auditor uses probes to generate test scenarios.  A higher
    temperature (default ``0.8``) encourages creative, diverse scenario
    generation.

    Attributes:
        scenarios_per_probe: Number of scenarios each probe should
            generate per invocation.
        temperature: Defaults to ``0.8`` for creative generation.
    """

    scenarios_per_probe: int = 3
    temperature: float | None = 0.8


class TargetConfig(StageConfig):
    """Configuration for the target stage.

    The target stage executes each scenario by sending it to the target
    LLM with the skill injected as system prompt.  Scenarios may run
    concurrently up to ``max_concurrent``.

    Attributes:
        max_concurrent: Maximum number of scenarios to execute in
            parallel (bounded semaphore).
    """

    max_concurrent: int = 5


class JudgeConfig(StageConfig):
    """Configuration for the judge stage.

    The judge uses detectors to score each (scenario, response) pair.
    A temperature of ``0.0`` (default) produces deterministic,
    reproducible scores.

    Attributes:
        temperature: Defaults to ``0.0`` for deterministic scoring.
    """

    temperature: float | None = 0.0


class PipelineConfig(BaseModel):
    """Top-level pipeline configuration.

    Corresponds to the ``pipeline:`` section in ``eval.yaml``.  When
    ``enabled`` is ``False`` (or the section is absent), the CLI uses the
    existing single-model evaluation path.

    Attributes:
        enabled: Whether pipeline mode is active.  Can be overridden by
            ``--pipeline`` / ``--no-pipeline`` CLI flags.
        halt_on_precheck_error: If ``True``, skip Auditor/Target/Judge
            stages when pre-check finds error-level findings and return
            grade ``"F"`` immediately.
        auditor: Auditor stage configuration.
        target: Target stage configuration.
        judge: Judge stage configuration.
        probes: List of active probe names to use.  Names are resolved
            against built-in probes first, then ``entry_points`` plugins.
        detectors: List of active detector names to use.  Same resolution
            order as probes.
    """

    enabled: bool = False
    halt_on_precheck_error: bool = True
    auditor: AuditorConfig = Field(default_factory=AuditorConfig)
    target: TargetConfig = Field(default_factory=TargetConfig)
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    probes: list[str] = Field(
        default_factory=lambda: ["dimension", "edge-case", "compliance"],
    )
    detectors: list[str] = Field(
        default_factory=lambda: ["llm-judge", "format", "security"],
    )
