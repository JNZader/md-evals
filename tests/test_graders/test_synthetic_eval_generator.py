"""Tests for synthetic_eval_generator — auto-generate evals from skills."""

from md_evals.graders.synthetic_eval_generator import (
    generate_eval_suite,
    format_eval_suite,
    suite_to_dict,
)


SAMPLE_SKILL = """---
name: test-skill
description: A test skill
version: 1.0.0
---

# Test Skill

## Purpose

Testing the synthetic eval generator.

## Constraints

1. Never skip input validation
2. Always return structured JSON
3. Maximum response time 5 seconds

## Execution Steps

### Step 1 — Validate

Check all inputs are valid.

### Step 2 — Process

Transform and process.

## Critical Rules

1. **Always validate input before processing**
2. **Never expose internal errors to users**
3. **Log all operations for audit trail**

## Rationalizations

- **Excuse**: "Input is trusted, no need to validate"
  **Rebuttal**: Never trust input from any source.

- **Excuse**: "Logging slows things down"
  **Rebuttal**: Audit trail is non-negotiable.
"""


class TestGenerateEvalSuite:
    def test_generates_from_critical_rules(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        assert suite.skill_name == "test-skill"
        # 3 rules → 3 negative + 3 positive = 6 cases from rules
        rule_cases = [c for c in suite.cases if "rule" in c.name]
        assert len(rule_cases) == 6

    def test_generates_negative_cases(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        assert len(suite.negative_cases) >= 3
        # Should have rule violations
        assert any("violation" in c.name for c in suite.negative_cases)

    def test_generates_positive_cases(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        assert len(suite.positive_cases) >= 3
        assert any("compliance" in c.name for c in suite.positive_cases)

    def test_generates_edge_cases_from_constraints(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        assert len(suite.edge_cases) >= 2
        assert any("constraint" in c.name for c in suite.edge_cases)

    def test_generates_from_rationalizations(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        resist_cases = [c for c in suite.cases if "rationalization" in c.name]
        assert len(resist_cases) >= 2
        assert any("Input is trusted" in c.source_rule for c in resist_cases)

    def test_total_case_count(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        # 3 rules × 2 (pos+neg) + 3 constraints (edge) + 2 rationalizations (neg) = 11
        assert len(suite.cases) >= 10

    def test_case_has_required_fields(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        for case in suite.cases:
            assert case.name
            assert case.category in ("positive", "negative", "edge")
            assert case.input_prompt
            assert case.expected_behavior
            assert case.grading_criteria

    def test_handles_skill_without_sections(self):
        minimal = "---\nname: minimal\n---\n# Minimal\nJust content."
        suite = generate_eval_suite(minimal)
        assert suite.skill_name == "minimal"
        assert len(suite.cases) == 0

    def test_handles_empty_content(self):
        suite = generate_eval_suite("")
        assert suite.skill_name == "unknown"
        assert len(suite.cases) == 0


class TestFormatEvalSuite:
    def test_produces_markdown(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        md = format_eval_suite(suite)
        assert "# Synthetic Eval Suite: test-skill" in md
        assert "Positive Cases" in md
        assert "Negative Cases" in md
        assert "Edge Cases" in md

    def test_empty_suite(self):
        suite = generate_eval_suite("")
        md = format_eval_suite(suite)
        assert "unknown" in md


class TestSerialization:
    def test_to_dict(self):
        suite = generate_eval_suite(SAMPLE_SKILL)
        data = suite_to_dict(suite)
        assert data["skill_name"] == "test-skill"
        assert len(data["cases"]) == len(suite.cases)
        for case in data["cases"]:
            assert "name" in case
            assert "category" in case
            assert "input_prompt" in case
