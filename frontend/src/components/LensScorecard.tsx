import { useState } from "react";
import { m as motion } from "framer-motion";
import {
  Trophy,
  MessageSquare,
  ScanSearch,
  ChevronDown,
  ChevronUp,
  BadgeCheck,
  Building2,
  Sparkles,
} from "lucide-react";
import type { LensScorecard as LensScorecardData } from "@/lib/api";

const CATEGORY_NAMES: Record<string, string> = {
  T: "Technical",
  P: "Project",
  B: "Behavioral",
  C: "Conceptual",
  R: "Role Fit",
};

function scoreColor(score: number): string {
  if (score >= 80) return "var(--success-color)";
  if (score >= 60) return "var(--warning-color)";
  return "var(--destructive-color)";
}

function hireChip(decision: string): string {
  if (decision === "hire")
    return "bg-success/10 border-success/30 text-success";
  if (decision === "consider")
    return "bg-amber-500/10 border-amber-500/30 text-amber-600";
  return "bg-destructive/10 border-destructive/30 text-destructive";
}

function ScoreRing({ score, size = 104 }: { score: number; size?: number }) {
  const strokeWidth = 8;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="-rotate-90 w-full h-full">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="fill-none stroke-muted"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="fill-none"
          stroke={scoreColor(score)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1.2s ease" }}
        />
      </svg>
      <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-xl font-extrabold font-mono">
        {score}%
      </span>
    </div>
  );
}

export default function LensScorecard({ scorecard }: { scorecard: LensScorecardData }) {
  const [openAnswers, setOpenAnswers] = useState<Record<number, boolean>>({});
  const categories = Object.entries(scorecard.category_breakdown || {}).sort(
    (a, b) => b[1] - a[1],
  );
  const plagiarism = scorecard.plagiarism_summary;

  const toggle = (questionNumber: number) =>
    setOpenAnswers((prev) => ({ ...prev, [questionNumber]: !prev[questionNumber] }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Header */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-center gap-6">
          <ScoreRing score={scorecard.overall_score} />
          <div className="flex-1 min-w-[220px]">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Building2 className="w-3 h-3" /> {scorecard.exam_title}
              </span>
              {scorecard.generated_by === "fallback" && (
                <span
                  title="Scored by the deterministic fallback — no LLM provider was reachable"
                  className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-muted border border-border text-muted-foreground"
                >
                  heuristic grade
                </span>
              )}
            </div>
            <h3 className="text-xl font-sans font-bold text-foreground mb-2">
              {scorecard.candidate_name}
              <span className="text-muted-foreground font-normal text-base">
                {" "}· {scorecard.overall_grade}
              </span>
            </h3>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-brand/10 border border-brand/20 text-brand">
                <Sparkles className="w-3 h-3" /> {scorecard.recommendation}
              </span>
              <span
                className={`inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full border capitalize ${hireChip(scorecard.hire_decision)}`}
              >
                <BadgeCheck className="w-3 h-3" /> {scorecard.hire_decision.replace("_", " ")}
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-muted border border-border text-muted-foreground">
                <MessageSquare className="w-3 h-3" />{" "}
                {scorecard.answered_questions}/{scorecard.total_questions} answered
              </span>
            </div>
            {scorecard.summary && (
              <p className="text-xs text-muted-foreground leading-relaxed mt-3">
                {scorecard.summary}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Category breakdown */}
      {categories.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">
            Standardized category scores
          </h4>
          <div className="space-y-3">
            {categories.map(([category, score], index) => (
              <div key={category}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-foreground">
                    {CATEGORY_NAMES[category] ?? category}
                  </span>
                  <span className="text-xs font-bold font-mono">{score}%</span>
                </div>
                <div className="h-2 bg-muted rounded-xl overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${score}%` }}
                    transition={{ delay: 0.15 + index * 0.08, duration: 0.7, ease: "easeOut" }}
                    className="h-full rounded-xl"
                    style={{ background: "var(--gradient-accent)" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Authenticity summary */}
      {plagiarism && (
        <div className="rounded-2xl border border-border bg-card p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
            <ScanSearch className="w-3.5 h-3.5" /> Authenticity review
          </h4>
          <div className="grid grid-cols-2 gap-3 mb-2">
            <div className="rounded-xl border border-warning/20 bg-warning/10 p-3">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Avg AI-likeness
              </p>
              <p className="text-xl font-extrabold text-warning mt-0.5">
                {Math.round(plagiarism.average_ai_generated_score)}%
              </p>
            </div>
            <div className="rounded-xl border border-brand/20 bg-brand/10 p-3">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Avg plagiarism risk
              </p>
              <p className="text-xl font-extrabold text-brand mt-0.5">
                {Math.round(plagiarism.average_plagiarism_score)}%
              </p>
            </div>
          </div>
          {plagiarism.summary && (
            <p className="text-xs text-muted-foreground leading-relaxed">
              {plagiarism.summary}
            </p>
          )}
        </div>
      )}

      {/* Per-answer breakdown */}
      <div className="rounded-2xl border border-border bg-card p-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">
          Question-by-question
        </h4>
        {scorecard.answers.length === 0 && (
          <p className="text-sm text-muted-foreground">No answers were recorded.</p>
        )}
        <div className="space-y-2.5">
          {scorecard.answers.map((answer) => {
            const open = openAnswers[answer.question_number] ?? false;
            return (
              <div key={answer.question_number} className="rounded-xl border border-border bg-muted/20 overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggle(answer.question_number)}
                  className="w-full flex items-center gap-3 px-3.5 py-2.5 text-left hover:bg-muted/40 transition-colors"
                >
                  <span className="w-7 h-7 rounded-lg bg-brand/10 text-brand flex items-center justify-center text-[11px] font-bold shrink-0">
                    {answer.question_number}
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className="block text-xs font-semibold text-foreground truncate">
                      {answer.question}
                    </span>
                    <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                      {answer.category} · {answer.grade}
                    </span>
                  </span>
                  <span
                    className="text-sm font-extrabold font-mono shrink-0"
                    style={{ color: scoreColor(answer.score) }}
                  >
                    {answer.score}
                  </span>
                  {open ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
                  )}
                </button>
                {open && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="px-4 pb-3.5 border-t border-border"
                  >
                    {answer.answer ? (
                      <p className="text-xs text-foreground leading-relaxed mt-2.5 whitespace-pre-wrap">
                        {answer.answer}
                      </p>
                    ) : (
                      <p className="text-xs text-muted-foreground italic mt-2.5">
                        No answer given.
                      </p>
                    )}
                    {answer.feedback && (
                      <p className="text-xs text-muted-foreground leading-relaxed mt-2">
                        <span className="font-semibold text-foreground">Feedback: </span>
                        {answer.feedback}
                      </p>
                    )}
                    {(answer.strengths.length > 0 || answer.improvements.length > 0) && (
                      <div className="grid sm:grid-cols-2 gap-3 mt-2.5">
                        {answer.strengths.length > 0 && (
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wide text-success mb-1">
                              Strengths
                            </p>
                            <ul className="space-y-1">
                              {answer.strengths.map((strength, i) => (
                                <li key={i} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                                  <Trophy className="w-3 h-3 text-success mt-0.5 shrink-0" />
                                  {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {answer.improvements.length > 0 && (
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wide text-warning mb-1">
                              To improve
                            </p>
                            <ul className="space-y-1">
                              {answer.improvements.map((improvement, i) => (
                                <li key={i} className="text-[11px] text-muted-foreground flex items-start gap-1.5">
                                  <span className="mt-1 w-1 h-1 rounded-full bg-warning shrink-0" />
                                  {improvement}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
