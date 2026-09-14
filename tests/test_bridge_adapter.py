"""Offline contract tests for the HTTP bridge completion adapter."""

import asyncio
import json
import os
import socket
import sys
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import httpx
import pytest

if any(name == "litellm" or name.startswith("md_evals") for name in sys.modules):
    raise RuntimeError("run this module alone with --noconftest; unexpected preload")


class OutboundDenied(AssertionError):
    """Raised before a test can open a real socket or child process."""


@contextmanager
def outbound_guard():
    events = []

    def deny(*args, **kwargs):
        events.append("denied")
        raise OutboundDenied("offline fixture: outbound operation denied")

    with ExitStack() as stack:
        for target in (
            "socket.getaddrinfo",
            "socket.socket.connect",
            "socket.socket.connect_ex",
            "socket.socket.sendto",
            "socket.socket.sendmsg",
            "subprocess.Popen",
            "os.system",
        ):
            stack.enter_context(patch(target, deny))
        yield events


_COST_MAP = os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP")
_CONNECT = socket.socket.connect
with (
    outbound_guard() as _import_events,
    patch.dict(os.environ, {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}),
):
    from md_evals.bridge_adapter import BridgeCompletionAdapter
    from md_evals.llm import LLMError, LLMTimeoutError
    from md_evals.models import Defaults

if _import_events:
    raise RuntimeError("adapter import attempted outbound work")


class TrackingTransport(httpx.MockTransport):
    def __init__(self, handler):
        super().__init__(handler)
        self.closed = False

    async def aclose(self):
        self.closed = True
        await super().aclose()


def bridge_payload(text="answer", **extra):
    return {
        "text": text,
        "resolvedProvider": "fixture-provider",
        "resolvedModel": "fixture-model",
        "fallbackUsed": False,
        **extra,
    }


def adapter(handler, *, defaults=None, transports=None):
    transports = [] if transports is None else transports

    def factory():
        transport = TrackingTransport(handler)
        transports.append(transport)
        return transport

    return (
        BridgeCompletionAdapter(
            base_url="https://gateway.fixture",
            model="fixture-model",
            provider="fixture-provider",
            defaults=defaults
            or Defaults(
                model="fixture-model", provider="fixture-provider", timeout=1, retry_attempts=1
            ),
            transport_factory=factory,
        ),
        transports,
    )


@pytest.fixture(autouse=True)
def offline_only():
    assert os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP") == _COST_MAP
    assert socket.socket.connect is _CONNECT
    with outbound_guard() as events:
        yield
    assert events == []


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_posts_exact_bridge_wire_and_preserves_empty_text_and_raw_payload():
    captured = []

    async def handler(request):
        captured.append(request)
        return httpx.Response(
            200,
            json=bridge_payload(
                "",
                usageProvenance={
                    "status": "reported",
                    "origin": "cli-output",
                    "eventCount": 1,
                    "inputTokens": 0,
                    "outputTokens": 0,
                },
                ignored="preserved",
            ),
        )

    completion, transports = adapter(handler)
    response = await completion.complete("prompt", system_prompt="system")

    assert captured[0].method == "POST"
    assert captured[0].url.path == "/v1/generate"
    assert json.loads(captured[0].content) == {
        "prompt": "prompt",
        "system": "system",
        "provider": "fixture-provider",
        "model": "fixture-model",
        "requireProvider": True,
        "maxTokens": 2048,
    }
    assert response.content == ""
    assert response.tokens == response.prompt_tokens == response.completion_tokens_detail == 0
    assert response.usage_provenance == {
        "status": "reported",
        "origin": "cli-output",
        "eventCount": 1,
        "inputTokens": 0,
        "outputTokens": 0,
    }
    assert response.raw_response["ignored"] == "preserved"
    assert transports[0].closed


@pytest.mark.anyio
async def test_omits_absent_system_and_unsupported_defaults_from_wire():
    seen = []

    async def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=bridge_payload())

    completion, _ = adapter(
        handler,
        defaults=Defaults(
            model="fixture-model",
            provider="fixture-provider",
            temperature=0.01,
            retry_delay=9,
            timeout=1,
            retry_attempts=1,
        ),
    )
    await completion.complete("prompt")
    assert seen == [
        {
            "prompt": "prompt",
            "provider": "fixture-provider",
            "model": "fixture-model",
            "requireProvider": True,
            "maxTokens": 2048,
        }
    ]


@pytest.mark.anyio
async def test_includes_tools_none_when_gate1_is_configured():
    seen = []

    async def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=bridge_payload(toolEvidence={"status": "complete"}))

    completion, _ = adapter(handler)
    completion.tools = "none"
    await completion.complete("prompt")
    assert seen[0]["tools"] == "none"


@pytest.mark.anyio
async def test_each_completion_owns_a_fresh_transport_and_does_not_replay_cookies():
    requests, transports = [], []

    async def handler(request):
        requests.append(request)
        return httpx.Response(200, headers={"set-cookie": "session=secret"}, json=bridge_payload())

    completion, _ = adapter(handler, transports=transports)
    await completion.complete("one")
    await completion.complete("two")

    assert len(transports) == 2
    assert transports[0] is not transports[1]
    assert all(transport.closed for transport in transports)
    assert all(request.headers.get("cookie") is None for request in requests)


