"""Tests for md_evals LLM adapter."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

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
