# Proposal: Phase 1 — The Scoring Engine

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: scoring-engine
> **Phase**: 1 of 5

---

## Intent

Replace md-evals' current binary pass/fail evaluation model with a **multi-dimensional scoring engine** that grades AI skills across 7 quality dimensions using letter grades (S/A/B/C/D/F), and add a **deterministic pre-check** that catches structural and security problems before spending LLM tokens.

### Why this matters

Today, `EvaluatorResult` in `md_evals/models.py` produces a single `passed: bool` + `score: float` per evaluator. This tells you *if* a skill passed but not *how well it performed* or *where it's weak*. A skill that barely passes on correctness but has excellent format looks the same as one that's perfect on both.

The scoring engine introduces:

1. **Multi-dimensional rubric**: 7 weighted dimensions that decompose "quality" into actionable sub-scores — teams can tune weights via `rubric.yaml` to match their priorities.
2. **Deterministic pre-check**: A free, instant validation pass (`md-evals check`) that catches missing sections, formatting violations, and security anti-patterns *before* the LLM eval runs — saving tokens and money on obviously broken skills.

### Why this is Phase 1

`EvalResult` (with its `DimensionScore` list, `PreCheckResult`, and `EvalMetadata`) becomes the **central data shape** that every downstream feature consumes:

- **Phase 2 (Pipeline)**: Orchestrates pre-check → LLM eval → scoring, consuming and producing `EvalResult`
- **Phase 3 (Citations)**: Populates `DimensionScore.evidence` with source references
- **Phase 4 (CI/Export)**: Serializes `EvalResult` to SARIF, JUnit XML, and badge SVGs
- **Phase 5 (Analytics)**: Aggregates `EvalResult` histories for trend detection

Getting the data model right now means phases 2–5 slot in without breaking changes.

---

## Scope

### In Scope (Phase 1)

| Feature | Description |
|---------|-------------|
| **`DimensionScore` model** | New dataclass: dimension name, score (0.0–1.0), weight, letter grade, evidence placeholder |
| **`EvalResult` model** | New top-level result aggregating dimensions, overall grade/score, pre-check result, and metadata |
| **`PreCheckResult` model** | Structured result from deterministic validation: passed, findings list, severity |
| **`EvalMetadata` model** | Cost, tokens, timing — wraps existing `CostMetrics`/`ContextMetrics` from `md_evals/metrics.py` |
| **`rubric.yaml` loader** | YAML config for dimension names, weights, grade thresholds — with schema validation |
| **Default rubric** | Built-in 7-dimension rubric (Correctness 25%, Completeness 20%, Format 15%, Adherence 15%, Safety 10%, Efficiency 10%, Robustness 5%) |
| **Grade calculator** | Pure function: `list[DimensionScore] + weights → overall_score + overall_grade` |
| **Pre-check engine** | Deterministic checks: required sections, formatting rules, security anti-patterns |
| **`md-evals check` CLI** | New command that runs pre-check only (no LLM, no cost) |
| **Radar chart component** | Recharts `RadarChart` in `apps/web/` for visualizing dimension scores |
| **JSON output extension** | `EvalResult` serialized in JSON report output alongside existing `ExecutionResult` |

### Out of Scope (Phase 1)

| Excluded | Reason | Phase |
|----------|--------|-------|
| LLM prompt engineering for per-dimension scoring | Requires pipeline orchestration | Phase 2 |
| Evidence/citation extraction | Depends on structured LLM output parsing | Phase 3 |
| SARIF/JUnit export | Needs stable `EvalResult` first | Phase 4 |
| Historical trend analysis | Needs persistent storage of `EvalResult` | Phase 5 |
| Rubric marketplace / sharing platform | Post-roadmap |  |
| Modifying existing `ExecutionResult`/`EvaluatorResult` | Additive only — no breaking changes | — |
| Web UI rubric editor | Nice-to-have, not MVP | Future |

