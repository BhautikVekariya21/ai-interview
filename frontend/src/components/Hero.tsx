/**
 * Hero — a clean, modern aurora-gradient hero for interviewer.ai.
 *
 * No photograph, no trust badges, no company logos. Just a bold headline over a
 * layered, parallax aurora backdrop driven by the app's brand tokens, with two
 * CTAs. Content is prop-driven so the same component can back multiple campaigns.
 *
 * The backdrop and signature "Resume → Insight" motif live in `HeroCanvas`,
 * which reads scroll + pointer from this header via a ref. The headline reveals
 * per word with a shared aurora easing; the optional `highlight` phrase is set
 * in the Fraunces display serif as the single editorial accent on the page.
 * Everything degrades to a calm, static state under `prefers-reduced-motion`.
 */
import { useRef } from "react";
import { m as motion } from "framer-motion";
import { Link } from "react-router-dom";

import HeroCanvas from "./hero/HeroCanvas";

export type HeroCta = {
  label: string;
  to: string;
};

export type HeroProps = {
  /** Optional small badge shown above the headline */
  eyebrow?: string;
  /** Each entry is one visual line of the headline */
  headline: string[];
  /** Optional serif-highlighted final word/phrase appended after the lines */
  highlight?: string;
  subtext: string;
  primaryCta: HeroCta;
  secondaryCta?: HeroCta;
};

const EASE = [0.16, 1, 0.3, 1] as const;

/** Container that staggers its children (words) into view. */
const headlineContainer = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.055, delayChildren: 0.08 },
  },
};

/** Each word rises + fades on the shared aurora curve. */
const wordVariant = {
  hidden: { opacity: 0, y: "0.5em" },
  show: { opacity: 1, y: "0em", transition: { duration: 0.7, ease: EASE } },
};

export default function Hero({
  eyebrow,
  headline,
  highlight,
  subtext,
  primaryCta,
  secondaryCta,
}: HeroProps) {
  const headerRef = useRef<HTMLElement>(null);

  return (
    <header
      ref={headerRef}
      className="relative isolate min-h-[92svh] w-full overflow-hidden bg-background font-sans"
    >
      {/* Signature parallax aurora + Resume→Insight motif */}
      <HeroCanvas target={headerRef} />

      <div className="relative mx-auto flex min-h-[92svh] w-full max-w-[1400px] flex-col items-center justify-center px-6 text-center lg:px-12">
        <div className="h-24 shrink-0 md:h-28" aria-hidden="true" />

        <div className="flex flex-1 flex-col items-center justify-center pb-16">
          {eyebrow && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: EASE }}
              className="glass mb-6 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-[13px] font-semibold text-foreground/90"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-brand" />
              {eyebrow}
            </motion.div>
          )}

          <motion.h1
            variants={headlineContainer}
            initial="hidden"
            animate="show"
            className="max-w-4xl text-foreground font-semibold tracking-tight text-[clamp(2.75rem,7vw,5rem)] leading-[1.02]"
          >
            {headline.map((line, i) => (
              <span key={i} className="block">
                {line.split(" ").map((word, j) => (
                  // Each word gets an inline-block wrapper so the y-lift clips
                  // cleanly per word; the trailing space keeps natural spacing.
                  <span
                    key={j}
                    className="inline-block -mb-[0.14em] overflow-hidden pb-[0.14em] align-bottom"
                  >
                    <motion.span variants={wordVariant} className="inline-block">
                      {word}
                    </motion.span>
                    {j < line.split(" ").length - 1 && " "}
                  </span>
                ))}
              </span>
            ))}
            {highlight && (
              <span className="mt-1 block -mb-[0.16em] overflow-hidden pb-[0.16em]">
                <motion.span
                  variants={wordVariant}
                  className="inline-block bg-gradient-to-r from-brand to-[hsl(var(--chart-3))] bg-clip-text font-serif font-medium italic tracking-[-0.01em] text-transparent"
                >
                  {highlight}
                </motion.span>
              </span>
            )}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.35, ease: EASE }}
            className="mt-7 max-w-2xl text-muted-foreground text-lg font-normal leading-relaxed md:text-xl"
          >
            {subtext}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45, ease: EASE }}
            className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center"
          >
            <Link
              to={primaryCta.to}
              className="inline-flex h-12 items-center justify-center rounded-xl bg-brand px-7 text-[15px] font-semibold text-brand-foreground shadow-[0_8px_30px_-8px_hsl(var(--brand)/0.6)] transition-transform duration-200 hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--brand-ring))]"
            >
              {primaryCta.label}
            </Link>
            {secondaryCta && (
              <Link
                to={secondaryCta.to}
                className="glass inline-flex h-12 items-center justify-center rounded-xl px-7 text-[15px] font-semibold text-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30"
              >
                {secondaryCta.label}
              </Link>
            )}
          </motion.div>
        </div>
      </div>
    </header>
  );
}
