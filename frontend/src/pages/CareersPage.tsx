import { Github, Code2, Sparkles, Heart, ArrowRight, Bug, Lightbulb } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";
import Reveal from "@/components/motion/Reveal";
import SpotlightCard from "@/components/cards/SpotlightCard";

const contributions = [
  {
    title: "Frontend & UX",
    area: "React / TypeScript",
    type: "Open Source",
    desc: "Improve the interview UI, code editor, whiteboard, or accessibility. There's always polish and new features to build.",
    tags: ["TypeScript", "React", "Tailwind", "Vite"],
  },
  {
    title: "AI & Evaluation",
    area: "Python / LLMs",
    type: "Open Source",
    desc: "Refine the multi-provider question generation and answer evaluation pipeline, or experiment with better prompts and models.",
    tags: ["Python", "NLP", "LLMs", "Prompting"],
  },
  {
    title: "Backend & Infra",
    area: "FastAPI",
    type: "Open Source",
    desc: "Help with the FastAPI backend, resume parsing, voice/TTS integration, or deployment and reliability.",
    tags: ["Python", "FastAPI", "APIs"],
  },
  {
    title: "Ideas & Feedback",
    area: "Anyone",
    type: "No Code Needed",
    desc: "Tried the app and have thoughts? Bug reports, feature ideas, and honest feedback are just as valuable as code.",
    tags: ["Testing", "Feedback", "Design"],
  },
];

const perks = [
  { icon: <Github className="h-5 w-5" />, title: "Fully Open", desc: "The whole project lives on GitHub" },
  { icon: <Code2 className="h-5 w-5" />, title: "Real Stack", desc: "Work with React, FastAPI, and modern LLMs" },
  { icon: <Lightbulb className="h-5 w-5" />, title: "Shape It", desc: "Your ideas can directly influence the roadmap" },
  { icon: <Bug className="h-5 w-5" />, title: "Good First Issues", desc: "Small, approachable tasks to get started" },
  { icon: <Sparkles className="h-5 w-5" />, title: "Learn by Building", desc: "A great way to grow full-stack + AI skills" },
  { icon: <Heart className="h-5 w-5" />, title: "Build Together", desc: "A friendly, no-pressure side-project vibe" },
];

export default function CareersPage() {
  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-accent/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-5xl px-4 pt-28 pb-20 md:px-6">
        {/* Header */}
        <Reveal className="mb-14 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Github className="h-3.5 w-3.5" /> Get Involved
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Help build the future of <span className="text-foreground">interview prep</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            interviewer.ai is an open, solo-built side project — not a company. There's no hiring here, but contributions,
            ideas, and feedback are always welcome. If you'd like to help shape it, jump in.
          </p>
        </Reveal>

        {/* Perks */}
        <div className="mb-14">
          <h2 className="text-xl font-bold tracking-tight text-center mb-6">Why Contribute</h2>
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
            {perks.map((perk, i) => (
              <Reveal key={perk.title} delay={i * 0.06}>
                <div className="flex h-full items-start gap-3 rounded-xl border border-border bg-card shadow-sm p-4 transition-colors hover:border-brand/30">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
                    {perk.icon}
                  </div>
                  <div>
                    <p className="text-sm font-bold">{perk.title}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{perk.desc}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        {/* Ways to contribute */}
        <div className="mb-14">
          <h2 className="text-xl font-bold tracking-tight text-center mb-6">Ways to Contribute</h2>
          <div className="space-y-4">
            {contributions.map((job, i) => (
              <Reveal key={job.title} delay={i * 0.06}>
                <SpotlightCard className="group">
                  <div className="rounded-3xl p-6">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-bold tracking-tight">{job.title}</h3>
                        <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1"><Code2 className="h-3 w-3" /> {job.area}</span>
                          <span className="flex items-center gap-1"><Sparkles className="h-3 w-3" /> {job.type}</span>
                        </div>
                      </div>
                      <a
                        href="https://github.com/BhautikVekariya21/ai-interview"
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 rounded-xl bg-brand/10 px-4 py-1.5 text-xs font-semibold text-brand transition-colors hover:bg-brand hover:text-white"
                      >
                        Contribute <ArrowRight className="h-3 w-3" />
                      </a>
                    </div>
                    <p className="mt-3 text-sm text-muted-foreground">{job.desc}</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {job.tags.map((tag) => (
                        <span key={tag} className="rounded-xl bg-muted/50 px-2.5 py-0.5 text-[10px] font-medium border border-border">{tag}</span>
                      ))}
                    </div>
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </div>

        {/* Get in touch */}
        <Reveal className="rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/5 via-background to-accent/5 p-8 text-center">
          <h3 className="text-lg font-bold">Want to Help or Just Chat?</h3>
          <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
            Open an issue or PR on GitHub, or reach out with ideas and feedback. Every bit of input helps make the project better.
          </p>
          <a
            href="https://github.com/BhautikVekariya21/ai-interview"
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-brand px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-brand/90"
          >
            <Github className="h-4 w-4" /> View on GitHub
          </a>
        </Reveal>
      </main>

      <Footer />
    </div>
  );
}
