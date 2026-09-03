/**
 * Reveal — the unified scroll-reveal primitive for interviewer.ai.
 *
 * A superset of the older `FadeUp`: same defaults (fade + 24px rise, fires once
 * when scrolled into view, shared aurora easing) plus directional entrance,
 * distance control, and an optional physical "settle" overshoot. It reuses the
 * app's `m` motion proxy so it stays inside the existing LazyMotion tree, and it
 * honours reduced-motion globally via the app-level `MotionConfig`.
 *
 * Drop-in for FadeUp:
 *   <Reveal>…</Reveal>
 *   <Reveal delay={0.1} className="…">…</Reveal>
 *
 * Extras:
 *   <Reveal direction="left" distance={32} settle>…</Reveal>
 *   <Reveal as="section" once={false}>…</Reveal>
 */
import { m as motion } from "framer-motion";
import type { ComponentPropsWithoutRef, ElementType, ReactNode } from "react";

/** Shared aurora easing — identical to the hero + legacy FadeUp. */
export const EASE = [0.16, 1, 0.3, 1] as const;

type Direction = "up" | "down" | "left" | "right" | "none";

export type RevealProps = {
  children: ReactNode;
  /** Seconds of delay before the entrance begins. */
  delay?: number;
  /** Entrance duration in seconds. */
  duration?: number;
  /** Which way the element travels in from. Default "up". */
  direction?: Direction;
  /** Travel distance in px for the entrance. Default 24. */
  distance?: number;
  /** Add a subtle overshoot so the element settles physically. Default false. */
  settle?: boolean;
  /** Fire only the first time it enters the viewport. Default true. */
  once?: boolean;
  /** Root margin passed to the viewport observer. Default "-40px". */
  margin?: string;
  /** Render a different element/component. Default "div". */
  as?: ElementType;
  className?: string;
} & Omit<ComponentPropsWithoutRef<typeof motion.div>, "children" | "className">;

function offset(direction: Direction, distance: number) {
  switch (direction) {
    case "up":
      return { y: distance };
    case "down":
      return { y: -distance };
    case "left":
      return { x: distance };
    case "right":
      return { x: -distance };
    case "none":
      return {};
  }
}

export default function Reveal({
  children,
  delay = 0,
  duration = 0.7,
  direction = "up",
  distance = 24,
  settle = false,
  once = true,
  margin = "-40px",
  as = "div",
  className = "",
  ...rest
}: RevealProps) {
  const MotionTag = motion(as as ElementType);
  const from = offset(direction, distance);

  return (
    <MotionTag
      initial={{ opacity: 0, ...from }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once, margin }}
      transition={{
        duration,
        delay,
        ease: EASE,
        // A gentle spring-like tail only when asked, keeping motion physical
        // without the unpredictability of a full spring.
        ...(settle ? { type: "spring", stiffness: 140, damping: 18, mass: 0.9 } : {}),
      }}
      className={className}
      {...rest}
    >
      {children}
    </MotionTag>
  );
}
