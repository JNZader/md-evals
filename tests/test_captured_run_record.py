import pytest

from md_evals.captured_run_record import (
    ARMS,
    CaptureRecordError,
    CompletionOperationalError,
    FrozenCell,
    capture_bound_cells,
    summarize_run,
)
from md_evals.models import LLMResponse


@pytest.fixture
def anyio_backend():
    return "asyncio"


def cell(arm="CONTROL", **changes):
    values = dict(
        cell_id=f"cell-{arm}",
        task_id="task-bound",
        prompt="frozen prompt",
        case_id="case-bound",
        capture_number=1,
        arm_id=arm,
        prompt_digest=__import__("hashlib").sha256(b"frozen prompt").hexdigest(),
        context_bytes=b"",
        context_digest=__import__("hashlib").sha256(b"").hexdigest(),
        selected_ids=(),
        tools="none",
        tool_configuration="none",
        provider_pin="pinned-provider",
        model_pin="pinned-model",
        endpoint_pin="approved-endpoint",
        model_config_digest="config",
        code_revision="revision",
        budget="approved",
        timeout="approved",
        operator="operator",
        reviewer="reviewer",
        arm_mapping_decision_id="decision",
        fixture_id="fixture",
        fixture_revision="fixture-revision",
        context_size=0,
        started_at="unknown",
        finished_at="unknown",
        request_id="unknown",
        raw_output_ref="raw-ref",
        state="missing",
        factual_failure_reason="not_applicable",
        route_label="route-label",
        identity_attestation="attested-input-provenance",
    )
    values.update(changes)
    return FrozenCell(**values)


@pytest.mark.anyio
async def test_one_call_and_private_public_split():
    calls = []

    async def complete(prompt, system_prompt=None):
        calls.append((prompt, system_prompt))
        return LLMResponse(
            content="sample answer",
            model="model-alpha",
            provider="provider-alpha",
            raw_response={"channel": "sample-wire"},
        )

    record = (await capture_bound_cells((cell(),), complete))[0]
    assert calls == [("frozen prompt", None)]
    public = record.public_reference()
    assert record.response.content == "sample answer"
    assert record.response.model == "model-alpha"
    assert record.response.provider == "provider-alpha"
    assert record.response.raw_response["channel"] == "sample-wire"
    assert record.raw_wire_payload == (
        '{"completion_tokens_detail":null,"content":"sample answer","duration_ms":0,'
        '"model":"model-alpha","prompt_tokens":null,"provider":"provider-alpha",'
        '"raw_response":{"channel":"sample-wire"},"stage_type":"single_pass",'
        '"tokens":0,"total_tokens":null,"usage_provenance":null}'
    )
    assert "secret" not in repr(public)
    assert public.denominator_eligible is True
    assert public.planned_denominator == 12
    assert record.route_label != record.identity_attestation


@pytest.mark.anyio
async def test_failure_is_explicit_and_does_not_reduce_denominator():
    async def complete(prompt, system_prompt=None):
        raise CompletionOperationalError("offline completion unavailable")

    record = (await capture_bound_cells((cell(),), complete))[0]
    summary = summarize_run((record,))
    assert record.state == "failed"
    assert record.factual_failure_reason == "offline completion unavailable"
    assert summary.planned_denominator == 12
    assert summary.denominator_reduced is False
    assert summary.gate1_decision is None


def test_rejects_legacy_arm_and_bad_digest():
    with pytest.raises(CaptureRecordError):
        cell("D_UNION")
    with pytest.raises(CaptureRecordError):
        cell(prompt_digest="0" * 64)


def test_declares_exact_four_arm_vocabulary_without_inventing_cells():
    assert ARMS == ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")


@pytest.mark.anyio
async def test_multiple_cells_are_captured_exactly_once_in_order():
    calls = []

    async def complete(prompt, system_prompt=None):
        calls.append(prompt)
        return LLMResponse(content=prompt, model="model-alpha", provider="provider-alpha")

    cells = tuple(cell(cell_id=f"cell-{index}") for index in range(3))
    records = await capture_bound_cells(cells, complete)
    assert calls == ["frozen prompt"] * 3
    assert [record.cell.cell_id for record in records] == ["cell-0", "cell-1", "cell-2"]


