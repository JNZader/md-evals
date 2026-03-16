"""T-17: Integration tests for reporter with usage metrics flag on/off.

Phase 6 — Verifies JSON output includes/excludes usage_metrics sections
based on feature flag. Tests backward compatibility (flag off = no new keys)
and structure correctness (flag on = separated domains).

AC coverage:
- AC-01: JSON with flag on has cost_metrics and context_metrics as separate objects
- AC-02: JSON with flag off is structurally identical to legacy (no new keys)
- AC-11: Sum of stage_breakdown tokens = variant total_tokens (or warning)
- AC-17: Legacy fields (tokens, duration_ms) present regardless of flag
- AC-18: data_quality present in both domains
"""

import json
import pytest

from md_evals.reporter import Reporter
from md_evals.models import (
    EvalConfig,
    ExecutionResult,
    LLMResponse,
    EvaluatorResult,
    OutputConfig,
    Defaults,
)


# ============================================================================
# Fixtures
# ============================================================================


def _make_response(
    *,
    content: str = "mock response",
    tokens: int = 50,
    duration_ms: int = 1000,
    prompt_tokens: int | None = None,
    completion_tokens_detail: int | None = None,
    stage_type: str = "single_pass",
) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="gpt-4o",
        provider="openai",
        tokens=tokens,
        duration_ms=duration_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens_detail=completion_tokens_detail,
        total_tokens=(
            (prompt_tokens or 0) + (completion_tokens_detail or 0)
            if prompt_tokens is not None or completion_tokens_detail is not None
            else None
        ),
        stage_type=stage_type,
    )


def _make_result(
    treatment: str = "CONTROL",
    test: str = "test_1",
    **kwargs,
) -> ExecutionResult:
    return ExecutionResult(
        treatment=treatment,
        test=test,
        prompt="mock prompt",
        response=_make_response(**kwargs),
        passed=True,
        evaluator_results=[
            EvaluatorResult(evaluator_name="check", passed=True, score=1.0)
        ],
        timestamp="2026-03-15T14:30:25Z",
    )


def _make_config(*, include_usage_metrics: bool = False, **kwargs) -> EvalConfig:
    return EvalConfig(
        name="test-eval",
        version="1.0",
        defaults=Defaults(model="gpt-4o", provider="openai", max_tokens=2048),
        output=OutputConfig(include_usage_metrics=include_usage_metrics),
        cost_map=kwargs.get("cost_map", {}),
        context_window_overrides=kwargs.get("context_window_overrides", {}),
    )


@pytest.fixture
def sample_results():
    """Two-treatment results with full token data."""
    return [
        _make_result(
            treatment="CONTROL",
            test="test_1",
            tokens=50,
            duration_ms=1000,
            prompt_tokens=5000,
            completion_tokens_detail=1500,
        ),
        _make_result(
            treatment="WITH_SKILL",
            test="test_1",
            tokens=60,
            duration_ms=1200,
            prompt_tokens=6000,
            completion_tokens_detail=2000,
        ),
    ]


# ============================================================================
# AC-02: Flag off — JSON is legacy-compatible (no new keys)
# ============================================================================


