"""File-based deterministic graders.

Check file existence, content (regex / exact), and size constraints
within an execution workspace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from md_evals.models import EvaluatorResult


@dataclass
class FileExistsGrader:
    """Assert that a file exists (or does not exist) in the workspace.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path inside the workspace.
        should_exist: If True, pass when file exists; if False, pass when absent.
    """

    name: str
    path: str
    should_exist: bool = True

    def grade(self, workspace: Path) -> EvaluatorResult:
        target = workspace / self.path
        exists = target.exists()
        passed = exists if self.should_exist else not exists

        if passed:
            reason = None
        elif self.should_exist:
            reason = f"Expected file '{self.path}' not found"
        else:
            reason = f"File '{self.path}' should not exist but does"

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=reason,
        )


@dataclass
class FileContentGrader:
    """Assert file content matches a regex pattern or exact string.

    Provide *either* ``pattern`` (regex) or ``expected`` (exact), not both.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path inside the workspace.
        pattern: Regex pattern to search in file content.
        expected: Exact string the file must contain.
    """

    name: str
    path: str
    pattern: str | None = None
    expected: str | None = None

    def grade(self, workspace: Path) -> EvaluatorResult:
        target = workspace / self.path

        if not target.exists():
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"File '{self.path}' not found",
            )

        content = target.read_text(encoding="utf-8", errors="replace")

        if self.pattern is not None:
            try:
                match = re.search(self.pattern, content, re.MULTILINE)
            except re.error as exc:
                return EvaluatorResult(
                    evaluator_name=self.name,
                    passed=False,
                    score=0.0,
                    reason=f"Invalid regex pattern: {exc}",
                )
            passed = match is not None
            reason = None if passed else f"Pattern '{self.pattern}' not found in '{self.path}'"
        elif self.expected is not None:
            passed = self.expected in content
            reason = None if passed else f"Expected content not found in '{self.path}'"
        else:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="FileContentGrader requires 'pattern' or 'expected'",
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=reason,
        )


@dataclass
class FileSizeGrader:
    """Assert file size is within a byte range.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path inside the workspace.
        min_bytes: Minimum file size (inclusive). 0 means no lower bound.
        max_bytes: Maximum file size (inclusive). None means no upper bound.
    """

    name: str
    path: str
    min_bytes: int = 0
    max_bytes: int | None = None

    def grade(self, workspace: Path) -> EvaluatorResult:
        target = workspace / self.path

        if not target.exists():
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"File '{self.path}' not found",
            )

        size = target.stat().st_size
        too_small = size < self.min_bytes
        too_large = self.max_bytes is not None and size > self.max_bytes

        if too_small:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"File '{self.path}' is {size}B, minimum is {self.min_bytes}B",
            )
        if too_large:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"File '{self.path}' is {size}B, maximum is {self.max_bytes}B",
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=True,
            score=1.0,
            reason=None,
            details={"size_bytes": size},
        )
