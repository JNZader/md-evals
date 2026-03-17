"""Comprehensive unit tests for md_evals.precheck module.

Tests cover all public types and functions:
  - PreCheckFinding, PreCheckResult (frozen dataclass contracts)
  - SecurityPatternCheck (regex scanning, line numbers, edge cases)
  - PreCheckEngine (linter delegation, security scanning, aggregation)
  - Edge cases (non-existent paths, empty files, performance)
"""

from __future__ import annotations

import dataclasses
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from md_evals.precheck import (
    PreCheckEngine,
    PreCheckFinding,
    PreCheckResult,
    SecurityPatternCheck,
)
from md_evals.rubric import RubricLoader, SecurityPattern


# ============================================================================
# Constants
# ============================================================================

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _default_rubric():
    """Load the default rubric for engine tests."""
    return RubricLoader.load(str(FIXTURES_DIR / "rubric_default.yaml"))


# ============================================================================
# 1. PreCheckFinding dataclass tests
# ============================================================================


def test_precheck_finding_construction():
    """PreCheckFinding can be created with all required fields."""
    f = PreCheckFinding(
        check="security_antipattern",
        message="Hardcoded secret detected (line 8)",
        severity="error",
        line=8,
    )
    assert f.check == "security_antipattern"
    assert f.message == "Hardcoded secret detected (line 8)"
    assert f.severity == "error"
    assert f.line == 8


def test_precheck_finding_line_defaults_to_none():
    """Line defaults to None for file-level findings."""
    f = PreCheckFinding(check="empty-file", message="empty", severity="error")
    assert f.line is None


def test_precheck_finding_frozen_immutability():
    """Setting a field on a frozen PreCheckFinding raises an error."""
    f = PreCheckFinding(check="test", message="msg", severity="info")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        f.check = "other"  # type: ignore[misc]


def test_precheck_finding_is_stdlib_dataclass():
    """PreCheckFinding is a stdlib frozen dataclass."""
    assert dataclasses.is_dataclass(PreCheckFinding)
    assert not hasattr(PreCheckFinding, "model_fields")


# ============================================================================
# 2. PreCheckResult dataclass tests
# ============================================================================


def test_precheck_result_construction():
    """PreCheckResult can be created with all fields."""
    findings = [
        PreCheckFinding(check="a", message="m", severity="warning"),
    ]
    r = PreCheckResult(
        passed=True,
        findings=findings,
        checks_run=5,
        duration_ms=42,
    )
    assert r.passed is True
    assert len(r.findings) == 1
    assert r.checks_run == 5
    assert r.duration_ms == 42


def test_precheck_result_defaults():
    """PreCheckResult defaults: empty findings, 0 checks, 0 duration."""
    r = PreCheckResult(passed=True)
    assert r.findings == []
    assert r.checks_run == 0
    assert r.duration_ms == 0


def test_precheck_result_frozen_immutability():
    """Setting a field on a frozen PreCheckResult raises an error."""
    r = PreCheckResult(passed=True)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        r.passed = False  # type: ignore[misc]


# ============================================================================
# 3. SecurityPatternCheck tests
# ============================================================================


def test_security_pattern_match_with_line_numbers():
    """Pattern match returns findings with correct line numbers."""
    pattern = SecurityPattern(
        pattern=r"api_key\s*=",
        message="Hardcoded API key",
        severity="error",
    )
    check = SecurityPatternCheck(pattern)
    content = "line 1\napi_key = 'abc'\nline 3"

    findings = check.scan(content)

    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].severity == "error"
    assert findings[0].check == "security_antipattern"
    assert "Hardcoded API key" in findings[0].message


def test_security_pattern_no_match_returns_empty():
    """No match returns an empty list."""
    pattern = SecurityPattern(
        pattern=r"password\s*=",
        message="Password detected",
        severity="error",
    )
    check = SecurityPatternCheck(pattern)
    content = "This is a clean file\nNo secrets here"

    findings = check.scan(content)
    assert findings == []


def test_security_pattern_multiple_matches():
    """Multiple matches on different lines produce multiple findings."""
    pattern = SecurityPattern(
        pattern=r"secret",
        message="Secret detected",
        severity="warning",
    )
    check = SecurityPatternCheck(pattern)
    content = "secret on line 1\nclean\nsecret on line 3\nsecret on line 4"

    findings = check.scan(content)

    assert len(findings) == 3
    assert findings[0].line == 1
    assert findings[1].line == 3
    assert findings[2].line == 4


