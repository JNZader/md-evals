"""Fail-closed tests for Gate 1 utility execute. No real gateway calls."""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from md_evals.gate1_utility_plan import MODEL, PROVIDER, PRODUCERS, build_plan
from md_evals.models import LLMResponse

BEARER = "GATE1_GATEWAY_BEARER"
SECRET = "sentinel-must-not-leak"
GATEWAY_ORIGIN = "http://127.0.0.1:3456"
HEAVY_MODULES = (
    "md_evals.bridge_adapter",
    "md_evals.llm",
    "litellm",
    "httpx",
    "requests",
)
ESCRITORIO = Path.home() / "Escritorio"


class NetworkForbidden(AssertionError):
    """Raised if a CLI or run invocation tries to open a network path."""


@pytest.fixture
def deny_network():
    def fail(*_args, **_kwargs):
        raise NetworkForbidden("network forbidden")

    with (
        patch("socket.getaddrinfo", side_effect=fail),
        patch("socket.socket.connect", side_effect=fail),
        patch("socket.socket.connect_ex", side_effect=fail),
        patch("socket.create_connection", side_effect=fail),
        patch("socket.socket.sendto", side_effect=fail),
        patch("socket.socket.sendmsg", side_effect=fail),
    ):
        yield


def _stdout_json(capsys):
    return json.loads(capsys.readouterr().out)


def _ok_response(**raw):
    payload = {
        "resolvedProvider": PROVIDER,
        "resolvedModel": MODEL,
        "fallbackUsed": False,
        "costEvidence": {"estimatedCost": 0},
    }
    payload.update(raw)
    return LLMResponse(content="offline", model=MODEL, provider=PROVIDER, raw_response=payload)


def _escritorio_utility_paths() -> set[Path]:
    if not ESCRITORIO.exists():
        return set()
    return set(ESCRITORIO.glob("gate-1-utility-*"))


def test_docstring_declares_injected_producers_and_transport_only():
    from md_evals import gate1_utility_execute as module

    doc = (module.__doc__ or "").lower()
    assert "declared, not executed" not in doc
    assert "transport execute" in doc
    assert "not a utility verdict" in doc
    assert hasattr(module, "default_produce")


def test_default_and_plan_print_build_plan_json_without_bearer_or_network(
    deny_network, capsys, monkeypatch
):
    from md_evals.gate1_utility_execute import main

    monkeypatch.setenv(BEARER, SECRET)
    getenv_keys: list[str] = []
    real_getenv = os.getenv

    def wrapped_getenv(key, default=None):
        getenv_keys.append(key)
        return real_getenv(key, default)

    monkeypatch.setattr(os, "getenv", wrapped_getenv)
    heavy_before = {name for name in HEAVY_MODULES if name in sys.modules}
    assert main([]) == 0
    default_plan = _stdout_json(capsys)
    assert main(["--plan"]) == 0
    flagged_plan = _stdout_json(capsys)
    assert default_plan == flagged_plan == build_plan()
    assert BEARER not in getenv_keys
    assert SECRET not in json.dumps(default_plan)
    assert {name for name in HEAVY_MODULES if name in sys.modules} == heavy_before


def test_preflight_without_bearer_exits_1_and_does_not_authorize(
    deny_network, capsys, monkeypatch
):
    from md_evals.gate1_utility_execute import main

    monkeypatch.delenv(BEARER, raising=False)
    heavy_before = {name for name in HEAVY_MODULES if name in sys.modules}
    assert main(["--preflight"]) == 1
    payload = _stdout_json(capsys)
    assert payload == {
        "status": payload["status"],
        "bearer_present": False,
        "planned_cells": 24,
        "network_called": False,
        "live_execution_authorized_by_this_preflight": False,
    }
    assert payload["status"]
    assert SECRET not in json.dumps(payload)
    assert {name for name in HEAVY_MODULES if name in sys.modules} == heavy_before


def test_preflight_with_bearer_exits_0_without_printing_token(
    deny_network, capsys, monkeypatch
):
    from md_evals.gate1_utility_execute import main

    monkeypatch.setenv(BEARER, SECRET)
    assert main(["--preflight"]) == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["bearer_present"] is True
    assert payload["planned_cells"] == 24
    assert payload["network_called"] is False
    assert payload["live_execution_authorized_by_this_preflight"] is False
    assert SECRET not in output


