# Spec: Phase 2 — The Pipeline

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: pipeline
> **Phase**: 2 of 5
> **Depends on**: Phase 1 (scoring-engine) — COMPLETE

---

## 1. Overview

This spec defines the requirements for the md-evals Pipeline: a staged evaluation architecture that replaces monolithic LLM evaluation with composable stages (PreCheck -> Auditor -> Target -> Judge), pluggable Probes and Detectors, and per-stage model routing.

The pipeline MUST produce `EvalResult` (from `md_evals/scoring.py`) as its canonical output.

---

## 2. Requirements

### 2.1 Pipeline Core

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-P01 | The pipeline SHALL execute stages sequentially in a defined order: PreCheck -> Auditor -> Target -> Judge | MUST |
| REQ-P02 | The pipeline SHALL use `EvalContext` as shared mutable state passed between stages | MUST |
| REQ-P03 | The pipeline SHALL produce a single `EvalResult` as its final output | MUST |
| REQ-P04 | The pipeline SHALL support graceful degradation: if a stage fails, subsequent stages receive partial context and the pipeline records errors rather than crashing | MUST |
| REQ-P05 | The pipeline SHALL support per-stage timeouts configurable in YAML | SHOULD |
| REQ-P06 | The pipeline SHALL be fully async (`async/await`) | MUST |
| REQ-P07 | The pipeline SHALL log stage transitions with timing at DEBUG level | SHOULD |

### 2.2 EvalContext

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-C01 | `EvalContext` SHALL contain: `skill: ParsedSkill`, `rubric: RubricConfig`, `pipeline_config: PipelineConfig` | MUST |
| REQ-C02 | `EvalContext` SHALL contain mutable fields: `pre_check_result: PreCheckResult | None`, `scenarios: list[Scenario]`, `responses: dict[str, str]`, `scores: list[DimensionScore]` | MUST |
| REQ-C03 | `EvalContext` SHALL contain `metadata: EvalMetadata` with per-stage timing populated incrementally | MUST |
| REQ-C04 | `EvalContext` SHALL contain `errors: list[StageError]` for recording per-stage failures | MUST |
| REQ-C05 | `EvalContext` SHALL be a mutable `@dataclass` (not frozen) since stages mutate it | MUST |

### 2.3 PipelineStage Protocol

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-S01 | `PipelineStage` SHALL be a `typing.Protocol` (not ABC) to allow duck-typing | MUST |
| REQ-S02 | `PipelineStage` SHALL define `name: str` property | MUST |
| REQ-S03 | `PipelineStage` SHALL define `async execute(self, context: EvalContext) -> StageResult` | MUST |
| REQ-S04 | `StageResult` SHALL contain: `success: bool`, `duration_ms: int`, `error: str | None` | MUST |
| REQ-S05 | Stages SHALL NOT modify `context.skill` or `context.rubric` (read-only inputs) | MUST |

### 2.4 PreCheckStage

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-PC01 | `PreCheckStage` SHALL delegate to the existing `PreCheckEngine` from `md_evals/precheck.py` | MUST |
| REQ-PC02 | `PreCheckStage` SHALL populate `context.pre_check_result` with the `PreCheckResult` | MUST |
| REQ-PC03 | `PreCheckStage` SHALL NOT make any LLM API calls | MUST |
| REQ-PC04 | If pre-check fails with errors and `pipeline.halt_on_precheck_error` is true, subsequent stages SHALL be skipped and the pipeline returns an `EvalResult` with grade "F" | SHOULD |

### 2.5 AuditorStage

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-A01 | `AuditorStage` SHALL use configured probes to generate `Scenario` objects | MUST |
| REQ-A02 | `AuditorStage` SHALL use the auditor-stage LLM model (may differ from target/judge) | MUST |
| REQ-A03 | `AuditorStage` SHALL populate `context.scenarios` with generated scenarios | MUST |
| REQ-A04 | `AuditorStage` SHALL generate at least 1 scenario per active probe | MUST |
| REQ-A05 | The number of scenarios per probe SHALL be configurable via `pipeline.auditor.scenarios_per_probe` (default: 3) | SHOULD |

