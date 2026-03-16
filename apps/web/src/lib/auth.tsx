/** Auth context: reads JWT from localStorage, exposes user info, PAT fallback. */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isPATMode: boolean;
  serverOnline: boolean | null;
  login: () => void;
  loginFromCallback: (jwt: string) => void;
  loginWithToken: (pat: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = "md_evals_token";
const USER_KEY = "md_evals_user";

function decodeJwtPayload(token: string): User | null {
  try {
    const parts = token.split(".");
    const payload = parts[1];
    if (!payload) return null;
    const decoded = JSON.parse(atob(payload)) as Record<string, unknown>;

    // Check expiration
    const exp = decoded.exp as number | undefined;
    if (exp && Date.now() / 1000 > exp) {
      return null; // Token expired
    }

    return {
      github_user_id: decoded.github_user_id as number,
      login: decoded.login as string,
      avatar_url: decoded.avatar_url as string,
    };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPATMode, setIsPATMode] = useState(false);
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);

  // Check server health on mount
  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL ?? "";
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);

    fetch(`${apiUrl}/health`, { signal: controller.signal })
      .then((r) => {
        clearTimeout(timer);
        setServerOnline(r.ok);
      })
      .catch(() => {
        clearTimeout(timer);
        setServerOnline(false);
      });

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, []);

  // Restore session from localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem(STORAGE_KEY);
    if (savedToken) {
      const decoded = decodeJwtPayload(savedToken);
      if (decoded) {
        setUser(decoded);
        setToken(savedToken);
      } else {
        // Token expired or invalid — clean up
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(USER_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(() => {
    const apiUrl = import.meta.env.VITE_API_URL ?? "";
    window.location.href = `${apiUrl}/auth/login`;
  }, []);

  const loginFromCallback = useCallback((jwt: string) => {
    const decoded = decodeJwtPayload(jwt);
    if (decoded) {
      localStorage.setItem(STORAGE_KEY, jwt);
      localStorage.setItem(USER_KEY, JSON.stringify(decoded));
      setToken(jwt);
      setUser(decoded);
      setIsPATMode(false);
    }
  }, []);

  const loginWithToken = useCallback(async (pat: string): Promise<boolean> => {
    try {
      const resp = await fetch("https://api.github.com/user", {
        headers: { Authorization: `Bearer ${pat}` },
      });
      if (!resp.ok) return false;

      const data = (await resp.json()) as {
        id: number;
        login: string;
        avatar_url: string;
      };
      const patUser: User = {
        github_user_id: data.id,
        login: data.login,
        avatar_url: data.avatar_url,
      };
      setUser(patUser);
      setToken(pat);
      setIsPATMode(true);
      // PAT only stored in memory, NOT in localStorage (per spec REQ-AUTH-03)
      return true;
    } catch {
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.clear();
    setUser(null);
    setToken(null);
    setIsPATMode(false);
    window.location.hash = "#/login";
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: user !== null,
        isPATMode,
        serverOnline,
        login,
        loginFromCallback,
        loginWithToken,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
