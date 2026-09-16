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


def test_docstring_declares_producers_not_executed_and_transport_only():
    from md_evals import gate1_utility_execute as module

    doc = (module.__doc__ or "").lower()
    assert "declared, not executed" in doc
    assert "transport execute" in doc
    assert "not a utility verdict" in doc


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
    assert "producer" not in control.lower()
    assert PRODUCERS["B_STRUCTURE"] in structured
    assert _escritorio_utility_paths() == before
    marker_hits = list((tmp_path / "run").rglob("*"))
    assert any(path.is_file() for path in marker_hits)


def test_abort_missing_cost_evidence_stops_remaining(deny_network):
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
    assert calls == 1
    assert result["status"] == "aborted"
    assert result["cells"][0]["status"] == "aborted"
    assert len(result["cells"]) == 1


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
        assert kwargs.get("authorize") is True
        assert callable(kwargs.get("completion"))
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
    assert defaults.timeout == 180
    assert defaults.retry_attempts == 1
    assert _escritorio_utility_paths() == before
