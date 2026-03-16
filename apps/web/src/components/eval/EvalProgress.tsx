/** SSE progress panel: shows real-time eval execution progress. */

import { useEffect, useState, useRef } from "react";
import { CheckCircle, XCircle, Loader2, AlertTriangle } from "lucide-react";
import { streamEval } from "../../lib/api";
import type { SSEEvent } from "../../lib/types";
import { cn } from "../../lib/cn";

interface TestEvent {
  test_index: number;
  test_name: string;
  treatment: string;
  status: "pending" | "running" | "passed" | "failed";
  score?: number;
  duration_ms?: number;
}

interface Props {
  evalId: string;
  onComplete?: (event: SSEEvent) => void;
  onError?: (event: SSEEvent) => void;
}

export default function EvalProgress({ evalId, onComplete, onError }: Props) {
  const [status, setStatus] = useState<
    "connecting" | "running" | "completed" | "error" | "timeout"
  >("connecting");
  const [tests, setTests] = useState<TestEvent[]>([]);
  const [totalTests, setTotalTests] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const cleanup = streamEval(
      evalId,
      (event: SSEEvent) => {
        switch (event.type) {
          case "eval_started": {
            setStatus("running");
            setTotalTests(event.total_tests as number);
            break;
          }
          case "test_started": {
            const te: TestEvent = {
              test_index: event.test_index as number,
              test_name: event.test_name as string,
              treatment: event.treatment as string,
              status: "running",
            };
            setTests((prev) => {
              const next = [...prev];
              next[te.test_index] = te;
              return next;
            });
            break;
          }
          case "test_completed": {
            const idx = event.test_index as number;
            const passed = event.passed as boolean;
            setTests((prev) => {
              const next = [...prev];
              const existing = next[idx];
              if (existing) {
                next[idx] = {
                  ...existing,
                  status: passed ? "passed" : "failed",
                  score: event.score as number | undefined,
                  duration_ms: event.duration_ms as number | undefined,
                };
              }
              return next;
            });
            setCompletedCount((c) => c + 1);
            break;
          }
          case "eval_completed": {
            setStatus("completed");
            onComplete?.(event);
            break;
          }
          case "eval_error": {
            setStatus("error");
            setMessage(event.message as string);
            onError?.(event);
            break;
          }
          case "eval_timeout": {
            setStatus("timeout");
            setMessage(
              `Eval timed out. ${event.completed as number}/${event.total as number} tests completed.`,
            );
            break;
          }
        }
      },
      () => {
        if (status === "connecting") {
          setStatus("error");
          setMessage("Could not connect to event stream.");
        }
      },
    );

    cleanupRef.current = cleanup;
    return () => cleanup();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evalId]);

  const progress = totalTests > 0 ? (completedCount / totalTests) * 100 : 0;

  return (
    <div className="space-y-4 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {status === "connecting" && "Connecting..."}
          {status === "running" && "Running Evaluation"}
          {status === "completed" && "Evaluation Complete"}
          {status === "error" && "Evaluation Failed"}
          {status === "timeout" && "Evaluation Timed Out"}
        </h3>
        <span className="text-xs text-gray-500">
          {completedCount}/{totalTests || "?"}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            status === "completed"
              ? "bg-green-500"
              : status === "error"
                ? "bg-red-500"
                : "bg-indigo-600",
          )}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Error/timeout message */}
      {message && (
        <div
          className={cn(
            "flex items-center gap-2 rounded-lg p-3 text-sm",
            status === "error"
              ? "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
              : "bg-yellow-50 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300",
          )}
        >
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {message}
        </div>
      )}

      {/* Test list */}
      {tests.length > 0 && (
        <div className="max-h-64 space-y-1 overflow-auto">
          {tests.map((test, idx) =>
            test ? (
              <div
                key={idx}
                className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm"
              >
                {test.status === "running" && (
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />
                )}
                {test.status === "passed" && (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                {test.status === "failed" && (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
                {test.status === "pending" && (
                  <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                )}
                <span className="flex-1 truncate text-gray-700 dark:text-gray-300">
                  {test.treatment} / {test.test_name}
                </span>
                {test.duration_ms != null && (
                  <span className="text-xs text-gray-400">
                    {(test.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
            ) : null,
          )}
        </div>
      )}

      {/* Connecting spinner */}
      {status === "connecting" && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
        </div>
      )}
    </div>
  );
}
