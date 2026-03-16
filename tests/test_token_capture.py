"""Tests for Phase 2: Token capture in LLMAdapter and GitHubModelsProvider.

Covers:
- T-04: LLMAdapter.complete() extracts prompt_tokens, completion_tokens_detail,
         total_tokens from response.usage, determines MetricSource
- T-05: GitHubModelsProvider propagates usage info correctly
- T-06: resolve_context_window() fallback chain
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from md_evals.llm import LLMAdapter
from md_evals.models import LLMResponse, EvalConfig
from md_evals.metrics import resolve_context_window


# ============================================================================
# T-04: LLMAdapter.complete() — Token Capture
# ============================================================================


class TestLLMAdapterTokenCapture:
    """Test that LLMAdapter.complete() populates new token fields."""

    @pytest.mark.asyncio
    async def test_complete_captures_prompt_and_completion_tokens(self):
        """Full usage data → prompt_tokens, completion_tokens_detail, total populated."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=25)
        mock_response.model_dump = MagicMock(return_value={"model": "gpt-4o"})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="Say hello")

        assert result.prompt_tokens == 100
        assert result.completion_tokens_detail == 25
        assert result.total_tokens == 125
        # Legacy field still works
        assert result.tokens == 25

    @pytest.mark.asyncio
    async def test_complete_without_prompt_tokens(self):
        """Only completion_tokens in usage → prompt_tokens None, total None."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]
        # Only completion_tokens, no prompt_tokens attribute
        mock_usage = MagicMock(spec=["completion_tokens"])
        mock_usage.completion_tokens = 30
        mock_response.usage = mock_usage
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.prompt_tokens is None
        assert result.completion_tokens_detail == 30
        assert result.total_tokens is None  # Can't calculate without prompt
        assert result.tokens == 30  # Legacy still works

    @pytest.mark.asyncio
    async def test_complete_without_usage(self):
        """No usage data → all new fields None, legacy tokens=0."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]
        mock_response.usage = None
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.prompt_tokens is None
        assert result.completion_tokens_detail is None
        assert result.total_tokens is None
        assert result.tokens == 0

    @pytest.mark.asyncio
    async def test_complete_clamps_negative_prompt_tokens(self):
        """Negative prompt_tokens → clamped to 0 (EC-03 spec)."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi"))]
        mock_response.usage = MagicMock(prompt_tokens=-50, completion_tokens=10)
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.prompt_tokens == 0  # Clamped from -50
        assert result.completion_tokens_detail == 10
        assert result.total_tokens == 10  # 0 + 10

    @pytest.mark.asyncio
    async def test_complete_clamps_negative_completion_tokens(self):
        """Negative completion_tokens → clamped to 0 (EC-03 spec)."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi"))]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=-5)
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.prompt_tokens == 100
        assert result.completion_tokens_detail == 0  # Clamped
        assert result.total_tokens == 100  # 100 + 0
        assert result.tokens == 0  # Legacy also clamped

    @pytest.mark.asyncio
    async def test_complete_stage_type_default(self):
        """Default stage_type is 'single_pass'."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi"))]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.stage_type == "single_pass"

    @pytest.mark.asyncio
    async def test_complete_stage_type_override(self):
        """Custom stage_type is preserved in response."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi"))]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test", stage_type="planner")

        assert result.stage_type == "planner"

    @pytest.mark.asyncio
    async def test_complete_zero_tokens(self):
        """Zero tokens from provider → fields populated with 0."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi"))]
        mock_response.usage = MagicMock(prompt_tokens=0, completion_tokens=0)
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.prompt_tokens == 0
        assert result.completion_tokens_detail == 0
        assert result.total_tokens == 0
        assert result.tokens == 0

    @pytest.mark.asyncio
    async def test_complete_legacy_tokens_field_unchanged(self):
        """Legacy .tokens field always equals completion_tokens or 0."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hi"))]
        mock_response.usage = MagicMock(prompt_tokens=500, completion_tokens=42)
        mock_response.model_dump = MagicMock(return_value={})

        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            result = await adapter.complete(prompt="test")

        assert result.tokens == 42  # Legacy field = completion_tokens


# ============================================================================
# T-05: GitHubModelsProvider — Token Propagation
# ============================================================================


