"""Focused offline tests for the non-authorizing authorization request artifact."""

import hashlib
import json

import pytest

from md_evals.strict_authorization_prompt import (
    StrictAuthorizationRequestError,
    build_strict_authorization_request,
    parse_strict_authorization_request,
)
from md_evals.strict_run_assembly import finalize_strict_run_assembly
from md_evals.strict_run_packet import build_strict_run_packet
from tests.test_strict_run_packet import checklist
from tests.test_strict_run_assembly import assemble, final_billing_attestation


def ready_packet(assembly=None):
    assembly = assembly or assemble()
    return build_strict_run_packet(assembly=assembly, checklist=checklist(assembly))


def test_valid_bound_request_is_deterministic_and_never_authorizes():
    assembly = assemble()
    packet = ready_packet(assembly)
    first = build_strict_authorization_request(packet=packet, assembly=assembly, generated_at="2026-09-13T00:00:00Z")
    second = build_strict_authorization_request(packet=packet, assembly=assembly, generated_at="2026-09-13T00:00:00Z")
    assert first == second
    assert first.sha256 == hashlib.sha256(first.manifest_json.encode()).hexdigest()
    assert first.to_dict()["execution_authorized"] is False
    assert first.to_dict()["live_execution_requested"] is False
    assert first.to_dict()["contains_command"] is False
    assert first.to_dict()["packet_sha256"] == packet.sha256
    assert first.to_dict()["assembly_sha256"] == assembly.sha256


def test_not_ready_packet_is_rejected():
    assembly = assemble()
    values = checklist(assembly)
    values["retry_policy"] = {"status": "pending", "evidence_payload": None, "evidence_digest": None}
    packet = build_strict_run_packet(assembly=assembly, checklist=values)
    with pytest.raises(StrictAuthorizationRequestError, match="not ready"):
        build_strict_authorization_request(packet=packet, assembly=assembly, generated_at="2026-09-13T00:00:00Z")


def test_unbound_or_mismatched_packet_is_rejected():
    first = assemble()
    second = finalize_strict_run_assembly(
        first, first.sha256, provider_billing_attestation=final_billing_attestation()
    )
    packet = ready_packet(first)
    with pytest.raises(StrictAuthorizationRequestError, match="not bound"):
        build_strict_authorization_request(packet=packet, assembly=second, generated_at="2026-09-13T00:00:00Z")


def test_pending_live_blockers_are_visible_and_pending():
    assembly = assemble()
    artifact = build_strict_authorization_request(packet=ready_packet(assembly), assembly=assembly, generated_at="2026-09-13T00:00:00Z")
    blockers = artifact.to_dict()["pending_live_blockers"]
    assert blockers
    assert {item["checklist_id"] for item in blockers} >= {"provider_authenticity", "provider_billing", "strict_live_execution"}
    assert all(item["status"] == "pending" for item in blockers)
    assert artifact.to_dict()["packet_status_snapshot"]["strict_live_execution"] == "pending"


def _canonical_artifact_values(artifact, mutate):
    values = artifact.to_dict()
    mutate(values)
    return json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def test_empty_pending_live_blockers_are_rejected():
    artifact = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z")
    forged = _canonical_artifact_values(artifact, lambda values: values.update({"pending_live_blockers": []}))
    with pytest.raises(StrictAuthorizationRequestError, match="do not match"):
        parse_strict_authorization_request(forged)


def test_missing_pending_live_blocker_is_rejected():
    artifact = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z")
    forged = _canonical_artifact_values(artifact, lambda values: values["pending_live_blockers"].pop())
    with pytest.raises(StrictAuthorizationRequestError, match="do not match"):
        parse_strict_authorization_request(forged)


def test_duplicate_pending_live_blocker_is_rejected():
    artifact = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z")
    forged = _canonical_artifact_values(artifact, lambda values: values["pending_live_blockers"].append(values["pending_live_blockers"][0]))
    with pytest.raises(StrictAuthorizationRequestError, match="unique"):
        parse_strict_authorization_request(forged)