@pytest.mark.anyio
async def test_middle_failure_does_not_stop_later_cells():
    calls = []

    async def complete(prompt, system_prompt=None):
        calls.append(prompt)
        if len(calls) == 2:
            raise CompletionOperationalError("middle completion unavailable")
        return LLMResponse(content=prompt, model="model-alpha", provider="provider-alpha")

    cells = tuple(cell(cell_id=f"cell-{index}") for index in range(3))
    records = await capture_bound_cells(cells, complete)

    assert calls == ["frozen prompt"] * 3
    assert [record.cell.cell_id for record in records] == ["cell-0", "cell-1", "cell-2"]
    assert [record.state for record in records] == ["complete", "failed", "complete"]
    assert records[1].factual_failure_reason == "middle completion unavailable"


@pytest.mark.anyio
async def test_programmer_errors_propagate_unchanged():
    error = CaptureRecordError("programmer mistake")

    async def complete(prompt, system_prompt=None):
        raise error

    with pytest.raises(CaptureRecordError) as raised:
        await capture_bound_cells((cell(),), complete)
    assert raised.value is error


@pytest.mark.anyio
async def test_non_awaitable_completion_result_propagates_capture_error():
    def complete(prompt, system_prompt=None):
        return LLMResponse(content="not awaited", model="model-alpha", provider="provider-alpha")

    with pytest.raises(CaptureRecordError, match="awaitable"):
        await capture_bound_cells((cell(),), complete)


def test_summary_never_uses_observed_count_as_denominator():
    assert summarize_run(()).status == "missing"
    assert summarize_run(()).planned_denominator == 12
    with pytest.raises(CaptureRecordError):
        summarize_run((), planned_cell_count=1)


def test_all_run_statuses_are_supported_without_inventing_gate_decisions():
    for status in ("complete", "incomplete", "inconclusive", "failed", "aborted", "missing"):
        reason = (
            "factually recorded"
            if status in ("inconclusive", "failed", "aborted")
            else "not_applicable"
        )
        summary = summarize_run((), run_status=status, factual_reason=reason)
        assert summary.status == status
        assert summary.gate1_decision is None
    for status in ("inconclusive", "failed", "aborted"):
        with pytest.raises(CaptureRecordError):
            summarize_run((), run_status=status)


@pytest.mark.parametrize(
    "field",
    [
        "provider_pin",
        "model_pin",
        "endpoint_pin",
        "model_config_digest",
        "budget",
        "timeout",
        "operator",
        "reviewer",
        "identity_attestation",
    ],
)
def test_rejects_empty_or_unknown_required_frozen_fields(field):
    with pytest.raises(CaptureRecordError):
        cell(**{field: ""})
    with pytest.raises(CaptureRecordError):
        cell(**{field: "unknown"})


@pytest.mark.anyio
async def test_private_raw_response_is_deeply_snapshotted_and_frozen():
    raw = {"nested": {"items": ["original"]}}

    async def complete(prompt, system_prompt=None):
        return LLMResponse(
            content="answer", model="model-alpha", provider="provider-alpha", raw_response=raw
        )

    record = (await capture_bound_cells((cell(),), complete))[0]
    assert record.raw_wire_payload == (
        '{"completion_tokens_detail":null,"content":"answer","duration_ms":0,'
        '"model":"model-alpha","prompt_tokens":null,"provider":"provider-alpha",'
        '"raw_response":{"nested":{"items":["original"]}},"stage_type":"single_pass",'
        '"tokens":0,"total_tokens":null,"usage_provenance":null}'
    )
    raw["nested"]["items"].append("caller mutation")
    assert record.response.raw_response["nested"]["items"] == ("original",)
    assert "caller mutation" not in record.raw_wire_payload
    with pytest.raises(TypeError):
        record.response.raw_response["nested"]["new"] = "blocked"
    with pytest.raises(TypeError):
        record.response.raw_response["nested"]["items"] += ("blocked",)


