/**
 * App is served under Vite `base` (e.g. `/ai-interview/`).
 * Use these helpers for absolute browser URLs (Clerk, redirects, window.location).
 * React Router `Link`/`navigate` already use the router basename — do NOT prefix those.
 */

const rawBase = (import.meta.env.BASE_URL || "/").replace(/\/$/, "");

/** Basename without trailing slash, e.g. `/ai-interview` or `` for root. */
export const APP_BASE = rawBase;

/** Absolute path under the app base, e.g. appPath("/auth") → `/ai-interview/auth`. */
export function appPath(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (!APP_BASE) return normalized;
  return `${APP_BASE}${normalized}`;
}