@pytest.mark.anyio
@pytest.mark.parametrize("status", [401, 429, 500])
async def test_status_failures_are_safe_single_attempt_errors(status):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, text="sentinel-secret-body")

    completion, transports = adapter(handler)
    with pytest.raises(LLMError) as raised:
        await completion.complete("sentinel-secret-prompt")
    assert type(raised.value) is LLMError
    assert "sentinel" not in str(raised.value)
    assert calls == 1
    assert transports[0].closed


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {"text": "answer", "fallbackUsed": False},
        {"text": "answer", "resolvedProvider": "wrong", "fallbackUsed": False},
        {"text": "answer", "resolvedProvider": "fixture-provider", "resolvedModel": "wrong", "fallbackUsed": False},
        {"text": "answer", "resolvedProvider": "fixture-provider", "resolvedModel": "fixture-model", "fallbackUsed": 0},
        {"text": "answer", "resolvedProvider": "fixture-provider", "fallbackUsed": True},
        {"text": 3, "resolvedProvider": "fixture-provider", "fallbackUsed": False},
    ],
)
async def test_bad_pin_or_decoder_payload_is_a_safe_llm_error(payload):
    async def handler(request):
        return httpx.Response(200, json=payload)

    completion, transports = adapter(handler)
    with pytest.raises(LLMError) as raised:
        await completion.complete("sentinel-secret-prompt")
    assert "sentinel" not in str(raised.value)
    assert transports[0].closed


@pytest.mark.anyio
async def test_redirect_malformed_json_and_non_object_are_rejected_safely():
    responses = [
        httpx.Response(302, headers={"location": "https://other.fixture"}),
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json=[]),
    ]

    async def handler(request):
        return responses.pop(0)

    completion, transports = adapter(handler)
    for _ in range(3):
        with pytest.raises(LLMError) as raised:
            await completion.complete("sentinel-secret-prompt")
        assert "sentinel" not in str(raised.value)
    assert all(transport.closed for transport in transports)


@pytest.mark.anyio
async def test_http_and_cooperative_deadline_timeouts_normalize_and_close_transport():
    async def http_timeout(request):
        raise httpx.ReadTimeout("sentinel-secret-timeout", request=request)

    completion, transports = adapter(http_timeout)
    with pytest.raises(LLMTimeoutError) as raised:
        await completion.complete("prompt")
    assert raised.value.to_error_payload()["error_code"] == "BRIDGE_HTTP_TIMEOUT"
    assert raised.value.to_error_payload()["attempt"] == 1
    assert raised.value.to_error_payload()["max_attempts"] == 1
    assert "sentinel" not in str(raised.value)
    assert transports[0].closed

    never = asyncio.Event()

    async def hanging(request):
        await never.wait()

    completion, transports = adapter(
        hanging,
        defaults=Defaults(
            model="fixture-model", provider="fixture-provider", timeout=1, retry_attempts=1
        ),
    )
    with pytest.raises(LLMTimeoutError):
        await completion.complete("prompt")
    assert transports[0].closed


@pytest.mark.anyio
async def test_external_cancellation_propagates_and_closes_owned_transport():
    entered, release = asyncio.Event(), asyncio.Event()

    async def hanging(request):
        entered.set()
        await release.wait()

    completion, transports = adapter(handler=hanging)
    task = asyncio.create_task(completion.complete("prompt"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert transports[0].closed


def test_invalid_configuration_fails_before_factory_or_io():
    calls = 0

    def factory():
        nonlocal calls
        calls += 1
        raise AssertionError("factory must not run")

    kwargs = dict(
        base_url="https://gateway.fixture",
        model="fixture-model",
        provider="fixture-provider",
        defaults=Defaults(
            model="fixture-model", provider="fixture-provider", timeout=1, retry_attempts=1
        ),
        transport_factory=factory,
    )
    for invalid_url in (
        "ftp://gateway.fixture",
        "https://user@gateway.fixture",
        "https://gateway.fixture/a",
        "https://gateway.fixture/?q=1",
    ):
        with pytest.raises(ValueError):
            BridgeCompletionAdapter(
                base_url=invalid_url, **{k: v for k, v in kwargs.items() if k != "base_url"}
            )
    with pytest.raises(ValueError):
        BridgeCompletionAdapter(**{**kwargs, "provider": " "})
    with pytest.raises(ValueError):
        BridgeCompletionAdapter(
            **{
                **kwargs,
                "defaults": Defaults(
                    model="fixture-model", provider="fixture-provider", retry_attempts=2
                ),
            }
        )
    assert calls == 0


def test_default_transport_factory_ignores_ambient_ssl_certificate_file(monkeypatch, tmp_path):
    missing_certificate = tmp_path / "missing-certificate.pem"
    completion = BridgeCompletionAdapter(
        base_url="https://gateway.fixture",
        model="fixture-model",
        provider="fixture-provider",
        defaults=Defaults(
            model="fixture-model", provider="fixture-provider", timeout=1, retry_attempts=1
        ),
    )

    with monkeypatch.context() as environment:
        environment.setenv("SSL_CERT_FILE", str(missing_certificate))
        transport = completion._transport_factory()
        asyncio.run(transport.aclose())


@pytest.mark.anyio
async def test_mutated_public_defaults_are_rejected_before_factory():
    async def handler(request):
        return httpx.Response(200, json=bridge_payload())

    completion, transports = adapter(handler)
    completion.defaults.timeout = 0
    with pytest.raises(ValueError):
        await completion.complete("prompt")
    assert transports == []