---

## Approach

### Data Model (New Types)

All new types live in a new module `md_evals/scoring.py` to avoid bloating `md_evals/models.py` (which owns Pydantic config/runtime models). Scoring types use `@dataclass` (frozen where possible) following the precedent set by `md_evals/metrics.py`.

```python
# md_evals/scoring.py

@dataclass(frozen=True)
class DimensionScore:
    dimension: str          # e.g. "correctness", "safety"
    score: float            # 0.0–1.0 normalized
    weight: float           # from rubric config, sums to 1.0
    grade: str              # S/A/B/C/D/F
    evidence: list[str]     # [] until Phase 3 — empty, not None

@dataclass(frozen=True)
class PreCheckFinding:
    check: str              # e.g. "required_sections", "security_antipattern"
    message: str            # human-readable explanation
    severity: str           # "error" | "warning" | "info"
    line: int | None        # line number if applicable

@dataclass(frozen=True)
class PreCheckResult:
    passed: bool
    findings: list[PreCheckFinding]
    checks_run: int
    duration_ms: int

@dataclass
class EvalMetadata:
    model: str
    provider: str
    cost_metrics: CostMetrics | None    # from md_evals/metrics.py
    context_metrics: ContextMetrics | None
    total_duration_ms: int
    pre_check_duration_ms: int
    llm_duration_ms: int
    timestamp: str                      # ISO 8601

@dataclass
class EvalResult:
    skill_path: str
    overall_grade: str                  # S/A/B/C/D/F
    overall_score: float                # 0.0–1.0 weighted
    dimensions: list[DimensionScore]
    pre_check: PreCheckResult | None
    metadata: EvalMetadata
    # Backward-compat: the raw ExecutionResults are still available
    execution_results: list[Any] | None = None
```

### Grade Scale

| Grade | Score Range | Meaning |
|-------|-----------|---------|
| **S** | 0.95–1.00 | Exceptional — reference quality |
| **A** | 0.85–0.94 | Excellent — production ready |
| **B** | 0.70–0.84 | Good — minor improvements possible |
| **C** | 0.50–0.69 | Adequate — significant gaps |
| **D** | 0.30–0.49 | Poor — major issues |
| **F** | 0.00–0.29 | Failing — fundamental problems |

Grade thresholds are configurable in `rubric.yaml` but ship with sensible defaults.

### Rubric Configuration (`rubric.yaml`)

```yaml
# rubric.yaml — default shipped with md-evals
version: "1.0"

dimensions:
  correctness:
    weight: 0.25
    description: "Technical accuracy of instructions and examples"
  completeness:
    weight: 0.20
    description: "Coverage of edge cases, error handling, constraints"
  format:
    weight: 0.15
    description: "Markdown structure, readability, consistent style"
  adherence:
    weight: 0.15
    description: "Follows the SKILL.md spec and conventions"
  safety:
    weight: 0.10
    description: "No dangerous patterns, injection risks, or secrets"
  efficiency:
    weight: 0.10
    description: "Concise, no redundancy, within line limits"
  robustness:
    weight: 0.05
    description: "Handles ambiguous inputs, edge cases, failure modes"

grade_thresholds:
  S: 0.95
  A: 0.85
  B: 0.70
  C: 0.50
  D: 0.30
  # Below D threshold → F

pre_check:
  required_sections:
    - "Description"
    - "Rules"
    - "Examples"
  max_lines: 400
  security_patterns:
    - pattern: "\\b(api[_-]?key|secret|password)\\s*[:=]\\s*['\"][^'\"]+['\"]"
      message: "Hardcoded secret detected"
      severity: "error"
    - pattern: "os\\.system\\(|subprocess\\.call\\(|eval\\(|exec\\("
      message: "Potentially dangerous shell/eval pattern"
      severity: "warning"
    - pattern: "chmod\\s+777|chmod\\s+0?777"
      message: "Overly permissive file permissions"
      severity: "warning"
```

