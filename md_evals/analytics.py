"""Analytics engine for eval run history and trend analysis.

Phase 5 — Intelligence Layer:
  Append-only JSONL store for eval records, trend computation,
  cost aggregation, skills × dimensions heatmap, and model comparison.

All dataclasses use stdlib @dataclass per ADR-03.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ─── Data Models ───


@dataclass
class EvalRecord:
    """A single eval run record for analytics."""

    id: str
    skill_path: str
    timestamp: str  # ISO 8601
    overall_grade: str
    overall_score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    model: str = ""
    provider: str = ""
    cost_usd: float | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: int = 0
    citations_valid: int = 0
    citations_total: int = 0
    suite_name: str | None = None


@dataclass
class TrendPoint:
    """A point in a score trend."""

    timestamp: str
    score: float
    grade: str


@dataclass
class SkillTrend:
    """Score trend for a single skill over time."""

    skill_path: str
    points: list[TrendPoint] = field(default_factory=list)
    latest_grade: str = "F"
    trend_direction: str = "stable"  # "improving", "declining", "stable"


@dataclass
class CostSummary:
    """Cost analytics summary."""

    total_cost_usd: float = 0.0
    total_tokens: int = 0
    avg_cost_per_eval: float = 0.0
    cost_by_model: dict[str, float] = field(default_factory=dict)


@dataclass
class HeatmapCell:
    """A cell in the skills × dimensions heatmap."""

    skill: str
    dimension: str
    score: float
    grade: str


# ─── Storage ───


class AnalyticsStore:
    """Append-only store for eval records. Uses JSON Lines format."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: EvalRecord) -> None:
        """Append an eval record to the store."""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def load_all(self) -> list[EvalRecord]:
        """Load all records from the store."""
        if not self.path.exists():
            return []
        records: list[EvalRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(EvalRecord(**data))
            except Exception:  # noqa: BLE001
                logger.warning("Skipping malformed analytics record")
                continue
        return records

    def query(
        self,
        skill_path: str | None = None,
        days: int | None = None,
        suite: str | None = None,
        model: str | None = None,
    ) -> list[EvalRecord]:
        """Query records with filters."""
        records = self.load_all()
        if skill_path:
            records = [r for r in records if r.skill_path == skill_path]
        if suite:
            records = [r for r in records if r.suite_name == suite]
        if model:
            records = [r for r in records if r.model == model]
        if days:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            records = [r for r in records if r.timestamp >= cutoff]
        return records


# ─── Engine ───


class AnalyticsEngine:
    """Compute analytics from eval history."""

    def __init__(self, store: AnalyticsStore) -> None:
        self.store = store

    def record_eval(
        self,
        result: Any,
        suite_name: str | None = None,
    ) -> EvalRecord:
        """Record an EvalResult to the analytics store.

        Args:
            result: An ``EvalResult`` from the scoring engine.
            suite_name: Optional suite name for grouping.

        Returns:
            The created EvalRecord.
        """
        record = EvalRecord(
            id=str(uuid.uuid4()),
            skill_path=result.skill_path,
            timestamp=datetime.utcnow().isoformat() + "Z",
            overall_grade=result.overall_grade,
            overall_score=result.overall_score,
            dimensions={d.dimension: d.score for d in result.dimensions},
            model=result.metadata.model if result.metadata else "",
            provider=result.metadata.provider if result.metadata else "",
            duration_ms=result.metadata.total_duration_ms if result.metadata else 0,
            suite_name=suite_name,
        )

        # Extract cost if available
        if result.metadata and result.metadata.cost_metrics:
            record.cost_usd = result.metadata.cost_metrics.estimated_cost_usd
            record.tokens_input = result.metadata.cost_metrics.prompt_tokens
            record.tokens_output = result.metadata.cost_metrics.completion_tokens

        # Extract citation stats from evidence
        for d in result.dimensions:
            record.citations_total += len(d.evidence)
            record.citations_valid += sum(
                1 for e in d.evidence if "[verified]" in e.lower()
            )

        self.store.append(record)
        return record

    def get_skill_trends(
        self,
        skill_path: str,
        days: int = 30,
    ) -> SkillTrend:
        """Get score trend for a skill.

        Args:
            skill_path: Path to the skill being queried.
            days: Number of days to look back.

        Returns:
            SkillTrend with data points and trend direction.
        """
        records = self.store.query(skill_path=skill_path, days=days)
        records.sort(key=lambda r: r.timestamp)

        points = [
            TrendPoint(r.timestamp, r.overall_score, r.overall_grade)
            for r in records
        ]

        trend = SkillTrend(skill_path=skill_path, points=points)
        if points:
            trend.latest_grade = points[-1].grade
            if len(points) >= 2:
                # Compare recent vs older scores
                recent_count = min(3, len(points))
                older_count = min(3, len(points))
                recent = sum(p.score for p in points[-recent_count:]) / recent_count
                older = sum(p.score for p in points[:older_count]) / older_count
                if recent > older + 0.05:
                    trend.trend_direction = "improving"
                elif recent < older - 0.05:
                    trend.trend_direction = "declining"

        return trend

    def get_cost_summary(self, days: int = 30) -> CostSummary:
        """Get cost analytics summary.

        Args:
            days: Number of days to look back.

        Returns:
            CostSummary with total cost, tokens, and per-model breakdown.
        """
        records = self.store.query(days=days)
        summary = CostSummary()

        for r in records:
            if r.cost_usd:
                summary.total_cost_usd += r.cost_usd
                summary.cost_by_model[r.model] = (
                    summary.cost_by_model.get(r.model, 0.0) + r.cost_usd
                )
            summary.total_tokens += r.tokens_input + r.tokens_output

        if records:
            summary.avg_cost_per_eval = summary.total_cost_usd / len(records)

        return summary

    def get_heatmap(self, suite: str | None = None) -> list[HeatmapCell]:
        """Get skills × dimensions heatmap using latest scores.

        Args:
            suite: Optional suite filter.

        Returns:
            List of HeatmapCell, one per (skill, dimension) pair.
        """
        from md_evals.scoring import score_to_grade

        records = self.store.query(suite=suite)

        # Group by skill, take latest
        latest: dict[str, EvalRecord] = {}
        for r in sorted(records, key=lambda x: x.timestamp):
            latest[r.skill_path] = r

        default_thresholds = {"S": 0.95, "A": 0.85, "B": 0.70, "C": 0.50, "D": 0.30}

        cells: list[HeatmapCell] = []
        for skill, record in latest.items():
            for dim, score in record.dimensions.items():
                grade = score_to_grade(score, default_thresholds)
                cells.append(
                    HeatmapCell(skill=skill, dimension=dim, score=score, grade=grade)
                )

        return cells

    def get_model_comparison(
        self,
        skill_path: str,
    ) -> dict[str, list[EvalRecord]]:
        """Get records grouped by model for comparison.

        Args:
            skill_path: Path to the skill being compared.

        Returns:
            Dict mapping model name → list of EvalRecords.
        """
        records = self.store.query(skill_path=skill_path)
        by_model: dict[str, list[EvalRecord]] = {}
        for r in records:
            by_model.setdefault(r.model, []).append(r)
        return by_model

    def get_summary_stats(self) -> dict[str, Any]:
        """Get high-level analytics summary.

        Returns:
            Dict with total_evals, unique_skills, avg_score, grade_distribution.
        """
        records = self.store.load_all()
        if not records:
            return {
                "total_evals": 0,
                "unique_skills": 0,
                "avg_score": 0.0,
                "grade_distribution": {},
            }

        skills = {r.skill_path for r in records}
        avg_score = sum(r.overall_score for r in records) / len(records)

        grade_dist: dict[str, int] = {}
        for r in records:
            grade_dist[r.overall_grade] = grade_dist.get(r.overall_grade, 0) + 1

        return {
            "total_evals": len(records),
            "unique_skills": len(skills),
            "avg_score": round(avg_score, 4),
            "grade_distribution": grade_dist,
        }
