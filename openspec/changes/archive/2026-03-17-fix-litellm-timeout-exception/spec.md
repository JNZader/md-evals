# Spec: Fix LiteLLM Timeout Exception Handling

> **Status**: DRAFT
> **Date**: 2026-03-17
> **Change**: fix-litellm-timeout-exception

---

## 1. Overview

This spec defines timeout exception behavior for LiteLLM calls so md-evals handles timeout failures consistently, preserves root cause diagnostics, and avoids swallowing unrelated errors.

---

## 2. Requirements

### 2.1 Timeout Classification and Mapping

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-TM-01 | The system SHALL classify LiteLLM timeout-related failures into a single md-evals timeout error path | MUST |
| REQ-TM-02 | Timeout mapping SHALL preserve root cause details (provider/model/stage and original exception text when available) | MUST |
| REQ-TM-03 | Timeout mapping SHALL include a stable error code/label usable in CLI and JSON outputs | MUST |
| REQ-TM-04 | Timeout classification SHALL be resilient to provider/version-specific exception shapes (type checks plus message/attribute fallback) | MUST |
| REQ-TM-05 | Non-timeout LiteLLM exceptions SHALL NOT be mapped as timeout errors | MUST |

### 2.2 Error Contract

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-EC-01 | Timeout failures SHALL produce a normalized error object consumable by orchestrator and non-orchestrator flows | MUST |
| REQ-EC-02 | Normalized timeout errors SHALL include at least: `error_type`, `error_code`, `message`, `provider`, `model`, `stage`, `is_retryable` | MUST |
| REQ-EC-03 | Normalized timeout message SHALL be action-oriented and indicate next step (increase timeout, retry, reduce payload) | SHOULD |
| REQ-EC-04 | Error contract SHALL be backward compatible for callers that currently consume generic failure paths | MUST |

### 2.3 Retry and Timeout Behavior

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-RT-01 | Timeout handling SHALL respect configured timeout values from existing md-evals configuration | MUST |
| REQ-RT-02 | Timeout handling SHALL respect configured retry policy (attempt count/backoff where already supported) | MUST |
| REQ-RT-03 | Timeout mapping SHALL not introduce implicit extra retries beyond configured policy | MUST |
| REQ-RT-04 | Final failure after retries SHALL emit normalized timeout error with retry-attempt metadata | SHOULD |

### 2.4 CLI and Structured Output

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-OUT-01 | CLI output SHALL clearly indicate timeout as the failure cause | MUST |
| REQ-OUT-02 | CLI output SHALL include concise remediation hint(s) for timeout failures | SHOULD |
| REQ-OUT-03 | JSON/structured outputs SHALL expose normalized timeout fields without losing existing output fields | MUST |
| REQ-OUT-04 | Timeout outputs SHALL be consistent across orchestrator and non-orchestrator execution modes | MUST |

### 2.5 Regression Safety

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-RG-01 | Existing non-timeout exception behavior SHALL remain unchanged | MUST |
| REQ-RG-02 | Successful evaluation flows SHALL remain unchanged | MUST |
| REQ-RG-03 | Timeout handling SHALL not mask programming/configuration errors unrelated to timeout | MUST |

---

## 3. Scenarios

### 3.1 Timeout Scenarios

**SC-TM-01: Provider timeout exception with known class**
- Given: LiteLLM raises a known timeout exception class
- When: md-evals executes an LLM call
- Then: Failure is mapped to normalized timeout error contract
- And: Root cause/provider/model metadata are retained

**SC-TM-02: Timeout signaled via message/attributes only**
- Given: LiteLLM/provider raises generic exception containing timeout indicators
- When: md-evals classifies the exception
- Then: Failure is still mapped to normalized timeout error
- And: Mapping uses fallback detection safely

**SC-TM-03: Non-timeout LiteLLM error**
- Given: LiteLLM raises authentication or validation error
- When: md-evals handles the exception
- Then: Error is NOT mapped as timeout
- And: Original non-timeout handling path is preserved

### 3.2 Retry and Policy Scenarios

**SC-RT-01: Timeout succeeds before retry limit**
- Given: First attempt times out, second attempt succeeds within policy
- When: Evaluation executes with retries enabled
- Then: Run succeeds and no terminal timeout error is emitted

**SC-RT-02: Timeout exceeds retry policy**
- Given: All attempts timeout up to configured retry limit
- When: Evaluation finishes attempts
- Then: Final result is normalized timeout error
- And: Output includes attempt count metadata

**SC-RT-03: Zero-retry policy**
- Given: Retry policy disabled/zero retries
- When: First timeout occurs
- Then: Failure returns immediately as normalized timeout error

### 3.3 Output Scenarios

**SC-OUT-01: CLI timeout presentation**
- Given: Evaluation fails due to timeout
- When: CLI renders result
- Then: CLI shows timeout cause explicitly and remediation hint

**SC-OUT-02: Structured timeout payload**
- Given: Evaluation fails due to timeout
- When: JSON/report output is generated
- Then: Output includes normalized timeout fields and existing schema compatibility

### 3.4 Regression Scenarios

**SC-RG-01: Non-timeout flow remains stable**
- Given: Evaluation fails with non-timeout error
- When: Error is handled
- Then: Behavior matches previous non-timeout semantics

**SC-RG-02: Happy path unchanged**
- Given: No timeout occurs
- When: Evaluation runs successfully
- Then: Outputs and scoring behavior remain unchanged

---

## 4. Acceptance Criteria

| AC | Criterion |
|----|-----------|
| AC-01 | Timeout exceptions from LiteLLM map to one consistent md-evals timeout path |
| AC-02 | Normalized timeout error retains actionable root-cause context (provider/model/stage/message) |
| AC-03 | CLI output explicitly names timeout and suggests next action |
| AC-04 | Structured outputs expose normalized timeout fields without breaking current consumers |
| AC-05 | Non-timeout exceptions are not misclassified as timeout |
| AC-06 | Configured timeout and retry settings are honored during execution |
| AC-07 | Retry behavior does not exceed configured retry limits |
| AC-08 | Existing success and non-timeout behaviors pass regression checks unchanged |

---

## 5. Edge Cases

| ID | Edge Case | Expected Behavior |
|----|-----------|-------------------|
| EC-01 | Timeout exception with missing provider/model metadata | Normalized error sets unknown/default metadata without crashing |
| EC-02 | Exception chain contains timeout nested as cause | Classifier identifies timeout via chained causes and maps correctly |
| EC-03 | Exception message includes ambiguous timeout wording | Classifier uses conservative rules to avoid false positives |
| EC-04 | Cancellation/interruption exception occurs | Not mapped as timeout unless explicitly timeout-classified |
| EC-05 | Mixed failures across retries (timeout then non-timeout) | Final surfaced error reflects terminal failure accurately |

---

## 6. Verification Plan

- Unit tests for timeout classifier and normalized error contract.
- Unit tests proving non-timeout exceptions bypass timeout mapping.
- Integration tests for retry/timeout policy behavior under simulated timeout failures.
- CLI snapshot or formatter tests for timeout messaging.
- Regression tests for existing non-timeout and success flows.
