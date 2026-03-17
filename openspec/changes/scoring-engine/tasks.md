# Tasks: Phase 1 — The Scoring Engine

> **Status**: COMPLETED
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: scoring-engine
> **Spec**: [spec.md](./spec.md)
> **Proposal**: [proposal.md](./proposal.md)

---

## Summary

- **Total tasks**: 40
- **Phases**: 10 (A through J)
- **Estimated effort**: ~7–8 days

---

## Phase A: Data Foundation

_New types and models for scoring. No dependencies on other phases._

### T-01 — Create `DimensionScore` frozen dataclass
- [x] **Description**: Create `md_evals/scoring.py` with the `DimensionScore` frozen dataclass. Fields: `dimension` (str), `score` (float 0.0–1.0), `weight` (float), `grade` (str S/A/B/C/D/F), `evidence` (list[str], default_factory=list). Include `from __future__ import annotations` import.
- **Files**: `md_evals/scoring.py` (NEW)
- **Depends on**: —
- **Acceptance Criteria**: AC-01, AC-04, AC-06, AC-07
- **Effort**: S

### T-02 — Create `EvalMetadata` dataclass
- [x] **Description**: Add `EvalMetadata` dataclass to `md_evals/scoring.py`. Fields: `model`, `provider`, `cost_metrics` (CostMetrics | None), `context_metrics` (ContextMetrics | None), `total_duration_ms`, `pre_check_duration_ms`, `llm_duration_ms`, `timestamp` (str ISO 8601). Import `CostMetrics` and `ContextMetrics` from `md_evals/metrics.py`.
- **Files**: `md_evals/scoring.py`
- **Depends on**: T-01
- **Acceptance Criteria**: AC-03, AC-06, AC-08
- **Effort**: S

### T-03 — Create `EvalResult` dataclass
- [x] **Description**: Add `EvalResult` dataclass to `md_evals/scoring.py`. Fields: `skill_path`, `overall_grade`, `overall_score`, `dimensions` (list[DimensionScore]), `pre_check` (PreCheckResult | None), `metadata` (EvalMetadata), `execution_results` (list[Any] | None = None). Use forward reference for `PreCheckResult` since it lives in `md_evals/precheck.py`.
- **Files**: `md_evals/scoring.py`
- **Depends on**: T-01, T-02
- **Acceptance Criteria**: AC-01, AC-06, AC-08
- **Effort**: S

### T-04 — Create `PreCheckFinding` and `PreCheckResult` frozen dataclasses
- [x] **Description**: Create `md_evals/precheck.py` with `PreCheckFinding` (frozen: `check`, `message`, `severity`, `line: int | None = None`) and `PreCheckResult` (frozen: `passed`, `findings`, `checks_run`, `duration_ms`). Both are `@dataclass(frozen=True)`.
- **Files**: `md_evals/precheck.py` (NEW)
- **Depends on**: —
- **Acceptance Criteria**: AC-02, AC-05, AC-06
- **Effort**: S

### T-05 — Verify no circular imports
- [x] **Description**: Add a simple smoke test (or script) that imports `md_evals.scoring`, `md_evals.precheck`, and `md_evals.rubric` (once created) in every permutation order. Ensure no `ImportError`. Resolve the `PreCheckResult` forward reference in `EvalResult` using `from __future__ import annotations` or a TYPE_CHECKING guard.
- **Files**: `md_evals/scoring.py`, `md_evals/precheck.py`, `tests/test_scoring.py`
- **Depends on**: T-01, T-02, T-03, T-04
- **Acceptance Criteria**: AC-08
- **Effort**: S

---

## Phase B: Rubric System

_RubricConfig Pydantic model, YAML loader, validation logic, default rubric file, and custom exceptions._

### T-06 — Create exception hierarchy in `md_evals/rubric.py`
- [x] **Description**: Create `md_evals/rubric.py` with `RubricError(Exception)`, `RubricValidationError(RubricError)`, and `RubricNotFoundError(RubricError)`. These follow the pattern of `ConfigLoaderError` in `md_evals/config.py`.
- **Files**: `md_evals/rubric.py` (NEW)
- **Depends on**: —
- **Acceptance Criteria**: AC-16, AC-17, AC-18, AC-19
- **Effort**: S