def test_live_without_authorize_is_blocked_exit_2(deny_network, capsys, monkeypatch):
    from md_evals.gate1_utility_execute import main

    monkeypatch.setenv(BEARER, SECRET)
    heavy_before = {name for name in HEAVY_MODULES if name in sys.modules}
    assert main(["--live"]) == 2
    payload = _stdout_json(capsys)
    assert payload["status"] == "blocked"
    assert SECRET not in json.dumps(payload)
    assert "md_evals.bridge_adapter" not in sys.modules or (
        "md_evals.bridge_adapter" in heavy_before
    )
    assert {name for name in HEAVY_MODULES if name in sys.modules} == heavy_before


def test_live_authorize_without_bearer_is_blocked_exit_2(deny_network, capsys, monkeypatch):
    from md_evals.gate1_utility_execute import main

    monkeypatch.delenv(BEARER, raising=False)
    heavy_before = {name for name in HEAVY_MODULES if name in sys.modules}
    assert main(["--live", "--authorize-utility-gate1"]) == 2
    payload = _stdout_json(capsys)
    assert payload["status"] == "blocked"
    assert SECRET not in json.dumps(payload)
    assert {name for name in HEAVY_MODULES if name in sys.modules} == heavy_before


def test_run_executes_twenty_four_plan_cells_in_order(deny_network, tmp_path):
    from md_evals.gate1_utility_execute import run_utility_execute

    seen: list[tuple[object, object, object]] = []
    prompts: list[str] = []
    before = _escritorio_utility_paths()

    def completion(cell):
        seen.append((cell["task"], cell["arm"], cell["repetition"]))
        prompts.append(cell["prompt"])
        return _ok_response()

    result = run_utility_execute(
        completion=completion, authorize=True, output_dir=tmp_path / "run"
    )
    expected = [
        (cell["task"], cell["arm"], cell["repetition"]) for cell in build_plan()["cells"]
    ]
    assert seen == expected
    assert len(seen) == 24
    assert result["status"] == "complete"
    control = prompts[0]
    structured = prompts[1]
    assert "conflict" in control and "CONTROL" in control and "1" in control
    assert "Question:" in control
    assert "producer_output:" not in control
    assert PRODUCERS["B_STRUCTURE"] in structured
    assert _escritorio_utility_paths() == before
    results = json.loads((tmp_path / "run" / "results.json").read_text(encoding="utf-8"))
    assert results["status"] == "complete"
    assert len(results["cells"]) == 24
    assert all(cell["answer"] == "offline" for cell in results["cells"])


def test_missing_cost_evidence_is_unverified_and_continues(deny_network):
    from md_evals.gate1_utility_execute import run_utility_execute

    calls = 0

    def completion(cell):
        nonlocal calls
        calls += 1
        return LLMResponse(
            content="offline",
            model=MODEL,
            provider=PROVIDER,
            raw_response={
                "resolvedProvider": PROVIDER,
                "resolvedModel": MODEL,
                "fallbackUsed": False,
            },
        )

    result = run_utility_execute(completion=completion, authorize=True)
    assert calls == 24
    assert result["status"] == "complete"
    assert {cell["billing"] for cell in result["cells"]} == {"unverified"}


def test_abort_transport_error_stops_remaining_without_traceback(deny_network):
    from md_evals.gate1_utility_execute import (
        UtilityTransportError,
        run_utility_execute,
    )

    calls = 0

    def completion(cell):
        nonlocal calls
        calls += 1
        raise UtilityTransportError("Bridge request failed")

    result = run_utility_execute(completion=completion, authorize=True)
    assert calls == 1
    assert result["status"] == "aborted"
    assert result["cells"] == [
        {
            "task": "conflict",
            "arm": "CONTROL",
            "repetition": 1,
            "status": "aborted",
            "reason": "Bridge request failed",
        }
    ]


def test_abort_nonzero_estimated_cost_stops_remaining(deny_network):
    from md_evals.gate1_utility_execute import run_utility_execute

    calls = 0

    def completion(cell):
        nonlocal calls
        calls += 1
        return _ok_response(costEvidence={"estimatedCost": 0.01})

    result = run_utility_execute(completion=completion, authorize=True)
    assert calls == 1
    assert result["status"] == "aborted"


