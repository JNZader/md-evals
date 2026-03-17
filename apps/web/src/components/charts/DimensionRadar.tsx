import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { DimensionScoreDTO } from "../../lib/types";

interface DimensionRadarProps {
  dimensions: DimensionScoreDTO[];
  height?: number;
}

const GRADE_COLORS: Record<string, string> = {
  S: "#FFD700",
  A: "#22C55E",
  B: "#3B82F6",
  C: "#EAB308",
  D: "#F97316",
  F: "#EF4444",
};

export function DimensionRadar({ dimensions, height = 400 }: DimensionRadarProps) {
  const data = dimensions.map((d) => ({
    dimension: d.dimension.charAt(0).toUpperCase() + d.dimension.slice(1),
    score: Math.round(d.score * 100) / 100,
    grade: d.grade,
    weight: d.weight,
    fullMark: 1.0,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="80%">
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
        <Radar
          dataKey="score"
          stroke="#8B5CF6"
          fill="#8B5CF6"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Tooltip
          content={({ payload }) => {
            if (!payload?.length) return null;
            const d = payload[0]?.payload;
            return (
              <div className="rounded-lg bg-gray-800 px-3 py-2 text-sm shadow-lg">
                <p className="font-semibold text-white">{d.dimension}</p>
                <p className="text-gray-300">
                  Score: {d.score} · Grade: <span style={{ color: GRADE_COLORS[d.grade] || "#fff" }}>{d.grade}</span>
                </p>
                <p className="text-gray-400">Weight: {(d.weight * 100).toFixed(0)}%</p>
              </div>
            );
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
