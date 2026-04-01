"""Base protocol and result type for deterministic graders.

Graders check side effects of agent task execution (files, commands,
workspace state) rather than evaluating LLM output text.  Every grader
implements the ``Grader`` protocol and returns an ``EvaluatorResult``
so the existing reporter / pipeline infrastructure can consume results
without changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from md_evals.models import EvaluatorResult


@runtime_checkable
class Grader(Protocol):
    """Protocol for deterministic graders.

    Each grader inspects a workspace directory and returns an
    ``EvaluatorResult`` indicating pass/fail with optional details.

    Attributes:
        name: Human-readable identifier used in reports.
    """

    name: str

    def grade(self, workspace: Path) -> EvaluatorResult:
        """Grade the workspace and return a result.

        Args:
            workspace: Root directory of the execution workspace.

        Returns:
            EvaluatorResult with passed, score, reason, and optional details.
        """
        ...
