/**
 * Hero — Granola-inspired clean editorial hero for interviewer.ai.
 *
 * Large sans-serif headline on a warm cream background. No complex canvas
 * or aurora backdrop. Clean, organic, with subtle grain texture and
 * floating accent shapes. The highlight uses the editorial sans-serif
 * typeface for editorial gravitas.
 */
import { m as motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export type HeroCta = {
  label: string;
  to: string;
};

export type HeroProps = {
  /** Optional small badge shown above the headline */
  eyebrow?: string;
  /** Each entry is one visual line of the headline */
  headline: string[];
  /** Optional sans-highlighted final word/phrase appended after the lines */
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
    transition: { staggerChildren: 0.04, delayChildren: 0.1 },
  },
};

/** Each word rises + fades on the shared easing curve. */
const wordVariant = {
  hidden: { opacity: 0, y: "0.35em" },
  show: { opacity: 1, y: "0em", transition: { duration: 0.65, ease: EASE } },
};

/**
 * Editor mockup — the `editor.py` source is revealed one line at a time so it
 * reads like it's being typed live. The container waits for the mockup's own
 * entrance (delay 0.6 + 0.8s) to settle, then cascades each line in.
 */
const codeContainer = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.14, delayChildren: 1.05 },
  },
};

/** Each code line slides in from the left as it "types" onto the screen. */
const codeLineVariant = {
  hidden: { opacity: 0, x: -6 },
  show: { opacity: 1, x: 0, transition: { duration: 0.4, ease: EASE } },
};

/**
 * editor.py source — one entry per visual line, indent measured in `ch` units
 * (4 = one Python level). `node: null` renders a blank spacer line. Colours
 * mirror the previous static block so syntax highlighting is unchanged.
 */
const codeLines = [
  { indent: 0, node: (<><span className="text-brand font-bold">class</span> <span className="text-blue-600 dark:text-blue-400 font-bold">DistributedLedger</span>:</>) },
  { indent: 4, node: (<><span className="text-brand font-bold">def</span> <span className="text-yellow-600 dark:text-yellow-400">__init__</span>(self, nodes):</>) },
  { indent: 8, node: (<>self.nodes = nodes</>) },
  { indent: 8, node: (<>self.write_buffer = []</>) },
  { indent: 0, node: null },
  { indent: 4, node: (<><span className="text-brand font-bold">def</span> <span className="text-yellow-600 dark:text-yellow-400">batch_write</span>(self, transactions):</>) },
  { indent: 8, node: (<span className="text-muted-foreground"># Batch writes to reduce network overhead</span>) },
  { indent: 8, node: (<>self.write_buffer.extend(transactions)</>) },
  { indent: 8, node: (<><span className="text-brand font-bold">if</span> len(self.write_buffer) &gt;= 1000:</>) },
  { indent: 12, node: (<>self.flush_buffer()<motion.span aria-hidden className="ml-0.5 inline-block h-[1.05em] w-[2px] translate-y-[0.15em] bg-brand align-middle" initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0] }} transition={{ duration: 1, repeat: Infinity, ease: "linear", delay: 2.6 }} /></>) },
];

