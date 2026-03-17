/** Results table and summary metrics for a completed eval. */

import { CheckCircle, XCircle } from "lucide-react";
import type { EvalResult, EvalSummary } from "../../lib/types";
import { cn } from "../../lib/cn";

interface Props {
  summary: EvalSummary;
  results: EvalResult[];
}

export default function EvalResults({ summary, results }: Props) {
  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <SummaryCard
          label="Pass Rate"
          value={`${Math.round(summary.pass_rate * 100)}%`}
          color={
            summary.pass_rate >= 0.8
              ? "text-green-600"
              : summary.pass_rate >= 0.5
                ? "text-yellow-600"
                : "text-red-600"
          }
        />
        <SummaryCard label="Total Tests" value={String(summary.total_tests)} />
        <SummaryCard
          label="Passed"
          value={`${summary.total_passed}/${summary.total_tests}`}
          color="text-green-600"
        />
        <SummaryCard
          label="Duration"
          value={`${(summary.duration_ms / 1000).toFixed(1)}s`}
        />
      </div>

      {/* Results table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                Status
              </th>
              <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                Test
              </th>
              <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                Treatment
              </th>
              <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                Score
              </th>
              <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                Tokens
              </th>
              <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                Duration
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {results.map((r, idx) => {
              const score =
                r.score ??
                (r.evaluator_results?.length
                  ? r.evaluator_results[0]?.score
                  : 0) ??
                0;

              return (
                <tr
                  key={r.id ?? idx}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/30"
                >
                  <td className="px-4 py-3">
                    {r.passed ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500" />
                    )}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                    {r.test}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
                        r.treatment === "CONTROL"
                          ? "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                          : "bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300",
                      )}
                    >
                      {r.treatment}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                    {score.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {r.cost_metrics
                      ? String(
                          (r.cost_metrics as { total_tokens?: number })
                            .total_tokens ?? "—",
                        )
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {(r.duration_ms / 1000).toFixed(1)}s
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
        {label}
      </p>
      <p
        className={cn(
          "mt-1 text-2xl font-bold",
          color ?? "text-gray-900 dark:text-gray-100",
        )}
      >
        {value}
      </p>
    </div>
  );
}
