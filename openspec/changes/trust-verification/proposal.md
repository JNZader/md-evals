# Proposal: Phase 3 — Trust & Verification

> **Status**: IMPLEMENTING
> **Author**: Javier Zader
> **Date**: 2026-03-17
> **Change**: trust-verification
> **Phase**: 3 of 5
> **Depends on**: Phase 2 (pipeline) — COMPLETE

---

## Intent

Add **evidence-backed scoring** to md-evals by requiring the LLM judge to cite specific lines from the SKILL.md file, and by allowing skill authors to embed **Gherkin-like acceptance criteria** that are automatically evaluated.

### Why this matters

Phase 2 gave us a structured pipeline (Auditor → Target → Judge), but the judge's scores are still opaque — you get a number and a rationale but no traceable evidence linking the score to the actual skill content. This creates two trust problems:

1. **Hallucinated reasoning**: The LLM judge may cite rules or lines that don't exist in the SKILL.md, inflating confidence in scores.
2. **Author-defined criteria gap**: Skill authors have no way to express "this is what success looks like" in a machine-evaluatable way.

Phase 3 introduces:

- **Citations Validator** (Feature #5): The judge must cite line numbers + text from SKILL.md. Citations are validated against actual content. Hallucinated citations trigger a score penalty.
- **Gherkin Eval Scenarios** (Feature #10): Skill authors embed `Given/When/Then` acceptance criteria that the pipeline automatically converts to test scenarios.

---

## Scope

### In Scope (Phase 3)

| Feature | Description |
|---------|-------------|
| Citation dataclass | `Citation(line, text, supports, verified)` frozen value object |
| CitationValidator | Validates citations against actual SKILL.md content (fuzzy match) |
| citation_penalty | Computes score adjustment (0.0–0.2) based on unverified citations |
| LLMJudgeDetector prompt update | Request citations in JSON output, parse and validate them |
| DimensionScore.evidence population | Verified citations become evidence strings |
| GherkinScenario dataclass | `GherkinScenario(given, when, then, raw)` frozen value object |
| parse_gherkin_scenarios | Parses `## Scenarios` / `## Acceptance Criteria` sections |
| GherkinProbe | Zero-LLM probe converting Gherkin scenarios to pipeline Scenarios |
| Plugin registration | GherkinProbe registered in BUILTIN_PROBES |

### Out of Scope

| Feature | Why |
|---------|-----|
| Citation line range references | Complexity — single line citations are sufficient for v1 |
| Custom Gherkin keywords | Standard Given/When/Then is sufficient |
| Scenario execution validation | Phase 4 concern — scenarios feed into existing pipeline |
| Score recalculation | Citations adjust per-dimension scores; overall grade recalculation is existing logic |

---

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| AC-01 | `Citation` is a frozen dataclass with `line`, `text`, `supports`, `verified` fields | Unit test |
| AC-02 | `CitationValidator.validate()` sets `verified=True` for citations where text matches actual line | Unit test |
| AC-03 | `CitationValidator.validate()` sets `verified=False` for out-of-range line numbers | Unit test |
| AC-04 | `CitationValidator.validate()` uses fuzzy (contains) matching, case-insensitive | Unit test |
| AC-05 | `citation_penalty()` returns 0.0 for all-verified citations | Unit test |
| AC-06 | `citation_penalty()` returns 0.2 for all-unverified citations | Unit test |
| AC-07 | `citation_penalty()` returns 0.0 for empty citation list | Unit test |
| AC-08 | `citation_penalty()` scales linearly between 0.0 and 0.2 | Unit test |
| AC-09 | LLMJudgeDetector prompt requests citations in JSON output | Code review |
| AC-10 | LLMJudgeDetector parses citations from judge response and validates them | Unit test (mocked LLM) |
| AC-11 | LLMJudgeDetector populates `DimensionScore.evidence` with verified citation strings | Unit test |
| AC-12 | `GherkinScenario` is a frozen dataclass with `given`, `when`, `then`, `raw` fields | Unit test |
| AC-13 | `parse_gherkin_scenarios()` parses bullet-format Given/When/Then | Unit test |
| AC-14 | `parse_gherkin_scenarios()` parses block-format Given/When/Then | Unit test |
| AC-15 | `parse_gherkin_scenarios()` recognizes both `## Scenarios` and `## Acceptance Criteria` | Unit test |
| AC-16 | `GherkinProbe` has `name = "gherkin"` and satisfies the Probe protocol | Unit test |
| AC-17 | `GherkinProbe.generate_scenarios()` converts Gherkin scenarios to pipeline Scenarios | Unit test |
| AC-18 | `GherkinProbe` is registered in `BUILTIN_PROBES` and discoverable via `discover_probes()` | Unit test |
| AC-19 | Empty/missing scenario sections produce empty scenario lists (no errors) | Unit test |
| AC-20 | All new types are exported from `md_evals.pipeline.__init__` | Import test |

---

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| LLM judge ignores citation instructions | High | Graceful degradation — missing citations = no penalty (not penalized for absence, only for hallucination) |
| Fuzzy matching too lenient | Medium | Contains check + case-insensitive is a good v1; can tighten with edit distance later |
| Gherkin parsing too rigid | Medium | Support both block and bullet formats; fall back to raw content parsing |

---

## Implementation

Two new modules + edits to three existing files:

- **CREATE** `md_evals/pipeline/citations.py` — Citation, CitationValidator, citation_penalty
- **CREATE** `md_evals/pipeline/gherkin.py` — GherkinScenario, parse_gherkin_scenarios, GherkinProbe
- **EDIT** `md_evals/pipeline/detectors.py` — update LLMJudgeDetector for citations
- **EDIT** `md_evals/pipeline/plugins.py` — register GherkinProbe
- **EDIT** `md_evals/pipeline/__init__.py` — export new types
