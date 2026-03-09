"""Tests for evaluator engine."""

import pytest
from md_evals.evaluator import EvaluatorEngine
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
