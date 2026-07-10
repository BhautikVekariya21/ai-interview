import { m as motion } from "framer-motion";
import { ClipboardList, Brain, Code2, Server, MessageSquare, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import type { Module5Evaluation } from "@/components/ResultsPage";

interface PracticePlanProps {
  evaluations?: Module5Evaluation[];
  scores: {
    overall: number;
    technicalScore: number;
    communicationScore: number;
    clarityScore: number;
    depthScore: number;
  };
}

interface PlanItem {
  key: string;
  title: string;
  reason: string;
  icon: React.ReactNode;
  cta: string;
  route: string;
}

const KEYWORD_ROUTES: { pattern: RegExp; route: string; label: string }[] = [
  { pattern: /system design|scalab|architect|distributed|database|cache|load balanc/i, route: "/app/system-design", label: "System Design Playbook" },
  { pattern: /algorithm|data structure|complexity|code|coding|leetcode|array|graph|tree/i, route: "/app/coding-practice", label: "Coding Practice" },
  { pattern: /behavior|star|situation|leadership|conflict|team/i, route: "/app/star-builder", label: "STAR Story Builder" },
];

/**
 * Builds a short, concrete list of what to practice next based on
 * where a candidate actually scored lowest — both from the numeric
 * category breakdown and from the free-text "improvements" the
 * evaluator called out per question.
 */
function buildPlan(evaluations: Module5Evaluation[] | undefined, scores: PracticePlanProps["scores"]): PlanItem[] {
  const items: PlanItem[] = [];
  const evals = Array.isArray(evaluations) ? evaluations : [];

  const improvementText = evals
    .flatMap((ev) => ev.improvements || [])
    .join(" ")
    .toLowerCase();

  const categories: { key: keyof typeof scores; label: string; icon: React.ReactNode; route: string; cta: string }[] = [
    { key: "technicalScore", label: "Technical Depth", icon: <Brain className="w-4 h-4" />, route: "/app/flashcards", cta: "Review DSA Flashcards" },
    { key: "depthScore", label: "Answer Depth", icon: <Code2 className="w-4 h-4" />, route: "/app/coding-practice", cta: "Practice Coding Problems" },
    { key: "clarityScore", label: "Clarity", icon: <Server className="w-4 h-4" />, route: "/app/system-design", cta: "Study System Design Playbook" },
    { key: "communicationScore", label: "Communication", icon: <MessageSquare className="w-4 h-4" />, route: "/app/star-builder", cta: "Build a STAR Story" },
  ];

  // Weakest two numeric categories, in order.
  const ranked = [...categories].sort((a, b) => scores[a.key] - scores[b.key]);
  for (const cat of ranked.slice(0, 2)) {
    if (scores[cat.key] >= 80) continue; // already strong, don't recommend
    items.push({
      key: cat.key,
      title: `Strengthen ${cat.label}`,
      reason: `Your ${cat.label.toLowerCase()} score was ${scores[cat.key]}% — the lowest of your interview categories.`,
      icon: cat.icon,
      cta: cat.cta,
      route: cat.route,
    });
  }

  // Add anything the evaluator explicitly flagged by keyword, if not
  // already covered by the category picks above.
  for (const kw of KEYWORD_ROUTES) {
    if (kw.pattern.test(improvementText) && !items.some((i) => i.route === kw.route)) {
      items.push({
        key: kw.route,
        title: `Focus on ${kw.label}`,
        reason: "Multiple evaluator notes called this out as an area to improve.",
        icon: <ClipboardList className="w-4 h-4" />,
        cta: `Open ${kw.label}`,
        route: kw.route,
      });
    }
  }

  if (items.length === 0) {
    items.push({
      key: "maintain",
      title: "Keep your streak going",
      reason: "Your scores are strong across the board — a quick daily challenge keeps you sharp.",
      icon: <ClipboardList className="w-4 h-4" />,
      cta: "Try Today's Daily Challenge",
      route: "/app/daily-challenge",
    });
  }

  return items.slice(0, 3);
}

export default function PracticePlan({ evaluations, scores }: PracticePlanProps) {
  const navigate = useNavigate();
  const plan = buildPlan(evaluations, scores);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.22 }}
      className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
    >
      <h3 className="text-sm font-bold mb-1 flex items-center gap-2">
        <ClipboardList className="w-4 h-4 text-primary" /> Your Personalized Practice Plan
      </h3>
      <p className="text-xs text-muted-foreground mb-4">
        Based on this interview, here's what to work on next.
      </p>
      <div className="space-y-3">
        {plan.map((item) => (
          <div
            key={item.key}
            className="flex items-center justify-between gap-4 rounded-xl border border-border bg-muted/20 p-4"
          >
            <div className="flex items-start gap-3 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                {item.icon}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-foreground">{item.title}</p>
                <p className="text-xs text-muted-foreground">{item.reason}</p>
              </div>
            </div>
            <Button size="sm" variant="outline" className="shrink-0" onClick={() => navigate(item.route)}>
              {item.cta} <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