### T-07 — Create `RubricConfig` Pydantic models
- [x] **Description**: Add Pydantic models to `md_evals/rubric.py`: `SecurityPattern` (pattern, message, severity), `PreCheckConfig` (required_sections, max_lines, security_patterns), `DimensionConfig` (weight, description), `RubricConfig` (version, dimensions dict, grade_thresholds dict, pre_check). Follow the Pydantic `BaseModel` pattern used by `EvalConfig` in `md_evals/models.py`.
- **Files**: `md_evals/rubric.py`
- **Depends on**: T-06
- **Acceptance Criteria**: AC-14, AC-15
- **Effort**: S

### T-08 — Implement rubric validation logic
- [x] **Description**: Add a `validate()` classmethod or post-init validator to `RubricConfig` that enforces: (1) weights sum to 1.0 ±0.001, (2) grade thresholds strictly monotonically decreasing, (3) thresholds in (0.0, 1.0], (4) A/B/C/D required, S optional, (5) security patterns compile as valid regex, (6) at least 1 dimension, (7) version == "1.0", (8) warn (log) if custom dimension lacks description. Raise `RubricValidationError` with descriptive messages including actual values.
- **Files**: `md_evals/rubric.py`
- **Depends on**: T-07
- **Acceptance Criteria**: AC-16, AC-17, AC-18, AC-19
- **Effort**: M

### T-09 — Create default rubric YAML file
- [x] **Description**: Create `md_evals/rubric_default.yaml` with the 7 default dimensions (correctness 0.25, completeness 0.20, format 0.15, adherence 0.15, safety 0.10, efficiency 0.10, robustness 0.05), default grade thresholds (S=0.95, A=0.85, B=0.70, C=0.50, D=0.30), and default pre_check config with 3 security patterns. Include YAML comments explaining each field.
- **Files**: `md_evals/rubric_default.yaml` (NEW)
- **Depends on**: T-07
- **Acceptance Criteria**: AC-14
- **Effort**: S

### T-10 — Implement `RubricLoader` with resolution chain
- [x] **Description**: Add `RubricLoader` class to `md_evals/rubric.py` with methods: `load(path) -> RubricConfig` (parse YAML, validate), `load_default() -> RubricConfig` (load built-in default), `resolve(cli_rubric=None) -> RubricConfig` (resolution chain: CLI flag -> CWD `rubric.yaml` -> `~/.md-evals/rubric.yaml` -> built-in default). Handle file-not-found with `RubricNotFoundError`, invalid YAML with `RubricValidationError`, empty file with `RubricValidationError`.
- **Files**: `md_evals/rubric.py`
- **Depends on**: T-08, T-09
- **Acceptance Criteria**: AC-14, AC-15, AC-20
- **Effort**: M

### T-11 — Configure package data for default rubric
- [x] **Description**: Update `pyproject.toml` to include `md_evals/rubric_default.yaml` in the package distribution via `[tool.hatch.build.targets.wheel]` or equivalent config. Verify the file is accessible at runtime via `Path(__file__).parent / "rubric_default.yaml"`.
- **Files**: `pyproject.toml`
- **Depends on**: T-09
- **Acceptance Criteria**: AC-14
- **Effort**: S

---

## Phase C: Pre-check Engine

_PreCheckEngine wrapping LinterEngine + security pattern checks._

### T-12 — Implement security pattern checker
- [x] **Description**: Add a `SecurityPatternCheck` class (or function) inside `md_evals/precheck.py` that takes a compiled regex pattern and scans file content line-by-line, returning `PreCheckFinding` objects with the correct `check="security_antipattern"`, `severity` from the pattern config, and `line` number (1-indexed).
- **Files**: `md_evals/precheck.py`
- **Depends on**: T-04, T-07
- **Acceptance Criteria**: AC-22, AC-23
- **Effort**: M