@pytest.mark.anyio
async def test_all_retained_container_fields_are_detached_and_frozen():
    raw = {"nested": {"items": ["original"]}}
    provenance = {"source": "usage", "attempts": 1}

    async def complete(prompt, system_prompt=None):
        return LLMResponse(
            content="answer",
            model="model-alpha",
            provider="provider-alpha",
            raw_response=raw,
            usage_provenance=provenance,
        )

    record = (await capture_bound_cells((cell(),), complete))[0]
    raw["nested"]["items"].append("caller mutation")
    provenance["source"] = "caller mutation"
    assert record.response.raw_response["nested"]["items"] == ("original",)
    assert record.response.usage_provenance["source"] == "usage"
    with pytest.raises(TypeError):
        record.response.usage_provenance["new"] = "blocked"


@pytest.mark.anyio
async def test_serialization_and_schema_errors_propagate_instead_of_becoming_failed_records():
    async def unserializable(prompt, system_prompt=None):
        return LLMResponse(
            content="answer",
            model="model-alpha",
            provider="provider-alpha",
            raw_response={"bad": object()},
        )

    with pytest.raises(TypeError):
        await capture_bound_cells((cell(),), unserializable)

    async def invalid_response(prompt, system_prompt=None):
        return {"not": "an LLMResponse"}

    with pytest.raises(CaptureRecordError, match="LLMResponse"):
        await capture_bound_cells((cell(),), invalid_response)


@pytest.mark.anyio
async def test_secret_raw_response_is_rejected_without_retention():
    async def complete(prompt, system_prompt=None):
        return LLMResponse(
            content="answer",
            model="model-alpha",
            provider="provider-alpha",
            raw_response={"api_key": "sk-secret-value-123456"},
        )

    record = (await capture_bound_cells((cell(),), complete))[0]
    assert record.state == "failed"
    assert record.response is None
    assert record.raw_wire_payload == ""
    assert "sk-secret" not in record.factual_failure_reason


@pytest.mark.anyio
@pytest.mark.parametrize(
    "secret_key",
    [
        "token",
        "api_key",
        "authorization",
        "credential",
        "access_token",
        "refresh_token",
        "client_secret",
        "private_key",
    ],
)
async def test_secret_key_forms_are_rejected_without_retention(secret_key):
    async def complete(prompt, system_prompt=None):
        return LLMResponse(
            content="answer",
            model="model-alpha",
            provider="provider-alpha",
            raw_response={secret_key: "ordinary value"},
        )

    record = (await capture_bound_cells((cell(),), complete))[0]
    assert record.state == "failed"
    assert record.response is None
    assert record.raw_wire_payload == ""


@pytest.mark.anyio
@pytest.mark.parametrize(
    "field,value",
    [
        ("content", "Bearer content-secret"),
        ("model", "sk-model-secret"),
        ("provider", "ghp_providersecret"),
        ("raw_response", {"nested": [{"credential": "not echoed"}]}),
        ("usage_provenance", {"access_token": "not echoed"}),
    ],
)
async def test_secrets_are_rejected_across_the_complete_response_surface(field, value):
    async def complete(prompt, system_prompt=None):
        values = {"content": "answer", "model": "model-alpha", "provider": "provider-alpha"}
        values[field] = value
        return LLMResponse(**values)

    record = (await capture_bound_cells((cell(),), complete))[0]
    assert record.response is None
    assert record.raw_wire_payload == ""
    assert "not echoed" not in record.factual_failure_reason


@pytest.mark.anyio
async def test_public_reference_exposes_only_comparable_denominator_eligibility():
    async def complete(prompt, system_prompt=None):
        return LLMResponse(
            content="private prompt response", model="model-alpha", provider="provider-alpha"
        )

    public = (await capture_bound_cells((cell(),), complete))[0].public_reference()
    rendered = repr(public)
    assert public.denominator_eligible is True
    assert public.planned_denominator == 12
    assert all(
        term not in rendered
        for term in ("private prompt", "raw_response", "digest", "wire", "secret")
    )