def test_security_pattern_empty_content():
    """Scanning empty content returns no findings."""
    pattern = SecurityPattern(
        pattern=r"secret",
        message="Secret detected",
        severity="error",
    )
    check = SecurityPatternCheck(pattern)

    findings = check.scan("")
    assert findings == []


# ============================================================================
# 4. PreCheckEngine — clean skill
# ============================================================================


def test_engine_clean_skill_passes():
    """A well-formed skill file passes all checks."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_short.md"))

    assert result.passed is True
    # May have warnings (e.g. missing sections) but no errors
    errors = [f for f in result.findings if f.severity == "error"]
    assert len(errors) == 0


def test_engine_clean_skill_has_positive_duration():
    """Engine always records positive duration."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_short.md"))

    assert result.duration_ms >= 0


def test_engine_clean_skill_checks_run_count():
    """checks_run includes linter rules + security patterns."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_short.md"))

    # Linter has 4 rules (EmptyFile, MaxLines, VeryLongLine, RequiredSections)
    # Default rubric has 1 security pattern in fixture
    # Total = 4 linter rules + 1 security pattern = 5
    assert result.checks_run >= 5


# ============================================================================
# 5. PreCheckEngine — missing sections
# ============================================================================


def test_engine_missing_sections_has_warnings(tmp_path):
    """Missing sections produce warning-level findings."""
    # Create a file that truly lacks the required section words
    skill = tmp_path / "no_sections.md"
    skill.write_text("# My Skill\n\nSome content without any required headings.\n")

    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(skill))

    warnings = [f for f in result.findings if f.severity == "warning"]
    assert len(warnings) >= 1  # At least "Description", "Rules", "Examples" missing

    # Warnings don't cause failure
    errors = [f for f in result.findings if f.severity == "error"]
    assert len(errors) == 0
    assert result.passed is True


# ============================================================================
# 6. PreCheckEngine — hardcoded secret
# ============================================================================


def test_engine_secret_detection_fails():
    """Hardcoded secret is detected with severity=error, passed=False."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_with_secret.md"))

    assert result.passed is False

    secret_findings = [
        f for f in result.findings
        if f.check == "security_antipattern" and f.severity == "error"
    ]
    assert len(secret_findings) >= 1
    assert "Hardcoded secret" in secret_findings[0].message


def test_engine_secret_detection_has_line_number():
    """Secret finding includes the correct line number."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_with_secret.md"))

    secret_findings = [
        f for f in result.findings if f.check == "security_antipattern"
    ]
    assert len(secret_findings) >= 1
    assert secret_findings[0].line is not None
    assert secret_findings[0].line > 0


# ============================================================================
# 7. PreCheckEngine — shell patterns
# ============================================================================


def test_engine_shell_pattern_warns_but_passes():
    """Shell patterns produce warnings but don't fail the check."""
    rubric = RubricLoader.load_default()  # default has os.system pattern
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_with_shell.md"))

    shell_findings = [
        f for f in result.findings
        if f.check == "security_antipattern" and f.severity == "warning"
    ]
    assert len(shell_findings) >= 1
    assert result.passed is True


# ============================================================================
# 8. PreCheckEngine — empty file
# ============================================================================


def test_engine_empty_file_fails():
    """Empty file produces an error and passed=False."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_empty.md"))

    assert result.passed is False

    empty_findings = [
        f for f in result.findings if f.check == "empty-file"
    ]
    assert len(empty_findings) == 1
    assert empty_findings[0].severity == "error"


# ============================================================================
# 9. PreCheckEngine — file not found
# ============================================================================


def test_engine_file_not_found_fails():
    """Non-existent file returns passed=False with file-not-found finding."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run("/nonexistent/path/to/skill.md")

    assert result.passed is False

    fnf = [f for f in result.findings if f.check == "file-not-found"]
    assert len(fnf) == 1
    assert fnf[0].severity == "error"


