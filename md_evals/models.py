"""Pydantic models for eval.yaml schemas."""

from pydantic import BaseModel


class Defaults(BaseModel):
    """Default configuration values."""
    model: str = "gpt-4o"
    provider: str = "openai"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


class Treatment(BaseModel):
    """Treatment definition."""
    description: str | None = None
    skill_path: str | None = None
    env: dict[str, str] = {}


class EvalConfig(BaseModel):
    """Top-level evaluation configuration."""
    name: str
    version: str = "1.0"
    description: str | None = None
    defaults: Defaults = Defaults()
    treatments: dict[str, Treatment] = {}
    tests: list = []
