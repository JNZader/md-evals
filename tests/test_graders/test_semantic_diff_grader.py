"""Tests for semantic diff grader — semantic unit parsing, matching, and grading."""

from pathlib import Path

from md_evals.graders.semantic_diff_grader import (
    SemanticDiffGrader,
    UnitType,
    parse_semantic_units,
    compute_semantic_diff,
    _extract_key_terms,
    _classify_unit,
)


# ── Unit Parsing ──


class TestParseSemanticUnits:
    """Tests for parse_semantic_units."""

    def test_empty_text_returns_empty(self):
        assert parse_semantic_units("") == []
        assert parse_semantic_units("   ") == []

    def test_single_sentence(self):
        units = parse_semantic_units("Python is an interpreted language.")
        assert len(units) == 1
        assert units[0].unit_type == UnitType.DEFINITION
        assert "python" in units[0].key_terms

    def test_multiple_sentences(self):
        text = "Python is fast. It supports OOP. It was released in 1991."
        units = parse_semantic_units(text)
        assert len(units) == 3

    def test_bullet_list_items(self):
        text = "Key features:\n- Dynamic typing\n- Garbage collection\n- Large standard library"
        units = parse_semantic_units(text)
        assert len(units) >= 3

    def test_numbered_list_items(self):
        text = "1. Install Python\n2. Create virtualenv\n3. Run tests"
        units = parse_semantic_units(text)
        assert len(units) == 3
        assert all(u.unit_type == UnitType.INSTRUCTION for u in units)

    def test_preserves_original_text(self):
        text = "Python is interpreted."
        units = parse_semantic_units(text)
        assert units[0].text == "Python is interpreted."

    def test_normalized_text_lowercased(self):
        text = "Python Is Great."
        units = parse_semantic_units(text)
        assert units[0].normalized == "python is great"


class TestClassifyUnit:
    """Tests for unit type classification."""

    def test_instruction_imperative(self):
        assert _classify_unit("Use Python 3.12 for this project.") == UnitType.INSTRUCTION

    def test_instruction_numbered(self):
        assert _classify_unit("1. Install dependencies") == UnitType.INSTRUCTION

    def test_definition(self):
        assert _classify_unit("Python is a programming language.") == UnitType.DEFINITION

    def test_example(self):
        assert _classify_unit("For example, you can use list comprehensions.") == UnitType.EXAMPLE

    def test_fact_with_numbers(self):
        assert _classify_unit("Python was released in 1991.") == UnitType.FACT

    def test_claim(self):
        assert _classify_unit("Python is better than Java for scripting.") == UnitType.CLAIM


class TestExtractKeyTerms:
    """Tests for key term extraction."""

    def test_filters_stop_words(self):
        terms = _extract_key_terms("The quick brown fox is a good animal")
        assert "the" not in terms
        assert "is" not in terms
        assert "quick" in terms
        assert "brown" in terms

    def test_filters_short_words(self):
        terms = _extract_key_terms("I am a Python developer")
        assert "i" not in terms
        assert "python" in terms
        assert "developer" in terms

    def test_empty_text(self):
        assert _extract_key_terms("") == frozenset()


# ── Semantic Diff ──


