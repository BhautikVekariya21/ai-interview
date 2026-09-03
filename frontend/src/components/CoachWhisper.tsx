import { useEffect, useState } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  MicOff,
  Gauge,
  Lightbulb,
  Expand,
  BatteryLow,
  Star,
  X,
  Loader2,
  Volume2,
} from "lucide-react";
import { getCoachTip, type CoachTipResult } from "@/lib/api";
import {
  countFillerWords,
  countInterviewWords,
} from "@/lib/interviewPace";

export interface CoachWhisperProps {
  /** The last submitted answer (skipped answers should be filtered out). */
  answer: { text: string; score?: number } | null;
  question?: string;
}

const CATEGORY_META: Record<
  string,
  { icon: React.ReactNode; tone: string }
> = {
  fillers: {
    icon: <MicOff className="w-4 h-4" />,
    tone: "bg-amber-500/10 border-amber-500/25 text-amber-600",
  },
  pace: {
    icon: <Gauge className="w-4 h-4" />,
    tone: "bg-blue-500/10 border-blue-500/25 text-blue-600",
  },
  confidence: {
    icon: <Lightbulb className="w-4 h-4" />,
    tone: "bg-purple-500/10 border-purple-500/25 text-purple-600",
  },
  depth: {
    icon: <Expand className="w-4 h-4" />,
    tone: "bg-brand/10 border-brand/25 text-brand",
  },
  momentum: {
    icon: <BatteryLow className="w-4 h-4" />,
    tone: "bg-orange-500/10 border-orange-500/25 text-orange-600",
  },
  reinforcement: {
    icon: <Star className="w-4 h-4" />,
    tone: "bg-success/10 border-success/25 text-success",
  },
};

/** Instant client-side fallback so the whisper never blocks on the network. */
function clientFallbackTip(text: string): CoachTipResult {
  const fillerCount = countFillerWords(text).reduce((s, f) => s + f.count, 0);
  const wordCount = countInterviewWords(text);

  if (fillerCount >= 4) {
    return {
      category: "fillers",
      icon: "mic_off",
      title: "Filler spike detected",
      tip: `You used ${fillerCount} filler words in that answer. Take a deliberate 1-second pause instead of reaching for "um" — purposeful silence reads as confidence.`,
    };
  }
  if (wordCount < 15) {
    return {
      category: "depth",
      icon: "expand",
      title: "Go deeper next answer",
      tip: "That answer was under 15 words — too thin to leave an impression. Add what you did, how you did it, and the result.",
    };
  }
  return {
    category: "reinforcement",
    icon: "star",
    title: "Keep this energy",
    tip: "Clean delivery on that answer. Keep the same claim → evidence → impact structure for the questions ahead.",
  };
}

export default function CoachWhisper({ answer, question }: CoachWhisperProps) {
  const [tip, setTip] = useState<CoachTipResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!answer) {
      // No active answer — clear any lingering whisper rather than showing
      // a tip that belongs to a previous question.
      setTip(null);
      return;
    }
    const text = answer.text || "";
    if (!text.trim() || text.trim().toUpperCase() === "[SKIPPED]") return;

    let cancelled = false;
    setLoading(true);

    const fillerCount = countFillerWords(text).reduce(
      (s, f) => s + f.count,
      0,
    );
    const wordCount = countInterviewWords(text);
    const fillerPercentage = wordCount > 0 ? (fillerCount / wordCount) * 100 : 0;

    getCoachTip({
      answer_text: text,
      word_count: wordCount,
      filler_count: fillerCount,
      filler_percentage: Math.round(fillerPercentage * 10) / 10,
      confidence_score: answer.score,
      question,
    })
      .then((result) => {
        if (!cancelled) setTip(result);
      })
      .catch(() => {
        if (!cancelled) setTip(clientFallbackTip(text));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // Deps are the primitive values, not the `answer` object: InterviewPage
    // re-renders every second (timer/clock) and hands us a fresh object literal
    // each time. Keying on the object would re-run the fetch every second.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [answer?.text, answer?.score, question]);

  if (!tip && !loading) return null;

  const meta = CATEGORY_META[tip?.category ?? ""] ?? CATEGORY_META.reinforcement;

  return (
    <AnimatePresence>
      <motion.div
        key="coach-whisper"
        initial={{ opacity: 0, y: -8, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -6, scale: 0.98 }}
        className="mb-2"
      >
        <div className="relative flex items-start gap-3 rounded-xl border border-border bg-card shadow-sm px-4 py-3">
          <div
            className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 ${meta.tone}`}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              meta.icon
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground inline-flex items-center gap-1">
                <Volume2 className="w-3 h-3" /> Coach Whisper
              </span>
              {tip?.title && (
                <span className="text-xs font-semibold text-foreground">
                  {tip.title}
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {loading
                ? "Listening to your delivery…"
                : tip?.tip ?? "Keep it up."}
            </p>
          </div>
          <button
            onClick={() => setTip(null)}
            className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-md -mr-1 -mt-1 shrink-0"
            aria-label="Dismiss whisper"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