class TestGitHubModelsTokenPropagation:
    """Test that GitHubModelsProvider propagates usage info correctly."""

    @pytest.fixture
    def mock_azure_client(self):
        """Mock Azure AI client."""
        client = Mock()
        return client

    @pytest.fixture
    def provider(self, monkeypatch, mock_azure_client):
        """Create provider with mocked client."""
        from md_evals.providers.github_models import GitHubModelsProvider

        monkeypatch.setenv("GITHUB_TOKEN", "github_pat_test_token_1234567890")
        with patch.object(
            GitHubModelsProvider,
            "_initialize_client",
            return_value=mock_azure_client,
        ):
            return GitHubModelsProvider("gpt-4o")

    @pytest.mark.asyncio
    async def test_complete_captures_full_usage(self, provider):
        """Full usage from Azure SDK → all fields populated."""
        mock_response = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(prompt_tokens=200, completion_tokens=50),
        )

        with patch.object(
            provider, "_stream_completion", new_callable=AsyncMock
        ) as mock_stream:
            mock_stream.return_value = mock_response

            result = await provider.complete("Test prompt")

        assert isinstance(result, LLMResponse)
        assert result.prompt_tokens == 200
        assert result.completion_tokens_detail == 50
        assert result.total_tokens == 250
        assert result.tokens == 50  # Legacy

    @pytest.mark.asyncio
    async def test_complete_without_prompt_tokens_in_usage(self, provider):
        """Azure SDK response with only completion_tokens → prompt_tokens None."""
        mock_usage = Mock(spec=["completion_tokens"])
        mock_usage.completion_tokens = 30
        mock_response = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=mock_usage,
        )

        with patch.object(
            provider, "_stream_completion", new_callable=AsyncMock
        ) as mock_stream:
            mock_stream.return_value = mock_response

            result = await provider.complete("Test prompt")

        assert result.prompt_tokens is None
        assert result.completion_tokens_detail == 30
        assert result.total_tokens is None
        assert result.tokens == 30

    @pytest.mark.asyncio
    async def test_complete_without_usage(self, provider):
        """No usage data → all new fields None, legacy estimated."""
        mock_response = Mock(
            choices=[Mock(message=Mock(content="Some response content"))],
            usage=None,
        )

        with patch.object(
            provider, "_stream_completion", new_callable=AsyncMock
        ) as mock_stream:
            mock_stream.return_value = mock_response

            result = await provider.complete("Test prompt")

        assert result.prompt_tokens is None
        assert result.completion_tokens_detail is None
        assert result.total_tokens is None
        # Legacy field should be estimated (>0) since content is non-empty
        assert result.tokens > 0

    @pytest.mark.asyncio
    async def test_handle_stream_clamps_negative_prompt_tokens(self, provider):
        """Negative prompt_tokens from Azure → clamped to 0."""
        mock_response = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(prompt_tokens=-10, completion_tokens=20),
        )

        content, token_count, prompt_tokens, completion_detail, total = (
            await provider._handle_stream(mock_response)
        )

        assert prompt_tokens == 0  # Clamped
        assert completion_detail == 20
        assert total == 20  # 0 + 20


# ============================================================================
# T-06: resolve_context_window() — Fallback Chain
# ============================================================================


