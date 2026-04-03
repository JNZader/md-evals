"""Command-based deterministic grader.

Runs a shell command inside the workspace and asserts exit code
and optionally stdout content.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from md_evals.models import EvaluatorResult

_DEFAULT_TIMEOUT = 30


@dataclass
class CommandGrader:
    """Run a command in the workspace and assert on exit code / output.

    Attributes:
        name: Grader identifier for reports.
        command: Shell command string to execute.
        expected_exit_code: Exit code that means "pass". Defaults to 0.
        expected_output: Optional substring that must appear in stdout.
        timeout: Maximum seconds to wait for the command.
    """

    name: str
    command: str
    expected_exit_code: int = 0
    expected_output: str | None = None
    timeout: int = _DEFAULT_TIMEOUT

    def grade(self, workspace: Path) -> EvaluatorResult:
        try:
            result = subprocess.run(
                shlex.split(self.command),
                shell=False,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Command timed out after {self.timeout}s",
            )
        except OSError as exc:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Command execution error: {exc}",
            )

        exit_ok = result.returncode == self.expected_exit_code
        output_ok = True
        if self.expected_output is not None:
            output_ok = self.expected_output in result.stdout

        passed = exit_ok and output_ok
        reasons: list[str] = []

        if not exit_ok:
            reasons.append(
                f"Exit code {result.returncode}, expected {self.expected_exit_code}"
            )
        if not output_ok:
            reasons.append(
                f"Expected output '{self.expected_output}' not found in stdout"
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason="; ".join(reasons) if reasons else None,
            details={
                "exit_code": result.returncode,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
            },
        )
