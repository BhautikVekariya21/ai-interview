import { ReactNode, createContext, useContext, useEffect, useMemo, useState } from "react";
import { useUser, useAuth as useClerkAuth } from "@clerk/react";
import {
  AuthUser,
  clearStoredAuth,
  getStoredAuth,
  setStoredAuth,
} from "@/lib/auth";
import {
  deleteUserAccount,
  exchangeClerkSession,
  forgotPassword as forgotPasswordRequest,
  loginUser,
  logoutUser,
  resetPassword as resetPasswordRequest,
  signupUser,
  verifyEmail as verifyEmailRequest,
  updateUserProfile,
  fetchCurrentUser,
  oauthLogin as oauthLoginRequest,
  type ForgotPasswordResponse,
  type SimpleMessageResponse,
} from "@/lib/api";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: { email: string; password: string }) => Promise<void>;
  signup: (payload: { email: string; password: string; full_name: string }) => Promise<SimpleMessageResponse>;
  verifyEmail: (token: string) => Promise<SimpleMessageResponse>;
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
  const { user: clerkUser, isLoaded: isClerkLoaded, isSignedIn: isClerkSignedIn } = useUser();
  const { getToken, signOut: clerkSignOut } = useClerkAuth();

  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isClerkLoaded) return;
    let cancelled = false;

    if (isClerkSignedIn && clerkUser) {
      const activeEmail = clerkUser.primaryEmailAddress?.emailAddress || "";
      const fullName = clerkUser.fullName || clerkUser.username || activeEmail.split("@")[0] || "User";
      setIsLoading(true);
      getToken()
        .then((clerkToken) => {
          if (!clerkToken || !activeEmail) throw new Error("Clerk session is incomplete");
          return exchangeClerkSession(clerkToken, { email: activeEmail, full_name: fullName });
        })
        .then((auth) => {
          if (cancelled) return;
          setStoredAuth(auth);
          setUser(auth.user);
          setToken(auth.token);
        })
        .catch(() => {
          if (cancelled) return;
          clearStoredAuth();
          setUser(null);
          setToken(null);
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    } else {
      const stored = getStoredAuth();
      if (stored) {
        setUser(stored.user);
        setToken(stored.token);
      } else {
        setUser(null);
        setToken(null);
      }
      setIsLoading(false);
    }
    return () => {
      cancelled = true;
    };
  }, [isClerkSignedIn, clerkUser, isClerkLoaded, getToken]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    // A Clerk browser session alone is not enough for protected API routes;
    // only expose an authenticated app state after the backend exchange.
    isAuthenticated: Boolean(user),
    isLoading: !isClerkLoaded || isLoading,
    async login(payload) {
      const auth = await loginUser(payload);
      setStoredAuth(auth);
      setUser(auth.user);
      setToken(auth.token);
    },
    async signup(payload) {
      return signupUser(payload);
    },
    async verifyEmail(token) {
      return verifyEmailRequest(token);
    },
    async oauthLogin(provider) {
      await oauthLoginRequest(provider);
    },
    async logout() {
      try {
        await clerkSignOut();
      } catch {
        // Ignore fallback
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
      if (clerkUser) {
        const activeEmail = clerkUser.primaryEmailAddress?.emailAddress || "";
        setUser({
          id: clerkUser.id,
          email: activeEmail,
          full_name: clerkUser.fullName || clerkUser.username || "User",
          auth_provider: "clerk",
        });
      }
    },
  }), [user, token, isClerkLoaded, isClerkSignedIn, clerkUser, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
