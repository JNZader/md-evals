/** Dashboard page: eval results overview with charts and recent evals list. */

import { useParams, Link } from "react-router-dom";
import {
  Beaker,
  TrendingUp,
  Coins,
  PlayCircle,
  Loader2,
} from "lucide-react";
import { useEval, useEvals } from "../lib/api";
import PassRateChart from "../components/charts/PassRateChart";
import TokenUsageChart from "../components/charts/TokenUsageChart";
import ContextGauge from "../components/charts/ContextGauge";
import EvalResults from "../components/eval/EvalResults";
import { cn } from "../lib/cn";
import type { EvalResult, EvalSummary } from "../lib/types";

export default function Dashboard() {
  const { id } = useParams<{ id: string }>();

  // If viewing a specific eval
  if (id) return <EvalDetail evalId={id} />;

  return <DashboardHome />;
}

function DashboardHome() {
  const { data: evalsResponse, isLoading } = useEvals({
    page: 1,
    per_page: 10,
  });

  const latestEvalId = evalsResponse?.items[0]?.eval_id;
  const { data: latestEval } = useEval(latestEvalId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  const items = evalsResponse?.items ?? [];
  const hasEvals = items.length > 0;

  // The backend stores results as { summary: {...}, results: [...] }
  // We need to extract the nested array
  const rawLatest = latestEval?.results as unknown as Record<string, unknown> | null;
  const latestEvalResults: EvalResult[] = Array.isArray(rawLatest?.results)
    ? (rawLatest.results as EvalResult[])
    : Array.isArray(latestEval?.results)
      ? (latestEval.results as unknown as EvalResult[])
      : [];

  // Build token data for chart from latest eval
  const tokenData =
    latestEvalResults.map((r) => ({
      label: `${r.treatment}/${r.test}`,
      prompt_tokens: (r.cost_metrics as { prompt_tokens?: number } | null)
        ?.prompt_tokens ?? 0,
      completion_tokens: (
        r.cost_metrics as { completion_tokens?: number } | null
      )?.completion_tokens ?? 0,
      total_tokens: (r.cost_metrics as { total_tokens?: number } | null)
        ?.total_tokens ?? 0,
    })) ?? [];

  // Average context utilization
  const contextUtils = latestEvalResults
    .map(
      (r) =>
        (r.context_metrics as { context_utilization_pct?: number } | null)
          ?.context_utilization_pct ?? 0,
    )
    .filter((v) => v > 0);
  const avgContextUtil =
    contextUtils.length > 0
      ? (contextUtils.reduce((a, b) => a + b, 0) / contextUtils.length) * 100
      : 0;

  // Total tokens across all recent evals
  const totalTokens = items.reduce((sum, item) => {
    return sum + (item.duration_ms > 0 ? item.total_tests * 175 : 0); // Estimate
  }, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Dashboard
          </h1>
          <p className="text-sm text-gray-500">
            Overview of your evaluation results
          </p>
        </div>
        <Link
          to="/eval/new"
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <PlayCircle className="h-4 w-4" />
          New Eval
        </Link>
      </div>

      {!hasEvals ? (
        <EmptyState />
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              icon={Beaker}
              label="Total Evals"
              value={String(evalsResponse?.total ?? 0)}
              color="bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400"
            />
            <StatCard
              icon={TrendingUp}
              label="Avg Pass Rate"
              value={
                items.length > 0
                  ? `${Math.round(
                      (items.reduce((s, i) => s + i.pass_rate, 0) /
                        items.length) *
                        100,
                    )}%`
                  : "—"
              }
              color="bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400"
            />
            <StatCard
              icon={Coins}
              label="Est. Total Tokens"
              value={totalTokens > 0 ? `~${totalTokens.toLocaleString()}` : "—"}
              color="bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400"
            />
          </div>

          {/* Charts row */}
          {latestEval?.summary && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Pass Rate Chart */}
              <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900 lg:col-span-1">
                <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Pass Rate by Treatment
                </h3>
                <PassRateChart treatments={latestEval.summary.treatments} />
              </div>

              {/* Token Usage Chart */}
              <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900 lg:col-span-1">
                <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Token Usage (Latest Eval)
                </h3>
                <TokenUsageChart data={tokenData.slice(0, 10)} />
              </div>

              {/* Context Gauge */}
              <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
                <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Context Utilization
                </h3>
                <ContextGauge
                  utilization={avgContextUtil}
                  label="Average across latest eval"
                />
              </div>
            </div>
          )}

          {/* Recent evals list */}
          <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
            <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Recent Evaluations
              </h3>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {items.map((item) => (
                <Link
                  key={item.eval_id}
                  to={`/eval/${item.eval_id}`}
                  className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                      {item.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(item.created_at).toLocaleDateString()} &middot;{" "}
                      {item.model}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        "text-sm font-semibold",
                        item.pass_rate >= 0.8
                          ? "text-green-600"
                          : item.pass_rate >= 0.5
                            ? "text-yellow-600"
                            : "text-red-600",
                      )}
                    >
                      {Math.round(item.pass_rate * 100)}%
                    </span>
                    <StatusBadge status={item.status} />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function EvalDetail({ evalId }: { evalId: string }) {
  const { data: evaluation, isLoading } = useEval(evalId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="py-20 text-center text-gray-500">
        Evaluation not found.
      </div>
    );
  }

  // Backend stores results as { summary: {...}, results: [...] }
  const rawResults = evaluation.results as unknown as Record<string, unknown> | null;
  const evalResultsArray: EvalResult[] = Array.isArray(rawResults?.results)
    ? (rawResults?.results as EvalResult[])
    : Array.isArray(evaluation.results)
      ? (evaluation.results as unknown as EvalResult[])
      : [];
  const evalSummary = (rawResults?.summary as EvalSummary | null) ?? evaluation.summary;

  // Build token data
  const tokenData = evalResultsArray.map((r) => ({
    label: `${r.treatment}/${r.test}`,
    prompt_tokens: (r.cost_metrics as { prompt_tokens?: number } | null)
      ?.prompt_tokens ?? 0,
    completion_tokens: (
      r.cost_metrics as { completion_tokens?: number } | null
    )?.completion_tokens ?? 0,
    total_tokens: (r.cost_metrics as { total_tokens?: number } | null)
      ?.total_tokens ?? 0,
  }));

  const contextUtils = evalResultsArray
    .map(
      (r) =>
        (r.context_metrics as { context_utilization_pct?: number } | null)
          ?.context_utilization_pct ?? 0,
    )
    .filter((v) => v > 0);
  const avgContextUtil =
    contextUtils.length > 0
      ? (contextUtils.reduce((a, b) => a + b, 0) / contextUtils.length) * 100
      : 0;

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/dashboard"
          className="text-sm text-indigo-600 hover:underline"
        >
          &larr; Back to Dashboard
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
          {(evaluation as unknown as Record<string, unknown>).title as string ?? evaluation.name}
        </h1>
        <p className="text-sm text-gray-500">
          {new Date(evaluation.created_at).toLocaleString()} &middot;{" "}
          <StatusBadge status={evaluation.status} />
        </p>
      </div>

      {evalSummary && (
        <>
          {/* Charts */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
              <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                Pass Rate by Treatment
              </h3>
              <PassRateChart treatments={evalSummary.treatments} />
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
              <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                Token Usage
              </h3>
              <TokenUsageChart data={tokenData} />
            </div>
            <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
              <h3 className="mb-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                Context Utilization
              </h3>
              <ContextGauge utilization={avgContextUtil} />
            </div>
          </div>

          {/* Results table */}
          <EvalResults
            summary={evalSummary}
            results={evalResultsArray}
          />
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 py-20 dark:border-gray-700">
      <Beaker className="mb-4 h-12 w-12 text-gray-300" />
      <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300">
        No evaluations yet
      </h3>
      <p className="mb-6 mt-1 text-sm text-gray-500">
        Run your first evaluation to see results here.
      </p>
      <Link
        to="/eval/new"
        className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
      >
        <PlayCircle className="h-4 w-4" />
        Run First Evaluation
      </Link>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Beaker;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
      <div className={cn("rounded-lg p-2.5", color)}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {label}
        </p>
        <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
          {value}
        </p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed:
      "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300",
    running:
      "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
    failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
    timeout:
      "bg-yellow-50 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300",
    pending:
      "bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  };

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        styles[status] ?? styles.pending,
      )}
    >
      {status}
    </span>
  );
}