### T-13 — Implement `PreCheckEngine` class
- [x] **Description**: Create `PreCheckEngine` class in `md_evals/precheck.py`. Constructor takes `RubricConfig`, initializes `LinterEngine` (from `md_evals/linter.py`) with `LinterConfig(max_lines=rubric.pre_check.max_lines, fail_on_violation=True)` and compiles security patterns once. The `run(skill_path) -> PreCheckResult` method: (1) delegates to `LinterEngine.run()` to get `LinterReport`, (2) converts `LinterViolation` objects to `PreCheckFinding` objects, (3) runs security pattern checks, (4) aggregates into `PreCheckResult` with timing, check count, and `passed` logic (False if any error-severity finding).
- **Files**: `md_evals/precheck.py`
- **Depends on**: T-04, T-10, T-12
- **Acceptance Criteria**: AC-21, AC-22, AC-23, AC-24, AC-25, AC-26, AC-27
- **Effort**: L

### T-14 — Handle edge cases in PreCheckEngine
- [x] **Description**: Ensure `PreCheckEngine.run()` handles: file not found (finding with `check="file_not_found"`, severity=error), read error / non-UTF-8 (finding with `check="read_error"`, severity=error), empty file (delegates to `EmptyFileRule` via LinterEngine), very large files (no O(n^2) behavior). No unhandled exceptions escape — always return `PreCheckResult`.
- **Files**: `md_evals/precheck.py`
- **Depends on**: T-13
- **Acceptance Criteria**: AC-24, AC-25
- **Effort**: M

---

## Phase D: Grade Calculation

_Pure functions for scoring: `score_to_grade`, `calculate_overall_grade`._

### T-15 — Implement `score_to_grade` pure function
- [x] **Description**: Add `score_to_grade(score: float, thresholds: dict[str, float]) -> str` to `md_evals/scoring.py`. Checks thresholds in descending order: S (if present), A, B, C, D. Score >= threshold gets that grade. Below D -> "F". When S is not in thresholds, skip it (max grade is A). Clamp input score to [0.0, 1.0].
- **Files**: `md_evals/scoring.py`
- **Depends on**: T-01
- **Acceptance Criteria**: AC-09, AC-11, AC-12, AC-13
- **Effort**: S

### T-16 — Implement `calculate_overall_grade` pure function
- [x] **Description**: Add `calculate_overall_grade(dimensions: list[DimensionScore], thresholds: dict[str, float]) -> tuple[float, str]` to `md_evals/scoring.py`. Computes weighted average `sum(d.score * d.weight for d in dimensions)`, then calls `score_to_grade`. Raise `ValueError` if dimensions list is empty. This function has no I/O, no side effects, no global state.
- **Files**: `md_evals/scoring.py`
- **Depends on**: T-01, T-15
- **Acceptance Criteria**: AC-09, AC-10
- **Effort**: S

### T-17 — Implement helper to build `DimensionScore` list from rubric
- [x] **Description**: Add a helper function `build_dimension_scores(scores: dict[str, float], rubric: RubricConfig, thresholds: dict[str, float]) -> list[DimensionScore]` to `md_evals/scoring.py`. Given a dict of dimension_name -> raw_score and a rubric, constructs `DimensionScore` objects with the correct weight, clamped score, and individual grade computed via `score_to_grade`. This bridges the gap between raw LLM scores (Phase 2) and the typed `DimensionScore` list.
- **Files**: `md_evals/scoring.py`
- **Depends on**: T-15, T-07
- **Acceptance Criteria**: AC-01, GC-05, GC-06
- **Effort**: S

---

## Phase E: CLI Integration

_New `check` command, new flags on `run`, `init` extension._

### T-18 — Add `md-evals check` command
- [x] **Description**: Add a new `check` Typer command to `md_evals/cli.py`. Arguments: `SKILL_PATH` (required). Options: `--rubric PATH`, `--verbose/-v`. Loads rubric via `RubricLoader.resolve(rubric_path)`, creates `PreCheckEngine`, runs `engine.run(skill_path)`, prints structured output (PASSED/FAILED, check count, finding count, duration). Exit code 0 = passed, 1 = config error, 2 = pre-check failed. Follow the pattern of the existing `lint` command.
- **Files**: `md_evals/cli.py`
- **Depends on**: T-10, T-13
- **Acceptance Criteria**: AC-28, AC-29, AC-30
- **Effort**: M

