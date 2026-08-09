import { useCallback, useEffect, useRef, useState } from "react";
import { m as motion } from "framer-motion";
import {
  Clapperboard,
  Loader2,
  Share2,
  Check,
  ShieldAlert,
  WifiOff,
} from "lucide-react";
import { toast } from "sonner";
import ReplayTimeline from "./ReplayTimeline";
import {
  buildReplay,
  fetchProctorSession,
  getInterviewHeatmap,
  saveReplay,
  type ReplayBuildPayload,
  type ReplayDocument,
  type ReplayQaPair,
} from "@/lib/api";
import { buildLocalReplayDocument } from "@/lib/replayBuilder";
import { replayShareUrl } from "@/lib/replayShare";
import { getInterviewSessionId } from "@/lib/interviewSession";

export interface GameTapeProps {
  candidateName: string;
  overallScore: number;
  overallGrade: string;
  totalQuestions: number;
  answeredQuestions: number;
  duration: number;
  targetRole?: string;
  qaPairs: ReplayQaPair[];
}

export default function GameTape({
  candidateName,
  overallScore,
  overallGrade,
  totalQuestions,
  answeredQuestions,
  duration,
  targetRole,
  qaPairs,
}: GameTapeProps) {
  const [doc, setDoc] = useState<ReplayDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [usingLocalFallback, setUsingLocalFallback] = useState(false);
  const [sharing, setSharing] = useState(false);
  const payloadRef = useRef<ReplayBuildPayload | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      const meta = {
        candidate_name: candidateName,
        overall_score:
          typeof overallScore === "number" ? overallScore : null,
        overall_grade: overallGrade ?? null,
        duration_seconds: typeof duration === "number" ? duration : 0,
        total_questions: totalQuestions,
        answered_questions: answeredQuestions,
        target_role: targetRole ?? null,
        created_at: new Date().toISOString(),
      };

      // Confidence heatmap — best-effort, never blocks the tape.
      let heatmap: ReplayBuildPayload["heatmap"] = null;
      try {
        const confidencePairs = qaPairs.map((pair) => ({
          question: pair.question,
          answer: pair.answer,
          category: pair.category || "T",
          question_number: pair.question_number,
        }));
        heatmap = await getInterviewHeatmap(confidencePairs);
      } catch {
        heatmap = null;
      }

      // Proctoring events for this sitting — best-effort.
      let proctorEvents: Record<string, unknown>[] = [];
      try {
        const proctor = await fetchProctorSession(getInterviewSessionId());
        proctorEvents = Array.isArray(proctor.events) ? proctor.events : [];
      } catch {
        proctorEvents = [];
      }

      const payload: ReplayBuildPayload = {
        meta,
        qa_pairs: qaPairs,
        heatmap,
        proctor_events: proctorEvents,
      };
      payloadRef.current = payload;

      if (cancelled) return;
      try {
        const built = await buildReplay(payload);
        if (cancelled) return;
        setDoc(built);
        setUsingLocalFallback(false);
      } catch {
        if (cancelled) return;
        setDoc(buildLocalReplayDocument(payload));
        setUsingLocalFallback(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [
    candidateName,
    overallScore,
    overallGrade,
    totalQuestions,
    answeredQuestions,
    duration,
    targetRole,
    qaPairs,
  ]);

  const share = useCallback(async () => {
    if (!payloadRef.current || sharing) return;
    setSharing(true);
    try {
      const { token } = await saveReplay({
        ...payloadRef.current,
        session_id: getInterviewSessionId(),
      });
      const url = replayShareUrl(token);
      await navigator.clipboard.writeText(url);
      toast.success("Replay link copied — anyone with it can watch the tape.");
    } catch {
      toast.error("Could not create the share link right now. Try again.");
    } finally {
      setSharing(false);
    }
  }, [sharing]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-border bg-card shadow-sm p-6 mb-5"
      >
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin text-brand" />
          Cutting the game tape…
        </div>
        <div className="mt-4 h-8 w-full rounded-lg bg-muted/50 animate-pulse" />
        <div className="mt-2 h-24 w-full rounded-lg bg-muted/30 animate-pulse" />
      </motion.div>
    );
  }

  if (!doc) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-border bg-card shadow-sm p-6 mb-5"
      >
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <WifiOff className="w-4 h-4 text-warning" />
          Game Tape could not be assembled.
        </div>
      </motion.div>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-border bg-card/60 shadow-sm p-5 mb-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <span className="w-10 h-10 rounded-xl bg-brand/10 text-brand flex items-center justify-center">
            <Clapperboard className="w-5 h-5" />
          </span>
          <div>
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              Game Tape · Replay Studio
            </h3>
            <p className="text-[11px] text-muted-foreground">
              {candidateName || "Candidate"} · {overallGrade || "—"} ·{" "}
              {Math.round(overallScore)}% · frame-by-frame playback with
              confidence and integrity events
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {usingLocalFallback && (
            <span
              title="Network was unavailable, so the tape was assembled in the browser. Sharing always persists via the server."
              className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full bg-warning/10 border border-warning/20 text-warning"
            >
              <WifiOff className="w-3 h-3" /> offline build
            </span>
          )}
          {doc.stats.violations > 0 && (
            <span
              title={`${doc.stats.violations} integrity event${doc.stats.violations === 1 ? "" : "s"} flagged on this tape`}
              className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full bg-destructive/10 border border-destructive/25 text-destructive"
            >
              <ShieldAlert className="w-3 h-3" />{" "}
              {doc.stats.violations} flagged
            </span>
          )}
          <button
            type="button"
            onClick={share}
            disabled={sharing}
            className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-brand text-brand-foreground hover:bg-brand-hover disabled:opacity-60 transition-colors"
          >
            {sharing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Share2 className="w-3.5 h-3.5" />
            )}
            {sharing ? "Sharing…" : "Share tape"}
          </button>
        </div>
      </div>

      <ReplayTimeline doc={doc} />

      {usingLocalFallback && (
        <p className="mt-3 text-[10px] text-muted-foreground flex items-center gap-1.5">
          <Check className="w-3 h-3" /> Assembled locally — the share link is
          persisted by the server when you share.
        </p>
      )}
    </motion.section>
  );
}
