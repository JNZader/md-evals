"""Tests for md_evals reporter."""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from md_evals.reporter import Reporter
from md_evals.models import (
    EvalConfig, ExecutionResult, LLMResponse,
    EvaluatorResult, Defaults
)


class TestReporter:
    """Test Reporter class."""
    
    def test_init(self):
        """Test reporter initialization."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        assert reporter.config == config
    
    def test_report_terminal_empty(self):
        """Test terminal report with empty results."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        # Should not raise
        reporter.report_terminal([])
    
    def test_report_terminal_with_results(self):
        """Test terminal report with results."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionResult(
                treatment="CONTROL",
                test="test2",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=2000
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        # Should not raise
        reporter.report_terminal(results, verbose=False)
    
    def test_report_terminal_verbose(self):
        """Test terminal report with verbose mode."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi there!",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[
                    EvaluatorResult(
                        evaluator_name="has_greeting",
                        passed=True,
                        score=1.0,
                        reason="Matched pattern"
                    )
                ],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        # Should not raise
        reporter.report_terminal(results, verbose=True)
    
    def test_report_terminal_multiple_treatments(self):
        """Test terminal report with multiple treatments."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionResult(
                treatment="WITH_SKILL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hello!",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1200
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:01"
            ),
            ExecutionResult(
                treatment="CONTROL",
                test="test2",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1500
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:02"
            )
        ]
        
        # Should not raise
        reporter.report_terminal(results, verbose=False)
    
    def test_report_terminal_all_pass(self):
        """Test terminal report with all tests passing."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionResult(
                treatment="WITH_SKILL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hello!",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1200
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:01"
            )
        ]
        
        # Should not raise - tests 100% pass
        reporter.report_terminal(results, verbose=False)
    
    def test_report_terminal_all_fail(self):
        """Test terminal report with all tests failing."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionResult(
                treatment="WITH_SKILL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hello!",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1200
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:01"
            )
        ]
        
        # Should not raise - tests 0% pass
        reporter.report_terminal(results, verbose=False)
    
    def test_report_terminal_partial_pass(self):
        """Test terminal report with partial pass rate."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionResult(
                treatment="CONTROL",
                test="test2",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1200
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:01"
            ),
            ExecutionResult(
                treatment="CONTROL",
                test="test3",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1500
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:02"
            )
        ]
        
        # Should not raise - 33% pass (between 50-80, should be yellow)
        reporter.report_terminal(results, verbose=False)
    
    def test_report_terminal_no_response(self):
        """Test terminal report with results that have no response."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        # This tests the case where response might be None
        # Note: Our model doesn't allow None now, but let's test with duration_ms=0
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="",
                    model="error",
                    provider="error",
                    duration_ms=0
                ),
                passed=False,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        # Should handle zero duration
        reporter.report_terminal(results, verbose=False)
    
    def test_report_json(self, tmp_path):
        """Test JSON report output."""
        config = EvalConfig(
            name="Test",
            output__results_dir=str(tmp_path)
        )
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        output_path = str(tmp_path / "results.json")
        reporter.report_json(results, output_path)
        
        assert Path(output_path).exists()
        
        # Verify JSON content
        with open(output_path) as f:
            data = json.load(f)
        
        assert "experiment_id" in data
        assert "timestamp" in data
        assert "config" in data
        assert "results" in data
    
    def test_report_json_creates_directory(self, tmp_path):
        """Test JSON report creates directory if needed."""
        results_dir = tmp_path / "subdir" / "results"
        config = EvalConfig(
            name="Test",
            output__results_dir=str(results_dir)
        )
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        output_path = str(results_dir / "results.json")
        reporter.report_json(results, output_path)
        
        assert Path(output_path).exists()
    
    def test_calculate_summary_empty(self):
        """Test calculate summary with empty results."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        summary = reporter.calculate_summary([])
        
        assert summary == {}
    
    def test_calculate_summary(self):
        """Test calculate summary."""
        config = EvalConfig(name="Test")
        reporter = Reporter(config)
        
        mock_response = MagicMock()
        mock_response.duration_ms = 1000
        mock_response.tokens = 50
        
        results = [
            MagicMock(
                treatment="CONTROL",
                passed=True,
                response=mock_response
            ),
            MagicMock(
                treatment="CONTROL",
                passed=False,
                response=mock_response
            ),
            MagicMock(
                treatment="WITH_SKILL",
                passed=True,
                response=mock_response
            ),
        ]
        
        summary = reporter.calculate_summary(results)
        
        assert "CONTROL" in summary
        assert summary["CONTROL"]["passed"] == 1
        assert summary["CONTROL"]["total"] == 2
        assert summary["CONTROL"]["pass_rate"] == 0.5
        
        assert "WITH_SKILL" in summary
        assert summary["WITH_SKILL"]["passed"] == 1
        assert summary["WITH_SKILL"]["total"] == 1


class TestReportMarkdown:
    """Test Markdown report generation."""
    
    def test_build_markdown(self, tmp_path):
        """Test markdown report generation."""
        config = EvalConfig(
            name="Test",
            version="1.0",
            output__results_dir=str(tmp_path)
        )
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            ),
            ExecutionResult(
                treatment="WITH_SKILL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hello!",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1200
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:01"
            )
        ]
        
        output_path = str(tmp_path / "results.md")
        reporter.report_markdown(results, output_path)
        
        assert Path(output_path).exists()
        
        # Verify markdown content
        content = Path(output_path).read_text()
        assert "# md-evals Results" in content
        assert "CONTROL" in content
        assert "WITH_SKILL" in content
    
    def test_markdown_creates_directory(self, tmp_path):
        """Test markdown report creates directory if needed."""
        results_dir = tmp_path / "reports"
        config = EvalConfig(
            name="Test",
            output__results_dir=str(results_dir)
        )
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        output_path = str(results_dir / "results.md")
        reporter.report_markdown(results, output_path)
        
        assert Path(output_path).exists()
    
    def test_markdown_creates_directory(self, tmp_path):
        """Test markdown report creates directory if needed."""
        results_dir = tmp_path / "reports"
        config = EvalConfig(
            name="Test",
            output__results_dir=str(results_dir)
        )
        reporter = Reporter(config)
        
        results = [
            ExecutionResult(
                treatment="CONTROL",
                test="test1",
                prompt="Hello",
                response=LLMResponse(
                    content="Hi",
                    model="gpt-4o",
                    provider="openai",
                    duration_ms=1000
                ),
                passed=True,
                evaluator_results=[],
                timestamp="2024-01-01T00:00:00"
            )
        ]
        
        output_path = str(results_dir / "results.md")
        reporter.report_markdown(results, output_path)
        
        assert Path(output_path).exists()
