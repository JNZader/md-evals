"""LLM adapter using litellm."""

import asyncio
from typing import Any

import litellm

from md_evals.models import LLMResponse, Defaults


class LLMError(Exception):
    """LLM API error."""

    def __init__(self, message: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self._payload = payload or {"error": message}

    def to_error_payload(self) -> dict[str, Any]:
        """Return a backward-compatible structured payload for error consumers."""
        return dict(self._payload)


class LLMTimeoutError(LLMError):
    """Normalized timeout error for LiteLLM calls."""

    def __init__(self, payload: dict[str, Any]):
        message = str(payload.get("message") or "LLM request timed out")
        merged_payload = {"error": message, **payload}
        super().__init__(message=message, payload=merged_payload)


TIMEOUT_ERROR_TYPE = "llm_timeout"
TIMEOUT_ERROR_CODE = "LITELLM_TIMEOUT"

_TIMEOUT_MESSAGE_TOKENS = (
    "timed out",
    "timeout",
    "read timeout",
    "connect timeout",
    "request timeout",
    "operation timed out",
)

_NON_TIMEOUT_MESSAGE_TOKENS = (
    "auth",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "rate limit",
    "quota",
    "validation",
    "bad request",
    "permission",
)


def classify_litellm_timeout(exc: BaseException) -> tuple[bool, str, str]:
    """Classify whether an exception should be treated as timeout.

    Ordered checks: explicit type, cause chain, timeout attributes,
    then conservative message fallback.
    """
    if _is_cancellation_exception(exc):
        return False, "cancellation_excluded", "high"

    if _is_known_timeout_type(exc):
        return True, "known_type", "high"

    for cause in _iter_exception_chain(exc):
        if _is_known_timeout_type(cause):
            return True, "cause_chain", "high"

    if _has_timeout_attributes(exc):
        return True, "attribute", "medium"

    message = _exception_text(exc)
    if _has_timeout_message(message) and not _has_non_timeout_message(message):
        return True, "message_fallback", "low"

    return False, "not_timeout", "high"


def normalize_timeout_error(
    exc: BaseException,
    *,
    provider: str | None,
    model: str | None,
    stage: str | None,
    attempt: int | None,
    max_attempts: int | None,
) -> dict[str, Any]:
    """Build normalized timeout contract for CLI and structured output."""
    provider_name = provider or "unknown"
    model_name = model or "unknown"
    stage_name = stage or "single_pass"
    raw_exception = _exception_text(exc)

    message = (
        f"LLM request timed out for {provider_name}/{model_name} during {stage_name}. "
        "Try increasing timeout, reducing payload size, or retrying with lower concurrency."
    )

    return {
        "error_type": TIMEOUT_ERROR_TYPE,
        "error_code": TIMEOUT_ERROR_CODE,
        "message": message,
        "provider": provider_name,
        "model": model_name,
        "stage": stage_name,
        "is_retryable": True,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "raw_exception": raw_exception,
    }


def map_litellm_error(
    exc: BaseException,
    *,
    provider: str,
    model: str,
    stage: str,
    attempt: int | None,
    max_attempts: int | None,
) -> LLMError | None:
    """Map LiteLLM exception into normalized md-evals error contract."""
    is_timeout, _, _ = classify_litellm_timeout(exc)
    if not is_timeout:
        return None

    payload = normalize_timeout_error(
        exc,
        provider=provider,
        model=model,
        stage=stage,
        attempt=attempt,
        max_attempts=max_attempts,
    )
    return LLMTimeoutError(payload)


def _iter_exception_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = exc
    seen_ids: set[int] = set()
    while current is not None and id(current) not in seen_ids:
        seen_ids.add(id(current))
        chain.append(current)
        next_exc = current.__cause__ or current.__context__
        current = next_exc if isinstance(next_exc, BaseException) else None
    return chain


def _is_cancellation_exception(exc: BaseException) -> bool:
    return isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt, GeneratorExit))


def _is_known_timeout_type(exc: BaseException) -> bool:
    timeout_error_type = getattr(getattr(litellm, "exceptions", object()), "TimeoutError", None)
    if timeout_error_type and isinstance(exc, timeout_error_type):
        return True
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return True

    name = type(exc).__name__.lower()
    return name in {"timeouterror", "readtimeout", "connecttimeout", "apitimeouterror"}


def _has_timeout_attributes(exc: BaseException) -> bool:
    for attr_name in ("timeout", "timed_out", "is_timeout"):
        value = getattr(exc, attr_name, None)
        if value is True:
            return True
    return False


def _exception_text(exc: BaseException) -> str:
    return str(exc).strip() or type(exc).__name__


def _has_timeout_message(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in _TIMEOUT_MESSAGE_TOKENS)


def _has_non_timeout_message(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in _NON_TIMEOUT_MESSAGE_TOKENS)


