"""Standalone offline runner proof; fail closed if providers were preloaded."""

import os
import socket
import sys
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import pytest

if any(name == "litellm" or name.startswith(("litellm.", "md_evals")) for name in sys.modules):
    pytest.skip(
        "run this module alone with --noconftest; unexpected provider preload",
        allow_module_level=True,
    )


@contextmanager
def outbound_guard():
    events = []

    def deny(*args, **kwargs):
        events.append("denied")
        raise AssertionError("offline runner: outbound operation forbidden")

    with ExitStack() as stack:
        for target in (
            "socket.getaddrinfo",
            "socket.socket.connect",
            "socket.socket.connect_ex",
            "socket.socket.sendto",
            "socket.socket.sendmsg",
            "subprocess.Popen",
            "os.system",
        ):
            stack.enter_context(patch(target, deny))
        yield events


_COST_BEFORE = os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP")
_CONNECT_BEFORE = socket.socket.connect
with (
    outbound_guard() as import_events,
    patch.dict(os.environ, {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}),
):
    import asyncio
    import hashlib
    import json
    from copy import deepcopy
    from datetime import datetime
    from pathlib import Path

    import httpx

    from md_evals.engine import ExecutionEngine
    from md_evals.bridge_adapter import BridgeCompletionAdapter
    from md_evals.bridge_usage import decode_generate_response
    from md_evals.captured_batch_comparison import compare_captured_batch
    from md_evals.captured_batch_report import render_captured_report_json
    from md_evals.llm import LLMError
    from md_evals.models import Defaults, EvalConfig, LLMResponse, OutputConfig, Task, Treatment
    from md_evals.context_renderer import (
        compose_paired_context,
        render_paired_context,
        render_selected_evidence,
    )
    from md_evals.captured_pilot_plan import CapturedPilotPlan, prepare_captured_pilot
    from tests.context_broker_capture_union_support import compose_capture
    from md_evals.captured_context_runner import (
        CapturedRunError,
        _ContextAdapter,
        run_captured_arms_offline,
        run_captured_arms,
    )
    from md_evals.offline_worker import INPUT_SCHEMA, OUTPUT_SCHEMA, OfflineWorkerInput

if import_events:
    raise RuntimeError("provider import attempted outbound work")

ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
BASE = Path(__file__).parents[1] / "fixtures/context_broker"


@pytest.fixture(autouse=True)
def offline_only():
    assert os.environ.get("LITELLM_LOCAL_MODEL_COST_MAP") == _COST_BEFORE
    assert socket.socket.connect is _CONNECT_BEFORE
    with (
        outbound_guard() as events,
        patch(
            "md_evals.llm.LLMAdapter.__init__", side_effect=AssertionError("provider constructor")
        ),
        patch.object(ExecutionEngine, "run_all", side_effect=AssertionError("run_all forbidden")),
    ):
        yield
    assert events == []


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def inputs():
    graph_root, memory_root = BASE / "repoforge_capture", BASE / "engram_capture"
    graph = (
        (graph_root / "graph.json").read_bytes(),
        {
            name: (graph_root / name).read_bytes()
            for name in ("src/base.ts", "src/consumer.ts", "src/entry.js")
        },
        (graph_root / "provenance.json").read_bytes(),
    )
    manifest = (memory_root / "provenance.json").read_bytes()
    files = {
        name: (memory_root / name).read_bytes()
        for name in (
            "save-response.json",
            "search-response.json",
            "get-response.json",
            "observation-rendering.txt",
        )
    }
    modes = {"B_STRUCTURE": "structure-only", "C_MEMORY": "memory-only"}
    arms = {"CONTROL": None}
    for arm, mode in modes.items():
        arms[arm] = compose_capture(
            graph,
            files,
            manifest,
            target=json.loads(manifest)["target"],
            mode=mode,
            expected_graph_manifest_sha256="45bf178c883014e1482661f210828622e221ad8f301e09b506a5af6d152842cf",
            expected_memory_manifest_sha256="a27107b7e2f72c41657c4d394455f7b93d05b7c9761259ea89b186ef2a6611a2",
        )
    arms["E_PAIRED"] = compose_paired_context(arms["B_STRUCTURE"], arms["C_MEMORY"])
    config = EvalConfig(
        name="captured",
        defaults=Defaults(model="offline", provider="recording"),
        treatments={arm: Treatment() for arm in ARMS},
        tests=[
            Task(name=name, prompt="Explain {name}", variables={"name": name})
            for name in ("first", "last")
        ],
        output=OutputConfig(save_results=False),
    )
    config.execution.repetitions = 2
    return config, {task.name: deepcopy(arms) for task in config.tests}


class Recorder:
    def __init__(self, defaults, effect=None):
        self.defaults = defaults.model_copy(deep=True)
        self.model, self.provider = defaults.model, defaults.provider
        self.calls, self.responses, self.effect = [], [], effect

    async def complete(self, prompt, system_prompt=None):
        self.calls.append((prompt, system_prompt, self.defaults.model_dump()))
        if self.effect:
            self.effect(len(self.calls))
        response = LLMResponse(
            content=str(len(self.calls)), model=self.model, provider=self.provider
        )
        self.responses.append(response)
        return response


class TrackingMockTransport(httpx.MockTransport):
    def __init__(self, handler):
        super().__init__(handler)
        self.closed = False

    async def aclose(self):
        self.closed = True
        await super().aclose()


