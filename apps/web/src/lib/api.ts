/** Fetch wrapper with auth header injection, error handling, and TanStack Query hooks. */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  CostSummary,
  Evaluation,
  EvalRunRequest,
  EvalRunResponse,
  HeatmapCell,
  HistoryItem,
  ModelComparison,
  PaginatedResponse,
  ProviderKey,
  SkillTrend,
  SSEEvent,
  SummaryStats,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "";

// ---------------------------------------------------------------------------
// Fetch wrapper
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("md_evals_token");

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem("md_evals_token");
    window.location.hash = "#/login";
    throw new ApiError(401, "unauthorized", "Unauthorized");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const b = body as { error?: string; message?: string };
    throw new ApiError(
      response.status,
      b.error ?? "unknown",
      b.message ?? response.statusText,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

// Evals
export async function fetchEvals(params?: {
  page?: number;
  per_page?: number;
  model?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
}): Promise<PaginatedResponse<HistoryItem>> {
  const query = new URLSearchParams();
  if (params?.page) query.set("page", String(params.page));
  if (params?.per_page) query.set("per_page", String(params.per_page));
  if (params?.model) query.set("model", params.model);
  if (params?.status) query.set("status", params.status);
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  const qs = query.toString();
  return fetchApi<PaginatedResponse<HistoryItem>>(
    `/api/eval/history${qs ? `?${qs}` : ""}`,
  );
}

export async function fetchEval(id: string): Promise<Evaluation> {
  return fetchApi<Evaluation>(`/api/eval/${id}`);
}

export async function runEval(data: EvalRunRequest): Promise<EvalRunResponse> {
  return fetchApi<EvalRunResponse>("/api/eval/run", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function streamEval(
  evalId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
): () => void {
  const token = localStorage.getItem("md_evals_token");
  const url = `${API_BASE_URL}/api/eval/${evalId}/stream`;

  const eventSource = new EventSource(
    token ? `${url}?token=${encodeURIComponent(token)}` : url,
  );

  const handleMessage = (eventType: string) => (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data as string) as SSEEvent;
      onEvent({ ...data, type: eventType });
    } catch {
      // ignore parse errors
    }
  };

  const eventTypes = [
    "eval_started",
    "test_started",
    "test_completed",
    "eval_completed",
    "eval_error",
    "eval_timeout",
  ];

  for (const type of eventTypes) {
    eventSource.addEventListener(type, handleMessage(type));
  }

  eventSource.onerror = () => {
    onError?.(new Error("SSE connection error"));
    eventSource.close();
  };

  return () => eventSource.close();
}

// Providers
export async function fetchProviders(): Promise<ProviderKey[]> {
  return fetchApi<ProviderKey[]>("/api/providers");
}

export async function createProvider(data: {
  provider: string;
  key: string;
  storage?: "persistent" | "session";
}): Promise<ProviderKey> {
  return fetchApi<ProviderKey>("/api/providers", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteSessionProvider(
  provider: string,
): Promise<void> {
  return fetchApi<void>(`/api/providers/session/${provider}`, {
    method: "DELETE",
  });
}

export async function validateProvider(data: {
  provider: string;
  key: string;
}): Promise<{ valid: boolean; provider: string }> {
  return fetchApi<{ valid: boolean; provider: string }>(
    "/api/providers/validate",
    { method: "POST", body: JSON.stringify(data) },
  );
}

export async function deleteProvider(provider: string): Promise<void> {
  return fetchApi<void>(`/api/providers/${provider}`, { method: "DELETE" });
}

// Analytics
export async function fetchAnalyticsTrends(
  skill: string,
  days = 30,
): Promise<SkillTrend> {
  return fetchApi<SkillTrend>(
    `/api/analytics/trends?skill=${encodeURIComponent(skill)}&days=${days}`,
  );
}

export async function fetchAnalyticsCost(days = 30): Promise<CostSummary> {
  return fetchApi<CostSummary>(`/api/analytics/cost?days=${days}`);
}

export async function fetchAnalyticsHeatmap(
  suite?: string,
): Promise<HeatmapCell[]> {
  const qs = suite ? `?suite=${encodeURIComponent(suite)}` : "";
  return fetchApi<HeatmapCell[]>(`/api/analytics/heatmap${qs}`);
}

export async function fetchAnalyticsComparison(
  skill: string,
): Promise<ModelComparison> {
  return fetchApi<ModelComparison>(
    `/api/analytics/comparison?skill=${encodeURIComponent(skill)}`,
  );
}

export async function fetchAnalyticsSummary(): Promise<SummaryStats> {
  return fetchApi<SummaryStats>("/api/analytics/summary");
}

// Health
export async function checkHealth(): Promise<{
  status: string;
  version: string;
  db: string;
}> {
  const resp = await fetch(`${API_BASE_URL}/health`);
  return resp.json() as Promise<{ status: string; version: string; db: string }>;
}

// ---------------------------------------------------------------------------
// TanStack Query Hooks
// ---------------------------------------------------------------------------

export function useEvals(params?: {
  page?: number;
  per_page?: number;
  model?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
}) {
  return useQuery({
    queryKey: ["evals", params],
    queryFn: () => fetchEvals(params),
  });
}

export function useEval(id: string | undefined) {
  return useQuery({
    queryKey: ["eval", id],
    queryFn: () => fetchEval(id!),
    enabled: !!id,
  });
}

export function useProviders() {
  return useQuery({
    queryKey: ["providers"],
    queryFn: fetchProviders,
  });
}

export function useRunEval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runEval,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["evals"] });
    },
  });
}

export function useCreateProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProvider,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });
}

export function useValidateProvider() {
  return useMutation({
    mutationFn: validateProvider,
  });
}

export function useDeleteProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteProvider,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });
}

export function useDeleteSessionProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteSessionProvider,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });
}

// Analytics hooks

export function useAnalyticsTrends(skill: string | undefined, days = 30) {
  return useQuery({
    queryKey: ["analytics", "trends", skill, days],
    queryFn: () => fetchAnalyticsTrends(skill!, days),
    enabled: !!skill,
  });
}

export function useAnalyticsCost(days = 30) {
  return useQuery({
    queryKey: ["analytics", "cost", days],
    queryFn: () => fetchAnalyticsCost(days),
  });
}

export function useAnalyticsHeatmap(suite?: string) {
  return useQuery({
    queryKey: ["analytics", "heatmap", suite],
    queryFn: () => fetchAnalyticsHeatmap(suite),
  });
}

export function useAnalyticsComparison(skill: string | undefined) {
  return useQuery({
    queryKey: ["analytics", "comparison", skill],
    queryFn: () => fetchAnalyticsComparison(skill!),
    enabled: !!skill,
  });
}

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: fetchAnalyticsSummary,
  });
}
