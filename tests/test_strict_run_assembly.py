"""Offline tests for the blocked strict-run assembly contract."""

import hashlib
import json

import pytest

from md_evals.captured_pilot_plan import CapturedPilotPlan, prepare_captured_pilot
from md_evals.context_renderer import compose_paired_context
from md_evals.strict_run_assembly import (
    StrictRunAssemblyError,
    build_strict_run_assembly,
    finalize_strict_run_assembly,
    parse_strict_run_assembly,
)
from md_evals.strict_billing_evidence import build_billing_scaffold, build_provider_billing_attestation

ID = "a" * 64
REVISION = "sha256:" + "b" * 64
DIGEST = "d" * 64


def record(kind="structure", identifier=None):
    return {"id": identifier or (ID if kind == "structure" else "e" * 64), "kind": kind,
            "repository": "repo", "revision": REVISION, "producer_instance": "producer",
            "source_id": "source", "path": "x.py", "quote": "quote", "claim": "claim",
            "value": "value", "freshness": "fresh", "git_state": "clean", "line": 1}


def pack(*items):
    return {"schema_version": "ContextPack.capture.union.v1", "repository": "repo",
            "revision": REVISION, "freshness": "fresh", "git_state": "clean", "producer": {},
            "providers": [], "evidence": list(items), "conflicts": [], "budget": {}, "trace": {}}


def plan():
    cases = []
    for name in ("one", "two", "three"):
        structure, memory = pack(record()), pack(record("memory"))
        cases.append({"name": name, "prompt": f"Prompt {name}",
                      "expected": {"answer": "VALUE", "citations": [], "abstain": False},
                      "packs": {"CONTROL": None, "B_STRUCTURE": structure, "C_MEMORY": memory,
                                "E_PAIRED": compose_paired_context(structure, memory)}})
    return prepare_captured_pilot(cases=cases, provider="provider", model="model",
                                  backend_config_sha256="c" * 64,
                                  limits={"max_primary_calls": 12, "per_call_timeout_seconds": 2,
                                          "total_timeout_seconds": 20})


