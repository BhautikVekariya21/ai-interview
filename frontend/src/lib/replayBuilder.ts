/**
 * Client-side replay document builder.
 *
 * The backend `replay_service` is the canonical implementation — this module
 * mirrors its merge rules so the Replay Studio can still render a tape when the
 * network drops (same offline-first spirit as the Coach Whisper fallback).
 * Documents built here are tagged `generated_by: "local"` so the UI can tell
 * them apart, and sharing always goes through the server's `/replay/save`,
 * which re-builds the document canonically.
 */
import type {
  ReplayBuildPayload,
  ReplayDocument,
  ReplayHeatmapSegment,
  ReplayTimelineEntry,
} from "./api";

const EVENT_SEVERITY: Record<string, "flag" | "warn" | "info"> = {
  tab_switch: "flag",
  window_blur: "flag",
  fullscreen_exit: "flag",
  screen_share_stopped: "warn",
  screen_share_denied: "warn",
  screen_share_wrong_surface: "warn",
  devtools_blocked: "warn",
  copy_blocked: "warn",
  paste_blocked: "warn",
  recorder_error: "info",
  upload_failed: "info",
  screen_share_granted: "info",
};

const EVENT_LABELS: Record<string, string> = {
  tab_switch: "Tab switch detected",
  window_blur: "Interview window lost focus",
  fullscreen_exit: "Fullscreen exited",
  screen_share_stopped: "Screen sharing stopped",
  screen_share_denied: "Screen sharing denied",
  screen_share_wrong_surface: "Wrong screen shared",
  devtools_blocked: "DevTools attempt blocked",
  copy_blocked: "Copy attempt blocked",
  paste_blocked: "Paste attempt blocked",
  recorder_error: "Recorder error",
  upload_failed: "Recording upload failed",
  screen_share_granted: "Screen sharing granted",
};

function severityOf(kind: unknown): string {
  return EVENT_SEVERITY[String(kind ?? "")] ?? "info";
}

function labelOf(kind: unknown): string {
  const key = String(kind ?? "");
  return (
    EVENT_LABELS[key] ??
    (key ? key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase()) : "Proctor event")
  );
}

function asNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function clamp(value: number | null, lo: number, hi: number): number | null {
  if (value === null) return null;
  return Math.max(lo, Math.min(hi, value));
}

export function buildLocalReplayDocument(
  payload: ReplayBuildPayload,
): ReplayDocument {
  const meta: Record<string, unknown> & { generated_by: string } = {
    ...(payload.meta ?? {}),
    generated_by: "local",
  };
  const qa = Array.isArray(payload.qa_pairs) ? payload.qa_pairs : [];
  const heat = payload.heatmap ?? {};
  const events = Array.isArray(payload.proctor_events)
    ? payload.proctor_events
    : [];

  const heatByNumber = new Map<number, { segments?: unknown[] }>();
  for (const question of heat.questions ?? []) {
    const number = asNumber(question.question_number);
    if (number !== null) heatByNumber.set(number, question);
  }

  const eventsByQuestion = new Map<number, Record<string, unknown>[]>();
  const trailingEvents: Record<string, unknown>[] = [];
  for (const event of events) {
    const index = asNumber(event.question_index);
    if (index !== null && index >= 1) {
      const bucket = eventsByQuestion.get(index) ?? [];
      bucket.push(event);
      eventsByQuestion.set(index, bucket);
    } else {
      trailingEvents.push(event);
    }
  }

  const timeline: ReplayTimelineEntry[] = [];
  const scores: number[] = [];
  let weakest: { question_number: number; score: number } | null = null;

  for (const q of qa) {
    const number = asNumber(q.question_number) ?? 0;
    timeline.push({
      type: "question",
      question_number: number,
      text: String(q.question ?? ""),
    });

    const score = asNumber(q.score);
    const segments: ReplayHeatmapSegment[] = [];
    const heatQuestion = heatByNumber.get(number);
    for (const raw of heatQuestion?.segments ?? []) {
      if (!raw || typeof raw !== "object") continue;
      const segment = raw as Record<string, unknown>;
      segments.push({
        text: String(segment.text ?? ""),
        score: clamp(asNumber(segment.score), 0, 100),
        start_pct: clamp(asNumber(segment.start_pct), 0, 100) ?? 0,
        end_pct: clamp(asNumber(segment.end_pct), 0, 100) ?? 0,
        flags: Array.isArray(segment.flags)
          ? segment.flags.map((f) => String(f)).filter(Boolean)
          : [],
      });
    }

    timeline.push({
      type: "answer",
      question_number: number,
      text: String(q.answer ?? ""),
      score,
      grade: q.grade ?? null,
      feedback: q.feedback ?? null,
      segments,
    });

    if (score !== null) {
      scores.push(score);
      if (!weakest || score < weakest.score) {
        weakest = { question_number: number, score };
      }
    }

    for (const event of eventsByQuestion.get(number) ?? []) {
      timeline.push({
        type: "proctor",
        kind: String(event.kind ?? ""),
        label: labelOf(event.kind),
        severity: severityOf(event.kind),
        detail: event.detail != null ? String(event.detail) : null,
        occurred_at:
          event.occurred_at != null
            ? String(event.occurred_at)
            : event.recorded_at != null
              ? String(event.recorded_at)
              : null,
      });
    }
  }

  for (const event of trailingEvents) {
    timeline.push({
      type: "proctor",
      kind: String(event.kind ?? ""),
      label: labelOf(event.kind),
      severity: severityOf(event.kind),
      detail: event.detail != null ? String(event.detail) : null,
      occurred_at:
        event.occurred_at != null
          ? String(event.occurred_at)
          : event.recorded_at != null
            ? String(event.recorded_at)
            : null,
    });
  }

  const violations = events.filter(
    (e) => severityOf(e.kind) === "flag" || severityOf(e.kind) === "warn",
  ).length;

  return {
    version: 1,
    meta,
    timeline,
    stats: {
      average_score:
        scores.length > 0
          ? Math.round((scores.reduce((s, v) => s + v, 0) / scores.length) * 10) / 10
          : null,
      // Every qa_pair is a recorded answer (skips included) — mirrors the
      // backend, which counts the transcript length, not just scored answers.
      answered_questions: qa.length,
      total_questions: asNumber(meta.total_questions) ?? qa.length,
      proctor_events_total: events.length,
      violations,
      weakest_question: weakest,
    },
  };
}