class TestComputeSemanticDiff:
    """Tests for compute_semantic_diff."""

    def test_identical_units(self):
        units = parse_semantic_units("Python is interpreted. It supports OOP.")
        diff = compute_semantic_diff(units, units)
        assert diff.overall_similarity == 1.0
        assert len(diff.missing_units) == 0
        assert len(diff.extra_units) == 0

    def test_empty_both(self):
        diff = compute_semantic_diff([], [])
        assert diff.overall_similarity == 1.0

    def test_empty_actual(self):
        expected = parse_semantic_units("Python is interpreted.")
        diff = compute_semantic_diff(expected, [])
        assert diff.overall_similarity == 0.0
        assert len(diff.missing_units) == 1

    def test_empty_expected(self):
        actual = parse_semantic_units("Python is interpreted.")
        diff = compute_semantic_diff([], actual)
        assert diff.overall_similarity == 0.0
        assert len(diff.extra_units) == 1

    def test_paraphrased_content_matches(self):
        expected = parse_semantic_units("Python is an interpreted language.")
        actual = parse_semantic_units("Python is an interpreted programming language.")
        diff = compute_semantic_diff(expected, actual, similarity_threshold=0.4)
        assert diff.overall_similarity >= 0.5
        assert len(diff.missing_units) == 0

    def test_completely_different_content(self):
        expected = parse_semantic_units("Python supports dynamic typing.")
        actual = parse_semantic_units("Rust enforces memory safety at compile time.")
        diff = compute_semantic_diff(expected, actual)
        assert diff.overall_similarity < 0.5

    def test_partial_match(self):
        expected = parse_semantic_units(
            "Python is interpreted. It supports OOP. It was released in 1991."
        )
        actual = parse_semantic_units(
            "Python is an interpreted language. It uses garbage collection."
        )
        diff = compute_semantic_diff(expected, actual, similarity_threshold=0.3)
        assert 0.0 < diff.overall_similarity < 1.0
        assert len(diff.missing_units) > 0


# ── SemanticDiffGrader ──


class TestSemanticDiffGrader:
    """Tests for SemanticDiffGrader."""

    def test_identical_content_passes(self, tmp_path: Path):
        text = "Python is interpreted. It supports OOP."
        grader = SemanticDiffGrader(
            name="test_diff",
            expected=text,
            actual=text,
            pass_threshold=0.7,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_similar_content_passes(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            expected="Python is an interpreted language.",
            actual="Python is an interpreted programming language.",
            pass_threshold=0.5,
            similarity_threshold=0.4,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_different_content_fails(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            expected="Python supports dynamic typing and garbage collection.",
            actual="Rust uses static typing and manual memory management.",
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_missing_expected_fails(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            actual="Some content",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Expected text not provided" in result.reason

    def test_missing_actual_fails(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            expected="Some content",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Actual text not provided" in result.reason

    def test_file_based_comparison(self, tmp_path: Path):
        expected_file = tmp_path / "expected.txt"
        expected_file.write_text("Python is interpreted. It supports OOP.")
        actual_file = tmp_path / "actual.txt"
        actual_file.write_text("Python is interpreted. It supports OOP.")

        grader = SemanticDiffGrader(
            name="test_diff",
            expected_path="expected.txt",
            actual_path="actual.txt",
            pass_threshold=0.7,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_unit_type_filter(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            expected="1. Install Python\n2. Run tests\nPython is a great language.",
            actual="1. Install Python\n2. Run tests\nJava is better for enterprises.",
            unit_types=[UnitType.INSTRUCTION],
            pass_threshold=0.5,
            similarity_threshold=0.4,
        )
        result = grader.grade(tmp_path)
        # Only instructions are compared; the instructions match
        assert result.passed is True

    def test_penalize_extra_reduces_score(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            expected="Python is interpreted.",
            actual="Python is interpreted. Java is compiled. Rust is fast. Go is concurrent.",
            pass_threshold=0.5,
            penalize_extra=True,
            extra_penalty_weight=0.3,
        )
        result = grader.grade(tmp_path)
        assert result.details["extra_count"] > 0

    def test_details_contain_matches(self, tmp_path: Path):
        grader = SemanticDiffGrader(
            name="test_diff",
            expected="Python is interpreted.",
            actual="Python is an interpreted language.",
            pass_threshold=0.3,
            similarity_threshold=0.3,
        )
        result = grader.grade(tmp_path)
        assert "matches" in result.details
        assert "missing" in result.details
        assert "extra" in result.details
        assert isinstance(result.details["expected_unit_count"], int)
        assert isinstance(result.details["actual_unit_count"], int)
