"""Offline tests for the Gate 1 smoke-dev runner."""

import asyncio
import contextlib
import json
import logging

import pytest

from md_evals.gate1_smoke_runner import (
    MODEL,
    PROVIDER,
    build_smoke_cells,
    main,
    preflight_manifest,
    require_live_preflight,
    run_smoke_dev,
    _safe_error,
    _write_outputs,
)
from md_evals.models import LLMResponse


def response(**kwargs):
    return LLMResponse(
        content="offline answer",
        model=MODEL,
        provider=PROVIDER,
        raw_response={
            "resolvedProvider": PROVIDER,
            "resolvedModel": MODEL,
            "fallbackUsed": False,
            "toolEvidence": zero_tool_evidence(),
            **kwargs,
        },
    )


def zero_cost_evidence():
    return {
        "status": "estimated_zero",
        "source": "catalog_estimate",
        "estimatedCost": 0,
        "currency": "USD",
        "inputTokens": 4,
        "outputTokens": 6,
        "providerChargeAttestation": False,
        "caveat": "Estimated from gateway model-price metadata; not provider charge attestation.",
    }


def zero_tool_evidence():
    return {
        "status": "complete",
        "mode": "none",
        "source": "opencode-json-events",
        "toolCallCount": 0,
        "enforcement": "temporary-opencode-agent-config",
        "observable": True,
    }


def test_builds_exact_12_cells_and_excludes_legacy_arm():
    cells = build_smoke_cells("TEST")
    assert len(cells) == 12
    assert [cell.cell_id for cell in cells] == [
        f"{task}-{arm.replace('_', '-')}"
        for task in ("T1", "T2", "T3")
        for arm in ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
    ]
    assert all(cell.arm_id != "D_UNION" for cell in cells)


def test_missing_bearer_preflight_is_blocked_without_printing_a_token(capsys, monkeypatch):
    secret = "offline-secret-token"
    monkeypatch.delenv("GATE1_GATEWAY_BEARER", raising=False)
    assert main(["--preflight", "--run-id", "TEST-PLAN"]) == 1
    output = capsys.readouterr().out
    assert json.loads(output)["status"] == "blocked"
    assert json.loads(output)["blocker_reason"] == "GATE1_GATEWAY_BEARER is missing or empty"
    assert secret not in output


def test_present_bearer_preflight_is_ready_without_printing_the_secret(capsys, monkeypatch):
    secret = "offline-secret-token"
    monkeypatch.setenv("GATE1_GATEWAY_BEARER", secret)
    assert main(["--preflight", "--run-id", "TEST-PLAN"]) == 0
    output = capsys.readouterr().out
    readiness = json.loads(output)
    assert readiness["status"] == "ready"
    assert readiness["bearer_present"] is True
    assert secret not in output


def test_preflight_reports_frozen_cells_and_no_network():
    readiness = preflight_manifest("TEST-PLAN", {})
    assert readiness["planned_cells"] == 12
    assert len(readiness["cell_ids"]) == 12
    assert readiness["network_called"] is False
    assert readiness["live_execution_authorized_by_this_preflight"] is False


def test_plan_remains_offline_and_does_not_authorize_live_execution(capsys):
    assert main(["--plan", "--run-id", "TEST-PLAN"]) == 0
    manifest = json.loads(capsys.readouterr().out)
    assert (
        manifest["authorization"]
        == "fresh exact smoke-dev authorization required at live invocation"
    )
    assert "live_execution_authorized_by_this_preflight" not in manifest


def test_missing_bearer_fails_before_completion():
    calls = 0

    async def completion(cell):
        nonlocal calls
        calls += 1
        raise AssertionError("must not be called")

    with pytest.raises(RuntimeError, match="missing or empty"):
        asyncio.run(
            run_smoke_dev(
                completion=completion, run_id="TEST", live=True, authorize=True, environ={}
            )
        )
    assert calls == 0


def test_bearer_is_not_logged(caplog):
    secret = "offline-secret-token"
    caplog.set_level(logging.INFO)
    assert (
        require_live_preflight(authorize=True, environ={"GATE1_GATEWAY_BEARER": secret}) == secret
    )
    assert secret not in caplog.text


