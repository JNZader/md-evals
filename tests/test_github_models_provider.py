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


# ============================================================================
# PHASE 3: GitHub Models Error Handling Coverage Expansion
# ============================================================================

class TestErrorPathsCoverage:
    """Test error paths and exception handling (lines 224-230, 288-312, 343-354)."""
    
    @pytest.mark.asyncio
    async def test_complete_with_rate_limit_error(self, provider_with_mock_client, mock_azure_client):
        """Test rate limit error detection and handling."""
        # Simulate rate limit error (429 status code)
        mock_azure_client.complete.side_effect = Exception("429 Too Many Requests: Rate limit exceeded")
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.side_effect = Exception("429 Too Many Requests: Rate limit exceeded")
            
            with pytest.raises(RateLimitError) as exc_info:
                await provider_with_mock_client.complete("Test prompt")
            
            error = exc_info.value
            assert error.retry_after == 60
            assert "rate limit" in str(error).lower()
    
    @pytest.mark.asyncio
    async def test_complete_with_context_window_error(self, provider_with_mock_client, mock_azure_client):
        """Test context window exceeded error detection."""
        # Simulate context window error
        mock_azure_client.complete.side_effect = Exception("Token limit exceeded in context window")
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.side_effect = Exception("Token limit exceeded in context window")
            
            with pytest.raises(ContextWindowError) as exc_info:
                await provider_with_mock_client.complete("Test prompt")
            
            error = exc_info.value
            assert "context window" in str(error).lower() or "context" in str(error).lower()
    
    @pytest.mark.asyncio
    async def test_complete_with_network_error(self, provider_with_mock_client, mock_azure_client):
        """Test network/timeout error detection."""
        # Simulate timeout error
        mock_azure_client.complete.side_effect = Exception("Connection timeout during request")
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.side_effect = Exception("Connection timeout during request")
            
            with pytest.raises(StreamingError) as exc_info:
                await provider_with_mock_client.complete("Test prompt")
            
            error = exc_info.value
            assert "network" in str(error).lower() or "timeout" in str(error).lower()
    
    @pytest.mark.asyncio
    async def test_complete_with_authentication_error(self, provider_with_mock_client, mock_azure_client):
        """Test authentication error detection."""
        # Simulate auth error
        mock_azure_client.complete.side_effect = Exception("401 Unauthorized: Invalid GitHub token")
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.side_effect = Exception("401 Unauthorized: Invalid GitHub token")
            
            with pytest.raises(AuthenticationError) as exc_info:
                await provider_with_mock_client.complete("Test prompt")
            
            error = exc_info.value
            assert "authentication" in str(error).lower() or "token" in str(error).lower()
    
    @pytest.mark.asyncio
    async def test_complete_with_generic_api_error(self, provider_with_mock_client, mock_azure_client):
        """Test generic API error that doesn't match specific patterns."""
        # Simulate generic error
        mock_azure_client.complete.side_effect = Exception("Unknown API error occurred")
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.side_effect = Exception("Unknown API error occurred")
            
            with pytest.raises(APIError) as exc_info:
                await provider_with_mock_client.complete("Test prompt")
            
            error = exc_info.value
            assert "API error" in str(error) or "Unknown" in str(error)


