import type { QueryClient } from "@tanstack/react-query";
import { fetchBlogFeed, type BlogFeedPayload } from "@/lib/api";

/* Shared query descriptor so an app-startup prefetch and the BlogPage read from
   the same cache entry — the page renders instantly from cache instead of
   firing a fresh request when the user first clicks "Blog". */
export const BLOG_FEED_QUERY_KEY = ["blog-feed", "all", 30] as const;

export const blogFeedQuery = {
  queryKey: BLOG_FEED_QUERY_KEY,
  queryFn: (): Promise<BlogFeedPayload> => fetchBlogFeed(undefined, 30),
  staleTime: 15 * 60 * 1000, // matches the backend's 15-minute blog-feed cache
};

/** Warm the blog-feed cache. */
export function prefetchBlogFeed(queryClient: QueryClient): void {
  void queryClient.prefetchQuery(blogFeedQuery);
}
