"""State-based deterministic grader.

Compares workspace state (which files exist) against expectations
for created, modified, or deleted files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from md_evals.graders._path_utils import validate_workspace_path
from md_evals.models import EvaluatorResult


@dataclass
class StateGrader:
    """Assert workspace file-system state after task execution.

    The caller captures a *before* snapshot (set of relative paths) and
    passes it via :meth:`grade`.  The grader compares the current state
    against expectations.

    Attributes:
        name: Grader identifier for reports.
        expected_created: Files that MUST exist after execution.
        expected_deleted: Files that MUST NOT exist after execution.
        expected_modified: Files whose mtime should differ from snapshot.
    """

    name: str
    expected_created: list[str] = field(default_factory=list)
    expected_deleted: list[str] = field(default_factory=list)
    expected_modified: list[str] = field(default_factory=list)

    # ── internal state set by snapshot() ──
    _before_mtimes: dict[str, float] = field(
        default_factory=dict, repr=False, compare=False,
    )

    def snapshot(self, workspace: Path) -> None:
        """Capture file modification times BEFORE task execution.

        Call this once after setup but before the task runs so that
        ``expected_modified`` checks have a baseline.

        Args:
            workspace: Root directory of the execution workspace.
        """
        self._before_mtimes = {}
        for item in workspace.rglob("*"):
            if item.is_file():
                rel = str(item.relative_to(workspace))
                self._before_mtimes[rel] = item.stat().st_mtime

    def grade(self, workspace: Path) -> EvaluatorResult:
        failures: list[str] = []

        # Check created files
        for rel_path in self.expected_created:
            target = validate_workspace_path(workspace, rel_path)
            if not target.exists():
                failures.append(f"Expected created file '{rel_path}' not found")

        # Check deleted files
        for rel_path in self.expected_deleted:
            target = validate_workspace_path(workspace, rel_path)
            if target.exists():
                failures.append(f"File '{rel_path}' should have been deleted")

        # Check modified files
        for rel_path in self.expected_modified:
            target = validate_workspace_path(workspace, rel_path)
            if not target.exists():
                failures.append(f"Expected modified file '{rel_path}' not found")
                continue
            current_mtime = target.stat().st_mtime
            before_mtime = self._before_mtimes.get(rel_path)
            if before_mtime is not None and current_mtime == before_mtime:
                failures.append(f"File '{rel_path}' was not modified")
            elif before_mtime is None:
                # File didn't exist before — it was created, not modified.
                # Still counts as "modified" for practical purposes.
                pass

        passed = len(failures) == 0
        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason="; ".join(failures) if failures else None,
            details={"failures": failures} if failures else None,
        )
