/** Gauge visual for context utilization percentage. */

import { cn } from "../../lib/cn";

interface Props {
  utilization: number; // 0-100
  label?: string;
}

function getRiskLevel(pct: number): {
  color: string;
  bg: string;
  risk: string;
} {
  if (pct < 70) return { color: "text-green-600", bg: "bg-green-500", risk: "Low Risk" };
  if (pct < 90) return { color: "text-yellow-600", bg: "bg-yellow-500", risk: "Medium Risk" };
  return { color: "text-red-600", bg: "bg-red-500", risk: "High Risk" };
}

export default function ContextGauge({ utilization, label }: Props) {
  const pct = Math.min(100, Math.max(0, utilization));
  const { color, bg, risk } = getRiskLevel(pct);

  // SVG arc for the gauge
  const radius = 60;
  const circumference = Math.PI * radius; // half circle
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg
        width="160"
        height="90"
        viewBox="0 0 160 90"
        className="overflow-visible"
      >
        {/* Background arc */}
        <path
          d="M 20 80 A 60 60 0 0 1 140 80"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <path
          d="M 20 80 A 60 60 0 0 1 140 80"
          fill="none"
          stroke="currentColor"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn(
            pct < 70
              ? "text-green-500"
              : pct < 90
                ? "text-yellow-500"
                : "text-red-500",
          )}
        />
        {/* Percentage text */}
        <text
          x="80"
          y="70"
          textAnchor="middle"
          className="fill-gray-900 text-2xl font-bold dark:fill-gray-100"
          fontSize="24"
        >
          {pct.toFixed(1)}%
        </text>
      </svg>
      <div className="text-center">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
            color,
          )}
        >
          <span className={cn("h-1.5 w-1.5 rounded-full", bg)} />
          {risk}
        </span>
        {label && (
          <p className="mt-1 text-xs text-gray-500">{label}</p>
        )}
      </div>
    </div>
  );
}
