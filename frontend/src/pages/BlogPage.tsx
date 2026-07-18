import { useEffect, useMemo, useState } from "react";
import { BookOpen, Calendar, Tag, Clock, PenSquare, Star, X, MessageCircle, Loader2, User } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";
import Reveal from "@/components/motion/Reveal";
import SpotlightCard from "@/components/cards/SpotlightCard";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/AuthProvider";
import {
  fetchBlogPosts,
  createBlogPost,
  fetchBlogFeedback,
  submitBlogFeedback,
  subscribeNewsletter,
  type BlogPost,
  type BlogFeedback,
} from "@/lib/api";

interface DisplayPost {
  id: string;
  title: string;
  excerpt: string;
  content?: string;
  category: string;
  date: string;
  readTime: string;
  featured: boolean;
  author?: string;
  community?: boolean;
  coverImage?: string;
}

const curatedPosts: DisplayPost[] = [
  {
    id: "mastering-system-design",
    title: "Mastering System Design Interviews: A Complete Guide",
    excerpt: "System design interviews are one of the most challenging parts of the technical interview process. Here's our comprehensive guide to approaching them with confidence.",
    category: "Interview Prep",
    date: "April 5, 2026",
    readTime: "12 min read",
    featured: true,
    coverImage: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80"
  },
  {
    id: "ai-interview-prep",
    title: "How AI is Transforming Interview Preparation in 2026",
    excerpt: "From personalized question generation to real-time voice interviews, AI is revolutionizing how engineers prepare for technical interviews.",
    category: "AI & Technology",
    date: "April 2, 2026",
    readTime: "8 min read",
    featured: true,
    coverImage: "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=800&q=80"
  },
  {
    id: "behavioral-questions",
    title: "50 Behavioral Interview Questions Every Engineer Should Practice",
    excerpt: "Technical skills alone won't get you the job. Prepare for the behavioral questions that top companies like Google, Meta, and Amazon always ask.",
    category: "Interview Prep",
    date: "March 28, 2026",
    readTime: "10 min read",
    featured: false,
    coverImage: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80"
  },
  {
    id: "resume-optimization",
    title: "How to Optimize Your Resume for ATS and AI Screening",
    excerpt: "Most resumes are screened by AI before a human ever sees them. Learn how to structure your resume to pass both automated and human review.",
    category: "Career Tips",
    date: "March 22, 2026",
    readTime: "7 min read",
    featured: false,
    coverImage: "https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&w=800&q=80"
  },
  {
    id: "coding-interview-patterns",
    title: "The 15 Coding Patterns That Cover 90% of Interview Questions",
    excerpt: "Stop grinding hundreds of LeetCode problems. Focus on these 15 fundamental patterns and you'll be prepared for the vast majority of coding challenges.",
    category: "Interview Prep",
    date: "March 15, 2026",
    readTime: "15 min read",
    featured: false,
    coverImage: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80"
  },
  {
    id: "salary-negotiation",
    title: "The Engineer's Guide to Salary Negotiation",
    excerpt: "You've aced the interview — now comes the negotiation. Learn proven strategies to maximize your compensation package at any company.",
    category: "Career Tips",
    date: "March 10, 2026",
    readTime: "9 min read",
    featured: false,
    coverImage: "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=800&q=80"
  },
];

const COMMUNITY_COVERS = [
  "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=800&q=80",
  "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=80"
];

const CATEGORY_OPTIONS = ["Interview Prep", "Career Tips", "AI & Technology", "Coding", "Community"];

function estimateReadTime(text: string): string {
  const words = (text || "").trim().split(/\s+/).filter(Boolean).length;
  const mins = Math.max(1, Math.round(words / 200));
  return `${mins} min read`;
}

