# Phase 5: Intelligence Layer — Analytics Dashboard

## Intent

Add eval history tracking and analytics visualization to md-evals, completing the final phase of the roadmap. This transforms md-evals from a "run and forget" tool into a system that learns from its history.

## Scope

### In Scope

1. **Analytics Engine** (`md_evals/analytics.py`)
   - `AnalyticsStore`: Append-only JSONL store for eval records
   - `AnalyticsEngine`: Compute trends, costs, heatmaps, model comparisons
   - Data models: `EvalRecord`, `TrendPoint`, `SkillTrend`, `CostSummary`, `HeatmapCell`

2. **API Endpoints** (`apps/server/app/routes/analytics.py`)
   - `GET /api/analytics/trends` — Score trends per skill
   - `GET /api/analytics/cost` — Cost aggregation summary
   - `GET /api/analytics/heatmap` — Skills × dimensions matrix
   - `GET /api/analytics/comparison` — Model comparison for a skill
   - `GET /api/analytics/summary` — High-level stats

3. **CLI Commands** (`md_evals/cli.py` — analytics subcommand)
   - `md-evals analytics trends --skill <path> --days 30`
   - `md-evals analytics cost --days 7`
   - `md-evals analytics heatmap [--suite <name>]`

4. **Web Frontend** (`apps/web/src/pages/Analytics.tsx`)
   - Score trends line chart (Recharts)
   - Cost tracking bar chart
   - Skills × dimensions heatmap (HTML table with grade badges)
   - Model comparison radar charts
   - Summary stats cards

5. **Tests** (`tests/test_analytics.py`)
   - ~25 tests covering store, engine, edge cases

### Out of Scope

- Database-backed analytics (file-based JSONL is sufficient for v1)
- Real-time websocket updates for analytics
- Export analytics to external BI tools

## Approach

- Append-only JSONL storage (simple, human-readable, git-friendly)
- Query-time filtering (no pre-built indexes needed for expected data volumes)
- Lazy import of analytics module from scoring to avoid circular deps
- Stateless API endpoints that construct engine per request
- Frontend uses TanStack Query for caching and deduplication

## Risks

| Risk | Mitigation |
|------|------------|
| JSONL grows too large | Future: add rotation/archival, switch to SQLite |
| Query performance degrades | Future: add in-memory caching or date-partitioned files |
| Circular imports with scoring | Lazy import `score_to_grade` only inside `get_heatmap()` |

## Acceptance Criteria

- [x] `AnalyticsStore` persists and loads records correctly
- [x] `AnalyticsEngine` computes trends, costs, heatmap, model comparison
- [x] API endpoints return well-typed responses
- [x] CLI `analytics` subcommand works for trends, cost, heatmap
- [x] Frontend Analytics page renders all four visualizations
- [x] Navigation updated with Analytics link
- [x] 25+ passing tests
- [x] All existing tests continue to pass
