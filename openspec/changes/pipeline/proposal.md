# Proposal: Phase 2 — The Pipeline

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: pipeline
> **Phase**: 2 of 5
> **Depends on**: Phase 1 (scoring-engine) — COMPLETE

---

## Intent

Replace md-evals' monolithic single-LLM evaluation with a **staged pipeline architecture** (Auditor -> Target -> Judge) where each stage can use a **different model**, and introduce a **Probe/Detector plugin system** that makes evaluation composable, extensible, and community-driven.

### Why this matters

Today, `md-evals run` sends a SKILL.md to a single LLM and asks it to simultaneously understand the skill, generate test scenarios, execute them, and judge the quality. This is like asking one person to write, perform, and critique a play. The result is:

1. **Model lock-in**: One model does everything. You can't use a cheap model for scenario generation and an analytical one for judging.
2. **Opaque evaluation**: The LLM's internal reasoning for scoring is a black box. You don't know *what* was tested or *how* it was judged.
3. **No extensibility**: Adding new evaluation criteria (security probes, compliance checks, format validation) requires modifying core evaluation code.
4. **No separation of concerns**: Scenario generation, skill execution, and quality judgment are tangled in a single prompt.

The Pipeline introduces:

- **Triple-model architecture**: Auditor (generates test scenarios), Target (follows the skill), Judge (scores the output). Each stage can use a different model optimized for its role.
- **Probes**: Pluggable scenario generators that define *what* to test (edge cases, negative paths, compliance, per-dimension quality).
- **Detectors**: Pluggable scoring components that define *how* to judge (LLM-based, regex-based, pattern-matching). Some detectors are free (no LLM calls).

### Why this is Phase 2

Phase 1 gave us the **data model** (`EvalResult`, `DimensionScore`, `PreCheckResult`, grade calculation). Phase 2 is the **execution engine** that *populates* that data model through a structured pipeline. The pipeline:

