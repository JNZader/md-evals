"""Tests for evaluator engine."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from md_evals.evaluator import EvaluatorEngine, create_evaluator
from md_evals.models import (
    RegexEvaluator, ExactMatchEvaluator, LLMJudgeEvaluator,
    EvaluatorResult
)


class TestRegexEvaluator:
    """Test RegexEvaluator."""
    
    def test_pattern_matches(self):
        """Test pattern that matches."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="has_hello",
            pattern="hello",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Hello world!", evaluator)
        
        assert result.passed
        assert result.score == 1.0
    
    def test_pattern_not_matches(self):
        """Test pattern that doesn't match."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="has_hello",
            pattern="goodbye",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Hello world!", evaluator)
        
        assert not result.passed
        assert result.score == 0.0
    
    def test_pass_on_match_false(self):
        """Test pass_on_match=False."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="no_hello",
            pattern="hello",
            pass_on_match=False
        )
        
        result = engine._evaluate_regex("Hello world!", evaluator)
        
        assert not result.passed
    
    def test_invalid_regex(self):
        """Test invalid regex."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="invalid",
            pattern="[invalid",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("test", evaluator)
        
        assert not result.passed
        assert "Invalid regex" in result.reason
    
    def test_multiline_pattern(self):
        """Test multiline pattern."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="starts_with",
            pattern="^Hello",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Hello\nWorld", evaluator)
        
        assert result.passed
    
    def test_fail_message(self):
        """Test custom fail message."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="has_hello",
            pattern="goodbye",
            pass_on_match=True,
            fail_message="Expected greeting"
        )
        
        result = engine._evaluate_regex("Hello world!", evaluator)
        
        assert not result.passed
        assert result.reason == "Expected greeting"
    
    def test_empty_output(self):
        """Test empty output."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="has_hello",
            pattern="hello",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("", evaluator)
        
        assert not result.passed


class TestExactMatchEvaluator:
    """Test ExactMatchEvaluator."""
    
    def test_exact_match(self):
        """Test exact match."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="hello",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("hello world", evaluator)
        
        assert result.passed
    
    def test_case_insensitive(self):
        """Test case insensitive."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="hello",
            case_sensitive=False
        )
        
        result = engine._evaluate_exact_match("HELLO world", evaluator)
        
        assert result.passed
    
    def test_no_match(self):
        """Test no match."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="goodbye",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("hello world", evaluator)
        
        assert not result.passed
    
    def test_empty_expected(self):
        """Test empty expected string."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("hello world", evaluator)
        
        # Empty string is always "in" any string
        assert result.passed


class TestLLMJudgeEvaluator:
    """Test LLMJudgeEvaluator."""
    
    @pytest.mark.asyncio
    async def test_llm_judge_success(self):
        """Test LLM judge with successful evaluation."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.9, "reason": "Good response"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test criteria",
            output_schema={"type": "object"},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("test output", [evaluator])
        
        assert len(results) == 1
        assert results[0].passed
        assert results[0].score == 0.9
    
    @pytest.mark.asyncio
    async def test_llm_judge_below_threshold(self):
        """Test LLM judge below threshold."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.5, "reason": "Poor response"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test criteria",
            output_schema={"type": "object"},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("test output", [evaluator])
        
        assert len(results) == 1
        assert not results[0].passed
    
    @pytest.mark.asyncio
    async def test_llm_judge_invalid_json(self):
        """Test LLM judge with invalid JSON response."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "not valid json"
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test criteria",
            output_schema={"type": "object"},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("test output", [evaluator])
        
        assert len(results) == 1
        assert not results[0].passed
        assert "JSON" in results[0].reason


class TestEvaluatorEngine:
    """Test EvaluatorEngine."""
    
    @pytest.mark.asyncio
    async def test_multiple_evaluators(self):
        """Test multiple evaluators."""
        engine = EvaluatorEngine()
        evaluators = [
            RegexEvaluator(name="has_hello", pattern="hello"),
            RegexEvaluator(name="has_world", pattern="world")
        ]
        
        results = await engine.evaluate("Hello world!", evaluators)
        
        assert len(results) == 2
        assert all(r.passed for r in results)
    
    @pytest.mark.asyncio
    async def test_llm_judge_no_adapter(self):
        """Test LLM judge without adapter."""
        engine = EvaluatorEngine(llm_adapter=None)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test criteria",
            output_schema={"type": "object"},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("test output", [evaluator])
        
        assert len(results) == 1
        assert not results[0].passed
        assert "not configured" in results[0].reason.lower()
    
    @pytest.mark.asyncio
    async def test_mixed_evaluators(self):
        """Test mixed evaluator types."""
        engine = EvaluatorEngine()
        evaluators = [
            RegexEvaluator(name="has_hello", pattern="hello"),
            ExactMatchEvaluator(name="exact", expected="test")
        ]
        
        results = await engine.evaluate("hello test", evaluators)
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_unknown_evaluator(self):
        """Test unknown evaluator type."""
        engine = EvaluatorEngine()
        
        # Create a mock evaluator with unknown type
        class UnknownEvaluator:
            name = "unknown"
        
        results = await engine.evaluate("test", [UnknownEvaluator()])
        
        assert len(results) == 1
        assert not results[0].passed
    
    @pytest.mark.asyncio
    async def test_empty_evaluators(self):
        """Test with no evaluators."""
        engine = EvaluatorEngine()
        
        results = await engine.evaluate("test output", [])
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_evaluate_with_no_output(self):
        """Test evaluate with empty output."""
        engine = EvaluatorEngine()
        evaluators = [
            RegexEvaluator(name="has_hello", pattern="hello")
        ]
        
        results = await engine.evaluate("", evaluators)
        
        assert len(results) == 1
        assert not results[0].passed


class TestCreateEvaluator:
    """Test create_evaluator factory function."""
    
    def test_create_regex_evaluator(self):
        """Test creating regex evaluator."""
        evaluator = create_evaluator(
            "regex",
            name="test",
            pattern="hello",
            pass_on_match=True
        )
        
        assert isinstance(evaluator, RegexEvaluator)
        assert evaluator.name == "test"
        assert evaluator.pattern == "hello"
    
    def test_create_exact_match_evaluator(self):
        """Test creating exact-match evaluator."""
        evaluator = create_evaluator(
            "exact-match",
            name="test",
            expected="hello",
            case_sensitive=True
        )
        
        assert isinstance(evaluator, ExactMatchEvaluator)
        assert evaluator.name == "test"
        assert evaluator.expected == "hello"
    
    def test_create_llm_judge_evaluator(self):
        """Test creating LLM judge evaluator."""
        evaluator = create_evaluator(
            "llm-judge",
            name="judge",
            judge_model="gpt-4o",
            criteria="Test criteria",
            pass_threshold=0.8
        )
        
        assert isinstance(evaluator, LLMJudgeEvaluator)
        assert evaluator.name == "judge"
        assert evaluator.judge_model == "gpt-4o"
    
    def test_create_unknown_evaluator(self):
        """Test creating unknown evaluator type."""
        with pytest.raises(ValueError, match="Unknown evaluator type"):
            create_evaluator("unknown_type", name="test")
