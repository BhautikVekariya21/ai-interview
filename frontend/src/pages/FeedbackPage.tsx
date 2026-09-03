import { useEffect, useState } from "react";
import { MessageSquareHeart, Star, Loader2, PenSquare, User, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";
import Reveal from "@/components/motion/Reveal";
import Loading from "@/components/Loading";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/AuthProvider";
import { fetchAppReviews, submitAppReview, type AppReview } from "@/lib/api";
import Seo from "@/components/Seo";

function formatDate(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

function Stars({ value, size = "h-4 w-4" }: { value: number; size?: string }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star key={n} className={cn(size, n <= Math.round(value) ? "fill-brand text-brand" : "text-muted-foreground/40")} />
      ))}
    </span>
  );
}

export default function FeedbackPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [reviews, setReviews] = useState<AppReview[]>([]);
  const [total, setTotal] = useState(0);
  const [average, setAverage] = useState(0);
  const [loading, setLoading] = useState(true);

  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [title, setTitle] = useState("");
  const [review, setReview] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    fetchAppReviews()
      .then((data) => {
        setReviews(data.items);
        setTotal(data.total);
        setAverage(data.average);
      })
      .catch(() => {/* public read; ignore transient errors */})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async () => {
    if (!isAuthenticated) {
      toast.error("Please sign in to write a review.");
      navigate("/auth");
      return;
    }
    if (rating === 0) {
      toast.error("Pick a star rating first.");
      return;
    }
    if (review.trim().length < 5) {
      toast.error("Tell us a bit more in your review.");
      return;
    }
    setSubmitting(true);
    try {
      await submitAppReview({ rating, title: title.trim(), review: review.trim() });
      toast.success("Thanks for your review!");
      setRating(0);
      setTitle("");
      setReview("");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to submit review.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <Seo
        title="Feedback Forum"
        description="Share your feedback on interviewer.ai and read what other users think. Your reviews help shape the future of AI-powered interview practice."
        path="/feedback"
      />
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-brand/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-4xl px-4 pt-28 pb-20 md:px-6">
        <Reveal className="mb-10 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <MessageSquareHeart className="h-3.5 w-3.5" /> Feedback
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Feedback <span className="text-foreground">Forum</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            Tell us how interviewer.ai is working for you — rate your experience and read what others think.
          </p>
          {total > 0 && (
            <div className="mt-5 inline-flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-3">
              <span className="text-3xl font-extrabold tabular-nums">{average.toFixed(1)}</span>
              <div className="text-left">
                <Stars value={average} />
                <p className="mt-0.5 text-xs text-muted-foreground">{total} review{total === 1 ? "" : "s"}</p>
              </div>
            </div>
          )}
        </Reveal>

        {/* Write a review */}
        <Reveal className="mb-10 rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <PenSquare className="h-4 w-4 text-brand" /> Write a review
          </h2>
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-1" onMouseLeave={() => setHoverRating(0)}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  onClick={() => setRating(n)}
                  onMouseEnter={() => setHoverRating(n)}
                  aria-label={`${n} star${n === 1 ? "" : "s"}`}
                >
                  <Star
                    className={cn(
                      "h-8 w-8 transition-colors",
                      n <= (hoverRating || rating) ? "fill-brand text-brand" : "text-muted-foreground/40 hover:text-brand/60",
                    )}
                  />
                </button>
              ))}
              {rating > 0 && (
                <span className="ml-2 text-sm font-semibold text-muted-foreground">
                  {["", "Poor", "Fair", "Good", "Very good", "Excellent"][rating]}
                </span>
              )}
            </div>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Review title (optional)"
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <textarea
              value={review}
              onChange={(e) => setReview(e.target.value)}
              placeholder="What did you like? What could be better?"
              rows={4}
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
            />
            <button
              onClick={submit}
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-brand/25 transition-all hover:bg-brand/90 disabled:opacity-60"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageSquareHeart className="h-4 w-4" />}
              Post review
            </button>
            {!isAuthenticated && (
              <p className="text-xs text-muted-foreground">You'll be asked to sign in before posting.</p>
            )}
          </div>
        </Reveal>

        {/* Reviews */}
        <div className="space-y-4">
          {loading ? (
            <div className="py-16">
              <Loading size="lg" label="Loading reviews…" />
            </div>
          ) : reviews.length === 0 ? (
            <p className="py-16 text-center text-sm text-muted-foreground">No reviews yet — be the first to share your experience.</p>
          ) : (
            reviews.map((r, i) => (
              <Reveal key={r.id} delay={i * 0.04}>
                <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand/10 text-brand">
                        <User className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">{r.author_name}</p>
                        {r.created_at && (
                          <p className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" /> {formatDate(r.created_at)}
                          </p>
                        )}
                      </div>
                    </div>
                    <Stars value={r.rating} />
                  </div>
                  {r.title && <h3 className="mt-3 text-base font-bold tracking-tight">{r.title}</h3>}
                  <p className="mt-1.5 text-sm leading-6 text-muted-foreground">{r.review}</p>
                </div>
              </Reveal>
            ))
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