@pytest.mark.anyio
async def test_decoded_usage_provenance_survives_captured_run_rows(inputs):
    config, packs = inputs
    config.execution.repetitions = 1
    config.tests = [Task(name="first", prompt="Literal first", variables={})]
    adapter = Recorder(config.defaults)

    async def complete(prompt, system_prompt=None):
        adapter.calls.append((prompt, system_prompt, adapter.defaults.model_dump()))
        response = decode_generate_response(
            {
                "text": "captured",
                "usageProvenance": {
                    "status": "partial",
                    "origin": "cli-output",
                    "eventCount": 1,
                    "outputTokens": 7,
                },
            },
            model=adapter.model,
            provider=adapter.provider,
        )
        adapter.responses.append(response)
        return response

    adapter.complete = complete
    rows = await run_captured_arms(config, adapter, {"first": packs["first"]})

    assert len(rows) == len(adapter.responses) == 4
    assert all(row.response is response for row, response in zip(rows, adapter.responses))
    assert all(
        row.response.usage_provenance
        == {
            "status": "partial",
            "origin": "cli-output",
            "eventCount": 1,
            "outputTokens": 7,
        }
        for row in rows
    )


def pilot_plan(config, packs):
    return prepare_captured_pilot(
        cases=[
            {
                "name": task.name,
                "prompt": task.prompt,
                "expected": {"answer": "VALUE", "citations": [], "abstain": False},
                "packs": packs[task.name],
            }
            for task in config.tests
        ],
        provider=config.defaults.provider,
        model=config.defaults.model,
        backend_config_sha256="c" * 64,
        limits={
            "max_primary_calls": len(config.tests) * 4,
            "per_call_timeout_seconds": config.defaults.timeout,
            "total_timeout_seconds": 100,
        },
    )


@pytest.mark.anyio
async def test_optional_pilot_plan_binds_one_attempt_snapshot_before_first_call(inputs):
    config, packs = inputs
    config.execution.repetitions = 1
    config.defaults.retry_attempts = 1
    config.tests = [Task(name="first", prompt="Literal first", variables={})]
    packs = {"first": packs["first"]}
    plan = pilot_plan(config, packs)
    plan_identity = (plan.manifest_json, plan.sha256)
    expected_context = render_paired_context(packs["first"]["E_PAIRED"])
    expected_ids = tuple(
        item["id"]
        for slot in ("structure", "memory")
        for item in packs["first"]["E_PAIRED"][slot]["evidence"]
    )

    def mutate_after_first(index):
        if index == 1:
            config.tests[0].prompt = "MUTATED"
            packs["first"]["E_PAIRED"]["structure"]["evidence"].clear()

    adapter = Recorder(config.defaults, mutate_after_first)
    rows = await run_captured_arms(config, adapter, packs, plan=plan)
    assert len(adapter.calls) == len(rows) == 4
    assert adapter.calls[-1][0] == "Literal first"
    assert adapter.calls[-1][1] == expected_context and rows[-1].selected_ids == expected_ids
    assert (plan.manifest_json, plan.sha256) == plan_identity
    assert plan.to_dict()["execution_authorized"] is False


@pytest.mark.parametrize("change", ["variables", "retry", "timeout", "provider", "manual"])
@pytest.mark.anyio
async def test_pilot_plan_admission_failures_make_zero_calls(inputs, change):
    config, packs = inputs
    config.execution.repetitions = 1
    config.defaults.retry_attempts = 1
    config.tests = [Task(name="first", prompt="Literal first", variables={})]
    packs = {"first": packs["first"]}
    plan = pilot_plan(config, packs)
    if change == "variables":
        config.tests[0].variables = {"x": "y"}
    elif change == "retry":
        config.defaults.retry_attempts = 0
    elif change == "timeout":
        config.defaults.timeout += 1
    elif change == "provider":
        config.defaults.provider = "other"
    else:
        plan = CapturedPilotPlan("{}", "0" * 64)
    adapter = Recorder(config.defaults)
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs, plan=plan)
    assert adapter.calls == []


def bound_inputs(inputs):
    config, packs = inputs
    config.execution.repetitions = 1
    config.defaults.retry_attempts = 1
    config.tests = [Task(name="first", prompt="Literal first", variables={})]
    return config, {"first": packs["first"]}


def rebuilt_plan(plan, mutate):
    value = plan.to_dict()
    mutate(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return CapturedPilotPlan(raw, hashlib.sha256(raw.encode()).hexdigest())


@pytest.mark.parametrize(
    "change",
    ["prompt", "order", "repetitions", "model", "metadata", "quote", "id", "origin", "last"],
)
@pytest.mark.anyio
async def test_bound_plan_contract_mismatches_admit_zero_calls(inputs, change):
    config, packs = bound_inputs(inputs)
    plan = pilot_plan(config, packs)
    if change == "prompt":
        config.tests[0].prompt = "different"
    elif change == "order":
        config.tests = [Task(name="other", prompt="Literal first", variables={})]
    elif change == "repetitions":
        config.execution.repetitions = 2
    elif change == "model":
        config.defaults.model = "other"
    elif change == "metadata":
        packs["first"]["E_PAIRED"]["structure"]["trace"]["unselected"] = "changed"
    elif change == "quote":
        packs["first"]["E_PAIRED"]["structure"]["evidence"][0]["quote"] = "changed"
    elif change == "id":
        packs["first"]["E_PAIRED"]["structure"]["evidence"][0]["id"] = "f" * 64
    elif change == "origin":
        packs["first"]["E_PAIRED"]["structure"]["repository"] = "other"
    else:
        plan = rebuilt_plan(plan, lambda value: value["cases"].append(value["cases"][0]))
    adapter = Recorder(config.defaults)
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs, plan=plan)
    assert adapter.calls == []


@pytest.mark.parametrize(
    "raw", ["{", '{"x":1}', "[[]]", '{"x":NaN}', "[" * 2000 + "]" * 2000, "\ud800"]
)
@pytest.mark.anyio
async def test_malformed_or_manually_constructed_plan_never_escapes_run_error(inputs, raw):
    config, packs = bound_inputs(inputs)
    try:
        digest = hashlib.sha256(raw.encode()).hexdigest()
    except UnicodeEncodeError:
        digest = "0" * 64
    adapter = Recorder(config.defaults)
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs, plan=CapturedPilotPlan(raw, digest))
    assert adapter.calls == []


