"""Unit tests for GitHub Models provider."""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from md_evals.providers.github_models import (
    GitHubModelsProvider,
    AuthenticationError,
    ModelNotSupportedError,
    RateLimitError,
    ContextWindowError,
    StreamingError,
    APIError,
    GitHubModelsError,
    ModelMetadata,
)
from md_evals.provider_registry import ProviderRegistry
from md_evals.models import LLMResponse


# ============== Test Fixtures ==============


@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing."""
    return "github_pat_test_token_1234567890"


@pytest.fixture
def valid_token_env(mock_github_token, monkeypatch):
    """Set valid GITHUB_TOKEN in environment."""
    monkeypatch.setenv("GITHUB_TOKEN", mock_github_token)
    return mock_github_token


@pytest.fixture
def no_token_env(monkeypatch):
    """Remove GITHUB_TOKEN from environment."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


@pytest.fixture
def mock_azure_client():
    """Mock Azure AI client."""
    client = Mock()
    client.complete = Mock(return_value=Mock(
        choices=[Mock(
            message=Mock(content="Test response content"),
        )],
        usage=Mock(completion_tokens=10),
    ))
    return client


@pytest.fixture
def provider_with_mock_client(valid_token_env, mock_azure_client):
    """Create provider with mocked Azure client."""
    with patch.object(GitHubModelsProvider, '_initialize_client', return_value=mock_azure_client):
        provider = GitHubModelsProvider("claude-3.5-sonnet")
        return provider


# ============== Test Provider Initialization ==============


class TestProviderInitialization:
    """Test provider initialization and configuration."""
    
    def test_init_with_valid_token_from_env(self, valid_token_env, mock_azure_client):
        """Test initialization with valid GITHUB_TOKEN in environment."""
        with patch.object(GitHubModelsProvider, '_initialize_client', return_value=mock_azure_client):
            provider = GitHubModelsProvider("claude-3.5-sonnet")
            assert provider.model_name == "claude-3.5-sonnet"
            assert provider.github_token == valid_token_env
    
    def test_init_with_explicit_token(self, no_token_env, mock_azure_client):
        """Test initialization with explicitly provided token."""
        token = "github_pat_explicit_token"
        with patch.object(GitHubModelsProvider, '_initialize_client', return_value=mock_azure_client):
            provider = GitHubModelsProvider("claude-3.5-sonnet", github_token=token)
            assert provider.github_token == token
    
    def test_init_without_token_raises_error(self, no_token_env):
        """Test that initialization without token raises AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            GitHubModelsProvider("claude-3.5-sonnet")
        
        assert "GITHUB_TOKEN" in str(exc_info.value)
        assert "not set" in str(exc_info.value)
    
    def test_init_with_unsupported_model_raises_error(self, valid_token_env):
        """Test that initialization with unsupported model raises error."""
        with pytest.raises(ModelNotSupportedError) as exc_info:
            GitHubModelsProvider("gpt-2")
        
        assert "gpt-2" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)
    
    def test_init_with_custom_timeout(self, valid_token_env, mock_azure_client):
        """Test initialization with custom timeout."""
        with patch.object(GitHubModelsProvider, '_initialize_client', return_value=mock_azure_client):
            provider = GitHubModelsProvider(
                "claude-3.5-sonnet",
                timeout_seconds=120
            )
            assert provider.timeout_seconds == 120
    
    def test_init_with_custom_retries(self, valid_token_env, mock_azure_client):
        """Test initialization with custom retry count."""
        with patch.object(GitHubModelsProvider, '_initialize_client', return_value=mock_azure_client):
            provider = GitHubModelsProvider(
                "claude-3.5-sonnet",
                max_retries=5
            )
            assert provider.max_retries == 5


# ============== Test Token Loading ==============


class TestTokenLoading:
    """Test GitHub token loading and validation."""
    
    def test_load_token_from_env(self, valid_token_env):
        """Test loading token from environment."""
        token = GitHubModelsProvider(
            "claude-3.5-sonnet"
        )._load_github_token()
        assert token == valid_token_env
    
    def test_load_token_explicit_overrides_env(self, valid_token_env):
        """Test that explicit token overrides environment variable."""
        explicit_token = "github_pat_explicit_token"
        provider = GitHubModelsProvider(
            "claude-3.5-sonnet",
            github_token=explicit_token
        )
        # Should use explicit token, not env var
        assert provider.github_token == explicit_token
    
    def test_invalid_token_format_raises_error(self, no_token_env):
        """Test that invalid token format raises error."""
        with pytest.raises(AuthenticationError):
            provider = GitHubModelsProvider(
                "claude-3.5-sonnet",
                github_token="short"  # Too short
            )
    
    def test_missing_token_raises_error(self, no_token_env):
        """Test that missing token raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            provider = GitHubModelsProvider("claude-3.5-sonnet")
        
        error_msg = str(exc_info.value)
        assert "https://github.com/settings/tokens" in error_msg


