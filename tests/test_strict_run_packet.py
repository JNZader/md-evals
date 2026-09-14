"""Focused offline tests for the strict pre-run packet."""

import hashlib
import json

import pytest

from md_evals.strict_run_assembly import finalize_strict_run_assembly
from md_evals.strict_run_packet import (
    CHECKLIST_IDS,
    StrictRunPacketError,
    build_strict_run_packet,
    parse_strict_run_packet,
    validate_strict_run_packet_binding,
)
from tests.test_strict_run_assembly import (
    assemble,
    final_billing_attestation,
    scoped_dirty_repository,
)


def evidence(payload):
    return {
        "status": "provided",
        "evidence_payload": payload,
        "evidence_digest": hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest(),
    }


def checklist(candidate):
    result = {
        item_id: {"status": "pending", "evidence_payload": None, "evidence_digest": None}
        for item_id in CHECKLIST_IDS
    }
    result.update(
        {
            "retry_policy": evidence({"adapter_retries": 0}),
            "fallback_policy": evidence({"fallbacks": False}),
            "tools_none_local_evidence": evidence(
                {
                    "tools": "none",
                    "mode": "none",
                    "enforced": True,
                    "source": "local-policy",
                    "evidence_digest": "1" * 64,
                }
            ),
            "independent_reviewer": evidence({"reviewer_identity": "independent"}),
        }
    )
    if candidate.to_dict()["state"] == "finalized":
        result["final_strict_consent"] = evidence(
            {"subject_manifest_sha256": candidate.to_dict()["consent"]["subject_manifest_sha256"]}
        )
        billing = candidate.to_dict()["provider_billing_attestation"]["evidence_payload"]
        result["provider_billing"] = evidence(
            {
                "provider": billing["provider"],
                "model": billing["model"],
                "kind": "provider_billing_evidence_recorded",
                "source": billing["source"],
                "observed_at": billing["observed_at"],
                "charge_assertion": billing["charge_assertion"],
                "authenticity_unproven_by_validator": billing["authenticity_unproven_by_validator"],
            }
        )
    return result


def test_candidate_packet_is_deterministic_hash_addressed_and_never_authorized():
    candidate = assemble()
    first = build_strict_run_packet(assembly=candidate, checklist=checklist(candidate))
    second = build_strict_run_packet(assembly=candidate, checklist=checklist(candidate))
    assert first.manifest_json == second.manifest_json
    assert first.sha256 == hashlib.sha256(first.manifest_json.encode()).hexdigest()
    assert first.sha256 == second.sha256
    assert first.to_dict()["assembly_sha256"] == candidate.sha256
    assert first.to_dict()["ready_for_live_request"] is True
    assert first.to_dict()["execution_authorized"] is False
    assert set(first.to_dict()["checklist"]) == set(CHECKLIST_IDS)


