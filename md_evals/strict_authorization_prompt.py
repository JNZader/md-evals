"""Offline generator for a non-authorizing strict live-run request.

The generated artifact is a human-facing request packet only.  It contains no
execution route, command, provider response, credential, or authorization
decision.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Sequence

from md_evals.strict_run_assembly import StrictRunAssembly
from md_evals.strict_run_packet import (
    StrictRunPacket,
    StrictRunPacketError,
    validate_strict_run_packet_binding,
)


class StrictAuthorizationRequestError(ValueError):
    """A human-facing authorization request is invalid or unsafe."""


_ISO_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_HEX256 = re.compile(r"^[0-9a-f]{64}$")
_SECRET_KEY = re.compile(
    r"(?:private[_-]?key|secret|token|password|credential|api[_-]?key|authorization|cookie)", re.I
)
_PRIVATE_CONTENT_KEY = re.compile(r"(?:prompt|context|rendered[_-]?context|raw[_-]?response)", re.I)
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

_LIVE_BLOCKERS = {
    "provider_authenticity": (
        "Provider identity and model authenticity must be verified during the separate live step."
    ),
    "provider_billing": (
        "Provider billing/authenticity evidence must be obtained during the separate live step."
    ),
    "final_strict_consent": (
        "Final strict consent must be supplied for the exact finalized assembly subject."
    ),
    "independent_reviewer": (
        "Independent reviewer execution/review must occur during the separate live step."
    ),
    "cleanup_deletion": "Cleanup and deletion evidence must be produced after the live step.",
    "repository_state": "Repository state must be captured again at execution time.",
    "strict_live_execution": "The strict retry-0/no-fallback live run has not been executed.",
}

_TOP_KEYS = {
    "profile",
    "packet_sha256",
    "assembly_sha256",
    "generated_at",
    "readiness",
    "packet_status_snapshot",
    "pending_live_blockers",
    "execution_authorized",
    "live_execution_requested",
    "contains_command",
    "answer_domain",
    "safety",
}
_READINESS_KEYS = {"ready_for_live_request", "summary"}
_BLOCKER_KEYS = {"checklist_id", "status", "reason"}
_ANSWER_KEYS = {"type", "allowed_tokens", "selected_answer"}
_SAFETY_KEYS = {"provider_network_credentials_policy", "non_authorization_notice"}

_DEFAULT_SAFETY_TEXT = (
    "Provider, network, and credentials will be touched only after a separate explicit "
    "user response."
)
_DEFAULT_NON_AUTHORIZATION = (
    "This artifact requests a human decision; it does not authorize or execute a live run."
)
_DEFAULT_ANSWER_TOKENS = ("authorize_live_run", "decline_live_run", "revise_packet")


def _fail(message: str) -> None:
    raise StrictAuthorizationRequestError(message)


def _canonical(value: object, label: str) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise StrictAuthorizationRequestError(f"{label} must be canonical JSON") from exc


def _closed(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        _fail(f"{label} has an invalid or extra field")
    return copy.deepcopy(value)


def _scan_unsafe(value: object, path: str = "artifact") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                _fail(f"{path} contains a non-string field")
            allowed_safety_key = path == "artifact.safety" and key in _SAFETY_KEYS
            if (
                not allowed_safety_key and key != "allowed_tokens" and _SECRET_KEY.search(key)
            ) or _PRIVATE_CONTENT_KEY.search(key):
                _fail(f"{path}.{key} is not allowed in an authorization artifact")
            _scan_unsafe(child, f"{path}.{key}")
    elif type(value) in (list, tuple):
        for index, child in enumerate(value):
            _scan_unsafe(child, f"{path}[{index}]")
    elif type(value) is str:
        if _PRIVATE_KEY_MARKER.search(value):
            _fail(f"{path} contains private-key content")
        if _COMMAND.search(value):
            _fail(f"{path} contains a command or shell-like string")


def _validate_manifest(manifest: object, *, raw: str | None = None) -> dict[str, Any]:
    result = _closed(manifest, _TOP_KEYS, "authorization request")
    if result["profile"] != "StrictAuthorizationRequest.v1":
        _fail("unsupported strict authorization request")
    for key in ("packet_sha256", "assembly_sha256"):
        if type(result[key]) is not str or _HEX256.fullmatch(result[key]) is None:
            _fail(f"{key} must be a SHA-256 digest")
    if (
        type(result["generated_at"]) is not str
        or _ISO_TIMESTAMP.fullmatch(result["generated_at"]) is None
    ):
        _fail("generated_at must be an ISO timestamp supplied by the caller")
    readiness = _closed(result["readiness"], _READINESS_KEYS, "readiness")
    if (
        readiness["ready_for_live_request"] is not True
        or type(readiness["summary"]) is not str
        or not readiness["summary"]
    ):
        _fail("authorization request readiness is invalid")
    snapshot = result["packet_status_snapshot"]
    if type(snapshot) is not dict or set(snapshot) != set(_LIVE_BLOCKERS):
        _fail("packet status snapshot must contain every live blocker exactly once")
    for checklist_id, status in snapshot.items():
        if type(status) is not str or status not in {"pending", "provided"}:
            _fail("packet status snapshot contains an invalid status")
    if snapshot["strict_live_execution"] != "pending":
        _fail("strict live execution must remain pending")
    blockers = result["pending_live_blockers"]
    if type(blockers) is not list:
        _fail("pending_live_blockers must be a list")
    expected_ids = {
        checklist_id for checklist_id, status in snapshot.items() if status == "pending"
    }
    blocker_ids = set()
    for blocker in blockers:
        item = _closed(blocker, _BLOCKER_KEYS, "pending live blocker")
        if (
            item["checklist_id"] not in _LIVE_BLOCKERS
            or item["status"] != "pending"
            or item["reason"] != _LIVE_BLOCKERS[item["checklist_id"]]
        ):
            _fail("pending live blocker is invalid or marked complete")
        if item["checklist_id"] in blocker_ids:
            _fail("pending live blockers must be unique")
        blocker_ids.add(item["checklist_id"])
    if blocker_ids != expected_ids:
        _fail("pending live blockers do not match the packet status snapshot")
    if (
        result["execution_authorized"] is not False
        or result["live_execution_requested"] is not False
        or result["contains_command"] is not False
    ):
        _fail("authorization boundary flags must all be false")
    answer = _closed(result["answer_domain"], _ANSWER_KEYS, "answer domain")
    if (
        answer["type"] != "closed_choice"
        or type(answer["allowed_tokens"]) is not list
        or tuple(answer["allowed_tokens"]) != _DEFAULT_ANSWER_TOKENS
        or answer["selected_answer"] is not None
    ):
        _fail("answer domain must be closed and must not choose an answer")
    safety = _closed(result["safety"], _SAFETY_KEYS, "safety text")
    if (
        safety["provider_network_credentials_policy"] != _DEFAULT_SAFETY_TEXT
        or safety["non_authorization_notice"] != _DEFAULT_NON_AUTHORIZATION
    ):
        _fail("authorization safety text is invalid")
    _scan_unsafe(result)
    if raw is not None and _canonical(result, "authorization request") != raw:
        _fail("authorization request is not canonical JSON")
    return result


@dataclass(frozen=True, init=False)
class StrictAuthorizationRequest:
    """Immutable canonical human-facing request artifact and digest."""

    manifest_json: str
    sha256: str

    _TOKEN = object()

    def __init__(self, manifest_json: str, sha256: str, *, _token: object = None) -> None:
        if _token is not StrictAuthorizationRequest._TOKEN:
            _fail("StrictAuthorizationRequest must be created by the builder or parser")
        object.__setattr__(self, "manifest_json", manifest_json)
        object.__setattr__(self, "sha256", sha256)

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.manifest_json)


def build_strict_authorization_request(
    *,
    packet: StrictRunPacket,
    assembly: StrictRunAssembly,
    generated_at: str,
    safety_text: str = _DEFAULT_SAFETY_TEXT,
    answer_tokens: Sequence[str] = _DEFAULT_ANSWER_TOKENS,
) -> StrictAuthorizationRequest:
    """Build a deterministic request after proving packet/assembly binding."""
    try:
        bound = validate_strict_run_packet_binding(packet, assembly)
    except StrictRunPacketError as exc:
        raise StrictAuthorizationRequestError(str(exc)) from exc
    packet_manifest = bound.to_dict()
    _scan_unsafe(packet_manifest, "packet")
    if packet_manifest["ready_for_live_request"] is not True:
        _fail("packet is not ready for a live authorization request")
    if type(generated_at) is not str or _ISO_TIMESTAMP.fullmatch(generated_at) is None:
        _fail("generated_at must be an ISO timestamp supplied by the caller")
    _scan_unsafe(safety_text, "options.safety_text")
    _scan_unsafe(tuple(answer_tokens), "options.answer_tokens")
    if safety_text != _DEFAULT_SAFETY_TEXT or tuple(answer_tokens) != _DEFAULT_ANSWER_TOKENS:
        _fail("authorization options must use the closed safe defaults")
    pending = [
        {"checklist_id": item_id, "status": "pending", "reason": _LIVE_BLOCKERS[item_id]}
        for item_id in _LIVE_BLOCKERS
        if packet_manifest["checklist"][item_id]["status"] == "pending"
    ]
    packet_status_snapshot = {
        item_id: packet_manifest["checklist"][item_id]["status"] for item_id in _LIVE_BLOCKERS
    }
    manifest = {
        "profile": "StrictAuthorizationRequest.v1",
        "packet_sha256": bound.sha256,
        "assembly_sha256": assembly.sha256,
        "generated_at": generated_at,
        "readiness": {
            "ready_for_live_request": True,
            "summary": "Strict packet is ready for a separate human live-authorization decision.",
        },
        "packet_status_snapshot": packet_status_snapshot,
        "pending_live_blockers": pending,
        "execution_authorized": False,
        "live_execution_requested": False,
        "contains_command": False,
        "answer_domain": {
            "type": "closed_choice",
            "allowed_tokens": list(_DEFAULT_ANSWER_TOKENS),
            "selected_answer": None,
        },
        "safety": {
            "provider_network_credentials_policy": _DEFAULT_SAFETY_TEXT,
            "non_authorization_notice": _DEFAULT_NON_AUTHORIZATION,
        },
    }
    _validate_manifest(manifest)
    raw = _canonical(manifest, "authorization request")
    return StrictAuthorizationRequest(
        raw, hashlib.sha256(raw.encode()).hexdigest(), _token=StrictAuthorizationRequest._TOKEN
    )


def parse_strict_authorization_request(manifest_json: str) -> StrictAuthorizationRequest:
    if type(manifest_json) is not str:
        _fail("authorization request manifest must be JSON text")
    try:
        manifest = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise StrictAuthorizationRequestError(
            "authorization request manifest must be JSON"
        ) from exc
    _validate_manifest(manifest, raw=manifest_json)
    return StrictAuthorizationRequest(
        manifest_json,
        hashlib.sha256(manifest_json.encode()).hexdigest(),
        _token=StrictAuthorizationRequest._TOKEN,
    )