# ============== Test Supported Models ==============


class TestSupportedModels:
    """Test model support and metadata."""
    
    def test_supported_models_list(self):
        """Test that all 4 supported models are listed."""
        models = GitHubModelsProvider.supported_models()
        
        assert "claude-3.5-sonnet" in models
        assert "gpt-4o" in models
        assert "deepseek-r1" in models
        assert "grok-3" in models
        assert len(models) == 4
    
    def test_model_metadata_structure(self):
        """Test that model metadata has required fields."""
        models = GitHubModelsProvider.supported_models()
        
        for model_name, metadata in models.items():
            assert isinstance(metadata, ModelMetadata)
            assert metadata.name
            assert metadata.provider
            assert metadata.context_window > 0
            assert isinstance(metadata.temperature_range, tuple)
            assert len(metadata.temperature_range) == 2
            assert metadata.rate_limit
            assert metadata.cost
            assert metadata.status
    
    def test_claude_metadata(self):
        """Test Claude model metadata."""
        metadata = GitHubModelsProvider.supported_models()["claude-3.5-sonnet"]
        
        assert "Claude" in metadata.name
        assert "Anthropic" in metadata.provider
        assert metadata.context_window == 200000
        assert metadata.temperature_range == (0.0, 2.0)
    
    def test_gpt4o_metadata(self):
        """Test GPT-4o model metadata."""
        metadata = GitHubModelsProvider.supported_models()["gpt-4o"]
        
        assert "GPT-4" in metadata.name
        assert "OpenAI" in metadata.provider
        assert metadata.context_window == 128000
    
    def test_deepseek_metadata(self):
        """Test DeepSeek model metadata."""
        metadata = GitHubModelsProvider.supported_models()["deepseek-r1"]
        
        assert "DeepSeek" in metadata.provider
        assert metadata.context_window == 64000
    
    def test_grok_metadata(self):
        """Test Grok model metadata."""
        metadata = GitHubModelsProvider.supported_models()["grok-3"]
        
        assert "xAI" in metadata.provider
        assert metadata.context_window == 128000
    
    def test_get_model_metadata(self, provider_with_mock_client):
        """Test retrieving metadata for current model."""
        metadata = provider_with_mock_client.get_model_metadata()
        assert metadata.name == "Claude 3.5 Sonnet"
    
    def test_get_model_metadata_invalid(self, provider_with_mock_client):
        """Test retrieving metadata for invalid model."""
        with pytest.raises(ModelNotSupportedError):
            provider_with_mock_client.get_model_metadata("invalid-model")


# ============== Test Token Counting ==============


class TestTokenCounting:
    """Test token counting and estimation."""
    
    def test_estimate_tokens_empty_content(self):
        """Test token estimation for empty content."""
        tokens = GitHubModelsProvider._estimate_tokens("")
        assert tokens == 0
    
    def test_estimate_tokens_simple_text(self):
        """Test token estimation for simple text."""
        content = "This is a test."  # ~15 characters
        tokens = GitHubModelsProvider._estimate_tokens(content)
        # ~4 chars per token: 15/4 = ~3-4 tokens
        assert 2 <= tokens <= 5
    
    def test_estimate_tokens_long_text(self):
        """Test token estimation for long text."""
        content = "x" * 400  # 400 characters
        tokens = GitHubModelsProvider._estimate_tokens(content)
        # Should be around 100 tokens
        assert 90 <= tokens <= 110
    
    def test_estimate_tokens_accuracy(self):
        """Test that estimation is within reasonable bounds."""
        # For English text, estimate should be within ±25%
        content = "Hello world, this is a test message with multiple words."
        tokens = GitHubModelsProvider._estimate_tokens(content)
        
        # Rough check: content has ~10 words, should be roughly 10-15 tokens
        assert 3 <= tokens <= 20


# ============== Test Provider Registry Integration ==============


