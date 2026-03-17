"""Plugin discovery for probes and detectors.

Discovers built-in and third-party probes/detectors via Python
``entry_points``.  Third-party plugins register under the groups
``md_evals.probes`` and ``md_evals.detectors``.

Built-in registries are populated eagerly; entry_points are scanned
once and cached.  Call :func:`clear_cache` to force re-discovery
(useful in tests).
"""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import Any

from md_evals.pipeline.probes import DimensionProbe, EdgeCaseProbe, ComplianceProbe
from md_evals.pipeline.detectors import LLMJudgeDetector, FormatDetector, SecurityDetector

logger = logging.getLogger(__name__)

_probe_cache: dict[str, type] | None = None
_detector_cache: dict[str, type] | None = None

BUILTIN_PROBES: dict[str, type] = {
    "dimension": DimensionProbe,
    "edge-case": EdgeCaseProbe,
    "compliance": ComplianceProbe,
}

BUILTIN_DETECTORS: dict[str, type] = {
    "llm-judge": LLMJudgeDetector,
    "format": FormatDetector,
    "security": SecurityDetector,
}


def discover_probes() -> dict[str, type]:
    """Discover all available probes (built-in + plugins).

    Scans the ``md_evals.probes`` entry_points group for third-party
    probe classes.  Results are cached after the first call.

    Returns:
        Mapping of probe name → probe class.
    """
    global _probe_cache
    if _probe_cache is not None:
        return _probe_cache

    registry = dict(BUILTIN_PROBES)

    # Scan entry_points
    try:
        eps = entry_points(group="md_evals.probes")
        for ep in eps:
            try:
                probe_class = ep.load()
                registry[ep.name] = probe_class
                logger.debug("Loaded probe plugin: %s", ep.name)
            except Exception as e:
                logger.warning("Failed to load probe plugin '%s': %s", ep.name, e)
    except Exception:
        pass

    _probe_cache = registry
    return registry


def discover_detectors() -> dict[str, type]:
    """Discover all available detectors (built-in + plugins).

    Scans the ``md_evals.detectors`` entry_points group for third-party
    detector classes.  Results are cached after the first call.

    Returns:
        Mapping of detector name → detector class.
    """
    global _detector_cache
    if _detector_cache is not None:
        return _detector_cache

    registry = dict(BUILTIN_DETECTORS)

    try:
        eps = entry_points(group="md_evals.detectors")
        for ep in eps:
            try:
                detector_class = ep.load()
                registry[ep.name] = detector_class
                logger.debug("Loaded detector plugin: %s", ep.name)
            except Exception as e:
                logger.warning("Failed to load detector plugin '%s': %s", ep.name, e)
    except Exception:
        pass

    _detector_cache = registry
    return registry


def clear_cache() -> None:
    """Clear plugin discovery cache (for testing)."""
    global _probe_cache, _detector_cache
    _probe_cache = None
    _detector_cache = None
