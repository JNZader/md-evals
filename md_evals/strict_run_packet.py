"""Offline, hash-addressed readiness packet for a strict Gate 1 request.

This module consumes a validated ``StrictRunAssembly.v2`` artifact.  It only
checks the shape and local integrity of a pre-run checklist; it never authorizes
or performs execution.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from md_evals.strict_run_assembly import (
    StrictRunAssembly,
    StrictRunAssemblyError,
    _validate_repository,
    parse_strict_run_assembly,
)


class StrictRunPacketError(ValueError):
    """A strict pre-run packet is incomplete, contradictory, or unsafe."""


_HEX256 = re.compile(r"[0-9a-f]{64}\Z")
_SECRET_KEY = re.compile(
    r"(?:secret|token|password|credential|api[_-]?key|authorization|cookie)", re.I
)
_SECRET_VALUE = re.compile(r"(?:Bearer\s+|sk-[A-Za-z0-9]|gh[pousr]_[A-Za-z0-9]|AKIA[0-9A-Z]{16})")
_PRIVATE_KEY_MARKER = re.compile(
    r"-----BEGIN(?:\s+[A-Z0-9]+)?\s+PRIVATE KEY-----|"
    r"BEGIN\s+(?:RSA|EC|DSA|OPENSSH)\s+PRIVATE KEY|OPENSSH PRIVATE KEY",
    re.I,
)
_COMMAND = re.compile(
    r"(?:```|`|\$\s*(?:bash|sh|zsh|python|pytest|curl|git|docker|npm|uv)\b|"
    r"(?:^|\s)(?:bash|sh|zsh|python(?:3)?|pytest|curl|git|docker|npm|uv)\s+|"
    r"(?:&&|\|\||;\s*(?:bash|sh|zsh|python|pytest|curl|git|docker|npm|uv)\b)|"
    r"(?:^|[\s;&|])(?:sudo|chmod|chown)\b(?:\s|$)|"
    r"(?:^|[\s;&|])rm\s+-[rf]{1,2}(?:\s|$))",
    re.I | re.M,
)
_FORBIDDEN_BILLING = re.compile(r"catalog|estimate|estimated|pricing|price|rate|quote|cost", re.I)
_FORBIDDEN_PUBLIC_KEY = re.compile(
    r"(?:prompt|context|rendered[_-]?context|raw[_-]?response|private[_-]?context)", re.I
)
_ISO_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

CHECKLIST_IDS = (
    "provider_authenticity",
    "provider_billing",
    "final_strict_consent",
    "retry_policy",
    "fallback_policy",
    "tools_none_local_evidence",
    "independent_reviewer",
    "cleanup_deletion",
    "repository_state",
    "strict_live_execution",
)

_ITEM_KEYS = {"status", "evidence_payload", "evidence_digest"}
_TOP_KEYS = {
    "profile",
    "assembly_sha256",
    "assembly_state",
    "checklist",
    "ready_for_live_request",
    "execution_authorized",
}


def _fail(message: str) -> None:
    raise StrictRunPacketError(message)


def _canonical(value: object, label: str) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise StrictRunPacketError(f"{label} must be canonical JSON") from exc


def _digest(payload: object, label: str) -> str:
    return hashlib.sha256(_canonical(payload, label).encode()).hexdigest()


def _closed(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        _fail(f"{label} has an invalid or extra field")
    return copy.deepcopy(value)


def _closed_variants(value: object, key_sets: tuple[set[str], ...], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) not in key_sets:
        _fail(f"{label} has an invalid or extra field")
    return copy.deepcopy(value)


def _sha(value: object, label: str) -> str:
    if type(value) is not str or _HEX256.fullmatch(value) is None:
        _fail(f"{label} must be a SHA-256 digest")
    return value


def _reject_sensitive(value: object, path: str = "packet") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                _fail(f"{path} contains a non-string field")
            if _SECRET_KEY.search(key):
                _fail(f"{path}.{key} is secret-like")
            if _FORBIDDEN_PUBLIC_KEY.search(key):
                _fail(f"{path}.{key} is not allowed in a public packet")
            _reject_sensitive(child, f"{path}.{key}")
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_sensitive(child, f"{path}[{index}]")
    elif type(value) is tuple:
        for index, child in enumerate(value):
            _reject_sensitive(child, f"{path}[{index}]")
    elif type(value) is str:
        if _PRIVATE_KEY_MARKER.search(value):
            _fail(f"{path} contains private-key content")
        if _SECRET_VALUE.search(value):
            _fail(f"{path} contains a secret-like value")
        if _COMMAND.search(value):
            _fail(f"{path} contains a command or shell-like string")


def _scan_billing(value: object) -> None:
    if type(value) is str and _FORBIDDEN_BILLING.search(value):
        _fail("catalog or estimated billing evidence cannot satisfy provider billing readiness")
    if type(value) is dict:
        for child in value.values():
            _scan_billing(child)
    elif type(value) is list:
        for child in value:
            _scan_billing(child)
    elif type(value) is tuple:
        for child in value:
            _scan_billing(child)


def _text(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{label} must be a non-empty string")
    return value


def _validate_payload(payload: object, item_id: str, assembly: dict[str, Any] | None) -> None:
    if item_id == "retry_policy":
        item = _closed(payload, {"adapter_retries"}, "retry policy evidence")
        if type(item["adapter_retries"]) is not int or item["adapter_retries"] != 0:
            _fail("retry policy evidence must set adapter_retries to exact integer zero")
    elif item_id == "fallback_policy":
        item = _closed(payload, {"fallbacks"}, "fallback policy evidence")
        if type(item["fallbacks"]) is not bool or item["fallbacks"] is not False:
            _fail("fallback policy evidence must set fallbacks to exactly false")
    elif item_id == "tools_none_local_evidence":
        item = _closed_variants(
            payload,
            (
                {"tools", "mode", "enforced", "source"},
                {"tools", "mode", "enforced", "source", "evidence_digest"},
            ),
            "tools evidence",
        )
        if item["tools"] != "none" or item["mode"] != "none":
            _fail("tools evidence must declare tools and mode as none")
        if type(item["enforced"]) is not bool or item["enforced"] is not True:
            _fail("tools evidence must set enforced to exactly true")
        _text(item["source"], "tools evidence source")
        if "evidence_digest" in item:
            _sha(item["evidence_digest"], "tools evidence digest")
    elif item_id == "provider_authenticity":
        item = _closed(
            payload,
            {"provider", "model", "source", "evidence_digest"},
            "provider authenticity evidence",
        )
        for key in ("provider", "model", "source"):
            _text(item[key], f"provider authenticity {key}")
        _sha(item["evidence_digest"], "provider authenticity evidence digest")
        if assembly is not None and (
            item["provider"] != assembly["plan"]["provider"]
            or item["model"] != assembly["plan"]["model"]
        ):
            _fail("provider authenticity evidence does not match the assembly provider/model")
    elif item_id == "provider_billing":
        item = _closed_variants(
            payload,
            (
                {"provider", "model", "kind", "source", "observed_at", "charge_assertion"},
                {
                    "provider",
                    "model",
                    "kind",
                    "source",
                    "observed_at",
                    "charge_assertion",
                    "evidence_digest",
                },
                {
                    "provider",
                    "model",
                    "kind",
                    "source",
                    "observed_at",
                    "charge_assertion",
                    "authenticity_unproven_by_validator",
                },
                {
                    "provider",
                    "model",
                    "kind",
                    "source",
                    "observed_at",
                    "charge_assertion",
                    "evidence_digest",
                    "authenticity_unproven_by_validator",
                },
            ),
            "provider billing evidence",
        )
        for key in ("provider", "model", "kind", "source", "charge_assertion"):
            _text(item[key], f"provider billing {key}")
        if item["kind"] not in {"pending_live_billing", "provider_billing_evidence_recorded"}:
            _fail("provider billing evidence kind is invalid")
        if item["kind"] == "pending_live_billing" and item["charge_assertion"] != "pending":
            _fail("pending provider billing must not assert a charge")
        if item["kind"] == "provider_billing_evidence_recorded":
            if item["charge_assertion"] not in {"charged", "zero_charge"}:
                _fail("provider billing evidence is not a complete evidence record")
            if "authenticity_unproven_by_validator" not in item:
                _fail("provider billing evidence must disclose unproven authenticity")
            if item["authenticity_unproven_by_validator"] is not True:
                _fail("provider billing evidence authenticity disclosure is invalid")
        _text(item["observed_at"], "provider billing observed_at")
        if _ISO_TIMESTAMP.fullmatch(item["observed_at"]) is None:
            _fail("provider billing observed_at must be an ISO timestamp")
        if "evidence_digest" in item:
            _sha(item["evidence_digest"], "provider billing evidence digest")
        if assembly is not None and (
            item["provider"] != assembly["plan"]["provider"]
            or item["model"] != assembly["plan"]["model"]
        ):
            _fail("provider billing evidence does not match the assembly provider/model")
    elif item_id == "final_strict_consent":
        item = _closed(payload, {"subject_manifest_sha256"}, "final strict consent evidence")
        _sha(item["subject_manifest_sha256"], "final strict consent subject digest")
        if assembly is not None:
            if assembly["state"] != "finalized":
                _fail("final strict consent cannot be provided for a candidate assembly")
            if item["subject_manifest_sha256"] != assembly["consent"]["subject_manifest_sha256"]:
                _fail("final strict consent is not bound to the exact assembly subject")
    elif item_id == "independent_reviewer":
        item = _closed(payload, {"reviewer_identity"}, "independent reviewer evidence")
        _text(item["reviewer_identity"], "reviewer identity")
        if assembly is not None and item["reviewer_identity"] in {
            assembly["reviewer_metadata"]["operator_identity"],
            assembly["reviewer_metadata"]["interpretation_authority_identity"],
        }:
            _fail("independent reviewer must differ from operator and interpretation authority")
    elif item_id == "cleanup_deletion":
        item = _closed(
            payload,
            {
                "retention_policy",
                "deletion_deadline",
                "deletion_evidence_required",
                "deletion_evidence_placeholder",
            },
            "cleanup evidence",
        )
        for key in ("retention_policy", "deletion_deadline", "deletion_evidence_placeholder"):
            _text(item[key], f"cleanup evidence {key}")
        if (
            type(item["deletion_evidence_required"]) is not bool
            or item["deletion_evidence_required"] is not True
        ):
            _fail("cleanup evidence must require deletion evidence")
    elif item_id == "repository_state":
        try:
            _validate_repository(payload)
        except StrictRunAssemblyError as exc:
            raise StrictRunPacketError(
                str(exc).replace("repository state", "repository evidence", 1)
            ) from exc
    elif item_id == "strict_live_execution":
        _fail("strict live execution result is not allowed in a pre-run packet")


def _validate_item(
    item: object, item_id: str, assembly: dict[str, Any] | None = None
) -> dict[str, Any]:
    result = _closed(item, _ITEM_KEYS, f"checklist item {item_id}")
    if result["status"] not in {"pending", "provided"}:
        _fail(f"checklist item {item_id} has an invalid status")
    payload, digest = result["evidence_payload"], result["evidence_digest"]
    if result["status"] == "pending":
        if payload is not None or digest is not None:
            _fail(f"pending checklist item {item_id} cannot contain evidence")
        return result
    if payload is None or digest is None:
        _fail(f"provided checklist item {item_id} requires evidence payload and digest")
    _sha(digest, f"checklist evidence digest for {item_id}")
    if digest != _digest(payload, f"checklist evidence for {item_id}"):
        _fail(f"checklist evidence digest does not match {item_id}")
    _reject_sensitive(payload, f"checklist.{item_id}.evidence_payload")
    if item_id == "provider_billing":
        _scan_billing(payload)
    _validate_payload(payload, item_id, assembly)
    return result


def _validate_packet(manifest: object, *, raw: str | None = None) -> dict[str, Any]:
    packet = _closed(manifest, _TOP_KEYS, "strict run packet")
    if packet["profile"] != "StrictRunPacket.v1":
        _fail("unsupported strict run packet")
    _sha(packet["assembly_sha256"], "assembly_sha256")
    if packet["assembly_state"] not in {"candidate", "finalized"}:
        _fail("invalid assembly state")
    if type(packet["checklist"]) is not dict or set(packet["checklist"]) != set(CHECKLIST_IDS):
        _fail("checklist must contain every required item exactly once")
    for item_id in CHECKLIST_IDS:
        _validate_item(packet["checklist"][item_id], item_id)
    consent_status = packet["checklist"]["final_strict_consent"]["status"]
    if packet["assembly_state"] == "candidate" and consent_status != "pending":
        _fail("candidate assembly requires pending final strict consent")
    if packet["assembly_state"] == "finalized" and consent_status != "provided":
        _fail("finalized assembly requires provided final strict consent")
    # The packet deliberately stores a digest/reference only.  The assembly is
    # validated by the builder before this closed public manifest is made.
    if (
        type(packet["ready_for_live_request"]) is not bool
        or packet["ready_for_live_request"]
        != _ready_for_request(packet["checklist"], packet["assembly_state"])
        or packet["execution_authorized"] is not False
    ):
        _fail("packet readiness or execution boundary is invalid")
    if raw is not None and _canonical(packet, "strict run packet") != raw:
        _fail("strict run packet is not canonical JSON")
    return packet


def _build_manifest(assembly: StrictRunAssembly, checklist: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(assembly, StrictRunAssembly):
        _fail("assembly must be a StrictRunAssembly")
    bound = parse_strict_run_assembly(assembly.manifest_json)
    if bound.sha256 != assembly.sha256:
        _fail("assembly object digest does not match its manifest")
    if bound.to_dict()["state"] != assembly.to_dict()["state"]:
        _fail("assembly object is internally inconsistent")
    if type(checklist) is not dict or set(checklist) != set(CHECKLIST_IDS):
        _fail("checklist must contain every required item exactly once")
    assembly_manifest = bound.to_dict()
    validated = {
        item_id: _validate_item(checklist[item_id], item_id, assembly_manifest)
        for item_id in CHECKLIST_IDS
    }
    if (
        assembly_manifest["state"] == "candidate"
        and validated["final_strict_consent"]["status"] != "pending"
    ):
        _fail("candidate assembly requires pending final strict consent")
    if (
        assembly_manifest["state"] == "finalized"
        and validated["final_strict_consent"]["status"] != "provided"
    ):
        _fail("finalized assembly requires provided final strict consent")
    # Live-only evidence is intentionally pending offline.  Readiness means the
    # packet is structurally safe to present for a separate human authorization;
    # it is never execution authorization.
    ready = _ready_for_request(validated, assembly_manifest["state"])
    manifest = {
        "profile": "StrictRunPacket.v1",
        "assembly_sha256": bound.sha256,
        "assembly_state": assembly_manifest["state"],
        "checklist": validated,
        "ready_for_live_request": ready,
        "execution_authorized": False,
    }
    _reject_sensitive(manifest)
    return manifest


def _ready_for_request(checklist: dict[str, Any], assembly_state: str) -> bool:
    structural = checklist["strict_live_execution"]["status"] == "pending" and all(
        checklist[item_id]["status"] == "provided"
        for item_id in ("retry_policy", "fallback_policy", "tools_none_local_evidence")
    )
    if not structural:
        return False
    if assembly_state == "candidate":
        return True
    billing = checklist["provider_billing"]
    return (
        billing["status"] == "provided"
        and isinstance(billing["evidence_payload"], dict)
        and billing["evidence_payload"].get("kind") == "provider_billing_evidence_recorded"
        and billing["evidence_payload"].get("authenticity_unproven_by_validator") is True
    )


@dataclass(frozen=True, init=False)
class StrictRunPacket:
    """Immutable canonical pre-run packet and its SHA-256 artifact digest."""

    manifest_json: str
    sha256: str
    assembly_sha256: str

    _TOKEN = object()

    def __init__(
        self, manifest_json: str, sha256: str, assembly_sha256: str, *, _token: object = None
    ) -> None:
        if _token is not StrictRunPacket._TOKEN:
            _fail("StrictRunPacket must be created by the builder or parser")
        object.__setattr__(self, "manifest_json", manifest_json)
        object.__setattr__(self, "sha256", sha256)
        object.__setattr__(self, "assembly_sha256", assembly_sha256)

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.manifest_json)


def build_strict_run_packet(
    *, assembly: StrictRunAssembly, checklist: dict[str, Any]
) -> StrictRunPacket:
    manifest = _build_manifest(assembly, copy.deepcopy(checklist))
    raw = _canonical(manifest, "strict run packet")
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return StrictRunPacket(raw, digest, manifest["assembly_sha256"], _token=StrictRunPacket._TOKEN)


def parse_strict_run_packet(manifest_json: str) -> StrictRunPacket:
    """Parse a packet with local checks; this does not prove assembly binding."""
    if type(manifest_json) is not str:
        _fail("packet manifest must be JSON text")
    try:
        manifest = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise StrictRunPacketError("packet manifest must be JSON") from exc
    # The assembly is deliberately supplied by digest/reference only in the
    # packet. Parser validation is local; callers must explicitly validate
    # assembly binding before treating the packet as assembly-bound.
    _validate_packet(manifest, raw=manifest_json)
    digest = hashlib.sha256(manifest_json.encode()).hexdigest()
    return StrictRunPacket(
        manifest_json, digest, manifest["assembly_sha256"], _token=StrictRunPacket._TOKEN
    )


def validate_strict_run_packet_binding(
    packet: StrictRunPacket, assembly: StrictRunAssembly
) -> StrictRunPacket:
    """Prove that a locally valid packet is bound to this exact assembly artifact."""
    if not isinstance(packet, StrictRunPacket) or not isinstance(assembly, StrictRunAssembly):
        _fail("packet and assembly must be their validated artifact types")
    if hashlib.sha256(packet.manifest_json.encode()).hexdigest() != packet.sha256:
        _fail("strict run packet digest does not match its manifest")
    bound = parse_strict_run_assembly(assembly.manifest_json)
    if bound.sha256 != assembly.sha256 or packet.assembly_sha256 != assembly.sha256:
        _fail("strict run packet is not bound to this assembly")
    manifest = _validate_packet(packet.to_dict())
    assembly_manifest = bound.to_dict()
    for item_id in CHECKLIST_IDS:
        _validate_item(manifest["checklist"][item_id], item_id, assembly_manifest)
    if manifest["assembly_state"] != assembly_manifest["state"]:
        _fail("strict run packet assembly state does not match assembly")
    return packet