### T-19 — Add `--rubric`, `--force`, `--no-pre-check` flags to `run` command
- [x] **Description**: Extend the existing `run` command in `md_evals/cli.py` with three new options: `--rubric PATH` (loads custom rubric), `--no-pre-check` (skips pre-check entirely, sets `EvalResult.pre_check = None`), `--force` (runs LLM eval even on pre-check errors, passes all findings as context). Implement flag interaction logic per spec §7.2. When `--no-pre-check` is given together with `--force`, `--no-pre-check` takes precedence.
- **Files**: `md_evals/cli.py`
- **Depends on**: T-10, T-13, T-18
- **Acceptance Criteria**: AC-31, AC-32
- **Effort**: M

### T-20 — Extend `md-evals init` to generate `rubric.yaml`
- [x] **Description**: Extend the `init` command in `md_evals/cli.py` to also generate a `rubric.yaml` file alongside the existing `eval.yaml` and `SKILL.md`. The generated rubric should contain the default configuration with explanatory YAML comments. Print `Created rubric.yaml` on success. Skip if `rubric.yaml` already exists (unless `--force`).
- **Files**: `md_evals/cli.py`
- **Depends on**: T-09
- **Acceptance Criteria**: AC-33
- **Effort**: S

---

## Phase F: Web UI

_DimensionRadar chart, GradeBadge component, TypeScript types._

### T-21 — Add TypeScript scoring types
- [x] **Description**: Add new interfaces to `apps/web/src/lib/types.ts`: `DimensionScoreDTO` (dimension, score, weight, grade, evidence), `PreCheckFindingDTO` (check, message, severity, line), `PreCheckResultDTO` (passed, findings, checks_run, duration_ms), `EvalResultScoring` (overall_grade, overall_score, dimensions, pre_check). Add optional `scoring?: EvalResultScoring | null` field to the existing `Evaluation` interface.
- **Files**: `apps/web/src/lib/types.ts`
- **Depends on**: —
- **Acceptance Criteria**: AC-36
- **Effort**: S

### T-22 — Create `DimensionRadar` component
- [x] **Description**: Create `apps/web/src/components/charts/DimensionRadar.tsx`. Uses Recharts `RadarChart`, `Radar`, `PolarGrid`, `PolarAngleAxis`, `PolarRadiusAxis`. Props: `dimensions: DimensionScoreDTO[]`. Maps dimension data to chart-compatible format. Domain [0, 1]. Renders dynamically for 3–15 dimensions. Follow the component patterns in existing chart components (`PassRateChart`, `TokenUsageChart`).
- **Files**: `apps/web/src/components/charts/DimensionRadar.tsx` (NEW)
- **Depends on**: T-21
- **Acceptance Criteria**: AC-34, WU-04, WU-05
- **Effort**: M

### T-23 — Create `GradeBadge` component
- [x] **Description**: Create `apps/web/src/components/charts/GradeBadge.tsx`. Props: `grade: string`, optional `size`. Displays the letter grade with color-coded background: S=gold/amber, A=green, B=blue, C=yellow, D=orange, F=red. Use Tailwind classes following existing styling patterns (e.g., `StatusBadge` in `Dashboard.tsx`). Uses `cn()` utility.
- **Files**: `apps/web/src/components/charts/GradeBadge.tsx` (NEW)
- **Depends on**: T-21
- **Acceptance Criteria**: AC-35
- **Effort**: S

---

## Phase G: API Integration

_Expand parameter on GET endpoint, Pydantic response schemas, scoring data storage._