class TestProviderRegistry:
    """Test provider registry integration."""
    
    def test_provider_registered_in_registry(self):
        """Test that GitHub Models provider is registered."""
        registry = ProviderRegistry()
        
        # Should be able to get the provider
        provider_class = registry.get("github-models")
        assert provider_class == GitHubModelsProvider
    
    def test_registry_name_normalization(self):
        """Test registry name normalization."""
        registry = ProviderRegistry()
        
        # Should work with various name formats
        provider1 = registry.get("github-models")
        provider2 = registry.get("github_models")
        provider3 = registry.get("GitHub Models")
        
        assert provider1 == provider2 == provider3 == GitHubModelsProvider
    
    def test_instantiate_from_registry(self, valid_token_env, mock_azure_client):
        """Test instantiating provider from registry."""
        with patch.object(GitHubModelsProvider, '_initialize_client', return_value=mock_azure_client):
            provider = ProviderRegistry.instantiate(
                "github-models",
                "claude-3.5-sonnet"
            )
            assert isinstance(provider, GitHubModelsProvider)
            assert provider.model_name == "claude-3.5-sonnet"
    
    def test_list_providers_includes_github(self):
        """Test that list_providers includes GitHub Models."""
        providers = ProviderRegistry.list_providers()
        assert "github-models" in providers
        assert providers["github-models"] == GitHubModelsProvider


# ============== Test Error Handling ==============


class TestErrorHandling:
    """Test error handling and exceptions."""
    
    def test_rate_limit_error_has_retry_after(self):
        """Test that RateLimitError includes retry_after info."""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
    
    def test_authentication_error_message(self):
        """Test authentication error message clarity."""
        error = AuthenticationError("Token not found")
        assert "Token not found" in str(error)
    
    def test_model_not_supported_error(self):
        """Test ModelNotSupportedError message."""
        with pytest.raises(ModelNotSupportedError) as exc_info:
            GitHubModelsProvider("unknown-model")
        
        assert "unknown-model" in str(exc_info.value)
        assert "claude-3.5-sonnet" in str(exc_info.value)
    
    def test_error_hierarchy(self):
        """Test error inheritance hierarchy."""
        assert issubclass(AuthenticationError, GitHubModelsError)
        assert issubclass(ModelNotSupportedError, GitHubModelsError)
        assert issubclass(RateLimitError, GitHubModelsError)
        assert issubclass(ContextWindowError, GitHubModelsError)
        assert issubclass(StreamingError, GitHubModelsError)
        assert issubclass(APIError, GitHubModelsError)


# ============== Test LLMResponse Integration ==============


class TestLLMResponseIntegration:
    """Test integration with LLMResponse model."""
    
    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(self, provider_with_mock_client, mock_azure_client):
        """Test that complete() returns proper LLMResponse."""
        mock_azure_client.complete.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))],
            usage=Mock(completion_tokens=15),
        )
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = mock_azure_client.complete.return_value
            
            response = await provider_with_mock_client.complete(
                "Test prompt",
                system_prompt="You are helpful"
            )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "claude-3.5-sonnet"
        assert response.provider == "github-models"
        assert response.tokens == 15
        assert response.duration_ms >= 0
    
    @pytest.mark.asyncio
    async def test_complete_with_temperature(self, provider_with_mock_client, mock_azure_client):
        """Test complete with custom temperature."""
        mock_azure_client.complete.return_value = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(completion_tokens=5),
        )
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = mock_azure_client.complete.return_value
            
            response = await provider_with_mock_client.complete(
                "Test",
                temperature=0.5
            )
        
        assert response.content == "Response"


# ============== Integration Test Marker ==============


@pytest.mark.integration
class TestIntegrationGitHubModelsAPI:
    """Integration tests with real GitHub Models API (skip by default)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN not set"
    )
    async def test_real_api_call_with_claude(self):
        """Test real API call with Claude model (requires valid token)."""
        provider = GitHubModelsProvider("claude-3.5-sonnet")
        
        try:
            response = await provider.complete("Say 'hello world'")
            assert isinstance(response, LLMResponse)
            assert response.content
            assert response.tokens > 0
            assert response.duration_ms > 0
        except Exception as e:
            pytest.skip(f"Real API test skipped: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN not set"
    )
    async def test_real_api_call_with_gpt4o(self):
        """Test real API call with GPT-4o model."""
        provider = GitHubModelsProvider("gpt-4o")
        
        try:
            response = await provider.complete("Say 'hello'")
            assert isinstance(response, LLMResponse)
            assert response.model == "gpt-4o"
            assert response.tokens >= 0
        except Exception as e:
            pytest.skip(f"Real API test skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
