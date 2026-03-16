/** EvalRun page: upload SKILL.md + eval YAML, configure, and run evaluation. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PlayCircle, Loader2, AlertTriangle } from "lucide-react";
import { useRunEval } from "../lib/api";
import FileDropZone from "../components/eval/FileDropZone";
import EvalProgress from "../components/eval/EvalProgress";
import EvalResults from "../components/eval/EvalResults";
import type { Evaluation, SSEEvent } from "../lib/types";
import { fetchEval } from "../lib/api";
import { cn } from "../lib/cn";

const DEFAULT_MODEL = "gpt-4o";
const DEFAULT_PROVIDER = "github-models";

export default function EvalRun() {
  const navigate = useNavigate();
  const runMutation = useRunEval();

  const [skillContent, setSkillContent] = useState("");
  const [evalYaml, setEvalYaml] = useState("");
  const [name, setName] = useState("");
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [provider, setProvider] = useState(DEFAULT_PROVIDER);
  const [collectMetrics, setCollectMetrics] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  // Execution state
  const [evalId, setEvalId] = useState<string | null>(null);
  const [completedEval, setCompletedEval] = useState<Evaluation | null>(null);

  const validate = (): string[] => {
    const errs: string[] = [];

    if (!skillContent.trim()) {
      errs.push("SKILL.md content is required.");
    } else if (new Blob([skillContent]).size > 100 * 1024) {
      errs.push("SKILL.md exceeds 100KB limit.");
    }

    if (!evalYaml.trim()) {
      errs.push("Eval YAML content is required.");
    } else if (new Blob([evalYaml]).size > 50 * 1024) {
      errs.push("Eval YAML exceeds 50KB limit.");
    } else {
      // Basic YAML validation
      if (!evalYaml.includes("tests:") && !evalYaml.includes("tests :")) {
        errs.push(
          'Eval YAML must contain a "tests" section with at least one test case.',
        );
      }
    }

    if (!name.trim()) {
      errs.push("Evaluation name is required.");
    }

    return errs;
  };

  const handleRun = () => {
    const validationErrors = validate();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors([]);
    runMutation.mutate(
      {
        name: name.trim(),
        skill_content: skillContent,
        eval_yaml: evalYaml,
        model,
        provider,
      },
      {
        onSuccess: (resp) => {
          setEvalId(resp.eval_id);
        },
        onError: (err) => {
          setErrors([(err as Error).message || "Failed to start evaluation."]);
        },
      },
    );
  };

  const handleComplete = async (_event: SSEEvent) => {
    if (!evalId) return;
    try {
      const eval_ = await fetchEval(evalId);
      setCompletedEval(eval_);
    } catch {
      // User can still navigate to the eval
    }
  };

  const skillLineCount = skillContent.split("\n").length;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Run Evaluation
        </h1>
        <p className="text-sm text-gray-500">
          Upload your SKILL.md and eval YAML to run a Control vs Treatment
          evaluation.
        </p>
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
          {errors.map((err, i) => (
            <p
              key={i}
              className="flex items-center gap-2 text-sm text-red-700 dark:text-red-300"
            >
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {err}
            </p>
          ))}
        </div>
      )}

      {!evalId ? (
        <>
          {/* Name */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Evaluation Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. React 19 Skill v2"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>

          {/* File inputs */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <FileDropZone
                label="SKILL.md"
                placeholder="Paste your SKILL.md content here..."
                value={skillContent}
                onChange={setSkillContent}
                accept=".md"
                maxSizeKB={100}
              />
              {skillLineCount > 400 && (
                <p className="mt-1 text-xs text-yellow-600">
                  Warning: This SKILL.md is very long ({skillLineCount} lines).
                  Long skills may consume significant context window and
                  increase costs.
                </p>
              )}
            </div>
            <FileDropZone
              label="Eval YAML"
              placeholder="Paste your eval configuration YAML here..."
              value={evalYaml}
              onChange={setEvalYaml}
              accept=".yaml,.yml"
              maxSizeKB={50}
            />
          </div>

          {/* Config row */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              >
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4.1">gpt-4.1</option>
                <option value="gpt-4.1-mini">gpt-4.1-mini</option>
                <option value="claude-sonnet-4-20250514">claude-sonnet-4</option>
                <option value="claude-3-5-haiku-20241022">
                  claude-3.5-haiku
                </option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              >
                <option value="github-models">GitHub Models</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={collectMetrics}
                  onChange={(e) => setCollectMetrics(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Collect usage metrics
                </span>
              </label>
            </div>
          </div>

          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={runMutation.isPending}
            className={cn(
              "flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-medium text-white transition-colors",
              runMutation.isPending
                ? "cursor-not-allowed bg-indigo-400"
                : "bg-indigo-600 hover:bg-indigo-700",
            )}
          >
            {runMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <PlayCircle className="h-4 w-4" />
            )}
            {runMutation.isPending ? "Starting..." : "Run Evaluation"}
          </button>
        </>
      ) : (
        <>
          {/* Progress panel */}
          <EvalProgress
            evalId={evalId}
            onComplete={(e) => void handleComplete(e)}
            onError={() => {}}
          />

          {/* Results after completion */}
          {completedEval?.summary && (
            <EvalResults
              summary={completedEval.summary}
              results={completedEval.results}
            />
          )}

          {/* Action buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => {
                setEvalId(null);
                setCompletedEval(null);
              }}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Run Another
            </button>
            {completedEval && (
              <button
                onClick={() => navigate(`/eval/${evalId}`)}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                View Details
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
