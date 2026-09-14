"""Offline tests for strict billing evidence helpers."""

import hashlib
import json
from pathlib import Path

import pytest

from md_evals.strict_billing_evidence import (
    StrictBillingEvidenceError,
    build_billing_scaffold,
    build_provider_billing_attestation,
    canonical_response_digest,
    validate_billing_scaffold,
    validate_live_billing_evidence_record,
    write_billing_scaffold,
)


CELLS = [(f"case-{case}", f"arm-{arm}") for case in range(3) for arm in range(4)]
BASE = dict(
    provider="provider",
    model="model",
    plan_sha256="a" * 64,
    planned_cells=CELLS,
    created_at="2026-09-13T00:00:00Z",
)
APPROVED_CELLS = [("strict-readiness-vs-authorization", f"arm-{arm}") for arm in range(4)] + [
    (case_id, f"arm-{arm}")
    for case_id in ("strict-readiness-vs-recovery", "strict-readiness-vs-determinism")
    for arm in range(4)
]


def test_scaffold_is_deterministic_and_has_twelve_pending_slots():
    first = build_billing_scaffold(**BASE)
    second = build_billing_scaffold(**BASE)
    assert first == second
    assert len(first["ledger"]) == 12
    assert len({slot["cell_id"] for slot in first["ledger"]}) == 12
    assert all(slot["status"] == "pending_live" for slot in first["ledger"])
    assert validate_billing_scaffold(first) == first


def test_approved_authorization_case_materializes_four_arms_and_twelve_slots():
    scaffold = build_billing_scaffold(**{**BASE, "planned_cells": APPROVED_CELLS})

    validated = validate_billing_scaffold(scaffold)

    assert validated == scaffold
    assert len(validated["ledger"]) == 12
    assert (
        sum(slot["case_id"] == "strict-readiness-vs-authorization" for slot in validated["ledger"])
        == 4
    )


