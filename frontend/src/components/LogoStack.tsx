import { cn } from "@/lib/utils";

type LogoStackProps = {
  className?: string;
  /** Render inside the filled dark rounded-square badge (matches the app mark). */
  badge?: boolean;
  title?: string;
};

/**
 * interviewer.ai brand mark — the stacked-layers glyph used on the home page.
 * Kept identical everywhere (navbar, auth, chat avatar, favicon, spinner).
 * `badge` wraps the glyph in the dark rounded-square; otherwise it inherits
 * `currentColor`.
 */
export default function LogoStack({ className, badge = false, title }: LogoStackProps) {
  const glyph = (
    <svg viewBox="0 0 24 24" fill="none" className={badge ? "h-1/2 w-1/2" : className}>
      {title ? <title>{title}</title> : null}
      <path
        d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );

  if (badge) {
    return (
      <span
        className={cn(
          "flex items-center justify-center rounded-lg bg-foreground text-background",
          className,
        )}
        role={title ? "img" : undefined}
        aria-hidden={title ? undefined : true}
      >
        {glyph}
      </span>
    );
  }

  return glyph;
}
