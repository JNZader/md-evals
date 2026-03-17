# Design: Phase 1 — The Scoring Engine

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: scoring-engine
> **Phase**: 1 of 5
> **Proposal**: [proposal.md](./proposal.md)
> **Spec**: [spec.md](./spec.md)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Architecture Decision Records](#2-architecture-decision-records)
3. [Module Design](#3-module-design)
4. [Integration Points](#4-integration-points)
5. [Testing Strategy](#5-testing-strategy)
6. [Phase 2 Preparation](#6-phase-2-preparation)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

Phase 1 adds three new modules to the `md_evals/` package. They are **leaf nodes** in the dependency graph — existing modules do not import them. Only the integration points (`cli.py`, `reporter.py`, server routes) gain new imports.

```
                        ┌─────────────────────────────────────────────┐
                        │              SKILL.md (input)                │
                        └──────────────────┬──────────────────────────┘
                                           │
                                           ▼
                        ┌──────────────────────────────────────────────┐
                        │           rubric.py (RubricLoader)           │
                        │  ┌────────────────────────────────────────┐  │
                        │  │ RubricConfig (Pydantic)                │  │
                        │  │  - DimensionConfig[]                   │  │
                        │  │  - GradeThresholds                    │  │
                        │  │  - PreCheckConfig                     │  │
                        │  └────────────────────────────────────────┘  │
                        └──────────┬───────────────────┬───────────────┘
                                   │                   │
                          ┌────────▼─────────┐  ┌──────▼──────────────┐
                          │   precheck.py     │  │    scoring.py       │
                          │  PreCheckEngine   │  │  DimensionScore     │
                          │  ┌─────────────┐  │  │  EvalResult         │
                          │  │LinterEngine │  │  │  EvalMetadata       │
                          │  │(composed)   │  │  │  calculate_overall  │
                          │  └─────────────┘  │  │  _grade()           │
                          │  SecurityChecks   │  │  score_to_grade()   │
                          └────────┬──────────┘  └──────┬─────────────┘
                                   │                    │
                                   ▼                    ▼
                        ┌──────────────────────────────────────────────┐
                        │                EvalResult                     │
                        │  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
                        │  │PreCheck  │ │Dimension │ │EvalMetadata  │ │
                        │  │Result    │ │Score[]   │ │(wraps Cost/  │ │
                        │  └──────────┘ └──────────┘ │ ContextMetr.)│ │
                        │                            └──────────────┘ │
                        └──────────────────┬───────────────────────────┘
                                           │
                     ┌─────────────────────┼──────────────────────┐
                     │                     │                      │
                     ▼                     ▼                      ▼
              ┌─────────────┐    ┌──────────────────┐    ┌───────────────┐
              │  cli.py     │    │  reporter.py      │    │ server/routes │
              │  (check cmd)│    │  (eval_result     │    │ (expand=      │
              │  (run flags)│    │   method)         │    │  scoring)     │
              └─────────────┘    └──────────────────┘    └───────────────┘
```

### 1.2 Data Flow

```
SKILL.md
  │
  ├──[1]──▶ RubricLoader.resolve(cli_rubric)
  │            └──▶ RubricConfig (loaded, validated)
  │
  ├──[2]──▶ PreCheckEngine(rubric).run(skill_path)
  │            ├── LinterEngine.run()  → LinterReport → mapped to PreCheckFinding[]
  │            ├── SecurityPatternChecks → PreCheckFinding[]
  │            └──▶ PreCheckResult { passed, findings[], checks_run, duration_ms }
  │
  ├──[3]──▶ (Phase 1: mock dimension scores OR derive from existing EvaluatorResult.score)
  │            └──▶ DimensionScore[] (7 dimensions with scores, weights, grades)
  │
  ├──[4]──▶ calculate_overall_grade(dimensions, thresholds)
  │            └──▶ (overall_score: float, overall_grade: str)
  │
  └──[5]──▶ EvalResult { skill_path, overall_grade, overall_score,
                          dimensions, pre_check, metadata, execution_results }
               │
               ├──▶ CLI output (terminal table + grade badge)
               ├──▶ JSON report (eval_result key)
               ├──▶ API response (expand=scoring)
               └──▶ Web UI (DimensionRadar + GradeBadge)
```

### 1.3 Import Graph (New → Existing Dependencies)

```
md_evals/rubric.py
  └── pydantic (BaseModel, Field)           # Same pattern as md_evals/models.py
  └── re                                     # Regex compilation for security patterns
  └── pathlib.Path                           # File resolution
  └── yaml                                   # YAML parsing (same as config.py)

md_evals/scoring.py
  └── md_evals.metrics.CostMetrics           # Referenced by EvalMetadata
  └── md_evals.metrics.ContextMetrics        # Referenced by EvalMetadata
  └── dataclasses (dataclass, field)         # Same pattern as metrics.py

md_evals/precheck.py
  └── md_evals.linter.LinterEngine           # Composed inside PreCheckEngine
  └── md_evals.linter.LinterConfig           # For configuring linter (from models.py → re-exported)
  └── md_evals.models.LinterConfig           # Actual import source
  └── md_evals.rubric.RubricConfig           # PreCheckConfig accessed via rubric
  └── dataclasses (dataclass, field)         # For PreCheckFinding, PreCheckResult
  └── re                                     # Compiled security patterns
  └── time                                   # For duration_ms measurement

md_evals/cli.py (MODIFIED — new imports only)
  └── md_evals.precheck.PreCheckEngine       # NEW
  └── md_evals.rubric.RubricLoader           # NEW
  └── md_evals.rubric.RubricValidationError  # NEW
  └── md_evals.rubric.RubricNotFoundError    # NEW

md_evals/reporter.py (MODIFIED — new imports only)
  └── md_evals.scoring.EvalResult            # NEW
  └── md_evals.scoring.DimensionScore        # NEW
```

**Circular dependency analysis**: No cycles. The new modules form a DAG:
- `rubric.py` imports only from stdlib + pydantic + yaml (no md_evals imports)
- `scoring.py` imports only from `md_evals.metrics` (which has no md_evals imports itself)
- `precheck.py` imports from `md_evals.linter`, `md_evals.models`, and `md_evals.rubric`
- None of the existing modules (`models.py`, `metrics.py`, `linter.py`, `config.py`, `engine.py`, `evaluator.py`) are modified to import from new modules

---

## 2. Architecture Decision Records

### ADR-01: stdlib `@dataclass` for Scoring Types (not Pydantic)

**Context**: The new types `DimensionScore`, `PreCheckFinding`, `PreCheckResult`, `EvalMetadata`, and `EvalResult` need a home. The project uses Pydantic `BaseModel` for config/API schemas (`md_evals/models.py`, `apps/server/app/models/schemas.py`) and stdlib `@dataclass` for internal computation objects (`md_evals/metrics.py`).

**Decision**: Use stdlib `@dataclass` for all scoring types.

**Rationale**:
1. **Precedent**: `md_evals/metrics.py` already establishes this pattern. Its module docstring explicitly states: *"All dataclasses use stdlib @dataclass (not Pydantic) per ADR-03, since these are internal computation objects, not API models."* The scoring types are internal computation objects.
2. **Performance**: `@dataclass` construction is 5-10x faster than Pydantic `BaseModel` construction. Grade calculation may run thousands of times in batch scenarios.
3. **Simplicity**: Scoring types don't need Pydantic's validation, serialization, or JSON schema generation — those concerns belong to the API layer (`apps/server/app/models/schemas.py`) which has separate Pydantic response models.
4. **Frozen immutability**: `@dataclass(frozen=True)` provides true immutability with `FrozenInstanceError`. Pydantic's `model_config = ConfigDict(frozen=True)` adds overhead.
5. **Interop**: `dataclasses.asdict()` works out of the box for JSON serialization in the reporter, same as `metrics.py` uses.

**Alternatives considered**:
- Pydantic BaseModel: Adds unnecessary validation overhead for types that are constructed programmatically (not from external input).
- NamedTuple: Lacks default values (`evidence: list[str] = field(default_factory=list)`) and mutation (`EvalMetadata` is mutable because it's built incrementally).
- attrs: Not in the project's dependency tree.

**Consequences**:
- API response schemas in `apps/server/app/models/schemas.py` will be separate Pydantic models that mirror the dataclass shapes (same pattern used for cost/context metrics today).
- Serialization in `reporter.py` uses `dataclasses.asdict()`.

---

### ADR-02: PreCheckEngine Wraps LinterEngine via Composition

**Context**: The existing `LinterEngine` (`md_evals/linter.py`) validates SKILL.md files against structural rules (`EmptyFileRule`, `MaxLinesRule`, `VeryLongLineRule`, `RequiredSectionsRule`). The new `PreCheckEngine` needs these same checks plus security anti-pattern detection.

**Decision**: `PreCheckEngine` **composes** `LinterEngine` — it instantiates a `LinterEngine` internally and delegates to it, then maps `LinterViolation` to `PreCheckFinding`.

**Rationale**:
1. **No duplication**: The spec (PC-02, AC-25) explicitly requires *"no rule duplication"*. Composition reuses the four existing rules without reimplementing them.
2. **No modification**: `LinterEngine` and `linter.py` remain completely unchanged (backward compat guarantee AC-43). Neither inheritance nor monkey-patching touches the existing code.
3. **Clean mapping**: `LinterViolation` and `PreCheckFinding` are structurally similar but semantically different. The mapping is a simple 1:1 translation:
   ```python
   PreCheckFinding(
       check=violation.rule,        # "max-lines" → "max_lines"
       message=violation.message,
       severity=violation.severity,
       line=violation.line,
   )
   ```
4. **Configurable**: `PreCheckEngine` constructs `LinterEngine` with settings from `RubricConfig.pre_check` (max_lines, required_sections), not from `eval.yaml`'s `LinterConfig`. This separates pre-check config from lint config.

**Alternative considered**: Inheritance (`PreCheckEngine(LinterEngine)`) — rejected because LinterEngine's `run()` returns `LinterReport` (a Pydantic model) and the pre-check needs a different return type (`PreCheckResult`). Overriding would require breaking the signature or complex wrapping anyway.

**Pattern**:
```python
class PreCheckEngine:
    def __init__(self, rubric: RubricConfig):
        self._linter = LinterEngine(LinterConfig(
            max_lines=rubric.pre_check.max_lines,
            fail_on_violation=True,
        ))
        # ... security patterns compiled here
    
    def run(self, skill_path: str) -> PreCheckResult:
        # 1. Delegate to linter
        linter_report = self._linter.run(skill_path)
        findings = [self._map_violation(v) for v in linter_report.violations]
        
        # 2. Run security checks (not in linter)
        findings.extend(self._run_security_checks(skill_path, content))
        
        # 3. Build PreCheckResult
        return PreCheckResult(...)
```

---

### ADR-03: RubricConfig Uses Pydantic (not @dataclass)

**Context**: `RubricConfig` is loaded from YAML files (`rubric.yaml`) and needs validation, default values, and structured parsing.

**Decision**: Use Pydantic `BaseModel` for `RubricConfig` and its nested models (`DimensionConfig`, `PreCheckConfig`, `SecurityPattern`).

**Rationale**:
1. **Precedent**: `EvalConfig` in `md_evals/models.py` is a Pydantic `BaseModel` loaded from `eval.yaml` via `ConfigLoader`. `RubricConfig` follows the identical pattern — a configuration model loaded from YAML.
2. **Validation**: Pydantic provides field-level validation (types, defaults, `Field(default_factory=...)`) that catches YAML parsing errors automatically. Custom validators handle weight-sum and threshold-monotonicity checks.
3. **Serialization**: `RubricConfig.model_dump()` makes it trivial to serialize back to YAML or include in API responses.
4. **Nested models**: Pydantic's nested model support (`DimensionConfig`, `PreCheckConfig`, `SecurityPattern`) maps cleanly to the YAML structure.

**Boundary**: This is the **only** new Pydantic model in `md_evals/`. The scoring types (`DimensionScore`, `EvalResult`, etc.) use `@dataclass` per ADR-01. The separation is:
- **Pydantic**: external input (files, API) → deserialization + validation
- **@dataclass**: internal computation → constructed programmatically

---

### ADR-04: Expand Pattern for the API

**Context**: The spec requires scoring data to be accessible via the existing `GET /api/eval/{eval_id}` endpoint without breaking backward compatibility. Options: (a) always include scoring data, (b) new endpoint, (c) expand parameter.

**Decision**: Use `?expand=scoring` query parameter on the existing endpoint.

**Rationale**:
1. **Backward compatibility (AP-01, AC-37)**: Without `expand`, the response is byte-for-byte identical to today's `EvalDetailResponse`. Zero risk of breaking existing frontend code.
2. **Future extensibility (AP-03)**: The expand pattern supports comma-separated values (`?expand=scoring,analytics`) — Phase 5 analytics slots in without another endpoint.
3. **Forward compatible (AP-04)**: Unknown expand values are silently ignored, so old servers don't break when new clients request future expand keys.
4. **Minimal API surface**: No new endpoints, no new route files. Just one query parameter on an existing route.
5. **Existing pattern in the wild**: GitHub API, Stripe API, and Shopify all use `?expand=` for optional data inclusion.

**Implementation detail**: The `scoring` data is stored in the existing `Evaluation.results` JSONB column under a new `"scoring"` key — no database migration required. The route handler in `apps/server/app/routes/eval.py` extracts and maps it to a `ScoringResponse` Pydantic model only when requested.

**Current route signature** (`eval.py` line 103-108):
```python
@router.get("/{eval_id}", response_model=EvalDetailResponse)
async def get_eval(
    eval_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> EvalDetailResponse:
```

**New signature** (additive only):
```python
@router.get("/{eval_id}", response_model=EvalDetailResponse)
async def get_eval(
    eval_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    expand: str | None = Query(default=None),  # NEW
) -> EvalDetailResponse:
```

---

### ADR-05: Grade Calculation as a Pure Function

**Context**: Grade calculation converts a list of weighted dimension scores into an overall score and letter grade. This could be a method on `EvalResult`, a classmethod on a `Grader` class, or a standalone pure function.

**Decision**: Implement as module-level pure functions `calculate_overall_grade()` and `score_to_grade()` in `md_evals/scoring.py`.

**Rationale**:
1. **Testability (GC-01, AC-10)**: Pure functions with no I/O, no side effects, and no global state are trivially testable. Hypothesis property-based testing (already in dev deps: `hypothesis>=6.75.0` in `pyproject.toml`) works perfectly with pure functions.
2. **Thread safety (AC-10, EC-15)**: No shared mutable state means concurrent calls from `ThreadPoolExecutor` are safe without locking. The spec explicitly requires this.
3. **Precedent**: `md_evals/metrics.py` uses exactly this pattern — `compute_cost_metrics()`, `compute_context_metrics()`, and `compute_comparison_deltas()` are all module-level pure functions, not methods on classes.
4. **Composability**: Pure functions compose naturally. Phase 2 pipeline can call `score_to_grade()` independently for individual dimensions and `calculate_overall_grade()` for the aggregate.
5. **Determinism**: Given the same inputs, the output is always the same. No hidden dependencies on config singletons or environment variables.

**Implementation**:
```python
def calculate_overall_grade(
    dimensions: list[DimensionScore],
    thresholds: dict[str, float],
) -> tuple[float, str]:
    """Weighted average → letter grade. Pure function, no I/O."""
    if not dimensions:
        raise ValueError("Cannot calculate grade with empty dimensions")
    total = sum(d.score * d.weight for d in dimensions)
    grade = score_to_grade(total, thresholds)
    return total, grade

def score_to_grade(score: float, thresholds: dict[str, float]) -> str:
    """Map a 0.0–1.0 score to a letter grade. Pure function."""
    score = min(max(score, 0.0), 1.0)  # Clamp
    for grade in ("S", "A", "B", "C", "D"):
        if grade in thresholds and score >= thresholds[grade]:
            return grade
    return "F"
```

---

### ADR-06: Pre-check Findings as LLM Context (Hybrid Blocking)

**Context**: Pre-check produces findings at two severity levels: errors (hardcoded secrets, empty file) and warnings (missing sections, long lines, shell patterns). The question is what happens after pre-check runs.

**Decision**: Implement a **hybrid blocking** approach:

| Finding Severity | Default Behavior | `--force` | `--no-pre-check` |
|-----------------|------------------|-----------|-------------------|
| **Error** | Block LLM eval (save tokens) | Run LLM anyway; pass ALL findings as context | Skip entirely |
| **Warning** | Pass to LLM as context | Pass to LLM as context | Skip entirely |

**Rationale**:
1. **Token savings (PC-06)**: If a SKILL.md has a hardcoded secret (`severity="error"`), there's no point spending LLM tokens on it. The pre-check catches it in <1 second for free.
2. **Nuanced scoring (PC-05)**: Warnings like "Missing recommended section: Examples" shouldn't block the eval — but the LLM judge should know about them so it can penalize the Completeness dimension. This is the key insight: **pre-check findings are data for the LLM, not just gates**.
3. **Escape hatch (PC-07, PC-08)**: `--force` runs everything (for debugging/experimentation). `--no-pre-check` skips the pre-check entirely (for backward compatibility with existing workflows).
4. **Phase 2 data flow**: The `PreCheckResult` is stored in `EvalResult.pre_check`. Phase 2's pipeline will read `pre_check.findings` and inject warning messages into the LLM judge prompt, enabling the LLM to say *"Completeness: B — missing Examples section (detected by pre-check)"*.

**Data flow designed in Phase 1, implemented in Phase 2**:
```
PreCheckResult.findings
  │
  ├── severity="error"  ──▶ Block LLM eval (default) or pass as context (--force)
  │
  └── severity="warning" ──▶ Injected into LLM judge prompt as context:
                              "Pre-check warnings detected:
                               - Missing recommended section: Examples
                               - Line 87 exceeds 200 characters
                               Consider these when scoring dimensions."
```

---

### ADR-07: Separation of Lint and Pre-check Configuration

**Context**: The existing `LinterConfig` lives in `md_evals/models.py` and is configured via the `lint:` section of `eval.yaml`. The new `PreCheckConfig` lives in `rubric.yaml`. Both affect the same underlying checks (max_lines, required_sections).

**Decision**: Pre-check configuration is independent of lint configuration. `PreCheckEngine` constructs its own `LinterEngine` with settings from `RubricConfig.pre_check`, not from `eval.yaml`'s `lint` section.

**Rationale**:
1. **Different purposes**: `md-evals lint` validates structural quality for the eval pipeline. `md-evals check` validates for scoring readiness. They may have different thresholds (lint max_lines=400, pre-check max_lines=500).
2. **Different config sources**: Lint reads from `eval.yaml` (per-project eval config). Pre-check reads from `rubric.yaml` (per-rubric scoring config). A team might use different rubrics with different pre-check rules.
3. **No breakage**: Existing `lint` command and the lint step in `run` continue to use `eval.yaml`'s `LinterConfig` unchanged.

**Consequence**: Users who want consistent behavior between `lint` and `check` must manually align the values in `eval.yaml` (lint section) and `rubric.yaml` (pre_check section). This is acceptable because the two commands serve different purposes.

---

### ADR-08: `RubricValidationError` Exception Hierarchy

**Context**: Rubric loading can fail for multiple reasons: file not found, invalid YAML, validation failures (weight sum, threshold monotonicity, regex compilation). The CLI needs to map these to different exit codes and messages.

**Decision**: Create a small exception hierarchy in `md_evals/rubric.py`:

```python
class RubricError(Exception):
    """Base for all rubric errors."""

class RubricValidationError(RubricError):
    """Rubric content is invalid (weights, thresholds, patterns)."""

class RubricNotFoundError(RubricError):
    """Rubric file does not exist."""
```

**Rationale**:
1. **Follows existing pattern**: `ConfigLoaderError` in `md_evals/config.py` is the precedent — a single exception class for config loading failures. We add one level of granularity (found vs. not-found vs. invalid) because the spec requires different error messages.
2. **CLI mapping**: `RubricNotFoundError` → exit code 1 with "file not found". `RubricValidationError` → exit code 1 with "invalid rubric: {detail}". Both caught at the CLI layer, same as `ConfigLoaderError` is caught in `cli.py` line 180-182.
3. **Descriptive messages**: The spec (§9.1) requires error messages to include specifics: actual weight sum, duplicate dimension name, invalid regex pattern. The exception message carries this context.

---

## 3. Module Design

### 3.1 `md_evals/scoring.py` — Scoring Data Model + Grade Functions

**Purpose**: Defines the central data types for multi-dimensional scoring and the pure functions that compute grades.

#### Public API

```python
# --- Data Types ---

@dataclass(frozen=True)
class DimensionScore:
    """Score for a single evaluation dimension."""
    dimension: str                              # e.g. "correctness"
    score: float                                # 0.0–1.0
    weight: float                               # from rubric, sums to 1.0
    grade: str                                  # S/A/B/C/D/F
    evidence: list[str] = field(default_factory=list)  # [] until Phase 3

@dataclass
class EvalMetadata:
    """Timing, cost, model info for an evaluation run."""
    model: str
    provider: str
    cost_metrics: CostMetrics | None = None
    context_metrics: ContextMetrics | None = None
    total_duration_ms: int = 0
    pre_check_duration_ms: int = 0
    llm_duration_ms: int = 0
    timestamp: str = ""                         # ISO 8601

@dataclass
class EvalResult:
    """Top-level scoring result for a single SKILL.md evaluation."""
    skill_path: str
    overall_grade: str                          # S/A/B/C/D/F
    overall_score: float                        # 0.0–1.0 weighted
    dimensions: list[DimensionScore]
    pre_check: PreCheckResult | None            # None when --no-pre-check
    metadata: EvalMetadata
    execution_results: list[Any] | None = None  # Backward compat escape hatch

# --- Pure Functions ---

def calculate_overall_grade(
    dimensions: list[DimensionScore],
    thresholds: dict[str, float],
) -> tuple[float, str]: ...

def score_to_grade(
    score: float,
    thresholds: dict[str, float],
) -> str: ...

# --- Constants ---

VALID_GRADES: set[str] = {"S", "A", "B", "C", "D", "F"}
DEFAULT_THRESHOLDS: dict[str, float] = {
    "S": 0.95, "A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30
}
```

#### Internal Implementation Details

- `score_to_grade` iterates grades in descending order `("S", "A", "B", "C", "D")`, skipping any grade not in `thresholds`. This handles the "S grade omitted" case (GC-04): if S is not in thresholds, iteration starts at A.
- Score clamping: `score = min(max(score, 0.0), 1.0)` applied silently per §9.1 — no exception for out-of-range.
- Empty dimensions: `calculate_overall_grade([])` raises `ValueError("Cannot calculate grade with empty dimensions")` per §9.1.
- `EvalResult` is **not** frozen because it's built incrementally: pre-check result is set first, then dimensions are added after LLM eval, then metadata is filled last (Phase 2 concern, but the type supports it now).
- `EvalMetadata` is **not** frozen for the same reason — `total_duration_ms` and `timestamp` are set after all phases complete.

#### Dependencies

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from md_evals.metrics import CostMetrics, ContextMetrics
# TYPE_CHECKING import for PreCheckResult to avoid circular
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from md_evals.precheck import PreCheckResult
```

Note: `PreCheckResult` is imported under `TYPE_CHECKING` to avoid a circular import (`scoring.py` ↔ `precheck.py`). At runtime, `EvalResult.pre_check` is typed as `PreCheckResult | None` via string annotation (`from __future__ import annotations`).

#### Dependents (What Imports This Module)

- `md_evals/cli.py` — imports `EvalResult` for JSON output assembly
- `md_evals/reporter.py` — imports `EvalResult`, `DimensionScore` for grade-aware reporting
- `apps/server/app/routes/eval.py` — indirectly, via schema mapping
- `tests/test_scoring.py` — all types and functions

---

### 3.2 `md_evals/precheck.py` — Pre-check Engine

**Purpose**: Deterministic validation of SKILL.md files. Fast, free, no LLM.

#### Public API

```python
# --- Data Types ---

@dataclass(frozen=True)
class PreCheckFinding:
    """A single finding from the pre-check engine."""
    check: str              # "required_sections", "security_antipattern", "empty_file", etc.
    message: str            # Human-readable
    severity: str           # "error" | "warning" | "info"
    line: int | None = None # 1-indexed, None for file-level findings

@dataclass(frozen=True)
class PreCheckResult:
    """Aggregated result from pre-check."""
    passed: bool            # True iff no error-severity findings
    findings: list[PreCheckFinding]
    checks_run: int         # Total checks executed (some produce 0 findings)
    duration_ms: int        # Wall-clock time

# --- Engine ---

class PreCheckEngine:
    """Deterministic pre-check: fast, free, no LLM."""

    def __init__(self, rubric: RubricConfig) -> None: ...
    def run(self, skill_path: str) -> PreCheckResult: ...
```

#### Internal Implementation Details

**Constructor**:
```python
def __init__(self, rubric: RubricConfig) -> None:
    self._rubric = rubric
    
    # Compose LinterEngine with rubric's pre-check settings
    self._linter = LinterEngine(LinterConfig(
        max_lines=rubric.pre_check.max_lines,
        fail_on_violation=True,
    ))
    
    # Pre-compile security patterns (PC-10: compiled once, reused across runs)
    self._compiled_patterns: list[tuple[re.Pattern, str, str]] = []
    for sp in rubric.pre_check.security_patterns:
        self._compiled_patterns.append((
            re.compile(sp.pattern),
            sp.message,
            sp.severity,
        ))
```

**`run()` method flow**:

1. **Start timer**: `start = time.monotonic_ns()`
2. **Delegate to LinterEngine**: `linter_report = self._linter.run(skill_path)`
3. **Map violations**: Convert each `LinterViolation` to `PreCheckFinding`:
   - Rule name mapping: `"max-lines"` → `"max_lines"`, `"empty-file"` → `"empty_file"`, `"very-long-line"` → `"very_long_line"`, `"required-sections"` → `"required_sections"`, `"file-not-found"` → `"file_not_found"`, `"read-error"` → `"read_error"`
   - Severity preserved as-is (linter already uses "error"/"warning")
   - `line` field preserved as-is
4. **Read file content** (if linter didn't fail on file-not-found/read-error):
   - Read with `Path(skill_path).read_text(encoding="utf-8")`
   - Handle encoding errors → `PreCheckFinding(check="read_error", severity="error")`
5. **Run security pattern checks** against file content:
   - For each line, check each compiled pattern
   - On match: `PreCheckFinding(check="security_antipattern", message=pattern.message, severity=pattern.severity, line=line_number)`
   - Multiple findings per line are possible (EC-18)
6. **Count checks**: `checks_run = len(self._linter.rules) + len(self._compiled_patterns)`
7. **Determine passed**: `passed = not any(f.severity == "error" for f in findings)`
8. **Stop timer**: `duration_ms = (time.monotonic_ns() - start) // 1_000_000`
9. **Return** `PreCheckResult(passed=passed, findings=findings, checks_run=checks_run, duration_ms=duration_ms)`

**Edge case handling**:
- File not found: Linter returns `LinterViolation(rule="file-not-found")` → mapped to finding → `passed=False`
- Non-UTF-8 encoding: Linter catches read errors → mapped to finding → `passed=False`
- Very large files (10,000+ lines): Security regex runs per-line (O(n × m) where m = number of patterns). For 10k lines × 3 patterns, this is ~30k regex matches — completes in <5s per EC-11.

#### Dependencies

```python
from __future__ import annotations
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from md_evals.linter import LinterEngine
from md_evals.models import LinterConfig, LinterViolation
from md_evals.rubric import RubricConfig
```

#### Dependents

- `md_evals/scoring.py` — `PreCheckResult` type referenced by `EvalResult.pre_check` (TYPE_CHECKING import)
- `md_evals/cli.py` — `PreCheckEngine` used in `check` command and `run` command
- `tests/test_precheck.py` — all types and engine class

---

### 3.3 `md_evals/rubric.py` — Rubric Configuration + Loader

**Purpose**: Pydantic models for `rubric.yaml`, loading/resolution chain, validation, and exceptions.

#### Public API

```python
# --- Exceptions ---

class RubricError(Exception): ...
class RubricValidationError(RubricError): ...
class RubricNotFoundError(RubricError): ...

# --- Pydantic Config Models ---

class SecurityPattern(BaseModel):
    pattern: str
    message: str
    severity: str = "warning"   # "error" | "warning" | "info"

class PreCheckConfig(BaseModel):
    required_sections: list[str] = Field(
        default_factory=lambda: ["Description", "Rules", "Examples"]
    )
    max_lines: int = 400
    security_patterns: list[SecurityPattern] = Field(default_factory=list)

class DimensionConfig(BaseModel):
    weight: float               # 0.0–1.0
    description: str = ""       # Required for custom dimensions (warning if empty)

class RubricConfig(BaseModel):
    version: str = "1.0"
    dimensions: dict[str, DimensionConfig]
    grade_thresholds: dict[str, float]
    pre_check: PreCheckConfig = Field(default_factory=PreCheckConfig)

# --- Loader ---

class RubricLoader:
    BUILTIN_PATH: Path         # Path(__file__).parent / "rubric_default.yaml"
    HOME_PATH: Path            # Path.home() / ".md-evals" / "rubric.yaml"

    @classmethod
    def resolve(cls, cli_rubric: str | None = None) -> RubricConfig: ...
    @classmethod
    def load(cls, path: str) -> RubricConfig: ...
    @classmethod
    def load_default(cls) -> RubricConfig: ...

# --- Constants ---

BUILTIN_DIMENSIONS: set[str] = {
    "correctness", "completeness", "format",
    "adherence", "safety", "efficiency", "robustness"
}
```

#### Internal Implementation Details

**`RubricLoader.load()` validation sequence**:

1. **File existence**: `Path(path).exists()` → `RubricNotFoundError` if missing
2. **YAML parsing**: `yaml.safe_load()` → `RubricValidationError("Invalid YAML")` on parse error
3. **Empty check**: `data is None` → `RubricValidationError("Rubric file is empty")`
4. **Pydantic parsing**: `RubricConfig(**data)` → catches `ValidationError` and re-raises as `RubricValidationError`
5. **Custom validation** (after Pydantic construction):
   a. **Version check**: `config.version != "1.0"` → error
   b. **At least one dimension**: `len(config.dimensions) < 1` → error
   c. **Weight sum**: `abs(sum(d.weight for d in config.dimensions.values()) - 1.0) > 0.001` → error with actual sum
   d. **Required thresholds**: A, B, C, D must all be present
   e. **Threshold monotonicity**: S > A > B > C > D (when each is present)
   f. **Threshold range**: Each value in (0.0, 1.0]
   g. **Regex compilation**: Each `SecurityPattern.pattern` → `re.compile()` → `RubricValidationError` with pattern and error message on failure
   h. **Custom dimension description warning**: If dimension name not in `BUILTIN_DIMENSIONS` and `description == ""`, emit `logger.warning()`

**Resolution chain** (`RubricLoader.resolve()`):
```
CLI --rubric flag  →  rubric.yaml in CWD  →  ~/.md-evals/rubric.yaml  →  built-in default
   (explicit)          (project-level)        (user-level)               (package-bundled)
```

**`rubric_default.yaml` packaging**: Shipped inside the `md_evals/` package directory. Referenced via `Path(__file__).parent / "rubric_default.yaml"`. Must be included in the wheel via `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["md_evals"]
# rubric_default.yaml is inside md_evals/, so it's included automatically
```

#### Dependencies

```python
from __future__ import annotations
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field
import yaml
```

No imports from other `md_evals` modules — `rubric.py` is a leaf in the dependency graph.

#### Dependents

- `md_evals/precheck.py` — imports `RubricConfig` for constructor
- `md_evals/cli.py` — imports `RubricLoader`, `RubricValidationError`, `RubricNotFoundError`
- `tests/test_rubric.py` — all types, loader, exceptions

---

## 4. Integration Points

### 4.1 `md_evals/cli.py` — Changes

**Current state**: 540 lines, 8 commands (`version`, `init`, `run`, `lint`, `smoke`, `list-models`, `list`).

**New additions** (all additive, existing commands unchanged):

#### 4.1.1 New `check` Command (~50 lines)

```python
@app.command()
def check(
    skill_path: Annotated[str, typer.Argument(help="Path to SKILL.md file to check")],
    rubric: Annotated[Optional[str], typer.Option("--rubric", help="Path to rubric.yaml")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed check results")] = False,
):
    """Run deterministic pre-check on a SKILL.md file (no LLM, no cost)."""
```

**Implementation pattern**: Follows the existing `lint` command (lines 334-363) exactly:
1. Load rubric via `RubricLoader.resolve(rubric)`
2. Create `PreCheckEngine(rubric_config)`
3. Call `engine.run(skill_path)`
4. Print results with Rich console
5. Exit code 0 (passed) or 2 (failed) — matches lint's exit code pattern

**Error handling**: Wraps rubric loading in try/except, same as `ConfigLoader.load()` is handled in `run` (lines 178-182):
```python
try:
    rubric_config = RubricLoader.resolve(rubric)
except RubricNotFoundError as e:
    console.print(f"[red]Error: {e}[/red]")
    raise typer.Exit(code=1)
except RubricValidationError as e:
    console.print(f"[red]Invalid rubric: {e}[/red]")
    raise typer.Exit(code=1)
```

#### 4.1.2 New Flags on `run` Command

Three new parameters added to the existing `run` function signature (line 156):

```python
@app.command()
def run(
    # ... existing parameters unchanged ...
    rubric: Annotated[Optional[str], typer.Option("--rubric", help="Path to rubric.yaml for scoring")] = None,
    no_pre_check: Annotated[bool, typer.Option("--no-pre-check", help="Skip pre-check phase")] = False,
    force: Annotated[bool, typer.Option("--force", help="Run LLM eval even on pre-check errors")] = False,
):
```

**Integration into `run` flow** — inserted between lint (line 211-234) and treatment execution (line 236+):

```python
# After lint, before execution:
pre_check_result = None
if not no_pre_check:
    try:
        rubric_config = RubricLoader.resolve(rubric)
        pre_check_engine = PreCheckEngine(rubric_config)
        # Run pre-check on each skill file
        for skill_file in skill_files:
            pre_check_result = pre_check_engine.run(skill_file)
            if not pre_check_result.passed and not force:
                # Print findings and exit
                console.print(f"[red]Pre-check failed for {skill_file}[/red]")
                for finding in pre_check_result.findings:
                    console.print(f"  [{finding.severity.upper()}] {finding.message}")
                raise typer.Exit(code=2)
    except (RubricNotFoundError, RubricValidationError) as e:
        console.print(f"[red]Rubric error: {e}[/red]")
        raise typer.Exit(code=1)
```

#### 4.1.3 Extension to `init` Command

Add `rubric.yaml` generation after the existing `eval.yaml` and `SKILL.md` creation (lines 56-152):

```python
# After skill_md.write_text(skill_content) (line 143):
rubric_yaml = directory_path / "rubric.yaml"
if not rubric_yaml.exists() or force:
    rubric_yaml.write_text(RUBRIC_TEMPLATE)
    console.print(f"[green]Created {rubric_yaml}[/green]")
```

Where `RUBRIC_TEMPLATE` is a commented YAML string with default values.

#### 4.1.4 New Imports

```python
# Added to top of cli.py:
from md_evals.precheck import PreCheckEngine
from md_evals.rubric import RubricLoader, RubricValidationError, RubricNotFoundError
```

---

### 4.2 `md_evals/reporter.py` — Changes

**Current state**: 542 lines, handles terminal/JSON/markdown output.

**New additions** (all additive):

#### 4.2.1 New Method: `report_eval_result()`

```python
def report_eval_result(
    self,
    eval_result: EvalResult,
    output_format: str = "table",
) -> None:
    """Print scoring-aware results to terminal."""
```

This renders:
1. Overall grade badge (colored: S=gold, A=green, B=blue, C=yellow, D=orange, F=red)
2. Dimension scores table (dimension, score, weight, grade)
3. Pre-check summary (if present)
4. Uses Rich tables, same as `report_terminal()` (lines 24-90)

#### 4.2.2 Extension to `_build_output_data()` (JSON Output)

Add `eval_result` key to the JSON output dict (line 408-447):

```python
# After existing output dict construction (line 438):
# Add eval_result if available (scoring engine)
if eval_result is not None:
    from dataclasses import asdict
    output["eval_result"] = {
        "overall_grade": eval_result.overall_grade,
        "overall_score": eval_result.overall_score,
        "dimensions": [asdict(d) for d in eval_result.dimensions],
        "pre_check": asdict(eval_result.pre_check) if eval_result.pre_check else None,
    }
```

#### 4.2.3 New Imports

```python
from md_evals.scoring import EvalResult, DimensionScore
```

---

### 4.3 `apps/server/` — Route and Schema Changes

#### 4.3.1 `apps/server/app/models/schemas.py` — New Response Models

Add after existing `EvalDetailResponse` (line 106):

```python
class DimensionScoreResponse(BaseModel):
    """Dimension score in API response."""
    dimension: str
    score: float
    weight: float
    grade: str
    evidence: list[str] = Field(default_factory=list)

class PreCheckFindingResponse(BaseModel):
    """Pre-check finding in API response."""
    check: str
    message: str
    severity: str
    line: int | None = None

class PreCheckResultResponse(BaseModel):
    """Pre-check result in API response."""
    passed: bool
    findings: list[PreCheckFindingResponse]
    checks_run: int
    duration_ms: int

class ScoringResponse(BaseModel):
    """Scoring data for expand=scoring."""
    overall_grade: str
    overall_score: float
    dimensions: list[DimensionScoreResponse]
    pre_check: PreCheckResultResponse | None = None
```

Modify `EvalDetailResponse` to add optional scoring field:

```python
class EvalDetailResponse(BaseModel):
    # ... all existing fields unchanged (lines 95-105) ...
    scoring: ScoringResponse | None = None  # NEW — only populated when expand=scoring
```

#### 4.3.2 `apps/server/app/routes/eval.py` — Expand Parameter

Modify `get_eval()` (line 103-136) to accept and process `expand`:

```python
@router.get("/{eval_id}", response_model=EvalDetailResponse)
async def get_eval(
    eval_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    expand: str | None = Query(default=None),  # NEW
) -> EvalDetailResponse:
    # ... existing query logic unchanged (lines 110-122) ...
    
    response = EvalDetailResponse(
        # ... existing fields unchanged (lines 124-136) ...
    )
    
    # NEW: expand=scoring
    if expand:
        expand_set = {v.strip().lower() for v in expand.split(",")}
        if "scoring" in expand_set:
            scoring_data = (evaluation.results or {}).get("scoring")
            if scoring_data:
                response.scoring = ScoringResponse(**scoring_data)
    
    return response
```

**Storage**: Scoring data is stored in `Evaluation.results` JSONB column under `"scoring"` key — no migration needed, the column already accepts arbitrary JSON.

---

### 4.4 `apps/web/` — Frontend Changes

#### 4.4.1 `apps/web/src/lib/types.ts` — New Type Definitions

Add after existing `Evaluation` interface (line 68):

```typescript
// --- Scoring Engine Types (Phase 1) ---

export interface DimensionScoreDTO {
  dimension: string;
  score: number;       // 0.0–1.0
  weight: number;      // 0.0–1.0, all weights sum to 1.0
  grade: string;       // S/A/B/C/D/F
  evidence: string[];  // empty until Phase 3
}

export interface PreCheckFindingDTO {
  check: string;
  message: string;
  severity: "error" | "warning" | "info";
  line: number | null;
}

export interface PreCheckResultDTO {
  passed: boolean;
  findings: PreCheckFindingDTO[];
  checks_run: number;
  duration_ms: number;
}

export interface EvalResultScoring {
  overall_grade: string;
  overall_score: number;
  dimensions: DimensionScoreDTO[];
  pre_check: PreCheckResultDTO | null;
}
```

Extend existing `Evaluation` interface:

```typescript
export interface Evaluation {
  // ... all existing fields unchanged ...
  scoring?: EvalResultScoring | null;  // NEW — present when expand=scoring
}
```

#### 4.4.2 `apps/web/src/components/charts/DimensionRadar.tsx` — New File

Follows the pattern of existing chart components (`PassRateChart.tsx`, `TokenUsageChart.tsx`, `ContextGauge.tsx`):
- Default export function component
- Uses Recharts with `ResponsiveContainer`
- Imports types from `../../lib/types`
- Handles empty data gracefully

```tsx
/** Radar chart: dimension scores for a SKILL.md evaluation. */

import {
  RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from "recharts";
import type { DimensionScoreDTO } from "../../lib/types";

interface Props {
  dimensions: DimensionScoreDTO[];
}

export default function DimensionRadar({ dimensions }: Props) {
  const data = dimensions.map((d) => ({
    dimension: d.dimension.charAt(0).toUpperCase() + d.dimension.slice(1),
    score: d.score,
    fullMark: 1.0,
  }));

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-400">
        No dimension data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fontSize: 11, fill: "#6b7280" }}
        />
        <PolarRadiusAxis
          domain={[0, 1]}
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          tickCount={5}
        />
        <Tooltip
          formatter={(value: number) => [value.toFixed(2), "Score"]}
          contentStyle={{
            backgroundColor: "#fff",
            border: "1px solid #e5e7eb",
            borderRadius: "8px",
            fontSize: "13px",
          }}
        />
        <Radar
          dataKey="score"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.3}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

#### 4.4.3 `apps/web/src/components/charts/GradeBadge.tsx` — New File

```tsx
/** Letter grade badge with color coding. */

import { cn } from "../../lib/cn";

interface Props {
  grade: string;
  size?: "sm" | "md" | "lg";
}

const GRADE_COLORS: Record<string, string> = {
  S: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-700",
  A: "bg-green-100 text-green-800 border-green-300 dark:bg-green-950 dark:text-green-300 dark:border-green-700",
  B: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-700",
  C: "bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-700",
  D: "bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-700",
  F: "bg-red-100 text-red-800 border-red-300 dark:bg-red-950 dark:text-red-300 dark:border-red-700",
};

const SIZES: Record<string, string> = {
  sm: "h-6 w-6 text-xs",
  md: "h-10 w-10 text-lg",
  lg: "h-14 w-14 text-2xl",
};

export default function GradeBadge({ grade, size = "md" }: Props) {
  const colorClass = GRADE_COLORS[grade] ?? GRADE_COLORS.F;
  const sizeClass = SIZES[size];

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-full border font-bold",
        colorClass,
        sizeClass,
      )}
    >
      {grade}
    </div>
  );
}
```

#### 4.4.4 Dashboard Integration

The `EvalDetail` component in `apps/web/src/pages/Dashboard.tsx` (line 212) will gain an optional scoring section. When `evaluation.scoring` is present, it renders:

1. `<GradeBadge grade={evaluation.scoring.overall_grade} size="lg" />` — next to the eval name
2. `<DimensionRadar dimensions={evaluation.scoring.dimensions} />` — in the charts row
3. Pre-check findings list — if `evaluation.scoring.pre_check` has findings

This is additive — the existing charts (`PassRateChart`, `TokenUsageChart`, `ContextGauge`) remain unchanged. The new components are conditionally rendered only when `scoring` data is present.

---

## 5. Testing Strategy

### 5.1 Test File Organization

```
tests/
├── test_scoring.py        # NEW — DimensionScore, EvalResult, grade functions
├── test_precheck.py       # NEW — PreCheckEngine, security checks
├── test_rubric.py         # NEW — RubricConfig, RubricLoader, validation
├── test_linter.py         # EXISTING — unchanged, verifies backward compat
├── test_cli.py            # EXISTING — unchanged
├── test_cli_flags.py      # EXISTING — may add new test cases for --rubric, --force, --no-pre-check
├── fixtures/
│   ├── skill_short.md     # EXISTING
│   ├── skill_long.md      # EXISTING
│   ├── eval.yaml          # EXISTING
│   ├── skill_with_secret.md         # NEW — contains api_key = "sk-12345"
│   ├── skill_with_shell.md          # NEW — contains os.system("rm -rf /")
│   ├── skill_empty.md               # NEW — 0 bytes
│   ├── rubric_default.yaml          # NEW — copy of default rubric for testing
│   ├── rubric_invalid_weights.yaml  # NEW — weights sum to 0.80
│   ├── rubric_custom_dimensions.yaml # NEW — 5 builtin + 2 custom
│   └── rubric_no_s_grade.yaml       # NEW — A through D only
```

### 5.2 Unit Test Plan: `test_scoring.py`

**Class: `TestDimensionScore`** (~10 tests)
- `test_frozen_immutability` — setting field raises `FrozenInstanceError`
- `test_evidence_defaults_to_empty_list` — not None
- `test_construction_with_all_fields`
- `test_evidence_list_is_independent` — two instances don't share the default list

**Class: `TestEvalResult`** (~5 tests)
- `test_construction_with_required_fields`
- `test_execution_results_default_none`
- `test_pre_check_optional`
- `test_mutable` — can set fields after construction

**Class: `TestScoreToGrade`** (~12 tests)
- `test_boundary_values` — parametrized: 0.0→F, 0.29→F, 0.30→D, 0.49→D, 0.50→C, 0.69→C, 0.70→B, 0.84→B, 0.85→A, 0.94→A, 0.95→S, 1.0→S
- `test_s_grade_omitted` — returns A for 0.99 when S not in thresholds
- `test_clamping_above_1` — score=1.5 → S
- `test_clamping_below_0` — score=-0.5 → F

**Class: `TestCalculateOverallGrade`** (~8 tests)
- `test_happy_path_scenario_2_1` — exact values from spec §2.1 → 0.8275, "B"
- `test_all_scores_zero` — EC-01: → 0.0, "F"
- `test_all_scores_one` — EC-02: → 1.0, "S"
- `test_empty_dimensions_raises` — ValueError
- `test_single_dimension` — EC-03: single dimension, weight=1.0
- `test_thread_safety` — EC-15: 100 concurrent calls via ThreadPoolExecutor

**Class: `TestHypothesisGradeProperties`** (~3 property tests)
- `test_grade_always_valid` — for any score in [0, 1], result in VALID_GRADES
- `test_grade_monotonicity` — if score_a > score_b, grade_rank(a) >= grade_rank(b)
- `test_weighted_sum_matches` — overall_score == sum(d.score * d.weight for d in dims)

### 5.3 Unit Test Plan: `test_precheck.py`

**Class: `TestPreCheckFinding`** (~4 tests)
- `test_frozen_immutability`
- `test_line_default_none`
- `test_construction_with_line`

**Class: `TestPreCheckResult`** (~4 tests)
- `test_passed_invariant` — passed iff no error findings
- `test_duration_positive`

**Class: `TestPreCheckEngine`** (~18 tests, using `tmp_path` fixture)
- `test_clean_skill` — valid SKILL.md → passed=True, 0 error findings
- `test_missing_sections_warning` — missing Examples → warning, passed=True
- `test_hardcoded_secret_error` — api_key="sk-123" → error, passed=False (§2.7)
- `test_shell_pattern_warning` — os.system() → warning, passed=True (§2.8)
- `test_chmod_777_warning` — chmod 777 → warning, passed=True
- `test_empty_file_error` — 0 bytes → error, passed=False (§2.9)
- `test_file_not_found` — nonexistent path → error, passed=False (EC-12)
- `test_encoding_error` — ISO-8859-1 file → error, passed=False (EC-10)
- `test_very_large_file` — 10,000 lines → max_lines error, completes in <5s (EC-11)
- `test_multiple_findings_same_line` — secret + shell on same line → 2 findings (EC-18)
- `test_checks_run_count` — count matches linter rules + security patterns (AC-26)
- `test_duration_ms_positive` — > 0 for any file (AC-27)
- `test_duration_ms_under_1s` — < 1000 for file under 400 lines (AC-27)
- `test_delegates_to_linter_engine` — violations come from LinterEngine rules (AC-25)
- `test_security_patterns_compiled_once` — patterns cached, not recompiled per run (PC-10)
- `test_custom_rubric_security_patterns` — custom patterns from rubric are used
- `test_missing_multiple_sections` — 2 warnings for Rules + Examples
- `test_all_checks_pass_clean_file` — comprehensive clean file test

### 5.4 Unit Test Plan: `test_rubric.py`

**Class: `TestRubricLoader`** (~15 tests)
- `test_load_default` — 7 dimensions, weights sum to 1.0, thresholds include S/A/B/C/D (AC-14)
- `test_load_custom_file` — valid YAML loads successfully (AC-15)
- `test_load_file_not_found` — RubricNotFoundError raised
- `test_load_invalid_yaml` — RubricValidationError on broken YAML
- `test_load_empty_file` — RubricValidationError (EC-06)
- `test_invalid_weights_sum` — weights=0.80 → error with "0.8" in message (AC-16)
- `test_non_monotonic_thresholds` — A=0.85, B=0.90 → error (AC-18)
- `test_invalid_regex_pattern` — "[invalid" → error mentioning "regex" (AC-19)
- `test_duplicate_dimensions` — handled by YAML (dict keys unique) — no error
- `test_missing_required_thresholds` — missing A → error
- `test_threshold_range` — threshold=1.5 → error
- `test_unsupported_version` — version="2.0" → error
- `test_custom_dimensions_with_description` — loads with 5+2 dims (§2.19)
- `test_custom_dimension_no_description_warns` — warning logged (§2.20)
- `test_zero_weight_dimension` — weight=0.0, valid rubric (EC-07)

**Class: `TestRubricResolution`** (~4 tests, using `tmp_path` and `monkeypatch`)
- `test_cli_flag_wins` — explicit path takes precedence (AC-20)
- `test_cwd_wins_over_home` — CWD file found → used (§2.16)
- `test_home_wins_over_default` — home dir file → used
- `test_falls_back_to_builtin` — no files → default loaded (§2.15)

**Class: `TestHypothesisRubric`** (~2 property tests)
- `test_weight_sum_invariant` — any valid rubric has weights summing to ~1.0
- `test_threshold_ordering` — thresholds are always strictly decreasing

### 5.5 Property-Based Testing (Hypothesis)

Hypothesis is already in dev dependencies (`hypothesis>=6.75.0` in `pyproject.toml`). Key strategies:

```python
from hypothesis import given, strategies as st

# Strategy: valid score
score_st = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy: valid thresholds
thresholds_st = st.fixed_dictionaries({
    "S": st.just(0.95),
    "A": st.just(0.85),
    "B": st.just(0.70),
    "C": st.just(0.50),
    "D": st.just(0.30),
})

@given(score=score_st, thresholds=thresholds_st)
def test_grade_always_in_valid_set(score, thresholds):
    grade = score_to_grade(score, thresholds)
    assert grade in VALID_GRADES

@given(score_a=score_st, score_b=score_st, thresholds=thresholds_st)
def test_grade_monotonicity(score_a, score_b, thresholds):
    """Higher score → same or higher grade (never lower)."""
    RANK = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4, "S": 5}
    if score_a >= score_b:
        assert RANK[score_to_grade(score_a, thresholds)] >= RANK[score_to_grade(score_b, thresholds)]
```

### 5.6 Integration Tests

**CLI integration tests** (in `test_cli_flags.py` or new file):

```python
from typer.testing import CliRunner
from md_evals.cli import app

runner = CliRunner()

def test_check_command_passes(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text("# Description\n## Rules\n## Examples\n")
    result = runner.invoke(app, ["check", str(skill)])
    assert result.exit_code == 0
    assert "PASSED" in result.stdout

def test_check_command_fails_on_secret(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text('api_key = "sk-12345"\n')
    result = runner.invoke(app, ["check", str(skill)])
    assert result.exit_code == 2
    assert "FAILED" in result.stdout

def test_run_with_no_pre_check():
    # Verify --no-pre-check flag is accepted and pre-check is skipped
    ...

def test_run_with_force():
    # Verify --force continues despite pre-check errors
    ...
```

### 5.7 Test Fixtures

**`tests/fixtures/skill_with_secret.md`**:
```markdown
# My Skill

## Description
A skill with a hardcoded secret.

## Rules
api_key = "sk-12345abcdef"
password = "hunter2"

## Examples
Example usage.
```

**`tests/fixtures/skill_with_shell.md`**:
```markdown
# My Skill

## Description
A skill with shell patterns.

## Rules
Use os.system("rm -rf /tmp/cache") to clean up.
Run subprocess.call(["ls"]) for listing.

## Examples
```

**`tests/fixtures/skill_empty.md`**: 0-byte file.

**`tests/fixtures/rubric_invalid_weights.yaml`**:
```yaml
version: "1.0"
dimensions:
  correctness:
    weight: 0.50
  completeness:
    weight: 0.30
grade_thresholds:
  A: 0.85
  B: 0.70
  C: 0.50
  D: 0.30
```

---

## 6. Phase 2 Preparation

### 6.1 Interfaces/Hooks Left for Phase 2 (Pipeline)

Phase 2 will introduce a `PipelineEngine` that orchestrates: pre-check → LLM eval → scoring. Phase 1 builds the data types and standalone engines that Phase 2 will compose.

#### 6.1.1 `PreCheckResult` as Pipeline Input

`PreCheckResult` is designed to flow directly into the pipeline:

```python
# Phase 2 pipeline pseudocode:
pre_check = PreCheckEngine(rubric).run(skill_path)

if not pre_check.passed and not force:
    return EvalResult(pre_check=pre_check, dimensions=[], overall_grade="F", ...)

# Pass warnings as LLM context
llm_context = build_llm_context(pre_check.findings)
dimension_scores = await llm_eval(skill_content, llm_context, rubric.dimensions)
```

The `PreCheckResult.findings` list is the interface:
- Each `PreCheckFinding` has `check`, `message`, `severity`, `line`
- Phase 2 filters warnings and formats them as LLM prompt context
- The `check` field (e.g., `"required_sections"`) allows the pipeline to map findings to specific dimensions (missing sections → lower Completeness score)

#### 6.1.2 `EvalResult` Construction Points

`EvalResult` is mutable (ADR-01) specifically so Phase 2 can build it incrementally:

```python
# Phase 2 construction flow:
result = EvalResult(
    skill_path=path,
    overall_grade="",       # Set after scoring
    overall_score=0.0,      # Set after scoring
    dimensions=[],          # Populated by LLM eval
    pre_check=pre_check,    # Set by pre-check phase
    metadata=EvalMetadata(model=model, provider=provider),
)

# After LLM eval:
result.dimensions = dimension_scores
result.overall_score, result.overall_grade = calculate_overall_grade(
    result.dimensions, rubric.grade_thresholds
)
result.metadata.llm_duration_ms = llm_duration
result.metadata.total_duration_ms = total_duration
result.metadata.timestamp = datetime.now(timezone.utc).isoformat()
```

#### 6.1.3 `RubricConfig.dimensions` as LLM Prompt Source

Phase 2 will use `DimensionConfig.description` to build per-dimension LLM judge prompts:

```python
for dim_name, dim_config in rubric.dimensions.items():
    if dim_name in BUILTIN_DIMENSIONS:
        prompt = BUILTIN_PROMPTS[dim_name]  # Optimized prompt per builtin
    else:
        prompt = f"Evaluate '{dim_name}': {dim_config.description}"
    
    score = await llm_judge(skill_content, prompt, context=pre_check_warnings)
    grade = score_to_grade(score, rubric.grade_thresholds)
    dimension_scores.append(DimensionScore(
        dimension=dim_name, score=score, weight=dim_config.weight,
        grade=grade, evidence=[],  # Phase 3
    ))
```

The `BUILTIN_DIMENSIONS` set in `rubric.py` enables Phase 2 to distinguish builtins (optimized prompts) from custom dimensions (use description).

### 6.2 `DimensionScore.evidence` — Phase 3 Hook

`evidence: list[str]` is always an empty list in Phase 1 (AC-07). The field exists now so the data shape doesn't change in Phase 3.

Phase 3 will populate it with source references:
```python
DimensionScore(
    dimension="safety",
    score=0.95,
    weight=0.10,
    grade="S",
    evidence=[
        "No security anti-patterns detected (pre-check clean)",
        "No hardcoded secrets found in 87 lines",
        "No shell injection patterns"
    ]
)
```

The evidence list is generic (`list[str]`) rather than a typed `Citation` object — this keeps Phase 1 simple while allowing Phase 3 to decide the exact evidence format without breaking the data model.

### 6.3 `EvalMetadata` — Phase 2 Timing Fields

`EvalMetadata` has `pre_check_duration_ms` and `llm_duration_ms` fields that Phase 2 will populate:

```python
metadata = EvalMetadata(
    model="gpt-4o",
    provider="github-models",
    pre_check_duration_ms=pre_check.duration_ms,       # From Phase 1 engine
    llm_duration_ms=llm_end - llm_start,               # Phase 2 measures this
    total_duration_ms=total_end - total_start,          # Phase 2 measures this
    cost_metrics=cost,                                  # From existing metrics.py
    context_metrics=context,                            # From existing metrics.py
    timestamp=datetime.now(timezone.utc).isoformat(),
)
```

`CostMetrics` and `ContextMetrics` from `md_evals/metrics.py` are referenced (not duplicated) — the existing `compute_cost_metrics()` and `compute_context_metrics()` functions will be called by Phase 2's pipeline.

### 6.4 Summary: Phase 1 → Phase 2 Contract

| Phase 1 Creates | Phase 2 Consumes |
|-----------------|-----------------|
| `PreCheckEngine.run() → PreCheckResult` | Pipeline calls pre-check, uses result to gate LLM eval |
| `PreCheckResult.findings` | Pipeline extracts warnings, formats as LLM context |
| `RubricConfig.dimensions` | Pipeline iterates dimensions, builds per-dimension LLM prompts |
| `DimensionConfig.description` | Pipeline uses description for custom dimension prompts |
| `calculate_overall_grade()` | Pipeline calls after collecting all dimension scores |
| `score_to_grade()` | Pipeline calls for individual dimension grades |
| `EvalResult` (mutable) | Pipeline constructs incrementally across phases |
| `EvalMetadata` (mutable) | Pipeline sets timing fields as each phase completes |
| `DimensionScore.evidence = []` | Phase 3 populates with citations |

---

## Appendix: File Change Summary

| File | Change Type | Est. Lines Changed |
|------|-------------|-------------------|
| `md_evals/scoring.py` | **NEW** | ~130 |
| `md_evals/precheck.py` | **NEW** | ~200 |
| `md_evals/rubric.py` | **NEW** | ~220 |
| `md_evals/rubric_default.yaml` | **NEW** | ~45 |
| `md_evals/cli.py` | MODIFIED (additive) | ~80 added |
| `md_evals/reporter.py` | MODIFIED (additive) | ~60 added |
| `apps/server/app/routes/eval.py` | MODIFIED (additive) | ~20 added |
| `apps/server/app/models/schemas.py` | MODIFIED (additive) | ~40 added |
| `apps/web/src/lib/types.ts` | MODIFIED (additive) | ~35 added |
| `apps/web/src/components/charts/DimensionRadar.tsx` | **NEW** | ~60 |
| `apps/web/src/components/charts/GradeBadge.tsx` | **NEW** | ~50 |
| `apps/web/src/pages/Dashboard.tsx` | MODIFIED (additive) | ~30 added |
| `pyproject.toml` | MODIFIED (package_data) | ~3 added |
| `tests/test_scoring.py` | **NEW** | ~280 |
| `tests/test_precheck.py` | **NEW** | ~250 |
| `tests/test_rubric.py` | **NEW** | ~230 |
| `tests/fixtures/` (7 new fixtures) | **NEW** | ~110 |
| **Total new/changed** | | **~1,843 lines** |
