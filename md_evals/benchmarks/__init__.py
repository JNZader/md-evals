"""SDD quality benchmark suite.

Evaluates the quality of SDD artifacts (proposals, specs, designs, tasks)
using scoring rubrics and cascade evaluation. Provides sample data with
known-good outputs for regression testing.
"""

from md_evals.benchmarks.sdd_benchmark import (
    SDDArtifactType,
    SDDBenchmarkCase,
    SDDBenchmarkResult,
    SDDBenchmarkSuite,
    SDDRubric,
    get_sample_cases,
    get_rubric,
)

__all__ = [
    "SDDArtifactType",
    "SDDBenchmarkCase",
    "SDDBenchmarkResult",
    "SDDBenchmarkSuite",
    "SDDRubric",
    "get_sample_cases",
    "get_rubric",
]
