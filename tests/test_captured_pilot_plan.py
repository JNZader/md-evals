"""Offline declaration tests for captured pilot plans."""

import sys

import pytest

from md_evals.captured_pilot_plan import PilotPlanError, prepare_captured_pilot
from md_evals.context_renderer import compose_paired_context


ID = "a" * 64
REVISION = "sha256:" + "b" * 64
CONFIG = "c" * 64


def record(kind="structure", identifier=None, quote="quote"):
    identifier = identifier or (ID if kind == "structure" else "d" * 64)
    return {
        "id": identifier,
        "kind": kind,
        "repository": "repo",
        "revision": REVISION,
        "producer_instance": kind + "-provider",
        "source_id": "source",
        "path": "x.py",
        "quote": quote,
        "claim": "claim",
        "value": "value",
        "freshness": "fresh",
        "git_state": "clean",
        "line": 1,
    }


def pack(*records):
    return {
        "schema_version": "ContextPack.capture.union.v1",
        "repository": "repo",
        "revision": REVISION,
        "freshness": "fresh",
        "git_state": "clean",
        "producer": {},
        "providers": [],
        "evidence": list(records),
        "conflicts": [],
        "budget": {},
        "trace": {},
    }


def case(name="one", *, expected=None):
    expected = expected or {"answer": "VALUE", "citations": [], "abstain": False}
    return {
        "name": name,
        "prompt": "Prompt " + name,
        "expected": expected,
        "packs": {
            "CONTROL": None,
            "B_STRUCTURE": pack(record()),
            "C_MEMORY": pack(record("memory")),
            "E_PAIRED": compose_paired_context(pack(record()), pack(record("memory"))),
        },
    }


def limits(calls=12):
    return {"max_primary_calls": calls, "per_call_timeout_seconds": 2, "total_timeout_seconds": 20}


def prepare(cases):
    return prepare_captured_pilot(
        cases=cases,
        provider="provider",
        model="model",
        backend_config_sha256=CONFIG,
        limits=limits(),
    )


def test_plan_binds_three_cases_to_twelve_calls_and_is_permanently_unready():
    plan = prepare([case("one"), case("two"), case("three")])
    manifest = plan.to_dict()
    assert plan.sha256 == __import__("hashlib").sha256(plan.manifest_json.encode()).hexdigest()
    assert manifest["profile"] == "CapturedPilotPlan.v1"
    assert manifest["planned_calls"] == 12 and manifest["repetitions"] == 1
    assert manifest["execution_authorized"] is False
    assert manifest["blockers"] == [
        "runner_admission_not_verified",
        "backend_preflight_not_verified",
        "live_execution_not_authorized",
    ]
    assert manifest["policy"] == {"adapter_retries": 0, "fallbacks": False}


def test_one_case_has_four_calls_preserves_orders_and_accepts_hidden_gold():
    hidden = {"answer": "VALUE", "citations": [ID], "abstain": False}
    plan = prepare([case("first", expected=hidden)])
    item = plan.to_dict()["cases"][0]
    assert plan.to_dict()["planned_calls"] == 4
    assert item["expected"] == hidden
    assert [arm["arm"] for arm in item["arms"]] == [
        "CONTROL",
        "B_STRUCTURE",
        "C_MEMORY",
        "E_PAIRED",
    ]
    assert item["arms"][0]["rendered_context"] is None


def test_validates_all_gold_before_attempting_any_render():
    bad = case("bad", expected={"answer": "VALUE", "citations": ["bad"], "abstain": False})
    bad["packs"]["B_STRUCTURE"] = {"bad": object()}
    with pytest.raises(PilotPlanError, match="expected"):
        prepare([bad])


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value.update(extra=True),
        lambda value: value.pop("packs"),
        lambda value: value.update(name=""),
        lambda value: value["packs"].update(EXTRA=None),
        lambda value: value["packs"].update(CONTROL=pack(record())),
        lambda value: value["packs"].update(B_STRUCTURE=None),
    ],
)
def test_rejects_case_and_arm_schema_errors(change):
    value = case()
    change(value)
    with pytest.raises(PilotPlanError):
        prepare([value])


def test_rejects_duplicate_names_bad_kinds_origins_and_conflicting_record_ids():
    with pytest.raises(PilotPlanError, match="unique"):
        prepare([case(), case()])
    bad_kind = case()
    bad_kind["packs"]["B_STRUCTURE"] = pack(record("memory"))
    with pytest.raises(PilotPlanError, match="kinds"):
        prepare([bad_kind])
    bad_origin = case()
    bad_origin["packs"]["C_MEMORY"]["repository"] = "other"
    with pytest.raises(PilotPlanError, match="origin"):
        prepare([bad_origin])
    conflict = case()
    conflict["packs"]["E_PAIRED"] = compose_paired_context(
        pack(record("structure", ID, "different")), pack(record("memory"))
    )
    with pytest.raises(PilotPlanError, match="conflicting"):
        prepare([conflict])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"provider": ""},
        {"model": ""},
        {"backend_config_sha256": "BAD"},
        {
            "limits": {
                "max_primary_calls": True,
                "per_call_timeout_seconds": 1,
                "total_timeout_seconds": 1,
            }
        },
        {
            "limits": {
                "max_primary_calls": 3,
                "per_call_timeout_seconds": 1,
                "total_timeout_seconds": 1,
            }
        },
        {
            "limits": {
                "max_primary_calls": 13,
                "per_call_timeout_seconds": 1,
                "total_timeout_seconds": 1,
            }
        },
        {
            "limits": {
                "max_primary_calls": 4,
                "per_call_timeout_seconds": 0,
                "total_timeout_seconds": 1,
            }
        },
    ],
)
def test_rejects_invalid_backend_declarations_and_limits(kwargs):
    options = {
        "cases": [case()],
        "provider": "provider",
        "model": "model",
        "backend_config_sha256": CONFIG,
        "limits": limits(4),
    }
    options.update(kwargs)
    with pytest.raises(PilotPlanError):
        prepare_captured_pilot(**options)


def test_snapshot_hash_binds_audit_metadata_but_to_dict_is_a_fresh_copy():
    cases = [case()]
    first = prepare(cases)
    cases[0]["prompt"] = "changed"
    cases[0]["packs"]["B_STRUCTURE"]["trace"]["audit"] = "changed"
    second = prepare(cases)
    copy_one = first.to_dict()
    copy_one["cases"][0]["prompt"] = "mutated copy"
    assert first.to_dict()["cases"][0]["prompt"] == "Prompt one"
    assert first.sha256 != second.sha256
    reordered = prepare([case("two"), case("one")])
    assert reordered.sha256 != prepare([case("one"), case("two")]).sha256


def test_rejects_non_json_pack_metadata_and_uses_no_heavy_modules():
    heavy_modules_before = {"litellm", "md_evals.engine", "md_evals.models"} & set(sys.modules)
    bad = case()
    bad["packs"]["B_STRUCTURE"]["trace"]["non_json"] = object()
    with pytest.raises(PilotPlanError, match="JSON"):
        prepare([bad])
    heavy_modules_after = {"litellm", "md_evals.engine", "md_evals.models"} & set(sys.modules)
    assert heavy_modules_after == heavy_modules_before
