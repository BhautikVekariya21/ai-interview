/**
 * HeroCanvas — the signature ambient backdrop for the hero.
 *
 * Two cooperating layers, both purely decorative (aria-hidden) and driven only
 * by transforms/opacity so they stay on the compositor:
 *
 *   1. Parallax aurora — three depth planes of soft brushed colour fields that
 *      drift on scroll and sway to the pointer (desktop, fine-pointer only).
 *      Travel is capped to ~20px by `useParallax`, so it reads as depth rather
 *      than movement, and stands fully down under `prefers-reduced-motion`.
 *
 *   2. "Resume → Insight" motif — a slow, looping SVG that shows résumé lines
 *      elegantly dissolving into a glowing confidence waveform terminating in
 *      verified claim nodes. This is the brand's core promise, rendered.
 *
 * The whole thing sits behind the hero content at `-z-10` and never intercepts
 * pointer events. When motion is reduced the SVG renders its resolved final
 * state (waveform + lit nodes) with no animation.
 */
import { useRef } from "react";
import { m as motion, useReducedMotion } from "framer-motion";

import { useParallax } from "./useParallax";

type HeroCanvasProps = {
  /** The hero element to measure for scroll + pointer parallax. */
  target: React.RefObject<HTMLElement>;
  className?: string;
};

