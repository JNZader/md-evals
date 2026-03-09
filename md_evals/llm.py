"""LLM adapter using litellm."""

import asyncio
from typing import Any
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

from md_evals.models import LLMResponse, Defaults


class LLMError(Exception):
    """LLM API error."""
    pass


class LLMAdapter:
    """Wrapper for litellm completions."""
    
    def __init__(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = model
        self.provider = provider
        self.api_base = api_base
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
        """Build kwargs for litellm completion."""
        return {
            "model": f"{self.provider}/{self.model}" if "/" not in self.model else self.model,
            "temperature": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Complete a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            LLMResponse instance
        """
        import time
        
        start_time = time.monotonic()
        
        kwargs = self._build_kwargs(
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if system_prompt:
            kwargs["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            kwargs["messages"] = [{"role": "user", "content": prompt}]
        
        try:
            response = await self._complete_with_retry(**kwargs)
        except Exception as e:
            raise LLMError(f"LLM API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        # Extract content
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content or ""
        else:
            content = str(response)
        
        # Count tokens (approximate)
        tokens = 0
        if hasattr(response, "usage"):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _complete_with_retry(self, **kwargs) -> Any:
        """Complete with retry logic."""
        try:
            return await litellm.acompletion(**kwargs)
        except litellm.exceptions.RateLimitError as e:
            # Rate limited, let tenacity handle retry
            raise
        except litellm.exceptions.TimeoutError as e:
            # Timeout, let tenacity handle retry
            raise
        except Exception as e:
            # Other errors, maybe retry helps
            raise
    
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