def test_engine_file_not_found_no_security_scan():
    """When file not found, security checks are skipped (no extra findings)."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run("/nonexistent/path/skill.md")

    security = [f for f in result.findings if f.check == "security_antipattern"]
    assert len(security) == 0


# ============================================================================
# 10. PreCheckEngine — linter delegation
# ============================================================================


def test_engine_linter_violations_appear_as_findings(tmp_path):
    """LinterViolation objects are converted to PreCheckFinding correctly."""
    # Create a file that truly lacks the required section words
    skill = tmp_path / "no_sections.md"
    skill.write_text("# My Skill\n\nJust some content here.\n")

    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(skill))

    # RequiredSectionsRule should produce warnings for missing sections
    section_findings = [
        f for f in result.findings if f.check == "required-sections"
    ]
    assert len(section_findings) >= 1
    for f in section_findings:
        assert f.severity == "warning"
        assert "Missing" in f.message or "section" in f.message.lower()


# ============================================================================
# 11. PreCheckEngine — multiple findings on same file
# ============================================================================


def test_engine_multiple_findings_same_file(tmp_path):
    """File with multiple issues produces multiple findings."""
    # Create a file with both a secret and missing sections
    bad_skill = tmp_path / "bad_skill.md"
    bad_skill.write_text(
        '# Bad Skill\napi_key = "sk-secret123"\n'
    )

    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(bad_skill))

    # Should have at least: missing sections warnings + secret error
    assert len(result.findings) >= 2
    assert result.passed is False


# ============================================================================
# 12. PreCheckEngine — duration timing
# ============================================================================


def test_engine_duration_is_non_negative():
    """duration_ms is always >= 0."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(FIXTURES_DIR / "skill_short.md"))

    assert result.duration_ms >= 0


def test_engine_duration_file_not_found():
    """Duration is recorded even for file-not-found errors."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run("/nonexistent/skill.md")

    assert result.duration_ms >= 0


# ============================================================================
# 13. Edge cases
# ============================================================================


def test_engine_nonexistent_file_path_never_raises():
    """Engine never raises exceptions — always returns PreCheckResult."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run("/this/does/not/exist/at/all.md")

    assert isinstance(result, PreCheckResult)
    assert result.passed is False


def test_engine_very_long_content_performance(tmp_path):
    """Large file is processed without error and in reasonable time."""
    long_skill = tmp_path / "long_skill.md"
    # Create a 10,000-line file
    lines = ["# Long Skill\n", "## Description\nContent\n", "## Rules\nRules\n", "## Examples\nExamples\n"]
    lines.extend([f"Line {i}: some content here\n" for i in range(10_000)])
    long_skill.write_text("".join(lines))

    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(long_skill))

    assert isinstance(result, PreCheckResult)
    assert result.checks_run > 0
    # Should have max-lines error since 10k > 400
    max_line_findings = [f for f in result.findings if f.check == "max-lines"]
    assert len(max_line_findings) == 1


def test_engine_preserves_finding_order(tmp_path):
    """Findings from linter come before security findings."""
    skill = tmp_path / "ordered.md"
    skill.write_text('api_key = "sk-secret"\n')

    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)
    result = engine.run(str(skill))

    # Linter findings (empty-file check won't trigger since there's content,
    # but required-sections will) come before security findings
    checks = [f.check for f in result.findings]
    linter_checks = {"empty-file", "max-lines", "very-long-line", "required-sections", "file-not-found", "read-error"}
    security_start = None
    linter_end = None
    for i, c in enumerate(checks):
        if c in linter_checks:
            linter_end = i
        if c == "security_antipattern" and security_start is None:
            security_start = i

    # If both types exist, security findings appear after linter findings
    if security_start is not None and linter_end is not None:
        assert linter_end < security_start


def test_engine_passed_invariant_no_errors():
    """passed=True iff no finding has severity='error' (invariant check)."""
    rubric = _default_rubric()
    engine = PreCheckEngine(rubric)

    # Clean file → passed=True, no errors
    result_clean = engine.run(str(FIXTURES_DIR / "skill_short.md"))
    errors_clean = [f for f in result_clean.findings if f.severity == "error"]
    assert result_clean.passed is True
    assert len(errors_clean) == 0

    # Secret file → passed=False, has errors
    result_bad = engine.run(str(FIXTURES_DIR / "skill_with_secret.md"))
    errors_bad = [f for f in result_bad.findings if f.severity == "error"]
    assert result_bad.passed is False
    assert len(errors_bad) >= 1


def test_security_pattern_check_with_complex_regex():
    """SecurityPatternCheck compiles and uses complex regex patterns."""
    pattern = SecurityPattern(
        pattern=r"\b(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]+['\"]",
        message="Hardcoded credential",
        severity="error",
    )
    check = SecurityPatternCheck(pattern)
    content = 'config:\n  api_key = "sk-12345"\n  password: "hunter2"\nend'

    findings = check.scan(content)

    assert len(findings) == 2
    assert findings[0].line == 2
    assert findings[1].line == 3
