"""Tests for file-based deterministic graders."""

import pytest
from pathlib import Path

from md_evals.graders.file_graders import (
    FileExistsGrader,
    FileContentGrader,
    FileSizeGrader,
)


class TestFileExistsGrader:
    """Tests for FileExistsGrader."""

    def test_file_exists_passes(self, tmp_path: Path):
        (tmp_path / "output.txt").write_text("hello")
        grader = FileExistsGrader(name="check_output", path="output.txt")
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.reason is None

    def test_file_missing_fails(self, tmp_path: Path):
        grader = FileExistsGrader(name="check_missing", path="missing.txt")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0
        assert "not found" in result.reason

    def test_should_not_exist_passes_when_absent(self, tmp_path: Path):
        grader = FileExistsGrader(
            name="no_debug", path="debug.log", should_exist=False
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_should_not_exist_fails_when_present(self, tmp_path: Path):
        (tmp_path / "debug.log").write_text("log data")
        grader = FileExistsGrader(
            name="no_debug", path="debug.log", should_exist=False
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "should not exist" in result.reason

    def test_nested_path(self, tmp_path: Path):
        nested = tmp_path / "sub" / "dir"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("nested")
        grader = FileExistsGrader(name="nested", path="sub/dir/file.txt")
        result = grader.grade(tmp_path)
        assert result.passed is True


class TestFileContentGrader:
    """Tests for FileContentGrader."""

    def test_regex_match_passes(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("Result: 42 items found")
        grader = FileContentGrader(
            name="has_number", path="out.txt", pattern=r"\d+"
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_regex_no_match_fails(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("no numbers here")
        grader = FileContentGrader(
            name="has_number", path="out.txt", pattern=r"\d+"
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_exact_match_passes(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("expected output")
        grader = FileContentGrader(
            name="exact", path="out.txt", expected="expected output"
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_exact_match_fails(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("wrong output")
        grader = FileContentGrader(
            name="exact", path="out.txt", expected="expected output"
        )
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_file_not_found(self, tmp_path: Path):
        grader = FileContentGrader(
            name="missing", path="nope.txt", pattern="anything"
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_invalid_regex(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("content")
        grader = FileContentGrader(
            name="bad_regex", path="out.txt", pattern="[invalid"
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Invalid regex" in result.reason

    def test_no_pattern_or_expected(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("content")
        grader = FileContentGrader(name="empty", path="out.txt")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "requires" in result.reason

    def test_multiline_regex(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("line1\nline2\nline3")
        grader = FileContentGrader(
            name="multiline", path="out.txt", pattern=r"^line2$"
        )
        result = grader.grade(tmp_path)
        assert result.passed is True


class TestFileSizeGrader:
    """Tests for FileSizeGrader."""

    def test_within_range(self, tmp_path: Path):
        (tmp_path / "data.bin").write_bytes(b"x" * 100)
        grader = FileSizeGrader(
            name="size_check", path="data.bin", min_bytes=50, max_bytes=200
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.details["size_bytes"] == 100

    def test_too_small(self, tmp_path: Path):
        (tmp_path / "tiny.txt").write_text("hi")
        grader = FileSizeGrader(
            name="size_check", path="tiny.txt", min_bytes=100
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "minimum" in result.reason

    def test_too_large(self, tmp_path: Path):
        (tmp_path / "big.txt").write_bytes(b"x" * 1000)
        grader = FileSizeGrader(
            name="size_check", path="big.txt", max_bytes=500
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "maximum" in result.reason

    def test_file_not_found(self, tmp_path: Path):
        grader = FileSizeGrader(name="size_check", path="nope.bin")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_no_upper_bound(self, tmp_path: Path):
        (tmp_path / "large.txt").write_bytes(b"x" * 10000)
        grader = FileSizeGrader(
            name="size_check", path="large.txt", min_bytes=1
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_exact_boundary(self, tmp_path: Path):
        (tmp_path / "exact.txt").write_bytes(b"x" * 100)
        grader = FileSizeGrader(
            name="boundary", path="exact.txt", min_bytes=100, max_bytes=100
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
