/** Analytics page: score trends, cost tracking, heatmap, model comparison. */

import { useState } from "react";
import {
  TrendingUp,
  Coins,
  Grid3X3,
  GitCompare,
  Loader2,
  ArrowUp,
  ArrowDown,
  Minus,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from "recharts";
import {
  useAnalyticsTrends,
  useAnalyticsCost,
  useAnalyticsHeatmap,
  useAnalyticsComparison,
  useAnalyticsSummary,
} from "../lib/api";
import { cn } from "../lib/cn";
import type {
  HeatmapCell,
  SkillTrend,
  CostSummary,
  ModelComparison,
  SummaryStats,
} from "../lib/types";

// ---------------------------------------------------------------------------
// Grade colors
// ---------------------------------------------------------------------------

const GRADE_COLORS: Record<string, string> = {
  S: "#FFD700",
  A: "#22C55E",
  B: "#3B82F6",
  C: "#EAB308",
  D: "#F97316",
  F: "#EF4444",
};

const GRADE_BG: Record<string, string> = {
  S: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  A: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  B: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  C: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  D: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  F: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function Analytics() {
  const [skillInput, setSkillInput] = useState("");
  const [activeSkill, setActiveSkill] = useState<string | undefined>();
  const [days, setDays] = useState(30);
  const [activeTab, setActiveTab] = useState<
    "trends" | "cost" | "heatmap" | "comparison"
  >("trends");

  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary();

  const handleSkillSearch = () => {
    if (skillInput.trim()) setActiveSkill(skillInput.trim());
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Analytics
        </h1>
        <p className="text-sm text-gray-500">
          Eval history trends, cost tracking, and skill insights
        </p>
      </div>

      {/* Summary cards */}
      {summaryLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
        </div>
      ) : summary ? (
        <SummaryCards stats={summary} />
      ) : null}

      {/* Controls */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium text-gray-500">
            Skill Path
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSkillSearch()}
              placeholder="e.g. react-19.md"
              className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
            <button
              onClick={handleSkillSearch}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Search
            </button>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-500">
            Period
          </label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>1 year</option>
          </select>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex gap-1 rounded-lg border border-gray-200 bg-gray-100 p-1 dark:border-gray-700 dark:bg-gray-800">
        {(
          [
            { id: "trends", label: "Trends", icon: TrendingUp },
            { id: "cost", label: "Cost", icon: Coins },
            { id: "heatmap", label: "Heatmap", icon: Grid3X3 },
            { id: "comparison", label: "Compare", icon: GitCompare },
          ] as const
        ).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={cn(
              "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
              activeTab === id
                ? "bg-white text-gray-900 shadow-sm dark:bg-gray-900 dark:text-gray-100"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-[400px]">
        {activeTab === "trends" && (
          <TrendsPanel skill={activeSkill} days={days} />
        )}
        {activeTab === "cost" && <CostPanel days={days} />}
        {activeTab === "heatmap" && <HeatmapPanel />}
        {activeTab === "comparison" && (
          <ComparisonPanel skill={activeSkill} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Summary Cards
// ---------------------------------------------------------------------------

function SummaryCards({ stats }: { stats: SummaryStats }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Total Evals
        </p>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {stats.total_evals}
        </p>
      </div>
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Unique Skills
        </p>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {stats.unique_skills}
        </p>
      </div>
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Avg Score
        </p>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {(stats.avg_score * 100).toFixed(0)}%
        </p>
      </div>
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Grade Distribution
        </p>
        <div className="mt-1 flex gap-2">
          {Object.entries(stats.grade_distribution)
            .sort()
            .map(([grade, count]) => (
              <span
                key={grade}
                className={cn(
                  "inline-flex rounded-full px-2 py-0.5 text-xs font-semibold",
                  GRADE_BG[grade] ?? "bg-gray-100 text-gray-600",
                )}
              >
                {grade}:{count}
              </span>
            ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Trends Panel
// ---------------------------------------------------------------------------

function TrendsPanel({
  skill,
  days,
}: {
  skill: string | undefined;
  days: number;
}) {
  const { data: trend, isLoading } = useAnalyticsTrends(skill, days);

  if (!skill) {
    return (
      <EmptyPanel message="Enter a skill path above to view score trends." />
    );
  }

  if (isLoading) return <LoadingPanel />;

  if (!trend || trend.points.length === 0) {
    return <EmptyPanel message={`No trend data found for "${skill}".`} />;
  }

  const chartData = trend.points.map((p) => ({
    date: new Date(p.timestamp).toLocaleDateString(),
    score: Math.round(p.score * 100) / 100,
    grade: p.grade,
  }));

  const TrendIcon =
    trend.trend_direction === "improving"
      ? ArrowUp
      : trend.trend_direction === "declining"
        ? ArrowDown
        : Minus;
  const trendColor =
    trend.trend_direction === "improving"
      ? "text-green-600"
      : trend.trend_direction === "declining"
        ? "text-red-600"
        : "text-gray-500";

  return (
    <div className="space-y-4">
      {/* Trend summary */}
      <div className="flex items-center gap-6 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <div>
          <p className="text-xs text-gray-500">Latest Grade</p>
          <span
            className={cn(
              "inline-flex rounded-full px-3 py-1 text-lg font-bold",
              GRADE_BG[trend.latest_grade] ?? "bg-gray-100",
            )}
          >
            {trend.latest_grade}
          </span>
        </div>
        <div>
          <p className="text-xs text-gray-500">Trend</p>
          <div className={cn("flex items-center gap-1 text-lg font-semibold", trendColor)}>
            <TrendIcon className="h-5 w-5" />
            {trend.trend_direction}
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500">Data Points</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {trend.points.length}
          </p>
        </div>
      </div>

      {/* Line chart */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
          Score Over Time
        </h3>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={chartData}
            margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#d1d5db" }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#d1d5db" }}
              tickFormatter={(v: number) => v.toFixed(1)}
            />
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null;
                const d = payload[0]?.payload;
                return (
                  <div className="rounded-lg bg-gray-800 px-3 py-2 text-sm shadow-lg">
                    <p className="text-gray-300">{d.date}</p>
                    <p className="font-semibold text-white">
                      Score: {d.score} &middot; Grade:{" "}
                      <span style={{ color: GRADE_COLORS[d.grade] }}>
                        {d.grade}
                      </span>
                    </p>
                  </div>
                );
              }}
            />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#6366f1"
              strokeWidth={2}
              dot={{ fill: "#6366f1", r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cost Panel
// ---------------------------------------------------------------------------

function CostPanel({ days }: { days: number }) {
  const { data: cost, isLoading } = useAnalyticsCost(days);

  if (isLoading) return <LoadingPanel />;

  if (!cost) {
    return <EmptyPanel message="No cost data available." />;
  }

  const modelData = Object.entries(cost.cost_by_model)
    .map(([model, amount]) => ({ model, cost: amount }))
    .sort((a, b) => b.cost - a.cost);

  const BAR_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"];

  return (
    <div className="space-y-4">
      {/* Cost summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Total Cost
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            ${cost.total_cost_usd.toFixed(4)}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Total Tokens
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {cost.total_tokens.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Avg Cost / Eval
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            ${cost.avg_cost_per_eval.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Cost by model bar chart */}
      {modelData.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
            Cost by Model
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={modelData}
              margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="model"
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={{ stroke: "#d1d5db" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={{ stroke: "#d1d5db" }}
                tickFormatter={(v: number) => `$${v.toFixed(3)}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(4)}`, "Cost"]}
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "none",
                  borderRadius: "8px",
                  color: "#f3f4f6",
                  fontSize: "13px",
                }}
              />
              <Bar dataKey="cost" radius={[4, 4, 0, 0]} maxBarSize={80}>
                {modelData.map((_entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={BAR_COLORS[index % BAR_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Heatmap Panel
// ---------------------------------------------------------------------------

function HeatmapPanel() {
  const { data: cells, isLoading } = useAnalyticsHeatmap();

  if (isLoading) return <LoadingPanel />;

  if (!cells || cells.length === 0) {
    return <EmptyPanel message="No heatmap data available. Run some evals first." />;
  }

  // Build matrix
  const skills = [...new Set(cells.map((c) => c.skill))].sort();
  const dimensions = [...new Set(cells.map((c) => c.dimension))].sort();

  const lookup = new Map<string, HeatmapCell>();
  for (const c of cells) {
    lookup.set(`${c.skill}::${c.dimension}`, c);
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
      <h3 className="mb-4 text-sm font-medium text-gray-700 dark:text-gray-300">
        Skills × Dimensions Heatmap
      </h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Skill
              </th>
              {dimensions.map((dim) => (
                <th
                  key={dim}
                  className="px-3 py-2 text-center text-xs font-medium uppercase tracking-wider text-gray-500"
                >
                  {dim}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {skills.map((skill) => (
              <tr key={skill}>
                <td className="whitespace-nowrap px-3 py-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                  {skill}
                </td>
                {dimensions.map((dim) => {
                  const cell = lookup.get(`${skill}::${dim}`);
                  if (!cell) {
                    return (
                      <td
                        key={dim}
                        className="px-3 py-2 text-center text-gray-300 dark:text-gray-600"
                      >
                        —
                      </td>
                    );
                  }
                  return (
                    <td key={dim} className="px-3 py-2 text-center">
                      <span
                        className={cn(
                          "inline-flex rounded-md px-2 py-1 text-xs font-semibold",
                          GRADE_BG[cell.grade] ?? "bg-gray-100",
                        )}
                        title={`Score: ${cell.score.toFixed(2)}`}
                      >
                        {cell.grade} ({(cell.score * 100).toFixed(0)}%)
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Comparison Panel
// ---------------------------------------------------------------------------

function ComparisonPanel({ skill }: { skill: string | undefined }) {
  const { data: comparison, isLoading } = useAnalyticsComparison(skill);

  if (!skill) {
    return (
      <EmptyPanel message="Enter a skill path above to compare models." />
    );
  }

  if (isLoading) return <LoadingPanel />;

  if (!comparison || Object.keys(comparison.models).length === 0) {
    return (
      <EmptyPanel message={`No comparison data found for "${skill}".`} />
    );
  }

  // Build summary per model
  const modelSummaries = Object.entries(comparison.models).map(
    ([model, records]) => {
      const avgScore =
        records.length > 0
          ? records.reduce((s, r) => s + r.overall_score, 0) / records.length
          : 0;
      const avgDuration =
        records.length > 0
          ? records.reduce((s, r) => s + r.duration_ms, 0) / records.length
          : 0;
      const totalCost = records.reduce(
        (s, r) => s + (r.cost_usd ?? 0),
        0,
      );

      // Aggregate dimensions across all records
      const dimAccum: Record<string, { sum: number; count: number }> = {};
      for (const r of records) {
        for (const [dim, score] of Object.entries(r.dimensions)) {
          if (!dimAccum[dim]) dimAccum[dim] = { sum: 0, count: 0 };
          dimAccum[dim].sum += score;
          dimAccum[dim].count += 1;
        }
      }
      const avgDimensions = Object.fromEntries(
        Object.entries(dimAccum).map(([dim, { sum, count }]) => [
          dim,
          sum / count,
        ]),
      );

      return {
        model,
        evals: records.length,
        avgScore,
        avgDuration,
        totalCost,
        avgDimensions,
      };
    },
  );

  // Radar chart data (all models on same radar)
  const allDims = [
    ...new Set(modelSummaries.flatMap((m) => Object.keys(m.avgDimensions))),
  ].sort();
  const radarData = allDims.map((dim) => {
    const point: Record<string, string | number> = {
      dimension: dim.charAt(0).toUpperCase() + dim.slice(1),
    };
    for (const m of modelSummaries) {
      point[m.model] = Math.round((m.avgDimensions[dim] ?? 0) * 100) / 100;
    }
    return point;
  });

  const RADAR_COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"];

  return (
    <div className="space-y-4">
      {/* Model summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modelSummaries.map((m) => (
          <div
            key={m.model}
            className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
          >
            <p className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
              {m.model}
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-gray-500">Evals</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  {m.evals}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Avg Score</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  {m.avgScore.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Avg Duration</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  {Math.round(m.avgDuration)}ms
                </p>
              </div>
              <div>
                <p className="text-gray-500">Total Cost</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  ${m.totalCost.toFixed(4)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Radar chart */}
      {radarData.length > 0 && modelSummaries.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
            Dimension Comparison
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis
                dataKey="dimension"
                tick={{ fill: "#9CA3AF", fontSize: 12 }}
              />
              <PolarRadiusAxis
                domain={[0, 1]}
                tick={{ fill: "#6B7280", fontSize: 10 }}
                tickCount={5}
              />
              {modelSummaries.map((m, i) => (
                <Radar
                  key={m.model}
                  name={m.model}
                  dataKey={m.model}
                  stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                  fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
              ))}
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "none",
                  borderRadius: "8px",
                  color: "#f3f4f6",
                  fontSize: "13px",
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-center gap-4">
            {modelSummaries.map((m, i) => (
              <div key={m.model} className="flex items-center gap-1.5 text-xs">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{
                    backgroundColor:
                      RADAR_COLORS[i % RADAR_COLORS.length],
                  }}
                />
                <span className="text-gray-600 dark:text-gray-400">
                  {m.model}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 py-20 dark:border-gray-700">
      <TrendingUp className="mb-4 h-10 w-10 text-gray-300" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}

function LoadingPanel() {
  return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
    </div>
  );
}
