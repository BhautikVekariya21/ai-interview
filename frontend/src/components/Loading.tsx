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
 * Shared loading spinner — the interviewer.ai stacked-layers brand mark with
 * its three layers pulsing in a wave. The single loading idiom the app should
 * use instead of per-screen ad-hoc spinners.
 */
export default function Loading({ label, size = "md", className }: LoadingProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn("flex flex-col items-center justify-center gap-3", className)}
    >
      <svg viewBox="0 0 24 24" fill="none" className={cn("text-brand", DIM[size])} aria-hidden>
        <path
          d="M12 2L2 7l10 5 10-5-10-5z"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="brand-loader-bar"
        />
        <path
          d="M2 12l10 5 10-5"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="brand-loader-bar [animation-delay:0.15s]"
        />
        <path
          d="M2 17l10 5 10-5"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="brand-loader-bar [animation-delay:0.3s]"
        />
      </svg>
      {label ? (
        <span className="text-caption text-muted-foreground">{label}</span>
      ) : (
        <span className="sr-only">Loading</span>
      )}
    </div>
  );
}
