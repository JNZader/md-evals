"""Offline tests for strict Gate 1 generation and injected execution."""

import asyncio
import json

import pytest

from md_evals.context_renderer import compose_paired_context
from md_evals.captured_pilot_plan import prepare_captured_pilot
from md_evals.strict_gate1_runner import (
    StrictGate1Error,
    StrictGate1CellResult,
    build_strict_gate1_artifacts,
    load_strict_gate1_input,
    main,
    prepare_strict_gate1_artifact_files,
    preflight_strict_gate1,
    run_strict_gate1,
    write_strict_gate1_artifacts,
)
from tests.test_strict_run_assembly import assemble, declarations
from tests.test_strict_run_packet import checklist


REVISION = "sha256:" + "b" * 64


def _record(kind: str, identifier: str):
    return {"id": identifier, "kind": kind, "repository": "repo", "revision": REVISION,
            "producer_instance": "producer", "source_id": "source", "path": "x.py",
            "quote": "quote", "claim": "claim", "value": "value", "freshness": "fresh",
            "git_state": "clean", "line": 1}


def _pack(record):
    return {"schema_version": "ContextPack.capture.union.v1", "repository": "repo",
            "revision": REVISION, "freshness": "fresh", "git_state": "clean", "producer": {},
            "providers": [], "evidence": [record], "conflicts": [],
            "budget": {"limit": 1, "measurement": "estimate",
                       "algorithm": "utf8_quote_bytes_div4_ceil_v0", "scope": "evidence_quotes"},
            "trace": {}}


def _valid_cases():
    cases = []
    for number, name in enumerate(("one", "two", "three")):
        structure = _pack(_record("structure", f"{number + 1:x}".zfill(64)))
        memory = _pack(_record("memory", f"{number + 10:x}".zfill(64)))
        cases.append({"name": name, "prompt": f"Prompt {name}",
                      "expected": {"answer": "VALUE", "citations": [], "abstain": False},
                      "packs": {"CONTROL": None, "B_STRUCTURE": structure,
                                "C_MEMORY": memory,
                                "E_PAIRED": compose_paired_context(structure, memory)}})
    return cases


def _artifacts():
    from tests.test_strict_run_assembly import assemble

    candidate_plan = prepare_captured_pilot(
        cases=_valid_cases(), provider="provider", model="model", backend_config_sha256="c" * 64,
        limits={"max_primary_calls": 12, "per_call_timeout_seconds": 2, "total_timeout_seconds": 20},
    )
    assembly = assemble()
    billing_scaffold = __import__("md_evals.strict_billing_evidence", fromlist=["build_billing_scaffold"]).build_billing_scaffold(
        plan=candidate_plan, created_at="2026-09-13T00:00:00Z"
    )
    return build_strict_gate1_artifacts(
        cases=_valid_cases(), provider="provider", model="model", backend_config_sha256="c" * 64,
        limits={"max_primary_calls": 12, "per_call_timeout_seconds": 2, "total_timeout_seconds": 20},
         checklist=checklist(assembly), billing_scaffold=billing_scaffold,
         generated_at="2026-09-13T00:00:00Z", **{key: value for key, value in declarations().items() if key != "billing_attestation"})


def _input_bundle():
    assembly = assemble()
    values = {
        "cases": _valid_cases(), "provider": "provider", "model": "model",
        "backend_config_sha256": "c" * 64,
        "limits": {"max_primary_calls": 12, "per_call_timeout_seconds": 2,
                   "total_timeout_seconds": 20},
        "checklist": checklist(assembly), "generated_at": "2026-09-13T00:00:00Z",
         **declarations(),
    }
    candidate_plan = prepare_captured_pilot(
        cases=_valid_cases(), provider="provider", model="model", backend_config_sha256="c" * 64,
        limits={"max_primary_calls": 12, "per_call_timeout_seconds": 2, "total_timeout_seconds": 20},
    )
    values["billing_scaffold"] = __import__("md_evals.strict_billing_evidence", fromlist=["build_billing_scaffold"]).build_billing_scaffold(
        plan=candidate_plan, created_at="2026-09-13T00:00:00Z"
    )
    values.pop("billing_attestation")
    return values


