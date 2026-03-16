/** Auth callback page: extracts JWT from URL, stores it, redirects to dashboard. */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function AuthCallback() {
  const { loginFromCallback } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      const messages: Record<string, string> = {
        invalid_state: "Login session expired. Please try again.",
        exchange_failed: "GitHub authentication failed. Please try again.",
        access_denied:
          "Login cancelled. You need to authorize the app to continue.",
      };
      setError(messages[errorParam] ?? `Authentication error: ${errorParam}`);
      return;
    }

    if (token) {
      loginFromCallback(token);
      navigate("/dashboard", { replace: true });
    } else {
      setError("No authentication token received. Please try logging in again.");
    }
  }, [searchParams, loginFromCallback, navigate]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="mx-auto max-w-md rounded-xl border border-red-200 bg-white p-6 text-center dark:border-red-900 dark:bg-gray-900">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-950">
            <span className="text-xl">!</span>
          </div>
          <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
            Authentication Error
          </h2>
          <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
            {error}
          </p>
          <button
            onClick={() => navigate("/login", { replace: true })}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
      <div className="text-center">
        <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-indigo-600" />
        <p className="text-sm text-gray-500">Authenticating...</p>
      </div>
    </div>
  );
}
