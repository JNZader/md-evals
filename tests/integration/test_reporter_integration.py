"""Integration tests for reporter — real output generation, no mocks."""

import json
from pathlib import Path

import pytest

from md_evals.models import (
    EvalConfig,
    Defaults,
    Treatment,
    Task,
    ExecutionResult,
    LLMResponse,
    EvaluatorResult,
    RegexEvaluator,
)
from md_evals.reporter import Reporter
from md_evals.scoring import DimensionScore, EvalMetadata, EvalResult


def _make_config() -> EvalConfig:
    return EvalConfig(
        name="Reporter Test",
        defaults=Defaults(provider="mock", model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(description="Control"),
            "TREATMENT": Treatment(description="Treatment"),
        },
        tests=[
            Task(
                name="test_1",
                prompt="Say hello",
                evaluators=[RegexEvaluator(name="has_hello", pattern="hello")],
            )
        ],
    )


def _make_result(
    treatment: str, test: str, passed: bool, content: str = "hello"
) -> ExecutionResult:
    return ExecutionResult(
        treatment=treatment,
        test=test,
        prompt="Say hello",
        response=LLMResponse(
            content=content,
            model="gpt-4o",
            provider="mock",
            tokens=10,
            duration_ms=150,
        ),
        passed=passed,
        evaluator_results=[
            EvaluatorResult(
                evaluator_name="has_hello",
                passed=passed,
                score=1.0 if passed else 0.0,
            )
        ],
        timestamp="2025-01-01T00:00:00Z",
    )


class TestReporterJson:
    """Test JSON report generation with real data."""

    def test_json_output_structure(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [
            _make_result("CONTROL", "test_1", True),
            _make_result("TREATMENT", "test_1", True),
        ]
        out = tmp_path / "results.json"
        reporter.report_json(results, str(out))

        assert out.exists()
        data = json.loads(out.read_text())
        assert "experiment_id" in data
        assert "timestamp" in data
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 2

    def test_json_summary_values(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [
            _make_result("CONTROL", "test_1", True),
            _make_result("CONTROL", "test_2", False, content="nope"),
            _make_result("TREATMENT", "test_1", True),
        ]
        out = tmp_path / "results.json"
        reporter.report_json(results, str(out))

        data = json.loads(out.read_text())
        assert data["summary"]["CONTROL"]["total"] == 2
        assert data["summary"]["CONTROL"]["passed"] == 1
        assert data["summary"]["TREATMENT"]["total"] == 1
        assert data["summary"]["TREATMENT"]["passed"] == 1

    def test_json_result_fields(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [_make_result("CONTROL", "test_1", True)]
        out = tmp_path / "results.json"
        reporter.report_json(results, str(out))

        data = json.loads(out.read_text())
        r = data["results"][0]
        assert r["treatment"] == "CONTROL"
        assert r["test"] == "test_1"
        assert r["passed"] is True
        assert r["duration_ms"] == 150
        assert len(r["evaluators"]) == 1

    def test_json_with_eval_result(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        eval_result = EvalResult(
            skill_path="/test/SKILL.md",
            overall_grade="A",
            overall_score=0.90,
            dimensions=[
                DimensionScore(dimension="correctness", score=0.90, weight=1.0, grade="A")
            ],
            pre_check=None,
            metadata=EvalMetadata(model="gpt-4o", provider="openai"),
        )
        reporter.set_eval_result(eval_result)
        results = [_make_result("CONTROL", "test_1", True)]
        out = tmp_path / "results.json"
        reporter.report_json(results, str(out))

        data = json.loads(out.read_text())
        assert "eval_result" in data
        assert data["eval_result"]["overall_grade"] == "A"


class TestReporterMarkdown:
    """Test Markdown report generation with real data."""

    def test_markdown_output_structure(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [
            _make_result("CONTROL", "test_1", True),
            _make_result("TREATMENT", "test_1", False, content="nope"),
        ]
        out = tmp_path / "results.md"
        reporter.report_markdown(results, str(out))

        assert out.exists()
        content = out.read_text()
        assert "# md-evals Results" in content
        assert "## Summary" in content
        assert "CONTROL" in content
        assert "TREATMENT" in content

    def test_markdown_table_format(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [
            _make_result("CONTROL", "test_1", True),
        ]
        out = tmp_path / "results.md"
        reporter.report_markdown(results, str(out))

        content = out.read_text()
        assert "| Treatment | Tests | Passed | Pass Rate |" in content
        assert "| CONTROL |" in content

    def test_markdown_details_section(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [
            _make_result("CONTROL", "test_1", True),
        ]
        out = tmp_path / "results.md"
        reporter.report_markdown(results, str(out))

        content = out.read_text()
        assert "## Details" in content
        assert "### CONTROL" in content


class TestReporterSummary:
    """Test calculate_summary with real results."""

    def test_summary_empty(self):
        config = _make_config()
        reporter = Reporter(config)
        assert reporter.calculate_summary([]) == {}

    def test_summary_stats(self):
        config = _make_config()
        reporter = Reporter(config)
        results = [
            _make_result("CONTROL", "test_1", True),
            _make_result("CONTROL", "test_2", False, content="nope"),
        ]
        summary = reporter.calculate_summary(results)
        assert summary["CONTROL"]["passed"] == 1
        assert summary["CONTROL"]["total"] == 2
        assert summary["CONTROL"]["pass_rate"] == 0.5
        assert summary["CONTROL"]["avg_duration_ms"] == 150

    def test_creates_parent_directories(self, tmp_path):
        config = _make_config()
        reporter = Reporter(config)
        results = [_make_result("CONTROL", "test_1", True)]
        nested = tmp_path / "deep" / "nested" / "results.json"
        reporter.report_json(results, str(nested))
        assert nested.exists()
