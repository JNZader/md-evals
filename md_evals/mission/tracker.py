"""Regression tracker — compares current mission results against previous runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RegressionItem:
    """A single regression finding.

    Attributes:
        test_name: Name of the test case.
        status: One of 'regression', 'improvement', 'stable', 'new'.
        previous_passed: Whether the test passed in the previous run.
        current_passed: Whether the test passed in the current run.
        previous_score: Score from the previous run.
        current_score: Score from the current run.
        score_delta: Change in score (current - previous).
    """

    test_name: str
    status: str
    previous_passed: bool | None = None
    current_passed: bool = False
    previous_score: float | None = None
    current_score: float = 0.0
    score_delta: float = 0.0


@dataclass
class RegressionReport:
    """Summary of regression analysis between two runs.

    Attributes:
        mission_name: Name of the mission.
        current_timestamp: Timestamp of the current run.
        previous_timestamp: Timestamp of the previous run (None if first run).
        items: Per-test regression items.
        regressions: Count of tests that regressed.
        improvements: Count of tests that improved.
        stable: Count of tests with unchanged status.
        new_tests: Count of tests not present in previous run.
        has_regressions: True if any test regressed.
    """

    mission_name: str
    current_timestamp: str = ""
    previous_timestamp: str | None = None
    items: list[RegressionItem] = field(default_factory=list)
    regressions: int = 0
    improvements: int = 0
    stable: int = 0
    new_tests: int = 0

    @property
    def has_regressions(self) -> bool:
        return self.regressions > 0


class RegressionTracker:
    """Compares mission results against the most recent previous run.

    Loads previous results from the results directory, matches test cases
    by name, and flags regressions (pass -> fail) and improvements
    (fail -> pass).
    """

    @staticmethod
    def find_previous_result(
        results_dir: str,
        mission_name: str,
        exclude_timestamp: str | None = None,
    ) -> dict[str, Any] | None:
        """Find the most recent previous result for a mission.

        Args:
            results_dir: Directory containing result JSON files.
            mission_name: Mission name to match.
            exclude_timestamp: Timestamp to exclude (current run).

        Returns:
            Parsed JSON dict of the previous result, or None if not found.
        """
        dir_path = Path(results_dir)
        if not dir_path.exists():
            return None

        import re as _re

        safe_name = _re.sub(r"[^\w\-]", "_", mission_name)

        candidates: list[tuple[str, Path]] = []
        for file_path in dir_path.glob(f"{safe_name}_*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ts = data.get("timestamp", "")
                if exclude_timestamp and ts == exclude_timestamp:
                    continue
                if data.get("mission_name") == mission_name:
                    candidates.append((ts, file_path))
            except (json.JSONDecodeError, OSError):
                continue

        if not candidates:
            return None

        # Sort by timestamp descending, pick latest
        candidates.sort(key=lambda x: x[0], reverse=True)
        with open(candidates[0][1], "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def compare(
        current: dict[str, Any],
        previous: dict[str, Any] | None,
    ) -> RegressionReport:
        """Compare current results against previous results.

        Args:
            current: Current mission result dict.
            previous: Previous mission result dict, or None for first run.

        Returns:
            RegressionReport with per-test analysis.
        """
        mission_name = current.get("mission_name", "unknown")
        current_ts = current.get("timestamp", "")

        if previous is None:
            # First run — everything is "new"
            items = []
            for tr in current.get("test_results", []):
                items.append(
                    RegressionItem(
                        test_name=tr["test_name"],
                        status="new",
                        current_passed=tr["passed"],
                        current_score=tr.get("score", 0.0),
                    )
                )
            return RegressionReport(
                mission_name=mission_name,
                current_timestamp=current_ts,
                items=items,
                new_tests=len(items),
            )

        previous_ts = previous.get("timestamp", "")

        # Build lookup of previous results by test name
        prev_by_name: dict[str, dict[str, Any]] = {}
        for tr in previous.get("test_results", []):
            prev_by_name[tr["test_name"]] = tr

        items: list[RegressionItem] = []
        regressions = 0
        improvements = 0
        stable = 0
        new_tests = 0

        for tr in current.get("test_results", []):
            test_name = tr["test_name"]
            current_passed = tr["passed"]
            current_score = tr.get("score", 0.0)

            prev = prev_by_name.get(test_name)
            if prev is None:
                items.append(
                    RegressionItem(
                        test_name=test_name,
                        status="new",
                        current_passed=current_passed,
                        current_score=current_score,
                    )
                )
                new_tests += 1
                continue

            prev_passed = prev["passed"]
            prev_score = prev.get("score", 0.0)
            score_delta = round(current_score - prev_score, 4)

            if prev_passed and not current_passed:
                status = "regression"
                regressions += 1
            elif not prev_passed and current_passed:
                status = "improvement"
                improvements += 1
            else:
                status = "stable"
                stable += 1

            items.append(
                RegressionItem(
                    test_name=test_name,
                    status=status,
                    previous_passed=prev_passed,
                    current_passed=current_passed,
                    previous_score=prev_score,
                    current_score=current_score,
                    score_delta=score_delta,
                )
            )

        return RegressionReport(
            mission_name=mission_name,
            current_timestamp=current_ts,
            previous_timestamp=previous_ts,
            items=items,
            regressions=regressions,
            improvements=improvements,
            stable=stable,
            new_tests=new_tests,
        )