class TestReporterFlagOff:
    """AC-02: Flag off → JSON has no new keys (backward compat strict)."""

    def test_flag_off_no_usage_metrics_key(self, sample_results):
        """JSON must NOT have usage_metrics when flag off."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        assert "usage_metrics" not in output

    def test_flag_off_no_report_schema_version(self, sample_results):
        """JSON must NOT have report_schema_version when flag off."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        assert "report_schema_version" not in output

    def test_flag_off_no_feature_flags(self, sample_results):
        """JSON must NOT have feature_flags when flag off."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        assert "feature_flags" not in output

    def test_flag_off_legacy_keys_only(self, sample_results):
        """EC-08: Flag off → only legacy keys present."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        legacy_keys = {"experiment_id", "timestamp", "config", "results", "summary"}
        assert set(output.keys()) == legacy_keys

    def test_flag_off_results_have_tokens_and_duration(self, sample_results):
        """AC-17: Legacy fields (tokens, duration_ms) present when flag off."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        for result in output["results"]:
            assert "tokens" in result
            assert "duration_ms" in result
            assert result["tokens"] is not None
            assert result["duration_ms"] is not None

    def test_flag_off_json_write(self, sample_results, tmp_path):
        """Flag off → JSON file has no new keys."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output_path = str(tmp_path / "results.json")
        reporter.report_json(sample_results, output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert "usage_metrics" not in data
        assert "report_schema_version" not in data
        assert "feature_flags" not in data


# ============================================================================
# AC-01: Flag on — JSON has separated cost_metrics and context_metrics
# ============================================================================


class TestReporterFlagOn:
    """AC-01: Flag on → cost_metrics and context_metrics in usage_metrics.variants."""

    def test_flag_on_has_usage_metrics(self, sample_results):
        """usage_metrics block present when flag on."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        assert "usage_metrics" in output

    def test_flag_on_has_report_schema_version(self, sample_results):
        """report_schema_version = "2.0" when flag on."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        assert output["report_schema_version"] == "2.0"

    def test_flag_on_has_feature_flags(self, sample_results):
        """feature_flags.include_usage_metrics = True when flag on."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        assert output["feature_flags"] == {"include_usage_metrics": True}

    def test_flag_on_variants_have_both_domains(self, sample_results):
        """AC-01: Each variant has cost_metrics and context_metrics as separate objects."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)
        variants = output["usage_metrics"]["variants"]

        for treatment_name, variant in variants.items():
            assert "cost_metrics" in variant, f"Missing cost_metrics in {treatment_name}"
            assert "context_metrics" in variant, f"Missing context_metrics in {treatment_name}"
            assert "stage_breakdown" in variant, f"Missing stage_breakdown in {treatment_name}"
            assert "pipeline_mode" in variant, f"Missing pipeline_mode in {treatment_name}"

    def test_flag_on_cost_context_no_overlap(self, sample_results):
        """AC-01: cost_metrics and context_metrics have no overlapping field names."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)
        variant = list(output["usage_metrics"]["variants"].values())[0]

        cost_keys = set(variant["cost_metrics"].keys())
        context_keys = set(variant["context_metrics"].keys())

        # Only data_quality is shared by design
        shared = cost_keys & context_keys
        assert shared == {"data_quality"}, f"Unexpected overlap: {shared}"


# ============================================================================
# AC-17: Legacy fields present regardless of flag
# ============================================================================


class TestLegacyFieldsPreserved:
    """AC-17: tokens and duration_ms in results[] regardless of feature flags."""

    def test_flag_on_results_have_tokens(self, sample_results):
        """AC-17: Flag on → results[].tokens still present."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        for result in output["results"]:
            assert "tokens" in result
            assert "duration_ms" in result
            assert isinstance(result["tokens"], int)
            assert isinstance(result["duration_ms"], int)

    def test_flag_on_results_tokens_values_match(self, sample_results):
        """Legacy tokens match the response tokens value."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        # First result has tokens=50
        assert output["results"][0]["tokens"] == 50
        # Second result has tokens=60
        assert output["results"][1]["tokens"] == 60


# ============================================================================
# AC-18: data_quality in both domains
# ============================================================================


class TestDataQualityInBothDomains:
    """AC-18: data_quality flag present in cost_metrics and context_metrics."""

    def test_data_quality_in_cost(self, sample_results):
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)
        for variant in output["usage_metrics"]["variants"].values():
            assert "data_quality" in variant["cost_metrics"]
            assert variant["cost_metrics"]["data_quality"] in (
                "measured", "estimated", "unavailable"
            )

    def test_data_quality_in_context(self, sample_results):
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)
        for variant in output["usage_metrics"]["variants"].values():
            assert "data_quality" in variant["context_metrics"]
            assert variant["context_metrics"]["data_quality"] in (
                "measured", "estimated", "unavailable"
            )


# ============================================================================
# AC-11: Stage breakdown sum consistency
# ============================================================================


class TestStageBreakdownConsistency:
    """AC-11: Sum of total_tokens in stage_breakdown = variant total_tokens."""

    def test_stage_sum_equals_cost_total(self, sample_results):
        """Sum of stage breakdown totals equals cost_metrics total."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output = reporter._build_output_data(sample_results)

        for variant in output["usage_metrics"]["variants"].values():
            cost_total = variant["cost_metrics"]["total_tokens"]
            stage_total = sum(
                s["total_tokens"] for s in variant["stage_breakdown"]
            )
            assert stage_total == cost_total


# ============================================================================
# JSON output E2E — write and read back
# ============================================================================


class TestReporterJsonOutput:
    """Integration test: write JSON, read back, verify structure."""

    def test_json_roundtrip_flag_on(self, sample_results, tmp_path):
        """Flag on → write JSON, read back, verify all keys present."""
        config = _make_config(
            include_usage_metrics=True,
            cost_map={"gpt-4o": {"input_rate_per_million": 2.50, "output_rate_per_million": 10.00}},
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        output_path = str(tmp_path / "results.json")
        reporter.report_json(sample_results, output_path)

        with open(output_path) as f:
            data = json.load(f)

        # Top-level
        assert "report_schema_version" in data
        assert "feature_flags" in data
        assert "usage_metrics" in data
        assert "results" in data
        assert "summary" in data

        # usage_metrics structure
        um = data["usage_metrics"]
        assert "model" in um
        assert "provider" in um
        assert "variants" in um

        # Each variant
        for name, variant in um["variants"].items():
            assert "cost_metrics" in variant
            assert "context_metrics" in variant
            assert "stage_breakdown" in variant
            assert "pipeline_mode" in variant

    def test_json_roundtrip_flag_off(self, sample_results, tmp_path):
        """Flag off → write JSON, read back, verify legacy-only."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        output_path = str(tmp_path / "results.json")
        reporter.report_json(sample_results, output_path)

        with open(output_path) as f:
            data = json.load(f)

        # Must NOT have new keys
        assert "usage_metrics" not in data
        assert "report_schema_version" not in data
        assert "feature_flags" not in data

        # Must have legacy keys
        assert "results" in data
        assert "summary" in data
        assert "config" in data


# ============================================================================
# Terminal output — flag on shows tables, flag off doesn't
# ============================================================================


class TestReporterTerminalOutput:
    """Verify terminal output includes/excludes usage tables based on flag."""

    def test_terminal_flag_on_no_crash(self, sample_results):
        """Flag on → terminal report runs without crash."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)

        # Should not raise
        reporter.report_terminal(sample_results, verbose=False)

    def test_terminal_flag_off_no_crash(self, sample_results):
        """Flag off → terminal report runs without crash."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)

        # Should not raise
        reporter.report_terminal(sample_results, verbose=False)

    def test_terminal_flag_on_shows_cost_table(self, sample_results, capsys):
        """Flag on → terminal shows Cost Metrics table."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)
        reporter.report_terminal(sample_results, verbose=False)

        captured = capsys.readouterr()
        assert "Cost Metrics" in captured.out

    def test_terminal_flag_on_shows_context_table(self, sample_results, capsys):
        """Flag on → terminal shows Context Metrics table."""
        config = _make_config(
            include_usage_metrics=True,
            context_window_overrides={"gpt-4o": 128000},
        )
        reporter = Reporter(config)
        reporter.report_terminal(sample_results, verbose=False)

        captured = capsys.readouterr()
        assert "Context Metrics" in captured.out

    def test_terminal_flag_off_no_metrics_tables(self, sample_results, capsys):
        """Flag off → terminal does NOT show Cost/Context Metrics tables."""
        config = _make_config(include_usage_metrics=False)
        reporter = Reporter(config)
        reporter.report_terminal(sample_results, verbose=False)

        captured = capsys.readouterr()
        assert "Cost Metrics" not in captured.out
        assert "Context Metrics" not in captured.out
