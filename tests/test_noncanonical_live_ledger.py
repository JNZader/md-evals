"""Offline tests for the public non-canonical live ledger safety guard."""

from collections import UserDict
from types import MappingProxyType

import pytest

from md_evals.noncanonical_live_ledger import (
    NoncanonicalLiveLedgerSafetyError,
    assert_public_noncanonical_live_ledger_safe,
)


def recovered_ledger(schema_version="Gate1StrictNonCanonicalRecoveredLiveLedger.v1"):
    return {
        "schema_version": schema_version,
        "status": "completed",
        "canonical_status": "smoke-only/non-canonical",
        "run_id": "RUN-123",
        "created_at": "2026-09-14T00:00:00Z",
        "source_db_digest": "d" * 64,
        "provider": "gateway",
        "model": "model-name",
        "authorization": {
            "selected_path": "approved",
            "raw_db_read_authorized": True,
            "execution_authorized_for_noncanonical_capture": False,
            "strict_input_created": True,
        },
        "safety": {
            "token_generated_ephemerally": True,
            "token_printed": False,
            "raw_prompts_stored": False,
            "raw_contexts_stored": False,
            "raw_response_bodies_stored": False,
            "provider_fallback_allowed": False,
            "raw_prompts_exported": False,
            "raw_contexts_exported": False,
            "raw_responses_exported": False,
        },
        "billing": {"attestation_created": True, "reason": "public aggregate evidence only"},
        "summary": {
            "request_logs_read": 12,
            "usage_logs_read": 12,
            "completed_cells": 1,
            "failed_cells": 0,
            "redacted_cells": 0,
            "attempted_calls": 1,
            "planned_calls": 1,
        },
        "results": [
            {
                "db_request_log_id": 7,
                "cell_index": 0,
                "case_name": "case",
                "arm": "arm",
                "status": "completed",
                "started_at": 1,
                "duration_ms": 10,
                "request_digest": "a" * 64,
                "response_digest": "b" * 64,
                "selected_evidence_ids": ["e1"],
                "usage": {
                    "tokensUsed": 12,
                    "prompt_tokens": 4,
                    "tool_evidence": {
                        "enforcement": "none",
                        "mode": "none",
                        "source": "none",
                        "status": "not_requested",
                        "observable": True,
                        "toolCallCount": 0,
                    },
                    "usage_provenance": {
                        "eventCount": 1,
                        "inputTokens": 4,
                        "outputTokens": 8,
                        "origin": "public",
                        "status": "observed",
                    },
                },
                "tool_evidence": {"toolCallCount": 0, "evidence_digest": "c" * 64},
            }
        ],
    }


def recovered_summary():
    return {
        "schema_version": "Gate1StrictNonCanonicalRecoveredLiveSummary.v1",
        "status": "completed",
        "canonical_status": "smoke-only/non-canonical",
        "run_id": "RUN-123",
        "created_at": "2026-09-14T00:00:00Z",
        "raw_prompts_exported": False,
        "raw_contexts_exported": False,
        "raw_responses_exported": False,
        "completed_cells": 1,
        "failed_cells": 0,
        "attempted_calls": 1,
        "planned_calls": 1,
    }


def assert_rejected(value):
    with pytest.raises(NoncanonicalLiveLedgerSafetyError):
        assert_public_noncanonical_live_ledger_safe(value)


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"status": "completed"},
        {"operator_note": "completed", "attempts": 1},
        {"schema_version": []},
        {"schema_version": {}},
    ],
)
def test_unknown_or_missing_schema_fails_closed(value):
    assert_rejected(value)


def test_recognized_recovered_ledger_and_smoke_schema_pass():
    assert_public_noncanonical_live_ledger_safe(recovered_ledger())
    assert_public_noncanonical_live_ledger_safe(
        recovered_ledger("Gate1StrictNonCanonicalPublicLedgerWriterSmoke.v1")
    )


def test_recognized_summary_schema_passes_export_flags():
    assert_public_noncanonical_live_ledger_safe(recovered_summary())


