"""Execute captured four-arm inputs through the real engine, without grading."""

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol

from md_evals.context_renderer import (
    ContextRenderError,
    render_paired_context,
    render_selected_evidence,
)
from md_evals.captured_pilot_plan import CapturedPilotPlan, PilotPlanError, prepare_captured_pilot
from md_evals.engine import ExecutionEngine
from md_evals.models import (
    Defaults,
    EvalConfig,
    LinterConfig,
    LLMResponse,
    OutputConfig,
    Task,
    Treatment,
)
from md_evals.llm import LLMError
from md_evals.offline_worker import OfflineWorkerInput, run_offline_worker

ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "E_PAIRED")
_LEGACY_ARM = "D_UNION"
_ARM_KINDS = {
    "CONTROL": (),
    "B_STRUCTURE": ("structure",),
    "C_MEMORY": ("memory",),
    "D_UNION": ("structure", "memory"),
    "E_PAIRED": None,
}
_BUDGET = ("limit", "measurement", "algorithm", "scope")


class CapturedRunError(ValueError):
    """The complete batch cannot be safely admitted to this execution subset."""


class CompletionAdapter(Protocol):
    model: str
    provider: str
    defaults: Defaults

    async def complete(self, prompt: str, system_prompt: str | None = None) -> LLMResponse: ...


