"""Test-only ContextPack.v0 mechanics; run the focused suite with --noconftest.

The parent conftest imports LiteLLM first; ordinary collection explicitly skips
this module rather than running it without pre-import denial.
Guards are restored after imports and every test. Synthetic skill reads are
in-memory: the real ExecutionEngine and inject_skill still execute unchanged.
jsonschema is currently installed/locked transitively, not a direct dependency.
No provider conformance, measured token telemetry, or model-quality claim.
"""

import sys
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import pytest

if any(name == "litellm" or name.startswith("md_evals") for name in sys.modules):
    pytest.skip(
        "requires standalone --noconftest for pre-import offline guard",
        allow_module_level=True,
    )

import os
import socket

_COST_MAP_BEFORE = os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP")
_CONNECT_BEFORE = socket.socket.connect


class OutboundDenied(RuntimeError):
    """Raised before DNS, socket transmission, or child-process execution."""


@contextmanager
def outbound_guard():
    events = []

    def deny(*args, **kwargs):
        events.append("denied")
        raise OutboundDenied("offline fixture: outbound operation denied")

    with ExitStack() as stack:
        for target in (
            "socket.getaddrinfo", "socket.socket.connect", "socket.socket.connect_ex",
            "socket.socket.sendto", "socket.socket.sendmsg",
            "subprocess.Popen", "os.system",
        ):
            stack.enter_context(patch(target, deny))
        yield events


# Inspected LiteLLM 1.82.6 get_model_cost_map.py:244-258 supports local-only import.
# patch.dict restores the prior environment immediately afterward.
with outbound_guard() as import_denials, patch.dict(
    "os.environ", {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}
):
    import hashlib
    import json
    from collections import Counter
    from copy import deepcopy
    from pathlib import Path

    import yaml
    from jsonschema import Draft202012Validator
    from md_evals.engine import ExecutionEngine
    from md_evals.evaluator import EvaluatorEngine
    from md_evals.models import EvalConfig, LLMResponse, RegexEvaluator, Task

if import_denials:
    raise RuntimeError("Import attempted an outbound operation; offline setup is unavailable")

