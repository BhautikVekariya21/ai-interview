import { useState, useEffect, useRef, useCallback } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Timer, Play, Pause, RotateCcw, Bell, BellOff,
  CheckSquare, Square, Shuffle, ChevronDown, ChevronUp,
  Zap, DollarSign, Target, Copy, CheckCheck,
  BarChart3, Hash, FileText, TrendingUp, CalendarDays,
  Award, Crown, Smile, Meh, Frown, Plus, Trash2,
  BookOpen, Shield, PenTool, Map,
  Calculator, Globe, Activity, HardDrive, Wifi, Server,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { CODING_PROBLEMS, CODING_TOPICS } from "./codingProblemsData";
import { toast } from "sonner";
import { useAuth } from "@/components/AuthProvider";
import ScratchPad from "@/components/ScratchPad";
import MindMapTool from "@/components/MindMapTool";
import type { SavedMindMap } from "@/lib/mindMap";

/* ─── Plan utils ─────────────────────────────────────── */

/* ─── Section Header ─────────────────────────────────── */
function SectionHeader({
  icon, title, subtitle, planBadge,
}: {
  icon: React.ReactNode; title: string; subtitle: string; planBadge?: "pro" | "enterprise";
}) {
  const badgeMap = {
    pro: { label: "Pro", cls: "text-primary bg-primary/10 border-primary/20", icon: <Crown className="w-2.5 h-2.5" /> },
    enterprise: { label: "Enterprise", cls: "text-amber-500 bg-amber-500/10 border-amber-500/20", icon: <Shield className="w-2.5 h-2.5" /> },
  };
  const badge = planBadge ? badgeMap[planBadge] : null;
  return (
    <div className="flex items-start gap-3 mb-6">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary border border-primary/20">{icon}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="text-lg font-bold text-foreground">{title}</h2>
          {badge && (
            <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badge.cls}`}>
              {badge.icon} {badge.label}
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   ── FREE TIER FEATURES ──────────────────────────────
   ══════════════════════════════════════════════════════ */

/* 1. Interview Countdown Timer (FREE) */
const PRESETS = [
  { label: "30 min", seconds: 30 * 60 },
  { label: "45 min", seconds: 45 * 60 },
  { label: "60 min", seconds: 60 * 60 },
  { label: "90 min", seconds: 90 * 60 },
];

function InterviewTimer() {
  const [total, setTotal] = useState(45 * 60);
  const [remaining, setRemaining] = useState(45 * 60);
  const [running, setRunning] = useState(false);
  const [soundOn, setSoundOn] = useState(true);
  const [finished, setFinished] = useState(false);
  const [laps, setLaps] = useState<{ label: string; time: string }[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  const playBeep = useCallback(() => {
    if (!soundOn) return;
    try {
      const ctx = audioCtxRef.current || new AudioContext();
      audioCtxRef.current = ctx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.type = "sine"; osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.4, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
      osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.6);
    } catch {}
  }, [soundOn]);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => {
        setRemaining((r) => {
          if (r <= 1) { clearInterval(intervalRef.current!); setRunning(false); setFinished(true); playBeep(); return 0; }
          if (r === 301) playBeep();
          return r - 1;
        });
      }, 1000);
    } else { clearInterval(intervalRef.current!); }
    return () => clearInterval(intervalRef.current!);
  }, [running, playBeep]);

  const reset = (secs: number) => { clearInterval(intervalRef.current!); setTotal(secs); setRemaining(secs); setRunning(false); setFinished(false); setLaps([]); };
  const addLap = () => {
    const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
    const ss = String(remaining % 60).padStart(2, "0");
    setLaps((l) => [...l, { label: `Lap ${l.length + 1}`, time: `${mm}:${ss}` }]);
  };

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");
  const pct = remaining / total;
  const radius = 54; const circ = 2 * Math.PI * radius;
  const danger = remaining < 300 && remaining > 0;
  const color = finished ? "#ef4444" : danger ? "#f59e0b" : "#6366f1";

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
      <SectionHeader icon={<Timer className="w-5 h-5" />} title="Interview Timer" subtitle="Countdown with 5-min warning bell, laps & end alarm" />
      <div className="flex flex-col items-center gap-6">
        <div className="relative flex items-center justify-center w-36 h-36">
          <svg className="absolute" width="144" height="144" style={{ transform: "rotate(-90deg)" }}>
            <circle cx="72" cy="72" r={radius} fill="none" stroke="currentColor" strokeWidth="6" className="text-muted/20" />
            <circle cx="72" cy="72" r={radius} fill="none" stroke={color} strokeWidth="6"
              strokeDasharray={circ} strokeDashoffset={circ * (1 - pct)}
              style={{ transition: "stroke-dashoffset 1s linear, stroke 0.5s" }} />
          </svg>
          <div className="flex flex-col items-center z-10">
            <span className={`text-3xl font-black font-mono tracking-tighter ${danger ? "text-amber-500" : "text-foreground"} ${finished ? "animate-pulse text-red-500" : ""}`}>{mm}:{ss}</span>
            {finished && <span className="text-xs font-bold text-red-500 animate-bounce mt-1">TIME UP!</span>}
          </div>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {PRESETS.map((p) => (
            <button key={p.label} onClick={() => reset(p.seconds)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${total === p.seconds ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-primary/40 hover:text-foreground"}`}>
              {p.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-center">
          <Button size="sm" variant="outline" className="h-9 w-9 p-0" onClick={() => setSoundOn((s) => !s)}>
            {soundOn ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4 text-muted-foreground" />}
          </Button>
          <Button size="sm" className={`h-9 px-5 font-semibold ${running ? "bg-amber-500 hover:bg-amber-600" : ""}`}
            onClick={() => { setFinished(false); setRunning((r) => !r); }}>
            {running ? <><Pause className="w-4 h-4 mr-1.5" />Pause</> : <><Play className="w-4 h-4 mr-1.5" />Start</>}
          </Button>
          <Button size="sm" variant="outline" className="h-9 px-3 font-semibold" onClick={addLap} disabled={!running}>Lap</Button>
          <Button size="sm" variant="outline" className="h-9 w-9 p-0" onClick={() => reset(total)}><RotateCcw className="w-4 h-4" /></Button>
        </div>
        {laps.length > 0 && (
          <div className="w-full rounded-xl border border-border bg-muted/30 px-4 py-3 space-y-1.5 max-h-36 overflow-y-auto">
            {laps.map((l, i) => (
              <div key={i} className="flex justify-between text-xs font-mono">
                <span className="text-muted-foreground">{l.label}</span>
                <span className="text-foreground font-bold">{l.time} remaining</span>
              </div>
            ))}
          </div>
        )}
        <p className="text-[11px] text-muted-foreground text-center">Bell rings at 5 min remaining & on time up</p>
      </div>
    </div>
  );
}

/* 2. Big-O Cheat Sheet (FREE) */
const BIG_O_DATA = [
  { ds: "Array (access)", best: "O(1)", avg: "O(1)", worst: "O(1)", space: "O(n)" },
  { ds: "Array (search)", best: "O(1)", avg: "O(n)", worst: "O(n)", space: "O(n)" },
  { ds: "Array (insert/del)", best: "O(1)", avg: "O(n)", worst: "O(n)", space: "O(n)" },
  { ds: "Hash Map", best: "O(1)", avg: "O(1)", worst: "O(n)", space: "O(n)" },
  { ds: "Binary Search", best: "O(1)", avg: "O(log n)", worst: "O(log n)", space: "O(1)" },
  { ds: "Linked List (search)", best: "O(1)", avg: "O(n)", worst: "O(n)", space: "O(n)" },
  { ds: "Linked List (insert)", best: "O(1)", avg: "O(1)", worst: "O(1)", space: "O(n)" },
  { ds: "BST (search)", best: "O(log n)", avg: "O(log n)", worst: "O(n)", space: "O(n)" },
  { ds: "Stack / Queue", best: "O(1)", avg: "O(1)", worst: "O(1)", space: "O(n)" },
  { ds: "Heap (insert/del)", best: "O(log n)", avg: "O(log n)", worst: "O(log n)", space: "O(n)" },
  { ds: "Bubble Sort", best: "O(n)", avg: "O(n²)", worst: "O(n²)", space: "O(1)" },
  { ds: "Merge Sort", best: "O(n log n)", avg: "O(n log n)", worst: "O(n log n)", space: "O(n)" },
  { ds: "Quick Sort", best: "O(n log n)", avg: "O(n log n)", worst: "O(n²)", space: "O(log n)" },
  { ds: "Dijkstra (heap)", best: "O(E log V)", avg: "O(E log V)", worst: "O(E log V)", space: "O(V)" },
  { ds: "BFS / DFS", best: "O(V+E)", avg: "O(V+E)", worst: "O(V+E)", space: "O(V)" },
];
const complexityColor: Record<string, string> = {
  "O(1)": "text-emerald-500", "O(log n)": "text-sky-500", "O(n)": "text-blue-500",
  "O(n log n)": "text-amber-500", "O(n²)": "text-orange-500",
};

function BigOCheatSheet() {
  const [filter, setFilter] = useState("");
  const filtered = BIG_O_DATA.filter((r) => r.ds.toLowerCase().includes(filter.toLowerCase()));
  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
      <SectionHeader icon={<BarChart3 className="w-5 h-5" />} title="Big-O Cheat Sheet" subtitle="Time & space complexity reference — free for all users" />
      <input className="w-full mb-4 px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
        placeholder="Filter data structure..." value={filter} onChange={(e) => setFilter(e.target.value)} />
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-muted/50 border-b border-border">
              <th className="px-3 py-2.5 text-left font-semibold text-muted-foreground">Operation</th>
              <th className="px-3 py-2.5 text-center font-semibold text-emerald-500">Best</th>
              <th className="px-3 py-2.5 text-center font-semibold text-amber-500">Avg</th>
              <th className="px-3 py-2.5 text-center font-semibold text-red-500">Worst</th>
              <th className="px-3 py-2.5 text-center font-semibold text-sky-500">Space</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-accent/20 transition-colors">
                <td className="px-3 py-2 font-medium text-foreground">{row.ds}</td>
                {[row.best, row.avg, row.worst, row.space].map((val, j) => (
                  <td key={j} className={`px-3 py-2 text-center font-mono font-bold ${complexityColor[val] || "text-foreground"}`}>{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* 3. Pre-Interview Checklist (FREE) */
const DEFAULT_CHECKLIST = [
  { id: "water", label: "Have water / snacks ready" },
  { id: "quiet", label: "Find a quiet space, no interruptions" },
  { id: "camera", label: "Camera & microphone tested" },
  { id: "resume", label: "Printed/opened your résumé" },
  { id: "company", label: "Researched the company (products, team, values)" },
  { id: "jd", label: "Re-read the job description" },
  { id: "stories", label: "Prepared 3–5 STAR stories" },
  { id: "questions", label: "Prepared 3–5 questions to ask the interviewer" },
  { id: "ide", label: "IDE / coding environment ready" },
  { id: "patterns", label: "Reviewed key DSA patterns (sliding window, BFS, DP)" },
  { id: "hr", label: "Ready for \u201cTell me about yourself\u201d opener" },
  { id: "negotiate", label: "Know your target salary & BATNA" },
];

function PreInterviewChecklist() {
  const LS = "interview_checklist";
  const [checked, setChecked] = useState<Record<string, boolean>>(() => {
    try { return JSON.parse(localStorage.getItem(LS) || "{}"); } catch { return {}; }
  });
  const toggle = (id: string) => {
    setChecked((c) => { const next = { ...c, [id]: !c[id] }; localStorage.setItem(LS, JSON.stringify(next)); return next; });
  };
  const reset = () => { setChecked({}); localStorage.removeItem(LS); };
  const done = DEFAULT_CHECKLIST.filter((i) => checked[i.id]).length;
  const pct = Math.round((done / DEFAULT_CHECKLIST.length) * 100);
  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
      <SectionHeader icon={<CheckSquare className="w-5 h-5" />} title="Pre-Interview Checklist" subtitle="Run through this before every interview — free for all users" />
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-sm font-semibold text-foreground">{done}/{DEFAULT_CHECKLIST.length} ready</span>
          <span className={`text-sm font-bold ${pct === 100 ? "text-emerald-500" : "text-muted-foreground"}`}>{pct}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {DEFAULT_CHECKLIST.map((item) => (
          <button key={item.id} onClick={() => toggle(item.id)}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-all ${checked[item.id] ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400" : "hover:bg-accent/30 text-foreground"}`}>
            {checked[item.id] ? <CheckSquare className="w-4 h-4 shrink-0 text-emerald-500" /> : <Square className="w-4 h-4 shrink-0 text-muted-foreground" />}
            <span className={`text-sm font-medium ${checked[item.id] ? "line-through opacity-70" : ""}`}>{item.label}</span>
          </button>
        ))}
      </div>
      <button onClick={reset} className="mt-3 text-xs text-muted-foreground hover:text-destructive transition-colors">Reset all</button>
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   ── PRO TIER FEATURES ───────────────────────────────
   ══════════════════════════════════════════════════════ */

/* 4. Random Problem Picker (PRO) */
const DIFFICULTIES = ["Easy", "Medium", "Hard"] as const;

function RandomProblemPicker() {
  const [topic, setTopic] = useState<string>("All");
  const [difficulty, setDifficulty] = useState<string>("All");
  const [picked, setPicked] = useState<typeof CODING_PROBLEMS[0] | null>(null);

  const pick = () => {
    let pool = [...CODING_PROBLEMS];
    if (topic !== "All") pool = pool.filter((p) => p.topic === topic);
    if (difficulty !== "All") pool = pool.filter((p) => p.difficulty === difficulty);
    if (pool.length === 0) { toast.error("No problems match those filters!"); return; }
    setPicked(pool[Math.floor(Math.random() * pool.length)]);
  };
  const dc: Record<string, string> = {
    Easy: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    Medium: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    Hard: "text-red-500 bg-red-500/10 border-red-500/20",
  };
  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
      <SectionHeader icon={<Shuffle className="w-5 h-5" />} title="Random Problem Picker" subtitle="Spin for a surprise coding challenge from 1000+ problems" />
      <div className="flex flex-wrap gap-3 mb-5">
        <select value={topic} onChange={(e) => setTopic(e.target.value)}
          className="flex-1 min-w-[140px] rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option value="All">All Topics</option>
          {CODING_TOPICS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}
          className="flex-1 min-w-[120px] rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option value="All">All Difficulties</option>
          {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <Button onClick={pick} className="gap-2 font-semibold"><Shuffle className="w-4 h-4" /> Pick!</Button>
      </div>
      <AnimatePresence mode="wait">
        {picked && (
          <motion.div key={picked.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            className="rounded-xl border border-border bg-background p-4 space-y-3">
            <div className="flex items-start justify-between gap-2 flex-wrap">
              <div><span className="text-xs font-mono text-muted-foreground mr-2">#{picked.id}</span><span className="font-bold text-foreground">{picked.title}</span></div>
              <div className="flex items-center gap-2">
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg border ${dc[picked.difficulty]}`}>{picked.difficulty}</span>
                <span className="text-[11px] px-2 py-0.5 rounded-lg bg-muted border border-border text-muted-foreground">{picked.topic}</span>
              </div>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">{picked.description.replace(/\*\*/g, "")}</p>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground font-mono">
              <span>⏱ {picked.timeComplexity}</span><span>💾 {picked.spaceComplexity}</span>
              {picked.companiesAsked.slice(0, 3).map((c) => <span key={c} className="px-1.5 py-0.5 rounded bg-primary/10 text-primary font-semibold">{c}</span>)}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* 5. Salary Scripts (PRO) */
const SCRIPTS = [
  { title: "Counter-Offer Opener", tag: "Salary", color: "text-violet-500 bg-violet-500/10 border-violet-500/20", text: "Thank you so much for the offer! I'm very excited about this role and the team. Based on my research and the value I'd bring, I was hoping we could discuss a base closer to [TARGET]. Is there any flexibility there?" },
  { title: "Deflect Salary First", tag: "Screen", color: "text-sky-500 bg-sky-500/10 border-sky-500/20", text: "I'd love to learn more about the full scope of the role and responsibilities before anchoring on a number. Could you share the budgeted range for this position?" },
  { title: "Benefits Trade-Off", tag: "Perks", color: "text-amber-500 bg-amber-500/10 border-amber-500/20", text: "If the base is fixed at [OFFER], would you be open to [additional equity / extra PTO / signing bonus / remote flexibility]? That would make the total package work for me." },
  { title: "Competing Offer", tag: "Leverage", color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20", text: "I have another offer at [AMOUNT], but this role is my top choice because of [REASON]. Is there a way to close that gap so I can say yes today?" },
  { title: "Graceful Decline", tag: "Exit", color: "text-rose-500 bg-rose-500/10 border-rose-500/20", text: "Thank you for the offer — I genuinely enjoyed meeting the team. After careful consideration, I've decided to pursue a role that's a closer fit for my goals at this stage. I hope our paths cross again." },
];

function SalaryNegotiationToolkit() {
  const [copied, setCopied] = useState<string | null>(null);

  const copy = (id: string, text: string) => {
    navigator.clipboard.writeText(text).then(() => { setCopied(id); setTimeout(() => setCopied(null), 1800); });
  };
  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
      <SectionHeader icon={<DollarSign className="w-5 h-5" />} title="Salary Negotiation Scripts" subtitle="Copy word-for-word scripts for every negotiation scenario" />
      <div className="space-y-3">
        {SCRIPTS.map((s) => (
          <div key={s.title} className="group rounded-xl border border-border bg-background/60 p-4 hover:border-primary/30 transition-all">
            <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
              <span className="font-semibold text-sm text-foreground">{s.title}</span>
              <div className="flex items-center gap-2">
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg border ${s.color}`}>{s.tag}</span>
                <button onClick={() => copy(s.title, s.text)} className="flex items-center gap-1 text-[11px] font-semibold text-muted-foreground hover:text-primary transition-colors">
                  {copied === s.title ? <CheckCheck className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied === s.title ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed italic">"{s.text}"</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* 6. JD Analyzer (PRO) */
const TECH_KEYWORDS = ["python","javascript","typescript","java","golang","rust","c++","react","next.js","node","sql","nosql","postgres","mongodb","redis","kafka","aws","gcp","azure","docker","kubernetes","ci/cd","graphql","rest","api","microservices","system design","distributed","ml","machine learning","data structures","algorithms","leetcode","agile","scrum"];
const BEHAVIORAL_MAP: Record<string, string[]> = {
  "leadership": ["Tell me about a time you led a team", "Describe a project where you drove key decisions"],
  "conflict": ["Tell me about a disagreement with a colleague", "How do you handle conflicting priorities?"],
  "fast-paced": ["Give an example of working under tight deadlines", "How do you manage stress?"],
  "cross-functional": ["Describe working with a non-technical stakeholder", "How do you align different teams?"],
  "ownership": ["Tell me about a project you owned end-to-end", "How do you handle ambiguity?"],
  "scale": ["Tell me about building something at scale", "What tradeoffs did you make for scalability?"],
};

function JDAnalyzer() {
  const [jd, setJd] = useState("");
  const [result, setResult] = useState<{ skills: string[]; behavioralQs: string[]; seniority: string } | null>(null);

  const analyze = () => {
    if (!jd.trim()) { toast.error("Paste a job description first"); return; }
    const lower = jd.toLowerCase();
    const skills = TECH_KEYWORDS.filter((kw) => lower.includes(kw));
    const behavioralQs: string[] = [];
    Object.entries(BEHAVIORAL_MAP).forEach(([kw, qs]) => { if (lower.includes(kw)) behavioralQs.push(...qs); });
    const seniority = ["senior","lead","principal","staff","architect","manager"].find((w) => lower.includes(w))
      ? "Senior / Lead" : lower.includes("junior") || lower.includes("entry") ? "Junior / Entry" : "Mid-Level";
    setResult({ skills: [...new Set(skills)], behavioralQs: [...new Set(behavioralQs)], seniority });
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
      <SectionHeader icon={<FileText className="w-5 h-5" />} title="JD Skill Analyzer" subtitle="Paste any job description to extract skills and predict questions" />
      <textarea value={jd} onChange={(e) => setJd(e.target.value)} rows={7}
        placeholder="Paste the full job description here..."
        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/30" />
      <div className="flex gap-2">
        <Button onClick={analyze} className="gap-2 font-semibold"><Zap className="w-4 h-4" /> Analyze JD</Button>
        {result && <Button variant="outline" onClick={() => { setResult(null); setJd(""); }}>Clear</Button>}
      </div>
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Seniority:</span>
              <span className="px-2 py-0.5 rounded-lg bg-primary/10 text-primary border border-primary/20 text-xs font-bold">{result.seniority}</span>
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Detected Tech Skills ({result.skills.length})</p>
              <div className="flex flex-wrap gap-2">
                {result.skills.length ? result.skills.map((s) => <span key={s} className="px-2.5 py-1 rounded-lg bg-primary/10 border border-primary/20 text-primary text-xs font-bold">{s}</span>)
                  : <span className="text-sm text-muted-foreground">No specific tech keywords found</span>}
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Predicted Behavioural Questions ({result.behavioralQs.length})</p>
              <ul className="space-y-2">
                {result.behavioralQs.length ? result.behavioralQs.map((q, i) => <li key={i} className="flex gap-2 text-sm text-foreground"><span className="font-bold text-primary shrink-0">{i + 1}.</span> {q}</li>)
                  : <li className="text-sm text-muted-foreground">No specific behavioral signals found</li>}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* 7. Answer Scorecard (PRO) */
const RUBRIC = [
  { id: "situation", label: "Situation", desc: "Clearly set the context & background" },
  { id: "task", label: "Task", desc: "Clearly stated your specific responsibility" },
  { id: "action", label: "Action", desc: "Explained what YOU did step-by-step" },
  { id: "result", label: "Result", desc: "Quantified impact & outcome" },
  { id: "clarity", label: "Clarity", desc: "Answer was structured and easy to follow" },
  { id: "concise", label: "Conciseness", desc: "Stayed under 2 minutes / avoided rambling" },
];

function AnswerScorecard() {
  const [scores, setScores] = useState<Record<string, number>>({});
  const [notes, setNotes] = useState("");

  const total = Object.values(scores).reduce((a, b) => a + b, 0);
  const max = RUBRIC.length * 5;
  const pct = Math.round((total / max) * 100);
  const grade = pct >= 85 ? { label: "Excellent", color: "text-emerald-500" } : pct >= 65 ? { label: "Good", color: "text-amber-500" } : { label: "Needs Work", color: "text-red-500" };

  const save = () => {
    const entry = { date: new Date().toLocaleString(), scores, notes, pct };
    const history = JSON.parse(localStorage.getItem("scorecard_history") || "[]");
    history.unshift(entry);
    localStorage.setItem("scorecard_history", JSON.stringify(history.slice(0, 20)));
    toast.success("Scorecard saved!");
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
      <SectionHeader icon={<Award className="w-5 h-5" />} title="STAR Answer Scorecard" subtitle="Rate your answer on each dimension — 1 (poor) to 5 (excellent)" />
      {RUBRIC.map((r) => (
        <div key={r.id}>
          <div className="flex items-center justify-between mb-1.5">
            <div><span className="text-sm font-semibold text-foreground">{r.label}</span><span className="text-xs text-muted-foreground ml-2">{r.desc}</span></div>
            <span className="text-sm font-bold text-primary">{scores[r.id] ?? "—"}/5</span>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((v) => (
              <button key={v} onClick={() => setScores((s) => ({ ...s, [r.id]: v }))}
                className={`flex-1 py-1.5 rounded-lg text-xs font-bold border transition-all ${scores[r.id] === v ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-primary/40"}`}>
                {v}
              </button>
            ))}
          </div>
        </div>
      ))}
      {Object.keys(scores).length > 0 && (
        <div className="rounded-xl border border-border bg-muted/30 px-4 py-3 flex items-center justify-between">
          <span className="text-sm font-semibold text-foreground">Overall Score</span>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-black font-mono text-foreground">{pct}%</span>
            <span className={`text-sm font-bold ${grade.color}`}>{grade.label}</span>
          </div>
        </div>
      )}
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3}
        placeholder="Notes / what to improve..."
        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/30" />
      <div className="flex gap-2">
        <Button onClick={save} className="gap-2" disabled={Object.keys(scores).length < RUBRIC.length}><CheckCheck className="w-4 h-4" /> Save Scorecard</Button>
        <Button variant="outline" onClick={() => { setScores({}); setNotes(""); }}>Reset</Button>
      </div>
    </div>
  );
}

/* 8. Readiness Tracker (PRO) */
const MOODS = [
  { id: "great", label: "Ready!", icon: <Smile className="w-5 h-5" />, color: "text-emerald-500 border-emerald-500/30 bg-emerald-500/10" },
  { id: "ok", label: "Okay", icon: <Meh className="w-5 h-5" />, color: "text-amber-500 border-amber-500/30 bg-amber-500/10" },
  { id: "low", label: "Struggling", icon: <Frown className="w-5 h-5" />, color: "text-red-500 border-red-500/30 bg-red-500/10" },
];
interface ReadinessEntry { date: string; mood: string; confidence: number; note: string; }

function ReadinessTracker() {
  const LS = "readiness_history";
  const [history, setHistory] = useState<ReadinessEntry[]>(() => {
    try { return JSON.parse(localStorage.getItem(LS) || "[]"); } catch { return []; }
  });
  const [mood, setMood] = useState("");
  const [confidence, setConfidence] = useState(5);
  const [note, setNote] = useState("");

  const checkin = () => {
    if (!mood) { toast.error("Select a mood first"); return; }
    const entry: ReadinessEntry = { date: new Date().toLocaleString(), mood, confidence, note };
    const next = [entry, ...history].slice(0, 30);
    setHistory(next); localStorage.setItem(LS, JSON.stringify(next));
    setMood(""); setNote(""); setConfidence(5);
    toast.success("Check-in saved!");
  };
  const avgConf = history.length ? Math.round(history.slice(0, 7).reduce((s, e) => s + e.confidence, 0) / Math.min(7, history.length)) : 0;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
      <SectionHeader icon={<TrendingUp className="w-5 h-5" />} title="Daily Readiness Tracker" subtitle="Check in daily to track your confidence leading up to your interview" />
      {history.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-border bg-muted/30 p-3 text-center">
            <p className="text-2xl font-black text-foreground">{avgConf}/10</p>
            <p className="text-xs text-muted-foreground mt-0.5">7-day avg confidence</p>
          </div>
          <div className="rounded-xl border border-border bg-muted/30 p-3 text-center">
            <p className="text-2xl font-black text-foreground">{history.length}</p>
            <p className="text-xs text-muted-foreground mt-0.5">Total check-ins</p>
          </div>
        </div>
      )}
      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">How are you feeling today?</p>
        <div className="flex gap-3">
          {MOODS.map((m) => (
            <button key={m.id} onClick={() => setMood(m.id)}
              className={`flex-1 flex flex-col items-center gap-1.5 rounded-xl border p-3 text-xs font-semibold transition-all ${mood === m.id ? m.color : "border-border text-muted-foreground hover:border-primary/30"}`}>
              {m.icon}{m.label}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Confidence Level</p>
          <span className="text-sm font-bold text-primary">{confidence}/10</span>
        </div>
        <input type="range" min={1} max={10} value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} className="w-full accent-primary" />
      </div>
      <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2}
        placeholder="Quick note: what did you study? Any concerns?"
        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/30" />
      <Button onClick={checkin} className="gap-2 w-full font-semibold"><Plus className="w-4 h-4" /> Save Check-In</Button>
      {history.length > 0 && (
        <div className="space-y-2 max-h-56 overflow-y-auto">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Recent History</p>
          {history.slice(0, 10).map((e, i) => {
            const m = MOODS.find((x) => x.id === e.mood);
            return (
              <div key={i} className="flex items-start gap-3 rounded-lg border border-border px-3 py-2.5 bg-muted/20">
                <span className={`shrink-0 ${m?.color.split(" ")[0]}`}>{m?.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-foreground">{m?.label}</span>
                    <span className="text-xs font-mono text-muted-foreground">{e.confidence}/10</span>
                  </div>
                  {e.note && <p className="text-xs text-muted-foreground mt-0.5 truncate">{e.note}</p>}
                  <p className="text-[10px] text-muted-foreground/60 mt-0.5">{e.date}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   ── ENTERPRISE TIER FEATURES ────────────────────────
   ══════════════════════════════════════════════════════ */

/* 9. DSA Pattern Recognition (ENTERPRISE) */
const PATTERNS = [
  { name: "Sliding Window", when: "Contiguous subarray/substring with constraint", example: "Max sum subarray of size k", complexity: "O(n)", code: "l=0\nfor r in range(len(arr)):\n  window.add(arr[r])\n  while invalid(window):\n    window.remove(arr[l]); l+=1\n  ans = max(ans, len(window))" },
  { name: "Two Pointers", when: "Sorted array, pair sum, palindrome check", example: "3Sum, trapping rain water", complexity: "O(n)", code: "l, r = 0, len(arr)-1\nwhile l < r:\n  if condition: return (l, r)\n  elif too_small: l += 1\n  else: r -= 1" },
  { name: "BFS (level-order)", when: "Shortest path, level traversal, spreading", example: "Rotten oranges, 0-1 BFS", complexity: "O(V+E)", code: "from collections import deque\nq = deque([start])\nvisited = {start}\nwhile q:\n  node = q.popleft()\n  for nbr in graph[node]:\n    if nbr not in visited:\n      visited.add(nbr); q.append(nbr)" },
  { name: "DFS / Backtracking", when: "All permutations, combinations, subsets", example: "N-Queens, word search", complexity: "O(b^d)", code: "def backtrack(state):\n  if is_solution(state): results.append(state[:]); return\n  for choice in choices(state):\n    state.append(choice)\n    backtrack(state)\n    state.pop()" },
  { name: "Dynamic Programming", when: "Optimal substructure + overlapping subproblems", example: "Coin change, LCS, knapsack", complexity: "O(n²)", code: "dp = [0] * (n+1)\ndp[0] = base_case\nfor i in range(1, n+1):\n  dp[i] = max(dp[i-1], dp[i-2] + val[i])" },
  { name: "Monotonic Stack", when: "Next greater/smaller element problems", example: "Daily temperatures, histogram", complexity: "O(n)", code: "stack = []\nfor i, val in enumerate(arr):\n  while stack and arr[stack[-1]] < val:\n    idx = stack.pop()\n    ans[idx] = i - idx\n  stack.append(i)" },
  { name: "Binary Search on Answer", when: "Minimize/maximize over sorted answer space", example: "Koko bananas, ship packages", complexity: "O(n log n)", code: "lo, hi = min_possible, max_possible\nwhile lo < hi:\n  mid = (lo + hi) // 2\n  if feasible(mid): hi = mid\n  else: lo = mid + 1" },
  { name: "Union Find", when: "Connected components, cycle detection", example: "Number of islands, redundant connection", complexity: "O(α(n))", code: "parent = list(range(n))\ndef find(x): return x if parent[x]==x else find(parent[x])\ndef union(a,b): parent[find(a)] = find(b)" },
  { name: "Topological Sort", when: "Ordering with dependencies (DAG)", example: "Course schedule, alien dictionary", complexity: "O(V+E)", code: "from collections import deque\nindegree = [0]*n\nfor u, v in edges: indegree[v] += 1\nq = deque(i for i in range(n) if indegree[i]==0)\norder = []\nwhile q:\n  u=q.popleft(); order.append(u)\n  for v in graph[u]:\n    indegree[v]-=1\n    if indegree[v]==0: q.append(v)" },
];

function DSAPatternsReference() {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
      <SectionHeader icon={<Zap className="w-5 h-5" />} title="DSA Pattern Library" subtitle="Code templates & when-to-use guides for every major pattern" />
      <div className="space-y-2">
        {PATTERNS.map((p) => (
          <div key={p.name} className="rounded-xl border border-border overflow-hidden">
            <button onClick={() => setOpen(open === p.name ? null : p.name)}
              className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-accent/20 transition-colors">
              <div className="flex items-center gap-3">
                <Hash className="w-4 h-4 text-primary shrink-0" />
                <span className="text-sm font-semibold text-foreground">{p.name}</span>
                <span className="hidden sm:block text-xs font-mono text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded">{p.complexity}</span>
              </div>
              {open === p.name ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
            </button>
            {open === p.name && (
              <div className="px-4 pb-4 pt-2 bg-accent/10 border-t border-border space-y-3">
                <div className="flex gap-2 text-xs"><span className="font-semibold text-primary w-16 shrink-0">When:</span><span className="text-foreground">{p.when}</span></div>
                <div className="flex gap-2 text-xs"><span className="font-semibold text-primary w-16 shrink-0">Example:</span><span className="text-foreground italic">{p.example}</span></div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1.5">Template (Python)</p>
                  <pre className="rounded-lg bg-muted/60 border border-border px-3 py-2.5 text-xs font-mono text-foreground overflow-x-auto whitespace-pre">{p.code}</pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* 10. Study Session Planner (ENTERPRISE) */
interface StudyTask { id: string; text: string; done: boolean; category: "dsa" | "behavioral" | "system"; }

function StudyPlanner() {
  const LS = "study_planner";
  const [tasks, setTasks] = useState<StudyTask[]>(() => {
    try { return JSON.parse(localStorage.getItem(LS) || "[]"); } catch { return []; }
  });
  const [newText, setNewText] = useState("");
  const [category, setCategory] = useState<StudyTask["category"]>("dsa");

  const persist = (next: StudyTask[]) => { setTasks(next); localStorage.setItem(LS, JSON.stringify(next)); };
  const add = () => {
    if (!newText.trim()) { toast.error("Enter a task"); return; }
    persist([...tasks, { id: Math.random().toString(36).slice(2), text: newText.trim(), done: false, category }]);
    setNewText("");
  };
  const toggle = (id: string) => persist(tasks.map((t) => t.id === id ? { ...t, done: !t.done } : t));
  const remove = (id: string) => persist(tasks.filter((t) => t.id !== id));

  const catColor: Record<string, string> = {
    dsa: "text-primary bg-primary/10 border-primary/20",
    behavioral: "text-violet-500 bg-violet-500/10 border-violet-500/20",
    system: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  };
  const catLabel: Record<string, string> = { dsa: "DSA", behavioral: "Behavioral", system: "System Design" };
  const done = tasks.filter((t) => t.done).length;
  const pct = tasks.length ? Math.round((done / tasks.length) * 100) : 0;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
      <SectionHeader icon={<CalendarDays className="w-5 h-5" />} title="Study Session Planner" subtitle="Plan, categorise, and track your daily interview prep tasks" />
      {tasks.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-foreground">{done}/{tasks.length} completed</span>
            <span className={`text-xs font-bold ${pct === 100 ? "text-emerald-500" : "text-muted-foreground"}`}>{pct}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}
      <div className="flex gap-2">
        <input value={newText} onChange={(e) => setNewText(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") add(); }}
          placeholder="Add a study task... (Enter to add)"
          className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30" />
        <select value={category} onChange={(e) => setCategory(e.target.value as StudyTask["category"])}
          className="rounded-lg border border-border bg-background px-2 py-2 text-xs font-semibold text-foreground focus:outline-none">
          <option value="dsa">DSA</option>
          <option value="behavioral">Behavioral</option>
          <option value="system">System</option>
        </select>
        <Button size="sm" onClick={add} className="h-9 w-9 p-0"><Plus className="w-4 h-4" /></Button>
      </div>
      {tasks.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <BookOpen className="w-8 h-8 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">No tasks yet — add your first study goal above</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
          {(["dsa", "behavioral", "system"] as const).map((cat) => {
            const catTasks = tasks.filter((t) => t.category === cat);
            if (!catTasks.length) return null;
            return (
              <div key={cat}>
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1.5 mt-1">{catLabel[cat]}</p>
                {catTasks.map((t) => (
                  <div key={t.id} className="flex items-center gap-2 rounded-lg border border-border px-3 py-2.5 hover:bg-accent/20 transition-colors group mb-1.5">
                    <button onClick={() => toggle(t.id)} className="shrink-0">
                      {t.done ? <CheckSquare className="w-4 h-4 text-emerald-500" /> : <Square className="w-4 h-4 text-muted-foreground" />}
                    </button>
                    <span className={`flex-1 text-sm font-medium ${t.done ? "line-through text-muted-foreground" : "text-foreground"}`}>{t.text}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${catColor[cat]}`}>{catLabel[cat]}</span>
                    <button onClick={() => remove(t.id)} className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive shrink-0">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* 11. System Design Estimator (PRO) */
function SystemDesignEstimator() {
  const [dau, setDau] = useState<number>(5000000);
  const [readPerUser, setReadPerUser] = useState<number>(20);
  const [writePerUser, setWritePerUser] = useState<number>(5);
  const [readKb, setReadKb] = useState<number>(50);
  const [writeKb, setWriteKb] = useState<number>(5);

  const SECONDS_PER_DAY = 86400;
  const readsPerSec = Math.round((dau * readPerUser) / SECONDS_PER_DAY);
  const writesPerSec = Math.round((dau * writePerUser) / SECONDS_PER_DAY);
  const totalQps = readsPerSec + writesPerSec;
  const peakQps = Math.round(totalQps * 2);

  const readBwMbps = Math.round(((readsPerSec * readKb * 8) / 1024) * 10) / 10;
  const writeBwMbps = Math.round(((writesPerSec * writeKb * 8) / 1024) * 10) / 10;
  const totalBw = Math.round((readBwMbps + writeBwMbps) * 10) / 10;

  const storagePerDayGB = (dau * writePerUser * writeKb) / (1024 * 1024);
  const storage5YTB = Math.round((storagePerDayGB * 365 * 5) / 1024 * 10) / 10;
  
  const cache8020GB = Math.round(((dau * readPerUser * readKb * 0.2) / (1024 * 1024)) * 10) / 10;

  const fmt = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
      <SectionHeader icon={<Calculator className="w-5 h-5" />} title="System Design Estimator" subtitle="Interactive back-of-the-envelope capacity planning" />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4 rounded-xl border border-border bg-muted/20 p-4">
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2"><Target className="w-4 h-4 text-primary" /> Traffic Assumptions</h3>
          
          <div>
            <div className="flex justify-between mb-1"><span className="text-xs font-semibold text-muted-foreground">Daily Active Users (DAU)</span><span className="text-xs font-bold text-primary">{fmt.format(dau)}</span></div>
            <input type="range" min="10000" max="100000000" step="10000" value={dau} onChange={(e) => setDau(Number(e.target.value))} className="w-full accent-primary" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between mb-1"><span className="text-xs font-semibold text-muted-foreground">Reads / User</span><span className="text-xs font-bold">{readPerUser}</span></div>
              <input type="range" min="1" max="200" value={readPerUser} onChange={(e) => setReadPerUser(Number(e.target.value))} className="w-full accent-sky-500" />
            </div>
            <div>
              <div className="flex justify-between mb-1"><span className="text-xs font-semibold text-muted-foreground">Writes / User</span><span className="text-xs font-bold">{writePerUser}</span></div>
              <input type="range" min="1" max="100" value={writePerUser} onChange={(e) => setWritePerUser(Number(e.target.value))} className="w-full accent-amber-500" />
            </div>
            <div>
              <div className="flex justify-between mb-1"><span className="text-xs font-semibold text-muted-foreground">Read Payload</span><span className="text-xs font-bold">{readKb} KB</span></div>
              <input type="range" min="1" max="1024" value={readKb} onChange={(e) => setReadKb(Number(e.target.value))} className="w-full accent-sky-500" />
            </div>
            <div>
              <div className="flex justify-between mb-1"><span className="text-xs font-semibold text-muted-foreground">Write Payload</span><span className="text-xs font-bold">{writeKb} KB</span></div>
              <input type="range" min="1" max="1024" value={writeKb} onChange={(e) => setWriteKb(Number(e.target.value))} className="w-full accent-amber-500" />
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-border bg-background p-3">
              <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mb-1"><Activity className="w-3.5 h-3.5" /> Average QPS</div>
              <div className="text-xl font-black font-mono">{fmt.format(totalQps)} <span className="text-xs text-muted-foreground font-sans font-medium">req/s</span></div>
              <div className="w-full flex h-1.5 rounded-full overflow-hidden mt-2 bg-muted">
                <div className="bg-sky-500" style={{ width: `${(readsPerSec/Math.max(1, totalQps))*100}%` }} />
                <div className="bg-amber-500" style={{ width: `${(writesPerSec/Math.max(1, totalQps))*100}%` }} />
              </div>
              <div className="flex justify-between text-[10px] mt-1 text-muted-foreground"><span className="text-sky-500 font-semibold">{Math.round((readsPerSec/Math.max(1, totalQps))*100)}% Read</span><span className="text-amber-500 font-semibold">{Math.round((writesPerSec/Math.max(1, totalQps))*100)}% Write</span></div>
            </div>
            <div className="rounded-xl border border-border bg-background p-3 border-l-4 border-l-rose-500">
              <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mb-1"><Zap className="w-3.5 h-3.5 text-rose-500" /> Peak QPS (Est.)</div>
              <div className="text-xl font-black font-mono">{fmt.format(peakQps)} <span className="text-xs text-muted-foreground font-sans font-medium">req/s</span></div>
            </div>
            
            <div className="rounded-xl border border-border bg-background p-3">
              <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mb-1"><Wifi className="w-3.5 h-3.5" /> Bandwidth</div>
              <div className="text-xl font-black font-mono">{fmt.format(totalBw)} <span className="text-xs text-muted-foreground font-sans font-medium">Mbps</span></div>
            </div>
            <div className="rounded-xl border border-border bg-background p-3">
              <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mb-1"><Server className="w-3.5 h-3.5 text-emerald-500" /> Cache (20% rule)</div>
              <div className="text-xl font-black font-mono">{fmt.format(cache8020GB)} <span className="text-xs text-muted-foreground font-sans font-medium">GB</span></div>
            </div>
          </div>
          
          <div className="rounded-xl border border-border bg-background p-4 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5 mb-1"><HardDrive className="w-3.5 h-3.5" /> Total Storage (5 Years)</div>
              <div className="text-2xl font-black font-mono text-primary">{fmt.format(storage5YTB)} <span className="text-sm text-muted-foreground font-sans font-medium">TB</span></div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-muted-foreground mb-1">Daily Growth</div>
              <div className="text-sm font-bold font-mono text-amber-500">+{storagePerDayGB.toFixed(1)} GB/day</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* 12. Network Latency Visualizer (ENTERPRISE) */
const LATENCIES = [
  { name: "L1 Cache Reference", ns: 0.5, group: "CPU" },
  { name: "Branch Mispredict", ns: 5, group: "CPU" },
  { name: "L2 Cache Reference", ns: 7, group: "CPU" },
  { name: "Mutex Lock/Unlock", ns: 25, group: "CPU" },
  { name: "Main Memory Reference", ns: 100, group: "RAM" },
  { name: "Compress 1K Bytes with Zippy", ns: 3000, group: "RAM" },
  { name: "Send 2K Bytes over 1 Gbps Net", ns: 20000, group: "Network" },
  { name: "Read 1 MB Sequentially from RAM", ns: 250000, group: "RAM" },
  { name: "Round Trip Datacenter", ns: 500000, group: "Network" },
  { name: "Disk Seek", ns: 10000000, group: "Disk" },
  { name: "Read 1 MB Sequentially from Network", ns: 10000000, group: "Network" },
  { name: "Read 1 MB Sequentially from Disk", ns: 20000000, group: "Disk" },
  { name: "Packet CA to Netherlands", ns: 150000000, group: "Network" },
];

function LatencyVisualizer() {
  const [scale, setScale] = useState<"ns" | "human">("ns");

  const formatNs = (ns: number) => {
    if (ns < 1000) return `${ns} ns`;
    if (ns < 1000000) return `${ns / 1000} \u00B5s`;
    return `${ns / 1000000} ms`;
  };

  const formatHuman = (ns: number) => {
    const sec = ns;
    if (sec < 60) return `${sec} secs`;
    if (sec < 3600) return `${Math.round(sec / 60)} mins`;
    if (sec < 86400) return `${Math.round((sec / 3600)*10)/10} hrs`;
    if (sec < 31536000) return `${Math.round((sec / 86400)*10)/10} days`;
    return `${Math.round((sec / 31536000)*10)/10} years`;
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
      <SectionHeader icon={<Globe className="w-5 h-5" />} title="Latency Numbers Every Programmer Should Know" subtitle="Visualize hardware timescales. Switch to human scale (1ns = 1s) for intuition." />
      
      <div className="flex items-center gap-2 mb-4 bg-muted/30 p-1.5 rounded-lg w-fit border border-border">
        <button onClick={() => setScale("ns")} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${scale === "ns" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}>Exact Time</button>
        <button onClick={() => setScale("human")} className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${scale === "human" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}>Human Scale (1ns = 1s)</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {LATENCIES.map((lat, i) => (
          <div key={i} className="flex items-center justify-between rounded-xl border border-border bg-background p-3 hover:border-primary/30 transition-colors group">
            <div>
              <div className="flex items-center gap-2">
                 <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${lat.group === 'CPU' ? 'text-sky-500 bg-sky-500/10 border-sky-500/20' : lat.group === 'RAM' ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' : lat.group === 'Disk' ? 'text-amber-500 bg-amber-500/10 border-amber-500/20' : 'text-violet-500 bg-violet-500/10 border-violet-500/20'}`}>{lat.group}</span>
                 <span className="text-sm font-semibold text-foreground">{lat.name}</span>
              </div>
            </div>
            <div className="text-right shrink-0">
              <span className="text-base font-black font-mono text-primary group-hover:scale-105 transition-transform inline-block">
                {scale === "ns" ? formatNs(lat.ns) : formatHuman(lat.ns)}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="rounded-xl border border-border bg-primary/5 p-4 text-xs text-muted-foreground">
        <strong>Takeaway:</strong> Modern CPUs are incredibly fast, but network and disk operations are orders of magnitude slower. Minimizing network round trips and avoiding disk seeks are critical for highly scalable systems.
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   ── TAB DEFINITIONS ─────────────────────────────────
   ══════════════════════════════════════════════════════ */
const TABS = [
  { id: "timer",     label: "Timer",          icon: <Timer className="w-4 h-4" /> },
  { id: "bigo",      label: "Big-O",          icon: <BarChart3 className="w-4 h-4" /> },
  { id: "checklist", label: "Checklist",       icon: <CheckSquare className="w-4 h-4" /> },
  { id: "mindmap",   label: "Mind Map",       icon: <Map className="w-4 h-4" /> },
  { id: "whiteboard",label: "Whiteboard",      icon: <PenTool className="w-4 h-4" /> },
  { id: "picker",    label: "Question Picker", icon: <Shuffle className="w-4 h-4" /> },
  { id: "salary",    label: "Salary Scripts",  icon: <DollarSign className="w-4 h-4" /> },
  { id: "jd",        label: "JD Analyzer",     icon: <FileText className="w-4 h-4" /> },
  { id: "scorecard", label: "Scorecard",       icon: <Award className="w-4 h-4" /> },
  { id: "readiness", label: "Readiness",       icon: <TrendingUp className="w-4 h-4" /> },
  { id: "estimator", label: "Estimator",       icon: <Calculator className="w-4 h-4" /> },
  { id: "patterns",  label: "DSA Patterns",    icon: <Zap className="w-4 h-4" /> },
  { id: "latency",   label: "Latency Map",     icon: <Globe className="w-4 h-4" /> },
  { id: "planner",   label: "Study Planner",   icon: <CalendarDays className="w-4 h-4" /> },
] as const;

type ToolkitTab = (typeof TABS)[number]["id"];

interface InterviewToolkitPageProps {
  mindMaps: SavedMindMap[];
  activeMindMapId?: string;
  onMindMapsChange: (mindMaps: SavedMindMap[], activeMindMapId?: string) => void;
}

export default function InterviewToolkitPage({
  mindMaps,
  activeMindMapId,
  onMindMapsChange,
}: InterviewToolkitPageProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<ToolkitTab>("timer");

  return (
    <div className="flex flex-col gap-0 h-full">
      {/* Header */}
      <div className="px-6 pt-6 pb-4 border-b border-border bg-background/60 backdrop-blur-sm shrink-0">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground"><Target className="w-5 h-5" /></div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Interview Toolkit</h1>
            <div className="flex items-center gap-3 mt-0.5 flex-wrap">
              <p className="text-sm text-muted-foreground">All-in-one tools to ace every stage of the interview process — free for everyone</p>
            </div>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none">
          {TABS.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                activeTab === tab.id ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              }`}>
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-6">
        <AnimatePresence mode="wait">
          <motion.div key={activeTab}
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}>
            {activeTab === "timer"     && <InterviewTimer />}
            {activeTab === "bigo"      && <BigOCheatSheet />}
            {activeTab === "checklist" && <PreInterviewChecklist />}
            {activeTab === "mindmap"   && (
              <MindMapTool
                mindMaps={mindMaps}
                activeMindMapId={activeMindMapId}
                onChange={onMindMapsChange}
              />
            )}
            {activeTab === "whiteboard" && (
              <div className="bg-card border border-border rounded-2xl h-[600px] shadow-sm overflow-hidden flex flex-col items-center">
                <div className="w-full text-left p-4 border-b border-border">
                  <SectionHeader icon={<PenTool className="w-5 h-5" />} title="Whiteboard" subtitle="Sketch out architectures, trees, and logic flows" />
                </div>
                <div className="flex-1 w-full relative">
                  <ScratchPad defaultTab="scratch" />
                </div>
              </div>
            )}
            {activeTab === "picker"    && <RandomProblemPicker />}
            {activeTab === "salary"    && <SalaryNegotiationToolkit />}
            {activeTab === "jd"        && <JDAnalyzer />}
            {activeTab === "scorecard" && <AnswerScorecard />}
            {activeTab === "readiness" && <ReadinessTracker />}
            {activeTab === "estimator" && <SystemDesignEstimator />}
            {activeTab === "patterns"  && <DSAPatternsReference />}
            {activeTab === "latency"   && <LatencyVisualizer />}
            {activeTab === "planner"   && <StudyPlanner />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
