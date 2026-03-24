"""Integration tests for PreCheckEngine — real files, real rubric, no mocks."""

from pathlib import Path

import pytest

from md_evals.precheck import PreCheckEngine, PreCheckResult, PreCheckFinding
from md_evals.rubric import RubricLoader, RubricConfig, DimensionConfig, PreCheckConfig, SecurityPattern


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestPreCheckWithDefaultRubric:
    """Run PreCheckEngine with the built-in default rubric against real files."""

    def test_valid_skill_passes(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        result = engine.run(str(FIXTURES / "skill_valid.md"))

        assert isinstance(result, PreCheckResult)
        assert result.passed is True
        assert result.checks_run > 0
        assert result.duration_ms >= 0

    def test_empty_file_fails(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        result = engine.run(str(FIXTURES / "skill_invalid_empty.md"))

        assert result.passed is False
        checks = [f.check for f in result.findings]
        assert "empty-file" in checks

    def test_missing_file_fails(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        result = engine.run("/nonexistent/SKILL.md")

        assert result.passed is False
        checks = [f.check for f in result.findings]
        assert "file-not-found" in checks

    def test_missing_sections_findings(self, tmp_path):
        """Use a file that truly lacks section keywords in the body."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("# My Skill\n\n## Description\nJust a description here.\n")
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        result = engine.run(str(skill))

        # Missing sections produce warnings
        section_findings = [
            f for f in result.findings if f.check == "required-sections"
        ]
        assert len(section_findings) >= 1

    def test_skill_with_secret(self):
        rubric = RubricLoader.load_default()
        engine = PreCheckEngine(rubric)
        result = engine.run(str(FIXTURES / "skill_with_secret.md"))

        security_findings = [
            f for f in result.findings if f.check == "security_antipattern"
        ]
        assert len(security_findings) >= 1


class TestPreCheckWithCustomRubric:
    """Test PreCheckEngine with custom rubric configs."""

    def test_custom_max_lines(self, tmp_path):
        skill = tmp_path / "SKILL.md"
        lines = ["# Skill", "", "## Description", "Test", "", "## Rules", "- R", "", "## Examples", "- E"]
        lines += [f"Extra line {i}" for i in range(20)]
        skill.write_text("\n".join(lines))

        rubric = RubricConfig(
            dimensions={"correctness": DimensionConfig(weight=1.0, description="test")},
            grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30},
            pre_check=PreCheckConfig(max_lines=10),
        )
        engine = PreCheckEngine(rubric)
        result = engine.run(str(skill))

        max_line_findings = [f for f in result.findings if f.check == "max-lines"]
        assert len(max_line_findings) == 1

    def test_custom_security_pattern(self, tmp_path):
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "# Skill\n\n## Description\nTest\n\n## Rules\n- R\n\n## Examples\n"
            "Use `sudo rm -rf /` to clean up\n"
        )

        rubric = RubricConfig(
            dimensions={"correctness": DimensionConfig(weight=1.0, description="test")},
            grade_thresholds={"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30},
            pre_check=PreCheckConfig(
                security_patterns=[
                    SecurityPattern(
                        pattern=r"sudo\s+rm\s+-rf",
                        message="Dangerous rm -rf detected",
                        severity="error",
                    )
                ]
            ),
        )
        engine = PreCheckEngine(rubric)
        result = engine.run(str(skill))

        security_findings = [
            f for f in result.findings if f.check == "security_antipattern"
        ]
        assert len(security_findings) >= 1
        assert "rm -rf" in security_findings[0].message


class TestPreCheckResultStructure:
    """Verify PreCheckResult dataclass integrity."""

    def test_result_is_frozen(self):
        result = PreCheckResult(passed=True, findings=[], checks_run=4, duration_ms=1)
        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore[misc]

    def test_finding_is_frozen(self):
        finding = PreCheckFinding(check="test", message="msg", severity="info")
        with pytest.raises(AttributeError):
            finding.severity = "error"  # type: ignore[misc]

    def test_finding_with_line_number(self):
        finding = PreCheckFinding(check="test", message="msg", severity="warning", line=42)
        assert finding.line == 42


class TestRubricLoadIntegration:
    """Test rubric loading (dependency for PreCheck)."""

    def test_load_default_rubric(self):
        rubric = RubricLoader.load_default()
        assert rubric.version == "1.0"
        assert len(rubric.dimensions) == 7
        assert "correctness" in rubric.dimensions
        assert "S" in rubric.grade_thresholds

    def test_load_custom_rubric_fixture(self):
        rubric = RubricLoader.load(str(FIXTURES / "rubric_default.yaml"))
        assert rubric.version == "1.0"

    def test_load_no_s_grade(self):
        rubric = RubricLoader.load(str(FIXTURES / "rubric_no_s_grade.yaml"))
        assert "S" not in rubric.grade_thresholds
