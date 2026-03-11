"""Tests for md_evals LLM adapter."""

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
