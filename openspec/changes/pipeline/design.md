# Design: Phase 2 — The Pipeline

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: pipeline
> **Phase**: 2 of 5
> **Depends on**: Phase 1 (scoring-engine) — COMPLETE

---

## 1. Architecture Overview

### 1.1 Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI / API Layer                              │
│  md-evals run --pipeline --probe edge-case,compliance               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    PipelineRunner      │  ← new orchestrator
                    │  (replaces direct      │
                    │   ExecutionEngine for   │
                    │   pipeline mode)        │
                    └───────────┬───────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │          ModelRouter               │
              │  Creates LLMAdapter per stage      │
              │  auditor_adapter, target_adapter,   │
              │  judge_adapter                      │
              └─────────────────┬─────────────────┘
                                │
         ┌──────────────────────▼──────────────────────┐
         │              Pipeline                        │
         │  Sequential stage executor                   │
         │  Manages EvalContext lifecycle                │
         └──────────┬──────────┬──────────┬────────────┘
                    │          │          │
         ┌──────────▼┐  ┌─────▼─────┐  ┌▼──────────┐
         │ PreCheck   │  │ Auditor   │  │ Target    │
         │ Stage      │  │ Stage     │  │ Stage     │
         │            │  │           │  │           │
         │ wraps      │  │ runs      │  │ executes  │
         │ PreCheck   │  │ probes →  │  │ scenarios │
         │ Engine     │  │ scenarios │  │ with skill│
         │ (Phase 1)  │  │           │  │           │
         │ no LLM     │  │ uses      │  │ uses      │
         └────────────┘  │ auditor   │  │ target    │
                         │ adapter   │  │ adapter   │
                         └───────────┘  └───────────┘
                                              │
                                     ┌────────▼────────┐
                                     │ Judge Stage      │
                                     │                  │
                                     │ runs detectors → │
                                     │ DimensionScore[] │
                                     │                  │
                                     │ uses judge       │
                                     │ adapter          │
                                     │                  │
                                     │ produces         │
                                     │ EvalResult       │
                                     └──────────────────┘
```

### 1.2 Data Flow

```
  SkillParser                    Probes                    Target LLM
      │                            │                          │
  ParsedSkill ──────────> generate_scenarios() ────> Scenario[]
                                                       │
                                                  TargetStage
                                                       │
                                                  Response[]
                                                       │
                                                  Detectors
                                                       │
                                               DimensionScore[]
                                                       │
                                          calculate_overall_grade()
                                                       │
                                                   EvalResult
