"""Tests for prompt baselines grader."""

from md_evals.graders.prompt_baselines import (
    BASELINE_PATTERNS,
    BaselineReport,
    compare_prompts,
    detect_pattern,
    evaluate_prompt,
    format_report,
)


GOOD_PROMPT = """You are a helpful AI coding assistant made by Acme Corp.
Your knowledge cutoff is January 2025. You don't have access to the internet.

You must not generate harmful, illegal, or deceptive content.
If you don't know something, say so rather than making things up.
Handle malformed input gracefully with clear error messages.

Focus only on coding tasks. Do not attempt medical or legal advice.
Think step by step before providing complex answers.

Use the available tools when appropriate. Call the search function
for questions about current events.

Respond in markdown format. Be concise and professional.
Cite sources when providing factual claims.

Consider the full conversation context when responding.
"""

MINIMAL_PROMPT = "You are a chatbot. Answer questions."

EMPTY_PROMPT = ""


class TestBaselinePatterns:
    def test_has_at_least_10_patterns(self):
        assert len(BASELINE_PATTERNS) >= 10

    def test_unique_names(self):
        names = [p.name for p in BASELINE_PATTERNS]
        assert len(set(names)) == len(names)

    def test_covers_multiple_categories(self):
        categories = {p.category for p in BASELINE_PATTERNS}
        assert len(categories) >= 4

    def test_all_have_keywords(self):
        for p in BASELINE_PATTERNS:
            assert len(p.detection_keywords) > 0

    def test_all_have_examples(self):
        for p in BASELINE_PATTERNS:
            assert len(p.example) > 0


class TestDetectPattern:
    def test_detects_identity(self):
        pattern = next(p for p in BASELINE_PATTERNS if p.name == "identity_declaration")
        assert detect_pattern("You are a helpful assistant", pattern)

    def test_detects_safety(self):
        pattern = next(p for p in BASELINE_PATTERNS if p.name == "safety_refusal")
        assert detect_pattern("You must not generate harmful content", pattern)

    def test_case_insensitive(self):
        pattern = next(p for p in BASELINE_PATTERNS if p.name == "identity_declaration")
        assert detect_pattern("YOU ARE an AI", pattern)

    def test_no_false_positive(self):
        pattern = next(p for p in BASELINE_PATTERNS if p.name == "tool_instructions")
        assert not detect_pattern("The weather is nice today", pattern)


class TestEvaluatePrompt:
    def test_good_prompt_scores_high(self):
        report = evaluate_prompt(GOOD_PROMPT, "good")
        assert report.score > 70
        assert report.coverage > 70

    def test_minimal_prompt_scores_low(self):
        report = evaluate_prompt(MINIMAL_PROMPT, "minimal")
        assert report.score < 30

    def test_empty_prompt_scores_zero(self):
        report = evaluate_prompt(EMPTY_PROMPT, "empty")
        assert report.score == 0
        assert report.coverage == 0

    def test_returns_correct_type(self):
        report = evaluate_prompt(GOOD_PROMPT)
        assert isinstance(report, BaselineReport)

    def test_results_count_matches_patterns(self):
        report = evaluate_prompt(GOOD_PROMPT)
        assert len(report.results) == len(BASELINE_PATTERNS)

    def test_missing_plus_strengths_equals_total(self):
        report = evaluate_prompt(GOOD_PROMPT)
        assert len(report.missing) + len(report.strengths) == len(BASELINE_PATTERNS)

    def test_coverage_percentage(self):
        report = evaluate_prompt(GOOD_PROMPT)
        expected = len(report.strengths) / len(BASELINE_PATTERNS) * 100
        assert abs(report.coverage - round(expected, 1)) < 0.2

    def test_identifies_missing_patterns(self):
        report = evaluate_prompt(MINIMAL_PROMPT)
        assert len(report.missing) > 5

    def test_identifies_strengths(self):
        report = evaluate_prompt(GOOD_PROMPT)
        assert "identity_declaration" in report.strengths
        assert "safety_refusal" in report.strengths


class TestFormatReport:
    def test_contains_header(self):
        report = evaluate_prompt(GOOD_PROMPT, "test")
        output = format_report(report)
        assert "## Prompt Baseline: test" in output

    def test_contains_scores(self):
        report = evaluate_prompt(GOOD_PROMPT, "test")
        output = format_report(report)
        assert "Score:" in output
        assert "Coverage:" in output

    def test_contains_strengths_section(self):
        report = evaluate_prompt(GOOD_PROMPT, "test")
        output = format_report(report)
        assert "### Strengths" in output

    def test_contains_missing_section_for_incomplete(self):
        report = evaluate_prompt(MINIMAL_PROMPT, "minimal")
        output = format_report(report)
        assert "### Missing" in output


class TestComparePrompts:
    def test_compares_multiple(self):
        reports = compare_prompts({"good": GOOD_PROMPT, "minimal": MINIMAL_PROMPT})
        assert len(reports) == 2
        assert reports[0].score > reports[1].score

    def test_empty_dict(self):
        reports = compare_prompts({})
        assert reports == []
