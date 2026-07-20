import type { QueryClient } from "@tanstack/react-query";
import { fetchTechnologyNews, type TechnologyNewsPayload } from "@/lib/api";

/* Shared query descriptor so the app-startup prefetch and the NewsPage read
   from the exact same cache entry — the page renders instantly from cache
   instead of firing a fresh request when the user first clicks "News". */
export const TECHNOLOGY_NEWS_QUERY_KEY = ["technology-news", "all", 300] as const;

export const technologyNewsQuery = {
  queryKey: TECHNOLOGY_NEWS_QUERY_KEY,
  queryFn: (): Promise<TechnologyNewsPayload> => fetchTechnologyNews("all", 300),
  staleTime: 15 * 60 * 1000, // matches the backend's 15-minute news cache
};

/** Warm the technology-news cache as soon as the app loads. */
export function prefetchTechnologyNews(queryClient: QueryClient): void {
  void queryClient.prefetchQuery(technologyNewsQuery);
}