### 2.6 TargetStage

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-T01 | `TargetStage` SHALL execute each scenario by sending it to the target LLM with the skill injected as system prompt | MUST |
| REQ-T02 | `TargetStage` SHALL populate `context.responses` mapping scenario IDs to LLM response strings | MUST |
| REQ-T03 | `TargetStage` SHALL use the target-stage LLM model | MUST |
| REQ-T04 | `TargetStage` SHALL support concurrent scenario execution (bounded by `pipeline.target.max_concurrent`, default: 5) | SHOULD |
| REQ-T05 | If a scenario execution fails, `TargetStage` SHALL record an empty response with an error annotation, not skip the scenario | MUST |

### 2.7 JudgeStage

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-J01 | `JudgeStage` SHALL use configured detectors to score each (scenario, response) pair | MUST |
| REQ-J02 | `JudgeStage` SHALL use the judge-stage LLM model for LLM-based detectors | MUST |
| REQ-J03 | `JudgeStage` SHALL include pre-check findings in the LLM judge prompt when available | MUST |
| REQ-J04 | `JudgeStage` SHALL aggregate detector scores per dimension (when multiple detectors score the same dimension) using weighted average | MUST |
| REQ-J05 | `JudgeStage` SHALL populate `context.scores` with final `DimensionScore` list | MUST |
| REQ-J06 | `JudgeStage` SHALL compute `overall_grade` and `overall_score` using `calculate_overall_grade()` from `md_evals/scoring.py` | MUST |
| REQ-J07 | `JudgeStage` SHALL produce the final `EvalResult` and return it as part of `StageResult` | MUST |

### 2.8 Probe Protocol

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-PR01 | `Probe` SHALL be a `typing.Protocol` with `name: str` and `generate_scenarios(skill, context) -> list[Scenario]` | MUST |
| REQ-PR02 | `Scenario` SHALL contain: `id: str` (UUID), `probe_name: str`, `prompt: str`, `expected_behavior: str`, `dimension: str | None`, `metadata: dict[str, Any]` | MUST |
| REQ-PR03 | `DimensionProbe` SHALL generate scenarios targeting a specific rubric dimension | MUST |
| REQ-PR04 | `EdgeCaseProbe` SHALL generate boundary/edge case scenarios derived from the skill's rules and examples | MUST |
| REQ-PR05 | `ComplianceProbe` SHALL generate scenarios testing adherence to explicit rules listed in the skill | MUST |
| REQ-PR06 | Probes MAY use an LLM (via the auditor model) or be purely deterministic | MUST |

### 2.9 Detector Protocol

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-D01 | `Detector` SHALL be a `typing.Protocol` with `name: str`, `dimension: str`, and `score(scenario, response, skill, context) -> DimensionScore` | MUST |
| REQ-D02 | `LLMJudgeDetector` SHALL use the judge LLM to score responses with structured JSON output | MUST |
| REQ-D03 | `FormatDetector` SHALL score the `format` dimension using regex patterns, making zero LLM calls | MUST |
| REQ-D04 | `SecurityDetector` SHALL score the `safety` dimension using pattern matching from the rubric's security patterns, making zero LLM calls | MUST |
| REQ-D05 | Detectors SHALL return `DimensionScore` (from `md_evals/scoring.py`) — not a custom type | MUST |
| REQ-D06 | Free detectors (no LLM) SHALL be clearly identifiable via a `requires_llm: bool` property | SHOULD |

### 2.10 Skill Parser

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-SP01 | `SkillParser.parse(path)` SHALL return a `ParsedSkill` from a SKILL.md file | MUST |
| REQ-SP02 | `ParsedSkill` SHALL contain: `raw_content`, `title`, `description`, `rules`, `examples`, `triggers`, `sections`, `metadata` | MUST |
| REQ-SP03 | The parser SHALL extract H2 sections (`## Section Name`) into `sections: dict[str, str]` | MUST |
| REQ-SP04 | The parser SHALL extract bullet-point rules from `## Rules` section into `rules: list[str]` | MUST |
| REQ-SP05 | The parser SHALL extract examples from `## Examples` section into `examples: list[SkillExample]` | SHOULD |
| REQ-SP06 | `SkillExample` SHALL contain: `title: str`, `input: str`, `expected_output: str` | SHOULD |
| REQ-SP07 | If parsing fails for a section, the parser SHALL return the section as raw text and log a warning, not raise an exception | MUST |

