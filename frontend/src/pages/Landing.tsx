import { Link } from "react-router-dom";
import { ArrowRight, Code, Brain, LineChart, Shield, Mic, FileText } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Hero from "@/components/Hero";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import { FadeUp } from "@/components/sections/FeatureSections";
import CursorGlow from "@/components/motion/CursorGlow";
import { m as motion } from "framer-motion";
import { useState } from "react";

/* ── Granola-inspired "Before / During / After" Interview Flow ── */
const phases = [
  {
    tab: "Before the interview",
    heading: "Start your interview prepared",
    description: "Upload your resume and job description. interviewer.ai generates a tailored Brief—matching your experience against the role, identifying weak spots, and preparing focused questions.",
    mockContent: (
      <div className="bg-card rounded-2xl border border-border p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 rounded-full bg-brand animate-pulse" />
          <span className="text-xs font-semibold text-brand tracking-wide uppercase">Preparing Brief</span>
        </div>
        <div className="space-y-3">
          <div className="bg-background rounded-xl p-4 border border-border">
            <div className="text-sm font-semibold text-foreground mb-2">Resume Analysis</div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">System Design experience</span>
                <span className="text-xs font-semibold text-brand bg-brand/10 px-2 py-0.5 rounded-full">Strong</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Graph algorithms</span>
                <span className="text-xs font-semibold text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">Review</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Dynamic programming</span>
                <span className="text-xs font-semibold text-red-600 bg-red-100 px-2 py-0.5 rounded-full">Focus</span>
              </div>
            </div>
          </div>
          <div className="bg-background rounded-xl p-4 border border-border">
            <div className="text-xs text-muted-foreground mb-1">Tailored Questions</div>
            <div className="text-sm text-foreground font-medium leading-relaxed">
              "Design a rate limiter for an API gateway serving 10M requests/day..."
            </div>
          </div>
        </div>
      </div>
    ),
  },
  {
    tab: "During the interview",
    heading: "Give your full attention",
    description: "Our AI speaks to you in real-time while tracking your code complexity, vocal confidence, and proctoring the environment—so you can focus on performing, not note-taking.",
    mockContent: (
      <div className="bg-card rounded-2xl border border-border p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-foreground/10" />
            <div className="w-3 h-3 rounded-full bg-foreground/10" />
            <div className="w-3 h-3 rounded-full bg-foreground/10" />
          </div>
          <div className="flex gap-2 mx-auto">
            <div className="bg-red-500/10 text-red-600 rounded-full text-[10px] font-bold px-2.5 py-0.5 flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> REC
            </div>
            <div className="bg-foreground/5 rounded-full text-[10px] font-bold px-2.5 py-0.5 text-muted-foreground">PROCTORING</div>
          </div>
        </div>
        <div className="bg-foreground rounded-xl font-mono text-[11px] p-4 leading-relaxed text-background/90 mb-3">
          <span className="text-green-400">def</span>{" "}
          <span className="text-blue-300">rate_limiter</span>(request):<br/>
          &nbsp;&nbsp;window = get_window(request.ip)<br/>
          &nbsp;&nbsp;<span className="text-yellow-400"># O(1) Time, O(N) Space</span><br/>
          <div className="mt-2 border-t border-background/20 pt-2 flex justify-between text-background/50 text-[10px]">
            <span>Runtime: 12ms</span>
            <span className="text-green-400 font-bold">✓ OPTIMAL</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-0.5 items-end h-8 flex-1">
            {[40, 60, 85, 95, 50, 70, 80, 90, 75].map((h, i) => (
              <div key={i} className="w-full rounded-t-sm transition-all" style={{ height: `${h}%`, background: h > 80 ? 'hsl(var(--brand))' : 'hsl(var(--foreground) / 0.12)' }} />
            ))}
          </div>
          <div className="text-[10px] font-mono text-muted-foreground whitespace-nowrap">92% confidence</div>
        </div>
      </div>
    ),
  },
  {
    tab: "After the interview",
    heading: "Results, instantly delivered",
    description: "Detailed analytics, competency breakdowns, and actionable improvement paths are ready the moment the interview ends. Know exactly where to improve.",
    mockContent: (
      <div className="bg-card rounded-2xl border border-border p-6 shadow-sm">
        <div className="text-xs font-semibold text-muted-foreground tracking-wide uppercase mb-4">Performance Summary</div>
        <div className="space-y-3">
          {[
            { label: "Algorithm Design", score: 88, color: "bg-brand" },
            { label: "System Architecture", score: 72, color: "bg-chart-3" },
            { label: "Communication", score: 95, color: "bg-brand" },
            { label: "Problem Solving", score: 80, color: "bg-chart-5" },
          ].map((item) => (
            <div key={item.label}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-foreground">{item.label}</span>
                <span className="text-sm font-bold text-foreground">{item.score}%</span>
              </div>
              <div className="h-2 w-full bg-foreground/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${item.score}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                  className={`h-full ${item.color} rounded-full`}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-border flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Overall Score</span>
          <span className="text-2xl font-bold text-foreground">84<span className="text-sm text-muted-foreground font-normal">/100</span></span>
        </div>
      </div>
    ),
  },
];

/* ── Feature highlights in a clean grid (Granola's "Features" section style) ── */
const features = [
  {
    icon: Code,
    title: "Code Complexity Engine",
    desc: "Real-time execution environments that evaluate your syntax and grade algorithmic space & time complexity.",
  },
  {
    icon: Mic,
    title: "Voice Analysis",
    desc: "Track filler words, speaking pace, and vocal confidence fluctuations throughout your interview.",
  },
  {
    icon: Shield,
    title: "Anti-Cheat Proctoring",
    desc: "Tab-switch detection, clipboard monitoring, and fullscreen enforcement for realistic conditions.",
  },
  {
    icon: Brain,
    title: "AI-Powered Feedback",
    desc: "Receive targeted improvement suggestions based on thousands of successful interview patterns.",
  },
  {
    icon: FileText,
    title: "Resume-Grounded Questions",
    desc: "Every scenario is dynamically generated from your uploaded resume and the target job description.",
  },
  {
    icon: LineChart,
    title: "Progress Analytics",
    desc: "Track your improvement over time with detailed session history and trend analysis.",
  },
];

export default function Landing() {
  const [activePhase, setActivePhase] = useState(0);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-brand/20 selection:text-foreground">
      <CursorGlow />
      <Seo
        title="interviewer.ai — Ace Your Next Technical Interview with AI"
        description="Practice technical interviews with an AI that adapts to your resume, speaks in real-time, evaluates your code, and gives actionable feedback. Start free today."
        path="/"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "interviewer.ai",
          applicationCategory: "EducationalApplication",
          operatingSystem: "Web",
          description:
            "AI-powered technical interview practice that adapts to your resume, grades your code, and analyzes your speech in real time.",
          url: "https://interviewer.ai/",
          offers: {
            "@type": "Offer",
            price: "0",
            priceCurrency: "USD",
          },
        }}
      />
      <PublicNavbar overHero />

      {/* HERO */}
      <Hero
        eyebrow="AI-powered interview prep — 100% free"
        headline={["The interview,", "mastered before"]}
        highlight="it happens."
        subtext="A hyper-realistic AI interviewer that reads your resume, grades your code complexity, traces your speech in real time, and proctors the room — so the real thing feels like a rerun."
        primaryCta={{ label: "Start free — no card", to: "/auth?mode=signup" }}
        secondaryCta={{ label: "See how it works", to: "/how-it-works" }}
      />

      {/* ── TRUSTED BY / SOCIAL PROOF ── */}
      <section className="py-16 border-t border-border">
        <div className="max-w-[1100px] mx-auto px-6 lg:px-10">
          <FadeUp>
            <p className="text-center text-sm font-medium text-muted-foreground tracking-wide uppercase mb-8">
              For the doers
            </p>
          </FadeUp>
          <FadeUp delay={0.1}>
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 opacity-40">
              {["Engineers", "Students", "Career Switchers", "Data Scientists", "Full Stack Devs"].map((name) => (
                <span key={name} className="text-lg font-semibold text-foreground tracking-tight">{name}</span>
              ))}
            </div>
          </FadeUp>
        </div>
      </section>

      {/* ── BEFORE / DURING / AFTER — Granola's signature layout ── */}
      <section className="py-24 md:py-32 border-t border-border bg-[#B4C24E]">
        <div className="max-w-[1100px] mx-auto px-6 lg:px-10">
          <FadeUp>
            <h2 className="text-4xl md:text-5xl lg:text-[3.5rem] font-medium tracking-tight text-foreground mb-3 text-center">
              interviewer.ai helps you<br className="hidden md:block" /> before, during and after.
            </h2>
          </FadeUp>
          <FadeUp delay={0.1}>
            <p className="text-lg text-muted-foreground text-center max-w-2xl mx-auto mb-16">
              A complete preparation system that adapts to your unique experience.
            </p>
          </FadeUp>

          {/* Phase tabs */}
          <FadeUp delay={0.15}>
            <div className="flex items-center justify-center gap-2 mb-12">
              {phases.map((phase, i) => (
                <button
                  key={phase.tab}
                  onClick={() => setActivePhase(i)}
                  className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 ${
                    activePhase === i
                      ? "bg-foreground text-background shadow-sm"
                      : "bg-foreground/5 text-foreground/60 hover:text-foreground hover:bg-foreground/10"
                  }`}
                >
                  {phase.tab}
                </button>
              ))}
            </div>
          </FadeUp>

          {/* Phase content */}
          <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-start">
            <FadeUp delay={0.2}>
              <div className="lg:sticky lg:top-32">
                <motion.div
                  key={activePhase}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                >
                  <h3 className="text-2xl md:text-3xl font-medium tracking-tight text-foreground mb-4">
                    {phases[activePhase].heading}
                  </h3>
                  <p className="text-[17px] text-muted-foreground leading-relaxed mb-6">
                    {phases[activePhase].description}
                  </p>
                  <Link
                    to="/how-it-works"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-foreground hover:text-brand transition-colors"
                  >
                    Learn more <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </motion.div>
              </div>
            </FadeUp>

            <FadeUp delay={0.3}>
              <motion.div
                key={activePhase}
                initial={{ opacity: 0, y: 16, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              >
                {phases[activePhase].mockContent}
              </motion.div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ── FEATURES GRID — "Helping busy people" style ── */}
      <section className="py-24 md:py-32 border-t border-border bg-card/50">
        <div className="max-w-[1100px] mx-auto px-6 lg:px-10">
          <FadeUp>
            <h2 className="text-4xl md:text-5xl lg:text-[3.5rem] font-medium tracking-tight text-foreground mb-3 text-center">
              Everything you need to{" "}
              <span className="font-sans italic text-brand">ace it</span>
            </h2>
          </FadeUp>
          <FadeUp delay={0.1}>
            <p className="text-lg text-muted-foreground text-center max-w-xl mx-auto mb-16">
              From algorithmic edge-cases to vocal analytics — every angle covered.
            </p>
          </FadeUp>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((feature, i) => (
              <FadeUp key={feature.title} delay={0.1 + i * 0.05} className="h-full">
                <div className="group h-full bg-background rounded-2xl border border-border p-7 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 hover:border-foreground/10">
                  <div className="w-10 h-10 rounded-xl bg-foreground/5 flex items-center justify-center mb-5 group-hover:bg-brand/10 transition-colors">
                    <feature.icon className="w-5 h-5 text-foreground/70 group-hover:text-brand transition-colors" strokeWidth={1.8} />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2 tracking-tight">{feature.title}</h3>
                  <p className="text-[15px] text-muted-foreground leading-relaxed">{feature.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ── GRANOLA-STYLE IMMERSIVE CTA — Exact Granola pricing-bg as full-bleed ── */}
      <section className="relative w-full overflow-hidden">
        {/* Full-width Granola pricing background */}
        <img
          src="https://www.granola.ai/_next/image?url=%2FhomepageAssets%2Fpricing-bg.jpg&w=1920&q=75"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 w-full h-full object-cover"
        />

        {/* Content layer */}
        <div className="relative z-10 flex items-center justify-center min-h-[680px] md:min-h-[740px] px-4 py-20">
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.97 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="bg-[#FAF9F5] rounded-3xl border border-[#E0DDD5] shadow-2xl w-full max-w-[760px] overflow-hidden"
          >
            {/* macOS traffic lights */}
            <div className="flex items-center gap-1.5 px-6 pt-6 pb-4 border-b border-[#E8E6DE]">
              <div className="w-3.5 h-3.5 rounded-full bg-[#FF5F57]" />
              <div className="w-3.5 h-3.5 rounded-full bg-[#FEBC2E]" />
              <div className="w-3.5 h-3.5 rounded-full bg-[#28C840]" />
            </div>

            {/* Card body */}
            <div className="px-8 py-12 md:px-16 md:py-16">
              {/* Large sans-serif headline — matching Granola's typography */}
              <h2 className="text-[3.2rem] md:text-[4.2rem] font-sans font-normal leading-[1.04] tracking-tight text-[#1C1917] mb-6">
                Unlimited<br />mock interviews for free
              </h2>

              {/* Sub-description */}
              <p className="text-[17px] md:text-[19px] text-[#6B6355] leading-relaxed mb-10 max-w-2xl">
                Practice as many sessions as you'd like. No credit card, no limit. 100% open source with deep AI analytics and real-time proctoring.
              </p>

              {/* CTA buttons — matching Granola's button style */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Link
                  to="/auth?mode=signup"
                  className="group inline-flex h-14 items-center justify-center gap-2 rounded-full bg-[#1C1917] px-8 text-[15px] font-semibold text-white transition-all hover:bg-[#2D2925] hover:shadow-lg"
                >
                  Get started free
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
                <a
                  href="https://github.com/BhautikVekariya21/ai-interview"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-14 items-center justify-center gap-2 rounded-full border border-[#D4D0C8] px-8 text-[15px] font-semibold text-[#1C1917] bg-transparent transition-all hover:bg-[#F0EDE6]"
                >
                  View on GitHub
                </a>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