@pytest.mark.anyio
async def test_sixteen_real_engine_calls_preserve_order_context_and_raw_metadata(inputs):
    config, packs = inputs
    original = deepcopy((config, packs))
    adapter = Recorder(config.defaults)
    observed = []
    run_single = ExecutionEngine.run_single

    async def observe(engine, treatment, task, treatment_name):
        observed.append((treatment_name, task.name, treatment.skill_path))
        return await run_single(engine, treatment, task, treatment_name)

    with (
        patch.object(ExecutionEngine, "run_single", observe),
        patch.object(Path, "read_text", side_effect=AssertionError("skill read forbidden")),
    ):
        rows = await run_captured_arms(config, adapter, packs)
    expected = [(rep, name, arm) for rep in range(2) for name in ("first", "last") for arm in ARMS]
    assert [(row.repetition, row.task, row.arm) for row in rows] == expected
    assert observed == [(arm, name, None) for _, name, arm in expected]
    for index, (row, (_, name, arm)) in enumerate(zip(rows, expected)):
        if arm == "E_PAIRED":
            context = render_paired_context(packs[name][arm])
            ids = tuple(
                item["id"]
                for slot in ("structure", "memory")
                for item in packs[name][arm][slot]["evidence"]
            )
        else:
            context = render_selected_evidence(packs[name][arm])
            ids = (
                ()
                if arm == "CONTROL"
                else tuple(item["id"] for item in packs[name][arm]["evidence"])
            )
        assert adapter.calls[index] == (f"Explain {name}", context, config.defaults.model_dump())
        assert row.prompt == f"Explain {name}" and row.selected_ids == ids
        assert row.rendered_context_sha256 == (
            None if context is None else hashlib.sha256(context.encode()).hexdigest()
        )
        assert row.response is adapter.responses[index] and row.status == "completed"
        assert row.response.prompt_tokens is row.response.total_tokens is None
        assert row.response.completion_tokens_detail is None and row.response.tokens == 0
        assert datetime.fromisoformat(row.timestamp).tzinfo is not None
        assert not hasattr(row, "passed") and not hasattr(row, "grade")
    assert (config, packs) == original


@pytest.mark.anyio
async def test_audit_sentinels_and_later_input_mutations_never_change_prepared_calls(inputs):
    config, packs = inputs
    for arms in packs.values():
        for arm, value in arms.items():
            if value is not None:
                slots = (value["structure"], value["memory"]) if arm == "E_PAIRED" else (value,)
                for slot in slots:
                    slot["trace"]["retrieval_digest"] = "ANSWER_SENTINEL"
                    for provider in slot["providers"]:
                        provider["detail"] = "MANIFEST_SENTINEL"
    expected = render_paired_context(packs["last"]["E_PAIRED"])

    def mutate_on_first(index):
        if index == 1:
            config.tests[-1].prompt = "MUTATED"
            packs["last"]["E_PAIRED"]["structure"]["evidence"].clear()

    adapter = Recorder(config.defaults, mutate_on_first)
    rows = await run_captured_arms(config, adapter, packs)
    assert adapter.calls[-1][0:2] == ("Explain last", expected)
    assert all(
        ("ANSWER_SENTINEL" in (call[1] or "") and "MANIFEST_SENTINEL" in (call[1] or ""))
        if row.arm == "E_PAIRED"
        else "SENTINEL" not in (call[1] or "")
        for row, call in zip(rows, adapter.calls)
    )
    assert rows[-1].rendered_context_sha256 == rows[7].rendered_context_sha256


def assign(value, path, replacement):
    for key in path[:-1]:
        value = value[key] if isinstance(value, (dict, list)) else getattr(value, key)
    if isinstance(value, (dict, list)):
        value[path[-1]] = replacement
    else:
        setattr(value, path[-1], replacement)


@pytest.mark.parametrize(
    "path,value",
    [
        (("execution", "repetitions"), True),
        (("execution", "repetitions"), 0),
        (("execution", "parallel_workers"), 2),
        (("execution", "fail_fast"), True),
        (("models",), ["unsupported"]),
        (("pipeline",), {}),
        (("cost_map",), {"x": {}}),
        (("context_window_overrides",), {"x": 1}),
        (("output", "save_results"), True),
        (("output", "include_usage_metrics"), True),
        (("lint", "max_lines"), 500),
        (("treatments", "E_PAIRED", "skill_path"), "forbidden.md"),
        (("treatments", "C_MEMORY", "env"), {"X": "ignored"}),
        (("tests", 1, "evaluators"), ["unsupported"]),
        (("tests", 1, "name"), ""),
        (("tests", 1, "name"), "first"),
        (("tests",), []),
    ],
)
@pytest.mark.anyio
async def test_invalid_configuration_admits_zero_calls_including_last_task(inputs, path, value):
    config, packs = inputs
    adapter = Recorder(config.defaults)
    assign(config, path, value)
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs)
    assert adapter.calls == []


@pytest.mark.parametrize(
    "path,value",
    [
        (("CONTROL",), {}),
        (("C_MEMORY",), None),
        (("E_PAIRED", "schema_version"), "ContextPack.v0"),
        (("E_PAIRED", "structure", "repository"), "fixture://other"),
        (("E_PAIRED", "structure", "revision"), "sha256:" + "0" * 64),
        (("E_PAIRED", "structure", "budget", "limit"), 100),
        (("E_PAIRED", "structure", "providers", 0, "instance"), "different"),
        (("E_PAIRED", "structure", "providers", 0, "detail"), "different"),
        (("E_PAIRED", "structure", "providers", 0, "kind"), "memory"),
        (("E_PAIRED", "structure", "evidence", 0, "producer_instance"), "unbound"),
        (("E_PAIRED", "structure", "evidence", 0, "quote"), "contradictory same ID"),
        (("B_STRUCTURE", "evidence", 0, "kind"), "memory"),
    ],
)
@pytest.mark.anyio
async def test_invalid_last_task_packs_admit_zero_total_calls(inputs, path, value):
    config, packs = inputs
    adapter = Recorder(config.defaults)
    assign(packs["last"], path, value)
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs)
    assert adapter.calls == []


