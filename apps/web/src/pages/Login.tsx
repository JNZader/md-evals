/** Login page — OAuth login button. */

import { useAuth } from "../lib/auth";

export default function Login() {
  const { login } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="mb-6 text-3xl font-bold text-gray-900">md-evals</h1>
        <p className="mb-8 text-gray-600">
          Evaluate AI skills with Control vs Treatment testing
        </p>
        <button
          onClick={login}
          className="rounded-lg bg-gray-900 px-6 py-3 text-white hover:bg-gray-800"
        >
          Login with GitHub
        </button>
      </div>
    </div>
  );
}
