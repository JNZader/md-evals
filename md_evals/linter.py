"""Linter for validating SKILL.md files."""

from pathlib import Path
from md_evals.models import LinterConfig, LinterReport, LinterViolation


class LinterRule:
    """Base class for linter rules."""
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        """Check skill file content.
        
        Args:
            skill_path: Path to skill file
            content: Skill file content
            
        Returns:
            List of violations
        """
        raise NotImplementedError


class MaxLinesRule(LinterRule):
    """Check if skill file exceeds maximum lines."""
    
    def __init__(self, limit: int = 400):
        self.limit = limit
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []


class RequiredSectionsRule(LinterRule):
    """Check if skill file has required sections."""
    
    def __init__(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "Rules", "Examples"]
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations


class EmptyFileRule(LinterRule):
    """Check if skill file is empty."""
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                severity="error"
            )]
        return []


class VeryLongLineRule(LinterRule):
    """Check for very long lines."""
    
    def __init__(self, limit: int = 200):
        self.limit = limit
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations


class LinterEngine:
    """Validates SKILL.md against constraints."""
    
    def __init__(self, config: LinterConfig | None = None):
        self.config = config or LinterConfig()
        self.rules: list[LinterRule] = [
            EmptyFileRule(),
            MaxLinesRule(self.config.max_lines),
            VeryLongLineRule(),
            RequiredSectionsRule()
        ]
    
    def run(self, skill_path: str) -> LinterReport:
        """Run linter on skill file.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            LinterReport with results
        """
        file_path = Path(skill_path)
        
        # Check file exists
        if not file_path.exists():
            return LinterReport(
                skill_path=skill_path,
                passed=False,
                violations=[LinterViolation(
                    rule="file-not-found",
                    message=f"Skill file not found: {skill_path}",
                    severity="error"
                )]
            )
        
        # Read content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return LinterReport(
                skill_path=skill_path,
                passed=False,
                violations=[LinterViolation(
                    rule="read-error",
                    message=f"Error reading file: {e}",
                    severity="error"
                )]
            )
        
        # Count lines
        line_count = len(content.splitlines())
        
        # Run all rules
        all_violations = []
        for rule in self.rules:
            violations = rule.check(skill_path, content)
            all_violations.extend(violations)
        
        # Determine if passed
        has_errors = any(v.severity == "error" for v in all_violations)
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def check(self, skill_path: str) -> bool:
        """Quick check if skill file passes.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            True if passes, False otherwise
        """
        report = self.run(skill_path)
        
        if self.config.fail_on_violation:
            return report.passed
        
        # If not failing on violation, only fail on errors
        return not any(v.severity == "error" for v in report.violations)