def test_pending_live_only_blockers_are_explicit_but_request_readiness_is_structural():
    packet = build_strict_run_packet(assembly=assemble(), checklist=checklist(assemble()))
    manifest = packet.to_dict()
    assert [
        item
        for item in (
            "provider_authenticity",
            "provider_billing",
            "cleanup_deletion",
            "repository_state",
            "strict_live_execution",
        )
        if manifest["checklist"][item]["status"] == "pending"
    ]
    assert manifest["ready_for_live_request"] is True


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: c.pop("retry_policy"),
        lambda c: c.update({"unexpected": c["retry_policy"]}),
    ],
)
def test_checklist_must_match_closed_catalog(mutation):
    values = checklist(assemble())
    mutation(values)
    with pytest.raises(StrictRunPacketError, match="every required item"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_consent_must_match_finalized_assembly_subject():
    candidate = assemble()
    final = finalize_strict_run_assembly(
        candidate, candidate.sha256, provider_billing_attestation=final_billing_attestation()
    )
    values = checklist(final)
    values["final_strict_consent"] = evidence({"subject_manifest_sha256": "0" * 64})
    with pytest.raises(StrictRunPacketError, match="exact assembly subject"):
        build_strict_run_packet(assembly=final, checklist=values)


def test_reviewer_collision_is_rejected():
    values = checklist(assemble())
    values["independent_reviewer"] = evidence({"reviewer_identity": "operator"})
    with pytest.raises(StrictRunPacketError, match="independent"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize(
    "reviewer_identity",
    [
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
    ],
)
def test_reviewer_private_key_content_is_rejected(reviewer_identity):
    values = checklist(assemble())
    values["independent_reviewer"] = evidence({"reviewer_identity": reviewer_identity})
    with pytest.raises(StrictRunPacketError, match="private-key"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_destructive_command_content_is_rejected():
    values = checklist(assemble())
    values["independent_reviewer"] = evidence({"reviewer_identity": "rm -rf /"})
    with pytest.raises(StrictRunPacketError, match="command"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_provided_repository_state_is_validated_without_type_error():
    values = checklist(assemble())
    values["repository_state"] = evidence(
        {
            "clean": True,
            "revision": "a" * 40,
            "digest": "b" * 64,
            "captured_at": "2026-09-13T00:00:00Z",
        }
    )

    packet = build_strict_run_packet(assembly=assemble(), checklist=values)

    assert packet.to_dict()["checklist"]["repository_state"]["status"] == "provided"


def test_packet_accepts_legacy_prefixed_clean_repository_digest():
    values = checklist(assemble())
    values["repository_state"] = evidence(
        {
            "clean": True,
            "revision": "a" * 40,
            "digest": "sha256:" + "b" * 64,
            "captured_at": "2026-09-13T00:00:00Z",
        }
    )

    packet = build_strict_run_packet(assembly=assemble(), checklist=values)

    assert (
        packet.to_dict()["checklist"]["repository_state"]["evidence_payload"]["digest"]
        == "sha256:" + "b" * 64
    )


def test_scoped_dirty_repository_state_evidence_is_accepted():
    values = checklist(assemble())
    values["repository_state"] = evidence(scoped_dirty_repository())
    packet = build_strict_run_packet(assembly=assemble(), checklist=values)
    repository = packet.to_dict()["checklist"]["repository_state"]["evidence_payload"]
    assert repository["clean"] is False
    assert repository["worktree_clean"] is False


def test_packet_rejects_legacy_prefixed_scoped_dirty_digest():
    values = checklist(assemble())
    repository = scoped_dirty_repository()
    repository["digest"] = "sha256:" + repository["digest"]
    values["repository_state"] = evidence(repository)
    with pytest.raises(StrictRunPacketError, match="repository digest"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_scoped_dirty_repository_state_evidence_rejects_stale_digest():
    values = checklist(assemble())
    repository = scoped_dirty_repository()
    repository["relevant_files"][0]["bytes"] = 8
    values["repository_state"] = evidence(repository)
    with pytest.raises(StrictRunPacketError, match="does not match"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize(
    "path",
    [
        "foo\\bar",
        "foo\\..\\secret.txt",
        "C:relative",
        "C:\\x",
        "foo/./bar",
        ".env",
        ".env.local",
        "config/token.txt",
        "config/api_key.txt",
        "config/privatekey",
        "key",
        "secret.pem",
        "id_rsa",
        "keys/private.key",
    ],
)
def test_packet_rejects_non_normalized_or_sensitive_repository_paths(path):
    values = checklist(assemble())
    repository = scoped_dirty_repository()
    repository["relevant_files"][0]["path"] = path
    repository["digest"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in repository.items() if key != "digest"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode()
    ).hexdigest()
    values["repository_state"] = evidence(repository)
    with pytest.raises(StrictRunPacketError):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize("digest", ["b" * 63, "g" * 64, "B" * 64])
def test_repository_state_rejects_invalid_digest(digest):
    values = checklist(assemble())
    values["repository_state"] = evidence(
        {
            "clean": True,
            "revision": "a" * 40,
            "digest": digest,
            "captured_at": "2026-09-13T00:00:00Z",
        }
    )

    with pytest.raises(StrictRunPacketError, match="repository digest"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize("clean", [1, 0, "true", "clean"])
def test_repository_state_rejects_clean_lookalikes(clean):
    values = checklist(assemble())
    values["repository_state"] = evidence(
        {
            "clean": clean,
            "revision": "a" * 40,
            "digest": "b" * 64,
            "captured_at": "2026-09-13T00:00:00Z",
        }
    )

    with pytest.raises(StrictRunPacketError, match="clean"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize("item_id", ["provider_authenticity", "provider_billing"])
def test_provided_provider_evidence_requires_payload_and_digest(item_id):
    values = checklist(assemble())
    values[item_id] = {"status": "provided", "evidence_payload": None, "evidence_digest": None}
    with pytest.raises(StrictRunPacketError, match="requires evidence"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_catalog_billing_evidence_is_not_provider_billing():
    values = checklist(assemble())
    values["provider_billing"] = evidence(
        {
            "provider": "provider",
            "model": "model",
            "kind": "provider_charge_attestation",
            "source": "catalog estimate",
            "observed_at": "2026-09-13T00:00:00Z",
            "charge_assertion": "zero_charge",
            "evidence_digest": "2" * 64,
        }
    )
    with pytest.raises(StrictRunPacketError, match="catalog or estimated"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_pre_run_packet_rejects_run_result():
    values = checklist(assemble())
    values["strict_live_execution"] = evidence({"result": "passed"})
    with pytest.raises(StrictRunPacketError, match="not allowed"):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize(
    ("item_id", "payload"),
    [
        ("retry_policy", {"adapter_retries": 1}),
        ("retry_policy", {"adapter_retries": 0.0}),
        ("retry_policy", {"adapter_retries": False}),
        ("fallback_policy", {"fallbacks": True}),
        ("fallback_policy", {"fallbacks": 0}),
        (
            "tools_none_local_evidence",
            {
                "tools": "shell",
                "mode": "none",
                "enforced": True,
                "source": "local-policy",
                "evidence_digest": "1" * 64,
            },
        ),
    ],
)
def test_required_control_payloads_are_semantically_bound(item_id, payload):
    values = checklist(assemble())
    values[item_id] = evidence(payload)
    with pytest.raises(StrictRunPacketError):
        build_strict_run_packet(assembly=assemble(), checklist=values)


@pytest.mark.parametrize(
    "item_id", [item for item in CHECKLIST_IDS if item != "strict_live_execution"]
)
def test_provided_items_are_closed_and_reject_public_context_fields(item_id):
    values = checklist(assemble())
    payload = values[item_id]["evidence_payload"]
    if payload is None:
        payload = (
            {"reviewer_identity": "independent"}
            if item_id == "independent_reviewer"
            else {"subject_manifest_sha256": "0" * 64}
        )
    payload["rendered_context"] = "private prompt"
    values[item_id] = evidence(payload)
    with pytest.raises(StrictRunPacketError):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_tuple_contained_secret_or_billing_terms_are_rejected():
    values = checklist(assemble())
    values["retry_policy"] = evidence({"adapter_retries": 0, "nested": ("Bearer secret",)})
    with pytest.raises(StrictRunPacketError):
        build_strict_run_packet(assembly=assemble(), checklist=values)

    values = checklist(assemble())
    values["provider_billing"] = evidence(
        {
            "provider": "provider",
            "model": "model",
            "kind": "provider_charge_attestation",
            "source": "offline",
            "observed_at": "2026-09-13T00:00:00Z",
            "charge_assertion": "zero_charge",
            "evidence_digest": "2" * 64,
            "extra": ("catalog",),
        }
    )
    with pytest.raises(StrictRunPacketError):
        build_strict_run_packet(assembly=assemble(), checklist=values)


def test_assembly_binding_and_mutation_safety():
    candidate = assemble()
    values = checklist(candidate)
    packet = build_strict_run_packet(assembly=candidate, checklist=values)
    values["retry_policy"]["evidence_payload"]["adapter_retries"] = 4
    assert packet.to_dict()["checklist"]["retry_policy"]["evidence_payload"]["adapter_retries"] == 0
    with pytest.raises(StrictRunPacketError, match="assembly object digest"):
        build_strict_run_packet(
            assembly=type(candidate)(
                candidate.manifest_json,
                "0" * 64,
                candidate.plan_sha256,
                _token=type(candidate)._TOKEN,
            ),
            checklist=checklist(candidate),
        )


def test_parser_validates_complete_packet_schema_and_canonical_json():
    packet = build_strict_run_packet(assembly=assemble(), checklist=checklist(assemble()))
    assert parse_strict_run_packet(packet.manifest_json) == packet
    with pytest.raises(StrictRunPacketError):
        parse_strict_run_packet(json.dumps({"profile": "StrictRunPacket.v1"}))
    with pytest.raises(StrictRunPacketError, match="canonical"):
        parse_strict_run_packet(json.dumps(packet.to_dict(), indent=2))


def test_binding_rejects_packet_with_stale_manifest_digest():
    assembly = assemble()
    packet = build_strict_run_packet(assembly=assembly, checklist=checklist(assembly))
    wrong_sha256 = "0" * 64 if packet.sha256 != "0" * 64 else "1" * 64
    forged = type(packet)(
        packet.manifest_json, wrong_sha256, packet.assembly_sha256, _token=type(packet)._TOKEN
    )

    with pytest.raises(StrictRunPacketError, match="digest does not match"):
        validate_strict_run_packet_binding(forged, assembly)


def test_finalized_packet_requires_explicit_assembly_binding():
    candidate = assemble()
    final = finalize_strict_run_assembly(
        candidate, candidate.sha256, provider_billing_attestation=final_billing_attestation()
    )
    packet = build_strict_run_packet(assembly=final, checklist=checklist(final))
    parsed = parse_strict_run_packet(packet.manifest_json)
    assert parsed == packet
    assert parsed.to_dict()["ready_for_live_request"] is True
    with pytest.raises(StrictRunPacketError, match="not bound"):
        forged = json.loads(packet.manifest_json)
        forged["checklist"]["final_strict_consent"]["evidence_payload"][
            "subject_manifest_sha256"
        ] = "f" * 64
        forged["checklist"]["final_strict_consent"]["evidence_digest"] = hashlib.sha256(
            json.dumps(
                forged["checklist"]["final_strict_consent"]["evidence_payload"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        ).hexdigest()
        raw = json.dumps(forged, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        validate_strict_run_packet_binding(parse_strict_run_packet(raw), final)
    assert validate_strict_run_packet_binding(parsed, final) == packet


def test_packet_manifest_contains_no_raw_assembly_context_or_execution_route():
    packet = build_strict_run_packet(assembly=assemble(), checklist=checklist(assemble()))
    assert "rendered_context" not in packet.manifest_json
    assert "gateway" not in packet.manifest_json.lower()
    assert "provider_call" not in packet.manifest_json.lower()


def test_finalized_packet_with_pending_provider_billing_is_not_ready():
    candidate = assemble()
    final = finalize_strict_run_assembly(
        candidate, candidate.sha256, provider_billing_attestation=final_billing_attestation()
    )
    values = checklist(final)
    values["provider_billing"] = {
        "status": "pending",
        "evidence_payload": None,
        "evidence_digest": None,
    }

    packet = build_strict_run_packet(assembly=final, checklist=values)

    assert packet.to_dict()["assembly_state"] == "finalized"
    assert packet.to_dict()["ready_for_live_request"] is False
