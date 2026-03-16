"""Tests for Phase 3: Derived metrics computation (T-07 to T-10).

Covers:
- T-07: compute_cost_metrics() — cost from token_usage + cost_map
- T-08: compute_context_metrics() — context utilization, overflow, truncation_risk
- T-09: compute_comparison_deltas() — deltas between variants, div-by-zero protection
- T-10: build_stage_breakdown() — aggregation by stage_type
"""

import pytest

from md_evals.metrics import (
    AttributionQuality,
    ComparisonDelta,
    ContextMetrics,
    CostMetrics,
    MetricSource,
    StageBreakdownResult,
    StageMetrics,
    TokenUsage,
    TruncationRisk,
    VariantMetrics,
    build_stage_breakdown,
    compute_comparison_deltas,
    compute_context_metrics,
    compute_cost_metrics,
    _compute_single_delta,
)


# ============================================================================
# T-07: compute_cost_metrics()
# ============================================================================


class TestComputeCostMetrics:
    """Test cost metrics calculation from token usage and cost map."""

    def test_full_data_with_rates(self):
        """REQ-02-S1: complete data → correct cost calculation.

        prompt=5000, completion=1500, rates=2.50/10.00
        cost = (5000 * 2.50 + 1500 * 10.00) / 1_000_000 = 0.0275
        """
        usage = TokenUsage(prompt_tokens=5000, completion_tokens=1500, total_tokens=6500)
        cost_map = {
            "gpt-4o": {
                "input_rate_per_million": 2.50,
                "output_rate_per_million": 10.00,
            }
        }

        result = compute_cost_metrics(usage, cost_map, "gpt-4o")

        assert result.prompt_tokens == 5000
        assert result.completion_tokens == 1500
        assert result.total_tokens == 6500
        assert result.estimated_cost_usd == pytest.approx(0.0275)
        assert result.data_quality == MetricSource.MEASURED

    def test_req03_s1_cost_with_different_rates(self):
        """REQ-03-S1: prompt=10000, completion=2000, rates=2.50/10.00 → cost=0.045."""
        usage = TokenUsage(prompt_tokens=10000, completion_tokens=2000)
        cost_map = {
            "gpt-4o": {
                "input_rate_per_million": 2.50,
                "output_rate_per_million": 10.00,
            }
        }

        result = compute_cost_metrics(usage, cost_map, "gpt-4o")

        assert result.estimated_cost_usd == pytest.approx(0.045)

    def test_req03_s2_no_rate_for_model(self):
        """REQ-03-S2: model not in cost_map → estimated_cost_usd = None."""
        usage = TokenUsage(prompt_tokens=5000, completion_tokens=1500)
        cost_map = {
            "gpt-4o": {
                "input_rate_per_million": 2.50,
                "output_rate_per_million": 10.00,
            }
        }

        result = compute_cost_metrics(usage, cost_map, "llama-3.1-70b")

        assert result.estimated_cost_usd is None
        # Tokens are still present
        assert result.prompt_tokens == 5000
        assert result.completion_tokens == 1500
        assert result.total_tokens == 6500
        assert result.data_quality == MetricSource.MEASURED

    def test_req03_s3_empty_cost_map(self):
        """REQ-03-S3: cost_map absent → estimated_cost_usd = None for all."""
        usage = TokenUsage(prompt_tokens=5000, completion_tokens=1500)

        result = compute_cost_metrics(usage, {}, "gpt-4o")

        assert result.estimated_cost_usd is None
        assert result.prompt_tokens == 5000

    def test_no_token_data(self):
        """No token data → all zeros, quality = unavailable."""
        usage = TokenUsage()

        result = compute_cost_metrics(usage, {}, "gpt-4o")

        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0
        assert result.estimated_cost_usd is None
        assert result.data_quality == MetricSource.UNAVAILABLE

    def test_only_completion_tokens(self):
        """Only completion_tokens available → quality = estimated."""
        usage = TokenUsage(completion_tokens=500)

        result = compute_cost_metrics(usage, {}, "gpt-4o")

        assert result.prompt_tokens == 0
        assert result.completion_tokens == 500
        assert result.total_tokens == 500
        assert result.data_quality == MetricSource.ESTIMATED

    def test_negative_tokens_clamped_to_zero(self):
        """Negative token values → clamped to 0 (EC-03)."""
        usage = TokenUsage(prompt_tokens=-100, completion_tokens=-50)

        result = compute_cost_metrics(usage, {}, "gpt-4o")

        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0

    def test_zero_rates_produce_zero_cost(self):
        """Rates of 0.0 → cost = 0.0 (not None)."""
        usage = TokenUsage(prompt_tokens=5000, completion_tokens=1500)
        cost_map = {
            "gpt-4o": {
                "input_rate_per_million": 0.0,
                "output_rate_per_million": 0.0,
            }
        }

        result = compute_cost_metrics(usage, cost_map, "gpt-4o")

        assert result.estimated_cost_usd == 0.0

    def test_latency_defaults_to_zero(self):
        """Latency is not set by compute_cost_metrics — caller sets it."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        result = compute_cost_metrics(usage, {}, "gpt-4o")

        assert result.latency_ms == 0

    def test_partial_rate_keys(self):
        """Rate dict missing one key → uses default 0 for that rate."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        cost_map = {
            "gpt-4o": {
                "input_rate_per_million": 5.0,
                # output_rate_per_million missing → defaults to 0
            }
        }

        result = compute_cost_metrics(usage, cost_map, "gpt-4o")

        # cost = (1000 * 5.0 + 500 * 0.0) / 1_000_000 = 0.005
        assert result.estimated_cost_usd == pytest.approx(0.005)


