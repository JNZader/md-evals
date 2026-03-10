"""LLM providers package for md-evals.

This package contains implementations of various LLM providers that can be
used for evaluations. Each provider implements a consistent async interface.
"""

# Import providers to trigger auto-registration
from md_evals.providers.github_models import GitHubModelsProvider

__all__ = ["GitHubModelsProvider"]
