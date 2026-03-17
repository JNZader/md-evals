/** EvalRun page — simplified: paste a SKILL.md and click Evaluate. */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  PlayCircle,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useRunEval } from "../lib/api";
import FileDropZone from "../components/eval/FileDropZone";
import EvalProgress from "../components/eval/EvalProgress";
import EvalResults from "../components/eval/EvalResults";
import type { Evaluation, SSEEvent } from "../lib/types";
import { fetchEval } from "../lib/api";
import { cn } from "../lib/cn";
import {
  generateEvalName,
  generateEvalYaml,
  hasGherkinContent,
  type Probe,
} from "../lib/eval-generator";

const DEFAULT_MODEL = "gpt-4o-mini";
const DEFAULT_PROVIDER = "github-models";

const PROBE_LABELS: Record<Probe, string> = {
  dimension: "Dimension",
  "edge-case": "Edge Cases",
  compliance: "Compliance",
  gherkin: "Gherkin Scenarios",
};

export default function EvalRun() {
  const navigate = useNavigate();
  const runMutation = useRunEval();

  // --- Form state ---
  const [skillContent, setSkillContent] = useState("");
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [provider, setProvider] = useState(DEFAULT_PROVIDER);
  const [errors, setErrors] = useState<string[]>([]);

  // Probe checkboxes
  const [probes, setProbes] = useState<Record<Probe, boolean>>({
    dimension: true,
    "edge-case": true,
    compliance: true,
    gherkin: false,
  });

  // Generated YAML + advanced toggle
  const [evalYaml, setEvalYaml] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Execution state
  const [evalId, setEvalId] = useState<string | null>(null);
  const [completedEval, setCompletedEval] = useState<Evaluation | null>(null);

  // --- Auto-detect gherkin when skill content changes ---
  useEffect(() => {
    if (!skillContent) return;
    const detected = hasGherkinContent(skillContent);
    setProbes((prev) => {
      if (prev.gherkin === detected) return prev;
      return { ...prev, gherkin: detected };
    });
  }, [skillContent]);

  // --- Re-generate YAML when inputs change ---
  useEffect(() => {
    if (!skillContent.trim()) {
      setEvalYaml("");
      return;
    }
    const activeProbes = (Object.keys(probes) as Probe[]).filter(
      (p) => probes[p],
    );
    const yaml = generateEvalYaml(skillContent, model, provider, activeProbes);
    setEvalYaml(yaml);
  }, [skillContent, model, provider, probes]);

  // --- Toggle a single probe ---
  const toggleProbe = useCallback((probe: Probe) => {
    setProbes((prev) => ({ ...prev, [probe]: !prev[probe] }));
  }, []);

  // --- Validation ---
  const validate = (): string[] => {
    const errs: string[] = [];

    if (!skillContent.trim()) {
      errs.push("SKILL.md content is required.");
    } else if (new Blob([skillContent]).size > 100 * 1024) {
      errs.push("SKILL.md exceeds 100KB limit.");
    }

    if (!evalYaml.trim()) {
      errs.push(
        "No eval YAML was generated. Check your skill content and probe selection.",
      );
    } else if (
      !evalYaml.includes("tests:") &&
      !evalYaml.includes("tests :")
    ) {
      errs.push(
        'Eval YAML must contain a "tests" section with at least one test case.',
      );
    }

    return errs;
  };

  // --- Submit ---
  const handleRun = () => {
    const validationErrors = validate();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors([]);
    const name = generateEvalName(skillContent);

    runMutation.mutate(
      {
        name,
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

  // --- SSE completion ---
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
  const activeProbeCount = (Object.keys(probes) as Probe[]).filter(
    (p) => probes[p],
  ).length;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Evaluate a Skill
        </h1>
        <p className="text-sm text-gray-500">
          Paste your SKILL.md content, choose probes, and click Evaluate.
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
          {/* SKILL.md input — full width */}
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
                Long skills may consume significant context window and increase
                costs.
              </p>
            )}
          </div>

          {/* Model + Provider row */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              >
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4o">gpt-4o</option>
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
          </div>

          {/* Probe checkboxes */}
          <fieldset className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
            <legend className="px-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Probes
            </legend>
            <div className="flex flex-wrap gap-x-6 gap-y-3">
              {(Object.keys(PROBE_LABELS) as Probe[]).map((probe) => (
                <label
                  key={probe}
                  className="flex cursor-pointer items-center gap-2"
                >
                  <input
                    type="checkbox"
                    checked={probes[probe]}
                    onChange={() => toggleProbe(probe)}
                    className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {PROBE_LABELS[probe]}
                    {probe === "gherkin" && hasGherkinContent(skillContent) && (
                      <span className="ml-1 text-xs text-indigo-500">
                        (detected)
                      </span>
                    )}
                  </span>
                </label>
              ))}
            </div>
            {activeProbeCount === 0 && (
              <p className="mt-2 text-xs text-yellow-600">
                Select at least one probe to generate test cases.
              </p>
            )}
          </fieldset>

          {/* Evaluate button */}
          <button
            onClick={handleRun}
            disabled={runMutation.isPending || !skillContent.trim()}
            className={cn(
              "flex items-center gap-2 rounded-xl bg-gradient-to-r px-6 py-3 text-sm font-medium text-white transition-all",
              runMutation.isPending || !skillContent.trim()
                ? "cursor-not-allowed from-indigo-400 to-purple-400 opacity-60"
                : "from-indigo-600 to-purple-600 shadow-md hover:from-indigo-700 hover:to-purple-700 hover:shadow-lg",
            )}
          >
            {runMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <PlayCircle className="h-4 w-4" />
            )}
            {runMutation.isPending ? "Starting..." : "Evaluate"}
          </button>

          {/* Advanced: collapsible YAML editor */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 text-sm text-gray-400 transition-colors hover:text-gray-200"
            >
              {showAdvanced ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              Advanced: View / Edit generated YAML
            </button>

            {showAdvanced && (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-gray-500">
                  This YAML is auto-generated from your SKILL.md. You can edit
                  it manually — your edits will be used as-is.
                </p>
                <textarea
                  value={evalYaml}
                  onChange={(e) => setEvalYaml(e.target.value)}
                  rows={16}
                  spellCheck={false}
                  className="w-full resize-y rounded-lg border border-gray-300 bg-gray-50 p-3 font-mono text-xs text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                  placeholder="Generated YAML will appear here once you paste a SKILL.md..."
                />
              </div>
            )}
          </div>
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
