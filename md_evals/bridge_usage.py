"""Pure decoder for captured bridge ``/v1/generate`` response payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from md_evals.models import LLMResponse, UsageProvenance


_MAX_SAFE_INTEGER = 2**53 - 1
_UNKNOWN_REASONS = frozenset({"absent", "invalid", "multiple-events", "overflow"})
_MISSING = object()


def decode_generate_response(
    payload: dict[str, Any],
    *,
    model: str,
    provider: str,
    duration_ms: int = 0,
    stage_type: str = "single_pass",
) -> LLMResponse:
    """Decode a bridge response without treating caller labels as attestation.

    Usage provenance is deliberately interpreted independently from the legacy
    ``tokensUsed`` field. Invalid provenance is represented as ``unknown`` so a
    valid generated answer remains usable.
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dictionary")

    text = payload.get("text")
    if not isinstance(text, str):
        raise ValueError("payload text must be a string")

    provenance, prompt_tokens, completion_tokens, total_tokens, tokens = _decode_usage(payload)
    from md_evals.models import LLMResponse

    return LLMResponse(
        content=text,
        model=model,
        provider=provider,
        tokens=tokens,
        duration_ms=duration_ms,
        raw_response=deepcopy(payload),
        prompt_tokens=prompt_tokens,
        completion_tokens_detail=completion_tokens,
        total_tokens=total_tokens,
        stage_type=stage_type,
        usage_provenance=provenance,
    )


def _decode_usage(
    payload: dict[str, Any],
) -> tuple[UsageProvenance, int | None, int | None, int | None, int]:
    return decode_usage_provenance(payload.get("usageProvenance", _MISSING))


def decode_usage_provenance(
    usage: object,
) -> tuple[UsageProvenance, int | None, int | None, int | None, int]:
    """Strictly normalize bridge telemetry, not billing or identity attestation.

    Returned counters are independently known only when validated provenance
    supplies them. Callers must not infer missing values from legacy fields.
    """
    if usage is _MISSING:
        return _unknown("absent")

    if not isinstance(usage, dict):
        return _unknown("invalid")

    status = usage.get("status")
    if status == "unknown":
        reason = usage.get("reason")
        if isinstance(reason, str) and reason in _UNKNOWN_REASONS:
            return ({"status": "unknown", "reason": reason}, None, None, None, 0)
        return _unknown("invalid")

    if not _has_valid_source(usage):
        return _unknown("invalid")

    if status == "reported":
        input_tokens = usage.get("inputTokens")
        output_tokens = usage.get("outputTokens")
        invalid_reason = _counter_reason(input_tokens) or _counter_reason(output_tokens)
        if invalid_reason is not None:
            return _unknown(invalid_reason)
        total_tokens = input_tokens + output_tokens
        if total_tokens > _MAX_SAFE_INTEGER:
            return _unknown("overflow")
        return (
            _project_usage("reported", input_tokens=input_tokens, output_tokens=output_tokens),
            input_tokens,
            output_tokens,
            total_tokens,
            output_tokens,
        )

    if status == "partial":
        has_input = "inputTokens" in usage
        has_output = "outputTokens" in usage
        if has_input == has_output:
            return _unknown("invalid")
        counter = usage["inputTokens"] if has_input else usage["outputTokens"]
        invalid_reason = _counter_reason(counter)
        if invalid_reason is not None:
            return _unknown(invalid_reason)
        if has_input:
            return (_project_usage("partial", input_tokens=counter), counter, None, None, 0)
        return (_project_usage("partial", output_tokens=counter), None, counter, None, counter)

    return _unknown("invalid")


def _has_valid_source(usage: dict[str, Any]) -> bool:
    return (
        usage.get("origin") == "cli-output"
        and type(usage.get("eventCount")) is int
        and usage["eventCount"] == 1
    )


def _counter_reason(value: Any) -> str | None:
    if type(value) is not int or value < 0:
        return "invalid"
    if value > _MAX_SAFE_INTEGER:
        return "overflow"
    return None


def _project_usage(
    status: str, *, input_tokens: int | None = None, output_tokens: int | None = None
) -> UsageProvenance:
    projected: UsageProvenance = {
        "status": status,
        "origin": "cli-output",
        "eventCount": 1,
    }
    if input_tokens is not None:
        projected["inputTokens"] = input_tokens
    if output_tokens is not None:
        projected["outputTokens"] = output_tokens
    return projected


def _unknown(reason: str) -> tuple[UsageProvenance, None, None, None, int]:
    return ({"status": "unknown", "reason": reason}, None, None, None, 0)
