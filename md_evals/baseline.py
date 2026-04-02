"""Baseline management for regression testing mode."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from md_evals.models import ExecutionResult


@dataclass
class BaselineReport:
    """Stored baseline for a single test."""

    test_name: str
    treatment: str
    passed: bool
    pass_count: int
    total_count: int
    pass_rate: float
    avg_duration_ms: float
    timestamp: str


@dataclass
class RegressionItem:
    """A single regression finding from baseline comparison."""

    test_name: str
    treatment: str
    dimension: str  # e.g. "pass_rate", "avg_duration_ms"
    baseline_value: float
    current_value: float
    delta: float
    status: str  # "regression", "improvement", "stable", "new"


class BaselineManager:
    """Save, load, and compare baselines for regression mode."""

    @staticmethod
    def _baseline_path(config_name: str, results_dir: str) -> Path:
        """Compute the baseline file path."""
        return Path(results_dir) / "baselines" / f"{config_name}.json"

    @staticmethod
    def save(
        results: list[ExecutionResult],
        config_name: str,
        results_dir: str,
    ) -> Path:
        """Save current results as a baseline.

        Groups results by (treatment, test) and stores aggregate stats.

        Args:
            results: Execution results from the run.
            config_name: Name of the eval config (used as filename).
            results_dir: Directory for result artifacts.

        Returns:
            Path to the saved baseline file.
        """
        grouped: dict[str, list[ExecutionResult]] = {}
        for r in results:
            key = f"{r.treatment}::{r.test}"
            grouped.setdefault(key, []).append(r)

        entries: list[dict] = []
        for key, group in grouped.items():
            treatment, test_name = key.split("::", 1)
            passed_count = sum(1 for r in group if r.passed)
            total = len(group)
            durations = [r.response.duration_ms for r in group if r.response]
            avg_dur = sum(durations) / len(durations) if durations else 0.0

            report = BaselineReport(
                test_name=test_name,
                treatment=treatment,
                passed=all(r.passed for r in group),
                pass_count=passed_count,
                total_count=total,
                pass_rate=passed_count / total if total else 0.0,
                avg_duration_ms=avg_dur,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            entries.append(asdict(report))

        path = BaselineManager._baseline_path(config_name, results_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def load(config_name: str, results_dir: str) -> list[BaselineReport] | None:
        """Load a previously saved baseline.

        Args:
            config_name: Name of the eval config.
            results_dir: Directory for result artifacts.

        Returns:
            List of BaselineReport entries, or None if no baseline exists.
        """
        path = BaselineManager._baseline_path(config_name, results_dir)
        if not path.exists():
            return None

        raw = json.loads(path.read_text(encoding="utf-8"))
        return [BaselineReport(**entry) for entry in raw]

    @staticmethod
    def compare(
        current_results: list[ExecutionResult],
        baseline: list[BaselineReport],
    ) -> list[RegressionItem]:
        """Compare current results against a baseline.

        Detects regressions (pass_rate dropped) per (treatment, test).

        Args:
            current_results: Results from the current run.
            baseline: Previously saved baseline entries.

        Returns:
            List of RegressionItem findings.
        """
        # Build baseline lookup
        bl_map: dict[str, BaselineReport] = {
            f"{b.treatment}::{b.test_name}": b for b in baseline
        }

        # Group current results
        grouped: dict[str, list[ExecutionResult]] = {}
        for r in current_results:
            key = f"{r.treatment}::{r.test}"
            grouped.setdefault(key, []).append(r)

        findings: list[RegressionItem] = []
        for key, group in grouped.items():
            treatment, test_name = key.split("::", 1)
            passed_count = sum(1 for r in group if r.passed)
            total = len(group)
            current_rate = passed_count / total if total else 0.0

            bl = bl_map.get(key)
            if bl is None:
                findings.append(
                    RegressionItem(
                        test_name=test_name,
                        treatment=treatment,
                        dimension="pass_rate",
                        baseline_value=0.0,
                        current_value=current_rate,
                        delta=current_rate,
                        status="new",
                    )
                )
                continue

            delta = current_rate - bl.pass_rate
            if delta < -0.001:
                status = "regression"
            elif delta > 0.001:
                status = "improvement"
            else:
                status = "stable"

            findings.append(
                RegressionItem(
                    test_name=test_name,
                    treatment=treatment,
                    dimension="pass_rate",
                    baseline_value=bl.pass_rate,
                    current_value=current_rate,
                    delta=delta,
                    status=status,
                )
            )

        return findings
