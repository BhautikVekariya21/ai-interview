import { useCallback, useEffect, useState } from "react";
import { m as motion } from "framer-motion";
import {
  Building2,
  Plus,
  Loader2,
  Trash2,
  Link2,
  Copy,
  FileQuestion,
  Users,
  ArrowLeft,
  X,
} from "lucide-react";
import { toast } from "sonner";
import LensScorecard from "./LensScorecard";
import {
  createLensExam,
  deleteLensExam,
  fetchLensAttemptScorecard,
  getLensExam,
  listLensExams,
  publishLensExam,
  type LensExamDetail,
  type LensExamSummary,
  type LensScorecard as LensScorecardData,
} from "@/lib/api";

const CATEGORY_NAMES: Record<string, string> = {
  T: "Technical",
  P: "Project",
  B: "Behavioral",
  C: "Conceptual",
  R: "Role Fit",
};

export default function CompanyLens() {
  const [exams, setExams] = useState<LensExamSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<LensExamDetail | null>(null);
  const [scorecard, setScorecard] = useState<LensScorecardData | null>(null);
  const [scorecardLoading, setScorecardLoading] = useState(false);

  // Create form state
  const [title, setTitle] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [questionCount, setQuestionCount] = useState(10);
  const [difficulty, setDifficulty] = useState("medium");

  const refresh = useCallback(async () => {
    try {
      const list = await listLensExams();
      setExams(list);
    } catch {
      toast.error("Could not load your exams.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const openDetail = useCallback(async (id: string) => {
    setScorecard(null);
    setScorecardLoading(false);
    try {
      const detail = await getLensExam(id);
      setSelected(detail);
    } catch {
      toast.error("Could not load the exam.");
    }
  }, []);

  const handleCreate = async () => {
    if (!title.trim() || jobDescription.trim().length < 20) {
      toast.error("Give the exam a title and a job description of at least 20 characters.");
      return;
    }
    setCreating(true);
    try {
      const detail = await createLensExam({
        title: title.trim(),
        target_role: targetRole.trim(),
        job_description: jobDescription.trim(),
        question_count: questionCount,
        difficulty,
      });
      setShowCreate(false);
      setTitle("");
      setTargetRole("");
      setJobDescription("");
      setQuestionCount(10);
      setDifficulty("medium");
      await refresh();
      setSelected(detail);
      toast.success(`Exam "${detail.title}" generated with ${detail.questions.length} questions.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not create the exam.");
    } finally {
      setCreating(false);
    }
  };

  const handlePublish = async (id: string) => {
    let token = "";
    try {
      ({ token } = await publishLensExam(id));
    } catch {
      toast.error("Could not publish the exam.");
      return;
    }
    // Refresh first so the card/detail flips to "published" regardless of
    // whether the clipboard copy below succeeds.
    if (selected?.id === id) {
      await openDetail(id);
    } else {
      await refresh();
    }
    // Clipboard copy is best-effort — the publish itself already succeeded.
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/lens/${token}`);
      toast.success("Exam published — candidate link copied to clipboard.");
    } catch {
      toast.error("Exam published, but the link could not be copied — copy it from the exam page.");
    }
  };

  const copyShareLink = async (token: string) => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/lens/${token}`);
      toast.success("Candidate link copied.");
    } catch {
      toast.error("Could not copy the link.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Delete this exam and all of its attempts? This cannot be undone.")) {
      return;
    }
    try {
      await deleteLensExam(id);
      if (selected?.id === id) {
        setSelected(null);
      }
      toast.success("Exam deleted.");
      await refresh();
    } catch {
      toast.error("Could not delete the exam.");
    }
  };

  const viewScorecard = async (attemptToken: string) => {
    if (!attemptToken) return;
    setScorecardLoading(true);
    setScorecard(null);
    try {
      const { scorecard: card } = await fetchLensAttemptScorecard(attemptToken);
      setScorecard(card);
    } catch {
      toast.error("Could not load that scorecard.");
    } finally {
      setScorecardLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-3 text-sm text-muted-foreground py-16 justify-center">
        <Loader2 className="w-4 h-4 animate-spin text-brand" /> Loading your exams…
      </div>
    );
  }

  /* ── Detail view ─────────────────────────────────────────────────── */
  if (selected) {
    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => {
              setSelected(null);
              setScorecard(null);
            }}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> All exams
          </button>
          {selected.share_token && (
            <button
              type="button"
              onClick={() => selected.share_token && copyShareLink(selected.share_token)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-brand/10 border border-brand/20 text-brand hover:bg-brand/15 transition-colors"
            >
              <Link2 className="w-3.5 h-3.5" /> Copy candidate link
            </button>
          )}
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  {selected.target_role || "Untitled role"} · {selected.difficulty} ·{" "}
                  {selected.question_count} questions
                </span>
                <span
                  className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                    selected.status === "published"
                      ? "bg-success/10 border border-success/25 text-success"
                      : "bg-muted border border-border text-muted-foreground"
                  }`}
                >
                  {selected.status}
                </span>
              </div>
              <h2 className="text-2xl font-sans font-bold text-foreground">{selected.title}</h2>
              {selected.job_description && (
                <p className="text-xs text-muted-foreground leading-relaxed mt-2 max-w-2xl line-clamp-3">
                  {selected.job_description}
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {selected.status !== "published" && (
                <button
                  type="button"
                  onClick={() => handlePublish(selected.id)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg bg-brand text-brand-foreground hover:bg-brand-hover transition-colors"
                >
                  <Link2 className="w-3.5 h-3.5" /> Publish & copy link
                </button>
              )}
              <button
                type="button"
                onClick={() => handleDelete(selected.id)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg bg-destructive/10 border border-destructive/25 text-destructive hover:bg-destructive/15 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" /> Delete
              </button>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-5">
          {/* Questions */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
              <FileQuestion className="w-3.5 h-3.5" /> Questions ({selected.questions.length})
            </h3>
            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {selected.questions.map((question) => (
                <div key={question.id} className="rounded-xl border border-border bg-muted/20 p-3">
                  <div className="flex items-start gap-2.5">
                    <span className="w-6 h-6 rounded-md bg-brand/10 text-brand text-[10px] font-bold flex items-center justify-center shrink-0">
                      {question.question_number}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-foreground leading-relaxed">
                        {question.question}
                      </p>
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-muted border border-border text-muted-foreground">
                          {CATEGORY_NAMES[question.category] ?? question.category}
                        </span>
                        <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-muted border border-border text-muted-foreground capitalize">
                          {question.difficulty}
                        </span>
                        {question.ideal_answer && (
                          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-brand/10 border border-brand/20 text-brand">
                            ideal answer included
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Attempts */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5" /> Candidates ({selected.attempts.length})
            </h3>
            {selected.attempts.length === 0 && (
              <p className="text-xs text-muted-foreground leading-relaxed">
                No attempts yet. Publish the exam and share the link — every candidate
                gets the same standardized scorecard.
              </p>
            )}
            <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
              {selected.attempts.map((attempt) => (
                <button
                  key={attempt.id}
                  type="button"
                  onClick={() => attempt.attempt_token && viewScorecard(attempt.attempt_token)}
                  className="w-full rounded-xl border border-border bg-muted/20 p-3 text-left hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-foreground truncate">
                        {attempt.candidate_name}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {attempt.recommendation}
                        {attempt.created_at
                          ? ` · ${new Date(attempt.created_at).toLocaleDateString()}`
                          : ""}
                      </p>
                    </div>
                    <span className="shrink-0">
                      <span className="text-base font-extrabold font-mono text-foreground">
                        {attempt.overall_score}%
                      </span>
                      <span className="ml-1.5 text-[10px] font-bold px-1.5 py-0.5 rounded bg-muted border border-border text-muted-foreground">
                        {attempt.overall_grade}
                      </span>
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {scorecardLoading && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground py-10 justify-center">
            <Loader2 className="w-4 h-4 animate-spin text-brand" /> Loading scorecard…
          </div>
        )}
        {scorecard && <LensScorecard scorecard={scorecard} />}
      </div>
    );
  }

  /* ── List view ───────────────────────────────────────────────────── */
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-bold text-foreground">
            <Building2 className="w-4 h-4 text-brand" /> Company Lens
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-xl leading-relaxed">
            Paste a job description and get a standardized interview exam. Every
            candidate takes the same questions, so their scorecards are directly
            comparable.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate((value) => !value)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg bg-brand text-brand-foreground hover:bg-brand-hover transition-colors"
        >
          {showCreate ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
          {showCreate ? "Cancel" : "New exam"}
        </button>
      </div>

      {showCreate && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-border bg-card p-5 space-y-3"
        >
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="block">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Exam title
              </span>
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="e.g. Senior Platform Engineer — Screening"
                className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
              />
            </label>
            <label className="block">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Target role
              </span>
              <input
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
                placeholder="e.g. Platform Engineer"
                className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
              />
            </label>
          </div>
          <label className="block">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Job description
            </span>
            <textarea
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              rows={6}
              placeholder="Paste the job description — the exam questions are generated from it."
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 resize-y"
            />
          </label>
          <div className="flex flex-wrap items-end gap-4">
            <label className="block">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Questions ({questionCount})
              </span>
              <input
                type="range"
                min={3}
                max={20}
                value={questionCount}
                onChange={(event) => setQuestionCount(Number(event.target.value))}
                className="mt-2 block w-44 accent-brand"
              />
            </label>
            <label className="block">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Difficulty
              </span>
              <select
                value={difficulty}
                onChange={(event) => setDifficulty(event.target.value)}
                className="mt-1 rounded-lg border border-border bg-background px-3 py-2 text-sm capitalize focus:outline-none focus:ring-2 focus:ring-brand/30"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
                <option value="expert">Expert</option>
              </select>
            </label>
            <button
              type="button"
              onClick={handleCreate}
              disabled={creating}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2.5 rounded-lg bg-brand text-brand-foreground hover:bg-brand-hover disabled:opacity-60 transition-colors"
            >
              {creating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Plus className="w-3.5 h-3.5" />
              )}
              {creating ? "Generating…" : "Generate exam"}
            </button>
          </div>
        </motion.div>
      )}

      {exams.length === 0 && !showCreate ? (
        <div className="rounded-2xl border border-dashed border-border bg-card/40 p-12 text-center">
          <Building2 className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <h3 className="text-base font-bold text-foreground mb-1">No exams yet</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
            Create your first exam from a job description. Candidates answer the
            same questions and get a standardized, comparable scorecard.
          </p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {exams.map((exam) => (
            <motion.div
              key={exam.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-border bg-card p-5 flex flex-col gap-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                    {exam.target_role || "Untitled role"} · {exam.difficulty}
                  </p>
                  <h3 className="text-base font-bold text-foreground truncate">{exam.title}</h3>
                </div>
                <span
                  className={`text-[9px] font-bold uppercase px-2 py-1 rounded shrink-0 ${
                    exam.status === "published"
                      ? "bg-success/10 border border-success/25 text-success"
                      : "bg-muted border border-border text-muted-foreground"
                  }`}
                >
                  {exam.status}
                </span>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <FileQuestion className="w-3 h-3" /> {exam.question_count} questions
                </span>
                <span className="inline-flex items-center gap-1">
                  <Users className="w-3 h-3" /> {exam.attempts} candidate{exam.attempts === 1 ? "" : "s"}
                </span>
              </div>
              <div className="flex flex-wrap gap-2 mt-auto pt-1">
                <button
                  type="button"
                  onClick={() => void openDetail(exam.id)}
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-muted border border-border hover:bg-accent transition-colors"
                >
                  View
                </button>
                {exam.status === "published" && exam.share_token ? (
                  <button
                    type="button"
                    onClick={() => copyShareLink(exam.share_token!)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-brand/10 border border-brand/20 text-brand hover:bg-brand/15 transition-colors"
                  >
                    <Copy className="w-3 h-3" /> Copy link
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => handlePublish(exam.id)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-brand text-brand-foreground hover:bg-brand-hover transition-colors"
                  >
                    <Link2 className="w-3 h-3" /> Publish
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleDelete(exam.id)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-destructive/10 border border-destructive/25 text-destructive hover:bg-destructive/15 transition-colors ml-auto"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
