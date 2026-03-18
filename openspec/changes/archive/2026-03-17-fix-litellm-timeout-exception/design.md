# Design: Fix LiteLLM Timeout Exception Handling

> **Status**: DRAFT
> **Date**: 2026-03-17
> **Change**: fix-litellm-timeout-exception

---

## 1. Design Goals

- Provide one canonical timeout exception path for all LiteLLM calls.
- Preserve diagnostics needed for troubleshooting and reporting.
- Keep existing non-timeout behavior untouched.
- Enforce configuration-driven timeout and retry behavior without hidden retries.
- Make timeout failures easy to identify in CLI and structured outputs.

---

## 2. Architecture and Boundaries

### 2.1 Proposed Components

1. **Timeout Classifier**
   - Input: raw exception plus optional execution context.
   - Output: timeout classification result (`is_timeout`, `reason`, `confidence`).
   - Strategy: ordered checks using type, known LiteLLM signals, chained causes, and conservative message fallback.

2. **Timeout Normalizer**
   - Input: classification result, exception, runtime context.
   - Output: normalized md-evals error payload.
   - Responsibility: build stable contract fields and preserve root-cause text safely.

3. **Error Mapping Entry Point**
   - Shared function used by orchestrator and non-orchestrator call paths.
   - Centralizes `try/except` mapping so behavior is consistent across execution modes.

4. **Output Adapters**
   - CLI formatter branch for timeout-specific, action-oriented messages.
   - JSON/report serialization branch that includes normalized timeout fields while keeping existing schema fields.

### 2.2 Flow

1. LLM call raises an exception.
2. Shared mapper invokes Timeout Classifier.
3. If timeout: invoke Timeout Normalizer and emit standardized timeout error.
4. If not timeout: re-raise or route through existing non-timeout logic unchanged.
5. Retry layer consults existing configured policy only; final failure includes attempt metadata.

---

## 3. Data Contract

The normalized timeout error contract will include:

- `error_type`: stable category (e.g. `llm_timeout`)
- `error_code`: stable machine-friendly code (e.g. `LITELLM_TIMEOUT`)
- `message`: actionable human-readable message
- `provider`: provider identifier or `unknown`
- `model`: model identifier or `unknown`
- `stage`: execution stage (e.g. generation/scoring/orchestrator step)
- `is_retryable`: boolean based on timeout semantics and policy
- `attempt`: current attempt number (when available)
- `max_attempts`: configured total attempts (when available)
- `raw_exception`: sanitized original exception text

Backward compatibility rule: existing top-level failure fields stay present; normalized fields are additive or mapped without removing current consumer-facing keys.

---

## 4. Classification Strategy

Classifier checks run in strict order to reduce false positives:

1. **Known exception type checks** for timeout classes exposed by LiteLLM/provider SDKs.
2. **Cause-chain inspection** (`__cause__`, `__context__`) for nested timeout signals.
3. **Attribute inspection** for timeout indicators on exception objects.
4. **Message heuristic fallback** using conservative timeout tokens.

Guardrails:

- Cancellation/interruption exceptions are excluded unless explicitly timeout-typed.
- Auth/validation/rate-limit/server errors are never remapped as timeout solely by weak message hints.
- Ambiguous cases default to non-timeout path.

---

## 5. Retry and Timeout Policy Integration

- Reuse existing timeout/retry configuration sources; do not introduce parallel config knobs.
- Retry coordinator remains source of truth for attempt count and backoff.
- Mapper is pure with respect to retry decisions; it only classifies/maps current failure.
- Final emitted timeout error includes attempt metadata when available from retry context.

---

## 6. CLI and Structured Output Design

### CLI

- Prefix timeout failures with explicit timeout label.
- Include one short remediation string:
  - increase timeout,
  - reduce payload size,
  - retry with lower concurrency.

### Structured Output

- Add normalized timeout fields under existing failure object.
- Keep current schema keys used by existing consumers.
- Ensure orchestrator and non-orchestrator paths serialize the same timeout contract.

---

## 7. Test Design

1. **Unit: Classifier**
   - known timeout classes,
   - cause-chain timeouts,
   - ambiguous messages,
   - explicit non-timeout exceptions.

2. **Unit: Normalizer**
   - required contract fields,
   - unknown metadata fallback,
   - retry metadata inclusion.

3. **Integration: Retry/Timeout Policy**
   - timeout then success before max attempts,
   - timeout through all attempts,
   - zero-retry policy.

4. **Output Tests**
   - CLI timeout rendering and remediation hint,
   - JSON payload contract and backward-compatible keys.

5. **Regression**
   - non-timeout failures unchanged,
   - happy path unchanged.

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Provider exception drift | Timeout misses or false positives | Keep classifier layered with type + cause + conservative fallback tests |
| Over-normalization | Loss of debugging context | Preserve original exception text and stage/provider/model metadata |
| Behavioral regression | Existing flows break | Add targeted regression suite for success and non-timeout failures |
| Retry inflation | Higher latency/cost | Keep retry ownership in existing policy layer and assert attempt counts in integration tests |

---

## 9. Rollout Plan

1. Introduce classifier + normalizer behind shared mapper.
2. Wire mapper into both orchestrator and non-orchestrator paths.
3. Update CLI/JSON output branches for timeout contract.
4. Add and pass unit/integration/regression tests.
5. Enable by default once parity checks pass.
