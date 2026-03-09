"""LLM adapter using litellm."""


class LLMAdapter:
    """Wrapper for litellm completions."""
    
    def __init__(self, model: str, provider: str = "openai"):
        self.model = model
        self.provider = provider
    
    async def complete(self, prompt: str):
        """Complete a prompt."""
        # TODO: Implement
        pass
