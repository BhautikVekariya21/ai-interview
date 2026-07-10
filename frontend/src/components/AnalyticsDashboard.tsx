import { useState, useEffect, useMemo } from "react";
import { m as motion } from "framer-motion";
import {
  BarChart3, TrendingUp, Target, Flame, Brain, Code2, MessageSquare, Server,
  Trophy, Clock, Calendar, Zap, ChevronRight, ArrowUpRight, ArrowDownRight, Gauge
} from "lucide-react";
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from "recharts";

/* ──────────────────────────────────────────── */
/*  Persistence                                 */
/* ──────────────────────────────────────────── */
const HISTORY_KEY = "interview_history_v2";
const STREAK_KEY = "daily_challenge_state";
const FLASHCARDS_KEY = "dsa_flashcards_progress";
const SD_KEY = "sd_playbook_progress";
const STAR_KEY = "star_builder_stories";
const CODING_KEY = "coding_practice_progress";
const ACHIEVEMENTS_KEY = "achievements_unlocked";
const READINESS_KEY = "readiness_streak_v1";

interface HistoryEntry {
  id?: string;
  candidateName?: string;
  date?: string;
  overallScore?: number;
  overallGrade?: string;
  duration?: number;
  totalQuestions?: number;
  answeredQuestions?: number;
}

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return [];
}

