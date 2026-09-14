import asyncio

import pytest

from md_evals.offline_worker import (
    INPUT_SCHEMA,
    OUTPUT_SCHEMA,
    OfflineWorkerInput,
    OfflineWorkerResult,
    run_offline_worker,
)


def request():
    return OfflineWorkerInput("private prompt", "private context")


def answer(value="VALUE"):
    return {"answer": value, "citations": [], "abstain": False}


def test_valid_completed_output_is_accepted_without_private_data_in_public_result():
    result = run_offline_worker(request(), lambda frozen: {"schema_version": OUTPUT_SCHEMA, "answer": answer()})
    assert result.status == "completed"
    assert result.to_dict() == {
        "schema_version": OUTPUT_SCHEMA,
        "status": "completed",
        "answer": answer(),
        "error_code": None,
        "error_message": None,
    }
    rendered = repr(result.to_dict())
    assert "private prompt" not in rendered and "private context" not in rendered


@pytest.mark.parametrize("secret", ["sk_live_123456789", "glpat-123456789", "xoxb-123456789"])
def test_direct_completed_result_rejects_secret_like_answer(secret):
    with pytest.raises(ValueError, match="secret material"):
        OfflineWorkerResult("completed", answer=answer(secret))


def test_completed_result_snapshots_answer_and_keeps_it_immutable():
    original = answer()
    result = OfflineWorkerResult("completed", answer=original)

    original["answer"] = "changed"
    original["citations"].append("a" * 64)
    assert result.to_dict()["answer"] == answer()

    with pytest.raises(TypeError):
        result.answer["answer"] = "changed"
    with pytest.raises(AttributeError):
        result.answer["citations"].append("b" * 64)
    assert result.to_dict()["answer"] == answer()


def test_to_dict_returns_a_fresh_answer_projection():
    result = OfflineWorkerResult("completed", answer=answer())

    public = result.to_dict()
    public["answer"]["answer"] = "changed"
    public["answer"]["citations"].append("a" * 64)

    assert result.to_dict()["answer"] == answer()


def test_input_and_output_extra_fields_are_rejected_fail_closed():
    with pytest.raises(ValueError):
        OfflineWorkerInput.from_dict({"schema_version": INPUT_SCHEMA, "prompt": "p", "context": None, "extra": 1})
    result = run_offline_worker(request(), lambda frozen: {"schema_version": OUTPUT_SCHEMA, "answer": answer(), "extra": 1})
    assert result.status == "malformed_output"
    assert result.error_code == "invalid_output_schema"


@pytest.mark.parametrize("raw", [None, {}, {"schema_version": OUTPUT_SCHEMA, "answer": {}}, {"schema_version": "other", "answer": answer()}])
def test_malformed_worker_output_is_never_success(raw):
    result = run_offline_worker(request(), lambda frozen: raw)
    assert result.status == "malformed_output"
    assert result.answer is None


def test_timeout_and_cancellation_are_explicit_states():
    timeout = run_offline_worker(request(), lambda frozen: (_ for _ in ()).throw(TimeoutError()))
    assert timeout.status == "timeout" and timeout.error_code == "timeout"
    cancelled = run_offline_worker(request(), lambda frozen: (_ for _ in ()).throw(asyncio.CancelledError()))
    assert cancelled.status == "cancelled" and cancelled.error_code == "cancelled"


def test_operational_failure_is_bounded_and_redacted():
    def fail(frozen):
        raise RuntimeError(f"{frozen.prompt} {frozen.context} token=sk-secret-value-123456 and " + "x" * 1000)

    result = run_offline_worker(request(), fail)
    assert result.status == "failed"
    assert result.error_code == "worker_exception"
    assert len(result.error_message) <= 160
    assert "sk-secret" not in repr(result.to_dict())
    assert "private prompt" not in repr(result.to_dict())
    assert "private context" not in repr(result.to_dict())


@pytest.mark.parametrize("field", ["error_code", "error_message"])
@pytest.mark.parametrize("value", ["sk_live_123456789", "glpat-123456789", "xoxb-123456789", "x" * 161])
def test_direct_result_construction_rejects_secret_or_overlong_errors(field, value):
    with pytest.raises(ValueError):
        OfflineWorkerResult("failed", **{field: value, "error_message" if field == "error_code" else "error_code": "failure"})


@pytest.mark.parametrize("field", ["error_code", "error_message"])
def test_direct_result_construction_rejects_non_string_errors(field):
    with pytest.raises(ValueError):
        OfflineWorkerResult("failed", **{field: 1, "error_message" if field == "error_code" else "error_code": "failure"})


@pytest.mark.parametrize(
    "secret", ["Bearer private-secret", "sk_live_123456789", "glpat-123456789", "xoxb-123456789"]
)
def test_secret_like_completed_output_is_rejected_without_leaking_it(secret):
    result = run_offline_worker(
        request(), lambda frozen: {"schema_version": OUTPUT_SCHEMA, "answer": answer(secret)}
    )
    assert result.status == "malformed_output"
    assert result.answer is None
    assert "private-secret" not in repr(result.to_dict())


def test_private_input_material_in_answer_is_rejected_without_public_leak():
    result = run_offline_worker(
        request(), lambda frozen: {"schema_version": OUTPUT_SCHEMA, "answer": answer(frozen.prompt)}
    )
    assert result.status == "malformed_output"
    assert result.error_code == "private_material"
    assert "private prompt" not in repr(result.to_dict())


def test_worker_receives_only_frozen_explicit_inputs():
    observed = []

    def worker(frozen):
        observed.append((frozen.prompt, frozen.context))
        return {"schema_version": OUTPUT_SCHEMA, "answer": answer()}

    result = run_offline_worker({"schema_version": INPUT_SCHEMA, "prompt": "p", "context": "c"}, worker)
    assert result.status == "completed"
    assert observed == [("p", "c")]