@dataclass(frozen=True)
class OfflineWorkerAdapter:
    """Adapt one injected callable to the captured runner's completion boundary.

    This is a callable boundary only; it does not provide process isolation or
    add retries, fallback, provider, gateway, or billing behavior.
    """

    defaults: Defaults
    worker: Callable[[OfflineWorkerInput], dict[str, Any]]

    @property
    def model(self):
        return self.defaults.model

    @property
    def provider(self):
        return self.defaults.provider

    async def complete(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        result = run_offline_worker(
            OfflineWorkerInput(prompt=prompt, context=system_prompt), self.worker
        )
        public_result = result.to_dict()
        if result.status != "completed":
            raise LLMError(f"offline worker {result.status}", public_result)
        return LLMResponse(
            content=json.dumps(public_result["answer"], sort_keys=True, separators=(",", ":")),
            model=self.model,
            provider=self.provider,
            raw_response=public_result,
        )


@dataclass(frozen=True)
class CapturedRunRow:
    arm: str
    task: str
    repetition: int
    prompt: str
    rendered_context_sha256: str | None
    selected_ids: tuple[str, ...]
    status: Literal["completed", "llm_error"]
    response: LLMResponse
    timestamp: str


@dataclass(frozen=True)
class _Prepared:
    task: str
    prompt: str
    variables: tuple[tuple[str, str], ...]
    arm: str
    context: str | None
    selected_ids: tuple[str, ...]


def _require(condition, message):
    if not condition:
        raise CapturedRunError(message)


def _adapter_matches(adapter, defaults):
    _require(
        isinstance(getattr(adapter, "defaults", None), Defaults)
        and adapter.defaults.model_dump() == defaults.model_dump()
        and getattr(adapter, "model", None) == defaults.model
        and getattr(adapter, "provider", None) == defaults.provider
        and callable(getattr(adapter, "complete", None)),
        "adapter model/provider/defaults must match the common configuration",
    )


@dataclass(frozen=True)
class _ContextAdapter:
    delegate: CompletionAdapter
    defaults: Defaults
    context: str | None

    @property
    def model(self):
        return self.defaults.model

    @property
    def provider(self):
        return self.defaults.provider

    async def complete(self, prompt, system_prompt=None):
        _require(system_prompt is None, "engine system context must be absent")
        _adapter_matches(self.delegate, self.defaults)
        return await self.delegate.complete(prompt=prompt, system_prompt=self.context)


def _validate_config(config, adapter):
    _require(
        isinstance(config, EvalConfig) and isinstance(config.defaults, Defaults), "configuration"
    )
    _adapter_matches(adapter, config.defaults)
    execution = config.execution
    _require(type(execution.repetitions) is int and execution.repetitions > 0, "repetitions")
    _require(
        type(execution.parallel_workers) is int
        and execution.parallel_workers == 1
        and execution.fail_fast is False,
        "only sequential non-fail-fast execution is supported",
    )
    _require(config.models == [] and config.pipeline is None, "models/pipeline are unsupported")
    _require(config.cost_map == {} and config.context_window_overrides == {}, "metric overrides")
    _require(
        config.output == OutputConfig(save_results=False) and config.lint == LinterConfig(),
        "disable output persistence and leave other output/lint settings at defaults",
    )
    _require(
        type(config.treatments) is dict
        and set(config.treatments) in (set(ARMS), set(ARMS) | {_LEGACY_ARM}),
        "unsupported arm set",
    )
    for treatment in config.treatments.values():
        _require(
            isinstance(treatment, Treatment)
            and treatment.skill_path is None
            and treatment.env == {},
            "skills/environment overrides are unsupported",
        )
    _require(type(config.tests) is list and bool(config.tests), "nonempty task list")
    names = []
    for task in config.tests:
        _require(isinstance(task, Task) and type(task.name) is str and bool(task.name), "task name")
        _require(type(task.prompt) is str and task.evaluators == [], "task prompt/evaluators")
        _require(
            type(task.variables) is dict
            and all(type(k) is str and type(v) is str for k, v in task.variables.items()),
            "task variables",
        )
        names.append(task.name)
    _require(len(names) == len(set(names)), "unique task names")


def _bind_plan(plan, snapshot, packs):
    _require(type(plan) is CapturedPilotPlan, "unsupported pilot plan")
    manifest_json, digest = plan.manifest_json, plan.sha256
    _require(type(manifest_json) is str, "invalid plan manifest")
    try:
        encoded = manifest_json.encode()
        _require(len(encoded) <= 1024 * 1024, "invalid plan manifest")
        _require(
            type(digest) is str and hashlib.sha256(encoded).hexdigest() == digest,
            "invalid plan hash",
        )
        manifest = json.loads(manifest_json)
        cases = manifest["cases"]
        _require(manifest["profile"] == "CapturedPilotPlan.v1", "invalid plan profile")
        _require(
            manifest["provider"] == snapshot.defaults.provider
            and manifest["model"] == snapshot.defaults.model,
            "plan provider/model",
        )
        _require(manifest["repetitions"] == 1 and manifest["planned_calls"] <= 12, "plan calls")
        _require(
            snapshot.execution.repetitions == 1 and snapshot.defaults.retry_attempts == 1,
            "plan requires one primary attempt",
        )
        _require(
            all(not task.variables for task in snapshot.tests), "plan requires literal prompts"
        )
        _require(
            manifest["limits"]["per_call_timeout_seconds"] == snapshot.defaults.timeout,
            "plan timeout declaration",
        )
        _require(len(cases) == len(snapshot.tests), "plan task count")
        rebuilt_cases = []
        for task, case in zip(snapshot.tests, cases):
            _require(
                case["name"] == task.name and case["prompt"] == task.prompt, "plan task binding"
            )
            rebuilt_cases.append(
                {
                    "name": task.name,
                    "prompt": task.prompt,
                    "expected": case["expected"],
                    "packs": packs[task.name],
                }
            )
        rebuilt = prepare_captured_pilot(
            cases=rebuilt_cases,
            provider=snapshot.defaults.provider,
            model=snapshot.defaults.model,
            backend_config_sha256=manifest["backend_config_sha256"],
            limits=manifest["limits"],
        )
    except (KeyError, TypeError, UnicodeError, ValueError, RecursionError, PilotPlanError) as exc:
        raise CapturedRunError("invalid pilot plan") from exc
    _require(
        rebuilt.manifest_json == manifest_json and rebuilt.sha256 == digest,
        "plan integrity mismatch",
    )


def _prepare(config, adapter, packs_by_task, plan=None):
    """Finish all validation and selected rendering before the first await."""
    _validate_config(config, adapter)
    snapshot = config.model_copy(deep=True)
    _require(
        type(packs_by_task) is dict
        and set(packs_by_task) == {task.name for task in snapshot.tests},
        "exact task coverage",
    )
    packs = deepcopy(packs_by_task)
    if plan is not None:
        _bind_plan(plan, snapshot, packs)
    prepared, known_providers, known_records = [], {}, {}
    active_arms = tuple(arm for arm in (*ARMS, _LEGACY_ARM) if arm in snapshot.treatments)
    for task in snapshot.tests:
        arms = packs[task.name]
        _require(type(arms) is dict and set(arms) == set(active_arms), "exact pack arms")
        _require(arms["CONTROL"] is None, "CONTROL must have no context")
        common_target, task_providers = None, {}
        for arm in active_arms:
            kinds = _ARM_KINDS[arm]
            pack = arms[arm]
            if arm != "CONTROL":
                _require(type(pack) is dict, "non-CONTROL arms require supported packs")
            if arm == "E_PAIRED":
                context = render_paired_context(pack)
                selected = pack["structure"]["evidence"] + pack["memory"]["evidence"]
            else:
                context = render_selected_evidence(pack)
                selected = [] if pack is None else pack["evidence"]
            if pack is not None:
                source_packs = (
                    (("structure", pack["structure"]), ("memory", pack["memory"]))
                    if arm == "E_PAIRED"
                    else ((None, pack),)
                )
                for source_kind, source_pack in source_packs:
                    budget = source_pack["budget"]
                    contract = tuple(budget[key] for key in _BUDGET)
                    _require(
                        type(contract[0]) is int
                        and contract[0] >= 0
                        and contract[1:]
                        == ("estimate", "utf8_quote_bytes_div4_ceil_v0", "evidence_quotes"),
                        "supported common budget contract",
                    )
                    target = (source_pack["repository"], source_pack["revision"], contract)
                    _require(
                        common_target is None or target == common_target, "common target/budget"
                    )
                    common_target = target
                    providers = {}
                    for provider in source_pack["providers"]:
                        _require(
                            type(provider) is dict
                            and set(provider) == {"kind", "instance", "status", "detail"},
                            "provider shape",
                        )
                        kind, instance = provider["kind"], provider["instance"]
                        _require(
                            kind in ("structure", "memory")
                            and kind not in providers
                            and type(instance) is str
                            and bool(instance)
                            and type(provider["detail"]) is str
                            and provider["status"] in ("ok", "empty", "error", "unsupported"),
                            "provider kind/identity",
                        )
                        _require(
                            kind not in task_providers or task_providers[kind] == provider,
                            "shared provider binding",
                        )
                        _require(
                            instance not in known_providers
                            or known_providers[instance] == provider,
                            "provider alias",
                        )
                        providers[kind] = task_providers[kind] = known_providers[instance] = (
                            provider
                        )
                    expected_kinds = {source_kind} if arm == "E_PAIRED" else set(kinds)
                    _require(set(providers) == expected_kinds, "arm provider kinds")
                    source_selected = source_pack["evidence"]
                    for record in source_selected:
                        _require(record["kind"] in providers, "selected evidence kind")
                        provider = providers[record["kind"]]
                        _require(
                            record["producer_instance"] == provider["instance"]
                            and provider["status"] == "ok",
                            "selected provider binding",
                        )
                        _require(
                            record["id"] not in known_records
                            or known_records[record["id"]] == record,
                            "contradictory selected identity",
                        )
                        known_records[record["id"]] = record
            prepared.append(
                _Prepared(
                    task.name,
                    task.prompt,
                    tuple(task.variables.items()),
                    arm,
                    context,
                    tuple(record["id"] for record in selected),
                )
            )
    return snapshot, tuple(prepared)


async def run_captured_arms(
    config: EvalConfig,
    adapter: CompletionAdapter,
    packs_by_task: dict,
    *,
    plan: CapturedPilotPlan | None = None,
) -> list[CapturedRunRow]:
    """Return raw rows; full schema/integrity/applicability validation is caller-owned."""
    try:
        snapshot, prepared = _prepare(config, adapter, packs_by_task, plan)
    except (ContextRenderError, KeyError, TypeError, AttributeError) as exc:
        raise CapturedRunError("invalid captured batch") from exc
    rows = []
    for repetition in range(snapshot.execution.repetitions):
        for cell in prepared:
            boundary = _ContextAdapter(
                adapter, snapshot.defaults.model_copy(deep=True), cell.context
            )
            engine = ExecutionEngine(snapshot, boundary)
            task = Task(name=cell.task, prompt=cell.prompt, variables=dict(cell.variables))
            result = await engine.run_single(Treatment(), task, cell.arm)
            rows.append(
                CapturedRunRow(
                    arm=cell.arm,
                    task=cell.task,
                    repetition=repetition,
                    prompt=result.prompt,
                    rendered_context_sha256=None
                    if cell.context is None
                    else hashlib.sha256(cell.context.encode()).hexdigest(),
                    selected_ids=cell.selected_ids,
                    status="completed" if result.passed else "llm_error",
                    response=result.response,
                    timestamp=result.timestamp,
                )
            )
    return rows


async def run_captured_arms_offline(
    config: EvalConfig,
    packs_by_task: dict,
    worker: Callable[[OfflineWorkerInput], dict[str, Any]],
    *,
    plan: CapturedPilotPlan | None = None,
) -> list[CapturedRunRow]:
    """Run frozen captured cells through an injected offline worker callable."""
    return await run_captured_arms(
        config,
        OfflineWorkerAdapter(config.defaults, worker),
        packs_by_task,
        plan=plan,
    )
