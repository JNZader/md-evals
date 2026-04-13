"""Tests for cascade evaluator: cheap checks first, expensive LLM-judge last."""

from md_evals.graders.cascade_evaluator import (
    CascadeEvaluator,
    CascadeVerdict,
    RegexStep,
    KeywordStep,
    LLMJudgeStep,
)


# ============================================================================
# RegexStep
# ============================================================================


class TestRegexStep:
    """Tests for RegexStep."""

    def test_match_returns_pass(self):
        step = RegexStep(name="has_json", pattern=r"\{.*\}")
        result = step.evaluate('Output: {"key": "value"}')
        assert result.verdict == CascadeVerdict.PASS
        assert result.score == 1.0

    def test_match_with_pass_on_match_false_returns_fail(self):
        step = RegexStep(name="no_error", pattern=r"error", pass_on_match=False)
        result = step.evaluate("An error occurred")
        assert result.verdict == CascadeVerdict.FAIL
        assert result.score == 0.0

    def test_no_match_uncertain_by_default(self):
        step = RegexStep(name="has_json", pattern=r"\{.*\}")
        result = step.evaluate("No json here")
        assert result.verdict == CascadeVerdict.UNCERTAIN
        assert result.score == 0.5

    def test_no_match_definitive_when_uncertain_disabled(self):
        step = RegexStep(
            name="has_json",
            pattern=r"\{.*\}",
            pass_on_match=True,
            uncertain_on_no_match=False,
        )
        result = step.evaluate("No json here")
        assert result.verdict == CascadeVerdict.FAIL

    def test_no_match_pass_when_pass_on_match_false_and_uncertain_disabled(self):
        step = RegexStep(
            name="no_error",
            pattern=r"error",
            pass_on_match=False,
            uncertain_on_no_match=False,
        )
        result = step.evaluate("Everything is fine")
        assert result.verdict == CascadeVerdict.PASS

    def test_invalid_regex_returns_uncertain(self):
        step = RegexStep(name="bad", pattern="[invalid")
        result = step.evaluate("test")
        assert result.verdict == CascadeVerdict.UNCERTAIN
        assert "Invalid regex" in result.reason

    def test_case_insensitive(self):
        step = RegexStep(name="check", pattern=r"hello")
        result = step.evaluate("HELLO WORLD")
        assert result.verdict == CascadeVerdict.PASS


# ============================================================================
# KeywordStep
# ============================================================================


class TestKeywordStep:
    """Tests for KeywordStep."""

    def test_all_keywords_pass(self):
        step = KeywordStep(
            name="kw_check",
            keywords=["react", "typescript"],
            pass_threshold=0.8,
        )
        result = step.evaluate("Uses React and TypeScript")
        assert result.verdict == CascadeVerdict.PASS
        assert result.score == 1.0

    def test_no_keywords_uncertain(self):
        step = KeywordStep(name="kw_check", keywords=[])
        result = step.evaluate("anything")
        assert result.verdict == CascadeVerdict.UNCERTAIN

    def test_low_coverage_fail(self):
        step = KeywordStep(
            name="kw_check",
            keywords=["react", "typescript", "redux", "nextjs", "tailwind"],
            pass_threshold=0.8,
            fail_threshold=0.3,
        )
        result = step.evaluate("Uses React")
        # 1/5 = 0.2, below fail_threshold 0.3
        assert result.verdict == CascadeVerdict.FAIL

    def test_mid_coverage_uncertain(self):
        step = KeywordStep(
            name="kw_check",
            keywords=["react", "typescript", "redux"],
            pass_threshold=0.8,
            fail_threshold=0.2,
        )
        result = step.evaluate("Uses React and Redux")
        # 2/3 = 0.66, between 0.2 and 0.8
        assert result.verdict == CascadeVerdict.UNCERTAIN

    def test_case_insensitive(self):
        step = KeywordStep(
            name="kw_check",
            keywords=["React", "TypeScript"],
            pass_threshold=0.8,
        )
        result = step.evaluate("react and typescript")
        assert result.verdict == CascadeVerdict.PASS


# ============================================================================
# LLMJudgeStep
# ============================================================================


class TestLLMJudgeStep:
    """Tests for LLMJudgeStep."""

    def test_no_score_returns_uncertain(self):
        step = LLMJudgeStep(name="judge", criteria="Be helpful")
        result = step.evaluate("output")
        assert result.verdict == CascadeVerdict.UNCERTAIN

    def test_high_score_passes(self):
        step = LLMJudgeStep(
            name="judge",
            criteria="Be helpful",
            pass_threshold=0.7,
        )
        result = step.evaluate("output", llm_score=0.9, llm_reason="Good")
        assert result.verdict == CascadeVerdict.PASS
        assert result.score == 0.9

    def test_low_score_fails(self):
        step = LLMJudgeStep(
            name="judge",
            criteria="Be helpful",
            pass_threshold=0.7,
            fail_threshold=0.3,
        )
        result = step.evaluate("output", llm_score=0.1, llm_reason="Bad")
        assert result.verdict == CascadeVerdict.FAIL

    def test_mid_score_uncertain(self):
        step = LLMJudgeStep(
            name="judge",
            criteria="Be helpful",
            pass_threshold=0.7,
            fail_threshold=0.3,
        )
        result = step.evaluate("output", llm_score=0.5, llm_reason="Meh")
        assert result.verdict == CascadeVerdict.UNCERTAIN


