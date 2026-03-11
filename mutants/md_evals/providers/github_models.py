"""GitHub Models provider for md-evals using Azure AI Inference SDK."""

import os
import time
import asyncio
import logging
from typing import Any, Optional
from dataclasses import dataclass

from md_evals.models import LLMResponse

logger = logging.getLogger(__name__)
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

# ============== Custom Exception Hierarchy ==============


class GitHubModelsError(Exception):
    """Base exception for GitHub Models provider."""
    pass


class AuthenticationError(GitHubModelsError):
    """Raised when GITHUB_TOKEN is missing or invalid."""
    pass


class ModelNotSupportedError(GitHubModelsError):
    """Raised when an unsupported model is requested."""
    pass


class RateLimitError(GitHubModelsError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        args = [message, retry_after]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRateLimitErrorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRateLimitErrorǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁRateLimitErrorǁ__init____mutmut_orig(self, message: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message)
    
    def xǁRateLimitErrorǁ__init____mutmut_1(self, message: str, retry_after: Optional[int] = None):
        self.retry_after = None
        super().__init__(message)
    
    def xǁRateLimitErrorǁ__init____mutmut_2(self, message: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(None)
    
    xǁRateLimitErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRateLimitErrorǁ__init____mutmut_1': xǁRateLimitErrorǁ__init____mutmut_1, 
        'xǁRateLimitErrorǁ__init____mutmut_2': xǁRateLimitErrorǁ__init____mutmut_2
    }
    xǁRateLimitErrorǁ__init____mutmut_orig.__name__ = 'xǁRateLimitErrorǁ__init__'


class ContextWindowError(GitHubModelsError):
    """Raised when prompt exceeds model's context window."""
    pass


class StreamingError(GitHubModelsError):
    """Raised when streaming is interrupted."""
    pass


class APIError(GitHubModelsError):
    """Raised for generic API errors."""
    pass


# ============== Model Metadata ==============


@dataclass
class ModelMetadata:
    """Metadata for a supported model."""
    name: str
    provider: str
    context_window: int
    temperature_range: tuple[float, float]
    rate_limit: str
    cost: str
    status: str
    notes: Optional[str] = None


# ============== GitHub Models Provider ==============


class GitHubModelsProvider:
    """
    GitHub Models provider using Azure AI Inference SDK.
    
    Provides async completion interface for models available via GitHub Models
    (Claude 3.5 Sonnet, GPT-4o, DeepSeek-R1, Grok-3).
    """
    
    # Supported models with metadata
    SUPPORTED_MODELS = {
        "claude-3.5-sonnet": ModelMetadata(
            name="Claude 3.5 Sonnet",
            provider="Anthropic",
            context_window=200000,
            temperature_range=(0.0, 2.0),
            rate_limit="15 req/min (free tier)",
            cost="free (free tier)",
            status="supported",
            notes="Recommended for complex reasoning and analysis"
        ),
        "gpt-4o": ModelMetadata(
            name="GPT-4 Optimized",
            provider="OpenAI",
            context_window=128000,
            temperature_range=(0.0, 2.0),
            rate_limit="15 req/min (free tier)",
            cost="free (free tier)",
            status="supported",
            notes="Strong general-purpose capability"
        ),
        "deepseek-r1": ModelMetadata(
            name="DeepSeek R1",
            provider="DeepSeek",
            context_window=64000,
            temperature_range=(0.0, 1.0),
            rate_limit="15 req/min (free tier)",
            cost="free (free tier)",
            status="supported",
            notes="Lower cost, good for coding tasks"
        ),
        "grok-3": ModelMetadata(
            name="Grok-3",
            provider="xAI",
            context_window=128000,
            temperature_range=(0.0, 2.0),
            rate_limit="15 req/min (free tier)",
            cost="free (free tier)",
            status="supported",
            notes="Latest reasoning model from xAI"
        ),
    }
    
    def __init__(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        args = [model_name, github_token, timeout_seconds, max_retries]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁGitHubModelsProviderǁ__init____mutmut_orig(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_1(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 61,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_2(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 4,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_3(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_4(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = None
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_5(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(None)
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_6(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = "XX, XX".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_7(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                None
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_8(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = None
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_9(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = None
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_10(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = None
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_11(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = None
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_12(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(None)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_13(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = None
        
        logger.info(f"GitHubModelsProvider initialized with model: {model_name}")
    
    def xǁGitHubModelsProviderǁ__init____mutmut_14(
        self,
        model_name: str,
        github_token: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Models provider.
        
        Args:
            model_name: One of 'claude-3.5-sonnet', 'gpt-4o', 'deepseek-r1', 'grok-3'
            github_token: GitHub PAT token (defaults to GITHUB_TOKEN env var)
            timeout_seconds: Request timeout in seconds
            max_retries: Retry count on transient errors
            
        Raises:
            AuthenticationError: Token missing or invalid
            ModelNotSupportedError: Unknown model name
        """
        # Validate model name
        if model_name not in self.SUPPORTED_MODELS:
            available = ", ".join(self.SUPPORTED_MODELS.keys())
            raise ModelNotSupportedError(
                f"Model '{model_name}' is not supported. "
                f"Available models: {available}"
            )
        
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Load GitHub token
        self.github_token = self._load_github_token(github_token)
        
        # Initialize Azure SDK client
        self._client = self._initialize_client()
        
        logger.info(None)
    
    xǁGitHubModelsProviderǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁ__init____mutmut_1': xǁGitHubModelsProviderǁ__init____mutmut_1, 
        'xǁGitHubModelsProviderǁ__init____mutmut_2': xǁGitHubModelsProviderǁ__init____mutmut_2, 
        'xǁGitHubModelsProviderǁ__init____mutmut_3': xǁGitHubModelsProviderǁ__init____mutmut_3, 
        'xǁGitHubModelsProviderǁ__init____mutmut_4': xǁGitHubModelsProviderǁ__init____mutmut_4, 
        'xǁGitHubModelsProviderǁ__init____mutmut_5': xǁGitHubModelsProviderǁ__init____mutmut_5, 
        'xǁGitHubModelsProviderǁ__init____mutmut_6': xǁGitHubModelsProviderǁ__init____mutmut_6, 
        'xǁGitHubModelsProviderǁ__init____mutmut_7': xǁGitHubModelsProviderǁ__init____mutmut_7, 
        'xǁGitHubModelsProviderǁ__init____mutmut_8': xǁGitHubModelsProviderǁ__init____mutmut_8, 
        'xǁGitHubModelsProviderǁ__init____mutmut_9': xǁGitHubModelsProviderǁ__init____mutmut_9, 
        'xǁGitHubModelsProviderǁ__init____mutmut_10': xǁGitHubModelsProviderǁ__init____mutmut_10, 
        'xǁGitHubModelsProviderǁ__init____mutmut_11': xǁGitHubModelsProviderǁ__init____mutmut_11, 
        'xǁGitHubModelsProviderǁ__init____mutmut_12': xǁGitHubModelsProviderǁ__init____mutmut_12, 
        'xǁGitHubModelsProviderǁ__init____mutmut_13': xǁGitHubModelsProviderǁ__init____mutmut_13, 
        'xǁGitHubModelsProviderǁ__init____mutmut_14': xǁGitHubModelsProviderǁ__init____mutmut_14
    }
    xǁGitHubModelsProviderǁ__init____mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁ__init__'
    
    def _load_github_token(self, token: Optional[str] = None) -> str:
        args = [token]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_load_github_token__mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_load_github_token__mutmut_mutants'), args, kwargs, self)
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_orig(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_1(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = None
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_2(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = None
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_3(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv(None)
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_4(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("XXGITHUB_TOKENXX")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_5(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("github_token")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_6(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_7(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                None
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_8(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "XXGITHUB_TOKEN environment variable not set or invalid. XX"
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_9(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "github_token environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_10(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN ENVIRONMENT VARIABLE NOT SET OR INVALID. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_11(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "XXPlease set your GitHub PAT token:\nXX"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_12(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "please set your github pat token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_13(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "PLEASE SET YOUR GITHUB PAT TOKEN:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_14(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "XX  export GITHUB_TOKEN=github_pat_... \nXX"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_15(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export github_token=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_16(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  EXPORT GITHUB_TOKEN=GITHUB_PAT_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_17(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "XXOr update your .env file with: GITHUB_TOKEN=github_pat_...\nXX"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_18(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "or update your .env file with: github_token=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_19(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "OR UPDATE YOUR .ENV FILE WITH: GITHUB_TOKEN=GITHUB_PAT_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_20(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "XXGenerate a token at: https://github.com/settings/tokensXX"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_21(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_22(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "GENERATE A TOKEN AT: HTTPS://GITHUB.COM/SETTINGS/TOKENS"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_23(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) and len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_24(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_25(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) <= 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_26(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 11:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_27(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                None
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_28(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "XXGITHUB_TOKEN appears to be invalid or malformed. XX"
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_29(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "github_token appears to be invalid or malformed. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_30(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN APPEARS TO BE INVALID OR MALFORMED. "
                "Check your GITHUB_TOKEN in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_31(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "XXCheck your GITHUB_TOKEN in ~/.bash_profile or .env fileXX"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_32(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "check your github_token in ~/.bash_profile or .env file"
            )
        
        return github_token
    
    def xǁGitHubModelsProviderǁ_load_github_token__mutmut_33(self, token: Optional[str] = None) -> str:
        """
        Load and validate GitHub token.
        
        Args:
            token: Optional token to use (overrides env var)
            
        Returns:
            Validated GitHub token
            
        Raises:
            AuthenticationError: Token missing or invalid
        """
        # Use provided token or load from environment
        if token:
            github_token = token
        else:
            github_token = os.getenv("GITHUB_TOKEN")
        
        # Validate token
        if not github_token:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable not set or invalid. "
                "Please set your GitHub PAT token:\n"
                "  export GITHUB_TOKEN=github_pat_... \n"
                "Or update your .env file with: GITHUB_TOKEN=github_pat_...\n"
                "Generate a token at: https://github.com/settings/tokens"
            )
        
        # Validate token format (GitHub PAT should start with github_pat_)
        if not isinstance(github_token, str) or len(github_token) < 10:
            raise AuthenticationError(
                "GITHUB_TOKEN appears to be invalid or malformed. "
                "CHECK YOUR GITHUB_TOKEN IN ~/.BASH_PROFILE OR .ENV FILE"
            )
        
        return github_token
    
    xǁGitHubModelsProviderǁ_load_github_token__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁ_load_github_token__mutmut_1': xǁGitHubModelsProviderǁ_load_github_token__mutmut_1, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_2': xǁGitHubModelsProviderǁ_load_github_token__mutmut_2, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_3': xǁGitHubModelsProviderǁ_load_github_token__mutmut_3, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_4': xǁGitHubModelsProviderǁ_load_github_token__mutmut_4, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_5': xǁGitHubModelsProviderǁ_load_github_token__mutmut_5, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_6': xǁGitHubModelsProviderǁ_load_github_token__mutmut_6, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_7': xǁGitHubModelsProviderǁ_load_github_token__mutmut_7, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_8': xǁGitHubModelsProviderǁ_load_github_token__mutmut_8, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_9': xǁGitHubModelsProviderǁ_load_github_token__mutmut_9, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_10': xǁGitHubModelsProviderǁ_load_github_token__mutmut_10, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_11': xǁGitHubModelsProviderǁ_load_github_token__mutmut_11, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_12': xǁGitHubModelsProviderǁ_load_github_token__mutmut_12, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_13': xǁGitHubModelsProviderǁ_load_github_token__mutmut_13, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_14': xǁGitHubModelsProviderǁ_load_github_token__mutmut_14, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_15': xǁGitHubModelsProviderǁ_load_github_token__mutmut_15, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_16': xǁGitHubModelsProviderǁ_load_github_token__mutmut_16, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_17': xǁGitHubModelsProviderǁ_load_github_token__mutmut_17, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_18': xǁGitHubModelsProviderǁ_load_github_token__mutmut_18, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_19': xǁGitHubModelsProviderǁ_load_github_token__mutmut_19, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_20': xǁGitHubModelsProviderǁ_load_github_token__mutmut_20, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_21': xǁGitHubModelsProviderǁ_load_github_token__mutmut_21, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_22': xǁGitHubModelsProviderǁ_load_github_token__mutmut_22, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_23': xǁGitHubModelsProviderǁ_load_github_token__mutmut_23, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_24': xǁGitHubModelsProviderǁ_load_github_token__mutmut_24, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_25': xǁGitHubModelsProviderǁ_load_github_token__mutmut_25, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_26': xǁGitHubModelsProviderǁ_load_github_token__mutmut_26, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_27': xǁGitHubModelsProviderǁ_load_github_token__mutmut_27, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_28': xǁGitHubModelsProviderǁ_load_github_token__mutmut_28, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_29': xǁGitHubModelsProviderǁ_load_github_token__mutmut_29, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_30': xǁGitHubModelsProviderǁ_load_github_token__mutmut_30, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_31': xǁGitHubModelsProviderǁ_load_github_token__mutmut_31, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_32': xǁGitHubModelsProviderǁ_load_github_token__mutmut_32, 
        'xǁGitHubModelsProviderǁ_load_github_token__mutmut_33': xǁGitHubModelsProviderǁ_load_github_token__mutmut_33
    }
    xǁGitHubModelsProviderǁ_load_github_token__mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁ_load_github_token'
    
    def _initialize_client(self):
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_initialize_client__mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_initialize_client__mutmut_mutants'), args, kwargs, self)
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_orig(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_1(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = None
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_2(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint=None,
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_3(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=None,
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_4(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_5(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_6(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="XXhttps://models.inference.ai.azure.comXX",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_7(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="HTTPS://MODELS.INFERENCE.AI.AZURE.COM",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_8(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(None),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_9(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                None
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_10(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "XXInstall with: pip install azure-ai-inference>=1.0.0XX"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_11(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_12(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "INSTALL WITH: PIP INSTALL AZURE-AI-INFERENCE>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(f"Failed to initialize Azure client: {e}") from e
    
    def xǁGitHubModelsProviderǁ_initialize_client__mutmut_13(self):
        """
        Initialize Azure AI Inference client.
        
        Returns:
            Initialized ChatCompletionsClient
            
        Raises:
            AuthenticationError: If client initialization fails
        """
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            
            client = ChatCompletionsClient(
                endpoint="https://models.inference.ai.azure.com",
                credential=AzureKeyCredential(self.github_token),
            )
            
            return client
        except ImportError as e:
            raise GitHubModelsError(
                f"Failed to import Azure AI Inference SDK: {e}. "
                "Install with: pip install azure-ai-inference>=1.0.0"
            ) from e
        except Exception as e:
            raise GitHubModelsError(None) from e
    
    xǁGitHubModelsProviderǁ_initialize_client__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁ_initialize_client__mutmut_1': xǁGitHubModelsProviderǁ_initialize_client__mutmut_1, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_2': xǁGitHubModelsProviderǁ_initialize_client__mutmut_2, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_3': xǁGitHubModelsProviderǁ_initialize_client__mutmut_3, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_4': xǁGitHubModelsProviderǁ_initialize_client__mutmut_4, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_5': xǁGitHubModelsProviderǁ_initialize_client__mutmut_5, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_6': xǁGitHubModelsProviderǁ_initialize_client__mutmut_6, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_7': xǁGitHubModelsProviderǁ_initialize_client__mutmut_7, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_8': xǁGitHubModelsProviderǁ_initialize_client__mutmut_8, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_9': xǁGitHubModelsProviderǁ_initialize_client__mutmut_9, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_10': xǁGitHubModelsProviderǁ_initialize_client__mutmut_10, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_11': xǁGitHubModelsProviderǁ_initialize_client__mutmut_11, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_12': xǁGitHubModelsProviderǁ_initialize_client__mutmut_12, 
        'xǁGitHubModelsProviderǁ_initialize_client__mutmut_13': xǁGitHubModelsProviderǁ_initialize_client__mutmut_13
    }
    xǁGitHubModelsProviderǁ_initialize_client__mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁ_initialize_client'
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        args = [prompt, system_prompt, temperature, max_tokens]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁcomplete__mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁcomplete__mutmut_mutants'), args, kwargs, self)
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_orig(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_1(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = None
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_2(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = None
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_3(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append(None)
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_4(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"XXroleXX": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_5(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"ROLE": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_6(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "XXsystemXX", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_7(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "SYSTEM", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_8(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "XXcontentXX": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_9(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "CONTENT": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_10(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append(None)
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_11(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"XXroleXX": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_12(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"ROLE": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_13(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "XXuserXX", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_14(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "USER", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_15(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "XXcontentXX": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_16(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "CONTENT": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_17(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is not None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_18(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = None  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_19(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 1.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_20(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is not None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_21(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = None  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_22(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2049  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_23(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = None
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_24(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = "XXXX"
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_25(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = None
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_26(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 1
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_27(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = None
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_28(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=None,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_29(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=None,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_30(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=None,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_31(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_32(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_33(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_34(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = None
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_35(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(None)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_36(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = None
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_37(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).upper()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_38(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(None).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_39(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str and "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_40(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "XXrateXX" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_41(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "RATE" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_42(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" not in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_43(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "XX429XX" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_44(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" not in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_45(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    None,
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_46(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=None
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_47(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_48(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_49(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "XXGitHub Models rate limit exceeded. Free tier: 15 requests/min. XX"
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_50(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "github models rate limit exceeded. free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_51(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GITHUB MODELS RATE LIMIT EXCEEDED. FREE TIER: 15 REQUESTS/MIN. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_52(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "XXConsider caching responses or upgrading to paid tier.XX",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_53(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_54(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "CONSIDER CACHING RESPONSES OR UPGRADING TO PAID TIER.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_55(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=61
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_56(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str and "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_57(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "XXcontextXX" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_58(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "CONTEXT" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_59(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" not in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_60(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "XXtoken limitXX" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_61(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "TOKEN LIMIT" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_62(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" not in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_63(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    None
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_64(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "XXTry using a model with larger context or shorter prompts.XX"
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_65(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_66(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "TRY USING A MODEL WITH LARGER CONTEXT OR SHORTER PROMPTS."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_67(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str and "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_68(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "XXtimeoutXX" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_69(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "TIMEOUT" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_70(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" not in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_71(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "XXconnectXX" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_72(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "CONNECT" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_73(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" not in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_74(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    None
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_75(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str and "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_76(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "XXauthenticationXX" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_77(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "AUTHENTICATION" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_78(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" not in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_79(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "XX401XX" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_80(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" not in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_81(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    None
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_82(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(None) from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_83(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = None
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_84(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int(None)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_85(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) / 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_86(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() + start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_87(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1001)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_88(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=None,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_89(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=None,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_90(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider=None,
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_91(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=None,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_92(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=None,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_93(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response=None
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_94(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_95(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_96(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_97(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_98(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_99(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_100(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="XXgithub-modelsXX",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_101(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="GITHUB-MODELS",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_102(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"XXmodelXX": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_103(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"MODEL": self.model_name, "provider": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_104(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "XXproviderXX": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_105(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "PROVIDER": "github-models"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_106(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "XXgithub-modelsXX"}
        )
    
    async def xǁGitHubModelsProviderǁcomplete__mutmut_107(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Complete a prompt using GitHub Models.
        
        Args:
            prompt: User message
            system_prompt: Optional system message
            temperature: 0.0–2.0 (default: model-specific)
            max_tokens: Max response length
            
        Returns:
            LLMResponse with content, tokens, duration_ms, model, provider
            
        Raises:
            RateLimitError: API rate limit exceeded
            ContextWindowError: Prompt exceeds model context window
            StreamingError: Network disconnect during streaming
            APIError: Generic API error
        """
        import time
        
        start_time = time.monotonic()
        
        # Build message list
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Set defaults for model-specific parameters
        if temperature is None:
            temperature = 0.7  # Default temperature
        if max_tokens is None:
            max_tokens = 2048  # Default max tokens
        
        try:
            # Call Azure SDK with streaming
            response_content = ""
            token_count = 0
            
            # Make the request
            response = await self._stream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Handle streaming response
            response_content, token_count = await self._handle_stream(response)
            
        except Exception as e:
            # Handle specific error types
            error_str = str(e).lower()
            
            if "rate" in error_str or "429" in error_str:
                raise RateLimitError(
                    "GitHub Models rate limit exceeded. Free tier: 15 requests/min. "
                    "Consider caching responses or upgrading to paid tier.",
                    retry_after=60
                ) from e
            elif "context" in error_str or "token limit" in error_str:
                raise ContextWindowError(
                    f"Prompt exceeds {self.model_name}'s context window. "
                    "Try using a model with larger context or shorter prompts."
                ) from e
            elif "timeout" in error_str or "connect" in error_str:
                raise StreamingError(
                    f"Network error during streaming: {e}"
                ) from e
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(
                    f"Authentication failed. Check your GITHUB_TOKEN: {e}"
                ) from e
            else:
                raise APIError(f"GitHub Models API error: {e}") from e
        
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        return LLMResponse(
            content=response_content,
            model=self.model_name,
            provider="github-models",
            tokens=token_count,
            duration_ms=duration_ms,
            raw_response={"model": self.model_name, "provider": "GITHUB-MODELS"}
        )
    
    xǁGitHubModelsProviderǁcomplete__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁcomplete__mutmut_1': xǁGitHubModelsProviderǁcomplete__mutmut_1, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_2': xǁGitHubModelsProviderǁcomplete__mutmut_2, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_3': xǁGitHubModelsProviderǁcomplete__mutmut_3, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_4': xǁGitHubModelsProviderǁcomplete__mutmut_4, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_5': xǁGitHubModelsProviderǁcomplete__mutmut_5, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_6': xǁGitHubModelsProviderǁcomplete__mutmut_6, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_7': xǁGitHubModelsProviderǁcomplete__mutmut_7, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_8': xǁGitHubModelsProviderǁcomplete__mutmut_8, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_9': xǁGitHubModelsProviderǁcomplete__mutmut_9, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_10': xǁGitHubModelsProviderǁcomplete__mutmut_10, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_11': xǁGitHubModelsProviderǁcomplete__mutmut_11, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_12': xǁGitHubModelsProviderǁcomplete__mutmut_12, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_13': xǁGitHubModelsProviderǁcomplete__mutmut_13, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_14': xǁGitHubModelsProviderǁcomplete__mutmut_14, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_15': xǁGitHubModelsProviderǁcomplete__mutmut_15, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_16': xǁGitHubModelsProviderǁcomplete__mutmut_16, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_17': xǁGitHubModelsProviderǁcomplete__mutmut_17, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_18': xǁGitHubModelsProviderǁcomplete__mutmut_18, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_19': xǁGitHubModelsProviderǁcomplete__mutmut_19, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_20': xǁGitHubModelsProviderǁcomplete__mutmut_20, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_21': xǁGitHubModelsProviderǁcomplete__mutmut_21, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_22': xǁGitHubModelsProviderǁcomplete__mutmut_22, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_23': xǁGitHubModelsProviderǁcomplete__mutmut_23, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_24': xǁGitHubModelsProviderǁcomplete__mutmut_24, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_25': xǁGitHubModelsProviderǁcomplete__mutmut_25, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_26': xǁGitHubModelsProviderǁcomplete__mutmut_26, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_27': xǁGitHubModelsProviderǁcomplete__mutmut_27, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_28': xǁGitHubModelsProviderǁcomplete__mutmut_28, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_29': xǁGitHubModelsProviderǁcomplete__mutmut_29, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_30': xǁGitHubModelsProviderǁcomplete__mutmut_30, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_31': xǁGitHubModelsProviderǁcomplete__mutmut_31, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_32': xǁGitHubModelsProviderǁcomplete__mutmut_32, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_33': xǁGitHubModelsProviderǁcomplete__mutmut_33, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_34': xǁGitHubModelsProviderǁcomplete__mutmut_34, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_35': xǁGitHubModelsProviderǁcomplete__mutmut_35, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_36': xǁGitHubModelsProviderǁcomplete__mutmut_36, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_37': xǁGitHubModelsProviderǁcomplete__mutmut_37, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_38': xǁGitHubModelsProviderǁcomplete__mutmut_38, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_39': xǁGitHubModelsProviderǁcomplete__mutmut_39, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_40': xǁGitHubModelsProviderǁcomplete__mutmut_40, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_41': xǁGitHubModelsProviderǁcomplete__mutmut_41, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_42': xǁGitHubModelsProviderǁcomplete__mutmut_42, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_43': xǁGitHubModelsProviderǁcomplete__mutmut_43, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_44': xǁGitHubModelsProviderǁcomplete__mutmut_44, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_45': xǁGitHubModelsProviderǁcomplete__mutmut_45, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_46': xǁGitHubModelsProviderǁcomplete__mutmut_46, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_47': xǁGitHubModelsProviderǁcomplete__mutmut_47, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_48': xǁGitHubModelsProviderǁcomplete__mutmut_48, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_49': xǁGitHubModelsProviderǁcomplete__mutmut_49, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_50': xǁGitHubModelsProviderǁcomplete__mutmut_50, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_51': xǁGitHubModelsProviderǁcomplete__mutmut_51, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_52': xǁGitHubModelsProviderǁcomplete__mutmut_52, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_53': xǁGitHubModelsProviderǁcomplete__mutmut_53, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_54': xǁGitHubModelsProviderǁcomplete__mutmut_54, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_55': xǁGitHubModelsProviderǁcomplete__mutmut_55, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_56': xǁGitHubModelsProviderǁcomplete__mutmut_56, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_57': xǁGitHubModelsProviderǁcomplete__mutmut_57, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_58': xǁGitHubModelsProviderǁcomplete__mutmut_58, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_59': xǁGitHubModelsProviderǁcomplete__mutmut_59, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_60': xǁGitHubModelsProviderǁcomplete__mutmut_60, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_61': xǁGitHubModelsProviderǁcomplete__mutmut_61, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_62': xǁGitHubModelsProviderǁcomplete__mutmut_62, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_63': xǁGitHubModelsProviderǁcomplete__mutmut_63, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_64': xǁGitHubModelsProviderǁcomplete__mutmut_64, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_65': xǁGitHubModelsProviderǁcomplete__mutmut_65, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_66': xǁGitHubModelsProviderǁcomplete__mutmut_66, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_67': xǁGitHubModelsProviderǁcomplete__mutmut_67, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_68': xǁGitHubModelsProviderǁcomplete__mutmut_68, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_69': xǁGitHubModelsProviderǁcomplete__mutmut_69, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_70': xǁGitHubModelsProviderǁcomplete__mutmut_70, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_71': xǁGitHubModelsProviderǁcomplete__mutmut_71, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_72': xǁGitHubModelsProviderǁcomplete__mutmut_72, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_73': xǁGitHubModelsProviderǁcomplete__mutmut_73, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_74': xǁGitHubModelsProviderǁcomplete__mutmut_74, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_75': xǁGitHubModelsProviderǁcomplete__mutmut_75, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_76': xǁGitHubModelsProviderǁcomplete__mutmut_76, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_77': xǁGitHubModelsProviderǁcomplete__mutmut_77, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_78': xǁGitHubModelsProviderǁcomplete__mutmut_78, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_79': xǁGitHubModelsProviderǁcomplete__mutmut_79, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_80': xǁGitHubModelsProviderǁcomplete__mutmut_80, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_81': xǁGitHubModelsProviderǁcomplete__mutmut_81, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_82': xǁGitHubModelsProviderǁcomplete__mutmut_82, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_83': xǁGitHubModelsProviderǁcomplete__mutmut_83, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_84': xǁGitHubModelsProviderǁcomplete__mutmut_84, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_85': xǁGitHubModelsProviderǁcomplete__mutmut_85, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_86': xǁGitHubModelsProviderǁcomplete__mutmut_86, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_87': xǁGitHubModelsProviderǁcomplete__mutmut_87, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_88': xǁGitHubModelsProviderǁcomplete__mutmut_88, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_89': xǁGitHubModelsProviderǁcomplete__mutmut_89, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_90': xǁGitHubModelsProviderǁcomplete__mutmut_90, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_91': xǁGitHubModelsProviderǁcomplete__mutmut_91, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_92': xǁGitHubModelsProviderǁcomplete__mutmut_92, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_93': xǁGitHubModelsProviderǁcomplete__mutmut_93, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_94': xǁGitHubModelsProviderǁcomplete__mutmut_94, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_95': xǁGitHubModelsProviderǁcomplete__mutmut_95, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_96': xǁGitHubModelsProviderǁcomplete__mutmut_96, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_97': xǁGitHubModelsProviderǁcomplete__mutmut_97, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_98': xǁGitHubModelsProviderǁcomplete__mutmut_98, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_99': xǁGitHubModelsProviderǁcomplete__mutmut_99, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_100': xǁGitHubModelsProviderǁcomplete__mutmut_100, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_101': xǁGitHubModelsProviderǁcomplete__mutmut_101, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_102': xǁGitHubModelsProviderǁcomplete__mutmut_102, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_103': xǁGitHubModelsProviderǁcomplete__mutmut_103, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_104': xǁGitHubModelsProviderǁcomplete__mutmut_104, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_105': xǁGitHubModelsProviderǁcomplete__mutmut_105, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_106': xǁGitHubModelsProviderǁcomplete__mutmut_106, 
        'xǁGitHubModelsProviderǁcomplete__mutmut_107': xǁGitHubModelsProviderǁcomplete__mutmut_107
    }
    xǁGitHubModelsProviderǁcomplete__mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁcomplete'
    
    async def _stream_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        args = [messages, temperature, max_tokens]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_stream_completion__mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_stream_completion__mutmut_mutants'), args, kwargs, self)
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_orig(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_1(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = None
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_2(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=None,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_3(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=None,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_4(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=None,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_5(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=None,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_6(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_7(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_8(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_9(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                )
        
        response = await loop.run_in_executor(None, make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_10(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = None
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_11(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, None)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_12(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(make_request)
        return response
    
    async def xǁGitHubModelsProviderǁ_stream_completion__mutmut_13(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """
        Stream completion from Azure SDK.
        
        Args:
            messages: List of message dicts
            temperature: Temperature setting
            max_tokens: Max tokens in response
            
        Returns:
            Streaming response object
        """
        # Run the blocking SDK call in a thread pool
        loop = asyncio.get_event_loop()
        
        def make_request():
            return self._client.complete(
                messages=messages,
                model=self.model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        response = await loop.run_in_executor(None, )
        return response
    
    xǁGitHubModelsProviderǁ_stream_completion__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁ_stream_completion__mutmut_1': xǁGitHubModelsProviderǁ_stream_completion__mutmut_1, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_2': xǁGitHubModelsProviderǁ_stream_completion__mutmut_2, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_3': xǁGitHubModelsProviderǁ_stream_completion__mutmut_3, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_4': xǁGitHubModelsProviderǁ_stream_completion__mutmut_4, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_5': xǁGitHubModelsProviderǁ_stream_completion__mutmut_5, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_6': xǁGitHubModelsProviderǁ_stream_completion__mutmut_6, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_7': xǁGitHubModelsProviderǁ_stream_completion__mutmut_7, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_8': xǁGitHubModelsProviderǁ_stream_completion__mutmut_8, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_9': xǁGitHubModelsProviderǁ_stream_completion__mutmut_9, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_10': xǁGitHubModelsProviderǁ_stream_completion__mutmut_10, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_11': xǁGitHubModelsProviderǁ_stream_completion__mutmut_11, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_12': xǁGitHubModelsProviderǁ_stream_completion__mutmut_12, 
        'xǁGitHubModelsProviderǁ_stream_completion__mutmut_13': xǁGitHubModelsProviderǁ_stream_completion__mutmut_13
    }
    xǁGitHubModelsProviderǁ_stream_completion__mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁ_stream_completion'
    
    async def _handle_stream(self, response) -> tuple[str, int]:
        args = [response]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_handle_stream__mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁ_handle_stream__mutmut_mutants'), args, kwargs, self)
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_orig(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_1(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') or response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_2(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(None, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_3(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, None) and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_4(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr('choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_5(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, ) and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_6(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'XXchoicesXX') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_7(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'CHOICES') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_8(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = None
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_9(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[1]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_10(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') or hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_11(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(None, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_12(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, None) and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_13(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr('message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_14(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, ) and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_15(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'XXmessageXX') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_16(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'MESSAGE') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_17(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(None, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_18(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, None):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_19(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr('content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_20(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, ):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_21(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'XXcontentXX'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_22(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'CONTENT'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_23(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = None
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_24(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content and ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_25(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or "XXXX"
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_26(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = None
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_27(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = "XXXX"
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_28(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = None
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_29(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 1
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_30(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') or response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_31(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(None, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_32(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, None) and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_33(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr('usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_34(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, ) and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_35(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'XXusageXX') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_36(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'USAGE') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_37(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(None, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_38(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, None):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_39(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr('completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_40(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, ):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_41(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'XXcompletion_tokensXX'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_42(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'COMPLETION_TOKENS'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_43(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = None
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_44(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens and 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_45(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 1
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_46(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 or content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_47(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count != 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_48(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 1 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_49(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = None
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_50(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(None)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_51(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = None
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_52(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(None) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_53(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else "XXXX"
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_54(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = None
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_55(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(None)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_56(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(None)
            raise StreamingError(f"Failed to process streaming response: {e}") from e
    
    async def xǁGitHubModelsProviderǁ_handle_stream__mutmut_57(self, response) -> tuple[str, int]:
        """
        Handle streaming response and extract token count.
        
        Args:
            response: Response object from Azure SDK
            
        Returns:
            Tuple of (content, token_count)
        """
        try:
            # Extract content and token count from response
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Get content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content or ""
                else:
                    content = ""
                
                # Get token count from usage if available
                token_count = 0
                if hasattr(response, 'usage') and response.usage:
                    if hasattr(response.usage, 'completion_tokens'):
                        token_count = response.usage.completion_tokens or 0
                
                # Fallback: estimate tokens if not provided
                if token_count == 0 and content:
                    token_count = self._estimate_tokens(content)
                
                return content, token_count
            else:
                # Fallback for different response format
                content = str(response) if response else ""
                token_count = self._estimate_tokens(content)
                return content, token_count
                
        except Exception as e:
            logger.error(f"Error handling stream: {e}")
            raise StreamingError(None) from e
    
    xǁGitHubModelsProviderǁ_handle_stream__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁ_handle_stream__mutmut_1': xǁGitHubModelsProviderǁ_handle_stream__mutmut_1, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_2': xǁGitHubModelsProviderǁ_handle_stream__mutmut_2, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_3': xǁGitHubModelsProviderǁ_handle_stream__mutmut_3, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_4': xǁGitHubModelsProviderǁ_handle_stream__mutmut_4, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_5': xǁGitHubModelsProviderǁ_handle_stream__mutmut_5, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_6': xǁGitHubModelsProviderǁ_handle_stream__mutmut_6, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_7': xǁGitHubModelsProviderǁ_handle_stream__mutmut_7, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_8': xǁGitHubModelsProviderǁ_handle_stream__mutmut_8, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_9': xǁGitHubModelsProviderǁ_handle_stream__mutmut_9, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_10': xǁGitHubModelsProviderǁ_handle_stream__mutmut_10, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_11': xǁGitHubModelsProviderǁ_handle_stream__mutmut_11, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_12': xǁGitHubModelsProviderǁ_handle_stream__mutmut_12, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_13': xǁGitHubModelsProviderǁ_handle_stream__mutmut_13, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_14': xǁGitHubModelsProviderǁ_handle_stream__mutmut_14, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_15': xǁGitHubModelsProviderǁ_handle_stream__mutmut_15, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_16': xǁGitHubModelsProviderǁ_handle_stream__mutmut_16, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_17': xǁGitHubModelsProviderǁ_handle_stream__mutmut_17, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_18': xǁGitHubModelsProviderǁ_handle_stream__mutmut_18, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_19': xǁGitHubModelsProviderǁ_handle_stream__mutmut_19, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_20': xǁGitHubModelsProviderǁ_handle_stream__mutmut_20, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_21': xǁGitHubModelsProviderǁ_handle_stream__mutmut_21, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_22': xǁGitHubModelsProviderǁ_handle_stream__mutmut_22, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_23': xǁGitHubModelsProviderǁ_handle_stream__mutmut_23, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_24': xǁGitHubModelsProviderǁ_handle_stream__mutmut_24, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_25': xǁGitHubModelsProviderǁ_handle_stream__mutmut_25, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_26': xǁGitHubModelsProviderǁ_handle_stream__mutmut_26, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_27': xǁGitHubModelsProviderǁ_handle_stream__mutmut_27, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_28': xǁGitHubModelsProviderǁ_handle_stream__mutmut_28, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_29': xǁGitHubModelsProviderǁ_handle_stream__mutmut_29, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_30': xǁGitHubModelsProviderǁ_handle_stream__mutmut_30, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_31': xǁGitHubModelsProviderǁ_handle_stream__mutmut_31, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_32': xǁGitHubModelsProviderǁ_handle_stream__mutmut_32, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_33': xǁGitHubModelsProviderǁ_handle_stream__mutmut_33, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_34': xǁGitHubModelsProviderǁ_handle_stream__mutmut_34, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_35': xǁGitHubModelsProviderǁ_handle_stream__mutmut_35, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_36': xǁGitHubModelsProviderǁ_handle_stream__mutmut_36, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_37': xǁGitHubModelsProviderǁ_handle_stream__mutmut_37, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_38': xǁGitHubModelsProviderǁ_handle_stream__mutmut_38, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_39': xǁGitHubModelsProviderǁ_handle_stream__mutmut_39, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_40': xǁGitHubModelsProviderǁ_handle_stream__mutmut_40, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_41': xǁGitHubModelsProviderǁ_handle_stream__mutmut_41, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_42': xǁGitHubModelsProviderǁ_handle_stream__mutmut_42, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_43': xǁGitHubModelsProviderǁ_handle_stream__mutmut_43, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_44': xǁGitHubModelsProviderǁ_handle_stream__mutmut_44, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_45': xǁGitHubModelsProviderǁ_handle_stream__mutmut_45, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_46': xǁGitHubModelsProviderǁ_handle_stream__mutmut_46, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_47': xǁGitHubModelsProviderǁ_handle_stream__mutmut_47, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_48': xǁGitHubModelsProviderǁ_handle_stream__mutmut_48, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_49': xǁGitHubModelsProviderǁ_handle_stream__mutmut_49, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_50': xǁGitHubModelsProviderǁ_handle_stream__mutmut_50, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_51': xǁGitHubModelsProviderǁ_handle_stream__mutmut_51, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_52': xǁGitHubModelsProviderǁ_handle_stream__mutmut_52, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_53': xǁGitHubModelsProviderǁ_handle_stream__mutmut_53, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_54': xǁGitHubModelsProviderǁ_handle_stream__mutmut_54, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_55': xǁGitHubModelsProviderǁ_handle_stream__mutmut_55, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_56': xǁGitHubModelsProviderǁ_handle_stream__mutmut_56, 
        'xǁGitHubModelsProviderǁ_handle_stream__mutmut_57': xǁGitHubModelsProviderǁ_handle_stream__mutmut_57
    }
    xǁGitHubModelsProviderǁ_handle_stream__mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁ_handle_stream'
    
    @staticmethod
    def _estimate_tokens(content: str) -> int:
        """
        Estimate token count using simple heuristic.
        
        Fallback when metadata is unavailable. Uses ~4 chars per token
        as a rough approximation for English text.
        
        Args:
            content: Text content to estimate
            
        Returns:
            Estimated token count
        """
        if not content:
            return 0
        
        # Rough estimation: ~4 characters per token
        # This gives ±15% accuracy for typical English text
        return max(1, len(content) // 4)
    
    @classmethod
    def supported_models(cls) -> dict[str, ModelMetadata]:
        """
        Return dict of supported models with metadata.
        
        Returns:
            Dict mapping model names to ModelMetadata objects
        """
        return cls.SUPPORTED_MODELS.copy()
    
    def get_model_metadata(self, model_name: Optional[str] = None) -> ModelMetadata:
        args = [model_name]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁGitHubModelsProviderǁget_model_metadata__mutmut_orig'), object.__getattribute__(self, 'xǁGitHubModelsProviderǁget_model_metadata__mutmut_mutants'), args, kwargs, self)
    
    def xǁGitHubModelsProviderǁget_model_metadata__mutmut_orig(self, model_name: Optional[str] = None) -> ModelMetadata:
        """
        Get metadata for a supported model.
        
        Args:
            model_name: Model name (defaults to current model)
            
        Returns:
            ModelMetadata for the model
            
        Raises:
            ModelNotSupportedError: If model not supported
        """
        model = model_name or self.model_name
        
        if model not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                f"Model '{model}' is not supported"
            )
        
        return self.SUPPORTED_MODELS[model]
    
    def xǁGitHubModelsProviderǁget_model_metadata__mutmut_1(self, model_name: Optional[str] = None) -> ModelMetadata:
        """
        Get metadata for a supported model.
        
        Args:
            model_name: Model name (defaults to current model)
            
        Returns:
            ModelMetadata for the model
            
        Raises:
            ModelNotSupportedError: If model not supported
        """
        model = None
        
        if model not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                f"Model '{model}' is not supported"
            )
        
        return self.SUPPORTED_MODELS[model]
    
    def xǁGitHubModelsProviderǁget_model_metadata__mutmut_2(self, model_name: Optional[str] = None) -> ModelMetadata:
        """
        Get metadata for a supported model.
        
        Args:
            model_name: Model name (defaults to current model)
            
        Returns:
            ModelMetadata for the model
            
        Raises:
            ModelNotSupportedError: If model not supported
        """
        model = model_name and self.model_name
        
        if model not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                f"Model '{model}' is not supported"
            )
        
        return self.SUPPORTED_MODELS[model]
    
    def xǁGitHubModelsProviderǁget_model_metadata__mutmut_3(self, model_name: Optional[str] = None) -> ModelMetadata:
        """
        Get metadata for a supported model.
        
        Args:
            model_name: Model name (defaults to current model)
            
        Returns:
            ModelMetadata for the model
            
        Raises:
            ModelNotSupportedError: If model not supported
        """
        model = model_name or self.model_name
        
        if model in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                f"Model '{model}' is not supported"
            )
        
        return self.SUPPORTED_MODELS[model]
    
    def xǁGitHubModelsProviderǁget_model_metadata__mutmut_4(self, model_name: Optional[str] = None) -> ModelMetadata:
        """
        Get metadata for a supported model.
        
        Args:
            model_name: Model name (defaults to current model)
            
        Returns:
            ModelMetadata for the model
            
        Raises:
            ModelNotSupportedError: If model not supported
        """
        model = model_name or self.model_name
        
        if model not in self.SUPPORTED_MODELS:
            raise ModelNotSupportedError(
                None
            )
        
        return self.SUPPORTED_MODELS[model]
    
    xǁGitHubModelsProviderǁget_model_metadata__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGitHubModelsProviderǁget_model_metadata__mutmut_1': xǁGitHubModelsProviderǁget_model_metadata__mutmut_1, 
        'xǁGitHubModelsProviderǁget_model_metadata__mutmut_2': xǁGitHubModelsProviderǁget_model_metadata__mutmut_2, 
        'xǁGitHubModelsProviderǁget_model_metadata__mutmut_3': xǁGitHubModelsProviderǁget_model_metadata__mutmut_3, 
        'xǁGitHubModelsProviderǁget_model_metadata__mutmut_4': xǁGitHubModelsProviderǁget_model_metadata__mutmut_4
    }
    xǁGitHubModelsProviderǁget_model_metadata__mutmut_orig.__name__ = 'xǁGitHubModelsProviderǁget_model_metadata'


# ============== Provider Registry Integration ==============

def register_github_models_provider():
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_register_github_models_provider__mutmut_orig, x_register_github_models_provider__mutmut_mutants, args, kwargs, None)


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_orig():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_1():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register(None, GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_2():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", None)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_3():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register(GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_4():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", )
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_5():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("XXgithub-modelsXX", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_6():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("GITHUB-MODELS", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_7():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug(None)
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_8():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("XXGitHub Models provider registeredXX")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_9():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("github models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_10():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GITHUB MODELS PROVIDER REGISTERED")
    except ImportError:
        logger.debug("Provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_11():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug(None)


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_12():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("XXProvider registry not yet availableXX")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_13():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("provider registry not yet available")


# ============== Provider Registry Integration ==============

def x_register_github_models_provider__mutmut_14():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("PROVIDER REGISTRY NOT YET AVAILABLE")

x_register_github_models_provider__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_register_github_models_provider__mutmut_1': x_register_github_models_provider__mutmut_1, 
    'x_register_github_models_provider__mutmut_2': x_register_github_models_provider__mutmut_2, 
    'x_register_github_models_provider__mutmut_3': x_register_github_models_provider__mutmut_3, 
    'x_register_github_models_provider__mutmut_4': x_register_github_models_provider__mutmut_4, 
    'x_register_github_models_provider__mutmut_5': x_register_github_models_provider__mutmut_5, 
    'x_register_github_models_provider__mutmut_6': x_register_github_models_provider__mutmut_6, 
    'x_register_github_models_provider__mutmut_7': x_register_github_models_provider__mutmut_7, 
    'x_register_github_models_provider__mutmut_8': x_register_github_models_provider__mutmut_8, 
    'x_register_github_models_provider__mutmut_9': x_register_github_models_provider__mutmut_9, 
    'x_register_github_models_provider__mutmut_10': x_register_github_models_provider__mutmut_10, 
    'x_register_github_models_provider__mutmut_11': x_register_github_models_provider__mutmut_11, 
    'x_register_github_models_provider__mutmut_12': x_register_github_models_provider__mutmut_12, 
    'x_register_github_models_provider__mutmut_13': x_register_github_models_provider__mutmut_13, 
    'x_register_github_models_provider__mutmut_14': x_register_github_models_provider__mutmut_14
}
x_register_github_models_provider__mutmut_orig.__name__ = 'x_register_github_models_provider'


# Auto-register on import
register_github_models_provider()