def declarations():
    def digest(payload):
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    source_payload = {"dataset": "gate-1", "version": 1, "entries": ["one", "two", "three"]}
    references = {}
    for name, label in (("one", "Answer A"), ("two", "Answer B"), ("three", "Answer C")):
        reference_payload = {"answer": "VALUE", "citations": [], "task": name}
        references[name] = {"reference_digest": digest(reference_payload), "reference_label": label,
                            "annotation_policy": "approved annotation policy", "reference_payload": reference_payload}
    gold_payload = {"version": "gold-v1",
                    "source_artifact": {"schema": "gold-source.v1", "source_id": "fixture-1",
                                        "artifact_digest": digest(source_payload), "artifact_payload": source_payload},
                    "per_task_references": references,
                    "scoring_policy": "exact answer with approved annotations"}
    billing_scaffold = build_billing_scaffold(
        provider="provider", model="model", plan_sha256=plan().sha256,
        planned_cells=[(case["name"], arm["arm"]) for case in plan().to_dict()["cases"] for arm in case["arms"]],
        created_at="2026-09-13T00:00:00Z",
    )
    return {
        "gold_reference": {**gold_payload, "digest": hashlib.sha256(
            json.dumps(gold_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()},
        "reviewer_metadata": {"operator_identity": "operator", "reviewer_identity": "reviewer",
                               "interpretation_authority_identity": "authority"},
        "billing_attestation": billing_scaffold,
        "repository_state": {"clean": True, "revision": "abc123", "digest": DIGEST,
                              "captured_at": "2026-09-13T00:00:00Z"},
        "cleanup_declaration": {"retention_policy": "delete raw artifacts after deadline",
                                 "deletion_deadline": "2026-09-20T00:00:00Z",
                                 "deletion_evidence_required": True,
                                 "deletion_evidence_placeholder": "receipt required"},
    }


def assemble(**changes):
    values = declarations()
    values.update(changes)
    return build_strict_run_assembly(plan=plan(), **values)


def final_billing_attestation():
    return build_provider_billing_attestation({
        "schema_version": "StrictLiveBillingEvidenceRecord.v1",
        "evidence_origin": "provider-live-receipt", "provider": "provider", "model": "model",
        "charge_assertion": "zero_charge", "observed_at": "2026-09-13T00:00:00Z",
        "external_evidence_digest": "b" * 64, "local_ledger_digest": "c" * 64,
        "source_classification": "provider-charge-attestation-record", "attestation_id": "charge-1",
        "attested_at": "2026-09-13T00:00:00Z", "authenticity_unproven_by_validator": True,
    })


def test_valid_assembly_is_deterministic_and_permanently_blocked():
    first, second = assemble(), assemble()
    assert first.manifest_json == second.manifest_json and first.sha256 == second.sha256
    assert first.to_dict()["execution_authorized"] is False
    final = finalize_strict_run_assembly(first, first.sha256, provider_billing_attestation=final_billing_attestation())
    assert final.to_dict()["execution_authorized"] is False
    assert final.to_dict()["consent"]["subject_manifest_sha256"] == first.sha256
    assert final.sha256 != first.sha256
    assert final.to_dict()["state"] == "finalized"
    assert final.to_dict()["plan_manifest_sha256"] == final.plan_sha256


def test_candidate_accepts_pending_scaffold_but_finalization_requires_live_attestation():
    candidate = assemble()
    assert candidate.to_dict()["billing_scaffold"]["status"] == "scaffold_pending_live_execution"
    assert candidate.to_dict()["provider_billing_attestation"] is None
    with pytest.raises(StrictRunAssemblyError, match="validated live provider billing evidence"):
        finalize_strict_run_assembly(candidate, candidate.sha256)


def test_synthetic_final_billing_is_not_accepted_as_candidate_evidence():
    synthetic = final_billing_attestation()
    with pytest.raises(StrictRunAssemblyError, match="invalid or extra field|scaffold"):
        assemble(billing_attestation=synthetic)


@pytest.mark.parametrize("policy", [{"adapter_retries": 1, "fallbacks": False},
                                     {"adapter_retries": 0, "fallbacks": True},
                                     {"adapter_retries": 0.0, "fallbacks": False},
                                     {"adapter_retries": 0, "fallbacks": 0}])
def test_retry_or_fallback_policy_is_rejected(policy):
    manifest = plan().to_dict()
    manifest["policy"] = policy
    manifest_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    broken = CapturedPilotPlan(manifest_json, hashlib.sha256(manifest_json.encode()).hexdigest())
    with pytest.raises(StrictRunAssemblyError, match="retry-0 and fallback-disabled"):
        build_strict_run_assembly(plan=broken, **declarations())


@pytest.mark.parametrize("key", ["gold_reference", "reviewer_metadata", "billing_attestation",
                                  "repository_state", "cleanup_declaration"])
def test_missing_required_declaration_rejected(key):
    value = declarations()[key]
    value.pop(next(iter(value)))
    with pytest.raises(StrictRunAssemblyError):
        assemble(**{key: value})


def test_gold_digest_mismatch_and_weak_reference_rejected():
    with pytest.raises(StrictRunAssemblyError, match="gold digest does not match"):
        assemble(gold_reference={**declarations()["gold_reference"], "digest": "0" * 64})
    gold = {**declarations()["gold_reference"],
            "per_task_references": {**declarations()["gold_reference"]["per_task_references"],
                                    "one": {}}}
    payload = {key: gold[key] for key in ("version", "per_task_references", "scoring_policy")}
    gold["digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    with pytest.raises(StrictRunAssemblyError, match="invalid or extra field"):
        assemble(gold_reference=gold)


def test_gold_payload_digests_are_bound_independently():
    gold = json.loads(json.dumps(declarations()["gold_reference"]))
    gold["source_artifact"]["artifact_digest"] = "0" * 64
    with pytest.raises(StrictRunAssemblyError, match="source artifact digest"):
        assemble(gold_reference=gold)
    gold = json.loads(json.dumps(declarations()["gold_reference"]))
    gold["per_task_references"]["one"]["reference_digest"] = "0" * 64
    with pytest.raises(StrictRunAssemblyError, match="reference digest"):
        assemble(gold_reference=gold)
    gold["per_task_references"]["one"].pop("reference_payload")
    with pytest.raises(StrictRunAssemblyError, match="invalid or extra field"):
        assemble(gold_reference=gold)


@pytest.mark.parametrize("reference", ["answer", [], {}])
def test_unstructured_reference_is_rejected_after_gold_rehash(reference):
    gold = {**declarations()["gold_reference"],
            "per_task_references": {**declarations()["gold_reference"]["per_task_references"],
                                    "one": reference}}
    payload = {key: gold[key] for key in ("version", "per_task_references", "scoring_policy")}
    gold["digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    with pytest.raises(StrictRunAssemblyError, match="invalid or extra field"):
        assemble(gold_reference=gold)


def test_reviewer_must_differ_from_operator_and_authority():
    base = declarations()["reviewer_metadata"]
    with pytest.raises(StrictRunAssemblyError):
        assemble(reviewer_metadata={**base, "reviewer_identity": "operator"})
    with pytest.raises(StrictRunAssemblyError):
        assemble(reviewer_metadata={**base, "reviewer_identity": "authority"})


def test_billing_requires_external_attestation_not_catalog_estimate():
    with pytest.raises(StrictRunAssemblyError, match="invalid or extra field|scaffold"):
        assemble(billing_attestation=final_billing_attestation())
    with pytest.raises(StrictRunAssemblyError, match="validated live"):
        finalize_strict_run_assembly(assemble(), assemble().sha256)


def test_billing_evidence_is_payload_bound_and_provider_bound():
    billing = json.loads(json.dumps(final_billing_attestation()))
    billing["evidence_digest"] = "0" * 64
    with pytest.raises(StrictRunAssemblyError, match="evidence digest"):
        finalize_strict_run_assembly(assemble(), assemble().sha256, provider_billing_attestation=billing)
    billing = final_billing_attestation()
    billing["evidence_payload"]["provider"] = "other-provider"
    with pytest.raises(StrictRunAssemblyError, match="provider/model"):
        finalize_strict_run_assembly(assemble(), assemble().sha256, provider_billing_attestation=billing)


def test_unproven_billing_evidence_cannot_claim_provider_charge():
    billing = final_billing_attestation()
    assert billing["provider_charge_attested"] is False
    assert billing["attestation_kind"] == "provider_billing_evidence_recorded"

    billing["provider_charge_attested"] = True
    with pytest.raises(StrictRunAssemblyError, match="must be exactly False"):
        finalize_strict_run_assembly(assemble(), assemble().sha256, provider_billing_attestation=billing)


def test_repo_cleanup_consent_and_secret_fail_closed():
    with pytest.raises(StrictRunAssemblyError):
        assemble(repository_state={**declarations()["repository_state"], "clean": False})
    with pytest.raises(StrictRunAssemblyError):
        assemble(cleanup_declaration={**declarations()["cleanup_declaration"],
                                      "deletion_evidence_placeholder": ""})
    candidate = assemble()
    with pytest.raises(StrictRunAssemblyError):
        finalize_strict_run_assembly(candidate, "f" * 64)
    with pytest.raises(StrictRunAssemblyError):
        assemble(repository_state={**declarations()["repository_state"], "revision": "Bearer secret"})


def test_mutation_extra_fields_and_execution_boundaries():
    values = declarations()
    candidate = build_strict_run_assembly(plan=plan(), **values)
    before = candidate.manifest_json, candidate.sha256
    values["gold_reference"]["per_task_references"]["one"]["reference_payload"]["answer"] = "MUTATED"
    assert (candidate.manifest_json, candidate.sha256) == before
    assert candidate.sha256 == hashlib.sha256(candidate.manifest_json.encode()).hexdigest()
    with pytest.raises(StrictRunAssemblyError):
        assemble(reviewer_metadata={**declarations()["reviewer_metadata"], "extra": "nope"})
    assert "BridgeCompletionAdapter" not in candidate.manifest_json


def test_mutating_input_evidence_after_build_does_not_change_artifact():
    values = declarations()
    candidate = build_strict_run_assembly(plan=plan(), **values)
    before = candidate.manifest_json
    values["billing_attestation"]["ledger"][0]["status"] = "mutated"
    values["gold_reference"]["source_artifact"]["artifact_payload"]["entries"].append("mutated")
    assert candidate.manifest_json == before


def test_parser_validates_complete_schema_before_returning_assembly():
    candidate = assemble()
    assert parse_strict_run_assembly(candidate.manifest_json) == candidate
    with pytest.raises(StrictRunAssemblyError):
        parse_strict_run_assembly(json.dumps({"profile": "StrictRunAssembly.v2", "state": "candidate"}))


def test_malformed_arm_entry_is_rejected_instead_of_filtered():
    manifest = plan().to_dict()
    manifest["cases"][0]["arms"].append({"arm": "MALFORMED"})
    manifest_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    broken = CapturedPilotPlan(manifest_json, hashlib.sha256(manifest_json.encode()).hexdigest())
    with pytest.raises(StrictRunAssemblyError, match="exactly four well-formed"):
        build_strict_run_assembly(plan=broken, **declarations())


def rehashed_plan_manifest(manifest):
    manifest_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return CapturedPilotPlan(manifest_json, hashlib.sha256(manifest_json.encode()).hexdigest())


@pytest.mark.parametrize("arm_index, mutation, message", [
    (1, lambda arm: arm.update(arm="UNKNOWN"), "unsupported arm label"),
    (1, lambda arm: arm.update(canonical_pack_snapshot_sha256="bad"), "pack snapshot digest"),
    (1, lambda arm: arm.update(selected_ids=["bad"]), "selected IDs"),
    (1, lambda arm: arm.update(selected_ids=[ID, ID]), "selected IDs"),
    (0, lambda arm: arm.update(rendered_context="control context"), "CONTROL arm"),
    (1, lambda arm: arm.update(rendered_context=""), "rendered context is required"),
    (1, lambda arm: arm.update(rendered_context=None), "rendered context is required"),
    (1, lambda arm: arm.update(rendered_context_sha256="0" * 64), "rendered context digest"),
])
def test_arm_payload_values_are_validated(arm_index, mutation, message):
    manifest = plan().to_dict()
    arm = manifest["cases"][0]["arms"][arm_index]
    mutation(arm)
    with pytest.raises(StrictRunAssemblyError, match=message):
        build_strict_run_assembly(plan=rehashed_plan_manifest(manifest), **declarations())


def test_boolean_repetitions_is_rejected_after_rehash():
    manifest = plan().to_dict()
    manifest["repetitions"] = True
    with pytest.raises(StrictRunAssemblyError, match="permanently blocked or has invalid repetitions"):
        build_strict_run_assembly(plan=rehashed_plan_manifest(manifest), **declarations())


def test_finalization_rejects_already_finalized_and_non_assembly_candidates():
    candidate = assemble()
    final = finalize_strict_run_assembly(candidate, candidate.sha256, provider_billing_attestation=final_billing_attestation())
    with pytest.raises(StrictRunAssemblyError, match="already finalized"):
        finalize_strict_run_assembly(final, final.sha256)

    corrupted = candidate.to_dict()
    corrupted["profile"] = "CapturedPilotPlan.v1"
    corrupted_json = json.dumps(corrupted, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    with pytest.raises(StrictRunAssemblyError, match="StrictRunAssembly must be created"):
        type(candidate)(corrupted_json, hashlib.sha256(corrupted_json.encode()).hexdigest(), candidate.plan_sha256)


def _rehash_assembly(manifest, *, plan_sha256=None):
    raw = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assembly_type = type(assemble())
    return assembly_type(raw, hashlib.sha256(raw.encode()).hexdigest(), plan_sha256 or assemble().plan_sha256,
                         _token=assembly_type._TOKEN)


@pytest.mark.parametrize("field,value", [
    ("planned_calls", 12.0),
    ("planned_calls", True),
    ("planned_calls", "12"),
])
def test_planned_calls_rejects_json_lookalikes(field, value):
    manifest = plan().to_dict()
    manifest[field] = value
    with pytest.raises(StrictRunAssemblyError, match="exactly 12 cells|exact integer"):
        build_strict_run_assembly(plan=rehashed_plan_manifest(manifest), **declarations())


@pytest.mark.parametrize("path,value", [
    (("limits", "max_primary_calls"), True),
    (("limits", "per_call_timeout_seconds"), 2.0),
    (("limits", "total_timeout_seconds"), "20"),
    (("policy", "adapter_retries"), True),
    (("policy", "fallbacks"), 0),
    (("repetitions",), False),
])
def test_every_plan_integer_boolean_invariant_rejects_lookalikes(path, value):
    manifest = plan().to_dict()
    target = manifest
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(StrictRunAssemblyError):
        build_strict_run_assembly(plan=rehashed_plan_manifest(manifest), **declarations())


def test_finalizer_validates_rehashed_nested_candidate_and_extra_fields():
    candidate = assemble()
    mutated = candidate.to_dict()
    mutated["gold_reference"]["per_task_references"]["one"]["reference_label"] = ""
    forged = _rehash_assembly(mutated, plan_sha256=candidate.plan_sha256)
    with pytest.raises(StrictRunAssemblyError, match="reference label"):
        finalize_strict_run_assembly(forged, forged.sha256)

    extra = candidate.to_dict()
    extra["plan"]["extra"] = "nope"
    forged = _rehash_assembly(extra, plan_sha256=candidate.plan_sha256)
    with pytest.raises(StrictRunAssemblyError, match="invalid or extra field"):
        finalize_strict_run_assembly(forged, forged.sha256)


def test_finalizer_rejects_self_hashed_fabricated_minimal_candidate():
    raw = json.dumps({"profile": "StrictRunAssembly.v2", "state": "candidate", "execution_authorized": False}, sort_keys=True, separators=(",", ":"))
    with pytest.raises(StrictRunAssemblyError, match="StrictRunAssembly must be created"):
        type(assemble())(raw, hashlib.sha256(raw.encode()).hexdigest(), "0" * 64)


@pytest.mark.parametrize("key,value", [
    ("clean", False), ("clean", 1), ("clean", "true"),
])
def test_repository_boolean_invariant_rejects_lookalikes(key, value):
    repository = {**declarations()["repository_state"], key: value}
    with pytest.raises(StrictRunAssemblyError):
        assemble(repository_state=repository)


def scoped_dirty_repository(**changes):
    payload = {
        "clean": False,
        "revision": "sha256:" + "a" * 64,
        "captured_at": "2026-09-13T00:00:00Z",
        "scope": "scoped_relevant_files_with_global_dirty_disclosure",
        "worktree_clean": False,
        "status_short_count": 1,
        "relevant_files": [{"path": "md_evals/example.py", "git_status": "??", "bytes": 7, "sha256": "e" * 64}],
    }
    payload.update(changes)
    payload["digest"] = hashlib.sha256(json.dumps(
        {key: value for key, value in payload.items() if key != "digest"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()
    return payload


def test_scoped_dirty_repository_state_is_digest_bound_and_not_clean():
    candidate = assemble(repository_state=scoped_dirty_repository())
    repository = candidate.to_dict()["repository_state"]
    assert repository["clean"] is False
    assert repository["worktree_clean"] is False
    assert repository["digest"] == hashlib.sha256(json.dumps(
        {key: value for key, value in repository.items() if key != "digest"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(worktree_clean=True),
    lambda value: value.pop("worktree_clean"),
    lambda value: value.update(status_short_count=True),
    lambda value: value.update(status_short_count=0),
    lambda value: value.update(relevant_files=[{"path": "/absolute", "git_status": "??", "bytes": 1, "sha256": "e" * 64}]),
    lambda value: value.update(relevant_files=[{"path": "../escape", "git_status": "??", "bytes": 1, "sha256": "e" * 64}]),
    lambda value: value.update(relevant_files=[{"path": "file", "git_status": "??", "bytes": True, "sha256": "e" * 64}]),
    lambda value: value.update(relevant_files=[{"path": "file", "git_status": "??", "bytes": 1, "sha256": "E" * 64}]),
])
def test_scoped_dirty_repository_state_rejects_unsafe_evidence(mutation):
    repository = scoped_dirty_repository()
    mutation(repository)
    with pytest.raises(StrictRunAssemblyError):
        assemble(repository_state=repository)


@pytest.mark.parametrize("path", [
    "foo\\bar", "foo\\..\\secret.txt", "C:relative", "C:\\x", "foo/./bar",
    ".env", ".env.local", "config/token.txt", "config/api_key.txt", "config/privatekey", "key",
    "secret.pem", "id_rsa", "keys/private.key",
])
def test_scoped_dirty_repository_state_rejects_non_normalized_or_sensitive_paths(path):
    repository = scoped_dirty_repository()
    repository["relevant_files"][0]["path"] = path
    repository["digest"] = hashlib.sha256(json.dumps(
        {key: value for key, value in repository.items() if key != "digest"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()
    with pytest.raises(StrictRunAssemblyError):
        assemble(repository_state=repository)


def test_scoped_dirty_repository_state_rejects_legacy_prefixed_digest():
    repository = scoped_dirty_repository()
    repository["digest"] = "sha256:" + repository["digest"]
    with pytest.raises(StrictRunAssemblyError, match="repository digest"):
        assemble(repository_state=repository)


@pytest.mark.parametrize("status", ["password=not-a-token", "??\nM ", "???", "/M", "M/", "token", "  "])
def test_scoped_dirty_repository_state_rejects_unsafe_git_status(status):
    repository = scoped_dirty_repository()
    repository["relevant_files"][0]["git_status"] = status
    repository["digest"] = hashlib.sha256(json.dumps(
        {key: value for key, value in repository.items() if key != "digest"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()
    with pytest.raises(StrictRunAssemblyError):
        assemble(repository_state=repository)


@pytest.mark.parametrize("status", ["??", " M", "M ", "MM", "A ", " D"])
def test_scoped_dirty_repository_state_accepts_safe_git_status(status):
    repository = scoped_dirty_repository()
    repository["relevant_files"][0]["git_status"] = status
    repository["digest"] = hashlib.sha256(json.dumps(
        {key: value for key, value in repository.items() if key != "digest"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()
    assemble(repository_state=repository)


def test_scoped_dirty_repository_state_rejects_stale_digest():
    repository = scoped_dirty_repository()
    repository["relevant_files"][0]["bytes"] = 8
    with pytest.raises(StrictRunAssemblyError, match="does not match"):
        assemble(repository_state=repository)


def test_billing_forbidden_strings_are_rejected_in_every_string_field():
    billing = final_billing_attestation()
    billing["evidence_payload"]["source"] = "catalog estimate"
    with pytest.raises(StrictRunAssemblyError, match="catalog or estimated"):
        finalize_strict_run_assembly(assemble(), assemble().sha256, provider_billing_attestation=billing)


def test_outer_candidate_state_and_consent_are_closed_and_bound():
    candidate = assemble()
    manifest = candidate.to_dict()
    manifest["consent"]["subject_manifest_sha256"] = "f" * 64
    forged = _rehash_assembly(manifest, plan_sha256=candidate.plan_sha256)
    with pytest.raises(StrictRunAssemblyError, match="already finalized"):
        finalize_strict_run_assembly(forged, forged.sha256)

    final = finalize_strict_run_assembly(candidate, candidate.sha256, provider_billing_attestation=final_billing_attestation())
    changed = final.to_dict()
    changed["consent"]["subject_manifest_sha256"] = "0" * 64
    forged_final = _rehash_assembly(changed, plan_sha256=final.plan_sha256)
    with pytest.raises(StrictRunAssemblyError, match="already finalized"):
        finalize_strict_run_assembly(forged_final, candidate.sha256)
