import { useState } from "react";
import { Loader2, Sparkles, Wand2, Target, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Seo from "@/components/Seo";
import { analyzeSTAR, type STARReport } from "@/lib/api";

const DIMENSIONS: { key: "S" | "T" | "A" | "R"; title: string; blurb: string }[] = [
  { key: "S", title: "Situation", blurb: "One line of context and stakes" },
  { key: "T", title: "Task", blurb: "What YOU owned in it" },
  { key: "A", title: "Action", blurb: "Concrete steps you took" },
  { key: "R", title: "Result", blurb: "Measured, quantified outcome" },
];

const EXAMPLE = `Our checkout service started timing out during flash sales, losing orders left and right. I was responsible for the incident response, so my task was to find the root cause and get it fixed within the sprint. First I instrumented the request path, then built a one-off profiler that exposed connection-pool exhaustion, and I rewrote the pooled handling and shipped it behind a flag. We reduced timeout errors by 92% and got positive feedback from the accounts that had been affected.`;

export default function StarCoachPage() {
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<STARReport | null>(null);

  const run = async () => {
    if (!answer.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeSTAR({ answer });
      setReport(result);
    } catch {
      setError("Could not reach the STAR analyzer. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const first = report?.answers?.[0];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Seo
        title="STAR Coach — structure your behavioral answers"
        description="Paste a behavioral interview answer and get instant Situation / Task / Action / Result scoring with targeted coaching. No signup."
      />
      <main className="mx-auto w-full max-w-[1100px] px-6 pb-16 pt-28 lg:px-10">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-brand mb-3">
            <Sparkles className="w-3.5 h-3.5" /> interviewer.ai · STAR Coach
          </div>
          <h1 className="text-3xl md:text-4xl font-sans font-bold tracking-tight mb-3">
            Does your behavioral answer follow STAR?
          </h1>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Paste any behavioral answer and get instant S/T/A/R structure scoring with
            targeted coaching. Free, no signup, no LLM key needed — it runs against a
            deterministic analyzer.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 items-start">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <label htmlFor="star-answer" className="text-sm font-medium leading-none mb-2 block">
              Your behavioral answer
            </label>
            <textarea
              id="star-answer"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={12}
              placeholder="Describe a project, problem, or conflict you handled…"
              className="w-full rounded-xl border border-border bg-background p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <div className="flex items-center justify-between mt-3 gap-2">
              <button
                type="button"
                onClick={() => setAnswer(EXAMPLE)}
                className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
              >
                Load example answer
              </button>
              <Button onClick={run} disabled={loading || !answer.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Analyzing…
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" /> Analyze structure
                  </>
                )}
              </Button>
            </div>
            {error && <p className="text-destructive text-xs mt-3">{error}</p>}
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm min-h-[300px]">
            {!first && (
              <div className="h-full flex flex-col items-center justify-center text-center py-12 text-muted-foreground">
                <Target className="w-10 h-10 mb-3 opacity-50" />
                <p className="text-sm max-w-xs mx-auto">
                  Your S / T / A / R breakdown appears here after you analyze an answer.
                </p>
              </div>
            )}
            {first && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-3xl font-bold">{first.structure_score}</div>
                    <div className="text-xs text-muted-foreground">structure score · {first.grade}</div>
                  </div>
                  <div className="text-xs text-muted-foreground">{first.words} words</div>
                </div>

                <div className="space-y-3 mb-5">
                  {DIMENSIONS.map(({ key, title, blurb }) => {
                    const value = first.star?.[key] ?? 0;
                    const ok = value >= 50;
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="font-medium">
                            {ok ? (
                              <CheckCircle2 className="w-4 h-4 inline text-emerald-500 -mt-0.5" />
                            ) : (
                              <XCircle className="w-4 h-4 inline text-amber-500 -mt-0.5" />
                            )}{" "}
                            {title}
                          </span>
                          <span className="text-xs text-muted-foreground">{blurb}</span>
                        </div>
                        <div className="h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full ${ok ? "bg-brand" : "bg-amber-500"}`}
                            style={{ width: `${Math.max(4, value)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {first.coaching.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Coaching</h3>
                    <ul className="space-y-1.5">
                      {first.coaching.map((tip, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex gap-2">
                          <span className="text-brand shrink-0">→</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
