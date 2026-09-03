import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import {
  BarChart3, TrendingUp, Target, Flame, Trophy, Clock, Calendar, Zap,
  ArrowUpRight, ArrowDownRight, Gauge
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from "recharts";
import EmptyState from "@/components/EmptyState";
import LeagueLeaderboard from "@/components/LeagueLeaderboard";
import { useAuth } from "@/components/AuthProvider";
<<<<<<< HEAD
import { getAnalyticsSummary, getInterviewHistory, type AnalyticsSummary } from "@/lib/api";
=======
import { getInterviewHistory } from "@/lib/api";
>>>>>>> origin/main
import { getActiveDays } from "@/lib/activityLog";

/* ──────────────────────────────────────────── */
/*  Types                                       */
/* ──────────────────────────────────────────── */
interface HistoryEntry {
  id?: string;
  candidateName?: string;
  date?: string;
  overallScore?: number;
  overallGrade?: string;
  duration?: number;
  totalQuestions?: number;
  answeredQuestions?: number;
  interviewType?: string;
}

// Normalize a backend history record into the flat shape this dashboard uses.
function normalizeEntry(raw: Record<string, unknown>): HistoryEntry {
  const finalScores = (raw.finalScores as { overall?: number } | undefined) || undefined;
  let duration: number | undefined;
  let interviewType: string | undefined;
  if (typeof raw.details_json === "string") {
    try {
      const details = JSON.parse(raw.details_json) as Record<string, unknown>;
      if (typeof details.duration === "number") duration = details.duration;
      if (typeof details.interviewType === "string") interviewType = details.interviewType;
    } catch {
      // Malformed details_json — fall back to the defaults above.
    }
  }
  return {
    id: raw.id as string | undefined,
    candidateName: raw.candidateName as string | undefined,
    date: raw.date as string | undefined,
    overallScore: finalScores?.overall ?? (raw.overallScore as number | undefined),
    overallGrade: raw.finalGrade as string | undefined,
    duration,
    totalQuestions: raw.totalQuestions as number | undefined,
    interviewType,
  };
}


/* ──────────────────────────────────────────── */
/*  Stat Card                                   */
/* ──────────────────────────────────────────── */
function StatCard({ icon, label, value, change, color }: {
  icon: React.ReactNode; label: string; value: string | number; change?: number; color?: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm flex items-center gap-4 group hover:shadow-md transition-shadow">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color || "bg-brand/10 text-brand"}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted-foreground font-medium">{label}</p>
        <p className="text-xl font-bold text-foreground tracking-tight">{value}</p>
      </div>
      {change !== undefined && (
        <div className={`flex items-center gap-0.5 text-xs font-bold ${change >= 0 ? "text-success" : "text-destructive"}`}>
          {change >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
          {Math.abs(change)}%
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Activity Heatmap (GitHub-style)             */
/* ──────────────────────────────────────────── */
const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

function toLocalDateStr(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function ActivityHeatmap({ history, activeDaySet }: { history: HistoryEntry[]; activeDaySet: Set<string> }) {
  const activityMap = useMemo(() => {
    const map: Record<string, number> = {};
    for (const h of history) {
      if (h.date) {
        const day = h.date.split("T")[0];
        map[day] = (map[day] || 0) + 1;
      }
    }
    return map;
  }, [history]);

  // Build a full year of weeks (GitHub-style), aligned so each column is a
  // Sun→Sat week. Start from ~53 weeks ago, snapped back to Sunday.
  const { weekColumns, monthTicks, totalActive } = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const start = new Date(today);
    start.setDate(start.getDate() - 364);
    start.setDate(start.getDate() - start.getDay()); // back to Sunday

    const columns: { date: string; count: number; used: boolean; inRange: boolean }[][] = [];
    const ticks: { col: number; label: string }[] = [];
    let active = 0;
    let lastMonth = -1;

    const cursor = new Date(start);
    while (cursor <= today) {
      const week: { date: string; count: number; used: boolean; inRange: boolean }[] = [];
      for (let d = 0; d < 7; d++) {
        const dateStr = toLocalDateStr(cursor);
        const inRange = cursor <= today;
        const count = inRange ? activityMap[dateStr] || 0 : 0;
        const used = inRange && activeDaySet.has(dateStr);
        if (count > 0 || used) active++;
        week.push({ date: dateStr, count, used, inRange });

        // First day of a new month → month label for this column.
        if (d === 0) {
          const month = cursor.getMonth();
          if (month !== lastMonth && cursor.getDate() <= 7) {
            ticks.push({ col: columns.length, label: MONTH_LABELS[month] });
            lastMonth = month;
          }
        }
        cursor.setDate(cursor.getDate() + 1);
      }
      columns.push(week);
    }
    return { weekColumns: columns, monthTicks: ticks, totalActive: active };
  }, [activityMap, activeDaySet]);

  // count = interviews that day; used = app opened that day (no interview).
  const getColor = (count: number, used: boolean, inRange: boolean) => {
    if (!inRange) return "bg-transparent";
    if (count === 0) return used ? "bg-brand/20" : "bg-muted";
    if (count === 1) return "bg-brand/40";
    if (count === 2) return "bg-brand/60";
    if (count === 3) return "bg-brand/80";
    return "bg-brand";
  };

  const CELL = 12; // px, matches w-3/h-3
  const GAP = 3;

  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold flex items-center gap-2 text-foreground">
          <Calendar className="w-4 h-4 text-brand" /> Activity
        </h3>
        <span className="text-xs text-muted-foreground font-medium">
          {totalActive} active {totalActive === 1 ? "day" : "days"} in the last year
        </span>
      </div>

      <div className="overflow-x-auto pb-1">
        <div className="inline-flex flex-col gap-[3px]">
          {/* Month labels */}
          <div className="flex gap-[3px] pl-[30px] h-4 relative">
            {monthTicks.map((tick) => (
              <span
                key={`${tick.col}-${tick.label}`}
                className="absolute text-[10px] text-muted-foreground"
                style={{ left: 30 + tick.col * (CELL + GAP) }}
              >
                {tick.label}
              </span>
            ))}
          </div>

          <div className="flex gap-[3px]">
            {/* Weekday labels */}
            <div className="flex flex-col gap-[3px] pr-1 w-[26px]">
              {WEEKDAY_LABELS.map((label, i) => (
                <span key={i} className="h-3 text-[9px] leading-3 text-muted-foreground text-right">
                  {label}
                </span>
              ))}
            </div>

            {/* Week columns */}
            {weekColumns.map((week, wi) => (
              <div key={wi} className="flex flex-col gap-[3px]">
                {week.map((cell) => (
                  <div
                    key={cell.date}
                    className={`w-3 h-3 rounded-[3px] ${getColor(cell.count, cell.used, cell.inRange)} transition-colors`}
                    title={cell.inRange ? `${cell.date}: ${cell.count > 0 ? `${cell.count} ${cell.count === 1 ? "session" : "sessions"}` : cell.used ? "active" : "no activity"}` : undefined}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-1.5 mt-3 text-[10px] text-muted-foreground">
        <span>Less</span>
        <div className="w-3 h-3 rounded-[3px] bg-muted" />
        <div className="w-3 h-3 rounded-[3px] bg-brand/20" title="Active (no interview)" />
        <div className="w-3 h-3 rounded-[3px] bg-brand/40" />
        <div className="w-3 h-3 rounded-[3px] bg-brand/60" />
        <div className="w-3 h-3 rounded-[3px] bg-brand/80" />
        <div className="w-3 h-3 rounded-[3px] bg-brand" />
        <span>More</span>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Main Analytics Page                         */
/* ──────────────────────────────────────────── */
export default function AnalyticsDashboard() {
  const { isAuthenticated } = useAuth();
  const [history, setHistory] = useState<HistoryEntry[]>([]);
<<<<<<< HEAD
  const [serverAnalytics, setServerAnalytics] = useState<AnalyticsSummary | null>(null);
=======
>>>>>>> origin/main

  useEffect(() => {
    if (!isAuthenticated) {
      setHistory([]);
<<<<<<< HEAD
      setServerAnalytics(null);
      return;
    }
    let cancelled = false;
    Promise.all([getInterviewHistory(), getAnalyticsSummary()])
      .then(([entries, summary]) => {
        if (cancelled) return;
        setServerAnalytics(summary);
        setHistory((entries as unknown as Record<string, unknown>[]).map(normalizeEntry));
      })
      .catch(() => {
        if (!cancelled) setServerAnalytics(null);
=======
      return;
    }
    let cancelled = false;
    getInterviewHistory()
      .then((entries) => {
        if (cancelled) return;
        setHistory((entries as unknown as Record<string, unknown>[]).map(normalizeEntry));
      })
      .catch(() => {
        if (!cancelled) setHistory([]);
>>>>>>> origin/main
      });
    return () => { cancelled = true; };
  }, [isAuthenticated]);

  // Days the user opened the app (recorded per-day in localStorage).
  const activeDaySet = useMemo(() => getActiveDays(), []);

  // Compute stats
<<<<<<< HEAD
  const totalInterviews = serverAnalytics?.total_interviews ?? history.length;
  const avgScore = serverAnalytics?.average_score ?? (totalInterviews > 0
    ? Math.round(history.reduce((s, h) => s + (h.overallScore || 0), 0) / totalInterviews)
    : 0);
=======
  const totalInterviews = history.length;
  const avgScore = totalInterviews > 0
    ? Math.round(history.reduce((s, h) => s + (h.overallScore || 0), 0) / totalInterviews)
    : 0;
>>>>>>> origin/main
  const totalDuration = history.reduce((s, h) => s + (h.duration || 0), 0);
  const avgDuration = totalInterviews > 0 ? Math.round(totalDuration / totalInterviews / 60) : 0;

  // Score trend data
  const scoreTrend = useMemo(() => {
    return history.slice(-15).map((h, i) => ({
      name: `#${i + 1}`,
      score: h.overallScore || 0,
      date: h.date ? new Date(h.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : `Interview ${i + 1}`
    }));
  }, [history]);

  // Improvement trend
  const scoreChange = useMemo(() => {
    if (history.length < 2) return undefined;
    const recent = history.slice(-3).reduce((s, h) => s + (h.overallScore || 0), 0) / Math.min(3, history.length);
    const older = history.slice(0, 3).reduce((s, h) => s + (h.overallScore || 0), 0) / Math.min(3, history.length);
    if (older === 0) return undefined;
    return Math.round(((recent - older) / older) * 100);
  }, [history]);

  // Breakdown by mock interview type practiced most recently
  const typeBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const h of history) {
      const key = h.interviewType || "General";
      counts[key] = (counts[key] || 0) + 1;
    }
    return Object.entries(counts).map(([subject, count]) => ({
      subject,
      score: Math.min(100, count * 20),
    }));
  }, [history]);

  const radarData = typeBreakdown.length > 0 ? typeBreakdown : [
    { subject: "Technical Screen", score: 0 },
    { subject: "Coding", score: 0 },
    { subject: "System Design", score: 0 },
    { subject: "Behavioral", score: 0 },
  ];

  /* ── Readiness Score ──────────────────────────────────────
   * A single 0-100 rollup of prep, weighted toward recent mock
   * interview performance but rewarding consistency too.
   * Recomputed live from existing localStorage state — no new
   * backend dependency required.
   */
  // Distinct calendar days the user was active — either an interview was
  // saved that day, or the app was opened (any usage). Union of both sources.
  const activeDays = useMemo(() => {
    const days = new Set<string>(activeDaySet);
    for (const h of history) {
      if (h.date) days.add(h.date.split("T")[0]);
    }
    return days.size;
  }, [history, activeDaySet]);

  const readiness = useMemo(() => {
    const interviewComponent = avgScore; // 0-100, already an average
    const volumeComponent = Math.min(100, totalInterviews * 10);
    const consistencyComponent = Math.min(100, activeDays * 10);

    const hasInterviews = totalInterviews > 0;
    const score = Math.round(
      (hasInterviews ? interviewComponent * 0.55 : 0) +
      volumeComponent * (hasInterviews ? 0.25 : 0.4) +
      consistencyComponent * (hasInterviews ? 0.2 : 0.6)
    );

    let tier: { label: string; color: string };
    if (score >= 80) tier = { label: "Interview Ready", color: "text-success" };
    else if (score >= 55) tier = { label: "Building Momentum", color: "text-brand" };
    else if (score >= 25) tier = { label: "Getting Started", color: "text-warning" };
    else tier = { label: "Just Beginning", color: "text-muted-foreground" };

    return { score: Math.min(100, Math.max(0, score)), tier };
  }, [avgScore, totalInterviews, activeDays]);

  return (
    <div className="max-w-5xl mx-auto py-6 space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 border border-brand/20">
            <BarChart3 className="w-5 h-5 text-brand" />
          </div>
          <div>
            <h1 className="text-3xl font-sans font-bold tracking-tight text-[#1E1F1B]">Analytics Dashboard</h1>
            <p className="text-sm text-muted-foreground">Track your mock interview progress</p>
          </div>
        </div>
      </motion.div>

      {/* Readiness Score */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.02 }}
        className="rounded-2xl border border-border bg-card p-5 shadow-sm flex flex-col md:flex-row items-center gap-6"
      >
        <div className="relative shrink-0" style={{ width: 96, height: 96 }}>
          <svg viewBox="0 0 96 96" className="-rotate-90 w-full h-full">
            <circle cx={48} cy={48} r={40} className="fill-none stroke-muted" strokeWidth={8} />
            <circle
              cx={48} cy={48} r={40}
              className="fill-none"
              stroke="hsl(var(--brand))"
              strokeWidth={8}
              strokeLinecap="round"
              strokeDasharray={2 * Math.PI * 40}
              strokeDashoffset={2 * Math.PI * 40 - (readiness.score / 100) * 2 * Math.PI * 40}
              style={{ transition: "stroke-dashoffset 1s ease" }}
            />
          </svg>
          <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-xl font-extrabold font-mono">
            {readiness.score}
          </span>
        </div>
        <div className="flex-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2 mb-1">
            <Gauge className="w-4 h-4 text-brand" />
            <h3 className="text-sm font-bold text-foreground">Interview Readiness Score</h3>
          </div>
          <p className={`text-lg font-extrabold ${readiness.tier.color}`}>{readiness.tier.label}</p>
          <p className="text-xs text-muted-foreground mt-1 max-w-md">
            A rolling 0–100 score blending your recent mock interview performance, practice
            volume, and day-to-day consistency.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-orange-500/20 bg-orange-500/10 px-4 py-3 shrink-0">
          <Flame className="w-5 h-5 text-orange-500" />
          <div>
            <p className="text-lg font-extrabold text-foreground leading-none">{activeDays}</p>
            <p className="text-[10px] text-muted-foreground font-medium">active days</p>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3"
      >
        <StatCard icon={<Trophy className="w-5 h-5" />} label="Total Interviews" value={totalInterviews} color="bg-brand/10 text-brand" />
        <StatCard icon={<Target className="w-5 h-5" />} label="Average Score" value={avgScore > 0 ? `${avgScore}/100` : "—"} change={scoreChange} color="bg-success/10 text-success" />
        <StatCard icon={<Flame className="w-5 h-5" />} label="Active Days" value={`${activeDays} ${activeDays === 1 ? "day" : "days"}`} color="bg-orange-500/10 text-orange-500" />
        <StatCard icon={<Clock className="w-5 h-5" />} label="Avg Duration" value={avgDuration > 0 ? `${avgDuration} min` : "—"} color="bg-info/10 text-info" />
      </motion.div>

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Score Trend */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl border border-border bg-card p-5 shadow-sm"
        >
          <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-foreground">
            <TrendingUp className="w-4 h-4 text-brand" /> Score Trend
          </h3>
          {scoreTrend.length > 1 ? (
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={scoreTrend}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--brand))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--brand))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <RechartsTooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }}
                  />
                  <Area type="monotone" dataKey="score" stroke="hsl(var(--brand))" fill="url(#scoreGrad)" strokeWidth={2.5} dot={{ r: 4, fill: "hsl(var(--brand))" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              icon={TrendingUp}
              title="No score trend yet"
              description="Complete a couple of interviews to see your progress plotted here."
              className="h-[220px] py-0"
            />
          )}
        </motion.div>

        {/* Interview Type Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-2xl border border-border bg-card p-5 shadow-sm"
        >
          <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-foreground">
            <Zap className="w-4 h-4 text-brand" /> Practice Coverage
          </h3>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="68%" data={radarData}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "hsl(var(--foreground))", fontSize: 11, fontWeight: 500 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }} />
                <Radar name="Sessions" dataKey="score" stroke="hsl(var(--brand))" fill="hsl(var(--brand))" fillOpacity={0.2} strokeWidth={2} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Activity Heatmap */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <ActivityHeatmap history={history} activeDaySet={activeDaySet} />
      </motion.div>

      {/* Interview League — ELO ladder over the graded coding corpus */}
      <LeagueLeaderboard />
    </div>
  );
}
