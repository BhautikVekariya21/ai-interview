import { Code, Cpu, LineChart, MousePointer, AppWindow, Network } from "lucide-react";
import Reveal from "@/components/motion/Reveal";

/**
 * FadeUp — retained as the section-local alias for the shared `Reveal` primitive.
 *
 * Every existing call site keeps working unchanged; the animation, easing, and
 * viewport behaviour now come from `Reveal` (fade + 24px rise, fires once,
 * reduced-motion aware) so there's a single source of truth for scroll reveals.
 */
export function FadeUp({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <Reveal delay={delay} className={className}>
      {children}
    </Reveal>
  );
}

/* ── FEATURE 1: Real-time Proctoring ── */
export function ProctoringSection({ id = "features" }: { id?: string }) {
  return (
    <section id={id} className="py-24 px-6 max-w-[1400px] mx-auto lg:px-12">
      <FadeUp>
        <h2 className="text-4xl md:text-5xl lg:text-[4rem] font-semibold tracking-tight mb-5 text-foreground">Real-time Proctoring</h2>
        <p className="text-xl md:text-[22px] text-foreground/70 font-medium leading-relaxed mb-12 max-w-3xl">
          Turn any job description into a high-pressure interview environment packed with algorithmic analysis and anti-cheat tracking.
        </p>
      </FadeUp>

      <div className="rounded-[2.5rem] border border-border flex flex-col lg:flex-row relative bg-transparent overflow-hidden">
        <div className="w-full lg:w-[45%] p-10 lg:p-14 lg:pr-16 border-b lg:border-b-0 lg:border-r border-border flex flex-col justify-start">
          <FadeUp className="mb-8 lg:mb-12 mt-6 lg:mt-12">
            <div className="text-[11px] font-semibold text-muted-foreground mb-4 tracking-widest pl-1 uppercase">Environment Check</div>
            <div className="bg-muted/50 rounded-[1.5rem] p-7 shadow-sm border border-border text-foreground font-medium leading-relaxed text-[17px] lg:text-[19px]">
              "Camera active. Proctoring secured. Generating systems design constraints tailored to your uploaded backend engineering resume."
            </div>
          </FadeUp>

          <div className="space-y-8 lg:space-y-12 pb-12 lg:pb-16">
            <FeatureRow icon={Code} title="Code Complexity Engine" text="Real-time interactive environments that execute your syntax and aggressively grade your algorithmic space & time complexity efficiency." />
            <FeatureRow icon={Cpu} title="Strict Anti-Cheat Proctoring" text="Simulate true pressure. Our platform actively monitors tab-switching, fullscreen exits, and dev-tools access to ensure clinical accuracy." />
            <FeatureRow icon={Network} title="Resume-Grounded Prompts" text="Every scenario is dynamically synthesized entirely from your explicit PDF history and matched aggressively against your target job." />
          </div>
        </div>

        <div className="hidden lg:flex w-full lg:w-[55%] relative items-center justify-center bg-card/30 backdrop-blur-sm">
          <div className="sticky top-12 h-[calc(100vh-6rem)] max-h-[800px] min-h-[500px] w-full flex items-center justify-center p-12">
            <FadeUp className="w-full">
              <div className="bg-muted/50 rounded-[2rem] p-6 md:p-8 aspect-square relative shadow-inner overflow-hidden border border-border transition-transform duration-500 w-full hover:shadow-2xl hover:scale-[1.02]">
                <div className="absolute top-8 left-8 right-8 bottom-8 bg-card/90 backdrop-blur-md rounded-2xl shadow-xl border border-border flex flex-col overflow-hidden">
                  <div className="h-10 bg-muted/30 border-b border-border flex items-center px-4 gap-2 shrink-0">
                    <div className="flex gap-1.5">
                      <div className="w-3 h-3 rounded-xl bg-muted-foreground/30" />
                      <div className="w-3 h-3 rounded-xl bg-muted-foreground/30" />
                      <div className="w-3 h-3 rounded-xl bg-muted-foreground/30" />
                    </div>
                    <div className="flex gap-2 mx-auto">
                      <div className="bg-red-500/20 text-red-700 rounded text-[10px] font-bold px-2 py-0.5 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> RECORDING
                      </div>
                      <div className="bg-muted/50 rounded text-[10px] font-bold px-2 py-0.5 text-muted-foreground">PROCTORING ACTIVE</div>
                    </div>
                  </div>
                  <div className="flex-1 p-6 flex flex-col gap-4 relative">
                    <div className="absolute top-6 right-6 w-16 h-12 bg-muted/50 border border-border rounded-lg shadow-sm overflow-hidden flex flex-col items-center justify-center">
                      <div className="w-4 h-4 rounded-full bg-muted-foreground/30 mb-1" />
                      <div className="w-8 h-3 rounded-t-xl bg-muted-foreground/30" />
                    </div>
                    <div className="w-1/2 h-4 bg-muted rounded-xl" />
                    <div className="w-full bg-foreground rounded-xl font-mono text-[10px] p-4 leading-relaxed relative overflow-hidden">
                      <div className="text-white/60 mb-2"># Submitting graph traversal...</div>
                      <span className="text-green-400">def</span> <span className="text-blue-300">find_path</span>(grid):<br/>
                      &nbsp;&nbsp;&nbsp;&nbsp;visited = set()<br/>
                      &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-yellow-400"># O(N^2) Space Complexity Warning</span><br/>
                      <div className="mt-4 border-t border-white/20 pt-2 flex justify-between text-white/50">
                        <span>Runtime: 42ms</span>
                        <span className="text-red-400 font-bold bg-red-500/20 px-1 rounded">WARN: N^2 SPACE</span>
                      </div>
                    </div>
                    <div className="w-1/2 h-3 bg-muted/50 rounded-xl mt-auto" />
                  </div>
                </div>
              </div>
            </FadeUp>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── FEATURE 2: Vocal Confidence & Pulse Metrics ── */
export function PulseSection({ id = "how-it-works" }: { id?: string }) {
  return (
    <section id={id} className="py-24 px-6 max-w-[1400px] mx-auto lg:px-12">
      <FadeUp className="flex flex-col lg:items-end lg:text-right">
        <h2 className="text-4xl md:text-5xl lg:text-[4rem] font-semibold tracking-tight mb-5 text-foreground">Vocal Confidence & Pulse Metrics</h2>
        <p className="text-xl md:text-[22px] text-foreground/70 font-medium leading-relaxed mb-12 max-w-3xl">
          Track real-time baseline fluctuations in your vocal authority and strip away demographics for absolute objective rubric scoring.
        </p>
      </FadeUp>

      <div className="rounded-[2.5rem] border border-border flex flex-col lg:flex-row relative bg-transparent overflow-hidden">
        <div className="hidden lg:flex w-full lg:w-[55%] relative items-center justify-center bg-card/30 backdrop-blur-sm border-b lg:border-b-0 lg:border-r border-border">
          <div className="sticky top-12 h-[calc(100vh-6rem)] max-h-[800px] min-h-[500px] w-full flex items-center justify-center p-12">
            <FadeUp className="w-full">
              <div className="bg-muted/50 rounded-[2rem] p-6 md:p-8 aspect-square relative shadow-inner overflow-hidden border border-border transition-transform duration-500 w-full hover:shadow-2xl hover:scale-[1.02]">
                <div className="absolute top-12 left-6 right-6 bottom-0 bg-card shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)] rounded-t-2xl border-x border-t border-border flex flex-col pt-6 px-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="h-6 w-1/3 bg-muted rounded-xl" />
                    <div className="bg-green-100/50 border border-green-500/20 text-green-700 text-[9px] font-bold px-2 py-1 rounded-lg ml-auto whitespace-nowrap">BIAS-FREE MODE</div>
                  </div>
                  <div className="flex gap-4 mb-6">
                    <div className="w-16 h-16 rounded-xl border-[4px] border-brand flex flex-col items-center justify-center font-bold text-foreground shrink-0 relative overflow-hidden bg-muted/30">
                      <span className="text-xl leading-none mb-0.5 text-foreground">160</span>
                      <span className="text-[8px] text-foreground/70 font-semibold tracking-widest">WPM</span>
                      <div className="absolute top-0 right-0 w-2 h-2 bg-red-400 rounded-bl-lg" />
                    </div>
                    <div className="flex-1 flex gap-1.5 items-end h-16 pb-1">
                      <div className="w-full h-[40%] bg-muted rounded-t-sm transition-all hover:bg-muted-foreground/30" />
                      <div className="w-full h-[60%] bg-muted rounded-t-sm transition-all hover:bg-muted-foreground/30" />
                      <div className="w-full h-[85%] bg-foreground rounded-t-sm relative transition-all group">
                        <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-brand text-brand-foreground text-[9px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-xl">uhm</div>
                      </div>
                      <div className="w-full h-[95%] bg-foreground rounded-t-sm relative transition-all group">
                        <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-brand text-brand-foreground text-[9px] font-semibold px-2 py-1 rounded shadow-xl whitespace-nowrap">uhm</div>
                      </div>
                      <div className="w-full h-[50%] bg-muted rounded-t-sm transition-all hover:bg-muted-foreground/30" />
                      <div className="w-full h-[70%] bg-muted-foreground/50 rounded-t-sm relative transition-all group">
                        <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-brand text-brand-foreground text-[9px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-xl">like</div>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 bg-muted/30 rounded-t-xl border-x border-t border-border p-4 flex flex-col gap-3">
                    <div className="text-[10px] font-bold text-muted-foreground tracking-wider">FILLER WORD ANALYSIS</div>
                    <div className="space-y-3">
                      <div className="h-2.5 w-full bg-muted/50 rounded-xl overflow-hidden flex shadow-inner">
                        <div className="w-[30%] bg-foreground h-full rounded-r-xl" />
                      </div>
                      <div className="h-2.5 w-5/6 bg-muted/50 rounded-xl overflow-hidden flex shadow-inner">
                        <div className="w-[15%] bg-muted-foreground/50 h-full rounded-r-xl" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </FadeUp>
          </div>
        </div>

        <div className="w-full lg:w-[45%] p-10 lg:p-14 lg:pl-16 flex flex-col justify-start bg-card">
          <FadeUp className="mb-8 lg:mb-12 mt-6 lg:mt-12">
            <div className="text-[11px] font-semibold text-muted-foreground mb-4 tracking-widest pl-1 uppercase">Pulse Report</div>
            <div className="bg-card rounded-[1.5rem] p-7 shadow-sm border border-border text-foreground font-medium leading-relaxed text-[17px] lg:text-[19px]">
              "Analysis complete: Detected 14 instances of conversational stumbles pacing above 160 WPM during the systems design whiteboard segment."
            </div>
          </FadeUp>

          <div className="space-y-8 lg:space-y-12 pb-12 lg:pb-16">
            <FeatureRow icon={LineChart} title="Speech Trajectory Heatmaps" text="Identify exact chronological conversational stumbles with highly precise filler word tracking and speaking pace analytics." />
            <FeatureRow icon={MousePointer} title="Bias-Free Results" text="Strip away demographic variables using our blind-evaluation switch for perfectly objective, rubric-driven scoring matrices." />
            <FeatureRow icon={AppWindow} title="Ideal Answer Mapping" text="Compare your algorithmic stumbling blocks directly against statically generated optimal path solutions for instant correction." />
          </div>
        </div>
      </div>
    </section>
  );
}

function FeatureRow({ icon: Icon, title, text }: { icon: typeof Code; title: string; text: string }) {
  return (
    <FadeUp>
      <div className="flex gap-6 items-start">
        <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
          <Icon className="w-6 h-6" strokeWidth={2} />
        </div>
        <div>
          <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">{title}</h4>
          <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">{text}</p>
        </div>
      </div>
    </FadeUp>
  );
}
