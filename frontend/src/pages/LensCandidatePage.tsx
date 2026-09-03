import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { m as motion } from "framer-motion";
import {
  Building2,
  Loader2,
  Link2Off,
  ArrowLeft,
  ArrowRight,
  Send,
  Clock,
  FileQuestion,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import Seo from "@/components/Seo";
import LensScorecard from "@/components/LensScorecard";
import {
  fetchLensShareExam,
  submitLensExam,
  type LensScorecard as LensScorecardData,
  type LensShareExam,
} from "@/lib/api";

const CATEGORY_NAMES: Record<string, string> = {
  T: "Technical",
  P: "Project",
  B: "Behavioral",
  C: "Conceptual",
  R: "Role Fit",
};

type Phase = "loading" | "error" | "intro" | "taking" | "submitting" | "done";

export default function LensCandidatePage() {
  const { token = "" } = useParams<{ token: string }>();
  const [phase, setPhase] = useState<Phase>("loading");
  const [exam, setExam] = useState<LensShareExam | null>(null);
  const [candidateName, setCandidateName] = useState("");
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [scorecard, setScorecard] = useState<LensScorecardData | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      setPhase("error");
      return;
    }
    fetchLensShareExam(token)
      .then((result) => {
        if (cancelled) return;
        setExam(result);
        setPhase("intro");
      })
      .catch(() => {
        if (!cancelled) setPhase("error");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const questions = useMemo(() => exam?.questions ?? [], [exam]);

  const startExam = () => {
    if (!candidateName.trim()) return;
    setAnswers({});
    setCurrentIndex(0);
    setPhase("taking");
  };

  const submit = async () => {
    if (!exam) return;
    setPhase("submitting");
    try {
      const result = await submitLensExam(token, {
        candidate_name: candidateName.trim(),
        answers: questions.map((question) => ({
          question_number: question.question_number,
          answer: answers[question.question_number] ?? "",
        })),
      });
      setScorecard(result.scorecard);
      setPhase("done");
    } catch {
      toast.error("Could not submit the exam. Check your connection and try again.");
      setPhase("taking");
    }
  };

  const current = questions[currentIndex];
  const answeredCount = questions.filter(
    (question) => (answers[question.question_number] ?? "").trim().length > 0,
  ).length;

  /* ── Loading ────────────────────────────────────────────────────── */
  if (phase === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin text-brand" /> Loading exam…
        </div>
      </div>
    );
  }

  /* ── Error ──────────────────────────────────────────────────────── */
  if (phase === "error" || !exam) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-6">
        <div className="max-w-md w-full text-center">
          <Link2Off className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h1 className="text-xl font-bold text-foreground mb-2">Exam link not found</h1>
          <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
            This link is invalid or the exam is no longer accepting candidates.
            Ask the employer to share the exam link again.
          </p>
          <Link to="/">
            <Button variant="outline">Go to interviewer.ai</Button>
          </Link>
        </div>
      </div>
    );
  }

  /* ── Done (scorecard) ───────────────────────────────────────────── */
  if (phase === "done" && scorecard) {
    return (
      <div className="min-h-screen bg-background py-10 px-4">
        <Seo title={`Exam result — ${scorecard.candidate_name}`} noindex />
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-6">
            <motion.div
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 14 }}
              className="w-14 h-14 rounded-2xl bg-success/10 border border-success/25 text-success flex items-center justify-center mx-auto mb-3"
            >
              <CheckCircle2 className="w-7 h-7" />
            </motion.div>
            <h1 className="text-2xl font-sans font-bold text-foreground">
              Exam submitted
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Your standardized scorecard is ready — the employer can see it on
              their dashboard.
            </p>
          </div>
          <LensScorecard scorecard={scorecard} />
          <div className="mt-6 text-center">
            <Link to="/">
              <Button variant="outline">Back to interviewer.ai</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  /* ── Intro ──────────────────────────────────────────────────────── */
  if (phase === "intro") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-6">
        <Seo title={`${exam.title} — Interview exam`} noindex />
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg w-full"
        >
          <div className="rounded-3xl border border-border bg-card shadow-lg overflow-hidden">
            <div className="h-1.5 w-full bg-gradient-to-r from-brand via-brand/60 to-brand/20" />
            <div className="p-8">
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">
                <Building2 className="w-3.5 h-3.5 text-brand" /> Standardized interview exam
              </div>
              <h1 className="text-2xl font-sans font-bold text-foreground mb-1">
                {exam.title}
              </h1>
              {exam.target_role && (
                <p className="text-sm text-muted-foreground mb-5">{exam.target_role}</p>
              )}
              <div className="grid grid-cols-3 gap-2 mb-6">
                {[
                  { icon: <FileQuestion className="w-3.5 h-3.5" />, label: `${exam.question_count} questions` },
                  { icon: <Clock className="w-3.5 h-3.5" />, label: "Self-paced" },
                  { icon: <Sparkles className="w-3.5 h-3.5" />, label: exam.difficulty },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="rounded-xl border border-border bg-muted/20 px-3 py-2.5 text-center"
                  >
                    <span className="text-brand flex items-center justify-center mb-1">
                      {item.icon}
                    </span>
                    <span className="text-[10px] font-semibold text-muted-foreground capitalize">
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
              <label className="block mb-6">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Your name
                </span>
                <input
                  value={candidateName}
                  onChange={(event) => setCandidateName(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && candidateName.trim()) startExam();
                  }}
                  placeholder="e.g. Alex Chen"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
                />
              </label>
              <Button
                className="w-full"
                size="lg"
                disabled={!candidateName.trim()}
                onClick={startExam}
              >
                Start exam
              </Button>
              <p className="text-[10px] text-muted-foreground text-center mt-4 leading-relaxed">
                Answer honestly and specifically. Your answers are evaluated
                against the same rubric as every other candidate.
              </p>
            </div>
          </div>
          <Link
            to="/exams"
            className="mt-5 flex items-center justify-center gap-1.5 text-[11px] font-semibold text-muted-foreground hover:text-brand transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Looking for another role? Browse all practice exams
          </Link>
        </motion.div>
      </div>
    );
  }

  /* ── Taking ─────────────────────────────────────────────────────── */
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <Seo title={`${exam.title} — Taking exam`} noindex />
      <div className="max-w-2xl w-full">
        {/* Progress */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-[11px] text-muted-foreground mb-1.5">
            <span className="font-semibold">
              Question {currentIndex + 1} of {questions.length}
            </span>
            <span>{answeredCount} answered</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-brand transition-all duration-500"
              style={{ width: `${(currentIndex / Math.max(questions.length, 1)) * 100}%` }}
            />
          </div>
        </div>

        {current && (
          <motion.div
            key={current.question_number}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            className="rounded-3xl border border-border bg-card shadow-sm p-6"
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full bg-brand/10 border border-brand/20 text-brand">
                {CATEGORY_NAMES[current.category] ?? current.category}
              </span>
              <span className="text-[10px] font-semibold px-2 py-1 rounded-full bg-muted border border-border text-muted-foreground capitalize">
                {current.difficulty}
              </span>
            </div>
            <h2 className="text-lg font-sans font-bold text-foreground leading-relaxed mb-4">
              {current.question}
            </h2>
            <textarea
              value={answers[current.question_number] ?? ""}
              onChange={(event) =>
                setAnswers((prev) => ({
                  ...prev,
                  [current.question_number]: event.target.value,
                }))
              }
              rows={8}
              placeholder="Type your answer… (be specific — concrete examples and reasoning score highest)"
              className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-brand/30 resize-y"
              autoFocus
            />
            <div className="flex items-center justify-between gap-3 mt-4">
              <Button
                variant="outline"
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((index) => index - 1)}
              >
                <ArrowLeft className="w-4 h-4" /> Previous
              </Button>
              {currentIndex < questions.length - 1 ? (
                <Button onClick={() => setCurrentIndex((index) => index + 1)}>
                  Next <ArrowRight className="w-4 h-4" />
                </Button>
              ) : (
                <Button
                  onClick={submit}
                  disabled={phase === "submitting"}
                  className="bg-success hover:bg-success/90"
                >
                  {phase === "submitting" ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  {phase === "submitting" ? "Scoring…" : "Submit exam"}
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