/* ──────────────────────────────────────────── */
/*  Stat Card                                   */
/* ──────────────────────────────────────────── */
function StatCard({ icon, label, value, change, color }: {
  icon: React.ReactNode; label: string; value: string | number; change?: number; color?: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm flex items-center gap-4 group hover:shadow-md transition-shadow">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color || "bg-primary/10 text-primary"}`}>
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
function ActivityHeatmap({ history }: { history: HistoryEntry[] }) {
  const weeks = 20;
  const now = new Date();

  const activityMap = useMemo(() => {
    const map: Record<string, number> = {};
    for (const h of history) {
      if (h.date) {
        const day = h.date.split("T")[0];
        map[day] = (map[day] || 0) + 1;
      }
    }
    // Also add daily challenge data
    try {
      const dcState = JSON.parse(localStorage.getItem(STREAK_KEY) || "{}");
      if (dcState.date) {
        map[dcState.date] = (map[dcState.date] || 0) + 1;
      }
    } catch {}
    return map;
  }, [history]);

  const cells: { date: string; count: number; dayOfWeek: number }[] = [];
  for (let i = weeks * 7 - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split("T")[0];
    cells.push({ date: dateStr, count: activityMap[dateStr] || 0, dayOfWeek: d.getDay() });
  }

  // Group into weeks
  const weekColumns: typeof cells[] = [];
  for (let i = 0; i < cells.length; i += 7) {
    weekColumns.push(cells.slice(i, i + 7));
  }

  const getColor = (count: number) => {
    if (count === 0) return "bg-muted";
    if (count === 1) return "bg-primary/30";
    if (count === 2) return "bg-primary/50";
    return "bg-primary/80";
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
      <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-foreground">
        <Calendar className="w-4 h-4 text-primary" /> Activity (Last {weeks} weeks)
      </h3>
      <div className="flex gap-[3px] overflow-x-auto pb-1">
        {weekColumns.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {week.map((cell) => (
              <div
                key={cell.date}
                className={`w-3 h-3 rounded-[3px] ${getColor(cell.count)} transition-colors`}
                title={`${cell.date}: ${cell.count} activities`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-3 text-[10px] text-muted-foreground">
        <span>Less</span>
        <div className="w-3 h-3 rounded-[3px] bg-muted" />
        <div className="w-3 h-3 rounded-[3px] bg-primary/30" />
        <div className="w-3 h-3 rounded-[3px] bg-primary/50" />
        <div className="w-3 h-3 rounded-[3px] bg-primary/80" />
        <span>More</span>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Main Analytics Page                         */
/* ──────────────────────────────────────────── */
export default function AnalyticsDashboard() {
  const history = useMemo(() => loadHistory(), []);

  // Compute stats
  const totalInterviews = history.length;
  const avgScore = totalInterviews > 0
    ? Math.round(history.reduce((s, h) => s + (h.overallScore || 0), 0) / totalInterviews)
    : 0;
  const totalDuration = history.reduce((s, h) => s + (h.duration || 0), 0);
  const avgDuration = totalInterviews > 0 ? Math.round(totalDuration / totalInterviews / 60) : 0;

  // Streak
  const streakData = useMemo(() => {
    try {
      const raw = localStorage.getItem(STREAK_KEY);
      if (raw) return JSON.parse(raw);
    } catch {}
    return { streak: 0 };
  }, []);

  // Flashcards
  const flashcardProgress = useMemo(() => {
    try {
      const raw = localStorage.getItem(FLASHCARDS_KEY);
      if (raw) {
        const p = JSON.parse(raw);
        return { mastered: p.mastered?.length || 0, review: p.review?.length || 0 };
      }
    } catch {}
    return { mastered: 0, review: 0 };
  }, []);

  // System Design
  const sdStudied = useMemo(() => {
    try {
      const raw = localStorage.getItem(SD_KEY);
      if (raw) return (JSON.parse(raw) as number[]).length;
    } catch {}
    return 0;
  }, []);

  // STAR stories
  const starCount = useMemo(() => {
    try {
      const raw = localStorage.getItem(STAR_KEY);
      if (raw) return (JSON.parse(raw) as any[]).length;
    } catch {}
    return 0;
  }, []);

  // Coding solved
  const { codingSolved, codingStreak } = useMemo(() => {
    try {
      const raw = localStorage.getItem(CODING_KEY);
      if (raw) {
        const p = JSON.parse(raw);
        return { codingSolved: Object.keys(p.solved || {}).length, codingStreak: p.streak || 0 };
      }
    } catch {}
    return { codingSolved: 0, codingStreak: 0 };
  }, []);

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

  // Category breakdown
  const radarData = [
    { subject: "Technical", score: Math.min(avgScore + 5, 100) },
    { subject: "Behavioral", score: Math.max(avgScore - 8, 20) },
    { subject: "System Design", score: sdStudied > 6 ? 75 : sdStudied > 3 ? 50 : 25 },
    { subject: "Coding", score: codingSolved > 10 ? 80 : codingSolved > 5 ? 55 : 30 },
    { subject: "Communication", score: Math.min(avgScore + 3, 100) },
  ];

  // Progress bars data
  const progressItems = [
    { label: "Flashcards Mastered", current: flashcardProgress.mastered, total: 75, icon: <Brain className="w-3.5 h-3.5" />, color: "bg-primary" },
    { label: "System Design Studied", current: sdStudied, total: 12, icon: <Server className="w-3.5 h-3.5" />, color: "bg-info" },
    { label: "STAR Stories Written", current: starCount, total: 10, icon: <MessageSquare className="w-3.5 h-3.5" />, color: "bg-amber-500" },
    { label: "Coding Problems Solved", current: codingSolved, total: 30, icon: <Code2 className="w-3.5 h-3.5" />, color: "bg-success" },
  ];

  /* ── Readiness Score ──────────────────────────────────────
   * A single 0-100 rollup of prep across every module, weighted
   * toward the things that actually predict interview performance
   * (recent interview scores) but rewarding consistent practice
   * everywhere else too. Recomputed live from existing localStorage
   * state — no new backend dependency required.
   */
  const readiness = useMemo(() => {
    const interviewComponent = avgScore; // 0-100, already an average
    const flashcardComponent = Math.min(100, Math.round((flashcardProgress.mastered / 75) * 100));
    const sdComponent = Math.min(100, Math.round((sdStudied / 12) * 100));
    const starComponent = Math.min(100, Math.round((starCount / 10) * 100));
    const codingComponent = Math.min(100, Math.round((codingSolved / 30) * 100));
    const practiceStreakDays = Math.max(streakData.streak || 0, codingStreak || 0);
    const streakComponent = Math.min(100, practiceStreakDays * 10);

    const hasInterviews = totalInterviews > 0;
    const score = Math.round(
      (hasInterviews ? interviewComponent * 0.4 : 0) +
      flashcardComponent * (hasInterviews ? 0.12 : 0.2) +
      sdComponent * (hasInterviews ? 0.12 : 0.2) +
      starComponent * (hasInterviews ? 0.1 : 0.15) +
      codingComponent * (hasInterviews ? 0.16 : 0.25) +
      streakComponent * (hasInterviews ? 0.1 : 0.2)
    );

    let tier: { label: string; color: string };
    if (score >= 80) tier = { label: "Interview Ready", color: "text-success" };
    else if (score >= 55) tier = { label: "Building Momentum", color: "text-primary" };
    else if (score >= 25) tier = { label: "Getting Started", color: "text-warning" };
    else tier = { label: "Just Beginning", color: "text-muted-foreground" };

    return { score: Math.min(100, Math.max(0, score)), tier, practiceStreakDays };
  }, [avgScore, flashcardProgress.mastered, sdStudied, starCount, codingSolved, streakData.streak, codingStreak, totalInterviews]);

  // Track a rolling "practice active today" streak that spans every
  // module (not just daily challenge or coding), so candidates are
  // rewarded for any form of consistent prep.
  useEffect(() => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const raw = localStorage.getItem(READINESS_KEY);
      const state = raw ? JSON.parse(raw) : { lastDate: null, streak: 0 };
      if (state.lastDate === today) return;
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const isConsecutive = state.lastDate === yesterday.toISOString().split("T")[0];
      const nextStreak = isConsecutive ? (state.streak || 0) + 1 : 1;
      localStorage.setItem(READINESS_KEY, JSON.stringify({ lastDate: today, streak: nextStreak }));
    } catch {}
  }, []);

  const overallPracticeStreak = (() => {
    try {
      const raw = localStorage.getItem(READINESS_KEY);
      if (raw) return (JSON.parse(raw).streak as number) || 0;
    } catch {}
    return 0;
  })();

  return (
    <div className="max-w-5xl mx-auto py-6 space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Analytics Dashboard</h1>
            <p className="text-sm text-muted-foreground">Track your interview preparation progress</p>
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
              stroke="hsl(var(--primary))"
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
            <Gauge className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-bold text-foreground">Interview Readiness Score</h3>
          </div>
          <p className={`text-lg font-extrabold ${readiness.tier.color}`}>{readiness.tier.label}</p>
          <p className="text-xs text-muted-foreground mt-1 max-w-md">
            A rolling 0–100 score blending your recent interview performance, flashcard mastery,
            system design and STAR prep, coding practice, and consistency across modules.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-orange-500/20 bg-orange-500/10 px-4 py-3 shrink-0">
          <Flame className="w-5 h-5 text-orange-500" />
          <div>
            <p className="text-lg font-extrabold text-foreground leading-none">{overallPracticeStreak}</p>
            <p className="text-[10px] text-muted-foreground font-medium">day practice streak</p>
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
        <StatCard icon={<Trophy className="w-5 h-5" />} label="Total Interviews" value={totalInterviews} color="bg-primary/10 text-primary" />
        <StatCard icon={<Target className="w-5 h-5" />} label="Average Score" value={avgScore > 0 ? `${avgScore}/100` : "—"} change={scoreChange} color="bg-success/10 text-success" />
        <StatCard icon={<Flame className="w-5 h-5" />} label="Current Streak" value={`${streakData.streak || 0} days`} color="bg-orange-500/10 text-orange-500" />
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
            <TrendingUp className="w-4 h-4 text-primary" /> Score Trend
          </h3>
          {scoreTrend.length > 1 ? (
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={scoreTrend}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <RechartsTooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }}
                  />
                  <Area type="monotone" dataKey="score" stroke="hsl(var(--primary))" fill="url(#scoreGrad)" strokeWidth={2.5} dot={{ r: 4, fill: "hsl(var(--primary))" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
              Complete interviews to see your score trend
            </div>
          )}
        </motion.div>

        {/* Skills Radar */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-2xl border border-border bg-card p-5 shadow-sm"
        >
          <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-foreground">
            <Zap className="w-4 h-4 text-primary" /> Skills Breakdown
          </h3>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="68%" data={radarData}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "hsl(var(--foreground))", fontSize: 11, fontWeight: 500 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }} />
                <Radar name="Score" dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.2} strokeWidth={2} />
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
        <ActivityHeatmap history={history} />
      </motion.div>

      {/* Preparation Progress */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="rounded-2xl border border-border bg-card p-5 shadow-sm"
      >
        <h3 className="text-sm font-bold mb-5 flex items-center gap-2 text-foreground">
          <Target className="w-4 h-4 text-primary" /> Preparation Progress
        </h3>
        <div className="space-y-4">
          {progressItems.map((item) => {
            const pct = item.total > 0 ? Math.round((item.current / item.total) * 100) : 0;
            return (
              <div key={item.label}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    {item.icon} {item.label}
                  </span>
                  <span className="text-xs font-bold font-mono text-foreground">{item.current}/{item.total}</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full rounded-full ${item.color}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
