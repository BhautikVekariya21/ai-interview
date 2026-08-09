import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import {
  Play,
  Pause,
  MessageSquare,
  FileText,
  ShieldAlert,
  AlertTriangle,
  Info,
  Clock,
  Trophy,
  Gauge,
  CornerDownRight,
} from "lucide-react";
import type { ReplayDocument, ReplayTimelineEntry } from "@/lib/api";

/** How long each entry is shown during auto-play (ms). */
const TICK_MS = 1600;

function scoreTone(score: number | null): string {
  if (score === null) return "bg-muted";
  if (score >= 70) return "bg-success/70";
  if (score >= 50) return "bg-amber-500/70";
  return "bg-destructive/70";
}

function scoreTextTone(score: number | null): string {
  if (score === null) return "text-muted-foreground";
  if (score >= 70) return "text-success";
  if (score >= 50) return "text-amber-600";
  return "text-destructive";
}

function proctorTone(severity: string): string {
  if (severity === "flag") return "bg-destructive";
  if (severity === "warn") return "bg-amber-500";
  return "bg-slate-400";
}

function proctorChip(severity: string): string {
  if (severity === "flag")
    return "bg-destructive/10 border-destructive/30 text-destructive";
  if (severity === "warn")
    return "bg-amber-500/10 border-amber-500/30 text-amber-600";
  return "bg-muted border-border text-muted-foreground";
}

function tileTone(entry: ReplayTimelineEntry): string {
  switch (entry.type) {
    case "answer":
      return scoreTone(entry.score);
    case "proctor":
      return proctorTone(entry.severity);
    default:
      return "bg-muted-foreground/25";
  }
}

function tileTitle(entry: ReplayTimelineEntry): string {
  switch (entry.type) {
    case "question":
      return `Q${entry.question_number} · ${entry.text.slice(0, 60)}`;
    case "answer":
      return `Answer ${entry.question_number} · ${
        entry.score !== null ? `${entry.score}/100` : "no score"
      }`;
    case "proctor":
      return `${entry.label}${entry.detail ? ` — ${entry.detail}` : ""}`;
  }
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  if (m <= 0) return `${s}s`;
  return `${m}m ${String(s).padStart(2, "0")}s`;
}

