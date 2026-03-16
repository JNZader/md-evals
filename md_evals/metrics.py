"""Usage metrics dataclasses for cost and context tracking.

Defines two separate metric domains:
- cost_metrics: token consumption and USD cost estimation
- context_metrics: context window utilization and truncation risk

All dataclasses use stdlib @dataclass (not Pydantic) per ADR-03,
since these are internal computation objects, not API models.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


# ─── Enums ───


class MetricSource(str, Enum):
    """Data quality indicator for metric values.

    Indicates how the metric data was obtained:
    - MEASURED: directly from provider telemetry (response.usage)
    - ESTIMATED: derived via heuristic or fallback
    - UNAVAILABLE: no data available
    """

    MEASURED = "measured"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class TruncationRisk(str, Enum):
    """Risk level for context window truncation.

    Thresholds (hardcoded, not configurable in V1):
    - LOW: utilization < 75%
    - MEDIUM: 75% <= utilization < 90%
    - HIGH: utilization >= 90%
    - UNKNOWN: context window size is unknown
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class AttributionQuality(str, Enum):
    """Quality of token attribution for a stage.

    - HIGH: measured directly from provider telemetry
    - MEDIUM: estimated with reasonable heuristic
    - LOW: fallback without telemetry
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StageType(str, Enum):
    """Semantic label for an LLM call stage.

    - SINGLE_PASS: standard non-orchestrator single call
    - PLANNER: orchestrator planning stage
    - ROUTER: orchestrator routing stage
    - TOOL_CALL: orchestrator tool invocation stage
    - SYNTHESIS: orchestrator final synthesis stage
    """

    SINGLE_PASS = "single_pass"
    PLANNER = "planner"
    ROUTER = "router"
    TOOL_CALL = "tool_call"
    SYNTHESIS = "synthesis"


# ─── Token Capture (raw from provider) ───


@dataclass(frozen=True)
class TokenUsage:
    """Raw token usage from a single LLM call.

    Captured at the adapter level (LLMAdapter.complete()) and stored
    in LLMResponse for downstream aggregation.
    """

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    source: MetricSource = MetricSource.UNAVAILABLE


# ─── Cost Domain ───


@dataclass
class CostMetrics:
    """Cost-oriented metrics for a variant (accumulated across all calls).

    Fields correspond to spec §3.1 cost_metrics table.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    latency_ms: int = 0
    data_quality: MetricSource = MetricSource.UNAVAILABLE


# ─── Context Domain ───


@dataclass
class ContextMetrics:
    """Context window risk metrics for a variant.

    Fields correspond to spec §3.2 context_metrics table.
    Derived values are null when context_window_max_tokens is unknown.
    """

    prompt_tokens_used: int = 0
    context_window_max_tokens: int | None = None
    context_utilization_pct: float | None = None
    headroom_tokens: int | None = None
    safe_headroom_tokens: int | None = None
    max_tokens_request: int = 0
    overflow: bool = False
    overflow_tokens: int = 0
    truncation_risk: TruncationRisk = TruncationRisk.UNKNOWN
    data_quality: MetricSource = MetricSource.UNAVAILABLE


# ─── Stage Breakdown ───


@dataclass
class StageMetrics:
    """Metrics for a single LLM call stage.

    In V1 (no orchestrator), every call is a single "single_pass" stage.
    Future orchestrator will produce multiple stages per variant.
    """

    stage_type: str  # "planner", "router", "tool_call", "synthesis", "single_pass"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_io_tokens: int = 0
    latency_ms: int = 0
    attribution_quality: AttributionQuality = AttributionQuality.HIGH


# ─── Per-Variant Aggregation ───


@dataclass
class VariantMetrics:
    """Aggregated metrics for one variant (orchestrator or non_orchestrator)."""

    pipeline_mode: str  # "orchestrator" | "non_orchestrator"
    cost_metrics: CostMetrics = field(default_factory=CostMetrics)
    context_metrics: ContextMetrics = field(default_factory=ContextMetrics)
    stage_breakdown: list[StageMetrics] = field(default_factory=list)


# ─── Comparison Delta ───


@dataclass
class ComparisonDelta:
    """Delta between orchestrator and non_orchestrator for one metric."""

    orchestrator: float | int | bool | None = None
    non_orchestrator: float | int | bool | None = None
    delta_abs: float | int | None = None
    delta_pct: float | None = None
    delta_pct_reason: str | None = None  # "baseline_zero", "boolean_metric", etc.


