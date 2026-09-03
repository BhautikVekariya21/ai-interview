import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Clapperboard, Loader2, Link2Off, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import Seo from "@/components/Seo";
import ReplayTimeline from "@/components/ReplayTimeline";
import { fetchReplay, type ReplayDocument } from "@/lib/api";

type PageState = "loading" | "error" | "ready";

export default function ReplayPage() {
  const token = useMemo(
    () => window.location.hash.replace(/^#/, "").trim(),
    [],
  );
  const [state, setState] = useState<PageState>("loading");
  const [doc, setDoc] = useState<ReplayDocument | null>(null);

  useEffect(() => {
    if (!token) {
      setState("error");
      return;
    }
    let cancelled = false;
    fetchReplay(token)
      .then((result) => {
        if (cancelled) return;
        setDoc(result.replay);
        setState("ready");
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const meta = doc?.meta ?? {};
  const candidateName = String(meta.candidate_name ?? "Candidate");

  return (
    <div className="min-h-screen bg-background py-10 px-4">
      <Seo title={`Game Tape — ${candidateName}`} noindex />
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-muted-foreground mb-3">
            <Sparkles className="w-3.5 h-3.5 text-brand" />
            interviewer.ai · Game Tape replay
          </div>
          {state === "ready" && doc && (
            <h1 className="text-2xl font-sans font-bold text-foreground">
              {candidateName}
              <span className="text-muted-foreground font-normal"> · replay</span>
            </h1>
          )}
        </div>

        {state === "loading" && (
          <div className="rounded-2xl border border-border bg-card shadow-sm p-8 flex flex-col items-center gap-3 text-muted-foreground">
            <Loader2 className="w-6 h-6 animate-spin text-brand" />
            <p className="text-sm">Loading the tape…</p>
          </div>
        )}

        {state === "error" && (
          <div className="rounded-2xl border border-border bg-card shadow-sm p-8 text-center">
            <Link2Off className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <h2 className="text-lg font-bold text-foreground mb-2">
              Replay link not found
            </h2>
            <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6 leading-relaxed">
              This link does not point to a saved replay, or the replay has
              been removed. Ask the candidate to share their Game Tape link
              again from the results page.
            </p>
            <Link to="/">
              <Button variant="outline">Go to interviewer.ai</Button>
            </Link>
          </div>
        )}

        {state === "ready" && doc && (
          <div className="rounded-2xl border border-border bg-card/60 shadow-sm p-5">
            <div className="flex items-center gap-2.5 mb-4 text-xs text-muted-foreground">
              <span className="w-8 h-8 rounded-lg bg-brand/10 text-brand flex items-center justify-center">
                <Clapperboard className="w-4 h-4" />
              </span>
              <span>
                Shared replay
                {typeof meta.overall_grade === "string" &&
                  meta.overall_grade && (
                    <> · {meta.overall_grade}</>
                  )}
                {meta.overall_score != null && (
                  <> · {Math.round(Number(meta.overall_score))}%</>
                )}
              </span>
            </div>
            <ReplayTimeline doc={doc} />
          </div>
        )}
      </div>
    </div>
  );
}
