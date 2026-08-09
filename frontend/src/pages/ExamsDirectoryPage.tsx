import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { m as motion } from "framer-motion";
import {
  ArrowRight,
  Building2,
  FileQuestion,
  Loader2,
  Search,
  SearchX,
  Sparkles,
  Users,
} from "lucide-react";
import Seo from "@/components/Seo";
import { listPublishedLensExams, type LensExamSummary } from "@/lib/api";

const DIFFICULTY_TONES: Record<string, string> = {
  easy: "text-emerald-600 bg-emerald-500/10 border-emerald-500/25",
  medium: "text-amber-600 bg-amber-500/10 border-amber-500/25",
  hard: "text-rose-600 bg-rose-500/10 border-rose-500/25",
  expert: "text-violet-600 bg-violet-500/10 border-violet-500/25",
};

const EASE = [0.16, 1, 0.3, 1] as const;

function formatDate(iso?: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export default function ExamsDirectoryPage() {
  const [exams, setExams] = useState<LensExamSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const requestId = useRef(0);

  // Debounce the search box so typing doesn't fire a request per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query.trim()), 350);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const id = ++requestId.current;
    setLoading(true);
    listPublishedLensExams(debouncedQuery || undefined)
      .then((items) => {
        if (requestId.current !== id) return;
        setExams(items);
        setError(false);
      })
      .catch(() => {
        if (requestId.current !== id) return;
        setError(true);
      })
      .finally(() => {
        if (requestId.current === id) setLoading(false);
      });
  }, [debouncedQuery, refreshKey]);

  const totalAttempts = exams.reduce((sum, exam) => sum + (exam.attempts ?? 0), 0);
  const searching = debouncedQuery.length > 0;
  const showEmpty = !loading && !error && exams.length === 0;

  return (
    <div>
      <Seo title="Interview exams — practice with real job-description questions" />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <div className="text-center mb-10">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE }}
        >
          <div className="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-muted-foreground mb-4 px-3 py-1.5 rounded-full border border-border bg-card/60">
            <Building2 className="w-3.5 h-3.5 text-brand" /> Company Lens · exam directory
          </div>
          <h1 className="text-4xl md:text-5xl font-sans font-bold tracking-tight text-foreground">
            Practice exams from
            <span className="text-brand"> real job descriptions</span>
          </h1>
          <p className="text-sm md:text-base text-muted-foreground max-w-xl mx-auto mt-4 leading-relaxed">
            Employers publish standardized interview exams grounded in the
            roles they hire for. Find one, take it, and get the same scorecard
            every other candidate receives — no account needed.
          </p>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08, ease: EASE }}
          className="max-w-lg mx-auto mt-8"
        >
          <div className="relative">
            <Search className="w-4 h-4 text-muted-foreground absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by role — e.g. platform engineer, data analyst…"
              className="w-full rounded-full border border-border bg-card/70 backdrop-blur px-11 py-3.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand/40 transition-shadow shadow-sm"
            />
            {loading && (
              <Loader2 className="w-4 h-4 animate-spin text-brand absolute right-4 top-1/2 -translate-y-1/2" />
            )}
          </div>
          <p className="text-[11px] text-muted-foreground mt-2.5">
            {searching
              ? `${exams.length} exam${exams.length === 1 ? "" : "s"} match${exams.length === 1 ? "es" : ""} “${debouncedQuery}”`
              : `${exams.length} published exam${exams.length === 1 ? "" : "s"} · ${totalAttempts} candidate${totalAttempts === 1 ? "" : "s"} scored`}
          </p>
        </motion.div>
      </div>

      {/* ── Error ────────────────────────────────────────────────────── */}
      {error && !loading && (
        <div className="rounded-2xl border border-border bg-card/60 p-10 text-center">
          <SearchX className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <h2 className="text-lg font-bold text-foreground mb-2">
            Couldn't load the directory
          </h2>
          <p className="text-sm text-muted-foreground mb-5">
            Something went wrong reaching the exam directory. Check your
            connection and try again.
          </p>
          <button
            onClick={() => setRefreshKey((key) => key + 1)}
            className="text-sm font-semibold text-brand hover:text-brand-hover transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Loading skeleton ─────────────────────────────────────────── */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[0, 1, 2].map((index) => (
            <div
              key={index}
              className="rounded-2xl border border-border bg-card p-6 animate-pulse"
            >
              <div className="h-8 w-8 rounded-xl bg-muted mb-4" />
              <div className="h-5 w-3/4 bg-muted rounded mb-3" />
              <div className="h-3.5 w-1/2 bg-muted rounded mb-5" />
              <div className="flex gap-2 mb-6">
                <div className="h-6 w-20 bg-muted rounded-full" />
                <div className="h-6 w-20 bg-muted rounded-full" />
              </div>
              <div className="h-4 w-1/3 bg-muted rounded" />
            </div>
          ))}
        </div>
      )}

      {/* ── Empty states ─────────────────────────────────────────────── */}
      {showEmpty && (
        <div className="rounded-2xl border border-dashed border-border bg-card/40 p-12 text-center">
          {searching ? (
            <>
              <SearchX className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <h2 className="text-lg font-bold text-foreground mb-2">
                No exams match “{debouncedQuery}”
              </h2>
              <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6 leading-relaxed">
                Try a broader role phrase, or browse the full directory.
              </p>
              <button
                onClick={() => setQuery("")}
                className="text-sm font-semibold text-brand hover:text-brand-hover transition-colors"
              >
                Clear search
              </button>
            </>
          ) : (
            <>
              <Sparkles className="w-10 h-10 text-brand/60 mx-auto mb-3" />
              <h2 className="text-lg font-bold text-foreground mb-2">
                No published exams yet
              </h2>
              <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6 leading-relaxed">
                Employers publish exams here from a job description — check
                back soon, or publish one yourself from the dashboard.
              </p>
              <Link
                to="/app/exams"
                className="inline-flex items-center gap-2 text-sm font-semibold text-brand hover:text-brand-hover transition-colors"
              >
                Create an exam <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          )}
        </div>
      )}

      {/* ── Cards ────────────────────────────────────────────────────── */}
      {!loading && !error && exams.length > 0 && (
        <motion.div
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.05 } } }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {exams.map((exam) => (
            <motion.div
              key={exam.id}
              variants={{
                hidden: { opacity: 0, y: 14 },
                show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE } },
              }}
            >
              <Link
                to={`/lens/${exam.share_token ?? exam.id}`}
                className="group flex h-full flex-col rounded-2xl border border-border bg-card/70 hover:bg-card transition-colors shadow-sm hover:shadow-md p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="w-9 h-9 rounded-xl bg-brand/10 text-brand flex items-center justify-center">
                    <Building2 className="w-4 h-4" />
                  </span>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border capitalize ${
                      DIFFICULTY_TONES[exam.difficulty] ??
                      "text-muted-foreground bg-muted border-border"
                    }`}
                  >
                    {exam.difficulty}
                  </span>
                </div>

                <h3 className="text-[15px] font-sans font-bold text-foreground leading-snug mb-1 group-hover:text-brand transition-colors">
                  {exam.title}
                </h3>
                {exam.target_role ? (
                  <p className="text-xs text-muted-foreground mb-4">
                    {exam.target_role}
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground/60 italic mb-4">
                    Role not specified
                  </p>
                )}

                <div className="mt-auto">
                  <div className="flex items-center gap-3 text-[11px] text-muted-foreground mb-4">
                    <span className="inline-flex items-center gap-1.5">
                      <FileQuestion className="w-3.5 h-3.5" />
                      {exam.question_count} questions
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5" />
                      {exam.attempts && exam.attempts > 0
                        ? `${exam.attempts} scored`
                        : "No candidates yet"}
                    </span>
                    {exam.created_at && (
                      <span className="ml-auto text-muted-foreground/70">
                        {formatDate(exam.created_at)}
                      </span>
                    )}
                  </div>
                  <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand">
                    Take the exam
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
