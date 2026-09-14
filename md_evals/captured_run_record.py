"""Offline records for an already-bound controlled capture cell.

This module deliberately stops at the injected ``complete`` callable.  It does
not know how to find, choose, retry, persist, or interpret a provider call.
"""

from __future__ import annotations

import inspect
import json
import re
from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Awaitable, Literal, Mapping, Protocol

from md_evals.models import LLMResponse

ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
EXPLICIT_UNKNOWN = "unknown"
EXPLICIT_MISSING = "missing"
NOT_APPLICABLE = "not_applicable"
PLANNED_CELL_COUNT = 12
CellState = Literal["complete", "failed", "aborted", "missing"]
RunStatus = Literal["complete", "incomplete", "inconclusive", "failed", "aborted", "missing"]
_REQUIRED = (
    "provider_pin",
    "model_pin",
    "endpoint_pin",
    "model_config_digest",
    "budget",
    "timeout",
    "operator",
    "reviewer",
    "code_revision",
    "arm_mapping_decision_id",
    "fixture_id",
    "fixture_revision",
    "route_label",
    "identity_attestation",
)
_SECRET_KEY = re.compile(
    r"(?:^|[_-])(?:password|passwd|secret|token|api[_-]?key|authorization|credential|private[_-]?key)(?:$|[_-])",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|"
    r"AKIA[0-9A-Z]{16}|Bearer\s+\S+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|"
    r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)\s*[:=]\s*\S+)"
)


class CaptureRecordError(ValueError):
    """An already-bound cell is not safe to capture."""


class CompletionOperationalError(RuntimeError):
    """Safe, factual failure from the injected completion boundary.

    Only this explicit error is converted into a failed capture row.  Its
    reason must describe the operational condition without including secrets.
    """

    def __init__(self, safe_reason: str) -> None:
        if not isinstance(safe_reason, str) or not safe_reason.strip():
            raise ValueError("safe_reason must be a non-empty string")
        self.safe_reason = safe_reason
        super().__init__(safe_reason)


class Completion(Protocol):
    def __call__(self, prompt: str, system_prompt: str | None = None) -> Awaitable[LLMResponse]: ...


@dataclass(frozen=True)
class FrozenCell:
    """All input and provenance needed to make one cell comparable."""

    cell_id: str
    task_id: str
    prompt: str
    case_id: str
    capture_number: int
    arm_id: str
    prompt_digest: str
    context_bytes: bytes
    context_digest: str
    selected_ids: tuple[str, ...]
    tools: str
    tool_configuration: str
    provider_pin: str
    model_pin: str
    endpoint_pin: str
    model_config_digest: str
    code_revision: str
    budget: str
    timeout: str
    operator: str
    reviewer: str
    arm_mapping_decision_id: str
    fixture_id: str
    fixture_revision: str
    context_size: int | str
    started_at: str
    finished_at: str
    request_id: str
    raw_output_ref: str
    state: CellState = "missing"
    factual_failure_reason: str = NOT_APPLICABLE
    route_label: str = EXPLICIT_UNKNOWN
    identity_attestation: str = EXPLICIT_UNKNOWN

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value
            for value in (self.cell_id, self.task_id, self.prompt, self.case_id)
        ):
            raise CaptureRecordError("cell identity and prompt are required")
        if self.arm_id not in ARMS:
            raise CaptureRecordError(
                "D_UNION is excluded; arm must be one of the four planned arms"
            )
        if type(self.capture_number) is not int or self.capture_number < 1:
            raise CaptureRecordError("capture_number must be a positive integer")
        if self.tools != "none" and self.arm_id == "CONTROL":
            raise CaptureRecordError("CONTROL requires tools=none")
        if not isinstance(self.context_bytes, bytes):
            raise CaptureRecordError("context_bytes must be exact bytes")
        if self.prompt_digest != sha256(self.prompt.encode()).hexdigest():
            raise CaptureRecordError("prompt digest does not match frozen prompt")
        if self.context_digest != sha256(self.context_bytes).hexdigest():
            raise CaptureRecordError("context digest does not match frozen context")
        if type(self.context_size) is not int and self.context_size not in (
            EXPLICIT_UNKNOWN,
            EXPLICIT_MISSING,
        ):
            raise CaptureRecordError("context_size must be measured or explicit unknown/missing")
        if self.state not in ("complete", "failed", "aborted", "missing"):
            raise CaptureRecordError("invalid cell state")
        if self.state in ("failed", "aborted") and not self.factual_failure_reason:
            raise CaptureRecordError("failed and aborted cells require a factual reason")
        for name in _REQUIRED:
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value
                or value in (EXPLICIT_UNKNOWN, EXPLICIT_MISSING, NOT_APPLICABLE)
            ):
                raise CaptureRecordError(f"{name} is required and cannot be unknown or missing")

    @classmethod
    def bind(cls, **values: Any) -> "FrozenCell":
        """Bind caller-supplied values; no capture decision is filled in here."""
        return cls(**values)


