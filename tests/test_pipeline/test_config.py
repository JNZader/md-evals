"""Tests for md_evals.pipeline.config — Pydantic pipeline configuration.

Verifies default values and custom value construction for PipelineConfig,
AuditorConfig, TargetConfig, JudgeConfig, and StageConfig.
"""

from __future__ import annotations

import pytest

from md_evals.pipeline.config import (
    AuditorConfig,
    JudgeConfig,
    PipelineConfig,
    StageConfig,
    TargetConfig,
)


# ============================================================================
# 1. StageConfig Defaults
# ============================================================================


def test_stage_config_defaults():
    """StageConfig defaults: model=None, provider=None, temperature=None, timeout=300."""
    cfg = StageConfig()
    assert cfg.model is None
    assert cfg.provider is None
    assert cfg.temperature is None
    assert cfg.timeout == 300


def test_stage_config_custom_values():
    """StageConfig accepts custom model/provider/temperature/timeout."""
    cfg = StageConfig(model="gpt-4o", provider="openai", temperature=0.5, timeout=120)
    assert cfg.model == "gpt-4o"
    assert cfg.provider == "openai"
    assert cfg.temperature == 0.5
    assert cfg.timeout == 120


# ============================================================================
# 2. AuditorConfig Defaults
# ============================================================================


def test_auditor_config_defaults():
    """AuditorConfig defaults: temperature=0.8, scenarios_per_probe=3."""
    cfg = AuditorConfig()
    assert cfg.temperature == 0.8
    assert cfg.scenarios_per_probe == 3
    # Inherits StageConfig defaults
    assert cfg.model is None
    assert cfg.provider is None
    assert cfg.timeout == 300


def test_auditor_config_custom():
    """AuditorConfig accepts custom scenarios_per_probe and temperature."""
    cfg = AuditorConfig(scenarios_per_probe=5, temperature=1.0)
    assert cfg.scenarios_per_probe == 5
    assert cfg.temperature == 1.0


# ============================================================================
# 3. TargetConfig Defaults
# ============================================================================


def test_target_config_defaults():
    """TargetConfig defaults: max_concurrent=5."""
    cfg = TargetConfig()
    assert cfg.max_concurrent == 5
    assert cfg.temperature is None
    assert cfg.timeout == 300


def test_target_config_custom():
    """TargetConfig accepts custom max_concurrent."""
    cfg = TargetConfig(max_concurrent=10)
    assert cfg.max_concurrent == 10


# ============================================================================
# 4. JudgeConfig Defaults
# ============================================================================


def test_judge_config_defaults():
    """JudgeConfig defaults: temperature=0.0."""
    cfg = JudgeConfig()
    assert cfg.temperature == 0.0
    assert cfg.model is None
    assert cfg.provider is None


def test_judge_config_custom():
    """JudgeConfig accepts custom temperature."""
    cfg = JudgeConfig(temperature=0.2, model="claude-3-sonnet")
    assert cfg.temperature == 0.2
    assert cfg.model == "claude-3-sonnet"


# ============================================================================
# 5. PipelineConfig Defaults
# ============================================================================


def test_pipeline_config_defaults():
    """PipelineConfig defaults: enabled=False, halt_on_precheck_error=True."""
    cfg = PipelineConfig()
    assert cfg.enabled is False
    assert cfg.halt_on_precheck_error is True
    assert isinstance(cfg.auditor, AuditorConfig)
    assert isinstance(cfg.target, TargetConfig)
    assert isinstance(cfg.judge, JudgeConfig)
    assert cfg.probes == ["dimension", "edge-case", "compliance"]
    assert cfg.detectors == ["llm-judge", "format", "security"]


def test_pipeline_config_custom():
    """PipelineConfig accepts nested stage configs and custom probes/detectors."""
    cfg = PipelineConfig(
        enabled=True,
        halt_on_precheck_error=False,
        auditor=AuditorConfig(scenarios_per_probe=10),
        probes=["dimension"],
        detectors=["format"],
    )
    assert cfg.enabled is True
    assert cfg.halt_on_precheck_error is False
    assert cfg.auditor.scenarios_per_probe == 10
    assert cfg.probes == ["dimension"]
    assert cfg.detectors == ["format"]


def test_pipeline_config_from_dict():
    """PipelineConfig can be constructed from a raw dict (YAML deserialization)."""
    data = {
        "enabled": True,
        "auditor": {"temperature": 0.9, "scenarios_per_probe": 7},
        "target": {"max_concurrent": 3},
        "judge": {"temperature": 0.1},
        "probes": ["edge-case"],
        "detectors": ["security"],
    }
    cfg = PipelineConfig(**data)
    assert cfg.enabled is True
    assert cfg.auditor.temperature == 0.9
    assert cfg.auditor.scenarios_per_probe == 7
    assert cfg.target.max_concurrent == 3
    assert cfg.judge.temperature == 0.1
    assert cfg.probes == ["edge-case"]
    assert cfg.detectors == ["security"]
