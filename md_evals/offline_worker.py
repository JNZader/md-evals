"""Deterministic, provider-free worker boundary for frozen captured inputs.

This module accepts only an already-frozen prompt/context pair and an injected
callable. It has no ambient repository, network, subprocess, or provider access.
The callable returns the existing closed captured-answer envelope; every other
value becomes an explicit non-success result.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping

from md_evals.captured_answer_grader import validate_answer_envelope

INPUT_SCHEMA = "offline-worker-input/v1"
OUTPUT_SCHEMA = "offline-worker-output/v1"
WorkerStatus = Literal["completed", "malformed_output", "timeout", "cancelled", "failed"]

_INPUT_KEYS = {"schema_version", "prompt", "context"}
_OUTPUT_KEYS = {"schema_version", "status", "answer", "error_code", "error_message"}
_MAX_ERROR_LENGTH = 160
_SECRET_KEY = re.compile(
    r"(?:^|[_-])(?:password|passwd|secret|token|api[_-]?key|authorization|credential|private[_-]?key)(?:$|[_-])",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{8,}|sk_(?:live|test)_[A-Za-z0-9_-]{8,}|"
    r"gh[pousr]_[A-Za-z0-9_]{8,}|glpat-[A-Za-z0-9_-]{8,}|"
    r"xox[baprs]-[A-Za-z0-9-]{8,}|AIza[A-Za-z0-9_-]{20,}|"
    r"Bearer\s+\S+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)",
)


class OfflineWorkerInputError(ValueError):
    """The frozen worker input is not the supported closed schema."""


@dataclass(frozen=True)
class OfflineWorkerInput:
    """Private input snapshot; callers must provide all execution inputs explicitly."""

    prompt: str
    context: str | None = None
    schema_version: str = INPUT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != INPUT_SCHEMA:
            raise OfflineWorkerInputError("unsupported input schema version")
        if type(self.prompt) is not str or not self.prompt:
            raise OfflineWorkerInputError("prompt must be a non-empty string")
        if self.context is not None and type(self.context) is not str:
            raise OfflineWorkerInputError("context must be a string or null")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "OfflineWorkerInput":
        if type(value) is not dict or set(value) != _INPUT_KEYS:
            raise OfflineWorkerInputError("input has unexpected fields")
        return cls(value["prompt"], value["context"], value["schema_version"])

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "prompt": self.prompt,
            "context": self.context,
        }


@dataclass(frozen=True)
class OfflineWorkerResult:
    """Public output projection; it never contains the private input snapshot."""

    status: WorkerStatus
    answer: dict[str, object] | None = None
    error_code: str | None = None
    error_message: str | None = None
    schema_version: str = OUTPUT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != OUTPUT_SCHEMA or self.status not in {
            "completed",
            "malformed_output",
            "timeout",
            "cancelled",
            "failed",
        }:
            raise ValueError("invalid worker output envelope")
        if self.status == "completed":
            if not validate_answer_envelope(self.answer):
                raise ValueError("completed result requires a valid answer envelope")
            if _contains_secret(self.answer):
                raise ValueError("completed result contains secret material")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("completed result cannot contain an error")
            object.__setattr__(self, "answer", _freeze_public_value(self.answer))
        elif (
            self.answer is not None
            or not _valid_public_error(self.error_code)
            or not _valid_public_error(self.error_message)
        ):
            raise ValueError("non-completed result requires a bounded error")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "answer": _thaw_public_value(self.answer),
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


def _valid_public_error(value: object) -> bool:
    return (
        type(value) is str and 0 < len(value) <= _MAX_ERROR_LENGTH and not _contains_secret(value)
    )


def _freeze_public_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_public_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_public_value(item) for item in value)
    return value


def _thaw_public_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_public_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_public_value(item) for item in value]
    return value


def _contains_secret(value: Any, key: str = "") -> bool:
    if _SECRET_KEY.search(key):
        return True
    if isinstance(value, Mapping):
        return any(_contains_secret(item, str(item_key)) for item_key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_secret(item) for item in value)
    return isinstance(value, str) and bool(_SECRET_VALUE.search(value))


def _safe_error(code: str, message: str, private_values: tuple[str, ...] = ()) -> tuple[str, str]:
    safe = " ".join(str(message).split())
    for private_value in private_values:
        if private_value:
            safe = safe.replace(private_value, "[redacted]")
    if _contains_secret(safe):
        safe = "worker failure details redacted"
    return code, safe[:_MAX_ERROR_LENGTH] or "worker failure"


def _failure(
    status: WorkerStatus,
    code: str,
    message: str,
    private_values: tuple[str, ...] = (),
) -> OfflineWorkerResult:
    safe_code, safe_message = _safe_error(code, message, private_values)
    return OfflineWorkerResult(status, error_code=safe_code, error_message=safe_message)


def _contains_private(value: Any, private_values: tuple[str, ...]) -> bool:
    if isinstance(value, str):
        return any(private_value and private_value in value for private_value in private_values)
    if isinstance(value, Mapping):
        return any(_contains_private(item, private_values) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_private(item, private_values) for item in value)
    return False


def run_offline_worker(
    request: OfflineWorkerInput | Mapping[str, Any],
    worker: Callable[[OfflineWorkerInput], Mapping[str, Any]],
) -> OfflineWorkerResult:
    """Run one injected local callable and fail closed on every invalid boundary result."""
    try:
        frozen = (
            request
            if isinstance(request, OfflineWorkerInput)
            else OfflineWorkerInput.from_dict(request)
        )
    except (TypeError, ValueError, KeyError) as exc:
        return _failure("failed", "invalid_input", str(exc))
    if not callable(worker):
        return _failure("failed", "invalid_worker", "worker is not callable")
    try:
        raw = worker(frozen)
    except asyncio.CancelledError:
        return _failure(
            "cancelled", "cancelled", "worker cancelled", (frozen.prompt, frozen.context or "")
        )
    except TimeoutError:
        return _failure(
            "timeout", "timeout", "worker timed out", (frozen.prompt, frozen.context or "")
        )
    except Exception as exc:  # noqa: BLE001 - operational boundary must be explicit.
        return _failure(
            "failed", "worker_exception", str(exc), (frozen.prompt, frozen.context or "")
        )
    if type(raw) is not dict or set(raw) != {"answer", "schema_version"}:
        return _failure(
            "malformed_output", "invalid_output_schema", "worker output schema rejected"
        )
    if raw["schema_version"] != OUTPUT_SCHEMA or not validate_answer_envelope(raw["answer"]):
        return _failure(
            "malformed_output", "invalid_answer_envelope", "worker answer envelope rejected"
        )
    if _contains_secret(raw["answer"]):
        return _failure(
            "malformed_output", "secret_material", "worker output contains secret material"
        )
    if _contains_private(raw["answer"], (frozen.prompt, frozen.context or "")):
        return _failure(
            "malformed_output", "private_material", "worker output contains private input material"
        )
    return OfflineWorkerResult("completed", answer=raw["answer"])