class LLMAdapter:
    """Wrapper for litellm completions."""
    
    def __init__(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        api_key: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = model
        self.provider = provider
        self.api_base = api_base
        self.api_key = api_key
        self.defaults = defaults or Defaults()
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def _build_kwargs(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion.

        Model string is ALWAYS ``provider/model`` so litellm can route
        correctly — even when the model id itself contains slashes
        (e.g. ``openrouter/google/gemma-3-27b-it:free``).
        """
        kwargs: dict[str, Any] = {
            "model": f"{self.provider}/{self.model}",
            "temperature": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key
        kwargs.update(extra_kwargs)
        return kwargs
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stage_type: str = "single_pass",
        **extra_kwargs,
    ) -> LLMResponse:
        """Complete a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens
            stage_type: Stage label for orchestrator support
            **extra_kwargs: Additional kwargs forwarded to litellm (e.g. response_format)
            
        Returns:
            LLMResponse instance
        """
        import time
        
        start_time = time.monotonic()
        
        kwargs = self._build_kwargs(
            temperature=temperature,
            max_tokens=max_tokens,
            **extra_kwargs
        )
        
        if system_prompt:
            kwargs["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            kwargs["messages"] = [{"role": "user", "content": prompt}]
        
        try:
            response = await self._complete_with_retry(stage_type=stage_type, **kwargs)
        except LLMTimeoutError:
            raise
        except Exception as e:
            raise LLMError(f"LLM API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        # Extract content
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content or ""
        else:
            content = str(response)
        
        # Extract token usage
        tokens = 0                      # Legacy field — backward compat
        prompt_tokens = None
        completion_tokens_detail = None
        total_tokens_val = None
        
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            raw_completion = getattr(usage, "completion_tokens", None)
            raw_prompt = getattr(usage, "prompt_tokens", None)
            
            # Only accept integer values (guard against non-numeric types)
            if isinstance(raw_completion, int):
                completion_tokens_detail = raw_completion
            if isinstance(raw_prompt, int):
                prompt_tokens = raw_prompt
            
            # Legacy field — keep as completion_tokens or 0
            tokens = completion_tokens_detail or 0
            
            # Clamp negatives (EC-03 from spec)
            if prompt_tokens is not None and prompt_tokens < 0:
                prompt_tokens = 0
            if completion_tokens_detail is not None and completion_tokens_detail < 0:
                completion_tokens_detail = 0
                tokens = 0
            
            # Calculate total
            if prompt_tokens is not None and completion_tokens_detail is not None:
                total_tokens_val = prompt_tokens + completion_tokens_detail
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
            prompt_tokens=prompt_tokens,
            completion_tokens_detail=completion_tokens_detail,
            total_tokens=total_tokens_val,
            stage_type=stage_type,
        )
    
    async def _complete_with_retry(self, *, stage_type: str = "single_pass", **kwargs) -> Any:
        """Complete with retry logic."""
        max_attempts = max(1, int(self.defaults.retry_attempts or 1))
        initial_backoff = max(0.0, float(self.defaults.retry_delay or 0.0))
        last_exception: BaseException | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                return await litellm.acompletion(**kwargs)
            except Exception as exc:  # pragma: no branch - single mapping path
                last_exception = exc
                if attempt >= max_attempts or _is_cancellation_exception(exc):
                    mapped_error = map_litellm_error(
                        exc,
                        provider=self.provider,
                        model=self.model,
                        stage=stage_type,
                        attempt=attempt,
                        max_attempts=max_attempts,
                    )
                    if mapped_error is not None:
                        raise mapped_error from exc
                    raise

                backoff_seconds = min(initial_backoff * (2 ** (attempt - 1)), 10.0)
                if backoff_seconds > 0:
                    await asyncio.sleep(backoff_seconds)

        if last_exception is not None:
            raise last_exception

        raise LLMError("LLM API error: unknown retry failure")
    
    async def complete_with_json(
        self,
        prompt: str,
        json_schema: dict[str, Any],
        **kwargs
    ) -> LLMResponse:
        """Complete with JSON response format.
        
        Args:
            prompt: User prompt
            json_schema: JSON schema for response
            **kwargs: Additional arguments
            
        Returns:
            LLMResponse with parsed JSON content
        """
        import json
        
        # Add schema to kwargs
        kwargs["response_format"] = json_schema
        
        response = await self.complete(prompt, **kwargs)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response


def inject_skill(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
    """Inject skill content into prompt.
    
    Args:
        prompt: User prompt
        skill_path: Path to skill file (None = CONTROL)
        
    Returns:
        Tuple of (final_prompt, system_prompt)
    """
    from pathlib import Path
    
    if skill_path is None:
        # CONTROL - no skill
        return prompt, None
    
    # Read skill file
    skill_file = Path(skill_path)
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")
    
    skill_content = skill_file.read_text(encoding="utf-8")
    
    # Inject as system prompt
    system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""
    
    return prompt, system_prompt