function formatStamp(value?: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** Stacked confidence heatmap bar for one answer's segments. */
function HeatmapBar({ entry }: { entry: Extract<ReplayTimelineEntry, { type: "answer" }> }) {
  const segments = entry.segments;
  if (segments.length === 0) return null;

  return (
    <div className="mt-2">
      <div className="flex items-center gap-1.5 mb-1">
        <Gauge className="w-3 h-3 text-muted-foreground" />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Confidence across the answer
        </span>
      </div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
        {segments.map((segment, i) => {
          const width = Math.max(
            (segment.end_pct - segment.start_pct) / 100,
            segments.length === 1 ? 1 : 0.02,
          );
          return (
            <div
              key={i}
              title={`${segment.text.slice(0, 120) || "segment"} · ${
                segment.score !== null ? Math.round(segment.score) : "—"
              }/100${segment.flags.length ? ` · ${segment.flags.join(", ")}` : ""}`}
              className={`${scoreTone(segment.score)} transition-all duration-500`}
              style={{ width: `${width * 100}%` }}
            />
          );
        })}
      </div>
      <div className="mt-1 flex flex-wrap gap-1">
        {segments
          .flatMap((s) => s.flags)
          .slice(0, 6)
          .map((flag, i) => (
            <span
              key={`${flag}-${i}`}
              className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-warning/10 border border-warning/20 text-warning"
            >
              {flag}
            </span>
          ))}
      </div>
    </div>
  );
}

function DetailCard({ entry }: { entry: ReplayTimelineEntry }) {
  if (entry.type === "question") {
    return (
      <motion.div
        key={`q-${entry.question_number}-${entry.text.length}`}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start gap-3 p-4 rounded-xl border border-border bg-card"
      >
        <span className="w-8 h-8 rounded-lg bg-brand/10 text-brand flex items-center justify-center shrink-0">
          <FileText className="w-4 h-4" />
        </span>
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
            Question {entry.question_number}
          </p>
          <p className="text-sm font-medium text-foreground leading-relaxed">
            {entry.text}
          </p>
        </div>
      </motion.div>
    );
  }

  if (entry.type === "answer") {
    return (
      <motion.div
        key={`a-${entry.question_number}-${entry.text.length}`}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 rounded-xl border border-border bg-card"
      >
        <div className="flex items-center justify-between gap-3 mb-2">
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
            <MessageSquare className="w-3 h-3" /> Answer {entry.question_number}
          </p>
          <span
            className={`text-xs font-extrabold font-mono px-2 py-0.5 rounded-full border bg-card/60 ${scoreTextTone(entry.score)}`}
          >
            {entry.score !== null ? `${Math.round(entry.score)}/100` : "Not scored"}
            {entry.grade ? ` · ${entry.grade}` : ""}
          </span>
        </div>
        <p
          className={`text-sm leading-relaxed ${
            entry.text ? "text-foreground" : "text-muted-foreground italic"
          }`}
        >
          {entry.text || "Answer not captured in this recording."}
        </p>
        <HeatmapBar entry={entry} />
        {entry.feedback && (
          <p className="mt-3 text-xs text-muted-foreground leading-relaxed border-t border-border pt-2">
            <span className="font-semibold text-foreground">Feedback: </span>
            {entry.feedback}
          </p>
        )}
      </motion.div>
    );
  }

  return (
    <motion.div
      key={`p-${entry.kind}-${entry.occurred_at ?? entry.label}`}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-3 p-4 rounded-xl border ${proctorChip(entry.severity)}`}
    >
      <span className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center shrink-0">
        {entry.severity === "flag" ? (
          <ShieldAlert className="w-4 h-4 text-destructive" />
        ) : entry.severity === "warn" ? (
          <AlertTriangle className="w-4 h-4 text-amber-500" />
        ) : (
          <Info className="w-4 h-4 text-muted-foreground" />
        )}
      </span>
      <div className="min-w-0">
        <p className="text-xs font-bold text-foreground">{entry.label}</p>
        {entry.detail && (
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            {entry.detail}
          </p>
        )}
        {formatStamp(entry.occurred_at) && (
          <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3" /> {formatStamp(entry.occurred_at)}
          </p>
        )}
      </div>
    </motion.div>
  );
}

export interface ReplayTimelineProps {
  doc: ReplayDocument;
}

export default function ReplayTimeline({ doc }: ReplayTimelineProps) {
  const timeline = doc.timeline;
  const [activeIndex, setActiveIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  // Keep the active index valid when a new document arrives.
  useEffect(() => {
    setActiveIndex(0);
    setPlaying(false);
  }, [doc]);

  useEffect(() => {
    if (!playing) return;
    if (activeIndex >= timeline.length - 1) {
      setPlaying(false);
      return;
    }
    const interval = setInterval(() => {
      setActiveIndex((current) => {
        if (current >= timeline.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, TICK_MS);
    return () => clearInterval(interval);
  }, [playing, activeIndex, timeline.length]);

  const activeEntry = timeline[Math.min(activeIndex, timeline.length - 1)];
  const stats = doc.stats;

  const seek = (index: number) => {
    setActiveIndex(Math.max(0, Math.min(index, timeline.length - 1)));
    setPlaying(false);
  };

  const counts = useMemo(() => {
    let questions = 0;
    let answers = 0;
    let proctors = 0;
    for (const entry of timeline) {
      if (entry.type === "question") questions += 1;
      else if (entry.type === "answer") answers += 1;
      else proctors += 1;
    }
    return { questions, answers, proctors };
  }, [timeline]);

  if (timeline.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-center text-sm text-muted-foreground">
        Nothing to replay — the interview produced no recorded answers.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Stats strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {[
          {
            label: "Average Score",
            value:
              stats.average_score !== null
                ? `${Math.round(stats.average_score)}%`
                : "—",
            icon: <Trophy className="w-3.5 h-3.5" />,
          },
          {
            label: "Answered",
            value: `${stats.answered_questions}/${stats.total_questions}`,
            icon: <MessageSquare className="w-3.5 h-3.5" />,
          },
          {
            label: "Duration",
            value: formatDuration(
              typeof doc.meta.duration_seconds === "number"
                ? doc.meta.duration_seconds
                : 0,
            ),
            icon: <Clock className="w-3.5 h-3.5" />,
          },
          {
            label: "Integrity Events",
            value: String(stats.proctor_events_total),
            icon: (
              <ShieldAlert
                className={`w-3.5 h-3.5 ${
                  stats.violations > 0 ? "text-destructive" : ""
                }`}
              />
            ),
          },
        ].map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-border bg-muted/20 px-3 py-2.5 flex items-center gap-2"
          >
            <span className="text-muted-foreground">{metric.icon}</span>
            <div>
              <p className="text-sm font-extrabold font-mono text-foreground leading-none">
                {metric.value}
              </p>
              <p className="text-[9px] uppercase tracking-wider text-muted-foreground mt-1">
                {metric.label}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Filmstrip scrubber */}
      <div className="rounded-xl border border-border bg-card p-3">
        <div className="flex items-center gap-2 mb-2.5">
          <button
            type="button"
            onClick={() => setPlaying((value) => !value)}
            className="w-8 h-8 rounded-lg bg-brand text-brand-foreground flex items-center justify-center hover:bg-brand/90 transition-colors"
            title={playing ? "Pause replay" : "Play replay"}
          >
            {playing ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>
          <div className="text-[11px] text-muted-foreground">
            <span className="font-bold text-foreground">
              {activeIndex + 1}
            </span>{" "}
            / {timeline.length} ·{" "}
            {counts.questions} questions · {counts.answers} answers ·{" "}
            {counts.proctors} events
          </div>
          <div className="ml-auto hidden sm:block text-[10px] text-muted-foreground">
            Click a frame to seek
          </div>
        </div>

        <div className="flex gap-1 overflow-x-auto pb-1">
          {timeline.map((entry, index) => (
            <button
              key={`${index}-${entry.type}`}
              type="button"
              onClick={() => seek(index)}
              title={tileTitle(entry)}
              className={`relative h-7 min-w-[18px] rounded-md transition-all duration-200 shrink-0 ${tileTone(entry)} ${
                index === activeIndex
                  ? "ring-2 ring-brand ring-offset-1 ring-offset-card scale-110"
                  : "opacity-70 hover:opacity-100 hover:scale-105"
              }`}
            >
              {entry.type === "proctor" && (
                <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-foreground/70" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Active detail card */}
      {activeEntry && <DetailCard entry={activeEntry} />}

      {/* Vertical timeline */}
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-3">
          Full timeline
        </p>
        <ol className="space-y-1.5">
          {timeline.map((entry, index) => {
            const isActive = index === activeIndex;
            return (
              <li key={`${index}-${entry.type}`}>
                <button
                  type="button"
                  onClick={() => seek(index)}
                  className={`w-full text-left flex items-start gap-2.5 rounded-lg px-2.5 py-2 transition-colors ${
                    isActive ? "bg-brand/10" : "hover:bg-muted/40"
                  }`}
                >
                  {entry.type === "question" && (
                    <span className="mt-0.5 w-5 h-5 rounded-md bg-muted text-muted-foreground flex items-center justify-center shrink-0">
                      <FileText className="w-3 h-3" />
                    </span>
                  )}
                  {entry.type === "answer" && (
                    <span
                      className={`mt-0.5 w-5 h-5 rounded-md flex items-center justify-center shrink-0 text-white ${scoreTone(entry.score)}`}
                    >
                      <CornerDownRight className="w-3 h-3" />
                    </span>
                  )}
                  {entry.type === "proctor" && (
                    <span className="mt-0.5 w-5 h-5 rounded-md bg-card border border-border flex items-center justify-center shrink-0">
                      {entry.severity === "flag" ? (
                        <ShieldAlert className="w-3 h-3 text-destructive" />
                      ) : (
                        <AlertTriangle className="w-3 h-3 text-amber-500" />
                      )}
                    </span>
                  )}
                  <span className="min-w-0 flex-1">
                    <span
                      className={`block text-xs truncate ${
                        isActive ? "text-foreground font-semibold" : "text-muted-foreground"
                      }`}
                    >
                      {entry.type === "question" &&
                        `Q${entry.question_number} · ${entry.text}`}
                      {entry.type === "answer" &&
                        `Answer ${entry.question_number}${
                          entry.score !== null ? ` · ${Math.round(entry.score)}/100` : ""
                        }`}
                      {entry.type === "proctor" && `${entry.label}`}
                    </span>
                    {entry.type === "answer" && entry.feedback && (
                      <span className="block text-[10px] text-muted-foreground truncate mt-0.5">
                        {entry.feedback}
                      </span>
                    )}
                    {entry.type === "proctor" && entry.detail && (
                      <span className="block text-[10px] text-muted-foreground truncate mt-0.5">
                        {entry.detail}
                      </span>
                    )}
                  </span>
                  {entry.type === "proctor" && (
                    <span
                      className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0 ${proctorChip(entry.severity)}`}
                    >
                      {entry.severity}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
