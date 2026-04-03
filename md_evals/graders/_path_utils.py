"""Shared path validation utilities for graders.

Prevents path traversal attacks when graders resolve user-supplied
relative paths against a workspace root.
"""

from __future__ import annotations

from pathlib import Path


def validate_workspace_path(workspace: Path, relative_path: str) -> Path:
    """Resolve a relative path inside a workspace and guard against traversal.

    Args:
        workspace: Root directory of the execution workspace.
        relative_path: User-supplied relative path (e.g. ``"output.txt"``).

    Returns:
        The resolved absolute ``Path`` guaranteed to be inside *workspace*.

    Raises:
        ValueError: If the resolved path escapes the workspace root.
    """
    target = (workspace / relative_path).resolve()
    resolved_workspace = workspace.resolve()
    if not str(target).startswith(str(resolved_workspace) + "/") and target != resolved_workspace:
        raise ValueError(
            f"Path traversal detected: '{relative_path}' resolves outside workspace"
        )
    return target
