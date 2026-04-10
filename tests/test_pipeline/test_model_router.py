"""Tests for md_evals.pipeline.model_router — per-stage LLM adapter factory.

Verifies ModelRouter creates, caches, and configures LLMAdapter instances
for each pipeline stage.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


from md_evals.pipeline.config import AuditorConfig, JudgeConfig, PipelineConfig, TargetConfig
from md_evals.pipeline.model_router import ModelRouter


# ── Helpers ──


def _make_defaults(model="gpt-4o", provider="openai", temperature=0.7):
    """Create a mock defaults object."""
    defaults = MagicMock()
    defaults.model = model
    defaults.provider = provider
    defaults.temperature = temperature
    return defaults


def _make_pipeline_config(**kwargs):
    """Create a PipelineConfig with optional overrides."""
    return PipelineConfig(**kwargs)


# ============================================================================
# 1. Basic Adapter Creation
# ============================================================================


@patch("md_evals.pipeline.model_router.LLMAdapter")
def test_router_returns_adapter_for_auditor(MockAdapter):
    """ModelRouter returns an adapter for the auditor stage."""
    instance = MagicMock()
    MockAdapter.return_value = instance

    defaults = _make_defaults()
    config = _make_pipeline_config()
    router = ModelRouter(defaults, config)

    adapter = router.get_adapter("auditor")

    assert adapter is instance
    MockAdapter.assert_called_once()


@patch("md_evals.pipeline.model_router.LLMAdapter")
def test_router_returns_adapter_for_each_stage(MockAdapter):
    """ModelRouter returns adapters for auditor, target, and judge."""
    MockAdapter.return_value = MagicMock()

    # Each stage has a different model to prevent caching
    config = _make_pipeline_config(
        auditor=AuditorConfig(model="model-a"),
        target=TargetConfig(model="model-b"),
        judge=JudgeConfig(model="model-c"),
    )
    defaults = _make_defaults()
    router = ModelRouter(defaults, config)

    router.get_adapter("auditor")
    router.get_adapter("target")
    router.get_adapter("judge")

    # Three distinct adapters created (different models)
    assert MockAdapter.call_count == 3


# ============================================================================
# 2. Fallback to Defaults
# ============================================================================


@patch("md_evals.pipeline.model_router.LLMAdapter")
def test_router_falls_back_to_defaults_when_stage_model_is_none(MockAdapter):
    """When stage model is None, router uses global default model/provider."""
    instance = MagicMock()
    MockAdapter.return_value = instance

    defaults = _make_defaults(model="default-model", provider="default-provider")
    config = _make_pipeline_config()  # no stage-specific models

    router = ModelRouter(defaults, config)
    router.get_adapter("auditor")

    # Should use default model/provider
    call_kwargs = MockAdapter.call_args
    assert call_kwargs.kwargs.get("model") == "default-model" or call_kwargs[1].get("model") == "default-model"


@patch("md_evals.pipeline.model_router.LLMAdapter")
def test_router_uses_stage_model_when_set(MockAdapter):
    """When stage has explicit model, it takes precedence over defaults."""
    MockAdapter.return_value = MagicMock()

    defaults = _make_defaults(model="default-model")
    config = _make_pipeline_config(
        auditor=AuditorConfig(model="custom-auditor-model"),
    )

    router = ModelRouter(defaults, config)
    router.get_adapter("auditor")

    call_kwargs = MockAdapter.call_args
    # Verify custom model used
    if call_kwargs.kwargs:
        assert call_kwargs.kwargs["model"] == "custom-auditor-model"
    else:
        assert call_kwargs[1]["model"] == "custom-auditor-model"


# ============================================================================
# 3. Caching
# ============================================================================


@patch("md_evals.pipeline.model_router.LLMAdapter")
def test_router_caches_same_model_provider(MockAdapter):
    """Same (model, provider) returns same adapter instance (caching)."""
    instance = MagicMock()
    MockAdapter.return_value = instance

    defaults = _make_defaults()
    config = _make_pipeline_config()  # all stages use defaults

    router = ModelRouter(defaults, config)
    a1 = router.get_adapter("auditor")
    a2 = router.get_adapter("target")

    # Same model/provider → cached → only one LLMAdapter created
    assert a1 is a2
    assert MockAdapter.call_count == 1


@patch("md_evals.pipeline.model_router.LLMAdapter")
def test_router_creates_different_adapters_for_different_models(MockAdapter):
    """Different models produce different adapter instances."""
    MockAdapter.side_effect = [MagicMock(), MagicMock()]

    defaults = _make_defaults()
    config = _make_pipeline_config(
        auditor=AuditorConfig(model="model-a"),
        judge=JudgeConfig(model="model-b"),
    )

    router = ModelRouter(defaults, config)
    a = router.get_adapter("auditor")
    j = router.get_adapter("judge")

    assert a is not j
    assert MockAdapter.call_count == 2


# ============================================================================
# 4. Temperature
# ============================================================================


def test_router_get_temperature_auditor():
    """Auditor temperature defaults to 0.8."""
    defaults = _make_defaults()
    config = _make_pipeline_config()
    router = ModelRouter(defaults, config)

    assert router.get_temperature("auditor") == 0.8


def test_router_get_temperature_judge():
    """Judge temperature defaults to 0.0."""
    defaults = _make_defaults()
    config = _make_pipeline_config()
    router = ModelRouter(defaults, config)

    assert router.get_temperature("judge") == 0.0


def test_router_get_temperature_unknown_stage():
    """Unknown stage falls back to global default temperature."""
    defaults = _make_defaults(temperature=0.7)
    config = _make_pipeline_config()
    router = ModelRouter(defaults, config)

    assert router.get_temperature("unknown") == 0.7