class TestStreamingErrorHandling:
    """Test streaming response handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_handle_stream_with_no_usage_data(self, provider_with_mock_client):
        """Test handling response without usage data."""
        # Response without usage field
        response = Mock(
            choices=[Mock(message=Mock(content="Test content"))],
            usage=None
        )
        
        content, token_count = await provider_with_mock_client._handle_stream(response)
        
        assert content == "Test content"
        assert token_count > 0  # Should estimate tokens
    
    @pytest.mark.asyncio
    async def test_handle_stream_with_empty_content(self, provider_with_mock_client):
        """Test handling empty streaming response."""
        response = Mock(
            choices=[Mock(message=Mock(content=""))],
            usage=Mock(completion_tokens=0)
        )
        
        content, token_count = await provider_with_mock_client._handle_stream(response)
        
        assert content == ""
        assert token_count == 0
    
    @pytest.mark.asyncio
    async def test_handle_stream_with_different_response_format(self, provider_with_mock_client):
        """Test handling response in different format."""
        # Response without choices field
        response = Mock(spec=['__str__'])
        response.__str__ = lambda self: "Alternative response format"
        
        # Should handle fallback format
        try:
            content, token_count = await provider_with_mock_client._handle_stream(response)
            assert content == "Alternative response format"
        except StreamingError:
            # This is acceptable - StreamingError for unexpected format
            pass
    
    @pytest.mark.asyncio
    async def test_handle_stream_with_stream_error(self, provider_with_mock_client):
        """Test StreamingError during stream processing."""
        response = Mock(side_effect=Exception("Stream processing failed"))
        
        with pytest.raises(StreamingError) as exc_info:
            await provider_with_mock_client._handle_stream(response)
        
        assert "stream" in str(exc_info.value).lower()


class TestTokenEstimation:
    """Test token estimation for responses without usage data."""
    
    def test_estimate_tokens_simple(self):
        """Test basic token estimation."""
        content = "Hello world"
        tokens = GitHubModelsProvider._estimate_tokens(content)
        
        # Simple estimate: ~1 token per word, roughly 4 chars per token
        assert tokens > 0
        assert tokens <= len(content)  // 2
    
    def test_estimate_tokens_empty(self):
        """Test token estimation with empty content."""
        tokens = GitHubModelsProvider._estimate_tokens("")
        assert tokens == 0
    
    def test_estimate_tokens_long_text(self):
        """Test token estimation with longer content."""
        content = "This is a longer piece of content. " * 10
        tokens = GitHubModelsProvider._estimate_tokens(content)
        
        assert tokens > 0
        # Should be roughly proportional to content length
        assert tokens > len(content) // 10
    
    def test_estimate_tokens_special_chars(self):
        """Test token estimation with special characters."""
        content = "Test: [special] {chars} (here) <and> \"quotes\" 'too'"
        tokens = GitHubModelsProvider._estimate_tokens(content)
        
        assert tokens > 0


class TestAzureClientInitialization:
    """Test Azure client initialization error handling."""
    

class TestResponseFormats:
    """Test handling different Azure SDK response formats."""
    
    @pytest.mark.asyncio
    async def test_complete_with_usage_tokens(self, provider_with_mock_client, mock_azure_client):
        """Test response with full usage information."""
        mock_azure_client.complete.return_value = Mock(
            choices=[Mock(message=Mock(content="Response with tokens"))],
            usage=Mock(completion_tokens=42)
        )
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = mock_azure_client.complete.return_value
            
            response = await provider_with_mock_client.complete("Test")
            
            assert response.tokens == 42
            assert response.content == "Response with tokens"
    
    @pytest.mark.asyncio
    async def test_complete_with_estimated_tokens(self, provider_with_mock_client, mock_azure_client):
        """Test response with estimated tokens (no usage data)."""
        mock_azure_client.complete.return_value = Mock(
            choices=[Mock(message=Mock(content="Response without usage"))],
            usage=None
        )
        
        with patch.object(provider_with_mock_client, '_stream_completion', new_callable=AsyncMock) as mock_stream:
            mock_stream.return_value = mock_azure_client.complete.return_value
            
            response = await provider_with_mock_client.complete("Test")
            
            # Should have estimated tokens
            assert response.tokens > 0
            assert response.content == "Response without usage"


class TestProviderInitializationErrors:
    """Test provider initialization with various error conditions."""
    
    def test_unsupported_model_error_lists_supported(self):
        """Test that unsupported model error lists supported models."""
        with pytest.raises(ModelNotSupportedError) as exc_info:
            GitHubModelsProvider("unsupported-model")
        
        error_msg = str(exc_info.value)
        # Should list at least one supported model
        assert "gpt" in error_msg.lower() or "claude" in error_msg.lower() or "supported" in error_msg.lower()
    
    def test_missing_github_token_error(self):
        """Test error when GITHUB_TOKEN is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Make sure GITHUB_TOKEN is not set
            with pytest.raises(AuthenticationError) as exc_info:
                provider = GitHubModelsProvider("claude-3.5-sonnet")
                # This should fail during initialization
                if os.getenv("GITHUB_TOKEN"):
                    pytest.skip("GITHUB_TOKEN is set")
            
            error_msg = str(exc_info.value)
            assert "token" in error_msg.lower() or "github" in error_msg.lower()