# ─── Usage Report (top-level container) ───


@dataclass
class UsageReport:
    """Top-level container for all usage metrics in the report output.

    Serialized as the `usage_metrics` block in JSON output.
    """

    model: str
    provider: str
    context_window_max_tokens: int | None = None
    max_tokens_request: int = 0
    variants: dict[str, VariantMetrics] = field(default_factory=dict)
    comparison: dict[str, dict[str, ComparisonDelta]] | None = None


# ─── Cost Rate Config ───


@dataclass(frozen=True)
class CostRate:
    """Cost rate for a model (USD per million tokens)."""

    input_rate_per_million: float
    output_rate_per_million: float


# ─── Context Window Resolution ───


def resolve_context_window(
    model: str,
    provider: str,
    config: object | None = None,
) -> int | None:
    """Resolve context window size with fallback chain.

    Priority:
    1. config.context_window_overrides[model]  (explicit user config)
    2. Provider metadata (e.g., GitHubModelsProvider.SUPPORTED_MODELS)
    3. litellm.get_model_info(model)
    4. None  (unknown — all derived metrics will be null/default)

    This is a pure function with no side effects. Never raises exceptions.

    Args:
        model: Model name (e.g. "gpt-4o")
        provider: Provider name (e.g. "github-models", "openai")
        config: EvalConfig instance (or any object with context_window_overrides)

    Returns:
        Context window size in tokens, or None if unknown.
    """
    # 1. Config override
    if config is not None:
        overrides = getattr(config, "context_window_overrides", None)
        if overrides and model in overrides:
            return overrides[model]

    # 2. Provider metadata via ProviderRegistry
    try:
        from md_evals.provider_registry import ProviderRegistry

        provider_class = ProviderRegistry.get(provider)
        if hasattr(provider_class, "supported_models"):
            models = provider_class.supported_models()
            if model in models:
                ctx = getattr(models[model], "context_window", None)
                if ctx is not None:
                    return ctx
    except (ValueError, AttributeError, ImportError):
        pass

    # 3. LiteLLM model registry
    try:
        import litellm

        info = litellm.get_model_info(model)
        if info and "max_input_tokens" in info:
            return info["max_input_tokens"]
    except Exception:
        pass

    # 4. Unknown
    return None


# ─── T-07: Cost Metrics Computation ───


def compute_cost_metrics(
    token_usage: TokenUsage,
    cost_map: dict[str, dict[str, float]],
    model: str,
) -> CostMetrics:
    """Compute cost metrics from raw token usage and cost rates.

    Pure function — no side effects. Calculates estimated_cost_usd from
    tokens × rate. If no rate exists for the model, cost = None.

    Formula: (prompt_tokens × input_rate + completion_tokens × output_rate) / 1_000_000

    Args:
        token_usage: Raw token counts (prompt, completion, total).
        cost_map: Dict mapping model name to rate dict with keys
                  ``input_rate_per_million`` and ``output_rate_per_million``.
        model: Model name to look up in cost_map.

    Returns:
        CostMetrics with aggregated token counts and optional cost estimate.
    """
    prompt = max(token_usage.prompt_tokens or 0, 0)
    completion = max(token_usage.completion_tokens or 0, 0)
    total = prompt + completion

    # Determine data_quality from source token data
    quality = MetricSource.UNAVAILABLE
    if token_usage.prompt_tokens is not None:
        quality = MetricSource.MEASURED
    elif token_usage.completion_tokens is not None:
        quality = MetricSource.ESTIMATED

    # Cost calculation — None if model not in cost_map
    estimated_cost: float | None = None
    if model in cost_map:
        rates = cost_map[model]
        input_rate = rates.get("input_rate_per_million", 0.0)
        output_rate = rates.get("output_rate_per_million", 0.0)
        estimated_cost = (prompt * input_rate + completion * output_rate) / 1_000_000

    return CostMetrics(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        estimated_cost_usd=estimated_cost,
        latency_ms=0,  # Latency is set by caller if needed
        data_quality=quality,
    )


# ─── T-08: Context Metrics Computation ───