### T-24 — Add Pydantic scoring response schemas
- [x] **Description**: Add new Pydantic models to `apps/server/app/models/schemas.py`: `DimensionScoreResponse`, `PreCheckFindingResponse`, `PreCheckResultResponse`, `ScoringResponse` (overall_grade, overall_score, dimensions, pre_check). Add optional `scoring: ScoringResponse | None = None` field to the existing `EvalDetailResponse`.
- **Files**: `apps/server/app/models/schemas.py`
- **Depends on**: —
- **Acceptance Criteria**: AC-37, AC-38
- **Effort**: S

### T-25 — Implement `expand` query parameter on `GET /api/eval/{eval_id}`
- [x] **Description**: Modify `get_eval` in `apps/server/app/routes/eval.py` to accept `expand: str | None = Query(default=None)`. Parse comma-separated values, trim, lowercase. When `"scoring"` is in the expand list, extract scoring data from the `Evaluation.results` JSONB column's `scoring` key and populate `EvalDetailResponse.scoring`. Unknown expand values are silently ignored. Without `expand`, the response is identical to the current response (backward compatible).
- **Files**: `apps/server/app/routes/eval.py`
- **Depends on**: T-24
- **Acceptance Criteria**: AC-37, AC-38, AC-39
- **Effort**: M

### T-26 — Store scoring data in results JSONB
- [x] **Description**: Ensure that when an eval completes with scoring data, the `EvalResult` serialization is stored under the `scoring` key in the `Evaluation.results` JSONB column. This involves adding a serialization helper (e.g., `EvalResult.to_dict()` or using `dataclasses.asdict()`) in `md_evals/scoring.py` and wiring it in the eval service where results are persisted. No database migration needed — `results` is already JSONB.
- **Files**: `md_evals/scoring.py`, `apps/server/app/services/eval_service.py`
- **Depends on**: T-03, T-25
- **Acceptance Criteria**: AP-05
- **Effort**: M

---

## Phase H: Reporter Integration

_JSON output with EvalResult, terminal grade display._

### T-27 — Add `EvalResult` serialization to JSON reporter
- [x] **Description**: Extend `Reporter._build_output_data()` in `md_evals/reporter.py` to include an `eval_result` key at the top level when scoring data is available. The key contains `overall_grade`, `overall_score`, `dimensions[]` (each with dimension, score, weight, grade, evidence), and `pre_check` (passed, findings, checks_run, duration_ms). Existing keys (`results`, `summary`, `usage_metrics`) remain unchanged.
- **Files**: `md_evals/reporter.py`
- **Depends on**: T-03, T-16
- **Acceptance Criteria**: AC-40
- **Effort**: M

### T-28 — Add grade summary to terminal reporter
- [x] **Description**: Add an optional grade summary section to `Reporter.report_terminal()` that displays overall grade and per-dimension grades when `EvalResult` data is available. Use Rich formatting with color-coded grades (matching GradeBadge colors). This is an additive display section — existing pass/fail tables remain unchanged.
- **Files**: `md_evals/reporter.py`
- **Depends on**: T-16, T-27
- **Acceptance Criteria**: AC-40
- **Effort**: S

---

## Phase I: Tests

_Unit tests, property-based tests, fixtures, integration tests._

### T-29 — Create test fixture YAML files for rubric tests
- [x] **Description**: Create test fixture rubric files: `tests/fixtures/rubric_default.yaml` (copy of built-in default), `tests/fixtures/rubric_invalid_weights.yaml` (weights sum to 0.80), `tests/fixtures/rubric_custom_dimensions.yaml` (5 builtin + 2 custom with descriptions), `tests/fixtures/rubric_no_s_grade.yaml` (A through D only, no S threshold), `tests/fixtures/rubric_bad_regex.yaml` (invalid security pattern regex), `tests/fixtures/rubric_non_monotonic.yaml` (A=0.85, B=0.90).
- **Files**: `tests/fixtures/rubric_*.yaml` (NEW, 6 files)
- **Depends on**: T-09
- **Acceptance Criteria**: AC-46
- **Effort**: S