# ============================================================================
# T-08: compute_context_metrics()
# ============================================================================


class TestComputeContextMetrics:
    """Test context metrics calculation with utilization, headroom, overflow, truncation risk."""

    def test_req02_s1_full_data(self):
        """REQ-02-S1: complete data → all derived metrics correct.

        prompt=5000, window=128000, max_tokens=2048
        utilization = (5000/128000)*100 = 3.90625
        headroom = 128000 - 5000 = 123000
        safe_headroom = 128000 - 5000 - 2048 = 120952
        """
        usage = TokenUsage(prompt_tokens=5000, completion_tokens=1500)

        result = compute_context_metrics(usage, context_window_max=128000, max_tokens_request=2048)

        assert result.prompt_tokens_used == 5000
        assert result.context_window_max_tokens == 128000
        assert result.context_utilization_pct == pytest.approx(3.90625)
        assert result.headroom_tokens == 123000
        assert result.safe_headroom_tokens == 120952
        assert result.max_tokens_request == 2048
        assert result.overflow is False
        assert result.overflow_tokens == 0
        assert result.truncation_risk == TruncationRisk.LOW
        assert result.data_quality == MetricSource.MEASURED

    def test_req02_s2_window_null(self):
        """REQ-02-S2: context_window = None → all derived are null/default."""
        usage = TokenUsage(prompt_tokens=5000)

        result = compute_context_metrics(usage, context_window_max=None, max_tokens_request=2048)

        assert result.prompt_tokens_used == 5000
        assert result.context_window_max_tokens is None
        assert result.context_utilization_pct is None
        assert result.headroom_tokens is None
        assert result.safe_headroom_tokens is None
        assert result.overflow is False
        assert result.overflow_tokens == 0
        assert result.truncation_risk == TruncationRisk.UNKNOWN

    def test_req02_s3_window_zero_ec01(self):
        """REQ-02-S3 / EC-01: context_window = 0 → division by zero guard.

        utilization = None, overflow = true if prompt > 0, overflow_tokens = prompt.
        """
        usage = TokenUsage(prompt_tokens=5000)

        result = compute_context_metrics(usage, context_window_max=0, max_tokens_request=2048)

        assert result.context_utilization_pct is None
        assert result.headroom_tokens == 0
        assert result.safe_headroom_tokens == 0
        assert result.overflow is True
        assert result.overflow_tokens == 5000
        assert result.truncation_risk == TruncationRisk.UNKNOWN

    def test_window_zero_no_prompt(self):
        """context_window = 0, prompt = 0 → overflow = false."""
        usage = TokenUsage(prompt_tokens=0)

        result = compute_context_metrics(usage, context_window_max=0, max_tokens_request=0)

        assert result.overflow is False
        assert result.overflow_tokens == 0

    def test_req08_s1_overflow_detected(self):
        """REQ-08-S1: prompt > window → overflow = true.

        prompt=140000, window=128000 → overflow_tokens=12000, headroom=0.
        """
        usage = TokenUsage(prompt_tokens=140000)

        result = compute_context_metrics(usage, context_window_max=128000, max_tokens_request=2048)

        assert result.overflow is True
        assert result.overflow_tokens == 12000
        assert result.headroom_tokens == 0
        # utilization = 140000/128000*100 = 109.375 → high
        assert result.truncation_risk == TruncationRisk.HIGH

    def test_req08_s2_no_overflow(self):
        """REQ-08-S2: prompt < window → no overflow."""
        usage = TokenUsage(prompt_tokens=5000)

        result = compute_context_metrics(usage, context_window_max=128000, max_tokens_request=2048)

        assert result.overflow is False
        assert result.overflow_tokens == 0
        assert result.headroom_tokens == 123000

    def test_req08_s3_window_unknown(self):
        """REQ-08-S3: window = None → overflow = false, overflow_tokens = 0."""
        usage = TokenUsage(prompt_tokens=5000)

        result = compute_context_metrics(usage, context_window_max=None, max_tokens_request=2048)

        assert result.overflow is False
        assert result.overflow_tokens == 0
        assert result.truncation_risk == TruncationRisk.UNKNOWN

    # ── Truncation risk thresholds ──

    def test_truncation_risk_low(self):
        """utilization < 75% → low."""
        # 74.99% utilization: 7499 / 10000 * 100 = 74.99
        usage = TokenUsage(prompt_tokens=7499)

        result = compute_context_metrics(usage, context_window_max=10000, max_tokens_request=0)

        assert result.truncation_risk == TruncationRisk.LOW

    def test_truncation_risk_medium_at_boundary(self):
        """utilization = 75% → medium (>= 0.75 threshold)."""
        usage = TokenUsage(prompt_tokens=7500)

        result = compute_context_metrics(usage, context_window_max=10000, max_tokens_request=0)

        assert result.context_utilization_pct == pytest.approx(75.0)
        assert result.truncation_risk == TruncationRisk.MEDIUM

    def test_truncation_risk_medium(self):
        """75% <= utilization < 90% → medium."""
        # 89.99%: 8999 / 10000 * 100 = 89.99
        usage = TokenUsage(prompt_tokens=8999)

        result = compute_context_metrics(usage, context_window_max=10000, max_tokens_request=0)

        assert result.truncation_risk == TruncationRisk.MEDIUM

    def test_truncation_risk_high_at_boundary(self):
        """utilization = 90% → high (>= 0.90 threshold)."""
        usage = TokenUsage(prompt_tokens=9000)

        result = compute_context_metrics(usage, context_window_max=10000, max_tokens_request=0)

        assert result.context_utilization_pct == pytest.approx(90.0)
        assert result.truncation_risk == TruncationRisk.HIGH

    def test_truncation_risk_high(self):
        """utilization >= 90% → high."""
        usage = TokenUsage(prompt_tokens=9500)

        result = compute_context_metrics(usage, context_window_max=10000, max_tokens_request=0)

        assert result.truncation_risk == TruncationRisk.HIGH

    def test_truncation_risk_unknown_no_window(self):
        """No window → unknown."""
        usage = TokenUsage(prompt_tokens=5000)

        result = compute_context_metrics(usage, context_window_max=None, max_tokens_request=0)

        assert result.truncation_risk == TruncationRisk.UNKNOWN

    def test_ec03_negative_prompt_clamped(self):
        """EC-03: Negative prompt_tokens → clamped to 0."""
        usage = TokenUsage(prompt_tokens=-100)

        result = compute_context_metrics(usage, context_window_max=128000, max_tokens_request=2048)

        assert result.prompt_tokens_used == 0
        assert result.overflow is False
        assert result.overflow_tokens == 0

    def test_ec07_context_window_unknown(self):
        """EC-07: context window unknown → all derived null/default."""
        usage = TokenUsage(prompt_tokens=5000)

        result = compute_context_metrics(usage, context_window_max=None, max_tokens_request=2048)

        assert result.context_window_max_tokens is None
        assert result.context_utilization_pct is None
        assert result.headroom_tokens is None
        assert result.safe_headroom_tokens is None
        assert result.overflow is False
        assert result.overflow_tokens == 0
        assert result.truncation_risk == TruncationRisk.UNKNOWN

    def test_no_prompt_tokens_data(self):
        """No prompt data → prompt_used=0, quality=unavailable."""
        usage = TokenUsage()

        result = compute_context_metrics(usage, context_window_max=128000, max_tokens_request=2048)

        assert result.prompt_tokens_used == 0
        assert result.data_quality == MetricSource.UNAVAILABLE
        assert result.context_utilization_pct == pytest.approx(0.0)
        assert result.headroom_tokens == 128000
        assert result.overflow is False

    def test_safe_headroom_clamps_to_zero(self):
        """safe_headroom = max(window - prompt - max_tokens, 0) → clamps negative."""
        # window=10000, prompt=9000, max_tokens=2000 → raw = -1000 → clamped to 0
        usage = TokenUsage(prompt_tokens=9000)

        result = compute_context_metrics(usage, context_window_max=10000, max_tokens_request=2000)

        assert result.safe_headroom_tokens == 0

    def test_headroom_clamps_to_zero(self):
        """headroom = max(window - prompt, 0) → clamps negative on overflow."""
        usage = TokenUsage(prompt_tokens=130000)

        result = compute_context_metrics(usage, context_window_max=128000, max_tokens_request=0)

        assert result.headroom_tokens == 0
        assert result.overflow is True
        assert result.overflow_tokens == 2000