```

### 1.3 Module Dependency Graph

```
md_evals/pipeline/
├── __init__.py          → public API (Pipeline, PipelineRunner)
├── protocols.py         → PipelineStage, Probe, Detector (zero deps)
├── context.py           → EvalContext, Scenario, StageResult, StageError (depends: scoring, precheck, rubric)
├── skill_parser.py      → SkillParser, ParsedSkill, SkillExample (zero internal deps)
├── config.py            → PipelineConfig, StageConfig (depends: models for Pydantic base)
├── model_router.py      → ModelRouter (depends: llm, config)
├── probes.py            → DimensionProbe, EdgeCaseProbe, ComplianceProbe (depends: protocols, context, skill_parser)
├── detectors.py         → LLMJudgeDetector, FormatDetector, SecurityDetector (depends: protocols, context, scoring)
├── stages.py            → PreCheckStage, AuditorStage, TargetStage, JudgeStage (depends: all above)
├── pipeline.py          → Pipeline orchestrator (depends: protocols, context, stages)
├── plugins.py           → discover_probes(), discover_detectors() (depends: protocols)
└── runner.py            → PipelineRunner (top-level, depends: pipeline, config, model_router)
```

---

## 2. Architecture Decision Records

### ADR-01: Protocols, Not ABCs

**Decision**: Use `typing.Protocol` for `PipelineStage`, `Probe`, and `Detector` interfaces.

**Context**: We need extensibility for community plugins. The choice is between:
- Abstract Base Classes (ABCs) with `@abstractmethod`
- `typing.Protocol` structural subtyping

**Rationale**:
1. **Duck-typing**: Protocols enable structural subtyping — any class with the right methods satisfies the protocol, no inheritance needed. This is critical for plugins that shouldn't depend on `md-evals` internals.
2. **No import coupling**: Plugin authors don't need to import our base classes. They just implement the right shape.
3. **Python convention**: The Python ecosystem favors duck-typing. Protocols are the type-safe version of this pattern.
4. **Consistency with stdlib**: `Iterable`, `Hashable`, `Sized` are all protocols.
5. **Runtime checking**: `isinstance(obj, Protocol)` works since Python 3.12 with `runtime_checkable`.

**Trade-off**: Protocols don't provide default implementations. If we later need shared behavior (e.g., logging, retries), we'll add mix-in classes alongside protocols.

**Status**: ACCEPTED

---

### ADR-02: entry_points for Plugin Discovery

**Decision**: Use Python `importlib.metadata.entry_points()` for probe/detector plugin discovery.

**Context**: We need community extensibility without custom config files or plugin registries. Options:
1. `entry_points` (standard Python mechanism)
2. Custom `plugins.yaml` configuration file
3. Namespace packages (`md_evals_plugins.*`)
4. Explicit registration API (`register_probe(probe_class)`)

**Rationale**:
1. **Standard mechanism**: `entry_points` is the official Python way to do plugin discovery. pip, pytest, and setuptools all use it.
2. **Zero configuration**: Plugins register themselves at install time. No config files needed.
3. **Lazy loading**: `ep.load()` only imports the plugin module when called.
4. **Isolation**: Each plugin is a separate pip package with its own dependencies.
5. **Ecosystem**: Tools like `pip list`, `pipdeptree` work naturally.

**Trade-off**: Slower discovery than direct imports (~10-100ms for `entry_points()` call). Mitigated by caching and lazy loading (only in pipeline mode).

**Status**: ACCEPTED

---

### ADR-03: Async Pipeline with Sequential Stages

**Decision**: The pipeline is async (`async/await`) with stages executing sequentially. Within a stage, operations may be concurrent.

**Context**: Stages have data dependencies (Auditor produces scenarios that Target consumes). The question is whether stages themselves should run in parallel.

**Rationale**:
1. **Data dependencies**: Each stage depends on the previous stage's output. PreCheck -> Auditor -> Target -> Judge is inherently sequential.
2. **Intra-stage parallelism**: Within `TargetStage`, multiple scenarios can execute concurrently (bounded by `max_concurrent`). This gives meaningful speedup without architectural complexity.
3. **Existing pattern**: `LLMAdapter.complete()` is already async. `ExecutionEngine.run_all()` uses `asyncio.gather()`. Pipeline follows the same pattern.
4. **Simplicity**: Sequential stages with concurrent intra-stage operations is much easier to debug and reason about than a DAG execution engine.
5. **Future flexibility**: If we need parallel stages (e.g., independent probes), we can add fan-out within the existing async framework.

**Trade-off**: A fully parallel DAG executor would theoretically be faster, but the sequential dependencies between stages make this moot. The real latency bottleneck is LLM API calls, addressed by intra-stage concurrency.

**Status**: ACCEPTED

---

### ADR-04: Model Routing Strategy

**Decision**: Per-stage model configuration with fallback to global defaults. `ModelRouter` creates and caches `LLMAdapter` instances.

**Context**: The triple-model architecture needs different models for different stages. We need a clean way to configure and instantiate them.

**Rationale**:
1. **Explicit configuration**: Each stage has its own `model`, `provider`, `temperature` in the YAML. Clear and auditable.
2. **Fallback chain**: Stage config -> global defaults. If you only care about the judge model, configure just that and let others use defaults.
3. **Adapter caching**: `ModelRouter` caches `LLMAdapter` instances by `(model, provider, api_base)` key. If all three stages use the same model, only one adapter is created.
4. **Existing LLMAdapter**: We reuse the existing `LLMAdapter` class without modification. `ModelRouter` is a factory/cache layer on top.
5. **No model validation at config time**: We don't validate model availability at YAML parse time (would require API calls). Instead, validation is at execution time with clear error messages.

**Trade-off**: Users might misconfigure a model name and only discover it at runtime. Mitigated by `md-evals smoke` preflight and clear error messages with model name in the error.

**Status**: ACCEPTED

---

### ADR-05: ParsedSkill as Structured Skill Representation

**Decision**: Create a `ParsedSkill` dataclass that provides structured access to SKILL.md content, separate from raw text injection.

**Context**: The pipeline needs to:
- Generate targeted scenarios (Auditor needs to understand skill structure)
- Inject skill as system prompt (Target needs raw content)
- Evaluate against skill intent (Judge needs structured understanding)

**Rationale**:
1. **Structured access**: `ParsedSkill.rules` is much more useful than regex-ing rules from raw markdown. Probes can iterate rules directly.
2. **Graceful degradation**: If the parser can't extract a section, `raw_content` is always available as fallback. We never fail because of parsing.
3. **Separation from raw injection**: `TargetStage` still injects `raw_content` via the existing `inject_skill()` pattern. `ParsedSkill` is for the Auditor and Probes.
4. **No external dependencies**: The parser uses Python's built-in string operations and simple regex. No dependency on markdown parsing libraries.
5. **Phase 3 preparation**: Structured skill data will be essential for evidence/citation extraction.

**Trade-off**: The parser will have edge cases with unusual markdown. Mitigated by returning raw text for unparseable sections and comprehensive test fixtures.

**Status**: ACCEPTED

---

### ADR-06: Detector Score Aggregation Strategy

**Decision**: When multiple detectors score the same dimension, use weighted average with LLM-based detectors weighted at 0.7 and free detectors at 0.3.

**Context**: The `format` dimension might be scored by both `LLMJudgeDetector` (expensive, nuanced) and `FormatDetector` (free, mechanical). We need a strategy for combining them.

**Rationale**:
1. **LLM scores are richer**: LLM judges can assess nuance, context, and intent. Their scores should carry more weight.
2. **Free detectors are reliable signals**: Regex-based checks are deterministic and fast. They catch mechanical issues the LLM might overlook.
3. **Weighted average preserves both signals**: Rather than "LLM wins" or "max of both", weighted average lets free detectors influence the score meaningfully.
4. **Configurable in future**: The 0.7/0.3 weights can be made configurable in rubric.yaml in a later phase.

**Trade-off**: The 0.7/0.3 split is somewhat arbitrary. We'll tune it based on empirical results.

**Status**: ACCEPTED

---

### ADR-07: PipelineRunner vs Modifying ExecutionEngine

**Decision**: Create a new `PipelineRunner` class rather than modifying the existing `ExecutionEngine`.

**Context**: Pipeline mode needs fundamentally different orchestration than the existing treatment-based execution. Options:
1. Modify `ExecutionEngine` to support both modes
2. Create a new `PipelineRunner` alongside `ExecutionEngine`

**Rationale**:
1. **Separation of concerns**: `ExecutionEngine` handles treatment-based testing (CONTROL vs WITH_SKILL). `PipelineRunner` handles staged evaluation. Different problems, different solutions.
2. **No risk to existing code**: `ExecutionEngine` is unchanged. All existing tests pass. Zero regression risk.
3. **Clean interface**: CLI decides which runner to use based on `--pipeline` flag. The reporter receives `EvalResult` from either path.
4. **Eventual convergence**: In a future phase, `PipelineRunner` may replace `ExecutionEngine` entirely. But for now, keeping both allows gradual migration.

**Trade-off**: Two code paths for evaluation. But since they share the same output type (`EvalResult`), downstream consumers (reporter, JSON output) don't care which path produced it.

**Status**: ACCEPTED

---

## 3. Module Design

### 3.1 `md_evals/pipeline/protocols.py`

**Purpose**: Pure protocol definitions. Zero imports from md_evals internals (except type annotations).

```python
"""Pipeline protocols — structural interfaces for stages, probes, and detectors."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from md_evals.pipeline.context import EvalContext, Scenario, StageResult
    from md_evals.pipeline.skill_parser import ParsedSkill
    from md_evals.scoring import DimensionScore


@runtime_checkable
class PipelineStage(Protocol):
    @property
    def name(self) -> str: ...
    async def execute(self, context: EvalContext) -> StageResult: ...


@runtime_checkable
class Probe(Protocol):
    @property
    def name(self) -> str: ...
    def generate_scenarios(
        self, skill: ParsedSkill, context: EvalContext
    ) -> list[Scenario]: ...


@runtime_checkable
class Detector(Protocol):
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

### 3.2 `md_evals/pipeline/context.py`

**Purpose**: Shared state dataclasses. `EvalContext` is the mutable state object flowing through stages.

Key design:
- `EvalContext` is a mutable dataclass (stages write to it)
- `Scenario`, `StageResult`, `StageError` are frozen (immutable after creation)
- `EvalContext` does NOT inherit from or contain `ExecutionResult` — it's a parallel data path

### 3.3 `md_evals/pipeline/skill_parser.py`

**Purpose**: Parse SKILL.md into structured `ParsedSkill`. No external markdown library dependencies.

**Parsing strategy**:
1. Read file content as string
2. Extract H1 as `title` (first `# ` line)
3. Split by H2 headers (`## `) into sections dict
4. Extract `## Description` content as `description`
5. Extract `## Rules` bullet points as `rules: list[str]`
6. Extract `## Examples` subsections as `SkillExample` list
7. Extract YAML frontmatter (if present) as `metadata`
8. Extract `Trigger:` line (common in SKILL.md files) as `triggers`

**Error handling**: If any extraction fails, log warning and return raw text / empty list. Never raise.

### 3.4 `md_evals/pipeline/config.py`

**Purpose**: Pydantic models for pipeline configuration.

```python
class StageConfig(BaseModel):
    model: str | None = None          # None = use defaults.model
    provider: str | None = None       # None = use defaults.provider
    temperature: float | None = None  # None = use stage-specific default
    timeout: int = 60                 # seconds

class AuditorConfig(StageConfig):
    temperature: float | None = 0.8   # higher for creativity
    timeout: int = 30
    scenarios_per_probe: int = 3

class TargetConfig(StageConfig):
    max_concurrent: int = 5

class JudgeConfig(StageConfig):
    temperature: float | None = 0.0   # deterministic

class PipelineConfig(BaseModel):
    enabled: bool = False
    halt_on_precheck_error: bool = False
    auditor: AuditorConfig = Field(default_factory=AuditorConfig)
    target: TargetConfig = Field(default_factory=TargetConfig)
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    probes: list[str] = Field(default_factory=lambda: ["dimension", "edge-case", "compliance"])
    detectors: list[str] = Field(default_factory=lambda: ["llm-judge", "format", "security"])
```

### 3.5 `md_evals/pipeline/model_router.py`

**Purpose**: Factory + cache for `LLMAdapter` instances.

```python
class ModelRouter:
    def __init__(self, defaults: Defaults, pipeline_config: PipelineConfig):
        self._defaults = defaults
        self._config = pipeline_config
        self._cache: dict[tuple[str, str, str | None], LLMAdapter] = {}

    def get_adapter(self, stage: str) -> LLMAdapter:
        """Get or create an LLMAdapter for a pipeline stage."""
        stage_config = getattr(self._config, stage)
        model = stage_config.model or self._defaults.model
        provider = stage_config.provider or self._defaults.provider
        # ... cache lookup and creation
```

### 3.6 `md_evals/pipeline/probes.py`

**Purpose**: Built-in probe implementations.

- **`DimensionProbe`**: Takes a dimension name + description. Uses auditor LLM to generate targeted scenarios. One instance per rubric dimension.
- **`EdgeCaseProbe`**: Analyzes `ParsedSkill.rules` to identify boundary conditions. Uses auditor LLM to generate edge case scenarios.
- **`ComplianceProbe`**: Iterates `ParsedSkill.rules`, generates one scenario per rule to test adherence.

### 3.7 `md_evals/pipeline/detectors.py`

**Purpose**: Built-in detector implementations.

- **`LLMJudgeDetector`**: Sends (scenario, response, skill) to judge LLM with structured JSON output requesting dimension score + rationale. Universal — works for any dimension.
- **`FormatDetector`**: Checks response formatting with regex: markdown headings, code block syntax, list formatting. Scores `format` dimension. Zero LLM calls.
- **`SecurityDetector`**: Reuses security patterns from `RubricConfig.pre_check.security_patterns`. Scores `safety` dimension. Zero LLM calls.

### 3.8 `md_evals/pipeline/stages.py`

**Purpose**: Concrete stage implementations.

Each stage follows the same pattern:
1. Read from `EvalContext` (inputs)
2. Do work (possibly async LLM calls)
3. Write to `EvalContext` (outputs)
4. Return `StageResult` with timing and success status

### 3.9 `md_evals/pipeline/pipeline.py`

**Purpose**: The `Pipeline` orchestrator that chains stages.

```python
class Pipeline:
    def __init__(self, stages: list[PipelineStage]):
        self._stages = stages

    async def execute(self, context: EvalContext) -> EvalResult:
        for stage in self._stages:
            try:
                result = await asyncio.wait_for(
                    stage.execute(context),
                    timeout=self._get_timeout(stage),
                )
                if not result.success:
                    context.errors.append(StageError(...))
            except asyncio.TimeoutError:
                context.errors.append(StageError(stage_name=stage.name, error_type="timeout", ...))
            except Exception as e:
                context.errors.append(StageError(stage_name=stage.name, error_type="exception", ...))

        return self._build_eval_result(context)
```

### 3.10 `md_evals/pipeline/runner.py`

**Purpose**: Top-level entry point. Constructs Pipeline, ModelRouter, probes, detectors, and runs the full evaluation.

```python
class PipelineRunner:
    """Top-level pipeline orchestrator. Called from CLI."""

    def __init__(self, config: EvalConfig, rubric: RubricConfig, pipeline_config: PipelineConfig):
        self.config = config
        self.rubric = rubric
        self.pipeline_config = pipeline_config

    async def run(self, skill_path: str) -> EvalResult:
        # 1. Parse skill
        skill = SkillParser.parse(skill_path)

        # 2. Create model router
        router = ModelRouter(self.config.defaults, self.pipeline_config)

        # 3. Discover and instantiate probes/detectors
        probes = self._resolve_probes(skill)
        detectors = self._resolve_detectors()

        # 4. Build stages
        stages = [
            PreCheckStage(self.rubric),
            AuditorStage(router.get_adapter("auditor"), probes, self.pipeline_config.auditor),
            TargetStage(router.get_adapter("target"), self.pipeline_config.target),
            JudgeStage(router.get_adapter("judge"), detectors, self.rubric, self.pipeline_config.judge),
        ]

        # 5. Build context
        context = EvalContext(
            skill=skill,
            rubric=self.rubric,
            pipeline_config=self.pipeline_config,
            skill_path=skill_path,
        )

        # 6. Execute pipeline
        pipeline = Pipeline(stages)
        return await pipeline.execute(context)
```

### 3.11 `md_evals/pipeline/plugins.py`

**Purpose**: Plugin discovery using `importlib.metadata.entry_points()`.

Caches results after first call. Separates built-in components from plugins in the registry.

---

## 4. Integration with Existing Code

### 4.1 CLI Changes (`md_evals/cli.py`)

```python
# Additions to cli.py (additive only)

@app.command()
def run(...,
    pipeline: bool = typer.Option(False, "--pipeline", help="Enable pipeline mode"),
    no_pipeline: bool = typer.Option(False, "--no-pipeline", help="Force single-model mode"),
    probe: str | None = typer.Option(None, "--probe", help="Comma-separated probe names"),
):
    # ... existing code ...

    # Decision: pipeline or single-model
    use_pipeline = pipeline or (pipeline_config and pipeline_config.enabled and not no_pipeline)

    if use_pipeline:
        from md_evals.pipeline.runner import PipelineRunner
        runner = PipelineRunner(config_obj, rubric_config, pipeline_config)
        eval_result = asyncio.run(runner.run(skill_path))
        reporter.set_eval_result(eval_result)
    else:
        # ... existing ExecutionEngine path ...
```

### 4.2 Config Changes (`md_evals/models.py`)

Add `pipeline` field to `EvalConfig` (additive):

```python
class EvalConfig(BaseModel):
    # ... existing fields ...
    pipeline: PipelineConfig | None = None  # NEW — None = not configured
```

### 4.3 Reporter Integration

The `Reporter` already has `set_eval_result()` (from Phase 1). Both `PipelineRunner` and `ExecutionEngine` can produce `EvalResult`, so the reporter works identically for both paths.

### 4.4 No Changes Required

| File | Status |
|------|--------|
| `md_evals/scoring.py` | No changes — consumed as-is |
| `md_evals/precheck.py` | No changes — wrapped by `PreCheckStage` |
| `md_evals/rubric.py` | No changes — consumed as-is |
| `md_evals/evaluator.py` | No changes — still used in single-model path |
| `md_evals/engine.py` | No changes — still used in single-model path |
| `md_evals/llm.py` | No changes — instantiated by `ModelRouter` |
| `md_evals/metrics.py` | No changes — `EvalMetadata` references these |
| `md_evals/reporter.py` | No changes — already supports `EvalResult` |
| `md_evals/linter.py` | No changes |
| `md_evals/models.py` | One additive field: `pipeline: PipelineConfig | None` |

---

## 5. Testing Strategy

### 5.1 Unit Tests

| Module | Test Focus | Mocking Strategy |
|--------|-----------|-----------------|
| `protocols.py` | Protocol compliance verification | Create test classes implementing protocols |
| `context.py` | EvalContext construction, mutation, error recording | No mocks needed |
| `skill_parser.py` | Parse various SKILL.md formats, edge cases | File fixtures |
| `config.py` | PipelineConfig validation, defaults, YAML parsing | No mocks needed |
| `model_router.py` | Adapter caching, fallback to defaults | Mock `LLMAdapter` constructor |
| `probes.py` | Scenario generation for each probe | Mock `LLMAdapter` responses |
| `detectors.py` | Scoring for each detector | Mock `LLMAdapter` for LLMJudgeDetector; real regex for FormatDetector/SecurityDetector |
| `stages.py` | Stage execution, context mutation, error handling | Mock LLM adapters, probes, detectors |
| `pipeline.py` | Stage chaining, timeout handling, error propagation | Mock stages |
| `plugins.py` | Entry_points discovery, error handling | Mock `entry_points()` |

### 5.2 Integration Tests

| Test | Description |
|------|-------------|
| Full pipeline with mock LLM | End-to-end pipeline run with mocked LLM responses; verify `EvalResult` structure |
| Pipeline produces valid EvalResult | Assert `EvalResult` fields match Phase 1 spec; grades are valid; dimensions match rubric |
| Pre-check flows to Judge | Verify pre-check findings appear in Judge's LLM prompt |
| Backward compatibility | Run existing tests with pipeline code imported but not activated |
| CLI `--pipeline` flag | Test CLI argument parsing and pipeline activation |

### 5.3 Test Fixtures

| Fixture | Purpose |
|---------|---------|
| `tests/fixtures/skills/valid_skill.md` | Well-formed SKILL.md for happy path |
| `tests/fixtures/skills/minimal_skill.md` | SKILL.md with only H1 and one paragraph |
| `tests/fixtures/skills/complex_skill.md` | SKILL.md with frontmatter, many sections, Unicode |
| `tests/fixtures/pipeline_configs/` | Various pipeline YAML configs |
| `tests/fixtures/llm_responses/` | Canned LLM responses for mocking |

### 5.4 Test Count Estimate

| Category | Estimated Tests |
|----------|----------------|
| Protocols | 6 |
| Context | 8 |
| Skill parser | 15 |
| Config | 8 |
| Model router | 6 |
| Probes | 12 |
| Detectors | 12 |
| Stages | 16 |
| Pipeline orchestrator | 10 |
| Plugins | 6 |
| CLI integration | 8 |
| End-to-end | 5 |
| **Total** | **~112 tests** |

---

## 6. Phase 3 Preparation

The pipeline architecture is designed with Phase 3 (Citations/Evidence) in mind:

### 6.1 Evidence Hooks

`DimensionScore.evidence: list[str]` is already defined (Phase 1) but empty. Phase 3 will:
1. Add an `EvidenceExtractor` detector that parses Judge LLM output for citations
2. Populate `evidence` field with source references
3. The pipeline's `JudgeStage` will be extended (not replaced) to run evidence extraction

### 6.2 Scenario Lineage

`Scenario.metadata: dict[str, Any]` can carry lineage information:
- Which probe generated it
- Which rules/examples it was derived from
- Source line numbers in the SKILL.md

This lineage enables Phase 3 to trace evidence back to skill sections.

### 6.3 Response Annotations

`EvalContext.responses` maps scenario IDs to response strings. Phase 3 will extend this to include annotated responses with highlighted evidence spans.

---

## 7. Error Handling Philosophy

The pipeline follows a **"degrade, don't crash"** philosophy:

1. **Stage failure**: Record error in `context.errors`, continue with subsequent stages if possible.
2. **LLM parse failure**: Return score 0.0 with error in metadata. Don't skip the dimension.
3. **Plugin failure**: Log warning, skip the plugin, continue with other probes/detectors.
4. **Timeout**: Cancel the stage, record timeout error, continue.
5. **Complete failure**: If all stages fail, return `EvalResult` with grade "F" and all errors recorded.

The user always gets an `EvalResult` — even if it's a failing one with recorded errors. This is better than crashing with an unhandled exception.

---

## 8. Performance Considerations

### 8.1 Latency Budget

| Operation | Expected Latency |
|-----------|-----------------|
| Skill parsing | <10ms |
| Pre-check stage | <100ms |
| Auditor (3 probes x 3 scenarios x 1 LLM call each) | ~3-9s |
| Target (9 scenarios concurrent x 1 LLM call each) | ~5-15s (bounded by max_concurrent) |
| Judge (9 scenarios x N detectors) | ~5-15s |
| Pipeline overhead | <200ms |
| **Total (default config)** | **~15-40s** |

### 8.2 Cost Budget

| Stage | Model | Calls | Est. Cost (per run) |
|-------|-------|-------|---------------------|
| Auditor | gpt-4o-mini | 9 | ~$0.005 |
| Target | claude-sonnet-4 | 9 | ~$0.03 |
| Judge | gpt-4o | 9 | ~$0.05 |
| **Total** | | **27** | **~$0.085** |

Compared to single-model evaluation (~$0.02-0.05 for 1 LLM call), the pipeline is ~2-4x more expensive but provides:
- Structured scenarios (know what was tested)
- Separated concerns (better scoring)
- Per-dimension granularity (where the skill is weak)
- Free detectors offset cost (format + security scoring is free)