### T-30 — Create test fixture SKILL.md files
- [x] **Description**: Create test fixture skill files: `tests/fixtures/skill_with_secret.md` (contains `api_key = "sk-12345abcdef"`), `tests/fixtures/skill_with_shell.md` (contains `os.system("rm -rf /tmp/cache")`), `tests/fixtures/skill_empty.md` (0 bytes empty file), `tests/fixtures/skill_missing_sections.md` (only Description, no Rules/Examples).
- **Files**: `tests/fixtures/skill_*.md` (NEW, 4 files)
- **Depends on**: —
- **Acceptance Criteria**: AC-46
- **Effort**: S

### T-31 — Write unit tests for `scoring.py` (DimensionScore, EvalResult, EvalMetadata)
- [x] **Description**: Create `tests/test_scoring.py` with tests: frozen immutability of `DimensionScore` (set field raises `FrozenInstanceError`), evidence defaults to empty list, `EvalResult` construction with all fields, `EvalMetadata` references `CostMetrics`/`ContextMetrics` correctly, stdlib dataclass verification (not Pydantic). Use class-based test organization matching the pattern in `tests/test_linter.py`.
- **Files**: `tests/test_scoring.py` (NEW)
- **Depends on**: T-01, T-02, T-03
- **Acceptance Criteria**: AC-01, AC-03, AC-04, AC-06, AC-07
- **Effort**: M

### T-32 — Write unit tests for grade calculation functions
- [x] **Description**: Add tests to `tests/test_scoring.py` for `score_to_grade` and `calculate_overall_grade`. Test all 12 boundary values (0.0->F, 0.29->F, 0.30->D, 0.49->D, 0.50->C, 0.69->C, 0.70->B, 0.84->B, 0.85->A, 0.94->A, 0.95->S, 1.0->S). Test S-grade omitted scenario (0.99 -> A). Test empty dimensions raises `ValueError`. Test the scenario from spec §2.1 (weighted average = 0.8275 -> B).
- **Files**: `tests/test_scoring.py`
- **Depends on**: T-15, T-16, T-31
- **Acceptance Criteria**: AC-09, AC-10, AC-11
- **Effort**: M

### T-33 — Write Hypothesis property-based tests for grade functions
- [x] **Description**: Add Hypothesis-based property tests to `tests/test_scoring.py`: (1) for any score in [0.0, 1.0], `score_to_grade` always returns one of S/A/B/C/D/F, (2) monotonicity: if score_a > score_b then grade_rank(grade_a) >= grade_rank(grade_b), (3) weight-sum invariant: for any valid weights summing to 1.0 and scores in [0.0, 1.0], overall_score is in [0.0, 1.0]. Use `hypothesis` (already in dev deps in `pyproject.toml`).
- **Files**: `tests/test_scoring.py`
- **Depends on**: T-15, T-16
- **Acceptance Criteria**: AC-12, AC-13, AC-45
- **Effort**: M

### T-34 — Write concurrency test for grade calculation
- [x] **Description**: Add a test to `tests/test_scoring.py` using `concurrent.futures.ThreadPoolExecutor` with 100 concurrent calls to `calculate_overall_grade` with different inputs. Verify all return correct results with no race conditions. This validates the "pure function" guarantee.
- **Files**: `tests/test_scoring.py`
- **Depends on**: T-16
- **Acceptance Criteria**: AC-10
- **Effort**: S

### T-35 — Write unit tests for rubric loading and validation
- [x] **Description**: Create `tests/test_rubric.py` with tests: `load_default()` returns 7 dimensions with weights summing to 1.0, loading custom rubric file works, invalid weights (sum=0.80) raises `RubricValidationError` with "0.80", duplicate dimension names rejected, non-monotonic thresholds rejected, invalid regex rejected, empty rubric file rejected, rubric resolution chain (4 test cases: CLI flag wins, CWD wins, home dir wins, built-in default). Custom dimension without description emits warning but loads.
- **Files**: `tests/test_rubric.py` (NEW)
- **Depends on**: T-10, T-29
- **Acceptance Criteria**: AC-14, AC-15, AC-16, AC-17, AC-18, AC-19, AC-20
- **Effort**: L

