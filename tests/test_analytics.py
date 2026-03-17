"""Comprehensive unit tests for md_evals.analytics module.

Tests cover:
  - AnalyticsStore: append, load, query with filters, edge cases
  - AnalyticsEngine: record_eval, trends, cost, heatmap, model comparison
  - Edge cases: empty store, single record, missing cost data, malformed lines
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timedelta

import pytest

from md_evals.analytics import (
    AnalyticsEngine,
    AnalyticsStore,
    CostSummary,
    EvalRecord,
    HeatmapCell,
    SkillTrend,
    TrendPoint,
)
from md_evals.metrics import CostMetrics
from md_evals.scoring import DimensionScore, EvalMetadata, EvalResult


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def tmp_store(tmp_path):
    """Create a temporary AnalyticsStore."""
    return AnalyticsStore(tmp_path / "analytics.jsonl")


@pytest.fixture()
def engine(tmp_store):
    """Create an AnalyticsEngine with a temporary store."""
    return AnalyticsEngine(tmp_store)


def _make_eval_result(
    skill_path: str = "test-skill.md",
    grade: str = "B",
    score: float = 0.78,
    model: str = "gpt-4o",
    provider: str = "github-models",
    cost_usd: float | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    evidence: list[str] | None = None,
) -> EvalResult:
    """Build a minimal EvalResult for testing."""
    cost_metrics = None
    if cost_usd is not None:
        cost_metrics = CostMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=cost_usd,
        )
    return EvalResult(
        skill_path=skill_path,
        overall_grade=grade,
        overall_score=score,
        dimensions=[
            DimensionScore("correctness", 0.9, 0.25, "A", evidence or []),
            DimensionScore("completeness", 0.7, 0.25, "B", evidence or []),
            DimensionScore("format", 0.8, 0.25, "B", []),
            DimensionScore("adherence", 0.65, 0.25, "C", []),
        ],
        pre_check=None,
        metadata=EvalMetadata(
            model=model,
            provider=provider,
            cost_metrics=cost_metrics,
            total_duration_ms=1500,
        ),
    )


def _make_record(
    skill: str = "skill-a.md",
    grade: str = "B",
    score: float = 0.78,
    model: str = "gpt-4o",
    timestamp: str | None = None,
    suite: str | None = None,
    cost_usd: float | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> EvalRecord:
    """Build a minimal EvalRecord for testing."""
    return EvalRecord(
        id=f"test-{hash((skill, grade, timestamp))}",
        skill_path=skill,
        timestamp=timestamp or datetime.utcnow().isoformat() + "Z",
        overall_grade=grade,
        overall_score=score,
        dimensions={"correctness": 0.9, "completeness": 0.7},
        model=model,
        provider="github-models",
        cost_usd=cost_usd,
        tokens_input=tokens_in,
        tokens_output=tokens_out,
        suite_name=suite,
    )


# ============================================================================
# AnalyticsStore Tests
# ============================================================================


class TestAnalyticsStore:
    """Tests for the append-only JSONL store."""

    def test_load_empty_store(self, tmp_store: AnalyticsStore):
        """Empty store returns empty list."""
        assert tmp_store.load_all() == []

    def test_load_nonexistent_file(self, tmp_path):
        """Non-existent file returns empty list."""
        store = AnalyticsStore(tmp_path / "nonexistent" / "data.jsonl")
        assert store.load_all() == []

    def test_append_and_load(self, tmp_store: AnalyticsStore):
        """Append a record and load it back."""
        record = _make_record()
        tmp_store.append(record)

        records = tmp_store.load_all()
        assert len(records) == 1
        assert records[0].skill_path == record.skill_path
        assert records[0].overall_grade == record.overall_grade

    def test_append_multiple(self, tmp_store: AnalyticsStore):
        """Append multiple records and verify order."""
        for i in range(5):
            tmp_store.append(_make_record(skill=f"skill-{i}.md", score=0.5 + i * 0.1))

        records = tmp_store.load_all()
        assert len(records) == 5

    def test_append_is_additive(self, tmp_store: AnalyticsStore):
        """Multiple appends accumulate without overwriting."""
        tmp_store.append(_make_record(skill="first.md"))
        tmp_store.append(_make_record(skill="second.md"))

        records = tmp_store.load_all()
        assert len(records) == 2
        assert records[0].skill_path == "first.md"
        assert records[1].skill_path == "second.md"

    def test_malformed_lines_skipped(self, tmp_store: AnalyticsStore):
        """Malformed lines are silently skipped."""
        tmp_store.append(_make_record())
        # Write a bad line
        with open(tmp_store.path, "a", encoding="utf-8") as f:
            f.write("this is not json\n")
            f.write('{"bad": "record"}\n')

        records = tmp_store.load_all()
        assert len(records) == 1  # only the valid record

    def test_empty_lines_skipped(self, tmp_store: AnalyticsStore):
        """Blank lines in the file are skipped."""
        tmp_store.append(_make_record())
        with open(tmp_store.path, "a", encoding="utf-8") as f:
            f.write("\n\n\n")

        records = tmp_store.load_all()
        assert len(records) == 1

    def test_query_no_filters(self, tmp_store: AnalyticsStore):
        """Query with no filters returns all records."""
        for i in range(3):
            tmp_store.append(_make_record(skill=f"skill-{i}.md"))

        records = tmp_store.query()
        assert len(records) == 3

    def test_query_by_skill(self, tmp_store: AnalyticsStore):
        """Query filters by skill_path."""
        tmp_store.append(_make_record(skill="react-19.md"))
        tmp_store.append(_make_record(skill="zustand-5.md"))
        tmp_store.append(_make_record(skill="react-19.md"))

        records = tmp_store.query(skill_path="react-19.md")
        assert len(records) == 2
        assert all(r.skill_path == "react-19.md" for r in records)

    def test_query_by_suite(self, tmp_store: AnalyticsStore):
        """Query filters by suite name."""
        tmp_store.append(_make_record(suite="frontend"))
        tmp_store.append(_make_record(suite="backend"))
        tmp_store.append(_make_record(suite="frontend"))

        records = tmp_store.query(suite="frontend")
        assert len(records) == 2

    def test_query_by_model(self, tmp_store: AnalyticsStore):
        """Query filters by model."""
        tmp_store.append(_make_record(model="gpt-4o"))
        tmp_store.append(_make_record(model="claude-3-sonnet"))

        records = tmp_store.query(model="gpt-4o")
        assert len(records) == 1
        assert records[0].model == "gpt-4o"

    def test_query_by_days(self, tmp_store: AnalyticsStore):
        """Query filters by days lookback."""
        recent = datetime.utcnow().isoformat() + "Z"
        old = (datetime.utcnow() - timedelta(days=60)).isoformat() + "Z"

        tmp_store.append(_make_record(timestamp=recent))
        tmp_store.append(_make_record(timestamp=old))

        records = tmp_store.query(days=30)
        assert len(records) == 1

    def test_query_combined_filters(self, tmp_store: AnalyticsStore):
        """Query with multiple filters combines them (AND logic)."""
        tmp_store.append(_make_record(skill="react.md", model="gpt-4o"))
        tmp_store.append(_make_record(skill="react.md", model="claude"))
        tmp_store.append(_make_record(skill="vue.md", model="gpt-4o"))

        records = tmp_store.query(skill_path="react.md", model="gpt-4o")
        assert len(records) == 1

    def test_creates_parent_dirs(self, tmp_path):
        """Store creates parent directories if needed."""
        store = AnalyticsStore(tmp_path / "deep" / "nested" / "data.jsonl")
        store.append(_make_record())

        assert store.path.exists()
        assert len(store.load_all()) == 1


# ============================================================================
# AnalyticsEngine Tests
# ============================================================================


class TestAnalyticsEngine:
    """Tests for analytics computation engine."""

    def test_record_eval_basic(self, engine: AnalyticsEngine, tmp_store: AnalyticsStore):
        """record_eval creates a record and persists it."""
        result = _make_eval_result()
        record = engine.record_eval(result)

        assert record.skill_path == "test-skill.md"
        assert record.overall_grade == "B"
        assert record.overall_score == 0.78
        assert record.model == "gpt-4o"
        assert record.provider == "github-models"
        assert len(record.id) > 0
        assert record.timestamp.endswith("Z")

        # Verify persisted
        stored = tmp_store.load_all()
        assert len(stored) == 1
        assert stored[0].id == record.id

    def test_record_eval_with_cost(self, engine: AnalyticsEngine):
        """record_eval extracts cost metrics."""
        result = _make_eval_result(
            cost_usd=0.0123,
            prompt_tokens=500,
            completion_tokens=200,
        )
        record = engine.record_eval(result)

        assert record.cost_usd == 0.0123
        assert record.tokens_input == 500
        assert record.tokens_output == 200

    def test_record_eval_without_cost(self, engine: AnalyticsEngine):
        """record_eval handles missing cost metrics gracefully."""
        result = _make_eval_result()
        record = engine.record_eval(result)

        assert record.cost_usd is None
        assert record.tokens_input == 0
        assert record.tokens_output == 0

    def test_record_eval_with_suite(self, engine: AnalyticsEngine):
        """record_eval stores suite name."""
        result = _make_eval_result()
        record = engine.record_eval(result, suite_name="backend-skills")

        assert record.suite_name == "backend-skills"

    def test_record_eval_citation_counting(self, engine: AnalyticsEngine):
        """record_eval counts citations from dimension evidence."""
        result = _make_eval_result(
            evidence=["[verified] source A", "source B", "[Verified] source C"],
        )
        record = engine.record_eval(result)

        # Two dimensions have evidence, each with 3 items
        assert record.citations_total == 6  # 3 per dimension × 2 dims with evidence
        assert record.citations_valid == 4  # 2 verified per dimension × 2 dims

    def test_record_eval_extracts_dimensions(self, engine: AnalyticsEngine):
        """record_eval maps dimension names to scores."""
        result = _make_eval_result()
        record = engine.record_eval(result)

        assert "correctness" in record.dimensions
        assert record.dimensions["correctness"] == 0.9
        assert record.dimensions["completeness"] == 0.7

    def test_get_skill_trends_empty(self, engine: AnalyticsEngine):
        """Trend for missing skill returns empty points."""
        trend = engine.get_skill_trends("nonexistent.md")
        assert trend.skill_path == "nonexistent.md"
        assert trend.points == []
        assert trend.latest_grade == "F"
        assert trend.trend_direction == "stable"

    def test_get_skill_trends_single_point(self, engine: AnalyticsEngine):
        """Single record gives one trend point, no direction change."""
        engine.record_eval(_make_eval_result(skill_path="single.md", grade="A", score=0.9))
        trend = engine.get_skill_trends("single.md")

        assert len(trend.points) == 1
        assert trend.latest_grade == "A"
        assert trend.trend_direction == "stable"

    def test_get_skill_trends_improving(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Improving scores detected when recent > older + 0.05."""
        # Older scores (low)
        for i in range(3):
            ts = (datetime.utcnow() - timedelta(days=20 - i)).isoformat() + "Z"
            tmp_store.append(_make_record(skill="improving.md", score=0.50, timestamp=ts))
        # Recent scores (high)
        for i in range(3):
            ts = (datetime.utcnow() - timedelta(days=3 - i)).isoformat() + "Z"
            tmp_store.append(_make_record(skill="improving.md", score=0.90, timestamp=ts))

        trend = engine.get_skill_trends("improving.md")
        assert trend.trend_direction == "improving"

    def test_get_skill_trends_declining(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Declining scores detected when recent < older - 0.05."""
        for i in range(3):
            ts = (datetime.utcnow() - timedelta(days=20 - i)).isoformat() + "Z"
            tmp_store.append(_make_record(skill="declining.md", score=0.90, timestamp=ts))
        for i in range(3):
            ts = (datetime.utcnow() - timedelta(days=3 - i)).isoformat() + "Z"
            tmp_store.append(_make_record(skill="declining.md", score=0.50, timestamp=ts))

        trend = engine.get_skill_trends("declining.md")
        assert trend.trend_direction == "declining"

    def test_get_cost_summary_empty(self, engine: AnalyticsEngine):
        """Cost summary from empty store returns zeros."""
        cost = engine.get_cost_summary()
        assert cost.total_cost_usd == 0.0
        assert cost.total_tokens == 0
        assert cost.avg_cost_per_eval == 0.0
        assert cost.cost_by_model == {}

    def test_get_cost_summary_with_data(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Cost summary aggregates correctly."""
        tmp_store.append(
            _make_record(model="gpt-4o", cost_usd=0.01, tokens_in=100, tokens_out=50)
        )
        tmp_store.append(
            _make_record(model="gpt-4o", cost_usd=0.02, tokens_in=200, tokens_out=100)
        )
        tmp_store.append(
            _make_record(model="claude", cost_usd=0.015, tokens_in=150, tokens_out=75)
        )

        cost = engine.get_cost_summary()
        assert abs(cost.total_cost_usd - 0.045) < 1e-9
        assert cost.total_tokens == 675  # 150 + 300 + 225
        assert abs(cost.avg_cost_per_eval - 0.015) < 1e-9
        assert abs(cost.cost_by_model["gpt-4o"] - 0.03) < 1e-9
        assert abs(cost.cost_by_model["claude"] - 0.015) < 1e-9

    def test_get_cost_summary_no_cost_data(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Cost summary with records that have no cost returns zero cost but counts tokens."""
        tmp_store.append(_make_record(tokens_in=100, tokens_out=50))

        cost = engine.get_cost_summary()
        assert cost.total_cost_usd == 0.0
        assert cost.total_tokens == 150
        assert cost.avg_cost_per_eval == 0.0

    def test_get_heatmap_empty(self, engine: AnalyticsEngine):
        """Heatmap from empty store returns empty list."""
        cells = engine.get_heatmap()
        assert cells == []

    def test_get_heatmap_uses_latest(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Heatmap uses latest record per skill."""
        old_ts = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
        new_ts = datetime.utcnow().isoformat() + "Z"

        old_record = _make_record(skill="react.md", timestamp=old_ts, score=0.5)
        old_record.dimensions = {"correctness": 0.5}
        tmp_store.append(old_record)

        new_record = _make_record(skill="react.md", timestamp=new_ts, score=0.9)
        new_record.dimensions = {"correctness": 0.95}
        tmp_store.append(new_record)

        cells = engine.get_heatmap()
        assert len(cells) == 1
        assert cells[0].score == 0.95
        assert cells[0].grade == "S"  # 0.95 >= S threshold

    def test_get_heatmap_multiple_skills(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Heatmap includes cells for all skills and dimensions."""
        r1 = _make_record(skill="react.md")
        r1.dimensions = {"correctness": 0.9, "format": 0.8}
        tmp_store.append(r1)

        r2 = _make_record(skill="vue.md")
        r2.dimensions = {"correctness": 0.6, "format": 0.7}
        tmp_store.append(r2)

        cells = engine.get_heatmap()
        assert len(cells) == 4  # 2 skills × 2 dimensions

    def test_get_heatmap_with_suite_filter(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Heatmap respects suite filter."""
        r1 = _make_record(skill="react.md", suite="frontend")
        r1.dimensions = {"correctness": 0.9}
        tmp_store.append(r1)

        r2 = _make_record(skill="django.md", suite="backend")
        r2.dimensions = {"correctness": 0.8}
        tmp_store.append(r2)

        cells = engine.get_heatmap(suite="frontend")
        assert len(cells) == 1
        assert cells[0].skill == "react.md"

    def test_get_model_comparison_empty(self, engine: AnalyticsEngine):
        """Model comparison for missing skill returns empty dict."""
        result = engine.get_model_comparison("nonexistent.md")
        assert result == {}

    def test_get_model_comparison(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Model comparison groups by model correctly."""
        tmp_store.append(_make_record(skill="skill.md", model="gpt-4o"))
        tmp_store.append(_make_record(skill="skill.md", model="gpt-4o"))
        tmp_store.append(_make_record(skill="skill.md", model="claude-3"))

        comparison = engine.get_model_comparison("skill.md")
        assert len(comparison) == 2
        assert len(comparison["gpt-4o"]) == 2
        assert len(comparison["claude-3"]) == 1

    def test_get_summary_stats_empty(self, engine: AnalyticsEngine):
        """Summary stats from empty store."""
        stats = engine.get_summary_stats()
        assert stats["total_evals"] == 0
        assert stats["unique_skills"] == 0
        assert stats["avg_score"] == 0.0
        assert stats["grade_distribution"] == {}

    def test_get_summary_stats_with_data(
        self, engine: AnalyticsEngine, tmp_store: AnalyticsStore
    ):
        """Summary stats computed correctly."""
        tmp_store.append(_make_record(skill="a.md", grade="A", score=0.90))
        tmp_store.append(_make_record(skill="b.md", grade="B", score=0.78))
        tmp_store.append(_make_record(skill="a.md", grade="A", score=0.92))

        stats = engine.get_summary_stats()
        assert stats["total_evals"] == 3
        assert stats["unique_skills"] == 2
        assert abs(stats["avg_score"] - round((0.90 + 0.78 + 0.92) / 3, 4)) < 1e-3
        assert stats["grade_distribution"]["A"] == 2
        assert stats["grade_distribution"]["B"] == 1


# ============================================================================
# EvalRecord dataclass tests
# ============================================================================


class TestEvalRecord:
    """Tests for the EvalRecord dataclass."""

    def test_default_values(self):
        """EvalRecord has sensible defaults."""
        record = EvalRecord(
            id="test-id",
            skill_path="skill.md",
            timestamp="2024-01-01T00:00:00Z",
            overall_grade="B",
            overall_score=0.78,
        )
        assert record.dimensions == {}
        assert record.model == ""
        assert record.cost_usd is None
        assert record.tokens_input == 0
        assert record.suite_name is None

    def test_serialization_roundtrip(self):
        """EvalRecord survives JSON roundtrip."""
        original = _make_record()
        serialized = json.dumps(asdict(original))
        deserialized = EvalRecord(**json.loads(serialized))

        assert deserialized.skill_path == original.skill_path
        assert deserialized.overall_score == original.overall_score
        assert deserialized.dimensions == original.dimensions
