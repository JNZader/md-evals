"""Schema-aware privacy guard for public non-canonical run documents."""

from __future__ import annotations

import math
import re


class NoncanonicalLiveLedgerSafetyError(ValueError):
    """A public non-canonical document contains private or secret material."""


_LEDGER_SCHEMA = "Gate1StrictNonCanonicalRecoveredLiveLedger.v1"
_SUMMARY_SCHEMA = "Gate1StrictNonCanonicalRecoveredLiveSummary.v1"
_SMOKE_SCHEMA = "Gate1StrictNonCanonicalPublicLedgerWriterSmoke.v1"

_SECRET_VALUE = re.compile(
    r"Bearer\s+\S+|sk-[A-Za-z0-9][A-Za-z0-9_-]*|"
    r"(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9][A-Za-z0-9_-]*|"
    r"(?:AKIA|ASIA)[A-Z0-9]{16}|"
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|"
    r"-----BEGIN(?:\s+[A-Z0-9]+)?\s+PRIVATE KEY-----",
    re.IGNORECASE,
)
_PRIVATE_FIELD = re.compile(
    r"(?:^|[_-])(request|response|request_data|response_data|request_metadata|"
    r"response_body|raw|raw_request|raw_response|rawresponse|"
    r"prompt|prompts|context|contexts|rendered_context|rendered_contexts|"
    r"authorization|auth|header|headers|bearer|token|tokens|apikey|api_key|"
    r"access_token|refresh_token|secret|password|credential|private_key|"
    r"authheader|authheaders|authorizationheader|authorizationheaders|"
    r"bearertoken|bearertokens|accesstoken|accesstokens|refreshtoken|refreshtokens|"
    r"xapikey|xapikeys|privatekey|"
    r"requestbody|responsebody|requestdata|responsedata|requestmetadata|responsemetadata|"
    r"rawrequest|rawresponse)(?:[_-]|$)",
    re.IGNORECASE,
)

_TOP = {
    "schema_version",
    "status",
    "canonical_status",
    "run_id",
    "created_at",
    "source_db_digest",
    "provider",
    "model",
    "authorization",
    "safety",
    "billing",
    "summary",
    "results",
}
_AUTH = {
    "selected_path",
    "raw_db_read_authorized",
    "execution_authorized_for_noncanonical_capture",
    "strict_input_created",
}
_SAFETY = {
    "token_generated_ephemerally",
    "token_printed",
    "raw_prompts_stored",
    "raw_contexts_stored",
    "raw_response_bodies_stored",
    "provider_fallback_allowed",
    "raw_prompts_exported",
    "raw_contexts_exported",
    "raw_responses_exported",
}
_BILLING = {"attestation_created", "reason"}
_SUMMARY = {
    "request_logs_read",
    "usage_logs_read",
    "completed_cells",
    "failed_cells",
    "redacted_cells",
    "attempted_calls",
    "planned_calls",
}
_RESULT = {
    "db_request_log_id",
    "cell_index",
    "case_name",
    "arm",
    "status",
    "started_at",
    "duration_ms",
    "request_digest",
    "response_digest",
    "selected_evidence_ids",
    "answer",
    "error_code",
    "error_message",
    "usage",
    "tool_evidence",
}
_DIGESTS = {"request_digest", "response_digest", "evidence_digest", "local_ledger_digest"}
_SAFE_AGGREGATES = {
    "prompt_tokens",
    "completion_tokens",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "token_count",
    "tokens_used",
    "tokensused",
    "tool_calls",
    "latency_ms",
    "attempts",
    "request_count",
    "response_count",
    "request_logs_read",
    "usage_logs_read",
    "redacted_cells",
    "request_id",
    "response_id",
    "request_status",
    "response_status",
    "db_request_log_id",
}
_USAGE_NESTED = {"tool_evidence", "usage_provenance"}
_USAGE_TOOL_EVIDENCE = {"enforcement", "mode", "source", "status", "observable", "toolCallCount"}
_USAGE_PROVENANCE = {"eventCount", "inputTokens", "outputTokens", "origin", "status"}


def _fail(path: str, message: str) -> None:
    raise NoncanonicalLiveLedgerSafetyError(f"{path} {message}")


def _normalise(key: str) -> str:
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    return camel_split.replace("-", "_").lower()


def _scalar(value: object) -> bool:
    return (
        value is None
        or type(value) in (str, bool, int)
        or (type(value) is float and math.isfinite(value))
    )


def _check_key(key: object, path: str, *, aggregate: bool = False, exempt: set[str] = set()) -> str:
    if type(key) is not str:
        _fail(path, "contains a non-string field name")
    normal = _normalise(key)
    if normal in exempt or (aggregate and normal in _SAFE_AGGREGATES):
        return normal
    if normal in _DIGESTS:
        return normal
    if _PRIVATE_FIELD.search(normal):
        _fail(f"{path}.{key}", "is not permitted in a public document")
    return normal


