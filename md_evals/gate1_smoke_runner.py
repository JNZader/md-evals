"""Fail-closed, smoke-only runner for the approved Gate 1 twelve-cell plan.

The default CLI action is an offline plan. Live execution requires both ``--live``
and ``--authorize-smoke-dev``; this module never treats smoke output as canonical
Gate 1 evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping

from md_evals.captured_run_record import FrozenCell, capture_cell
from md_evals.models import Defaults, LLMResponse

PROVIDER = "opencode-cli"
MODEL = "opencode/muse-spark-1.3-contributor-free"
GATEWAY_BASE = "http://127.0.0.1:3456"
GATEWAY_ROUTE = "/v1/generate"
BEARER_ENV = "GATE1_GATEWAY_BEARER"
MAX_TOKENS = 4096
TOOLS = "none"
ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
TASKS = ("T1", "T2", "T3")
_SAFE_REASON = re.compile(r"[\r\n]")
_SECRET_KEY = re.compile(
    r"(?:authorization|bearer|password|passwd|secret|token|api[_-]?key|credential|private[_-]?key)", re.I
)
_SECRET_VALUE = re.compile(
    r"Bearer\s+\S+|sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|"
    r"AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|"
    r"(?:authorization|bearer|password|passwd|secret|token|api[_-]?key|credential)\s*[:=]\s*\S+",
    re.I,
)
_REDACTED = "[REDACTED]"
_OUTPUT_MARKER = ".gate1-smoke-runner"

TASK_PROMPTS = {
    "T1": """You are completing a synthetic smoke-dev evaluation. Summarize the project note below in no more than two sentences. Preserve all five facts and the explicit constraint exactly. Do not add claims, explanations, or facts that are not in the note. Return only the summary.

Synthetic project note:
- Project name: Cedar Clock.
- Component: reminder display.
- Change: add a quiet-hours indicator.
- Owner: Mina.
- Review date: 2026-10-14.
- Explicit constraint: the indicator must not send notifications or change reminder timing.""",
    "T2": """You are completing a synthetic smoke-dev evaluation. Extract the five named fields from the changelog paragraph and return valid JSON with exactly these keys: component, change_type, risk, owner, deadline. Use the source values without adding keys or commentary. Do not use Markdown fences.

Synthetic changelog paragraph: \"The Lantern Parser component received a documentation update. The risk is low. The owner is Noor. The deadline is 2026-11-03.\"""",
    "T3": """You are completing a synthetic smoke-dev evaluation. Consider this decision: a canonical model-capture study can use strict no-fallback and zero retries, or it can use flexible fallback and one retry to improve operational completion. Explain the tradeoff in a concise paragraph and recommend the safer option for canonical evidence. Explicitly address evidence contamination and operational resilience. Do not claim that either option has been executed.""",
}

CONTEXTS = {
    "CONTROL": "",
    "B_STRUCTURE": "[Synthetic structure context]\nDocument type: short operational note.\nRequired output property: preserve source facts and explicit constraints.\nOrdering hint: identify facts first, then identify constraints.\nNo external facts are available.\n",
    "C_MEMORY": "[Synthetic memory context]\nRemember only the supplied synthetic source in this request.\nDo not add facts from prior conversations or outside knowledge.\nIf a detail is absent from the source, mark it as absent rather than guessing.\n",
    "E_PAIRED": "[Synthetic paired context]\nStructure: preserve source facts and explicit constraints; organize the answer clearly.\nMemory: use only the supplied synthetic source; do not import outside or prior information.\nIf a detail is absent, do not guess.\n",
}


class SmokeRunnerError(RuntimeError):
    """A fail-closed runner admission or response error."""


class SmokeAbort(SmokeRunnerError):
    """An abort condition that must stop remaining cells."""


Completion = Callable[[FrozenCell], Awaitable[LLMResponse]]


@dataclass(frozen=True)
class SmokeRunResult:
    manifest: dict[str, Any]
    output_dir: Path | None