### 2.11 Model Routing

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-MR01 | `ModelRouter` SHALL create and cache `LLMAdapter` instances per stage configuration | MUST |
| REQ-MR02 | Each stage SHALL receive its own `LLMAdapter` configured with the stage's model/provider/temperature | MUST |
| REQ-MR03 | If no per-stage model is configured, the stage SHALL fall back to the global `defaults.model` | MUST |
| REQ-MR04 | `ModelRouter` SHALL validate that all configured models are accessible before pipeline execution starts | SHOULD |

### 2.12 Pipeline Configuration

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-CF01 | Pipeline configuration SHALL be defined in a `pipeline:` section of `eval.yaml` | MUST |
| REQ-CF02 | `PipelineConfig` SHALL be a Pydantic model with: `enabled: bool`, `auditor: StageConfig`, `target: StageConfig`, `judge: StageConfig`, `probes: list[str]`, `detectors: list[str]` | MUST |
| REQ-CF03 | `StageConfig` SHALL contain: `model: str | None`, `provider: str | None`, `temperature: float | None`, `timeout: int` (seconds), plus stage-specific fields | MUST |
| REQ-CF04 | If `pipeline.enabled` is `false` or absent, `md-evals run` SHALL use the existing single-model evaluation path | MUST |
| REQ-CF05 | Probe and detector names in config SHALL be resolved against built-in names first, then `entry_points` plugins | MUST |

### 2.13 CLI Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-CL01 | `md-evals run --pipeline` SHALL activate pipeline mode regardless of YAML config | MUST |
| REQ-CL02 | `md-evals run --probe edge-case,compliance` SHALL filter active probes | MUST |
| REQ-CL03 | `md-evals run --no-pipeline` SHALL force single-model mode regardless of YAML config | MUST |
| REQ-CL04 | `md-evals plugins list` SHALL list all installed probes and detectors with source (built-in / plugin) | MUST |
| REQ-CL05 | All existing CLI commands SHALL continue to work unchanged | MUST |

### 2.14 Plugin Discovery

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-PL01 | Probes SHALL be discoverable via the `md_evals.probes` entry_points group | MUST |
| REQ-PL02 | Detectors SHALL be discoverable via the `md_evals.detectors` entry_points group | MUST |
| REQ-PL03 | Built-in probes/detectors SHALL always be available regardless of entry_points | MUST |
| REQ-PL04 | Plugin discovery SHALL be lazy (only when pipeline mode is active) | SHOULD |
| REQ-PL05 | Plugin load errors SHALL be logged as warnings, not crash the pipeline | MUST |

---

## 3. Scenarios

### 3.1 Pipeline Core Scenarios

**SC-01: Happy path — full pipeline run**
- Given: A valid SKILL.md, default rubric, pipeline config with all 3 stage models
- When: `md-evals run --pipeline` is executed
- Then: Pipeline runs PreCheck -> Auditor -> Target -> Judge
- And: Returns an `EvalResult` with populated dimensions, overall grade, and pre-check result
- And: `EvalMetadata` contains per-stage timing information

**SC-02: Pipeline with single model (no per-stage config)**
- Given: Pipeline enabled but no per-stage models configured
- When: Pipeline executes
- Then: All stages use `defaults.model` from `eval.yaml`
- And: Result is equivalent to single-model mode but with pipeline structure

**SC-03: Pipeline with pre-check failure (halt mode)**
- Given: A SKILL.md with error-level pre-check findings
- And: `pipeline.halt_on_precheck_error: true`
- When: Pipeline executes
- Then: PreCheckStage returns failure
- And: Auditor, Target, Judge stages are skipped
- And: EvalResult has `overall_grade: "F"` and populated `pre_check` field

**SC-04: Pipeline with pre-check failure (continue mode)**
- Given: A SKILL.md with error-level pre-check findings
- And: `pipeline.halt_on_precheck_error: false` (default)
- When: Pipeline executes
- Then: All stages run; pre-check findings flow to Judge as LLM context
- And: Judge may reduce scores based on pre-check issues

