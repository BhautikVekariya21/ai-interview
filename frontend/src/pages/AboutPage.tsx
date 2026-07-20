import { Users, Sparkles, Target, Globe, Heart, Award } from "lucide-react";
import { Link } from "react-router-dom";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";
import Reveal from "@/components/motion/Reveal";
import SpotlightCard from "@/components/cards/SpotlightCard";
import Seo from "@/components/Seo";

const values = [
  {
    icon: <Target className="h-6 w-6" />,
    title: "Built to Solve a Real Problem",
    desc: "This started because generic question banks didn't cut it. Every feature exists to make interview prep genuinely more useful.",
  },
  {
    icon: <Sparkles className="h-6 w-6" />,
    title: "Learning in the Open",
    desc: "A hands-on playground for combining resume parsing, LLMs, voice, and live coding into one cohesive product.",
  },
  {
    icon: <Heart className="h-6 w-6" />,
    title: "Accessible by Default",
    desc: "Bias-free mode and an accessible design keep the practice experience fair and usable for everyone.",
  },
];

export default function AboutPage() {
  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <Seo
        title="About"
        description="interviewer.ai is a personal project built to help engineers ace their technical interviews with a hyper-realistic AI interviewer, resume-grounded questions, and actionable feedback."
        path="/about"
      />
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[700px] w-[900px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-brand/12 blur-[140px]" />
        <div className="absolute right-0 top-1/3 h-[400px] w-[400px] rounded-xl bg-accent/10 blur-[120px]" />
      </div>

      <main className="relative mx-auto max-w-6xl px-4 pt-28 pb-20 md:px-6">
        {/* Hero */}
        <Reveal className="mb-16 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Users className="h-3.5 w-3.5" /> About the Project
          </span>
          <h1 className="mt-5 text-4xl font-serif font-semibold tracking-tight md:text-5xl lg:text-6xl">
            A personal project to help engineers{" "}
            <span className="text-foreground">ace their interviews</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
            interviewer.ai is a solo-built project born from a simple observation: technical interviews are stressful, and
            most preparation tools haven't evolved with the times. It's my attempt to build the AI-powered interview coach
            I wished I had.
          </p>
        </Reveal>

        {/* Our Story */}
        <Reveal delay={0.05} className="mb-16 rounded-2xl border border-border bg-card shadow-sm overflow-hidden p-0">
          <div className="grid md:grid-cols-5">
            <div className="md:col-span-3 p-8 md:p-12 flex flex-col justify-center">
              <h2 className="text-2xl font-serif font-bold tracking-tight mb-4 text-[#1E1F1B]">The Story</h2>
              <div className="space-y-4 text-sm leading-relaxed text-muted-foreground md:text-base">
                <p>
                  interviewer.ai started as a side project, born from the frustration of preparing for technical interviews
                  with outdated tools and generic question banks. Traditional mock interview platforms offered the same 100 questions
                  to everyone — they didn't adapt to your experience, your target role, or your actual resume.
                </p>
                <p>
                  The question that drove it: <em>what if an AI could read your resume, understand your background, and create a truly
                  personalized interview experience?</em> One that speaks questions aloud, listens to your answers, watches you code, and
                  gives you detailed, actionable feedback — just like a real senior engineer across the table.
                </p>
                <p>
                  Today, interviewer.ai combines resume parsing with NER, multi-provider AI question generation, real-time voice
                  interviews with TTS and speech recognition, live code editing, a freehand whiteboard, and deep AI-powered evaluation
                  — all in one project. And it's still evolving.
                </p>
              </div>
            </div>
            <div className="md:col-span-2 relative min-h-[300px] md:min-h-full bg-muted overflow-hidden group">
              <img 
                src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80" 
                alt="Abstract premium fluid canvas" 
                className="w-full h-full object-cover absolute inset-0 transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-black/5" />
            </div>
          </div>
        </Reveal>

        {/* Values */}
        <div className="mb-16">
          <h2 className="text-2xl font-serif font-semibold tracking-tight text-center mb-8">What Guides It</h2>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {values.map((v, i) => (
              <Reveal key={v.title} delay={i * 0.08}>
                <SpotlightCard className="h-full">
                  <div className="rounded-3xl p-6">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
                      {v.icon}
                    </div>
                    <h3 className="text-base font-serif font-semibold">{v.title}</h3>
                    <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{v.desc}</p>
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </div>

        {/* CTA */}
        <Reveal className="rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/10 via-background to-accent/10 p-10 text-center">
          <Award className="mx-auto h-10 w-10 text-primary mb-4" />
          <h2 className="text-2xl font-serif font-semibold tracking-tight md:text-3xl">
            Experience the future of <span className="text-foreground">interview preparation</span>
          </h2>
          <p className="mt-3 text-sm text-muted-foreground max-w-md mx-auto">
            Start your free interview today and experience the future of interview preparation.
          </p>
          <Link
            to="/app"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-brand px-8 py-3 text-base font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-brand/90"
          >
            Get Started Free
          </Link>
        </Reveal>
      </main>

      <Footer />
    </div>
  );
}
