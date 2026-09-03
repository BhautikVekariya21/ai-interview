import { useState, useEffect, useMemo } from "react";
import { m as motion } from "framer-motion";
import { History, Calendar, Trash2, Download, Eye, BarChart3, Clock, FileJson, AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/AuthProvider";
import EmptyState from "@/components/EmptyState";
import Loading from "@/components/Loading";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface HistoryEntry {
  id?: string;
  candidateName: string;
  date: string;
  finalScores: {
    overall: number;
    completionRate: number;
  };
  finalGrade: string;
  totalQuestions: number;
  details_json?: string;
}

import { getInterviewHistory, clearInterviewHistory } from "@/lib/api";

export default function HistoryPage() {
  const { isAuthenticated } = useAuth();
  
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getInterviewHistory();
      setHistory(data);
    } catch (e) {
      console.error(e);
      setError("We couldn't load your interview history. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      setHistory([]);
      setLoading(false);
      return;
    }
    fetchHistory();
  }, [isAuthenticated]);

  const clearHistory = async () => {
    try {
      await clearInterviewHistory();
      setHistory([]);
    } catch (e) {
      console.error(e);
    }
  };

  const selectedDetails = useMemo(() => {
    if (!selectedEntry?.details_json) return null;
    try {
      return JSON.parse(selectedEntry.details_json) as Record<string, unknown>;
    } catch {
      return null;
    }
  }, [selectedEntry]);

  const exportHistory = (format: "json" | "md") => {
    const enriched = history.map((entry) => ({
      ...entry,
      details: (() => {
        try {
          return entry.details_json ? JSON.parse(entry.details_json) : null;
        } catch {
          return null;
        }
      })(),
    }));

    const content = format === "json"
      ? JSON.stringify(enriched, null, 2)
      : enriched.map((entry) => {
          const details = entry.details as Record<string, unknown> | null;
          const evaluations = Array.isArray(details?.evaluations) ? details?.evaluations as Array<Record<string, unknown>> : [];
          return [
            `# ${entry.candidateName}`,
            `Date: ${new Date(entry.date).toLocaleString()}`,
            `Score: ${entry.finalScores?.overall || 0}%`,
            `Grade: ${entry.finalGrade || "N/A"}`,
            `Questions: ${entry.totalQuestions}`,
            "",
            `Summary: ${String(details?.summary || "No detailed summary saved.")}`,
            "",
            "## Evaluations",
            evaluations.length
              ? evaluations.map((ev, index) => `- Q${ev.question_number || index + 1}: ${ev.score || 0}/100 - ${String(ev.feedback || "")}`).join("\n")
              : "- No detailed evaluation saved.",
            "",
          ].join("\n");
        }).join("\n---\n\n");

    const blob = new Blob([content], { type: format === "json" ? "application/json;charset=utf-8" : "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `interview-history-export.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
            <h1 className="text-4xl md:text-5xl font-sans font-bold tracking-tight leading-tight mb-3 text-[#1E1F1B]">
              Interview History
            </h1>
            <p className="text-muted-foreground text-base max-w-lg mx-auto leading-relaxed">
              Review your past interview performances and track your progress over time.
            </p>
          </motion.div>

      <div className="flex justify-end gap-2 mb-4 flex-wrap">
        {history.length > 0 && (
          <>
            <Button variant="outline" onClick={() => exportHistory("json")}>
              <FileJson className="w-4 h-4 mr-2" /> Export JSON
            </Button>
            <Button variant="outline" onClick={() => exportHistory("md")}>
              <Download className="w-4 h-4 mr-2" /> Export Report
            </Button>
          </>
        )}
        {history.length > 0 && (
          <Button variant="ghost" className="text-destructive hover:bg-destructive/10" onClick={clearHistory}>
            <Trash2 className="w-4 h-4 mr-2" /> Clear History
          </Button>
        )}
      </div>

      {loading ? (
        <div className="bg-card border border-border shadow-sm rounded-xl">
          <Loading size="lg" label="Loading interview history..." className="py-16" />
        </div>
      ) : error ? (
        <div className="bg-card border border-border shadow-sm rounded-xl">
          <EmptyState
            icon={AlertCircle}
            title="Couldn't load history"
            description={error}
            action={
              <Button variant="outline" onClick={fetchHistory}>
                <RotateCcw className="w-4 h-4 mr-2" /> Try again
              </Button>
            }
          />
        </div>
      ) : history.length === 0 ? (
        <div className="bg-card border border-border shadow-sm rounded-xl">
          <EmptyState
            icon={History}
            title={isAuthenticated ? "No interview history found" : "Sign in to view saved history"}
            description={isAuthenticated ? "Complete an interview to see your results here." : "Your history is shown per account after login."}
          />
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((entry, idx) => (
            <motion.div 
              initial={{ opacity: 0, y: 8 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ delay: idx * 0.05 }}
              key={idx} 
              className="flex flex-col md:flex-row items-center gap-4 p-5 bg-card border border-border shadow-sm rounded-xl hover:border-brand/30 transition-all"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-bold text-lg">{entry.candidateName}</h3>
                  <span className="px-2 py-0.5 rounded-xl text-[10px] bg-brand/10 text-brand border border-brand/20 font-mono">
                    {entry.totalQuestions} Questions
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> {new Date(entry.date).toLocaleString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <Button variant="outline" size="sm" onClick={() => setSelectedEntry(entry)}>
                  <Eye className="w-4 h-4 mr-2" /> Details
                </Button>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-0.5">Score</p>
                  <p className="font-bold text-xl">{entry.finalScores?.overall || 0}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground mb-0.5">Grade</p>
                  <p className="font-bold text-xl font-mono text-brand">{entry.finalGrade || 'N/A'}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <Dialog open={Boolean(selectedEntry)} onOpenChange={(open) => !open && setSelectedEntry(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{selectedEntry?.candidateName || "Interview Details"}</DialogTitle>
            <DialogDescription>
              {selectedEntry?.date ? new Date(selectedEntry.date).toLocaleString() : ""}
            </DialogDescription>
          </DialogHeader>

          {selectedEntry && (
            <div className="space-y-5 max-h-[70vh] overflow-y-auto pr-1">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="rounded-xl border border-border bg-muted/20 p-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Overall</p>
                  <p className="text-xl font-extrabold">{selectedEntry.finalScores?.overall || 0}%</p>
                </div>
                <div className="rounded-xl border border-border bg-muted/20 p-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Grade</p>
                  <p className="text-xl font-extrabold text-brand">{selectedEntry.finalGrade}</p>
                </div>
                <div className="rounded-xl border border-border bg-muted/20 p-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Completion</p>
                  <p className="text-xl font-extrabold">{selectedEntry.finalScores?.completionRate || 0}%</p>
                </div>
                <div className="rounded-xl border border-border bg-muted/20 p-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Questions</p>
                  <p className="text-xl font-extrabold">{selectedEntry.totalQuestions}</p>
                </div>
              </div>

              {selectedDetails && (
                <>
                  <div className="rounded-xl border border-border bg-muted/20 p-4">
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-2">
                      <BarChart3 className="w-4 h-4 text-brand" /> Summary
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {String(selectedDetails.summary || "No summary saved.")}
                    </p>
                    {"duration" in selectedDetails && (
                      <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" /> Duration: {Math.round(Number(selectedDetails.duration || 0) / 60)} min
                      </p>
                    )}
                  </div>

                  {Array.isArray(selectedDetails.evaluations) && selectedDetails.evaluations.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="text-sm font-bold">Per-question evaluations</h3>
                      {(selectedDetails.evaluations as Array<Record<string, unknown>>).map((ev, index) => (
                        <div key={index} className="rounded-xl border border-border p-4 bg-muted/10">
                          <p className="text-xs text-muted-foreground mb-1">Q{Number(ev.question_number || index + 1)}</p>
                          <p className="text-sm font-semibold mb-1">{String(ev.question || "Untitled question")}</p>
                          <p className="text-sm text-muted-foreground mb-1">
                            Score {Number(ev.score || 0)}/100 • {String(ev.grade || "N/A")}
                          </p>
                          <p className="text-sm text-muted-foreground">{String(ev.feedback || "No feedback saved.")}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
        </>
    </div>
  );
}