- Produces `EvalResult` (Phase 1's canonical output type) — non-negotiable
- Reuses `PreCheckEngine` as its first stage (PreCheck -> Audit -> Target -> Judge)
- Feeds pre-check findings as LLM context to the Judge (the hybrid approach)
- Populates `DimensionScore` list via Detectors mapped to rubric dimensions
- Computes grades using existing `calculate_overall_grade()` pure functions

Phase 3 (Citations) will add evidence extraction; Phase 4 (CI/Export) will consume pipeline results; Phase 5 (Analytics) will trend them. The pipeline is the bridge between data model and downstream features.

---

## Scope

### In Scope (Phase 2)

| Feature | Description |
|---------|-------------|
| **`PipelineStage` protocol** | `typing.Protocol` defining the stage contract: `async execute(context) -> StageResult` |
| **`Pipeline` orchestrator** | Chains stages sequentially, manages `EvalContext`, handles errors and timeouts |
| **`EvalContext` dataclass** | Shared mutable context flowing through stages: skill content, scenarios, responses, scores |
| **`PreCheckStage`** | Wraps existing `PreCheckEngine`, populates `EvalContext.pre_check_result` |
| **`AuditorStage`** | Uses an LLM to generate test `Scenario` objects from the parsed skill |
| **`TargetStage`** | Feeds each scenario to an LLM following the skill instructions, captures responses |
| **`JudgeStage`** | Scores target responses against skill intent, produces `DimensionScore` list |
| **`Probe` protocol** | Pluggable scenario generator: `generate_scenarios(skill) -> list[Scenario]` |
| **`Detector` protocol** | Pluggable scorer: `score(scenario, response, skill) -> DimensionScore` |
| **Built-in probes** | `DimensionProbe`, `EdgeCaseProbe`, `ComplianceProbe` |
| **Built-in detectors** | `LLMJudgeDetector`, `FormatDetector`, `SecurityDetector` |
| **`Scenario` model** | Dataclass: probe name, prompt, expected behavior, dimension, metadata |
| **`ParsedSkill` model** | Structured representation of a SKILL.md: sections, triggers, examples, rules |
| **Skill parser** | Markdown parser that extracts structure from SKILL.md into `ParsedSkill` |
| **Per-stage model routing** | Pipeline config allows different models per stage (auditor, target, judge) |
| **`LLMAdapter` multi-model** | Factory/pool that creates adapters for different model configs |
| **Pipeline YAML config** | New `pipeline:` section in `eval.yaml` or standalone `pipeline.yaml` |
| **CLI `--probe` flag** | Filter which probes run: `md-evals run --probe edge-case,compliance` |
| **CLI `--pipeline` flag** | Enable pipeline mode: `md-evals run --pipeline` (default: backward-compat single-model) |
| **Plugin discovery** | `entry_points` group `md_evals.probes` and `md_evals.detectors` for community plugins |
| **`md-evals plugins list`** | CLI command listing installed probes and detectors |
| **Backward compatibility** | `md-evals run` without `--pipeline` works exactly as today |

### Out of Scope (Phase 2)

| Excluded | Reason | Phase |
|----------|--------|-------|
| Evidence/citation extraction in `DimensionScore.evidence` | Requires structured LLM output parsing | Phase 3 |
| SARIF/JUnit export of pipeline results | Needs stable pipeline output first | Phase 4 |
| Historical trend analysis of pipeline runs | Needs persistent storage | Phase 5 |
| Parallel stage execution (fan-out) | Sequential pipeline is sufficient for V1 | Future |
| Web UI for pipeline visualization | Not MVP | Future |
| Probe/Detector marketplace | Post-roadmap | Future |
| Custom prompt templates for stages | Nice-to-have, not MVP | Future |
| Modifying existing `ExecutionResult`/`EvaluatorResult` models | Additive only | -- |

---

## Approach

### Pipeline Architecture

```
                        EvalContext (shared mutable state)
                        ┌──────────────────────────────┐
                        │ skill: ParsedSkill            │
                        │ rubric: RubricConfig          │
                        │ pre_check: PreCheckResult?    │
                        │ scenarios: list[Scenario]     │
                        │ responses: dict[id, str]      │
                        │ scores: list[DimensionScore]  │
                        │ metadata: EvalMetadata        │
                        └──────────────┬───────────────┘
                                       │
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ PreCheck  │───>│ Auditor  │───>│ Target   │───>│ Judge    │
    │  Stage    │    │  Stage   │    │  Stage   │    │  Stage   │
    │           │    │          │    │          │    │          │
    │ reuses    │    │ probes → │    │ skill +  │    │ detectors│
    │ PreCheck  │    │ scenarios│    │ scenario │    │ → scores │
    │ Engine    │    │          │    │ → resp   │    │          │
    │           │    │ model:   │    │ model:   │    │ model:   │
    │ (no LLM)  │    │ gpt-4o-  │    │ claude-  │    │ gpt-4o   │
    │           │    │ mini     │    │ sonnet   │    │          │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
         │                │                │               │
         ▼                ▼                ▼               ▼
    PreCheckResult   Scenario[]      Response[]     DimensionScore[]
                                                          │
                                                          ▼
                                                    ┌──────────┐
                                                    │ EvalResult│
                                                    │ (Phase 1) │
                                                    └──────────┘
```

### Triple-Model Strategy

Each pipeline stage has a different optimization target:

| Stage | Optimized For | Default Model | Why |
|-------|--------------|---------------|-----|
| **Auditor** | Creativity + cost | `gpt-4o-mini` | Generating scenarios is divergent thinking; cheap models suffice |
| **Target** | Instruction following | `claude-sonnet-4` | The target must faithfully follow skill instructions |
| **Judge** | Analytical reasoning | `gpt-4o` | Scoring requires careful rubric analysis |

Users override per-stage models in `eval.yaml`:

```yaml
pipeline:
  enabled: true
  auditor:
    model: gpt-4o-mini
    provider: openai
    temperature: 0.8        # higher creativity for scenario generation
    scenarios_per_probe: 3
  target:
    model: claude-sonnet-4
    provider: anthropic
    temperature: 0.3        # lower for faithful instruction following
  judge:
    model: gpt-4o
    provider: openai
    temperature: 0.0        # deterministic scoring
  probes:
    - dimension              # one probe per rubric dimension
    - edge-case
    - compliance
  detectors:
    - llm-judge              # default LLM-based scoring
    - format                 # free regex-based format check
```

### Probe/Detector Plugin Architecture

**Probes** generate test scenarios. Each probe targets a quality dimension or testing strategy:

```python
# md_evals/pipeline/probes.py

class Probe(Protocol):
    """Generates test scenarios for a specific evaluation dimension."""
    name: str

    def generate_scenarios(
        self, skill: ParsedSkill, context: EvalContext
    ) -> list[Scenario]: ...

# Built-in probes:
# - DimensionProbe: one per rubric dimension, LLM generates targeted scenarios
# - EdgeCaseProbe: generates boundary/edge case scenarios
# - ComplianceProbe: tests adherence to explicit rules in the skill
```

**Detectors** score responses. They map to rubric dimensions and produce `DimensionScore`:

```python
# md_evals/pipeline/detectors.py

class Detector(Protocol):
    """Scores a response against specific criteria."""
    name: str
    dimension: str  # maps to rubric dimension

    def score(
        self,
        scenario: Scenario,
        response: str,
        skill: ParsedSkill,
        context: EvalContext,
    ) -> DimensionScore: ...

# Built-in detectors:
# - LLMJudgeDetector: uses LLM for scoring (the default, most powerful)
# - FormatDetector: regex-based format validation (free, no LLM)
# - SecurityDetector: pattern matching for security issues (free, no LLM)
```

**Plugin discovery** uses Python `entry_points`:

```toml
# Community plugin's pyproject.toml
[project.entry-points."md_evals.probes"]
security = "md_evals_security:SecurityProbe"

[project.entry-points."md_evals.detectors"]
security = "md_evals_security:SecurityDetector"
```

### Skill Parser (`ParsedSkill`)

The pipeline needs structured access to SKILL.md content. The parser extracts:

```python
@dataclass
class ParsedSkill:
    raw_content: str            # full markdown
    title: str                  # H1 heading
    description: str            # ## Description section
    rules: list[str]            # ## Rules bullet points
    examples: list[SkillExample]  # ## Examples with input/output pairs
    triggers: list[str]         # Trigger keywords (from metadata)
    sections: dict[str, str]    # all H2 sections by heading
    metadata: dict[str, str]    # frontmatter or inline metadata
```

### Integration with Phase 1

| Phase 1 Component | Pipeline Integration |
|-------------------|---------------------|
| `EvalResult` | Pipeline's final output — assembled from detector scores + pre-check + metadata |
| `DimensionScore` | Populated by detectors, one per rubric dimension |
| `PreCheckResult` | `PreCheckStage` wraps `PreCheckEngine`, result flows into context |
| `PreCheckFinding` | Findings serialized as LLM context for the Judge stage |
| `RubricConfig` | Drives probe selection (one `DimensionProbe` per rubric dimension) and grade thresholds |
| `calculate_overall_grade()` | Called after all detectors produce scores |
| `build_dimension_scores()` | Assembles raw detector outputs into typed `DimensionScore` list |
| `score_to_grade()` | Per-dimension grading within detectors |
| `EvalMetadata` | Populated with per-stage timing, multi-model info, aggregate costs |

### New Files

| File | Purpose |
|------|---------|
| `md_evals/pipeline/__init__.py` | Package init, public API |
| `md_evals/pipeline/context.py` | `EvalContext`, `StageResult`, `Scenario`, `SkillExample` dataclasses |
| `md_evals/pipeline/protocols.py` | `PipelineStage`, `Probe`, `Detector` protocols |
| `md_evals/pipeline/pipeline.py` | `Pipeline` orchestrator class |
| `md_evals/pipeline/stages.py` | `PreCheckStage`, `AuditorStage`, `TargetStage`, `JudgeStage` |
| `md_evals/pipeline/probes.py` | Built-in probes: `DimensionProbe`, `EdgeCaseProbe`, `ComplianceProbe` |
| `md_evals/pipeline/detectors.py` | Built-in detectors: `LLMJudgeDetector`, `FormatDetector`, `SecurityDetector` |
| `md_evals/pipeline/skill_parser.py` | `SkillParser`, `ParsedSkill` model |
| `md_evals/pipeline/model_router.py` | `ModelRouter` for per-stage LLM adapter resolution |
| `md_evals/pipeline/plugins.py` | Plugin discovery via `entry_points` |
| `md_evals/pipeline/config.py` | `PipelineConfig`, `StageConfig` Pydantic models |
| `tests/test_pipeline/` | Test directory for all pipeline tests |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Multi-model cost explosion** | High | Medium | Default to single-model mode (backward compat); `gpt-4o-mini` for auditor is 10x cheaper; detectors like `FormatDetector` are free |
| **Pipeline latency** | Medium | Medium | Stages run sequentially but scenarios within a stage can be parallelized; pre-check stage is instant; provide `--timeout` per stage |
| **Prompt engineering complexity** | High | High | Ship well-tested default prompts for auditor/judge; allow user prompt overrides in Phase 3; keep prompts in separate template files for iteration |
| **Probe/Detector protocol too rigid** | Medium | Medium | Protocols (not ABCs) allow duck-typing; minimal required interface; `EvalContext` passed for maximum flexibility |
| **Plugin security** | Low | High | Plugins are Python packages installed via pip — same trust model as any dependency; no arbitrary code loading from URLs |
| **LLM output parsing failures** | High | Medium | Structured JSON output via `complete_with_json()`; fallback parsing with regex; graceful degradation (score=0 + error in metadata) |
| **Scenario quality variance** | Medium | Medium | Multiple scenarios per probe (configurable); statistical aggregation of detector scores; outlier detection in Phase 5 |
| **Backward compatibility breakage** | Low | High | Pipeline is opt-in (`--pipeline` flag); without it, existing `run` command works identically; no changes to `ExecutionResult`/`EvaluatorResult` |
| **Entry_points discovery is slow** | Low | Low | Cache discovered plugins at startup; lazy load only when pipeline mode is active |
| **ParsedSkill parser edge cases** | Medium | Medium | Graceful degradation: if parsing fails, raw content is still available; warn but don't fail |

---

## Acceptance Criteria

1. **Pipeline produces `EvalResult`**: The pipeline's final output is a valid `EvalResult` (from Phase 1) with populated `dimensions`, `overall_grade`, `overall_score`, `pre_check`, and `metadata`.

2. **Backward compatibility**: `md-evals run` without `--pipeline` works identically to the current behavior. All existing tests pass.

3. **Triple-model routing**: Each stage (auditor, target, judge) can be configured with a different model/provider. Verified by running a pipeline where auditor uses `gpt-4o-mini`, target uses `claude-sonnet-4`, and judge uses `gpt-4o`.

4. **Pre-check flows to Judge**: Pre-check findings from `PreCheckStage` are available as LLM context in the `JudgeStage` prompt, influencing scoring decisions.

5. **`PipelineStage` protocol is extensible**: A custom stage implementing the `PipelineStage` protocol can be injected into the pipeline without modifying core code.

6. **Built-in probes generate scenarios**: `DimensionProbe` generates at least 1 scenario per rubric dimension. `EdgeCaseProbe` generates edge case scenarios. `ComplianceProbe` generates rule-adherence scenarios.

7. **Built-in detectors produce scores**: `LLMJudgeDetector` returns a `DimensionScore` with score in [0.0, 1.0]. `FormatDetector` scores format dimension without LLM calls. `SecurityDetector` scores safety dimension without LLM calls.

8. **Free detectors cost nothing**: `FormatDetector` and `SecurityDetector` make zero LLM API calls.

9. **Skill parser extracts structure**: `SkillParser.parse()` extracts title, description, rules, examples, and sections from a well-formed SKILL.md.

10. **Pipeline config in YAML**: A `pipeline:` section in `eval.yaml` configures per-stage models, probe selection, and detector selection.

11. **CLI `--pipeline` flag**: `md-evals run --pipeline` activates pipeline mode. Without the flag, existing behavior is preserved.

12. **CLI `--probe` filter**: `md-evals run --pipeline --probe edge-case,compliance` runs only the specified probes.

13. **Plugin discovery**: Third-party probes/detectors installed via pip and registered with `entry_points` are discoverable by the pipeline.

14. **`md-evals plugins list`**: CLI command lists all installed probes and detectors with their source (built-in or plugin package).

15. **Graceful degradation**: If a stage fails (LLM error, parse error), the pipeline continues with reduced data and records the error in `EvalMetadata`, rather than crashing.

---

## Open Questions

1. **Should pipeline mode be the default?** Current proposal: opt-in via `--pipeline`. After stabilization (Phase 3+), consider making it the default.

2. **Scenario count per probe**: How many scenarios should each probe generate by default? Current proposal: 3, configurable via `pipeline.auditor.scenarios_per_probe`.

3. **Detector aggregation strategy**: When multiple detectors score the same dimension, how should scores combine? Current proposal: weighted average with LLM detector having higher weight than free detectors.

4. **Should the Judge see Target model info?** If the judge knows the target used Claude, it might bias scoring. Current proposal: Judge receives response only, not model metadata.

5. **Pipeline timeout strategy**: Should there be a global pipeline timeout or per-stage timeouts? Current proposal: per-stage timeouts with a global maximum.

---

## Estimated Effort

| Component | Effort |
|-----------|--------|
| Pipeline core (context, protocols, orchestrator) | 1.5 days |
| Skill parser (`ParsedSkill`) | 1 day |
| Built-in probes (3) | 1.5 days |
| Built-in detectors (3) | 1.5 days |
| Pipeline stages (4) | 2 days |
| Model routing | 0.5 days |
| CLI + config integration | 1 day |
| Plugin discovery (entry_points) | 0.5 days |
| Tests (unit + integration) | 2.5 days |
| Prompt engineering + tuning | 1.5 days |
| **Total estimated** | **~13-14 days** |
