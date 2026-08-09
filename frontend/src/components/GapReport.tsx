import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import {
  Target,
  Loader2,
  Lightbulb,
  Briefcase,
  FileSearch,
  ArrowRight,
  ClipboardList,
  BookOpen,
} from "lucide-react";
import {
  generateGapReport,
  type GapReportResult,
  type AtsReport,
} from "@/lib/api";
import {
  buildSignals,
  assessSignals,
  type SignalAssessment,
} from "@/components/ResumeProofMap";

interface GapEvaluation {
  question_number?: number;
  question?: string;
  score: number;
  strengths?: string[];
  improvements?: string[];
  feedback?: string;
}

interface GapQuestion {
  id: number;
  text: string;
  category: string;
  difficulty: string;
}

interface GapReportProps {
  candidateName: string;
  resumeData?: Record<string, unknown>;
  evaluations?: GapEvaluation[];
  questions?: GapQuestion[];
  targetRole?: string;
}

const STATUS_TONE: Record<string, string> = {
  validated: "text-success",
  explored: "text-primary",
  fragile: "text-warning",
  untested: "text-muted-foreground",
};

function statusPill(status: string) {
  if (status === "validated")
    return "border-success/30 bg-success/10 text-success";
  if (status === "explored")
    return "border-primary/30 bg-primary/10 text-primary";
  if (status === "fragile")
    return "border-warning/30 bg-warning/10 text-warning";
  return "border-border bg-muted text-muted-foreground";
}

export default function GapReport({
  candidateName,
  resumeData,
  evaluations,
  questions,
  targetRole,
}: GapReportProps) {
  const [report, setReport] = useState<GapReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assessments = useMemo<SignalAssessment[]>(() => {
    if (!resumeData) return [];
    return assessSignals(buildSignals(resumeData), evaluations, questions);
  }, [resumeData, evaluations, questions]);

  const atsReport = useMemo<AtsReport | undefined>(() => {
    const embedded = (resumeData as Record<string, unknown> | undefined)
      ?.ats_report;
    return (embedded as AtsReport | undefined) ?? undefined;
  }, [resumeData]);

  const hasInput =
    assessments.some((a) => a.status === "fragile" || a.status === "untested") ||
    (atsReport?.keyword_match?.missing?.length ?? 0) > 0;

  useEffect(() => {
    if (!hasInput) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    generateGapReport({
      resume_data: resumeData ?? null,
      ats_report: atsReport ?? null,
      assessments: assessments.map((a) => ({
        label: a.label,
        kind: a.kind,
        status: a.status,
        average_score: a.averageScore,
        best_score: a.bestScore,
        matched_questions: a.matchedQuestions,
      })),
      candidate_name: candidateName,
      target_role: targetRole ?? "",
    })
      .then((result) => {
        if (!cancelled) setReport(result);
      })
      .catch(() => {
        if (!cancelled) setError("The improvement plan could not be generated right now.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [hasInput, resumeData, atsReport, assessments, candidateName, targetRole]);

  if (!hasInput) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
    >
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-brand" /> The Gap Report
          </h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl leading-relaxed">
            Which resume claims did this interview fail to substantiate — and
            what to practice before the next round.
          </p>
        </div>
        {report && (
          <span className="rounded-xl border border-border bg-muted/20 px-3 py-1.5 text-[11px] text-muted-foreground capitalize shrink-0">
            {report.generated_by === "llm" ? "AI-generated plan" : "Coach plan"}
          </span>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
          <Loader2 className="w-4 h-4 animate-spin text-brand" />
          Building your improvement plan…
        </div>
      )}

      {error && (
        <p className="text-sm text-destructive rounded-lg border border-destructive/20 bg-destructive/5 px-3 py-2">
          {error}
        </p>
      )}

      {report && (
        <div className="space-y-5">
          <p className="text-sm text-muted-foreground leading-relaxed">
            {report.overview}
          </p>

          {report.focus_areas.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <Target className="w-3.5 h-3.5 text-brand" /> Claims to
                Strengthen
              </h4>
              <div className="space-y-3">
                {report.focus_areas.map((area, idx) => (
                  <div
                    key={`${area.claim}-${idx}`}
                    className="rounded-xl border border-border bg-muted/20 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                      <p className="text-sm font-semibold text-foreground">
                        {area.claim}
                      </p>
                      <span
                        className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold border capitalize ${statusPill(area.status.toLowerCase())}`}
                      >
                        {area.status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3 leading-relaxed">
                      {area.why}
                    </p>
                    <ul className="space-y-1.5">
                      {(area.actions || []).map((action) => (
                        <li
                          key={action}
                          className="text-xs text-muted-foreground flex items-start gap-2"
                        >
                          <ArrowRight className="w-3 h-3 text-brand mt-0.5 flex-shrink-0" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.ats_gaps.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <FileSearch className="w-3.5 h-3.5 text-brand" /> Resume
                Keyword Gaps
              </h4>
              <div className="space-y-2">
                {report.ats_gaps.map((gap) => (
                  <div
                    key={gap.keyword}
                    className="flex flex-col md:flex-row md:items-start gap-1.5 rounded-lg border border-border bg-card/60 px-3 py-2.5"
                  >
                    <span className="text-xs font-mono font-bold text-foreground shrink-0 px-2 py-0.5 rounded-md bg-warning/10 border border-warning/20 self-start">
                      {gap.keyword}
                    </span>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {gap.action}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.next_round_probes.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <Lightbulb className="w-3.5 h-3.5 text-warning" /> Probes for
                Your Next Mock
              </h4>
              <div className="flex flex-wrap gap-2">
                {report.next_round_probes.map((probe) => (
                  <span
                    key={probe}
                    className="text-xs rounded-lg bg-warning/5 border border-warning/20 px-2.5 py-1.5 text-muted-foreground"
                  >
                    {probe}
                  </span>
                ))}
              </div>
            </div>
          )}

          {report.resources.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-brand" /> Practice
                Resources
              </h4>
              <ul className="space-y-1.5">
                {report.resources.map((resource) => (
                  <li
                    key={resource}
                    className="text-xs text-muted-foreground flex items-start gap-2"
                  >
                    <Briefcase className="w-3 h-3 text-brand mt-0.5 flex-shrink-0" />
                    {resource}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
