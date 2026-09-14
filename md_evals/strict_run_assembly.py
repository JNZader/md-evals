"""Offline, schema-first preparation contract for a strict Gate 1 run.

This module only validates and assembles data.  It has no execution dependency
and every artifact produced here remains explicitly blocked from execution.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from md_evals.captured_pilot_plan import CapturedPilotPlan
from md_evals.strict_billing_evidence import validate_billing_scaffold


class StrictRunAssemblyError(ValueError):
    """A strict-run declaration is missing, contradictory, or unsafe."""


_SHA256 = re.compile(r"(?:sha256:)?[0-9a-f]{64}\Z")
_HEX256 = re.compile(r"[0-9a-f]{64}\Z")
_SECRET_KEY = re.compile(
    r"(?:secret|token|password|credential|api[_-]?key|authorization|cookie)", re.I
)
_SECRET_VALUE = re.compile(r"(?:Bearer\s+|sk-[A-Za-z0-9]|gh[pousr]_[A-Za-z0-9]|AKIA[0-9A-Z]{16})")
_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_SENSITIVE_PATH_BASENAME = re.compile(
    r"(?:secret|credential|token|password|id_rsa|id_ed25519|\.pem|\.key|"
    r"(?:^|[-_.])(?:api[_-]?key|private[_-]?key|key)(?:$|[-_.]))",
    re.I,
)
_GIT_STATUS_CHARS = frozenset(" MADRCUT?!")
_BILLING_FORBIDDEN = re.compile(r"catalog|estimate|estimated|pricing|price|rate|quote|cost", re.I)
_ISO_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SCOPED_DIRTY_SCOPE = "scoped_relevant_files_with_global_dirty_disclosure"
_SCOPED_DIRTY_KEYS = {
    "clean",
    "revision",
    "digest",
    "captured_at",
    "scope",
    "worktree_clean",
    "status_short_count",
    "relevant_files",
}
_SCOPED_DIRTY_FILE_KEYS = {"path", "git_status", "bytes", "sha256"}
_ARM_KEYS = {
    "arm",
    "repository",
    "revision",
    "canonical_pack_snapshot_sha256",
    "selected_ids",
    "rendered_context",
    "rendered_context_sha256",
}
_PLAN_KEYS = {
    "profile",
    "purpose",
    "provider",
    "model",
    "backend_config_sha256",
    "limits",
    "repetitions",
    "planned_calls",
    "policy",
    "execution_authorized",
    "blockers",
    "required_backend_checks",
    "cases",
}
_CASE_KEYS = {"name", "prompt", "expected", "arms"}
_LIMIT_KEYS = {"max_primary_calls", "per_call_timeout_seconds", "total_timeout_seconds"}
_POLICY_KEYS = {"fallbacks", "adapter_retries"}
_TOP_KEYS = {
    "profile",
    "state",
    "plan_manifest_sha256",
    "plan",
    "gold_reference",
    "reviewer_metadata",
    "billing_scaffold",
    "provider_billing_attestation",
    "repository_state",
    "cleanup_declaration",
    "consent",
    "execution_authorized",
}


def _fail(message: str) -> None:
    raise StrictRunAssemblyError(message)


def _exact_int(value: object, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or (positive and value <= 0):
        _fail(f"{label} must be an exact {'positive ' if positive else ''}integer")
    return value


def _exact_bool(value: object, label: str, expected: bool | None = None) -> bool:
    if type(value) is not bool or (expected is not None and value is not expected):
        _fail(
            f"{label} must be exactly {expected}"
            if expected is not None
            else f"{label} must be boolean"
        )
    return value


def _sha(value: object, label: str, *, hex_only: bool = False) -> str:
    pattern = _HEX256 if hex_only else _SHA256
    if type(value) is not str or pattern.fullmatch(value) is None:
        _fail(f"{label} must be a SHA-256 digest")
    return value


def _canonical(value: object, label: str) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise StrictRunAssemblyError(f"{label} must be canonical JSON") from exc


def _closed(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        _fail(f"{label} has an invalid or extra field")
    return copy.deepcopy(value)


def _nonempty(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{label} is required")
    return value


def _reject_secrets(value: object, path: str = "manifest") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                _fail(f"{path} contains a non-string field")
            if _SECRET_KEY.search(key):
                _fail(f"{path}.{key} is secret-like")
            _reject_secrets(child, f"{path}.{key}")
    elif type(value) in (list, tuple):
        for index, child in enumerate(value):
            _reject_secrets(child, f"{path}[{index}]")
    elif type(value) is str and _SECRET_VALUE.search(value):
        _fail(f"{path} contains a secret-like value")


def _validate_scoped_path(path: object) -> str:
    if type(path) is not str or not path or path.startswith(("/", "\\")):
        _fail("repository relevant file path must be relative and normalized")
    if "\\" in path or _DRIVE_PREFIX.match(path) is not None:
        _fail("repository relevant file path must be relative and normalized")
    normalized = PurePosixPath(path).as_posix()
    if normalized != path or any(part in {"", ".", ".."} for part in path.split("/")):
        _fail("repository relevant file path must be relative and normalized")
    basename = PurePosixPath(path).name
    if (
        basename == ".env"
        or basename.startswith(".env.")
        or _SENSITIVE_PATH_BASENAME.search(basename) is not None
    ):
        _fail("repository relevant file path is sensitive")
    return path


def _validate_git_status(value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 2
        or not any(char != " " for char in value)
        or any(char not in _GIT_STATUS_CHARS for char in value)
    ):
        _fail("repository relevant file git_status must be a safe porcelain status token")
    return value


def _validate_arm(value: object) -> dict[str, Any]:
    arm = _closed(value, _ARM_KEYS, "strict plan arm")
    label = arm["arm"]
    if type(label) is not str or label not in {"CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED"}:
        _fail("strict plan arm has an unsupported arm label")
    if label == "CONTROL":
        if (
            any(
                arm[key] is not None
                for key in (
                    "repository",
                    "revision",
                    "canonical_pack_snapshot_sha256",
                    "rendered_context",
                    "rendered_context_sha256",
                )
            )
            or arm["selected_ids"] != []
        ):
            _fail("CONTROL arm must contain no context")
        return arm
    if label in {"B_STRUCTURE", "C_MEMORY"}:
        _nonempty(arm["repository"], f"{label} repository")
        _nonempty(arm["revision"], f"{label} revision")
    elif arm["repository"] is not None or arm["revision"] is not None:
        _fail("E_PAIRED arm must not have repository or revision")
    _sha(arm["canonical_pack_snapshot_sha256"], f"{label} pack snapshot digest")
    ids = arm["selected_ids"]
    if (
        type(ids) is not list
        or not ids
        or any(type(item) is not str or _HEX256.fullmatch(item) is None for item in ids)
        or len(ids) != len(set(ids))
    ):
        _fail(f"{label} selected IDs must be unique 64-hex strings")
    context = arm["rendered_context"]
    if type(context) is not str or not context:
        _fail(f"{label} rendered context is required")
    digest = _sha(arm["rendered_context_sha256"], f"{label} rendered context digest")
    if hashlib.sha256(context.encode()).hexdigest() != digest:
        _fail(f"{label} rendered context digest does not match rendered context")
    return arm


def _bind_plan(plan: CapturedPilotPlan) -> tuple[dict[str, Any], str]:
    if not isinstance(plan, CapturedPilotPlan) or type(plan.manifest_json) is not str:
        _fail("plan must be a CapturedPilotPlan")
    digest = _sha(plan.sha256, "plan digest", hex_only=True)
    if hashlib.sha256(plan.manifest_json.encode()).hexdigest() != digest:
        _fail("plan digest does not match manifest JSON")
    try:
        manifest = json.loads(plan.manifest_json)
    except json.JSONDecodeError as exc:
        raise StrictRunAssemblyError("plan manifest is not JSON") from exc
    return _validate_plan(manifest, plan.manifest_json, digest), digest


def _validate_plan(
    manifest: object, raw: str | None = None, digest: str | None = None
) -> dict[str, Any]:
    plan = _closed(manifest, _PLAN_KEYS, "captured pilot plan")
    if raw is not None and _canonical(plan, "plan manifest") != raw:
        _fail("plan manifest is not canonical")
    if plan["profile"] != "CapturedPilotPlan.v1" or type(plan["purpose"]) is not str:
        _fail("unsupported captured pilot plan")
    for key in ("provider", "model", "purpose"):
        _nonempty(plan[key], f"plan {key}")
    _sha(plan["backend_config_sha256"], "backend config digest", hex_only=True)
    limits = _closed(plan["limits"], _LIMIT_KEYS, "plan limits")
    for value in limits.values():
        _exact_int(value, "plan limit", positive=True)
    if type(plan["repetitions"]) is not int:
        _fail("plan is not permanently blocked or has invalid repetitions")
    _exact_int(plan["repetitions"], "repetitions")
    if plan["repetitions"] != 1:
        _fail("plan is not permanently blocked or has invalid repetitions")
    _exact_int(plan["planned_calls"], "planned_calls")
    if plan["planned_calls"] != 12:
        _fail("strict plan must contain exactly 12 cells")
    policy = _closed(plan["policy"], _POLICY_KEYS, "strict plan policy")
    if type(policy["adapter_retries"]) is not int or type(policy["fallbacks"]) is not bool:
        _fail("strict plan policy must be retry-0 and fallback-disabled")
    _exact_int(policy["adapter_retries"], "adapter retries")
    if policy["adapter_retries"] != 0 or policy["fallbacks"] is not False:
        _fail("strict plan policy must be retry-0 and fallback-disabled")
    _exact_bool(plan["execution_authorized"], "plan execution_authorized", False)
    for key in ("blockers", "required_backend_checks"):
        if type(plan[key]) is not list or not all(type(item) is str and item for item in plan[key]):
            _fail(f"plan {key} must be a list of strings")
    cases = plan["cases"]
    if type(cases) is not list or len(cases) != 3:
        _fail("strict plan must contain exactly three cases")
    names = set()
    for case in cases:
        item = _closed(case, _CASE_KEYS, "plan case")
        _nonempty(item["name"], "plan case name")
        if item["name"] in names:
            _fail("plan case names must be unique")
        names.add(item["name"])
        _nonempty(item["prompt"], "plan case prompt")
        expected = item["expected"]
        if (
            type(expected) is not dict
            or set(expected) != {"answer", "citations", "abstain"}
            or type(expected["abstain"]) is not bool
            or type(expected["citations"]) is not list
            or not all(type(x) is str and _HEX256.fullmatch(x) for x in expected["citations"])
            or len(expected["citations"]) != len(set(expected["citations"]))
        ):
            _fail("plan case expected gold has an invalid schema")
        if expected["abstain"] is False and (
            type(expected["answer"]) is not str or not expected["answer"]
        ):
            _fail("plan case expected answer is required")
        if expected["abstain"] is True and (
            expected["answer"] is not None or expected["citations"] != []
        ):
            _fail("plan case abstention has invalid gold")
        arms = item["arms"]
        if type(arms) is not list or len(arms) != 4:
            _fail("strict plan arms must contain exactly four well-formed entries")
        validated = [_validate_arm(arm) for arm in arms]
        if {arm["arm"] for arm in validated} != {"CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED"}:
            _fail("strict plan must represent exactly four supported arms")
        item["arms"] = validated
    if (
        plan["planned_calls"] != len(cases) * 4
        or limits["max_primary_calls"] < plan["planned_calls"]
    ):
        _fail("strict plan must contain exactly 12 cells")
    _reject_secrets(plan)
    return plan


def _payload_digest(payload: object, label: str) -> str:
    return hashlib.sha256(_canonical(payload, label).encode()).hexdigest()


def _validate_gold(value: object, names: set[str]) -> dict[str, Any]:
    result = _closed(
        value,
        {"version", "source_artifact", "per_task_references", "scoring_policy", "digest"},
        "gold/reference",
    )
    _nonempty(result["version"], "gold version")
    source = _closed(
        result["source_artifact"],
        {"schema", "source_id", "artifact_digest", "artifact_payload"},
        "gold source artifact",
    )
    _nonempty(source["schema"], "gold source schema")
    _nonempty(source["source_id"], "gold source ID")
    _sha(source["artifact_digest"], "gold source artifact digest", hex_only=True)
    if source["artifact_payload"] is None:
        _fail("gold source artifact payload is required")
    if source["artifact_digest"] != _payload_digest(
        source["artifact_payload"], "gold source artifact payload"
    ):
        _fail("gold source artifact digest does not match payload")
    result["source_artifact"] = source
    refs = result["per_task_references"]
    if type(refs) is not dict or set(refs) != names:
        _fail("gold references must cover every plan case")
    for name, reference in refs.items():
        item = _closed(
            reference,
            {"reference_digest", "reference_label", "annotation_policy", "reference_payload"},
            f"gold reference for {name}",
        )
        _sha(item["reference_digest"], f"gold reference digest for {name}", hex_only=True)
        _nonempty(item["reference_label"], f"gold reference label for {name}")
        _nonempty(item["annotation_policy"], f"annotation policy for {name}")
        if item["reference_payload"] is None:
            _fail(f"gold reference payload is required for {name}")
        if item["reference_digest"] != _payload_digest(
            item["reference_payload"], f"gold reference payload for {name}"
        ):
            _fail(f"gold reference digest does not match payload for {name}")
        refs[name] = item
    _nonempty(result["scoring_policy"], "scoring policy")
    _sha(result["digest"], "gold digest", hex_only=True)
    payload = {
        key: result[key]
        for key in ("version", "source_artifact", "per_task_references", "scoring_policy")
    }
    if (
        result["digest"]
        != hashlib.sha256(_canonical(payload, "gold/reference").encode()).hexdigest()
    ):
        _fail("gold digest does not match gold/reference content")
    _reject_secrets(result, "gold_reference")
    return result


def _validate_declarations(
    manifest: object, *, state: str, subject: str | None = None, raw: str | None = None
) -> dict[str, Any]:
    result = _closed(manifest, _TOP_KEYS, "strict assembly")
    if result["profile"] != "StrictRunAssembly.v2":
        _fail("candidate is not a StrictRunAssembly.v2 artifact")
    if result["state"] != state:
        _fail("strict assembly has an invalid state")
    _exact_bool(result["execution_authorized"], "execution_authorized", False)
    _sha(result["plan_manifest_sha256"], "plan_manifest_sha256", hex_only=True)
    plan = _validate_plan(result["plan"])
    plan_raw = _canonical(plan, "embedded plan")
    if result["plan_manifest_sha256"] != hashlib.sha256(plan_raw.encode()).hexdigest():
        _fail("plan_manifest_sha256 does not match embedded plan")
    names = {case["name"] for case in plan["cases"]}
    result["gold_reference"] = _validate_gold(result["gold_reference"], names)
    result["reviewer_metadata"] = _validate_review(result["reviewer_metadata"])
    result["billing_scaffold"] = _validate_scaffold(
        result["billing_scaffold"],
        plan_sha=result["plan_manifest_sha256"],
        plan_provider=plan["provider"],
        plan_model=plan["model"],
    )
    if state == "candidate":
        if result["provider_billing_attestation"] is not None:
            _fail("candidate cannot contain final provider billing evidence")
    else:
        result["provider_billing_attestation"] = _validate_billing(
            result["provider_billing_attestation"],
            plan_provider=plan["provider"],
            plan_model=plan["model"],
        )
    result["repository_state"] = _validate_repository(result["repository_state"])
    result["cleanup_declaration"] = _validate_cleanup(result["cleanup_declaration"])
    consent = _closed(result["consent"], {"required", "subject_manifest_sha256"}, "consent")
    _exact_bool(consent["required"], "consent required", True)
    if state == "candidate" and consent["subject_manifest_sha256"] is not None:
        _fail("candidate is already finalized")
    if state == "finalized":
        _sha(consent["subject_manifest_sha256"], "consent subject digest", hex_only=True)
        if consent["subject_manifest_sha256"] != subject:
            _fail("consent subject does not match candidate digest")
    _reject_secrets(result)
    if raw is not None and _canonical(result, "strict assembly") != raw:
        _fail("strict assembly is not canonical JSON")
    return result


def _validate_review(value: object) -> dict[str, Any]:
    result = _closed(
        value,
        {"operator_identity", "reviewer_identity", "interpretation_authority_identity"},
        "reviewer metadata",
    )
    for key, item in result.items():
        _nonempty(item, key)
    if result["reviewer_identity"] in {
        result["operator_identity"],
        result["interpretation_authority_identity"],
    }:
        _fail("reviewer must be independent")
    return result


def _validate_scaffold(
    value: object, *, plan_sha: str, plan_provider: str, plan_model: str
) -> dict[str, Any]:
    try:
        result = validate_billing_scaffold(value)
    except ValueError as exc:
        _fail(str(exc))
    if (
        result["plan_sha256"] != plan_sha
        or result["provider"] != plan_provider
        or result["model"] != plan_model
    ):
        _fail("billing scaffold is not bound to the plan")
    return result


def _validate_billing(value: object, *, plan_provider: str, plan_model: str) -> dict[str, Any]:
    result = _closed(
        value,
        {
            "provider_charge_attested",
            "provider_identity",
            "attestation_kind",
            "attestation_id",
            "attested_at",
            "evidence_payload",
            "evidence_digest",
        },
        "billing attestation",
    )

    def scan(item: object) -> None:
        if type(item) is str and _BILLING_FORBIDDEN.search(item):
            _fail("catalog or estimated billing evidence cannot attest to a provider charge")
        if type(item) is dict:
            for child in item.values():
                scan(child)
        elif type(item) is list:
            for child in item:
                scan(child)

    scan(result)
    _exact_bool(result["provider_charge_attested"], "provider charge attestation", False)
    _nonempty(result["provider_identity"], "billing provider identity")
    if result["provider_identity"] != plan_provider:
        _fail("billing provider identity does not match plan provider")
    if result["attestation_kind"] != "provider_billing_evidence_recorded":
        _fail("billing evidence kind is invalid")
    for key in ("attestation_id", "attested_at"):
        _nonempty(result[key], f"billing {key}")
    if _ISO_TIMESTAMP.fullmatch(result["attested_at"]) is None:
        _fail("billing attested_at must be an ISO timestamp")
    evidence = _closed(
        result["evidence_payload"],
        {
            "provider",
            "model",
            "charge_assertion",
            "source",
            "observed_at",
            "external_evidence_digest",
            "local_ledger_digest",
            "authenticity_unproven_by_validator",
        },
        "billing evidence payload",
    )
    if evidence["provider"] != plan_provider or evidence["model"] != plan_model:
        _fail("billing evidence provider/model does not match plan")
    if evidence["charge_assertion"] not in {"charged", "zero_charge"}:
        _fail("billing charge assertion is invalid")
    for key in ("provider", "model", "source", "observed_at"):
        _nonempty(evidence[key], f"billing evidence {key}")
    if _ISO_TIMESTAMP.fullmatch(evidence["observed_at"]) is None:
        _fail("billing evidence observed_at must be an ISO timestamp")
    _sha(evidence["external_evidence_digest"], "external evidence digest", hex_only=True)
    _sha(evidence["local_ledger_digest"], "local ledger digest", hex_only=True)
    _exact_bool(
        evidence["authenticity_unproven_by_validator"],
        "billing authenticity_unproven_by_validator",
        True,
    )
    result["evidence_payload"] = evidence
    _sha(result["evidence_digest"], "billing evidence digest", hex_only=True)
    if result["evidence_digest"] != _payload_digest(evidence, "billing evidence payload"):
        _fail("billing evidence digest does not match payload")
    return result


def _validate_repository(value: object, *, digest_hex_only: bool = False) -> dict[str, Any]:
    if type(value) is not dict:
        _fail("repository state has an invalid or extra field")
    keys = set(value)
    if keys == {"clean", "revision", "digest", "captured_at"}:
        result = _closed(value, keys, "repository state")
        _exact_bool(result["clean"], "repository clean", True)
        _nonempty(result["revision"], "repository revision")
        _sha(result["digest"], "repository digest", hex_only=digest_hex_only)
        _nonempty(result["captured_at"], "repository captured timestamp")
        return result
    if keys != _SCOPED_DIRTY_KEYS:
        _fail("repository state has an invalid or extra field")

    result = _closed(value, _SCOPED_DIRTY_KEYS, "repository state")
    _exact_bool(result["clean"], "repository clean", False)
    _nonempty(result["revision"], "repository revision")
    _sha(result["digest"], "repository digest", hex_only=True)
    _nonempty(result["captured_at"], "repository captured timestamp")
    if result["scope"] != _SCOPED_DIRTY_SCOPE:
        _fail("repository dirty scope is invalid")
    _exact_bool(result["worktree_clean"], "repository worktree_clean", False)
    _exact_int(result["status_short_count"], "repository status_short_count", positive=True)

    files = result["relevant_files"]
    if type(files) is not list or not files:
        _fail("repository relevant_files must be a non-empty list")
    for entry in files:
        item = _closed(entry, _SCOPED_DIRTY_FILE_KEYS, "repository relevant file")
        _validate_scoped_path(item["path"])
        _validate_git_status(item["git_status"])
        _exact_int(item["bytes"], "repository relevant file bytes", positive=True)
        _sha(item["sha256"], "repository relevant file sha256", hex_only=True)

    payload = {key: result[key] for key in _SCOPED_DIRTY_KEYS if key != "digest"}
    if result["digest"] != _payload_digest(payload, "scoped dirty repository state"):
        _fail("repository digest does not match scoped dirty payload")
    return result


def _validate_cleanup(value: object) -> dict[str, Any]:
    result = _closed(
        value,
        {
            "retention_policy",
            "deletion_deadline",
            "deletion_evidence_required",
            "deletion_evidence_placeholder",
        },
        "cleanup declaration",
    )
    for key in ("retention_policy", "deletion_deadline", "deletion_evidence_placeholder"):
        _nonempty(result[key], key)
    _exact_bool(result["deletion_evidence_required"], "deletion evidence required", True)
    return result


@dataclass(frozen=True, init=False)
class StrictRunAssembly:
    """An immutable canonical manifest and its artifact digest."""

    manifest_json: str
    sha256: str
    plan_sha256: str

    _TOKEN = object()

    def __init__(
        self, manifest_json: str, sha256: str, plan_sha256: str, *, _token: object = None
    ) -> None:
        if _token is not StrictRunAssembly._TOKEN:
            _fail("StrictRunAssembly must be created by the builder or parser")
        object.__setattr__(self, "manifest_json", manifest_json)
        object.__setattr__(self, "sha256", sha256)
        object.__setattr__(self, "plan_sha256", plan_sha256)

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.manifest_json)


def build_strict_run_assembly(
    *,
    plan: CapturedPilotPlan,
    gold_reference: dict[str, Any],
    reviewer_metadata: dict[str, str],
    billing_scaffold: dict[str, Any] | None = None,
    billing_attestation: dict[str, Any] | None = None,
    repository_state: dict[str, Any],
    cleanup_declaration: dict[str, Any],
) -> StrictRunAssembly:
    if billing_scaffold is None:
        billing_scaffold = billing_attestation
    if billing_scaffold is None:
        _fail("billing_scaffold is required before live execution")
    plan_manifest, plan_digest = _bind_plan(plan)
    names = {case["name"] for case in plan_manifest["cases"]}
    manifest = {
        "profile": "StrictRunAssembly.v2",
        "state": "candidate",
        "plan_manifest_sha256": plan_digest,
        "plan": plan_manifest,
        "gold_reference": _validate_gold(gold_reference, names),
        "reviewer_metadata": _validate_review(reviewer_metadata),
        "billing_scaffold": _validate_scaffold(
            billing_scaffold,
            plan_sha=plan_digest,
            plan_provider=plan_manifest["provider"],
            plan_model=plan_manifest["model"],
        ),
        "provider_billing_attestation": None,
        "repository_state": _validate_repository(repository_state),
        "cleanup_declaration": _validate_cleanup(cleanup_declaration),
        "consent": {"required": True, "subject_manifest_sha256": None},
        "execution_authorized": False,
    }
    manifest_json = _canonical(
        _validate_declarations(manifest, state="candidate"), "strict assembly"
    )
    digest = hashlib.sha256(manifest_json.encode()).hexdigest()
    return StrictRunAssembly(manifest_json, digest, plan_digest, _token=StrictRunAssembly._TOKEN)


def parse_strict_run_assembly(manifest_json: str) -> StrictRunAssembly:
    """Load a complete candidate/finalized artifact after validating its schema."""
    if type(manifest_json) is not str:
        _fail("assembly manifest must be JSON text")
    try:
        manifest = json.loads(manifest_json)
    except json.JSONDecodeError as exc:
        raise StrictRunAssemblyError("assembly manifest must be JSON") from exc
    state = manifest.get("state") if type(manifest) is dict else None
    if state not in {"candidate", "finalized"}:
        _fail("strict assembly has an invalid state")
    _validate_declarations(
        manifest,
        state=state,
        subject=None
        if state == "candidate"
        else manifest.get("consent", {}).get("subject_manifest_sha256"),
        raw=manifest_json,
    )
    digest = hashlib.sha256(manifest_json.encode()).hexdigest()
    return StrictRunAssembly(
        manifest_json, digest, manifest["plan_manifest_sha256"], _token=StrictRunAssembly._TOKEN
    )


def finalize_strict_run_assembly(
    candidate: StrictRunAssembly,
    consent_digest: str,
    *,
    provider_billing_attestation: dict[str, Any] | None = None,
) -> StrictRunAssembly:
    if not isinstance(candidate, StrictRunAssembly):
        _fail("candidate must be a StrictRunAssembly")
    try:
        candidate_manifest = candidate.to_dict()
    except (json.JSONDecodeError, TypeError, RecursionError) as exc:
        raise StrictRunAssemblyError("candidate manifest must be canonical JSON") from exc
    if (
        candidate_manifest.get("state") == "finalized"
        or candidate_manifest.get("consent", {}).get("subject_manifest_sha256") is not None
    ):
        _fail("candidate is already finalized")
    if (
        _sha(consent_digest, "consent digest", hex_only=True) != candidate.sha256
        or hashlib.sha256(candidate.manifest_json.encode()).hexdigest() != candidate.sha256
    ):
        _fail("consent is not bound to this candidate manifest subject")
    manifest = _validate_declarations(
        candidate_manifest, state="candidate", raw=candidate.manifest_json
    )
    if provider_billing_attestation is None:
        _fail("finalization requires validated live provider billing evidence")
    manifest["provider_billing_attestation"] = _validate_billing(
        provider_billing_attestation,
        plan_provider=manifest["plan"]["provider"],
        plan_model=manifest["plan"]["model"],
    )
    if candidate.plan_sha256 != manifest["plan_manifest_sha256"]:
        _fail("candidate plan digest does not match embedded plan")
    manifest["state"] = "finalized"
    manifest["consent"]["subject_manifest_sha256"] = candidate.sha256
    final_json = _canonical(
        _validate_declarations(manifest, state="finalized", subject=candidate.sha256),
        "final strict assembly",
    )
    return StrictRunAssembly(
        final_json,
        hashlib.sha256(final_json.encode()).hexdigest(),
        candidate.plan_sha256,
        _token=StrictRunAssembly._TOKEN,
    )


prepare_strict_run_assembly = build_strict_run_assembly
