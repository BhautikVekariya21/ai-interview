import { useState, useMemo, useEffect } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Award, Lock, Trophy, Flame, Brain, Code2, MessageSquare, Server, Star, Target,
  Zap, CheckCircle2, Crown, Sparkles, Rocket, Medal, Shield
} from "lucide-react";
import { toast } from "sonner";

/* ──────────────────────────────────────────── */
/*  Achievement definitions                     */
/* ──────────────────────────────────────────── */
interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  category: "interviews" | "streak" | "practice" | "mastery";
  check: () => { unlocked: boolean; progress: number; total: number };
}

const STORAGE_KEY = "achievements_unlocked";
const HISTORY_KEY = "interview_history_v2";
const STREAK_KEY = "daily_challenge_state";
const FLASHCARDS_KEY = "dsa_flashcards_progress";
const SD_KEY = "sd_playbook_progress";
const STAR_KEY = "star_builder_stories";
const CODING_KEY = "coding_practice_solved";

function safeParseJson(key: string, fallback: any = null) {
  try { const raw = localStorage.getItem(key); if (raw) return JSON.parse(raw); } catch {} return fallback;
}

const ACHIEVEMENTS: Achievement[] = [
  // Interview milestones
  {
    id: "first_interview", title: "First Steps", description: "Complete your first mock interview",
    icon: <Rocket className="w-5 h-5" />, color: "from-blue-500 to-cyan-400", category: "interviews",
    check: () => { const h = safeParseJson(HISTORY_KEY, []); return { unlocked: h.length >= 1, progress: Math.min(h.length, 1), total: 1 }; },
  },
  {
    id: "five_interviews", title: "Getting Serious", description: "Complete 5 mock interviews",
    icon: <Target className="w-5 h-5" />, color: "from-indigo-500 to-blue-400", category: "interviews",
    check: () => { const h = safeParseJson(HISTORY_KEY, []); return { unlocked: h.length >= 5, progress: Math.min(h.length, 5), total: 5 }; },
  },
  {
    id: "ten_interviews", title: "Interview Veteran", description: "Complete 10 mock interviews",
    icon: <Shield className="w-5 h-5" />, color: "from-purple-500 to-pink-400", category: "interviews",
    check: () => { const h = safeParseJson(HISTORY_KEY, []); return { unlocked: h.length >= 10, progress: Math.min(h.length, 10), total: 10 }; },
  },
  {
    id: "perfect_score", title: "Perfection", description: "Score 90+ on any interview",
    icon: <Crown className="w-5 h-5" />, color: "from-yellow-500 to-amber-400", category: "interviews",
    check: () => {
      const h = safeParseJson(HISTORY_KEY, []);
      const best = h.reduce((max: number, e: any) => Math.max(max, e.overallScore || 0), 0);
      return { unlocked: best >= 90, progress: Math.min(best, 90), total: 90 };
    },
  },

  // Streak
  {
    id: "streak_3", title: "On Fire", description: "Build a 3-day challenge streak",
    icon: <Flame className="w-5 h-5" />, color: "from-orange-500 to-red-400", category: "streak",
    check: () => { const s = safeParseJson(STREAK_KEY, {}); const streak = s.streak || 0; return { unlocked: streak >= 3, progress: Math.min(streak, 3), total: 3 }; },
  },
  {
    id: "streak_7", title: "Weekly Warrior", description: "Build a 7-day challenge streak",
    icon: <Zap className="w-5 h-5" />, color: "from-amber-500 to-orange-400", category: "streak",
    check: () => { const s = safeParseJson(STREAK_KEY, {}); const streak = s.streak || 0; return { unlocked: streak >= 7, progress: Math.min(streak, 7), total: 7 }; },
  },
  {
    id: "streak_30", title: "Unstoppable", description: "Build a 30-day challenge streak",
    icon: <Trophy className="w-5 h-5" />, color: "from-red-500 to-rose-400", category: "streak",
    check: () => { const s = safeParseJson(STREAK_KEY, {}); const streak = s.streak || 0; return { unlocked: streak >= 30, progress: Math.min(streak, 30), total: 30 }; },
  },

  // Practice
  {
    id: "flashcards_25", title: "Pattern Learner", description: "Master 25 DSA flashcards",
    icon: <Brain className="w-5 h-5" />, color: "from-emerald-500 to-teal-400", category: "practice",
    check: () => { const p = safeParseJson(FLASHCARDS_KEY, { mastered: [] }); const c = p.mastered?.length || 0; return { unlocked: c >= 25, progress: Math.min(c, 25), total: 25 }; },
  },
  {
    id: "flashcards_75", title: "Algorithm Master", description: "Master all 75 DSA flashcards",
    icon: <Sparkles className="w-5 h-5" />, color: "from-teal-500 to-cyan-400", category: "practice",
    check: () => { const p = safeParseJson(FLASHCARDS_KEY, { mastered: [] }); const c = p.mastered?.length || 0; return { unlocked: c >= 75, progress: Math.min(c, 75), total: 75 }; },
  },
  {
    id: "sd_6", title: "System Thinker", description: "Study 6 system design problems",
    icon: <Server className="w-5 h-5" />, color: "from-sky-500 to-blue-400", category: "practice",
    check: () => { const s = safeParseJson(SD_KEY, []); return { unlocked: s.length >= 6, progress: Math.min(s.length, 6), total: 6 }; },
  },
  {
    id: "sd_12", title: "Architect", description: "Study all 12 system design problems",
    icon: <Medal className="w-5 h-5" />, color: "from-violet-500 to-purple-400", category: "practice",
    check: () => { const s = safeParseJson(SD_KEY, []); return { unlocked: s.length >= 12, progress: Math.min(s.length, 12), total: 12 }; },
  },

  // Mastery
  {
    id: "star_5", title: "Storyteller", description: "Write 5 STAR stories",
    icon: <Star className="w-5 h-5" />, color: "from-yellow-500 to-orange-400", category: "mastery",
    check: () => { const s = safeParseJson(STAR_KEY, []); return { unlocked: s.length >= 5, progress: Math.min(s.length, 5), total: 5 }; },
  },
  {
    id: "coding_10", title: "Code Warrior", description: "Solve 10 coding problems",
    icon: <Code2 className="w-5 h-5" />, color: "from-green-500 to-emerald-400", category: "mastery",
    check: () => { const s = safeParseJson(CODING_KEY, []); return { unlocked: s.length >= 10, progress: Math.min(s.length, 10), total: 10 }; },
  },
  {
    id: "all_tools", title: "Full Arsenal", description: "Use every prep tool at least once",
    icon: <Award className="w-5 h-5" />, color: "from-fuchsia-500 to-pink-400", category: "mastery",
    check: () => {
      let count = 0;
      if (safeParseJson(HISTORY_KEY, []).length > 0) count++;
      if (safeParseJson(FLASHCARDS_KEY, { mastered: [] }).mastered?.length > 0) count++;
      if (safeParseJson(SD_KEY, []).length > 0) count++;
      if (safeParseJson(STAR_KEY, []).length > 0) count++;
      if (safeParseJson(CODING_KEY, []).length > 0) count++;
      return { unlocked: count >= 5, progress: count, total: 5 };
    },
  },
];

