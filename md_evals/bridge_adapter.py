"""Explicit, one-shot HTTP adapter for the bridge ``/v1/generate`` endpoint."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from md_evals.bridge_usage import decode_generate_response
from md_evals.llm import LLMError, LLMTimeoutError
from md_evals.models import Defaults, LLMResponse

TransportFactory = Callable[[], httpx.AsyncBaseTransport]
_TIMEOUT_CODE = "BRIDGE_HTTP_TIMEOUT"


class BridgeCompletionAdapter:
    """Use an explicitly configured bridge origin once per call.

    This adapter deliberately does not read environment configuration or credentials.
    The bridge endpoint has no supported temperature field: a configured temperature is
    retained in ``defaults`` for the runner but is not sent to the bridge.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        provider: str,
        defaults: Defaults,
        transport_factory: TransportFactory | None = None,
        bearer: str | None = None,
        allow_fallback_metadata: bool = False,
        tools: str | None = None,
    ) -> None:
        self._endpoint = _validate_origin(base_url)
        self.model = _require_nonblank(model, "model")
        self.provider = _require_nonblank(provider, "provider")
        if bearer is not None and (not isinstance(bearer, str) or not bearer.strip()):
            raise ValueError("bearer must be a nonblank string or None")
        self._bearer = bearer
        if type(allow_fallback_metadata) is not bool:
            raise ValueError("allow_fallback_metadata must be a bool")
        self._allow_fallback_metadata = allow_fallback_metadata
        if tools not in {None, "none"}:
            raise ValueError("tools must be None or 'none'")
        self.tools = tools
        self.defaults = _validate_defaults(defaults, self.model, self.provider).model_copy(
            deep=True
        )
        if transport_factory is not None and not callable(transport_factory):
            raise ValueError("transport_factory must be callable")
        self._transport_factory = transport_factory or _default_transport_factory

    async def complete(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        """POST one bridge request and normalize only public contract failures.

        A local deadline stops waiting for this client operation; it cannot prove remote
        process termination, remote cancellation, or model identity.
        """
        defaults = _validate_defaults(self.defaults, self.model, self.provider)
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        if system_prompt is not None and not isinstance(system_prompt, str):
            raise ValueError("system_prompt must be a string or None")

        transport = self._transport_factory()
        if not isinstance(transport, httpx.AsyncBaseTransport):
            raise LLMError("Bridge transport is unavailable")

        payload: dict[str, Any] = {
            "prompt": prompt,
            "provider": self.provider,
            "model": self.model,
            "requireProvider": True,
            "maxTokens": defaults.max_tokens,
        }
        if system_prompt is not None:
            payload["system"] = system_prompt
        if self.tools is not None:
            payload["tools"] = self.tools

        started = time.monotonic()
        try:
            async with httpx.AsyncClient(
                transport=transport,
                timeout=httpx.Timeout(float(defaults.timeout)),
                trust_env=False,
                follow_redirects=False,
            ) as client:
                headers = (
                    {} if self._bearer is None else {"Authorization": f"Bearer {self._bearer}"}
                )
                async with asyncio.timeout(float(defaults.timeout)):
                    response = await client.post(self._endpoint, json=payload, headers=headers)
        except (asyncio.TimeoutError, httpx.TimeoutException):
            raise _timeout_error(self.provider, self.model) from None
        except httpx.HTTPError:
            raise LLMError("Bridge request failed") from None

        if not 200 <= response.status_code < 300:
            raise LLMError("Bridge request failed")

        try:
            wire_payload = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            raise LLMError("Bridge response was invalid") from None
        if not isinstance(wire_payload, dict):
            raise LLMError("Bridge response was invalid")
        if (
            not isinstance(wire_payload.get("resolvedProvider"), str)
            or not wire_payload["resolvedProvider"].strip()
        ):
            raise LLMError("Bridge provider pin was not confirmed")
        if (
            not isinstance(wire_payload.get("resolvedModel"), str)
            or not wire_payload["resolvedModel"].strip()
        ):
            raise LLMError("Bridge model pin was not confirmed")
        if type(wire_payload.get("fallbackUsed")) is not bool:
            raise LLMError("Bridge provider pin was not confirmed")
        if wire_payload["resolvedProvider"] != self.provider:
            raise LLMError("Bridge provider pin was not confirmed")
        if wire_payload["resolvedModel"] != self.model:
            raise LLMError("Bridge model pin was not confirmed")
        if not self._allow_fallback_metadata and wire_payload["fallbackUsed"] is not False:
            raise LLMError("Bridge provider pin was not confirmed")

        try:
            return decode_generate_response(
                wire_payload,
                model=self.model,
                provider=self.provider,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
        except ValueError:
            raise LLMError("Bridge response was invalid") from None


def _validate_origin(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("base_url must be a nonblank HTTP(S) origin")
    parsed = urlsplit(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("base_url must be an HTTP(S) origin")
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("base_url must have a valid port") from None
    host = parsed.hostname
    if ":" in host:
        host = f"[{host}]"
    origin = f"{parsed.scheme}://{host}"
    if port is not None:
        origin = f"{origin}:{port}"
    return f"{origin}/v1/generate"


def _default_transport_factory() -> httpx.AsyncBaseTransport:
    return httpx.AsyncHTTPTransport(trust_env=False)


def _validate_defaults(defaults: Defaults, model: str, provider: str) -> Defaults:
    if not isinstance(defaults, Defaults):
        raise ValueError("defaults must be Defaults")
    if defaults.model != model or defaults.provider != provider:
        raise ValueError("defaults model and provider must match adapter")
    if type(defaults.timeout) is not int or defaults.timeout <= 0:
        raise ValueError("defaults.timeout must be positive")
    if type(defaults.max_tokens) is not int or defaults.max_tokens <= 0:
        raise ValueError("defaults.max_tokens must be positive")
    if defaults.retry_attempts != 1:
        raise ValueError("defaults.retry_attempts must be 1")
    return defaults


def _require_nonblank(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonblank")
    return value


def _timeout_error(provider: str, model: str) -> LLMTimeoutError:
    return LLMTimeoutError(
        {
            "error_type": "llm_timeout",
            "error_code": _TIMEOUT_CODE,
            "message": "Bridge request timed out.",
            "provider": provider,
            "model": model,
            "stage": "single_pass",
            "is_retryable": False,
            "attempt": 1,
            "max_attempts": 1,
        }
    )