**SC-05: Pipeline stage failure mid-execution**
- Given: AuditorStage fails (LLM timeout)
- When: Pipeline continues
- Then: TargetStage receives empty scenarios list
- And: JudgeStage receives no responses to score
- And: EvalResult has `errors` recorded, `overall_grade: "F"`

### 3.2 Probe Scenarios

**SC-06: DimensionProbe generates targeted scenarios**
- Given: A rubric with dimensions: correctness, completeness, format
- When: `DimensionProbe("correctness")` generates scenarios
- Then: Returns 3 scenarios (default) specifically targeting correctness quality
- And: Each scenario has `dimension: "correctness"`

**SC-07: EdgeCaseProbe generates boundary scenarios**
- Given: A SKILL.md with rules about "maximum 3 items" and "must handle empty input"
- When: `EdgeCaseProbe` generates scenarios
- Then: Returns scenarios testing boundary values: 0, 1, 3, 4 items
- And: Scenarios are derived from the skill's rules, not generic

**SC-08: ComplianceProbe generates rule-adherence tests**
- Given: A SKILL.md with 5 bullet-point rules in the Rules section
- When: `ComplianceProbe` generates scenarios
- Then: Returns at least one scenario per rule
- And: Each scenario's `expected_behavior` references the specific rule being tested

**SC-09: Custom probe via plugin**
- Given: A third-party package `md-evals-security-probes` installed with entry_point
- When: Pipeline discovers probes
- Then: `SecurityProbe` from the plugin is available alongside built-in probes

**SC-10: Probe filter via CLI**
- Given: `md-evals run --pipeline --probe edge-case`
- When: AuditorStage runs
- Then: Only `EdgeCaseProbe` generates scenarios; `DimensionProbe` and `ComplianceProbe` are skipped

### 3.3 Detector Scenarios

**SC-11: LLMJudgeDetector scores with structured output**
- Given: A scenario with response text
- When: `LLMJudgeDetector` scores it
- Then: Sends a structured prompt to the judge LLM requesting JSON output
- And: Returns `DimensionScore` with score in [0.0, 1.0] and appropriate grade
- And: The LLM prompt includes pre-check findings if available

**SC-12: FormatDetector scores without LLM**
- Given: A response text
- When: `FormatDetector` scores it
- Then: Uses regex patterns to check formatting quality (headings, code blocks, lists)
- And: Returns `DimensionScore` for the `format` dimension
- And: Makes exactly 0 LLM API calls

**SC-13: SecurityDetector scores without LLM**
- Given: A response text with hardcoded API keys
- When: `SecurityDetector` scores it
- Then: Pattern matching detects the security issue
- And: Returns `DimensionScore` for `safety` with reduced score
- And: Makes exactly 0 LLM API calls

**SC-14: Multiple detectors on same dimension — aggregation**
- Given: Both `LLMJudgeDetector` and `FormatDetector` score the `format` dimension
- When: JudgeStage aggregates scores
- Then: Weighted average is computed (LLM weight: 0.7, free detector weight: 0.3)
- And: A single `DimensionScore` is produced for `format`

**SC-15: Detector returns score for unknown dimension**
- Given: A detector returns a `DimensionScore` for dimension "creativity" which is not in the rubric
- When: JudgeStage processes scores
- Then: The score is logged as a warning and excluded from the rubric-weighted calculation
- And: It is available in extended metadata for inspection

### 3.4 Model Routing Scenarios

**SC-16: Per-stage model configuration**
- Given: Pipeline config with `auditor.model: gpt-4o-mini`, `target.model: claude-sonnet-4`, `judge.model: gpt-4o`
- When: Pipeline executes
- Then: AuditorStage uses gpt-4o-mini, TargetStage uses claude-sonnet-4, JudgeStage uses gpt-4o
- And: `EvalMetadata` records all three models used

**SC-17: Fallback to default model**
- Given: Pipeline config with `auditor.model: null` (not configured)
- When: AuditorStage needs an LLM
- Then: Uses `defaults.model` from `eval.yaml`

