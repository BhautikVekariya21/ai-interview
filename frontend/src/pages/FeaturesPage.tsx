import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FadeUp, ProctoringSection } from "@/components/sections/FeatureSections";

export default function FeaturesPage() {
  return (
    <div className="mx-auto max-w-[1400px]">
      <FadeUp>
        <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-brand">Features</p>
        <h1 className="mt-3 text-4xl md:text-5xl lg:text-[3.75rem] font-semibold tracking-tight text-foreground leading-[1.05]">
          Everything you need to walk in prepared.
        </h1>
        <p className="mt-5 max-w-2xl text-lg md:text-xl text-foreground/70 font-medium leading-relaxed">
          A hyper-realistic AI interviewer that reads your resume, grades your complexity, traces
          your speech in real time, and proctors the room.
        </p>
      </FadeUp>

      <div className="-mx-6 lg:-mx-12">
        <ProctoringSection id="features-proctoring" />
      </div>

      <FadeUp className="flex flex-col items-start gap-4 border-t border-border pt-12 pb-8">
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Ready to try it?</h2>
        <Button asChild size="lg" className="h-12 rounded-xl px-7 font-bold bg-brand text-brand-foreground hover:bg-brand-hover">
          <Link to="/auth?mode=signup">Start free — no card</Link>
        </Button>
      </FadeUp>
    </div>
  );
}
