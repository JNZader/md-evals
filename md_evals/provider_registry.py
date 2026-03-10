"""Global provider registry for md-evals.

Supports dynamic provider registration and discovery at runtime.
"""

import logging
from typing import Type, Optional, Any

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Global registry for LLM providers.
    
    Implements singleton pattern to maintain a single registry of
    all available providers. Supports registration, lookup, and
    instantiation of providers.
    """
    
    _instance: Optional['ProviderRegistry'] = None
    _providers: dict[str, Type] = {}
    
    def __new__(cls) -> 'ProviderRegistry':
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: str, provider_class: Type) -> None:
        """
        Register a provider class.
        
        Args:
            name: Provider name (e.g., "github-models", "openai")
            provider_class: Provider class to register
        """
        instance = cls()
        instance._providers[name.lower()] = provider_class
        logger.info(f"Registered provider: {name}")
    
    @classmethod
    def get(cls, name: str) -> Type:
        """
        Retrieve provider class by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider class
            
        Raises:
            ValueError: If provider not found
        """
        instance = cls()
        normalized_name = cls._normalize_name(name)
        
        if normalized_name not in instance._providers:
            available = ", ".join(instance._providers.keys())
            raise ValueError(
                f"Provider '{name}' not found. "
                f"Available providers: {available}"
            )
        
        return instance._providers[normalized_name]
    
    @classmethod
    def list_providers(cls) -> dict[str, Type]:
        """
        List all registered providers.
        
        Returns:
            Dict mapping provider names to classes
        """
        instance = cls()
        return instance._providers.copy()
    
    @classmethod
    def instantiate(
        cls,
        provider_name: str,
        model_name: str,
        **kwargs
    ) -> Any:
        """
        Instantiate a provider.
        
        Args:
            provider_name: Provider name
            model_name: Model name
            **kwargs: Additional arguments to pass to provider
            
        Returns:
            Instantiated provider
            
        Raises:
            ValueError: If provider not found
        """
        provider_class = cls.get(provider_name)
        return provider_class(model_name=model_name, **kwargs)
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize provider name for lookup.
        
        Supports variants:
        - "github-models"
        - "GitHub Models"
        - "github_models"
        
        Args:
            name: Provider name
            
        Returns:
            Normalized name
        """
        # Convert to lowercase and replace spaces/underscores with hyphens
        normalized = name.lower().replace("_", "-").replace(" ", "-")
        return normalized
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (useful for testing)."""
        instance = cls()
        instance._providers.clear()
        logger.debug("Cleared provider registry")


# Convenience function for registration
def register_provider(name: str, provider_class: Type) -> None:
    """
    Register a provider in the global registry.
    
    Args:
        name: Provider name
        provider_class: Provider class
    """
    ProviderRegistry.register(name, provider_class)
