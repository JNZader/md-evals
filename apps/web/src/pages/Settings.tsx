/** Settings page: provider keys management + defaults. */

import { useState } from "react";
import {
  Key,
  Plus,
  Trash2,
  CheckCircle,
  Loader2,
  Shield,
  Eye,
  EyeOff,
  AlertTriangle,
} from "lucide-react";
import {
  useProviders,
  useCreateProvider,
  useDeleteProvider,
  useDeleteSessionProvider,
  useValidateProvider,
} from "../lib/api";
import { cn } from "../lib/cn";

const PROVIDERS = [
  { id: "openai", name: "OpenAI", prefix: "sk-" },
  { id: "anthropic", name: "Anthropic", prefix: "sk-ant-" },
  { id: "google", name: "Google", prefix: "AI" },
  {
    id: "github-models",
    name: "GitHub Models",
    prefix: "",
    oauth: true,
  },
] as const;

export default function Settings() {
  const { data: providers, isLoading } = useProviders();
  const createMutation = useCreateProvider();
  const deleteMutation = useDeleteProvider();
  const deleteSessionMutation = useDeleteSessionProvider();
  const validateMutation = useValidateProvider();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newProvider, setNewProvider] = useState("openai");
  const [newKey, setNewKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [storageMode, setStorageMode] = useState<"persistent" | "session">(
    "persistent",
  );

  const handleAdd = () => {
    if (!newKey.trim()) return;
    setAddError(null);

    createMutation.mutate(
      { provider: newProvider, key: newKey.trim(), storage: storageMode },
      {
        onSuccess: () => {
          setNewKey("");
          setShowAddForm(false);
          setStorageMode("persistent");
        },
        onError: (err) => {
          setAddError((err as Error).message || "Failed to add provider key.");
        },
      },
    );
  };

  const handleValidate = () => {
    if (!newKey.trim()) return;
    setAddError(null);

    validateMutation.mutate(
      { provider: newProvider, key: newKey.trim() },
      {
        onSuccess: (result) => {
          if (result.valid) {
            setAddError(null);
          } else {
            setAddError("Key validation failed. Check your API key.");
          }
        },
        onError: (err) => {
          setAddError((err as Error).message || "Validation failed.");
        },
      },
    );
  };

  const handleDelete = (provider: string) => {
    const saved = providers?.find((pk) => pk.provider === provider);
    const isSession = saved?.storage === "session";

    if (isSession) {
      deleteSessionMutation.mutate(provider, {
        onSuccess: () => setDeleteConfirm(null),
      });
    } else {
      deleteMutation.mutate(provider, {
        onSuccess: () => setDeleteConfirm(null),
      });
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Settings
        </h1>
        <p className="text-sm text-gray-500">
          Manage provider API keys and evaluation defaults.
        </p>
      </div>

      {/* Provider Keys */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Provider API Keys
            </h2>
          </div>
          {!showAddForm && (
            <button
              onClick={() => setShowAddForm(true)}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              Add Key
            </button>
          )}
        </div>

        {/* Existing keys */}
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
          </div>
        ) : (
          <div className="space-y-2">
            {PROVIDERS.map((p) => {
              const saved = providers?.find((pk) => pk.provider === p.id);
              const isOAuth = "oauth" in p && p.oauth;
              const isSession = saved?.storage === "session";
              const isDeleting =
                deleteMutation.isPending ||
                deleteSessionMutation.isPending;

              return (
                <div
                  key={p.id}
                  className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold",
                        saved || isOAuth
                          ? "bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400"
                          : "bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-600",
                      )}
                    >
                      {p.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {p.name}
                      </p>
                      {isOAuth ? (
                        <p className="text-xs text-green-600 dark:text-green-400">
                          Uses your OAuth token
                        </p>
                      ) : saved ? (
                        <div>
                          <p className="text-xs text-gray-500">
                            {saved.key_hint ?? "****"}{" "}
                            {saved.validated_at && (
                              <span className="text-green-600">
                                &middot; Validated{" "}
                                {new Date(
                                  saved.validated_at,
                                ).toLocaleDateString()}
                              </span>
                            )}
                          </p>
                          {isSession && (
                            <p className="mt-0.5 text-xs text-amber-600 dark:text-amber-400">
                              <AlertTriangle className="mr-1 inline h-3 w-3" />
                              This key will be lost when you log out
                            </p>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400">Not configured</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isOAuth && (
                      <span className="flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-950 dark:text-green-300">
                        <Shield className="h-3 w-3" />
                        Available
                      </span>
                    )}
                    {saved && !isOAuth && (
                      <>
                        {isSession ? (
                          <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                            Session
                          </span>
                        ) : (
                          <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-950 dark:text-green-300">
                            Saved
                          </span>
                        )}
                        {deleteConfirm === p.id ? (
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-red-600">
                              Delete?
                            </span>
                            <button
                              onClick={() => handleDelete(p.id)}
                              disabled={isDeleting}
                              className="rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700"
                            >
                              {isDeleting ? "..." : "Yes"}
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400"
                            >
                              No
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(p.id)}
                            className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
                            title="Delete key"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Add key form */}
        {showAddForm && (
          <div className="rounded-xl border border-indigo-200 bg-indigo-50/30 p-4 dark:border-indigo-800 dark:bg-indigo-950/20">
            <h3 className="mb-3 text-sm font-medium text-gray-900 dark:text-gray-100">
              Add Provider Key
            </h3>

            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">
                  Provider
                </label>
                <select
                  value={newProvider}
                  onChange={(e) => setNewProvider(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                >
                  {PROVIDERS.filter((p) => !("oauth" in p && p.oauth)).map(
                    (p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ),
                  )}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showKey ? "text" : "password"}
                    value={newKey}
                    onChange={(e) => {
                      setNewKey(e.target.value);
                      setAddError(null);
                    }}
                    placeholder="sk-..."
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    type="button"
                  >
                    {showKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Storage mode toggle */}
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-500">
                  Storage
                </label>
                <div className="flex gap-3">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="storageMode"
                      value="persistent"
                      checked={storageMode === "persistent"}
                      onChange={() => setStorageMode("persistent")}
                      className="accent-indigo-600"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Save permanently
                    </span>
                  </label>
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="storageMode"
                      value="session"
                      checked={storageMode === "session"}
                      onChange={() => setStorageMode("session")}
                      className="accent-amber-600"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Use for this session only
                    </span>
                  </label>
                </div>
                {storageMode === "session" && (
                  <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                    <AlertTriangle className="mr-1 inline h-3 w-3" />
                    This key will only be stored in server memory. It will be
                    lost when you log out or the server restarts.
                  </p>
                )}
              </div>

              {addError && (
                <div className="flex items-center gap-2 text-sm text-red-600">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  {addError}
                </div>
              )}

              {validateMutation.isSuccess && validateMutation.data.valid && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  Key is valid!
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={handleValidate}
                  disabled={
                    !newKey.trim() || validateMutation.isPending
                  }
                  className="flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  {validateMutation.isPending && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  )}
                  Validate
                </button>
                <button
                  onClick={handleAdd}
                  disabled={!newKey.trim() || createMutation.isPending}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50",
                    storageMode === "session"
                      ? "bg-amber-600 hover:bg-amber-700"
                      : "bg-indigo-600 hover:bg-indigo-700",
                  )}
                >
                  {createMutation.isPending && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  )}
                  {storageMode === "session"
                    ? "Use for Session"
                    : "Save Key"}
                </button>
                <button
                  onClick={() => {
                    setShowAddForm(false);
                    setNewKey("");
                    setAddError(null);
                    setStorageMode("persistent");
                  }}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-500 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-800"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Default Model Selection */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Defaults
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Default Model
              </label>
              <select
                defaultValue="gpt-4o"
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
                Default Provider
              </label>
              <select
                defaultValue="github-models"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              >
                <option value="github-models">GitHub Models</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
              </select>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-400">
            These defaults will be pre-selected when running new evaluations.
          </p>
        </div>
      </section>
    </div>
  );
}
