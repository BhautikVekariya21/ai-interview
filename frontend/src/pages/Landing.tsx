import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
import { FadeUp, ProctoringSection, PulseSection } from "@/components/sections/FeatureSections";
import SpotlightCard from "@/components/cards/SpotlightCard";

export default function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-brand selection:text-brand-foreground">
      <PublicNavbar overHero />

      {/* HERO — clean aurora-gradient, reusable <Hero /> */}
      <Hero
        eyebrow="AI-powered interview prep — 100% free"
        headline={["The interview,", "mastered before"]}
        highlight="it happens."
        subtext="A hyper-realistic AI interviewer that reads your resume, grades your space-time complexity, traces your speech in real time, and proctors the room — so the real thing feels like a rerun."
        primaryCta={{ label: "Start free — no card", to: "/auth?mode=signup" }}
        secondaryCta={{ label: "See how it works", to: "/how-it-works" }}
      />

      {/* FEATURE SECTIONS */}
      <ProctoringSection />
      <PulseSection />

      {/* VALUE PROPS (Mirroring exhaustive research section) */}
      <section className="py-24 md:py-32 px-6 lg:px-12 max-w-[1400px] mx-auto border-t border-border">
        <FadeUp>
          <h2 className="text-4xl md:text-6xl lg:text-[4.5rem] leading-[1.05] font-semibold tracking-tight max-w-4xl mb-6 text-foreground">
            Exhaustive practice. <span className="bg-gradient-to-r from-brand to-[hsl(190,78%,62%)] bg-clip-text text-transparent">Expressive results.</span>
          </h2>
        </FadeUp>
        <FadeUp delay={0.1}>
          <p className="text-xl max-w-5xl text-foreground/70 font-medium mb-16 leading-relaxed">
            From algorithmic edge-case generation and runtime performance checking, down to behavioral vocal analytics—interviewer.ai forces you to confront and correct your weaknesses.
          </p>
        </FadeUp>
        
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          <FadeUp delay={0.1}>
            <SpotlightCard className="h-full min-h-[420px]">
              <div className="group relative flex h-full flex-col overflow-hidden rounded-3xl p-8 md:p-10">
                <h3 className="text-2xl font-bold mb-4 tracking-tight z-10 text-foreground">Actionable Competency Frameworks</h3>
                <p className="text-foreground/70 text-[17px] font-medium leading-relaxed mb-8 z-10">
                  We break down dense technical hurdles—Algorithms, System Design, Behavioral scenarios—into explicit passed/failed micro-checkpoints.
                </p>

                <div className="absolute -bottom-8 left-6 right-6 bg-card rounded-t-xl border border-border shadow-[0_-5px_20px_-10px_rgba(0,0,0,0.1)] p-5 group-hover:-translate-y-4 transition-transform duration-500">
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-bold text-foreground">System Design</div>
                      <div className="text-[9px] text-white bg-green-500 font-bold tracking-wider px-2 py-0.5 rounded flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> PASS</div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-bold text-foreground">Time Complexity</div>
                      <div className="text-[9px] text-white bg-red-500 font-bold tracking-wider px-2 py-0.5 rounded">FAIL</div>
                    </div>
                  </div>
                </div>
              </div>
            </SpotlightCard>
          </FadeUp>

          <FadeUp delay={0.2}>
            <SpotlightCard className="h-full min-h-[420px]">
              <div className="group relative flex h-full flex-col overflow-hidden rounded-3xl p-8 md:p-10">
                <h3 className="text-2xl font-bold mb-4 tracking-tight z-10 text-foreground">The Confidence Pulse</h3>
                <p className="text-foreground/70 text-[17px] font-medium leading-relaxed mb-8 z-10">
                  Track real-time drops in your conversational authority. Our proprietary voice engine highlights exactly when your confidence dips under pressure.
                </p>

                <div className="absolute -bottom-8 left-8 right-8 bg-[#1B2B23] text-white rounded-t-2xl border border-border shadow-2xl p-6 group-hover:-translate-y-4 transition-transform duration-500">
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-[10px] text-green-400 tracking-widest font-mono font-bold flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /> LIVE PULSE
                    </div>
                    <div className="text-white/40 text-[10px] font-mono">94% CONFIDENCE</div>
                  </div>

                  <div className="flex gap-1 items-end h-12 w-full">
                    <div className="w-full h-[40%] bg-white/20 rounded-t-[1px]" />
                    <div className="w-full h-[60%] bg-white/40 rounded-t-[1px]" />
                    <div className="w-full h-[100%] bg-card rounded-t-[1px]" />
                    <div className="w-full h-[80%] bg-white/80 rounded-t-[1px]" />
                    <div className="w-full h-[30%] bg-red-400 rounded-t-[1px]" />
                    <div className="w-full h-[20%] bg-red-400 rounded-t-[1px]" />
                    <div className="w-full h-[50%] bg-card/60 rounded-t-[1px]" />
                    <div className="w-full h-[70%] bg-white/80 rounded-t-[1px]" />
                    <div className="w-full h-[90%] bg-card rounded-t-[1px]" />
                  </div>
                </div>
              </div>
            </SpotlightCard>
          </FadeUp>

          <FadeUp delay={0.3}>
            <SpotlightCard className="h-full min-h-[420px]">
              <div className="group relative flex h-full flex-col overflow-hidden rounded-3xl p-8 md:p-10">
                <h3 className="text-2xl font-bold mb-4 tracking-tight z-10 text-foreground">Anti-Cheat Hardening</h3>
                <p className="text-foreground/70 text-[17px] font-medium leading-relaxed mb-8 z-10">
                  We strictly disable right-clicks, monitor clipboard usage, and penalize window exits to guarantee your mock statistics remain flawless.
                </p>

                <div className="absolute bottom-10 left-6 right-6 rounded-xl bg-card shadow-xl flex items-center p-4 border border-red-500/30 group-hover:-translate-y-2 transition-transform duration-500">
                   <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-bold mr-3 shrink-0">!</div>
                   <div>
                     <div className="text-[12px] font-bold text-foreground">Action blocked</div>
                     <div className="text-[10px] text-muted-foreground">Copy/Paste is disabled during proctoring.</div>
                   </div>
                </div>
              </div>
            </SpotlightCard>
          </FadeUp>
        </div>
      </section>

      {/* 100% FREE CALL TO ACTION SECTION */}
      <section className="py-24 px-6 md:py-32 lg:px-12 border-t border-border bg-muted/50 flex flex-col items-center">
        <FadeUp>
          <div className="max-w-[1400px] mx-auto w-full flex flex-col md:flex-row items-center justify-between gap-12 bg-muted/40 rounded-[2rem] p-10 md:p-16 border border-border text-foreground">
            
            <div className="flex-1 text-left">
              <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-2">100% Free & Open Source</h2>
              <p className="text-xl md:text-2xl text-foreground/80 font-medium mb-12">No premium limits. No credit cards. Just high-fidelity prep.</p>
              
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-xl bg-muted/50 text-foreground flex items-center justify-center text-[10px]">✓</div>
                  <span className="text-lg font-bold">Unlimited mock interviews</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-xl bg-muted/50 text-foreground flex items-center justify-center text-[10px]">✓</div>
                  <span className="text-lg font-bold">Deep analytic readouts & insights</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-xl bg-muted/50 text-foreground flex items-center justify-center text-[10px]">✓</div>
                  <span className="text-lg font-bold">Fully open for personal custom deployments</span>
                </div>
              </div>
            </div>

            <div className="w-full md:w-[400px] bg-card rounded-3xl p-8 border border-border shadow-2xl shrink-0 flex flex-col hover:-translate-y-1 transition-transform">
              <h3 className="text-lg font-semibold tracking-tight mb-6">interviewer.ai Free</h3>
              <div className="mb-8">
                <span className="text-5xl font-semibold tracking-tight text-foreground">$0</span>
                <span className="text-xl text-foreground/80 font-medium">/forever</span>
              </div>
              <Button asChild size="lg" className="h-14 w-full rounded-xl text-base font-bold bg-brand text-brand-foreground hover:bg-foreground/80 transition-all shadow-none">
                <Link to="/auth?mode=signup">
                  Get Started Now
                </Link>
              </Button>
            </div>
            
          </div>
        </FadeUp>
      </section>

      <Footer />
    </div>
  );
}
