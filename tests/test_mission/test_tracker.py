"""Tests for RegressionTracker."""

import json
from pathlib import Path

import pytest

from md_evals.mission.tracker import RegressionItem, RegressionReport, RegressionTracker


class TestRegressionCompare:
    """Tests for RegressionTracker.compare()."""

    def test_first_run_all_new(self):
        current = {
            "mission_name": "test",
            "timestamp": "2026-03-31T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
                {"test_name": "t2", "passed": False, "score": 0.0},
            ],
        }
        report = RegressionTracker.compare(current, None)
        assert report.mission_name == "test"
        assert report.new_tests == 2
        assert report.regressions == 0
        assert report.improvements == 0
        assert report.stable == 0
        assert not report.has_regressions
        assert all(item.status == "new" for item in report.items)

    def test_regression_detected(self):
        previous = {
            "mission_name": "test",
            "timestamp": "2026-03-30T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
                {"test_name": "t2", "passed": True, "score": 0.8},
            ],
        }
        current = {
            "mission_name": "test",
            "timestamp": "2026-03-31T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
                {"test_name": "t2", "passed": False, "score": 0.3},
            ],
        }
        report = RegressionTracker.compare(current, previous)
        assert report.has_regressions is True
        assert report.regressions == 1
        assert report.stable == 1

        t2 = next(i for i in report.items if i.test_name == "t2")
        assert t2.status == "regression"
        assert t2.previous_passed is True
        assert t2.current_passed is False
        assert t2.score_delta == pytest.approx(-0.5)

    def test_improvement_detected(self):
        previous = {
            "mission_name": "test",
            "timestamp": "2026-03-30T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": False, "score": 0.2},
            ],
        }
        current = {
            "mission_name": "test",
            "timestamp": "2026-03-31T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 0.9},
            ],
        }
        report = RegressionTracker.compare(current, previous)
        assert report.improvements == 1
        assert not report.has_regressions

        t1 = report.items[0]
        assert t1.status == "improvement"
        assert t1.score_delta == pytest.approx(0.7)

    def test_new_test_in_current(self):
        previous = {
            "mission_name": "test",
            "timestamp": "2026-03-30T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
            ],
        }
        current = {
            "mission_name": "test",
            "timestamp": "2026-03-31T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
                {"test_name": "t2", "passed": True, "score": 0.8},
            ],
        }
        report = RegressionTracker.compare(current, previous)
        assert report.new_tests == 1
        assert report.stable == 1

    def test_stable_results(self):
        previous = {
            "mission_name": "test",
            "timestamp": "2026-03-30T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
                {"test_name": "t2", "passed": False, "score": 0.0},
            ],
        }
        current = {
            "mission_name": "test",
            "timestamp": "2026-03-31T00:00:00Z",
            "test_results": [
                {"test_name": "t1", "passed": True, "score": 1.0},
                {"test_name": "t2", "passed": False, "score": 0.0},
            ],
        }
        report = RegressionTracker.compare(current, previous)
        assert report.stable == 2
        assert report.regressions == 0
        assert report.improvements == 0


class TestFindPreviousResult:
    """Tests for RegressionTracker.find_previous_result()."""

    def test_no_results_dir(self, tmp_path):
        result = RegressionTracker.find_previous_result(
            str(tmp_path / "nonexistent"), "test"
        )
        assert result is None

    def test_empty_results_dir(self, tmp_path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        result = RegressionTracker.find_previous_result(
            str(results_dir), "test"
        )
        assert result is None

    def test_finds_latest(self, tmp_path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Create two result files with proper timestamps
        timestamps = [
            ("2026-03-30T00:00:00+00:00", "test_2026-03-30T00-00-00_00-00.json"),
            ("2026-03-31T00:00:00+00:00", "test_2026-03-31T00-00-00_00-00.json"),
        ]
        for ts, fname in timestamps:
            data = {
                "mission_name": "test",
                "timestamp": ts,
                "test_results": [],
            }
            (results_dir / fname).write_text(json.dumps(data))

        result = RegressionTracker.find_previous_result(
            str(results_dir), "test"
        )
        assert result is not None
        assert "2026-03-31" in result["timestamp"]

    def test_excludes_current_timestamp(self, tmp_path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        ts1 = "2026-03-30T00:00:00+00:00"
        ts2 = "2026-03-31T00:00:00+00:00"

        for ts in [ts1, ts2]:
            safe_ts = ts.replace(":", "-").replace("+", "_")
            data = {"mission_name": "test", "timestamp": ts, "test_results": []}
            (results_dir / f"test_{safe_ts}.json").write_text(json.dumps(data))

        result = RegressionTracker.find_previous_result(
            str(results_dir), "test", exclude_timestamp=ts2
        )
        assert result is not None
        assert result["timestamp"] == ts1

    def test_ignores_different_mission(self, tmp_path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        data = {
            "mission_name": "other-mission",
            "timestamp": "2026-03-31T00:00:00Z",
            "test_results": [],
        }
        (results_dir / "test_2026-03-31.json").write_text(json.dumps(data))

        result = RegressionTracker.find_previous_result(
            str(results_dir), "test"
        )
        assert result is None


class TestRegressionReport:
    """Tests for RegressionReport model."""

    def test_has_regressions_property(self):
        report = RegressionReport(mission_name="test", regressions=0)
        assert report.has_regressions is False

        report = RegressionReport(mission_name="test", regressions=1)
        assert report.has_regressions is True