# ============================================================================
# T-09: compute_comparison_deltas() and _compute_single_delta()
# ============================================================================


class TestComputeSingleDelta:
    """Test _compute_single_delta() low-level delta calculation."""

    def test_normal_delta(self):
        """Both values present → delta_abs and delta_pct computed."""
        delta = _compute_single_delta(8500, 5000)

        assert delta.orchestrator == 8500
        assert delta.non_orchestrator == 5000
        assert delta.delta_abs == 3500
        assert delta.delta_pct == pytest.approx(70.0)
        assert delta.delta_pct_reason is None

    def test_req06_s3_baseline_zero(self):
        """REQ-06-S3 / EC-02: baseline = 0 → delta_pct = None, reason = baseline_zero."""
        delta = _compute_single_delta(5000, 0)

        assert delta.orchestrator == 5000
        assert delta.non_orchestrator == 0
        assert delta.delta_abs == 5000
        assert delta.delta_pct is None
        assert delta.delta_pct_reason == "baseline_zero"

    def test_ec05_variant_not_executed_orq_none(self):
        """EC-05: orchestrator value None → reason = variant_not_executed."""
        delta = _compute_single_delta(None, 5000)

        assert delta.orchestrator is None
        assert delta.non_orchestrator == 5000
        assert delta.delta_abs is None
        assert delta.delta_pct is None
        assert delta.delta_pct_reason == "variant_not_executed"

    def test_ec05_variant_not_executed_non_orq_none(self):
        """EC-05: non_orchestrator value None → reason = variant_not_executed."""
        delta = _compute_single_delta(5000, None)

        assert delta.delta_abs is None
        assert delta.delta_pct is None
        assert delta.delta_pct_reason == "variant_not_executed"

    def test_both_none(self):
        """Both values None → all delta None, reason = variant_not_executed."""
        delta = _compute_single_delta(None, None)

        assert delta.delta_abs is None
        assert delta.delta_pct is None
        assert delta.delta_pct_reason == "variant_not_executed"

    def test_ec10_boolean_metric(self):
        """EC-10: Boolean metric → delta_abs/pct = None, reason = boolean_metric."""
        delta = _compute_single_delta(True, False, is_boolean=True)

        assert delta.orchestrator is True
        assert delta.non_orchestrator is False
        assert delta.delta_abs is None
        assert delta.delta_pct is None
        assert delta.delta_pct_reason == "boolean_metric"

    def test_negative_delta(self):
        """Orchestrator < baseline → negative delta."""
        delta = _compute_single_delta(3000, 5000)

        assert delta.delta_abs == -2000
        assert delta.delta_pct == pytest.approx(-40.0)

    def test_equal_values(self):
        """Both values equal → delta = 0."""
        delta = _compute_single_delta(5000, 5000)

        assert delta.delta_abs == 0
        assert delta.delta_pct == pytest.approx(0.0)

    def test_float_values(self):
        """Float values → delta computed correctly with rounding."""
        delta = _compute_single_delta(0.165, 0.1225)

        assert delta.delta_abs == pytest.approx(0.0425)
        assert delta.delta_pct == pytest.approx(34.69, rel=0.01)

    def test_both_zero(self):
        """Both values 0 → delta_abs = 0, delta_pct = None (baseline_zero)."""
        delta = _compute_single_delta(0, 0)

        assert delta.delta_abs == 0
        assert delta.delta_pct is None
        assert delta.delta_pct_reason == "baseline_zero"