**SC-18: Per-stage temperature override**
- Given: `auditor.temperature: 0.8`, `judge.temperature: 0.0`
- When: Stages execute LLM calls
- Then: Auditor calls use temperature 0.8, Judge calls use temperature 0.0

### 3.5 CLI Scenarios

**SC-19: Pipeline mode via CLI flag**
- Given: `eval.yaml` does NOT have `pipeline.enabled: true`
- When: `md-evals run --pipeline` is executed
- Then: Pipeline mode is activated with default pipeline config
- And: ProbeS use defaults: `[dimension, edge-case, compliance]`

**SC-20: Single-model mode override**
- Given: `eval.yaml` HAS `pipeline.enabled: true`
- When: `md-evals run --no-pipeline` is executed
- Then: Existing single-model evaluation runs; pipeline is bypassed

**SC-21: Plugins list command**
- Given: md-evals installed with `md-evals-security-probes` plugin
- When: `md-evals plugins list`
- Then: Output shows:
  ```
  Probes:
    [built-in] dimension
    [built-in] edge-case
    [built-in] compliance
    [plugin: md-evals-security-probes] security

  Detectors:
    [built-in] llm-judge
    [built-in] format
    [built-in] security
  ```

### 3.6 Skill Parser Scenarios

**SC-22: Parse well-formed SKILL.md**
- Given: A SKILL.md with Description, Rules (5 bullets), Examples (3), and Trigger metadata
- When: `SkillParser.parse("SKILL.md")`
- Then: Returns `ParsedSkill` with:
  - `title`: H1 heading content
  - `rules`: 5-item list
  - `examples`: 3 `SkillExample` objects
  - `sections`: dict with all H2 headings as keys

**SC-23: Parse SKILL.md with missing sections**
- Given: A SKILL.md with Description but NO Rules section
- When: `SkillParser.parse("SKILL.md")`
- Then: `rules` is an empty list
- And: `sections` dict does not contain "Rules" key
- And: No exception is raised

**SC-24: Parse SKILL.md with frontmatter**
- Given: A SKILL.md with YAML frontmatter containing `trigger:` keywords
- When: `SkillParser.parse("SKILL.md")`
- Then: `triggers` list is populated from frontmatter
- And: `metadata` dict contains frontmatter key-value pairs

### 3.7 Integration Scenarios

**SC-25: Pre-check findings in Judge context**
- Given: PreCheckStage found 2 warnings (long lines, missing section)
- When: JudgeStage builds the LLM prompt
- Then: The prompt includes a "Pre-Check Findings" section with the 2 warnings
- And: Judge can reference these findings in scoring rationale

---

## 4. Acceptance Criteria

### 4.1 Pipeline Core

| AC | Criterion |
|----|-----------|
| AC-01 | Pipeline produces a valid `EvalResult` with all fields populated (skill_path, overall_grade, overall_score, dimensions, pre_check, metadata) |
| AC-02 | Pipeline stages execute in order: PreCheck -> Auditor -> Target -> Judge, verified by stage timing in `EvalMetadata` |
| AC-03 | Pipeline is fully async: all stage `execute()` methods are `async def` |
| AC-04 | Pipeline handles stage failure: if AuditorStage raises, pipeline records error and produces EvalResult with grade "F" |
| AC-05 | `EvalContext` is not accessible outside the pipeline — it is an internal implementation detail |

### 4.2 Stages

| AC | Criterion |
|----|-----------|
| AC-06 | `PreCheckStage` delegates to `PreCheckEngine` (no duplication of pre-check logic) |
| AC-07 | `PreCheckStage` makes zero LLM API calls |
| AC-08 | `AuditorStage` generates scenarios using configured probes |
| AC-09 | `AuditorStage` respects `scenarios_per_probe` configuration |
| AC-10 | `TargetStage` executes each scenario with the skill as system prompt |
| AC-11 | `TargetStage` populates `context.responses` keyed by scenario ID |
| AC-12 | `JudgeStage` uses detectors to produce one `DimensionScore` per rubric dimension |
| AC-13 | `JudgeStage` includes pre-check findings in LLM judge prompt |
| AC-14 | `JudgeStage` calls `calculate_overall_grade()` to compute final grade |

