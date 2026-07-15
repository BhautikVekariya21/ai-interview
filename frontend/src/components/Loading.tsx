import { cn } from "@/lib/utils";

export interface LoadingProps {
  /** Optional label announced to screen readers and shown under the spinner */
  label?: string;
  /** sm = inline, md = block, lg = full-section */
  size?: "sm" | "md" | "lg";
  className?: string;
}

const DIM: Record<NonNullable<LoadingProps["size"]>, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-7 w-7 border-2",
  lg: "h-10 w-10 border-[3px]",
};

/**
 * Shared loading spinner. A brand-accented ring — the single loading idiom the
 * app should use instead of per-screen ad-hoc spinners.
 */
export default function Loading({ label, size = "md", className }: LoadingProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn("flex flex-col items-center justify-center gap-3", className)}
    >
      <span
        className={cn(
          "inline-block animate-spin rounded-full border-muted border-t-brand",
          DIM[size],
        )}
      />
      {label ? (
        <span className="text-caption text-muted-foreground">{label}</span>
      ) : (
        <span className="sr-only">Loading</span>
      )}
    </div>
  );
}
