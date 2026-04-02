"""Deterministic graders for agent task evaluation.

Graders check side effects (files, commands, state) after task execution,
complementing the existing regex / LLM-judge evaluators that inspect
LLM output text.

Three-phase graders extend this system for structured evaluation:
- Structure: JSON validation, required fields, type checking
- Analysis: keyword coverage, section coverage, minimum length
- Generation: output matching, constraint checking
"""

from md_evals.graders.base import Grader
from md_evals.graders.file_graders import (
    FileContentGrader,
    FileExistsGrader,
    FileSizeGrader,
)
from md_evals.graders.command_grader import CommandGrader
from md_evals.graders.state_grader import StateGrader
from md_evals.graders.structure_grader import (
    JSONValidGrader,
    RequiredFieldsGrader,
    FieldTypeGrader,
)
from md_evals.graders.analysis_grader import (
    KeywordCoverageGrader,
    SectionCoverageGrader,
    MinLengthGrader,
)
from md_evals.graders.generation_grader import (
    OutputMatchGrader,
    ConstraintGrader,
)
from md_evals.graders.contract_grader import (
    OutputContract,
    ContractAssertionGrader,
    ABContractGrader,
)
from md_evals.graders.code_ref_grader import CodeRefGrader
from md_evals.graders.sql_grader import SQLGrader

__all__ = [
    "Grader",
    # Original graders
    "FileExistsGrader",
    "FileContentGrader",
    "FileSizeGrader",
    "CommandGrader",
    "StateGrader",
    # Structure phase
    "JSONValidGrader",
    "RequiredFieldsGrader",
    "FieldTypeGrader",
    # Analysis phase
    "KeywordCoverageGrader",
    "SectionCoverageGrader",
    "MinLengthGrader",
    # Generation phase
    "OutputMatchGrader",
    "ConstraintGrader",
    # Contract assertions
    "OutputContract",
    "ContractAssertionGrader",
    "ABContractGrader",
    # Code reference validation
    "CodeRefGrader",
    # SQL execution validation
    "SQLGrader",
]
