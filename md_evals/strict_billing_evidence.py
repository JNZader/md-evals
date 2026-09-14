"""Offline-only billing evidence scaffolding for strict runs.

This module deliberately prepares evidence slots but never contacts a provider,
reads process credentials, or makes a charge assertion.  A provider attestation
can only be assembled later from explicit live evidence supplied by a caller.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from md_evals.captured_pilot_plan import CapturedPilotPlan


class StrictBillingEvidenceError(ValueError):
    """Billing evidence is malformed, incomplete, or unsafe."""


_HEX256 = re.compile(r"[0-9a-f]{64}\Z")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SECRET_KEY = re.compile(
    r"secret|token|password|credential|api[_-]?key|authorization|cookie|bearer|private[_-]?key",
    re.I,
)
_SECRET_VALUE = re.compile(r"Bearer\s+|sk-[A-Za-z0-9]|gh[pousr]_[A-Za-z0-9]|AKIA[0-9A-Z]{16}", re.I)
_PRIVATE_KEY = re.compile(r"raw[_-]?(?:prompt|response)|private(?:[_-]context)?|credential", re.I)
_BILLING_FORBIDDEN = re.compile(r"catalog|estimate|estimated|pricing|price|rate|quote|cost", re.I)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
# Identifier policy is narrower than response scanning: domain case names may
# contain "authorization" (for example, strict-readiness-vs-authorization),
# while the bare word remains reserved as an ambiguous credential-like label.
_IDENTIFIER_SENSITIVE_MARKER = (
    r"(?<![A-Za-z0-9])(?:raw|private|secret|password|token|credential)"
    r"(?![A-Za-z0-9])"
)
_SENSITIVE_MARKER = (
    r"(?<![A-Za-z0-9])(?:raw|private|secret|authorization|password|token|credential)"
    r"(?![A-Za-z0-9])"
)
_CREDENTIAL_LIKE_VALUE = (
    r"(?<![A-Za-z0-9])(?:sk|gh[pousr]|github_pat)[-_][A-Za-z0-9][A-Za-z0-9_-]*"
    r"(?![A-Za-z0-9])|"
    r"(?<![A-Za-z0-9])(?:AKIA|ASIA|AIDA|AROA)[0-9A-Z]{16}(?![A-Za-z0-9])"
)
_IDENTIFIER_FORBIDDEN = re.compile(
    r"\Aauthorization\Z|" + _IDENTIFIER_SENSITIVE_MARKER + r"|api[_-]?key|bearer|"
    + _CREDENTIAL_LIKE_VALUE + r"|"
    r"(?:^|[^a-z])(bash|curl|docker|git|npm|pytest|python|rm|sh|sudo|wget)(?:[^a-z]|$)|"
    r"&&|\|\||\$\(|[;\n\r]",
    re.I,
)
_RESPONSE_FORBIDDEN = re.compile(
    _SENSITIVE_MARKER + r"|headers|raw[ _-]?response|private[ _-]?context|api[ _-]?key|"
    r"bearer\s+|" + _CREDENTIAL_LIKE_VALUE + r"|"
    r"(?:^|\s)(bash|curl|docker|git|npm|pytest|python|rm|sh|sudo|wget)(?:\s|$)|"
    r"&&|\|\||\$\(|[;\n\r]|(?:^|\s)--[A-Za-z]",
    re.I,
)
_COMMAND = re.compile(
    r"(?:^|\s)(?:bash|curl|docker|git|npm|pytest|python|rm|sh|sudo|wget)(?:\s|$)|"
    r"&&|\|\||\$\(|[;\n\r]|(?:^|\s)--[A-Za-z]",
    re.I,
)

_POLICY = {
    "provider_usage_before_after": "preferred_when_safe",
    "local_request_response_ledger": "required",
    "manual_dashboard_receipt": "optional_if_available",
}
_SCAFFOLD_KEYS = {
    "schema_version", "status", "provider", "model", "plan_sha256", "created_at",
    "capture_policy", "observed_calls", "ledger", "sha256",
}
_SLOT_KEYS = {"cell_id", "case_id", "arm_id", "status", "response_digest", "usage", "observed_at"}
_ATTESTATION_KEYS = {
    "provider_charge_attested", "provider_identity", "attestation_kind", "attestation_id",
    "attested_at", "evidence_payload", "evidence_digest",
}
_LIVE_EVIDENCE_KEYS = {
    "schema_version", "evidence_origin", "provider", "model", "charge_assertion", "observed_at",
    "external_evidence_digest", "local_ledger_digest", "source_classification",
    "attestation_id", "attested_at", "authenticity_unproven_by_validator",
}


def _fail(message: str) -> None:
    raise StrictBillingEvidenceError(message)


def _canonical(value: object, label: str) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise StrictBillingEvidenceError(f"{label} must be canonical JSON") from exc


def _nonempty(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{label} is required")
    return value


def _digest(value: object, label: str) -> str:
    return hashlib.sha256(_canonical(value, label).encode()).hexdigest()


def _sha(value: object, label: str) -> str:
    if type(value) is not str or _HEX256.fullmatch(value) is None:
        _fail(f"{label} must be a SHA-256 digest")
    return value


def _timestamp(value: object, label: str) -> str:
    _nonempty(value, label)
    if _TIMESTAMP.fullmatch(value) is None:
        _fail(f"{label} must be an ISO UTC timestamp")
    return value


def _identifier(value: object, label: str) -> str:
    _nonempty(value, label)
    if _IDENTIFIER.fullmatch(value) is None or _IDENTIFIER_FORBIDDEN.search(value):
        _fail(f"{label} is not a safe identifier")
    return value


def _scan(value: object, path: str = "billing") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                _fail(f"{path} contains a non-string field")
            if _SECRET_KEY.search(key) or _PRIVATE_KEY.search(key):
                _fail(f"{path}.{key} is forbidden")
            _scan(child, f"{path}.{key}")
    elif type(value) is list:
        for index, child in enumerate(value):
            _scan(child, f"{path}[{index}]")
    elif type(value) is str and _SECRET_VALUE.search(value):
        _fail(f"{path} contains a secret-like value")


def _scan_scaffold(value: object) -> None:
    _scan(value)
    def visit(item: object, path: str = "scaffold") -> None:
        if type(item) is dict:
            for key, child in item.items():
                if _BILLING_FORBIDDEN.search(key) or key in {"charged", "zero_charge", "provider_charge_attestation"}:
                    _fail(f"{path}.{key} is not permitted in a scaffold")
                visit(child, f"{path}.{key}")
        elif type(item) is list:
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")
        elif type(item) is str and (_BILLING_FORBIDDEN.search(item) or _COMMAND.search(item)):
            _fail(f"{path} contains forbidden billing or command text")
    visit(value)


def _reject_billing_terms(value: object, path: str = "billing") -> None:
    if type(value) is dict:
        for key, child in value.items():
            _reject_billing_terms(child, f"{path}.{key}")
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_billing_terms(child, f"{path}[{index}]")
    elif type(value) is str and _BILLING_FORBIDDEN.search(value):
        _fail(f"{path} contains catalog or estimated billing text")


def _cells_from_plan(plan: CapturedPilotPlan) -> tuple[str, list[dict[str, str]]]:
    if not isinstance(plan, CapturedPilotPlan) or type(plan.manifest_json) is not str:
        _fail("plan must be a CapturedPilotPlan")
    plan_sha = _sha(plan.sha256, "plan_sha256")
    if hashlib.sha256(plan.manifest_json.encode()).hexdigest() != plan_sha:
        _fail("plan_sha256 does not match plan manifest")
    try:
        manifest = json.loads(plan.manifest_json)
    except json.JSONDecodeError as exc:
        raise StrictBillingEvidenceError("plan manifest must be JSON") from exc
    if type(manifest) is not dict or manifest.get("planned_calls") != 12:
        _fail("strict plan must contain exactly 12 cells")
    cells = [
        {"cell_id": f"{case['name']}::{arm['arm']}", "case_id": case["name"], "arm_id": arm["arm"]}
        for case in manifest.get("cases", []) for arm in case.get("arms", [])
    ]
    for cell in cells:
        _identifier(cell["case_id"], "plan case_id")
        _identifier(cell["arm_id"], "plan arm_id")
    if len(cells) != 12 or len({cell["cell_id"] for cell in cells}) != 12:
        _fail("strict plan must contain exactly 12 unique cells")
    return plan_sha, cells


def _normalise_cells(planned_cells: object) -> list[dict[str, str]]:
    if type(planned_cells) is not list:
        _fail("planned_cells must be a list")
    result: list[dict[str, str]] = []
    for cell in planned_cells:
        if type(cell) is dict and set(cell) == {"case_id", "arm_id"}:
            case_id, arm_id = cell["case_id"], cell["arm_id"]
        elif type(cell) in (tuple, list) and len(cell) == 2:
            case_id, arm_id = cell
        else:
            _fail("planned cell must contain case_id and arm_id")
        _identifier(case_id, "cell case_id")
        _identifier(arm_id, "cell arm_id")
        result.append({"cell_id": f"{case_id}::{arm_id}", "case_id": case_id, "arm_id": arm_id})
    if len(result) != 12 or len({cell["cell_id"] for cell in result}) != 12:
        _fail("scaffold must contain exactly 12 unique cells")
    return result


def build_billing_scaffold(
    *, provider: str | None = None, model: str | None = None, plan_sha256: str | None = None,
    planned_cells: list[object] | None = None, created_at: str | None = None,
    plan: CapturedPilotPlan | None = None,
) -> dict[str, Any]:
    """Build a deterministic, pending-live-execution billing ledger."""
    if plan is not None:
        plan_sha256, cells = _cells_from_plan(plan)
        manifest = plan.to_dict()
        provider = manifest.get("provider")
        model = manifest.get("model")
    else:
        _sha(plan_sha256, "plan_sha256")
        cells = _normalise_cells(planned_cells)
    _nonempty(provider, "provider")
    _nonempty(model, "model")
    _timestamp(created_at, "created_at")
    ledger = [
        {**cell, "status": "pending_live", "response_digest": None, "usage": None, "observed_at": None}
        for cell in cells
    ]
    scaffold = {
        "schema_version": "StrictBillingEvidenceScaffold.v1",
        "status": "scaffold_pending_live_execution",
        "provider": provider, "model": model, "plan_sha256": plan_sha256, "created_at": created_at,
        "capture_policy": dict(_POLICY), "observed_calls": 0, "ledger": ledger, "sha256": None,
    }
    _scan_scaffold(scaffold)
    payload = {key: scaffold[key] for key in _SCAFFOLD_KEYS if key != "sha256"}
    scaffold["sha256"] = _digest(payload, "billing scaffold")
    return scaffold


def validate_billing_scaffold(manifest: object) -> dict[str, Any]:
    """Validate and return a detached strict scaffold."""
    if type(manifest) is not dict or set(manifest) != _SCAFFOLD_KEYS:
        _fail("billing scaffold has an invalid or extra field")
    _scan_scaffold(manifest)
    if manifest["schema_version"] != "StrictBillingEvidenceScaffold.v1" or manifest["status"] != "scaffold_pending_live_execution":
        _fail("billing scaffold has an invalid schema or status")
    _nonempty(manifest["provider"], "provider")
    _nonempty(manifest["model"], "model")
    _sha(manifest["plan_sha256"], "plan_sha256")
    _timestamp(manifest["created_at"], "created_at")
    if manifest["capture_policy"] != _POLICY or manifest["observed_calls"] != 0:
        _fail("billing scaffold capture policy or observed_calls is invalid")
    ledger = manifest["ledger"]
    if type(ledger) is not list or len(ledger) != 12:
        _fail("billing scaffold ledger must contain exactly 12 slots")
    ids: set[str] = set()
    for slot in ledger:
        if type(slot) is not dict or set(slot) != _SLOT_KEYS:
            _fail("billing scaffold slot has an invalid or extra field")
        if slot["status"] != "pending_live" or slot["response_digest"] is not None or slot["usage"] is not None or slot["observed_at"] is not None:
            _fail("billing scaffold slot is not pending live")
        _identifier(slot["case_id"], "case_id")
        _identifier(slot["arm_id"], "arm_id")
        _nonempty(slot["cell_id"], "cell_id")
        if slot["cell_id"] != f"{slot['case_id']}::{slot['arm_id']}" or slot["cell_id"] in ids:
            _fail("billing scaffold cells must be unique and bound")
        ids.add(slot["cell_id"])
    payload = {key: manifest[key] for key in _SCAFFOLD_KEYS if key != "sha256"}
    if _sha(manifest["sha256"], "scaffold digest") != _digest(payload, "billing scaffold"):
        _fail("billing scaffold digest does not match")
    return json.loads(_canonical(manifest, "billing scaffold"))


def canonical_response_digest(response_payload: object) -> str:
    """Return only a digest; reject payloads that look like secret material."""
    def scan(item: object, path: str = "response_payload") -> None:
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str or _RESPONSE_FORBIDDEN.search(key):
                    _fail(f"{path} contains forbidden response text")
                scan(child, f"{path}.{key}")
        elif type(item) is list:
            for index, child in enumerate(item):
                scan(child, f"{path}[{index}]")
        elif type(item) is str and _RESPONSE_FORBIDDEN.search(item):
            _fail(f"{path} contains forbidden response text")
    scan(response_payload)
    return _digest(response_payload, "response payload")


@dataclass(frozen=True)
class StrictLiveBillingEvidenceRecord:
    """Validated live evidence input; validation does not establish authenticity."""

    schema_version: str
    evidence_origin: str
    provider: str
    model: str
    charge_assertion: str
    observed_at: str
    external_evidence_digest: str
    local_ledger_digest: str
    source_classification: str
    attestation_id: str
    attested_at: str
    authenticity_unproven_by_validator: bool

    @classmethod
    def from_dict(cls, value: object) -> "StrictLiveBillingEvidenceRecord":
        if type(value) is not dict or set(value) != _LIVE_EVIDENCE_KEYS:
            _fail("live billing evidence record has an invalid or extra field")
        _scan(value, "live_evidence")
        if value["schema_version"] != "StrictLiveBillingEvidenceRecord.v1":
            _fail("unsupported live billing evidence record")
        if re.search(r"scaffold|pending_live|offline", value["evidence_origin"], re.I) or re.search(
            r"scaffold|pending_live|offline", value["source_classification"], re.I
        ):
            _fail("scaffold or offline evidence cannot attest to a provider charge")
        for key in ("evidence_origin", "provider", "model", "source_classification", "attestation_id"):
            _nonempty(value[key], f"live evidence {key}")
        if _BILLING_FORBIDDEN.search(value["source_classification"]):
            _fail("catalog or estimated sources cannot attest to a provider charge")
        if value["charge_assertion"] not in {"charged", "zero_charge"}:
            _fail("charge_assertion must be charged or zero_charge")
        _timestamp(value["observed_at"], "live evidence observed_at")
        _timestamp(value["attested_at"], "live evidence attested_at")
        _sha(value["external_evidence_digest"], "external evidence digest")
        _sha(value["local_ledger_digest"], "local ledger digest")
        if value["authenticity_unproven_by_validator"] is not True:
            _fail("live evidence must declare authenticity is unproven by validator")
        return cls(**value)


def validate_live_billing_evidence_record(value: object) -> StrictLiveBillingEvidenceRecord:
    if isinstance(value, StrictLiveBillingEvidenceRecord):
        return StrictLiveBillingEvidenceRecord.from_dict(value.__dict__)
    return StrictLiveBillingEvidenceRecord.from_dict(value)


def build_provider_billing_attestation(
    evidence_record: StrictLiveBillingEvidenceRecord | dict[str, Any],
) -> dict[str, Any]:
    """Build assembly-compatible billing data only from a validated live record."""
    record = validate_live_billing_evidence_record(evidence_record)
    evidence = {
        "provider": record.provider, "model": record.model, "charge_assertion": record.charge_assertion,
        "source": record.source_classification, "observed_at": record.observed_at,
        "external_evidence_digest": record.external_evidence_digest,
        "local_ledger_digest": record.local_ledger_digest,
        "authenticity_unproven_by_validator": record.authenticity_unproven_by_validator,
    }
    return {
        "provider_charge_attested": False, "provider_identity": record.provider,
        "attestation_kind": "provider_billing_evidence_recorded", "attestation_id": record.attestation_id,
        "attested_at": record.attested_at, "evidence_payload": evidence,
        "evidence_digest": _digest(evidence, "billing evidence payload"),
    }


def write_billing_scaffold(scaffold: dict[str, Any], path: str | Path) -> None:
    """Write a validated scaffold without overwriting an existing file."""
    validated = validate_billing_scaffold(scaffold)
    destination = Path(path)
    if (
        not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
        or os.open not in getattr(os, "supports_dir_fd", ())
    ):
        _fail("safe billing scaffold creation is unavailable on this platform")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent_fd: int | None = None
    temporary: str | None = None
    try:
        if destination.name in {"", ".", ".."}:
            _fail("billing scaffold destination must have a basename")
        parent = destination.parent
        parent_components = parent.parts
        if destination.is_absolute():
            parent_components = parent_components[1:]
            parent_fd = os.open(destination.anchor or "/", directory_flags)
        else:
            parent_fd = os.open(".", directory_flags)
        for component in parent_components:
            if component in {".", ".."}:
                _fail("billing scaffold parent contains an unsafe component")
            next_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        temporary = f".{destination.name}.{secrets.token_hex(12)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        fd = os.open(temporary, flags, 0o600, dir_fd=parent_fd)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", errors="strict") as output:
                fd = -1
                output.write(_canonical(validated, "billing scaffold") + "\n")
                output.flush()
                os.fsync(output.fileno())
        finally:
            if fd != -1:
                os.close(fd)
        # link() publishes atomically without replacing an existing target.
        os.link(temporary, destination.name, src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd, follow_symlinks=False)
        os.unlink(temporary, dir_fd=parent_fd)
        temporary = None
        os.close(parent_fd)
        parent_fd = None
    except (FileExistsError, IsADirectoryError) as exc:
        raise StrictBillingEvidenceError("refusing to overwrite billing scaffold") from exc
    except (OSError, TypeError, ValueError) as exc:
        raise StrictBillingEvidenceError("safe billing scaffold creation failed") from exc
    finally:
        if temporary is not None and parent_fd is not None:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except OSError:
                pass
        if parent_fd is not None:
            os.close(parent_fd)