def build_smoke_cells(run_id: str = "PLAN") -> tuple[FrozenCell, ...]:
    """Construct exactly the frozen three-task by four-arm smoke matrix."""
    cells: list[FrozenCell] = []
    for task_id in TASKS:
        for arm in ARMS:
            context = CONTEXTS[arm].encode("utf-8")
            prompt = TASK_PROMPTS[task_id]
            cell_id = f"{task_id}-{arm.replace('_', '-') }"
            cells.append(
                FrozenCell.bind(
                    cell_id=cell_id,
                    task_id=task_id,
                    prompt=prompt,
                    case_id=f"{task_id}-SYNTHETIC",
                    capture_number=1,
                    arm_id=arm,
                    prompt_digest=sha256(prompt.encode()).hexdigest(),
                    context_bytes=context,
                    context_digest=sha256(context).hexdigest(),
                    selected_ids=(),
                    tools=TOOLS,
                     tool_configuration="tools=none enforced by temporary OpenCode no-tools agent; toolEvidence required",
                    provider_pin=PROVIDER,
                    model_pin=MODEL,
                    endpoint_pin=f"{GATEWAY_BASE}{GATEWAY_ROUTE}",
                    model_config_digest=sha256(f"{PROVIDER}:{MODEL}:{MAX_TOKENS}".encode()).hexdigest(),
                    code_revision="smoke-dev-runner",
                    budget="billing-cap-0",
                    timeout="60s",
                    operator="Javier",
                    reviewer="Javier",
                    arm_mapping_decision_id="GATE-1-SMOKE-DEV-RUN-PACKET",
                    fixture_id="GATE-1-SMOKE-DEV-FROZEN-TASKS",
                    fixture_revision="2026-09-12",
                    context_size=len(context),
                    started_at="not-started",
                    finished_at="not-started",
                    request_id=f"{run_id}:{cell_id}:1",
                    raw_output_ref=f"raw-responses/{cell_id}-attempt-1.json",
                    route_label=GATEWAY_ROUTE,
                    identity_attestation="observed response labels only; not an identity attestation",
                )
            )
    return tuple(cells)


def plan_manifest(run_id: str = "PLAN") -> dict[str, Any]:
    cells = build_smoke_cells(run_id)
    return {
        "scope": "Gate 1 smoke-dev only; 3 frozen synthetic tasks x 4 arms",
        "canonical_status": "smoke-only/non-canonical",
        "run_id": run_id,
        "cells": [cell.cell_id for cell in cells],
        "provider": PROVIDER,
        "model": MODEL,
        "gateway_base": GATEWAY_BASE,
        "route": GATEWAY_ROUTE,
        "requireProvider": True,
        "maxTokens": MAX_TOKENS,
        "tools": "none",
        "tools_limitation": "tools=none is enforced and observed through gateway-local toolEvidence; this is not provider-side attestation.",
        "retry_limit_per_cell": 1,
        "fallback_policy": "Smoke-only metadata; alternate provider/model pins are not authorized.",
        "billing_cap": 0,
        "billing_evidence": "response metadata must explicitly report zero charge; missing evidence aborts",
        "authorization": "fresh exact smoke-dev authorization required at live invocation",
    }