@pytest.mark.parametrize("location", ["config-arm", "pack-arm", "task"])
@pytest.mark.anyio
async def test_exact_arm_and_task_coverage(inputs, location):
    config, packs = inputs
    adapter = Recorder(config.defaults)
    if location == "config-arm":
        del config.treatments["CONTROL"]
    elif location == "pack-arm":
        packs["last"]["extra"] = None
    else:
        packs["extra"] = packs["last"]
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs)
    assert adapter.calls == []


@pytest.mark.parametrize(
    "attribute,value", [("model", "other"), ("provider", "other"), ("defaults", None)]
)
@pytest.mark.anyio
async def test_adapter_identity_and_defaults_must_match(inputs, attribute, value):
    config, packs = inputs
    adapter = Recorder(config.defaults)
    setattr(adapter, attribute, value)
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs)
    assert adapter.calls == []


@pytest.mark.parametrize("keep", [0, 1])
@pytest.mark.anyio
async def test_union_truncation_can_remove_one_or_both_kinds(inputs, keep):
    config, packs = inputs
    for arms in packs.values():
        union = arms["E_PAIRED"]["structure"]
        dropped = union["evidence"][keep:]
        union["evidence"] = union["evidence"][:keep]
        union["budget"].update(truncated=True, dropped_ids=[item["id"] for item in dropped])
    rows = await run_captured_arms(config, Recorder(config.defaults), packs)
    pair = packs["first"]["E_PAIRED"]
    expected_ids = tuple(
        item["id"] for slot in ("structure", "memory") for item in pair[slot]["evidence"]
    )
    expected_context = render_paired_context(pair)
    assert len(rows) == 16
    assert rows[3].selected_ids == expected_ids
    assert rows[3].rendered_context_sha256 == hashlib.sha256(expected_context.encode()).hexdigest()


@pytest.mark.anyio
async def test_engine_llm_error_rows_continue_without_inventing_usage(inputs):
    config, packs = inputs

    def fail_first(index):
        if index == 1:
            raise LLMError("offline error", {"code": "SIMULATED"})

    adapter = Recorder(config.defaults, fail_first)
    rows = await run_captured_arms(config, adapter, packs)
    assert len(adapter.calls) == len(rows) == 16
    assert rows[0].status == "llm_error" and rows[1].status == "completed"
    assert rows[0].response.raw_response == {"code": "SIMULATED"}
    assert rows[0].response.content == "[LLM ERROR] offline error"
    assert rows[0].response.duration_ms == 0 and rows[0].response.prompt_tokens is None


@pytest.mark.parametrize("failure", [RuntimeError("unexpected"), asyncio.CancelledError()])
@pytest.mark.anyio
async def test_unexpected_failure_and_cancellation_stop_without_retry(inputs, failure):
    config, packs = inputs

    def fail_second(index):
        if index == 2:
            raise failure

    adapter = Recorder(config.defaults, fail_second)
    with pytest.raises(type(failure)):
        await run_captured_arms(config, adapter, packs)
    assert len(adapter.calls) == 2


@pytest.mark.anyio
async def test_bound_adapter_refuses_engine_system_context(inputs):
    config, _ = inputs
    adapter = Recorder(config.defaults)
    boundary = _ContextAdapter(adapter, config.defaults.model_copy(deep=True), "selected")
    with pytest.raises(CapturedRunError):
        await boundary.complete("prompt", system_prompt="unexpected")
    assert adapter.calls == []


class ScriptedRecorder(Recorder):
    """Keep Recorder's offline call contract while assigning deterministic answers by call."""

    def __init__(self, defaults, scripted_calls, effect=None):
        super().__init__(defaults, effect)
        self.scripted_calls = tuple(scripted_calls)
        self.trace = []

    async def complete(self, prompt, system_prompt=None):
        index = len(self.calls)
        key, content = self.scripted_calls[index]
        self.trace.append((key, prompt, system_prompt))
        response = await super().complete(prompt, system_prompt)
        response.content = content
        return response


def _answer(answer, citations=(), abstain=False):
    return json.dumps(
        {"answer": answer, "citations": list(citations), "abstain": abstain},
        sort_keys=True,
    )


def _record_by_kind(arms, kind, path, quote):
    records = [
        record
        for slot in ("structure", "memory")
        for record in arms["E_PAIRED"][slot]["evidence"]
        if (record["kind"], record["path"], record["quote"]) == (kind, path, quote)
    ]
    assert len(records) == 1
    return records[0]


