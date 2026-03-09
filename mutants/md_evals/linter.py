"""Linter for validating SKILL.md files."""

from pathlib import Path
from md_evals.models import LinterConfig, LinterReport, LinterViolation
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


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
        args = [limit]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁMaxLinesRuleǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁMaxLinesRuleǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁMaxLinesRuleǁ__init____mutmut_orig(self, limit: int = 400):
        self.limit = limit
    
    def xǁMaxLinesRuleǁ__init____mutmut_1(self, limit: int = 401):
        self.limit = limit
    
    def xǁMaxLinesRuleǁ__init____mutmut_2(self, limit: int = 400):
        self.limit = None
    
    xǁMaxLinesRuleǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁMaxLinesRuleǁ__init____mutmut_1': xǁMaxLinesRuleǁ__init____mutmut_1, 
        'xǁMaxLinesRuleǁ__init____mutmut_2': xǁMaxLinesRuleǁ__init____mutmut_2
    }
    xǁMaxLinesRuleǁ__init____mutmut_orig.__name__ = 'xǁMaxLinesRuleǁ__init__'
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        args = [skill_path, content]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁMaxLinesRuleǁcheck__mutmut_orig'), object.__getattribute__(self, 'xǁMaxLinesRuleǁcheck__mutmut_mutants'), args, kwargs, self)
    
    def xǁMaxLinesRuleǁcheck__mutmut_orig(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_1(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = None
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_2(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = None
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_3(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count >= self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_4(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule=None,
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_5(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=None,
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_6(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity=None
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_7(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_8(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_9(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_10(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="XXmax-linesXX",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_11(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="MAX-LINES",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="error"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_12(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="XXerrorXX"
            )]
        
        return []
    
    def xǁMaxLinesRuleǁcheck__mutmut_13(self, skill_path: str, content: str) -> list[LinterViolation]:
        lines = content.splitlines()
        line_count = len(lines)
        
        if line_count > self.limit:
            return [LinterViolation(
                rule="max-lines",
                message=f"Skill file has {line_count} lines, exceeds limit of {self.limit}",
                severity="ERROR"
            )]
        
        return []
    
    xǁMaxLinesRuleǁcheck__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁMaxLinesRuleǁcheck__mutmut_1': xǁMaxLinesRuleǁcheck__mutmut_1, 
        'xǁMaxLinesRuleǁcheck__mutmut_2': xǁMaxLinesRuleǁcheck__mutmut_2, 
        'xǁMaxLinesRuleǁcheck__mutmut_3': xǁMaxLinesRuleǁcheck__mutmut_3, 
        'xǁMaxLinesRuleǁcheck__mutmut_4': xǁMaxLinesRuleǁcheck__mutmut_4, 
        'xǁMaxLinesRuleǁcheck__mutmut_5': xǁMaxLinesRuleǁcheck__mutmut_5, 
        'xǁMaxLinesRuleǁcheck__mutmut_6': xǁMaxLinesRuleǁcheck__mutmut_6, 
        'xǁMaxLinesRuleǁcheck__mutmut_7': xǁMaxLinesRuleǁcheck__mutmut_7, 
        'xǁMaxLinesRuleǁcheck__mutmut_8': xǁMaxLinesRuleǁcheck__mutmut_8, 
        'xǁMaxLinesRuleǁcheck__mutmut_9': xǁMaxLinesRuleǁcheck__mutmut_9, 
        'xǁMaxLinesRuleǁcheck__mutmut_10': xǁMaxLinesRuleǁcheck__mutmut_10, 
        'xǁMaxLinesRuleǁcheck__mutmut_11': xǁMaxLinesRuleǁcheck__mutmut_11, 
        'xǁMaxLinesRuleǁcheck__mutmut_12': xǁMaxLinesRuleǁcheck__mutmut_12, 
        'xǁMaxLinesRuleǁcheck__mutmut_13': xǁMaxLinesRuleǁcheck__mutmut_13
    }
    xǁMaxLinesRuleǁcheck__mutmut_orig.__name__ = 'xǁMaxLinesRuleǁcheck'


class RequiredSectionsRule(LinterRule):
    """Check if skill file has required sections."""
    
    def __init__(self, sections: list[str] | None = None):
        args = [sections]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRequiredSectionsRuleǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRequiredSectionsRuleǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_orig(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "Rules", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_1(self, sections: list[str] | None = None):
        self.sections = None
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_2(self, sections: list[str] | None = None):
        self.sections = sections and ["Description", "Rules", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_3(self, sections: list[str] | None = None):
        self.sections = sections or ["XXDescriptionXX", "Rules", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_4(self, sections: list[str] | None = None):
        self.sections = sections or ["description", "Rules", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_5(self, sections: list[str] | None = None):
        self.sections = sections or ["DESCRIPTION", "Rules", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_6(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "XXRulesXX", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_7(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "rules", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_8(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "RULES", "Examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_9(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "Rules", "XXExamplesXX"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_10(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "Rules", "examples"]
    
    def xǁRequiredSectionsRuleǁ__init____mutmut_11(self, sections: list[str] | None = None):
        self.sections = sections or ["Description", "Rules", "EXAMPLES"]
    
    xǁRequiredSectionsRuleǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRequiredSectionsRuleǁ__init____mutmut_1': xǁRequiredSectionsRuleǁ__init____mutmut_1, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_2': xǁRequiredSectionsRuleǁ__init____mutmut_2, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_3': xǁRequiredSectionsRuleǁ__init____mutmut_3, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_4': xǁRequiredSectionsRuleǁ__init____mutmut_4, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_5': xǁRequiredSectionsRuleǁ__init____mutmut_5, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_6': xǁRequiredSectionsRuleǁ__init____mutmut_6, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_7': xǁRequiredSectionsRuleǁ__init____mutmut_7, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_8': xǁRequiredSectionsRuleǁ__init____mutmut_8, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_9': xǁRequiredSectionsRuleǁ__init____mutmut_9, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_10': xǁRequiredSectionsRuleǁ__init____mutmut_10, 
        'xǁRequiredSectionsRuleǁ__init____mutmut_11': xǁRequiredSectionsRuleǁ__init____mutmut_11
    }
    xǁRequiredSectionsRuleǁ__init____mutmut_orig.__name__ = 'xǁRequiredSectionsRuleǁ__init__'
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        args = [skill_path, content]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRequiredSectionsRuleǁcheck__mutmut_orig'), object.__getattribute__(self, 'xǁRequiredSectionsRuleǁcheck__mutmut_mutants'), args, kwargs, self)
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_orig(self, skill_path: str, content: str) -> list[LinterViolation]:
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
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_1(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = None
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
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_2(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = None
        
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
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_3(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.upper()
        
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
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_4(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = None
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_5(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.upper()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_6(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower or section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_7(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_8(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.upper() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_9(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_10(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(None)
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_11(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule=None,
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_12(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=None,
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_13(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity=None
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_14(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_15(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_16(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_17(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="XXrequired-sectionsXX",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_18(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="REQUIRED-SECTIONS",
                    message=f"Missing recommended section: {section}",
                    severity="warning"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_19(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="XXwarningXX"
                ))
        
        return violations
    
    def xǁRequiredSectionsRuleǁcheck__mutmut_20(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        content_lower = content.lower()
        
        for section in self.sections:
            # Check for section header (e.g., "# Description" or "## Description")
            section_pattern = f"# {section.lower()}"
            if section_pattern not in content_lower and section.lower() not in content_lower:
                violations.append(LinterViolation(
                    rule="required-sections",
                    message=f"Missing recommended section: {section}",
                    severity="WARNING"
                ))
        
        return violations
    
    xǁRequiredSectionsRuleǁcheck__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRequiredSectionsRuleǁcheck__mutmut_1': xǁRequiredSectionsRuleǁcheck__mutmut_1, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_2': xǁRequiredSectionsRuleǁcheck__mutmut_2, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_3': xǁRequiredSectionsRuleǁcheck__mutmut_3, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_4': xǁRequiredSectionsRuleǁcheck__mutmut_4, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_5': xǁRequiredSectionsRuleǁcheck__mutmut_5, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_6': xǁRequiredSectionsRuleǁcheck__mutmut_6, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_7': xǁRequiredSectionsRuleǁcheck__mutmut_7, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_8': xǁRequiredSectionsRuleǁcheck__mutmut_8, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_9': xǁRequiredSectionsRuleǁcheck__mutmut_9, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_10': xǁRequiredSectionsRuleǁcheck__mutmut_10, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_11': xǁRequiredSectionsRuleǁcheck__mutmut_11, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_12': xǁRequiredSectionsRuleǁcheck__mutmut_12, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_13': xǁRequiredSectionsRuleǁcheck__mutmut_13, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_14': xǁRequiredSectionsRuleǁcheck__mutmut_14, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_15': xǁRequiredSectionsRuleǁcheck__mutmut_15, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_16': xǁRequiredSectionsRuleǁcheck__mutmut_16, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_17': xǁRequiredSectionsRuleǁcheck__mutmut_17, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_18': xǁRequiredSectionsRuleǁcheck__mutmut_18, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_19': xǁRequiredSectionsRuleǁcheck__mutmut_19, 
        'xǁRequiredSectionsRuleǁcheck__mutmut_20': xǁRequiredSectionsRuleǁcheck__mutmut_20
    }
    xǁRequiredSectionsRuleǁcheck__mutmut_orig.__name__ = 'xǁRequiredSectionsRuleǁcheck'


class EmptyFileRule(LinterRule):
    """Check if skill file is empty."""
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        args = [skill_path, content]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEmptyFileRuleǁcheck__mutmut_orig'), object.__getattribute__(self, 'xǁEmptyFileRuleǁcheck__mutmut_mutants'), args, kwargs, self)
    
    def xǁEmptyFileRuleǁcheck__mutmut_orig(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_1(self, skill_path: str, content: str) -> list[LinterViolation]:
        if content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_2(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule=None,
                message="Skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_3(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message=None,
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_4(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                severity=None
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_5(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                message="Skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_6(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_7(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_8(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="XXempty-fileXX",
                message="Skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_9(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="EMPTY-FILE",
                message="Skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_10(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="XXSkill file is emptyXX",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_11(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="skill file is empty",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_12(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="SKILL FILE IS EMPTY",
                severity="error"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_13(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                severity="XXerrorXX"
            )]
        return []
    
    def xǁEmptyFileRuleǁcheck__mutmut_14(self, skill_path: str, content: str) -> list[LinterViolation]:
        if not content.strip():
            return [LinterViolation(
                rule="empty-file",
                message="Skill file is empty",
                severity="ERROR"
            )]
        return []
    
    xǁEmptyFileRuleǁcheck__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEmptyFileRuleǁcheck__mutmut_1': xǁEmptyFileRuleǁcheck__mutmut_1, 
        'xǁEmptyFileRuleǁcheck__mutmut_2': xǁEmptyFileRuleǁcheck__mutmut_2, 
        'xǁEmptyFileRuleǁcheck__mutmut_3': xǁEmptyFileRuleǁcheck__mutmut_3, 
        'xǁEmptyFileRuleǁcheck__mutmut_4': xǁEmptyFileRuleǁcheck__mutmut_4, 
        'xǁEmptyFileRuleǁcheck__mutmut_5': xǁEmptyFileRuleǁcheck__mutmut_5, 
        'xǁEmptyFileRuleǁcheck__mutmut_6': xǁEmptyFileRuleǁcheck__mutmut_6, 
        'xǁEmptyFileRuleǁcheck__mutmut_7': xǁEmptyFileRuleǁcheck__mutmut_7, 
        'xǁEmptyFileRuleǁcheck__mutmut_8': xǁEmptyFileRuleǁcheck__mutmut_8, 
        'xǁEmptyFileRuleǁcheck__mutmut_9': xǁEmptyFileRuleǁcheck__mutmut_9, 
        'xǁEmptyFileRuleǁcheck__mutmut_10': xǁEmptyFileRuleǁcheck__mutmut_10, 
        'xǁEmptyFileRuleǁcheck__mutmut_11': xǁEmptyFileRuleǁcheck__mutmut_11, 
        'xǁEmptyFileRuleǁcheck__mutmut_12': xǁEmptyFileRuleǁcheck__mutmut_12, 
        'xǁEmptyFileRuleǁcheck__mutmut_13': xǁEmptyFileRuleǁcheck__mutmut_13, 
        'xǁEmptyFileRuleǁcheck__mutmut_14': xǁEmptyFileRuleǁcheck__mutmut_14
    }
    xǁEmptyFileRuleǁcheck__mutmut_orig.__name__ = 'xǁEmptyFileRuleǁcheck'


class VeryLongLineRule(LinterRule):
    """Check for very long lines."""
    
    def __init__(self, limit: int = 200):
        args = [limit]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁVeryLongLineRuleǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁVeryLongLineRuleǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁVeryLongLineRuleǁ__init____mutmut_orig(self, limit: int = 200):
        self.limit = limit
    
    def xǁVeryLongLineRuleǁ__init____mutmut_1(self, limit: int = 201):
        self.limit = limit
    
    def xǁVeryLongLineRuleǁ__init____mutmut_2(self, limit: int = 200):
        self.limit = None
    
    xǁVeryLongLineRuleǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁVeryLongLineRuleǁ__init____mutmut_1': xǁVeryLongLineRuleǁ__init____mutmut_1, 
        'xǁVeryLongLineRuleǁ__init____mutmut_2': xǁVeryLongLineRuleǁ__init____mutmut_2
    }
    xǁVeryLongLineRuleǁ__init____mutmut_orig.__name__ = 'xǁVeryLongLineRuleǁ__init__'
    
    def check(self, skill_path: str, content: str) -> list[LinterViolation]:
        args = [skill_path, content]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁVeryLongLineRuleǁcheck__mutmut_orig'), object.__getattribute__(self, 'xǁVeryLongLineRuleǁcheck__mutmut_mutants'), args, kwargs, self)
    
    def xǁVeryLongLineRuleǁcheck__mutmut_orig(self, skill_path: str, content: str) -> list[LinterViolation]:
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
    
    def xǁVeryLongLineRuleǁcheck__mutmut_1(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = None
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_2(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(None, 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_3(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), None):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_4(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_5(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), ):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_6(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 2):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_7(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) >= self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_8(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(None)
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_9(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule=None,
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_10(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=None,
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_11(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity=None,
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_12(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=None
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_13(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_14(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_15(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_16(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_17(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="XXvery-long-lineXX",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_18(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="VERY-LONG-LINE",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="warning",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_19(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="XXwarningXX",
                    line=i
                ))
        
        return violations
    
    def xǁVeryLongLineRuleǁcheck__mutmut_20(self, skill_path: str, content: str) -> list[LinterViolation]:
        violations = []
        
        for i, line in enumerate(content.splitlines(), 1):
            if len(line) > self.limit:
                violations.append(LinterViolation(
                    rule="very-long-line",
                    message=f"Line {i} exceeds {self.limit} characters ({len(line)} chars)",
                    severity="WARNING",
                    line=i
                ))
        
        return violations
    
    xǁVeryLongLineRuleǁcheck__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁVeryLongLineRuleǁcheck__mutmut_1': xǁVeryLongLineRuleǁcheck__mutmut_1, 
        'xǁVeryLongLineRuleǁcheck__mutmut_2': xǁVeryLongLineRuleǁcheck__mutmut_2, 
        'xǁVeryLongLineRuleǁcheck__mutmut_3': xǁVeryLongLineRuleǁcheck__mutmut_3, 
        'xǁVeryLongLineRuleǁcheck__mutmut_4': xǁVeryLongLineRuleǁcheck__mutmut_4, 
        'xǁVeryLongLineRuleǁcheck__mutmut_5': xǁVeryLongLineRuleǁcheck__mutmut_5, 
        'xǁVeryLongLineRuleǁcheck__mutmut_6': xǁVeryLongLineRuleǁcheck__mutmut_6, 
        'xǁVeryLongLineRuleǁcheck__mutmut_7': xǁVeryLongLineRuleǁcheck__mutmut_7, 
        'xǁVeryLongLineRuleǁcheck__mutmut_8': xǁVeryLongLineRuleǁcheck__mutmut_8, 
        'xǁVeryLongLineRuleǁcheck__mutmut_9': xǁVeryLongLineRuleǁcheck__mutmut_9, 
        'xǁVeryLongLineRuleǁcheck__mutmut_10': xǁVeryLongLineRuleǁcheck__mutmut_10, 
        'xǁVeryLongLineRuleǁcheck__mutmut_11': xǁVeryLongLineRuleǁcheck__mutmut_11, 
        'xǁVeryLongLineRuleǁcheck__mutmut_12': xǁVeryLongLineRuleǁcheck__mutmut_12, 
        'xǁVeryLongLineRuleǁcheck__mutmut_13': xǁVeryLongLineRuleǁcheck__mutmut_13, 
        'xǁVeryLongLineRuleǁcheck__mutmut_14': xǁVeryLongLineRuleǁcheck__mutmut_14, 
        'xǁVeryLongLineRuleǁcheck__mutmut_15': xǁVeryLongLineRuleǁcheck__mutmut_15, 
        'xǁVeryLongLineRuleǁcheck__mutmut_16': xǁVeryLongLineRuleǁcheck__mutmut_16, 
        'xǁVeryLongLineRuleǁcheck__mutmut_17': xǁVeryLongLineRuleǁcheck__mutmut_17, 
        'xǁVeryLongLineRuleǁcheck__mutmut_18': xǁVeryLongLineRuleǁcheck__mutmut_18, 
        'xǁVeryLongLineRuleǁcheck__mutmut_19': xǁVeryLongLineRuleǁcheck__mutmut_19, 
        'xǁVeryLongLineRuleǁcheck__mutmut_20': xǁVeryLongLineRuleǁcheck__mutmut_20
    }
    xǁVeryLongLineRuleǁcheck__mutmut_orig.__name__ = 'xǁVeryLongLineRuleǁcheck'


class LinterEngine:
    """Validates SKILL.md against constraints."""
    
    def __init__(self, config: LinterConfig | None = None):
        args = [config]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁLinterEngineǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁLinterEngineǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁLinterEngineǁ__init____mutmut_orig(self, config: LinterConfig | None = None):
        self.config = config or LinterConfig()
        self.rules: list[LinterRule] = [
            EmptyFileRule(),
            MaxLinesRule(self.config.max_lines),
            VeryLongLineRule(),
            RequiredSectionsRule()
        ]
    
    def xǁLinterEngineǁ__init____mutmut_1(self, config: LinterConfig | None = None):
        self.config = None
        self.rules: list[LinterRule] = [
            EmptyFileRule(),
            MaxLinesRule(self.config.max_lines),
            VeryLongLineRule(),
            RequiredSectionsRule()
        ]
    
    def xǁLinterEngineǁ__init____mutmut_2(self, config: LinterConfig | None = None):
        self.config = config and LinterConfig()
        self.rules: list[LinterRule] = [
            EmptyFileRule(),
            MaxLinesRule(self.config.max_lines),
            VeryLongLineRule(),
            RequiredSectionsRule()
        ]
    
    def xǁLinterEngineǁ__init____mutmut_3(self, config: LinterConfig | None = None):
        self.config = config or LinterConfig()
        self.rules: list[LinterRule] = None
    
    def xǁLinterEngineǁ__init____mutmut_4(self, config: LinterConfig | None = None):
        self.config = config or LinterConfig()
        self.rules: list[LinterRule] = [
            EmptyFileRule(),
            MaxLinesRule(None),
            VeryLongLineRule(),
            RequiredSectionsRule()
        ]
    
    xǁLinterEngineǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLinterEngineǁ__init____mutmut_1': xǁLinterEngineǁ__init____mutmut_1, 
        'xǁLinterEngineǁ__init____mutmut_2': xǁLinterEngineǁ__init____mutmut_2, 
        'xǁLinterEngineǁ__init____mutmut_3': xǁLinterEngineǁ__init____mutmut_3, 
        'xǁLinterEngineǁ__init____mutmut_4': xǁLinterEngineǁ__init____mutmut_4
    }
    xǁLinterEngineǁ__init____mutmut_orig.__name__ = 'xǁLinterEngineǁ__init__'
    
    def run(self, skill_path: str) -> LinterReport:
        args = [skill_path]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁLinterEngineǁrun__mutmut_orig'), object.__getattribute__(self, 'xǁLinterEngineǁrun__mutmut_mutants'), args, kwargs, self)
    
    def xǁLinterEngineǁrun__mutmut_orig(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_1(self, skill_path: str) -> LinterReport:
        """Run linter on skill file.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            LinterReport with results
        """
        file_path = None
        
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
    
    def xǁLinterEngineǁrun__mutmut_2(self, skill_path: str) -> LinterReport:
        """Run linter on skill file.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            LinterReport with results
        """
        file_path = Path(None)
        
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
    
    def xǁLinterEngineǁrun__mutmut_3(self, skill_path: str) -> LinterReport:
        """Run linter on skill file.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            LinterReport with results
        """
        file_path = Path(skill_path)
        
        # Check file exists
        if file_path.exists():
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
    
    def xǁLinterEngineǁrun__mutmut_4(self, skill_path: str) -> LinterReport:
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
                skill_path=None,
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
    
    def xǁLinterEngineǁrun__mutmut_5(self, skill_path: str) -> LinterReport:
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
                passed=None,
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
    
    def xǁLinterEngineǁrun__mutmut_6(self, skill_path: str) -> LinterReport:
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
                violations=None
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
    
    def xǁLinterEngineǁrun__mutmut_7(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_8(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_9(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_10(self, skill_path: str) -> LinterReport:
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
                passed=True,
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
    
    def xǁLinterEngineǁrun__mutmut_11(self, skill_path: str) -> LinterReport:
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
                    rule=None,
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
    
    def xǁLinterEngineǁrun__mutmut_12(self, skill_path: str) -> LinterReport:
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
                    message=None,
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
    
    def xǁLinterEngineǁrun__mutmut_13(self, skill_path: str) -> LinterReport:
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
                    severity=None
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
    
    def xǁLinterEngineǁrun__mutmut_14(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_15(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_16(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_17(self, skill_path: str) -> LinterReport:
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
                    rule="XXfile-not-foundXX",
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
    
    def xǁLinterEngineǁrun__mutmut_18(self, skill_path: str) -> LinterReport:
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
                    rule="FILE-NOT-FOUND",
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
    
    def xǁLinterEngineǁrun__mutmut_19(self, skill_path: str) -> LinterReport:
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
                    severity="XXerrorXX"
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
    
    def xǁLinterEngineǁrun__mutmut_20(self, skill_path: str) -> LinterReport:
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
                    severity="ERROR"
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
    
    def xǁLinterEngineǁrun__mutmut_21(self, skill_path: str) -> LinterReport:
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
            content = None
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
    
    def xǁLinterEngineǁrun__mutmut_22(self, skill_path: str) -> LinterReport:
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
            content = file_path.read_text(encoding=None)
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
    
    def xǁLinterEngineǁrun__mutmut_23(self, skill_path: str) -> LinterReport:
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
            content = file_path.read_text(encoding="XXutf-8XX")
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
    
    def xǁLinterEngineǁrun__mutmut_24(self, skill_path: str) -> LinterReport:
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
            content = file_path.read_text(encoding="UTF-8")
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
    
    def xǁLinterEngineǁrun__mutmut_25(self, skill_path: str) -> LinterReport:
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
                skill_path=None,
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
    
    def xǁLinterEngineǁrun__mutmut_26(self, skill_path: str) -> LinterReport:
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
                passed=None,
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
    
    def xǁLinterEngineǁrun__mutmut_27(self, skill_path: str) -> LinterReport:
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
                violations=None
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
    
    def xǁLinterEngineǁrun__mutmut_28(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_29(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_30(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_31(self, skill_path: str) -> LinterReport:
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
                passed=True,
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
    
    def xǁLinterEngineǁrun__mutmut_32(self, skill_path: str) -> LinterReport:
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
                    rule=None,
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
    
    def xǁLinterEngineǁrun__mutmut_33(self, skill_path: str) -> LinterReport:
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
                    message=None,
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
    
    def xǁLinterEngineǁrun__mutmut_34(self, skill_path: str) -> LinterReport:
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
                    severity=None
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
    
    def xǁLinterEngineǁrun__mutmut_35(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_36(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_37(self, skill_path: str) -> LinterReport:
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
    
    def xǁLinterEngineǁrun__mutmut_38(self, skill_path: str) -> LinterReport:
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
                    rule="XXread-errorXX",
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
    
    def xǁLinterEngineǁrun__mutmut_39(self, skill_path: str) -> LinterReport:
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
                    rule="READ-ERROR",
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
    
    def xǁLinterEngineǁrun__mutmut_40(self, skill_path: str) -> LinterReport:
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
                    severity="XXerrorXX"
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
    
    def xǁLinterEngineǁrun__mutmut_41(self, skill_path: str) -> LinterReport:
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
                    severity="ERROR"
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
    
    def xǁLinterEngineǁrun__mutmut_42(self, skill_path: str) -> LinterReport:
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
        line_count = None
        
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
    
    def xǁLinterEngineǁrun__mutmut_43(self, skill_path: str) -> LinterReport:
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
        all_violations = None
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
    
    def xǁLinterEngineǁrun__mutmut_44(self, skill_path: str) -> LinterReport:
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
            violations = None
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
    
    def xǁLinterEngineǁrun__mutmut_45(self, skill_path: str) -> LinterReport:
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
            violations = rule.check(None, content)
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
    
    def xǁLinterEngineǁrun__mutmut_46(self, skill_path: str) -> LinterReport:
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
            violations = rule.check(skill_path, None)
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
    
    def xǁLinterEngineǁrun__mutmut_47(self, skill_path: str) -> LinterReport:
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
            violations = rule.check(content)
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
    
    def xǁLinterEngineǁrun__mutmut_48(self, skill_path: str) -> LinterReport:
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
            violations = rule.check(skill_path, )
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
    
    def xǁLinterEngineǁrun__mutmut_49(self, skill_path: str) -> LinterReport:
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
            all_violations.extend(None)
        
        # Determine if passed
        has_errors = any(v.severity == "error" for v in all_violations)
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_50(self, skill_path: str) -> LinterReport:
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
        has_errors = None
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_51(self, skill_path: str) -> LinterReport:
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
        has_errors = any(None)
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_52(self, skill_path: str) -> LinterReport:
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
        has_errors = any(v.severity != "error" for v in all_violations)
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_53(self, skill_path: str) -> LinterReport:
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
        has_errors = any(v.severity == "XXerrorXX" for v in all_violations)
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_54(self, skill_path: str) -> LinterReport:
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
        has_errors = any(v.severity == "ERROR" for v in all_violations)
        passed = not has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_55(self, skill_path: str) -> LinterReport:
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
        passed = None
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_56(self, skill_path: str) -> LinterReport:
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
        passed = has_errors
        
        return LinterReport(
            skill_path=skill_path,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_57(self, skill_path: str) -> LinterReport:
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
            skill_path=None,
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_58(self, skill_path: str) -> LinterReport:
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
            passed=None,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_59(self, skill_path: str) -> LinterReport:
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
            violations=None,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_60(self, skill_path: str) -> LinterReport:
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
            line_count=None
        )
    
    def xǁLinterEngineǁrun__mutmut_61(self, skill_path: str) -> LinterReport:
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
            passed=passed,
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_62(self, skill_path: str) -> LinterReport:
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
            violations=all_violations,
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_63(self, skill_path: str) -> LinterReport:
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
            line_count=line_count
        )
    
    def xǁLinterEngineǁrun__mutmut_64(self, skill_path: str) -> LinterReport:
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
            )
    
    xǁLinterEngineǁrun__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLinterEngineǁrun__mutmut_1': xǁLinterEngineǁrun__mutmut_1, 
        'xǁLinterEngineǁrun__mutmut_2': xǁLinterEngineǁrun__mutmut_2, 
        'xǁLinterEngineǁrun__mutmut_3': xǁLinterEngineǁrun__mutmut_3, 
        'xǁLinterEngineǁrun__mutmut_4': xǁLinterEngineǁrun__mutmut_4, 
        'xǁLinterEngineǁrun__mutmut_5': xǁLinterEngineǁrun__mutmut_5, 
        'xǁLinterEngineǁrun__mutmut_6': xǁLinterEngineǁrun__mutmut_6, 
        'xǁLinterEngineǁrun__mutmut_7': xǁLinterEngineǁrun__mutmut_7, 
        'xǁLinterEngineǁrun__mutmut_8': xǁLinterEngineǁrun__mutmut_8, 
        'xǁLinterEngineǁrun__mutmut_9': xǁLinterEngineǁrun__mutmut_9, 
        'xǁLinterEngineǁrun__mutmut_10': xǁLinterEngineǁrun__mutmut_10, 
        'xǁLinterEngineǁrun__mutmut_11': xǁLinterEngineǁrun__mutmut_11, 
        'xǁLinterEngineǁrun__mutmut_12': xǁLinterEngineǁrun__mutmut_12, 
        'xǁLinterEngineǁrun__mutmut_13': xǁLinterEngineǁrun__mutmut_13, 
        'xǁLinterEngineǁrun__mutmut_14': xǁLinterEngineǁrun__mutmut_14, 
        'xǁLinterEngineǁrun__mutmut_15': xǁLinterEngineǁrun__mutmut_15, 
        'xǁLinterEngineǁrun__mutmut_16': xǁLinterEngineǁrun__mutmut_16, 
        'xǁLinterEngineǁrun__mutmut_17': xǁLinterEngineǁrun__mutmut_17, 
        'xǁLinterEngineǁrun__mutmut_18': xǁLinterEngineǁrun__mutmut_18, 
        'xǁLinterEngineǁrun__mutmut_19': xǁLinterEngineǁrun__mutmut_19, 
        'xǁLinterEngineǁrun__mutmut_20': xǁLinterEngineǁrun__mutmut_20, 
        'xǁLinterEngineǁrun__mutmut_21': xǁLinterEngineǁrun__mutmut_21, 
        'xǁLinterEngineǁrun__mutmut_22': xǁLinterEngineǁrun__mutmut_22, 
        'xǁLinterEngineǁrun__mutmut_23': xǁLinterEngineǁrun__mutmut_23, 
        'xǁLinterEngineǁrun__mutmut_24': xǁLinterEngineǁrun__mutmut_24, 
        'xǁLinterEngineǁrun__mutmut_25': xǁLinterEngineǁrun__mutmut_25, 
        'xǁLinterEngineǁrun__mutmut_26': xǁLinterEngineǁrun__mutmut_26, 
        'xǁLinterEngineǁrun__mutmut_27': xǁLinterEngineǁrun__mutmut_27, 
        'xǁLinterEngineǁrun__mutmut_28': xǁLinterEngineǁrun__mutmut_28, 
        'xǁLinterEngineǁrun__mutmut_29': xǁLinterEngineǁrun__mutmut_29, 
        'xǁLinterEngineǁrun__mutmut_30': xǁLinterEngineǁrun__mutmut_30, 
        'xǁLinterEngineǁrun__mutmut_31': xǁLinterEngineǁrun__mutmut_31, 
        'xǁLinterEngineǁrun__mutmut_32': xǁLinterEngineǁrun__mutmut_32, 
        'xǁLinterEngineǁrun__mutmut_33': xǁLinterEngineǁrun__mutmut_33, 
        'xǁLinterEngineǁrun__mutmut_34': xǁLinterEngineǁrun__mutmut_34, 
        'xǁLinterEngineǁrun__mutmut_35': xǁLinterEngineǁrun__mutmut_35, 
        'xǁLinterEngineǁrun__mutmut_36': xǁLinterEngineǁrun__mutmut_36, 
        'xǁLinterEngineǁrun__mutmut_37': xǁLinterEngineǁrun__mutmut_37, 
        'xǁLinterEngineǁrun__mutmut_38': xǁLinterEngineǁrun__mutmut_38, 
        'xǁLinterEngineǁrun__mutmut_39': xǁLinterEngineǁrun__mutmut_39, 
        'xǁLinterEngineǁrun__mutmut_40': xǁLinterEngineǁrun__mutmut_40, 
        'xǁLinterEngineǁrun__mutmut_41': xǁLinterEngineǁrun__mutmut_41, 
        'xǁLinterEngineǁrun__mutmut_42': xǁLinterEngineǁrun__mutmut_42, 
        'xǁLinterEngineǁrun__mutmut_43': xǁLinterEngineǁrun__mutmut_43, 
        'xǁLinterEngineǁrun__mutmut_44': xǁLinterEngineǁrun__mutmut_44, 
        'xǁLinterEngineǁrun__mutmut_45': xǁLinterEngineǁrun__mutmut_45, 
        'xǁLinterEngineǁrun__mutmut_46': xǁLinterEngineǁrun__mutmut_46, 
        'xǁLinterEngineǁrun__mutmut_47': xǁLinterEngineǁrun__mutmut_47, 
        'xǁLinterEngineǁrun__mutmut_48': xǁLinterEngineǁrun__mutmut_48, 
        'xǁLinterEngineǁrun__mutmut_49': xǁLinterEngineǁrun__mutmut_49, 
        'xǁLinterEngineǁrun__mutmut_50': xǁLinterEngineǁrun__mutmut_50, 
        'xǁLinterEngineǁrun__mutmut_51': xǁLinterEngineǁrun__mutmut_51, 
        'xǁLinterEngineǁrun__mutmut_52': xǁLinterEngineǁrun__mutmut_52, 
        'xǁLinterEngineǁrun__mutmut_53': xǁLinterEngineǁrun__mutmut_53, 
        'xǁLinterEngineǁrun__mutmut_54': xǁLinterEngineǁrun__mutmut_54, 
        'xǁLinterEngineǁrun__mutmut_55': xǁLinterEngineǁrun__mutmut_55, 
        'xǁLinterEngineǁrun__mutmut_56': xǁLinterEngineǁrun__mutmut_56, 
        'xǁLinterEngineǁrun__mutmut_57': xǁLinterEngineǁrun__mutmut_57, 
        'xǁLinterEngineǁrun__mutmut_58': xǁLinterEngineǁrun__mutmut_58, 
        'xǁLinterEngineǁrun__mutmut_59': xǁLinterEngineǁrun__mutmut_59, 
        'xǁLinterEngineǁrun__mutmut_60': xǁLinterEngineǁrun__mutmut_60, 
        'xǁLinterEngineǁrun__mutmut_61': xǁLinterEngineǁrun__mutmut_61, 
        'xǁLinterEngineǁrun__mutmut_62': xǁLinterEngineǁrun__mutmut_62, 
        'xǁLinterEngineǁrun__mutmut_63': xǁLinterEngineǁrun__mutmut_63, 
        'xǁLinterEngineǁrun__mutmut_64': xǁLinterEngineǁrun__mutmut_64
    }
    xǁLinterEngineǁrun__mutmut_orig.__name__ = 'xǁLinterEngineǁrun'
    
    def check(self, skill_path: str) -> bool:
        args = [skill_path]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁLinterEngineǁcheck__mutmut_orig'), object.__getattribute__(self, 'xǁLinterEngineǁcheck__mutmut_mutants'), args, kwargs, self)
    
    def xǁLinterEngineǁcheck__mutmut_orig(self, skill_path: str) -> bool:
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
    
    def xǁLinterEngineǁcheck__mutmut_1(self, skill_path: str) -> bool:
        """Quick check if skill file passes.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            True if passes, False otherwise
        """
        report = None
        
        if self.config.fail_on_violation:
            return report.passed
        
        # If not failing on violation, only fail on errors
        return not any(v.severity == "error" for v in report.violations)
    
    def xǁLinterEngineǁcheck__mutmut_2(self, skill_path: str) -> bool:
        """Quick check if skill file passes.
        
        Args:
            skill_path: Path to skill file
            
        Returns:
            True if passes, False otherwise
        """
        report = self.run(None)
        
        if self.config.fail_on_violation:
            return report.passed
        
        # If not failing on violation, only fail on errors
        return not any(v.severity == "error" for v in report.violations)
    
    def xǁLinterEngineǁcheck__mutmut_3(self, skill_path: str) -> bool:
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
        return any(v.severity == "error" for v in report.violations)
    
    def xǁLinterEngineǁcheck__mutmut_4(self, skill_path: str) -> bool:
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
        return not any(None)
    
    def xǁLinterEngineǁcheck__mutmut_5(self, skill_path: str) -> bool:
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
        return not any(v.severity != "error" for v in report.violations)
    
    def xǁLinterEngineǁcheck__mutmut_6(self, skill_path: str) -> bool:
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
        return not any(v.severity == "XXerrorXX" for v in report.violations)
    
    def xǁLinterEngineǁcheck__mutmut_7(self, skill_path: str) -> bool:
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
        return not any(v.severity == "ERROR" for v in report.violations)
    
    xǁLinterEngineǁcheck__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLinterEngineǁcheck__mutmut_1': xǁLinterEngineǁcheck__mutmut_1, 
        'xǁLinterEngineǁcheck__mutmut_2': xǁLinterEngineǁcheck__mutmut_2, 
        'xǁLinterEngineǁcheck__mutmut_3': xǁLinterEngineǁcheck__mutmut_3, 
        'xǁLinterEngineǁcheck__mutmut_4': xǁLinterEngineǁcheck__mutmut_4, 
        'xǁLinterEngineǁcheck__mutmut_5': xǁLinterEngineǁcheck__mutmut_5, 
        'xǁLinterEngineǁcheck__mutmut_6': xǁLinterEngineǁcheck__mutmut_6, 
        'xǁLinterEngineǁcheck__mutmut_7': xǁLinterEngineǁcheck__mutmut_7
    }
    xǁLinterEngineǁcheck__mutmut_orig.__name__ = 'xǁLinterEngineǁcheck'