def preflight_manifest(
    run_id: str = "PLAN", environ: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Return secret-safe, non-network readiness information for a smoke run."""
    environment = os.environ if environ is None else environ
    bearer_present = bool(environment.get(BEARER_ENV, "").strip())
    manifest = plan_manifest(run_id)
    result: dict[str, Any] = {
        "status": "ready" if bearer_present else "blocked",
        "env_var": BEARER_ENV,
        "bearer_present": bearer_present,
        "provider": manifest["provider"],
        "model": manifest["model"],
        "gateway": manifest["gateway_base"],
        "route": manifest["route"],
        "maxTokens": manifest["maxTokens"],
        "tools": manifest["tools"],
        "fallback_policy": manifest["fallback_policy"],
        "retry_policy": f"at most {manifest['retry_limit_per_cell']} retry per cell",
        "billing_policy": manifest["billing_evidence"],
        "planned_cells": len(manifest["cells"]),
        "cell_ids": manifest["cells"],
        "canonical_status": manifest["canonical_status"],
        "network_called": False,
        "live_execution_authorized_by_this_preflight": False,
    }
    if not bearer_present:
        result["blocker_reason"] = f"{BEARER_ENV} is missing or empty"
    return result


def require_live_preflight(*, authorize: bool, environ: Mapping[str, str] | None = None) -> str:
    """Validate live admission without printing or logging the bearer value."""
    if not authorize:
        raise SmokeRunnerError("live mode requires fresh exact smoke-dev authorization")
    environment = os.environ if environ is None else environ
    bearer = environment.get(BEARER_ENV, "")
    if not bearer.strip():
        raise SmokeRunnerError(f"{BEARER_ENV} is missing or empty")
    return bearer


def _response_meta(response: LLMResponse) -> Mapping[str, Any]:
    return response.raw_response if isinstance(response.raw_response, Mapping) else {}


def _billing_values(value: Any, key: str = "") -> list[Any]:
    values: list[Any] = []
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_name = str(child_key)
            if re.search(r"billing|cost|charge|overage|price|amount", child_name, re.I):
                if isinstance(child, (Mapping, list)):
                    values.extend(_billing_values(child, child_name))
                else:
                    values.append(child)
            else:
                values.extend(_billing_values(child, child_name))
    elif isinstance(value, list):
        for child in value:
            values.extend(_billing_values(child, key))
    return values


def _billing_status(response: LLMResponse) -> str:
    metadata = _response_meta(response)
    evidence = metadata.get("costEvidence")
    if isinstance(evidence, Mapping):
        expected_keys = {
            "status",
            "source",
            "estimatedCost",
            "currency",
            "inputTokens",
            "outputTokens",
            "providerChargeAttestation",
            "caveat",
        }
        estimated_cost = evidence.get("estimatedCost")
        input_tokens = evidence.get("inputTokens")
        output_tokens = evidence.get("outputTokens")
        if (
            set(evidence.keys()) == expected_keys
            and evidence.get("status") == "estimated_zero"
            and evidence.get("source") == "catalog_estimate"
            and type(estimated_cost) in {int, float}
            and estimated_cost == 0
            and evidence.get("currency") == "USD"
            and evidence.get("providerChargeAttestation") is False
            and type(input_tokens) is int
            and type(output_tokens) is int
            and input_tokens >= 0
            and output_tokens >= 0
            and evidence.get("caveat")
            == "Estimated from gateway model-price metadata; not provider charge attestation."
        ):
            remaining_metadata = {key: value for key, value in metadata.items() if key != "costEvidence"}
            values = _billing_values(remaining_metadata)
            if values:
                raise SmokeAbort("response metadata included unapproved billing fields outside costEvidence")
            return "explicit-zero-catalog-estimate"
        raise SmokeAbort("response metadata did not include explicit zero-charge billing evidence")
    if evidence is not None:
        raise SmokeAbort("response metadata did not include explicit zero-charge billing evidence")

    raise SmokeAbort("response metadata did not include explicit zero-charge billing evidence")


def _fallback_used(response: LLMResponse) -> bool:
    value = _response_meta(response).get("fallbackUsed", False)
    return value is True


def _tool_evidence_status(response: LLMResponse) -> str:
    evidence = _response_meta(response).get("toolEvidence")
    if not isinstance(evidence, Mapping):
        raise SmokeAbort("response metadata did not include strict toolEvidence")
    expected_keys = {
        "status",
        "mode",
        "source",
        "toolCallCount",
        "enforcement",
        "observable",
    }
    if (
        set(evidence.keys()) != expected_keys
        or evidence.get("status") != "complete"
        or evidence.get("mode") != "none"
        or evidence.get("source") != "opencode-json-events"
        or type(evidence.get("toolCallCount")) is not int
        or evidence.get("toolCallCount") != 0
        or evidence.get("enforcement") != "temporary-opencode-agent-config"
        or evidence.get("observable") is not True
    ):
        raise SmokeAbort("response metadata included malformed or non-zero toolEvidence")
    return "strict-zero-observed"


def _redact(value: Any, secrets: tuple[str, ...] = (), key: str = "") -> Any:
    if isinstance(value, Mapping):
        return {
            _redact(key_item, secrets): _redact(item, secrets, str(key_item))
            for key_item, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, secrets, key) for item in value]
    if isinstance(value, tuple):
        return [_redact(item, secrets, key) for item in value]
    if isinstance(value, str):
        redacted = value
        for secret in secrets:
            if secret:
                redacted = redacted.replace(secret, _REDACTED)
        if _SECRET_KEY.search(key):
            return _REDACTED
        return _SECRET_VALUE.sub(_REDACTED, redacted)
    return value


def _safe_error(exc: BaseException, secrets: tuple[str, ...] = ()) -> str:
    reason = str(exc) or type(exc).__name__
    return _SAFE_REASON.sub(" ", _redact(reason, secrets))[:240]


def _write_outputs(
    output_dir: Path,
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
    secrets: tuple[str, ...] = (),
) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise SmokeRunnerError(f"output path is not a directory: {output_dir}")
        marker = output_dir / _OUTPUT_MARKER
        if not marker.exists() and any(output_dir.iterdir()):
            raise SmokeRunnerError("refusing to overwrite a non-empty unrelated output directory")
    else:
        output_dir.mkdir(parents=True)
    (output_dir / _OUTPUT_MARKER).write_text("Gate 1 smoke-dev runner output\n", encoding="utf-8")
    (output_dir / "raw-responses").mkdir(exist_ok=True)
    manifest = _redact(manifest, secrets)
    rows = _redact(rows, secrets)
    (output_dir / "manifest.md").write_text("# Gate 1 Smoke-Dev Manifest\n\n```json\n" + json.dumps(manifest, indent=2) + "\n```\n", encoding="utf-8")
    for row in rows:
        if row.get("raw") is not None:
            raw = row["raw"]
            (output_dir / raw["path"]).write_text(json.dumps(raw, indent=2), encoding="utf-8")
    table = ["# Score Sheet", "", "| Cell ID | State | Retry | Fallback | Provider | Model | Tools | Billing | Canonical status |", "|---|---|---:|---|---|---|---|---|---|"]
    table.extend(f"| {r['cell_id']} | {r['state']} | {r['retry_count']} | {r['fallback_used']} | {r['provider_observed']} | {r['model_observed']} | none (enforced; observed) | {r['billing']} | smoke-only/non-canonical |" for r in rows)
    (output_dir / "score-sheet.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    complete = sum(row["state"] == "complete" for row in rows)
    summary = {"status": manifest["status"], "complete_cells": complete, "planned_cells": 12, "retry_count": sum(r["retry_count"] for r in rows), "fallback_count": sum(r["fallback_used"] for r in rows), "canonical_status": "smoke-only/non-canonical"}
    (output_dir / "public-summary.md").write_text("# Gate 1 Smoke-Dev Summary\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n\nThis is non-canonical smoke-dev evidence and cannot decide Gate 1.\n", encoding="utf-8")
    (output_dir / "deletion-receipt.md").write_text(
        f"# Deletion Receipt\n\nRun status: {manifest['status']}.\nPending retention cleanup; no deletion has been performed.\n",
        encoding="utf-8",
    )


async def run_smoke_dev(*, completion: Completion, run_id: str, output_dir: Path | None = None, live: bool = False, authorize: bool = False, environ: Mapping[str, str] | None = None) -> SmokeRunResult:
    """Run with an injected completion boundary; tests can therefore remain offline."""
    bearer = require_live_preflight(authorize=authorize, environ=environ) if live else None
    secrets = (bearer,) if bearer else ()
    cells = build_smoke_cells(run_id)
    manifest = plan_manifest(run_id)
    manifest["status"] = "in_progress"
    manifest["complete_cells"] = 0
    manifest["planned_cells"] = len(cells)
    rows: list[dict[str, Any]] = []
    if output_dir is not None:
        _write_outputs(output_dir, manifest, rows, secrets)

    def checkpoint() -> None:
        manifest["complete_cells"] = sum(row["state"] == "complete" for row in rows)
        if output_dir is not None:
            _write_outputs(output_dir, manifest, rows, secrets)

    for cell in cells:
        retry_count = 0
        fallback = False
        attempts = 0
        record: dict[str, Any] = {"cell_id": cell.cell_id, "state": "missing", "attempt_count": 0, "retry_count": 0, "retry_used": False, "fallback_used": False, "provider_observed": "unknown", "model_observed": "unknown", "billing": "unverified"}
        while True:
            attempts += 1
            record["attempt_count"] = attempts
            try:
                async def invoke(_prompt: str, _system_prompt: str | None = None) -> LLMResponse:
                    return await completion(cell)

                result = await capture_cell(cell, invoke)
                if result.state == "failed":
                    if any(term in result.factual_failure_reason.lower() for term in ("secret", "credential", "private", "sensitive")):
                        raise SmokeAbort("response or input violated secret/privacy retention controls")
                    raise SmokeRunnerError(result.factual_failure_reason)
                response = result.response
                assert response is not None
                raw_meta = _response_meta(response)
                observed_provider = raw_meta.get("resolvedProvider")
                observed_model = raw_meta.get("resolvedModel")
                if not isinstance(observed_provider, str) or not isinstance(observed_model, str):
                    raise SmokeAbort("response identity metadata was missing or invalid")
                if observed_provider != PROVIDER or observed_model != MODEL:
                    raise SmokeAbort("response provider/model did not match approved smoke pins")
                record["provider_observed"], record["model_observed"] = observed_provider, observed_model
                record["billing"] = _billing_status(response)
                record["tools"] = _tool_evidence_status(response)
                fallback = _fallback_used(response)
                record["fallback_used"] = fallback
                record["state"] = "complete"
                record["raw"] = {"path": f"raw-responses/{cell.cell_id}-attempt-{attempts}.json", "cell_id": cell.cell_id, "attempt": attempts, "provider_observed": observed_provider, "model_observed": observed_model, "smoke_only": True, "response": response.model_dump(mode="python")}
                break
            except SmokeAbort:
                record["state"] = "aborted"
                rows.append(record)
                manifest["status"] = "aborted"
                checkpoint()
                raise
            except Exception as exc:
                if attempts <= 1:
                    retry_count = 1
                    record["retry_count"] = retry_count
                    record["retry_used"] = True
                    continue
                record["state"] = "failed"
                record["error"] = _safe_error(exc, secrets)
                break
        rows.append(record)
        checkpoint()
    manifest["status"] = "complete" if all(row["state"] == "complete" for row in rows) else "incomplete"
    if output_dir is not None:
        checkpoint()
    return SmokeRunResult(manifest, output_dir)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or explicitly invoke the Gate 1 smoke-dev runner")
    parser.add_argument("--plan", action="store_true", help="print the offline manifest (default)")
    parser.add_argument("--preflight", action="store_true", help="print secret-safe offline readiness JSON")
    parser.add_argument("--live", action="store_true", help="invoke the approved local gateway")
    parser.add_argument("--authorize-smoke-dev", action="store_true", help="fresh exact smoke-dev authorization")
    parser.add_argument("--run-id", default="RUN-0001")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.preflight:
        readiness = preflight_manifest(args.run_id)
        print(json.dumps(readiness, indent=2))
        return 0 if readiness["status"] == "ready" else 1
    if not args.live:
        print(json.dumps(plan_manifest(args.run_id), indent=2))
        return 0
    bearer = require_live_preflight(authorize=args.authorize_smoke_dev)
    from md_evals.bridge_adapter import BridgeCompletionAdapter

    adapter = BridgeCompletionAdapter(
        base_url=GATEWAY_BASE, model=MODEL, provider=PROVIDER,
        defaults=Defaults(model=MODEL, provider=PROVIDER, max_tokens=MAX_TOKENS, retry_attempts=1),
        bearer=bearer,
        allow_fallback_metadata=True,
        tools=TOOLS,
    )

    async def complete(cell: FrozenCell) -> LLMResponse:
        return await adapter.complete(cell.prompt, None if cell.arm_id == "CONTROL" else cell.context_bytes.decode())

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir = Path.home() / "Escritorio" / f"gate-1-smoke-dev-{timestamp}-{args.run_id}"
    asyncio.run(run_smoke_dev(completion=complete, run_id=args.run_id, output_dir=output_dir, live=True, authorize=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