The rubric loader (`md_evals/rubric.py`) validates:
- Weights sum to 1.0 (within floating-point tolerance)
- All grade thresholds are monotonically decreasing
- No duplicate dimension names
- Security patterns compile as valid regex

Resolution order: CLI `--rubric` flag → `rubric.yaml` in CWD → built-in default.

### Grade Calculation (Pure Function)

```python
# md_evals/scoring.py

def calculate_overall_grade(
    dimensions: list[DimensionScore],
    thresholds: dict[str, float],
) -> tuple[float, str]:
    """Weighted average → letter grade. Pure function."""
    total = sum(d.score * d.weight for d in dimensions)
    grade = score_to_grade(total, thresholds)
    return total, grade

def score_to_grade(score: float, thresholds: dict[str, float]) -> str:
    for grade in ["S", "A", "B", "C", "D"]:
        if score >= thresholds[grade]:
            return grade
    return "F"
```

This is intentionally a pure function with no I/O — easy to test with Hypothesis property-based testing (already in dev deps).

### Pre-Check Engine

Extends the existing `LinterEngine` pattern from `md_evals/linter.py` but produces `PreCheckResult` instead of `LinterReport`. The pre-check engine:

1. Runs all deterministic checks (required sections, formatting, security anti-patterns)
2. Returns `PreCheckResult` with structured findings
3. If any finding has `severity: "error"` → `passed = False`
4. When `passed = False` and used in the pipeline (Phase 2), the LLM eval is skipped

The existing `LinterEngine` and its rules (`MaxLinesRule`, `RequiredSectionsRule`, `EmptyFileRule`, `VeryLongLineRule`) will be **reused** — the pre-check engine wraps them and adds security checks. No duplication.

```python
# md_evals/precheck.py

class PreCheckEngine:
    """Deterministic pre-check: fast, free, no LLM."""

    def __init__(self, rubric: RubricConfig):
        self.rubric = rubric
        # Reuse existing linter rules
        self.linter = LinterEngine(LinterConfig(
            max_lines=rubric.pre_check.max_lines,
            fail_on_violation=True,
        ))
        self.security_checks = [
            SecurityPatternCheck(p) for p in rubric.pre_check.security_patterns
        ]

    def run(self, skill_path: str) -> PreCheckResult:
        """Run all deterministic checks. Returns PreCheckResult."""
        ...
```

### New CLI Command

```bash
# Fast pre-check only (no LLM, no cost)
md-evals check SKILL.md
md-evals check SKILL.md --rubric custom-rubric.yaml

# Output:
# SKILL.md — Pre-check PASSED (7 checks, 0 findings, 12ms)
#   or
# SKILL.md — Pre-check FAILED
#   [ERROR] Missing required section: Examples
#   [WARNING] Potentially dangerous shell/eval pattern (line 42)
#   [WARNING] Line 87 exceeds 200 characters
```

This is a new Typer command in `md_evals/cli.py`, following the same pattern as the existing `lint` command.

### Web UI: Radar Chart

The `apps/web/` frontend already uses Recharts (`recharts: ^2.15.0` in `package.json`). A new `<DimensionRadar>` component renders `DimensionScore[]` as a radar chart:

```tsx
// apps/web/src/components/DimensionRadar.tsx
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

interface Props {
  dimensions: DimensionScore[];
}

export function DimensionRadar({ dimensions }: Props) {
  const data = dimensions.map(d => ({
    dimension: d.dimension,
    score: d.score,
    fullMark: 1.0,
  }));

  return (
    <RadarChart data={data} width={400} height={400}>
      <PolarGrid />
      <PolarAngleAxis dataKey="dimension" />
      <PolarRadiusAxis domain={[0, 1]} />
      <Radar dataKey="score" fill="#8884d8" fillOpacity={0.6} />
    </RadarChart>
  );
}
```

### Integration Points (No Breaking Changes)