def test_retry_is_at_most_one():
    calls = 0

    async def completion(cell):
        nonlocal calls
        calls += 1
        raise RuntimeError("offline failure")

    result = asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))
    assert calls == 24
    assert result.manifest["status"] == "incomplete"


def test_pin_mismatch_aborts():
    async def completion(cell):
        return LLMResponse(content="x", model="wrong", provider=PROVIDER)

    with pytest.raises(RuntimeError, match="identity metadata"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_missing_resolved_model_aborts_instead_of_falling_back():
    async def completion(cell):
        return LLMResponse(
            content="x",
            model=MODEL,
            provider=PROVIDER,
            raw_response={"resolvedProvider": PROVIDER, "fallbackUsed": False},
        )

    with pytest.raises(RuntimeError, match="identity metadata"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_bearer_and_token_fields_are_redacted_from_artifacts_and_errors(tmp_path):
    secret = "offline-secret-token"
    _write_outputs(
        tmp_path / "run",
        {"status": "complete", "token": secret},
        [
            {
                "cell_id": "T1-CONTROL",
                "state": "complete",
                "retry_count": 0,
                "fallback_used": False,
                "provider_observed": PROVIDER,
                "model_observed": MODEL,
                "billing": "explicit-zero",
                "raw": {
                    "path": "raw-responses/row.json",
                    "response": {"Authorization": f"Bearer {secret}", "token": secret},
                },
            }
        ],
        (secret,),
    )
    artifacts = "".join(
        path.read_text() for path in (tmp_path / "run").rglob("*") if path.is_file()
    )
    assert secret not in artifacts
    safe_error = _safe_error(RuntimeError(f"Authorization: Bearer {secret}"), (secret,))
    assert secret not in safe_error
    assert "Bearer" not in safe_error


def test_exception_text_is_redacted_from_error_artifact(tmp_path):
    secret = "offline-secret-token"

    async def completion(cell):
        raise RuntimeError(f"Authorization: Bearer {secret}")

    asyncio.run(
        run_smoke_dev(
            completion=completion,
            run_id="TEST",
            output_dir=tmp_path / "run",
            live=True,
            authorize=True,
            environ={"GATE1_GATEWAY_BEARER": secret},
        )
    )
    artifacts = "".join(
        path.read_text() for path in (tmp_path / "run").rglob("*") if path.is_file()
    )
    assert secret not in artifacts


def test_nonzero_billing_aborts():
    async def completion(cell):
        return response(cost=0.01)

    with pytest.raises(RuntimeError, match="billing"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_gateway_catalog_zero_cost_evidence_is_accepted():
    async def completion(cell):
        return response(costEvidence=zero_cost_evidence())

    result = asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))
    assert result.manifest["status"] == "complete"


def test_malformed_gateway_zero_cost_evidence_still_aborts():
    async def completion(cell):
        return response(costEvidence={"status": "estimated_zero", "estimatedCost": 0})

    with pytest.raises(RuntimeError, match="zero-charge billing evidence"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


@pytest.mark.parametrize(
    "tool_evidence",
    [
        None,
        {"status": "complete", "mode": "none"},
        {**zero_tool_evidence(), "toolCallCount": 1},
        {**zero_tool_evidence(), "toolCallCount": True},
        {**zero_tool_evidence(), "source": "provider-claimed"},
        {**zero_tool_evidence(), "enforcement": "provider-claimed"},
        {**zero_tool_evidence(), "extra": "unexpected"},
    ],
)
def test_missing_malformed_or_nonzero_tool_evidence_aborts(tool_evidence):
    async def completion(cell):
        metadata = {"costEvidence": zero_cost_evidence()}
        if tool_evidence is not None:
            metadata["toolEvidence"] = tool_evidence
        result = response(**metadata)
        if tool_evidence is None:
            result.raw_response.pop("toolEvidence", None)
        return result

    with pytest.raises(RuntimeError, match="toolEvidence"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_boolean_token_counts_do_not_satisfy_zero_cost_evidence():
    async def completion(cell):
        evidence = zero_cost_evidence()
        evidence["inputTokens"] = True
        return response(costEvidence=evidence)

    with pytest.raises(RuntimeError, match="zero-charge billing evidence"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_extra_cost_evidence_fields_abort():
    async def completion(cell):
        evidence = zero_cost_evidence()
        evidence["debug"] = "extra"
        return response(costEvidence=evidence)

    with pytest.raises(RuntimeError, match="zero-charge billing evidence"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_unrelated_zero_billing_metadata_is_rejected_even_with_valid_evidence():
    async def completion(cell):
        return response(costEvidence=zero_cost_evidence(), cost=0)

    with pytest.raises(RuntimeError, match="unapproved billing fields"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST"))


def test_missing_billing_metadata_aborts_without_complete_cell(tmp_path):
    async def completion(cell):
        return response()

    output_dir = tmp_path / "run"
    with pytest.raises(RuntimeError, match="zero-charge billing evidence"):
        asyncio.run(run_smoke_dev(completion=completion, run_id="TEST", output_dir=output_dir))

    score_sheet = (output_dir / "score-sheet.md").read_text()
    assert "| T1-CONTROL | aborted |" in score_sheet
    assert "| T1-CONTROL | complete |" not in score_sheet


def test_output_checkpoint_exists_before_first_completion_finishes(tmp_path):
    output_dir = tmp_path / "run"
    started = asyncio.Event()
    release = asyncio.Event()

    async def completion(cell):
        started.set()
        await release.wait()
        return response(costEvidence=zero_cost_evidence())

    async def exercise():
        task = asyncio.create_task(
            run_smoke_dev(completion=completion, run_id="TEST", output_dir=output_dir)
        )
        await started.wait()
        manifest_text = (output_dir / "manifest.md").read_text()
        manifest = json.loads(manifest_text.split("```json\n")[1].split("\n```")[0])
        assert output_dir.is_dir()
        assert (output_dir / "raw-responses").is_dir()
        assert manifest["status"] == "in_progress"
        assert manifest["complete_cells"] == 0
        assert manifest["planned_cells"] == 12
        assert "| Cell ID | State |" in (output_dir / "score-sheet.md").read_text()
        assert 'complete_cells": 0' in (output_dir / "public-summary.md").read_text()
        assert "Run status: in_progress." in (output_dir / "deletion-receipt.md").read_text()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(exercise())


def test_partial_rows_are_checkpointed_after_complete_and_failed_cells(tmp_path):
    output_dir = tmp_path / "run"
    observed_first_checkpoint = False

    async def completion(cell):
        nonlocal observed_first_checkpoint
        if cell.cell_id == "T1-CONTROL":
            return response(costEvidence=zero_cost_evidence())
        if cell.cell_id == "T1-B-STRUCTURE":
            score_sheet = (output_dir / "score-sheet.md").read_text()
            observed_first_checkpoint = "| T1-CONTROL | complete |" in score_sheet
            raise RuntimeError("offline cell failure")
        return response(costEvidence=zero_cost_evidence())

    result = asyncio.run(run_smoke_dev(completion=completion, run_id="TEST", output_dir=output_dir))

    score_sheet = (output_dir / "score-sheet.md").read_text()
    assert observed_first_checkpoint is True
    assert "| T1-CONTROL | complete |" in score_sheet
    assert "| T1-B-STRUCTURE | failed | 1 |" in score_sheet
    assert result.manifest["status"] == "incomplete"


def test_fallback_metadata_is_recorded_as_smoke_only_when_pins_match(tmp_path):
    async def completion(cell):
        return response(costEvidence=zero_cost_evidence(), fallbackUsed=True)

    result = asyncio.run(
        run_smoke_dev(completion=completion, run_id="TEST", output_dir=tmp_path / "run")
    )

    assert result.manifest["status"] == "complete"
    score_sheet = (tmp_path / "run" / "score-sheet.md").read_text()
    assert "| T1-CONTROL | complete | 0 | True |" in score_sheet
    assert "smoke-only/non-canonical" in score_sheet


def test_output_manifest_is_smoke_only_and_tools_limitation_is_recorded(tmp_path):
    async def completion(cell):
        return response(costEvidence=zero_cost_evidence())

    result = asyncio.run(
        run_smoke_dev(completion=completion, run_id="TEST", output_dir=tmp_path / "run")
    )
    assert result.manifest["canonical_status"] == "smoke-only/non-canonical"
    assert "enforced and observed" in result.manifest["tools_limitation"]
    manifest = json.loads(
        (tmp_path / "run" / "manifest.md").read_text().split("```json\n")[1].split("\n```")[0]
    )
    assert manifest["tools"] == "none"
