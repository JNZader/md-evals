"""Structure phase graders — validate input/output format.

Deterministic graders that check structural correctness:
- Is the output valid JSON?
- Are required fields present?
- Do field types match expectations?
- Does the structure conform to a schema?

These run FIRST in the three-phase pipeline because there's no
point analyzing or evaluating content if the format is broken.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_evals.models import EvaluatorResult


@dataclass
class JSONValidGrader:
    """Assert that file content or a string is valid JSON.

    Can operate in two modes:
    - **File mode**: provide ``path`` to check a file in the workspace.
    - **Content mode**: provide ``content`` directly (workspace is ignored).

    Attributes:
        name: Grader identifier for reports.
        path: Relative path inside workspace to check (file mode).
        content: Raw string to validate as JSON (content mode).
    """

    name: str
    path: str | None = None
    content: str | None = None

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        try:
            json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Invalid JSON: {exc}",
                details={"raw_preview": raw[:500]},
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=True,
            score=1.0,
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = workspace / self.path
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"


@dataclass
class RequiredFieldsGrader:
    """Assert that a JSON object contains all required fields.

    Parses the target as JSON and checks top-level keys.  Supports
    nested field checks using dot notation (e.g. ``"metadata.version"``).

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to JSON file in workspace.
        content: Raw JSON string (alternative to path).
        required_fields: List of field names that must be present.
    """

    name: str
    required_fields: list[str] = field(default_factory=list)
    path: str | None = None
    content: str | None = None

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Cannot parse JSON: {exc}",
            )

        if not isinstance(data, dict):
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="JSON root is not an object",
            )

        missing = []
        for field_path in self.required_fields:
            if not self._has_field(data, field_path):
                missing.append(field_path)

        if missing:
            present_count = len(self.required_fields) - len(missing)
            total = len(self.required_fields)
            score = present_count / total if total > 0 else 0.0
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=score,
                reason=f"Missing required fields: {', '.join(missing)}",
                details={"missing": missing, "present_count": present_count},
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=True,
            score=1.0,
        )

    @staticmethod
    def _has_field(data: dict[str, Any], field_path: str) -> bool:
        """Check if a field exists, supporting dot-notation for nesting."""
        parts = field_path.split(".")
        current: Any = data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return True

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = workspace / self.path
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"


@dataclass
class FieldTypeGrader:
    """Assert that JSON fields have expected types.

    Validates that specific fields in a JSON object match their
    expected Python types (str, int, float, bool, list, dict).

    Attributes:
        name: Grader identifier for reports.
        path: Relative path to JSON file in workspace.
        content: Raw JSON string (alternative to path).
        field_types: Mapping of field name (dot-notation) to expected type name.
    """

    name: str
    field_types: dict[str, str] = field(default_factory=dict)
    path: str | None = None
    content: str | None = None

    _TYPE_MAP: dict[str, type] = field(
        default_factory=lambda: {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "number": (int, float),
        },
        init=False,
        repr=False,
    )

    def grade(self, workspace: Path) -> EvaluatorResult:
        raw = self._resolve_content(workspace)
        if raw is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=self._missing_reason(),
            )

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Cannot parse JSON: {exc}",
            )

        if not isinstance(data, dict):
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="JSON root is not an object",
            )

        type_errors: list[str] = []
        for field_path, expected_type_name in self.field_types.items():
            value = self._get_field(data, field_path)
            if value is _MISSING:
                type_errors.append(f"Field '{field_path}' not found")
                continue

            expected = self._TYPE_MAP.get(expected_type_name)
            if expected is None:
                type_errors.append(
                    f"Unknown type '{expected_type_name}' for '{field_path}'"
                )
                continue

            if not isinstance(value, expected):
                actual = type(value).__name__
                type_errors.append(
                    f"Field '{field_path}': expected {expected_type_name}, got {actual}"
                )

        if type_errors:
            correct = len(self.field_types) - len(type_errors)
            total = len(self.field_types)
            score = correct / total if total > 0 else 0.0
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=score,
                reason="; ".join(type_errors),
                details={"errors": type_errors},
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=True,
            score=1.0,
        )

    @staticmethod
    def _get_field(data: dict[str, Any], field_path: str) -> Any:
        """Get nested field value or _MISSING sentinel."""
        parts = field_path.split(".")
        current: Any = data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return _MISSING
            current = current[part]
        return current

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = workspace / self.path
            if not target.exists():
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _missing_reason(self) -> str:
        if self.path is not None:
            return f"File '{self.path}' not found"
        return "No content or path provided"


class _MissingSentinel:
    """Sentinel for missing field values (distinct from None)."""

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingSentinel()
