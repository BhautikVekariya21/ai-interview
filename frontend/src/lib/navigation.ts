export type AppPage =
  | "upload"
  | "interview"
  | "coding"
  | "results"
  | "history"
  | "account"
  | "analytics"
  | "news";

export const pageRouteMap: Record<AppPage, string> = {
  upload: "/app",
  interview: "/app/interview",
  coding: "/coding",
  results: "/app/results",
  history: "/app/history",
  account: "/app/account",
  analytics: "/app/analytics",
  news: "/news",
};

const pathnameToPage: Record<string, AppPage> = {
  "/app": "upload",
  "/app/interview": "interview",
  "/coding": "coding",
  "/app/results": "results",
  "/app/history": "history",
  "/app/account": "account",
  "/app/analytics": "analytics",
};

export function getPageFromPathname(pathname: string): AppPage {
  const normalized = pathname.replace(/\/+$/, "") || "/app";
  return pathnameToPage[normalized] ?? "upload";
}
