import { Users, Sparkles, Target, Globe, Heart, Award } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

const values = [
  {
    icon: <Target className="h-6 w-6" />,
    title: "Mission-Driven",
    desc: "We believe every developer deserves access to world-class interview preparation, regardless of their background or budget.",
  },
  {
    icon: <Sparkles className="h-6 w-6" />,
    title: "AI for Good",
    desc: "We harness the latest in AI to create tools that genuinely help people grow, not just generate profit.",
  },
  {
    icon: <Heart className="h-6 w-6" />,
    title: "Inclusive by Design",
    desc: "Our bias-free mode and accessible design ensure every candidate gets a fair, equitable interview experience.",
  },
];

export default function AboutPage() {
  return (
    <div className="relative min-h-screen bg-white text-[#000]">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[700px] w-[900px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-[#000]/12 blur-[140px]" />
        <div className="absolute right-0 top-1/3 h-[400px] w-[400px] rounded-xl bg-accent/10 blur-[120px]" />
      </div>

      <main className="relative mx-auto max-w-6xl px-4 pt-28 pb-20 md:px-6">
        {/* Hero */}
        <div className="mb-16 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-[#000]/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Users className="h-3.5 w-3.5" /> About Us
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl lg:text-6xl">
            Empowering engineers to{" "}
            <span className="text-black">ace their interviews</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-black/60">
            interviewer.ai was born from a simple observation: technical interviews are stressful, and most preparation
            tools haven't evolved with the times. We set out to build the AI-powered interview coach we wished we had.
          </p>
        </div>

        {/* Our Story */}
        <div className="mb-16 rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-8 md:p-12">
          <h2 className="text-2xl font-bold tracking-tight mb-4">Our Story</h2>
          <div className="space-y-4 text-sm leading-relaxed text-black/60 md:text-base">
            <p>
              interviewer.ai started as a side project in 2024, born from the frustration of preparing for technical interviews
              with outdated tools and generic question banks. Traditional mock interview platforms offered the same 100 questions
              to everyone — they didn't adapt to your experience, your target role, or your actual resume.
            </p>
            <p>
              We asked: <em>what if an AI could read your resume, understand your background, and create a truly personalized
              interview experience?</em> One that speaks questions aloud, listens to your answers, watches you code, and gives
              you detailed, actionable feedback — just like a real senior engineer across the table.
            </p>
            <p>
              Today, interviewer.ai combines resume parsing with NER, multi-provider AI question generation, real-time voice
              interviews with TTS and speech recognition, live code editing, a freehand whiteboard, and deep AI-powered evaluation
              — all in one platform. And we're just getting started.
            </p>
          </div>
        </div>

        {/* Values */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold tracking-tight text-center mb-8">Our Values</h2>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {values.map((v) => (
              <div key={v.title} className="rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-6 transition-all duration-300 hover:border-primary/20 hover:-translate-y-1">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#000]/10 text-primary">
                  {v.icon}
                </div>
                <h3 className="text-base font-bold">{v.title}</h3>
                <p className="mt-2 text-sm text-black/60 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/10 via-background to-accent/10 p-10 text-center">
          <Award className="mx-auto h-10 w-10 text-primary mb-4" />
          <h2 className="text-2xl font-extrabold tracking-tight md:text-3xl">
            Experience the future of <span className="text-black">interview preparation</span>
          </h2>
          <p className="mt-3 text-sm text-black/60 max-w-md mx-auto">
            Start your free interview today and experience the future of interview preparation.
          </p>
          <a
            href="/app"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#000] px-8 py-3 text-base font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-[#000]/90"
          >
            Get Started Free
          </a>
        </div>
      </main>

      <Footer />
    </div>
  );
}
