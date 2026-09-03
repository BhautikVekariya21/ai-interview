export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  auth_provider?: string;
  created_at?: string | null;
  updated_at?: string | null;
  [key: string]: unknown;
}

export interface StoredAuth {
  token: string;
  user: AuthUser;
}

const STORAGE_KEY = "interviewer_auth";

export function getStoredAuth(): StoredAuth | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredAuth;
    if (!parsed?.token || !parsed?.user) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function setStoredAuth(auth: StoredAuth): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
  } catch {
    // Ignore storage write failures (private mode, quota, etc.).
  }
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore storage removal failures.
  }
}

export function getStoredAuthToken(): string | null {
  return getStoredAuth()?.token ?? null;
}
