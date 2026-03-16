/** Bar chart: pass rate per treatment. */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { TreatmentSummary } from "../../lib/types";

interface Props {
  treatments: Record<string, TreatmentSummary>;
}

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function PassRateChart({ treatments }: Props) {
  const data = Object.entries(treatments).map(([name, t]) => ({
    name,
    passRate: Math.round(t.pass_rate * 100),
    passed: t.passed,
    total: t.total,
  }));

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-gray-400">
        No treatment data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12, fill: "#6b7280" }}
          axisLine={{ stroke: "#d1d5db" }}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 12, fill: "#6b7280" }}
          axisLine={{ stroke: "#d1d5db" }}
          tickFormatter={(v: number) => `${v}%`}
        />
        <Tooltip
          formatter={(value: number) => [`${value}%`, "Pass Rate"]}
          contentStyle={{
            backgroundColor: "#fff",
            border: "1px solid #e5e7eb",
            borderRadius: "8px",
            fontSize: "13px",
          }}
        />
        <Bar dataKey="passRate" radius={[4, 4, 0, 0]} maxBarSize={80}>
          {data.map((_entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[index % COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
