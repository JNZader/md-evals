# Tasks: fix-litellm-timeout-exception

> **Status**: VERIFIED (AC mapping artifact completed)
> **Date**: 2026-03-17
> **Change**: fix-litellm-timeout-exception

---

## Phase 1: Timeout Classification and Normalization

- [x] **1.1** Inventory all LiteLLM call sites and current timeout exception handling paths.
- [x] **1.2** Implement a shared timeout classifier with ordered checks (type, cause chain, attribute, conservative message fallback).
- [x] **1.3** Implement normalized timeout error contract fields (`error_type`, `error_code`, `message`, `provider`, `model`, `stage`, `is_retryable`, retry metadata).
- [x] **1.4** Add guardrails to avoid timeout false positives for non-timeout exception classes/signals.

## Phase 2: Shared Error Mapping Integration

- [x] **2.1** Add a shared error-mapping entry point used by orchestrator and non-orchestrator flows.
- [x] **2.2** Route timeout exceptions through the classifier + normalizer path.
- [x] **2.3** Preserve existing non-timeout behavior by re-raising/routing unchanged.
- [x] **2.4** Keep backward compatibility for existing failure object consumers.

## Phase 3: Retry and Timeout Policy Alignment

- [x] **3.1** Ensure configured timeout values are honored in all mapped LiteLLM execution paths.
- [x] **3.2** Ensure retry behavior follows configured attempts/backoff without hidden retries.
- [x] **3.3** Include attempt and max-attempt metadata on terminal timeout failures.
- [x] **3.4** Validate mixed retry outcomes (timeout then non-timeout, timeout then success) preserve terminal error semantics.

## Phase 4: CLI and Structured Output

- [x] **4.1** Update CLI timeout presentation with explicit timeout label and concise remediation guidance.
- [x] **4.2** Update JSON/report outputs to include normalized timeout fields while preserving existing schema keys.
- [x] **4.3** Verify output consistency across orchestrator and non-orchestrator execution modes.

## Phase 5: Tests and Regression Safety

- [x] **5.1** Add unit tests for timeout classifier (known class, chained cause, fallback message, ambiguous/non-timeout cases).
- [x] **5.2** Add unit tests for timeout normalizer (required contract fields, unknown metadata fallback, retry metadata).
- [x] **5.3** Add integration tests for retry/timeout scenarios (success before limit, exhaust retries, zero-retry policy).
- [x] **5.4** Add CLI/output tests for timeout messaging and structured payload compatibility.
- [x] **5.5** Add regression tests to confirm success paths and non-timeout failure behavior remain unchanged.

## Completion Criteria

- [x] **C.1** All acceptance criteria in `openspec/changes/fix-litellm-timeout-exception/spec.md` are covered by tests.
- [x] **C.2** Verification artifacts document AC-to-test mapping and pass results.
- [x] **C.3** Change is ready for `/sdd:apply fix-litellm-timeout-exception`.
