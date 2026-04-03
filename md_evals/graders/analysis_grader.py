"""Analysis phase graders — evaluate quality of analysis output.

Graders that check whether an analysis identified the right things:
- Did it find expected keywords/concepts?
- Does it cover required analysis dimensions?
- Is the analysis sufficiently detailed (not trivially short)?

These run SECOND in the three-phase pipeline, after structure
validation passes.  They assume the output is already well-formed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from md_evals.graders._path_utils import validate_workspace_path
from md_evals.models import EvaluatorResult


@dataclass
class KeywordCoverageGrader:
    """Assert that output covers expected keywords or concepts.

    Checks what fraction of expected keywords appear in the text.
    Useful for verifying that an analysis mentions the right topics,
    technologies, risks, etc.

    Scoring is proportional: 3 of 5 keywords found = 0.6 score.
    ``pass_threshold`` controls the minimum fraction to pass.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to file in workspace.
        content: Raw string to check (alternative to path).
        keywords: List of expected keywords/phrases.
        case_sensitive: Whether matching is case-sensitive.
        pass_threshold: Minimum fraction of keywords required to pass (0.0-1.0).
    """

    name: str
    keywords: list[str] = field(default_factory=list)
    path: str | None = None
    content: str | None = None
    case_sensitive: bool = False
    pass_threshold: float = 1.0

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        if not self.keywords:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason="No keywords to check",
            )

        text = raw if self.case_sensitive else raw.lower()
        found: list[str] = []
        missing: list[str] = []

        for kw in self.keywords:
            check = kw if self.case_sensitive else kw.lower()
            if check in text:
                found.append(kw)
            else:
                missing.append(kw)

        coverage = len(found) / len(self.keywords)
        passed = coverage >= self.pass_threshold

        reason = None
        if not passed:
            reason = (
                f"Keyword coverage {coverage:.0%} below threshold "
                f"{self.pass_threshold:.0%}. Missing: {', '.join(missing)}"
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=round(coverage, 4),
            reason=reason,
            details={"found": found, "missing": missing, "coverage": coverage},
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = validate_workspace_path(workspace, self.path)
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"


@dataclass
class SectionCoverageGrader:
    """Assert that output contains expected sections or headings.

    Checks for the presence of expected section markers (e.g. markdown
    headings, XML tags, or custom delimiters) using regex patterns.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to file in workspace.
        content: Raw string to check (alternative to path).
        sections: List of regex patterns that should match section headers.
        pass_threshold: Minimum fraction of sections required to pass.
    """

    name: str
    sections: list[str] = field(default_factory=list)
    path: str | None = None
    content: str | None = None
    pass_threshold: float = 1.0

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        if not self.sections:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason="No sections to check",
            )

        found: list[str] = []
        missing: list[str] = []

        for pattern in self.sections:
            try:
                if re.search(pattern, raw, re.MULTILINE | re.IGNORECASE):
                    found.append(pattern)
                else:
                    missing.append(pattern)
            except re.error:
                missing.append(pattern)

        coverage = len(found) / len(self.sections)
        passed = coverage >= self.pass_threshold

        reason = None
        if not passed:
            reason = (
                f"Section coverage {coverage:.0%} below threshold "
                f"{self.pass_threshold:.0%}. Missing: {', '.join(missing)}"
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=round(coverage, 4),
            reason=reason,
            details={"found": found, "missing": missing, "coverage": coverage},
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = validate_workspace_path(workspace, self.path)
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"


@dataclass
class MinLengthGrader:
    """Assert that output meets a minimum length (word count or char count).

    Prevents trivially short or empty analysis outputs from passing.

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to file in workspace.
        content: Raw string to check (alternative to path).
        min_words: Minimum word count (0 = no word check).
        min_chars: Minimum character count (0 = no char check).
    """

    name: str
    path: str | None = None
    content: str | None = None
    min_words: int = 0
    min_chars: int = 0

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        failures: list[str] = []
        details: dict = {}

        if self.min_words > 0:
            word_count = len(raw.split())
            details["word_count"] = word_count
            if word_count < self.min_words:
                failures.append(
                    f"Word count {word_count} below minimum {self.min_words}"
                )

        if self.min_chars > 0:
            char_count = len(raw)
            details["char_count"] = char_count
            if char_count < self.min_chars:
                failures.append(
                    f"Char count {char_count} below minimum {self.min_chars}"
                )

        passed = len(failures) == 0
        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason="; ".join(failures) if failures else None,
            details=details if details else None,
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = validate_workspace_path(workspace, self.path)
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"