def compute_context_metrics(
    token_usage: TokenUsage,
    context_window_max: int | None,
    max_tokens_request: int,
) -> ContextMetrics:
    """Compute context window risk metrics from token usage.

    Pure function — no side effects. Uses prompt_tokens to evaluate context
    window pressure, overflow risk, and truncation risk.

    Truncation risk thresholds (hardcoded):
    - HIGH:    utilization >= 90%
    - MEDIUM:  utilization >= 75%
    - LOW:     utilization < 75%
    - UNKNOWN: context_window_max is None or data missing

    Args:
        token_usage: Raw token counts from LLM call.
        context_window_max: Maximum context window size in tokens, or None.
        max_tokens_request: The max_tokens parameter used in the request.

    Returns:
        ContextMetrics with utilization, headroom, overflow, and risk data.
    """
    prompt_used = max(token_usage.prompt_tokens or 0, 0)

    # Determine data quality
    quality = MetricSource.UNAVAILABLE
    if token_usage.prompt_tokens is not None:
        quality = MetricSource.MEASURED

    # Derived defaults
    utilization: float | None = None
    headroom: int | None = None
    safe_headroom: int | None = None
    is_overflow = False
    overflow_tok = 0
    risk = TruncationRisk.UNKNOWN

    if context_window_max is not None and context_window_max > 0:
        utilization = (prompt_used / context_window_max) * 100
        headroom = max(context_window_max - prompt_used, 0)
        safe_headroom = max(context_window_max - prompt_used - max_tokens_request, 0)
        is_overflow = prompt_used > context_window_max
        overflow_tok = max(prompt_used - context_window_max, 0)

        # Truncation risk thresholds
        if utilization >= 90.0:
            risk = TruncationRisk.HIGH
        elif utilization >= 75.0:
            risk = TruncationRisk.MEDIUM
        else:
            risk = TruncationRisk.LOW
    elif context_window_max is not None and context_window_max == 0:
        # context_window = 0: division by zero guard
        # utilization stays None, headroom/safe_headroom = 0
        headroom = 0
        safe_headroom = 0
        is_overflow = prompt_used > 0
        overflow_tok = prompt_used
        risk = TruncationRisk.UNKNOWN
    # else: context_window_max is None → all derived stay null/default

    return ContextMetrics(
        prompt_tokens_used=prompt_used,
        context_window_max_tokens=context_window_max,
        context_utilization_pct=utilization,
        headroom_tokens=headroom,
        safe_headroom_tokens=safe_headroom,
        max_tokens_request=max_tokens_request,
        overflow=is_overflow,
        overflow_tokens=overflow_tok,
        truncation_risk=risk,
        data_quality=quality,
    )


# ─── T-09: Comparison Deltas ───


def compute_comparison_deltas(
    variant_a_metrics: VariantMetrics,
    variant_b_metrics: VariantMetrics,
) -> list[ComparisonDelta]:
    """Compute deltas between two variant metrics (a = orchestrator, b = non_orchestrator).

    Pure function — no side effects. Generates one ComparisonDelta per
    comparable metric across both cost and context domains.

    Division-by-zero protection: if non_orchestrator value is 0,
    delta_pct = None with reason ``baseline_zero``.

    Boolean metrics (overflow): delta_abs and delta_pct are None
    with reason ``boolean_metric``.

    Args:
        variant_a_metrics: Orchestrator variant metrics.
        variant_b_metrics: Non-orchestrator (baseline) variant metrics.

    Returns:
        List of ComparisonDelta, one per metric field.
    """
    deltas: list[ComparisonDelta] = []

    # ── Cost domain fields ──
    cost_fields: list[tuple[str, bool]] = [
        ("prompt_tokens", False),
        ("completion_tokens", False),
        ("total_tokens", False),
        ("estimated_cost_usd", False),
        ("latency_ms", False),
    ]

    a_cost = variant_a_metrics.cost_metrics
    b_cost = variant_b_metrics.cost_metrics

    for field_name, is_bool in cost_fields:
        orq_val = getattr(a_cost, field_name, None)
        non_orq_val = getattr(b_cost, field_name, None)
        deltas.append(_compute_single_delta(orq_val, non_orq_val, is_bool))

    # ── Context domain fields ──
    context_fields: list[tuple[str, bool]] = [
        ("prompt_tokens_used", False),
        ("context_utilization_pct", False),
        ("headroom_tokens", False),
        ("safe_headroom_tokens", False),
        ("overflow", True),
        ("overflow_tokens", False),
    ]

    a_ctx = variant_a_metrics.context_metrics
    b_ctx = variant_b_metrics.context_metrics

    for field_name, is_bool in context_fields:
        orq_val = getattr(a_ctx, field_name, None)
        non_orq_val = getattr(b_ctx, field_name, None)
        deltas.append(_compute_single_delta(orq_val, non_orq_val, is_bool))

    return deltas


