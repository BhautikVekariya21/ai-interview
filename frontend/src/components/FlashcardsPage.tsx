import { useState, useMemo, useCallback, useEffect } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Shuffle,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Check,
  X,
  Filter,
  Layers,
  Zap,
  Clock,
  Target,
  BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  FLASHCARDS,
  TOPICS,
  DIFFICULTY_COLORS,
  type Flashcard,
  type Topic,
} from "./flashcardsData";

/* ────────────────────────────────────────────────────────── */
/*  Persistence helpers                                       */
/* ────────────────────────────────────────────────────────── */
const STORAGE_KEY = "dsa_flashcards_progress";

interface Progress {
  mastered: number[]; // card ids
  review: number[];
}

function loadProgress(): Progress {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Progress;
  } catch {}
  return { mastered: [], review: [] };
}

function saveProgress(p: Progress) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}

/* ────────────────────────────────────────────────────────── */
/*  Flashcard flip component                                  */
/* ────────────────────────────────────────────────────────── */
function FlipCard({
  card,
  flipped,
  onFlip,
}: {
  card: Flashcard;
  flipped: boolean;
  onFlip: () => void;
}) {
  const dc = DIFFICULTY_COLORS[card.difficulty];

  return (
    <div
      className="perspective-1000 w-full cursor-pointer select-none"
      onClick={onFlip}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onFlip()}
    >
      <motion.div
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        className="preserve-3d relative w-full"
        style={{ minHeight: 340 }}
      >
        {/* FRONT */}
        <div className="backface-hidden absolute inset-0 flex flex-col rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-muted-foreground tracking-wider uppercase">
              {card.topic}
            </span>
            <span
              className={`px-2.5 py-0.5 rounded-lg text-[11px] font-bold border ${dc.bg} ${dc.text} ${dc.border}`}
            >
              {card.difficulty}
            </span>
          </div>

          <h3 className="text-xl font-bold mb-3 text-foreground">{card.title}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed flex-1">
            {card.question}
          </p>

          <div className="mt-6 pt-4 border-t border-border">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Zap className="w-3.5 h-3.5" />
              <span className="font-medium">Hint:</span> {card.hint}
            </div>
          </div>

          <p className="text-[11px] text-center text-muted-foreground mt-4 opacity-60">
            Click to reveal solution →
          </p>
        </div>

        {/* BACK */}
        <div
          className="backface-hidden absolute inset-0 flex flex-col rounded-2xl border border-border bg-card p-6 shadow-sm"
          style={{ transform: "rotateY(180deg)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-primary tracking-wider uppercase flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5" /> Solution
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-lg bg-primary/10 text-primary border border-primary/20">
              {card.pattern}
            </span>
          </div>

          <p className="text-sm text-foreground leading-relaxed flex-1">
            {card.approach}
          </p>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-border bg-muted/40 p-3">
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                Time
              </p>
              <p className="text-sm font-bold font-mono text-foreground">
                {card.timeComplexity}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-muted/40 p-3">
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                Space
              </p>
              <p className="text-sm font-bold font-mono text-foreground">
                {card.spaceComplexity}
              </p>
            </div>
          </div>

          <p className="text-[11px] text-center text-muted-foreground mt-4 opacity-60">
            Click to flip back
          </p>
        </div>
      </motion.div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────── */
/*  Topic filter pill                                         */
/* ────────────────────────────────────────────────────────── */
function TopicPill({
  topic,
  active,
  count,
  mastered,
  onClick,
}: {
  topic: string;
  active: boolean;
  count: number;
  mastered: number;
  onClick: () => void;
}) {
  const pct = count > 0 ? Math.round((mastered / count) * 100) : 0;
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold transition-all cursor-pointer ${
        active
          ? "border-primary/30 bg-primary/10 text-primary scale-[1.02]"
          : "border-transparent text-muted-foreground hover:border-border hover:bg-accent/30"
      }`}
    >
      <span>{topic}</span>
      <span className="font-mono text-[10px] opacity-60">{count}</span>
      {mastered > 0 && (
        <span className="ml-auto text-[10px] font-mono text-success">{pct}%</span>
      )}
    </button>
  );
}

/* ────────────────────────────────────────────────────────── */
/*  Main FlashcardsPage                                      */
/* ────────────────────────────────────────────────────────── */
export default function FlashcardsPage() {
  const [progress, setProgress] = useState<Progress>(loadProgress);
  const [activeTopic, setActiveTopic] = useState<Topic | "All">("All");
  const [activeDifficulty, setActiveDifficulty] = useState<
    "All" | "Easy" | "Medium" | "Hard"
  >("All");
  const [shuffled, setShuffled] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);

  // filter cards
  const filteredCards = useMemo(() => {
    let cards = FLASHCARDS.filter((c) => {
      if (activeTopic !== "All" && c.topic !== activeTopic) return false;
      if (activeDifficulty !== "All" && c.difficulty !== activeDifficulty)
        return false;
      return true;
    });
    if (shuffled) {
      cards = [...cards].sort(() => Math.random() - 0.5);
    }
    return cards;
  }, [activeTopic, activeDifficulty, shuffled]);

  const currentCard = filteredCards[currentIndex] as Flashcard | undefined;

  // Reset index when filters change
  useEffect(() => {
    setCurrentIndex(0);
    setFlipped(false);
  }, [activeTopic, activeDifficulty, shuffled]);

  // Persist progress
  useEffect(() => {
    saveProgress(progress);
  }, [progress]);

  const navigate = useCallback(
    (dir: 1 | -1) => {
      setFlipped(false);
      setCurrentIndex((prev) => {
        const next = prev + dir;
        if (next < 0) return filteredCards.length - 1;
        if (next >= filteredCards.length) return 0;
        return next;
      });
    },
    [filteredCards.length],
  );

  const markCard = useCallback(
    (type: "mastered" | "review") => {
      if (!currentCard) return;
      setProgress((prev) => {
        const id = currentCard.id;
        const newMastered = prev.mastered.filter((x) => x !== id);
        const newReview = prev.review.filter((x) => x !== id);
        if (type === "mastered") newMastered.push(id);
        else newReview.push(id);
        return { mastered: newMastered, review: newReview };
      });
      navigate(1);
    },
    [currentCard, navigate],
  );

  const resetProgress = useCallback(() => {
    setProgress({ mastered: [], review: [] });
  }, []);

  // Stats
  const topicCounts = useMemo(() => {
    const map: Record<string, { total: number; mastered: number }> = {};
    for (const t of TOPICS) map[t] = { total: 0, mastered: 0 };
    for (const c of FLASHCARDS) {
      map[c.topic].total++;
      if (progress.mastered.includes(c.id)) map[c.topic].mastered++;
    }
    return map;
  }, [progress.mastered]);

  const totalMastered = progress.mastered.length;
  const totalReview = progress.review.length;
  const totalCards = FLASHCARDS.length;
  const masteryPct = Math.round((totalMastered / totalCards) * 100);

  // Keyboard nav
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") navigate(1);
      else if (e.key === "ArrowLeft") navigate(-1);
      else if (e.key === " ") {
        e.preventDefault();
        setFlipped((f) => !f);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate]);

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
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
            <Brain className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              DSA Flashcards
            </h1>
            <p className="text-sm text-muted-foreground">
              75 essential patterns • Blind 75 + NeetCode coverage
            </p>
          </div>
        </div>
      </motion.div>

      {/* Stats row */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6"
      >
        {[
          {
            icon: <Layers className="w-4 h-4" />,
            value: totalCards,
            label: "Total Cards",
          },
          {
            icon: <Check className="w-4 h-4" />,
            value: totalMastered,
            label: "Mastered",
            color: "text-success",
          },
          {
            icon: <RotateCcw className="w-4 h-4" />,
            value: totalReview,
            label: "Review",
            color: "text-amber-500",
          },
          {
            icon: <Target className="w-4 h-4" />,
            value: `${masteryPct}%`,
            label: "Overall Mastery",
            color: masteryPct >= 70 ? "text-success" : undefined,
          },
        ].map((s, i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-3.5 rounded-xl bg-card border border-border shadow-sm"
          >
            <div className="w-9 h-9 rounded-lg bg-accent/50 border border-border flex items-center justify-center text-foreground">
              {s.icon}
            </div>
            <div>
              <span className={`text-base font-bold block ${s.color || ""}`}>
                {s.value}
              </span>
              <span className="text-xs text-muted-foreground">{s.label}</span>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Mastery bar */}
      <div className="mb-6 px-1">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-semibold text-muted-foreground">
            Overall Progress
          </span>
          <span className="text-xs font-bold font-mono text-foreground">
            {totalMastered}/{totalCards}
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${masteryPct}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="h-full rounded-full"
            style={{ background: "var(--gradient-accent)" }}
          />
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Topic filter sidebar */}
        <div className="lg:w-64 shrink-0">
          <button
            className="lg:hidden flex items-center gap-2 text-sm font-semibold mb-3 text-foreground"
            onClick={() => setFilterOpen(!filterOpen)}
          >
            <Filter className="w-4 h-4" /> Filters{" "}
            {filterOpen ? "▲" : "▼"}
          </button>

          <div className={`space-y-1 ${filterOpen ? "" : "hidden lg:block"}`}>
            <TopicPill
              topic="All Topics"
              active={activeTopic === "All"}
              count={totalCards}
              mastered={totalMastered}
              onClick={() => setActiveTopic("All")}
            />
            {TOPICS.map((t) => (
              <TopicPill
                key={t}
                topic={t}
                active={activeTopic === t}
                count={topicCounts[t]?.total || 0}
                mastered={topicCounts[t]?.mastered || 0}
                onClick={() => setActiveTopic(t)}
              />
            ))}

            <div className="pt-4 border-t border-border mt-4 space-y-1">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2 font-semibold">
                Difficulty
              </p>
              {(["All", "Easy", "Medium", "Hard"] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setActiveDifficulty(d)}
                  className={`block w-full text-left rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                    activeDifficulty === d
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "text-muted-foreground hover:bg-accent/30 border border-transparent"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>

            <div className="pt-4 border-t border-border mt-4 space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start text-xs"
                onClick={() => setShuffled(!shuffled)}
              >
                <Shuffle className="w-3.5 h-3.5 mr-2" />
                {shuffled ? "Unshuffle" : "Shuffle"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-xs text-destructive hover:bg-destructive/10"
                onClick={resetProgress}
              >
                <RotateCcw className="w-3.5 h-3.5 mr-2" />
                Reset Progress
              </Button>
            </div>
          </div>
        </div>

        {/* Right: Card area */}
        <div className="flex-1 min-w-0">
          {filteredCards.length === 0 ? (
            <div className="text-center py-16 rounded-2xl border border-border bg-card">
              <Brain className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
              <p className="text-muted-foreground font-medium">
                No cards match your filters
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Try adjusting your topic or difficulty selection.
              </p>
            </div>
          ) : (
            <>
              {/* Card counter */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold text-muted-foreground">
                  Card {currentIndex + 1} of {filteredCards.length}
                </span>
                <div className="flex items-center gap-1">
                  {currentCard &&
                    progress.mastered.includes(currentCard.id) && (
                      <span className="text-[11px] font-bold text-success bg-success/10 border border-success/20 px-2 py-0.5 rounded-lg">
                        Mastered
                      </span>
                    )}
                  {currentCard &&
                    progress.review.includes(currentCard.id) && (
                      <span className="text-[11px] font-bold text-amber-600 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-lg">
                        Review
                      </span>
                    )}
                </div>
              </div>

              {/* The card */}
              <AnimatePresence mode="wait">
                {currentCard && (
                  <motion.div
                    key={currentCard.id}
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.25 }}
                  >
                    <FlipCard
                      card={currentCard}
                      flipped={flipped}
                      onFlip={() => setFlipped((f) => !f)}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Controls */}
              <div className="flex items-center justify-between mt-6 gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(-1)}
                  className="gap-1.5"
                >
                  <ChevronLeft className="w-4 h-4" /> Prev
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 border-amber-500/30 text-amber-600 hover:bg-amber-500/10"
                    onClick={() => markCard("review")}
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Review
                  </Button>
                  <Button
                    size="sm"
                    className="gap-1.5"
                    onClick={() => markCard("mastered")}
                  >
                    <Check className="w-3.5 h-3.5" /> Got it
                  </Button>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(1)}
                  className="gap-1.5"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </Button>
              </div>

              {/* Keyboard hint */}
              <p className="text-[11px] text-center text-muted-foreground mt-4 opacity-50">
                ← → to navigate • Space to flip • Shortcuts work anywhere on the page
              </p>
            </>
          )}
        </div>
      </div>

      {/* Per-topic mastery breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="mt-10 bg-card border border-border rounded-2xl p-5 shadow-sm"
      >
        <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-foreground">
          <BarChart3 className="w-4 h-4 text-primary" /> Topic Mastery Breakdown
        </h3>
        <div className="space-y-3">
          {TOPICS.map((t) => {
            const tc = topicCounts[t];
            const pct =
              tc.total > 0 ? Math.round((tc.mastered / tc.total) * 100) : 0;
            return (
              <div key={t}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    {t}
                  </span>
                  <span className="text-xs font-bold font-mono text-foreground">
                    {tc.mastered}/{tc.total}
                  </span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className="h-full rounded-full bg-primary"
                  />
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>
        </>
    </div>
  );
}
