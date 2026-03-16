/** History page: paginated list of past evaluations with filters. */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, Filter, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { useEvals } from "../lib/api";
import { cn } from "../lib/cn";

const PER_PAGE = 20;

export default function History() {
  const [page, setPage] = useState(1);
  const [model, setModel] = useState("");
  const [status, setStatus] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading } = useEvals({
    page,
    per_page: PER_PAGE,
    model: model || undefined,
    status: status || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const items = data?.items ?? [];
  const totalPages = data?.pages ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            History
          </h1>
          <p className="text-sm text-gray-500">
            {data ? `${data.total} evaluations` : "Loading..."}
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
            showFilters
              ? "border-indigo-300 bg-indigo-50 text-indigo-700 dark:border-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
              : "border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800",
          )}
        >
          <Filter className="h-4 w-4" />
          Filters
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="grid grid-cols-1 gap-4 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900 sm:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">
              From Date
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">
              To Date
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">
              Model
            </label>
            <select
              value={model}
              onChange={(e) => {
                setModel(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">All models</option>
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4.1">gpt-4.1</option>
              <option value="gpt-4.1-mini">gpt-4.1-mini</option>
              <option value="claude-sonnet-4-20250514">claude-sonnet-4</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">All statuses</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="timeout">Timeout</option>
              <option value="running">Running</option>
            </select>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 py-20 dark:border-gray-700">
          <Search className="mb-4 h-12 w-12 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300">
            No evaluations found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {model || status || dateFrom || dateTo
              ? "Try adjusting your filters."
              : "Run your first evaluation to see it here."}
          </p>
          <Link
            to="/eval/new"
            className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Run First Evaluation
          </Link>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Date
                </th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Name
                </th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Model
                </th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Pass Rate
                </th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Tests
                </th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Duration
                </th>
                <th className="px-4 py-3 font-medium text-gray-600 dark:text-gray-400">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {items.map((item) => (
                <tr
                  key={item.eval_id}
                  className="cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/30"
                >
                  <td className="px-4 py-3 text-gray-500">
                    <Link
                      to={`/eval/${item.eval_id}`}
                      className="hover:underline"
                    >
                      {new Date(item.created_at).toLocaleDateString()}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/eval/${item.eval_id}`}
                      className="font-medium text-gray-900 hover:text-indigo-600 dark:text-gray-100 dark:hover:text-indigo-400"
                    >
                      {item.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{item.model}</td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "font-semibold",
                        item.pass_rate >= 0.8
                          ? "text-green-600"
                          : item.pass_rate >= 0.5
                            ? "text-yellow-600"
                            : "text-red-600",
                      )}
                    >
                      {Math.round(item.pass_rate * 100)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {item.total_passed}/{item.total_tests}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {(item.duration_ms / 1000).toFixed(1)}s
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={item.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed:
      "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300",
    running: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
    failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
    timeout:
      "bg-yellow-50 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300",
    pending: "bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
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
