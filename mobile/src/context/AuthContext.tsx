import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { apiGet, apiPost } from "../api";
import { getUser, setUser } from "../storage";
import { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    phone?: string;
    state?: string;
  }) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkSession = useCallback(async () => {
    setLoading(true);
    try {
      const me = await apiGet<{ authenticated: boolean; user: User | null }>(
        "/api/auth/me"
      );
      if (me.authenticated && me.user) {
        await setUser(me.user);
        setUserState(me.user);
        setLoading(false);
        return;
      }
    } catch {
      // server unreachable or session expired — fall back to stored user
    }
    const stored = await getUser();
    setUserState(stored);
    setLoading(false);
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = async (email: string, password: string) => {
    const res = await apiPost<{ success: boolean; user: User }>("/api/auth/login", {
      email,
      password,
    });
    await setUser(res.user);
    setUserState(res.user);
    return res.user;
  };

  const register = async (data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    phone?: string;
    state?: string;
  }) => {
    const res = await apiPost<{ success: boolean; user: User }>("/api/auth/register", data);
    await setUser(res.user);
    setUserState(res.user);
    return res.user;
  };

  const logout = async () => {
    try {
      await apiPost("/api/auth/logout", {});
    } catch {
      // ignore network errors on logout
    }
    await setUser(null);
    setUserState(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refresh: checkSession }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