def _compute_single_delta(
    orq_value: float | int | bool | None,
    non_orq_value: float | int | bool | None,
    is_boolean: bool = False,
) -> ComparisonDelta:
    """Compute a single comparison delta between orchestrator and non-orchestrator values.

    Args:
        orq_value: Orchestrator metric value.
        non_orq_value: Non-orchestrator (baseline) metric value.
        is_boolean: If True, skip numeric delta calculation.

    Returns:
        ComparisonDelta with abs/pct deltas and optional reason codes.
    """
    if is_boolean:
        return ComparisonDelta(
            orchestrator=orq_value,
            non_orchestrator=non_orq_value,
            delta_abs=None,
            delta_pct=None,
            delta_pct_reason="boolean_metric",
        )

    if orq_value is None or non_orq_value is None:
        return ComparisonDelta(
            orchestrator=orq_value,
            non_orchestrator=non_orq_value,
            delta_abs=None,
            delta_pct=None,
            delta_pct_reason="variant_not_executed",
        )

    # Both values are numeric — compute delta
    delta_abs = orq_value - non_orq_value  # type: ignore[operator]

    if non_orq_value == 0:
        return ComparisonDelta(
            orchestrator=orq_value,
            non_orchestrator=non_orq_value,
            delta_abs=delta_abs,
            delta_pct=None,
            delta_pct_reason="baseline_zero",
        )

    delta_pct = round((delta_abs / non_orq_value) * 100, 2)  # type: ignore[operator]

    return ComparisonDelta(
        orchestrator=orq_value,
        non_orchestrator=non_orq_value,
        delta_abs=delta_abs,
        delta_pct=delta_pct,
    )


# ─── T-10: Stage Breakdown ───


@dataclass
class StageBreakdownResult:
    """Result from build_stage_breakdown aggregation."""

    stages: list[StageMetrics]
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_latency_ms: int = 0


def build_stage_breakdown(
    stage_metrics_list: list[StageMetrics],
) -> StageBreakdownResult:
    """Aggregate a list of StageMetrics by stage_type with totals and share_pct.

    Pure function — groups incoming stages by ``stage_type``, sums tokens and
    latency per group, and computes overall totals.

    Args:
        stage_metrics_list: Individual stage metrics from LLM calls.

    Returns:
        StageBreakdownResult with aggregated stages and totals.
    """
    # Group by stage_type
    groups: dict[str, StageMetrics] = {}

    for sm in stage_metrics_list:
        key = sm.stage_type
        if key not in groups:
            # Determine attribution quality: if any field is missing data, downgrade
            groups[key] = StageMetrics(
                stage_type=key,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                tool_io_tokens=0,
                latency_ms=0,
                attribution_quality=sm.attribution_quality,
            )
        agg = groups[key]
        agg.prompt_tokens += sm.prompt_tokens
        agg.completion_tokens += sm.completion_tokens
        agg.total_tokens += sm.total_tokens
        agg.tool_io_tokens += sm.tool_io_tokens
        agg.latency_ms += sm.latency_ms

        # Downgrade attribution quality if any contributing stage is lower
        quality_rank = {
            AttributionQuality.HIGH: 2,
            AttributionQuality.MEDIUM: 1,
            AttributionQuality.LOW: 0,
        }
        if quality_rank.get(sm.attribution_quality, 0) < quality_rank.get(
            agg.attribution_quality, 2
        ):
            agg.attribution_quality = sm.attribution_quality

    aggregated = list(groups.values())

    total_prompt = sum(s.prompt_tokens for s in aggregated)
    total_completion = sum(s.completion_tokens for s in aggregated)
    total_tok = sum(s.total_tokens for s in aggregated)
    total_lat = sum(s.latency_ms for s in aggregated)

    return StageBreakdownResult(
        stages=aggregated,
        total_prompt_tokens=total_prompt,
        total_completion_tokens=total_completion,
        total_tokens=total_tok,
        total_latency_ms=total_lat,
    )


