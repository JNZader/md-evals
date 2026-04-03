"""Tests for WorkspaceRunner."""

from md_evals.workspace import (
    SetupFile,
    WorkspaceConfig,
    WorkspaceRunner,
)
from md_evals.graders.file_graders import FileExistsGrader, FileContentGrader
from md_evals.graders.state_grader import StateGrader


class TestWorkspaceRunner:
    """Tests for WorkspaceRunner lifecycle."""

    def test_basic_lifecycle(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="basic_test",
            setup_files=[
                SetupFile(path="input.txt", content="hello world"),
            ],
            task_command="cp input.txt output.txt",
            graders=[
                FileExistsGrader(name="output_exists", path="output.txt"),
            ],
        )
        result = runner.run(config)
        assert result.passed is True
        assert result.task_exit_code == 0
        assert len(result.grader_results) == 1
        assert result.grader_results[0].passed is True

    def test_setup_creates_nested_dirs(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="nested_setup",
            setup_files=[
                SetupFile(path="a/b/c/deep.txt", content="deep"),
            ],
            graders=[
                FileExistsGrader(name="deep_check", path="a/b/c/deep.txt"),
            ],
        )
        result = runner.run(config)
        assert result.passed is True

    def test_task_command_runs_in_workspace(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="cwd_test",
            setup_files=[
                SetupFile(path="marker.txt", content="found_it"),
            ],
            task_command="bash -c 'cat marker.txt > result.txt'",
            graders=[
                FileContentGrader(
                    name="result_check", path="result.txt", expected="found_it"
                ),
            ],
        )
        result = runner.run(config)
        assert result.passed is True

    def test_grader_failure_propagates(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="fail_test",
            graders=[
                FileExistsGrader(name="missing_file", path="nope.txt"),
            ],
        )
        result = runner.run(config)
        assert result.passed is False
        assert result.grader_results[0].passed is False

    def test_multiple_graders(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="multi_grader",
            setup_files=[
                SetupFile(path="input.txt", content="data"),
            ],
            task_command="bash -c 'echo processed > output.txt'",
            graders=[
                FileExistsGrader(name="input_ok", path="input.txt"),
                FileExistsGrader(name="output_ok", path="output.txt"),
                FileContentGrader(
                    name="output_content", path="output.txt", expected="processed"
                ),
            ],
        )
        result = runner.run(config)
        assert result.passed is True
        assert len(result.grader_results) == 3
        assert all(r.passed for r in result.grader_results)

    def test_partial_grader_failure(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="partial_fail",
            setup_files=[
                SetupFile(path="exists.txt", content="yes"),
            ],
            graders=[
                FileExistsGrader(name="ok", path="exists.txt"),
                FileExistsGrader(name="fail", path="missing.txt"),
            ],
        )
        result = runner.run(config)
        assert result.passed is False
        assert result.grader_results[0].passed is True
        assert result.grader_results[1].passed is False

    def test_no_task_command(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="no_task",
            setup_files=[
                SetupFile(path="file.txt", content="setup only"),
            ],
            graders=[
                FileExistsGrader(name="check", path="file.txt"),
            ],
        )
        result = runner.run(config)
        assert result.passed is True
        assert result.task_exit_code is None

    def test_no_graders(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="no_graders",
            task_command="echo test",
        )
        result = runner.run(config)
        assert result.passed is True
        assert result.task_exit_code == 0
        assert len(result.grader_results) == 0

    def test_task_timeout(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="timeout",
            task_command="sleep 10",
            task_timeout=1,
        )
        result = runner.run(config)
        assert result.passed is False
        assert result.error is not None
        assert "timed out" in result.error

    def test_cleanup_after_success(self):
        """Workspace temp dir should be cleaned up after run."""
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="cleanup_test",
            setup_files=[SetupFile(path="test.txt", content="data")],
            task_command="echo done",
        )
        # Run and verify no temp dirs leaked
        result = runner.run(config)
        assert result.passed is True
        # The temp dir is cleaned inside run(), we can't check it directly
        # but the run should complete without error

    def test_state_grader_integration(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="state_test",
            setup_files=[
                SetupFile(path="to_delete.txt", content="bye"),
            ],
            task_command="bash -c 'rm to_delete.txt && echo created > new.txt'",
            graders=[
                StateGrader(
                    name="state_check",
                    expected_created=["new.txt"],
                    expected_deleted=["to_delete.txt"],
                ),
            ],
        )
        result = runner.run(config)
        assert result.passed is True

    def test_stdout_captured(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="stdout_test",
            task_command="echo captured_output",
        )
        result = runner.run(config)
        assert "captured_output" in result.task_stdout

    def test_stderr_captured(self):
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="stderr_test",
            task_command="bash -c 'echo error_msg >&2'",
        )
        result = runner.run(config)
        assert "error_msg" in result.task_stderr
