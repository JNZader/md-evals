/** Login page: OAuth login button + PAT fallback + server status. */

import { useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { Github, Key, Loader2, CheckCircle, XCircle } from "lucide-react";
import { useAuth } from "../lib/auth";
import { cn } from "../lib/cn";

export default function Login() {
  const { login, loginWithToken, isAuthenticated, serverOnline } = useAuth();
  const [searchParams] = useSearchParams();
  const [showPAT, setShowPAT] = useState(false);
  const [pat, setPAT] = useState("");
  const [patLoading, setPATLoading] = useState(false);
  const [patError, setPATError] = useState<string | null>(null);

  const errorParam = searchParams.get("error");

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handlePATLogin = async () => {
    if (!pat.trim()) return;
    setPATLoading(true);
    setPATError(null);
    const success = await loginWithToken(pat.trim());
    setPATLoading(false);
    if (!success) {
      setPATError(
        "Invalid or expired token. Make sure it has the read:user scope.",
      );
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4 dark:from-gray-950 dark:to-gray-900">
      <div className="w-full max-w-md space-y-6">
        {/* Logo & title */}
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg">
            <svg
              viewBox="0 0 24 24"
              className="h-8 w-8"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            md-evals
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Evaluate AI skills with Control vs Treatment testing
          </p>
        </div>

        {/* Error from OAuth callback */}
        {errorParam && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {errorParam === "access_denied"
              ? "Login cancelled. You need to authorize the app to continue."
              : errorParam === "invalid_state"
                ? "Login session expired. Please try again."
                : `Authentication error: ${errorParam}`}
          </div>
        )}

        {/* Main card */}
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          {/* Server status */}
          <div className="mb-4 flex items-center gap-2 text-xs">
            {serverOnline === null && (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin text-gray-400" />
                <span className="text-gray-400">Checking server...</span>
              </>
            )}
            {serverOnline === true && (
              <>
                <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                <span className="text-green-600 dark:text-green-400">
                  Server online
                </span>
              </>
            )}
            {serverOnline === false && (
              <>
                <XCircle className="h-3.5 w-3.5 text-red-500" />
                <span className="text-red-600 dark:text-red-400">
                  Server offline
                </span>
              </>
            )}
          </div>

          {/* GitHub OAuth button */}
          <button
            onClick={login}
            disabled={serverOnline === false}
            className={cn(
              "flex w-full items-center justify-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors",
              serverOnline === false
                ? "cursor-not-allowed bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-600"
                : "bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200",
            )}
          >
            <Github className="h-5 w-5" />
            Sign in with GitHub
          </button>

          {/* Divider */}
          <div className="my-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
            <span className="text-xs text-gray-400">or</span>
            <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700" />
          </div>

          {/* PAT section */}
          {!showPAT ? (
            <button
              onClick={() => setShowPAT(true)}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              <Key className="h-4 w-4" />
              Use Personal Access Token
            </button>
          ) : (
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                GitHub Personal Access Token
              </label>
              <input
                type="password"
                value={pat}
                onChange={(e) => {
                  setPAT(e.target.value);
                  setPATError(null);
                }}
                placeholder="ghp_xxxxxxxxxxxx"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                onKeyDown={(e) => {
                  if (e.key === "Enter") void handlePATLogin();
                }}
              />
              {patError && (
                <p className="text-sm text-red-600">{patError}</p>
              )}
              <button
                onClick={() => void handlePATLogin()}
                disabled={patLoading || !pat.trim()}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {patLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                Authenticate
              </button>
              <p className="text-xs text-gray-500">
                Create a PAT with{" "}
                <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">
                  read:user
                </code>{" "}
                scope at{" "}
                <a
                  href="https://github.com/settings/tokens/new"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-600 underline"
                >
                  github.com/settings/tokens
                </a>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
