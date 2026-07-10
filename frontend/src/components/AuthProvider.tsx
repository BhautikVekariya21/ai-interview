import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  AuthUser,
  clearStoredAuth,
  getStoredAuth,
  setStoredAuth,
} from "@/lib/auth";
import {
  deleteUserAccount,
  forgotPassword as forgotPasswordRequest,
  loginUser,
  logoutUser,
  resetPassword as resetPasswordRequest,
  signupUser,
  updateUserProfile,
  fetchCurrentUser,
  oauthLogin as oauthLoginRequest,
  type ForgotPasswordResponse,
} from "@/lib/api";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: { email: string; password: string }) => Promise<void>;
  signup: (payload: { email: string; password: string; full_name: string }) => Promise<void>;
  oauthLogin: (provider: "google" | "github") => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<ForgotPasswordResponse>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  updateProfile: (payload: { full_name?: string; email?: string; current_password?: string; new_password?: string }) => Promise<void>;
  deleteAccount: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = getStoredAuth();
    if (stored) {
      setUser(stored.user);
      setToken(stored.token);
    }

    fetchCurrentUser(stored?.token)
      .then((nextUser) => {
        setUser(nextUser);
        if (stored?.token) {
          setStoredAuth({ token: stored.token, user: nextUser });
        }
      })
      .catch(() => {
        clearStoredAuth();
        setUser(null);
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    isAuthenticated: Boolean(user),
    isLoading,
    async login(payload) {
      const auth = await loginUser(payload);
      setStoredAuth(auth);
      setUser(auth.user);
      setToken(auth.token);
    },
    async signup(payload) {
      const auth = await signupUser(payload);
      setStoredAuth(auth);
      setUser(auth.user);
      setToken(auth.token);
    },
    async oauthLogin(provider) {
      const auth = await oauthLoginRequest(provider);
      setStoredAuth(auth);
      setUser(auth.user);
      setToken(auth.token);
    },
    async logout() {
      try {
        await logoutUser(token);
      } catch {
        // Ignore network/logout cleanup failures.
      }
      clearStoredAuth();
      setUser(null);
      setToken(null);
    },
    async forgotPassword(email) {
      return forgotPasswordRequest(email);
    },
    async resetPassword(resetToken, newPassword) {
      await resetPasswordRequest(resetToken, newPassword);
    },
    async updateProfile(payload) {
      const auth = await updateUserProfile(payload);
      if (auth.token) {
        setToken(auth.token);
        setStoredAuth(auth);
      }
      setUser(auth.user);
    },
    async deleteAccount() {
      await deleteUserAccount();
      clearStoredAuth();
      setUser(null);
      setToken(null);
    },
    async refreshUser() {
      const nextUser = await fetchCurrentUser(token);
      setUser(nextUser);
      if (token) {
        setStoredAuth({ token, user: nextUser });
      }
    },
  }), [user, token, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