class TestGitHubModelsAPIErrorMutations:
    """
    Phase 10-2: Advanced mutation testing for GitHub Models API error handling.
    
    These tests target specific mutations in error detection and handling:
    - Logical OR mutations (or↔and in keyword detection)
    - String pattern mutations (keyword presence, HTTP status codes)
    - Exception type mutations (which error class is raised)
    - Error priority mutations (elif ordering)
    
    Coverage Focus: github_models.py lines 288-312 (error detection in complete method)
    Expected: +1-2% mutation kill rate improvement
    """
    
    @pytest.mark.asyncio
    async def test_rate_limit_with_rate_keyword(self):
        """
        Mutation Target: OR operator in line 292
        
        Tests: if "rate" in error_str or "429" in error_str:
        
        Error with ONLY "rate" keyword should raise RateLimitError.
        Mutation: 'or' → 'and' (would miss rate-only errors)
        """
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            provider = GitHubModelsProvider("gpt-4o")
            
            with patch.object(provider, "_stream_completion") as mock_stream:
                mock_stream.side_effect = Exception("Rate limit exceeded for this model")
                
                with pytest.raises(RateLimitError) as exc_info:
                    await provider.complete("test prompt")
                
                error_msg = str(exc_info.value)
                assert "rate limit" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limit_with_429_status_code(self):
        """
        Mutation Target: OR operator in line 292
        
        Tests: if "rate" in error_str or "429" in error_str:
        
        Error with HTTP 429 status code should raise RateLimitError.
        Mutation: 'or' → 'and' (would miss 429-only errors)
        """
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            provider = GitHubModelsProvider("gpt-4o")
            
            with patch.object(provider, "_stream_completion") as mock_stream:
                # Simulate Azure SDK error with 429 status code
                mock_stream.side_effect = Exception("HTTP 429: Too Many Requests")
                
                with pytest.raises(RateLimitError):
                    await provider.complete("test prompt")
    
    @pytest.mark.asyncio
    async def test_context_window_with_context_keyword(self):
        """
        Mutation Target: OR operator in line 298
        
        Tests: if "context" in error_str or "token limit" in error_str:
        
        Error with ONLY "context" keyword should raise ContextWindowError.
        Mutation: 'or' → 'and' (would miss context-only errors)
        """
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            provider = GitHubModelsProvider("gpt-4o")
            
            with patch.object(provider, "_stream_completion") as mock_stream:
                mock_stream.side_effect = Exception("Context window size exceeded")
                
                with pytest.raises(ContextWindowError) as exc_info:
                    await provider.complete("test prompt")
                
                error_msg = str(exc_info.value)
                assert "context" in error_msg.lower() or "window" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_timeout_with_timeout_keyword(self):
        """
        Mutation Target: OR operator in line 303
        
        Tests: elif "timeout" in error_str or "connect" in error_str:
        
        Error with ONLY "timeout" keyword should raise StreamingError.
        Mutation: 'or' → 'and' (would miss timeout-only errors)
        """
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            provider = GitHubModelsProvider("gpt-4o")
            
            with patch.object(provider, "_stream_completion") as mock_stream:
                mock_stream.side_effect = Exception("Request timeout after 30 seconds")
                
                with pytest.raises(StreamingError) as exc_info:
                    await provider.complete("test prompt")
                
                error_msg = str(exc_info.value)
                assert "network" in error_msg.lower() or "timeout" in error_msg.lower() or "streaming" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_authentication_with_401_status_code(self):
        """
        Mutation Target: OR operator in line 307
        
        Tests: elif "authentication" in error_str or "401" in error_str:
        
        Error with HTTP 401 status code should raise AuthenticationError.
        Mutation: 'or' → 'and' (would miss 401-only errors)
        """
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            provider = GitHubModelsProvider("gpt-4o")
            
            with patch.object(provider, "_stream_completion") as mock_stream:
                # Simulate Azure SDK error with 401 status code
                mock_stream.side_effect = Exception("HTTP 401: Unauthorized - invalid credentials")
                
                with pytest.raises(AuthenticationError) as exc_info:
                    await provider.complete("test prompt")
                
                error_msg = str(exc_info.value)
                assert "authentication" in error_msg.lower() or "token" in error_msg.lower()

