"""Tests for linter."""

import pytest
from md_evals.linter import (
    LinterEngine, MaxLinesRule, RequiredSectionsRule,
    EmptyFileRule, VeryLongLineRule
)
from md_evals.models import LinterConfig, LinterViolation


class TestMaxLinesRule:
    """Test MaxLinesRule."""
    
    def test_under_limit(self):
        """Test file under line limit."""
        rule = MaxLinesRule(limit=10)
        content = "\n".join([f"line {i}" for i in range(10)])
        
        violations = rule.check("skill.md", content)
        
        assert len(violations) == 0
    
    def test_over_limit(self):
        """Test file over line limit."""
        rule = MaxLinesRule(limit=10)
        content = "\n".join([f"line {i}" for i in range(15)])
        
        violations = rule.check("skill.md", content)
        
        assert len(violations) == 1
        assert violations[0].rule == "max-lines"
        assert "15" in violations[0].message
        assert violations[0].severity == "error"
    
    def test_exactly_limit(self):
        """Test file exactly at line limit."""
        rule = MaxLinesRule(limit=10)
        content = "\n".join([f"line {i}" for i in range(10)])
        
        violations = rule.check("skill.md", content)
        
        assert len(violations) == 0


class TestRequiredSectionsRule:
    """Test RequiredSectionsRule."""
    
    def test_all_sections_present(self):
        """Test all sections present."""
        rule = RequiredSectionsRule()
        content = """
# Description
Some description

## Rules
Some rules

## Examples
Some examples
"""
        
        violations = rule.check("skill.md", content)
        
        # Warnings only, not errors
        assert all(v.severity == "warning" for v in violations)
    
    def test_missing_sections(self):
        """Test missing sections."""
        rule = RequiredSectionsRule()
        content = """
# Description
Some description
"""
        
        violations = rule.check("skill.md", content)
        
        assert len(violations) > 0
        assert any("Rules" in v.message for v in violations)


class TestEmptyFileRule:
    """Test EmptyFileRule."""
    
    def test_empty_content(self):
        """Test empty content."""
        rule = EmptyFileRule()
        
        violations = rule.check("skill.md", "")
        
        assert len(violations) == 1
        assert violations[0].rule == "empty-file"
        assert violations[0].severity == "error"
    
    def test_whitespace_only(self):
        """Test whitespace only."""
        rule = EmptyFileRule()
        
        violations = rule.check("skill.md", "   \n\t\n   ")
        
        assert len(violations) == 1
    
    def test_valid_content(self):
        """Test valid content."""
        rule = EmptyFileRule()
        
        violations = rule.check("skill.md", "# Hello\nWorld")
        
        assert len(violations) == 0


class TestVeryLongLineRule:
    """Test VeryLongLineRule."""
    
    def test_long_line(self):
        """Test very long line."""
        rule = VeryLongLineRule(limit=50)
        content = "a" * 100
        
        violations = rule.check("skill.md", content)
        
        assert len(violations) == 1
        assert violations[0].line == 1
        assert violations[0].severity == "warning"
    
    def test_short_lines(self):
        """Test short lines."""
        rule = VeryLongLineRule(limit=50)
        content = "short line\nanother short line"
        
        violations = rule.check("skill.md", content)
        
        assert len(violations) == 0


class TestLinterEngine:
    """Test LinterEngine."""
    
    def test_file_not_found(self, tmp_path):
        """Test file not found."""
        config = LinterConfig()
        engine = LinterEngine(config)
        
        report = engine.run(str(tmp_path / "nonexistent.md"))
        
        assert not report.passed
        assert any("not found" in v.message.lower() for v in report.violations)
    
    def test_empty_file(self, tmp_path):
        """Test empty file."""
        skill_file = tmp_path / "empty.md"
        skill_file.write_text("")
        
        config = LinterConfig()
        engine = LinterEngine(config)
        
        report = engine.run(str(skill_file))
        
        assert not report.passed
        assert report.line_count == 0
    
    def test_valid_file(self, tmp_path):
        """Test valid file."""
        skill_file = tmp_path / "valid.md"
        skill_file.write_text("""# Description
Some description

## Rules
- Rule 1
- Rule 2

## Examples
Example 1
""")
        
        config = LinterConfig()
        engine = LinterEngine(config)
        
        report = engine.run(str(skill_file))
        
        assert report.passed
        assert report.line_count > 0
    
    def test_fail_on_violation(self, tmp_path):
        """Test fail_on_violation config."""
        skill_file = tmp_path / "long.md"
        skill_file.write_text("\n".join([f"line {i}" for i in range(500)]))
        
        config = LinterConfig(fail_on_violation=True)
        engine = LinterEngine(config)
        
        result = engine.check(str(skill_file))
        
        assert not result
    
    def test_no_fail_on_warning(self, tmp_path):
        """Test not failing on warnings only."""
        skill_file = tmp_path / "no_desc.md"
        skill_file.write_text("# Just a title\n\nNo description section")
        
        config = LinterConfig(fail_on_violation=True)
        engine = LinterEngine(config)
        
        # Should not fail on warnings
        result = engine.check(str(skill_file))
        
        # Only warnings, no errors -> should pass
        assert result
