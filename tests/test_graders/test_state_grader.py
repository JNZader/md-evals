"""Tests for StateGrader."""

import time
import pytest
from pathlib import Path

from md_evals.graders.state_grader import StateGrader


class TestStateGrader:
    """Tests for StateGrader."""

    def test_expected_created_passes(self, tmp_path: Path):
        grader = StateGrader(
            name="state_test", expected_created=["new.txt"]
        )
        grader.snapshot(tmp_path)
        (tmp_path / "new.txt").write_text("created")
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_expected_created_missing_fails(self, tmp_path: Path):
        grader = StateGrader(
            name="state_test", expected_created=["new.txt"]
        )
        grader.snapshot(tmp_path)
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_expected_deleted_passes(self, tmp_path: Path):
        (tmp_path / "temp.txt").write_text("to be deleted")
        grader = StateGrader(
            name="state_test", expected_deleted=["temp.txt"]
        )
        grader.snapshot(tmp_path)
        (tmp_path / "temp.txt").unlink()
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_expected_deleted_still_exists_fails(self, tmp_path: Path):
        (tmp_path / "temp.txt").write_text("still here")
        grader = StateGrader(
            name="state_test", expected_deleted=["temp.txt"]
        )
        grader.snapshot(tmp_path)
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "should have been deleted" in result.reason

    def test_expected_modified_passes(self, tmp_path: Path):
        (tmp_path / "data.txt").write_text("original")
        grader = StateGrader(
            name="state_test", expected_modified=["data.txt"]
        )
        grader.snapshot(tmp_path)
        # Ensure mtime changes — sleep briefly for filesystem granularity
        time.sleep(0.05)
        (tmp_path / "data.txt").write_text("modified content")
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_expected_modified_not_changed_fails(self, tmp_path: Path):
        (tmp_path / "data.txt").write_text("original")
        grader = StateGrader(
            name="state_test", expected_modified=["data.txt"]
        )
        grader.snapshot(tmp_path)
        # Don't modify the file
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "was not modified" in result.reason

    def test_expected_modified_file_missing_fails(self, tmp_path: Path):
        grader = StateGrader(
            name="state_test", expected_modified=["gone.txt"]
        )
        grader.snapshot(tmp_path)
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_multiple_assertions(self, tmp_path: Path):
        (tmp_path / "existing.txt").write_text("old")
        grader = StateGrader(
            name="multi",
            expected_created=["new.txt"],
            expected_deleted=["to_remove.txt"],
        )
        (tmp_path / "to_remove.txt").write_text("bye")
        grader.snapshot(tmp_path)

        (tmp_path / "new.txt").write_text("hello")
        (tmp_path / "to_remove.txt").unlink()

        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_empty_expectations_passes(self, tmp_path: Path):
        grader = StateGrader(name="empty")
        grader.snapshot(tmp_path)
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_created_file_counts_as_modified(self, tmp_path: Path):
        """A file that didn't exist before but now does should pass modified check."""
        grader = StateGrader(
            name="new_as_modified", expected_modified=["brand_new.txt"]
        )
        grader.snapshot(tmp_path)
        (tmp_path / "brand_new.txt").write_text("new")
        result = grader.grade(tmp_path)
        assert result.passed is True