def _scan_public_values(value: object, path: str, active: set[int]) -> None:
    """Scan already schema-validated values for secrets, invalid values, and cycles."""
    if type(value) is dict:
        if id(value) in active:
            _fail(path, "contains a cyclic value")
        active.add(id(value))
        try:
            for key, child in value.items():
                _scan_public_values(child, f"{path}.{key}", active)
        finally:
            active.remove(id(value))
    elif type(value) is list:
        if id(value) in active:
            _fail(path, "contains a cyclic value")
        active.add(id(value))
        try:
            for index, child in enumerate(value):
                _scan_public_values(child, f"{path}[{index}]", active)
        finally:
            active.remove(id(value))
    elif type(value) is str:
        if _SECRET_VALUE.search(value):
            _fail(path, "contains a secret-like value")
    elif not _scalar(value):
        _fail(path, "contains a non-JSON value")


def _dict(value: object, path: str) -> dict:
    if type(value) is not dict:
        _fail(path, "must be a JSON object")
    return value


def _exact(value: object, path: str, allowed: set[str], required: set[str]) -> dict:
    obj = _dict(value, path)
    unknown = set(obj) - allowed
    if unknown:
        _fail(f"{path}.{next(iter(unknown))}", "is not permitted")
    missing = required - set(obj)
    if missing:
        _fail(f"{path}.{next(iter(missing))}", "is required")
    return obj


def _typed(
    obj: dict,
    path: str,
    strings: set[str] = set(),
    booleans: set[str] = set(),
    ints: set[str] = set(),
) -> None:
    for key, value in obj.items():
        if key in strings and type(value) is not str:
            _fail(f"{path}.{key}", "must be a string")
        if key in booleans and type(value) is not bool:
            _fail(f"{path}.{key}", "must be a boolean")
        if key in ints and (type(value) is not int):
            _fail(f"{path}.{key}", "must be an integer")


def _answer(value: object, path: str, active: set[int]) -> None:
    obj = _exact(
        value, path, {"answer", "citations", "abstain"}, {"answer", "citations", "abstain"}
    )
    if obj["answer"] is not None and type(obj["answer"]) is not str:
        _fail(f"{path}.answer", "must be a string or null")
    if type(obj["citations"]) is not list or any(
        type(item) is not str for item in obj["citations"]
    ):
        _fail(f"{path}.citations", "must be a list of strings")
    if type(obj["abstain"]) is not bool:
        _fail(f"{path}.abstain", "must be a boolean")
    _scan_public_values(obj, path, active)


def _public_summary(value: object, path: str, active: set[int]) -> None:
    """Validate an extensible summary whose values contain no nested payloads."""
    obj = _dict(value, path)
    if id(obj) in active:
        _fail(path, "contains a cyclic value")
    active.add(id(obj))
    try:
        for key, child in obj.items():
            _check_key(key, path, aggregate=True)
            if _scalar(child):
                if type(child) is str and _SECRET_VALUE.search(child):
                    _fail(f"{path}.{key}", "contains a secret-like value")
            elif type(child) is list and all(_scalar(item) for item in child):
                for item in child:
                    if type(item) is str and _SECRET_VALUE.search(item):
                        _fail(f"{path}.{key}", "contains a secret-like value")
            else:
                _fail(f"{path}.{key}", "must be a public scalar summary")
    finally:
        active.remove(id(obj))


def _usage_summary(value: object, path: str, active: set[int]) -> None:
    """Validate public usage summaries, including known nested public evidence sections."""
    obj = _dict(value, path)
    if id(obj) in active:
        _fail(path, "contains a cyclic value")
    active.add(id(obj))
    try:
        for key, child in obj.items():
            normal = _check_key(key, path, aggregate=True, exempt=_USAGE_NESTED)
            if normal == "tool_evidence":
                nested = _exact(child, f"{path}.{key}", _USAGE_TOOL_EVIDENCE, set())
                _typed(
                    nested,
                    f"{path}.{key}",
                    strings={"enforcement", "mode", "source", "status"},
                    booleans={"observable"},
                    ints={"toolCallCount"},
                )
                _scan_public_values(nested, f"{path}.{key}", active)
            elif normal == "usage_provenance":
                nested = _exact(child, f"{path}.{key}", _USAGE_PROVENANCE, set())
                _typed(
                    nested,
                    f"{path}.{key}",
                    strings={"origin", "status"},
                    ints={"eventCount", "inputTokens", "outputTokens"},
                )
                _scan_public_values(nested, f"{path}.{key}", active)
            elif _scalar(child):
                if type(child) is str and _SECRET_VALUE.search(child):
                    _fail(f"{path}.{key}", "contains a secret-like value")
            elif type(child) is list and all(_scalar(item) for item in child):
                for item in child:
                    if type(item) is str and _SECRET_VALUE.search(item):
                        _fail(f"{path}.{key}", "contains a secret-like value")
            else:
                _fail(f"{path}.{key}", "must be a public scalar summary")
    finally:
        active.remove(id(obj))


