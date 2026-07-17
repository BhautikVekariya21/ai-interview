/**
 * SpotlightCard — a glass panel that responds to the cursor.
 *
 * Three composable effects, all GPU-cheap and all opt-out under reduced motion:
 *   1. Spotlight  — a soft radial glow tracks the pointer via two CSS custom
 *                   properties (`--spot-x`/`--spot-y`), updated on rAF. No React
 *                   re-render per mouse move; we write straight to the node.
 *   2. Border     — a 1px gradient border fades in on hover (masked so only the
 *                   ring is painted, never the fill).
 *   3. Lift       — a gentle translateY/scale on hover for physical presence.
 *
 * It builds on the existing `.glass` utility so it sits inside the current design
 * language rather than replacing it. Fully keyboard-accessible: the spotlight
 * also centres on focus-within, and the border reacts to focus.
 *
 * Usage:
 *   <SpotlightCard className="p-6">…</SpotlightCard>
 *   <SpotlightCard as={Link} to="/pricing" className="p-6">…</SpotlightCard>
 */
import { useRef, type ComponentPropsWithoutRef, type ElementType, type ReactNode } from "react";
import { useReducedMotion } from "framer-motion";

type SpotlightCardOwnProps = {
  children: ReactNode;
  /** Radius of the spotlight glow in px. Default 280. */
  radius?: number;
  /** Render as a different element/component (e.g. Link, "article"). Default "div". */
  as?: ElementType;
  className?: string;
};

export type SpotlightCardProps<T extends ElementType = "div"> = SpotlightCardOwnProps &
  Omit<ComponentPropsWithoutRef<T>, keyof SpotlightCardOwnProps>;

export default function SpotlightCard<T extends ElementType = "div">({
  children,
  radius = 280,
  as,
  className = "",
  ...rest
}: SpotlightCardProps<T>) {
  const Tag = (as ?? "div") as ElementType;
  const ref = useRef<HTMLElement>(null);
  const frame = useRef(0);
  const reduce = useReducedMotion();

  const onPointerMove = (e: React.PointerEvent) => {
    if (reduce) return;
    const el = ref.current;
    if (!el || frame.current) return;
    const { clientX, clientY } = e;
    frame.current = requestAnimationFrame(() => {
      frame.current = 0;
      const rect = el.getBoundingClientRect();
      el.style.setProperty("--spot-x", `${clientX - rect.left}px`);
      el.style.setProperty("--spot-y", `${clientY - rect.top}px`);
      el.style.setProperty("--spot-opacity", "1");
    });
  };

  const onLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.setProperty("--spot-opacity", "0");
  };

  return (
    <Tag
      ref={ref}
      onPointerMove={onPointerMove}
      onPointerLeave={onLeave}
      style={
        {
          "--spot-size": `${radius}px`,
        } as React.CSSProperties
      }
      className={[
        "group/spot relative overflow-hidden rounded-3xl",
        // Base surface — reuses the app glass treatment.
        "glass",
        // Gentle physical lift on hover/focus. Motion-safe only.
        "transition-transform duration-300 ease-out",
        !reduce && "hover:-translate-y-1 focus-within:-translate-y-1",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {/* Spotlight glow — tracks the pointer, fades with --spot-opacity. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0 opacity-[var(--spot-opacity,0)] transition-opacity duration-300"
        style={{
          background:
            "radial-gradient(var(--spot-size) circle at var(--spot-x, 50%) var(--spot-y, 50%), hsl(var(--brand) / 0.16), transparent 70%)",
        }}
      />
      {/* 1px gradient border — painted only as a ring via mask, revealed on hover. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0 rounded-3xl opacity-0 transition-opacity duration-300 group-hover/spot:opacity-100 group-focus-within/spot:opacity-100"
        style={{
          padding: "1px",
          background:
            "linear-gradient(140deg, hsl(var(--brand) / 0.55), hsl(var(--chart-3) / 0.45) 55%, transparent)",
          WebkitMask: "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
        }}
      />
      {/* Content sits above the decorative layers. */}
      <span className="relative z-10 block h-full">{children}</span>
    </Tag>
  );
}