### 4.3 Probes

| AC | Criterion |
|----|-----------|
| AC-15 | `DimensionProbe` generates at least 1 scenario per target dimension |
| AC-16 | `EdgeCaseProbe` generates scenarios derived from skill rules (not generic) |
| AC-17 | `ComplianceProbe` generates at least 1 scenario per extracted rule |
| AC-18 | Probe protocol has exactly 2 required members: `name` and `generate_scenarios()` |
| AC-19 | A class implementing `Probe` protocol without inheriting works correctly (duck-typing) |

### 4.4 Detectors

| AC | Criterion |
|----|-----------|
| AC-20 | `LLMJudgeDetector.score()` returns `DimensionScore` with score in [0.0, 1.0] |
| AC-21 | `FormatDetector.score()` makes zero LLM calls, verified by mock assertion |
| AC-22 | `SecurityDetector.score()` makes zero LLM calls, verified by mock assertion |
| AC-23 | All detectors return `DimensionScore` (from `md_evals/scoring.py`), not custom types |
| AC-24 | When multiple detectors score same dimension, weighted average is computed correctly |

### 4.5 Skill Parser

| AC | Criterion |
|----|-----------|
| AC-25 | `SkillParser.parse()` returns `ParsedSkill` with at least `title`, `description`, `rules`, `sections` |
| AC-26 | Parser handles SKILL.md files with 0-7 H2 sections without errors |
| AC-27 | Parser extracts bullet points from Rules section into `rules: list[str]` |
| AC-28 | Parser gracefully handles malformed markdown (returns raw text for unparseable sections) |

### 4.6 Model Routing

| AC | Criterion |
|----|-----------|
| AC-29 | `ModelRouter` returns different `LLMAdapter` instances for auditor/target/judge when configured |
| AC-30 | `ModelRouter` falls back to `defaults.model` when stage model is not configured |
| AC-31 | `LLMAdapter` instances are cached (same config -> same instance) |

### 4.7 CLI & Config

| AC | Criterion |
|----|-----------|
| AC-32 | `--pipeline` flag activates pipeline mode |
| AC-33 | `--no-pipeline` flag forces single-model mode |
| AC-34 | `--probe` flag filters active probes |
| AC-35 | `md-evals plugins list` shows built-in and installed plugins |
| AC-36 | `eval.yaml` with `pipeline:` section parses into `PipelineConfig` |
| AC-37 | `eval.yaml` without `pipeline:` section works as today (backward compat) |

### 4.8 Plugin Discovery

| AC | Criterion |
|----|-----------|
| AC-38 | Probes registered via `md_evals.probes` entry_points are discoverable |
| AC-39 | Detectors registered via `md_evals.detectors` entry_points are discoverable |
| AC-40 | Built-in probes/detectors are always available even if no plugins installed |
| AC-41 | Plugin load failure is logged as warning, does not crash pipeline |

### 4.9 Backward Compatibility

| AC | Criterion |
|----|-----------|
| AC-42 | All existing CLI commands work unchanged |
| AC-43 | `md-evals run` without `--pipeline` produces identical output to current version |
| AC-44 | `ExecutionResult`, `EvaluatorResult`, `LLMResponse`, `EvalConfig` are NOT modified |
| AC-45 | All existing tests pass without modification |

---

## 5. Edge Cases

