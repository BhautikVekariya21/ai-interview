import { useState, useCallback, useEffect, useMemo } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Star,
  ChevronRight,
  ChevronLeft,
  Trash2,
  Download,
  Plus,
  Eye,
  Sparkles,
  Save,
  FileText,
  Target,
  Zap,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useAuth } from "@/components/AuthProvider";

/* ──────────────────────────────────────────── */
/*  Types                                       */
/* ──────────────────────────────────────────── */
interface StarStory {
  id: string;
  promptLabel: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  createdAt: string;
}

const STAR_STEPS = ["Situation", "Task", "Action", "Result"] as const;
type StarStep = (typeof STAR_STEPS)[number];

const STEP_CONFIG: Record<
  StarStep,
  { icon: React.ReactNode; color: string; placeholder: string; tip: string }
> = {
  Situation: {
    icon: <Target className="w-4 h-4" />,
    color: "text-info",
    placeholder:
      "Set the scene. Describe the context, project, team, and what was happening at the time...",
    tip: "Be specific: mention the company, team size, timeline, and what was at stake.",
  },
  Task: {
    icon: <Zap className="w-4 h-4" />,
    color: "text-warning",
    placeholder:
      "What was your specific responsibility or goal in this situation?",
    tip: "Clarify YOUR role vs. the team's role. What were you accountable for?",
  },
  Action: {
    icon: <ArrowRight className="w-4 h-4" />,
    color: "text-primary",
    placeholder:
      "What steps did YOU take? Be specific about your individual contributions...",
    tip: "Use 'I' not 'we'. Describe the technical approach, decisions you made, and why.",
  },
  Result: {
    icon: <CheckCircle2 className="w-4 h-4" />,
    color: "text-success",
    placeholder:
      "What happened? Quantify the outcomes — metrics, improvements, impact...",
    tip: "Numbers matter: 40% faster, $2M saved, 99.9% uptime, 3x user growth.",
  },
};

const BEHAVIORAL_PROMPTS = [
  "Tell me about a time you disagreed with a teammate",
  "Describe a project that failed and what you learned",
  "Tell me about the most complex technical problem you solved",
  "Describe a time you had to meet a tight deadline",
  "Tell me about a time you influenced a decision without authority",
  "Describe a situation where you went above and beyond",
  "Tell me about a time you had to make a decision with incomplete data",
  "Describe a conflict with a manager and how you handled it",
  "Tell me about a time you had to learn something quickly",
  "Describe how you prioritized competing tasks under pressure",
  "Tell me about a time you received critical feedback",
  "Describe a situation where you improved a process",
  "Tell me about a time you mentored someone",
  "Describe a situation where you had to push back on a requirement",
  "Tell me about a time you took ownership of a problem outside your scope",
];

/* ──────────────────────────────────────────── */
/*  Persistence                                 */
/* ──────────────────────────────────────────── */
const STORAGE_KEY = "star_builder_stories";

function loadStories(): StarStory[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as StarStory[];
  } catch {
    // ignore corrupt/missing localStorage data
  }
  return [];
}

