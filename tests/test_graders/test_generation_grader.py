"""Tests for generation phase graders (output matching, constraints)."""

import pytest
from pathlib import Path

from md_evals.graders.generation_grader import (
    OutputMatchGrader,
    ConstraintGrader,
)


class TestOutputMatchGrader:
    """Tests for OutputMatchGrader."""

    def test_all_patterns_match(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="Hello World! Version 2.0 released.",
            patterns=[r"Hello", r"Version \d+\.\d+"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_pattern_not_found(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="Hello World!",
            patterns=[r"Goodbye"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_partial_match_score(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="Hello World",
            patterns=[r"Hello", r"Goodbye"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.5  # 1/2 matched

    def test_negate_mode_passes_when_no_match(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="Clean output",
            patterns=[r"ERROR", r"WARN"],
            negate=True,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_negate_mode_fails_when_match(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="This has an ERROR in it",
            patterns=[r"ERROR", r"WARN"],
            negate=True,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Excluded patterns found" in result.reason

    def test_empty_patterns(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check", content="anything", patterns=[]
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_invalid_regex(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="test",
            patterns=["[invalid"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Invalid pattern" in result.reason

    def test_multiline_match(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check",
            content="line1\nline2\nline3",
            patterns=[r"line1.*line3"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True  # DOTALL flag

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "output.txt").write_text("Generated content: OK")
        grader = OutputMatchGrader(
            name="match_check",
            path="output.txt",
            patterns=[r"Generated content"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_not_found(self, tmp_path: Path):
        grader = OutputMatchGrader(
            name="match_check", path="missing.txt", patterns=[r"test"]
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_no_content_or_path(self, tmp_path: Path):
        grader = OutputMatchGrader(name="match_check", patterns=[r"test"])
        result = grader.grade(tmp_path)
        assert result.passed is False


class TestConstraintGrader:
    """Tests for ConstraintGrader."""

    def test_within_constraints(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="short text",
            max_words=100,
            max_chars=500,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_exceeds_word_limit(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="word " * 20,
            max_words=10,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "exceeds maximum" in result.reason

    def test_exceeds_char_limit(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="a" * 200,
            max_chars=100,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Char count" in result.reason

    def test_forbidden_pattern_found(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="This contains a SECRET_KEY=abc123",
            forbidden_patterns=[r"SECRET_KEY=\w+"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Forbidden pattern matched" in result.reason

    def test_forbidden_pattern_absent(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="Clean output with no secrets",
            forbidden_patterns=[r"SECRET_KEY", r"PASSWORD"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_no_constraints(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check", content="anything goes"
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_invalid_forbidden_regex(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="test",
            forbidden_patterns=["[invalid"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Invalid forbidden pattern" in result.reason

    def test_multiple_violations(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check",
            content="word " * 200,
            max_words=10,
            max_chars=50,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.details is not None
        assert len(result.details["violations"]) == 2

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("short text")
        grader = ConstraintGrader(
            name="constraint_check",
            path="out.txt",
            max_words=100,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_not_found(self, tmp_path: Path):
        grader = ConstraintGrader(
            name="constraint_check", path="missing.txt", max_words=10
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
