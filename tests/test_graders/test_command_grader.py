"""Tests for CommandGrader."""

from pathlib import Path

from md_evals.graders.command_grader import CommandGrader


class TestCommandGrader:
    """Tests for CommandGrader."""

    def test_echo_succeeds(self, tmp_path: Path):
        grader = CommandGrader(
            name="echo_test", command="echo hello"
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.details["exit_code"] == 0
        assert "hello" in result.details["stdout"]

    def test_false_command_fails(self, tmp_path: Path):
        grader = CommandGrader(name="false_test", command="false")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0
        assert "Exit code" in result.reason

    def test_expected_output_match(self, tmp_path: Path):
        grader = CommandGrader(
            name="output_test",
            command="echo 'success marker'",
            expected_output="success marker",
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_expected_output_mismatch(self, tmp_path: Path):
        grader = CommandGrader(
            name="output_test",
            command="echo wrong",
            expected_output="expected",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Expected output" in result.reason

    def test_custom_exit_code(self, tmp_path: Path):
        grader = CommandGrader(
            name="exit_test",
            command="bash -c 'exit 42'",
            expected_exit_code=42,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_timeout(self, tmp_path: Path):
        grader = CommandGrader(
            name="timeout_test",
            command="sleep 10",
            timeout=1,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "timed out" in result.reason

    def test_runs_in_workspace_dir(self, tmp_path: Path):
        (tmp_path / "marker.txt").write_text("found_it")
        grader = CommandGrader(
            name="cwd_test",
            command="cat marker.txt",
            expected_output="found_it",
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_stderr_captured(self, tmp_path: Path):
        grader = CommandGrader(
            name="stderr_test",
            command="bash -c 'echo err >&2'",
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert "err" in result.details["stderr"]

    def test_both_exit_and_output_fail(self, tmp_path: Path):
        grader = CommandGrader(
            name="both_fail",
            command="bash -c 'echo wrong && exit 1'",
            expected_exit_code=0,
            expected_output="expected",
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Exit code" in result.reason
        assert "Expected output" in result.reason
