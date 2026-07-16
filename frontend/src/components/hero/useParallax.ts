/**
 * useParallax — motion values for the layered hero aurora.
 *
 * Combines two cheap, GPU-friendly signals into per-plane transforms:
 *   • scroll   — how far the hero has scrolled through the viewport
 *   • pointer  — cursor position relative to the hero centre (desktop only)
 *
 * Everything is capped to a small travel budget (default 20px) so the effect
 * reads as depth, never motion-sickness. It fully stands down when the user
 * prefers reduced motion, or on touch/coarse pointers where pointer-parallax is
 * meaningless and battery matters.
 *
 * It exposes a FIXED set of depth planes (foreground → deep background) created
 * at the top level of the hook, so there are no hooks inside loops or callbacks
 * — the consumer just reads `planes[i]`.
 *
 * Usage:
 *   const ref = useRef<HTMLElement>(null);
 *   const { planes } = useParallax(ref);
 *   <motion.div style={{ x: planes[2].x, y: planes[2].y }} />  // deepest
 */
import { useEffect } from "react";
import {
  useMotionValue,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
  type MotionValue,
  type RefObject,
} from "framer-motion";

/** Depth of each plane, foreground → background. Drives sway + scroll drift. */
export const PLANE_DEPTHS = [0.35, 0.6, 1] as const;

type UseParallaxOptions = {
  /** Max px the deepest plane may travel from scroll or pointer. Default 20. */
  maxTravel?: number;
  /** Enable pointer parallax on fine pointers. Default true. */
  pointer?: boolean;
};

export type ParallaxPlane = {
  x: MotionValue<number>;
  y: MotionValue<number>;
};

export function useParallax(
  ref: RefObject<HTMLElement>,
  { maxTravel = 20, pointer = true }: UseParallaxOptions = {},
) {
  const reduce = useReducedMotion();

  const finePointer =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(pointer: fine)").matches;

  const enabled = !reduce;
  const pointerEnabled = enabled && pointer && finePointer;

  // ── Scroll signal: hero top→bottom maps to 0 … 1 ──
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });

  // ── Pointer signal: normalised -0.5 … 0.5 on each axis, spring-smoothed ──
  const pxRaw = useMotionValue(0);
  const pyRaw = useMotionValue(0);
  const px = useSpring(pxRaw, { stiffness: 90, damping: 20, mass: 0.6 });
  const py = useSpring(pyRaw, { stiffness: 90, damping: 20, mass: 0.6 });

  useEffect(() => {
    if (!pointerEnabled) return;
    const el = ref.current;
    if (!el) return;

    let frame = 0;
    const onMove = (e: PointerEvent) => {
      if (frame) return; // one update per animation frame
      frame = requestAnimationFrame(() => {
        frame = 0;
        const rect = el.getBoundingClientRect();
        pxRaw.set((e.clientX - rect.left) / rect.width - 0.5);
        pyRaw.set((e.clientY - rect.top) / rect.height - 0.5);
      });
    };
    const onLeave = () => {
      pxRaw.set(0);
      pyRaw.set(0);
    };

    el.addEventListener("pointermove", onMove, { passive: true });
    el.addEventListener("pointerleave", onLeave);
    return () => {
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [pointerEnabled, ref, pxRaw, pyRaw]);

  // ── Three fixed planes. Each useTransform is a stable top-level hook call. ──
  // x: pointer sway only. y: pointer sway + downward scroll drift.
  const p0x = useTransform(px, (v) => (pointerEnabled ? v * maxTravel * PLANE_DEPTHS[0] : 0));
  const p1x = useTransform(px, (v) => (pointerEnabled ? v * maxTravel * PLANE_DEPTHS[1] : 0));
  const p2x = useTransform(px, (v) => (pointerEnabled ? v * maxTravel * PLANE_DEPTHS[2] : 0));

  const p0y = useTransform(
    [py, scrollYProgress],
    ([pv, sv]: number[]) =>
      (pointerEnabled ? pv * maxTravel * PLANE_DEPTHS[0] : 0) +
      (enabled ? sv * maxTravel * PLANE_DEPTHS[0] : 0),
  );
  const p1y = useTransform(
    [py, scrollYProgress],
    ([pv, sv]: number[]) =>
      (pointerEnabled ? pv * maxTravel * PLANE_DEPTHS[1] : 0) +
      (enabled ? sv * maxTravel * PLANE_DEPTHS[1] : 0),
  );
  const p2y = useTransform(
    [py, scrollYProgress],
    ([pv, sv]: number[]) =>
      (pointerEnabled ? pv * maxTravel * PLANE_DEPTHS[2] : 0) +
      (enabled ? sv * maxTravel * PLANE_DEPTHS[2] : 0),
  );

  const planes: ParallaxPlane[] = [
    { x: p0x, y: p0y },
    { x: p1x, y: p1y },
    { x: p2x, y: p2y },
  ];

  return { planes, enabled, pointerEnabled };
}

export default useParallax;
