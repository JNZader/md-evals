"""Integration tests for the linter — real SKILL.md files, no mocks."""

from pathlib import Path


from md_evals.linter import LinterEngine
from md_evals.models import LinterConfig


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLinterValidFiles:
    """Run linter on valid SKILL.md files."""

    def test_valid_skill_passes(self):
        engine = LinterEngine()
        report = engine.run(str(FIXTURES / "skill_valid.md"))
        assert report.passed is True
        assert report.line_count > 0

    def test_short_skill_passes(self):
        engine = LinterEngine()
        report = engine.run(str(FIXTURES / "skill_short.md"))
        assert report.passed is True

    def test_valid_skill_no_errors(self):
        engine = LinterEngine()
        report = engine.run(str(FIXTURES / "skill_valid.md"))
        errors = [v for v in report.violations if v.severity == "error"]
        assert len(errors) == 0


class TestLinterInvalidFiles:
    """Run linter on files with real issues."""

    def test_empty_file_fails(self):
        engine = LinterEngine()
        report = engine.run(str(FIXTURES / "skill_invalid_empty.md"))
        assert report.passed is False
        rules = [v.rule for v in report.violations]
        assert "empty-file" in rules

    def test_missing_sections_warning(self, tmp_path):
        """Create a file truly missing section keywords for reliable detection."""
        skill = tmp_path / "SKILL.md"
        skill.write_text("# My Skill\n\n## Description\nJust a desc, nothing else here.\n")
        engine = LinterEngine()
        report = engine.run(str(skill))
        warnings = [v for v in report.violations if v.severity == "warning"]
        missing_rules = [v for v in warnings if v.rule == "required-sections"]
        assert len(missing_rules) >= 1  # missing Rules and/or Examples

    def test_nonexistent_file(self):
        engine = LinterEngine()
        report = engine.run("/nonexistent/SKILL.md")
        assert report.passed is False
        rules = [v.rule for v in report.violations]
        assert "file-not-found" in rules

    def test_long_file_exceeds_limit(self):
        engine = LinterEngine()
        report = engine.run(str(FIXTURES / "skill_long.md"))
        # skill_long.md exists in fixtures — check if it triggers max-lines
        if report.line_count > 400:
            rules = [v.rule for v in report.violations]
            assert "max-lines" in rules


class TestLinterCustomConfig:
    """Test linter with custom configurations."""

    def test_custom_max_lines(self, tmp_path):
        skill = tmp_path / "SKILL.md"
        content = "# Skill\n\n## Description\nTest\n\n## Rules\n- Rule\n\n## Examples\n- Ex\n"
        content += "\n".join([f"Line {i}" for i in range(50)])
        skill.write_text(content)

        config = LinterConfig(max_lines=20)
        engine = LinterEngine(config)
        report = engine.run(str(skill))
        rules = [v.rule for v in report.violations]
        assert "max-lines" in rules

    def test_fail_on_violation_false(self):
        config = LinterConfig(fail_on_violation=False)
        engine = LinterEngine(config)
        # Even with violations, check() returns True when fail_on_violation=False
        result = engine.check(str(FIXTURES / "skill_missing_sections.md"))
        # Only errors cause failure, not warnings
        assert result is True

    def test_very_long_lines(self, tmp_path):
        skill = tmp_path / "SKILL.md"
        long_line = "x" * 250
        skill.write_text(f"# Skill\n\n## Description\n{long_line}\n\n## Rules\n- R\n\n## Examples\n- E\n")
        engine = LinterEngine()
        report = engine.run(str(skill))
        long_line_violations = [v for v in report.violations if v.rule == "very-long-line"]
        assert len(long_line_violations) >= 1
        assert long_line_violations[0].line is not None


class TestLinterCheckMethod:
    """Test the quick check() method."""

    def test_check_valid_returns_true(self):
        engine = LinterEngine()
        assert engine.check(str(FIXTURES / "skill_valid.md")) is True

    def test_check_empty_returns_false(self):
        engine = LinterEngine()
        assert engine.check(str(FIXTURES / "skill_invalid_empty.md")) is False

    def test_check_nonexistent_returns_false(self):
        engine = LinterEngine()
        assert engine.check("/nonexistent/SKILL.md") is False
