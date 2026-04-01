"""Contract-based assertion graders for skill evaluation.

Define output contracts (required sections, format rules, constraints)
and assert that outputs satisfy them.  The :class:`ABContractGrader`
extends this to A/B testing: both variants must satisfy the *same*
contract while producing different content.

These graders follow the established dataclass + ``Grader`` protocol
pattern used throughout ``md_evals.graders``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from md_evals.models import EvaluatorResult


@dataclass
class OutputContract:
    """Definition of structural rules an output must satisfy.

    Attributes:
        required_sections: Regex patterns that must each match at least
            once (e.g. ``"^## Purpose"`` for a markdown heading).
        format_rules: Regex patterns the content MUST match.
        forbidden_patterns: Regex patterns the content MUST NOT match.
        min_words: Minimum word count (0 = no check).
        max_words: Maximum word count (0 = no check).
    """

    required_sections: list[str] = field(default_factory=list)
    format_rules: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)
    min_words: int = 0
    max_words: int = 0


@dataclass
class ContractAssertionGrader:
    """Assert that content satisfies an :class:`OutputContract`.

    Checks every rule in the contract and reports a proportional score
    (fraction of rules satisfied).  Supports file-mode (``path``) and
    content-mode (``content``).

    Attributes:
        name: Grader identifier for reports.
        contract: The output contract to validate against.
        path: Relative path to file in workspace.
        content: Raw string to check (alternative to path).
    """

    name: str
    contract: OutputContract
    path: str | None = None
    content: str | None = None

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
        total_rules = 0

        # --- Required sections ---
        for pattern in self.contract.required_sections:
            total_rules += 1
            try:
                if not re.search(pattern, raw, re.MULTILINE | re.IGNORECASE):
                    violations.append(f"Missing required section: '{pattern}'")
            except re.error as exc:
                violations.append(f"Invalid section pattern '{pattern}': {exc}")

        # --- Format rules (must match) ---
        for pattern in self.contract.format_rules:
            total_rules += 1
            try:
                if not re.search(pattern, raw, re.MULTILINE | re.DOTALL):
                    violations.append(f"Format rule not satisfied: '{pattern}'")
            except re.error as exc:
                violations.append(f"Invalid format pattern '{pattern}': {exc}")

        # --- Forbidden patterns (must NOT match) ---
        for pattern in self.contract.forbidden_patterns:
            total_rules += 1
            try:
                if re.search(pattern, raw, re.MULTILINE):
                    violations.append(f"Forbidden pattern found: '{pattern}'")
            except re.error as exc:
                violations.append(f"Invalid forbidden pattern '{pattern}': {exc}")

        # --- Word count constraints ---
        word_count = len(raw.split())

        if self.contract.min_words > 0:
            total_rules += 1
            if word_count < self.contract.min_words:
                violations.append(
                    f"Word count {word_count} below minimum {self.contract.min_words}"
                )

        if self.contract.max_words > 0:
            total_rules += 1
            if word_count > self.contract.max_words:
                violations.append(
                    f"Word count {word_count} exceeds maximum {self.contract.max_words}"
                )

        if total_rules == 0:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason="Empty contract — nothing to check",
            )

        passed_rules = total_rules - len(violations)
        score = passed_rules / total_rules
        passed = len(violations) == 0

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=round(score, 4),
            reason="; ".join(violations) if violations else None,
            details={
                "violations": violations,
                "total_rules": total_rules,
                "passed_rules": passed_rules,
                "word_count": word_count,
            },
        )

    # ── helpers ──

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
class ABContractGrader:
    """Assert that two A/B variants both satisfy the same contract.

    Both ``variant_a`` and ``variant_b`` are validated against the shared
    :class:`OutputContract`.  The grader also verifies that the variants
    are not identical — A/B testing requires different approaches.

    Attributes:
        name: Grader identifier for reports.
        contract: The output contract both variants must satisfy.
        variant_a: Content of the first (control) variant.
        variant_b: Content of the second (treatment) variant.
    """

    name: str
    contract: OutputContract
    variant_a: str
    variant_b: str

    def grade(self, workspace: Path) -> EvaluatorResult:
        # Check for identical variants first
        if self.variant_a == self.variant_b:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="Variants are identical — A/B testing requires different content",
            )

        # Validate each variant
        grader_a = ContractAssertionGrader(
            name=f"{self.name}__variant_a",
            contract=self.contract,
            content=self.variant_a,
        )
        grader_b = ContractAssertionGrader(
            name=f"{self.name}__variant_b",
            contract=self.contract,
            content=self.variant_b,
        )

        result_a = grader_a.grade(workspace)
        result_b = grader_b.grade(workspace)

        failures: list[str] = []
        if not result_a.passed:
            failures.append(f"variant_a failed: {result_a.reason}")
        if not result_b.passed:
            failures.append(f"variant_b failed: {result_b.reason}")

        passed = len(failures) == 0
        # Average of both scores
        score = round((result_a.score + result_b.score) / 2, 4)

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reason="; ".join(failures) if failures else None,
            details={
                "variant_a": {
                    "passed": result_a.passed,
                    "score": result_a.score,
                    "reason": result_a.reason,
                },
                "variant_b": {
                    "passed": result_b.passed,
                    "score": result_b.score,
                    "reason": result_b.reason,
                },
            },
        )