# ============================================================================
# CascadeEvaluator — integration
# ============================================================================


class TestCascadeEvaluator:
    """Tests for the cascade orchestrator."""

    def test_short_circuits_on_regex_pass(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(name="has_json", pattern=r"\{.*\}"),
                KeywordStep(name="keywords", keywords=["react"]),
                LLMJudgeStep(name="judge", criteria="quality"),
            ],
        )
        result = cascade.evaluate('Here is {"data": 1}')
        assert result.passed is True
        assert result.decisive_step == "has_json"
        assert result.steps_executed == 1
        assert result.total_steps == 3

    def test_short_circuits_on_regex_fail(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(
                    name="no_error",
                    pattern=r"ERROR",
                    pass_on_match=False,
                ),
                KeywordStep(name="keywords", keywords=["react"]),
            ],
        )
        result = cascade.evaluate("ERROR: something broke")
        assert result.passed is False
        assert result.decisive_step == "no_error"
        assert result.steps_executed == 1

    def test_falls_through_to_keyword(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(name="has_json", pattern=r"\{.*\}"),
                KeywordStep(
                    name="keywords",
                    keywords=["react", "typescript"],
                    pass_threshold=0.8,
                ),
            ],
        )
        result = cascade.evaluate("Uses React and TypeScript for the frontend")
        # Regex uncertain (no JSON), keyword passes
        assert result.passed is True
        assert result.decisive_step == "keywords"
        assert result.steps_executed == 2

    def test_falls_through_to_llm_judge(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(name="has_json", pattern=r"\{.*\}"),
                KeywordStep(
                    name="keywords",
                    keywords=["react", "typescript", "redux"],
                    pass_threshold=0.8,
                    fail_threshold=0.2,
                ),
                LLMJudgeStep(name="judge", criteria="quality"),
            ],
        )
        # No JSON, partial keywords (1/3 = 0.33 — uncertain), LLM judge gets score
        result = cascade.evaluate(
            "Uses React for the UI", llm_score=0.85, llm_reason="Good output"
        )
        assert result.passed is True
        assert result.decisive_step == "judge"
        assert result.steps_executed == 3

    def test_all_uncertain_defaults_to_fail(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(name="check1", pattern=r"xyz123"),
                KeywordStep(
                    name="check2",
                    keywords=["foo", "bar", "baz"],
                    pass_threshold=0.9,
                    fail_threshold=0.1,
                ),
            ],
            default_pass=False,
        )
        result = cascade.evaluate("Some foo output")
        assert result.passed is False
        assert result.decisive_step == "default"

    def test_all_uncertain_defaults_to_pass_when_configured(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(name="check1", pattern=r"xyz123"),
            ],
            default_pass=True,
        )
        result = cascade.evaluate("no match here")
        assert result.passed is True
        assert result.decisive_step == "default"

    def test_empty_cascade_uses_default(self):
        cascade = CascadeEvaluator(name="empty", steps=[], default_pass=False)
        result = cascade.evaluate("anything")
        assert result.passed is False
        assert result.steps_executed == 0
        assert result.total_steps == 0

    def test_to_evaluator_result(self):
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(name="has_json", pattern=r"\{.*\}"),
            ],
        )
        result = cascade.evaluate('{"ok": true}')
        eval_result = result.to_evaluator_result(name="my_cascade")
        assert eval_result.evaluator_name == "my_cascade"
        assert eval_result.passed is True
        assert eval_result.details["decisive_step"] == "has_json"
        assert eval_result.details["steps_executed"] == 1

    def test_cost_savings_llm_not_invoked_when_regex_decides(self):
        """Verify LLM step is never reached when regex is decisive."""
        cascade = CascadeEvaluator(
            name="test_cascade",
            steps=[
                RegexStep(
                    name="no_error",
                    pattern=r"error",
                    pass_on_match=False,
                    uncertain_on_no_match=False,
                ),
                LLMJudgeStep(name="expensive_judge", criteria="quality"),
            ],
        )
        # No error → regex passes definitively
        result = cascade.evaluate("Clean output")
        assert result.passed is True
        assert result.steps_executed == 1
        # LLM judge was never invoked
        assert len(result.step_results) == 1
        assert result.step_results[0].evaluator_name == "no_error"

    def test_three_step_cascade_full_chain(self):
        """End-to-end: regex uncertain → keyword uncertain → LLM decides."""
        cascade = CascadeEvaluator(
            name="full_chain",
            steps=[
                RegexStep(name="regex", pattern=r"impossible_pattern_xyz"),
                KeywordStep(
                    name="keywords",
                    keywords=["alpha", "beta", "gamma", "delta"],
                    pass_threshold=0.9,
                    fail_threshold=0.1,
                ),
                LLMJudgeStep(
                    name="judge",
                    criteria="overall quality",
                    pass_threshold=0.6,
                    fail_threshold=0.3,
                ),
            ],
        )
        result = cascade.evaluate(
            "Output with alpha and beta concepts",
            llm_score=0.75,
            llm_reason="Solid quality",
        )
        assert result.passed is True
        assert result.decisive_step == "judge"
        assert result.steps_executed == 3
        assert len(result.step_results) == 3