IMPORT_STATE_RESTORED = (
    socket.socket.connect is _CONNECT_BEFORE
    and os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP") == _COST_MAP_BEFORE
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "context_broker"
SCHEMA = json.loads((FIXTURES / "context-pack.schema.json").read_text())
CASES = json.loads((FIXTURES / "cases.json").read_text())
ARMS = {"CONTROL": (), "B_STRUCTURE": ("structure",),
        "C_MEMORY": ("memory",), "D_UNION": ("structure", "memory")}
PRODUCER = {"name": "offline-fixture", "version": "0", "instance": "fixture-local"}


@pytest.fixture(autouse=True)
def no_outbound():
    with outbound_guard() as events:
        yield events


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def identity(record):
    return {key: record[key] for key in (
        "kind", "repository", "revision", "producer_instance", "source_id", "path", "line"
    )}


def quote_estimate(records):
    """Deterministic estimate of quote bytes only, NOT a real tokenizer."""
    return sum((len(item["quote"].encode("utf-8")) + 3) // 4 for item in records)


def retrieval(case, arm):
    providers = [deepcopy(p) for p in case["providers"] if p["kind"] in ARMS[arm]]
    available = {p["kind"] for p in providers if p["status"] == "ok"}
    records = [dict(deepcopy(r), id=digest(identity(r)))
               for r in case["records"] if r["kind"] in available]
    return providers, records


def prefix_within_budget(records, limit):
    kept = []
    for record in records:
        if quote_estimate(kept + [record]) > limit:
            break
        kept.append(record)
    return kept, records[len(kept):]


def conflict_pairs(records):
    return [[left["id"], right["id"]]
            for index, left in enumerate(records) for right in records[index + 1:]
            if left["claim"] == right["claim"] and left["value"] != right["value"]]


def traces(case, providers, records, producer):
    return {
        "retrieval_digest": digest({"providers": providers, "records": records}),
        "provenance_digest": digest({
            "repository": case["repository"], "revision": case["revision"],
            "producer": producer, "sources": [identity(r) for r in records],
        }),
    }


def make_pack(case, arm, limit=4096):
    """Fixture-owned prefix selection, not a production retrieval broker."""
    providers, records = retrieval(case, arm)
    kept, dropped = prefix_within_budget(records, limit)
    return {
        "schema_version": "ContextPack.v0",
        "repository": case["repository"], "revision": case["revision"],
        "producer": deepcopy(PRODUCER), "freshness": "fresh", "git_state": "clean",
        "providers": providers, "evidence": kept, "conflicts": conflict_pairs(kept),
        "budget": {
            "limit": limit, "estimated_tokens": quote_estimate(kept),
            "measurement": "estimate", "algorithm": "utf8_quote_bytes_div4_ceil_v0",
            "scope": "evidence_quotes", "truncated": bool(dropped),
            "dropped_ids": [record["id"] for record in dropped],
        },
        "trace": traces(case, providers, records, PRODUCER),
    }


class ContractError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ContractError(reason)


def validate_contract(pack, case, arm):
    """Bind structural validation to an independent synthetic source manifest."""
    require(not list(Draft202012Validator(SCHEMA).iter_errors(pack)), "schema")
    require(pack["repository"] == case["repository"], "repository")
    require(pack["revision"] == case["revision"], "revision")
    require(pack["producer"] == PRODUCER, "producer")
    require(pack["freshness"] == "fresh", "freshness")
    require(pack["git_state"] == "clean", "worktree")
    providers, records = retrieval(case, arm)
    require(pack["providers"] == providers, "provider")
    for provider in providers:
        matches = [r for r in case["records"] if r["kind"] == provider["kind"]]
        require((provider["status"] == "ok") == bool(matches), "provider")
        require(provider["status"] not in ("error", "unsupported") or provider["detail"], "provider")

    expected = {record["id"]: record for record in records}
    for record in pack["evidence"]:
        require(record["repository"] == case["repository"], "repository")
        require(record["revision"] == case["revision"], "revision")
        require(record["freshness"] == "fresh", "freshness")
        require(record["git_state"] == "clean", "worktree")
        lines = case["files"].get(record["path"], "").splitlines()
        require(0 < record["line"] <= len(lines), "citation")
        require(lines[record["line"] - 1] == record["quote"], "citation")
        require(record["id"] == digest(identity(record)), "evidence_id")
        require(record["id"] in expected, "evidence_id")
        require(record == expected[record["id"]], "evidence")
    ids = [record["id"] for record in pack["evidence"]]
    require(len(ids) == len(set(ids)), "evidence_id")
    kept, dropped = prefix_within_budget(records, pack["budget"]["limit"])
    require(ids == [record["id"] for record in kept], "selection")
    require(pack["conflicts"] == conflict_pairs(kept), "conflicts")
    budget = pack["budget"]
    require(budget["estimated_tokens"] == quote_estimate(kept), "budget")
    require(budget["estimated_tokens"] <= budget["limit"], "budget")
    require(budget["truncated"] == bool(dropped), "budget")
    require(budget["dropped_ids"] == [record["id"] for record in dropped], "budget")
    require(pack["trace"] == traces(case, providers, records, pack["producer"]), "trace")


def mutate(pack, path, value):
    target = pack
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def test_schema_is_closed_and_valid():
    Draft202012Validator.check_schema(SCHEMA)
    for case in CASES:
        for arm in ARMS:
            validate_contract(make_pack(case, arm), case, arm)


def test_rejects_wrong_repository():
    case = CASES[0]
    pack = make_pack(case, "D_UNION")
    validate_contract(pack, case, "D_UNION")
    pack["repository"] = CASES[1]["repository"]
    with pytest.raises(ContractError, match="^repository$"):
        validate_contract(pack, case, "D_UNION")


@pytest.mark.parametrize("path,value,reason", [
    (("unexpected",), True, "schema"),
    (("budget", "limit"), "4096", "schema"),
    (("schema_version",), "ContextPack.v1", "schema"),
    (("revision",), "c" * 40, "revision"),
    (("producer", "instance"), "other", "producer"),
    (("evidence", 0, "repository"), "fixture://other", "repository"),
    (("evidence", 0, "revision"), "c" * 40, "revision"),
    (("evidence", 0, "quote"), "invented citation", "citation"),
    (("evidence", 0, "path"), "../shared.py", "citation"),
    (("evidence", 0, "line"), 99, "citation"),
    (("evidence", 0, "id"), "0" * 64, "evidence_id"),
    (("evidence", 1, "producer_instance"), "memory-other", "evidence_id"),
    (("evidence", 1, "source_id"), "8", "evidence_id"),
    (("freshness",), "stale", "freshness"),
    (("freshness",), "unknown", "freshness"),
    (("git_state",), "dirty", "worktree"),
    (("git_state",), "unknown", "worktree"),
    (("evidence", 0, "freshness"), "stale", "freshness"),
    (("evidence", 1, "freshness"), "unknown", "freshness"),
    (("evidence", 0, "git_state"), "dirty", "worktree"),
    (("evidence", 1, "git_state"), "unknown", "worktree"),
    (("conflicts",), [], "conflicts"),
    (("budget", "estimated_tokens"), 0, "budget"),
    (("budget", "measurement"), "measured", "schema"),
    (("budget", "algorithm"), "real-tokenizer", "schema"),
    (("budget", "scope"), "complete-model-context", "schema"),
    (("trace", "retrieval_digest"), "0" * 64, "trace"),
    (("trace", "provenance_digest"), "0" * 64, "trace"),
])
def test_independent_contract_mutations(path, value, reason):
    case = CASES[0]
    pack = make_pack(case, "D_UNION")
    validate_contract(pack, case, "D_UNION")
    mutate(pack, path, value)
    with pytest.raises(ContractError, match=f"^{reason}$"):
        validate_contract(pack, case, "D_UNION")


def test_duplicate_evidence_is_rejected():
    case = CASES[0]
    pack = make_pack(case, "D_UNION")
    pack["evidence"].append(deepcopy(pack["evidence"][0]))
    with pytest.raises(ContractError, match="^evidence_id$"):
        validate_contract(pack, case, "D_UNION")


@pytest.mark.parametrize("status", ["empty", "error", "unsupported"])
def test_provider_outcomes_are_distinct_and_not_silently_empty(status):
    case = deepcopy(CASES[0])
    case["providers"][0].update(status=status, detail="" if status == "empty" else status)
    case["records"] = [r for r in case["records"] if r["kind"] != "structure"]
    pack = make_pack(case, "B_STRUCTURE")
    validate_contract(pack, case, "B_STRUCTURE")
    assert pack["providers"][0]["status"] == status
    assert pack["evidence"] == []
    pack["providers"][0]["status"] = "empty" if status != "empty" else "ok"
    with pytest.raises(ContractError, match="^provider$"):
        validate_contract(pack, case, "B_STRUCTURE")


@pytest.mark.parametrize("offset,kept", [(-1, 0), (0, 1), (1, 1)])
def test_budget_below_exactly_at_and_above_boundary(offset, kept):
    case = CASES[0]
    cost = (len(case["records"][0]["quote"].encode("utf-8")) + 3) // 4
    pack = make_pack(case, "B_STRUCTURE", cost + offset)
    validate_contract(pack, case, "B_STRUCTURE")
    assert len(pack["evidence"]) == kept
    assert pack["budget"]["estimated_tokens"] == (cost if kept else 0)
    assert pack["budget"]["truncated"] is (not kept)


@pytest.mark.parametrize("field,value", [("truncated", False), ("dropped_ids", [])])
def test_truncation_cannot_be_hidden(field, value):
    case = CASES[0]
    pack = make_pack(case, "D_UNION", 0)
    validate_contract(pack, case, "D_UNION")
    pack["budget"][field] = value
    with pytest.raises(ContractError, match="^budget$"):
        validate_contract(pack, case, "D_UNION")


def test_ids_bind_repositories_revisions_and_provider_instances():
    left, right = [make_pack(case, "D_UNION") for case in CASES]
    assert left["evidence"][0]["path"] == right["evidence"][0]["path"]
    assert left["evidence"][0]["line"] == right["evidence"][0]["line"]
    assert left["evidence"][1]["source_id"] == right["evidence"][1]["source_id"] == "7"
    assert left["evidence"][1]["producer_instance"] != right["evidence"][1]["producer_instance"]
    assert len({r["id"] for pack in (left, right) for r in pack["evidence"]}) == 4
    original = left["evidence"][1]
    for key, value in (("repository", "fixture://beta"), ("revision", "b" * 40),
                       ("producer_instance", "memory-beta")):
        changed = dict(original, **{key: value})
        assert digest(identity(changed)) != original["id"]


def test_digest_sensitivity_matches_declared_scope():
    case = CASES[0]
    providers, records = retrieval(case, "D_UNION")
    base = traces(case, providers, records, PRODUCER)
    changed_records = deepcopy(records)
    changed_records[0]["quote"] += " changed"
    content = traces(case, providers, changed_records, PRODUCER)
    assert content["retrieval_digest"] != base["retrieval_digest"]
    assert content["provenance_digest"] == base["provenance_digest"]
    producer = dict(PRODUCER, instance="other")
    origin = traces(case, providers, records, producer)
    assert origin["provenance_digest"] != base["provenance_digest"]
    assert origin["retrieval_digest"] == base["retrieval_digest"]


def test_outbound_denial_negative_control(no_outbound):
    before = len(no_outbound)
    with socket.socket() as connection:
        with pytest.raises(OutboundDenied, match="outbound operation denied"):
            connection.connect(("203.0.113.1", 443))
    with pytest.raises(OutboundDenied, match="outbound operation denied"):
        socket.getaddrinfo("fixture.invalid", 443)
    assert len(no_outbound) == before + 2


def test_preloaded_collection_is_explicitly_skipped(no_outbound):
    # Probe only this module under already-loaded imports, never the real conftest.
    import runpy

    with pytest.raises(pytest.skip.Exception) as skipped:
        runpy.run_path(str(Path(__file__)))
    assert skipped.value.allow_module_level is True
    assert str(skipped.value) == "requires standalone --noconftest for pre-import offline guard"
    assert not no_outbound


def test_import_and_nested_guards_restore_state():
    assert IMPORT_STATE_RESTORED
    previous_connect = socket.socket.connect
    with outbound_guard():
        assert socket.socket.connect is not previous_connect
    assert socket.socket.connect is previous_connect


class RecordingAdapter:
    model = "fixture-replay"
    provider = "offline"

    def __init__(self, expected_prompt, systems):
        self.expected_prompt = expected_prompt
        self.systems = systems
        self.calls = []
        self.counts = Counter()

    async def complete(self, prompt, system_prompt=None):
        assert prompt == self.expected_prompt
        assert system_prompt in self.systems
        arm = self.systems[system_prompt]
        repetition = self.counts[arm]
        self.counts[arm] += 1
        self.calls.append({"arm": arm, "repetition": repetition, "prompt": prompt,
                           "system_prompt": system_prompt,
                           "prompt_digest": digest(prompt), "system_digest": digest(system_prompt)})
        return LLMResponse(
            content=canonical({"arm": arm, "repetition": repetition}),
            model=self.model, provider=self.provider,
            raw_response={"telemetry": "unavailable_fixture"},
        )


def wrapped_skill(content):
    """Independent exact expected bytes for the existing inject_skill contract."""
    return ("You are a helpful AI assistant.\n\n"
            "Below is a skill that provides guidelines for your responses:\n---\n"
            + content + "\n---\n\n"
            "Follow the skill guidelines above when responding to the user.")


@pytest.mark.asyncio
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
async def test_real_engine_four_arms_two_repetitions(case, no_outbound):
    config = EvalConfig.model_validate(yaml.safe_load((FIXTURES / "eval.yaml").read_text()))
    assert tuple(config.treatments) == tuple(ARMS)
    assert config.execution.repetitions == 2
    prompt = f"Inspect {case['repository']}@{case['revision']}: src/shared.py:1."
    config.tests = [Task(name=case["id"], prompt=prompt, evaluators=[
        RegexEvaluator(name="replay-json-envelope", pattern=r"^\{.*\}$")
    ])]
    packs = {arm: make_pack(case, arm) for arm in ARMS}
    for arm, pack in packs.items():
        validate_contract(pack, case, arm)
    assert packs["D_UNION"]["evidence"] == (
        packs["B_STRUCTURE"]["evidence"] + packs["C_MEMORY"]["evidence"]
    )
    assert packs["D_UNION"]["conflicts"] == [
        [record["id"] for record in packs["D_UNION"]["evidence"]]
    ]
    virtual = {}
    systems = {None: "CONTROL"}
    for arm, treatment in config.treatments.items():
        if arm == "CONTROL":
            assert treatment.skill_path is None
            continue
        path = f"/__contextpack_fixture__/{case['id']}/{arm}.md"
        content = canonical(packs[arm])
        virtual[path] = content
        treatment.skill_path = path
        systems[wrapped_skill(content)] = arm
    adapter = RecordingAdapter(prompt, systems)
    exists, read_text = Path.exists, Path.read_text

    def fixture_exists(path):
        return str(path) in virtual or exists(path)

    def fixture_read(path, *args, **kwargs):
        return virtual[str(path)] if str(path) in virtual else read_text(path, *args, **kwargs)

    with patch.object(Path, "exists", fixture_exists), patch.object(Path, "read_text", fixture_read):
        results = await ExecutionEngine(config, adapter, EvaluatorEngine()).run_all(list(ARMS))
    expected = [(rep, arm) for rep in range(2) for arm in ARMS]
    assert len(results) == len(adapter.calls) == 8
    assert [(call["repetition"], call["arm"]) for call in adapter.calls] == expected
    for result, call, (rep, arm) in zip(results, adapter.calls, expected, strict=True):
        system = None if arm == "CONTROL" else wrapped_skill(canonical(packs[arm]))
        assert result.test == case["id"] and result.treatment == arm
        assert result.prompt == call["prompt"] == prompt
        assert call["system_prompt"] == system
        assert call["prompt_digest"] == digest(prompt)
        assert call["system_digest"] == digest(system)
        assert json.loads(result.response.content) == {"arm": arm, "repetition": rep}
        assert result.passed and len(result.evaluator_results) == 1
        assert result.response.prompt_tokens is None and result.response.total_tokens is None
        assert result.response.raw_response == {"telemetry": "unavailable_fixture"}
    assert not no_outbound