| ID | Edge Case | Expected Behavior |
|----|-----------|-------------------|
| EC-01 | SKILL.md is empty (0 bytes) | `SkillParser.parse()` returns `ParsedSkill` with empty fields; PreCheckStage reports "empty file" error; pipeline produces grade "F" |
| EC-02 | SKILL.md has no Rules section | `ParsedSkill.rules` is empty list; `ComplianceProbe` generates 0 scenarios; pipeline continues with other probes |
| EC-03 | All probes generate 0 scenarios | TargetStage has nothing to execute; JudgeStage has nothing to score; EvalResult has empty dimensions and grade "F" with error message |
| EC-04 | LLM returns invalid JSON from auditor | `AuditorStage` catches parse error, logs warning, returns empty scenario list; pipeline continues with degraded data |
| EC-05 | LLM returns score outside [0.0, 1.0] | Detector clamps score to [0.0, 1.0] (using existing `max(0.0, min(1.0, score))` pattern from `scoring.py`) |
| EC-06 | All LLM calls fail (network down) | Pipeline records errors for each stage; EvalResult has grade "F" with `errors` populated; exit code indicates failure |
| EC-07 | Rubric has 1 dimension only | Pipeline works with 1 dimension; `DimensionProbe` generates scenarios for that 1 dimension; grade calculation works normally |
| EC-08 | Rubric has custom (non-builtin) dimensions | `DimensionProbe` generates scenarios for custom dimensions using the dimension's description as guidance |
| EC-09 | Plugin probe raises unhandled exception | Plugin error is caught, logged, skipped; other probes continue; pipeline does not crash |
| EC-10 | Detector returns score for dimension not in rubric | Score is excluded from rubric-weighted calculation; logged as warning; available in extended metadata |
| EC-11 | Target model is unavailable (wrong API key) | TargetStage fails; responses are empty; Judge scores all as 0.0; pipeline completes with grade "F" |
| EC-12 | Pipeline timeout exceeded | Pipeline orchestrator cancels running stages; returns partial EvalResult with recorded timeout error |
| EC-13 | Same model configured for all 3 stages | Works correctly; `ModelRouter` may reuse same adapter instance; functionally equivalent to single-model pipeline |
| EC-14 | `--probe` specifies non-existent probe name | CLI prints error listing available probes; exits with code 1 |
| EC-15 | SKILL.md contains Unicode/emoji content | Parser handles Unicode correctly; scenarios and responses preserve encoding |

---

## 6. Protocol & Interface Specifications

### 6.1 PipelineStage Protocol

```python
from typing import Protocol

class PipelineStage(Protocol):
    """Contract for pipeline stages."""

    @property
    def name(self) -> str: ...

    async def execute(self, context: EvalContext) -> StageResult: ...
```

### 6.2 Probe Protocol

```python
class Probe(Protocol):
    """Contract for scenario generators."""

    @property
    def name(self) -> str: ...

    def generate_scenarios(
        self, skill: ParsedSkill, context: EvalContext
    ) -> list[Scenario]: ...
```

### 6.3 Detector Protocol

```python
class Detector(Protocol):
    """Contract for response scorers."""

    @property
    def name(self) -> str: ...

    @property
    def dimension(self) -> str: ...

    def score(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> DimensionScore: ...
```

### 6.4 Key Dataclasses

```python
@dataclass
class EvalContext:
    skill: ParsedSkill
    rubric: RubricConfig
    pipeline_config: PipelineConfig
    skill_path: str
    # Mutable fields populated by stages
    pre_check_result: PreCheckResult | None = None
    scenarios: list[Scenario] = field(default_factory=list)
    responses: dict[str, str] = field(default_factory=dict)
    scores: list[DimensionScore] = field(default_factory=list)
    metadata: EvalMetadata = field(default_factory=lambda: EvalMetadata(model="", provider=""))
    errors: list[StageError] = field(default_factory=list)

@dataclass(frozen=True)
class Scenario:
    id: str                      # UUID
    probe_name: str              # which probe generated this
    prompt: str                  # the test prompt to send to target
    expected_behavior: str       # what good output looks like
    dimension: str | None        # target rubric dimension, or None for general
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class StageResult:
    success: bool
    duration_ms: int
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)  # stage-specific output

@dataclass(frozen=True)
class StageError:
    stage_name: str
    error_type: str              # "timeout", "llm_error", "parse_error", etc.
    message: str
    timestamp: str               # ISO 8601

@dataclass
class ParsedSkill:
    raw_content: str
    title: str
    description: str
    rules: list[str]
    examples: list[SkillExample]
    triggers: list[str]
    sections: dict[str, str]     # H2 heading -> section content
    metadata: dict[str, str]     # frontmatter key-value pairs

@dataclass(frozen=True)
class SkillExample:
    title: str
    input: str
    expected_output: str
```

---

## 7. Pipeline Config YAML Format

