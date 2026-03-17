"""Analytics API routes for eval history trends and cost tracking.

Phase 5 — Intelligence Layer:
  Provides REST endpoints for skill trends, cost summaries,
  heatmap data, and model comparison analytics.
"""

import logging
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Query

from app.models.schemas import (
    CostSummaryResponse,
    HeatmapCellResponse,
    ModelComparisonResponse,
    SkillTrendResponse,
    SummaryStatsResponse,
    TrendPointResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Default analytics store path (relative to project root)
_ANALYTICS_STORE_PATH = Path("data/analytics.jsonl")


def _get_engine():
    """Lazy-load analytics engine with default store path."""
    from md_evals.analytics import AnalyticsEngine, AnalyticsStore

    store = AnalyticsStore(_ANALYTICS_STORE_PATH)
    return AnalyticsEngine(store)


# ---------- GET /api/analytics/trends ----------


@router.get("/trends", response_model=SkillTrendResponse)
async def get_trends(
    skill: str = Query(..., description="Skill path to get trends for"),
    days: int = Query(default=30, ge=1, le=365, description="Lookback period in days"),
) -> SkillTrendResponse:
    """Get score trend for a skill over time."""
    engine = _get_engine()
    trend = engine.get_skill_trends(skill, days=days)

    return SkillTrendResponse(
        skill_path=trend.skill_path,
        points=[
            TrendPointResponse(
                timestamp=p.timestamp,
                score=p.score,
                grade=p.grade,
            )
            for p in trend.points
        ],
        latest_grade=trend.latest_grade,
        trend_direction=trend.trend_direction,
    )


# ---------- GET /api/analytics/cost ----------


@router.get("/cost", response_model=CostSummaryResponse)
async def get_cost(
    days: int = Query(default=30, ge=1, le=365, description="Lookback period in days"),
) -> CostSummaryResponse:
    """Get cost analytics summary."""
    engine = _get_engine()
    cost = engine.get_cost_summary(days=days)

    return CostSummaryResponse(
        total_cost_usd=round(cost.total_cost_usd, 6),
        total_tokens=cost.total_tokens,
        avg_cost_per_eval=round(cost.avg_cost_per_eval, 6),
        cost_by_model={k: round(v, 6) for k, v in cost.cost_by_model.items()},
    )


# ---------- GET /api/analytics/heatmap ----------


@router.get("/heatmap", response_model=list[HeatmapCellResponse])
async def get_heatmap(
    suite: str | None = Query(default=None, description="Suite filter"),
) -> list[HeatmapCellResponse]:
    """Get skills × dimensions heatmap data."""
    engine = _get_engine()
    cells = engine.get_heatmap(suite=suite)

    return [
        HeatmapCellResponse(
            skill=c.skill,
            dimension=c.dimension,
            score=round(c.score, 4),
            grade=c.grade,
        )
        for c in cells
    ]


# ---------- GET /api/analytics/comparison ----------


@router.get("/comparison", response_model=ModelComparisonResponse)
async def get_comparison(
    skill: str = Query(..., description="Skill path to compare models for"),
) -> ModelComparisonResponse:
    """Get model comparison data for a skill."""
    engine = _get_engine()
    by_model = engine.get_model_comparison(skill)

    models: dict[str, list[dict]] = {}
    for model_name, records in by_model.items():
        models[model_name] = [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "overall_grade": r.overall_grade,
                "overall_score": r.overall_score,
                "dimensions": r.dimensions,
                "cost_usd": r.cost_usd,
                "duration_ms": r.duration_ms,
            }
            for r in records
        ]

    return ModelComparisonResponse(skill_path=skill, models=models)


# ---------- GET /api/analytics/summary ----------


@router.get("/summary", response_model=SummaryStatsResponse)
async def get_summary() -> SummaryStatsResponse:
    """Get high-level analytics summary."""
    engine = _get_engine()
    stats = engine.get_summary_stats()

    return SummaryStatsResponse(
        total_evals=stats["total_evals"],
        unique_skills=stats["unique_skills"],
        avg_score=stats["avg_score"],
        grade_distribution=stats["grade_distribution"],
    )