function saveStories(s: StarStory[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

/* ──────────────────────────────────────────── */
/*  Word counter                                */
/* ──────────────────────────────────────────── */
function wordCount(text: string) {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

/* ──────────────────────────────────────────── */
/*  Story preview card                          */
/* ──────────────────────────────────────────── */
function StoryCard({
  story,
  active,
  onSelect,
  onDelete,
}: {
  story: StarStory;
  active: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const totalWords =
    wordCount(story.situation) +
    wordCount(story.task) +
    wordCount(story.action) +
    wordCount(story.result);
  const filledSteps = [
    story.situation,
    story.task,
    story.action,
    story.result,
  ].filter(Boolean).length;

  return (
    <div
      onClick={onSelect}
      className={`rounded-xl border p-3.5 cursor-pointer transition-all group ${
        active
          ? "border-primary/30 bg-primary/5 ring-1 ring-primary/10"
          : "border-border bg-card hover:border-primary/20"
      }`}
    >
      <p className="text-sm font-semibold text-foreground line-clamp-2 mb-2">
        {story.promptLabel || "Untitled Story"}
      </p>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {STAR_STEPS.map((step, i) => {
            const filled =
              step === "Situation"
                ? !!story.situation
                : step === "Task"
                  ? !!story.task
                  : step === "Action"
                    ? !!story.action
                    : !!story.result;
            return (
              <div
                key={i}
                className={`w-5 h-1.5 rounded-full ${filled ? "bg-primary" : "bg-muted"}`}
              />
            );
          })}
          <span className="text-[10px] text-muted-foreground ml-1">
            {filledSteps}/4
          </span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
      <p className="text-[10px] text-muted-foreground mt-1.5">
        {totalWords} words •{" "}
        {new Date(story.createdAt).toLocaleDateString()}
      </p>
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Main page                                   */
/* ──────────────────────────────────────────── */
export default function StarBuilderPage() {
  const { user } = useAuth();

  const [stories, setStories] = useState<StarStory[]>(loadStories);
  const [activeStoryId, setActiveStoryId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [showPreview, setShowPreview] = useState(false);
  const [isPolishing, setIsPolishing] = useState(false);

  const activeStory = stories.find((s) => s.id === activeStoryId) || null;

  // Persist
  useEffect(() => {
    saveStories(stories);
  }, [stories]);

  const createStory = useCallback(
    (prompt: string) => {
      const newStory: StarStory = {
        id: `star_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        promptLabel: prompt,
        situation: "",
        task: "",
        action: "",
        result: "",
        createdAt: new Date().toISOString(),
      };
      setStories((prev) => [newStory, ...prev].slice(0, 10)); // max 10
      setActiveStoryId(newStory.id);
      setCurrentStep(0);
      setShowPreview(false);
    },
    [],
  );

  const updateStoryField = useCallback(
    (field: "situation" | "task" | "action" | "result", value: string) => {
      setStories((prev) =>
        prev.map((s) => (s.id === activeStoryId ? { ...s, [field]: value } : s)),
      );
    },
    [activeStoryId],
  );

  const deleteStory = useCallback(
    (id: string) => {
      setStories((prev) => prev.filter((s) => s.id !== id));
      if (activeStoryId === id) {
        setActiveStoryId(null);
        setCurrentStep(0);
      }
    },
    [activeStoryId],
  );

  const exportStories = useCallback(() => {
    const md = stories
      .map(
        (s) =>
          `## ${s.promptLabel}\n\n**Situation:** ${s.situation || "_empty_"}\n\n**Task:** ${s.task || "_empty_"}\n\n**Action:** ${s.action || "_empty_"}\n\n**Result:** ${s.result || "_empty_"}\n\n---`,
      )
      .join("\n\n");
    const blob = new Blob(
      [`# STAR Stories — Interview Prep\n\n${md}`],
      { type: "text/markdown;charset=utf-8" },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "star-stories.md";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success("Stories exported as Markdown!");
  }, [stories]);

  const handlePolish = useCallback(async () => {
    if (!activeStory) return;
    setIsPolishing(true);
    try {
      const { improveStarStory } = await import("@/lib/api");
      const result = await improveStarStory({
        situation: activeStory.situation,
        task: activeStory.task,
        action: activeStory.action,
        result: activeStory.result,
      });
      if (result.success) {
        if (result.situation) updateStoryField("situation", result.situation);
        if (result.task) updateStoryField("task", result.task);
        if (result.action) updateStoryField("action", result.action);
        if (result.result) updateStoryField("result", result.result);
        const feedbackParts: string[] = [];
        if (result.score) feedbackParts.push(`Score: ${result.score}/100`);
        if (result.feedback) feedbackParts.push(result.feedback);
        toast.success(feedbackParts.length > 0 ? feedbackParts.join(" — ") : "Story polished by AI! Review the changes.");
      } else {
        throw new Error(result.error || "AI polish failed");
      }
    } catch {
      // Fallback to local polish if backend unavailable
      const fields: Array<"situation" | "task" | "action" | "result"> = ["situation", "task", "action", "result"];
      for (const field of fields) {
        const val = activeStory[field];
        if (val && val.length > 20) {
          const polished = val.charAt(0).toUpperCase() + val.slice(1).trim() + (val.trim().endsWith(".") ? "" : ".");
          updateStoryField(field, polished);
        }
      }
      toast.success("Story polished locally. Connect to backend for AI-powered improvements.");
    } finally {
      setIsPolishing(false);
    }
  }, [activeStory, updateStoryField]);

  const stepKey = STAR_STEPS[currentStep];
  const stepConfig = STEP_CONFIG[stepKey];
  const fieldMap: Record<number, "situation" | "task" | "action" | "result"> = {
    0: "situation",
    1: "task",
    2: "action",
    3: "result",
  };
  const currentFieldKey = fieldMap[currentStep];
  const currentFieldValue = activeStory?.[currentFieldKey] || "";

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
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 border border-amber-500/20">
            <Star className="w-5 h-5 text-amber-500" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Behavioral STAR Builder
            </h1>
            <p className="text-sm text-muted-foreground">
              Craft powerful STAR stories • Save up to 10 • Export for review
            </p>
          </div>
        </div>
      </motion.div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Story list */}
        <div className="lg:w-72 shrink-0">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-foreground">
              My Stories ({stories.length}/10)
            </span>
            {stories.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs h-7"
                onClick={exportStories}
              >
                <Download className="w-3 h-3 mr-1" /> Export
              </Button>
            )}
          </div>

          <div className="space-y-2 mb-4">
            {stories.map((s) => (
              <StoryCard
                key={s.id}
                story={s}
                active={s.id === activeStoryId}
                onSelect={() => {
                  setActiveStoryId(s.id);
                  setCurrentStep(0);
                  setShowPreview(false);
                }}
                onDelete={() => deleteStory(s.id)}
              />
            ))}
          </div>

          {stories.length < 10 && (
            <div className="border border-dashed border-border rounded-xl p-4">
              <p className="text-xs font-semibold text-foreground mb-2">
                Start from a prompt:
              </p>
              <div className="space-y-1.5 max-h-[300px] overflow-y-auto hidden-scrollbar">
                {BEHAVIORAL_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => createStory(prompt)}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs text-muted-foreground hover:bg-accent/30 hover:text-foreground transition-all cursor-pointer border border-transparent hover:border-border"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-3 text-xs"
                onClick={() => createStory("Custom Story")}
              >
                <Plus className="w-3 h-3 mr-1.5" /> Blank Story
              </Button>
            </div>
          )}
        </div>

        {/* Right: Editor */}
        <div className="flex-1 min-w-0">
          {!activeStory ? (
            <div className="text-center py-16 rounded-2xl border border-border bg-card">
              <Star className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
              <p className="text-lg font-medium text-muted-foreground">
                Select or create a STAR story
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Choose a behavioral prompt from the left panel to get started.
              </p>
            </div>
          ) : showPreview ? (
            /* Preview mode */
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl border border-border bg-card p-6 shadow-sm"
            >
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                  <Eye className="w-5 h-5 text-primary" /> Full Story Preview
                </h3>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePolish}
                    disabled={isPolishing}
                    className="gap-1.5 text-xs"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    {isPolishing ? "Polishing..." : "AI Polish"}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowPreview(false)}
                    className="text-xs"
                  >
                    Edit
                  </Button>
                </div>
              </div>

              <p className="text-sm font-semibold text-primary mb-4">
                "{activeStory.promptLabel}"
              </p>

              {STAR_STEPS.map((step, i) => {
                const field = fieldMap[i];
                const value = activeStory[field];
                const cfg = STEP_CONFIG[step];
                return (
                  <div key={step} className="mb-4">
                    <h4
                      className={`text-xs font-bold uppercase tracking-wider ${cfg.color} mb-1.5 flex items-center gap-1.5`}
                    >
                      {cfg.icon} {step}
                    </h4>
                    <p className="text-sm text-foreground leading-relaxed pl-6">
                      {value || (
                        <span className="italic text-muted-foreground">
                          Not filled in yet
                        </span>
                      )}
                    </p>
                  </div>
                );
              })}

              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground">
                  Total:{" "}
                  {wordCount(activeStory.situation) +
                    wordCount(activeStory.task) +
                    wordCount(activeStory.action) +
                    wordCount(activeStory.result)}{" "}
                  words • Aim for 150-250 words total for a 2-minute answer
                </p>
              </div>
            </motion.div>
          ) : (
            /* Editor mode */
            <div>
              <p className="text-sm font-semibold text-primary mb-4">
                "{activeStory.promptLabel}"
              </p>

              {/* Step progress */}
              <div className="flex items-center gap-1 mb-6">
                {STAR_STEPS.map((step, i) => {
                  const cfg = STEP_CONFIG[step];
                  const completed = !!activeStory[fieldMap[i]];
                  const isCurrent = i === currentStep;
                  return (
                    <button
                      key={step}
                      onClick={() => setCurrentStep(i)}
                      className={`flex-1 text-center py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer border ${
                        isCurrent
                          ? "border-primary/30 bg-primary/10 text-primary"
                          : completed
                            ? "border-success/20 bg-success/5 text-success"
                            : "border-transparent text-muted-foreground hover:bg-accent/20"
                      }`}
                    >
                      <span className="flex items-center justify-center gap-1.5">
                        {completed && !isCurrent ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          cfg.icon
                        )}
                        {step}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Current step editor */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="rounded-2xl border border-border bg-card p-6 shadow-sm"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <span className={`${stepConfig.color}`}>
                      {stepConfig.icon}
                    </span>
                    <h3 className="text-base font-bold text-foreground">
                      {stepKey}
                    </h3>
                    <span className="text-xs text-muted-foreground ml-auto font-mono">
                      {wordCount(currentFieldValue)} words
                    </span>
                  </div>

                  <div className="mb-3 rounded-lg bg-accent/30 border border-border px-3 py-2">
                    <p className="text-xs text-muted-foreground">
                      💡 {stepConfig.tip}
                    </p>
                  </div>

                  <textarea
                    value={currentFieldValue}
                    onChange={(e) =>
                      updateStoryField(currentFieldKey, e.target.value)
                    }
                    placeholder={stepConfig.placeholder}
                    rows={6}
                    className="w-full bg-transparent border border-border rounded-xl p-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all resize-none leading-relaxed"
                  />

                  {/* Nav buttons */}
                  <div className="flex items-center justify-between mt-5">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentStep === 0}
                      onClick={() => setCurrentStep((s) => s - 1)}
                      className="gap-1.5"
                    >
                      <ChevronLeft className="w-4 h-4" /> Back
                    </Button>

                    {currentStep < 3 ? (
                      <Button
                        size="sm"
                        onClick={() => setCurrentStep((s) => s + 1)}
                        className="gap-1.5"
                      >
                        Next <ChevronRight className="w-4 h-4" />
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => setShowPreview(true)}
                        className="gap-1.5"
                      >
                        <Eye className="w-4 h-4" /> Preview Story
                      </Button>
                    )}
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
        </>
    </div>
  );
}
