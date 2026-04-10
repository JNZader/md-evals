"""Tests for MissionReporter."""


from md_evals.mission.models import (
    MissionResult,
    MissionSummary,
    MissionTestResult,
)
from md_evals.mission.reporter import MissionReporter
from md_evals.mission.tracker import RegressionItem, RegressionReport


class TestMissionReporter:
    """Tests for MissionReporter.generate()."""

    def _make_result(self, **kwargs) -> MissionResult:
        defaults = {
            "mission_name": "test-mission",
            "version": "1.0",
            "timestamp": "2026-03-31T00:00:00Z",
            "model": "gpt-4o",
            "provider": "openai",
            "test_results": [
                MissionTestResult(test_name="t1", passed=True, score=1.0, duration_ms=100),
                MissionTestResult(test_name="t2", passed=False, score=0.0, duration_ms=200,
                                  criteria_results=[
                                      {"name": "check", "type": "regex", "passed": False,
                                       "score": 0.0, "reason": "Pattern not matched"}
                                  ]),
            ],
            "summary": MissionSummary(
                total=2, passed=1, failed=1, pass_rate=0.5, duration_ms=300
            ),
        }
        defaults.update(kwargs)
        return MissionResult(**defaults)

    def test_basic_report(self):
        result = self._make_result()
        md = MissionReporter.generate(result)

        assert "# Mission Report: test-mission" in md
        assert "**Model:** gpt-4o" in md
        assert "| Total Tests | 2 |" in md
        assert "| Passed | 1 |" in md
        assert "| t1 |" in md
        assert "| t2 |" in md
        assert "PASS" in md
        assert "FAIL" in md

    def test_failed_details_section(self):
        result = self._make_result()
        md = MissionReporter.generate(result)

        assert "## Failed Test Details" in md
        assert "### t2" in md
        assert "Pattern not matched" in md

    def test_no_failed_details_when_all_pass(self):
        result = self._make_result(
            test_results=[
                MissionTestResult(test_name="t1", passed=True, score=1.0),
            ],
            summary=MissionSummary(total=1, passed=1, failed=0, pass_rate=1.0),
        )
        md = MissionReporter.generate(result)
        assert "## Failed Test Details" not in md

    def test_with_regression_report(self):
        result = self._make_result()
        regression = RegressionReport(
            mission_name="test-mission",
            current_timestamp="2026-03-31T00:00:00Z",
            previous_timestamp="2026-03-30T00:00:00Z",
            items=[
                RegressionItem(
                    test_name="t2",
                    status="regression",
                    previous_passed=True,
                    current_passed=False,
                    previous_score=0.8,
                    current_score=0.0,
                    score_delta=-0.8,
                ),
                RegressionItem(
                    test_name="t1",
                    status="stable",
                    previous_passed=True,
                    current_passed=True,
                    previous_score=1.0,
                    current_score=1.0,
                ),
            ],
            regressions=1,
            stable=1,
        )
        md = MissionReporter.generate(result, regression)

        assert "## Regression Analysis" in md
        assert "Compared against" in md
        assert "| Regressions | 1 |" in md
        assert "### Regressions" in md
        assert "t2" in md

    def test_first_run_regression(self):
        result = self._make_result()
        regression = RegressionReport(
            mission_name="test-mission",
            current_timestamp="2026-03-31T00:00:00Z",
            new_tests=2,
        )
        md = MissionReporter.generate(result, regression)

        assert "## Regression Analysis" in md
        assert "First run" in md

    def test_with_improvements(self):
        result = self._make_result()
        regression = RegressionReport(
            mission_name="test-mission",
            current_timestamp="2026-03-31T00:00:00Z",
            previous_timestamp="2026-03-30T00:00:00Z",
            items=[
                RegressionItem(
                    test_name="t1",
                    status="improvement",
                    previous_passed=False,
                    current_passed=True,
                    previous_score=0.2,
                    current_score=1.0,
                    score_delta=0.8,
                ),
            ],
            improvements=1,
        )
        md = MissionReporter.generate(result, regression)
        assert "### Improvements" in md

    def test_with_skill_and_tags(self):
        result = self._make_result(
            skill_under_test="./SKILL.md",
            tags=["weekly", "regression"],
        )
        md = MissionReporter.generate(result)
        assert "**Skill:** ./SKILL.md" in md
        assert "**Tags:** weekly, regression" in md

    def test_save_report(self, tmp_path):
        result = self._make_result()
        md = MissionReporter.generate(result)
        path = MissionReporter.save(md, tmp_path / "report.md")

        assert path.exists()
        content = path.read_text()
        assert "# Mission Report" in content

    def test_save_creates_dirs(self, tmp_path):
        result = self._make_result()
        md = MissionReporter.generate(result)
        path = MissionReporter.save(md, tmp_path / "a" / "b" / "report.md")
        assert path.exists()
