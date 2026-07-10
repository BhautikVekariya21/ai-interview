import { BookOpen, Calendar, ArrowRight, Tag, Clock } from "lucide-react";
import { Link } from "react-router-dom";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

const posts = [
  {
    id: "mastering-system-design",
    title: "Mastering System Design Interviews: A Complete Guide",
    excerpt: "System design interviews are one of the most challenging parts of the technical interview process. Here's our comprehensive guide to approaching them with confidence.",
    category: "Interview Prep",
    date: "April 5, 2026",
    readTime: "12 min read",
    featured: true,
  },
  {
    id: "ai-interview-prep",
    title: "How AI is Transforming Interview Preparation in 2026",
    excerpt: "From personalized question generation to real-time voice interviews, AI is revolutionizing how engineers prepare for technical interviews.",
    category: "AI & Technology",
    date: "April 2, 2026",
    readTime: "8 min read",
    featured: true,
  },
  {
    id: "behavioral-questions",
    title: "50 Behavioral Interview Questions Every Engineer Should Practice",
    excerpt: "Technical skills alone won't get you the job. Prepare for the behavioral questions that top companies like Google, Meta, and Amazon always ask.",
    category: "Interview Prep",
    date: "March 28, 2026",
    readTime: "10 min read",
    featured: false,
  },
  {
    id: "resume-optimization",
    title: "How to Optimize Your Resume for ATS and AI Screening",
    excerpt: "Most resumes are screened by AI before a human ever sees them. Learn how to structure your resume to pass both automated and human review.",
    category: "Career Tips",
    date: "March 22, 2026",
    readTime: "7 min read",
    featured: false,
  },
  {
    id: "coding-interview-patterns",
    title: "The 15 Coding Patterns That Cover 90% of Interview Questions",
    excerpt: "Stop grinding hundreds of LeetCode problems. Focus on these 15 fundamental patterns and you'll be prepared for the vast majority of coding challenges.",
    category: "Interview Prep",
    date: "March 15, 2026",
    readTime: "15 min read",
    featured: false,
  },
  {
    id: "salary-negotiation",
    title: "The Engineer's Guide to Salary Negotiation",
    excerpt: "You've aced the interview — now comes the negotiation. Learn proven strategies to maximize your compensation package at any company.",
    category: "Career Tips",
    date: "March 10, 2026",
    readTime: "9 min read",
    featured: false,
  },
];

const categories = [...new Set(posts.map((p) => p.category))];

export default function BlogPage() {
  const featured = posts.filter((p) => p.featured);
  const regular = posts.filter((p) => !p.featured);

  return (
    <div className="relative min-h-screen bg-white text-[#000]">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-[#000]/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-5xl px-4 pt-28 pb-20 md:px-6">
        <div className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-[#000]/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <BookOpen className="h-3.5 w-3.5" /> Blog
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Insights & <span className="text-black">Resources</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-black/60 md:text-lg">
            Expert tips, interview strategies, and career advice to help you land your dream role.
          </p>
        </div>

        {/* Category Pills */}
        <div className="mb-10 flex flex-wrap justify-center gap-2">
          <span className="rounded-xl bg-[#000] px-4 py-1.5 text-xs font-semibold text-white">All</span>
          {categories.map((cat) => (
            <span key={cat} className="rounded-xl border border-black/10 bg-[#F9F9F9] px-4 py-1.5 text-xs font-medium text-black/60 cursor-pointer hover:border-primary/30 hover:text-[#000] transition-colors">
              {cat}
            </span>
          ))}
        </div>

        {/* Featured Posts */}
        <div className="grid gap-6 md:grid-cols-2 mb-10">
          {featured.map((post) => (
            <div key={post.id} className="group relative overflow-hidden rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-6 transition-all duration-300 hover:border-primary/30 hover:-translate-y-1 hover:shadow-sm hover:shadow-primary/5">
              <div className="absolute top-4 right-4 rounded-xl bg-[#000]/10 px-2.5 py-0.5 text-[10px] font-semibold text-primary">Featured</div>
              <span className="inline-flex items-center gap-1.5 rounded-xl bg-[#F9F9F9] px-3 py-1 text-[10px] font-semibold border border-black/10">
                <Tag className="h-3 w-3" /> {post.category}
              </span>
              <h3 className="mt-4 text-xl font-bold tracking-tight leading-snug group-hover:text-primary transition-colors">{post.title}</h3>
              <p className="mt-3 text-sm text-black/60 leading-relaxed">{post.excerpt}</p>
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-3 text-xs text-black/50">
                  <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {post.date}</span>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {post.readTime}</span>
                </div>
                <span className="flex items-center gap-1 text-xs font-semibold text-primary hover:text-primary/80 cursor-pointer transition-colors">
                  Read <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Regular Posts */}
        <div className="space-y-4">
          {regular.map((post) => (
            <div key={post.id} className="group rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-5 transition-all duration-300 hover:border-primary/20 hover:-translate-y-0.5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <span className="inline-flex items-center gap-1 rounded-xl bg-[#F9F9F9] px-2.5 py-0.5 text-[10px] font-semibold border border-black/10 mb-2">
                    <Tag className="h-2.5 w-2.5" /> {post.category}
                  </span>
                  <h3 className="text-base font-bold tracking-tight group-hover:text-primary transition-colors">{post.title}</h3>
                  <p className="mt-1.5 text-sm text-black/60 line-clamp-2">{post.excerpt}</p>
                </div>
                <span className="flex items-center gap-1 rounded-xl bg-[#000]/10 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-[#000] hover:text-white cursor-pointer transition-colors">
                  Read <ArrowRight className="h-3 w-3" />
                </span>
              </div>
              <div className="mt-3 flex items-center gap-3 text-xs text-black/50">
                <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {post.date}</span>
                <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {post.readTime}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Newsletter CTA */}
        <div className="mt-14 rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/5 via-background to-accent/5 p-8 text-center">
          <h3 className="text-lg font-bold">Stay Updated</h3>
          <p className="mt-2 text-sm text-black/60 max-w-md mx-auto">
            Get the latest interview tips and career advice delivered to your inbox every week.
          </p>
          <div className="mt-5 flex items-center justify-center gap-2 max-w-sm mx-auto">
            <input
              type="email"
              placeholder="your@email.com"
              className="flex-1 rounded-xl border border-black/10 bg-white px-4 py-2.5 text-sm placeholder:text-black/50 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button className="rounded-xl bg-[#000] px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-[#000]/90">
              Subscribe
            </button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
