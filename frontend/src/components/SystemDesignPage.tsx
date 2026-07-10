import { useState, useMemo, useCallback, useEffect } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Server,
  ChevronDown,
  ChevronRight,
  Check,
  Clock,
  Target,
  Layers,
  AlertTriangle,
  ArrowUpRight,
  Lightbulb,
  BarChart3,
  Boxes,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/AuthProvider";
import {
  SYSTEM_DESIGN_PROBLEMS,
  type SystemDesignProblem,
} from "./systemDesignData";

/* ──────────────────────────────────────────── */
/*  Progress persistence                        */
/* ──────────────────────────────────────────── */
const STORAGE_KEY = "sd_playbook_progress";

function loadStudied(): number[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as number[];
  } catch {
    // ignore corrupt/missing localStorage data
  }
  return [];
}
function saveStudied(ids: number[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
}

/* ──────────────────────────────────────────── */
/*  Difficulty badge                            */
/* ──────────────────────────────────────────── */
const diffColors: Record<string, string> = {
  Medium: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  Hard: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  Expert: "bg-purple-500/10 text-purple-600 border-purple-500/20",
};

/* ──────────────────────────────────────────── */
/*  Collapsible section                         */
/* ──────────────────────────────────────────── */
function Section({
  title,
  icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2.5 px-4 py-3 text-sm font-semibold text-foreground hover:bg-accent/20 transition-colors cursor-pointer"
      >
        {icon}
        <span className="flex-1 text-left">{title}</span>
        <ChevronDown
          className={`w-4 h-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Problem detail view                         */
/* ──────────────────────────────────────────── */
function ProblemDetail({
  problem,
  studied,
  onToggleStudied,
  onBack,
}: {
  problem: SystemDesignProblem;
  studied: boolean;
  onToggleStudied: () => void;
  onBack: () => void;
}) {
  const dc = diffColors[problem.difficulty] || diffColors.Medium;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
    >
      {/* Back + title */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4 cursor-pointer"
      >
        ← Back to all problems
      </button>

      <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
        <div>
          <h2 className="text-2xl font-bold text-foreground mb-2">
            {problem.title}
          </h2>
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold border ${dc}`}
            >
              {problem.difficulty}
            </span>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3.5 h-3.5" /> {problem.estimatedTime}
            </span>
            {problem.company.map((c) => (
              <span
                key={c}
                className="px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-accent/50 text-muted-foreground border border-border"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
        <Button
          variant={studied ? "outline" : "default"}
          size="sm"
          onClick={onToggleStudied}
          className="gap-1.5"
        >
          {studied ? (
            <>
              <Check className="w-3.5 h-3.5" /> Studied
            </>
          ) : (
            <>
              <Target className="w-3.5 h-3.5" /> Mark as Studied
            </>
          )}
        </Button>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed mb-6">
        {problem.description}
      </p>

      <div className="space-y-3">
        {/* Requirements */}
        <Section
          title="Requirements"
          icon={<Target className="w-4 h-4 text-primary" />}
          defaultOpen
        >
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                Functional
              </p>
              <ul className="space-y-1.5">
                {problem.requirements.functional.map((r, i) => (
                  <li
                    key={i}
                    className="text-sm text-foreground flex items-start gap-2"
                  >
                    <ChevronRight className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                Non-Functional
              </p>
              <ul className="space-y-1.5">
                {problem.requirements.nonFunctional.map((r, i) => (
                  <li
                    key={i}
                    className="text-sm text-foreground flex items-start gap-2"
                  >
                    <ChevronRight className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Section>

        {/* High-Level Design */}
        <Section
          title="High-Level Design"
          icon={<Boxes className="w-4 h-4 text-info" />}
          defaultOpen
        >
          <div className="mb-4">
            <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
              Components
            </p>
            <div className="flex flex-wrap gap-2">
              {problem.highLevelDesign.components.map((c, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium bg-accent/50 border border-border text-foreground"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-xl bg-muted/40 border border-border p-4 font-mono text-xs text-foreground whitespace-pre-wrap leading-relaxed">
            {problem.highLevelDesign.diagram}
          </div>
        </Section>

        {/* Deep Dive */}
        {problem.deepDive.map((dd, i) => (
          <Section
            key={i}
            title={dd.title}
            icon={<Search className="w-4 h-4 text-warning" />}
          >
            <p className="text-sm text-foreground leading-relaxed">
              {dd.content}
            </p>
          </Section>
        ))}

        {/* Bottlenecks */}
        <Section
          title="Bottlenecks & Challenges"
          icon={<AlertTriangle className="w-4 h-4 text-destructive" />}
        >
          <ul className="space-y-2">
            {problem.bottlenecks.map((b, i) => (
              <li
                key={i}
                className="text-sm text-foreground flex items-start gap-2"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-destructive mt-0.5 shrink-0" />
                {b}
              </li>
            ))}
          </ul>
        </Section>

        {/* Scaling Strategies */}
        <Section
          title="Scaling Strategies"
          icon={<ArrowUpRight className="w-4 h-4 text-success" />}
        >
          <ul className="space-y-2">
            {problem.scaling.map((s, i) => (
              <li
                key={i}
                className="text-sm text-foreground flex items-start gap-2"
              >
                <ArrowUpRight className="w-3.5 h-3.5 text-success mt-0.5 shrink-0" />
                {s}
              </li>
            ))}
          </ul>
        </Section>

        {/* Key Takeaways */}
        <div className="bg-primary/5 border border-primary/15 rounded-xl p-5">
          <h4 className="text-sm font-bold flex items-center gap-2 mb-3 text-foreground">
            <Lightbulb className="w-4 h-4 text-primary" /> Key Takeaways
          </h4>
          <div className="flex flex-wrap gap-2">
            {problem.keyTakeaways.map((kt, i) => (
              <span
                key={i}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-card border border-border text-foreground"
              >
                {kt}
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ──────────────────────────────────────────── */
/*  Problem card (grid view)                    */
/* ──────────────────────────────────────────── */
function ProblemCard({
  problem,
  studied,
  onClick,
}: {
  problem: SystemDesignProblem;
  studied: boolean;
  onClick: () => void;
}) {
  const dc = diffColors[problem.difficulty] || diffColors.Medium;

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ y: -2 }}
      className="w-full text-left rounded-2xl border border-border bg-card p-5 shadow-sm hover:border-primary/30 transition-all cursor-pointer group"
    >
      <div className="flex items-center justify-between mb-3">
        <span
          className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold border ${dc}`}
        >
          {problem.difficulty}
        </span>
        {studied && (
          <span className="flex items-center gap-1 text-[11px] font-bold text-success bg-success/10 border border-success/20 px-2 py-0.5 rounded-lg">
            <Check className="w-3 h-3" /> Studied
          </span>
        )}
      </div>

      <h3 className="text-base font-bold mb-2 text-foreground group-hover:text-primary transition-colors">
        {problem.title}
      </h3>

      <p className="text-xs text-muted-foreground leading-relaxed mb-3 line-clamp-2">
        {problem.description}
      </p>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
          <Clock className="w-3 h-3" /> {problem.estimatedTime}
        </span>
        {problem.company.slice(0, 2).map((c) => (
          <span
            key={c}
            className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-accent/50 text-muted-foreground"
          >
            {c}
          </span>
        ))}
        {problem.company.length > 2 && (
          <span className="text-[10px] text-muted-foreground">
            +{problem.company.length - 2}
          </span>
        )}
      </div>
    </motion.button>
  );
}

/* ──────────────────────────────────────────── */
/*  Main page                                   */
/* ──────────────────────────────────────────── */
export default function SystemDesignPage() {
  const { user } = useAuth();

  const [studied, setStudied] = useState<number[]>(loadStudied);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [difficultyFilter, setDifficultyFilter] = useState<string>("All");

  useEffect(() => {
    saveStudied(studied);
  }, [studied]);

  const toggleStudied = useCallback(
    (id: number) => {
      setStudied((prev) =>
        prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
      );
    },
    [],
  );

  const filteredProblems = useMemo(() => {
    if (difficultyFilter === "All") return SYSTEM_DESIGN_PROBLEMS;
    return SYSTEM_DESIGN_PROBLEMS.filter(
      (p) => p.difficulty === difficultyFilter,
    );
  }, [difficultyFilter]);

  const selectedProblem = SYSTEM_DESIGN_PROBLEMS.find(
    (p) => p.id === selectedId,
  );

  const studiedCount = studied.length;
  const totalCount = SYSTEM_DESIGN_PROBLEMS.length;
  const progressPct = Math.round((studiedCount / totalCount) * 100);

  return (
    <div className="max-w-5xl mx-auto py-6">
        <>
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-info/10 border border-info/20">
            <Server className="w-5 h-5 text-info" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              System Design Playbook
            </h1>
            <p className="text-sm text-muted-foreground">
              12 classic problems asked at MAANG • Step-by-step breakdowns
            </p>
          </div>
        </div>
      </motion.div>

      {/* Stats + Progress */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="flex items-center gap-4 mb-6 flex-wrap"
      >
        <div className="flex items-center gap-3 p-3 rounded-xl bg-card border border-border shadow-sm">
          <Layers className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-bold text-foreground">{totalCount} Problems</span>
        </div>
        <div className="flex items-center gap-3 p-3 rounded-xl bg-card border border-border shadow-sm">
          <Check className="w-4 h-4 text-success" />
          <span className="text-sm font-bold text-success">
            {studiedCount} Studied
          </span>
        </div>
        <div className="flex-1 min-w-[200px]">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressPct}%` }}
              transition={{ duration: 0.6 }}
              className="h-full rounded-full bg-info"
            />
          </div>
          <p className="text-[11px] text-muted-foreground mt-1 font-mono">
            {progressPct}% complete
          </p>
        </div>
      </motion.div>

      <AnimatePresence mode="wait">
        {selectedProblem ? (
          <ProblemDetail
            key={selectedProblem.id}
            problem={selectedProblem}
            studied={studied.includes(selectedProblem.id)}
            onToggleStudied={() => toggleStudied(selectedProblem.id)}
            onBack={() => setSelectedId(null)}
          />
        ) : (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {/* Difficulty filter */}
            <div className="flex items-center gap-2 mb-5 flex-wrap">
              {["All", "Medium", "Hard", "Expert"].map((d) => (
                <button
                  key={d}
                  onClick={() => setDifficultyFilter(d)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
                    difficultyFilter === d
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-transparent text-muted-foreground hover:border-border hover:bg-accent/30"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>

            {/* Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredProblems.map((p, i) => (
                <motion.div
                  key={p.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <ProblemCard
                    problem={p}
                    studied={studied.includes(p.id)}
                    onClick={() => setSelectedId(p.id)}
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
        </>
    </div>
  );
}