@pytest.mark.anyio
async def test_captured_pipeline_runs_real_engine_then_strict_comparison(inputs):
    """Exercise compose -> render -> engine -> strict comparison with no provider."""
    config, original_packs = inputs
    config.tests = [
        Task(
            name="structure",
            prompt="Which named import is used in src/consumer.ts?",
            variables={},
        ),
        Task(
            name="memory",
            prompt="What is the synthetic captured named-export policy value?",
            variables={},
        ),
        Task(
            name="unknown",
            prompt=(
                "What is this repository's actual current Git commit? "
                "Abstain if it is not captured."
            ),
            variables={},
        ),
    ]
    packs = {task.name: deepcopy(original_packs["first"]) for task in config.tests}
    structure_quote = 'import { VALUE } from "./base";'
    memory_quote = "**What**: Keep VALUE as a named export from src/base.ts for src/consumer.ts."
    structure = _record_by_kind(packs["structure"], "structure", "src/consumer.ts", structure_quote)
    memory = _record_by_kind(packs["memory"], "memory", "observation-rendering.txt", memory_quote)
    assert structure["path"] == "src/consumer.ts"
    assert structure["source_id"] == "imports:src/consumer.ts:src/base.ts"
    assert structure["quote"] == structure_quote
    assert memory["source_id"].startswith("observation:")
    assert memory["quote"] == memory_quote
    assert (
        memory["revision"]
        == "sha256:"
        + hashlib.sha256((BASE / "engram_capture/get-response.json").read_bytes()).hexdigest()
    )

    expected = {
        "structure": {"answer": "VALUE", "citations": [structure["id"]], "abstain": False},
        "memory": {"answer": "keep", "citations": [memory["id"]], "abstain": False},
        "unknown": {"answer": None, "citations": [], "abstain": True},
    }
    gold = {
        "structure": _answer("VALUE", (structure["id"],)),
        "memory": _answer("keep", (memory["id"],)),
        "unknown": _answer(None, abstain=True),
    }
    planned = [
        (repetition, task.name, arm)
        for repetition in range(config.execution.repetitions)
        for task in config.tests
        for arm in ARMS
    ]
    responses = {key: gold[key[1]] for key in planned}
    responses[(0, "memory", "CONTROL")] = "not JSON"
    responses[(0, "unknown", "E_PAIRED")] = _answer("not-a-commit")
    responses[(1, "structure", "E_PAIRED")] = _answer("WRONG", (structure["id"],))
    responses[(1, "memory", "E_PAIRED")] = _answer("WRONG", (memory["id"],))
    before = deepcopy((config, packs, expected, gold, responses))

    def fail_first(index):
        if index == 1:
            raise LLMError("offline error", {"code": "SIMULATED"})

    adapter = ScriptedRecorder(
        config.defaults,
        [(key, responses[key]) for key in planned],
        effect=fail_first,
    )
    rows = await run_captured_arms(config, adapter, packs)
    assert (config, packs, expected, gold, responses) == before

    assert [(row.repetition, row.task, row.arm) for row in rows] == planned
    assert [entry[0] for entry in adapter.trace] == planned
    assert len(adapter.calls) == len(adapter.trace) == len(rows) == 24
    assert [
        response for row in rows if row.status == "completed" for response in [row.response]
    ] == (adapter.responses)

    for row, (_, prompt, seen_context) in zip(rows, adapter.trace):
        pack = packs[row.task][row.arm]
        expected_context = (
            None
            if pack is None
            else render_paired_context(pack)
            if row.arm == "E_PAIRED"
            else render_selected_evidence(pack)
        )
        expected_ids = (
            ()
            if pack is None
            else tuple(
                item["id"] for slot in ("structure", "memory") for item in pack[slot]["evidence"]
            )
            if row.arm == "E_PAIRED"
            else tuple(item["id"] for item in pack["evidence"])
        )
        assert (row.prompt, seen_context) == (prompt, expected_context)
        assert row.selected_ids == expected_ids
        assert row.rendered_context_sha256 == (
            None
            if expected_context is None
            else hashlib.sha256(expected_context.encode()).hexdigest()
        )
    assert adapter.trace[0][2] is None
    assert all(
        "structure" in (context or "")
        for key, _, context in adapter.trace
        if key[2] == "B_STRUCTURE"
    )
    assert all(
        "memory" in (context or "") for key, _, context in adapter.trace if key[2] == "C_MEMORY"
    )
    assert all(
        "structure" in context and "memory" in context
        for key, _, context in adapter.trace
        if key[2] == "E_PAIRED"
    )

    from md_evals.captured_answer_grader import GradeResult

    comparison = compare_captured_batch(rows, expected_by_task=expected, repetitions=2)
    cells = {(cell.task, cell.repetition, cell.arm): cell for cell in comparison.cells}
    summaries = {summary.arm: summary for summary in comparison.arm_summaries}
    assert comparison.complete and comparison.declared_n == 6 and len(comparison.assessments) == 24
    assert all(
        isinstance(cell.grade, GradeResult) for cell in cells.values() if cell.state == "completed"
    )
    assert (cells[("structure", 0, "CONTROL")].state, cells[("structure", 0, "CONTROL")].grade) == (
        "llm_error",
        None,
    )
    malformed = cells[("memory", 0, "CONTROL")]
    assert malformed.state == "completed" and malformed.grade.reason_code == "invalid_json"
    assert [
        (item.arm, item.completed, item.llm_errors, item.malformed_answers, item.passes)
        for item in summaries.values()
    ] == [
        ("CONTROL", 5, 1, 1, 2),
        ("B_STRUCTURE", 6, 0, 0, 4),
        ("C_MEMORY", 6, 0, 0, 4),
        ("E_PAIRED", 6, 0, 0, 3),
    ]
    assert summaries["CONTROL"].contract_pass_rate == pytest.approx(1 / 3)
    assert summaries["E_PAIRED"].contract_pass_rate == pytest.approx(1 / 2)
    for task, hidden_arm in (("structure", "C_MEMORY"), ("memory", "B_STRUCTURE")):
        hidden = cells[(task, 0, hidden_arm)].grade
        assert hidden.answer_matches and hidden.citations_match and not hidden.citations_visible
        assert not hidden.passed
    assert all(
        cell.grade is None or not cell.grade.passed
        for repetition in range(2)
        for arm in ("CONTROL", "C_MEMORY")
        for cell in [cells[("structure", repetition, arm)]]
    )
    assert all(
        cell.grade is None or not cell.grade.passed
        for repetition in range(2)
        for arm in ("CONTROL", "B_STRUCTURE")
        for cell in [cells[("memory", repetition, arm)]]
    )

    pairs = {pair.name: pair for pair in comparison.paired_comparisons}
    assert set(pairs) == {"E_PAIRED_vs_B_STRUCTURE", "E_PAIRED_vs_C_MEMORY"}
    for pair in pairs.values():
        assert (
            pair.declared_n,
            pair.available,
            pair.wins,
            pair.losses,
            pair.both_pass,
            pair.both_nonpass,
        ) == (
            6,
            True,
            1,
            2,
            2,
            1,
        )
        assert pair.delta == pytest.approx(-1 / 6)

    incomplete = compare_captured_batch(rows[:-1], expected_by_task=expected, repetitions=2)
    assert not incomplete.complete and len(incomplete.assessments) == 24
    assert sum(cell.state == "missing" and cell.grade is None for cell in incomplete.cells) == 1
    assert all(summary.contract_pass_rate is None for summary in incomplete.arm_summaries)
    assert all(summary.contract_pass_rate is None for summary in incomplete.cohort_summaries)
    assert all(
        not pair.available
        and (pair.wins, pair.losses, pair.both_pass, pair.both_nonpass, pair.delta)
        == (None, None, None, None, None)
        for pair in incomplete.paired_comparisons
    )
    assert (config, packs, expected, gold, responses) == before


