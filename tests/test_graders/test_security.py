"""Security regression tests for shell injection and path traversal.

These tests verify that:
1. CommandGrader with shell=False prevents shell metacharacter execution.
2. Path traversal via '../' is rejected by all graders and workspace setup.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from md_evals.graders.command_grader import CommandGrader
from md_evals.graders.file_graders import (
    FileExistsGrader,
    FileContentGrader,
    FileSizeGrader,
)
from md_evals.graders.state_grader import StateGrader
from md_evals.graders.structure_grader import (
    JSONValidGrader,
)
from md_evals.graders.analysis_grader import (
    KeywordCoverageGrader,
)
from md_evals.graders.generation_grader import (
    OutputMatchGrader,
)
from md_evals.workspace import SetupFile, WorkspaceConfig, WorkspaceRunner


class TestShellInjectionPrevention:
    """Verify that shell metacharacters do NOT execute via CommandGrader."""

    def test_pipe_does_not_execute(self, tmp_path: Path):
        """Shell pipe should NOT work with shell=False."""
        grader = CommandGrader(
            name="pipe_test",
            command="echo hello | cat",
        )
        result = grader.grade(tmp_path)
        # With shell=False, 'echo' receives 'hello', '|', 'cat' as arguments
        # It should NOT pipe — echo will print 'hello | cat' literally
        # or the command may fail depending on OS behavior
        assert "hello" in result.details.get("stdout", "")
        # The pipe character should appear as literal text, NOT be interpreted
        assert "|" in result.details.get("stdout", "") or not result.passed

    def test_semicolon_injection_blocked(self, tmp_path: Path):
        """Semicolon command chaining should NOT work."""
        marker = tmp_path / "pwned.txt"
        grader = CommandGrader(
            name="semicolon_test",
            command=f"echo safe; touch {marker}",
        )
        grader.grade(tmp_path)
        # With shell=False, the semicolon is passed as an argument to echo
        assert not marker.exists(), "Shell injection via semicolon succeeded!"

    def test_backtick_substitution_blocked(self, tmp_path: Path):
        """Backtick command substitution should NOT execute."""
        grader = CommandGrader(
            name="backtick_test",
            command="echo `whoami`",
        )
        result = grader.grade(tmp_path)
        # With shell=False, backticks are literal arguments
        stdout = result.details.get("stdout", "")
        assert "`whoami`" in stdout or not result.passed

    def test_dollar_substitution_blocked(self, tmp_path: Path):
        """$(cmd) substitution should NOT execute."""
        grader = CommandGrader(
            name="dollar_test",
            command="echo $(whoami)",
        )
        result = grader.grade(tmp_path)
        stdout = result.details.get("stdout", "")
        assert "$(whoami)" in stdout or not result.passed

    def test_redirect_not_interpreted(self, tmp_path: Path):
        """Redirect operators should NOT create files."""
        outfile = tmp_path / "redirected.txt"
        grader = CommandGrader(
            name="redirect_test",
            command=f"echo data > {outfile}",
        )
        grader.grade(tmp_path)
        assert not outfile.exists(), "Shell redirect was interpreted!"

    def test_workspace_runner_shell_injection_blocked(self, tmp_path: Path):
        """WorkspaceRunner task_command should not interpret shell metacharacters."""
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="shell_injection_test",
            task_command="echo safe; echo pwned",
        )
        result = runner.run(config)
        # With shell=False, the semicolon is a literal arg to echo
        # The second 'echo pwned' should NOT execute as a separate command
        if result.task_stdout:
            assert "pwned" not in result.task_stdout.split("\n")[-1] or ";" in result.task_stdout


class TestPathTraversalPrevention:
    """Verify that path traversal via '../' is rejected."""

    def test_setup_file_path_traversal_raises(self, tmp_path: Path):
        """SetupFile with '../../../etc/passwd' must raise ValueError."""
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="traversal_test",
            setup_files=[
                SetupFile(path="../../../etc/passwd", content="malicious"),
            ],
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            runner.run(config)

    def test_setup_file_absolute_path_traversal_raises(self):
        """SetupFile with absolute path must raise ValueError."""
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="abs_traversal_test",
            setup_files=[
                SetupFile(path="/etc/passwd", content="malicious"),
            ],
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            runner.run(config)

    def test_file_exists_grader_traversal_raises(self, tmp_path: Path):
        """FileExistsGrader with traversal path must raise ValueError."""
        grader = FileExistsGrader(
            name="traversal", path="../../../etc/passwd"
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_file_content_grader_traversal_raises(self, tmp_path: Path):
        """FileContentGrader with traversal path must raise ValueError."""
        grader = FileContentGrader(
            name="traversal",
            path="../../../etc/passwd",
            pattern="root",
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_file_size_grader_traversal_raises(self, tmp_path: Path):
        """FileSizeGrader with traversal path must raise ValueError."""
        grader = FileSizeGrader(
            name="traversal", path="../../../etc/passwd"
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_json_valid_grader_traversal_raises(self, tmp_path: Path):
        """JSONValidGrader with traversal path must raise ValueError."""
        grader = JSONValidGrader(
            name="traversal", path="../../../etc/passwd"
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_state_grader_created_traversal_raises(self, tmp_path: Path):
        """StateGrader expected_created with traversal must raise ValueError."""
        grader = StateGrader(
            name="traversal",
            expected_created=["../../../etc/passwd"],
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_state_grader_deleted_traversal_raises(self, tmp_path: Path):
        """StateGrader expected_deleted with traversal must raise ValueError."""
        grader = StateGrader(
            name="traversal",
            expected_deleted=["../../../etc/passwd"],
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_keyword_grader_traversal_raises(self, tmp_path: Path):
        """KeywordCoverageGrader with traversal path must raise ValueError."""
        grader = KeywordCoverageGrader(
            name="traversal",
            path="../../../etc/passwd",
            keywords=["root"],
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_output_match_grader_traversal_raises(self, tmp_path: Path):
        """OutputMatchGrader with traversal path must raise ValueError."""
        grader = OutputMatchGrader(
            name="traversal",
            path="../../../etc/passwd",
            patterns=["root"],
        )
        with pytest.raises(ValueError, match="Path traversal detected"):
            grader.grade(tmp_path)

    def test_safe_nested_path_works(self, tmp_path: Path):
        """Legitimate nested paths must still work fine."""
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("hello")

        grader = FileExistsGrader(name="nested", path="a/b/file.txt")
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_setup_file_safe_nested_path_works(self):
        """Legitimate nested setup files must still work."""
        runner = WorkspaceRunner()
        config = WorkspaceConfig(
            name="safe_nested",
            setup_files=[
                SetupFile(path="a/b/c/deep.txt", content="deep"),
            ],
            graders=[
                FileExistsGrader(name="check", path="a/b/c/deep.txt"),
            ],
        )
        result = runner.run(config)
        assert result.passed is True