class TestComputeComparisonDeltas:
    """Test compute_comparison_deltas() full variant comparison."""

    def _make_variant(
        self,
        mode: str,
        prompt: int = 0,
        completion: int = 0,
        cost: float | None = None,
        latency: int = 0,
        ctx_prompt: int = 0,
        ctx_util: float | None = None,
        headroom: int | None = None,
        safe_headroom: int | None = None,
        overflow: bool = False,
        overflow_tokens: int = 0,
    ) -> VariantMetrics:
        """Helper to create a VariantMetrics for testing."""
        return VariantMetrics(
            pipeline_mode=mode,
            cost_metrics=CostMetrics(
                prompt_tokens=prompt,
                completion_tokens=completion,
                total_tokens=prompt + completion,
                estimated_cost_usd=cost,
                latency_ms=latency,
            ),
            context_metrics=ContextMetrics(
                prompt_tokens_used=ctx_prompt,
                context_utilization_pct=ctx_util,
                headroom_tokens=headroom,
                safe_headroom_tokens=safe_headroom,
                overflow=overflow,
                overflow_tokens=overflow_tokens,
            ),
        )

    def test_req06_s1_full_comparison(self):
        """REQ-06-S1: Both variants present → deltas computed for all metrics."""
        orq = self._make_variant(
            "orchestrator",
            prompt=32000,
            completion=8500,
            cost=0.165,
            latency=15200,
            ctx_prompt=32000,
            ctx_util=25.0,
            headroom=96000,
            safe_headroom=93952,
            overflow=False,
            overflow_tokens=0,
        )
        non_orq = self._make_variant(
            "non_orchestrator",
            prompt=25000,
            completion=6000,
            cost=0.1225,
            latency=11500,
            ctx_prompt=25000,
            ctx_util=19.53,
            headroom=103000,
            safe_headroom=100952,
            overflow=False,
            overflow_tokens=0,
        )

        deltas = compute_comparison_deltas(orq, non_orq)

        # Should have 11 deltas total: 5 cost + 6 context
        assert len(deltas) == 11

        # Cost: total_tokens delta (index 2)
        total_tokens_delta = deltas[2]
        assert total_tokens_delta.orchestrator == 40500
        assert total_tokens_delta.non_orchestrator == 31000
        assert total_tokens_delta.delta_abs == 9500
        assert total_tokens_delta.delta_pct == pytest.approx(30.65, rel=0.01)

        # Context: overflow (boolean) at index 9
        overflow_delta = deltas[9]
        assert overflow_delta.delta_pct_reason == "boolean_metric"

    def test_req06_s2_variant_missing(self):
        """REQ-06-S2: variant has None cost → reason = variant_not_executed."""
        orq = self._make_variant("orchestrator")
        orq.cost_metrics.estimated_cost_usd = None

        non_orq = self._make_variant("non_orchestrator")
        non_orq.cost_metrics.estimated_cost_usd = None

        deltas = compute_comparison_deltas(orq, non_orq)

        # estimated_cost_usd is at index 3
        cost_delta = deltas[3]
        assert cost_delta.delta_pct_reason == "variant_not_executed"

    def test_returns_correct_number_of_deltas(self):
        """Always returns 11 deltas: 5 cost + 6 context."""
        orq = self._make_variant("orchestrator")
        non_orq = self._make_variant("non_orchestrator")

        deltas = compute_comparison_deltas(orq, non_orq)

        assert len(deltas) == 11

    def test_overflow_always_boolean(self):
        """Overflow delta always has boolean_metric reason."""
        orq = self._make_variant("orchestrator", overflow=True, overflow_tokens=5000)
        non_orq = self._make_variant("non_orchestrator", overflow=False, overflow_tokens=0)

        deltas = compute_comparison_deltas(orq, non_orq)

        # overflow is at index 9
        assert deltas[9].orchestrator is True
        assert deltas[9].non_orchestrator is False
        assert deltas[9].delta_pct_reason == "boolean_metric"