def test_abort_fallback_used_stops_remaining(deny_network):
    from md_evals.gate1_utility_execute import run_utility_execute

    calls = 0

    def completion(cell):
        nonlocal calls
        calls += 1
        return _ok_response(fallbackUsed=True)

    result = run_utility_execute(completion=completion, authorize=True)
    assert calls == 1
    assert result["status"] == "aborted"


def test_abort_provider_model_mismatch_stops_remaining(deny_network):
    from md_evals.gate1_utility_execute import run_utility_execute

    calls = 0

    def completion(cell):
        nonlocal calls
        calls += 1
        return _ok_response(resolvedProvider="other-cli", resolvedModel=MODEL)

    result = run_utility_execute(completion=completion, authorize=True)
    assert calls == 1
    assert result["status"] == "aborted"


def test_live_authorized_constructs_adapter_and_does_not_touch_escritorio(
    deny_network, capsys, monkeypatch, tmp_path
):
    from md_evals.gate1_utility_execute import main

    monkeypatch.setenv(BEARER, SECRET)
    monkeypatch.setattr(Path, "home", lambda *_args, **_kwargs: tmp_path)
    constructed: dict[str, object] = {}
    before = _escritorio_utility_paths()

    class FakeAdapter:
        def __init__(self, **kwargs):
            constructed.update(kwargs)

        async def complete(self, prompt, system_prompt=None):
            raise AssertionError("injected run must not call adapter.complete")

    fake_mod = types.ModuleType("md_evals.bridge_adapter")
    fake_mod.BridgeCompletionAdapter = FakeAdapter

    def fake_run(**kwargs):
        from md_evals.gate1_utility_execute import default_produce

        assert kwargs.get("authorize") is True
        assert callable(kwargs.get("completion"))
        assert kwargs.get("produce") is default_produce
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(
        "md_evals.gate1_utility_execute.run_utility_execute", fake_run
    )
    with patch.dict(sys.modules, {"md_evals.bridge_adapter": fake_mod}):
        code = main(["--live", "--authorize-utility-gate1", "--run-id", "TEST"])
    assert code == 0
    output = capsys.readouterr().out
    assert SECRET not in output
    assert constructed["base_url"] == GATEWAY_ORIGIN
    assert constructed["model"] == MODEL
    assert constructed["provider"] == PROVIDER
    assert constructed["allow_fallback_metadata"] is False
    assert constructed["tools"] == "none"
    defaults = constructed["defaults"]
    assert defaults.timeout == 300
    assert defaults.retry_attempts == 1
    assert _escritorio_utility_paths() == before


B_JSON = '{"nodes":[{"id":"injected"}]}'
C_MEMORY_HIT = "engram-hit:conflict"
ORCHESTRATION = "orchestration: smart-context (RepoForge first, Engram second)"


def _injected_produce(cell):
    arm = cell["arm"]
    if arm == "B_STRUCTURE":
        return B_JSON
    if arm == "C_MEMORY":
        return C_MEMORY_HIT
    if arm == "D_SHADOW":
        return f"{B_JSON}\n{C_MEMORY_HIT}\n{ORCHESTRATION}"
    raise AssertionError(f"produce must not run for {arm}")


def test_injected_produce_is_called_per_non_control_cell(deny_network):
    from md_evals.gate1_utility_execute import run_utility_execute

    seen: list[tuple[object, object, object]] = []
    prompts: dict[str, list[str]] = {
        "CONTROL": [],
        "B_STRUCTURE": [],
        "C_MEMORY": [],
        "D_SHADOW": [],
    }

    def produce(cell):
        seen.append((cell["task"], cell["arm"], cell["repetition"]))
        return _injected_produce(cell)

    def completion(cell):
        prompts[cell["arm"]].append(cell["prompt"])
        return _ok_response()

    result = run_utility_execute(completion=completion, produce=produce)
    expected = [
        (cell["task"], cell["arm"], cell["repetition"])
        for cell in build_plan()["cells"]
        if cell["arm"] != "CONTROL"
    ]
    assert result["status"] == "complete"
    assert seen == expected
    assert len(seen) == 18
    assert all("producer_output:" not in prompt for prompt in prompts["CONTROL"])
    assert all(
        B_JSON in prompt and "producer_output:" in prompt
        for prompt in prompts["B_STRUCTURE"]
    )
    assert all(B_JSON in prompt and "producer_output:" in prompt for prompt in prompts["D_SHADOW"])
    assert all(C_MEMORY_HIT in prompt for prompt in prompts["C_MEMORY"])