@pytest.mark.anyio
async def test_frozen_twelve_call_pilot_decodes_usage_and_renders_private_report(inputs):
    """Exercise the frozen offline pilot seam without exporting captured inputs."""
    config, original_packs = inputs
    config.execution.repetitions = 1
    config.defaults.retry_attempts = 1
    config.tests = [
        Task(
            name="PRIVATE-TASK-STRUCTURE",
            prompt="PRIVATE-PROMPT: name the captured import",
            variables={},
        ),
        Task(
            name="PRIVATE-TASK-MEMORY",
            prompt="PRIVATE-PROMPT: state the captured policy",
            variables={},
        ),
        Task(
            name="PRIVATE-TASK-UNKNOWN",
            prompt="PRIVATE-PROMPT: state the uncaptured revision",
            variables={},
        ),
    ]
    packs = {task.name: deepcopy(original_packs["first"]) for task in config.tests}
    structure = _record_by_kind(
        packs["PRIVATE-TASK-STRUCTURE"],
        "structure",
        "src/consumer.ts",
        'import { VALUE } from "./base";',
    )
    memory = _record_by_kind(
        packs["PRIVATE-TASK-MEMORY"],
        "memory",
        "observation-rendering.txt",
        "**What**: Keep VALUE as a named export from src/base.ts for src/consumer.ts.",
    )
    expected = {
        "PRIVATE-TASK-STRUCTURE": {
            "answer": "VALUE",
            "citations": [structure["id"]],
            "abstain": False,
        },
        "PRIVATE-TASK-MEMORY": {"answer": "keep", "citations": [memory["id"]], "abstain": False},
        "PRIVATE-TASK-UNKNOWN": {"answer": None, "citations": [], "abstain": True},
    }
    answers = {
        "CONTROL": {
            "PRIVATE-TASK-STRUCTURE": _answer("VALUE"),
            "PRIVATE-TASK-MEMORY": _answer("keep"),
            "PRIVATE-TASK-UNKNOWN": _answer(None, abstain=True),
        },
        "B_STRUCTURE": {
            "PRIVATE-TASK-STRUCTURE": _answer("VALUE", (structure["id"],)),
            "PRIVATE-TASK-MEMORY": _answer("keep"),
            "PRIVATE-TASK-UNKNOWN": _answer(None, abstain=True),
        },
        "C_MEMORY": {
            "PRIVATE-TASK-STRUCTURE": _answer("VALUE"),
            "PRIVATE-TASK-MEMORY": _answer("keep", (memory["id"],)),
            "PRIVATE-TASK-UNKNOWN": _answer(None, abstain=True),
        },
        "E_PAIRED": {
            "PRIVATE-TASK-STRUCTURE": _answer("VALUE", (structure["id"],)),
            "PRIVATE-TASK-MEMORY": _answer("keep", (memory["id"],)),
            "PRIVATE-TASK-UNKNOWN": _answer(None, abstain=True),
        },
    }
    counter_matrix = {
        "CONTROL": {"status": "reported", "inputTokens": 0, "outputTokens": 0},
        "B_STRUCTURE": {"status": "partial", "inputTokens": 2},
        "C_MEMORY": None,
        "E_PAIRED": {"status": "reported", "inputTokens": 3, "outputTokens": 4},
    }
    planned = [(task.name, arm) for task in config.tests for arm in ARMS]
    assert len(planned) == 12 and all(len(answers[arm]) == 3 for arm in ARMS)
    plan = prepare_captured_pilot(
        cases=[
            {
                "name": task.name,
                "prompt": task.prompt,
                "expected": expected[task.name],
                "packs": packs[task.name],
            }
            for task in config.tests
        ],
        provider=config.defaults.provider,
        model=config.defaults.model,
        backend_config_sha256="c" * 64,
        limits={
            "max_primary_calls": 12,
            "per_call_timeout_seconds": config.defaults.timeout,
            "total_timeout_seconds": 100,
        },
    )
    plan_before = plan.to_dict()
    plan_identity = (plan.manifest_json, plan.sha256)

    requests, transports = [], []
    factory_calls = 0

    async def handler(request):
        index = len(requests)
        assert index < len(planned)
        task, arm = planned[index]
        requests.append(request)
        payload = {
            "text": answers[arm][task],
            "resolvedProvider": config.defaults.provider,
            "resolvedModel": config.defaults.model,
            "fallbackUsed": False,
            "tokensUsed": 999,
        }
        if counter_matrix[arm] is not None:
            payload["usageProvenance"] = {
                "origin": "cli-output",
                "eventCount": 1,
                **counter_matrix[arm],
            }
        return httpx.Response(
            200,
            headers={"set-cookie": "sentinel-session=not-replayed"},
            json=payload,
        )

    def transport_factory():
        nonlocal factory_calls
        factory_calls += 1
        transport = TrackingMockTransport(handler)
        transports.append(transport)
        return transport

    adapter = BridgeCompletionAdapter(
        base_url="https://bridge.fixture",
        model=config.defaults.model,
        provider=config.defaults.provider,
        defaults=config.defaults,
        transport_factory=transport_factory,
    )
    original_prompt = config.tests[0].prompt
    config.tests[0].prompt = "PRIVATE-PLAN-MISMATCH"
    with pytest.raises(CapturedRunError):
        await run_captured_arms(config, adapter, packs, plan=plan)
    assert factory_calls == 0 and requests == [] and transports == []
    assert plan.to_dict() == plan_before and (plan.manifest_json, plan.sha256) == plan_identity
    config.tests[0].prompt = original_prompt

    before_run = deepcopy((config, packs, expected, answers, counter_matrix))
    rows = await run_captured_arms(config, adapter, packs, plan=plan)
    assert [(row.repetition, row.task, row.arm) for row in rows] == [
        (0, task, arm) for task, arm in planned
    ]
    assert len(requests) == len(transports) == len(rows) == factory_calls == 12
    assert all(transport.closed for transport in transports)
    for request, (task, arm) in zip(requests, planned):
        context = (
            render_paired_context(packs[task][arm])
            if arm == "E_PAIRED"
            else render_selected_evidence(packs[task][arm])
        )
        expected_wire = {
            "prompt": next(item.prompt for item in config.tests if item.name == task),
            "provider": config.defaults.provider,
            "model": config.defaults.model,
            "requireProvider": True,
            "maxTokens": config.defaults.max_tokens,
        }
        if context is not None:
            expected_wire["system"] = context
        assert request.method == "POST"
        assert request.url == httpx.URL("https://bridge.fixture/v1/generate")
        assert request.headers.get("cookie") is None
        assert json.loads(request.content) == expected_wire
    normalized = {
        "CONTROL": {
            "status": "reported",
            "origin": "cli-output",
            "eventCount": 1,
            "inputTokens": 0,
            "outputTokens": 0,
        },
        "B_STRUCTURE": {
            "status": "partial",
            "origin": "cli-output",
            "eventCount": 1,
            "inputTokens": 2,
        },
        "C_MEMORY": {"status": "unknown", "reason": "absent"},
        "E_PAIRED": {
            "status": "reported",
            "origin": "cli-output",
            "eventCount": 1,
            "inputTokens": 3,
            "outputTokens": 4,
        },
    }
    assert all(row.response.usage_provenance == normalized[row.arm] for row in rows)
    assert all(row.response.raw_response["tokensUsed"] == 999 for row in rows)
    assert plan.to_dict() == plan_before and plan.to_dict()["execution_authorized"] is False
    assert (config, packs, expected, answers, counter_matrix) == before_run

    comparison = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    quality = {summary.arm: summary for summary in comparison.arm_summaries}
    assert comparison.complete and comparison.declared_n == 3
    assert {arm: quality[arm].passes for arm in ARMS} == {
        "CONTROL": 1,
        "B_STRUCTURE": 2,
        "C_MEMORY": 2,
        "E_PAIRED": 3,
    }
    hidden = {
        (cell.task, cell.arm): cell.grade for cell in comparison.cells if cell.grade is not None
    }
    assert hidden[("PRIVATE-TASK-STRUCTURE", "C_MEMORY")].citations_match is False
    assert hidden[("PRIVATE-TASK-MEMORY", "B_STRUCTURE")].citations_match is False

    rendered = render_captured_report_json(rows, expected_by_task=expected, repetitions=1)
    assert rendered == render_captured_report_json(
        reversed(rows), expected_by_task=expected, repetitions=1
    )
    report = json.loads(rendered)
    report_arms = {item["arm"]: item for item in report["arms"]}
    assert report["schema_version"] == "captured-batch-report/v1"
    assert report["complete"] is True and report["declared_n_per_arm"] == 3
    assert [item["arm"] for item in report["arms"]] == list(ARMS)
    assert {arm: report_arms[arm]["quality"]["passes"] for arm in ARMS} == {
        arm: quality[arm].passes for arm in ARMS
    }
    assert all(
        item["quality"]["declared_n"] == item["usage"]["declared_n"] == 3 for item in report["arms"]
    )
    assert report_arms["CONTROL"]["usage"] == {
        "declared_n": 3,
        "responses": 3,
        "llm_errors": 0,
        "missing": 0,
        "reported": 3,
        "partial": 0,
        "unknown": 0,
        "prompt_tokens_known_subtotal": "0",
        "completion_tokens_known_subtotal": "0",
        "total_tokens_known_subtotal": "0",
        "prompt_tokens_complete_total": "0",
        "completion_tokens_complete_total": "0",
        "total_tokens_complete_total": "0",
        "token_count_encoding": "decimal-string",
    }
    assert report_arms["B_STRUCTURE"]["usage"]["partial"] == 3
    assert report_arms["B_STRUCTURE"]["usage"]["total_tokens_complete_total"] is None
    assert report_arms["C_MEMORY"]["usage"]["unknown"] == 3
    assert report_arms["E_PAIRED"]["usage"]["total_tokens_complete_total"] == "21"
    assert all(
        value not in rendered
        for value in (
            *(expected.keys()),
            *(task.prompt for task in config.tests),
            structure["id"],
            memory["id"],
            config.defaults.provider,
            config.defaults.model,
            "VALUE",
            "keep",
        )
    )