# ============================================================================
# T-10: build_stage_breakdown()
# ============================================================================


class TestBuildStageBreakdown:
    """Test stage breakdown aggregation by stage_type."""

    def test_single_pass_one_stage(self):
        """V1 (non-orchestrator): single stage → one entry in result."""
        stages = [
            StageMetrics(
                stage_type="single_pass",
                prompt_tokens=5000,
                completion_tokens=1500,
                total_tokens=6500,
                latency_ms=2000,
            ),
        ]

        result = build_stage_breakdown(stages)

        assert len(result.stages) == 1
        assert result.stages[0].stage_type == "single_pass"
        assert result.stages[0].prompt_tokens == 5000
        assert result.stages[0].completion_tokens == 1500
        assert result.stages[0].total_tokens == 6500
        assert result.total_tokens == 6500
        assert result.total_latency_ms == 2000

    def test_multi_stage_orchestrator(self):
        """REQ-05-S1: Multiple stages → entries grouped by stage_type."""
        stages = [
            StageMetrics(
                stage_type="planner",
                prompt_tokens=2000,
                completion_tokens=500,
                total_tokens=2500,
                latency_ms=450,
            ),
            StageMetrics(
                stage_type="tool_call",
                prompt_tokens=1500,
                completion_tokens=800,
                total_tokens=2300,
                tool_io_tokens=340,
                latency_ms=600,
            ),
            StageMetrics(
                stage_type="synthesis",
                prompt_tokens=3000,
                completion_tokens=1200,
                total_tokens=4200,
                latency_ms=900,
            ),
        ]

        result = build_stage_breakdown(stages)

        assert len(result.stages) == 3
        assert result.total_tokens == 9000
        assert result.total_prompt_tokens == 6500
        assert result.total_completion_tokens == 2500
        assert result.total_latency_ms == 1950

        # Find tool_call stage
        tool_stage = next(s for s in result.stages if s.stage_type == "tool_call")
        assert tool_stage.tool_io_tokens == 340

    def test_same_stage_type_aggregated(self):
        """Multiple entries with same stage_type → aggregated into one."""
        stages = [
            StageMetrics(
                stage_type="tool_call",
                prompt_tokens=1000,
                completion_tokens=500,
                total_tokens=1500,
                tool_io_tokens=100,
                latency_ms=300,
            ),
            StageMetrics(
                stage_type="tool_call",
                prompt_tokens=2000,
                completion_tokens=800,
                total_tokens=2800,
                tool_io_tokens=200,
                latency_ms=400,
            ),
        ]

        result = build_stage_breakdown(stages)

        assert len(result.stages) == 1
        agg = result.stages[0]
        assert agg.stage_type == "tool_call"
        assert agg.prompt_tokens == 3000
        assert agg.completion_tokens == 1300
        assert agg.total_tokens == 4300
        assert agg.tool_io_tokens == 300
        assert agg.latency_ms == 700

    def test_empty_list(self):
        """Empty input → empty result with zero totals."""
        result = build_stage_breakdown([])

        assert len(result.stages) == 0
        assert result.total_tokens == 0
        assert result.total_latency_ms == 0

    def test_attribution_quality_preserved_high(self):
        """All high quality stages → aggregate stays high."""
        stages = [
            StageMetrics(
                stage_type="single_pass",
                prompt_tokens=1000,
                completion_tokens=500,
                total_tokens=1500,
                attribution_quality=AttributionQuality.HIGH,
            ),
        ]

        result = build_stage_breakdown(stages)

        assert result.stages[0].attribution_quality == AttributionQuality.HIGH

    def test_attribution_quality_downgraded(self):
        """REQ-05-S3: Partial telemetry → attribution downgraded to lowest."""
        stages = [
            StageMetrics(
                stage_type="tool_call",
                prompt_tokens=1000,
                completion_tokens=500,
                total_tokens=1500,
                attribution_quality=AttributionQuality.HIGH,
            ),
            StageMetrics(
                stage_type="tool_call",
                prompt_tokens=500,
                completion_tokens=200,
                total_tokens=700,
                attribution_quality=AttributionQuality.LOW,
            ),
        ]

        result = build_stage_breakdown(stages)

        assert len(result.stages) == 1
        assert result.stages[0].attribution_quality == AttributionQuality.LOW

    def test_attribution_quality_medium(self):
        """HIGH + MEDIUM → result is MEDIUM."""
        stages = [
            StageMetrics(
                stage_type="synthesis",
                prompt_tokens=1000,
                completion_tokens=500,
                total_tokens=1500,
                attribution_quality=AttributionQuality.HIGH,
            ),
            StageMetrics(
                stage_type="synthesis",
                prompt_tokens=500,
                completion_tokens=200,
                total_tokens=700,
                attribution_quality=AttributionQuality.MEDIUM,
            ),
        ]

        result = build_stage_breakdown(stages)

        assert result.stages[0].attribution_quality == AttributionQuality.MEDIUM

    def test_totals_match_sum_of_stages(self):
        """AC-11: Sum of stage totals = breakdown totals."""
        stages = [
            StageMetrics(
                stage_type="planner",
                prompt_tokens=2000,
                completion_tokens=500,
                total_tokens=2500,
                latency_ms=400,
            ),
            StageMetrics(
                stage_type="router",
                prompt_tokens=1000,
                completion_tokens=200,
                total_tokens=1200,
                latency_ms=200,
            ),
            StageMetrics(
                stage_type="synthesis",
                prompt_tokens=3000,
                completion_tokens=1000,
                total_tokens=4000,
                latency_ms=600,
            ),
        ]

        result = build_stage_breakdown(stages)

        stage_prompt_sum = sum(s.prompt_tokens for s in result.stages)
        stage_completion_sum = sum(s.completion_tokens for s in result.stages)
        stage_total_sum = sum(s.total_tokens for s in result.stages)
        stage_latency_sum = sum(s.latency_ms for s in result.stages)

        assert result.total_prompt_tokens == stage_prompt_sum
        assert result.total_completion_tokens == stage_completion_sum
        assert result.total_tokens == stage_total_sum
        assert result.total_latency_ms == stage_latency_sum

    def test_mixed_stage_types_ordering(self):
        """Mixed stage types all appear in result."""
        stages = [
            StageMetrics(stage_type="planner", prompt_tokens=100, completion_tokens=50, total_tokens=150),
            StageMetrics(stage_type="router", prompt_tokens=200, completion_tokens=100, total_tokens=300),
            StageMetrics(stage_type="tool_call", prompt_tokens=300, completion_tokens=150, total_tokens=450),
            StageMetrics(stage_type="synthesis", prompt_tokens=400, completion_tokens=200, total_tokens=600),
        ]

        result = build_stage_breakdown(stages)

        assert len(result.stages) == 4
        stage_types = {s.stage_type for s in result.stages}
        assert stage_types == {"planner", "router", "tool_call", "synthesis"}