@pytest.mark.parametrize(
    "mapping", [MappingProxyType({"status": "ok"}), UserDict({"status": "ok"})]
)
def test_non_json_mapping_types_are_rejected(mapping):
    assert_rejected(mapping)


@pytest.mark.parametrize(
    "key",
    [
        "request_data",
        "response_data",
        "raw_response",
        "rawResponse",
        "prompt",
        "prompts",
        "context",
        "contexts",
        "rendered_context",
        "request",
        "response",
        "raw",
    ],
)
def test_recognized_ledger_rejects_raw_fields(key):
    ledger = recovered_ledger()
    ledger["results"][0][key] = "private"
    assert_rejected(ledger)


def test_recognized_ledger_rejects_unknown_top_level_and_result_keys():
    ledger = recovered_ledger()
    ledger["unexpected"] = 1
    assert_rejected(ledger)

    ledger = recovered_ledger()
    ledger["results"][0]["unexpected"] = 1
    assert_rejected(ledger)


@pytest.mark.parametrize("section", ["usage", "tool_evidence"])
def test_flexible_sections_reject_nested_unknown_values(section):
    ledger = recovered_ledger()
    ledger["results"][0][section]["unknown"] = {"nested": "value"}
    assert_rejected(ledger)


def test_usage_allows_only_known_public_nested_sections():
    assert_public_noncanonical_live_ledger_safe(recovered_ledger())

    ledger = recovered_ledger()
    ledger["results"][0]["usage"]["tool_evidence"]["unexpected"] = 1
    assert_rejected(ledger)

    ledger = recovered_ledger()
    ledger["results"][0]["usage"]["usage_provenance"]["unexpected"] = 1
    assert_rejected(ledger)


@pytest.mark.parametrize(
    "key",
    [
        "authheader",
        "authheaders",
        "authorizationheader",
        "authorizationheaders",
        "bearertoken",
        "bearertokens",
        "accesstoken",
        "accesstokens",
        "refreshtoken",
        "refreshtokens",
        "xapikey",
        "xapikeys",
        "privatekey",
        "requestbody",
        "responsebody",
        "requestmetadata",
        "responsemetadata",
        "authorization",
        "raw_prompts_stored",
        "raw_response_bodies_stored",
        "authorization_header",
        "bearerToken",
        "api-key",
        "x-api-key",
        "private_key",
        "request_data",
        "responseBody",
    ],
)
def test_flexible_sections_reject_sensitive_key_variants(key):
    for section in ("usage", "tool_evidence"):
        ledger = recovered_ledger()
        ledger["results"][0][section][key] = "redacted"
        assert_rejected(ledger)


@pytest.mark.parametrize(
    "value",
    [
        "Bearer abc",
        "sk-test",
        "ghp_test",
        "github_pat_test",
        "AKIA1234567890ABCDEF",
        "ASIA1234567890ABCDEF",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_secret_like_values_are_rejected_in_recognized_schemas(value):
    ledger = recovered_ledger()
    ledger["results"][0]["answer"] = {"answer": value, "citations": [], "abstain": False}
    assert_rejected(ledger)

    summary = recovered_summary()
    summary["provider"] = value
    assert_rejected(summary)


def test_closed_answer_envelope_is_allowed_but_malformed_one_is_not():
    ledger = recovered_ledger()
    ledger["results"][0]["answer"] = {"answer": "VALUE", "citations": ["e1"], "abstain": False}
    assert_public_noncanonical_live_ledger_safe(ledger)

    ledger["results"][0]["answer"]["extra"] = "nope"
    assert_rejected(ledger)


def test_bad_safety_type_is_rejected():
    ledger = recovered_ledger()
    ledger["safety"]["token_printed"] = "false"
    assert_rejected(ledger)


def test_cycles_fail_without_generic_top_level_acceptance():
    ledger = recovered_ledger()
    cycle = []
    cycle.append(cycle)
    ledger["results"][0]["selected_evidence_ids"] = cycle
    assert_rejected(ledger)
