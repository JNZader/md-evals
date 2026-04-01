"""Pydantic models for Mission YAML schema and runtime results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============== Mission YAML Schema ==============


class MissionPassCriteria(BaseModel):
    """Pass criteria for a single test case.

    Supports the same evaluator types as eval.yaml (regex, exact-match,
    llm-judge) plus grader references for deterministic checks.
    """

    type: Literal["regex", "exact-match", "llm-judge", "grader"] = "regex"
    name: str = ""
    # regex / exact-match fields
    pattern: str | None = None
    expected: str | None = None
    pass_on_match: bool = True
    case_sensitive: bool = False
    # llm-judge fields
    judge_model: str | None = None
    criteria: str | None = None
    pass_threshold: float = 0.8
    # grader fields
    grader_type: str | None = None
    grader_config: dict[str, Any] = Field(default_factory=dict)


class MissionTestCase(BaseModel):
    """A single test case within a mission."""

    name: str
    description: str | None = None
    prompt: str
    variables: dict[str, str] = Field(default_factory=dict)
    pass_criteria: list[MissionPassCriteria] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class MissionConfig(BaseModel):
    """Top-level mission YAML configuration.

    Example YAML::

        name: skill-quality-regression
        version: "1.0"
        description: Weekly regression suite for coding skill
        skill_under_test: ./skills/coding/SKILL.md
        model: gpt-4o
        provider: openai
        schedule_hint: "0 0 * * 0"
        results_dir: .mission-results
        test_cases:
          - name: basic_greeting
            prompt: "Say hello"
            pass_criteria:
              - type: regex
                name: has_greeting
                pattern: "[Hh]ello"
    """

    name: str
    version: str = "1.0"
    description: str | None = None
    skill_under_test: str | None = None
    model: str = "gpt-4o"
    provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    schedule_hint: str | None = None
    results_dir: str = ".mission-results"
    test_cases: list[MissionTestCase] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


# ============== Runtime Result Models ==============


class MissionTestResult(BaseModel):
    """Result from executing a single test case."""

    test_name: str
    passed: bool
    score: float = 0.0
    criteria_results: list[dict[str, Any]] = Field(default_factory=list)
    response_content: str = ""
    duration_ms: int = 0
    error: str | None = None


class MissionSummary(BaseModel):
    """Aggregate summary of a mission run."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    duration_ms: int = 0


class MissionResult(BaseModel):
    """Complete result of a mission run."""

    mission_name: str
    version: str = "1.0"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    skill_under_test: str | None = None
    model: str = ""
    provider: str = ""
    test_results: list[MissionTestResult] = Field(default_factory=list)
    summary: MissionSummary = Field(default_factory=MissionSummary)
    tags: list[str] = Field(default_factory=list)
