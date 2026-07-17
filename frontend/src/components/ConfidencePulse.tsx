/**
 * Module 12: AI Confidence Pulse — Speech Intelligence Dashboard
 *
 * A stunning, animated dashboard that analyzes HOW candidates communicate,
 * not just WHAT they say.
 */

import { useEffect, useState } from "react";
import { m as motion } from "framer-motion";
import {
  Activity,
  Brain,
  Gauge,
  Lightbulb,
  MessageSquare,
  Mic,
  MicOff,
  Rocket,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Minus,
  Trophy,
  Zap,
  BookOpen,
  CheckCircle2,
  Star,
} from "lucide-react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
  Cell,
  Pie,
  PieChart,
} from "recharts";
import {
  analyzeConfidence,
  getInterviewHeatmap,
  type ConfidenceReport,
  type ConfidenceCoachingTip,
  type HeatmapReport,
  type HeatmapSegment,
} from "@/lib/api";
import type { Module5Evaluation } from "./ResultsPage";
import Loading from "@/components/Loading";

/* ─── Helper: score ring ────────────────────────────────────── */
function PulseRing({
  score,
  size = 110,
  strokeWidth = 8,
  label,
  sublabel,
  color,
}: {
  score: number;
  size?: number;
  strokeWidth?: number;
  label: string;
  sublabel?: string;
  color?: string;
}) {
  const r = (size - strokeWidth) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const stroke =
    color ||
    (score >= 70
      ? "hsl(var(--success))"
      : score >= 45
        ? "hsl(var(--warning))"
        : "hsl(var(--destructive))");

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90 w-full h-full"
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            className="fill-none stroke-muted"
            strokeWidth={strokeWidth}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            className="fill-none"
            stroke={stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
        </svg>
        <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-lg font-extrabold font-mono">
          {score}
        </span>
      </div>
      <span className="text-xs font-semibold text-muted-foreground">
        {label}
      </span>
      {sublabel && (
        <span className="text-[10px] text-muted-foreground">{sublabel}</span>
      )}
    </div>
  );
}

/* ─── Helper: icon resolver for coaching ───────────────────── */
function CoachIcon({ icon }: { icon: string }) {
  const cls = "w-5 h-5";
  switch (icon) {
    case "trophy":
      return <Trophy className={`${cls} text-amber-400`} />;
    case "trending_up":
      return <TrendingUp className={`${cls} text-success`} />;
    case "lightbulb":
      return <Lightbulb className={`${cls} text-amber-400`} />;
    case "mic_off":
      return <MicOff className={`${cls} text-destructive`} />;
    case "check":
    case "check_circle":
      return <CheckCircle2 className={`${cls} text-success`} />;
    case "star":
    case "sparkles":
      return <Sparkles className={`${cls} text-primary`} />;
    case "slow_down":
      return <Gauge className={`${cls} text-warning`} />;
    case "speed_up":
      return <Zap className={`${cls} text-warning`} />;
    case "book":
      return <BookOpen className={`${cls} text-primary`} />;
    case "battery_low":
      return <TrendingDown className={`${cls} text-destructive`} />;
    case "rocket":
      return <Rocket className={`${cls} text-primary`} />;
    default:
      return <Brain className={`${cls} text-primary`} />;
  }
}

