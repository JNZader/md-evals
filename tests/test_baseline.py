"""Tests for md_evals.baseline."""

import pytest

from md_evals.baseline import BaselineManager, BaselineReport
from md_evals.models import ExecutionResult, LLMResponse


def _make_result(
    treatment: str = "CONTROL",
    test: str = "test_1",
    passed: bool = True,
    duration_ms: int = 100,
) -> ExecutionResult:
    """Helper to create an ExecutionResult for testing."""
    return ExecutionResult(
        treatment=treatment,
        test=test,
        prompt="test prompt",
        response=LLMResponse(
            content="response",
            model="gpt-4o",
            provider="openai",
            tokens=10,
            duration_ms=duration_ms,
            raw_response={},
        ),
        passed=passed,
        evaluator_results=[],
        timestamp="2026-01-01T00:00:00+00:00",
    )


class TestBaselineManagerSaveLoad:
    """Test save/load round-trip."""

    def test_save_creates_file(self, tmp_path):
        results = [_make_result()]
        path = BaselineManager.save(results, "my-eval", str(tmp_path))
        assert path.exists()
        assert path.suffix == ".json"

    def test_save_load_roundtrip(self, tmp_path):
        results = [
            _make_result(treatment="CONTROL", test="t1", passed=True),
            _make_result(treatment="CONTROL", test="t1", passed=False),
            _make_result(treatment="WITH_SKILL", test="t1", passed=True),
        ]
        BaselineManager.save(results, "eval1", str(tmp_path))
        loaded = BaselineManager.load("eval1", str(tmp_path))

        assert loaded is not None
        assert len(loaded) == 2  # 2 unique (treatment, test) combos

        control_entry = next(
            (e for e in loaded if e.treatment == "CONTROL"), None
        )
        assert control_entry is not None
        assert control_entry.test_name == "t1"
        assert control_entry.pass_count == 1
        assert control_entry.total_count == 2
        assert control_entry.pass_rate == pytest.approx(0.5)

    def test_load_nonexistent_returns_none(self, tmp_path):
        result = BaselineManager.load("nonexistent", str(tmp_path))
        assert result is None


class TestBaselineManagerCompare:
    """Test compare detects regressions and stability."""

    def test_stable_results(self):
        baseline = [
            BaselineReport(
                test_name="t1",
                treatment="CONTROL",
                passed=True,
                pass_count=5,
                total_count=5,
                pass_rate=1.0,
                avg_duration_ms=100.0,
                timestamp="2026-01-01T00:00:00+00:00",
            )
        ]
        current = [_make_result(treatment="CONTROL", test="t1", passed=True)]
        findings = BaselineManager.compare(current, baseline)

        assert len(findings) == 1
        assert findings[0].status == "stable"
        assert findings[0].delta == pytest.approx(0.0, abs=0.01)

    def test_regression_detected(self):
        baseline = [
            BaselineReport(
                test_name="t1",
                treatment="CONTROL",
                passed=True,
                pass_count=5,
                total_count=5,
                pass_rate=1.0,
                avg_duration_ms=100.0,
                timestamp="2026-01-01T00:00:00+00:00",
            )
        ]
        current = [_make_result(treatment="CONTROL", test="t1", passed=False)]
        findings = BaselineManager.compare(current, baseline)

        assert len(findings) == 1
        assert findings[0].status == "regression"
        assert findings[0].delta < 0

    def test_improvement_detected(self):
        baseline = [
            BaselineReport(
                test_name="t1",
                treatment="CONTROL",
                passed=False,
                pass_count=0,
                total_count=5,
                pass_rate=0.0,
                avg_duration_ms=100.0,
                timestamp="2026-01-01T00:00:00+00:00",
            )
        ]
        current = [_make_result(treatment="CONTROL", test="t1", passed=True)]
        findings = BaselineManager.compare(current, baseline)

        assert len(findings) == 1
        assert findings[0].status == "improvement"
        assert findings[0].delta > 0

    def test_new_test_detected(self):
        baseline = [
            BaselineReport(
                test_name="t1",
                treatment="CONTROL",
                passed=True,
                pass_count=5,
                total_count=5,
                pass_rate=1.0,
                avg_duration_ms=100.0,
                timestamp="2026-01-01T00:00:00+00:00",
            )
        ]
        # Current has a test that baseline doesn't
        current = [_make_result(treatment="CONTROL", test="t2", passed=True)]
        findings = BaselineManager.compare(current, baseline)

        assert len(findings) == 1
        assert findings[0].status == "new"
        assert findings[0].test_name == "t2"

    def test_no_change_empty(self):
        findings = BaselineManager.compare([], [])
        assert findings == []
