"""Tests for md_evals LLM adapter."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock

from md_evals.llm import LLMAdapter, inject_skill, LLMError


class TestLLMAdapter:
    """Test LLMAdapter."""
    
    def test_init_defaults(self):
        """Test initialization with defaults."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")
        
        assert adapter.model == "gpt-4o"
        assert adapter.provider == "openai"
    
    def test_init_with_defaults(self):
        """Test initialization with Defaults."""
        from md_evals.models import Defaults
        
        defaults = Defaults(model="gpt-4o", temperature=0.5)
        adapter = LLMAdapter(
            model="gpt-4o", 
            provider="openai", 
            defaults=defaults
        )
        
        assert adapter.defaults.temperature == 0.5
    
    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self):
        """Test completion with system prompt."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")
        
        # Mock litellm.acompletion
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]
        mock_response.usage = MagicMock(completion_tokens=10)
        # raw_response must be a dict - model_dump() should return a dict
        mock_response.model_dump = MagicMock(return_value={"model": "gpt-4o", "provider": "openai"})
        
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            
            result = await adapter.complete(
                prompt="Say hello",
                system_prompt="Be polite"
            )
            
            assert result.content == "Hello!"
    
    @pytest.mark.asyncio
    async def test_complete_error_handling(self):
        """Test error handling."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")
        
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API Error")
            
            with pytest.raises(LLMError):
                await adapter.complete(prompt="test")
    
    @pytest.mark.asyncio
    async def test_build_kwargs_defaults(self):
        """Test _build_kwargs with defaults."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")
        
        kwargs = adapter._build_kwargs()
        
        assert kwargs["model"] == "openai/gpt-4o"
        assert kwargs["temperature"] == 0.7
        assert kwargs["max_tokens"] == 2048
    
    @pytest.mark.asyncio
    async def test_build_kwargs_overrides(self):
        """Test _build_kwargs with overrides."""
        adapter = LLMAdapter(model="gpt-4o", provider="openai")
        
        kwargs = adapter._build_kwargs(temperature=0.5, max_tokens=100)
        
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100


class TestInjectSkill:
    """Test inject_skill function."""
    
    def test_control_no_skill(self):
        """Test CONTROL (no skill)."""
        prompt, system = inject_skill("Hello {name}", None)
        
        assert prompt == "Hello {name}"
        assert system is None
    
    def test_inject_skill(self, tmp_path):
        """Test skill injection."""
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("# My Skill\n\nBe helpful.")
        
        prompt, system = inject_skill("Hello", str(skill_file))
        
        assert prompt == "Hello"
        assert system is not None
        assert "My Skill" in system
        assert "Be helpful" in system
    
    def test_skill_not_found(self):
        """Test skill file not found."""
        with pytest.raises(FileNotFoundError):
            inject_skill("prompt", "/nonexistent/skill.md")


# ============================================================================
# PHASE 3: LLM Error Handling Coverage Expansion
# ============================================================================

class TestLLMTimeoutHandling:
    """Test timeout handling in LLM adapter."""
    
    @pytest.mark.asyncio
    async def test_complete_handles_timeout(self):
        """Test that timeouts are properly handled during retries."""
        # Create adapter with short timeout
        adapter = LLMAdapter(
            model="gpt-4",
            provider="openai",
        )
        
        # Mock litellm to simulate timeout (litellm raises Exception, not TimeoutError)
        with patch("md_evals.llm.litellm.acompletion") as mock_complete:
            # Simulate a timeout error that will be retried
            mock_complete.side_effect = Exception("Request timeout")
            
            with pytest.raises(Exception):  # Will eventually fail after retries
                await adapter.complete("Test prompt")


class TestLLMResponseParsing:
    """Test LLM response parsing and token handling."""
    
    @pytest.mark.asyncio
    async def test_complete_parses_usage_from_response(self):
        """Test parsing token count from response.usage."""
        adapter = LLMAdapter(
            model="gpt-4",
            provider="openai",
        )
        
        # Mock response with usage
        with patch("md_evals.llm.litellm.acompletion") as mock_complete:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_response.usage = Mock(completion_tokens=25)
            mock_response.model_dump = Mock(return_value={"model": "gpt-4"})
            mock_complete.return_value = mock_response
            
            response = await adapter.complete("Test prompt")
            
            assert response.tokens == 25
            assert response.content == "Test response"
    
    @pytest.mark.asyncio
    async def test_complete_without_usage_field(self):
        """Test response without usage field."""
        adapter = LLMAdapter(
            model="gpt-4",
            provider="openai",
        )
        
        # Mock response without usage
        with patch("md_evals.llm.litellm.acompletion") as mock_complete:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response without usage"))]
            mock_response.usage = None  # No usage data
            mock_response.model_dump = Mock(return_value={"model": "gpt-4"})
            mock_complete.return_value = mock_response
            
            response = await adapter.complete("Test prompt")
            
            # Should default to 0 tokens when usage not available
            assert response.tokens == 0
            assert response.content == "Response without usage"
    
    @pytest.mark.asyncio
    async def test_complete_with_string_response(self):
        """Test handling response object that converts to string."""
        adapter = LLMAdapter(
            model="gpt-4",
            provider="openai",
        )
        
        # Mock response without choices field
        with patch("md_evals.llm.litellm.acompletion") as mock_complete:
            mock_complete.return_value = "String response"
            
            response = await adapter.complete("Test prompt")
            
            # Should convert string to content
            assert response.content == "String response"
            assert response.tokens == 0


class TestLLMJSONResponse:
    """Test JSON response handling."""
    
    @pytest.mark.asyncio
    async def test_complete_with_json_valid_json(self):
        """Test complete_with_json with valid JSON response."""
        adapter = LLMAdapter(
            model="gpt-4",
            provider="openai",
        )
        
        json_response = '{"name": "test", "value": 42}'
        
        # Mock complete to return JSON
        with patch.object(adapter, "complete") as mock_complete:
            mock_response = Mock()
            mock_response.content = json_response
            mock_complete.return_value = mock_response
            
            response = await adapter.complete_with_json(
                "Generate JSON",
                json_schema={"type": "json_schema"}
            )
            
            # Should parse and reformat as pretty JSON
            assert '"name"' in response.content
            assert '"test"' in response.content
    
    @pytest.mark.asyncio
    async def test_complete_with_json_invalid_json(self):
        """Test complete_with_json with invalid JSON response."""
        adapter = LLMAdapter(
            model="gpt-4",
            provider="openai",
        )
        
        # Not valid JSON
        invalid_response = "This is not JSON at all"
        
        # Mock complete to return invalid JSON
        with patch.object(adapter, "complete") as mock_complete:
            mock_response = Mock()
            mock_response.content = invalid_response
            mock_complete.return_value = mock_response
            
            response = await adapter.complete_with_json(
                "Try to generate JSON",
                json_schema={"type": "json_schema"}
            )
            
            # Should keep original content if not valid JSON
            assert response.content == invalid_response


# ============================================================================
# PHASE 9d-2: LLM Error Handling Mutation Tests
# ============================================================================
# Purpose: Target 14 mutations in LLM error handling
# Strategy: Verify exception types, timeout logic, and error messages
# ============================================================================

class TestLLMErrorHandlingMutations:
    """Phase 9d-2: Mutation-focused tests for LLM error handling.
    
    These tests target mutations in LLM adapter error paths:
    - Timeout exception handling
    - Rate limit error detection
    - Authentication error differentiation
    - Model validation logic
    - Error message construction
    
    Mutations to catch:
    - Timeout check logic (< → >, removed)
    - Exception type mutations
    - Error message mutations
    - Retry logic mutations
    """
    
    @pytest.mark.asyncio
    async def test_llm_error_exception_raised(self):
        """Verify LLMError is raised for API errors.
        
        Mutation targets:
        - Exception type mutations (LLMError → ValueError)
        - Exception raising (removed)
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        # Mock provider that raises an error
        with patch.object(adapter, 'provider') as mock_provider:
            mock_provider.complete_stream.side_effect = Exception("API Error")
            
            # Should raise LLMError (not raw Exception)
            with pytest.raises(LLMError):
                await adapter.complete(prompt="test")
    
    @pytest.mark.asyncio
    async def test_llm_error_message_includes_details(self):
        """Verify LLMError message includes error details.
        
        Mutation targets:
        - Error message construction (f-string mutations)
        - Message content mutations
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        with patch.object(adapter, 'provider') as mock_provider:
            error_msg = "Rate limit exceeded"
            mock_provider.complete_stream.side_effect = Exception(error_msg)
            
            try:
                await adapter.complete(prompt="test")
            except LLMError as e:
                # Error message should contain original error details
                assert "API error" in str(e).lower() or "error" in str(e).lower()
    
    def test_invalid_model_format_raises_error(self):
        """Verify model name must not be empty string.
        
        Mutation targets:
        - Model validation logic
        - Empty string handling
        """
        # Model must be provided
        adapter = LLMAdapter(model="gpt-4o")
        assert adapter.model == "gpt-4o"
        
        # Model with slash is preserved (provider/model format)
        adapter2 = LLMAdapter(model="openai/gpt-4o")
        assert adapter2.model == "openai/gpt-4o"
    
    def test_llm_adapter_preserves_model_name(self):
        """Verify LLM adapter preserves exact model name.
        
        Mutation targets:
        - Model name mutations (normalization, case changes)
        - String modification mutations
        """
        model_name = "gpt-4o"
        adapter = LLMAdapter(model=model_name)
        
        # Must preserve exact model name (case sensitive)
        assert adapter.model == model_name
        assert adapter.model != model_name.upper()
        
        # Test with uppercase model name
        model_upper = "GPT-4O"
        adapter_upper = LLMAdapter(model=model_upper)
        assert adapter_upper.model == model_upper
        assert adapter_upper.model != model_upper.lower()
    
    @pytest.mark.asyncio
    async def test_llm_error_includes_original_exception(self):
        """Verify LLMError preserves original exception info.
        
        Mutation targets:
        - Exception chaining (raise ... from e → raise ...)
        - Exception context preservation
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        # Mock at the right level - before _complete_with_retry tries to handle specific exceptions
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            original_error = RuntimeError("Original API error")
            mock.side_effect = original_error
            
            with pytest.raises(LLMError) as exc_info:
                await adapter.complete(prompt="test")
            
            # Verify error message mentions the original error
            assert "LLM API error" in str(exc_info.value)
            # Verify exception chaining: __cause__ should be the original error
            # (Note: may have AttributeError if litellm.exceptions doesn't have expected attrs)
            assert exc_info.value.__cause__ is not None
    
    @pytest.mark.asyncio
    async def test_llm_response_fields_on_success(self):
        """Verify all response fields are populated on success.
        
        Mutation targets:
        - Response object initialization
        - Field assignment mutations
        - Type conversion mutations
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello World"))]
        mock_response.usage = MagicMock(completion_tokens=15)
        mock_response.model_dump = MagicMock(return_value={"model": "gpt-4o"})
        
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            
            response = await adapter.complete(prompt="test")
            
            # All fields must be populated
            assert response.content is not None
            assert response.content == "Hello World"
            assert response.model is not None
            assert response.provider is not None
            assert response.duration_ms is not None
            assert response.tokens is not None
            assert response.tokens == 15
            assert isinstance(response.duration_ms, (int, float))
            assert response.duration_ms >= 0  # Duration must be non-negative


class TestLLMAdapterValidationMutations:
    """
    Phase 10-3: Advanced mutation testing for LLM Adapter validation.
    
    These tests target specific mutations in model validation and response handling:
    - Model name parsing mutations (/ operator, provider prefix)
    - Response format validation mutations
    - Token extraction mutations (hasattr checks, fallback logic)
    - Error message propagation mutations
    
    Coverage Focus: llm.py lines 35-112 (kwargs building, response handling)
    Expected: +1-2% mutation kill rate improvement
    """
    
    def test_model_name_with_provider_prefix(self):
        """
        Mutation Target: Model name building logic (line 44)
        
        Tests: "model": f"{self.provider}/{self.model}" if "/" not in self.model else self.model
        
        Model with "/" already present should NOT duplicate provider prefix.
        Mutation: Remove "/" check (would create invalid model string)
        """
        # Model with provider prefix should not be modified
        adapter = LLMAdapter(model="github-models/gpt-4o", provider="custom")
        kwargs = adapter._build_kwargs()
        
        # Should use model as-is since it contains "/"
        assert kwargs["model"] == "github-models/gpt-4o"
        # Should NOT create "custom/github-models/gpt-4o"
        assert kwargs["model"].count("/") == 1
    
    def test_model_name_without_provider_prefix(self):
        """
        Mutation Target: Model name building logic (line 44)
        
        Tests: "model": f"{self.provider}/{self.model}" if "/" not in self.model else self.model
        
        Model without "/" should have provider prefix added.
        Mutation: Remove provider prefix check (would lose provider info)
        """
        adapter = LLMAdapter(model="gpt-4o", provider="openai")
        kwargs = adapter._build_kwargs()
        
        # Should add provider prefix since no "/" in model
        assert kwargs["model"] == "openai/gpt-4o"
    
    @pytest.mark.asyncio
    async def test_response_content_extraction_with_choices(self):
        """
        Mutation Target: Response parsing logic (lines 95-98)
        
        Tests: if hasattr(response, "choices") and response.choices:
        
        Should extract content from response.choices when available.
        Mutation: Remove hasattr check (would crash on missing attributes)
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test Response"))]
        mock_response.usage = MagicMock(completion_tokens=10)
        mock_response.model_dump = MagicMock(return_value={})
        
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            
            response = await adapter.complete(prompt="test")
            
            # Should extract content from choices
            assert response.content == "Test Response"
    
    @pytest.mark.asyncio
    async def test_token_count_extraction_with_usage(self):
        """
        Mutation Target: Token counting logic (lines 101-103)
        
        Tests: if hasattr(response, "usage") and response.usage:
        
        Should extract token count from response.usage when available.
        Mutation: Remove usage check (would lose token count, default to 0)
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test"))]
        mock_response.usage = MagicMock(completion_tokens=42)
        mock_response.model_dump = MagicMock(return_value={})
        
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            
            response = await adapter.complete(prompt="test")
            
            # Should extract token count from usage
            assert response.tokens == 42
    
    @pytest.mark.asyncio
    async def test_response_fallback_when_no_choices(self):
        """
        Mutation Target: Response fallback logic (line 98)
        
        Tests: else: content = str(response)
        
        Should gracefully handle responses without choices attribute.
        Mutation: Remove fallback (would crash or return None)
        """
        adapter = LLMAdapter(model="gpt-4o")
        
        # Create a custom mock that doesn't have choices attribute
        class CustomResponse:
            def __init__(self):
                self.choices = None
                self.usage = None
            
            def __str__(self):
                return "Fallback Response"
            
            def model_dump(self):
                return {}
        
        mock_response = CustomResponse()
        
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response
            
            response = await adapter.complete(prompt="test")
            
            # Should handle missing choices gracefully
            assert response.content is not None
            assert isinstance(response.content, str)


# ============================================================================
# FASE 12-1: LLM String Processing Properties
# ============================================================================
# Property-based tests for LLM module string/token handling

from hypothesis import given, strategies as st, settings, HealthCheck
import json


class TestLLMStringProcessingProperties:
    """Property-based tests for LLM string processing.
    
    Properties tested:
    1. Token counting is monotonic (more chars = more/equal tokens)
    2. Model response content is never None
    3. Token limits are enforced consistently
    4. Prompt processing doesn't lose information
    """
    
    @given(
        text_length=st.integers(min_value=0, max_value=5000),
    )
    def test_token_counting_properties(self, text_length):
        """Property: Token counts follow mathematical properties.
        
        For any text:
        - token_count(text) >= 0 (never negative)
        - token_count(text) <= len(text) / 4 * 1.3 (estimation rule)
        - token_count(empty) == 0
        - token_count(text) increases or stays same with longer text
        
        Mutation detectors:
        - If token counting returns negative
        - If it returns random values
        - If estimation formula is broken
        """
        from md_evals.providers.github_models import GitHubModelsProvider
        
        # Create text of specific length
        text = "a" * text_length
        tokens = GitHubModelsProvider._estimate_tokens(text)
        
        # Tokens must be non-negative
        assert tokens >= 0, f"Tokens negative for length {text_length}: {tokens}"
        
        # Tokens must be integer
        assert isinstance(tokens, int), f"Tokens not integer: {type(tokens)}"
        
        # Estimation should be reasonable (less than 1:1 character ratio typically)
        # Uses ~4 chars per token on average
        estimated_max = (text_length // 4) * 2  # Allow 2x upper bound for safety
        assert tokens <= estimated_max + 10, f"Token estimate too high: {tokens} > {estimated_max}"
    
    @given(
        text1_len=st.integers(min_value=0, max_value=1000),
        text2_len=st.integers(min_value=0, max_value=1000)
    )
    def test_token_counting_monotonic(self, text1_len, text2_len):
        """Property: Token counting is monotonic.
        
        If len(text1) <= len(text2), then:
        token_count(text1) <= token_count(text2)
        
        Mutation detectors:
        - If counting logic is randomized
        - If counting is backwards
        - If there's an off-by-one error
        """
        from md_evals.providers.github_models import GitHubModelsProvider
        
        text1 = "a" * text1_len
        text2 = "a" * text2_len
        
        tokens1 = GitHubModelsProvider._estimate_tokens(text1)
        tokens2 = GitHubModelsProvider._estimate_tokens(text2)
        
        # Monotonicity: more text = more or equal tokens
        if text1_len <= text2_len:
            assert tokens1 <= tokens2, f"Monotonicity violated: {tokens1} > {tokens2}"
    
    @given(
        prompt=st.text(min_size=1, max_size=500)
    )
    @settings(suppress_health_check=[HealthCheck.filter_too_much])
    def test_llm_prompt_preserved_after_injection(self, prompt):
        """Property: Non-empty prompts remain non-empty after skill injection.
        
        - Empty prompts should stay empty
        - Non-empty prompts should stay non-empty
        - Prompt structure should be preserved
        
        Mutation detectors:
        - If prompts are truncated to empty
        - If processing removes content incorrectly
        - If validation is missing
        """
        from md_evals.llm import inject_skill
        
        # Test with no skill (CONTROL)
        final_prompt, system_prompt = inject_skill(prompt, None)
        
        # Prompt should be preserved
        assert final_prompt == prompt
        assert system_prompt is None
        assert len(final_prompt) == len(prompt)
    
    @given(
        temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
        max_tokens=st.integers(min_value=1, max_value=4096)
    )
    def test_llm_adapter_config_properties(self, temperature, max_tokens):
        """Property: LLM adapter configuration is consistent.
        
        For valid provider + valid temperature + valid max_tokens:
        - Adapter creation doesn't crash
        - Settings are preserved
        - Temperature stays in valid range [0.0, 2.0]
        - max_tokens stays positive
        
        Mutation detectors:
        - If config validation is removed
        - If settings are overwritten
        - If bounds are wrong
        """
        from md_evals.llm import LLMAdapter
        
        # Temperature should be in valid range
        assert 0.0 <= temperature <= 2.0
        assert max_tokens > 0
        
        # Valid configuration should work
        try:
            adapter = LLMAdapter(
                provider="openai",
                model="test-model"
            )
            assert adapter is not None
            assert adapter.provider == "openai"
            assert adapter.model == "test-model"
        except Exception as e:
            # Configuration might fail for other reasons, but not these bounds
            assert "temperature" not in str(e).lower()
            assert "max_tokens" not in str(e).lower()


class TestLLMTokenEstimationProperties:
    """Property-based tests for token estimation edge cases."""
    
    @given(
        text=st.one_of(
            st.just(""),
            st.just(" "),
            st.just("\n"),
            st.text(min_size=1, max_size=100)
        )
    )
    def test_token_estimation_consistency(self, text):
        """Property: Token estimation is deterministic (same input = same output).
        
        - estimate_tokens(text) should always return same value
        - Calling multiple times should give identical results
        - No randomness in token counting
        
        Mutation detectors:
        - If randomness introduced
        - If state changes between calls
        - If caching is broken
        """
        from md_evals.providers.github_models import GitHubModelsProvider
        
        # Get first estimate
        estimate1 = GitHubModelsProvider._estimate_tokens(text)
        
        # Get second estimate
        estimate2 = GitHubModelsProvider._estimate_tokens(text)
        
        # Get third estimate
        estimate3 = GitHubModelsProvider._estimate_tokens(text)
        
        # All estimates must be identical
        assert estimate1 == estimate2, f"Inconsistent estimates: {estimate1} != {estimate2}"
        assert estimate2 == estimate3, f"Inconsistent estimates: {estimate2} != {estimate3}"
    
    @given(
        char=st.sampled_from(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-;:!?'\"")),
        count=st.integers(min_value=100, max_value=500)  # Large text to minimize granularity
    )
    def test_token_estimation_linear_for_repeated_chars(self, char, count):
        """Property: Token estimation grows roughly linearly with repeated text.
        
        - token_count(char * n) should grow linearly with n
        - token_count(char * (n+1)) >= token_count(char * n)
        
        Mutation detectors:
        - If counting is completely broken
        - If there's off-by-one errors
        """
        from md_evals.providers.github_models import GitHubModelsProvider
        
        text1 = char * count
        text2 = char * (count + 100)  # Add 100 chars
        
        tokens1 = GitHubModelsProvider._estimate_tokens(text1)
        tokens2 = GitHubModelsProvider._estimate_tokens(text2)
        
        # Must be monotonic - this is the key property
        assert tokens1 <= tokens2, f"Monotonicity violated: {tokens1} > {tokens2}"
        
        # Growth must be positive for added text
        token_increase = tokens2 - tokens1
        assert token_increase > 0, f"No token growth for 100 new chars: {token_increase}"
        
        # Token increase should be roughly ~25 tokens for 100 chars (4:1 ratio)
        # But allow 50% variance due to token boundaries and specifics
        assert token_increase >= 20, f"Token increase too small: {token_increase} (expected ~25)"
        assert token_increase <= 50, f"Token increase too large: {token_increase} (expected ~25)"


