"""Tests for md_evals.pipeline.citations — citation validation.

Verifies Citation, CitationValidator, and citation_penalty with
comprehensive edge-case coverage.
"""

from __future__ import annotations

import pytest

from md_evals.pipeline.citations import Citation, CitationValidator, citation_penalty


# ── Test fixtures ──


SKILL_CONTENT = """\
# TypeScript Strict Skill

A skill for TypeScript development.

## Rules

- Always use TypeScript strict mode
- Never use `any` type explicitly
- Prefer interfaces over type aliases
- Use readonly for immutable data
- Export types from index files"""

SKILL_LINES = SKILL_CONTENT.splitlines()


# ============================================================================
# 1. Citation Dataclass Tests
# ============================================================================


class TestCitationDataclass:
    """Tests for the Citation frozen dataclass."""

    def test_create_citation(self):
        """Citation can be created with required fields."""
        c = Citation(line=4, text="Always use TypeScript strict mode", supports="correctness")
        assert c.line == 4
        assert c.text == "Always use TypeScript strict mode"
        assert c.supports == "correctness"
        assert c.verified is False

    def test_create_citation_verified(self):
        """Citation can be created with verified=True."""
        c = Citation(line=1, text="Test", supports="format", verified=True)
        assert c.verified is True

    def test_citation_is_frozen(self):
        """Citation is immutable (frozen dataclass)."""
        c = Citation(line=1, text="Test", supports="format")
        with pytest.raises(AttributeError):
            c.verified = True  # type: ignore[misc]

    def test_citation_equality(self):
        """Two Citations with same values are equal."""
        c1 = Citation(line=1, text="Test", supports="format")
        c2 = Citation(line=1, text="Test", supports="format")
        assert c1 == c2

    def test_citation_inequality(self):
        """Citations with different values are not equal."""
        c1 = Citation(line=1, text="Test", supports="format")
        c2 = Citation(line=2, text="Test", supports="format")
        assert c1 != c2


# ============================================================================
# 2. CitationValidator Tests
# ============================================================================