@dataclass(frozen=True)
class PrivateRawRecord:
    """Restricted in-memory raw record; never returned by ``public_reference``."""

    cell: FrozenCell
    response: LLMResponse | None
    raw_output_ref: str
    raw_wire_payload: str
    request_id: str
    route_label: str
    identity_attestation: str
    state: CellState
    factual_failure_reason: str

    def public_reference(self) -> "PublicCaptureReference":
        return PublicCaptureReference(
            cell_id=self.cell.cell_id,
            task_id=self.cell.task_id,
            case_id=self.cell.case_id,
            capture_number=self.cell.capture_number,
            arm_id=self.cell.arm_id,
            state=self.state,
            planned_denominator=PLANNED_CELL_COUNT,
            denominator_eligible=self.state == "complete" and self.cell.state == "complete",
            has_raw_output_ref=self.raw_output_ref not in ("", EXPLICIT_UNKNOWN, EXPLICIT_MISSING),
            outcome_ref=EXPLICIT_UNKNOWN
            if self.state != "complete"
            else "available-in-private-review",
            private_review_pointer="approved-private-review-required",
        )


@dataclass(frozen=True)
class PublicCaptureReference:
    """Privacy-minimized projection: no prompt, context, response, digest, or wire data."""

    cell_id: str
    task_id: str
    case_id: str
    capture_number: int
    arm_id: str
    state: CellState
    planned_denominator: int
    denominator_eligible: bool
    has_raw_output_ref: bool
    outcome_ref: str
    private_review_pointer: str


@dataclass(frozen=True)
class CaptureRunSummary:
    status: RunStatus
    planned_denominator: int
    complete_cells: int
    denominator_reduced: bool = False
    gate1_decision: None = None
    factual_reason: str = NOT_APPLICABLE


def _wire(response: LLMResponse | None) -> str:
    if response is None:
        return ""
    return json.dumps(plain_response(response), sort_keys=True, separators=(",", ":"))