```yaml
# eval.yaml — pipeline section
pipeline:
  enabled: true
  halt_on_precheck_error: false    # default: false (continue with warnings)

  auditor:
    model: gpt-4o-mini
    provider: openai
    temperature: 0.8
    timeout: 30                     # seconds
    scenarios_per_probe: 3

  target:
    model: claude-sonnet-4
    provider: anthropic
    temperature: 0.3
    timeout: 60
    max_concurrent: 5               # parallel scenario execution

  judge:
    model: gpt-4o
    provider: openai
    temperature: 0.0
    timeout: 60

  probes:                           # list of active probe names
    - dimension                     # built-in: one per rubric dimension
    - edge-case                     # built-in: boundary testing
    - compliance                    # built-in: rule adherence

  detectors:                        # list of active detector names
    - llm-judge                     # built-in: LLM-based scoring
    - format                        # built-in: regex format check (free)
    - security                      # built-in: pattern matching (free)
```

### Defaults when pipeline is enabled but sections omitted:

| Field | Default |
|-------|---------|
| `auditor.model` | `defaults.model` |
| `auditor.temperature` | `0.8` |
| `auditor.timeout` | `30` |
| `auditor.scenarios_per_probe` | `3` |
| `target.model` | `defaults.model` |
| `target.temperature` | `defaults.temperature` |
| `target.timeout` | `60` |
| `target.max_concurrent` | `5` |
| `judge.model` | `defaults.model` |
| `judge.temperature` | `0.0` |
| `judge.timeout` | `60` |
| `probes` | `["dimension", "edge-case", "compliance"]` |
| `detectors` | `["llm-judge", "format", "security"]` |

---

## 8. Plugin Discovery via entry_points

### Registration

```toml
# Third-party pyproject.toml
[project.entry-points."md_evals.probes"]
security = "md_evals_security.probes:SecurityProbe"
pentesting = "md_evals_security.probes:PentestProbe"

[project.entry-points."md_evals.detectors"]
security-deep = "md_evals_security.detectors:DeepSecurityDetector"
```

### Discovery

```python
# md_evals/pipeline/plugins.py
from importlib.metadata import entry_points

def discover_probes() -> dict[str, type]:
    """Discover all probes: built-in + entry_points."""
    probes = {
        "dimension": DimensionProbe,
        "edge-case": EdgeCaseProbe,
        "compliance": ComplianceProbe,
    }
    for ep in entry_points(group="md_evals.probes"):
        try:
            probes[ep.name] = ep.load()
        except Exception as e:
            logger.warning("Failed to load probe plugin '%s': %s", ep.name, e)
    return probes

def discover_detectors() -> dict[str, type]:
    """Discover all detectors: built-in + entry_points."""
    detectors = {
        "llm-judge": LLMJudgeDetector,
        "format": FormatDetector,
        "security": SecurityDetector,
    }
    for ep in entry_points(group="md_evals.detectors"):
        try:
            detectors[ep.name] = ep.load()
        except Exception as e:
            logger.warning("Failed to load detector plugin '%s': %s", ep.name, e)
    return detectors
```

---

## 9. Pre-Check Findings as Judge Context

When the JudgeStage builds the LLM prompt, it includes pre-check findings:

```
## Pre-Check Findings
The following issues were detected in the SKILL.md before LLM evaluation:
- [WARNING] Line 87 exceeds 200 characters
- [WARNING] Missing recommended section: Examples
- [ERROR] Hardcoded secret detected (line 42)

Consider these findings when scoring the safety and format dimensions.
```

This allows the Judge to factor in structural/security issues discovered by the deterministic pre-check, creating a hybrid approach where cheap deterministic checks inform expensive LLM analysis.

---

## 10. Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| NFR-01 | Pipeline execution for a single SKILL.md SHALL complete within 5 minutes with default configuration |
| NFR-02 | Pre-check stage SHALL complete within 100ms (no LLM calls) |
| NFR-03 | Free detectors (Format, Security) SHALL complete within 50ms each |
| NFR-04 | Plugin discovery SHALL complete within 500ms |
| NFR-05 | Pipeline overhead (excluding LLM calls) SHALL be under 200ms |
| NFR-06 | Memory usage SHALL not exceed 100MB for pipeline state (excluding LLM response content) |
