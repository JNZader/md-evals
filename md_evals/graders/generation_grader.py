"""Generation phase graders — evaluate final output quality.

Graders that check whether generated content matches intent:
- Does the output match an expected pattern/template?
- Is the output semantically consistent (no contradictions)?
- Does the generated content respect constraints (length, format)?

These run LAST in the three-phase pipeline, after both structure
and analysis validation pass.  They evaluate the final deliverable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from md_evals.models import EvaluatorResult


@dataclass
class OutputMatchGrader:
    """Assert that generated output matches expected patterns.

    Checks multiple regex patterns against the output.  All patterns
    must match for the grader to pass (AND logic).  Use multiple
    ``OutputMatchGrader`` instances for OR logic.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to file in workspace.
        content: Raw string to check (alternative to path).
        patterns: List of regex patterns that must ALL match.
        negate: If True, NONE of the patterns should match (exclusion check).
    """

    name: str
    patterns: list[str] = field(default_factory=list)
    path: str | None = None
    content: str | None = None
    negate: bool = False

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        if not self.patterns:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason="No patterns to check",
            )

        matched: list[str] = []
        unmatched: list[str] = []
        errors: list[str] = []

        for pattern in self.patterns:
            try:
                if re.search(pattern, raw, re.MULTILINE | re.DOTALL):
                    matched.append(pattern)
                else:
                    unmatched.append(pattern)
            except re.error as exc:
                errors.append(f"Invalid pattern '{pattern}': {exc}")

        if errors:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="; ".join(errors),
            )

        if self.negate:
            # Pass if NONE matched
            passed = len(matched) == 0
            score = 1.0 - (len(matched) / len(self.patterns))
            reason = None
            if not passed:
                reason = f"Excluded patterns found: {', '.join(matched)}"
        else:
            # Pass if ALL matched
            passed = len(unmatched) == 0
            score = len(matched) / len(self.patterns)
            reason = None
            if not passed:
                reason = f"Patterns not found: {', '.join(unmatched)}"

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=round(score, 4),
            reason=reason,
            details={"matched": matched, "unmatched": unmatched},
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = workspace / self.path
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"


@dataclass
class ConstraintGrader:
    """Assert that generated output respects size/format constraints.

    Combines multiple constraint checks into one grader:
    - Maximum word count
    - Maximum character count
    - Forbidden patterns (regex list)

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to file in workspace.
        content: Raw string to check (alternative to path).
        max_words: Maximum word count (0 = no limit).
        max_chars: Maximum character count (0 = no limit).
        forbidden_patterns: Regex patterns that must NOT appear.
    """

    name: str
    path: str | None = None
    content: str | None = None
    max_words: int = 0
    max_chars: int = 0
    forbidden_patterns: list[str] = field(default_factory=list)

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        violations: list[str] = []

        if self.max_words > 0:
            word_count = len(raw.split())
            if word_count > self.max_words:
                violations.append(
                    f"Word count {word_count} exceeds maximum {self.max_words}"
                )

        if self.max_chars > 0:
            if len(raw) > self.max_chars:
                violations.append(
                    f"Char count {len(raw)} exceeds maximum {self.max_chars}"
                )

        for pattern in self.forbidden_patterns:
            try:
                if re.search(pattern, raw, re.MULTILINE):
                    violations.append(f"Forbidden pattern matched: '{pattern}'")
            except re.error:
                violations.append(f"Invalid forbidden pattern: '{pattern}'")

        passed = len(violations) == 0
        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason="; ".join(violations) if violations else None,
            details={"violations": violations} if violations else None,
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = workspace / self.path
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"