### T-36 — Write unit tests for PreCheckEngine
- [x] **Description**: Create `tests/test_precheck.py` with tests: clean skill passes, missing sections produce warnings (not errors), hardcoded secret produces error finding with correct line number, `chmod 777` produces warning, empty file produces error, file not found returns `PreCheckResult(passed=False)`, LinterEngine delegation verified (MaxLinesRule/EmptyFileRule/VeryLongLineRule violations appear as PreCheckFinding), `checks_run` count is accurate, `duration_ms > 0`, multiple findings on same line.
- **Files**: `tests/test_precheck.py` (NEW)
- **Depends on**: T-13, T-14, T-30
- **Acceptance Criteria**: AC-21, AC-22, AC-23, AC-24, AC-25, AC-26, AC-27
- **Effort**: L

### T-37 — Write CLI integration tests for `check` command
- [x] **Description**: Add tests to `tests/test_cli.py` (or create `tests/test_cli_check.py`) using Typer's `CliRunner` for: `md-evals check tests/fixtures/skill_short.md` exits 0 with "PASSED", `md-evals check tests/fixtures/skill_with_secret.md` exits 2 with "FAILED" and "[ERROR]", `md-evals check --rubric custom.yaml SKILL.md` uses custom rubric. Follow the testing pattern already established in `tests/test_cli.py`.
- **Files**: `tests/test_cli.py` or `tests/test_cli_check.py` (NEW)
- **Depends on**: T-18, T-30
- **Acceptance Criteria**: AC-28, AC-29, AC-30
- **Effort**: M

### T-38 — Write CLI integration tests for `run` new flags
- [x] **Description**: Add tests for the new `run` flags: `--no-pre-check` skips pre-check entirely, `--force` runs LLM eval even on pre-check errors, `--rubric custom.yaml` loads custom rubric. These can use mocked LLM adapters. Verify `EvalResult.pre_check` is `None` with `--no-pre-check`, and that findings are present with `--force`.
- **Files**: `tests/test_cli_flags.py` or `tests/test_cli.py`
- **Depends on**: T-19
- **Acceptance Criteria**: AC-31, AC-32
- **Effort**: M

---

## Phase J: Documentation & Polish

_Default rubric comments, init generation quality, backward compatibility verification._

### T-39 — Verify backward compatibility (zero modifications to existing modules)
- [x] **Description**: Add a verification step (can be a test or CI check): `git diff md_evals/models.py`, `git diff md_evals/linter.py`, `git diff md_evals/metrics.py`, `git diff md_evals/config.py` all show zero modifications. Run the full existing test suite (`pytest` without new test files) and confirm all 457+ tests pass. This is a gate before merging.
- **Files**: `md_evals/models.py`, `md_evals/linter.py`, `md_evals/metrics.py`, `md_evals/config.py`
- **Depends on**: All previous tasks
- **Acceptance Criteria**: AC-41, AC-42, AC-43
- **Effort**: S

### T-40 — Polish default rubric YAML with documentation comments
- [x] **Description**: Ensure `md_evals/rubric_default.yaml` has thorough YAML comments explaining: what each dimension measures, how weights affect scoring, what each grade threshold means, how security patterns work and how to add custom ones. Also ensure the `rubric.yaml` generated by `md-evals init` (T-20) includes these same helpful comments. Review the generated file for clarity and completeness.
- **Files**: `md_evals/rubric_default.yaml`, `md_evals/cli.py` (init command template)
- **Depends on**: T-09, T-20
- **Acceptance Criteria**: AC-33
- **Effort**: S

---

## Dependency Graph

```
Phase A (Data Foundation)      Phase B (Rubric System)
  T-01 ─┬─ T-02 ─ T-03         T-06 ─ T-07 ─┬─ T-08 ─ T-10
         │                                     │         ↑
         └─ T-05                    T-09 ──────┘── T-11
         │
  T-04 ──┘                   Phase C (Pre-check)
                               T-12 ─┬─ T-13 ─ T-14
                                     │
Phase D (Grade Calc)          Phase E (CLI)
  T-15 ─ T-16                 T-18 ─ T-19
  T-17                        T-20

Phase F (Web UI)              Phase G (API)
  T-21 ─┬─ T-22              T-24 ─ T-25 ─ T-26
         └─ T-23

Phase H (Reporter)            Phase I (Tests)
  T-27 ─ T-28                T-29, T-30 (fixtures, parallel)
                              T-31 ─ T-32 ─ T-33, T-34
                              T-35, T-36, T-37, T-38

Phase J (Polish)
  T-39, T-40
```