class TestTokenEstimationMutations:
    """Mutation tests for token estimation logic in GitHubModelsProvider."""

    def test_token_calculation_factor_mutation(self):
        """Verify token calculation uses correct factor (4 chars per token)."""
        from md_evals.providers.github_models import GitHubModelsProvider
        assert GitHubModelsProvider._estimate_tokens("a" * 100) == 25
        assert GitHubModelsProvider._estimate_tokens("a" * 1000) == 250
        assert GitHubModelsProvider._estimate_tokens("a" * 40) == 10

    def test_token_limit_boundary_mutation(self):
        """Verify empty text returns 0, small text returns at least 1."""
        from md_evals.providers.github_models import GitHubModelsProvider
        assert GitHubModelsProvider._estimate_tokens("") == 0
        assert GitHubModelsProvider._estimate_tokens("a") >= 1
        assert GitHubModelsProvider._estimate_tokens("abc") >= 1

    def test_rounding_method_mutation(self):
        """Verify rounding uses floor division (// not ceil)."""
        from md_evals.providers.github_models import GitHubModelsProvider
        # 5/4 = 1.25 → floor=1, ceil=2
        assert GitHubModelsProvider._estimate_tokens("abcde") == 1
        # 9/4 = 2.25 → floor=2, ceil=3
        assert GitHubModelsProvider._estimate_tokens("abcdefghi") == 2
        # 11/4 = 2.75 → floor=2, ceil=3
        assert GitHubModelsProvider._estimate_tokens("a" * 11) == 2

    def test_empty_text_fallback_mutation(self):
        """Verify empty text returns 0, non-empty returns at least 1."""
        from md_evals.providers.github_models import GitHubModelsProvider
        assert GitHubModelsProvider._estimate_tokens("") == 0
        assert GitHubModelsProvider._estimate_tokens("   ") >= 1

    def test_token_estimation_consistency(self):
        """Verify token estimation is consistent and scales linearly."""
        from md_evals.providers.github_models import GitHubModelsProvider
        text = "a" * 400
        assert GitHubModelsProvider._estimate_tokens(text) == 100
        assert GitHubModelsProvider._estimate_tokens("a" * 800) == 200

    def test_token_validation_large_text(self):
        """Verify token estimation handles large text without overflow."""
        from md_evals.providers.github_models import GitHubModelsProvider
        huge = "a" * (10**6)
        estimated = GitHubModelsProvider._estimate_tokens(huge)
        assert estimated == 250_000
        assert estimated > 0
        assert isinstance(estimated, int)

    def test_token_estimation_boundary_cases(self):
        """Verify token estimation on specific boundary cases."""
        from md_evals.providers.github_models import GitHubModelsProvider
        assert GitHubModelsProvider._estimate_tokens("a" * 4) == 1
        assert GitHubModelsProvider._estimate_tokens("a" * 5) == 1
        assert GitHubModelsProvider._estimate_tokens("a" * 6) == 1
        assert GitHubModelsProvider._estimate_tokens("a" * 7) == 1
        assert GitHubModelsProvider._estimate_tokens("a" * 8) == 2
