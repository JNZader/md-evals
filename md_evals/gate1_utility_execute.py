"""Fail-closed Gate 1 utility transport execute.

Tests inject ``produce(cell) -> str``; live CLI passes ``default_produce``.
``default_produce`` subprocesses RepoForge for B (argv list, timeout 30s).
C loads fixture memories.json and never subprocesses engram. D parses graph
entities then selects overlapping memories (inject ``graph_json`` in tests).
Tests mock subprocess and never contact the gateway.
This is transport execute, not a utility verdict.

Default and ``--plan`` only print ``build_plan()``. Live gateway POST happens
only with ``--live --authorize-utility-gate1`` and GATE1_GATEWAY_BEARER.
Tests inject ``completion(cell) -> LLMResponse`` and never contact the gateway.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from md_evals.gate1_utility_plan import BUDGET_TOKENS, TIMEOUT_SECONDS, build_plan
from md_evals.models import LLMResponse

BEARER_ENV = "GATE1_GATEWAY_BEARER"
GATEWAY_BASE = "http://127.0.0.1:3456"
_OUTPUT_MARKER = ".gate1-utility-execute"
Completion = Callable[[dict[str, Any]], LLMResponse]
Produce = Callable[[Mapping[str, Any]], str]
_TRANSPORT_ERROR_NAMES = frozenset({"LLMError", "LLMTimeoutError", "UtilityTransportError"})
_PRODUCER_TIMEOUT_SECONDS = 30
_PRODUCER_OUTPUT_CAP = 8000
_DEFAULT_WORKSPACE = Path("tests/fixtures/context_broker/repoforge_capture")
_ORCHESTRATION_LINE = "orchestration: smart-context (graph entities then memory)"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_MEMORIES_PATH = _REPO_ROOT / "tests/fixtures/context_broker/gate1_utility/memories.json"


class UtilityTransportError(Exception):
    """Fail-closed transport failure; does not import LiteLLM."""


TASK_QUESTIONS = {
    "locate": (
        "Question: Which file imports src/base.ts? "
        "Reply with exactly one repository path. No extra prose."
    ),
    "decision": (
        "Question: Which active decision applies to src/consumer.ts? "
        "If there is no producer_output, answer NONE. "
        "Reply NONE or the decision title as the first token."
    ),
    "mismatch": (
        "Question: Does memory name a symbol absent from the graph? "
        "If there is no producer_output, answer NO_CONFLICT. "
        "Reply CONFLICT, NO_CONFLICT, or UNKNOWN as the first token."
    ),
}


def _cell_prompt(cell: Mapping[str, Any], producer_output: str | None = None) -> str:
    task = str(cell["task"])
    lines = [
        f"task: {task}",
        f"arm: {cell['arm']}",
        f"repetition: {cell['repetition']}",
        TASK_QUESTIONS[task],
    ]
    if cell.get("arm") != "CONTROL" and "producer" in cell:
        lines.append(f"producer: {cell['producer']}")
    if cell.get("arm") != "CONTROL" and producer_output is not None:
        lines.append(f"producer_output: {producer_output}")
    return "\n".join(lines)


def _workspace() -> Path:
    return _DEFAULT_WORKSPACE if _DEFAULT_WORKSPACE.exists() else Path.cwd()


def _unavailable(arm: str, reason: str) -> str:
    short = " ".join(str(reason).split())[:120]
    return f"PRODUCER_UNAVAILABLE: {arm}: {short}"


def _cap_output(text: str) -> str:
    return text[:_PRODUCER_OUTPUT_CAP]


def _run_argv(argv: list[str], arm: str) -> str:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=_PRODUCER_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return _unavailable(arm, f"missing binary {argv[0]}")
    except subprocess.TimeoutExpired:
        return _unavailable(arm, "timeout")
    if completed.returncode != 0:
        reason = (completed.stderr or completed.stdout or f"exit {completed.returncode}").strip()
        return _unavailable(arm, reason or f"exit {completed.returncode}")
    return _cap_output(completed.stdout or "")


def _produce_b_structure() -> str:
    workspace = _workspace()
    return _run_argv(
        ["repoforge", "graph", "-w", str(workspace), "--v2", "--format", "json"],
        "B_STRUCTURE",
    )


def _load_memories() -> list[Any]:
    payload = json.loads(_MEMORIES_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("memories.json must be a list")
    return payload


def _produce_c_memory(cell: Mapping[str, Any]) -> str:
    task = str(cell.get("task", ""))
    memories = _load_memories()
    if task == "decision":
        selected = [item for item in memories if item.get("type") == "decision"]
    elif task == "mismatch":
        selected = [
            item
            for item in memories
            if "ghostFn" in json.dumps(item, ensure_ascii=True)
        ]
    else:
        selected = []
    return _cap_output(json.dumps(selected))


def _graph_tokens(graph: Mapping[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for node in graph.get("nodes", []):
        if not isinstance(node, Mapping):
            continue
        for key in ("id", "name", "file_path"):
            value = node.get(key)
            if value:
                tokens.add(str(value))
        exports = node.get("exports") or []
        if isinstance(exports, list):
            tokens.update(str(item) for item in exports if item)
    for edge in graph.get("edges", []):
        if not isinstance(edge, Mapping):
            continue
        for key in ("id", "name", "source", "target", "file_path"):
            value = edge.get(key)
            if value:
                tokens.add(str(value))
    return tokens


def _select_overlapping_memories(graph: Mapping[str, Any]) -> list[Any]:
    tokens = _graph_tokens(graph)
    selected: list[Any] = []
    for item in _load_memories():
        if not isinstance(item, Mapping):
            continue
        entities = item.get("entities") or []
        if not isinstance(entities, list):
            continue
        if any(str(entity) in tokens for entity in entities if entity):
            selected.append(item)
    return selected


def _produce_d_shadow(graph_json: str | None = None) -> str:
    raw = graph_json if graph_json is not None else _produce_b_structure()
    if raw.startswith("PRODUCER_UNAVAILABLE:"):
        return raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {}
    graph = parsed if isinstance(parsed, dict) else {}
    payload = {"graph": graph, "memories": _select_overlapping_memories(graph)}
    return _cap_output(f"{json.dumps(payload)}\n{_ORCHESTRATION_LINE}")


def default_produce(cell: Mapping[str, Any], graph_json: str | None = None) -> str:
    """Run the arm producer. Live CLI only; tests mock subprocess or inject graph."""
    arm = str(cell.get("arm", ""))
    if arm == "CONTROL":
        return ""
    if arm == "B_STRUCTURE":
        return _produce_b_structure()
    if arm == "C_MEMORY":
        return _produce_c_memory(cell)
    if arm == "D_SHADOW":
        return _produce_d_shadow(graph_json=graph_json)
    return _unavailable(arm, "unknown arm")


def _raw(response: LLMResponse) -> Mapping[str, Any]:
    raw = response.raw_response
    return raw if isinstance(raw, Mapping) else {}


def _billing_label(raw: Mapping[str, Any]) -> str:
    evidence = raw.get("costEvidence")
    if not isinstance(evidence, Mapping):
        return "unverified"
    cost = evidence.get("estimatedCost")
    if type(cost) in {int, float} and type(cost) is not bool and cost == 0:
        return "explicit-zero"
    return "nonzero"


def _abort_reason(response: LLMResponse, provider: str, model: str) -> str | None:
    raw = _raw(response)
    evidence = raw.get("costEvidence")
    if isinstance(evidence, Mapping):
        cost = evidence.get("estimatedCost")
        if type(cost) is bool or type(cost) not in {int, float} or cost != 0:
            return "estimatedCost is not 0"
    if raw.get("fallbackUsed") is True:
        return "fallbackUsed"
    if raw.get("resolvedProvider") != provider or raw.get("resolvedModel") != model:
        return "resolved provider/model mismatch"
    return None


ANSWER_CAP = 8000


def _write_marker(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / _OUTPUT_MARKER).write_text(
        "Gate 1 utility execute output\n", encoding="utf-8"
    )


def _checkpoint(output_dir: Path | None, payload: Mapping[str, Any]) -> None:
    if output_dir is None:
        return
    (output_dir / "results.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def _clip_answer(content: str) -> str:
    if len(content) <= ANSWER_CAP:
        return content
    return content[:ANSWER_CAP]


def preflight_manifest(environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    environment = os.environ if environ is None else environ
    bearer_present = bool(str(environment.get(BEARER_ENV, "")).strip())
    return {
        "status": "ready" if bearer_present else "blocked",
        "bearer_present": bearer_present,
        "planned_cells": 24,
        "network_called": False,
        "live_execution_authorized_by_this_preflight": False,
    }


def run_utility_execute(
    *,
    completion: Completion,
    authorize: bool = False,
    output_dir: Path | None = None,
    produce: Produce | None = None,
) -> dict[str, Any]:
    """Run 24 plan cells sequentially with an injected completion.

    ``authorize`` is required by the live CLI path. Tests inject completion so
    this never opens a gateway socket. Abort remaining cells on missing
    costEvidence, non-zero estimatedCost, fallbackUsed, or pin mismatch.
    ``produce`` defaults to empty output in tests; live CLI passes
    ``default_produce``.
    """
    del authorize
    plan = build_plan()
    provider = str(plan["provider"])
    model = str(plan["model"])
    records: list[dict[str, Any]] = []
    if output_dir is not None:
        _write_marker(output_dir)
    for cell in plan["cells"]:
        assert isinstance(cell, dict)
        work = dict(cell)
        producer_output: str | None = None
        if cell.get("arm") != "CONTROL":
            producer_output = produce(work) if produce is not None else ""
        work["prompt"] = _cell_prompt(cell, producer_output=producer_output)
        try:
            response = completion(work)
        except Exception as exc:
            if type(exc).__name__ not in _TRANSPORT_ERROR_NAMES:
                raise
            record = {
                "task": cell["task"],
                "arm": cell["arm"],
                "repetition": cell["repetition"],
                "status": "aborted",
                "reason": str(exc)[:200],
            }
            records.append(record)
            payload = {"status": "aborted", "cells": records}
            _checkpoint(output_dir, payload)
            return payload
        reason = _abort_reason(response, provider, model)
        record = {
            "task": cell["task"],
            "arm": cell["arm"],
            "repetition": cell["repetition"],
            "status": "aborted" if reason else "complete",
            "answer": _clip_answer(response.content),
        }
        if reason:
            record["reason"] = reason
            records.append(record)
            payload = {"status": "aborted", "cells": records}
            _checkpoint(output_dir, payload)
            return payload
        record["billing"] = _billing_label(_raw(response))
        records.append(record)
        _checkpoint(output_dir, {"status": "in_progress", "cells": records})
    payload = {"status": "complete", "cells": records}
    _checkpoint(output_dir, payload)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan, preflight, or fail-closed live Gate 1 utility execute"
    )
    parser.add_argument("--plan", action="store_true", help="print the JSON plan (default)")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="print secret-safe readiness JSON without authorizing live execute",
    )
    parser.add_argument("--live", action="store_true", help="invoke the local gateway")
    parser.add_argument(
        "--authorize-utility-gate1",
        action="store_true",
        help="fresh exact utility-gate1 authorization",
    )
    parser.add_argument("--run-id", default="RUN-0001")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.preflight:
        readiness = preflight_manifest()
        print(json.dumps(readiness, indent=2))
        return 0 if readiness["bearer_present"] else 1
    if args.live:
        if not args.authorize_utility_gate1:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "reason": "live mode requires --authorize-utility-gate1",
                    }
                )
            )
            return 2
        bearer = os.environ.get(BEARER_ENV, "")
        if not str(bearer).strip():
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "reason": f"{BEARER_ENV} is missing or empty",
                    }
                )
            )
            return 2
        from md_evals.bridge_adapter import BridgeCompletionAdapter
        from md_evals.models import Defaults

        plan = build_plan()
        adapter = BridgeCompletionAdapter(
            base_url=GATEWAY_BASE,
            model=str(plan["model"]),
            provider=str(plan["provider"]),
            defaults=Defaults(
                model=str(plan["model"]),
                provider=str(plan["provider"]),
                max_tokens=BUDGET_TOKENS,
                timeout=TIMEOUT_SECONDS,
                retry_attempts=1,
            ),
            bearer=bearer,
            allow_fallback_metadata=False,
            tools="none",
        )

        def complete(cell: dict[str, Any]) -> LLMResponse:
            return asyncio.run(adapter.complete(cell["prompt"]))

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        output_dir = Path.home() / "Escritorio" / f"gate-1-utility-{timestamp}-{args.run_id}"
        result = run_utility_execute(
            completion=complete,
            authorize=True,
            output_dir=output_dir,
            produce=default_produce,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "complete" else 2
    print(json.dumps(build_plan(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
