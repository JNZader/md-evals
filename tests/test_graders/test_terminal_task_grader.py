"""Tests for terminal_task_grader — CLI task execution and verification."""

import tempfile
from pathlib import Path

from md_evals.graders.terminal_task_grader import (
    TerminalTask,
    TerminalTaskGrader,
    execute_task,
)


class TestExecuteTask:
    def test_passing_task(self):
        task = TerminalTask(
            name="echo-test",
            description="Echo hello",
            verification_script="test -f hello.txt",
        )
        result = execute_task(task, "echo 'hello' > hello.txt")
        assert result.passed is True
        assert result.exit_code == 0

    def test_failing_verification(self):
        task = TerminalTask(
            name="missing-file",
            description="Check nonexistent file",
            verification_script="test -f nonexistent.txt",
        )
        result = execute_task(task, "echo 'nothing'")
        assert result.passed is False

    def test_command_error(self):
        task = TerminalTask(
            name="bad-command",
            description="Run invalid command",
            verification_script="true",
        )
        result = execute_task(task, "false")
        # The command fails but verification might still pass
        assert result.exit_code != 0 or result.passed is True

    def test_setup_script_runs_first(self):
        task = TerminalTask(
            name="with-setup",
            description="Test with setup",
            setup_script="mkdir -p testdir",
            verification_script="test -d testdir",
        )
        result = execute_task(task, "ls testdir")
        assert result.passed is True

    def test_timeout(self):
        task = TerminalTask(
            name="slow-task",
            description="Slow task",
            timeout_seconds=1,
        )
        result = execute_task(task, "sleep 10")
        assert result.passed is False
        assert result.error is not None
        assert "Timeout" in result.error

    def test_captures_stdout(self):
        task = TerminalTask(name="output", description="Capture output")
        result = execute_task(task, "echo 'captured output'")
        assert "captured output" in result.stdout

    def test_captures_stderr(self):
        task = TerminalTask(name="stderr", description="Capture stderr")
        result = execute_task(task, "echo 'error message' >&2")
        assert "error message" in result.stderr

    def test_duration_tracked(self):
        task = TerminalTask(name="timed", description="Track duration")
        result = execute_task(task, "echo fast")
        assert result.duration_ms >= 0

    def test_custom_work_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            task = TerminalTask(
                name="workdir",
                description="Custom workdir",
                verification_script="test -f marker.txt",
            )
            result = execute_task(task, "touch marker.txt", work_dir=tmpdir)
            assert result.passed is True
            assert (Path(tmpdir) / "marker.txt").exists()

    def test_no_verification_uses_exit_code(self):
        task = TerminalTask(name="exit-only", description="No verification")
        result = execute_task(task, "true")
        assert result.passed is True

        result2 = execute_task(task, "false")
        assert result2.passed is False


class TestTerminalTaskGrader:
    def test_grade_passing(self):
        grader = TerminalTaskGrader(
            name="file-create",
            command_description="Create hello.txt",
            verification_script="test -f hello.txt && grep -q 'Hello' hello.txt",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = grader.grade(Path(tmpdir), actual_command="echo 'Hello World' > hello.txt")
            assert result.passed is True
            assert result.score == 1.0

    def test_grade_failing(self):
        grader = TerminalTaskGrader(
            name="file-check",
            command_description="Check file exists",
            verification_script="test -f nonexistent.txt",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = grader.grade(Path(tmpdir), actual_command="echo 'wrong'")
            assert result.passed is False
            assert result.score == 0.0

    def test_grade_no_command(self):
        grader = TerminalTaskGrader(
            name="no-cmd",
            command_description="Missing command",
            verification_script="true",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = grader.grade(Path(tmpdir))
            assert result.passed is False
            assert "No command" in result.reason

    def test_grade_reads_command_from_file(self):
        grader = TerminalTaskGrader(
            name="file-cmd",
            command_description="Read from file",
            verification_script="test -f created.txt",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            actual_dir = Path(tmpdir) / "actual"
            actual_dir.mkdir()
            (actual_dir / "command.txt").write_text("touch created.txt\n")
            result = grader.grade(Path(tmpdir))
            assert result.passed is True
