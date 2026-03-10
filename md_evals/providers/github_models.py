"""GitHub Models provider for md-evals using Azure AI Inference SDK."""

import os
import time
import asyncio
import logging
from typing import Any, Optional
from dataclasses import dataclass

from md_evals.models import LLMResponse

logger = logging.getLogger(__name__)

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
        self.retry_after = retry_after
        super().__init__(message)


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
    
    def _load_github_token(self, token: Optional[str] = None) -> str:
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
    
    def _initialize_client(self):
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
    
    async def complete(
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
    
    async def _stream_completion(
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
    
    async def _handle_stream(self, response) -> tuple[str, int]:
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


# ============== Provider Registry Integration ==============

def register_github_models_provider():
    """Auto-register GitHub Models provider in global registry."""
    try:
        from md_evals.provider_registry import ProviderRegistry
        
        ProviderRegistry.register("github-models", GitHubModelsProvider)
        logger.debug("GitHub Models provider registered")
    except ImportError:
        logger.debug("Provider registry not yet available")


# Auto-register on import
register_github_models_provider()