def _plain_copy(value: Any) -> Any:
    """Return a detached, JSON-compatible container tree without proxy wrappers."""
    if isinstance(value, Mapping):
        return {_plain_copy(key): _plain_copy(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_copy(item) for item in value]
    return deepcopy(value)


def plain_response(response: LLMResponse) -> dict[str, Any]:
    """Materialize response fields without invoking Pydantic serialization."""
    return {
        field_name: _plain_copy(getattr(response, field_name))
        for field_name in type(response).model_fields
    }


def _contains_secret(value: Any, key: str = "") -> bool:
    if _SECRET_KEY.search(key):
        return True
    if isinstance(value, Mapping):
        return any(_contains_secret(item, str(item_key)) for item_key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_secret(item) for item in value)
    return isinstance(value, str) and bool(_SECRET_VALUE.search(value))


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({deepcopy(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return deepcopy(value)


def _frozen_response(response: LLMResponse) -> LLMResponse:
    snapshot = response.model_copy(deep=True)
    for field_name in type(snapshot).model_fields:
        object.__setattr__(snapshot, field_name, _freeze(getattr(snapshot, field_name)))
    return snapshot


async def capture_cell(cell: FrozenCell, complete: Completion) -> PrivateRawRecord:
    """Make exactly one injected completion call for ``cell``; failures are terminal."""
    if not callable(complete):
        raise CaptureRecordError("complete must be an injected callable")

    try:
        system_prompt = None if cell.arm_id == "CONTROL" else cell.context_bytes.decode("utf-8")
        result = complete(cell.prompt, system_prompt)
        if not inspect.isawaitable(result):
            raise CaptureRecordError("complete must return an awaitable LLMResponse")
        response = await result
    except CompletionOperationalError as exc:
        failed = replace(cell, state="failed", factual_failure_reason=exc.safe_reason)
        return PrivateRawRecord(
            failed,
            None,
            cell.raw_output_ref,
            "",
            cell.request_id,
            cell.route_label,
            cell.identity_attestation,
            "failed",
            failed.factual_failure_reason,
        )

    if not isinstance(response, LLMResponse):
        raise CaptureRecordError("complete must return LLMResponse")
    try:
        snapshot = _frozen_response(response)
        materialized_response = plain_response(response)
        if _contains_secret(materialized_response) or _contains_secret(plain_response(snapshot)):
            raise CompletionOperationalError(
                "response contains credential or secret material; retention rejected"
            )
        wire_payload = json.dumps(materialized_response, sort_keys=True, separators=(",", ":"))
        if _contains_secret(wire_payload):
            raise CompletionOperationalError(
                "serialized response contains credential or secret material; retention rejected"
            )
    except CompletionOperationalError as exc:
        failed = replace(cell, state="failed", factual_failure_reason=exc.safe_reason)
        return PrivateRawRecord(
            failed,
            None,
            cell.raw_output_ref,
            "",
            cell.request_id,
            cell.route_label,
            cell.identity_attestation,
            "failed",
            failed.factual_failure_reason,
        )
    captured = replace(cell, state="complete", factual_failure_reason=NOT_APPLICABLE)
    return PrivateRawRecord(
        captured,
        snapshot,
        cell.raw_output_ref,
        wire_payload,
        cell.request_id,
        cell.route_label,
        cell.identity_attestation,
        "complete",
        NOT_APPLICABLE,
    )


async def capture_bound_cells(
    cells: tuple[FrozenCell, ...], complete: Completion
) -> tuple[PrivateRawRecord, ...]:
    """Capture each supplied cell once, in order; this does not invent a matrix."""
    if len({cell.cell_id for cell in cells}) != len(cells):
        raise CaptureRecordError("cell_id must be unique")
    records: list[PrivateRawRecord] = []
    for cell in cells:
        records.append(await capture_cell(cell, complete))
    return tuple(records)


def summarize_run(
    records: tuple[PrivateRawRecord, ...],
    *,
    planned_cell_count: int = PLANNED_CELL_COUNT,
    run_status: RunStatus | None = None,
    factual_reason: str = NOT_APPLICABLE,
) -> CaptureRunSummary:
    if planned_cell_count != PLANNED_CELL_COUNT:
        raise CaptureRecordError("planned_cell_count is immutable and must be 12")
    if run_status in ("failed", "aborted", "inconclusive") and factual_reason in (
        "",
        NOT_APPLICABLE,
    ):
        raise CaptureRecordError("failed, aborted, and inconclusive runs require a factual reason")
    if run_status is not None and run_status not in (
        "complete",
        "incomplete",
        "inconclusive",
        "failed",
        "aborted",
        "missing",
    ):
        raise CaptureRecordError("invalid run status")
    complete = sum(record.state == "complete" for record in records)
    if run_status is None:
        if not records or all(record.state == "missing" for record in records):
            status = "missing"
        elif any(record.state == "aborted" for record in records):
            status = "aborted"
            factual_reason = next(
                record.factual_failure_reason for record in records if record.state == "aborted"
            )
        elif any(record.state == "failed" for record in records):
            status = "failed"
            factual_reason = next(
                record.factual_failure_reason for record in records if record.state == "failed"
            )
        else:
            status = (
                "complete"
                if len(records) == planned_cell_count and complete == planned_cell_count
                else "incomplete"
            )
    else:
        status = run_status
    return CaptureRunSummary(status, planned_cell_count, complete, False, None, factual_reason)