# ─── T-13: Build Usage Metrics (aggregation per treatment) ───


def _aggregate_token_usage_from_results(
    results: list[Any],
) -> tuple[TokenUsage, int]:
    """Aggregate token usage and latency from a list of ExecutionResults.

    Sums prompt_tokens, completion_tokens, total_tokens across all results.
    Also sums latency_ms.

    Args:
        results: List of ExecutionResult objects.

    Returns:
        Tuple of (aggregated TokenUsage, total_latency_ms).
    """
    total_prompt = 0
    total_completion = 0
    total_latency = 0
    has_prompt = False
    has_completion = False

    for r in results:
        resp = r.response
        if resp.prompt_tokens is not None:
            total_prompt += max(resp.prompt_tokens, 0)
            has_prompt = True
        if resp.completion_tokens_detail is not None:
            total_completion += max(resp.completion_tokens_detail, 0)
            has_completion = True
        total_latency += resp.duration_ms

    total = total_prompt + total_completion

    # Determine source quality
    if has_prompt:
        source = MetricSource.MEASURED
    elif has_completion:
        source = MetricSource.ESTIMATED
    else:
        source = MetricSource.UNAVAILABLE

    return TokenUsage(
        prompt_tokens=total_prompt if has_prompt else None,
        completion_tokens=total_completion if has_completion else None,
        total_tokens=total if (has_prompt or has_completion) else None,
        source=source,
    ), total_latency


def _build_stage_metrics_from_results(
    results: list[Any],
) -> list[StageMetrics]:
    """Extract StageMetrics from ExecutionResults for stage breakdown.

    Each ExecutionResult maps to one StageMetrics entry based on
    response.stage_type.

    Args:
        results: List of ExecutionResult objects.

    Returns:
        List of StageMetrics, one per result.
    """
    stages: list[StageMetrics] = []
    for r in results:
        resp = r.response
        prompt = max(resp.prompt_tokens or 0, 0)
        completion = max(resp.completion_tokens_detail or 0, 0)

        # Determine attribution quality
        if resp.prompt_tokens is not None and resp.completion_tokens_detail is not None:
            quality = AttributionQuality.HIGH
        elif resp.completion_tokens_detail is not None:
            quality = AttributionQuality.MEDIUM
        else:
            quality = AttributionQuality.LOW

        stages.append(
            StageMetrics(
                stage_type=resp.stage_type,
                prompt_tokens=prompt,
                completion_tokens=completion,
                total_tokens=prompt + completion,
                tool_io_tokens=0,
                latency_ms=resp.duration_ms,
                attribution_quality=quality,
            )
        )
    return stages


def _build_comparison_dict(
    variants: dict[str, VariantMetrics],
) -> dict[str, dict[str, Any]] | None:
    """Build comparison dict between variants.

    Only generates comparison when there are 2+ variants.
    Compares all cost and context fields with deltas.

    Args:
        variants: Dict of treatment_name -> VariantMetrics.

    Returns:
        Comparison dict or None if < 2 variants.
    """
    names = list(variants.keys())
    if len(names) < 2:
        return None

    # Use first two variants for comparison
    name_a, name_b = names[0], names[1]
    var_a = variants[name_a]
    var_b = variants[name_b]

    cost_comparison: dict[str, Any] = {}
    context_comparison: dict[str, Any] = {}

    # Cost domain fields
    cost_fields = [
        ("prompt_tokens", False),
        ("completion_tokens", False),
        ("total_tokens", False),
        ("estimated_cost_usd", False),
        ("latency_ms", False),
    ]
    for field_name, is_bool in cost_fields:
        val_a = getattr(var_a.cost_metrics, field_name, None)
        val_b = getattr(var_b.cost_metrics, field_name, None)
        delta = _compute_single_delta(val_a, val_b, is_bool)
        d = asdict(delta)
        # Rename keys to use treatment names
        d[name_a] = d.pop("orchestrator")
        d[name_b] = d.pop("non_orchestrator")
        cost_comparison[field_name] = d

    # Context domain fields
    context_fields = [
        ("prompt_tokens_used", False),
        ("context_utilization_pct", False),
        ("headroom_tokens", False),
        ("safe_headroom_tokens", False),
        ("overflow", True),
        ("overflow_tokens", False),
    ]
    for field_name, is_bool in context_fields:
        val_a = getattr(var_a.context_metrics, field_name, None)
        val_b = getattr(var_b.context_metrics, field_name, None)
        delta = _compute_single_delta(val_a, val_b, is_bool)
        d = asdict(delta)
        d[name_a] = d.pop("orchestrator")
        d[name_b] = d.pop("non_orchestrator")
        context_comparison[field_name] = d

    return {
        "cost_metrics": cost_comparison,
        "context_metrics": context_comparison,
    }


