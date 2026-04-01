"""Tests for contract-based assertion graders."""

from pathlib import Path

from md_evals.graders.contract_grader import (
    OutputContract,
    ContractAssertionGrader,
    ABContractGrader,
)


# ── Fixtures ──

VALID_SKILL_OUTPUT = """\
# My Skill

## Purpose

This skill does something useful for the user. It provides
a structured approach to solving problems with clear guidance.

## Critical Rules

1. Always validate input before processing.
2. Never expose internal state to callers.
3. Handle errors gracefully with meaningful messages.

## Examples

Here is an example of correct usage with detailed explanation
that covers the main use case and edge cases thoroughly.
"""

ALT_SKILL_OUTPUT = """\
# My Skill

## Purpose

An alternative approach to the same problem using different
techniques and patterns that achieve equivalent results.

## Critical Rules

1. Prefer composition over inheritance in all designs.
2. Keep functions pure where possible for testability.
3. Document all public interfaces with examples.

## Examples

A different example showing the alternative approach with
comprehensive coverage of common scenarios and edge cases.
"""


class TestOutputContract:
    """Tests for OutputContract dataclass."""

    def test_default_empty_contract(self):
        contract = OutputContract()
        assert contract.required_sections == []
        assert contract.format_rules == []
        assert contract.forbidden_patterns == []
        assert contract.min_words == 0
        assert contract.max_words == 0

    def test_contract_with_all_fields(self):
        contract = OutputContract(
            required_sections=[r"^## Purpose"],
            format_rules=[r"^# "],
            forbidden_patterns=[r"TODO"],
            min_words=10,
            max_words=500,
        )
        assert len(contract.required_sections) == 1
        assert contract.min_words == 10
        assert contract.max_words == 500


class TestContractAssertionGrader:
    """Tests for ContractAssertionGrader."""

    def test_all_contract_rules_satisfied(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose", r"^## Critical Rules", r"^## Examples"],
            format_rules=[r"^# "],
            min_words=20,
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content=VALID_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_missing_required_section(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose", r"^## Risks"],
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content=VALID_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Missing required section" in result.reason
        assert "Risks" in result.reason

    def test_forbidden_pattern_found(self, tmp_path: Path):
        content = "## Purpose\n\nThis has a TODO that should not be here."
        contract = OutputContract(
            forbidden_patterns=[r"TODO"],
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content=content,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Forbidden pattern found" in result.reason

    def test_word_count_below_minimum(self, tmp_path: Path):
        contract = OutputContract(min_words=100)
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content="Too short.",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "below minimum" in result.reason

    def test_word_count_above_maximum(self, tmp_path: Path):
        contract = OutputContract(max_words=5)
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content="This content has way more than five words in total here.",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "exceeds maximum" in result.reason

    def test_partial_score(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose", r"^## Missing"],
            format_rules=[r"^# "],
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content=VALID_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        # 2 of 3 rules pass = 0.6667
        assert 0.6 < result.score < 0.7

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "output.md").write_text(VALID_SKILL_OUTPUT)
        contract = OutputContract(
            required_sections=[r"^## Purpose"],
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            path="output.md",
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_not_found(self, tmp_path: Path):
        contract = OutputContract(required_sections=[r"^## Purpose"])
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            path="missing.md",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_no_content_or_path(self, tmp_path: Path):
        contract = OutputContract(required_sections=[r"^## Purpose"])
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "No content or path" in result.reason

    def test_empty_contract_passes(self, tmp_path: Path):
        contract = OutputContract()
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content="Anything goes.",
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_invalid_regex_pattern(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"[invalid("],
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content="Some content",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Invalid section pattern" in result.reason

    def test_details_contain_metadata(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose"],
            min_words=5,
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content=VALID_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.details is not None
        assert "total_rules" in result.details
        assert "passed_rules" in result.details
        assert "word_count" in result.details

    def test_multiple_violations(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Missing1", r"^## Missing2"],
            forbidden_patterns=[r"Purpose"],
            min_words=1000,
        )
        grader = ContractAssertionGrader(
            name="contract_check",
            contract=contract,
            content=VALID_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert len(result.details["violations"]) >= 3


class TestABContractGrader:
    """Tests for ABContractGrader."""

    def test_both_variants_satisfy_contract(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose", r"^## Critical Rules", r"^## Examples"],
            format_rules=[r"^# "],
            min_words=20,
        )
        grader = ABContractGrader(
            name="ab_check",
            contract=contract,
            variant_a=VALID_SKILL_OUTPUT,
            variant_b=ALT_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.details["variant_a"]["passed"] is True
        assert result.details["variant_b"]["passed"] is True

    def test_one_variant_fails(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose", r"^## Risks"],
        )
        grader = ABContractGrader(
            name="ab_check",
            contract=contract,
            variant_a=VALID_SKILL_OUTPUT,
            variant_b=ALT_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        # Both fail (neither has ## Risks)
        assert "variant_a failed" in result.reason

    def test_identical_variants_fail(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose"],
        )
        grader = ABContractGrader(
            name="ab_check",
            contract=contract,
            variant_a=VALID_SKILL_OUTPUT,
            variant_b=VALID_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "identical" in result.reason

    def test_score_averages_both_variants(self, tmp_path: Path):
        contract = OutputContract(
            required_sections=[r"^## Purpose", r"^## Nonexistent"],
        )
        # variant_a has Purpose (1/2 = 0.5), variant_b also (1/2 = 0.5)
        grader = ABContractGrader(
            name="ab_check",
            contract=contract,
            variant_a=VALID_SKILL_OUTPUT,
            variant_b=ALT_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.5

    def test_details_structure(self, tmp_path: Path):
        contract = OutputContract(required_sections=[r"^## Purpose"])
        grader = ABContractGrader(
            name="ab_check",
            contract=contract,
            variant_a=VALID_SKILL_OUTPUT,
            variant_b=ALT_SKILL_OUTPUT,
        )
        result = grader.grade(tmp_path)
        assert "variant_a" in result.details
        assert "variant_b" in result.details
        assert "passed" in result.details["variant_a"]
        assert "score" in result.details["variant_a"]
