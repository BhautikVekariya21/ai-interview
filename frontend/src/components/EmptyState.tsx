import type { ComponentType, ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  /** Lucide (or any) icon component rendered in the lead tile */
  icon?: ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  /** Primary/secondary actions, e.g. a <Button> */
  action?: ReactNode;
  className?: string;
}

/**
 * Shared empty-state block. Replaces the per-screen reinventions the audit
 * flagged (History, Analytics placeholders, etc.). Token-driven, dark-safe.
 */
export default function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center px-6 py-16",
        className,
      )}
    >
      {Icon && (
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-muted/60 text-muted-foreground">
          <Icon className="h-6 w-6" />
        </div>
      )}
      <h3 className="text-h3 text-foreground">{title}</h3>
      {description && (
        <p className="mt-2 max-w-sm text-body text-muted-foreground">{description}</p>
      )}
      {action && <div className="mt-6 flex flex-wrap items-center justify-center gap-3">{action}</div>}
    </div>
  );
}
