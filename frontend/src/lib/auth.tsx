import { createContext, useContext, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useMe } from "../api/hooks";
import { login as apiLogin, token } from "../api/client";
import type { Me } from "../api/types";

interface Ctx {
  me: Me | undefined;
  loading: boolean;
  can: (perm: string) => boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [hasToken, setHasToken] = useState(() => !!token.get());
  const { data: me, isLoading, isError } = useMe(hasToken);

  const login = async (email: string, password: string) => {
    await apiLogin(email, password);
    qc.clear();
    setHasToken(true);
  };
  const logout = () => {
    token.set(null);
    qc.clear();
    setHasToken(false);
  };
  const value: Ctx = {
    me: hasToken && !isError ? me : undefined,
    loading: hasToken && isLoading,
    can: (perm) => !!me?.permissions.includes(perm),
    login,
    logout,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): Ctx {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