function formatDate(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

function toDisplay(post: BlogPost): DisplayPost {
  let hash = 0;
  for (let i = 0; i < post.id.length; i++) {
    hash = (hash * 31 + post.id.charCodeAt(i)) >>> 0;
  }
  const coverImage = COMMUNITY_COVERS[hash % COMMUNITY_COVERS.length];

  return {
    id: post.id,
    title: post.title,
    excerpt: post.excerpt || (post.content || "").slice(0, 180),
    content: post.content,
    category: post.category || "Community",
    date: formatDate(post.created_at),
    readTime: estimateReadTime(post.content || post.excerpt),
    featured: false,
    author: post.author_name,
    community: true,
    coverImage,
  };
}

export default function BlogPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [community, setCommunity] = useState<DisplayPost[]>([]);
  const [activeCategory, setActiveCategory] = useState("All");
  const [showForm, setShowForm] = useState(false);
  const [feedbackFor, setFeedbackFor] = useState<DisplayPost | null>(null);
  const [email, setEmail] = useState("");
  const [subscribing, setSubscribing] = useState(false);

  const handleSubscribe = async () => {
    const value = email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      toast.error("Please enter a valid email address.");
      return;
    }
    setSubscribing(true);
    try {
      const result = await subscribeNewsletter(value);
      if (result.already_subscribed) {
        toast.info("You're already subscribed!");
      } else {
        toast.success("You're subscribed! Check your inbox for a confirmation.");
      }
      setEmail("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Subscription failed. Please try again.");
    } finally {
      setSubscribing(false);
    }
  };

  const loadPosts = () => {
    fetchBlogPosts()
      .then((posts) => setCommunity(posts.map(toDisplay)))
      .catch(() => {/* public read; ignore transient errors */});
  };

  useEffect(() => {
    loadPosts();
  }, []);

  const allPosts = useMemo(() => [...community, ...curatedPosts], [community]);

  const categories = useMemo(
    () => [...new Set(allPosts.map((p) => p.category))],
    [allPosts],
  );

  const visiblePosts = useMemo(
    () => (activeCategory === "All" ? allPosts : allPosts.filter((p) => p.category === activeCategory)),
    [allPosts, activeCategory],
  );

  const featured = visiblePosts.filter((p) => p.featured);
  const regular = visiblePosts.filter((p) => !p.featured);

  const handleWriteClick = () => {
    if (!isAuthenticated) {
      toast.error("Please sign in to write a post.");
      navigate("/auth");
      return;
    }
    setShowForm(true);
  };

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-brand/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-5xl px-4 pt-28 pb-20 md:px-6">
        <Reveal className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <BookOpen className="h-3.5 w-3.5" /> Blog
          </span>
          <h1 className="mt-5 text-4xl font-serif font-bold tracking-tight md:text-5xl text-[#1E1F1B]">
            Insights & Resources
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            Expert tips, interview strategies, and career advice to help you land your dream role.
          </p>
          <button
            onClick={handleWriteClick}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-brand/25 transition-all hover:bg-brand/90"
          >
            <PenSquare className="h-4 w-4" /> Write a post
          </button>
        </Reveal>

        {/* Category Pills */}
        <div className="mb-10 flex flex-wrap justify-center gap-2">
          {["All", ...categories].map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={cn(
                "rounded-xl px-4 py-1.5 text-xs font-semibold transition-colors",
                activeCategory === cat
                  ? "bg-brand text-white"
                  : "border border-border bg-muted/50 text-muted-foreground hover:border-primary/30 hover:text-foreground",
              )}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Featured Posts */}
        {featured.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 mb-10">
            {featured.map((post, i) => (
              <Reveal key={post.id} delay={i * 0.08}>
                <SpotlightCard className="group h-full overflow-hidden flex flex-col">
                  {post.coverImage && (
                    <div className="h-56 w-full overflow-hidden border-b border-border bg-muted">
                      <img
                        src={post.coverImage}
                        alt={post.title}
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                    </div>
                  )}
                  <div className="relative p-6 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-4">
                        <span className="inline-flex items-center gap-1.5 rounded-xl bg-brand/15 px-3 py-1 text-[10px] font-semibold text-brand">
                          <Tag className="h-3 w-3" /> {post.category}
                        </span>
                        <div className="rounded-xl bg-brand/10 px-2.5 py-0.5 text-[10px] font-semibold text-brand">Featured</div>
                      </div>
                      <h3 className="text-2xl font-serif tracking-tight leading-snug group-hover:text-brand transition-colors">{post.title}</h3>
                      <p className="mt-3 text-sm text-muted-foreground leading-relaxed line-clamp-3">{post.excerpt}</p>
                    </div>
                    <div className="mt-6 flex items-center gap-3 text-[11px] text-muted-foreground border-t border-border/60 pt-4">
                      <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" /> {post.date}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {post.readTime}</span>
                    </div>
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        )}

        {/* Regular Posts */}
        <div className="grid gap-6 md:grid-cols-3">
          {regular.map((post, i) => (
            <Reveal key={post.id} delay={i * 0.05}>
              <SpotlightCard className="group h-full overflow-hidden flex flex-col">
                {post.coverImage && (
                  <div className="h-44 w-full overflow-hidden border-b border-border bg-muted">
                    <img
                      src={post.coverImage}
                      alt={post.title}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                  </div>
                )}
                <div className="p-5 flex-1 flex flex-col justify-between">
                  <div>
                    <span className="inline-flex items-center gap-2 mb-3">
                      <span className="inline-flex items-center gap-1 rounded-xl bg-muted/70 px-2.5 py-0.5 text-[10px] font-semibold border border-border">
                        <Tag className="h-2.5 w-2.5" /> {post.category}
                      </span>
                      {post.community && (
                        <span className="inline-flex items-center gap-1 rounded-xl bg-brand/10 px-2.5 py-0.5 text-[10px] font-semibold text-brand">
                          <User className="h-2.5 w-2.5" /> {post.author || "Community"}
                        </span>
                      )}
                    </span>
                    <h3 className="text-lg font-serif leading-snug group-hover:text-brand transition-colors line-clamp-2">{post.title}</h3>
                    <p className="mt-2 text-xs text-muted-foreground leading-relaxed line-clamp-3">{post.excerpt}</p>
                  </div>
                  <div className="mt-5 flex items-center justify-between border-t border-border/60 pt-3">
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      {post.date && <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {post.date}</span>}
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {post.readTime}</span>
                    </div>
                    {post.community && (
                      <button
                        onClick={() => setFeedbackFor(post)}
                        className="flex items-center gap-1 rounded-xl bg-brand/10 px-2.5 py-1 text-[10px] font-semibold text-brand hover:bg-brand hover:text-white transition-colors"
                      >
                        <MessageCircle className="h-3 w-3" /> Feedback
                      </button>
                    )}
                  </div>
                </div>
              </SpotlightCard>
            </Reveal>
          ))}
        </div>
        {regular.length === 0 && featured.length === 0 && (
          <p className="text-center text-sm text-muted-foreground py-10">No posts in this category yet.</p>
        )}

        {/* Newsletter CTA */}
        <Reveal className="mt-14 rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/5 via-background to-accent/5 p-8 text-center">
          <h3 className="text-lg font-bold">Stay Updated</h3>
          <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
            Get the latest interview tips and career advice delivered to your inbox every week.
          </p>
          <div className="mt-5 flex items-center justify-center gap-2 max-w-sm mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !subscribing && handleSubscribe()}
              placeholder="your@email.com"
              className="flex-1 rounded-xl border border-border bg-card px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              onClick={handleSubscribe}
              disabled={subscribing}
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-brand/90 disabled:opacity-60"
            >
              {subscribing && <Loader2 className="h-4 w-4 animate-spin" />}
              Subscribe
            </button>
          </div>
        </Reveal>
      </main>

      {showForm && (
        <WritePostModal
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false);
            loadPosts();
          }}
        />
      )}

      {feedbackFor && (
        <FeedbackModal
          post={feedbackFor}
          isAuthenticated={isAuthenticated}
          onSignIn={() => navigate("/auth")}
          onClose={() => setFeedbackFor(null)}
        />
      )}

      <Footer />
    </div>
  );
}

function WritePostModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState(CATEGORY_OPTIONS[0]);
  const [excerpt, setExcerpt] = useState("");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (title.trim().length < 3 || content.trim().length < 10) {
      toast.error("Add a title and some content first.");
      return;
    }
    setSubmitting(true);
    try {
      await createBlogPost({ title: title.trim(), category, excerpt: excerpt.trim(), content: content.trim() });
      toast.success("Post published!");
      onCreated();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to publish post.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-2xl border border-border bg-background p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Write a post</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-5 w-5" /></button>
        </div>
        <div className="space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          >
            {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input
            value={excerpt}
            onChange={(e) => setExcerpt(e.target.value)}
            placeholder="Short summary (optional)"
            className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your post…"
            rows={8}
            className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
          />
          <button
            onClick={submit}
            disabled={submitting}
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-brand/90 disabled:opacity-60"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <PenSquare className="h-4 w-4" />}
            Publish
          </button>
        </div>
      </div>
    </div>
  );
}

function FeedbackModal({
  post,
  isAuthenticated,
  onSignIn,
  onClose,
}: {
  post: DisplayPost;
  isAuthenticated: boolean;
  onSignIn: () => void;
  onClose: () => void;
}) {
  const [items, setItems] = useState<BlogFeedback[]>([]);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    fetchBlogFeedback(post.id).then(setItems).catch(() => {/* ignore */});
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [post.id]);

  const submit = async () => {
    if (!isAuthenticated) {
      toast.error("Please sign in to leave feedback.");
      onSignIn();
      return;
    }
    setSubmitting(true);
    try {
      await submitBlogFeedback(post.id, { rating, comment: comment.trim() });
      toast.success("Thanks for your feedback!");
      setComment("");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-2xl border border-border bg-background p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-lg font-bold line-clamp-1">{post.title}</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="h-5 w-5" /></button>
        </div>
        <p className="text-xs text-muted-foreground mb-4">Feedback from readers</p>

        <div className="space-y-3 mb-5">
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} onClick={() => setRating(n)} aria-label={`${n} star`}>
                <Star className={cn("h-6 w-6", n <= rating ? "fill-brand text-brand" : "text-muted-foreground")} />
              </button>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Share your thoughts…"
            rows={3}
            className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
          />
          <button
            onClick={submit}
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-brand/90 disabled:opacity-60"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageCircle className="h-4 w-4" />}
            Submit feedback
          </button>
        </div>

        <div className="space-y-3 border-t border-border pt-4">
          {items.length === 0 && <p className="text-sm text-muted-foreground">No feedback yet. Be the first!</p>}
          {items.map((f) => (
            <div key={f.id} className="rounded-xl border border-border bg-muted/30 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{f.author_name}</span>
                <span className="flex items-center gap-0.5">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <Star key={n} className={cn("h-3.5 w-3.5", n <= f.rating ? "fill-brand text-brand" : "text-muted-foreground")} />
                  ))}
                </span>
              </div>
              {f.comment && <p className="mt-1.5 text-sm text-muted-foreground">{f.comment}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