| Existing Module | Change | Nature |
|----------------|--------|--------|
| `md_evals/models.py` | No changes | — |
| `md_evals/metrics.py` | `CostMetrics`/`ContextMetrics` referenced by `EvalMetadata` | Read-only import |
| `md_evals/linter.py` | `LinterEngine` reused inside `PreCheckEngine` | Composition, no modification |
| `md_evals/cli.py` | New `check` command added | Additive |
| `md_evals/reporter.py` | New method `report_eval_result()` for grade-aware output | Additive |
| `md_evals/config.py` | New `RubricLoader` class (separate from `ConfigLoader`) | New module |
| `apps/web/` | New `DimensionRadar` component + grade display | Additive |

### New Files

| File | Purpose |
|------|---------|
| `md_evals/scoring.py` | `DimensionScore`, `EvalResult`, `EvalMetadata`, grade functions |
| `md_evals/precheck.py` | `PreCheckEngine`, `PreCheckResult`, `PreCheckFinding`, security checks |
| `md_evals/rubric.py` | `RubricConfig` model, YAML loader, validation, default rubric |
| `md_evals/rubric_default.yaml` | Built-in default rubric shipped with package |
| `apps/web/src/components/DimensionRadar.tsx` | Radar chart for dimension scores |
| `apps/web/src/components/GradeBadge.tsx` | Letter grade display component (S=gold, A=green, etc.) |
| `tests/test_scoring.py` | Unit tests for grade calculation, score normalization |
| `tests/test_precheck.py` | Unit tests for pre-check engine, security patterns |
| `tests/test_rubric.py` | Unit tests for rubric loading, validation, weight sums |
| `tests/fixtures/rubric_*.yaml` | Test fixture rubrics (valid, invalid weights, custom dimensions) |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Grade thresholds feel arbitrary** | High | Medium | Ship defaults but make fully configurable via `rubric.yaml`; document rationale; let teams tune |
| **LLM judges can't reliably score 7 dimensions at once** | Medium | High | Phase 1 only builds the data model and grade functions — actual LLM prompt decomposition is Phase 2. For now, dimensions can be populated from existing `EvaluatorResult.score` |
| **Weight configuration UX is confusing** | Medium | Medium | Validate weights sum to 1.0 with clear error messages; provide examples in `rubric.yaml` comments |
| **Security pattern false positives** | High | Low | Default patterns are conservative (high precision, lower recall); `severity: "warning"` doesn't block the eval — only `severity: "error"` does |
| **Pre-check kills useful evals** | Low | Medium | Pre-check failures are advisory in Phase 1 (logged, not blocking by default); `--force` flag bypasses |
| **`EvalResult` shape locks us in prematurely** | Medium | High | Use `evidence: list[str]` (generic) instead of typed citation objects; keep `execution_results` as escape hatch; `EvalMetadata` wraps existing metrics rather than replacing |
| **Rubric YAML is yet another config file** | Low | Low | Falls back to built-in default if no file present; resolution chain is CLI flag → CWD → built-in |
| **Breaking 457+ existing tests** | Low | High | All changes are additive — new modules, new CLI command, new models. Zero modifications to existing modules. Run full test suite in CI before merge |

---

## Acceptance Criteria

1. **`DimensionScore` and `EvalResult` models exist** in `md_evals/scoring.py` with the fields specified in the data model section, importable and constructible.

2. **Grade calculation is correct**: `calculate_overall_grade()` returns the correct weighted score and letter grade for all boundary values (0.0, 0.29, 0.30, 0.49, 0.50, 0.69, 0.70, 0.84, 0.85, 0.94, 0.95, 1.0).

3. **Grade calculation is a pure function**: No I/O, no side effects, no global state. Verified by calling from multiple threads without locking.

4. **Default rubric loads successfully**: `RubricLoader.load_default()` returns a valid `RubricConfig` with 7 dimensions whose weights sum to 1.0.