def test_preflight_is_secret_safe_and_fail_closed():
    report = preflight_strict_gate1(bearer_present=False, retry_attempts=0, fallbacks=False,
                                    tools="none", tools_enforced=True, planned_cells=12)
    assert report["status"] == "blocked"
    assert report["network_called"] is False
    assert report["execution_authorized"] is False
    assert "bearer" in report["blockers"][0]
    assert "secret" not in json.dumps(report).lower()


@pytest.mark.parametrize("kwargs", [
    {"retry_attempts": 1}, {"fallbacks": True}, {"planned_cells": 8}, {"smoke_runner": True},
])
def test_strict_preflight_rejects_non_strict_policy(kwargs):
    values = {"bearer_present": True, "retry_attempts": 0, "fallbacks": False,
              "tools": "none", "tools_enforced": True, "planned_cells": 12}
    values.update(kwargs)
    assert preflight_strict_gate1(**values)["status"] == "blocked"


def test_artifact_generator_builds_bound_non_authorizing_artifacts():
    artifacts = _artifacts()
    assert artifacts.plan.to_dict()["planned_calls"] == 12
    assert all(item.to_dict()["execution_authorized"] is False
               for item in (artifacts.assembly, artifacts.packet, artifacts.authorization_request))
    assert artifacts.to_dict()["live_execution_requested"] is False


def test_loader_accepts_valid_frozen_input_bundle(tmp_path):
    path = tmp_path / "strict-input.json"
    path.write_text(json.dumps(_input_bundle()), encoding="utf-8")

    loaded = load_strict_gate1_input(path)

    assert set(loaded) == {
        "cases", "provider", "model", "backend_config_sha256", "limits",
        "gold_reference", "reviewer_metadata", "billing_scaffold",
        "repository_state", "cleanup_declaration", "checklist", "generated_at",
    }


@pytest.mark.parametrize("mutation", [
    lambda payload: payload.pop("cases"),
    lambda payload: payload.update({"unexpected": "must not be accepted"}),
])
def test_loader_rejects_invalid_top_level_keys_without_printing_payload(tmp_path, capsys, mutation):
    payload = _input_bundle()
    mutation(payload)
    path = tmp_path / "strict-input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(StrictGate1Error):
        load_strict_gate1_input(path)

    assert capsys.readouterr().out == ""


def test_writer_keeps_private_manifests_out_of_public_index(tmp_path):
    index = write_strict_gate1_artifacts(_artifacts(), tmp_path)

    assert {path.name for path in tmp_path.iterdir()} == {
        "plan.private.json", "assembly.private.json", "packet.json",
        "authorization-request.json", "index.json",
    }
    public = json.dumps(index).lower()
    assert all(term not in public for term in ("prompt", "rendered_context", "context", "raw_response"))
    assert index["files"]["plan"] == "plan.private.json"
    assert index["status"] == "prepared"
    assert json.loads((tmp_path / "plan.private.json").read_text())
    assert json.loads((tmp_path / "assembly.private.json").read_text())


def test_writer_rejects_symlink_output_directory(tmp_path):
    real_dir = tmp_path / "real-artifacts"
    real_dir.mkdir()
    output_dir = tmp_path / "artifacts-link"
    output_dir.symlink_to(real_dir, target_is_directory=True)

    with pytest.raises(StrictGate1Error, match="output directory"):
        write_strict_gate1_artifacts(_artifacts(), output_dir)

    assert list(real_dir.iterdir()) == []


def test_writer_rejects_symlink_parent_component(tmp_path):
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    (tmp_path / "parent-link").symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(StrictGate1Error, match="output directory"):
        write_strict_gate1_artifacts(_artifacts(), tmp_path / "parent-link" / "artifacts")

    assert list(real_parent.iterdir()) == []


