"""Offline contract tests for bridge ``/v1/generate`` response decoding."""

from copy import deepcopy

import pytest

from md_evals.bridge_usage import decode_generate_response
from md_evals.models import LLMResponse


def payload(text="answer", **extra):
    return {"text": text, **extra}


def test_generate_wire_uses_source_backed_text_field():
    response = decode_generate_response(
        {"text": "source-backed answer"}, model="model", provider="provider"
    )

    assert response.content == "source-backed answer"


def test_text_is_canonical_and_preserves_unrelated_content_in_raw_payload():
    source = {"text": "canonical", "content": "unrelated extra"}
    before = deepcopy(source)

    response = decode_generate_response(source, model="model", provider="provider")

    assert response.content == "canonical"
    assert source == before
    assert response.raw_response == before
    assert response.raw_response is not source


def reported(input_tokens, output_tokens, **extra):
    return {
        "status": "reported",
        "origin": "cli-output",
        "eventCount": 1,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        **extra,
    }


def test_reported_usage_preserves_zero_and_projects_only_known_fields():
    response = decode_generate_response(
        payload(
            usageProvenance=reported(0, 0, internalTrace="never retain"),
            tokensUsed=999,
        ),
        model="caller-model",
        provider="caller-provider",
        duration_ms=12,
        stage_type="bridge",
    )

    assert response.content == "answer"
    assert (response.model, response.provider, response.duration_ms, response.stage_type) == (
        "caller-model",
        "caller-provider",
        12,
        "bridge",
    )
    assert response.tokens == 0
    assert response.prompt_tokens == 0
    assert response.completion_tokens_detail == 0
    assert response.total_tokens == 0
    assert response.usage_provenance == {
        "status": "reported",
        "origin": "cli-output",
        "eventCount": 1,
        "inputTokens": 0,
        "outputTokens": 0,
    }
    assert response.raw_response["usageProvenance"]["internalTrace"] == "never retain"


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        (
            {
                "status": "partial",
                "origin": "cli-output",
                "eventCount": 1,
                "inputTokens": 4,
            },
            (4, None, None, 0),
        ),
        (
            {
                "status": "partial",
                "origin": "cli-output",
                "eventCount": 1,
                "outputTokens": 5,
            },
            (None, 5, None, 5),
        ),
    ],
)
def test_partial_usage_keeps_only_one_present_counter(usage, expected):
    response = decode_generate_response(
        payload(usageProvenance=usage), model="model", provider="provider"
    )

    assert (
        response.prompt_tokens,
        response.completion_tokens_detail,
        response.total_tokens,
        response.tokens,
    ) == expected
    assert response.usage_provenance == usage


@pytest.mark.parametrize(
    ("usage", "reason"),
    [
        (None, "invalid"),
        ({}, "invalid"),
        ({**reported(1, 1), "status": "unsupported"}, "invalid"),
        ({**reported(1, 1), "origin": "unsupported"}, "invalid"),
        *[
            ({**reported(1, 1), "eventCount": value}, "invalid")
            for value in (2, True, 1.0, 0, -1, "1", [])
        ],
        *[(reported(value, 0), "invalid") for value in (-1, 1.0, "1", None, True)],
        (reported(2**53, 0), "overflow"),
        (reported(2**53 - 1, 1), "overflow"),
        (
            {"status": "reported", "origin": "cli-output", "eventCount": 1, "inputTokens": 1},
            "invalid",
        ),
        ({"status": "partial", "origin": "cli-output", "eventCount": 1}, "invalid"),
        (
            {
                "status": "partial",
                "origin": "cli-output",
                "eventCount": 1,
                "inputTokens": 1,
                "outputTokens": None,
            },
            "invalid",
        ),
        (
            {
                "status": "partial",
                "origin": "cli-output",
                "eventCount": 1,
                "inputTokens": 1,
                "outputTokens": 1,
            },
            "invalid",
        ),
    ],
)
def test_invalid_or_missing_usage_is_unknown_without_rejecting_content(usage, reason):
    response = decode_generate_response(
        payload(usageProvenance=usage, tokensUsed=17), model="model", provider="provider"
    )

    assert response.content == "answer"
    assert (response.prompt_tokens, response.completion_tokens_detail, response.total_tokens) == (
        None,
        None,
        None,
    )
    assert response.tokens == 0
    assert response.usage_provenance == {
        "status": "unknown",
        "reason": reason,
    }


def test_missing_usage_is_unknown_absent_without_legacy_inference():
    response = decode_generate_response(payload(tokensUsed=17), model="model", provider="provider")

    assert response.usage_provenance == {"status": "unknown", "reason": "absent"}
    assert response.tokens == 0


@pytest.mark.parametrize("reason", ["absent", "invalid", "multiple-events", "overflow"])
def test_explicit_supported_unknown_reason_is_preserved_without_legacy_inference(reason):
    response = decode_generate_response(
        payload(
            usageProvenance={"status": "unknown", "reason": reason, "detail": "strip"},
            tokensUsed=0,
        ),
        model="model",
        provider="provider",
    )

    assert response.usage_provenance == {"status": "unknown", "reason": reason}
    assert response.tokens == 0
    assert (
        response.prompt_tokens is response.completion_tokens_detail is response.total_tokens is None
    )


def test_safe_boundary_and_raw_payload_are_retained_without_mutation():
    source = payload(usageProvenance=reported(2**53 - 1, 0), tokensUsed=3)
    before = deepcopy(source)

    response = decode_generate_response(source, model="model", provider="provider")

    assert source == before
    assert response.raw_response == before
    assert response.raw_response is not source
    assert response.prompt_tokens == 2**53 - 1
    assert response.total_tokens == 2**53 - 1


def test_empty_text_and_legacy_response_default_are_preserved():
    assert decode_generate_response(payload(""), model="model", provider="provider").content == ""
    assert LLMResponse(content="", model="model", provider="provider").usage_provenance is None


@pytest.mark.parametrize("value", [None, 1, [], {}])
def test_invalid_text_is_rejected_without_coercion(value):
    with pytest.raises(ValueError, match="text"):
        decode_generate_response(payload(value), model="model", provider="provider")


def test_content_only_payload_is_rejected_without_legacy_fallback():
    with pytest.raises(ValueError, match="text"):
        decode_generate_response({"content": "legacy"}, model="model", provider="provider")


@pytest.mark.parametrize("value", [None, [], "answer"])
def test_invalid_top_level_payload_is_rejected_without_coercion(value):
    with pytest.raises(ValueError, match="payload"):
        decode_generate_response(value, model="model", provider="provider")
