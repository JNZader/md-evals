"""LLM adapter using litellm."""

import asyncio
from typing import Any
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

from md_evals.models import LLMResponse, Defaults
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


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
        args = [model, provider, api_base, defaults]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁLLMAdapterǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁLLMAdapterǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁLLMAdapterǁ__init____mutmut_orig(
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
    
    def xǁLLMAdapterǁ__init____mutmut_1(
        self,
        model: str,
        provider: str = "XXopenaiXX",
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
    
    def xǁLLMAdapterǁ__init____mutmut_2(
        self,
        model: str,
        provider: str = "OPENAI",
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
    
    def xǁLLMAdapterǁ__init____mutmut_3(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = None
        self.provider = provider
        self.api_base = api_base
        self.defaults = defaults or Defaults()
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_4(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = model
        self.provider = None
        self.api_base = api_base
        self.defaults = defaults or Defaults()
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_5(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = model
        self.provider = provider
        self.api_base = None
        self.defaults = defaults or Defaults()
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_6(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = model
        self.provider = provider
        self.api_base = api_base
        self.defaults = None
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_7(
        self,
        model: str,
        provider: str = "openai",
        api_base: str | None = None,
        defaults: Defaults | None = None
    ):
        self.model = model
        self.provider = provider
        self.api_base = api_base
        self.defaults = defaults and Defaults()
        
        # Configure litellm
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_8(
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
        litellm.drop_params = None
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_9(
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
        litellm.drop_params = False
        litellm.set_verbose = False
    
    def xǁLLMAdapterǁ__init____mutmut_10(
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
        litellm.set_verbose = None
    
    def xǁLLMAdapterǁ__init____mutmut_11(
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
        litellm.set_verbose = True
    
    xǁLLMAdapterǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLLMAdapterǁ__init____mutmut_1': xǁLLMAdapterǁ__init____mutmut_1, 
        'xǁLLMAdapterǁ__init____mutmut_2': xǁLLMAdapterǁ__init____mutmut_2, 
        'xǁLLMAdapterǁ__init____mutmut_3': xǁLLMAdapterǁ__init____mutmut_3, 
        'xǁLLMAdapterǁ__init____mutmut_4': xǁLLMAdapterǁ__init____mutmut_4, 
        'xǁLLMAdapterǁ__init____mutmut_5': xǁLLMAdapterǁ__init____mutmut_5, 
        'xǁLLMAdapterǁ__init____mutmut_6': xǁLLMAdapterǁ__init____mutmut_6, 
        'xǁLLMAdapterǁ__init____mutmut_7': xǁLLMAdapterǁ__init____mutmut_7, 
        'xǁLLMAdapterǁ__init____mutmut_8': xǁLLMAdapterǁ__init____mutmut_8, 
        'xǁLLMAdapterǁ__init____mutmut_9': xǁLLMAdapterǁ__init____mutmut_9, 
        'xǁLLMAdapterǁ__init____mutmut_10': xǁLLMAdapterǁ__init____mutmut_10, 
        'xǁLLMAdapterǁ__init____mutmut_11': xǁLLMAdapterǁ__init____mutmut_11
    }
    xǁLLMAdapterǁ__init____mutmut_orig.__name__ = 'xǁLLMAdapterǁ__init__'
    
    def _build_kwargs(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        args = [temperature, max_tokens, timeout]# type: ignore
        kwargs = {**extra_kwargs}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁLLMAdapterǁ_build_kwargs__mutmut_orig'), object.__getattribute__(self, 'xǁLLMAdapterǁ_build_kwargs__mutmut_mutants'), args, kwargs, self)
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_orig(
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
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_1(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "XXmodelXX": f"{self.provider}/{self.model}" if "/" not in self.model else self.model,
            "temperature": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_2(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "MODEL": f"{self.provider}/{self.model}" if "/" not in self.model else self.model,
            "temperature": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_3(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "model": f"{self.provider}/{self.model}" if "XX/XX" not in self.model else self.model,
            "temperature": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_4(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "model": f"{self.provider}/{self.model}" if "/" in self.model else self.model,
            "temperature": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_5(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "model": f"{self.provider}/{self.model}" if "/" not in self.model else self.model,
            "XXtemperatureXX": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_6(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "model": f"{self.provider}/{self.model}" if "/" not in self.model else self.model,
            "TEMPERATURE": temperature or self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_7(
        self,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **extra_kwargs
    ) -> dict[str, Any]:
        """Build kwargs for litellm completion."""
        return {
            "model": f"{self.provider}/{self.model}" if "/" not in self.model else self.model,
            "temperature": temperature and self.defaults.temperature,
            "max_tokens": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_8(
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
            "XXmax_tokensXX": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_9(
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
            "MAX_TOKENS": max_tokens or self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_10(
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
            "max_tokens": max_tokens and self.defaults.max_tokens,
            "timeout": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_11(
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
            "XXtimeoutXX": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_12(
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
            "TIMEOUT": timeout or self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_13(
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
            "timeout": timeout and self.defaults.timeout,
            "api_base": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_14(
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
            "XXapi_baseXX": self.api_base,
            **extra_kwargs
        }
    
    def xǁLLMAdapterǁ_build_kwargs__mutmut_15(
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
            "API_BASE": self.api_base,
            **extra_kwargs
        }
    
    xǁLLMAdapterǁ_build_kwargs__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLLMAdapterǁ_build_kwargs__mutmut_1': xǁLLMAdapterǁ_build_kwargs__mutmut_1, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_2': xǁLLMAdapterǁ_build_kwargs__mutmut_2, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_3': xǁLLMAdapterǁ_build_kwargs__mutmut_3, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_4': xǁLLMAdapterǁ_build_kwargs__mutmut_4, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_5': xǁLLMAdapterǁ_build_kwargs__mutmut_5, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_6': xǁLLMAdapterǁ_build_kwargs__mutmut_6, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_7': xǁLLMAdapterǁ_build_kwargs__mutmut_7, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_8': xǁLLMAdapterǁ_build_kwargs__mutmut_8, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_9': xǁLLMAdapterǁ_build_kwargs__mutmut_9, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_10': xǁLLMAdapterǁ_build_kwargs__mutmut_10, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_11': xǁLLMAdapterǁ_build_kwargs__mutmut_11, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_12': xǁLLMAdapterǁ_build_kwargs__mutmut_12, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_13': xǁLLMAdapterǁ_build_kwargs__mutmut_13, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_14': xǁLLMAdapterǁ_build_kwargs__mutmut_14, 
        'xǁLLMAdapterǁ_build_kwargs__mutmut_15': xǁLLMAdapterǁ_build_kwargs__mutmut_15
    }
    xǁLLMAdapterǁ_build_kwargs__mutmut_orig.__name__ = 'xǁLLMAdapterǁ_build_kwargs'
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        args = [prompt, system_prompt, temperature, max_tokens]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁLLMAdapterǁcomplete__mutmut_orig'), object.__getattribute__(self, 'xǁLLMAdapterǁcomplete__mutmut_mutants'), args, kwargs, self)
    
    async def xǁLLMAdapterǁcomplete__mutmut_orig(
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_1(
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
        
        start_time = None
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_2(
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
        
        kwargs = None
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_3(
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
            temperature=None,
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_4(
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
            max_tokens=None
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_5(
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_6(
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_7(
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
            kwargs["messages"] = None
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_8(
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
            kwargs["XXmessagesXX"] = [
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_9(
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
            kwargs["MESSAGES"] = [
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_10(
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
                {"XXroleXX": "system", "content": system_prompt},
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_11(
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
                {"ROLE": "system", "content": system_prompt},
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_12(
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
                {"role": "XXsystemXX", "content": system_prompt},
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_13(
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
                {"role": "SYSTEM", "content": system_prompt},
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_14(
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
                {"role": "system", "XXcontentXX": system_prompt},
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_15(
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
                {"role": "system", "CONTENT": system_prompt},
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_16(
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
                {"XXroleXX": "user", "content": prompt}
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_17(
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
                {"ROLE": "user", "content": prompt}
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_18(
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
                {"role": "XXuserXX", "content": prompt}
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_19(
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
                {"role": "USER", "content": prompt}
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_20(
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
                {"role": "user", "XXcontentXX": prompt}
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_21(
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
                {"role": "user", "CONTENT": prompt}
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_22(
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
            kwargs["messages"] = None
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_23(
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
            kwargs["XXmessagesXX"] = [{"role": "user", "content": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_24(
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
            kwargs["MESSAGES"] = [{"role": "user", "content": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_25(
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
            kwargs["messages"] = [{"XXroleXX": "user", "content": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_26(
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
            kwargs["messages"] = [{"ROLE": "user", "content": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_27(
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
            kwargs["messages"] = [{"role": "XXuserXX", "content": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_28(
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
            kwargs["messages"] = [{"role": "USER", "content": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_29(
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
            kwargs["messages"] = [{"role": "user", "XXcontentXX": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_30(
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
            kwargs["messages"] = [{"role": "user", "CONTENT": prompt}]
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_31(
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
            response = None
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_32(
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
            raise LLMError(None) from e
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_33(
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
        
        duration_ms = None
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_34(
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
        
        duration_ms = int(None)
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_35(
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
        
        duration_ms = int((time.monotonic() - start_time) / 1000)
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_36(
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
        
        duration_ms = int((time.monotonic() + start_time) * 1000)
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_37(
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
        
        duration_ms = int((time.monotonic() - start_time) * 1001)
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_38(
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
        if hasattr(response, "choices") or response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_39(
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
        if hasattr(None, "choices") and response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_40(
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
        if hasattr(response, None) and response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_41(
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
        if hasattr("choices") and response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_42(
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
        if hasattr(response, ) and response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_43(
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
        if hasattr(response, "XXchoicesXX") and response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_44(
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
        if hasattr(response, "CHOICES") and response.choices:
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_45(
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
            content = None
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_46(
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
            content = response.choices[0].message.content and ""
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_47(
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
            content = response.choices[1].message.content or ""
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_48(
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
            content = response.choices[0].message.content or "XXXX"
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_49(
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
            content = None
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_50(
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
            content = str(None)
        
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_51(
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
        tokens = None
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_52(
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
        tokens = 1
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
    
    async def xǁLLMAdapterǁcomplete__mutmut_53(
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
        if hasattr(None, "usage"):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_54(
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
        if hasattr(response, None):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_55(
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
        if hasattr("usage"):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_56(
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
        if hasattr(response, ):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_57(
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
        if hasattr(response, "XXusageXX"):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_58(
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
        if hasattr(response, "USAGE"):
            tokens = response.usage.completion_tokens or 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_59(
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
            tokens = None
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_60(
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
            tokens = response.usage.completion_tokens and 0
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_61(
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
            tokens = response.usage.completion_tokens or 1
        
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_62(
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
            content=None,
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_63(
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
            model=None,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_64(
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
            provider=None,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_65(
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
            tokens=None,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_66(
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
            duration_ms=None,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_67(
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
            raw_response=None
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_68(
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
            model=self.model,
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_69(
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
            provider=self.provider,
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_70(
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
            tokens=tokens,
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_71(
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
            duration_ms=duration_ms,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_72(
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
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_73(
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
            )
    
    async def xǁLLMAdapterǁcomplete__mutmut_74(
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
            raw_response=response.model_dump() if hasattr(None, "model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_75(
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
            raw_response=response.model_dump() if hasattr(response, None) else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_76(
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
            raw_response=response.model_dump() if hasattr("model_dump") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_77(
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
            raw_response=response.model_dump() if hasattr(response, ) else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_78(
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
            raw_response=response.model_dump() if hasattr(response, "XXmodel_dumpXX") else {}
        )
    
    async def xǁLLMAdapterǁcomplete__mutmut_79(
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
            raw_response=response.model_dump() if hasattr(response, "MODEL_DUMP") else {}
        )
    
    xǁLLMAdapterǁcomplete__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLLMAdapterǁcomplete__mutmut_1': xǁLLMAdapterǁcomplete__mutmut_1, 
        'xǁLLMAdapterǁcomplete__mutmut_2': xǁLLMAdapterǁcomplete__mutmut_2, 
        'xǁLLMAdapterǁcomplete__mutmut_3': xǁLLMAdapterǁcomplete__mutmut_3, 
        'xǁLLMAdapterǁcomplete__mutmut_4': xǁLLMAdapterǁcomplete__mutmut_4, 
        'xǁLLMAdapterǁcomplete__mutmut_5': xǁLLMAdapterǁcomplete__mutmut_5, 
        'xǁLLMAdapterǁcomplete__mutmut_6': xǁLLMAdapterǁcomplete__mutmut_6, 
        'xǁLLMAdapterǁcomplete__mutmut_7': xǁLLMAdapterǁcomplete__mutmut_7, 
        'xǁLLMAdapterǁcomplete__mutmut_8': xǁLLMAdapterǁcomplete__mutmut_8, 
        'xǁLLMAdapterǁcomplete__mutmut_9': xǁLLMAdapterǁcomplete__mutmut_9, 
        'xǁLLMAdapterǁcomplete__mutmut_10': xǁLLMAdapterǁcomplete__mutmut_10, 
        'xǁLLMAdapterǁcomplete__mutmut_11': xǁLLMAdapterǁcomplete__mutmut_11, 
        'xǁLLMAdapterǁcomplete__mutmut_12': xǁLLMAdapterǁcomplete__mutmut_12, 
        'xǁLLMAdapterǁcomplete__mutmut_13': xǁLLMAdapterǁcomplete__mutmut_13, 
        'xǁLLMAdapterǁcomplete__mutmut_14': xǁLLMAdapterǁcomplete__mutmut_14, 
        'xǁLLMAdapterǁcomplete__mutmut_15': xǁLLMAdapterǁcomplete__mutmut_15, 
        'xǁLLMAdapterǁcomplete__mutmut_16': xǁLLMAdapterǁcomplete__mutmut_16, 
        'xǁLLMAdapterǁcomplete__mutmut_17': xǁLLMAdapterǁcomplete__mutmut_17, 
        'xǁLLMAdapterǁcomplete__mutmut_18': xǁLLMAdapterǁcomplete__mutmut_18, 
        'xǁLLMAdapterǁcomplete__mutmut_19': xǁLLMAdapterǁcomplete__mutmut_19, 
        'xǁLLMAdapterǁcomplete__mutmut_20': xǁLLMAdapterǁcomplete__mutmut_20, 
        'xǁLLMAdapterǁcomplete__mutmut_21': xǁLLMAdapterǁcomplete__mutmut_21, 
        'xǁLLMAdapterǁcomplete__mutmut_22': xǁLLMAdapterǁcomplete__mutmut_22, 
        'xǁLLMAdapterǁcomplete__mutmut_23': xǁLLMAdapterǁcomplete__mutmut_23, 
        'xǁLLMAdapterǁcomplete__mutmut_24': xǁLLMAdapterǁcomplete__mutmut_24, 
        'xǁLLMAdapterǁcomplete__mutmut_25': xǁLLMAdapterǁcomplete__mutmut_25, 
        'xǁLLMAdapterǁcomplete__mutmut_26': xǁLLMAdapterǁcomplete__mutmut_26, 
        'xǁLLMAdapterǁcomplete__mutmut_27': xǁLLMAdapterǁcomplete__mutmut_27, 
        'xǁLLMAdapterǁcomplete__mutmut_28': xǁLLMAdapterǁcomplete__mutmut_28, 
        'xǁLLMAdapterǁcomplete__mutmut_29': xǁLLMAdapterǁcomplete__mutmut_29, 
        'xǁLLMAdapterǁcomplete__mutmut_30': xǁLLMAdapterǁcomplete__mutmut_30, 
        'xǁLLMAdapterǁcomplete__mutmut_31': xǁLLMAdapterǁcomplete__mutmut_31, 
        'xǁLLMAdapterǁcomplete__mutmut_32': xǁLLMAdapterǁcomplete__mutmut_32, 
        'xǁLLMAdapterǁcomplete__mutmut_33': xǁLLMAdapterǁcomplete__mutmut_33, 
        'xǁLLMAdapterǁcomplete__mutmut_34': xǁLLMAdapterǁcomplete__mutmut_34, 
        'xǁLLMAdapterǁcomplete__mutmut_35': xǁLLMAdapterǁcomplete__mutmut_35, 
        'xǁLLMAdapterǁcomplete__mutmut_36': xǁLLMAdapterǁcomplete__mutmut_36, 
        'xǁLLMAdapterǁcomplete__mutmut_37': xǁLLMAdapterǁcomplete__mutmut_37, 
        'xǁLLMAdapterǁcomplete__mutmut_38': xǁLLMAdapterǁcomplete__mutmut_38, 
        'xǁLLMAdapterǁcomplete__mutmut_39': xǁLLMAdapterǁcomplete__mutmut_39, 
        'xǁLLMAdapterǁcomplete__mutmut_40': xǁLLMAdapterǁcomplete__mutmut_40, 
        'xǁLLMAdapterǁcomplete__mutmut_41': xǁLLMAdapterǁcomplete__mutmut_41, 
        'xǁLLMAdapterǁcomplete__mutmut_42': xǁLLMAdapterǁcomplete__mutmut_42, 
        'xǁLLMAdapterǁcomplete__mutmut_43': xǁLLMAdapterǁcomplete__mutmut_43, 
        'xǁLLMAdapterǁcomplete__mutmut_44': xǁLLMAdapterǁcomplete__mutmut_44, 
        'xǁLLMAdapterǁcomplete__mutmut_45': xǁLLMAdapterǁcomplete__mutmut_45, 
        'xǁLLMAdapterǁcomplete__mutmut_46': xǁLLMAdapterǁcomplete__mutmut_46, 
        'xǁLLMAdapterǁcomplete__mutmut_47': xǁLLMAdapterǁcomplete__mutmut_47, 
        'xǁLLMAdapterǁcomplete__mutmut_48': xǁLLMAdapterǁcomplete__mutmut_48, 
        'xǁLLMAdapterǁcomplete__mutmut_49': xǁLLMAdapterǁcomplete__mutmut_49, 
        'xǁLLMAdapterǁcomplete__mutmut_50': xǁLLMAdapterǁcomplete__mutmut_50, 
        'xǁLLMAdapterǁcomplete__mutmut_51': xǁLLMAdapterǁcomplete__mutmut_51, 
        'xǁLLMAdapterǁcomplete__mutmut_52': xǁLLMAdapterǁcomplete__mutmut_52, 
        'xǁLLMAdapterǁcomplete__mutmut_53': xǁLLMAdapterǁcomplete__mutmut_53, 
        'xǁLLMAdapterǁcomplete__mutmut_54': xǁLLMAdapterǁcomplete__mutmut_54, 
        'xǁLLMAdapterǁcomplete__mutmut_55': xǁLLMAdapterǁcomplete__mutmut_55, 
        'xǁLLMAdapterǁcomplete__mutmut_56': xǁLLMAdapterǁcomplete__mutmut_56, 
        'xǁLLMAdapterǁcomplete__mutmut_57': xǁLLMAdapterǁcomplete__mutmut_57, 
        'xǁLLMAdapterǁcomplete__mutmut_58': xǁLLMAdapterǁcomplete__mutmut_58, 
        'xǁLLMAdapterǁcomplete__mutmut_59': xǁLLMAdapterǁcomplete__mutmut_59, 
        'xǁLLMAdapterǁcomplete__mutmut_60': xǁLLMAdapterǁcomplete__mutmut_60, 
        'xǁLLMAdapterǁcomplete__mutmut_61': xǁLLMAdapterǁcomplete__mutmut_61, 
        'xǁLLMAdapterǁcomplete__mutmut_62': xǁLLMAdapterǁcomplete__mutmut_62, 
        'xǁLLMAdapterǁcomplete__mutmut_63': xǁLLMAdapterǁcomplete__mutmut_63, 
        'xǁLLMAdapterǁcomplete__mutmut_64': xǁLLMAdapterǁcomplete__mutmut_64, 
        'xǁLLMAdapterǁcomplete__mutmut_65': xǁLLMAdapterǁcomplete__mutmut_65, 
        'xǁLLMAdapterǁcomplete__mutmut_66': xǁLLMAdapterǁcomplete__mutmut_66, 
        'xǁLLMAdapterǁcomplete__mutmut_67': xǁLLMAdapterǁcomplete__mutmut_67, 
        'xǁLLMAdapterǁcomplete__mutmut_68': xǁLLMAdapterǁcomplete__mutmut_68, 
        'xǁLLMAdapterǁcomplete__mutmut_69': xǁLLMAdapterǁcomplete__mutmut_69, 
        'xǁLLMAdapterǁcomplete__mutmut_70': xǁLLMAdapterǁcomplete__mutmut_70, 
        'xǁLLMAdapterǁcomplete__mutmut_71': xǁLLMAdapterǁcomplete__mutmut_71, 
        'xǁLLMAdapterǁcomplete__mutmut_72': xǁLLMAdapterǁcomplete__mutmut_72, 
        'xǁLLMAdapterǁcomplete__mutmut_73': xǁLLMAdapterǁcomplete__mutmut_73, 
        'xǁLLMAdapterǁcomplete__mutmut_74': xǁLLMAdapterǁcomplete__mutmut_74, 
        'xǁLLMAdapterǁcomplete__mutmut_75': xǁLLMAdapterǁcomplete__mutmut_75, 
        'xǁLLMAdapterǁcomplete__mutmut_76': xǁLLMAdapterǁcomplete__mutmut_76, 
        'xǁLLMAdapterǁcomplete__mutmut_77': xǁLLMAdapterǁcomplete__mutmut_77, 
        'xǁLLMAdapterǁcomplete__mutmut_78': xǁLLMAdapterǁcomplete__mutmut_78, 
        'xǁLLMAdapterǁcomplete__mutmut_79': xǁLLMAdapterǁcomplete__mutmut_79
    }
    xǁLLMAdapterǁcomplete__mutmut_orig.__name__ = 'xǁLLMAdapterǁcomplete'
    
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
        args = [prompt, json_schema]# type: ignore
        kwargs = {**kwargs}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁLLMAdapterǁcomplete_with_json__mutmut_orig'), object.__getattribute__(self, 'xǁLLMAdapterǁcomplete_with_json__mutmut_mutants'), args, kwargs, self)
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_orig(
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
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_1(
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
        kwargs["response_format"] = None
        
        response = await self.complete(prompt, **kwargs)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_2(
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
        kwargs["XXresponse_formatXX"] = json_schema
        
        response = await self.complete(prompt, **kwargs)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_3(
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
        kwargs["RESPONSE_FORMAT"] = json_schema
        
        response = await self.complete(prompt, **kwargs)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_4(
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
        
        response = None
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_5(
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
        
        response = await self.complete(None, **kwargs)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_6(
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
        
        response = await self.complete(**kwargs)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_7(
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
        
        response = await self.complete(prompt, )
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response.content)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_8(
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
            parsed = None
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_9(
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
            parsed = json.loads(None)
            response.content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_10(
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
            response.content = None
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_11(
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
            response.content = json.dumps(None, indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_12(
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
            response.content = json.dumps(parsed, indent=None)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_13(
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
            response.content = json.dumps(indent=2)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_14(
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
            response.content = json.dumps(parsed, )
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    async def xǁLLMAdapterǁcomplete_with_json__mutmut_15(
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
            response.content = json.dumps(parsed, indent=3)
        except json.JSONDecodeError:
            pass  # Keep original content if not valid JSON
        
        return response
    
    xǁLLMAdapterǁcomplete_with_json__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁLLMAdapterǁcomplete_with_json__mutmut_1': xǁLLMAdapterǁcomplete_with_json__mutmut_1, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_2': xǁLLMAdapterǁcomplete_with_json__mutmut_2, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_3': xǁLLMAdapterǁcomplete_with_json__mutmut_3, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_4': xǁLLMAdapterǁcomplete_with_json__mutmut_4, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_5': xǁLLMAdapterǁcomplete_with_json__mutmut_5, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_6': xǁLLMAdapterǁcomplete_with_json__mutmut_6, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_7': xǁLLMAdapterǁcomplete_with_json__mutmut_7, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_8': xǁLLMAdapterǁcomplete_with_json__mutmut_8, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_9': xǁLLMAdapterǁcomplete_with_json__mutmut_9, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_10': xǁLLMAdapterǁcomplete_with_json__mutmut_10, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_11': xǁLLMAdapterǁcomplete_with_json__mutmut_11, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_12': xǁLLMAdapterǁcomplete_with_json__mutmut_12, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_13': xǁLLMAdapterǁcomplete_with_json__mutmut_13, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_14': xǁLLMAdapterǁcomplete_with_json__mutmut_14, 
        'xǁLLMAdapterǁcomplete_with_json__mutmut_15': xǁLLMAdapterǁcomplete_with_json__mutmut_15
    }
    xǁLLMAdapterǁcomplete_with_json__mutmut_orig.__name__ = 'xǁLLMAdapterǁcomplete_with_json'


def inject_skill(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
    args = [prompt, skill_path]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_inject_skill__mutmut_orig, x_inject_skill__mutmut_mutants, args, kwargs, None)


def x_inject_skill__mutmut_orig(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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


def x_inject_skill__mutmut_1(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
    """Inject skill content into prompt.
    
    Args:
        prompt: User prompt
        skill_path: Path to skill file (None = CONTROL)
        
    Returns:
        Tuple of (final_prompt, system_prompt)
    """
    from pathlib import Path
    
    if skill_path is not None:
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


def x_inject_skill__mutmut_2(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    skill_file = None
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


def x_inject_skill__mutmut_3(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    skill_file = Path(None)
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


def x_inject_skill__mutmut_4(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    if skill_file.exists():
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


def x_inject_skill__mutmut_5(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
        raise FileNotFoundError(None)
    
    skill_content = skill_file.read_text(encoding="utf-8")
    
    # Inject as system prompt
    system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""
    
    return prompt, system_prompt


def x_inject_skill__mutmut_6(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    
    skill_content = None
    
    # Inject as system prompt
    system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""
    
    return prompt, system_prompt


def x_inject_skill__mutmut_7(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    
    skill_content = skill_file.read_text(encoding=None)
    
    # Inject as system prompt
    system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""
    
    return prompt, system_prompt


def x_inject_skill__mutmut_8(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    
    skill_content = skill_file.read_text(encoding="XXutf-8XX")
    
    # Inject as system prompt
    system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""
    
    return prompt, system_prompt


def x_inject_skill__mutmut_9(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    
    skill_content = skill_file.read_text(encoding="UTF-8")
    
    # Inject as system prompt
    system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""
    
    return prompt, system_prompt


def x_inject_skill__mutmut_10(prompt: str, skill_path: str | None) -> tuple[str, str | None]:
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
    system_prompt = None
    
    return prompt, system_prompt

x_inject_skill__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_inject_skill__mutmut_1': x_inject_skill__mutmut_1, 
    'x_inject_skill__mutmut_2': x_inject_skill__mutmut_2, 
    'x_inject_skill__mutmut_3': x_inject_skill__mutmut_3, 
    'x_inject_skill__mutmut_4': x_inject_skill__mutmut_4, 
    'x_inject_skill__mutmut_5': x_inject_skill__mutmut_5, 
    'x_inject_skill__mutmut_6': x_inject_skill__mutmut_6, 
    'x_inject_skill__mutmut_7': x_inject_skill__mutmut_7, 
    'x_inject_skill__mutmut_8': x_inject_skill__mutmut_8, 
    'x_inject_skill__mutmut_9': x_inject_skill__mutmut_9, 
    'x_inject_skill__mutmut_10': x_inject_skill__mutmut_10
}
x_inject_skill__mutmut_orig.__name__ = 'x_inject_skill'
