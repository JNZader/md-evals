"""Pre-check engine for deterministic SKILL.md validation.

Phase A — Data Foundation:
  Defines the frozen dataclasses `PreCheckFinding` and `PreCheckResult`
  used as the canonical output of the pre-check pipeline.

Phase C — Pre-check Engine:
  `PreCheckEngine` wraps `LinterEngine` via composition, converts
  `LinterViolation` objects to `PreCheckFinding`, and adds security
  pattern scanning from the rubric configuration.

All checks are deterministic, fast, and free (no LLM calls).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from md_evals.linter import LinterEngine
from md_evals.models import LinterConfig
from md_evals.rubric import RubricConfig, SecurityPattern


# ============== Phase A: Data Foundation ==============


@dataclass(frozen=True)
class PreCheckFinding:
    """A single finding from the pre-check engine.

    Attributes:
        check: Machine-readable identifier (e.g. ``"required_sections"``,
            ``"security_antipattern"``, ``"empty_file"``, ``"max_lines"``,
            ``"very_long_line"``, ``"file_not_found"``, ``"read_error"``).
        message: Human-readable description of the finding.
        severity: Impact level — ``"error"``, ``"warning"``, or ``"info"``.
        line: 1-indexed line number if applicable, ``None`` for file-level findings.
    """

    check: str
    message: str
    severity: str
    line: int | None = None


@dataclass(frozen=True)
class PreCheckResult:
    """Aggregated result from the pre-check engine.

    Invariants:
        - ``passed`` is ``True`` iff no finding has ``severity == "error"``.
        - ``checks_run >= len(findings)`` (some checks produce 0 findings).
        - ``duration_ms >= 0``.

    Attributes:
        passed: Whether the file passed all error-level checks.
        findings: All findings (errors + warnings + info).
        checks_run: Total number of checks executed.
        duration_ms: Wall-clock execution time in milliseconds.
    """

    passed: bool
    findings: list[PreCheckFinding] = field(default_factory=list)
    checks_run: int = 0
    duration_ms: int = 0


# ============== Phase C: Pre-check Engine ==============


class SecurityPatternCheck:
    """Compiled security regex check.

    Pre-compiles a :class:`SecurityPattern` regex once and provides a
    ``scan()`` method that checks file content line-by-line, returning
    :class:`PreCheckFinding` objects for each match.
    """

    def __init__(self, pattern: SecurityPattern):
        self.regex = re.compile(pattern.pattern)
        self.message = pattern.message
        self.severity = pattern.severity

    def scan(self, content: str) -> list[PreCheckFinding]:
        """Scan content line-by-line, return findings with line numbers."""
        findings = []
        for i, line in enumerate(content.splitlines(), 1):
            if self.regex.search(line):
                findings.append(PreCheckFinding(
                    check="security_antipattern",
                    message=f"{self.message} (line {i})",
                    severity=self.severity,
                    line=i,
                ))
        return findings


class PreCheckEngine:
    """Deterministic pre-check engine: fast, free, no LLM.

    Wraps :class:`LinterEngine` via composition and adds security pattern
    checks from the rubric configuration. All checks are deterministic.

    Args:
        rubric: The rubric configuration containing pre-check settings
            (max lines, required sections, security patterns).
    """

    def __init__(self, rubric: RubricConfig):
        self.rubric = rubric
        # Create LinterEngine with rubric config
        self.linter = LinterEngine(LinterConfig(
            max_lines=rubric.pre_check.max_lines,
            fail_on_violation=True,
        ))
        # Compile security patterns once
        self.security_checks = [
            SecurityPatternCheck(p) for p in rubric.pre_check.security_patterns
        ]

    def run(self, skill_path: str) -> PreCheckResult:
        """Run all deterministic checks on a SKILL.md file.

        Steps:
            1. Delegate to ``LinterEngine.run()`` for structural checks.
            2. Convert ``LinterViolation`` → ``PreCheckFinding``.
            3. Run security pattern checks on file content.
            4. Aggregate into ``PreCheckResult``.

        Never raises exceptions — always returns a :class:`PreCheckResult`.
        On file-not-found or read error, returns a failed ``PreCheckResult``.

        Args:
            skill_path: Path to the SKILL.md file to check.

        Returns:
            A :class:`PreCheckResult` with all findings, timing, and pass/fail.
        """
        start = time.monotonic()

        findings: list[PreCheckFinding] = []
        checks_run = 0

        # Step 1: Run linter (handles file-not-found, read-error, etc.)
        linter_report = self.linter.run(skill_path)
        checks_run += len(self.linter.rules)

        # Step 2: Convert LinterViolation -> PreCheckFinding
        for v in linter_report.violations:
            findings.append(PreCheckFinding(
                check=v.rule,  # "max-lines", "empty-file", etc.
                message=v.message,
                severity=v.severity,
                line=v.line,
            ))

        # Step 3: Security checks (only if file was readable)
        has_fatal = any(
            f.check in ("file-not-found", "read-error") for f in findings
        )
        if not has_fatal:
            try:
                content = Path(skill_path).read_text(encoding="utf-8")
                for check in self.security_checks:
                    check_findings = check.scan(content)
                    findings.extend(check_findings)
                    checks_run += 1
            except Exception:
                pass  # Already handled by linter

        elapsed_ms = int((time.monotonic() - start) * 1000)

        # passed = no error-severity findings
        has_errors = any(f.severity == "error" for f in findings)

        return PreCheckResult(
            passed=not has_errors,
            findings=findings,
            checks_run=checks_run,
            duration_ms=elapsed_ms,
        )
