"""Terminal task grader — evaluate LLM on CLI tasks with automated verification.

Defines terminal challenges in markdown, runs them in sandboxed environments,
and verifies results with test scripts. Extends md-evals beyond text-output
evaluation into execution-based evaluation.

Usage:
    grader = TerminalTaskGrader(
        name="file-creation",
        command="Create a file called hello.txt with 'Hello World' inside",
        verification_script="test -f hello.txt && grep -q 'Hello World' hello.txt",
    )
    result = grader.grade(workspace_path)
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from md_evals.models import EvaluatorResult


@dataclass
class TerminalTask:
    """A terminal task that can be graded by executing commands."""
    name: str
    description: str
    setup_script: str = ""  # commands to run before the task
    expected_command: str = ""  # the command the LLM should produce
    verification_script: str = ""  # script that returns 0 if task passed
    timeout_seconds: int = 30
    cleanup_script: str = ""


@dataclass
class TerminalTaskResult:
    """Result of executing and verifying a terminal task."""
    task_name: str
    passed: bool
    stdout: str
    stderr: str
    exit_code: int
    verification_stdout: str = ""
    verification_exit_code: int = -1
    duration_ms: int = 0
    error: str | None = None


def execute_task(
    task: TerminalTask,
    actual_command: str,
    *,
    work_dir: str | None = None,
) -> TerminalTaskResult:
    """Execute a terminal task and verify the result.

    Args:
        task: The task definition with verification script.
        actual_command: The command produced by the LLM.
        work_dir: Working directory (defaults to a temp dir).

    Returns:
        TerminalTaskResult with pass/fail and captured output.
    """
    import time
    start = time.monotonic()

    if work_dir is None:
        tmpdir = tempfile.mkdtemp(prefix="terminal-eval-")
        work_dir = tmpdir
    else:
        tmpdir = None

    try:
        # Run setup if needed
        if task.setup_script:
            _run_script(task.setup_script, work_dir, task.timeout_seconds)

        # Execute the LLM's command
        cmd_result = _run_script(actual_command, work_dir, task.timeout_seconds)

        # Verify
        if task.verification_script:
            verify_result = _run_script(
                task.verification_script, work_dir, task.timeout_seconds,
            )
            passed = verify_result.returncode == 0
            verification_stdout = verify_result.stdout
            verification_exit_code = verify_result.returncode
        else:
            # No verification = just check exit code
            passed = cmd_result.returncode == 0
            verification_stdout = ""
            verification_exit_code = cmd_result.returncode

        duration_ms = int((time.monotonic() - start) * 1000)

        return TerminalTaskResult(
            task_name=task.name,
            passed=passed,
            stdout=cmd_result.stdout,
            stderr=cmd_result.stderr,
            exit_code=cmd_result.returncode,
            verification_stdout=verification_stdout,
            verification_exit_code=verification_exit_code,
            duration_ms=duration_ms,
        )

    except subprocess.TimeoutExpired:
        return TerminalTaskResult(
            task_name=task.name,
            passed=False,
            stdout="",
            stderr="",
            exit_code=-1,
            error=f"Timeout after {task.timeout_seconds}s",
            duration_ms=int((time.monotonic() - start) * 1000),
        )
    except Exception as e:
        return TerminalTaskResult(
            task_name=task.name,
            passed=False,
            stdout="",
            stderr=str(e),
            exit_code=-1,
            error=str(e),
            duration_ms=int((time.monotonic() - start) * 1000),
        )
    finally:
        # Cleanup
        if task.cleanup_script:
            try:
                _run_script(task.cleanup_script, work_dir, 10)
            except Exception:
                pass


def _run_script(
    script: str, cwd: str, timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run a shell script and capture output."""
    return subprocess.run(
        ["bash", "-c", script],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TerminalTaskGrader:
    """Grader that evaluates LLM output by executing it as a terminal command."""

    def __init__(
        self,
        name: str,
        command_description: str,
        verification_script: str,
        *,
        setup_script: str = "",
        timeout_seconds: int = 30,
        pass_threshold: float = 1.0,
    ):
        self.name = name
        self.task = TerminalTask(
            name=name,
            description=command_description,
            setup_script=setup_script,
            verification_script=verification_script,
            timeout_seconds=timeout_seconds,
        )
        self.pass_threshold = pass_threshold

    def grade(self, workspace: Path, actual_command: str = "") -> EvaluatorResult:
        """Grade a terminal task.

        Args:
            workspace: Working directory for execution.
            actual_command: The command to execute (from LLM output).
        """
        # Read command from workspace file if not provided directly
        if not actual_command:
            cmd_file = workspace / "actual" / "command.txt"
            if cmd_file.exists():
                actual_command = cmd_file.read_text().strip()

        if not actual_command:
            return EvaluatorResult(
                evaluator_name=self.name,
                score=0.0,
                passed=False,
                reason="No command provided for terminal task evaluation",
            )

        result = execute_task(self.task, actual_command, work_dir=str(workspace))

        return EvaluatorResult(
            evaluator_name=self.name,
            score=1.0 if result.passed else 0.0,
            passed=result.passed,
            reason=result.error or (
                f"Task {'passed' if result.passed else 'failed'} "
                f"(exit={result.exit_code}, verify={result.verification_exit_code}, "
                f"{result.duration_ms}ms)"
            ),
            details={
                "stdout": result.stdout[:500],
                "stderr": result.stderr[:500],
                "exit_code": result.exit_code,
                "verification_exit_code": result.verification_exit_code,
                "duration_ms": result.duration_ms,
            },
        )
