import { Briefcase, MapPin, Clock, Sparkles, Heart, Zap, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

const openings = [
  {
    title: "Senior ML Engineer",
    team: "AI Research",
    location: "Remote (Global)",
    type: "Full-Time",
    desc: "Build and optimize our multi-provider AI pipeline, improve evaluation models, and develop next-gen interview question generation.",
    tags: ["Python", "PyTorch", "NLP", "LLMs"],
  },
  {
    title: "Full-Stack Engineer",
    team: "Platform",
    location: "Remote (Global)",
    type: "Full-Time",
    desc: "Work on our React/TypeScript frontend and FastAPI backend, building features used by thousands of engineers daily.",
    tags: ["TypeScript", "React", "Python", "FastAPI"],
  },
  {
    title: "DevOps / SRE Engineer",
    team: "Infrastructure",
    location: "Remote (Global)",
    type: "Full-Time",
    desc: "Own our deployment pipeline, Kubernetes clusters, monitoring stack, and ensure 99.9% uptime for our global user base.",
    tags: ["Kubernetes", "Docker", "Terraform", "Prometheus"],
  },
  {
    title: "Product Designer",
    team: "Design",
    location: "Remote (Global)",
    type: "Full-Time",
    desc: "Design beautiful, accessible interfaces for our interview platform. Shape the UX of AI-powered interview preparation.",
    tags: ["Figma", "Design Systems", "User Research"],
  },
  {
    title: "Technical Writer",
    team: "Developer Relations",
    location: "Remote (Global)",
    type: "Part-Time / Contract",
    desc: "Create documentation, tutorials, and educational content that helps developers prepare for technical interviews.",
    tags: ["Documentation", "API Docs", "Technical Writing"],
  },
];

const perks = [
  { icon: <MapPin className="h-5 w-5" />, title: "Fully Remote", desc: "Work from anywhere in the world" },
  { icon: <Clock className="h-5 w-5" />, title: "Flexible Hours", desc: "We care about output, not hours logged" },
  { icon: <Heart className="h-5 w-5" />, title: "Health & Wellness", desc: "Comprehensive health benefits for you & family" },
  { icon: <Sparkles className="h-5 w-5" />, title: "Learning Budget", desc: "$2,000/year for conferences, courses, books" },
  { icon: <Zap className="h-5 w-5" />, title: "Latest Hardware", desc: "MacBook Pro or equivalent of your choice" },
  { icon: <Briefcase className="h-5 w-5" />, title: "Equity", desc: "Competitive equity package for all employees" },
];

export default function CareersPage() {
  return (
    <div className="relative min-h-screen bg-white text-[#000]">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-accent/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-5xl px-4 pt-28 pb-20 md:px-6">
        {/* Header */}
        <div className="mb-14 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-[#000]/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Briefcase className="h-3.5 w-3.5" /> Careers
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Build the future of <span className="text-black">interview prep</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-black/60 md:text-lg">
            Join a small, passionate team building AI tools that help engineers land their dream jobs. We're remote-first and always looking for talented people.
          </p>
        </div>

        {/* Perks */}
        <div className="mb-14">
          <h2 className="text-xl font-bold tracking-tight text-center mb-6">Why Join Us</h2>
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
            {perks.map((perk) => (
              <div key={perk.title} className="flex items-start gap-3 rounded-xl border border-black/5 bg-white shadow-sm border border-black/10 p-4 transition-all hover:border-primary/20">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-[#000]/10 text-primary">
                  {perk.icon}
                </div>
                <div>
                  <p className="text-sm font-bold">{perk.title}</p>
                  <p className="mt-0.5 text-xs text-black/50">{perk.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Openings */}
        <div className="mb-14">
          <h2 className="text-xl font-bold tracking-tight text-center mb-6">Open Positions</h2>
          <div className="space-y-4">
            {openings.map((job) => (
              <div key={job.title} className="group rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-6 transition-all duration-300 hover:border-primary/30 hover:-translate-y-0.5 hover:shadow-sm hover:shadow-primary/5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-bold tracking-tight">{job.title}</h3>
                    <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-black/50">
                      <span className="flex items-center gap-1"><Briefcase className="h-3 w-3" /> {job.team}</span>
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {job.location}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {job.type}</span>
                    </div>
                  </div>
                  <a
                    href="mailto:careers@interviewer.ai"
                    className="flex items-center gap-1 rounded-xl bg-[#000]/10 px-4 py-1.5 text-xs font-semibold text-primary transition-colors hover:bg-[#000] hover:text-white"
                  >
                    Apply <ArrowRight className="h-3 w-3" />
                  </a>
                </div>
                <p className="mt-3 text-sm text-black/60">{job.desc}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {job.tags.map((tag) => (
                    <span key={tag} className="rounded-xl bg-[#F9F9F9] px-2.5 py-0.5 text-[10px] font-medium border border-black/10">{tag}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Don't see your role? */}
        <div className="rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/5 via-background to-accent/5 p-8 text-center">
          <h3 className="text-lg font-bold">Don't See Your Role?</h3>
          <p className="mt-2 text-sm text-black/60 max-w-md mx-auto">
            We're always interested in hearing from talented people. Send us your resume and a note about what you'd like to work on.
          </p>
          <a
            href="mailto:careers@interviewer.ai"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#000] px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-[#000]/90"
          >
            careers@interviewer.ai
          </a>
        </div>
      </main>

      <Footer />
    </div>
  );
}