def test_without_produce_control_has_no_producer_output(deny_network):
    from md_evals.gate1_utility_execute import run_utility_execute

    prompts: list[str] = []

    def completion(cell):
        prompts.append(cell["prompt"])
        return _ok_response()

    run_utility_execute(completion=completion)
    control = prompts[0]
    structured = prompts[1]
    assert "producer_output:" not in control
    assert "producer_output:" in structured


def test_default_produce_control_is_empty_without_subprocess(deny_network, monkeypatch):
    from md_evals.gate1_utility_execute import default_produce

    def fail(*_args, **_kwargs):
        raise AssertionError("CONTROL must not subprocess")

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", fail)
    assert default_produce({"arm": "CONTROL", "task": "conflict"}) == ""


def test_default_produce_b_structure_argv_caps_and_unavailable(deny_network, monkeypatch):
    from md_evals.gate1_utility_execute import default_produce

    recorded: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        recorded["argv"] = list(argv)
        recorded["kwargs"] = kwargs
        assert kwargs.get("shell") in (None, False)
        return types.SimpleNamespace(returncode=0, stdout="{" + "x" * 9000 + "}", stderr="")

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", fake_run)
    out = default_produce({"arm": "B_STRUCTURE", "task": "conflict"})
    argv = recorded["argv"]
    assert argv[:2] == ["repoforge", "graph"]
    assert "-w" in argv
    workspace = argv[argv.index("-w") + 1]
    fixture = Path("tests/fixtures/context_broker/repoforge_capture")
    assert workspace == str(fixture if fixture.exists() else Path.cwd())
    assert argv[argv.index("-w") + 2 :] == ["--v2", "--format", "json"]
    assert recorded["kwargs"]["timeout"] == 30
    assert recorded["kwargs"]["capture_output"] is True
    assert len(out) == 8000

    def missing(*_args, **_kwargs):
        raise FileNotFoundError("repoforge")

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", missing)
    unavailable = default_produce({"arm": "B_STRUCTURE", "task": "conflict"})
    assert unavailable.startswith("PRODUCER_UNAVAILABLE: B_STRUCTURE:")

    def boom(*_args, **_kwargs):
        return types.SimpleNamespace(returncode=2, stdout="", stderr="graph failed")

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", boom)
    nonzero = default_produce({"arm": "B_STRUCTURE", "task": "stale_dirty"})
    assert nonzero.startswith("PRODUCER_UNAVAILABLE: B_STRUCTURE:")
    assert "graph failed" in nonzero


def test_default_produce_c_memory_search_argv_and_unavailable(deny_network, monkeypatch):
    from md_evals.gate1_utility_execute import default_produce

    recorded: dict[str, object] = {}

    def fake_run(argv, **kwargs):
        recorded["argv"] = list(argv)
        recorded["kwargs"] = kwargs
        assert kwargs.get("shell") in (None, False)
        return types.SimpleNamespace(returncode=0, stdout="hit\n", stderr="")

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", fake_run)
    out = default_produce({"arm": "C_MEMORY", "task": "locate"})
    argv = recorded["argv"]
    assert argv[0] == "engram"
    assert argv[1] == "search"
    assert "locate" in argv
    assert "save" not in argv
    assert recorded["kwargs"]["timeout"] == 30
    assert out.strip() == "hit"

    def missing(*_args, **_kwargs):
        raise FileNotFoundError("engram")

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", missing)
    unavailable = default_produce({"arm": "C_MEMORY", "task": "locate"})
    assert unavailable.startswith("PRODUCER_UNAVAILABLE: C_MEMORY:")


def test_default_produce_d_shadow_joins_b_and_c(deny_network, monkeypatch):
    from md_evals.gate1_utility_execute import default_produce

    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        assert kwargs.get("shell") in (None, False)
        if argv[0] == "repoforge":
            return types.SimpleNamespace(returncode=0, stdout=B_JSON, stderr="")
        if argv[0] == "engram":
            return types.SimpleNamespace(returncode=0, stdout=C_MEMORY_HIT, stderr="")
        raise AssertionError(argv)

    monkeypatch.setattr("md_evals.gate1_utility_execute.subprocess.run", fake_run)
    out = default_produce({"arm": "D_SHADOW", "task": "conflict"})
    assert [call[0] for call in calls] == ["repoforge", "engram"]
    assert B_JSON in out
    assert C_MEMORY_HIT in out
    assert ORCHESTRATION in out