export default function Hero({
  eyebrow,
  headline,
  highlight,
  subtext,
  primaryCta,
  secondaryCta,
}: HeroProps) {
  return (
    <header className="relative isolate min-h-[90svh] w-full overflow-hidden bg-background font-sans">
      {/* Subtle ambient shapes — Granola-like organic blobs */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        {/* Warm glow top-right */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1, x: [0, 30, 0], y: [0, -20, 0] }}
          transition={{
            opacity: { duration: 2, ease: "easeOut" },
            scale: { duration: 2, ease: "easeOut" },
            x: { duration: 16, ease: "easeInOut", repeat: Infinity },
            y: { duration: 16, ease: "easeInOut", repeat: Infinity },
          }}
          className="absolute -right-[15%] -top-[10%] h-[600px] w-[600px] rounded-full bg-[radial-gradient(closest-side,hsl(var(--brand)/0.12),transparent)] blur-[80px]"
        />
        {/* Soft glow bottom-left */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1, x: [0, -25, 0], y: [0, 20, 0] }}
          transition={{
            opacity: { duration: 2, delay: 0.3, ease: "easeOut" },
            scale: { duration: 2, delay: 0.3, ease: "easeOut" },
            x: { duration: 20, ease: "easeInOut", repeat: Infinity },
            y: { duration: 20, ease: "easeInOut", repeat: Infinity },
          }}
          className="absolute -left-[10%] bottom-[5%] h-[500px] w-[500px] rounded-full bg-[radial-gradient(closest-side,hsl(var(--chart-5)/0.08),transparent)] blur-[100px]"
        />
        {/* Light grid texture, masked to centre */}
        <div className="absolute inset-0 opacity-[0.03] [background-image:linear-gradient(hsl(var(--foreground))_1px,transparent_1px),linear-gradient(90deg,hsl(var(--foreground))_1px,transparent_1px)] [background-size:48px_48px] [mask-image:radial-gradient(ellipse_at_center,black_20%,transparent_70%)]" />
        {/* Painterly grain */}
        <div className="absolute inset-0 opacity-[0.04] mix-blend-multiply [background-image:url(&quot;data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='240'%20height='240'%3E%3Cfilter%20id='n'%3E%3CfeTurbulence%20type='fractalNoise'%20baseFrequency='0.8'%20numOctaves='3'%20stitchTiles='stitch'/%3E%3C/filter%3E%3Crect%20width='100%25'%20height='100%25'%20filter='url(%23n)'/%3E%3C/svg%3E&quot;)] [background-size:200px_200px]" />
      </div>

      <div className="relative mx-auto flex min-h-[90svh] w-full max-w-[1100px] flex-col items-center justify-center px-6 text-center lg:px-10">
        <div className="h-24 shrink-0 md:h-28" aria-hidden="true" />

        <div className="flex flex-1 flex-col items-center justify-center pb-20">
          {eyebrow && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: EASE }}
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-background px-4 py-1.5 text-[13px] font-medium text-foreground/70"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-brand animate-pulse" />
              {eyebrow}
            </motion.div>
          )}

          <motion.h1
            variants={headlineContainer}
            initial="hidden"
            animate="show"
            className="max-w-[900px] text-foreground font-medium tracking-tight text-[clamp(2.75rem,7vw,5.25rem)] leading-[1.06]"
          >
            {headline.map((line, i) => (
              <span key={i} className="block">
                {line.split(" ").map((word, j) => (
                  <span key={j} className="inline-flex align-bottom">
                    <span className="inline-block -mb-[0.12em] overflow-hidden pb-[0.12em]">
                      <motion.span variants={wordVariant} className="inline-block">
                        {word}
                      </motion.span>
                    </span>
                    {j < line.split(" ").length - 1 && <span>&nbsp;</span>}
                  </span>
                ))}
              </span>
            ))}
            {highlight && (
              <span className="mt-1 block -mb-[0.14em] overflow-hidden pb-[0.14em]">
                <motion.span
                  variants={wordVariant}
                  className="inline-block font-sans font-normal italic tracking-[-0.01em] text-brand"
                >
                  {highlight}
                </motion.span>
              </span>
            )}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.35, ease: EASE }}
            className="mt-7 max-w-xl text-muted-foreground text-[17px] font-normal leading-relaxed md:text-lg"
          >
            {subtext}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45, ease: EASE }}
            className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center"
          >
            <Link
              to={primaryCta.to}
              className="group inline-flex h-12 items-center justify-center gap-2 rounded-full bg-foreground px-7 text-[15px] font-semibold text-background transition-all duration-300 hover:scale-[1.03] hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {primaryCta.label}
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            {secondaryCta && (
              <Link
                to={secondaryCta.to}
                className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-border px-7 text-[15px] font-semibold text-foreground transition-all duration-300 hover:bg-foreground/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {secondaryCta.label}
              </Link>
            )}
          </motion.div>

          {/* Trust signal — small note under CTAs, Granola-style */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            className="mt-5 text-[13px] text-muted-foreground/60 font-medium"
          >
            Open source · No credit card required
          </motion.p>

          {/* Mockup wrapper with premium landscape background (Granola-style) */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6, ease: EASE }}
            className="mt-16 w-full max-w-4xl rounded-3xl border border-border bg-card p-6 shadow-2xl relative overflow-hidden group"
          >
            {/* Diagonal shimmer sweep — periodic premium light pass */}
            <motion.div
              aria-hidden
              className="pointer-events-none absolute inset-0 z-20 -skew-x-12 bg-gradient-to-r from-transparent via-white/15 to-transparent"
              initial={{ x: "-150%" }}
              animate={{ x: "150%" }}
              transition={{ duration: 1.6, ease: "easeInOut", repeat: Infinity, repeatDelay: 5, delay: 2 }}
            />
            {/* Scenic Landscape Backdrop */}
            <div className="absolute inset-0 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=1200&q=80"
                alt=""
                aria-hidden="true"
                loading="lazy"
                decoding="async"
                className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.01]"
              />
              <div className="absolute inset-0 bg-black/40 backdrop-blur-[1.5px]" />
            </div>

            <div className="relative z-10 rounded-2xl border border-white/10 bg-background/95 backdrop-blur-md overflow-hidden flex flex-col shadow-2xl">
              {/* Browser chrome header */}
              <div className="h-10 bg-card/90 border-b border-border/80 flex items-center px-4 gap-2.5">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/20 group-hover:bg-red-500 transition-colors" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/20 group-hover:bg-yellow-500 transition-colors" />
                  <div className="w-3 h-3 rounded-full bg-green-500/20 group-hover:bg-green-500 transition-colors" />
                </div>
                <div className="flex-1 max-w-sm mx-auto h-6 bg-background/80 rounded-md border border-border/60 flex items-center justify-center text-[10px] text-muted-foreground/80 font-mono tracking-tight select-none">
                  interviewer.ai/session/active
                </div>
                <div className="w-12" /> {/* spacer */}
              </div>

              {/* Workspace interface */}
              <div className="grid md:grid-cols-5 h-[340px] md:h-[400px]">
                {/* Left: AI/Webcam panel */}
                <div className="md:col-span-2 border-b md:border-b-0 md:border-r border-border/80 p-5 flex flex-col justify-between bg-card/25 relative overflow-hidden">
                  <div className="absolute inset-0 opacity-40 mix-blend-overlay">
                    <img
                      src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=800&q=80"
                      alt="Interviewer"
                      loading="lazy"
                      decoding="async"
                      className="w-full h-full object-cover filter saturate-[0.85] contrast-[1.05]"
                    />
                  </div>
                  <div className="relative z-10 flex justify-between items-start">
                    <span className="bg-red-500/10 text-red-600 rounded-full text-[10px] font-bold px-2.5 py-0.5 flex items-center gap-1 border border-red-500/20 select-none">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> LIVE
                    </span>
                    <span className="bg-black/60 backdrop-blur-md text-white rounded-md text-[9px] font-semibold px-2 py-0.5 select-none">
                      AI Interviewer
                    </span>
                  </div>

                  <div className="relative z-10 mt-auto bg-black/60 backdrop-blur-md rounded-xl p-3 border border-white/10 text-left">
                    <p className="text-[10px] text-white/60 font-semibold uppercase tracking-wider mb-1 select-none">Current Question</p>
                    <p className="text-xs text-white/95 leading-relaxed font-sans font-medium">
                      "How would you optimize the write throughput of a globally distributed ledger system?"
                    </p>
                  </div>
                </div>

                {/* Right: Code / Whiteboard workspace */}
                <div className="md:col-span-3 p-5 flex flex-col justify-between bg-background text-left relative">
                  <div className="flex items-center justify-between border-b border-border/80 pb-3 mb-3 select-none">
                    <span className="text-xs font-semibold text-foreground/80 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-brand animate-pulse" /> editor.py
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground bg-card px-2 py-0.5 rounded border border-border/60">
                      Python 3.10
                    </span>
                  </div>

                  <motion.div
                    variants={codeContainer}
                    initial="hidden"
                    animate="show"
                    className="flex-1 font-mono text-[11px] leading-relaxed text-foreground/90 overflow-hidden"
                  >
                    {codeLines.map((line, i) => (
                      <motion.div
                        key={i}
                        variants={codeLineVariant}
                        className="min-h-[1.35em] whitespace-pre"
                        style={{ paddingLeft: `${line.indent}ch` }}
                      >
                        {line.node ?? " "}
                      </motion.div>
                    ))}
                  </motion.div>
                  <div className="border-t border-border/80 pt-3 mt-3 flex items-center justify-between text-[10px] font-mono text-muted-foreground select-none">
                    <span>Lines: 12  Chars: 312</span>
                    <span className="text-brand font-semibold bg-brand/10 px-2 py-0.5 rounded-full">
                      Auto-saving...
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </header>
  );
}
