import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Upload, Cpu, LineChart } from "lucide-react";
import { FadeUp, PulseSection } from "@/components/sections/FeatureSections";
import SpotlightCard from "@/components/cards/SpotlightCard";

const steps = [
  {
    icon: Upload,
    title: "Upload your resume",
    text: "Drop in a PDF and pick a target role. The AI reads your real experience and skill level.",
  },
  {
    icon: Cpu,
    title: "Run a proctored interview",
    text: "Resume-grounded questions, a live coding environment, and anti-cheat proctoring simulate real pressure.",
  },
  {
    icon: LineChart,
    title: "Get a deep readout",
    text: "Scores, filler-word heatmaps, confidence pulse, and ideal-answer mapping — so you know exactly what to fix.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-[1400px]">
      <FadeUp>
        <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-brand">How it works</p>
        <h1 className="mt-3 text-4xl md:text-5xl lg:text-[3.75rem] font-semibold tracking-tight text-foreground leading-[1.05]">
          Three steps to a rerun of the real thing.
        </h1>
      </FadeUp>

      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {steps.map(({ icon: Icon, title, text }, i) => (
          <FadeUp key={title} delay={i * 0.1}>
            <SpotlightCard className="h-full">
              <div className="flex h-full flex-col rounded-3xl p-8">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-11 h-11 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                    <Icon className="w-5 h-5" strokeWidth={2} />
                  </div>
                  <span className="text-3xl font-bold text-brand/40">{String(i + 1).padStart(2, "0")}</span>
                </div>
                <h3 className="text-xl font-bold mb-2 text-foreground">{title}</h3>
                <p className="text-foreground/70 text-[16px] font-medium leading-relaxed">{text}</p>
              </div>
            </SpotlightCard>
          </FadeUp>
        ))}
      </div>

      <div className="-mx-6 lg:-mx-12 mt-6">
        <PulseSection id="how-pulse" />
      </div>

      <FadeUp className="flex flex-col items-start gap-4 border-t border-border pt-12 pb-8">
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">See it on your own resume.</h2>
        <Button asChild size="lg" className="h-12 rounded-xl px-7 font-bold bg-brand text-brand-foreground hover:bg-brand-hover">
          <Link to="/auth?mode=signup">Start free — no card</Link>
        </Button>
      </FadeUp>
    </div>
  );
}
