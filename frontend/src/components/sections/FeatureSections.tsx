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
    <section id={id} className="py-24 px-6 max-w-[1100px] mx-auto lg:px-10">
      <FadeUp>
        <h2 className="text-4xl md:text-5xl lg:text-[3.5rem] font-medium tracking-tight mb-4 text-foreground">Real-time Proctoring</h2>
        <p className="text-lg md:text-[19px] text-muted-foreground leading-relaxed mb-12 max-w-3xl">
          Turn any job description into a high-pressure interview environment packed with algorithmic analysis and anti-cheat tracking.
        </p>
      </FadeUp>

      <div className="rounded-2xl border border-border flex flex-col lg:flex-row relative bg-background overflow-hidden">
        <div className="w-full lg:w-[45%] p-8 lg:p-12 lg:pr-14 border-b lg:border-b-0 lg:border-r border-border flex flex-col justify-start">
          <FadeUp className="mb-8 lg:mb-10 mt-4 lg:mt-8">
            <div className="text-[11px] font-semibold text-muted-foreground mb-3 tracking-widest pl-1 uppercase">Environment Check</div>
            <div className="bg-card rounded-xl p-6 border border-border text-foreground font-medium leading-relaxed text-[16px] lg:text-[17px]">
              "Camera active. Proctoring secured. Generating systems design constraints tailored to your uploaded backend engineering resume."
            </div>
          </FadeUp>

          <div className="space-y-8 lg:space-y-10 pb-10 lg:pb-14">
            <FeatureRow icon={Code} title="Code Complexity Engine" text="Real-time interactive environments that execute your syntax and aggressively grade your algorithmic space & time complexity efficiency." />
            <FeatureRow icon={Cpu} title="Strict Anti-Cheat Proctoring" text="Simulate true pressure. Our platform actively monitors tab-switching, fullscreen exits, and dev-tools access to ensure clinical accuracy." />
            <FeatureRow icon={Network} title="Resume-Grounded Prompts" text="Every scenario is dynamically synthesized entirely from your explicit PDF history and matched aggressively against your target job." />
          </div>
        </div>

        <div className="hidden lg:flex w-full lg:w-[55%] relative items-center justify-center bg-card/30">
          <div className="sticky top-12 h-[calc(100vh-6rem)] max-h-[800px] min-h-[500px] w-full flex items-center justify-center p-10">
            <FadeUp className="w-full">
              <div className="bg-card rounded-2xl p-6 md:p-8 aspect-square relative shadow-sm overflow-hidden border border-border transition-all duration-500 w-full hover:shadow-lg">
                <div className="absolute top-6 left-6 right-6 bottom-6 bg-background rounded-xl shadow-sm border border-border flex flex-col overflow-hidden">
                  <div className="h-10 bg-card border-b border-border flex items-center px-4 gap-2 shrink-0">
                    <div className="flex gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-foreground/10" />
                      <div className="w-2.5 h-2.5 rounded-full bg-foreground/10" />
                      <div className="w-2.5 h-2.5 rounded-full bg-foreground/10" />
                    </div>
                    <div className="flex gap-2 mx-auto">
                      <div className="bg-red-500/10 text-red-600 rounded-full text-[10px] font-bold px-2.5 py-0.5 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> RECORDING
                      </div>
                      <div className="bg-foreground/5 rounded-full text-[10px] font-bold px-2.5 py-0.5 text-muted-foreground">PROCTORING ACTIVE</div>
                    </div>
                  </div>
                  <div className="flex-1 p-5 flex flex-col gap-3 relative">
                    <div className="absolute top-5 right-5 w-14 h-10 bg-card border border-border rounded-lg shadow-sm overflow-hidden flex flex-col items-center justify-center">
                      <div className="w-3.5 h-3.5 rounded-full bg-foreground/10 mb-0.5" />
                      <div className="w-7 h-2.5 rounded-t-lg bg-foreground/10" />
                    </div>
                    <div className="w-1/2 h-3.5 bg-foreground/5 rounded-lg" />
                    <div className="w-full bg-foreground rounded-xl font-mono text-[10px] p-4 leading-relaxed relative overflow-hidden">
                      <div className="text-background/50 mb-2"># Submitting graph traversal...</div>
                      <span className="text-green-400">def</span> <span className="text-blue-300">find_path</span>(grid):<br/>
                      &nbsp;&nbsp;&nbsp;&nbsp;visited = set()<br/>
                      &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-yellow-400"># O(N^2) Space Complexity Warning</span><br/>
                      <div className="mt-3 border-t border-background/20 pt-2 flex justify-between text-background/50">
                        <span>Runtime: 42ms</span>
                        <span className="text-red-400 font-bold bg-red-500/20 px-1.5 rounded-full text-[9px]">WARN: N^2 SPACE</span>
                      </div>
                    </div>
                    <div className="w-1/2 h-2.5 bg-foreground/5 rounded-lg mt-auto" />
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
    <section id={id} className="py-24 px-6 max-w-[1100px] mx-auto lg:px-10">
      <FadeUp className="flex flex-col lg:items-end lg:text-right">
        <h2 className="text-4xl md:text-5xl lg:text-[3.5rem] font-medium tracking-tight mb-4 text-foreground">Vocal Confidence & Pulse</h2>
        <p className="text-lg md:text-[19px] text-muted-foreground leading-relaxed mb-12 max-w-3xl">
          Track real-time baseline fluctuations in your vocal authority and strip away demographics for absolute objective rubric scoring.
        </p>
      </FadeUp>

      <div className="rounded-2xl border border-border flex flex-col lg:flex-row relative bg-background overflow-hidden">
        <div className="hidden lg:flex w-full lg:w-[55%] relative items-center justify-center bg-card/30 border-b lg:border-b-0 lg:border-r border-border">
          <div className="sticky top-12 h-[calc(100vh-6rem)] max-h-[800px] min-h-[500px] w-full flex items-center justify-center p-10">
            <FadeUp className="w-full">
              <div className="bg-card rounded-2xl p-6 md:p-8 aspect-square relative shadow-sm overflow-hidden border border-border transition-all duration-500 w-full hover:shadow-lg">
                <div className="absolute top-10 left-5 right-5 bottom-0 bg-background shadow-sm rounded-t-xl border-x border-t border-border flex flex-col pt-5 px-5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="h-5 w-1/3 bg-foreground/5 rounded-lg" />
                    <div className="bg-brand/10 border border-brand/20 text-brand text-[9px] font-bold px-2 py-1 rounded-full ml-auto whitespace-nowrap">BIAS-FREE MODE</div>
                  </div>
                  <div className="flex gap-3 mb-5">
                    <div className="w-14 h-14 rounded-xl border-[3px] border-brand flex flex-col items-center justify-center font-bold text-foreground shrink-0 relative overflow-hidden bg-card">
                      <span className="text-lg leading-none mb-0.5 text-foreground">160</span>
                      <span className="text-[7px] text-muted-foreground font-semibold tracking-widest">WPM</span>
                    </div>
                    <div className="flex-1 flex gap-1 items-end h-14 pb-1">
                      {[40, 60, 85, 95, 50, 70].map((h, i) => (
                        <div
                          key={i}
                          className="w-full rounded-t-sm transition-all"
                          style={{
                            height: `${h}%`,
                            background: h > 80 ? 'hsl(var(--foreground))' : 'hsl(var(--foreground) / 0.10)',
                          }}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="flex-1 bg-card rounded-t-xl border-x border-t border-border p-4 flex flex-col gap-3">
                    <div className="text-[10px] font-bold text-muted-foreground tracking-wider">FILLER WORD ANALYSIS</div>
                    <div className="space-y-2.5">
                      <div className="h-2 w-full bg-foreground/5 rounded-full overflow-hidden">
                        <div className="w-[30%] bg-foreground h-full rounded-full" />
                      </div>
                      <div className="h-2 w-5/6 bg-foreground/5 rounded-full overflow-hidden">
                        <div className="w-[15%] bg-foreground/30 h-full rounded-full" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </FadeUp>
          </div>
        </div>

        <div className="w-full lg:w-[45%] p-8 lg:p-12 lg:pl-14 flex flex-col justify-start bg-card/50">
          <FadeUp className="mb-8 lg:mb-10 mt-4 lg:mt-8">
            <div className="text-[11px] font-semibold text-muted-foreground mb-3 tracking-widest pl-1 uppercase">Pulse Report</div>
            <div className="bg-background rounded-xl p-6 border border-border text-foreground font-medium leading-relaxed text-[16px] lg:text-[17px]">
              "Analysis complete: Detected 14 instances of conversational stumbles pacing above 160 WPM during the systems design whiteboard segment."
            </div>
          </FadeUp>

          <div className="space-y-8 lg:space-y-10 pb-10 lg:pb-14">
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
      <div className="flex gap-5 items-start">
        <div className="w-10 h-10 shrink-0 rounded-xl bg-foreground/5 border border-border flex items-center justify-center text-foreground/60">
          <Icon className="w-5 h-5" strokeWidth={1.8} />
        </div>
        <div>
          <h4 className="text-lg font-semibold mb-1.5 text-foreground tracking-tight">{title}</h4>
          <p className="text-muted-foreground text-[15px] leading-relaxed">{text}</p>
        </div>
      </div>
    </FadeUp>
  );
}
