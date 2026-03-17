# Tasks: Phase 2 — The Pipeline

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: pipeline
> **Phase**: 2 of 5
> **Total tasks**: 42
> **Estimated effort**: ~13-14 days

---

## Phase A: Pipeline Core (Foundation)

### T-01: Create pipeline package structure
- [ ] Create `md_evals/pipeline/__init__.py` with public API exports
- **Files**: `md_evals/pipeline/__init__.py`
- **Deps**: None
- **ACs**: AC-05 (EvalContext is internal)
- **Effort**: 0.25h

### T-02: Define PipelineStage protocol
- [ ] Implement `PipelineStage` protocol in `protocols.py` with `name` property and `async execute(context) -> StageResult`
- [ ] Use `@runtime_checkable` decorator
- [ ] Zero imports from md_evals internals (use `TYPE_CHECKING` guards)
- **Files**: `md_evals/pipeline/protocols.py`
- **Deps**: None
- **ACs**: REQ-S01, REQ-S02, REQ-S03, AC-19
- **Effort**: 0.5h

### T-03: Define Probe protocol
- [ ] Implement `Probe` protocol with `name` property and `generate_scenarios(skill, context) -> list[Scenario]`
- [ ] Use `@runtime_checkable` decorator
- **Files**: `md_evals/pipeline/protocols.py`
- **Deps**: T-02
- **ACs**: REQ-PR01, AC-18, AC-19
- **Effort**: 0.25h

### T-04: Define Detector protocol
- [ ] Implement `Detector` protocol with `name`, `dimension` properties and `score(scenario, response, skill, context) -> DimensionScore`
- [ ] Use `@runtime_checkable` decorator
- **Files**: `md_evals/pipeline/protocols.py`
- **Deps**: T-02
- **ACs**: REQ-D01, REQ-D05
- **Effort**: 0.25h

### T-05: Implement EvalContext and supporting dataclasses
- [ ] `EvalContext` mutable dataclass with: `skill`, `rubric`, `pipeline_config`, `skill_path`, `pre_check_result`, `scenarios`, `responses`, `scores`, `metadata`, `errors`
- [ ] `Scenario` frozen dataclass with: `id` (UUID), `probe_name`, `prompt`, `expected_behavior`, `dimension`, `metadata`
- [ ] `StageResult` frozen dataclass with: `success`, `duration_ms`, `error`, `data`
- [ ] `StageError` frozen dataclass with: `stage_name`, `error_type`, `message`, `timestamp`
- **Files**: `md_evals/pipeline/context.py`
- **Deps**: T-02 (imports Protocol types for type annotations)
- **ACs**: REQ-C01, REQ-C02, REQ-C03, REQ-C04, REQ-C05, REQ-PR02, REQ-S04
- **Effort**: 1h