/* ─── Helper: momentum icon ────────────────────────────────── */
function MomentumBadge({ momentum }: { momentum: string }) {
  if (momentum === "rising")
    return (
      <span className="inline-flex items-center gap-1.5 rounded-xl bg-success/15 border border-success/25 px-3 py-1 text-xs font-semibold text-success">
        <TrendingUp className="w-3.5 h-3.5" /> Rising
      </span>
    );
  if (momentum === "declining")
    return (
      <span className="inline-flex items-center gap-1.5 rounded-xl bg-destructive/15 border border-destructive/25 px-3 py-1 text-xs font-semibold text-destructive">
        <TrendingDown className="w-3.5 h-3.5" /> Declining
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1.5 rounded-xl bg-[#F9F9F9] border border-border px-3 py-1 text-xs font-semibold text-muted-foreground">
      <Minus className="w-3.5 h-3.5" /> Stable
    </span>
  );
}

/* ─── Pace gauge mini ──────────────────────────────────────── */
function PaceGauge({ wpm, label }: { wpm: number; label: string }) {
  // Map WPM to 0-100 scale (60 WPM = 0%, 200 WPM = 100%)
  const pct = Math.min(100, Math.max(0, ((wpm - 60) / 140) * 100));
  const idealLow = ((120 - 60) / 140) * 100;
  const idealHigh = ((160 - 60) / 140) * 100;

  const labelText =
    label === "ideal"
      ? "Ideal Pace"
      : label === "too_fast"
        ? "Too Fast"
        : label === "too_slow"
          ? "Too Slow"
          : label === "slightly_fast"
            ? "Slightly Fast"
            : label === "slightly_slow"
              ? "Slightly Slow"
              : "—";

  const clr =
    label === "ideal"
      ? "text-success"
      : label.includes("slow") || label.includes("fast")
        ? "text-warning"
        : "text-muted-foreground";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Gauge className="w-4 h-4" /> Speaking Pace
        </span>
        <span className={`text-sm font-bold font-mono ${clr}`}>
          {wpm} WPM
        </span>
      </div>
      <div className="relative h-3 bg-[#F9F9F9] rounded-xl overflow-hidden">
        {/* Ideal zone */}
        <div
          className="absolute top-0 h-full bg-success/20 rounded-xl"
          style={{
            left: `${idealLow}%`,
            width: `${idealHigh - idealLow}%`,
          }}
        />
        {/* Needle */}
        <motion.div
          className="absolute top-0 h-full w-1.5 rounded-xl bg-foreground shadow-sm"
          initial={{ left: "0%" }}
          animate={{ left: `${pct}%` }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </div>
      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>Slow</span>
        <span className={`font-semibold ${clr}`}>{labelText}</span>
        <span>Fast</span>
      </div>
    </div>
  );
}

/* ─── Segment score -> color (matches PulseRing thresholds) ──── */
function segmentColor(score: number): string {
  if (score >= 70) return "hsl(var(--success))";
  if (score >= 45) return "hsl(var(--warning))";
  return "hsl(var(--destructive))";
}

function flagsSummary(seg: HeatmapSegment): string {
  if (seg.flags.length === 0) return "";
  return `[${seg.flags.map(flagLabel).join(", ")}] `;
}

function flagLabel(flag: string): string {
  switch (flag) {
    case "hedge":
      return "Hedging language";
    case "filler_spike":
      return "Filler word spike";
    case "low_confidence":
      return "Low confidence";
    default:
      return flag;
  }
}

/* ─── Donut colors for filler words ────────────────────────── */
const DONUT_COLORS = [
  "hsl(270, 70%, 60%)",
  "hsl(340, 65%, 55%)",
  "hsl(200, 70%, 55%)",
  "hsl(45, 80%, 55%)",
  "hsl(160, 50%, 45%)",
  "hsl(30, 60%, 50%)",
];

/* ─── Main Component ───────────────────────────────────────── */
interface ConfidencePulseProps {
  evaluations?: Module5Evaluation[];
  duration?: number;
}

export default function ConfidencePulse({
  evaluations,
  duration = 0,
}: ConfidencePulseProps) {
  const [report, setReport] = useState<ConfidenceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapReport | null>(null);

  useEffect(() => {
    if (!evaluations || evaluations.length === 0) {
      setLoading(false);
      return;
    }

    const qaPairs = evaluations
      .filter((ev) => ev.question)
      .map((ev, i) => ({
        question: ev.question || "",
        answer: `Score ${ev.score}. ${ev.feedback || ""}`,
        category: "T",
        question_number: ev.question_number || i + 1,
      }));

    if (qaPairs.length === 0) {
      setLoading(false);
      return;
    }

    analyzeConfidence(qaPairs, duration)
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

    getInterviewHeatmap(qaPairs)
      .then(setHeatmap)
      .catch(() => setHeatmap(null));
  }, [evaluations, duration]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-card border border-border shadow-sm rounded-2xl p-6 mb-5"
      >
        <div className="flex items-center gap-3 mb-6">
          <Loading size="sm" />
          <span className="text-sm font-semibold">
            Analyzing speech patterns...
          </span>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-4 rounded bg-[#F9F9F9] animate-pulse" />
          ))}
        </div>
      </motion.div>
    );
  }

  if (error || !report) {
    return null;
  }

  const { overall, trajectory, filler_breakdown, coaching } = report;

  // Trajectory chart data
  const chartData = trajectory.map((score, i) => ({
    question: `Q${i + 1}`,
    confidence: score,
  }));

  // Weakest moments across the whole interview, for the callout list
  const weakestMoments = (heatmap?.questions || [])
    .flatMap((q) =>
      q.segments
        .filter((s) => s.flags.length > 0)
        .map((s) => ({ ...s, question_number: q.question_number }))
    )
    .sort((a, b) => a.score - b.score)
    .slice(0, 3);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.22 }}
      className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5 relative overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-bold flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          AI Confidence Pulse
          <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-xl bg-foreground/10 border border-primary/20 text-primary">
            Module 12
          </span>
        </h3>
        <MomentumBadge momentum={overall.momentum} />
      </div>

      {/* ── Top metrics row ─────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <PulseRing
          score={Math.round(overall.confidence_score)}
          label="Confidence"
          sublabel={overall.confidence_label}
        />
        <PulseRing
          score={Math.round(overall.vocabulary_richness)}
          label="Vocab Richness"
          color="hsl(var(--primary))"
        />
        <PulseRing
          score={Math.max(
            0,
            Math.min(
              100,
              100 - Math.round(overall.filler_percentage * 5)
            )
          )}
          label="Speech Clarity"
          sublabel={`${overall.total_fillers} fillers`}
          color="hsl(200, 70%, 55%)"
        />
        <div className="flex flex-col items-center justify-center gap-1">
          <div className="text-3xl font-extrabold font-mono text-foreground">
            {overall.speaking_pace_wpm}
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            Words/Min
          </span>
          <span className="text-[10px] text-muted-foreground capitalize">
            {overall.pace_label?.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      {/* ── Stats mini-row ──────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="rounded-xl border border-border bg-[#F9F9F9]/20 p-3 text-center">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Total Words
          </p>
          <p className="text-lg font-extrabold font-mono mt-0.5">
            {overall.total_words.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-[#F9F9F9]/20 p-3 text-center">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Answered
          </p>
          <p className="text-lg font-extrabold font-mono mt-0.5">
            {overall.questions_answered}/{overall.questions_total}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-[#F9F9F9]/20 p-3 text-center">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Fillers Rate
          </p>
          <p className="text-lg font-extrabold font-mono mt-0.5">
            {overall.filler_percentage}%
          </p>
        </div>
      </div>

      <>
          {/* Confidence Trajectory Chart */}
          {chartData.length > 1 && (
            <div className="mb-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5" /> Confidence Trajectory
              </h4>
              <div className="h-[200px] w-full rounded-xl bg-[#F9F9F9]/10 border border-border p-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient
                        id="confidenceGrad"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="hsl(270, 70%, 60%)"
                          stopOpacity={0.4}
                        />
                        <stop
                          offset="95%"
                          stopColor="hsl(270, 70%, 60%)"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="question"
                      tick={{
                        fill: "hsl(var(--muted-foreground))",
                        fontSize: 11,
                      }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{
                        fill: "hsl(var(--muted-foreground))",
                        fontSize: 11,
                      }}
                      axisLine={false}
                      tickLine={false}
                      width={30}
                    />
                    <RechartsTooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="confidence"
                      stroke="hsl(270, 70%, 60%)"
                      strokeWidth={2.5}
                      fill="url(#confidenceGrad)"
                      dot={{
                        r: 4,
                        fill: "hsl(270, 70%, 60%)",
                        stroke: "hsl(var(--card))",
                        strokeWidth: 2,
                      }}
                      activeDot={{
                        r: 6,
                        fill: "hsl(270, 70%, 60%)",
                        stroke: "hsl(var(--card))",
                        strokeWidth: 2,
                      }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ── Replay Heatmap ──────────────────────────────── */}
          {heatmap && heatmap.questions.some((q) => q.segments.length > 0) && (
            <div className="mb-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <Zap className="w-3.5 h-3.5" /> Replay Heatmap
              </h4>
              <div className="space-y-2.5">
                {heatmap.questions
                  .filter((q) => q.segments.length > 0)
                  .map((q) => (
                    <div key={q.question_number} className="flex items-center gap-2">
                      <span className="w-7 flex-shrink-0 text-[10px] font-mono font-semibold text-muted-foreground">
                        Q{q.question_number}
                      </span>
                      <div className="relative flex h-4 flex-1 overflow-hidden rounded-xl border border-border">
                        {q.segments.map((seg, i) => (
                          <div
                            key={i}
                            title={`${flagsSummary(seg)}${seg.text}`}
                            className="h-full transition-opacity hover:opacity-80"
                            style={{
                              width: `${Math.max(
                                1,
                                (seg.end_pct - seg.start_pct) * 100
                              )}%`,
                              backgroundColor: segmentColor(seg.score),
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
              <p className="mt-2 text-[10px] text-muted-foreground">
                Segment position reflects each sentence's share of the answer, not real elapsed time.
              </p>

              {weakestMoments.length > 0 && (
                <div className="mt-4 space-y-2">
                  <h5 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                    Moments You Lost Momentum
                  </h5>
                  {weakestMoments.map((m, i) => (
                    <div
                      key={i}
                      className="rounded-xl border border-border bg-[#F9F9F9]/20 p-3"
                    >
                      <div className="mb-1 flex items-center justify-between">
                        <span className="text-[10px] font-mono font-semibold text-muted-foreground">
                          Q{m.question_number} &middot; score {m.score}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {m.flags.map(flagLabel).join(", ")}
                        </span>
                      </div>
                      <p className="text-xs text-foreground/70 italic">"{m.text}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Pace Gauge + Filler Donut side by side */}
          <div className="grid md:grid-cols-2 gap-5 mb-6">
            {/* Pace Gauge */}
            <div className="rounded-xl border border-border bg-[#F9F9F9]/10 p-4">
              <PaceGauge
                wpm={overall.speaking_pace_wpm}
                label={overall.pace_label}
              />
            </div>

            {/* Filler Word Donut */}
            {filler_breakdown.length > 0 && (
              <div className="rounded-xl border border-border bg-[#F9F9F9]/10 p-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                  <Mic className="w-3.5 h-3.5" /> Filler Words Breakdown
                </h4>
                <div className="flex items-center gap-4">
                  <div className="h-[130px] w-[130px] flex-shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={filler_breakdown}
                          dataKey="count"
                          nameKey="word"
                          cx="50%"
                          cy="50%"
                          innerRadius={35}
                          outerRadius={55}
                          paddingAngle={3}
                          strokeWidth={0}
                        >
                          {filler_breakdown.map((_entry, i) => (
                            <Cell
                              key={i}
                              fill={DONUT_COLORS[i % DONUT_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <RechartsTooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                            fontSize: 12,
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex-1 space-y-1.5">
                    {filler_breakdown.slice(0, 5).map((f, i) => (
                      <div
                        key={f.word}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="flex items-center gap-2">
                          <span
                            className="w-2.5 h-2.5 rounded-xl"
                            style={{
                              backgroundColor:
                                DONUT_COLORS[i % DONUT_COLORS.length],
                            }}
                          />
                          <span className="font-medium text-foreground">
                            "{f.word}"
                          </span>
                        </span>
                        <span className="font-mono font-bold text-muted-foreground">
                          ×{f.count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </>

      {/* ── AI Communication Coach ──────────────────────────── */}
      {coaching.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-primary" /> AI Communication
            Coach
          </h4>
          <div className="grid gap-3 md:grid-cols-2">
            {coaching.map((tip, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
                className="rounded-xl border border-border bg-card shadow-sm border border-border p-4 transition-all hover:border-primary/20 hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-foreground/10 flex items-center justify-center flex-shrink-0">
                    <CoachIcon icon={tip.icon} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-foreground mb-1">
                      {tip.title}
                    </p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {tip.tip}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>


        </div>
      )}
    </motion.div>
  );
}