export default function HeroCanvas({ target, className = "" }: HeroCanvasProps) {
  const reduce = useReducedMotion();
  const { planes } = useParallax(target, { maxTravel: 20 });

  return (
    <div
      aria-hidden
      className={`pointer-events-none absolute inset-0 -z-10 overflow-hidden ${className}`}
    >
      {/* ── Plane 3 (deepest): the broad brand wash, moves most ── */}
      <motion.div
        style={{ x: planes[2].x, y: planes[2].y }}
        className="absolute inset-0 will-change-transform"
      >
        <div className="absolute left-1/2 top-[-18%] h-[720px] w-[960px] -translate-x-1/2 rounded-[50%] bg-[radial-gradient(closest-side,hsl(var(--brand)/0.40),transparent)] blur-[120px]" />
        <div className="absolute left-[-12%] bottom-[-20%] h-[640px] w-[640px] rounded-[60%_40%_45%_55%] bg-[radial-gradient(closest-side,hsl(var(--chart-2)/0.30),transparent)] blur-[140px]" />
      </motion.div>

      {/* ── Plane 2 (mid): cooler accents, moderate drift ── */}
      <motion.div
        style={{ x: planes[1].x, y: planes[1].y }}
        className="absolute inset-0 will-change-transform"
      >
        <div className="absolute right-[-10%] top-[2%] h-[600px] w-[600px] rounded-[46%_54%_60%_40%] bg-[radial-gradient(closest-side,hsl(var(--chart-3)/0.32),transparent)] blur-[130px]" />
        <div className="absolute left-[16%] top-[28%] h-[400px] w-[400px] rounded-[55%_45%_50%_50%] bg-[radial-gradient(closest-side,hsl(var(--chart-4)/0.22),transparent)] blur-[110px]" />
      </motion.div>

      {/* ── Plane 1 (foreground): the signature motif, moves least ── */}
      <motion.div
        style={{ x: planes[0].x, y: planes[0].y }}
        className="absolute inset-0 will-change-transform"
      >
        <ResumeToInsight reduce={!!reduce} />
      </motion.div>

      {/* Brush-stroke sweep — static, ties the planes together */}
      <div className="absolute inset-0 opacity-70 [background:conic-gradient(from_210deg_at_60%_40%,transparent,hsl(var(--brand)/0.10),transparent_35%,hsl(var(--chart-3)/0.08),transparent_70%)] blur-[40px]" />
      {/* Painterly grain */}
      <div className="absolute inset-0 opacity-[0.12] mix-blend-soft-light [background-image:url(&quot;data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='240'%20height='240'%3E%3Cfilter%20id='n'%3E%3CfeTurbulence%20type='fractalNoise'%20baseFrequency='0.9'%20numOctaves='3'%20stitchTiles='stitch'/%3E%3C/filter%3E%3Crect%20width='100%25'%20height='100%25'%20filter='url(%23n)'/%3E%3C/svg%3E&quot;)] [background-size:220px_220px]" />
      {/* Grid texture, masked to the centre */}
      <div className="absolute inset-0 opacity-[0.06] [background-image:linear-gradient(hsl(var(--foreground))_1px,transparent_1px),linear-gradient(90deg,hsl(var(--foreground))_1px,transparent_1px)] [background-size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />
      {/* Legibility wash so the headline stays readable over everything */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/40 to-background" />
    </div>
  );
}

/**
 * ResumeToInsight — the looping SVG. Positioned to the upper-right so it frames
 * rather than fights the centred headline. Built from three motion groups:
 * résumé lines that fade, a waveform that draws itself, and claim nodes that
 * light up in sequence — then the whole cycle repeats.
 */
function ResumeToInsight({ reduce }: { reduce: boolean }) {
  // Confidence waveform path — a calm, rising signal.
  const wave =
    "M8 60 C 40 60, 52 30, 84 30 S 132 78, 164 60 S 214 20, 252 40 S 300 66, 344 44";
  const nodes = [
    { cx: 164, cy: 60, d: 0 },
    { cx: 252, cy: 40, d: 0.5 },
    { cx: 344, cy: 44, d: 1 },
  ];

  return (
    <div className="absolute right-[4%] top-[16%] hidden w-[min(46vw,560px)] max-w-[560px] opacity-90 lg:block xl:right-[7%]">
      <svg
        viewBox="0 0 360 120"
        fill="none"
        className="h-auto w-full overflow-visible"
        role="presentation"
      >
        <defs>
          <linearGradient id="hc-wave" x1="0" y1="0" x2="360" y2="0" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="hsl(var(--brand))" />
            <stop offset="0.55" stopColor="hsl(var(--chart-3))" />
            <stop offset="1" stopColor="hsl(var(--chart-4))" />
          </linearGradient>
          <filter id="hc-glow" x="-40%" y="-60%" width="180%" height="220%">
            <feGaussianBlur stdDeviation="3.2" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Résumé lines — fade out as the insight resolves */}
        <motion.g
          stroke="hsl(var(--foreground))"
          strokeWidth="3"
          strokeLinecap="round"
          initial={false}
          animate={reduce ? { opacity: 0.12 } : { opacity: [0.42, 0.42, 0.08, 0.42] }}
          transition={
            reduce
              ? undefined
              : { duration: 9, times: [0, 0.25, 0.55, 1], repeat: Infinity, ease: "easeInOut" }
          }
        >
          <line x1="8" y1="20" x2="120" y2="20" opacity="0.9" />
          <line x1="8" y1="38" x2="96" y2="38" opacity="0.6" />
          <line x1="8" y1="56" x2="112" y2="56" opacity="0.75" />
          <line x1="8" y1="74" x2="72" y2="74" opacity="0.5" />
          <line x1="8" y1="92" x2="104" y2="92" opacity="0.65" />
        </motion.g>

        {/* Confidence waveform — draws itself, then holds */}
        <motion.path
          d={wave}
          stroke="url(#hc-wave)"
          strokeWidth="3.25"
          strokeLinecap="round"
          filter="url(#hc-glow)"
          initial={false}
          animate={reduce ? { pathLength: 1, opacity: 1 } : { pathLength: [0, 1, 1, 0], opacity: [0.2, 1, 1, 0.2] }}
          transition={
            reduce
              ? undefined
              : { duration: 9, times: [0, 0.45, 0.85, 1], repeat: Infinity, ease: "easeInOut" }
          }
        />

        {/* Verified claim nodes — light up in sequence along the signal */}
        {nodes.map((n, i) => (
          <motion.g
            key={i}
            initial={false}
            animate={
              reduce
                ? { opacity: 1, scale: 1 }
                : { opacity: [0, 0, 1, 1, 0], scale: [0.4, 0.4, 1, 1, 0.4] }
            }
            transition={
              reduce
                ? undefined
                : {
                    duration: 9,
                    times: [0, 0.5 + n.d * 0.08, 0.62 + n.d * 0.08, 0.85, 1],
                    repeat: Infinity,
                    ease: "easeOut",
                  }
            }
            style={{ transformOrigin: `${n.cx}px ${n.cy}px` }}
          >
            <circle cx={n.cx} cy={n.cy} r="7.5" fill="hsl(var(--chart-3)/0.16)" />
            <circle cx={n.cx} cy={n.cy} r="4" fill="hsl(var(--chart-3))" filter="url(#hc-glow)" />
            {/* Verified check */}
            <path
              d={`M${n.cx - 2.1} ${n.cy} l1.6 1.7 l2.9 -3.3`}
              stroke="hsl(var(--background))"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </motion.g>
        ))}
      </svg>
    </div>
  );
}