## Cross-Phase Dependencies

| Task | Depends on (cross-phase) |
|------|--------------------------|
| T-12 (security checker) | T-04 (Phase A: PreCheckFinding), T-07 (Phase B: RubricConfig) |
| T-13 (PreCheckEngine) | T-10 (Phase B: RubricLoader) |
| T-17 (build_dimension_scores) | T-07 (Phase B: RubricConfig) |
| T-18 (check CLI) | T-10 (Phase B: RubricLoader), T-13 (Phase C: PreCheckEngine) |
| T-19 (run flags) | T-10 (Phase B), T-13 (Phase C) |
| T-26 (storage) | T-03 (Phase A), T-25 (Phase G: expand) |
| T-27 (JSON reporter) | T-03 (Phase A), T-16 (Phase D) |
| T-35 (rubric tests) | T-10 (Phase B), T-29 (Phase I fixtures) |
| T-36 (precheck tests) | T-13 (Phase C), T-30 (Phase I fixtures) |
| T-37 (CLI check tests) | T-18 (Phase E), T-30 (Phase I fixtures) |

## Parallelization Opportunities

These task groups can be worked on **in parallel** by different developers:

1. **Phase A + Phase D** (scoring types + grade functions) — same file, one developer
2. **Phase B** (rubric system) — independent developer
3. **Phase F** (web UI) — frontend developer, only needs T-21 types first
4. **Phase G** (API) — backend developer, independent of Python CLI work
5. **Phase I fixtures** (T-29, T-30) — can start immediately, no dependencies

## AC Coverage Matrix

| AC | Task(s) |
|----|---------|
| AC-01 | T-01, T-03, T-31 |
| AC-02 | T-04, T-36 |
| AC-03 | T-02, T-31 |
| AC-04 | T-01, T-31 |
| AC-05 | T-04, T-36 |
| AC-06 | T-01, T-02, T-03, T-04, T-31 |
| AC-07 | T-01, T-31 |
| AC-08 | T-05 |
| AC-09 | T-15, T-16, T-32 |
| AC-10 | T-16, T-34 |
| AC-11 | T-15, T-32 |
| AC-12 | T-33 |
| AC-13 | T-33 |
| AC-14 | T-09, T-10, T-11, T-35 |
| AC-15 | T-10, T-35 |
| AC-16 | T-08, T-35 |
| AC-17 | T-08, T-35 |
| AC-18 | T-08, T-35 |
| AC-19 | T-08, T-35 |
| AC-20 | T-10, T-35 |
| AC-21 | T-13, T-36 |
| AC-22 | T-12, T-13, T-36 |
| AC-23 | T-12, T-13, T-36 |
| AC-24 | T-14, T-36 |
| AC-25 | T-13, T-36 |
| AC-26 | T-13, T-36 |
| AC-27 | T-13, T-36 |
| AC-28 | T-18, T-37 |
| AC-29 | T-18, T-37 |
| AC-30 | T-18, T-37 |
| AC-31 | T-19, T-38 |
| AC-32 | T-19, T-38 |
| AC-33 | T-20, T-40 |
| AC-34 | T-22 |
| AC-35 | T-23 |
| AC-36 | T-21 |
| AC-37 | T-24, T-25 |
| AC-38 | T-25 |
| AC-39 | T-25 |
| AC-40 | T-27, T-28 |
| AC-41 | T-39 |
| AC-42 | T-39 |
| AC-43 | T-39 |
| AC-44 | T-31–T-38 (35+ tests across all test tasks) |
| AC-45 | T-33 |
| AC-46 | T-29, T-30 |
