"""Utility functions for md-evals."""

from pathlib import Path


def read_file(path: str) -> str:
    """Read file contents."""
    return Path(path).read_text()


def ensure_dir(path: str) -> Path:
    """Ensure directory exists."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
