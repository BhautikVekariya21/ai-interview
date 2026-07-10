import { m as motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Code, Cpu, LineChart, MousePointer, AppWindow, Network } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

function FadeUp({
  children,
  delay = 0,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.7, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-foreground selection:text-background">
      <PublicNavbar />

      {/* HERO SECTION */}
      <section className="pt-24 pb-20 px-6 max-w-full mx-auto md:pt-32 md:pb-32 overflow-hidden flex flex-col items-center text-center">
        <FadeUp>
          <h1 className="text-[12vw] sm:text-[14vw] md:text-[13vw] lg:text-[11vw] xl:text-[10vw] font-semibold tracking-tighter text-foreground leading-none whitespace-nowrap">
            master the interview
          </h1>
        </FadeUp>
        
        <FadeUp delay={0.1}>
          <p className="mt-8 md:mt-12 text-lg md:text-2xl max-w-3xl text-foreground/80 font-medium leading-relaxed tracking-tight px-4 inline-block">
            Stop practicing in a vacuum. Train with a hyper-realistic AI that parses your resume, evaluates space-time complexity, traces your speech pulse, and heavily proctors your environment to build unbreakable muscle memory.
          </p>
        </FadeUp>
      </section>

      {/* FEATURE 1: Smart Interviews */}
      <section id="features" className="py-24 px-6 max-w-[1400px] mx-auto lg:px-12">
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
              <FadeUp>
                <div className="flex gap-6 items-start">
                  <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                     <Code className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <div>
                    <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">Code Complexity Engine</h4>
                    <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">
                      Real-time interactive environments that execute your syntax and aggressively grade your algorithmic space & time complexity efficiency.
                    </p>
                  </div>
                </div>
              </FadeUp>
              
              <FadeUp>
                <div className="flex gap-6 items-start">
                  <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                     <Cpu className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <div>
                    <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">Strict Anti-Cheat Proctoring</h4>
                    <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">
                      Simulate true pressure. Our platform actively monitors tab-switching, fullscreen exits, and dev-tools access to ensure clinical accuracy.
                    </p>
                  </div>
                </div>
              </FadeUp>

              <FadeUp>
                <div className="flex gap-6 items-start">
                  <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                     <Network className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <div>
                    <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">Resume-Grounded Prompts</h4>
                    <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">
                      Every scenario is dynamically synthesized entirely from your explicit PDF history and matched aggressively against your target job.
                    </p>
                  </div>
                </div>
              </FadeUp>
            </div>
          </div>
          
          <div className="hidden lg:flex w-full lg:w-[55%] relative items-center justify-center bg-card/30 backdrop-blur-sm">
            <div className="sticky top-12 h-[calc(100vh-6rem)] max-h-[800px] min-h-[500px] w-full flex items-center justify-center p-12">
               <FadeUp className="w-full">
                <div className="bg-muted/50 rounded-[2rem] p-6 md:p-8 aspect-square relative shadow-inner overflow-hidden border border-[#FFEFE5]/50 transition-transform duration-500 w-full hover:shadow-2xl hover:scale-[1.02]">
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

      {/* FEATURE 2: Deep Analytics */}
      <section className="py-24 px-6 max-w-[1400px] mx-auto lg:px-12">
        <FadeUp className="flex flex-col lg:items-end lg:text-right">
          <h2 className="text-4xl md:text-5xl lg:text-[4rem] font-semibold tracking-tight mb-5 text-foreground">Vocal Confidence & Pulse Metrics</h2>
          <p className="text-xl md:text-[22px] text-foreground/70 font-medium leading-relaxed mb-12 max-w-3xl">
            Track real-time baseline fluctuations in your vocal authority and strip away demographics for absolute objective rubric scoring.
          </p>
        </FadeUp>
        
        <div className="rounded-[2.5rem] border border-border flex flex-col lg:flex-row relative bg-transparent overflow-hidden">
          
          {/* VISUAL ON LEFT */}
          <div className="hidden lg:flex w-full lg:w-[55%] relative items-center justify-center bg-card/30 backdrop-blur-sm border-b lg:border-b-0 lg:border-r border-border">
            <div className="sticky top-12 h-[calc(100vh-6rem)] max-h-[800px] min-h-[500px] w-full flex items-center justify-center p-12">
               <FadeUp className="w-full">
                <div className="bg-muted/50 rounded-[2rem] p-6 md:p-8 aspect-square relative shadow-inner overflow-hidden border border-[#F0F5FF]/50 transition-transform duration-500 w-full hover:shadow-2xl hover:scale-[1.02]">
                  <div className="absolute top-12 left-6 right-6 bottom-0 bg-card shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)] rounded-t-2xl border-x border-t border-border flex flex-col pt-6 px-6">
                    <div className="flex items-center gap-3 mb-6">
                       <div className="h-6 w-1/3 bg-muted rounded-xl" />
                       <div className="bg-green-100/50 border border-green-500/20 text-green-700 text-[9px] font-bold px-2 py-1 rounded-lg ml-auto whitespace-nowrap">BIAS-FREE MODE</div>
                    </div>
                    <div className="flex gap-4 mb-6">
                      <div className="w-16 h-16 rounded-xl border-[4px] border-[#000] flex flex-col items-center justify-center font-bold text-foreground shrink-0 relative overflow-hidden bg-muted/30">
                         <span className="text-xl leading-none mb-0.5 text-foreground">160</span>
                         <span className="text-[8px] text-foreground/70 font-semibold tracking-widest">WPM</span>
                         <div className="absolute top-0 right-0 w-2 h-2 bg-red-400 rounded-bl-lg" />
                      </div>
                      <div className="flex-1 flex gap-1.5 items-end h-16 pb-1">
                         <div className="w-full h-[40%] bg-muted rounded-t-sm transition-all hover:bg-muted-foreground/30" />
                         <div className="w-full h-[60%] bg-muted rounded-t-sm transition-all hover:bg-muted-foreground/30" />
                         <div className="w-full h-[85%] bg-foreground rounded-t-sm relative transition-all group">
                           <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-foreground text-white text-[9px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-xl">uhm</div>
                         </div>
                         <div className="w-full h-[95%] bg-foreground rounded-t-sm relative transition-all group">
                           <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-foreground text-white text-[9px] font-semibold px-2 py-1 rounded shadow-xl whitespace-nowrap">uhm</div>
                         </div>
                         <div className="w-full h-[50%] bg-muted rounded-t-sm transition-all hover:bg-muted-foreground/30" />
                         <div className="w-full h-[70%] bg-muted-foreground/50 rounded-t-sm relative transition-all group">
                            <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-foreground text-white text-[9px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-xl">like</div>
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
          
          {/* TEXT ON RIGHT */}
          <div className="w-full lg:w-[45%] p-10 lg:p-14 lg:pl-16 flex flex-col justify-start bg-card">
            
            <FadeUp className="mb-8 lg:mb-12 mt-6 lg:mt-12">
              <div className="text-[11px] font-semibold text-muted-foreground mb-4 tracking-widest pl-1 uppercase">Pulse Report</div>
              <div className="bg-card rounded-[1.5rem] p-7 shadow-sm border border-border text-foreground font-medium leading-relaxed text-[17px] lg:text-[19px]">
                 "Analysis complete: Detected 14 instances of conversational stumbles pacing above 160 WPM during the systems design whiteboard segment."
              </div>
            </FadeUp>
            
            <div className="space-y-8 lg:space-y-12 pb-12 lg:pb-16">
              <FadeUp>
                <div className="flex gap-6 items-start">
                  <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                     <LineChart className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <div>
                    <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">Speech Trajectory Heatmaps</h4>
                    <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">
                      Identify exact chronological conversational stumbles with highly precise filler word tracking and speaking pace analytics.
                    </p>
                  </div>
                </div>
              </FadeUp>
              
              <FadeUp>
                <div className="flex gap-6 items-start">
                  <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                     <MousePointer className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <div>
                    <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">Bias-Free Results</h4>
                    <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">
                      Strip away demographic variables using our blind-evaluation switch for perfectly objective, rubric-driven scoring matrices.
                    </p>
                  </div>
                </div>
              </FadeUp>

              <FadeUp>
                <div className="flex gap-6 items-start">
                  <div className="w-12 h-12 shrink-0 rounded-xl bg-muted/50 border border-border flex items-center justify-center text-foreground/80">
                     <AppWindow className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <div>
                    <h4 className="text-lg lg:text-xl font-bold mb-2 text-foreground">Ideal Answer Mapping</h4>
                    <p className="text-foreground/70 text-[16px] lg:text-[17px] font-medium leading-relaxed">
                      Compare your algorithmic stumbling blocks directly against statically generated optimal path solutions for instant correction.
                    </p>
                  </div>
                </div>
              </FadeUp>
            </div>
          </div>
          
        </div>
      </section>

      {/* VALUE PROPS (Mirroring exhaustive research section) */}
      <section className="py-24 md:py-32 px-6 lg:px-12 max-w-[1400px] mx-auto border-t border-border">
        <FadeUp>
          <h2 className="text-4xl md:text-6xl lg:text-[4.5rem] leading-[1.05] font-semibold tracking-tight max-w-4xl mb-6 text-foreground">
            Exhaustive practice. <span className="bg-gradient-to-r from-[#8E215C] to-[#D794C2] bg-clip-text text-transparent">Expressive results.</span>
          </h2>
        </FadeUp>
        <FadeUp delay={0.1}>
          <p className="text-xl max-w-5xl text-foreground/70 font-medium mb-16 leading-relaxed">
            From algorithmic edge-case generation and runtime performance checking, down to behavioral vocal analytics—interviewer.ai forces you to confront and correct your weaknesses.
          </p>
        </FadeUp>
        
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          <FadeUp delay={0.1}>
            <div className="bg-card rounded-[2rem] p-8 md:p-10 border border-border flex flex-col h-full min-h-[420px] overflow-hidden relative group hover:shadow-lg transition-shadow">
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
          </FadeUp>
          
          <FadeUp delay={0.2}>
            <div className="bg-card rounded-[2rem] p-8 md:p-10 border border-border flex flex-col h-full min-h-[420px] overflow-hidden relative group hover:shadow-lg transition-shadow">
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
          </FadeUp>
          
          <FadeUp delay={0.3}>
            <div className="bg-card rounded-[2rem] p-8 md:p-10 border border-border flex flex-col h-full min-h-[420px] overflow-hidden relative group hover:shadow-lg transition-shadow">
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
              <Button asChild size="lg" className="h-14 w-full rounded-xl text-base font-bold bg-foreground text-white hover:bg-foreground/80 transition-all shadow-none">
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