class TestCitationValidator:
    """Tests for the CitationValidator class."""

    def setup_method(self):
        self.validator = CitationValidator()

    def test_validate_exact_match(self):
        """Citation with exact line text verifies successfully."""
        citations = [
            Citation(line=7, text="Always use TypeScript strict mode", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert len(result) == 1
        assert result[0].verified is True

    def test_validate_fuzzy_match_substring(self):
        """Citation with substring of actual line verifies (fuzzy match)."""
        citations = [
            Citation(line=7, text="TypeScript strict mode", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is True

    def test_validate_case_insensitive(self):
        """Citation matching is case-insensitive."""
        citations = [
            Citation(line=7, text="ALWAYS USE TYPESCRIPT STRICT MODE", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is True

    def test_validate_out_of_range_high(self):
        """Citation with line number beyond file length is unverified."""
        citations = [
            Citation(line=999, text="nonexistent", supports="format"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is False

    def test_validate_out_of_range_zero(self):
        """Citation with line 0 (before 1-based range) is unverified."""
        citations = [
            Citation(line=0, text="something", supports="format"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is False

    def test_validate_negative_line(self):
        """Citation with negative line number is unverified."""
        citations = [
            Citation(line=-1, text="something", supports="format"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is False

    def test_validate_wrong_text(self):
        """Citation with correct line but wrong text is unverified."""
        citations = [
            Citation(line=7, text="Never use JavaScript", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is False

    def test_validate_empty_citation_text(self):
        """Citation with empty text is never verified."""
        citations = [
            Citation(line=7, text="", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is False

    def test_validate_empty_citations_list(self):
        """Empty citation list returns empty list."""
        result = self.validator.validate([], SKILL_CONTENT)
        assert result == []

    def test_validate_mixed_citations(self):
        """Mix of valid and invalid citations are correctly classified."""
        citations = [
            Citation(line=7, text="TypeScript strict mode", supports="correctness"),
            Citation(line=999, text="nonexistent", supports="format"),
            Citation(line=8, text="any", supports="safety"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is True
        assert result[1].verified is False
        assert result[2].verified is True  # "any" is substring of "Never use `any` type explicitly"

    def test_validate_preserves_citation_fields(self):
        """Validation preserves all original citation fields."""
        c = Citation(line=7, text="TypeScript strict mode", supports="correctness")
        result = self.validator.validate([c], SKILL_CONTENT)
        assert result[0].line == 7
        assert result[0].text == "TypeScript strict mode"
        assert result[0].supports == "correctness"

    def test_validate_with_leading_bullet_marker(self):
        """Lines with bullet markers (- ) are matched correctly."""
        # Line 7 starts with "- Always use TypeScript strict mode"
        citations = [
            Citation(line=7, text="- Always use TypeScript strict mode", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is True

    def test_validate_whitespace_tolerance(self):
        """Citation with extra whitespace still matches."""
        citations = [
            Citation(line=7, text="  Always use TypeScript strict mode  ", supports="correctness"),
        ]
        result = self.validator.validate(citations, SKILL_CONTENT)
        assert result[0].verified is True

    def test_validate_single_line_content(self):
        """Validation works with single-line content."""
        content = "Only one line"
        citations = [
            Citation(line=1, text="one line", supports="format"),
        ]
        result = self.validator.validate(citations, content)
        assert result[0].verified is True

    def test_validate_returns_new_objects(self):
        """Validation returns new Citation objects (not mutated originals)."""
        c = Citation(line=7, text="TypeScript strict mode", supports="correctness")
        result = self.validator.validate([c], SKILL_CONTENT)
        assert result[0] is not c
        assert result[0].verified is True
        assert c.verified is False  # Original unchanged


# ============================================================================
# 3. citation_penalty Tests
# ============================================================================


class TestCitationPenalty:
    """Tests for the citation_penalty function."""

    def test_all_verified_no_penalty(self):
        """All verified citations → penalty is 0.0."""
        citations = [
            Citation(line=1, text="t", supports="x", verified=True),
            Citation(line=2, text="t", supports="x", verified=True),
        ]
        assert citation_penalty(citations) == 0.0

    def test_none_verified_max_penalty(self):
        """No verified citations → penalty is 0.2."""
        citations = [
            Citation(line=1, text="t", supports="x", verified=False),
            Citation(line=2, text="t", supports="x", verified=False),
        ]
        assert citation_penalty(citations) == 0.2

    def test_empty_list_no_penalty(self):
        """Empty citation list → penalty is 0.0."""
        assert citation_penalty([]) == 0.0

    def test_half_verified_half_penalty(self):
        """50% verified → penalty is 0.1."""
        citations = [
            Citation(line=1, text="t", supports="x", verified=True),
            Citation(line=2, text="t", supports="x", verified=False),
        ]
        assert citation_penalty(citations) == 0.1

    def test_one_of_four_unverified(self):
        """25% unverified → penalty is 0.05."""
        citations = [
            Citation(line=1, text="t", supports="x", verified=True),
            Citation(line=2, text="t", supports="x", verified=True),
            Citation(line=3, text="t", supports="x", verified=True),
            Citation(line=4, text="t", supports="x", verified=False),
        ]
        assert citation_penalty(citations) == 0.05

    def test_penalty_bounded_at_0_2(self):
        """Penalty never exceeds 0.2 even with many unverified."""
        citations = [
            Citation(line=i, text="t", supports="x", verified=False)
            for i in range(100)
        ]
        penalty = citation_penalty(citations)
        assert penalty == 0.2

    def test_penalty_bounded_at_0_0(self):
        """Penalty never goes below 0.0."""
        citations = [
            Citation(line=i, text="t", supports="x", verified=True)
            for i in range(1, 100)
        ]
        penalty = citation_penalty(citations)
        assert penalty == 0.0