# ============================================================================
# Dataclass sanity checks (ensure types are correct for serialization)
# ============================================================================


class TestDataclassSerialization:
    """Verify dataclass instances can be serialized via asdict."""

    def test_cost_metrics_asdict(self):
        """CostMetrics → dict via dataclasses.asdict."""
        from dataclasses import asdict

        cm = CostMetrics(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.005,
            data_quality=MetricSource.MEASURED,
        )
        d = asdict(cm)

        assert d["prompt_tokens"] == 100
        assert d["estimated_cost_usd"] == 0.005
        assert d["data_quality"] == "measured"

    def test_context_metrics_asdict(self):
        """ContextMetrics → dict via dataclasses.asdict."""
        from dataclasses import asdict

        ctx = ContextMetrics(
            prompt_tokens_used=5000,
            truncation_risk=TruncationRisk.LOW,
        )
        d = asdict(ctx)

        assert d["prompt_tokens_used"] == 5000
        assert d["truncation_risk"] == "low"

    def test_comparison_delta_asdict(self):
        """ComparisonDelta → dict via dataclasses.asdict."""
        from dataclasses import asdict

        delta = ComparisonDelta(
            orchestrator=8500,
            non_orchestrator=5000,
            delta_abs=3500,
            delta_pct=70.0,
        )
        d = asdict(delta)

        assert d["orchestrator"] == 8500
        assert d["delta_pct"] == 70.0
        assert d["delta_pct_reason"] is None

    def test_stage_breakdown_result_asdict(self):
        """StageBreakdownResult → dict."""
        from dataclasses import asdict

        result = StageBreakdownResult(
            stages=[
                StageMetrics(
                    stage_type="single_pass",
                    prompt_tokens=100,
                    completion_tokens=50,
                    total_tokens=150,
                )
            ],
            total_tokens=150,
        )
        d = asdict(result)

        assert d["total_tokens"] == 150
        assert len(d["stages"]) == 1
        assert d["stages"][0]["stage_type"] == "single_pass"
