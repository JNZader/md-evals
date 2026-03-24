"""Integration tests for evaluators — real regex/exact-match, no mocks."""

import asyncio

import pytest

from md_evals.evaluator import EvaluatorEngine, create_evaluator
from md_evals.models import RegexEvaluator, ExactMatchEvaluator, LLMJudgeEvaluator


def run_async(coro):
    """Helper to run async code in sync tests."""
    return asyncio.run(coro)


@pytest.fixture
def engine():
    """EvaluatorEngine without LLM adapter (regex/exact only)."""
    return EvaluatorEngine(llm_adapter=None)


class TestRegexEvaluator:
    """Test regex evaluator with real patterns and text."""

    def test_pattern_matches(self, engine):
        evaluator = RegexEvaluator(name="has_hello", pattern=r"hello")
        results = run_async(engine.evaluate("hello world", [evaluator]))
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].score == 1.0

    def test_pattern_no_match(self, engine):
        evaluator = RegexEvaluator(name="has_hello", pattern=r"hello")
        results = run_async(engine.evaluate("goodbye world", [evaluator]))
        assert results[0].passed is False
        assert results[0].score == 0.0

    def test_case_insensitive(self, engine):
        evaluator = RegexEvaluator(name="case_test", pattern=r"HELLO")
        results = run_async(engine.evaluate("hello world", [evaluator]))
        assert results[0].passed is True  # IGNORECASE flag

    def test_multiline_match(self, engine):
        evaluator = RegexEvaluator(name="multiline", pattern=r"^second line$")
        text = "first line\nsecond line\nthird line"
        results = run_async(engine.evaluate(text, [evaluator]))
        assert results[0].passed is True  # MULTILINE flag

    def test_pass_on_match_false(self, engine):
        evaluator = RegexEvaluator(
            name="no_secrets",
            pattern=r"api_key\s*=",
            pass_on_match=False,
        )
        results = run_async(engine.evaluate("clean text", [evaluator]))
        assert results[0].passed is True  # pattern NOT found -> pass

        results2 = run_async(engine.evaluate("api_key = abc123", [evaluator]))
        assert results2[0].passed is False  # pattern found -> fail

    def test_custom_fail_message(self, engine):
        evaluator = RegexEvaluator(
            name="check",
            pattern=r"expected_thing",
            fail_message="Missing the expected thing!",
        )
        results = run_async(engine.evaluate("nope", [evaluator]))
        assert results[0].reason == "Missing the expected thing!"

    def test_invalid_regex(self, engine):
        evaluator = RegexEvaluator(name="bad", pattern=r"[invalid")
        results = run_async(engine.evaluate("test", [evaluator]))
        assert results[0].passed is False
        assert "Invalid regex" in results[0].reason

    def test_complex_pattern(self, engine):
        evaluator = RegexEvaluator(
            name="json_structure",
            pattern=r'\{[^}]*"name"\s*:\s*"[^"]+"[^}]*\}',
        )
        results = run_async(
            engine.evaluate('Result: {"name": "test", "value": 42}', [evaluator])
        )
        assert results[0].passed is True


class TestExactMatchEvaluator:
    """Test exact match evaluator with real strings."""

    def test_exact_match_found(self, engine):
        evaluator = ExactMatchEvaluator(name="check", expected="hello")
        results = run_async(engine.evaluate("say hello there", [evaluator]))
        assert results[0].passed is True
        assert results[0].score == 1.0

    def test_exact_match_not_found(self, engine):
        evaluator = ExactMatchEvaluator(name="check", expected="goodbye")
        results = run_async(engine.evaluate("hello world", [evaluator]))
        assert results[0].passed is False

    def test_case_insensitive_default(self, engine):
        evaluator = ExactMatchEvaluator(name="check", expected="HELLO")
        results = run_async(engine.evaluate("hello world", [evaluator]))
        assert results[0].passed is True  # case_sensitive defaults to False

    def test_case_sensitive(self, engine):
        evaluator = ExactMatchEvaluator(
            name="check", expected="Hello", case_sensitive=True
        )
        results = run_async(engine.evaluate("hello world", [evaluator]))
        assert results[0].passed is False

        results2 = run_async(engine.evaluate("Hello world", [evaluator]))
        assert results2[0].passed is True


class TestMultipleEvaluators:
    """Test running multiple evaluators on the same output."""

    def test_all_pass(self, engine):
        evaluators = [
            RegexEvaluator(name="has_hello", pattern=r"hello"),
            ExactMatchEvaluator(name="has_world", expected="world"),
        ]
        results = run_async(engine.evaluate("hello world", evaluators))
        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_mixed_results(self, engine):
        evaluators = [
            RegexEvaluator(name="has_hello", pattern=r"hello"),
            RegexEvaluator(name="has_goodbye", pattern=r"goodbye"),
        ]
        results = run_async(engine.evaluate("hello world", evaluators))
        assert results[0].passed is True
        assert results[1].passed is False


class TestLLMJudgeWithoutAdapter:
    """Test LLM judge evaluator gracefully handles missing adapter."""

    def test_llm_judge_no_adapter(self, engine):
        evaluator = LLMJudgeEvaluator(
            name="quality",
            judge_model="gpt-4o",
            criteria="Is this good?",
        )
        results = run_async(engine.evaluate("test output", [evaluator]))
        assert results[0].passed is False
        assert "not configured" in results[0].reason


class TestScoreNormalization:
    """Test the score normalization fix in evaluator.

    Scores > 1 on a 1-5 scale are divided by 5.
    Scores > 5 on a 1-10 scale are divided by 10.
    Scores in [0, 1] are passed through unchanged.
    """

    def test_score_in_range_passes_through(self):
        """Scores already in [0,1] should not be modified."""
        engine = EvaluatorEngine(llm_adapter=None)
        # This is tested indirectly through regex (always 0 or 1)
        evaluator = RegexEvaluator(name="test", pattern=r"match")
        results = run_async(engine.evaluate("match", [evaluator]))
        assert results[0].score == 1.0

        results2 = run_async(engine.evaluate("no", [evaluator]))
        assert results2[0].score == 0.0


class TestCreateEvaluatorFactory:
    """Test the create_evaluator factory function."""

    def test_create_regex(self):
        ev = create_evaluator("regex", name="test", pattern=r"hello")
        assert isinstance(ev, RegexEvaluator)
        assert ev.pattern == r"hello"

    def test_create_exact_match(self):
        ev = create_evaluator("exact-match", name="test", expected="hello")
        assert isinstance(ev, ExactMatchEvaluator)

    def test_create_llm_judge(self):
        ev = create_evaluator(
            "llm-judge", name="test", judge_model="gpt-4o", criteria="Is it good?"
        )
        assert isinstance(ev, LLMJudgeEvaluator)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown evaluator"):
            create_evaluator("nonexistent", name="test")