def test_extra_pending_live_blocker_is_rejected():
    artifact = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z")

    def add_provided_blocker(values):
        values["pending_live_blockers"].append({
            "checklist_id": "independent_reviewer",
            "status": "pending",
            "reason": "Independent reviewer execution/review must occur during the separate live step.",
        })

    forged = _canonical_artifact_values(artifact, add_provided_blocker)
    with pytest.raises(StrictAuthorizationRequestError, match="do not match"):
        parse_strict_authorization_request(forged)


def test_status_snapshot_mismatch_is_rejected():
    artifact = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z")
    forged = _canonical_artifact_values(artifact, lambda values: values["packet_status_snapshot"].update({"provider_billing": "provided"}))
    with pytest.raises(StrictAuthorizationRequestError, match="do not match"):
        parse_strict_authorization_request(forged)


def test_answer_domain_is_closed_without_a_selected_answer():
    answer = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z").to_dict()["answer_domain"]
    assert answer["selected_answer"] is None
    assert answer["allowed_tokens"] == ["authorize_live_run", "decline_live_run", "revise_packet"]


@pytest.mark.parametrize("generated_at", [None, "", "2026-09-13", "not-a-timestamp"])
def test_generated_at_must_be_explicit_timestamp(generated_at):
    with pytest.raises(StrictAuthorizationRequestError, match="generated_at"):
        build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at=generated_at)


def test_unsafe_options_and_packet_payload_strings_are_rejected():
    with pytest.raises(StrictAuthorizationRequestError, match="command"):
        assembly = assemble()
        build_strict_authorization_request(packet=ready_packet(assembly), assembly=assembly,
                                           generated_at="2026-09-13T00:00:00Z", safety_text="run pytest now")


def test_private_key_marker_in_packet_is_rejected_by_authorization_builder():
    assembly = assemble()
    packet = ready_packet(assembly)
    forged = packet.to_dict()
    forged["checklist"]["independent_reviewer"]["evidence_payload"]["reviewer_identity"] = (
        "-----BEGIN OPENSSH PRIVATE KEY-----"
    )
    forged["checklist"]["independent_reviewer"]["evidence_digest"] = hashlib.sha256(
        json.dumps(forged["checklist"]["independent_reviewer"]["evidence_payload"],
                   sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    raw = json.dumps(forged, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    packet = type(packet)(raw, hashlib.sha256(raw.encode()).hexdigest(), packet.assembly_sha256,
                         _token=type(packet)._TOKEN)
    with pytest.raises(StrictAuthorizationRequestError, match="private-key"):
        build_strict_authorization_request(packet=packet, assembly=assembly,
                                           generated_at="2026-09-13T00:00:00Z")


def test_destructive_command_in_options_is_rejected_by_authorization_builder():
    assembly = assemble()
    with pytest.raises(StrictAuthorizationRequestError, match="command"):
        build_strict_authorization_request(
            packet=ready_packet(assembly),
            assembly=assembly,
            generated_at="2026-09-13T00:00:00Z", safety_text="rm -rf /",
        )


def test_private_names_are_not_in_generated_artifact_and_parser_is_canonical():
    artifact = build_strict_authorization_request(packet=ready_packet(), assembly=assemble(), generated_at="2026-09-13T00:00:00Z")
    assert not any(name in artifact.manifest_json.lower() for name in ("private_key", "prompt", "context", "rendered_context", "raw_response"))
    assert parse_strict_authorization_request(artifact.manifest_json) == artifact
    with pytest.raises(StrictAuthorizationRequestError, match="canonical"):
        parse_strict_authorization_request(json.dumps(artifact.to_dict(), indent=2))


def test_mutating_inputs_after_build_does_not_change_artifact():
    assembly = assemble()
    packet = ready_packet(assembly)
    before = build_strict_authorization_request(packet=packet, assembly=assembly, generated_at="2026-09-13T00:00:00Z")
    packet.to_dict()["checklist"]["provider_authenticity"]["status"] = "provided"
    assert before.manifest_json == build_strict_authorization_request(packet=packet, assembly=assembly, generated_at="2026-09-13T00:00:00Z").manifest_json
