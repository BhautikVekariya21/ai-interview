/**
 * Hero — a clean, modern aurora-gradient hero for interviewer.ai.
 *
 * No photograph, no trust badges, no company logos. Just a bold headline over a
 * layered aurora glow driven by the app's brand tokens, with two CTAs. Content
 * is prop-driven so the same component can back multiple campaigns.
 */
import { m as motion } from "framer-motion";
import { Link } from "react-router-dom";

export type HeroCta = {
  label: string;
  to: string;
};

export type HeroProps = {
  /** Optional small badge shown above the headline */
  eyebrow?: string;
  /** Each entry is one visual line of the headline */
  headline: string[];
  /** Optional gradient-highlighted final word/phrase appended after the lines */
  highlight?: string;
  subtext: string;
  primaryCta: HeroCta;
  secondaryCta?: HeroCta;
};

const EASE = [0.16, 1, 0.3, 1] as const;

export default function Hero({
  eyebrow,
  headline,
  highlight,
  subtext,
  primaryCta,
  secondaryCta,
}: HeroProps) {
  return (
    <header className="relative isolate min-h-[92svh] w-full overflow-hidden bg-background font-sans">
      {/* Painterly, hand-painted-style background */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        {/* Watercolor wash blobs — soft, brushed color fields */}
        <div className="absolute left-1/2 top-[-16%] h-[680px] w-[900px] -translate-x-1/2 rounded-[50%] bg-[radial-gradient(closest-side,hsl(var(--brand)/0.42),transparent)] blur-[110px]" />
        <div className="absolute right-[-8%] top-[4%] h-[560px] w-[560px] rounded-[46%_54%_60%_40%] bg-[radial-gradient(closest-side,hsl(var(--chart-3)/0.34),transparent)] blur-[120px]" />
        <div className="absolute left-[-10%] bottom-[-16%] h-[600px] w-[600px] rounded-[60%_40%_45%_55%] bg-[radial-gradient(closest-side,hsl(var(--chart-2)/0.30),transparent)] blur-[130px]" />
        <div className="absolute left-[18%] top-[30%] h-[380px] w-[380px] rounded-[55%_45%_50%_50%] bg-[radial-gradient(closest-side,hsl(var(--chart-4)/0.22),transparent)] blur-[100px]" />
        {/* Brush-stroke sweep across the canvas */}
        <div className="absolute inset-0 opacity-70 [background:conic-gradient(from_210deg_at_60%_40%,transparent,hsl(var(--brand)/0.10),transparent_35%,hsl(var(--chart-3)/0.08),transparent_70%)] blur-[40px]" />
        {/* Painterly grain — SVG turbulence gives a canvas/paper texture */}
        <div className="absolute inset-0 opacity-[0.12] mix-blend-soft-light [background-image:url(&quot;data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='240'%20height='240'%3E%3Cfilter%20id='n'%3E%3CfeTurbulence%20type='fractalNoise'%20baseFrequency='0.9'%20numOctaves='3'%20stitchTiles='stitch'/%3E%3C/filter%3E%3Crect%20width='100%25'%20height='100%25'%20filter='url(%23n)'/%3E%3C/svg%3E&quot;)] [background-size:220px_220px]" />
        {/* Grid texture */}
        <div className="absolute inset-0 opacity-[0.06] [background-image:linear-gradient(hsl(var(--foreground))_1px,transparent_1px),linear-gradient(90deg,hsl(var(--foreground))_1px,transparent_1px)] [background-size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />
        {/* Legibility wash so the headline stays readable */}
        <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/40 to-background" />
      </div>

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
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.75, delay: 0.05, ease: EASE }}
            className="max-w-4xl text-foreground font-semibold tracking-tight text-[clamp(2.75rem,7vw,5rem)] leading-[1.02]"
          >
            {headline.map((line, i) => (
              <span key={i} className="block">
                {line}
              </span>
            ))}
            {highlight && (
              <span className="block bg-gradient-to-r from-brand to-[hsl(var(--chart-3))] bg-clip-text text-transparent">
                {highlight}
              </span>
            )}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15, ease: EASE }}
            className="mt-7 max-w-2xl text-muted-foreground text-lg font-normal leading-relaxed md:text-xl"
          >
            {subtext}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25, ease: EASE }}
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