def test_writer_rejects_symlink_canonical_target_before_writing(tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text("sentinel", encoding="utf-8")
    (tmp_path / "plan.private.json").symlink_to(outside)

    with pytest.raises(StrictGate1Error, match="target already exists"):
        write_strict_gate1_artifacts(_artifacts(), tmp_path)

    assert [path.name for path in tmp_path.iterdir()] == ["outside.json", "plan.private.json"]
    assert outside.read_text(encoding="utf-8") == "sentinel"


def test_writer_rejects_existing_canonical_target_before_writing_anything(tmp_path):
    existing = tmp_path / "packet.json"
    existing.write_text("sentinel", encoding="utf-8")

    with pytest.raises(StrictGate1Error, match="target already exists"):
        write_strict_gate1_artifacts(_artifacts(), tmp_path)

    assert [path.name for path in tmp_path.iterdir()] == ["packet.json"]
    assert existing.read_text(encoding="utf-8") == "sentinel"


def test_convenience_function_builds_and_writes_bundle(tmp_path):
    input_path = tmp_path / "strict-input.json"
    output_dir = tmp_path / "strict-artifacts"
    input_path.write_text(json.dumps(_input_bundle()), encoding="utf-8")

    index = prepare_strict_gate1_artifact_files(input_path, output_dir)

    assert index["planned_calls"] == 12
    assert (output_dir / "index.json").exists()


def test_module_command_is_offline_and_prints_public_index_only(tmp_path, capsys):
    input_path = tmp_path / "strict-input.json"
    output_dir = tmp_path / "strict-artifacts"
    input_path.write_text(json.dumps(_input_bundle()), encoding="utf-8")

    assert main(["--input", str(input_path), "--output-dir", str(output_dir)]) == 0

    stdout = capsys.readouterr().out.lower()
    assert "plan.private.json" in stdout
    assert all(term not in stdout for term in ("prompt", "rendered_context", "raw_response"))


def test_artifact_projection_is_public_safe():
    projection = _artifacts().to_dict()
    serialized = json.dumps(projection).lower()
    assert all(term not in serialized for term in ("prompt", "rendered_context", "context", "raw_response"))
    assert set(projection) == {
        "plan_sha256", "assembly_sha256", "packet_sha256", "authorization_request_sha256",
        "planned_calls", "execution_authorized", "live_execution_requested",
    }


def test_runner_requires_authorization_and_validated_artifacts_before_call():
    calls = []
    with pytest.raises(StrictGate1Error, match="validated strict artifacts"):
        asyncio.run(run_strict_gate1(artifacts=object(), bearer_present=True, retry_attempts=0,
                                     fallbacks=False, tools="none", tools_enforced=True,
                                     authorize=False, adapter=lambda cell: calls.append(cell)))
    assert calls == []


def test_runner_uses_injected_adapter_for_exactly_twelve_cells_without_retry_or_fallback():
    artifacts = _artifacts()
    calls = []

    async def fake_adapter(cell):
        calls.append(cell)
        return StrictGate1CellResult(
            case_name=cell.case_name, arm=cell.arm, status="completed",
            answer={"answer": "VALUE", "citations": [], "abstain": False},
            raw_response_digest="d" * 64,
        )

    results = asyncio.run(run_strict_gate1(
        artifacts=artifacts, bearer_present=True, retry_attempts=0, fallbacks=False,
        tools="none", tools_enforced=True, authorize=True, adapter=fake_adapter))
    assert len(calls) == len(results) == 12
    assert {cell.arm for cell in calls} == {"CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED"}


def test_runner_rejects_malformed_adapter_output():
    artifacts = _artifacts()
    calls = []

    def bad_adapter(cell):
        calls.append(cell)
        return {"case": cell.case_name, "arm": cell.arm}

    with pytest.raises(StrictGate1Error, match="strict cell result"):
        asyncio.run(run_strict_gate1(
            artifacts=artifacts, bearer_present=True, retry_attempts=0, fallbacks=False,
            tools="none", tools_enforced=True, authorize=True, adapter=bad_adapter))
    assert len(calls) == 1


def test_runner_rejects_stale_authorization_request_before_adapter_call():
    artifacts = _artifacts()
    object.__setattr__(artifacts.authorization_request, "sha256", "0" * 64)
    calls = []
    with pytest.raises(StrictGate1Error, match="self-hash"):
        asyncio.run(run_strict_gate1(
            artifacts=artifacts, bearer_present=True, retry_attempts=0, fallbacks=False,
            tools="none", tools_enforced=True, authorize=True,
            adapter=lambda cell: calls.append(cell)))
    assert calls == []


@pytest.mark.parametrize("field,value", [("prompt", "private prompt"), ("rendered_context", "private context"), ("private_key", "-----BEGIN PRIVATE KEY-----")])
def test_cell_result_rejects_private_material(field, value):
    payload = {
        "schema_version": "strict-gate1-cell-result/v1", "case_name": "one", "arm": "CONTROL",
        "status": "completed", "answer": {"answer": "VALUE", "citations": [], "abstain": False},
        "raw_response_digest": "d" * 64, "error_code": None, "error_message": None,
    }
    payload[field] = value
    with pytest.raises(StrictGate1Error):
        StrictGate1CellResult.from_value(payload)


def _completed_cell_result_payload(answer):
    return {
        "schema_version": "strict-gate1-cell-result/v1", "case_name": "one", "arm": "CONTROL",
        "status": "completed", "answer": answer, "raw_response_digest": "d" * 64,
        "error_code": None, "error_message": None,
    }


@pytest.mark.parametrize("credential", [
    "ghp_" + "a" * 36,
    "AKIA" + "A" * 16,
    "ASIA" + "B" * 16,
])
def test_completed_cell_result_rejects_common_credential_formats(credential):
    payload = _completed_cell_result_payload(
        {"answer": f"Explanation: {credential}", "citations": [], "abstain": False}
    )

    with pytest.raises(StrictGate1Error, match="invalid strict cell result"):
        StrictGate1CellResult.from_value(payload)


def test_completed_cell_result_allows_benign_bearer_explanation():
    result = StrictGate1CellResult.from_value(_completed_cell_result_payload(
        {"answer": "Bearer token is sent in the Authorization header.", "citations": [], "abstain": False}
    ))

    assert result.to_dict()["answer"]["answer"] == "Bearer token is sent in the Authorization header."


def test_cell_result_snapshots_original_answer_payload():
    answer = {"answer": "VALUE", "citations": [], "abstain": False}
    result = StrictGate1CellResult(**_completed_cell_result_payload(answer))

    answer.update({"prompt": "private prompt", "secret": "token", "private_key": "-----BEGIN PRIVATE KEY-----"})

    assert result.to_dict()["answer"] == {"answer": "VALUE", "citations": [], "abstain": False}


def test_cell_result_to_dict_returns_an_independent_answer_copy():
    result = StrictGate1CellResult(**_completed_cell_result_payload(
        {"answer": "VALUE", "citations": [], "abstain": False}
    ))
    projection = result.to_dict()
    projection["answer"].update({"raw_response": "private", "token": "secret"})

    assert result.to_dict()["answer"] == {"answer": "VALUE", "citations": [], "abstain": False}


def test_cell_result_from_value_snapshots_payload_dict():
    answer = {"answer": "VALUE", "citations": [], "abstain": False}
    payload = _completed_cell_result_payload(answer)
    result = StrictGate1CellResult.from_value(payload)

    answer["prompt"] = "private prompt"
    payload["answer"]["rendered_context"] = "private context"

    assert result.to_dict()["answer"] == {"answer": "VALUE", "citations": [], "abstain": False}


@pytest.mark.parametrize("key,value", [
    ("prompt", "private prompt"), ("rendered_context", "private context"),
    ("raw_response", "private response"), ("secret", "secret value"),
    ("token", "token value"), ("private_key", "-----BEGIN PRIVATE KEY-----"),
])
def test_post_validation_answer_mutation_cannot_leak_private_fields(key, value):
    answer = {"answer": "VALUE", "citations": [], "abstain": False}
    result = StrictGate1CellResult(**_completed_cell_result_payload(answer))
    answer[key] = value

    projection = result.to_dict()
    assert key not in projection["answer"]
    assert not any(term in json.dumps(projection["answer"]).lower()
                   for term in ("prompt", "rendered_context", "raw_response", "secret", "token", "private_key"))


def test_malformed_explicit_evidence_blocks_before_adapter():
    cases = _valid_cases()
    cases[0]["expected"] = {"answer": "", "citations": [], "abstain": False}
    with pytest.raises(Exception):
        build_strict_gate1_artifacts(
            cases=cases, provider="provider", model="model", backend_config_sha256="c" * 64,
            limits={"max_primary_calls": 12, "per_call_timeout_seconds": 2, "total_timeout_seconds": 20},
            checklist={}, generated_at="2026-09-13T00:00:00Z", **declarations())
