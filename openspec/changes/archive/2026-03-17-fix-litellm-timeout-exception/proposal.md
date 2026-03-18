# Proposal: Fix LiteLLM Timeout Exception Handling

> **Status**: PROPOSED
> **Date**: 2026-03-17
> **Change**: fix-litellm-timeout-exception

---

## Intent

Fix timeout-related exceptions from LiteLLM so md-evals fails gracefully, reports clear diagnostics, and applies consistent retry/timeout behavior across evaluation flows.

## Scope

### In Scope

- Identify where LiteLLM timeout exceptions surface in the evaluation pipeline and API/server flows.
- Normalize timeout exception handling into a predictable error contract.
- Improve user-facing messages for timeout failures (CLI and structured outputs).
- Add tests for timeout scenarios and expected recovery/failure behavior.

### Out of Scope

- Broad networking reliability redesign (circuit breakers, global backoff strategy).
- Provider-specific advanced timeout policies beyond current md-evals configuration model.
- Unrelated LiteLLM exception classes not tied to timeout behavior.

## Approach

- Map current timeout paths and exception types thrown by LiteLLM in the project.
- Introduce a single timeout handling path that preserves root cause while returning md-evals-friendly errors.
- Ensure retries and timeout configuration are respected consistently by orchestrator/pipeline execution.
- Validate with unit/integration tests and regression checks for existing evaluation behavior.

## Risks

| Risk | Mitigation |
|------|------------|
| LiteLLM exception shape varies by provider/version | Use robust type/attribute checks and fallback normalization |
| Over-catching hides non-timeout failures | Match timeout-specific signals and re-raise unrelated exceptions |
| Retry changes affect runtime/cost | Keep defaults conservative and test expected retry counts |

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| AC-01 | Timeout exceptions from LiteLLM are mapped to a consistent md-evals error type/path | Unit test |
| AC-02 | CLI output clearly indicates timeout cause and next action | CLI test/snapshot |
| AC-03 | Timeout handling does not swallow non-timeout exceptions | Unit test |
| AC-04 | Existing non-timeout evaluation flows remain unchanged | Regression test |
| AC-05 | Configuration-driven timeout/retry behavior is respected during execution | Integration test |
