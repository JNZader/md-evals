"""Offline, deterministic declaration of a captured four-arm pilot plan."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from md_evals.captured_answer_grader import GradingCaseError, grade_captured_answer
from md_evals.context_renderer import render_paired_context, render_selected_evidence


ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
_LEGACY_ARM = "D_UNION"
_CASE_KEYS = {"name", "prompt", "expected", "packs"}
_LIMIT_KEYS = {"max_primary_calls", "per_call_timeout_seconds", "total_timeout_seconds"}
_ID = re.compile(r"[0-9a-f]{64}")
_MAX_BYTES = 1024 * 1024


class PilotPlanError(ValueError):
    """A pilot declaration cannot be frozen into a supported offline plan."""


@dataclass(frozen=True)
class CapturedPilotPlan:
    """Immutable canonical manifest and its exact UTF-8 SHA-256 digest."""

    manifest_json: str
    sha256: str

    def to_dict(self) -> dict[str, object]:
        """Return a fresh, caller-mutable manifest copy."""
        return json.loads(self.manifest_json)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotPlanError(message)


def _canonical(value: object, message: str) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise PilotPlanError(message) from exc


def _validate_gold(cases: list[dict[str, object]]) -> None:
    for case in cases:
        try:
            grade_captured_answer("", case["expected"], [])
        except GradingCaseError as exc:
            raise PilotPlanError("invalid expected gold") from exc


def _validate_cases(cases: object) -> list[dict[str, object]]:
    _require(type(cases) is list and 1 <= len(cases) <= 3, "cases must be an ordered list of 1-3")
    _require(
        all(type(case) is dict and set(case) == _CASE_KEYS for case in cases), "invalid case schema"
    )
    _require(all(type(case["name"]) is str and case["name"] for case in cases), "invalid case name")
    _require(
        all(type(case["prompt"]) is str and case["prompt"] for case in cases), "invalid case prompt"
    )
    names = [case["name"] for case in cases]
    _require(len(names) == len(set(names)), "case names must be unique")
    _require(
        all(
            type(case["packs"]) is dict
            and set(case["packs"]) in (set(ARMS), set(ARMS) | {_LEGACY_ARM})
            for case in cases
        ),
        "invalid arm schema",
    )
    _require(
        all(case["packs"]["CONTROL"] is None for case in cases), "CONTROL must have no context"
    )
    _require(
        all(case["packs"][arm] is not None for case in cases for arm in ARMS[1:]),
        "non-CONTROL pack required",
    )
    return cases


def _validate_backend(
    provider: object, model: object, digest: object, limits: object, calls: int
) -> dict[str, int]:
    _require(type(provider) is str and bool(provider), "provider is required")
    _require(type(model) is str and bool(model), "model is required")
    _require(
        type(digest) is str and _ID.fullmatch(digest) is not None, "invalid backend config digest"
    )
    _require(type(limits) is dict and set(limits) == _LIMIT_KEYS, "invalid limits")
    _require(
        all(type(value) is int and value > 0 for value in limits.values()),
        "limits must be positive ints",
    )
    _require(
        calls <= limits["max_primary_calls"] <= 12, "max_primary_calls must bound planned calls"
    )
    return dict(limits)


def _arm_snapshot(pack: object, arm: str, seen: dict[str, dict[str, object]]) -> dict[str, object]:
    _require(type(pack) is dict, "invalid non-CONTROL pack")
    snapshot = _canonical(pack, "pack is not canonical JSON")
    try:
        if arm == "E_PAIRED":
            rendered = render_paired_context(pack)
            source_packs = (pack["structure"], pack["memory"])
            records = source_packs[0]["evidence"] + source_packs[1]["evidence"]
            repository = revision = None
        else:
            rendered = render_selected_evidence(pack)
            source_packs = (pack,)
            records = pack["evidence"]
            repository, revision = pack["repository"], pack["revision"]
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        raise PilotPlanError("unsupported pack shape") from exc
    allowed = {
        "B_STRUCTURE": {"structure"},
        "C_MEMORY": {"memory"},
        "D_UNION": {"structure", "memory"},
        "E_PAIRED": {"structure", "memory"},
    }[arm]
    if arm == "E_PAIRED":
        _require(
            all(record["kind"] == kind for kind, source in zip(("structure", "memory"), source_packs)
                for record in source["evidence"]),
            "invalid paired evidence kinds",
        )
    else:
        _require(all(record["kind"] in allowed for record in records), "invalid arm evidence kinds")
    for record in records:
        identifier = record["id"]
        _require(
            identifier not in seen or seen[identifier] == record, "conflicting repeated record ID"
        )
        seen[identifier] = record
    selected = [record["id"] for record in records]
    return {
        "arm": arm,
        "repository": repository,
        "revision": revision,
        "canonical_pack_snapshot_sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
        "selected_ids": selected,
        "rendered_context": rendered,
        "rendered_context_sha256": None
        if rendered is None
        else hashlib.sha256(rendered.encode()).hexdigest(),
    }


def _case_manifest(
    case: dict[str, object], seen: dict[str, dict[str, object]]
) -> dict[str, object]:
    arm_names = tuple(arm for arm in (*ARMS[1:], _LEGACY_ARM) if arm in case["packs"])
    arms = [_arm_snapshot(case["packs"][arm], arm, seen) for arm in arm_names]
    origins = {(item["repository"], item["revision"]) for item in arms if item["arm"] != "E_PAIRED"}
    _require(len(origins) == 1, "non-CONTROL arm origins must agree")
    return {
        "name": case["name"],
        "prompt": case["prompt"],
        "expected": case["expected"],
        "arms": [
            {
                "arm": "CONTROL",
                "repository": None,
                "revision": None,
                "canonical_pack_snapshot_sha256": None,
                "selected_ids": [],
                "rendered_context": None,
                "rendered_context_sha256": None,
            }
        ]
        + arms,
    }


def prepare_captured_pilot(
    *,
    cases: list[dict[str, object]],
    provider: str,
    model: str,
    backend_config_sha256: str,
    limits: dict[str, int],
) -> CapturedPilotPlan:
    """Freeze declarations only; this never authorizes or launches live execution."""
    declared = _validate_cases(cases)
    _validate_gold(declared)  # Intentionally precedes all renderer calls.
    planned_calls = len(declared) * (
        len(ARMS) + int(any(_LEGACY_ARM in case["packs"] for case in declared))
    )
    backend_limits = _validate_backend(
        provider, model, backend_config_sha256, limits, planned_calls
    )
    seen: dict[str, dict[str, object]] = {}
    manifest = {
        "profile": "CapturedPilotPlan.v1",
        "purpose": "conformance",
        "provider": provider,
        "model": model,
        "backend_config_sha256": backend_config_sha256,
        "limits": backend_limits,
        "repetitions": 1,
        "planned_calls": planned_calls,
        "policy": {"fallbacks": False, "adapter_retries": 0},
        "execution_authorized": False,
        "blockers": [
            "runner_admission_not_verified",
            "backend_preflight_not_verified",
            "live_execution_not_authorized",
        ],
        "required_backend_checks": [
            "pre_dispatch_provider_pin",
            "context_isolation",
            "bounded_termination",
            "observed_usage_semantics",
        ],
        "cases": [_case_manifest(case, seen) for case in declared],
    }
    manifest_json = _canonical(manifest, "manifest is not canonical JSON")
    _require(len(manifest_json.encode()) <= _MAX_BYTES, "manifest exceeds 1 MiB")
    return CapturedPilotPlan(manifest_json, hashlib.sha256(manifest_json.encode()).hexdigest())
