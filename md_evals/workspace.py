"""WorkspaceRunner — creates temp workspace, runs tasks, applies graders.

Orchestrates the full lifecycle for deterministic evaluation:
1. Create temporary directory
2. Copy/create setup files
3. Snapshot state (for StateGrader)
4. Execute the task command
5. Apply all graders
6. Cleanup
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_evals.graders.state_grader import StateGrader
from md_evals.models import EvaluatorResult

_DEFAULT_TASK_TIMEOUT = 60


@dataclass
class SetupFile:
    """A file to create in the workspace before task execution.

    Attributes:
        path: Relative path inside the workspace.
        content: Text content to write.
    """

    path: str
    content: str = ""


@dataclass
class WorkspaceConfig:
    """Configuration for a single workspace evaluation run.

    Attributes:
        name: Identifier for this test case.
        setup_files: Files to create before execution.
        task_command: Shell command representing the agent task.
        graders: Deterministic graders to apply after execution.
        task_timeout: Max seconds for the task command.
    """

    name: str
    setup_files: list[SetupFile] = field(default_factory=list)
    task_command: str = ""
    graders: list[Any] = field(default_factory=list)  # list[Grader]
    task_timeout: int = _DEFAULT_TASK_TIMEOUT


@dataclass
class WorkspaceResult:
    """Result of a complete workspace evaluation run.

    Attributes:
        name: Test case identifier.
        passed: True if ALL graders passed.
        grader_results: Individual results from each grader.
        task_exit_code: Exit code of the task command (None if not run).
        task_stdout: Stdout from the task command.
        task_stderr: Stderr from the task command.
        error: Error message if the run itself failed.
    """

    name: str
    passed: bool
    grader_results: list[EvaluatorResult] = field(default_factory=list)
    task_exit_code: int | None = None
    task_stdout: str = ""
    task_stderr: str = ""
    error: str | None = None


class WorkspaceRunner:
    """Creates a temp workspace, executes a task, and applies graders."""

    def run(self, config: WorkspaceConfig) -> WorkspaceResult:
        """Execute a full workspace evaluation lifecycle.

        Args:
            config: Workspace configuration with setup, task, and graders.

        Returns:
            WorkspaceResult with grader outcomes and task output.
        """
        workspace = Path(tempfile.mkdtemp(prefix="md_evals_ws_"))

        try:
            # 1. Setup files
            self._setup_files(workspace, config.setup_files)

            # 2. Snapshot state for StateGraders
            for grader in config.graders:
                if isinstance(grader, StateGrader):
                    grader.snapshot(workspace)

            # 3. Execute task command
            task_exit_code = None
            task_stdout = ""
            task_stderr = ""

            if config.task_command:
                try:
                    proc = subprocess.run(
                        shlex.split(config.task_command),
                        shell=False,
                        cwd=str(workspace),
                        capture_output=True,
                        text=True,
                        timeout=config.task_timeout,
                    )
                    task_exit_code = proc.returncode
                    task_stdout = proc.stdout
                    task_stderr = proc.stderr
                except subprocess.TimeoutExpired:
                    return WorkspaceResult(
                        name=config.name,
                        passed=False,
                        error=f"Task command timed out after {config.task_timeout}s",
                    )
                except OSError as exc:
                    return WorkspaceResult(
                        name=config.name,
                        passed=False,
                        error=f"Task command error: {exc}",
                    )

            # 4. Apply graders
            grader_results: list[EvaluatorResult] = []
            for grader in config.graders:
                result = grader.grade(workspace)
                grader_results.append(result)

            passed = all(r.passed for r in grader_results) if grader_results else True

            return WorkspaceResult(
                name=config.name,
                passed=passed,
                grader_results=grader_results,
                task_exit_code=task_exit_code,
                task_stdout=task_stdout,
                task_stderr=task_stderr,
            )

        finally:
            # 5. Cleanup
            shutil.rmtree(workspace, ignore_errors=True)

    def _setup_files(
        self, workspace: Path, setup_files: list[SetupFile]
    ) -> None:
        """Create setup files in the workspace.

        Args:
            workspace: Root directory.
            setup_files: Files to create.
        """
        resolved_workspace = workspace.resolve()
        for sf in setup_files:
            target = (workspace / sf.path).resolve()
            if not str(target).startswith(str(resolved_workspace)):
                raise ValueError(
                    f"Path traversal detected: '{sf.path}' resolves outside workspace"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(sf.content, encoding="utf-8")
