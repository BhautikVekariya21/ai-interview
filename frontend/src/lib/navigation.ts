export type AppPage =
  | "upload"
  | "interview"
  | "results"
  | "history"
  | "account"
  | "daily-challenge"
  | "analytics"
  | "faq"
  | "news";

export const pageRouteMap: Record<AppPage, string> = {
  upload: "/app",
  interview: "/app/interview",
  results: "/app/results",
  history: "/app/history",
  account: "/app/account",
  "daily-challenge": "/app/daily-challenge",
  analytics: "/app/analytics",
  faq: "/faq",
  news: "/news",
};

const pathnameToPage: Record<string, AppPage> = {
  "/app": "upload",
  "/app/interview": "interview",
  "/app/results": "results",
  "/app/history": "history",
  "/app/account": "account",
  "/app/daily-challenge": "daily-challenge",
  "/app/analytics": "analytics",
};

export function getPageFromPathname(pathname: string): AppPage {
  const normalized = pathname.replace(/\/+$/, "") || "/app";
  return pathnameToPage[normalized] ?? "upload";
}