const CATEGORY_LABELS: Record<string, string> = {
  interviews: "Interview Milestones",
  streak: "Streak Champions",
  practice: "Practice Progress",
  mastery: "Mastery Badges",
};

/* ──────────────────────────────────────────── */
/*  Achievement Card                            */
/* ──────────────────────────────────────────── */
function AchievementCard({ achievement }: { achievement: Achievement }) {
  const { unlocked, progress, total } = achievement.check();
  const pct = Math.round((progress / total) * 100);

  return (
    <motion.div
      whileHover={{ y: -3 }}
      className={`rounded-2xl border p-5 transition-all ${
        unlocked
          ? "border-primary/30 bg-card shadow-lg"
          : "border-border bg-card/60 opacity-70"
      }`}
    >
      {/* Icon */}
      <div className="flex items-center justify-between mb-3">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white bg-gradient-to-br ${achievement.color} ${
          unlocked ? "shadow-lg" : "grayscale opacity-50"
        }`}>
          {unlocked ? achievement.icon : <Lock className="w-5 h-5" />}
        </div>
        {unlocked && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="flex items-center gap-1 text-[11px] font-bold text-success bg-success/10 border border-success/20 px-2 py-0.5 rounded-lg"
          >
            <CheckCircle2 className="w-3 h-3" /> Unlocked
          </motion.div>
        )}
      </div>

      {/* Title */}
      <h3 className={`text-base font-bold mb-1 ${unlocked ? "text-foreground" : "text-muted-foreground"}`}>
        {achievement.title}
      </h3>
      <p className="text-xs text-muted-foreground mb-3">{achievement.description}</p>

      {/* Progress bar */}
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className={`h-full rounded-full ${unlocked ? "bg-gradient-to-r " + achievement.color : "bg-muted-foreground/30"}`}
        />
      </div>
      <p className="text-[10px] font-mono text-muted-foreground mt-1.5 text-right">
        {progress}/{total}
      </p>
    </motion.div>
  );
}

/* ──────────────────────────────────────────── */
/*  Main Page                                   */
/* ──────────────────────────────────────────── */
export default function AchievementsPage() {
  const [filter, setFilter] = useState<string>("all");

  const results = useMemo(() => {
    return ACHIEVEMENTS.map(a => ({ ...a, ...a.check() }));
  }, []);

  const unlockedCount = results.filter(r => r.unlocked).length;
  const totalCount = ACHIEVEMENTS.length;
  const pct = Math.round((unlockedCount / totalCount) * 100);

  const filteredAchievements = useMemo(() => {
    if (filter === "all") return ACHIEVEMENTS;
    if (filter === "unlocked") return ACHIEVEMENTS.filter(a => a.check().unlocked);
    if (filter === "locked") return ACHIEVEMENTS.filter(a => !a.check().unlocked);
    return ACHIEVEMENTS.filter(a => a.category === filter);
  }, [filter]);

  // Check for newly unlocked achievements
  useEffect(() => {
    const prev = safeParseJson(STORAGE_KEY, []) as string[];
    const nowUnlocked = results.filter(r => r.unlocked).map(r => r.id);
    const newOnes = nowUnlocked.filter(id => !prev.includes(id));

    if (newOnes.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nowUnlocked));
      for (const id of newOnes) {
        const ach = ACHIEVEMENTS.find(a => a.id === id);
        if (ach) {
          toast.success(`🏆 Achievement Unlocked: ${ach.title}!`, { description: ach.description });
        }
      }
    }
  }, [results]);

  return (
    <div className="max-w-5xl mx-auto py-6 space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 border border-amber-500/20">
            <Award className="w-5 h-5 text-amber-500" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Achievements</h1>
            <p className="text-sm text-muted-foreground">Track your milestones & unlock badges</p>
          </div>
        </div>
      </motion.div>

      {/* Overall Progress */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="rounded-2xl border border-border bg-card p-5 shadow-sm"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold flex items-center gap-2 text-foreground">
            <Trophy className="w-4 h-4 text-primary" /> Overall Progress
          </h3>
          <span className="text-sm font-bold font-mono text-foreground">{unlockedCount}/{totalCount}</span>
        </div>
        <div className="h-3 bg-muted rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 1 }}
            className="h-full rounded-full"
            style={{ background: "var(--gradient-accent, linear-gradient(135deg, hsl(var(--primary)), hsl(var(--info))))" }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">{pct}% of achievements unlocked</p>
      </motion.div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        {[
          { id: "all", label: "All" },
          { id: "unlocked", label: `Unlocked (${unlockedCount})` },
          { id: "locked", label: `Locked (${totalCount - unlockedCount})` },
          { id: "interviews", label: "Interviews" },
          { id: "streak", label: "Streaks" },
          { id: "practice", label: "Practice" },
          { id: "mastery", label: "Mastery" },
        ].map(f => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
              filter === f.id
                ? "border-primary/30 bg-primary/10 text-primary"
                : "border-transparent text-muted-foreground hover:border-border hover:bg-accent/30"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Achievement Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAchievements.map((ach, i) => (
          <motion.div
            key={ach.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <AchievementCard achievement={ach} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
