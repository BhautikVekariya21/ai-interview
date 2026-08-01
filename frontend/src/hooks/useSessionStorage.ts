import { useState, useEffect, useCallback } from "react";
import { getStoredAuthToken } from "@/lib/auth";
import { loadCloudSession, saveCloudSession } from "@/lib/api";
import { AppPage } from "@/lib/navigation";
import { getItem, setItem, removeItem } from "@/lib/indexedDB";

const SESSION_KEY = "interviewer_session";

export interface SessionData {
  activePage: AppPage;
  candidateName: string;
  resumeData?: Record<string, unknown>;
  generatedQuestions: {
    id: number;
    text: string;
    category: string;
    difficulty: string;
    problemId?: string;
  }[];
  interviewMessages?: { role: "ai" | "user"; text: string; timestamp: string }[];
  interviewQuestionIndex?: number;
  interviewTimer?: number;
  interviewResult?: {
    candidateName: string;
    totalQuestions: number;
    answeredQuestions: number;
    duration: number;
    messages: { role: "ai" | "user"; text: string }[];
    overallScore?: number;
    overallGrade?: string;
    summary?: string;
    evaluations?: Record<string, unknown>[];
    plagiarismSummary?: Record<string, unknown>;
  };
}

const getDefaultSession = (): SessionData => ({
  activePage: "upload",
  candidateName: "Candidate",
  generatedQuestions: [],
});

/**
 * The bank problems the question generator picked for this candidate, in the
 * order they will be asked.
 *
 * The code sandbox is a standalone route outside the dashboard tree, so it
 * cannot reach the session through `useSessionStorage`'s state. It reads the
 * persisted copy directly instead, which is what lets it open the candidate's
 * own problem rather than whichever one the bank happens to list first.
 */
export async function loadSelectedProblemIds(): Promise<string[]> {
  const stored = await getItem<SessionData>(SESSION_KEY);
  return (stored?.generatedQuestions ?? [])
    .map((q) => q.problemId)
    .filter((id): id is string => Boolean(id));
}

export function useSessionStorage() {
  const [session, setSession] = useState<SessionData>(getDefaultSession());
  const [localLoaded, setLocalLoaded] = useState(false);
  const [remoteLoaded, setRemoteLoaded] = useState(false);
  const [remoteSyncEnabled, setRemoteSyncEnabled] = useState(false);

  useEffect(() => {
    const token = getStoredAuthToken();
    if (!token) {
      setRemoteSyncEnabled(false);
      setRemoteLoaded(true);
      return;
    }
    loadCloudSession(token)
      .then((data) => {
        setRemoteSyncEnabled(true);
        if (data.session) {
          setSession((prev) => ({ ...prev, ...(data.session as unknown as SessionData) }));
        }
      })
      .catch(() => {
        setRemoteSyncEnabled(false);
        // Keep local session if cloud load fails.
      })
      .finally(() => setRemoteLoaded(true));
  }, []);

  useEffect(() => {
    getItem<SessionData>(SESSION_KEY).then((stored) => {
      if (stored) {
        setSession((prev) => ({ ...prev, ...stored }));
      }
      setLocalLoaded(true);
    });
  }, []);

  useEffect(() => {
    if (!localLoaded) return;

    const persist = () => {
      void setItem(SESSION_KEY, session);
    };
    persist();
    const onHidden = () => persist();
    window.addEventListener("beforeunload", onHidden);
    document.addEventListener("visibilitychange", onHidden);
    return () => {
      window.removeEventListener("beforeunload", onHidden);
      document.removeEventListener("visibilitychange", onHidden);
    };
  }, [session, localLoaded]);

  useEffect(() => {
    if (!remoteLoaded) return;
    const token = getStoredAuthToken();
    if (!token && !remoteSyncEnabled) return;

    const timeout = window.setTimeout(() => {
      void saveCloudSession(token, session as unknown as Record<string, unknown>).catch(() => {
        // Preserve local mode if sync fails.
      });
    }, 400);

    return () => window.clearTimeout(timeout);
  }, [session, remoteLoaded, remoteSyncEnabled]);

  const updateSession = useCallback((patch: Partial<SessionData>) => {
    setSession(prev => ({ ...prev, ...patch }));
  }, []);

  const clearSession = useCallback(() => {
    void removeItem(SESSION_KEY);
    setSession(getDefaultSession());
  }, []);

  return { session, updateSession, clearSession };
}
