import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { tokenService } from "../../services/tokenService";
import * as authApi from "./authApi";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(tokenService.get()));

  const logout = useCallback(() => {
    tokenService.clear();
    setUser(null);
  }, []);

  // Restore the session on page load.
  useEffect(() => {
    if (!tokenService.get()) return;
    authApi
      .fetchMe()
      .then(setUser)
      .catch(() => tokenService.clear())
      .finally(() => setLoading(false));
  }, []);

  // apiClient fires this when the server rejects the token.
  useEffect(() => {
    window.addEventListener("auth:logout", logout);
    return () => window.removeEventListener("auth:logout", logout);
  }, [logout]);

  const login = useCallback(async (email, password) => {
    const { access_token } = await authApi.login(email, password);
    tokenService.set(access_token);
    const me = await authApi.fetchMe();
    setUser(me);
    return me;
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      can: (permission) => Boolean(user?.permissions?.includes(permission)),
      hasRole: (...roles) => Boolean(user && roles.includes(user.role.name)),
    }),
    [user, loading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
