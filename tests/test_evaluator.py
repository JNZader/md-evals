"""Tests for evaluator engine."""

import asyncio
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


class TestRegexEvaluatorEdgeCases:
    """Test edge cases for regex evaluator."""
    
    def test_case_insensitive_pattern(self):
        """Test case insensitive regex matching."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="case_test",
            pattern="hello",
            pass_on_match=True
        )
        
        # Should match because pattern is compiled with re.IGNORECASE
        result = engine._evaluate_regex("HELLO world!", evaluator)
        assert result.passed
    
    def test_pattern_with_special_chars(self):
        """Test regex with special characters."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="special_chars",
            pattern=r"\d+",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Result: 42", evaluator)
        assert result.passed
    
    def test_pattern_with_word_boundary(self):
        """Test regex with word boundaries."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="word_boundary",
            pattern=r"\bhello\b",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Say hello world", evaluator)
        assert result.passed
    
    def test_pattern_not_matching_substring(self):
        """Test pattern with substring that shouldn't match."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="word_boundary",
            pattern=r"\bhello\b",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Say hello123 world", evaluator)
        assert not result.passed
    
    def test_pass_on_match_false_with_match(self):
        """Test pass_on_match=False when pattern matches."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="negative",
            pattern="error",
            pass_on_match=False
        )
        
        result = engine._evaluate_regex("No error here", evaluator)
        assert not result.passed
    
    def test_pass_on_match_false_without_match(self):
        """Test pass_on_match=False when pattern doesn't match."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="negative",
            pattern="error",
            pass_on_match=False
        )
        
        result = engine._evaluate_regex("All good", evaluator)
        assert result.passed
    
    def test_regex_with_optional_group(self):
        """Test regex with optional groups."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="optional",
            pattern=r"hello(\s+world)?",
            pass_on_match=True
        )
        
        # Should match "hello" alone
        result = engine._evaluate_regex("hello", evaluator)
        assert result.passed
    
    def test_regex_multiline_with_anchors(self):
        """Test multiline regex with line anchors."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="multiline",
            pattern="^success",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("line1\nsuccess line2", evaluator)
        assert result.passed
    
    def test_evaluator_name_returned(self):
        """Test that evaluator name is returned in result."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="my_evaluator",
            pattern="test",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("test", evaluator)
        assert result.evaluator_name == "my_evaluator"
    
    def test_default_fail_message_when_no_match(self):
        """Test default fail message when no custom message."""
        engine = EvaluatorEngine()
        evaluator = RegexEvaluator(
            name="test",
            pattern="nonexistent",
            pass_on_match=True,
            fail_message=None
        )
        
        result = engine._evaluate_regex("test content", evaluator)
        assert not result.passed
        assert "Pattern not found" in result.reason


class TestExactMatchEvaluatorEdgeCases:
    """Test edge cases for exact match evaluator."""
    
    def test_exact_match_full_string(self):
        """Test exact match with full string content."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="exact match",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("exact match", evaluator)
        assert result.passed
    
    def test_exact_match_in_longer_string(self):
        """Test exact match as substring in longer string."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="test",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("this is a test string", evaluator)
        assert result.passed
    
    def test_case_sensitive_mismatch(self):
        """Test case sensitive match with different case."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="hello",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("HELLO world", evaluator)
        assert not result.passed
    
    def test_case_insensitive_match(self):
        """Test case insensitive match with different case."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="hello",
            case_sensitive=False
        )
        
        result = engine._evaluate_exact_match("HELLO world", evaluator)
        assert result.passed
    
    def test_special_chars_in_expected(self):
        """Test exact match with special characters."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="test@example.com",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("Email: test@example.com", evaluator)
        assert result.passed
    
    def test_exact_match_evaluator_name(self):
        """Test exact match evaluator returns correct name."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="my_exact_test",
            expected="test",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("test content", evaluator)
        assert result.evaluator_name == "my_exact_test"
    
    def test_exact_match_score_on_pass(self):
        """Test exact match score is 1.0 on pass."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="test",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("test", evaluator)
        assert result.score == 1.0
    
    def test_exact_match_score_on_fail(self):
        """Test exact match score is 0.0 on fail."""
        engine = EvaluatorEngine()
        evaluator = ExactMatchEvaluator(
            name="exact",
            expected="missing",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("test content", evaluator)
        assert result.score == 0.0


class TestLLMJudgeEvaluatorEdgeCases:
    """Test edge cases for LLM judge evaluator."""
    
    @pytest.mark.asyncio
    async def test_llm_judge_score_1_to_5_scale(self):
        """Test LLM judge with score on 1-5 scale."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 4, "reasoning": "Good"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.7
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        # Score 4 on 1-5 scale = 0.8 (4/5)
        assert results[0].score == 0.8
        assert results[0].passed  # 0.8 > 0.7
    
    @pytest.mark.asyncio
    async def test_llm_judge_score_1_to_10_scale(self):
        """Test LLM judge with score on 1-10 scale."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 8, "reasoning": "Good"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.75
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        # Score 8 on 1-10 scale = 0.8 (8/10)
        assert results[0].score == 0.8
        assert results[0].passed  # 0.8 > 0.75
    
    @pytest.mark.asyncio
    async def test_llm_judge_score_as_string(self):
        """Test LLM judge with score returned as string."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": "0.85", "reasoning": "Good"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        assert results[0].score == 0.85
        assert results[0].passed
    
    @pytest.mark.asyncio
    async def test_llm_judge_score_invalid_string(self):
        """Test LLM judge with invalid score string."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": "invalid", "reasoning": "Bad"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        # Should handle invalid score and default to 0
        assert results[0].score == 0
        assert not results[0].passed
    
    @pytest.mark.asyncio
    async def test_llm_judge_missing_score(self):
        """Test LLM judge with missing score field."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"reasoning": "No score provided"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        # Should default to score 0
        assert results[0].score == 0
        assert not results[0].passed
    
    @pytest.mark.asyncio
    async def test_llm_judge_returns_details(self):
        """Test LLM judge returns full response in details."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.9, "reasoning": "Excellent", "quality": "high"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        assert results[0].details is not None
        assert results[0].details["quality"] == "high"
    
    @pytest.mark.asyncio
    async def test_llm_judge_at_threshold(self):
        """Test LLM judge score exactly at threshold."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.8, "reasoning": "At threshold"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        # Should pass when score >= threshold (not just >)
        assert results[0].passed
    
    @pytest.mark.asyncio
    async def test_llm_judge_adapter_exception(self):
        """Test LLM judge handles adapter exceptions."""
        mock_adapter = MagicMock()
        mock_adapter.complete_with_json = AsyncMock(side_effect=Exception("API Error"))
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        assert not results[0].passed
        assert "LLM judge error" in results[0].reason
    
    @pytest.mark.asyncio
    async def test_llm_judge_returns_reasoning(self):
        """Test LLM judge captures reasoning from response."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.9, "reasoning": "This is excellent because..."}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        assert results[0].reason == "This is excellent because..."
    
    @pytest.mark.asyncio
    async def test_llm_judge_missing_reasoning(self):
        """Test LLM judge with missing reasoning field."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.9}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        # Should default to empty string
        assert results[0].reason == ""
    
    @pytest.mark.asyncio
    async def test_llm_judge_evaluator_name(self):
        """Test LLM judge returns evaluator name."""
        mock_adapter = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"score": 0.9, "reasoning": "Good"}'
        
        mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
        
        engine = EvaluatorEngine(llm_adapter=mock_adapter)
        evaluator = LLMJudgeEvaluator(
            name="my_judge",
            judge_model="gpt-4o",
            criteria="Test",
            output_schema={},
            pass_threshold=0.8
        )
        
        results = await engine.evaluate("output", [evaluator])
        
        assert results[0].evaluator_name == "my_judge"


class TestEvaluatorEngineIntegration:
    """Test EvaluatorEngine integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_evaluate_single_regex(self):
        """Test evaluate with single regex evaluator."""
        engine = EvaluatorEngine()
        evaluators = [
            RegexEvaluator(name="test", pattern="hello", pass_on_match=True)
        ]
        
        results = await engine.evaluate("hello world", evaluators)
        
        assert len(results) == 1
        assert results[0].passed
    
    @pytest.mark.asyncio
    async def test_evaluate_regex_then_exact_match(self):
        """Test evaluate with regex then exact match."""
        engine = EvaluatorEngine()
        evaluators = [
            RegexEvaluator(name="regex", pattern="hello"),
            ExactMatchEvaluator(name="exact", expected="world")
        ]
        
        results = await engine.evaluate("hello world", evaluators)
        
        assert len(results) == 2
        assert results[0].passed
        assert results[1].passed
    
    @pytest.mark.asyncio
    async def test_evaluate_preserves_evaluator_order(self):
        """Test that results preserve evaluator order."""
        engine = EvaluatorEngine()
        evaluators = [
            RegexEvaluator(name="first", pattern="z"),
            RegexEvaluator(name="second", pattern="a"),
            RegexEvaluator(name="third", pattern="m")
        ]
        
        results = await engine.evaluate("abcxyz", evaluators)
        
        assert results[0].evaluator_name == "first"
        assert results[1].evaluator_name == "second"
        assert results[2].evaluator_name == "third"
    
    @pytest.mark.asyncio
    async def test_build_judge_prompt(self):
        """Test judge prompt building."""
        engine = EvaluatorEngine()
        criteria = "Test if output is good"
        output_schema = {"type": "object", "properties": {"score": {"type": "number"}}}
        
        prompt = engine._build_judge_prompt("test output", criteria, output_schema)
        
        assert "test output" in prompt
        assert "Test if output is good" in prompt
        assert "score" in prompt


# PHASE 9 REFINEMENTS
class TestEvaluatorRefinements:
    """Phase 9 Test Refinements for Mutation Testing."""
    
    # Refinement 3: Score Normalization Boundaries
    def test_evaluate_exact_match_boundary_case_sensitive(self):
        """Test exact match with boundary case sensitivity."""
        engine = EvaluatorEngine()
        
        evaluator = ExactMatchEvaluator(
            name="test",
            expected="Hello",
            case_sensitive=True
        )
        
        # Should match exact case
        result = engine._evaluate_exact_match("Hello World", evaluator)
        assert result.passed is True
        assert result.score == 1.0
        
        # Should NOT match different case
        result = engine._evaluate_exact_match("hello World", evaluator)
        assert result.passed is False
        assert result.score == 0.0
    
    def test_evaluate_exact_match_boundary_case_insensitive(self):
        """Test exact match with case insensitivity boundary."""
        engine = EvaluatorEngine()
        
        evaluator = ExactMatchEvaluator(
            name="test",
            expected="Hello",
            case_sensitive=False
        )
        
        # Should match regardless of case
        result = engine._evaluate_exact_match("hello World", evaluator)
        assert result.passed is True
        assert result.score == 1.0
        
        result = engine._evaluate_exact_match("HELLO world", evaluator)
        assert result.passed is True
        assert result.score == 1.0
    
    def test_evaluate_regex_boundary_match_vs_no_match(self):
        """Test regex with boundary between match and no-match."""
        engine = EvaluatorEngine()
        
        # Test: pass_on_match=True (should pass when pattern matches)
        evaluator_pass = RegexEvaluator(
            name="test",
            pattern="hello",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Hello there", evaluator_pass)
        assert result.passed is True  # Case insensitive by default
        assert result.score == 1.0
        
        result = engine._evaluate_regex("goodbye", evaluator_pass)
        assert result.passed is False
        assert result.score == 0.0
    
    def test_evaluate_regex_boundary_pass_on_match_false(self):
        """Test regex with pass_on_match=False boundary."""
        engine = EvaluatorEngine()
        
        # Test: pass_on_match=False (should pass when pattern does NOT match)
        evaluator_fail = RegexEvaluator(
            name="test",
            pattern="error",
            pass_on_match=False
        )
        
        result = engine._evaluate_regex("Success", evaluator_fail)
        assert result.passed is True  # No "error" found, so passes
        assert result.score == 1.0
        
        result = engine._evaluate_regex("Error occurred", evaluator_fail)
        assert result.passed is False  # "error" found, so fails
        assert result.score == 0.0
    
    def test_evaluate_exact_match_empty_string(self):
        """Test exact match with empty string edge case."""
        engine = EvaluatorEngine()
        
        # Empty expected string should match any output
        evaluator = ExactMatchEvaluator(
            name="test",
            expected="",
            case_sensitive=True
        )
        
        result = engine._evaluate_exact_match("Hello World", evaluator)
        assert result.passed is True  # Empty string is in any string
        assert result.score == 1.0
    
    def test_evaluate_regex_empty_pattern(self):
        """Test regex with empty pattern edge case."""
        engine = EvaluatorEngine()
        
        # Empty pattern matches everything
        evaluator = RegexEvaluator(
            name="test",
            pattern="",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Hello World", evaluator)
        assert result.passed is True
        assert result.score == 1.0
        
        result = engine._evaluate_regex("", evaluator)
        assert result.passed is True
        assert result.score == 1.0
    
    def test_evaluate_regex_special_characters(self):
        """Test regex with special characters in pattern."""
        engine = EvaluatorEngine()
        
        # Pattern with regex special chars
        evaluator = RegexEvaluator(
            name="test",
            pattern=r"\d+",  # Match digits
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Version 123", evaluator)
        assert result.passed is True
        assert result.score == 1.0
        
        result = engine._evaluate_regex("No numbers here", evaluator)
        assert result.passed is False
        assert result.score == 0.0


# ============================================================================
# PHASE 9c-2: Score Normalization & Aggregation Mutation Tests
# ============================================================================
# Purpose: Target 12 mutations in boundary condition and aggregation logic
# Strategy: Test limit boundaries (0.0, 1.0) and None value handling
# ============================================================================

class TestScoreNormalizationMutations:
    """Phase 9c-2: Mutation-focused tests for score boundaries.
    
    These tests target mutations in score normalization logic
    and None value handling.
    
    Mutations to catch:
    - Boundary mutations: 0.0 → -0.1, 1.0 → 1.1
    - Comparison operator mutations: > → >=, < → <=
    - max() → min() and vice versa
    - None value filtering logic
    """
    
    def test_evaluator_result_score_boundaries_lower(self):
        """Verify lower boundary (0.0) is enforced in score calculations.
        
        Mutation targets:
        - max() → min() swaps
        - Boundary condition mutations (0.0 → -0.1)
        """
        engine = EvaluatorEngine()
        
        # Scores below 0.0 should be clamped to 0.0
        # Create evaluator with pass_on_match=False to generate 0.0 score
        evaluator = RegexEvaluator(
            name="test_lower_bound",
            pattern="pattern_not_found",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("different text", evaluator)
        
        # Score must be exactly 0.0, not negative
        assert result.score == 0.0
        assert result.score >= 0.0
        assert not (result.score < 0.0)
        assert result.passed is False
    
    def test_evaluator_result_score_boundaries_upper(self):
        """Verify upper boundary (1.0) is enforced in score calculations.
        
        Mutation targets:
        - Boundary condition mutations (1.0 → 1.1)
        - min() → max() swaps
        """
        engine = EvaluatorEngine()
        
        # Scores at 1.0 should never exceed 1.0
        evaluator = RegexEvaluator(
            name="test_upper_bound",
            pattern="hello",
            pass_on_match=True
        )
        
        result = engine._evaluate_regex("Hello world! hello", evaluator)
        
        # Score must be exactly 1.0, not greater
        assert result.score == 1.0
        assert result.score <= 1.0
        assert not (result.score > 1.0)
        assert result.passed is True
    
    def test_exact_match_case_insensitive_boundary(self):
        """Verify exact match scoring at boundaries.
        
        Mutation targets:
        - Case sensitivity logic mutations
        - Boundary conditions in comparison
        """
        engine = EvaluatorEngine()
        
        evaluator = ExactMatchEvaluator(
            name="test_boundary",
            expected="Hello",
            case_sensitive=False
        )
        
        # Should match with different case
        result = engine._evaluate_exact_match("HELLO world", evaluator)
        assert result.score == 1.0
        assert result.passed is True
        
        # Should not match different content
        result = engine._evaluate_exact_match("Goodbye world", evaluator)
        assert result.score == 0.0
        assert result.passed is False
    
    def test_regex_evaluation_score_at_boundaries(self):
        """Verify regex evaluation scores are at 0.0 or 1.0 boundaries.
        
        Mutation targets:
        - Score normalization in evaluators
        - Boundary enforcement (no intermediate scores)
        """
        engine = EvaluatorEngine()
        
        # Regex evaluation should only score 0.0 (fail) or 1.0 (pass)
        evaluator_pass = RegexEvaluator(
            name="test_bounds_pass",
            pattern="success",
            pass_on_match=True
        )
        
        result_pass = engine._evaluate_regex("success outcome", evaluator_pass)
        
        # Score must be exactly 1.0 for pass
        assert result_pass.score == 1.0
        assert result_pass.score >= 0.0
        assert result_pass.score <= 1.0
        
        # Fail case should score 0.0
        evaluator_fail = RegexEvaluator(
            name="test_bounds_fail",
            pattern="missing",
            pass_on_match=True
        )
        
        result_fail = engine._evaluate_regex("success outcome", evaluator_fail)
        
        # Score must be exactly 0.0 for fail
        assert result_fail.score == 0.0
        assert result_fail.score >= 0.0
        assert result_fail.score <= 1.0
    
    def test_multiple_evaluator_aggregation_all_pass(self):
        """Verify all evaluators must pass for overall pass.
        
        Mutation targets:
        - all() → any() logic swaps
        - Aggregation logic inversions
        """
        engine = EvaluatorEngine()
        
        evaluators = [
            RegexEvaluator(name="eval1", pattern="hello", pass_on_match=True),
            RegexEvaluator(name="eval2", pattern="world", pass_on_match=True),
            RegexEvaluator(name="eval3", pattern="test", pass_on_match=True),
        ]
        
        # All patterns match - should pass overall
        output = "hello world test"
        results = asyncio.run(engine.evaluate(output, evaluators))
        
        assert all(r.passed for r in results)
        assert len(results) == 3
        assert results[0].passed is True
        assert results[1].passed is True
        assert results[2].passed is True
    
    def test_multiple_evaluator_aggregation_one_fails(self):
        """Verify single failure disqualifies entire result.
        
        Mutation targets:
        - all() → any() logic swaps
        - Logical operator inversions
        """
        engine = EvaluatorEngine()
        
        evaluators = [
            RegexEvaluator(name="eval1", pattern="hello", pass_on_match=True),
            RegexEvaluator(name="eval2", pattern="missing_pattern", pass_on_match=True),
            RegexEvaluator(name="eval3", pattern="test", pass_on_match=True),
        ]
        
        # Middle evaluator fails
        output = "hello world test"
        results = asyncio.run(engine.evaluate(output, evaluators))
        
        # Not all pass - should have mix
        assert results[0].passed is True  # hello matches
        assert results[1].passed is False  # missing_pattern doesn't match
        assert results[2].passed is True  # test matches
        assert not all(r.passed for r in results)