@pytest.mark.parametrize(
    "bad",
    [
        {"charged": True},
        {"catalog": "estimate"},
        {"raw_response": "x"},
        {"private_context": "x"},
        {"command": "curl https://example.test"},
        {"api_key": "sk-test"},
    ],
)
def test_scaffold_rejects_unsafe_fields_and_values(bad):
    manifest = build_billing_scaffold(**BASE)
    manifest["ledger"][0][next(iter(bad))] = next(iter(bad.values()))
    manifest["sha256"] = hashlib.sha256(
        json.dumps(
            {key: manifest[key] for key in manifest if key != "sha256"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode()
    ).hexdigest()
    with pytest.raises(StrictBillingEvidenceError):
        validate_billing_scaffold(manifest)


def test_duplicate_missing_and_tampered_cells_are_rejected():
    with pytest.raises(StrictBillingEvidenceError):
        build_billing_scaffold(**{**BASE, "planned_cells": [*CELLS[:-1], CELLS[0]]})
    manifest = build_billing_scaffold(**BASE)
    manifest["ledger"][0]["case_id"] = "other"
    with pytest.raises(StrictBillingEvidenceError):
        validate_billing_scaffold(manifest)


@pytest.mark.parametrize(
    "bad_id",
    [
        "../case",
        "case/escape",
        "case\\escape",
        "token",
        "case;rm",
        "ghp_test",
        "gho_test",
        "github_pat_test",
        "AKIA1234567890ABCDEF",
        "raw",
        "private",
        "secret",
        "authorization",
        "git status",
    ],
)
def test_unsafe_ids_are_rejected_from_explicit_cells(bad_id):
    cells = [*CELLS]
    cells[0] = (bad_id, "arm-0")
    with pytest.raises(StrictBillingEvidenceError):
        build_billing_scaffold(**{**BASE, "planned_cells": cells})
    manifest = build_billing_scaffold(**BASE)
    manifest["provider"] = "other"
    with pytest.raises(StrictBillingEvidenceError):
        validate_billing_scaffold(manifest)


def test_response_digest_returns_digest_only_and_rejects_secrets():
    digest = canonical_response_digest({"answer": "ok"})
    assert digest == hashlib.sha256(b'{"answer":"ok"}').hexdigest()
    assert len(digest) == 64
    for payload in [
        "raw",
        "private",
        "secret",
        "authorization",
        "headers",
        "raw response",
        "raw_response",
        "private context",
        "private_context",
        "password",
        "token",
        "api key",
        "Bearer abc",
        "sk-test",
        "ghp_test",
        "gho_test",
        "github_pat_test",
        "AKIA1234567890ABCDEF",
        {"raw": "x"},
        {"headers": {"authorization": "x"}},
        {"nested": {"private": "x"}},
        {"nested": {"value": "private_context"}},
    ]:
        with pytest.raises(StrictBillingEvidenceError):
            canonical_response_digest(payload)


def test_response_digest_avoids_false_positives_for_normal_words():
    assert canonical_response_digest({"answer": "secretary privateer tokenization"})


def live_record(**overrides):
    value = {
        "schema_version": "StrictLiveBillingEvidenceRecord.v1",
        "evidence_origin": "provider-live-receipt",
        "provider": "provider",
        "model": "model",
        "charge_assertion": "zero_charge",
        "observed_at": "2026-09-13T00:00:00Z",
        "external_evidence_digest": "b" * 64,
        "local_ledger_digest": "c" * 64,
        "source_classification": "provider-charge-attestation-record",
        "attestation_id": "live-1",
        "attested_at": "2026-09-13T00:00:00Z",
        "authenticity_unproven_by_validator": True,
    }
    value.update(overrides)
    return value


def test_provider_attestation_matches_strict_assembly_shape_and_digest():
    record = validate_live_billing_evidence_record(live_record())
    attestation = build_provider_billing_attestation(record)
    assert set(attestation) == {
        "provider_charge_attested",
        "provider_identity",
        "attestation_kind",
        "attestation_id",
        "attested_at",
        "evidence_payload",
        "evidence_digest",
    }
    evidence_json = json.dumps(
        attestation["evidence_payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    assert attestation["evidence_digest"] == hashlib.sha256(evidence_json.encode()).hexdigest()
    assert attestation["evidence_payload"]["external_evidence_digest"] == "b" * 64
    assert attestation["evidence_payload"]["local_ledger_digest"] == "c" * 64
    assert attestation["evidence_payload"]["authenticity_unproven_by_validator"] is True
    assert attestation["provider_charge_attested"] is False
    assert attestation["attestation_kind"] == "provider_billing_evidence_recorded"
    with pytest.raises(StrictBillingEvidenceError):
        build_provider_billing_attestation(build_billing_scaffold(**BASE))
    with pytest.raises(StrictBillingEvidenceError):
        validate_live_billing_evidence_record(live_record(source_classification="pricing-record"))
    with pytest.raises(StrictBillingEvidenceError):
        validate_live_billing_evidence_record(live_record(charge_assertion="estimate"))


def test_write_billing_scaffold_is_no_clobber_and_rejects_symlinks(tmp_path: Path):
    scaffold = build_billing_scaffold(**BASE)
    existing = tmp_path / "existing.json"
    existing.write_text("keep", encoding="utf-8")
    with pytest.raises(StrictBillingEvidenceError):
        write_billing_scaffold(scaffold, existing)

    dangling = tmp_path / "dangling.json"
    dangling.symlink_to(tmp_path / "missing.json")
    with pytest.raises(StrictBillingEvidenceError):
        write_billing_scaffold(scaffold, dangling)

    real_parent = tmp_path / "real"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(StrictBillingEvidenceError):
        write_billing_scaffold(scaffold, linked_parent / "scaffold.json")

    other_parent = tmp_path / "other"
    other_parent.mkdir()
    nested_link = real_parent / "nested-link"
    nested_link.symlink_to(other_parent, target_is_directory=True)
    with pytest.raises(StrictBillingEvidenceError):
        write_billing_scaffold(scaffold, nested_link / "scaffold.json")
    assert not (other_parent / "scaffold.json").exists()

    with pytest.raises(StrictBillingEvidenceError):
        write_billing_scaffold(scaffold, tmp_path / "missing" / "scaffold.json")

    destination = real_parent / "scaffold.json"
    write_billing_scaffold(scaffold, destination)
    assert json.loads(destination.read_text(encoding="utf-8")) == scaffold