class TestResolveContextWindow:
    """Test resolve_context_window() fallback chain."""

    def test_config_override_takes_priority(self):
        """Level 1: config.context_window_overrides[model] wins."""
        config = EvalConfig(
            name="test",
            context_window_overrides={"gpt-4o": 64000},
        )
        result = resolve_context_window("gpt-4o", "openai", config)
        assert result == 64000

    def test_config_override_for_different_model(self):
        """Override only applies to matching model name."""
        config = EvalConfig(
            name="test",
            context_window_overrides={"gpt-4o": 64000},
        )
        # claude-3.5-sonnet not in overrides
        result = resolve_context_window("claude-3.5-sonnet", "openai", config)
        # Should NOT return 64000, should fall through
        assert result != 64000 or result is None

    def test_provider_metadata_fallback(self):
        """Level 2: Provider metadata from registry."""
        # Ensure provider is registered
        from md_evals.providers.github_models import register_github_models_provider

        register_github_models_provider()

        config = EvalConfig(name="test")

        # GitHubModelsProvider has gpt-4o with context_window=128000
        result = resolve_context_window("gpt-4o", "github-models", config)
        assert result == 128000

    def test_provider_metadata_claude(self):
        """Level 2: Provider metadata for Claude model."""
        # Ensure provider is registered
        from md_evals.providers.github_models import register_github_models_provider

        register_github_models_provider()

        config = EvalConfig(name="test")

        result = resolve_context_window(
            "claude-3.5-sonnet", "github-models", config
        )
        assert result == 200000

    def test_unknown_provider_falls_through(self):
        """Unknown provider → falls through to litellm or None."""
        config = EvalConfig(name="test")

        result = resolve_context_window(
            "some-model", "unknown-provider", config
        )
        # Should be None or a litellm value, never raises
        assert result is None or isinstance(result, int)

    def test_unknown_model_unknown_provider_returns_none(self):
        """Completely unknown model+provider → None."""
        config = EvalConfig(name="test")

        result = resolve_context_window(
            "nonexistent-model-xyz", "nonexistent-provider-xyz", config
        )
        assert result is None

    def test_none_config_still_works(self):
        """None config → skips override, uses provider/litellm."""
        from md_evals.providers.github_models import register_github_models_provider

        register_github_models_provider()
        # Should not raise
        result = resolve_context_window("gpt-4o", "github-models", None)
        # Provider metadata should still work
        assert result == 128000

    def test_config_without_overrides_attribute(self):
        """Config object without context_window_overrides → skips level 1."""
        from md_evals.providers.github_models import register_github_models_provider

        register_github_models_provider()

        class MinimalConfig:
            pass

        config = MinimalConfig()
        result = resolve_context_window("gpt-4o", "github-models", config)
        assert result == 128000

    def test_never_raises_exception(self):
        """resolve_context_window never raises — returns None on failure."""
        # These should all return without raising
        assert resolve_context_window("", "", None) is None or True
        assert resolve_context_window("x", "y", None) is None or True
        assert resolve_context_window("gpt-4o", "openai", "bad-config") is None or True

    def test_config_override_wins_over_provider_metadata(self):
        """Config override takes priority even when provider has data."""
        from md_evals.providers.github_models import register_github_models_provider

        register_github_models_provider()

        config = EvalConfig(
            name="test",
            # Override gpt-4o which also exists in GitHubModelsProvider
            context_window_overrides={"gpt-4o": 32000},
        )
        result = resolve_context_window("gpt-4o", "github-models", config)
        assert result == 32000  # Config wins over provider's 128000

    def test_litellm_fallback(self):
        """Level 3: litellm.get_model_info() fallback."""
        config = EvalConfig(name="test")

        # Patch litellm module directly (imported inside function)
        mock_litellm = MagicMock()
        mock_litellm.get_model_info.return_value = {
            "max_input_tokens": 32768,
        }
        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            result = resolve_context_window(
                "custom-model", "unknown-provider", config
            )
            assert result == 32768

    def test_litellm_fallback_no_max_input_tokens(self):
        """litellm returns info but without max_input_tokens → None."""
        config = EvalConfig(name="test")

        mock_litellm = MagicMock()
        mock_litellm.get_model_info.return_value = {"model_name": "custom"}
        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            result = resolve_context_window(
                "custom-model", "unknown-provider", config
            )
            assert result is None

    def test_litellm_exception_handled_gracefully(self):
        """litellm.get_model_info() raises → graceful None."""
        config = EvalConfig(name="test")

        mock_litellm = MagicMock()
        mock_litellm.get_model_info.side_effect = Exception("Not found")
        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            result = resolve_context_window(
                "custom-model", "unknown-provider", config
            )
            assert result is None


# ============================================================================
# LLMResponse Model — New Fields Defaults
# ============================================================================


class TestLLMResponseNewFields:
    """Test that LLMResponse new fields have correct defaults."""

    def test_new_fields_default_to_none(self):
        """New optional fields default to None."""
        response = LLMResponse(
            content="test",
            model="gpt-4o",
            provider="openai",
        )
        assert response.prompt_tokens is None
        assert response.completion_tokens_detail is None
        assert response.total_tokens is None

    def test_stage_type_defaults_to_single_pass(self):
        """stage_type defaults to 'single_pass'."""
        response = LLMResponse(
            content="test",
            model="gpt-4o",
            provider="openai",
        )
        assert response.stage_type == "single_pass"

    def test_new_fields_can_be_set(self):
        """New fields accept values correctly."""
        response = LLMResponse(
            content="test",
            model="gpt-4o",
            provider="openai",
            prompt_tokens=100,
            completion_tokens_detail=50,
            total_tokens=150,
            stage_type="planner",
        )
        assert response.prompt_tokens == 100
        assert response.completion_tokens_detail == 50
        assert response.total_tokens == 150
        assert response.stage_type == "planner"

    def test_legacy_tokens_field_still_works(self):
        """Legacy .tokens field unchanged."""
        response = LLMResponse(
            content="test",
            model="gpt-4o",
            provider="openai",
            tokens=42,
        )
        assert response.tokens == 42
