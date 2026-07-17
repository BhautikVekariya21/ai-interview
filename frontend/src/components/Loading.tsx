import { cn } from "@/lib/utils";

export interface LoadingProps {
  /** Optional label announced to screen readers and shown under the spinner */
  label?: string;
  /** sm = inline, md = block, lg = full-section */
  size?: "sm" | "md" | "lg";
  className?: string;
}

const DIM: Record<NonNullable<LoadingProps["size"]>, string> = {
  sm: "h-4 w-4",
  md: "h-8 w-8",
  lg: "h-12 w-12",
};

/**
 * Shared loading spinner — the animated interviewer.ai logo mark (the three
 * bars from the favicon) pulsing in a wave. The single loading idiom the app
 * should use instead of per-screen ad-hoc spinners.
 */
export default function Loading({ label, size = "md", className }: LoadingProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn("flex flex-col items-center justify-center gap-3", className)}
    >
      <svg viewBox="0 0 32 32" className={cn("text-brand", DIM[size])} aria-hidden>
        <rect x="7" y="6" width="18" height="5" rx="2.5" fill="currentColor" className="brand-loader-bar" />
        <rect x="3" y="13.5" width="26" height="5" rx="2.5" fill="currentColor" className="brand-loader-bar [animation-delay:0.15s]" />
        <rect x="7" y="21" width="18" height="5" rx="2.5" fill="currentColor" className="brand-loader-bar [animation-delay:0.3s]" />
      </svg>
      {label ? (
        <span className="text-caption text-muted-foreground">{label}</span>
      ) : (
        <span className="sr-only">Loading</span>
      )}
    </div>
  );
}