def build_usage_metrics(
    results: list[Any],
    config: Any,
) -> dict[str, Any] | None:
    """Build the complete usage_metrics block for the JSON report.

    Groups results by treatment, computes cost and context metrics per
    treatment, builds stage breakdown, and optionally generates comparison.

    Returns None if ``config.output.include_usage_metrics`` is False.

    Pure function except for ``resolve_context_window`` which may query
    external registries (but never raises).

    Args:
        results: List of ExecutionResult objects.
        config: EvalConfig instance.

    Returns:
        Dict matching spec §5 ``usage_metrics`` structure, or None.
    """
    if not getattr(getattr(config, "output", None), "include_usage_metrics", False):
        return None

    model = config.defaults.model
    provider = config.defaults.provider
    context_window = resolve_context_window(model, provider, config)
    max_tokens_req = config.defaults.max_tokens

    # Group results by treatment
    by_treatment: dict[str, list[Any]] = {}
    for r in results:
        if r.treatment not in by_treatment:
            by_treatment[r.treatment] = []
        by_treatment[r.treatment].append(r)

    variants: dict[str, VariantMetrics] = {}
    warnings: list[str] = []

    for treatment_name, treatment_results in by_treatment.items():
        # Aggregate token usage across all results for this treatment
        agg_usage, total_latency = _aggregate_token_usage_from_results(treatment_results)

        # Compute cost metrics
        cost = compute_cost_metrics(agg_usage, config.cost_map, model)
        cost.latency_ms = total_latency

        # Compute context metrics (uses max prompt across calls for worst-case)
        max_prompt = 0
        has_prompt = False
        for r in treatment_results:
            if r.response.prompt_tokens is not None:
                max_prompt = max(max_prompt, max(r.response.prompt_tokens, 0))
                has_prompt = True

        ctx_usage = TokenUsage(
            prompt_tokens=max_prompt if has_prompt else None,
            source=MetricSource.MEASURED if has_prompt else MetricSource.UNAVAILABLE,
        )
        context = compute_context_metrics(ctx_usage, context_window, max_tokens_req)

        # Build stage breakdown
        stage_list = _build_stage_metrics_from_results(treatment_results)
        breakdown = build_stage_breakdown(stage_list)

        # Check for stage sum mismatch (EC-09)
        if breakdown.total_tokens != cost.total_tokens and cost.total_tokens > 0:
            warnings.append("stage_sum_mismatch")

        # Determine pipeline_mode
        has_multi_stage = any(
            r.response.stage_type != "single_pass" for r in treatment_results
        )
        mode = "orchestrator" if has_multi_stage else "non_orchestrator"

        variants[treatment_name] = VariantMetrics(
            pipeline_mode=mode,
            cost_metrics=cost,
            context_metrics=context,
            stage_breakdown=breakdown.stages,
        )

    # Build comparison (if 2+ variants)
    comparison = _build_comparison_dict(variants)

    # Determine quality flags
    has_cost_map = bool(config.cost_map) and model in config.cost_map
    all_measured = all(
        v.cost_metrics.data_quality == MetricSource.MEASURED for v in variants.values()
    )

    # Serialize variants
    serialized_variants: dict[str, Any] = {}
    for name, vm in variants.items():
        serialized_variants[name] = {
            "pipeline_mode": vm.pipeline_mode,
            "cost_metrics": asdict(vm.cost_metrics),
            "context_metrics": asdict(vm.context_metrics),
            "stage_breakdown": [asdict(s) for s in vm.stage_breakdown],
        }

    return {
        "model": model,
        "provider": provider,
        "context_window_max_tokens": context_window,
        "max_tokens_request": max_tokens_req,
        "variants": serialized_variants,
        "comparison": comparison,
        "quality_flags": {
            "attribution_coverage": "full" if not warnings else "partial",
            "provider_telemetry": "complete" if all_measured else "partial",
            "cost_map_available": has_cost_map,
            "warnings": warnings,
        },
    }
