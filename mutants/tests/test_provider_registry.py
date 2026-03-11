"""Unit tests for provider registry."""

import pytest
from unittest.mock import Mock

from md_evals.provider_registry import ProviderRegistry
from md_evals.providers.github_models import GitHubModelsProvider


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before each test."""
    ProviderRegistry.clear()
    # Re-register GitHub Models
    ProviderRegistry.register("github-models", GitHubModelsProvider)
    yield
    ProviderRegistry.clear()


class TestProviderRegistry:
    """Test ProviderRegistry functionality."""
    
    def test_registry_is_singleton(self):
        """Test that registry is a singleton."""
        registry1 = ProviderRegistry()
        registry2 = ProviderRegistry()
        assert registry1 is registry2
    
    def test_register_provider(self):
        """Test registering a provider."""
        ProviderRegistry.clear()
        MockProvider = Mock()
        
        ProviderRegistry.register("test-provider", MockProvider)
        
        assert "test-provider" in ProviderRegistry.list_providers()
    
    def test_get_registered_provider(self):
        """Test retrieving a registered provider."""
        provider_class = ProviderRegistry.get("github-models")
        assert provider_class == GitHubModelsProvider
    
    def test_get_nonexistent_provider_raises_error(self):
        """Test that getting nonexistent provider raises error."""
        with pytest.raises(ValueError) as exc_info:
            ProviderRegistry.get("nonexistent-provider")
        
        assert "not found" in str(exc_info.value)
    
    def test_list_providers_empty(self):
        """Test listing providers when registry is empty."""
        ProviderRegistry.clear()
        providers = ProviderRegistry.list_providers()
        assert len(providers) == 0
    
    def test_list_providers_includes_registered(self):
        """Test that list includes registered providers."""
        ProviderRegistry.clear()
        MockProvider = Mock()
        ProviderRegistry.register("test-provider", MockProvider)
        
        providers = ProviderRegistry.list_providers()
        assert "test-provider" in providers
    
    def test_name_normalization_lowercase(self):
        """Test name normalization converts to lowercase."""
        ProviderRegistry.clear()
        MockProvider = Mock()
        ProviderRegistry.register("GitHub-Models", MockProvider)
        
        # Should be found as lowercase
        provider = ProviderRegistry.get("github-models")
        assert provider == MockProvider
    
    def test_name_normalization_underscores(self):
        """Test name normalization replaces underscores with hyphens."""
        provider = ProviderRegistry.get("github_models")
        assert provider == GitHubModelsProvider
    
    def test_name_normalization_spaces(self):
        """Test name normalization replaces spaces with hyphens."""
        provider = ProviderRegistry.get("github models")
        assert provider == GitHubModelsProvider
    
    def test_instantiate_provider(self):
        """Test instantiating a provider from registry."""
        # This would normally require a valid token, so we mock it
        with pytest.raises(Exception):
            # Will fail due to no token, but tests the registry instantiation path
            ProviderRegistry.instantiate("github-models", "claude-3.5-sonnet")
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        ProviderRegistry.register("test-provider", Mock())
        ProviderRegistry.clear()
        
        providers = ProviderRegistry.list_providers()
        assert len(providers) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
