"""Pydantic models for eval.yaml schemas."""

from typing import Literal, Any
from pydantic import BaseModel, Field


# ============== Core Configuration ==============


class Defaults(BaseModel):
    """Default configuration values."""
    model: str = "gpt-4o"
    provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


class TreatmentEnv(BaseModel):
    """Environment variables for treatment."""
    pass  # Allows arbitrary key-value pairs


class Treatment(BaseModel):
    """Treatment definition."""
    description: str | None = None
    skill_path: str | None = None
    env: dict[str, str] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Model configuration."""
    name: str
    provider: str
    api_base: str | None = None
    api_key: str | None = None


# ============== Linter Configuration ==============


class LinterRule(BaseModel):
    """Linter rule configuration."""
    type: str
    limit: int | None = None
    sections: list[str] | None = None


class LinterConfig(BaseModel):
    """Linter configuration."""
    max_lines: int = 400
    fail_on_violation: bool = True
    rules: list[LinterRule] = Field(default_factory=list)


# ============== Output Configuration ==============


class OutputConfig(BaseModel):
    """Output configuration."""
    format: Literal["table", "json", "markdown"] = "table"
    save_results: bool = True
    results_dir: str = "./results"
    verbose: bool = False


# ============== Execution Configuration ==============


class ExecutionConfig(BaseModel):
    """Execution configuration."""
    parallel_workers: int = 1
    repetitions: int = 1
    fail_fast: bool = False


# ============== Evaluator Configuration ==============


class RegexEvaluator(BaseModel):
    """Regex evaluator configuration."""
    type: Literal["regex"] = "regex"
    name: str
    pattern: str
    pass_on_match: bool = True
    fail_message: str | None = None


class ExactMatchEvaluator(BaseModel):
    """Exact match evaluator configuration."""
    type: Literal["exact-match"] = "exact-match"
    name: str
    expected: str
    case_sensitive: bool = False


class LLMJudgeEvaluator(BaseModel):
    """LLM Judge evaluator configuration."""
    type: Literal["llm-judge"] = "llm-judge"
    name: str
    judge_model: str
    criteria: str
    output_schema: dict[str, Any] = Field(default_factory=dict)
    pass_threshold: float = 0.8
    pass


# Union type for all evaluators
Evaluator = RegexEvaluator | ExactMatchEvaluator | LLMJudgeEvaluator


# ============== Task Configuration ==============


class Task(BaseModel):
    """Test task configuration."""
    name: str
    description: str | None = None
    prompt: str
    variables: dict[str, str] = Field(default_factory=dict)
    evaluators: list[Evaluator] = Field(default_factory=list)


# ============== Top-Level Configuration ==============


class EvalConfig(BaseModel):
    """Top-level evaluation configuration."""
    name: str
    version: str = "1.0"
    description: str | None = None
    defaults: Defaults = Field(default_factory=Defaults)
    treatments: dict[str, Treatment] = Field(default_factory=dict)
    models: list[ModelConfig] = Field(default_factory=list)
    lint: LinterConfig = Field(default_factory=LinterConfig)
    tests: list[Task] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)


# ============== Runtime Models ==============


class LLMResponse(BaseModel):
    """LLM response model."""
    content: str
    model: str
    provider: str
    tokens: int = 0
    duration_ms: int = 0
    raw_response: dict[str, Any] = Field(default_factory=dict)


class EvaluatorResult(BaseModel):
    """Evaluator result."""
    evaluator_name: str
    passed: bool
    score: float = 0.0
    reason: str | None = None
    details: dict[str, Any] | None = None


class ExecutionResult(BaseModel):
    """Execution result for a single run."""
    treatment: str
    test: str
    prompt: str
    response: LLMResponse
    passed: bool
    evaluator_results: list[EvaluatorResult]
    timestamp: str


# ============== Linter Models ==============


class LinterViolation(BaseModel):
    """Linter violation."""
    rule: str
    message: str
    line: int | None = None
    severity: Literal["error", "warning"] = "error"


class LinterReport(BaseModel):
    """Linter report."""
    skill_path: str
    passed: bool
    violations: list[LinterViolation] = Field(default_factory=list)
    line_count: int = 0