@pytest.mark.anyio
async def test_bridge_http_429_becomes_one_complete_error_row_without_private_report_leaks(inputs):
    config, original_packs = inputs
    config.execution.repetitions = 1
    config.defaults.retry_attempts = 1
    task = Task(name="PRIVATE-HTTP-ERROR", prompt="PRIVATE-HTTP-ERROR-PROMPT", variables={})
    config.tests = [task]
    packs = {task.name: deepcopy(original_packs["first"])}
    expected = {task.name: {"answer": "value", "citations": [], "abstain": False}}
    requests, transports = [], []

    async def handler(request):
        arm = ARMS[len(requests)]
        requests.append(request)
        if arm == "C_MEMORY":
            return httpx.Response(429, text="SENTINEL-HTTP-ERROR-BODY")
        return httpx.Response(
            200,
            headers={"set-cookie": "sentinel-session=not-replayed"},
            json={
                "text": _answer("value"),
                "resolvedProvider": config.defaults.provider,
                "fallbackUsed": False,
                "usageProvenance": {
                    "status": "reported",
                    "origin": "cli-output",
                    "eventCount": 1,
                    "inputTokens": 1,
                    "outputTokens": 1,
                },
            },
        )

    def transport_factory():
        transport = TrackingMockTransport(handler)
        transports.append(transport)
        return transport

    adapter = BridgeCompletionAdapter(
        base_url="https://bridge.fixture",
        model=config.defaults.model,
        provider=config.defaults.provider,
        defaults=config.defaults,
        transport_factory=transport_factory,
    )
    rows = await run_captured_arms(config, adapter, packs)

    assert [(row.task, row.arm) for row in rows] == [(task.name, arm) for arm in ARMS]
    assert len(requests) == len(transports) == 4
    assert all(transport.closed for transport in transports)
    assert all(request.headers.get("cookie") is None for request in requests)
    assert all(
        request.url == httpx.URL("https://bridge.fixture/v1/generate") for request in requests
    )
    error_row = next(row for row in rows if row.arm == "C_MEMORY")
    assert error_row.status == "llm_error"
    assert error_row.response.content == "[LLM ERROR] Bridge request failed"
    assert error_row.response.raw_response == {"error": "Bridge request failed"}
    assert error_row.response.usage_provenance is None

    comparison = compare_captured_batch(rows, expected_by_task=expected, repetitions=1)
    cells = {(cell.task, cell.arm): cell for cell in comparison.cells}
    usage = {summary.arm: summary for summary in comparison.usage_summaries}
    assert comparison.complete and comparison.declared_n == 1
    assert cells[(task.name, "C_MEMORY")].state == "llm_error"
    assert usage["C_MEMORY"].responses == 0 and usage["C_MEMORY"].llm_errors == 1
    assert usage["C_MEMORY"].unknown == 0
    assert all(
        getattr(usage["C_MEMORY"], field) is None
        for field in (
            "prompt_tokens_known_subtotal",
            "completion_tokens_known_subtotal",
            "total_tokens_known_subtotal",
            "prompt_tokens_complete_total",
            "completion_tokens_complete_total",
            "total_tokens_complete_total",
        )
    )

    rendered = render_captured_report_json(rows, expected_by_task=expected, repetitions=1)
    report = json.loads(rendered)
    report_arms = {item["arm"]: item for item in report["arms"]}
    assert report_arms["C_MEMORY"]["quality"]["llm_errors"] == 1
    assert report_arms["C_MEMORY"]["usage"]["responses"] == 0
    assert report_arms["C_MEMORY"]["usage"]["llm_errors"] == 1
    assert all(
        secret not in rendered
        for secret in (
            "SENTINEL-HTTP-ERROR-BODY",
            config.defaults.provider,
            config.defaults.model,
            task.prompt,
        )
    )