def _ledger(value: object, path: str, active: set[int]) -> None:
    required = _TOP - {"source_db_digest"}
    obj = _exact(value, path, _TOP, required)
    _typed(
        obj,
        path,
        strings={
            "schema_version",
            "status",
            "canonical_status",
            "run_id",
            "created_at",
            "source_db_digest",
            "provider",
            "model",
        },
    )
    auth = _exact(
        obj["authorization"],
        f"{path}.authorization",
        _AUTH,
        {"selected_path", "strict_input_created"},
    )
    _typed(
        auth, f"{path}.authorization", strings={"selected_path"}, booleans=_AUTH - {"selected_path"}
    )
    safety = _exact(
        obj["safety"],
        f"{path}.safety",
        _SAFETY,
        set(_SAFETY) - {"raw_prompts_exported", "raw_contexts_exported", "raw_responses_exported"},
    )
    _typed(safety, f"{path}.safety", booleans=set(safety))
    billing = _exact(obj["billing"], f"{path}.billing", _BILLING, _BILLING)
    _typed(billing, f"{path}.billing", strings={"reason"}, booleans={"attestation_created"})
    summary = _exact(
        obj["summary"],
        f"{path}.summary",
        _SUMMARY,
        {"completed_cells", "failed_cells", "attempted_calls", "planned_calls"},
    )
    _typed(summary, f"{path}.summary", ints=set(summary))
    if type(obj["results"]) is not list:
        _fail(f"{path}.results", "must be a list")
    for index, result in enumerate(obj["results"]):
        row = _exact(result, f"{path}.results[{index}]", _RESULT, set())
        _typed(
            row,
            f"{path}.results[{index}]",
            strings={
                "case_name",
                "arm",
                "status",
                "request_digest",
                "response_digest",
                "error_code",
                "error_message",
            },
            ints={"db_request_log_id", "cell_index", "duration_ms"},
        )
        if "started_at" in row and type(row["started_at"]) not in (str, int):
            _fail(f"{path}.results[{index}].started_at", "must be a string or integer")
        if "selected_evidence_ids" in row and (
            type(row["selected_evidence_ids"]) is not list
            or any(type(x) is not str for x in row["selected_evidence_ids"] or [])
        ):
            _fail(f"{path}.results[{index}].selected_evidence_ids", "must be a list of strings")
        if "answer" in row:
            _answer(row["answer"], f"{path}.results[{index}].answer", active)
        if "usage" in row:
            _usage_summary(row["usage"], f"{path}.results[{index}].usage", active)
        if "tool_evidence" in row:
            _public_summary(row["tool_evidence"], f"{path}.results[{index}].tool_evidence", active)
    _scan_public_values(obj, path, active)


def _summary(value: object, path: str, active: set[int]) -> None:
    obj = _exact(
        value,
        path,
        {
            "schema_version",
            "status",
            "canonical_status",
            "run_id",
            "created_at",
            "provider",
            "model",
            "raw_prompts_exported",
            "raw_contexts_exported",
            "raw_responses_exported",
            "completed_cells",
            "failed_cells",
            "redacted_cells",
            "attempted_calls",
            "planned_calls",
        },
        {
            "schema_version",
            "status",
            "canonical_status",
            "run_id",
            "created_at",
            "raw_prompts_exported",
            "raw_contexts_exported",
            "raw_responses_exported",
            "completed_cells",
            "failed_cells",
            "attempted_calls",
            "planned_calls",
        },
    )
    _typed(
        obj,
        path,
        strings={
            "schema_version",
            "status",
            "canonical_status",
            "run_id",
            "created_at",
            "provider",
            "model",
        },
        booleans={"raw_prompts_exported", "raw_contexts_exported", "raw_responses_exported"},
        ints={
            "completed_cells",
            "failed_cells",
            "redacted_cells",
            "attempted_calls",
            "planned_calls",
        },
    )
    _scan_public_values(obj, path, active)


def assert_public_noncanonical_live_ledger_safe(value: object) -> None:
    """Reject private material while validating recognized public schemas."""
    if type(value) is not dict:
        _fail("ledger", "must be a plain JSON object")

    schema_version = value.get("schema_version")
    if type(schema_version) is not str:
        _fail("ledger.schema_version", "must be a recognized public schema")
    if schema_version in {_LEDGER_SCHEMA, _SMOKE_SCHEMA}:
        _ledger(value, "ledger", set())
    elif schema_version == _SUMMARY_SCHEMA:
        _summary(value, "summary", set())
    else:
        _fail("ledger.schema_version", "must be a recognized public schema")
