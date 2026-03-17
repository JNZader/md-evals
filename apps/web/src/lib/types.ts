/** Core TypeScript types matching the API contracts. */

export interface User {
  github_user_id: number;
  login: string;
  avatar_url: string;
}

export interface EvalRunRequest {
  name: string;
  skill_content: string;
  eval_yaml: string;
  model: string;
  provider: string;
}

export interface EvalRunResponse {
  eval_id: string;
  status: string;
  created_at: string;
}

export interface EvalResult {
  id?: string;
  treatment: string;
  test: string;
  model?: string;
  passed: boolean;
  score?: number;
  response_text: string | null;
  cost_metrics: Record<string, unknown> | null;
  context_metrics?: Record<string, unknown> | null;
  evaluator_results: EvaluatorResult[] | null;
  duration_ms: number;
}

export interface EvaluatorResult {
  evaluator_name: string;
  passed: boolean;
  score: number;
  reason: string | null;
}

export interface TreatmentSummary {
  passed: number;
  total: number;
  pass_rate: number;
}

export interface EvalSummary {
  total_tests: number;
  total_passed: number;
  pass_rate: number;
  duration_ms: number;
  treatments: Record<string, TreatmentSummary>;
}

export interface Evaluation {
  eval_id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "timeout";
  config: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
  summary: EvalSummary | null;
  results: EvalResult[];
  usage_metrics: Record<string, unknown> | null;
  scoring?: EvalResultScoring | null;
}

export interface ProviderKey {
  provider: string;
  key_hint: string | null;
  validated_at: string | null;
  status?: string;
  note?: string;
  storage?: "persistent" | "session";
}

export interface HistoryItem {
  eval_id: string;
  name: string;
  status: string;
  model: string;
  pass_rate: number;
  total_tests: number;
  total_passed: number;
  duration_ms: number;
  created_at: string;
  config_hash: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface SSEEvent {
  type: string;
  [key: string]: unknown;
}

// --- Scoring Engine Types ---

export interface DimensionScoreDTO {
  dimension: string;
  score: number;
  weight: number;
  grade: string;
  evidence: string[];
}

export interface PreCheckFindingDTO {
  check: string;
  message: string;
  severity: "error" | "warning" | "info";
  line: number | null;
}

export interface PreCheckResultDTO {
  passed: boolean;
  findings: PreCheckFindingDTO[];
  checks_run: number;
  duration_ms: number;
}

export interface EvalResultScoring {
  overall_grade: string;
  overall_score: number;
  dimensions: DimensionScoreDTO[];
  pre_check: PreCheckResultDTO | null;
}

// --- Analytics Types ---

export interface TrendPoint {
  timestamp: string;
  score: number;
  grade: string;
}

export interface SkillTrend {
  skill_path: string;
  points: TrendPoint[];
  latest_grade: string;
  trend_direction: "improving" | "declining" | "stable";
}

export interface CostSummary {
  total_cost_usd: number;
  total_tokens: number;
  avg_cost_per_eval: number;
  cost_by_model: Record<string, number>;
}

export interface HeatmapCell {
  skill: string;
  dimension: string;
  score: number;
  grade: string;
}

export interface ModelComparisonRecord {
  id: string;
  timestamp: string;
  overall_grade: string;
  overall_score: number;
  dimensions: Record<string, number>;
  cost_usd: number | null;
  duration_ms: number;
}

export interface ModelComparison {
  skill_path: string;
  models: Record<string, ModelComparisonRecord[]>;
}

export interface SummaryStats {
  total_evals: number;
  unique_skills: number;
  avg_score: number;
  grade_distribution: Record<string, number>;
}