### T-06: Implement Pipeline orchestrator
- [ ] `Pipeline` class that takes a list of `PipelineStage` instances
- [ ] Sequential execution with `asyncio.wait_for()` for per-stage timeouts
- [ ] Error recording in `context.errors` on failure (don't crash)
- [ ] `_build_eval_result(context)` to assemble final `EvalResult` from context
- [ ] Stage transition logging at DEBUG level
- **Files**: `md_evals/pipeline/pipeline.py`
- **Deps**: T-02, T-05
- **ACs**: REQ-P01, REQ-P02, REQ-P03, REQ-P04, REQ-P06, REQ-P07, AC-01, AC-02, AC-03, AC-04
- **Effort**: 2h

---

## Phase B: Skill Parser

### T-07: Implement ParsedSkill and SkillExample models
- [ ] `ParsedSkill` dataclass with: `raw_content`, `title`, `description`, `rules`, `examples`, `triggers`, `sections`, `metadata`
- [ ] `SkillExample` frozen dataclass with: `title`, `input`, `expected_output`
- **Files**: `md_evals/pipeline/skill_parser.py`
- **Deps**: None
- **ACs**: REQ-SP02, REQ-SP06
- **Effort**: 0.5h

### T-08: Implement SkillParser
- [ ] `SkillParser.parse(path: str) -> ParsedSkill` class method
- [ ] Extract H1 heading as `title`
- [ ] Split content by H2 headers into `sections: dict[str, str]`
- [ ] Extract `## Description` content as `description`
- [ ] Extract `## Rules` bullet points (lines starting with `- ` or `* `) as `rules: list[str]`
- [ ] Extract `## Examples` subsections (H3 headings) as `SkillExample` list
- [ ] Extract YAML frontmatter (between `---` markers) as `metadata`
- [ ] Extract `Trigger:` line as `triggers: list[str]`
- [ ] Graceful degradation: if parsing fails for a section, return raw text + log warning
- **Files**: `md_evals/pipeline/skill_parser.py`
- **Deps**: T-07
- **ACs**: REQ-SP01, REQ-SP03, REQ-SP04, REQ-SP05, REQ-SP07, AC-25, AC-26, AC-27, AC-28
- **Effort**: 3h

---

## Phase C: Probes (Scenario Generators)

### T-09: Implement DimensionProbe
- [ ] Takes a dimension name + description at construction time
- [ ] `generate_scenarios()` uses the auditor LLM to generate targeted scenarios
- [ ] Prompt includes: skill content, dimension name, dimension description, number of scenarios
- [ ] Returns `Scenario` objects with `dimension` set to the target dimension
- [ ] Configurable `scenarios_per_probe` (from `AuditorConfig`)
- **Files**: `md_evals/pipeline/probes.py`
- **Deps**: T-03, T-05, T-07
- **ACs**: REQ-PR03, AC-15
- **Effort**: 2h

### T-10: Implement EdgeCaseProbe
- [ ] Analyzes `ParsedSkill.rules` and `ParsedSkill.examples` to identify boundary conditions
- [ ] Uses auditor LLM to generate edge case scenarios (boundary values, empty inputs, max lengths)
- [ ] Scenarios are derived from the skill's specific content, not generic edge cases
- **Files**: `md_evals/pipeline/probes.py`
- **Deps**: T-03, T-05, T-07
- **ACs**: REQ-PR04, AC-16
- **Effort**: 2h

### T-11: Implement ComplianceProbe
- [ ] Iterates `ParsedSkill.rules` list
- [ ] Generates at least 1 scenario per rule
- [ ] Each scenario's `expected_behavior` references the specific rule being tested
- [ ] If rules list is empty, returns empty scenario list (no error)
- **Files**: `md_evals/pipeline/probes.py`
- **Deps**: T-03, T-05, T-07
- **ACs**: REQ-PR05, AC-17
- **Effort**: 1.5h

---

## Phase D: Detectors (Response Scorers)

### T-12: Implement LLMJudgeDetector
- [ ] Uses judge LLM to score (scenario, response) pairs
- [ ] Structured JSON prompt requesting: score (0.0-1.0), rationale, dimension
- [ ] Includes pre-check findings in prompt when available in context
- [ ] Parses JSON response, clamps score to [0.0, 1.0]
- [ ] Returns `DimensionScore` (from `md_evals/scoring.py`)
- [ ] Graceful degradation: returns score 0.0 on parse failure
- **Files**: `md_evals/pipeline/detectors.py`
- **Deps**: T-04, T-05
- **ACs**: REQ-D02, AC-20, AC-23
- **Effort**: 2.5h

### T-13: Implement FormatDetector
- [ ] Regex-based format quality scoring for the `format` dimension
- [ ] Checks: markdown headings present, code blocks use fences, lists are well-formed, consistent indentation
- [ ] Score formula: (checks_passed / total_checks) as float in [0.0, 1.0]
- [ ] Zero LLM API calls — must be verifiable by mock assertion
- [ ] Returns `DimensionScore` with `dimension="format"`
- **Files**: `md_evals/pipeline/detectors.py`
- **Deps**: T-04, T-05
- **ACs**: REQ-D03, AC-21, AC-23
- **Effort**: 1.5h

### T-14: Implement SecurityDetector
- [ ] Pattern-matching for the `safety` dimension
- [ ] Reuses security patterns from `RubricConfig.pre_check.security_patterns`
- [ ] Checks: hardcoded secrets, dangerous commands, overly permissive patterns
- [ ] Score: 1.0 if no matches, decremented per match (min 0.0)
- [ ] Zero LLM API calls — must be verifiable by mock assertion
- [ ] Returns `DimensionScore` with `dimension="safety"`
- **Files**: `md_evals/pipeline/detectors.py`
- **Deps**: T-04, T-05
- **ACs**: REQ-D04, AC-22, AC-23
- **Effort**: 1h

### T-15: Implement detector score aggregation
- [ ] When multiple detectors score the same dimension, compute weighted average
- [ ] LLM-based detectors: weight 0.7; free detectors: weight 0.3
- [ ] Produce single `DimensionScore` per dimension after aggregation
- [ ] Handle unknown dimensions (detector scores dimension not in rubric): log warning, exclude from rubric calculation
- **Files**: `md_evals/pipeline/detectors.py` (utility function)
- **Deps**: T-12, T-13, T-14
- **ACs**: REQ-J04, AC-24
- **Effort**: 1h

---

## Phase E: Pipeline Stages

### T-16: Implement PreCheckStage
- [ ] Wraps existing `PreCheckEngine` from `md_evals/precheck.py`
- [ ] Populates `context.pre_check_result` with `PreCheckResult`
- [ ] Zero LLM API calls
- [ ] If `halt_on_precheck_error` is true and pre-check fails, returns `StageResult(success=False)`
- [ ] Timing recorded in `StageResult.duration_ms`
- **Files**: `md_evals/pipeline/stages.py`
- **Deps**: T-05, T-06
- **ACs**: REQ-PC01, REQ-PC02, REQ-PC03, REQ-PC04, AC-06, AC-07
- **Effort**: 1h

### T-17: Implement AuditorStage
- [ ] Receives list of `Probe` instances and auditor `LLMAdapter`
- [ ] Iterates probes, calling `probe.generate_scenarios()` for each
- [ ] Populates `context.scenarios` with all generated scenarios
- [ ] Respects `scenarios_per_probe` configuration
- [ ] Handles probe failures: log warning, skip failing probe, continue
- [ ] Passes `EvalContext` to probes for access to rubric, config, etc.
- **Files**: `md_evals/pipeline/stages.py`
- **Deps**: T-05, T-06, T-09, T-10, T-11
- **ACs**: REQ-A01, REQ-A02, REQ-A03, REQ-A04, REQ-A05, AC-08, AC-09
- **Effort**: 1.5h

### T-18: Implement TargetStage
- [ ] For each scenario in `context.scenarios`, send prompt to target LLM with skill as system prompt
- [ ] Inject skill content as system prompt using existing `inject_skill()` pattern
- [ ] Populate `context.responses` mapping `scenario.id -> response_text`
- [ ] Support concurrent execution bounded by `max_concurrent` (use `asyncio.Semaphore`)
- [ ] Handle per-scenario failures: record empty response with error annotation
- **Files**: `md_evals/pipeline/stages.py`
- **Deps**: T-05, T-06
- **ACs**: REQ-T01, REQ-T02, REQ-T03, REQ-T04, REQ-T05, AC-10, AC-11
- **Effort**: 2h

### T-19: Implement JudgeStage
- [ ] Iterates (scenario, response) pairs from context
- [ ] Runs configured detectors on each pair
- [ ] Aggregates detector scores per dimension (T-15)
- [ ] Includes pre-check findings in LLM detector prompts (REQ-J03)
- [ ] Populates `context.scores` with final `DimensionScore` list
- [ ] Computes `overall_grade` and `overall_score` via `calculate_overall_grade()`
- [ ] Produces final `EvalResult` and stores it in `StageResult.data`
- **Files**: `md_evals/pipeline/stages.py`
- **Deps**: T-05, T-06, T-12, T-13, T-14, T-15
- **ACs**: REQ-J01, REQ-J02, REQ-J03, REQ-J04, REQ-J05, REQ-J06, REQ-J07, AC-12, AC-13, AC-14
- **Effort**: 2.5h

---

## Phase F: Model Routing

### T-20: Implement PipelineConfig Pydantic models
- [ ] `StageConfig` base model with: `model`, `provider`, `temperature`, `timeout`
- [ ] `AuditorConfig(StageConfig)` with: `scenarios_per_probe` (default 3), temperature default 0.8
- [ ] `TargetConfig(StageConfig)` with: `max_concurrent` (default 5)
- [ ] `JudgeConfig(StageConfig)` with: temperature default 0.0
- [ ] `PipelineConfig` with: `enabled`, `halt_on_precheck_error`, `auditor`, `target`, `judge`, `probes`, `detectors`
- [ ] Defaults for all fields as specified in spec section 7
- **Files**: `md_evals/pipeline/config.py`
- **Deps**: None
- **ACs**: REQ-CF02, REQ-CF03, AC-36
- **Effort**: 1h

### T-21: Implement ModelRouter
- [ ] `ModelRouter.__init__(defaults: Defaults, pipeline_config: PipelineConfig)`
- [ ] `get_adapter(stage: str) -> LLMAdapter` method
- [ ] Per-stage model resolution: stage config -> global defaults fallback
- [ ] Adapter caching: same `(model, provider, api_base)` tuple reuses instance
- [ ] Temperature passed to adapter at call time, not construction time
- **Files**: `md_evals/pipeline/model_router.py`
- **Deps**: T-20
- **ACs**: REQ-MR01, REQ-MR02, REQ-MR03, AC-29, AC-30, AC-31
- **Effort**: 1.5h

---

## Phase G: CLI + Config Integration

### T-22: Add pipeline field to EvalConfig
- [ ] Add `pipeline: PipelineConfig | None = None` field to `EvalConfig` in `md_evals/models.py`
- [ ] Ensure YAML parsing handles missing `pipeline:` section (returns None)
- [ ] Verify all existing tests pass with the additive change
- **Files**: `md_evals/models.py`
- **Deps**: T-20
- **ACs**: REQ-CF04, AC-37, AC-44
- **Effort**: 0.5h

### T-23: Add --pipeline and --no-pipeline CLI flags
- [ ] Add `--pipeline` boolean flag to `run` command
- [ ] Add `--no-pipeline` boolean flag to `run` command
- [ ] Decision logic: `--pipeline` forces pipeline mode; `--no-pipeline` forces single-model; neither: check `eval.yaml` pipeline.enabled
- [ ] When pipeline mode active: import and use `PipelineRunner`
- [ ] When single-model: use existing `ExecutionEngine` (unchanged)
- **Files**: `md_evals/cli.py`
- **Deps**: T-06, T-22, T-28 (PipelineRunner)
- **ACs**: REQ-CL01, REQ-CL03, AC-32, AC-33, AC-42, AC-43
- **Effort**: 1.5h

### T-24: Add --probe CLI flag
- [ ] Add `--probe` string flag to `run` command (comma-separated probe names)
- [ ] Parse and validate probe names against built-in + discovered plugins
- [ ] Pass filtered probe list to `PipelineRunner`
- [ ] Error with available probes list if unknown probe specified
- **Files**: `md_evals/cli.py`
- **Deps**: T-23, T-29
- **ACs**: REQ-CL02, AC-34
- **Effort**: 0.5h

### T-25: Implement `md-evals plugins list` command
- [ ] New `plugins` Typer group with `list` subcommand
- [ ] Discover all probes and detectors (built-in + plugins)
- [ ] Display formatted table: Name | Type (probe/detector) | Source (built-in/plugin-package)
- [ ] Use Rich table for formatting
- **Files**: `md_evals/cli.py`
- **Deps**: T-29
- **ACs**: REQ-CL04, AC-35
- **Effort**: 1h

---

## Phase H: Plugin Discovery

### T-26: Implement probe discovery via entry_points
- [ ] `discover_probes() -> dict[str, type]` function
- [ ] Built-in probes always in registry: `dimension`, `edge-case`, `compliance`
- [ ] Scan `md_evals.probes` entry_points group for community plugins
- [ ] Catch and log plugin load errors as warnings (don't crash)
- [ ] Cache discovered probes after first call
- **Files**: `md_evals/pipeline/plugins.py`
- **Deps**: T-09, T-10, T-11
- **ACs**: REQ-PL01, REQ-PL03, REQ-PL04, REQ-PL05, AC-38, AC-40, AC-41
- **Effort**: 1h

### T-27: Implement detector discovery via entry_points
- [ ] `discover_detectors() -> dict[str, type]` function
- [ ] Built-in detectors always in registry: `llm-judge`, `format`, `security`
- [ ] Scan `md_evals.detectors` entry_points group for community plugins
- [ ] Catch and log plugin load errors as warnings (don't crash)
- [ ] Cache discovered detectors after first call
- **Files**: `md_evals/pipeline/plugins.py`
- **Deps**: T-12, T-13, T-14
- **ACs**: REQ-PL02, REQ-PL03, REQ-PL04, REQ-PL05, AC-39, AC-40, AC-41
- **Effort**: 0.5h

---

## Phase I: Top-Level Runner + Assembly

### T-28: Implement PipelineRunner
- [ ] `PipelineRunner.__init__(config, rubric, pipeline_config)`
- [ ] `async run(skill_path: str) -> EvalResult` main method
- [ ] Parse skill via `SkillParser`
- [ ] Create `ModelRouter` from config
- [ ] Resolve probes (built-in + plugins, filtered by config)
- [ ] Instantiate `DimensionProbe` for each rubric dimension
- [ ] Resolve detectors (built-in + plugins, filtered by config)
- [ ] Build stage list: `[PreCheckStage, AuditorStage, TargetStage, JudgeStage]`
- [ ] Build `EvalContext` with skill, rubric, config
- [ ] Execute `Pipeline` and return `EvalResult`
- **Files**: `md_evals/pipeline/runner.py`
- **Deps**: T-06, T-08, T-16, T-17, T-18, T-19, T-20, T-21, T-26, T-27
- **ACs**: AC-01, AC-02, AC-05
- **Effort**: 2h

---

## Phase J: Tests

### T-29: Tests for protocols
- [ ] Verify `PipelineStage` protocol compliance with test implementation
- [ ] Verify `Probe` protocol compliance with test implementation
- [ ] Verify `Detector` protocol compliance with test implementation
- [ ] Verify duck-typing works (class without inheritance satisfies protocol)
- [ ] Verify `runtime_checkable` works with `isinstance()`
- [ ] Test invalid implementations are rejected by type checker
- **Files**: `tests/test_pipeline/test_protocols.py`
- **Deps**: T-02, T-03, T-04
- **ACs**: AC-19
- **Effort**: 1h

### T-30: Tests for EvalContext and dataclasses
- [ ] Test `EvalContext` construction with all fields
- [ ] Test `EvalContext` mutation (adding scenarios, responses, scores)
- [ ] Test `Scenario` frozen dataclass immutability
- [ ] Test `StageResult` construction
- [ ] Test `StageError` construction with timestamps
- [ ] Test `EvalContext.errors` accumulation across stages
- [ ] Test UUID generation for `Scenario.id`
- [ ] Test default values for optional fields
- **Files**: `tests/test_pipeline/test_context.py`
- **Deps**: T-05
- **Effort**: 1h

### T-31: Tests for SkillParser
- [ ] Parse well-formed SKILL.md with all sections (SC-22)
- [ ] Parse SKILL.md with missing Rules section (SC-23)
- [ ] Parse SKILL.md with YAML frontmatter (SC-24)
- [ ] Parse SKILL.md with only H1 heading (minimal)
- [ ] Parse empty SKILL.md (0 bytes) (EC-01)
- [ ] Parse SKILL.md with Unicode/emoji content (EC-15)
- [ ] Parse SKILL.md with multiple H2 sections
- [ ] Extract bullet points from Rules section
- [ ] Extract examples with H3 subsections
- [ ] Graceful degradation on malformed markdown
- [ ] Test with real SKILL.md fixtures from the skill ecosystem
- [ ] Verify `raw_content` always contains full file content
- [ ] Verify `sections` dict has correct heading -> content mapping
- [ ] Test file-not-found error handling
- [ ] Test file with only whitespace
- **Files**: `tests/test_pipeline/test_skill_parser.py`, `tests/fixtures/skills/*.md`
- **Deps**: T-07, T-08
- **Effort**: 2.5h

### T-32: Tests for PipelineConfig
- [ ] Parse complete pipeline YAML config
- [ ] Parse config with missing sections (defaults apply)
- [ ] Parse config with `pipeline.enabled: false`
- [ ] Parse config with no `pipeline:` section at all (None)
- [ ] Validate stage-specific defaults (auditor temp 0.8, judge temp 0.0)
- [ ] Validate probe/detector name lists
- [ ] Test `eval.yaml` backward compatibility (no pipeline section)
- [ ] Parse config with per-stage model overrides
- **Files**: `tests/test_pipeline/test_config.py`, `tests/fixtures/pipeline_configs/*.yaml`
- **Deps**: T-20, T-22
- **Effort**: 1h

### T-33: Tests for ModelRouter
- [ ] Return different adapters for different stage configs
- [ ] Fallback to defaults when stage model is None
- [ ] Cache: same config returns same adapter instance
- [ ] Temperature is set per-stage
- [ ] All three stages use defaults when no overrides
- [ ] Mixed: some stages override, some use defaults
- **Files**: `tests/test_pipeline/test_model_router.py`
- **Deps**: T-21
- **Effort**: 1h

### T-34: Tests for Probes
- [ ] `DimensionProbe` generates scenarios with correct dimension (SC-06)
- [ ] `DimensionProbe` respects `scenarios_per_probe` count
- [ ] `EdgeCaseProbe` generates boundary scenarios from rules (SC-07)
- [ ] `EdgeCaseProbe` handles empty rules list
- [ ] `ComplianceProbe` generates 1+ scenario per rule (SC-08)
- [ ] `ComplianceProbe` handles 0 rules gracefully (EC-02)
- [ ] All probes return valid `Scenario` objects with UUIDs
- [ ] Probes handle LLM errors gracefully
- [ ] Mock LLM responses for deterministic testing
- [ ] Test probe with complex multi-rule skill
- [ ] Test probe with minimal skill (only title)
- [ ] Verify probes receive correct `EvalContext`
- **Files**: `tests/test_pipeline/test_probes.py`
- **Deps**: T-09, T-10, T-11
- **Effort**: 2h

### T-35: Tests for Detectors
- [ ] `LLMJudgeDetector` returns `DimensionScore` with valid score (SC-11)
- [ ] `LLMJudgeDetector` clamps out-of-range scores (EC-05)
- [ ] `LLMJudgeDetector` handles JSON parse failure gracefully (EC-04)
- [ ] `LLMJudgeDetector` includes pre-check findings in prompt (SC-25)
- [ ] `FormatDetector` makes zero LLM calls (SC-12, verified by mock)
- [ ] `FormatDetector` scores well-formatted text higher than poorly formatted
- [ ] `SecurityDetector` makes zero LLM calls (SC-13, verified by mock)
- [ ] `SecurityDetector` detects hardcoded secrets (score < 1.0)
- [ ] `SecurityDetector` returns 1.0 for clean content
- [ ] Detector aggregation: weighted average of multiple detectors (SC-14)
- [ ] Detector returns score for unknown dimension (EC-10)
- [ ] All detectors return `DimensionScore` (not custom types)
- **Files**: `tests/test_pipeline/test_detectors.py`
- **Deps**: T-12, T-13, T-14, T-15
- **Effort**: 2h

### T-36: Tests for Pipeline Stages
- [ ] `PreCheckStage` wraps `PreCheckEngine` correctly (AC-06)
- [ ] `PreCheckStage` populates `context.pre_check_result`
- [ ] `PreCheckStage` makes zero LLM calls (AC-07)
- [ ] `PreCheckStage` halt mode: returns failure on pre-check error (SC-03)
- [ ] `PreCheckStage` continue mode: returns success even with errors (SC-04)
- [ ] `AuditorStage` runs all configured probes
- [ ] `AuditorStage` populates `context.scenarios`
- [ ] `AuditorStage` handles probe failure gracefully
- [ ] `TargetStage` executes scenarios with skill as system prompt
- [ ] `TargetStage` populates `context.responses` keyed by scenario ID
- [ ] `TargetStage` handles concurrent execution
- [ ] `TargetStage` handles failed scenario execution (EC-11)
- [ ] `JudgeStage` runs detectors on (scenario, response) pairs
- [ ] `JudgeStage` produces `DimensionScore` list
- [ ] `JudgeStage` calls `calculate_overall_grade()`
- [ ] `JudgeStage` includes pre-check in LLM prompt (SC-25)
- **Files**: `tests/test_pipeline/test_stages.py`
- **Deps**: T-16, T-17, T-18, T-19
- **Effort**: 2.5h

### T-37: Tests for Pipeline orchestrator
- [ ] Full pipeline happy path with mock stages (SC-01)
- [ ] Pipeline with stage failure mid-execution (SC-05)
- [ ] Pipeline with stage timeout (EC-12)
- [ ] Pipeline records errors in `context.errors`
- [ ] Pipeline produces `EvalResult` even on total failure (EC-06)
- [ ] Pipeline produces grade "F" when all stages fail
- [ ] Pipeline timing: stages execute sequentially
- [ ] Pipeline with single model for all stages (EC-13)
- [ ] Pipeline with empty scenario list (EC-03)
- [ ] Pipeline returns valid `EvalResult` matching Phase 1 spec
- **Files**: `tests/test_pipeline/test_pipeline.py`
- **Deps**: T-06
- **Effort**: 2h

### T-38: Tests for Plugin Discovery
- [ ] Built-in probes always available
- [ ] Built-in detectors always available
- [ ] Entry_points discovery finds mock plugin
- [ ] Plugin load failure logged as warning
- [ ] Plugin load failure doesn't crash pipeline
- [ ] `md-evals plugins list` shows built-in + installed
- **Files**: `tests/test_pipeline/test_plugins.py`
- **Deps**: T-26, T-27
- **Effort**: 1h

### T-39: Tests for CLI integration
- [ ] `--pipeline` flag activates pipeline mode (SC-19)
- [ ] `--no-pipeline` flag forces single-model mode (SC-20)
- [ ] `--probe edge-case` filters probes (SC-10)
- [ ] `--probe nonexistent` shows error with available list (EC-14)
- [ ] `md-evals plugins list` output format (SC-21)
- [ ] `md-evals run` without `--pipeline` works as before
- [ ] `eval.yaml` with `pipeline.enabled: true` auto-activates pipeline
- [ ] `eval.yaml` without `pipeline:` section works as before
- **Files**: `tests/test_pipeline/test_cli_integration.py`
- **Deps**: T-23, T-24, T-25
- **Effort**: 1.5h

### T-40: End-to-end integration tests
- [ ] Full pipeline run with mock LLM (SC-01 end-to-end)
- [ ] Verify `EvalResult` structure matches Phase 1 spec
- [ ] Verify pre-check findings flow to Judge prompt (SC-25)
- [ ] Verify backward compatibility: existing `run` produces same output
- [ ] Verify `--pipeline` + `--output json` includes `eval_result` in JSON
- **Files**: `tests/test_pipeline/test_e2e.py`
- **Deps**: T-28
- **Effort**: 2h

---

## Phase K: Verify + Polish

### T-41: Backward compatibility verification
- [ ] Run ALL existing tests (`pytest tests/ -x`) — must pass with zero failures
- [ ] Verify `md-evals run` (no pipeline) produces identical output
- [ ] Verify `md-evals check` still works
- [ ] Verify `md-evals lint` still works
- [ ] Verify `md-evals smoke` still works
- [ ] Diff `md_evals/models.py` — only change is additive `pipeline` field
- [ ] No modifications to: `scoring.py`, `precheck.py`, `rubric.py`, `evaluator.py`, `engine.py`, `llm.py`, `metrics.py`, `linter.py`
- **Files**: All existing test files
- **Deps**: T-22, T-23
- **ACs**: AC-42, AC-43, AC-44, AC-45
- **Effort**: 1h

### T-42: Documentation and examples
- [ ] Update `eval.yaml` scaffold (`md-evals init`) to include commented-out pipeline section
- [ ] Create example `eval_with_pipeline.yaml` in `examples/`
- [ ] Update CLI help text for new flags
- [ ] Add docstrings to all public classes and methods in `md_evals/pipeline/`
- **Files**: `md_evals/cli.py`, `examples/eval_with_pipeline.yaml`
- **Deps**: T-28, T-41
- **Effort**: 1.5h

---

## Task Dependency Graph

```
T-01 ────────────────────────────────────────────────────────
T-02 ─┬─ T-03 ──────────── T-09, T-10, T-11 ──── T-26 ──┐
       ├─ T-04 ──────────── T-12, T-13, T-14 ──── T-27 ──┤
       └─ T-05 ─── T-06 ─── T-16 ───────────────────────── │
                                                             │
T-07 ─── T-08 ────────────── (feeds T-09..T-11)             │
                                                             │
T-20 ─── T-21 ────────────── (feeds T-28)                   │
       └─ T-22 ─── T-23 ─── T-24, T-25                     │
                                                             │
T-15 ──── T-19 ──────────── (feeds T-28)                    │
T-17, T-18 ─────────────── (feeds T-28)                     │
                                                             │
T-28 ──── T-40, T-41, T-42                                  │
                                                             │
T-29..T-39 (tests — parallel, after respective modules)  ◄──┘
```

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | **42** |
| **Total ACs verified** | **45** |
| **Total requirements covered** | **58** |
| **Total edge cases covered** | **15** |
| **Total scenarios covered** | **25** |
| **Estimated new tests** | **~112** |
| **New Python files** | **12** (pipeline package) |
| **Modified files** | **2** (`models.py` additive, `cli.py` additive) |
| **Unmodified existing files** | **10** (scoring, precheck, rubric, evaluator, engine, llm, metrics, linter, reporter, config) |
| **Estimated effort** | **~13-14 days** |

### Phase Execution Order (can partially parallelize)

| Wave | Tasks | Parallelizable? |
|------|-------|-----------------|
| Wave 1 | T-01 through T-05 (core + protocols + context) | Yes |
| Wave 2 | T-06 (pipeline), T-07..T-08 (parser), T-20 (config) | Yes |
| Wave 3 | T-09..T-11 (probes), T-12..T-15 (detectors), T-21 (router) | Yes |
| Wave 4 | T-16..T-19 (stages) | Partially (T-16 independent) |
| Wave 5 | T-22..T-28 (CLI + plugins + runner) | Partially |
| Wave 6 | T-29..T-40 (tests) | Yes (all parallel) |
| Wave 7 | T-41..T-42 (verify + polish) | Sequential |
