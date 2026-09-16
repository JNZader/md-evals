"""Fail-closed tests for the Gate 1 utility preregister plan."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from md_evals.gate1_utility_plan import MODEL, PROVIDER, build_plan, main

ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "D_SHADOW")
TASKS = ("conflict", "stale_dirty", "locate")
GATEWAY = "http://127.0.0.1:3456/v1/generate"
PRODUCERS = {
    "B_STRUCTURE": "repoforge graph -w . --v2 --format json",
    "C_MEMORY": "Engram search+get",
    "D_SHADOW": "smart-context skill",
}
FORBIDDEN_ARMS = ("E_PAIRED", "D_UNION")
MODULE_PATH = Path(__file__).resolve().parents[1] / "md_evals" / "gate1_utility_plan.py"
HEAVY_MODULES = (
    "md_evals.bridge_adapter",
    "md_evals.llm",
    "md_evals.captured_pilot_plan",
    "litellm",
    "httpx",
    "requests",
)


class NetworkForbidden(AssertionError):
    """Raised if a CLI invocation tries to open a network path."""


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


def test_build_plan_prints_locked_twenty_four_cell_preregister():
    plan = build_plan()
    cells = plan["cells"]
    assert plan["canonical_status"] == "utility-preregister/not-executed"
    assert plan["execution_authorized"] is False
    assert plan["provider"] == "opencode-cli" == PROVIDER
    assert plan["model"] == "opencode/muse-spark-1.3-contributor-free" == MODEL
    assert plan["gateway"] == GATEWAY
    assert plan["n"] == 2
    assert tuple(plan["arms"]) == ARMS
    assert tuple(plan["tasks"]) == TASKS
    assert plan["timeout_seconds"] == 300
    assert plan["spend_cap_usd"] == 0
    assert plan["retry"] == 0
    assert plan["fallback"] == "forbidden"
    assert plan["temperature"] == 0
    assert plan["tools"] == ["Read", "rg/Grep"]
    assert len(cells) == 24
    expected = [
        (repetition, task, arm)
        for repetition in (1, 2)
        for task in TASKS
        for arm in ARMS
    ]
    assert [(cell["repetition"], cell["task"], cell["arm"]) for cell in cells] == expected
    for cell in cells:
        assert cell["repetition"] in (1, 2)
        assert cell["timeout"] == 300
        assert cell["model"] == MODEL
        assert cell["provider"] == PROVIDER
        if cell["arm"] == "CONTROL":
            assert cell["budget_tokens"] is None
            assert "producer" not in cell
        else:
            assert cell["budget_tokens"] == 4000
            assert cell["producer"] == PRODUCERS[cell["arm"]]
    serialized = json.dumps(plan)
    for forbidden in FORBIDDEN_ARMS:
        assert forbidden not in serialized


def test_docstring_rejects_smoke_and_unimplemented_live_execute():
    from md_evals import gate1_utility_plan as module

    doc = module.__doc__ or ""
    lowered = doc.lower()
    assert "not smoke-dev" in lowered
    assert "smoke cannot decide gate 1" in lowered
    assert "live execute is not implemented" in lowered


def test_source_never_reads_bearer_or_imports_live_backends():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "GATE1_GATEWAY_BEARER" not in source
    assert "bridge_adapter" not in source
    assert "litellm" not in source.lower()
    assert "repoforge graph" in source
    assert source.count("http://127.0.0.1:3456/v1/generate") >= 1


def test_default_and_plan_print_json_without_network_or_bearer(
    deny_network, capsys, monkeypatch
):
    monkeypatch.setenv("GATE1_GATEWAY_BEARER", "sentinel-must-not-leak")
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
    assert default_plan["execution_authorized"] is False
    assert "GATE1_GATEWAY_BEARER" not in getenv_keys
    assert "sentinel-must-not-leak" not in json.dumps(default_plan)
    assert {name for name in HEAVY_MODULES if name in sys.modules} == heavy_before


@pytest.mark.parametrize("flag", ["--live", "--execute"])
def test_live_and_execute_are_blocked_without_bridge_or_network(
    flag, deny_network, capsys, monkeypatch
):
    monkeypatch.setenv("GATE1_GATEWAY_BEARER", "sentinel-must-not-leak")
    heavy_before = {name for name in HEAVY_MODULES if name in sys.modules}
    assert main([flag]) == 2
    payload = _stdout_json(capsys)
    assert payload["status"] == "blocked"
    assert "reason" in payload
    assert "sentinel-must-not-leak" not in json.dumps(payload)
    assert "md_evals.bridge_adapter" not in sys.modules
    assert {name for name in HEAVY_MODULES if name in sys.modules} == heavy_before


def test_plan_plus_live_stays_blocked(deny_network, capsys):
    assert main(["--plan", "--live"]) == 2
    payload = _stdout_json(capsys)
    assert payload == {
        "status": "blocked",
        "reason": payload["reason"],
    }
    assert payload["reason"]