def test_injected_offline_worker_runs_frozen_prompt_context_without_private_output(inputs):
    config, original_packs = inputs
    config.execution.repetitions = 1
    config.tests = [Task(name="PRIVATE-TASK", prompt="PRIVATE-PROMPT", variables={})]
    packs = {config.tests[0].name: deepcopy(original_packs["first"])}
    requests = []

    def worker(request: OfflineWorkerInput):
        requests.append(request)
        return {
            "schema_version": OUTPUT_SCHEMA,
            "answer": {"answer": "local", "citations": [], "abstain": False},
        }

    rows = asyncio.run(run_captured_arms_offline(config, packs, worker))

    assert len(rows) == len(requests) == 4
    assert all(request.schema_version == INPUT_SCHEMA for request in requests)
    assert requests[0].prompt == "PRIVATE-PROMPT" and requests[0].context is None
    assert requests[-1].context is not None
    assert all(row.status == "completed" for row in rows)
    assert all(
        row.response.raw_response
        == {
            "schema_version": OUTPUT_SCHEMA,
            "status": "completed",
            "answer": {"answer": "local", "citations": [], "abstain": False},
            "error_code": None,
            "error_message": None,
        }
        for row in rows
    )


def test_malformed_offline_worker_output_is_non_success_and_public_only(inputs):
    config, original_packs = inputs
    config.execution.repetitions = 1
    config.tests = [Task(name="PRIVATE-TASK", prompt="PRIVATE-PROMPT", variables={})]
    packs = {config.tests[0].name: deepcopy(original_packs["first"])}

    def worker(_request: OfflineWorkerInput):
        return {"schema_version": OUTPUT_SCHEMA, "answer": "not an answer envelope"}

    rows = asyncio.run(run_captured_arms_offline(config, packs, worker))
    assert len(rows) == 4
    assert all(row.status == "llm_error" for row in rows)
    assert all(
        row.response.raw_response
        == {
            "schema_version": OUTPUT_SCHEMA,
            "status": "malformed_output",
            "answer": None,
            "error_code": "invalid_answer_envelope",
            "error_message": "worker answer envelope rejected",
        }
        for row in rows
    )
    serialized = json.dumps([row.response.raw_response for row in rows])
    assert "PRIVATE-PROMPT" not in serialized
    assert "structure" not in serialized
