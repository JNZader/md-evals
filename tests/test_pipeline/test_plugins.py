"""Tests for md_evals.pipeline.plugins — probe and detector discovery.

Verifies that built-in probes/detectors are discovered, caching works,
and unknown plugins are handled gracefully.
"""

from __future__ import annotations

import pytest

from md_evals.pipeline.plugins import (
    BUILTIN_DETECTORS,
    BUILTIN_PROBES,
    clear_cache,
    discover_detectors,
    discover_probes,
)
from md_evals.pipeline.probes import ComplianceProbe, DimensionProbe, EdgeCaseProbe
from md_evals.pipeline.detectors import FormatDetector, LLMJudgeDetector, SecurityDetector


# Always clear cache between tests to avoid test ordering issues
@pytest.fixture(autouse=True)
def _clear_plugin_cache():
    """Clear plugin caches before each test."""
    clear_cache()
    yield
    clear_cache()


# ============================================================================
# 1. discover_probes Tests
# ============================================================================


def test_discover_probes_returns_builtins():
    """discover_probes returns all three built-in probes."""
    probes = discover_probes()
    assert "dimension" in probes
    assert "edge-case" in probes
    assert "compliance" in probes


def test_discover_probes_types():
    """Probe registry maps to correct classes."""
    probes = discover_probes()
    assert probes["dimension"] is DimensionProbe
    assert probes["edge-case"] is EdgeCaseProbe
    assert probes["compliance"] is ComplianceProbe


def test_discover_probes_caching():
    """discover_probes caches results after first call."""
    result1 = discover_probes()
    result2 = discover_probes()
    assert result1 is result2  # Same object → caching works


# ============================================================================
# 2. discover_detectors Tests
# ============================================================================


def test_discover_detectors_returns_builtins():
    """discover_detectors returns all three built-in detectors."""
    detectors = discover_detectors()
    assert "llm-judge" in detectors
    assert "format" in detectors
    assert "security" in detectors


def test_discover_detectors_types():
    """Detector registry maps to correct classes."""
    detectors = discover_detectors()
    assert detectors["llm-judge"] is LLMJudgeDetector
    assert detectors["format"] is FormatDetector
    assert detectors["security"] is SecurityDetector


def test_discover_detectors_caching():
    """discover_detectors caches results after first call."""
    result1 = discover_detectors()
    result2 = discover_detectors()
    assert result1 is result2  # Same object → caching works


# ============================================================================
# 3. clear_cache Tests
# ============================================================================


def test_clear_cache_forces_rediscovery():
    """clear_cache forces re-discovery on next call."""
    result1 = discover_probes()
    clear_cache()
    result2 = discover_probes()
    # After clearing, should be a different object
    assert result1 is not result2
    # But same contents
    assert set(result1.keys()) == set(result2.keys())


# ============================================================================
# 4. BUILTIN Registries
# ============================================================================


def test_builtin_probes_registry():
    """BUILTIN_PROBES contains expected entries."""
    assert len(BUILTIN_PROBES) == 3
    assert set(BUILTIN_PROBES.keys()) == {"dimension", "edge-case", "compliance"}


def test_builtin_detectors_registry():
    """BUILTIN_DETECTORS contains expected entries."""
    assert len(BUILTIN_DETECTORS) == 3
    assert set(BUILTIN_DETECTORS.keys()) == {"llm-judge", "format", "security"}
