# Spec: Phase 1 — The Scoring Engine

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: scoring-engine
> **Phase**: 1 of 5
> **Proposal**: [proposal.md](./proposal.md)

---

## Table of Contents

1. [Requirements](#1-requirements)
2. [Scenarios](#2-scenarios)
3. [Acceptance Criteria](#3-acceptance-criteria)
4. [Edge Cases](#4-edge-cases)
5. [Data Model](#5-data-model)
6. [Configuration](#6-configuration)
7. [CLI Specification](#7-cli-specification)
8. [API Specification](#8-api-specification)
9. [Error Handling](#9-error-handling)
10. [Backward Compatibility](#10-backward-compatibility)

---

## 1. Requirements

### 1.1 Data Model

| ID | Requirement | Priority |
|----|-------------|----------|
| DM-01 | `DimensionScore` frozen dataclass in `md_evals/scoring.py` with fields: `dimension` (str), `score` (float 0.0–1.0), `weight` (float 0.0–1.0), `grade` (str S/A/B/C/D/F), `evidence` (list[str], empty until Phase 3) | MUST |
| DM-02 | `PreCheckFinding` frozen dataclass in `md_evals/precheck.py` with fields: `check` (str), `message` (str), `severity` ("error" \| "warning" \| "info"), `line` (int \| None) | MUST |
| DM-03 | `PreCheckResult` frozen dataclass in `md_evals/precheck.py` with fields: `passed` (bool), `findings` (list[PreCheckFinding]), `checks_run` (int), `duration_ms` (int) | MUST |
| DM-04 | `EvalMetadata` dataclass in `md_evals/scoring.py` with fields: `model` (str), `provider` (str), `cost_metrics` (CostMetrics \| None), `context_metrics` (ContextMetrics \| None), `total_duration_ms` (int), `pre_check_duration_ms` (int), `llm_duration_ms` (int), `timestamp` (str ISO 8601) | MUST |
| DM-05 | `EvalResult` dataclass in `md_evals/scoring.py` with fields: `skill_path` (str), `overall_grade` (str), `overall_score` (float 0.0–1.0), `dimensions` (list[DimensionScore]), `pre_check` (PreCheckResult \| None), `metadata` (EvalMetadata), `execution_results` (list[Any] \| None, default None) | MUST |
| DM-06 | All new scoring types use stdlib `@dataclass` (not Pydantic), following the precedent set by `md_evals/metrics.py` (CostMetrics, ContextMetrics, etc.) | MUST |
| DM-07 | `DimensionScore` and `PreCheckFinding` are `frozen=True` for immutability | MUST |
| DM-08 | All new types are importable from their respective modules with no circular imports | MUST |

### 1.2 Rubric Configuration

| ID | Requirement | Priority |
|----|-------------|----------|
| RC-01 | `RubricConfig` Pydantic model in `md_evals/rubric.py` for parsing and validating `rubric.yaml` files | MUST |
| RC-02 | Resolution chain: CLI `--rubric` flag → `rubric.yaml` in CWD → `~/.md-evals/rubric.yaml` → built-in default (`md_evals/rubric_default.yaml` shipped with package via `package_data`) | MUST |
| RC-03 | Default rubric ships with 7 dimensions: correctness (0.25), completeness (0.20), format (0.15), adherence (0.15), safety (0.10), efficiency (0.10), robustness (0.05) | MUST |
| RC-04 | Dimension weights MUST sum to 1.0 within floating-point tolerance (±0.001) | MUST |
| RC-05 | Grade thresholds are configurable: S (0.95), A (0.85), B (0.70), C (0.50), D (0.30). Below D → F | MUST |
| RC-06 | S grade is optional in rubric: if user omits S threshold, maximum achievable grade is A | MUST |
| RC-07 | Custom string dimensions are allowed. Each custom dimension MUST include a `description` field. Warning emitted if description is missing | MUST |
| RC-08 | Builtin dimensions have optimized LLM prompts (used in Phase 2); custom dimensions use their `description` field for LLM context | SHOULD |
| RC-09 | `md-evals init` generates `rubric.yaml` in project directory with commented defaults | SHOULD |
| RC-10 | Rubric validation: no duplicate dimension names, grade thresholds monotonically decreasing, security patterns compile as valid regex | MUST |
| RC-11 | `RubricValidationError` raised with descriptive message when validation fails (including the actual weight sum, actual duplicates, etc.) | MUST |

### 1.3 Grade Calculation

| ID | Requirement | Priority |
|----|-------------|----------|
| GC-01 | `calculate_overall_grade(dimensions, thresholds)` → `(float, str)`: weighted average → letter grade. Pure function, no I/O, no side effects, no global state | MUST |
| GC-02 | `score_to_grade(score, thresholds)` → `str`: maps a single 0.0–1.0 score to a letter grade using threshold dict. Pure function | MUST |
| GC-03 | Grade boundaries: score >= threshold gets that grade. Thresholds checked in descending order: S, A, B, C, D. Scores below D threshold → F | MUST |
| GC-04 | When S is not in thresholds, grade lookup starts at A | MUST |
| GC-05 | `score_to_grade` applies to both individual dimension scores and overall weighted score | MUST |
| GC-06 | Individual `DimensionScore.grade` is computed from `DimensionScore.score` using the same thresholds | MUST |

### 1.4 Pre-check Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| PC-01 | `PreCheckEngine` class in `md_evals/precheck.py` runs deterministic checks on SKILL.md files. No LLM, no cost, <1s execution | MUST |
| PC-02 | Pre-check engine wraps/reuses existing `LinterEngine` from `md_evals/linter.py` for max-lines, empty-file, long-line, and required-sections checks — no rule duplication | MUST |
| PC-03 | Pre-check engine adds security anti-pattern checks via configurable regex patterns from `rubric.yaml` | MUST |
| PC-04 | Severity semantics: "error" findings → `PreCheckResult.passed = False`; "warning" and "info" → `passed = True` (warnings don't block) | MUST |
| PC-05 | Warnings are passed as LLM context so the LLM judge can penalize specific dimensions (e.g., missing Examples → LLM lowers Completeness score) — implemented in Phase 2 pipeline, data flow designed now | MUST |
| PC-06 | Errors (hardcoded secrets, empty file) block LLM eval by default to save tokens | MUST |
| PC-07 | `--force` flag: always runs LLM eval regardless of pre-check errors; passes ALL findings (errors + warnings) as LLM context | MUST |
| PC-08 | `--no-pre-check` flag: disables pre-check entirely; LLM eval runs unconditionally | MUST |
| PC-09 | `PreCheckEngine.run(skill_path)` returns `PreCheckResult` with structured findings, timing, and check count | MUST |
| PC-10 | Security patterns from rubric are compiled once at engine initialization and reused across runs | SHOULD |

### 1.5 CLI

| ID | Requirement | Priority |
|----|-------------|----------|
| CL-01 | New `md-evals check SKILL.md` command: runs pre-check only (no LLM, no cost) | MUST |
| CL-02 | `md-evals check` accepts `--rubric <path>` flag to specify custom rubric | MUST |
| CL-03 | `md-evals check` prints structured output: filename, PASSED/FAILED status, check count, finding count, duration | MUST |
| CL-04 | `md-evals check` exit codes: 0 = passed, 2 = pre-check failed (errors found) | MUST |
| CL-05 | `md-evals run` gains `--rubric <path>` flag | MUST |
| CL-06 | `md-evals run` gains `--no-pre-check` flag to skip pre-check | MUST |
| CL-07 | `md-evals run` gains `--force` flag to run LLM eval even on pre-check errors | MUST |
| CL-08 | `md-evals init` gains optional `rubric.yaml` generation alongside existing `eval.yaml` scaffold | SHOULD |
| CL-09 | JSON output (`--output json`) includes `eval_result` key with full `EvalResult` serialization | MUST |

### 1.6 Web UI

| ID | Requirement | Priority |
|----|-------------|----------|
| WU-01 | `<DimensionRadar>` Recharts RadarChart component in `apps/web/src/components/charts/DimensionRadar.tsx` | MUST |
| WU-02 | `<GradeBadge>` component in `apps/web/src/components/charts/GradeBadge.tsx` displaying letter grade with color coding (S=gold, A=green, B=blue, C=yellow, D=orange, F=red) | MUST |
| WU-03 | TypeScript types for scoring data (`DimensionScore`, `EvalResultScoring`, `PreCheckResult`) in `apps/web/src/lib/types.ts` | MUST |
| WU-04 | Radar chart renders 7 axes when given builtin dimensions; adapts dynamically to custom dimension count | MUST |
| WU-05 | Radar chart uses PolarGrid, PolarAngleAxis (dimension names), PolarRadiusAxis (0–1 domain) | MUST |

### 1.7 API

| ID | Requirement | Priority |
|----|-------------|----------|
| AP-01 | `GET /api/eval/{eval_id}` — existing response unchanged (backward compatible) | MUST |
| AP-02 | `GET /api/eval/{eval_id}?expand=scoring` — response includes `scoring` key with full `EvalResult` serialization (dimensions, overall grade/score, pre-check result) | MUST |
| AP-03 | Expand parameter supports comma-separated values: `?expand=scoring,analytics` (analytics reserved for Phase 5) | SHOULD |
| AP-04 | Unknown expand values are silently ignored (forward compatible) | MUST |
| AP-05 | `scoring` expand data stored in `Evaluation.results` JSONB column alongside existing results data | MUST |

---

## 2. Scenarios

### 2.1 Grade Calculation — Happy Path

**Given** a rubric with default 7 dimensions and default grade thresholds
**And** dimension scores: correctness=0.90, completeness=0.85, format=0.80, adherence=0.75, safety=0.95, efficiency=0.70, robustness=0.60
**When** `calculate_overall_grade()` is called
**Then** the weighted average is:
  `0.90×0.25 + 0.85×0.20 + 0.80×0.15 + 0.75×0.15 + 0.95×0.10 + 0.70×0.10 + 0.60×0.05 = 0.8275`
**And** the overall grade is `B` (0.70 ≤ 0.8275 < 0.85)
**And** individual dimension grades are: correctness=A, completeness=A, format=B, adherence=B, safety=S, efficiency=B, robustness=C

### 2.2 Grade Calculation — S Grade

**Given** a rubric with S threshold = 0.95
**And** all 7 dimensions score 0.97
**When** `calculate_overall_grade()` is called
**Then** the weighted average is 0.97
**And** the overall grade is `S`

### 2.3 Grade Calculation — S Grade Omitted

**Given** a rubric without S threshold (only A through D defined)
**And** all 7 dimensions score 0.97
**When** `calculate_overall_grade()` is called
**Then** the weighted average is 0.97
**And** the overall grade is `A` (max achievable without S)

### 2.4 Grade Calculation — Boundary F

**Given** a rubric with default thresholds
**And** all dimensions score 0.10
**When** `calculate_overall_grade()` is called
**Then** the weighted average is 0.10
**And** the overall grade is `F` (below D threshold of 0.30)

### 2.5 Pre-check — Clean SKILL.md

**Given** `tests/fixtures/skill_short.md` which has Description, Rules, Examples sections and no security issues
**And** default rubric
**When** `PreCheckEngine.run("tests/fixtures/skill_short.md")` is called
**Then** `PreCheckResult.passed` is `True`
**And** `findings` contains 0 error-severity findings
**And** `duration_ms` is > 0

### 2.6 Pre-check — Missing Section

**Given** a SKILL.md with only `# Description` (missing Rules and Examples)
**And** default rubric with required_sections: ["Description", "Rules", "Examples"]
**When** `PreCheckEngine.run()` is called
**Then** `PreCheckResult.passed` is `True` (missing sections are warnings, not errors)
**And** `findings` contains 2 findings with `severity="warning"` for Rules and Examples
**And** each finding has `check="required_sections"`

### 2.7 Pre-check — Hardcoded Secret Detected

**Given** a SKILL.md containing `api_key = "sk-12345abcdef"`
**And** default rubric with security pattern for hardcoded secrets
**When** `PreCheckEngine.run()` is called
**Then** `PreCheckResult.passed` is `False` (security error)
**And** `findings` contains at least one finding with `check="security_antipattern"`, `severity="error"`
**And** the finding's `line` field points to the line number containing the secret

### 2.8 Pre-check — Dangerous Shell Pattern (Warning)

**Given** a SKILL.md containing `os.system("rm -rf /tmp/cache")`
**And** default rubric with security pattern for dangerous shell patterns
**When** `PreCheckEngine.run()` is called
**Then** `PreCheckResult.passed` is `True` (shell pattern is a warning, not error)
**And** `findings` contains a finding with `severity="warning"` and `check="security_antipattern"`

### 2.9 Pre-check — Empty File (Error)

**Given** an empty SKILL.md (0 bytes)
**When** `PreCheckEngine.run()` is called
**Then** `PreCheckResult.passed` is `False`
**And** `findings` contains a finding from the `EmptyFileRule` with `severity="error"`

### 2.10 CLI — `md-evals check` Passes

**Given** `tests/fixtures/skill_short.md` is a valid SKILL.md
**When** `md-evals check tests/fixtures/skill_short.md` is executed
**Then** stdout contains `PASSED`
**And** stdout contains check count and duration
**And** exit code is 0

### 2.11 CLI — `md-evals check` Fails

**Given** a SKILL.md with hardcoded secret `password = "hunter2"`
**When** `md-evals check <path>` is executed
**Then** stdout contains `FAILED`
**And** stdout shows `[ERROR]` finding with the security message
**And** exit code is 2

### 2.12 CLI — `md-evals check` with Custom Rubric

**Given** a custom rubric at `./custom-rubric.yaml` with additional security pattern
**When** `md-evals check SKILL.md --rubric custom-rubric.yaml` is executed
**Then** the custom rubric is loaded instead of defaults
**And** pre-check uses the custom security patterns

### 2.13 CLI — `md-evals run` with `--force`

**Given** a SKILL.md with a pre-check error (hardcoded secret)
**When** `md-evals run --config eval.yaml --force` is executed
**Then** pre-check runs and reports findings
**And** LLM eval runs anyway (not skipped)
**And** all findings are passed as context for the LLM evaluators

### 2.14 CLI — `md-evals run` with `--no-pre-check`

**Given** any SKILL.md
**When** `md-evals run --config eval.yaml --no-pre-check` is executed
**Then** pre-check does NOT run
**And** `EvalResult.pre_check` is `None`
**And** LLM eval runs unconditionally

### 2.15 Rubric — Default Loads Successfully

**Given** no `rubric.yaml` in CWD and no `~/.md-evals/rubric.yaml`
**When** `RubricLoader.load_default()` is called
**Then** returns valid `RubricConfig` with 7 dimensions
**And** weights sum to 1.0
**And** grade thresholds include S, A, B, C, D

### 2.16 Rubric — CWD File Takes Precedence

**Given** `rubric.yaml` exists in CWD with custom weights
**And** no CLI `--rubric` flag
**When** `RubricLoader.resolve()` is called
**Then** the CWD rubric is loaded (not built-in default)

### 2.17 Rubric — CLI Flag Takes Precedence Over CWD

**Given** `rubric.yaml` in CWD with default weights
**And** `--rubric custom.yaml` flag pointing to a different rubric
**When** `RubricLoader.resolve("custom.yaml")` is called
**Then** `custom.yaml` is loaded (not CWD rubric)

### 2.18 Rubric — Invalid Weights Rejected

**Given** a rubric YAML where dimension weights sum to 0.80
**When** `RubricLoader.load("bad-rubric.yaml")` is called
**Then** `RubricValidationError` is raised
**And** the error message contains "0.80" and mentions expected sum of 1.0

### 2.19 Rubric — Custom Dimensions

**Given** a rubric with 5 builtin dimensions + 2 custom dimensions ("creativity", "tone") each with `description`
**And** weights sum to 1.0
**When** loaded via `RubricLoader.load()`
**Then** the rubric has 7 dimensions total (5 builtin + 2 custom)
**And** custom dimensions have their `description` field populated

### 2.20 Rubric — Custom Dimension Without Description

**Given** a rubric with custom dimension "creativity" that lacks a `description` field
**When** loaded via `RubricLoader.load()`
**Then** a warning is emitted (logged)
**And** the rubric still loads (not rejected)
**And** the dimension's description defaults to empty string

### 2.21 Web UI — Radar Chart Renders

**Given** `DimensionScore[]` with 7 builtin dimensions
**When** `<DimensionRadar dimensions={scores} />` is rendered
**Then** a Recharts `RadarChart` is displayed with 7 labeled axes
**And** each axis ranges from 0 to 1
**And** the radar polygon fills according to dimension scores

### 2.22 Web UI — Grade Badge

**Given** an overall grade of "A"
**When** `<GradeBadge grade="A" />` is rendered
**Then** a badge displays "A" in green color

### 2.23 API — Expand Scoring

**Given** eval `{eval_id}` has completed with scoring data stored
**When** `GET /api/eval/{eval_id}?expand=scoring` is requested
**Then** the response includes all fields from `EvalDetailResponse`
**And** additionally includes `scoring` key with `overall_grade`, `overall_score`, `dimensions[]`, `pre_check`

### 2.24 API — No Expand (Backward Compatible)

**Given** eval `{eval_id}` has completed with scoring data
**When** `GET /api/eval/{eval_id}` is requested (no expand parameter)
**Then** the response matches the existing `EvalDetailResponse` schema exactly
**And** no `scoring` key is included

### 2.25 JSON Output — EvalResult Included

**Given** a completed eval run with scoring data
**When** `md-evals run --output json` produces results
**Then** the JSON file contains an `eval_result` key
**And** `eval_result.overall_grade` is a valid letter grade
**And** `eval_result.overall_score` is a float 0.0–1.0
**And** `eval_result.dimensions` is a list of dimension objects
**And** `eval_result.pre_check` contains the pre-check findings (or null)

---

## 3. Acceptance Criteria

### Data Model (AC-01 through AC-08)

**AC-01**: `DimensionScore` and `EvalResult` models exist in `md_evals/scoring.py` with the fields specified in §5 Data Model. Both are importable: `from md_evals.scoring import DimensionScore, EvalResult`.

**AC-02**: `PreCheckResult` and `PreCheckFinding` models exist in `md_evals/precheck.py` with the fields specified in §5 Data Model. Both are importable: `from md_evals.precheck import PreCheckResult, PreCheckFinding`.

**AC-03**: `EvalMetadata` exists in `md_evals/scoring.py` and correctly references `CostMetrics` and `ContextMetrics` from `md_evals/metrics.py` via import.

**AC-04**: `DimensionScore` is `frozen=True` — attempting to set a field after construction raises `FrozenInstanceError`.

**AC-05**: `PreCheckFinding` is `frozen=True` — attempting to set a field after construction raises `FrozenInstanceError`.

**AC-06**: All scoring types use stdlib `@dataclass`, not Pydantic `BaseModel`. Verified by checking `type(DimensionScore)` is not a Pydantic model metaclass.

**AC-07**: `EvalResult.evidence` defaults to empty list `[]`, never `None`. Verified: `DimensionScore(dimension="x", score=0.5, weight=0.1, grade="C").evidence == []`.

**AC-08**: No circular imports: importing `md_evals.scoring`, `md_evals.precheck`, and `md_evals.rubric` in any order succeeds without `ImportError`.

### Grade Calculation (AC-09 through AC-13)

**AC-09**: `calculate_overall_grade()` returns the correct weighted score and letter grade for all boundary values: 0.0→F, 0.29→F, 0.30→D, 0.49→D, 0.50→C, 0.69→C, 0.70→B, 0.84→B, 0.85→A, 0.94→A, 0.95→S, 1.0→S.

**AC-10**: Grade calculation is a pure function: no I/O, no side effects, no global state. Verified by calling from multiple threads (concurrent.futures.ThreadPoolExecutor) with different inputs — all return correct results with no race conditions.

**AC-11**: When S is not defined in thresholds, `score_to_grade(0.99, {"A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30})` returns `"A"`.

**AC-12**: Hypothesis property test: for any score in [0.0, 1.0] and valid thresholds, `score_to_grade` always returns one of "S", "A", "B", "C", "D", "F".

**AC-13**: Hypothesis property test: if score_a > score_b, then `grade_rank(score_to_grade(score_a)) >= grade_rank(score_to_grade(score_b))` (monotonicity).

### Rubric Configuration (AC-14 through AC-20)

**AC-14**: `RubricLoader.load_default()` returns a valid `RubricConfig` with 7 dimensions whose weights sum to 1.0 (verified: `abs(sum(d.weight for d in config.dimensions.values()) - 1.0) < 0.001`).

**AC-15**: `RubricLoader.load("custom-rubric.yaml")` parses a valid rubric file and validates weight sum, dimension names, and grade thresholds.

**AC-16**: Loading a rubric with weights summing to 0.80 raises `RubricValidationError` with a message containing the string `"0.80"` or `"0.8"`.

**AC-17**: Loading a rubric with duplicate dimension names raises `RubricValidationError` mentioning the duplicate name.

**AC-18**: Loading a rubric with non-monotonic thresholds (e.g., A=0.85, B=0.90) raises `RubricValidationError`.

**AC-19**: Loading a rubric with an invalid security pattern regex (e.g., `"[unclosed"`) raises `RubricValidationError` mentioning "regex" or "pattern".

**AC-20**: Rubric resolution chain works: given `--rubric=flag.yaml`, a CWD `rubric.yaml`, and `~/.md-evals/rubric.yaml`, the CLI flag wins. With no flag, CWD wins. With neither, home dir wins. With none, built-in default is used. Verified via 4 separate test cases.

### Pre-check Engine (AC-21 through AC-27)

**AC-21**: `PreCheckEngine.run()` on a SKILL.md missing "Examples" produces a finding with `check="required_sections"` and `severity="warning"`.

**AC-22**: `PreCheckEngine.run()` on a SKILL.md containing `api_key = "sk-12345"` produces a finding with `check="security_antipattern"` and `severity="error"`. `PreCheckResult.passed` is `False`.

**AC-23**: `PreCheckEngine.run()` on a SKILL.md containing `chmod 777 /tmp` produces a finding with `severity="warning"`. `PreCheckResult.passed` is `True`.

**AC-24**: `PreCheckEngine.run()` on an empty file produces `PreCheckResult.passed = False` with a finding from the empty-file check.

**AC-25**: `PreCheckEngine` delegates to `LinterEngine` — verified by checking that `MaxLinesRule`, `EmptyFileRule`, and `VeryLongLineRule` violations appear as `PreCheckFinding` objects in the result (no reimplementation of those rules).

**AC-26**: `PreCheckResult.checks_run` accurately counts the total number of checks executed (linter rules + security patterns).

**AC-27**: `PreCheckResult.duration_ms` is > 0 for any file and < 1000 for a file under 400 lines (performance guarantee).

### CLI (AC-28 through AC-33)

**AC-28**: `md-evals check tests/fixtures/skill_short.md` exits with code 0 and stdout contains "PASSED" with check count and timing.

**AC-29**: `md-evals check <broken-fixture>` (file with hardcoded secret) exits with code 2 and stdout contains "FAILED" with "[ERROR]" findings.

**AC-30**: `md-evals check --rubric custom.yaml SKILL.md` uses the specified rubric (not defaults).

**AC-31**: `md-evals run --no-pre-check --config eval.yaml` skips pre-check entirely — `EvalResult.pre_check` is `None` in the output.

**AC-32**: `md-evals run --force --config eval.yaml` runs LLM eval even when pre-check finds errors — findings are included in `EvalResult.pre_check` and the overall result includes LLM scores.

**AC-33**: `md-evals init` generates `rubric.yaml` alongside `eval.yaml` with commented defaults. File exists after init completes.

### Web UI (AC-34 through AC-36)

**AC-34**: `<DimensionRadar>` renders a Recharts `RadarChart` with the correct number of axes matching the input dimension count. Component renders without errors for 3–15 dimensions.

**AC-35**: `<GradeBadge>` renders letter grades S through F with correct color mapping: S=gold/amber, A=green, B=blue, C=yellow, D=orange, F=red.

**AC-36**: TypeScript types `DimensionScoreDTO`, `PreCheckResultDTO`, `EvalResultScoring` are defined in `apps/web/src/lib/types.ts` and compile without errors.

### API (AC-37 through AC-39)

**AC-37**: `GET /api/eval/{eval_id}` without `expand` parameter returns the existing `EvalDetailResponse` schema — no new fields added. Existing frontend code continues to work.

**AC-38**: `GET /api/eval/{eval_id}?expand=scoring` returns the base response plus a `scoring` key containing `overall_grade` (str), `overall_score` (float), `dimensions` (list), and `pre_check` (object|null).

**AC-39**: `GET /api/eval/{eval_id}?expand=unknown_thing` returns the base response with no error — unknown expand values are silently ignored.

### JSON Output (AC-40)

**AC-40**: When `--output json` is used, the JSON file contains an `eval_result` key at the top level with `overall_grade`, `overall_score`, `dimensions[]`, and `pre_check`. The `eval_result` key is present alongside existing `results` and `summary` keys.

### Backward Compatibility (AC-41 through AC-43)

**AC-41**: All 457+ existing tests continue to pass without modification. Verified by running `pytest` with no changes to existing test files.

**AC-42**: `ExecutionResult`, `EvaluatorResult`, `LLMResponse`, `EvalConfig`, `LinterConfig`, `LinterReport`, `LinterViolation` in `md_evals/models.py` are completely unchanged. Verified by `git diff md_evals/models.py` showing zero modifications.

**AC-43**: `LinterEngine` in `md_evals/linter.py` is not modified. The `PreCheckEngine` uses it via composition (dependency injection), not inheritance or monkey-patching.

### Test Coverage (AC-44 through AC-46)

**AC-44**: At least 35 new tests covering scoring, pre-check, and rubric loading. Tests organized as `tests/test_scoring.py`, `tests/test_precheck.py`, `tests/test_rubric.py`.

**AC-45**: Hypothesis property-based tests for grade boundary invariants: monotonicity, exhaustive grade coverage, weight-sum invariant.

**AC-46**: New test fixtures: `tests/fixtures/rubric_default.yaml`, `tests/fixtures/rubric_invalid_weights.yaml`, `tests/fixtures/rubric_custom_dimensions.yaml`, `tests/fixtures/rubric_no_s_grade.yaml`, `tests/fixtures/skill_with_secret.md`, `tests/fixtures/skill_with_shell.md`, `tests/fixtures/skill_empty.md`.

---

## 4. Edge Cases

### EC-01: All Dimensions Score 0.0

**Given** all 7 dimensions have score=0.0
**Expected**: overall_score=0.0, overall_grade="F", all dimension grades="F". No division errors, no NaN.

### EC-02: All Dimensions Score 1.0

**Given** all 7 dimensions have score=1.0 and S threshold is defined
**Expected**: overall_score=1.0, overall_grade="S". No overflow.

### EC-03: Single Dimension Rubric

**Given** a rubric with exactly 1 dimension, weight=1.0
**Expected**: valid rubric loads, overall_score equals that dimension's score, grade calculated normally.

### EC-04: Weight Sum Floating-Point Precision

**Given** 7 dimensions with weights that sum to 0.9999999999999998 (floating-point artifact)
**Expected**: rubric validates successfully (within ±0.001 tolerance). Not rejected.

### EC-05: Score Exactly at Grade Boundary

**Given** score = 0.85 exactly, A threshold = 0.85
**Expected**: grade = "A" (boundary inclusive: score >= threshold).

**Given** score = 0.8499999999 (just below)
**Expected**: grade = "B".

### EC-06: Empty Rubric YAML File

**Given** a `rubric.yaml` that exists but contains no YAML content (empty or only comments)
**Expected**: `RubricValidationError` with message mentioning "empty" or "invalid".

### EC-07: Rubric with Zero-Weight Dimension

**Given** a dimension with weight=0.0 and other weights sum to 1.0
**Expected**: valid rubric. Dimension contributes 0.0 to overall score but is still evaluated and reported with its own grade.

### EC-08: Security Pattern with Regex Special Characters

**Given** a security pattern containing regex metacharacters that form a valid regex
**Expected**: pattern compiles and matches correctly. No escaped-character issues.

### EC-09: Security Pattern that Doesn't Compile

**Given** a rubric with security pattern `"[invalid"`
**Expected**: `RubricValidationError` at load time (not at check time). Message mentions pattern compilation failure.

### EC-10: SKILL.md with Non-UTF-8 Encoding

**Given** a SKILL.md file with ISO-8859-1 encoding containing accented characters
**Expected**: `PreCheckEngine.run()` returns `PreCheckResult.passed = False` with a finding about encoding/read error. No unhandled exception.

### EC-11: Very Large SKILL.md (10,000+ Lines)

**Given** a SKILL.md with 10,000 lines
**Expected**: Pre-check completes within 5 seconds (not O(n²)). MaxLinesRule violation reported as error. Security regex scan completes in reasonable time.

### EC-12: Pre-check on Non-Existent File

**Given** `PreCheckEngine.run("nonexistent.md")` called
**Expected**: `PreCheckResult.passed = False` with a finding about file not found. No unhandled `FileNotFoundError`.

### EC-13: Rubric with Overlapping Custom and Builtin Dimension Names

**Given** a rubric with a custom dimension named "correctness" (same as builtin)
**Expected**: `RubricValidationError` — duplicate dimension names detected.

### EC-14: Grade Thresholds with Same Value

**Given** thresholds A=0.85, B=0.85 (A and B at same threshold)
**Expected**: `RubricValidationError` — thresholds must be strictly monotonically decreasing.

### EC-15: Concurrent Grade Calculations

**Given** 100 concurrent calls to `calculate_overall_grade()` with different inputs
**Expected**: all return correct results. No shared mutable state, no race conditions. Verified with ThreadPoolExecutor.

### EC-16: Custom Dimension with Very Long Description

**Given** a custom dimension with a 10,000-character description
**Expected**: rubric loads successfully. Description is not truncated at load time (truncation, if needed, is a Phase 2 concern for LLM prompt fitting).

### EC-17: `--rubric` Flag Points to Non-Existent File

**Given** `md-evals check SKILL.md --rubric nonexistent.yaml`
**Expected**: exit code 1 with error message "Rubric file not found: nonexistent.yaml". Pre-check does not run.

### EC-18: Multiple Security Findings on Same Line

**Given** a SKILL.md line: `api_key = "sk-123"; os.system("rm -rf /")`
**Expected**: two separate findings for that line — one error (hardcoded secret) and one warning (shell pattern). Both reported with the correct line number.

---

## 5. Data Model

### 5.1 `DimensionScore` (frozen dataclass)

```python
# md_evals/scoring.py
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class DimensionScore:
    """Score for a single evaluation dimension."""
    dimension: str          # Dimension name, e.g. "correctness", "safety"
    score: float            # Normalized score, 0.0–1.0 inclusive
    weight: float           # From rubric config, all weights sum to 1.0
    grade: str              # Letter grade: "S", "A", "B", "C", "D", or "F"
    evidence: list[str] = field(default_factory=list)  # Empty until Phase 3
```

**Constraints**:
- `score`: must be in range [0.0, 1.0]. Values outside range are clamped by the constructor caller (not enforced by dataclass itself).
- `weight`: must be in range [0.0, 1.0]. Sum of all weights across all DimensionScores in an EvalResult should be 1.0.
- `grade`: must be one of `{"S", "A", "B", "C", "D", "F"}`.
- `evidence`: always a list, never None. Empty list until Phase 3 populates it.
- `dimension`: non-empty string, lowercase recommended but not enforced.

### 5.2 `PreCheckFinding` (frozen dataclass)

```python
# md_evals/precheck.py
@dataclass(frozen=True)
class PreCheckFinding:
    """A single finding from the pre-check engine."""
    check: str              # Check identifier: "required_sections", "security_antipattern",
                            # "empty_file", "max_lines", "very_long_line"
    message: str            # Human-readable description
    severity: str           # "error" | "warning" | "info"
    line: int | None = None # Line number (1-indexed) if applicable, None otherwise
```

**Constraints**:
- `severity`: must be one of `{"error", "warning", "info"}`.
- `check`: machine-readable identifier. Standardized values: `"required_sections"`, `"security_antipattern"`, `"empty_file"`, `"max_lines"`, `"very_long_line"`, `"file_not_found"`, `"read_error"`.
- `line`: 1-indexed. None when the finding is file-level (e.g., empty file, file not found).

### 5.3 `PreCheckResult` (frozen dataclass)

```python
# md_evals/precheck.py
@dataclass(frozen=True)
class PreCheckResult:
    """Aggregated result from pre-check engine."""
    passed: bool            # True if no error-severity findings
    findings: list[PreCheckFinding]  # All findings (errors + warnings + info)
    checks_run: int         # Total checks executed
    duration_ms: int        # Wall-clock execution time
```

**Invariants**:
- `passed == True` iff no finding in `findings` has `severity == "error"`.
- `checks_run >= len(findings)` (some checks may produce 0 findings).
- `duration_ms >= 0`.

### 5.4 `EvalMetadata` (mutable dataclass)

```python
# md_evals/scoring.py
from md_evals.metrics import CostMetrics, ContextMetrics

@dataclass
class EvalMetadata:
    """Metadata about an evaluation run."""
    model: str                                  # e.g. "gpt-4o"
    provider: str                               # e.g. "github-models"
    cost_metrics: CostMetrics | None = None     # From md_evals/metrics.py
    context_metrics: ContextMetrics | None = None  # From md_evals/metrics.py
    total_duration_ms: int = 0                  # Total wall-clock time
    pre_check_duration_ms: int = 0              # Pre-check phase time
    llm_duration_ms: int = 0                    # LLM evaluation phase time
    timestamp: str = ""                         # ISO 8601, e.g. "2026-03-17T14:30:22Z"
```

**Constraints**:
- `timestamp`: ISO 8601 format string. Empty string only when metadata is being constructed incrementally.
- `total_duration_ms >= pre_check_duration_ms + llm_duration_ms` (may include overhead).
- `cost_metrics` and `context_metrics` are the same types already defined in `md_evals/metrics.py`. No new types.

### 5.5 `EvalResult` (mutable dataclass)

```python
# md_evals/scoring.py
from typing import Any

@dataclass
class EvalResult:
    """Top-level scoring result for a single SKILL.md evaluation."""
    skill_path: str                             # Path to evaluated SKILL.md
    overall_grade: str                          # "S", "A", "B", "C", "D", "F"
    overall_score: float                        # 0.0–1.0 weighted average
    dimensions: list[DimensionScore]            # Per-dimension scores
    pre_check: PreCheckResult | None            # None when --no-pre-check
    metadata: EvalMetadata                      # Timing, cost, model info
    execution_results: list[Any] | None = None  # Raw ExecutionResults for backward compat
```

**Invariants**:
- `overall_grade` is consistent with `overall_score` given the rubric thresholds.
- `len(dimensions) >= 1`.
- `sum(d.weight for d in dimensions) ≈ 1.0` (within ±0.001).
- `overall_score == sum(d.score * d.weight for d in dimensions)` (within floating-point tolerance).

### 5.6 `RubricConfig` (Pydantic model)

```python
# md_evals/rubric.py
from pydantic import BaseModel, Field

class SecurityPattern(BaseModel):
    """A regex-based security check pattern."""
    pattern: str            # Valid regex
    message: str            # Human-readable description of what it detects
    severity: str = "warning"  # "error" | "warning" | "info"

class PreCheckConfig(BaseModel):
    """Pre-check configuration within a rubric."""
    required_sections: list[str] = Field(default_factory=lambda: ["Description", "Rules", "Examples"])
    max_lines: int = 400
    security_patterns: list[SecurityPattern] = Field(default_factory=list)

class DimensionConfig(BaseModel):
    """Configuration for a single evaluation dimension."""
    weight: float           # 0.0–1.0, all weights sum to 1.0
    description: str = ""   # Description for LLM prompt (required for custom dimensions)

class RubricConfig(BaseModel):
    """Top-level rubric configuration."""
    version: str = "1.0"
    dimensions: dict[str, DimensionConfig]      # Dimension name → config
    grade_thresholds: dict[str, float]          # Grade letter → threshold score
    pre_check: PreCheckConfig = Field(default_factory=PreCheckConfig)
```

**Pydantic model note**: `RubricConfig` uses Pydantic (not stdlib dataclass) because it's a configuration/deserialization model loaded from YAML, consistent with the pattern used by `EvalConfig` in `md_evals/models.py`.

---

## 6. Configuration

### 6.1 `rubric.yaml` Full Schema

```yaml
# rubric.yaml — Full schema with all fields, types, defaults, and validation rules
# Version: 1.0

version: "1.0"                    # Required. String. Must be "1.0" for this spec.

dimensions:                        # Required. Map of dimension_name → config.
                                   # At least 1 dimension required.
                                   # Keys: lowercase string, no spaces (e.g., "correctness").
                                   # Builtin keys: correctness, completeness, format, adherence,
                                   #   safety, efficiency, robustness.
                                   # Custom keys: any other lowercase string.

  correctness:                     # Builtin dimension — has optimized LLM prompt.
    weight: 0.25                   # Required. Float 0.0–1.0. All weights must sum to 1.0±0.001.
    description: "Technical accuracy of instructions and examples"
                                   # Optional for builtins (has default). Required for custom.

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

grade_thresholds:                  # Required. Map of grade_letter → minimum_score.
                                   # Grades checked in descending order: S, A, B, C, D.
                                   # Score below lowest threshold → "F".
                                   # Values must be strictly monotonically decreasing.
  S: 0.95                         # Optional. If omitted, max grade is A.
  A: 0.85                         # Required.
  B: 0.70                         # Required.
  C: 0.50                         # Required.
  D: 0.30                         # Required.
                                   # F is implicit: score < D threshold.

pre_check:                         # Optional. Defaults to built-in pre_check config.

  required_sections:               # Optional. List of section names to check for.
    - "Description"                # Default: ["Description", "Rules", "Examples"]
    - "Rules"
    - "Examples"

  max_lines: 400                   # Optional. Integer > 0. Default: 400.
                                   # Files exceeding this produce severity="error".

  security_patterns:               # Optional. List of regex-based security checks.
    - pattern: "\\b(api[_-]?key|secret|password)\\s*[:=]\\s*['\"][^'\"]+['\"]"
      message: "Hardcoded secret detected"
      severity: "error"            # "error" | "warning" | "info". Default: "warning".

    - pattern: "os\\.system\\(|subprocess\\.call\\(|eval\\(|exec\\("
      message: "Potentially dangerous shell/eval pattern"
      severity: "warning"

    - pattern: "chmod\\s+777|chmod\\s+0?777"
      message: "Overly permissive file permissions"
      severity: "warning"
```

### 6.2 Validation Rules

| Rule | Condition | Error |
|------|-----------|-------|
| Weight sum | `abs(sum(d.weight for d in dimensions.values()) - 1.0) > 0.001` | `RubricValidationError("Dimension weights must sum to 1.0, got {actual_sum}")` |
| No duplicates | Dimensions dict handles this inherently (YAML keys are unique) | N/A — YAML syntax prevents this |
| Threshold monotonicity | Thresholds must satisfy: S > A > B > C > D (when present) | `RubricValidationError("Grade thresholds must be strictly decreasing: {details}")` |
| Threshold range | Each threshold must be in (0.0, 1.0] | `RubricValidationError("Threshold {grade}={value} must be in (0.0, 1.0]")` |
| Regex compilation | Each security pattern must compile with `re.compile()` | `RubricValidationError("Invalid regex in security pattern: {pattern} — {error}")` |
| Custom dimension description | Custom dimensions should have `description`. Warning logged if empty | Warning only (not an error). `logger.warning("Custom dimension '{name}' has no description")` |
| Version check | `version` must equal "1.0" | `RubricValidationError("Unsupported rubric version: {version}")` |
| At least one dimension | `len(dimensions) >= 1` | `RubricValidationError("Rubric must have at least one dimension")` |
| A/B/C/D required | `grade_thresholds` must include at minimum A, B, C, D | `RubricValidationError("Missing required grade threshold: {grade}")` |

### 6.3 Resolution Chain Implementation

```python
# md_evals/rubric.py

class RubricLoader:
    BUILTIN_PATH = Path(__file__).parent / "rubric_default.yaml"
    HOME_PATH = Path.home() / ".md-evals" / "rubric.yaml"

    @classmethod
    def resolve(cls, cli_rubric: str | None = None) -> RubricConfig:
        """Load rubric with resolution chain: CLI → CWD → home → builtin."""
        if cli_rubric:
            return cls.load(cli_rubric)

        cwd_rubric = Path.cwd() / "rubric.yaml"
        if cwd_rubric.exists():
            return cls.load(str(cwd_rubric))

        if cls.HOME_PATH.exists():
            return cls.load(str(cls.HOME_PATH))

        return cls.load_default()

    @classmethod
    def load(cls, path: str) -> RubricConfig:
        """Load and validate rubric from YAML file."""
        ...

    @classmethod
    def load_default(cls) -> RubricConfig:
        """Load built-in default rubric."""
        return cls.load(str(cls.BUILTIN_PATH))
```

### 6.4 `rubric_default.yaml` Package Distribution

The default rubric file `md_evals/rubric_default.yaml` MUST be included in the package distribution. In `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["md_evals"]

# Ensure YAML is included
[tool.hatch.build.targets.wheel.force-include]
"md_evals/rubric_default.yaml" = "md_evals/rubric_default.yaml"
```

Or via `package_data` if using `MANIFEST.in`:
```
include md_evals/rubric_default.yaml
```

---

## 7. CLI Specification

### 7.1 `md-evals check`

```
Usage: md-evals check [OPTIONS] SKILL_PATH

  Run deterministic pre-check on a SKILL.md file (no LLM, no cost).

Arguments:
  SKILL_PATH  Path to SKILL.md file to check  [required]

Options:
  --rubric PATH   Path to rubric.yaml (default: resolution chain)
  --verbose, -v   Show detailed check results
  --help          Show this message and exit.
```

**Output format (passed)**:
```
✓ SKILL.md — Pre-check PASSED (7 checks, 0 findings, 12ms)
```

**Output format (failed with findings)**:
```
✗ SKILL.md — Pre-check FAILED (9 checks, 3 findings, 15ms)
  [ERROR] Hardcoded secret detected (line 42)
  [WARNING] Missing recommended section: Examples
  [WARNING] Potentially dangerous shell/eval pattern (line 87)
```

**Exit codes**:

| Code | Meaning |
|------|---------|
| 0 | Pre-check passed (no error-severity findings) |
| 1 | Configuration error (rubric not found, invalid rubric, etc.) |
| 2 | Pre-check failed (at least one error-severity finding) |

### 7.2 `md-evals run` — New Flags

```
Existing: md-evals run [OPTIONS]

New Options:
  --rubric PATH           Path to rubric.yaml for scoring dimensions
  --no-pre-check          Skip pre-check phase entirely
  --force                 Run LLM eval even when pre-check finds errors
```

**Flag interactions**:

| Flags | Pre-check | LLM Eval | Pre-check findings as LLM context |
|-------|-----------|----------|-----------------------------------|
| (default) | Runs | Runs if pre-check passes | Warnings only |
| `--force` | Runs | Always runs | All findings (errors + warnings) |
| `--no-pre-check` | Skipped | Always runs | N/A |
| `--force --no-pre-check` | Skipped | Always runs | N/A (`--no-pre-check` takes precedence) |

**Exit codes** (existing, unchanged):

| Code | Meaning |
|------|---------|
| 0 | All tests passed (or partial success) |
| 1 | Configuration error |
| 2 | Linter/pre-check failure (when not forced) |
| 3 | Execution error |
| 4 | All tests failed |

### 7.3 `md-evals init` — Extension

Current `init` generates `eval.yaml` and `SKILL.md`. Extended to also generate `rubric.yaml`:

```
✓ Created eval.yaml
✓ Created SKILL.md
✓ Created rubric.yaml    ← NEW
✓ Created results/
```

The generated `rubric.yaml` contains the default configuration with comments explaining each field.

---

## 8. API Specification

### 8.1 `GET /api/eval/{eval_id}` — Expand Parameter

**Current behavior** (unchanged):
```
GET /api/eval/{eval_id}

Response 200:
{
  "eval_id": "uuid",
  "title": "My Eval",
  "status": "completed",
  "skill_content": "...",
  "eval_config": {...},
  "results": {...},
  "cost_metrics": {...},
  "context_metrics": {...},
  "error_message": null,
  "created_at": "2026-03-17T...",
  "completed_at": "2026-03-17T..."
}
```

**New behavior** with `expand=scoring`:
```
GET /api/eval/{eval_id}?expand=scoring

Response 200:
{
  // ... all existing fields unchanged ...
  "eval_id": "uuid",
  "title": "My Eval",
  "status": "completed",
  "skill_content": "...",
  "eval_config": {...},
  "results": {...},
  "cost_metrics": {...},
  "context_metrics": {...},
  "error_message": null,
  "created_at": "2026-03-17T...",
  "completed_at": "2026-03-17T...",

  // NEW — only present when expand=scoring
  "scoring": {
    "overall_grade": "B",
    "overall_score": 0.8275,
    "dimensions": [
      {
        "dimension": "correctness",
        "score": 0.90,
        "weight": 0.25,
        "grade": "A",
        "evidence": []
      },
      {
        "dimension": "completeness",
        "score": 0.85,
        "weight": 0.20,
        "grade": "A",
        "evidence": []
      }
      // ... 5 more dimensions
    ],
    "pre_check": {
      "passed": true,
      "findings": [],
      "checks_run": 7,
      "duration_ms": 12
    }
  }
}
```

### 8.2 Expand Parameter Behavior

```python
# In apps/server/app/routes/eval.py

@router.get("/{eval_id}", response_model=EvalDetailResponse)
async def get_eval(
    eval_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    expand: str | None = Query(default=None),  # NEW parameter
) -> EvalDetailResponse:
```

**Parsing rules**:
- `expand` is a comma-separated string: `"scoring"`, `"scoring,analytics"`, etc.
- Each value is trimmed and lowercased.
- Unknown values are silently ignored.
- Supported values in Phase 1: `"scoring"`.
- Reserved for future: `"analytics"` (Phase 5).

### 8.3 Schema Updates

```python
# apps/server/app/models/schemas.py — additions

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

class EvalDetailResponse(BaseModel):
    """Response for GET /api/eval/{id} — extended with optional scoring."""
    eval_id: str
    title: str
    status: str
    skill_content: str | None = None
    eval_config: dict | None = None
    results: dict | None = None
    cost_metrics: dict | None = None
    context_metrics: dict | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    # NEW — only populated when expand=scoring
    scoring: ScoringResponse | None = None
```

### 8.4 Storage

Scoring data is stored in the existing `Evaluation.results` JSONB column alongside current results data. The `results` column gains a `scoring` key:

```json
{
  "execution_results": [...],
  "scoring": {
    "overall_grade": "B",
    "overall_score": 0.8275,
    "dimensions": [...],
    "pre_check": {...}
  }
}
```

No database migration needed — `results` is already a JSONB column that accepts arbitrary structure.

### 8.5 TypeScript Types

Added to `apps/web/src/lib/types.ts`:

```typescript
export interface DimensionScoreDTO {
  dimension: string;
  score: number;
  weight: number;
  grade: string;
  evidence: string[];
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

The existing `Evaluation` interface gains an optional `scoring` field:

```typescript
export interface Evaluation {
  // ... existing fields unchanged ...
  scoring?: EvalResultScoring | null;
}
```

---

## 9. Error Handling

### 9.1 Error Catalog

| Error | Module | Type | Behavior |
|-------|--------|------|----------|
| Rubric file not found | `md_evals/rubric.py` | `RubricValidationError` | CLI: exit code 1 with "Rubric file not found: {path}" |
| Rubric invalid YAML | `md_evals/rubric.py` | `RubricValidationError` | CLI: exit code 1 with "Invalid YAML in rubric: {details}" |
| Rubric empty/null | `md_evals/rubric.py` | `RubricValidationError` | CLI: exit code 1 with "Rubric file is empty" |
| Weights don't sum to 1.0 | `md_evals/rubric.py` | `RubricValidationError` | Message includes actual sum |
| Duplicate dimension names | `md_evals/rubric.py` | `RubricValidationError` | Message includes duplicate name |
| Non-monotonic thresholds | `md_evals/rubric.py` | `RubricValidationError` | Message includes the offending pair |
| Invalid regex in security pattern | `md_evals/rubric.py` | `RubricValidationError` | Message includes pattern and regex error |
| Missing required thresholds (A/B/C/D) | `md_evals/rubric.py` | `RubricValidationError` | Message includes which threshold is missing |
| Unsupported rubric version | `md_evals/rubric.py` | `RubricValidationError` | Message includes the version string |
| SKILL.md file not found | `md_evals/precheck.py` | Returns `PreCheckResult(passed=False)` | Finding with check="file_not_found" |
| SKILL.md read error | `md_evals/precheck.py` | Returns `PreCheckResult(passed=False)` | Finding with check="read_error" |
| Score out of range | `md_evals/scoring.py` | Clamped silently | `min(max(score, 0.0), 1.0)` — no exception |
| Empty dimension list | `md_evals/scoring.py` | `ValueError` | "Cannot calculate grade with empty dimensions" |

### 9.2 Exception Hierarchy

```python
# md_evals/rubric.py

class RubricError(Exception):
    """Base exception for rubric operations."""
    pass

class RubricValidationError(RubricError):
    """Raised when rubric validation fails."""
    pass

class RubricNotFoundError(RubricError):
    """Raised when rubric file is not found."""
    pass
```

### 9.3 CLI Error Handling Pattern

All rubric/pre-check errors are caught in the CLI layer and converted to user-friendly messages + exit codes. No stack traces shown to users unless `--debug` is passed (following existing pattern from `md_evals/cli.py`):

```python
try:
    rubric = RubricLoader.resolve(rubric_path)
except RubricNotFoundError as e:
    console.print(f"[red]Error: {e}[/red]")
    raise typer.Exit(code=1)
except RubricValidationError as e:
    console.print(f"[red]Invalid rubric: {e}[/red]")
    raise typer.Exit(code=1)
```

---

## 10. Backward Compatibility

### 10.1 Guarantees

| Guarantee | Verification |
|-----------|-------------|
| `md_evals/models.py` is NOT modified | `git diff md_evals/models.py` shows 0 changes |
| `md_evals/linter.py` is NOT modified | `git diff md_evals/linter.py` shows 0 changes |
| `md_evals/metrics.py` is NOT modified | `git diff md_evals/metrics.py` shows 0 changes |
| `md_evals/config.py` is NOT modified (rubric loading is in new `md_evals/rubric.py`) | `git diff md_evals/config.py` shows 0 changes |
| `ExecutionResult`, `EvaluatorResult`, `LLMResponse`, `EvalConfig` types are unchanged | Import and instantiation tests pass |
| Existing CLI commands (`run`, `lint`, `smoke`, `init`, `list`, `list-models`, `version`) work identically | Existing CLI tests pass |
| `GET /api/eval/{eval_id}` without `expand` parameter returns identical response | Existing API tests pass |
| JSON output format: existing keys (`experiment_id`, `timestamp`, `config`, `results`, `summary`, `usage_metrics`) are unchanged | Existing reporter tests pass |
| All 457+ existing tests pass without modification | `pytest` green |

### 10.2 Additive Changes Only

| Module | Change | Nature |
|--------|--------|--------|
| `md_evals/scoring.py` | **NEW FILE** | New dataclasses and pure functions |
| `md_evals/precheck.py` | **NEW FILE** | PreCheckEngine, wraps LinterEngine |
| `md_evals/rubric.py` | **NEW FILE** | RubricConfig, RubricLoader, validation |
| `md_evals/rubric_default.yaml` | **NEW FILE** | Default rubric YAML |
| `md_evals/cli.py` | New `check` command added; new flags on `run` | Additive (existing commands unchanged) |
| `md_evals/reporter.py` | New `report_eval_result()` method | Additive (existing methods unchanged) |
| `apps/server/app/routes/eval.py` | `expand` query param on `get_eval` | Additive (no expand = old behavior) |
| `apps/server/app/models/schemas.py` | New response models; optional `scoring` field on `EvalDetailResponse` | Additive |
| `apps/web/src/lib/types.ts` | New TS interfaces | Additive |
| `apps/web/src/components/charts/DimensionRadar.tsx` | **NEW FILE** | New component |
| `apps/web/src/components/charts/GradeBadge.tsx` | **NEW FILE** | New component |
| `tests/test_scoring.py` | **NEW FILE** | New test file |
| `tests/test_precheck.py` | **NEW FILE** | New test file |
| `tests/test_rubric.py` | **NEW FILE** | New test file |
| `tests/fixtures/rubric_*.yaml` | **NEW FILES** | Test fixtures |
| `tests/fixtures/skill_with_secret.md` | **NEW FILE** | Test fixture |
| `tests/fixtures/skill_with_shell.md` | **NEW FILE** | Test fixture |
| `tests/fixtures/skill_empty.md` | **NEW FILE** | Test fixture |

### 10.3 Import Compatibility

The new modules import from existing modules but no existing module imports from new modules:

```
md_evals/scoring.py  → imports from md_evals/metrics.py (CostMetrics, ContextMetrics)
md_evals/precheck.py → imports from md_evals/linter.py (LinterEngine, LinterConfig)
                      → imports from md_evals/rubric.py (RubricConfig)
md_evals/rubric.py   → imports from pydantic (standalone, no md_evals imports)
md_evals/cli.py      → imports from md_evals/precheck.py, md_evals/rubric.py (NEW imports only)
md_evals/reporter.py → imports from md_evals/scoring.py (NEW imports only)
```

No existing import graph is modified. No circular dependencies introduced.

---

## Appendix A: New File Inventory

| File | Purpose | LOC (est.) |
|------|---------|------------|
| `md_evals/scoring.py` | DimensionScore, EvalResult, EvalMetadata, grade functions | ~120 |
| `md_evals/precheck.py` | PreCheckEngine, PreCheckResult, PreCheckFinding, security checks | ~180 |
| `md_evals/rubric.py` | RubricConfig, RubricLoader, validation, exceptions | ~200 |
| `md_evals/rubric_default.yaml` | Default rubric shipped with package | ~40 |
| `apps/web/src/components/charts/DimensionRadar.tsx` | Radar chart for dimension scores | ~60 |
| `apps/web/src/components/charts/GradeBadge.tsx` | Letter grade display component | ~50 |
| `tests/test_scoring.py` | Unit + property tests for scoring | ~250 |
| `tests/test_precheck.py` | Unit tests for pre-check engine | ~200 |
| `tests/test_rubric.py` | Unit tests for rubric loading/validation | ~200 |
| `tests/fixtures/rubric_*.yaml` | 4 test rubric fixtures | ~80 |
| `tests/fixtures/skill_*.md` | 3 test skill fixtures | ~30 |

**Total new code**: ~1,410 lines (estimated)

## Appendix B: Counts Summary

| Category | Count |
|----------|-------|
| Requirements | 48 (DM: 8, RC: 11, GC: 6, PC: 10, CL: 9, WU: 5, AP: 5) |
| Scenarios | 25 |
| Acceptance Criteria | 46 |
| Edge Cases | 18 |