5. **Custom rubric loads from YAML**: `RubricLoader.load("custom-rubric.yaml")` parses a valid rubric file and validates weight sum, dimension names, and grade thresholds.

6. **Invalid rubric is rejected with clear error**: Loading a rubric with weights summing to 0.8 raises `RubricValidationError` with a message containing the actual sum.

7. **Pre-check detects missing sections**: Running `PreCheckEngine.run()` on a SKILL.md missing "Examples" produces a finding with `check="required_sections"` and `severity="warning"`.

8. **Pre-check detects security anti-patterns**: A SKILL.md containing `api_key = "sk-12345"` produces a finding with `check="security_antipattern"` and `severity="error"`.

9. **Pre-check detects overly permissive patterns**: A SKILL.md containing `chmod 777` produces a finding with `severity="warning"`.

10. **`md-evals check` CLI command works**: Running `md-evals check tests/fixtures/valid_skill.md` exits with code 0 and prints a PASSED summary. Running against a broken fixture exits with code 2 and prints findings.

11. **Pre-check reuses `LinterEngine`**: The `PreCheckEngine` delegates to `LinterEngine` for max-lines, empty-file, and long-line checks — no rule duplication.

12. **Radar chart renders**: The `<DimensionRadar>` component renders a Recharts `RadarChart` with 7 axes when given valid `DimensionScore[]` data.

13. **JSON output includes `EvalResult`**: When `--output json` is used, the JSON report contains an `eval_result` key with `overall_grade`, `overall_score`, `dimensions`, and `pre_check`.

14. **Existing tests pass**: All 457+ existing tests continue to pass without modification.

15. **New tests added**: At least 30 new tests covering scoring, pre-check, and rubric loading, including Hypothesis property-based tests for grade boundary invariants.

16. **No breaking changes to existing models**: `ExecutionResult`, `EvaluatorResult`, `LLMResponse`, `EvalConfig` are unchanged. Verified by diffing `md_evals/models.py`.

---

## Open Questions

1. **Should pre-check block LLM eval by default or be advisory?** Current proposal: advisory in Phase 1 (logged, reported, but doesn't prevent LLM eval). Phase 2 pipeline makes it a gate. User preference?

2. **`rubric.yaml` location**: Should the default rubric live inside the package (`md_evals/rubric_default.yaml`, shipped via `package_data`) or as a dotfile (`~/.md-evals/rubric.yaml`)? Package-internal is simpler but harder to discover.

3. **S-grade: is it needed?** Many rubrics use A–F. The S-grade (0.95+) distinguishes "excellent" from "reference quality". Keep it, or simplify to A–F?

4. **Should `md-evals check` be a standalone command or a `--pre-check` flag on `md-evals run`?** Current proposal: both — standalone `check` command + `--pre-check` / `--no-pre-check` on `run` (default: enabled when rubric has pre-check config).

5. **Dimension naming**: Should dimensions use fixed enum values (`correctness`, `completeness`, ...) or be fully user-defined strings? Fixed enums enable typed handling; free strings enable custom rubrics with arbitrary dimensions.

6. **How should the API (FastAPI) expose `EvalResult`?** New endpoint (`/api/evals/{id}/scoring`) or embedded in the existing eval results response? This affects the web frontend contract.

---

## Estimated Effort

| Component | Effort |
|-----------|--------|
| Data models (`scoring.py`) | 0.5 days |
| Rubric loader + validation (`rubric.py`) | 1 day |
| Grade calculation + pure functions | 0.5 days |
| Pre-check engine (`precheck.py`) | 1–1.5 days |
| CLI `check` command | 0.5 days |
| JSON reporter extension | 0.5 days |
| Radar chart + grade badge (web) | 1 day |
| Tests (unit + property-based) | 1.5–2 days |
| Documentation + rubric examples | 0.5 days |
| **Total estimated** | **~7–8 days** |
