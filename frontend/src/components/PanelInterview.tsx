/**
 * Module 13: AI Panel Interview — a live, multi-persona hiring panel.
 *
 * Three distinct AI personas (Hiring Manager, Tech Lead, People & Culture) each
 * react to the candidate's answers in their own voice, then hold a visible
 * DELIBERATION and cast a weighted hire / no-hire verdict.
 *
 * Self-contained showcase: paste a question + answer, watch the panel come
 * alive. Reuses the backend /api/v1/panel/* endpoints and the accent-aware
 * /tts/speak endpoint for distinct per-persona voices.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Users,
  Volume2,
  Loader2,
  Gavel,
  ThumbsUp,
  ThumbsDown,
  Scale,
  Sparkles,
  MessageSquarePlus,
  Send,
} from "lucide-react";
import {
  fetchPanelPersonas,
  fetchPanelReaction,
  fetchPanelDeliberation,
  textToSpeech,
  playAudioWithFeedback,
  type PanelPersona,
  type PanelReaction,
  type PanelDeliberation,
  type PanelTranscriptItem,
} from "../lib/api";

interface QaRow {
  question: string;
  answer: string;
}

const IMPRESSION_STYLES: Record<string, string> = {
  impressed:
    "bg-success/15 border-success/25 text-success",
  neutral:
    "bg-[#F9F9F9] border-border text-muted-foreground",
  unconvinced:
    "bg-destructive/15 border-destructive/25 text-destructive",
};

const VOTE_META: Record<
  string,
  { label: string; className: string; Icon: typeof ThumbsUp }
> = {
  hire: { label: "Hire", className: "text-success", Icon: ThumbsUp },
  no_hire: { label: "No Hire", className: "text-destructive", Icon: ThumbsDown },
  borderline: { label: "Borderline", className: "text-amber-500", Icon: Scale },
};

export default function PanelInterview() {
  const [personas, setPersonas] = useState<PanelPersona[]>([]);
  const [candidateName, setCandidateName] = useState("Candidate");
  const [question, setQuestion] = useState(
    "Tell me about a time you scaled a system under pressure.",
  );
  const [answer, setAnswer] = useState("");
  const [rows, setRows] = useState<QaRow[]>([]);
  const [reactions, setReactions] = useState<Record<string, PanelReaction>>({});
  const [reactingId, setReactingId] = useState<string | null>(null);
  const [deliberation, setDeliberation] = useState<PanelDeliberation | null>(
    null,
  );
  const [deliberating, setDeliberating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [speakingId, setSpeakingId] = useState<string | null>(null);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    fetchPanelPersonas()
      .then((p) => mountedRef.current && setPersonas(p))
      .catch(() => setError("Could not load the panel. Is the backend running?"));
  }, []);

  const transcript: PanelTranscriptItem[] = useMemo(
    () => rows.map((r) => ({ question: r.question, answer: r.answer })),
    [rows],
  );

  const speak = async (persona: PanelPersona, text: string) => {
    if (!text.trim()) return;
    try {
      setSpeakingId(persona.id);
      const blob = await textToSpeech(text, undefined, persona.accent);
      await playAudioWithFeedback(blob);
    } catch {
      /* voice is best-effort — never block the UI */
    } finally {
      if (mountedRef.current) setSpeakingId(null);
    }
  };

  const askPanel = async () => {
    if (!answer.trim() || !question.trim()) return;
    setError(null);
    setReactions({});
    setDeliberation(null);

    // Persist this Q/A into the running transcript for the final deliberation.
    setRows((prev) => [...prev, { question, answer }]);

    // Fan out to each persona sequentially so their voices don't overlap.
    for (const persona of personas) {
      try {
        setReactingId(persona.id);
        const r = await fetchPanelReaction({
          persona_id: persona.id,
          question,
          answer,
        });
        if (!mountedRef.current) return;
        setReactions((prev) => ({ ...prev, [persona.id]: r }));
        await speak(persona, r.follow_up ? `${r.reaction} ${r.follow_up}` : r.reaction);
      } catch {
        setError("A panelist could not respond. Try again.");
      } finally {
        if (mountedRef.current) setReactingId(null);
      }
    }
    setAnswer("");
  };

  const runDeliberation = async () => {
    if (transcript.length === 0) {
      setError("Answer at least one question before the panel deliberates.");
      return;
    }
    setError(null);
    setDeliberating(true);
    try {
      const result = await fetchPanelDeliberation({
        candidate_name: candidateName || "Candidate",
        transcript,
      });
      if (mountedRef.current) setDeliberation(result);
    } catch {
      setError("Deliberation failed. Try again.");
    } finally {
      if (mountedRef.current) setDeliberating(false);
    }
  };

  const decisionTone = (decision: string) =>
    decision === "HIRE"
      ? "text-success"
      : decision === "NO HIRE"
        ? "text-destructive"
        : "text-amber-500";

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-primary/10 p-2.5 text-primary">
          <Users className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-xl font-extrabold tracking-tight">
            AI Panel Interview
          </h2>
          <p className="text-sm text-muted-foreground">
            Three AI interviewers. Distinct voices. A live verdict you can defend.
          </p>
        </div>
      </div>

      {/* Panelist cards */}
      <div className="grid gap-3 sm:grid-cols-3">
        {personas.map((p) => {
          const r = reactions[p.id];
          const busy = reactingId === p.id;
          const impressionClass =
            (r && IMPRESSION_STYLES[r.impression]) || IMPRESSION_STYLES.neutral;
          return (
            <motion.div
              key={p.id}
              layout
              className="relative flex flex-col rounded-2xl border border-border bg-white p-4 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <span className="text-2xl" aria-hidden>
                  {p.emoji}
                </span>
                <div className="min-w-0">
                  <div className="truncate text-sm font-bold">{p.name}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {p.role}
                  </div>
                </div>
                {speakingId === p.id && (
                  <Volume2 className="ml-auto h-4 w-4 animate-pulse text-primary" />
                )}
              </div>

              <div className="mt-3 min-h-[3.5rem] text-sm">
                {busy ? (
                  <span className="inline-flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" /> thinking…
                  </span>
                ) : r ? (
                  <AnimatePresence mode="wait">
                    <motion.p
                      key={r.reaction}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="leading-snug"
                    >
                      “{r.reaction}”
                    </motion.p>
                  </AnimatePresence>
                ) : (
                  <span className="text-xs italic text-muted-foreground">
                    {p.temperament}
                  </span>
                )}
              </div>

              {r?.follow_up && (
                <div className="mt-2 rounded-xl bg-primary/5 px-2.5 py-1.5 text-xs text-primary">
                  <MessageSquarePlus className="mr-1 inline h-3 w-3" />
                  {r.follow_up}
                </div>
              )}

              {r && (
                <div className="mt-3 flex items-center justify-between">
                  <span
                    className={`inline-flex items-center gap-1 rounded-lg border px-2 py-0.5 text-[11px] font-semibold ${impressionClass}`}
                  >
                    {r.impression}
                  </span>
                  <button
                    type="button"
                    onClick={() => speak(p, r.reaction)}
                    className="text-muted-foreground transition hover:text-primary"
                    title="Replay voice"
                  >
                    <Volume2 className="h-4 w-4" />
                  </button>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Ask box */}
      <div className="space-y-3 rounded-2xl border border-border bg-white p-4 shadow-sm">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-xs font-semibold text-muted-foreground">
            Candidate
            <input
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-border bg-[#F9F9F9] px-3 py-2 text-sm font-normal text-foreground outline-none focus:border-primary"
            />
          </label>
          <label className="text-xs font-semibold text-muted-foreground">
            Question
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="mt-1 w-full rounded-xl border border-border bg-[#F9F9F9] px-3 py-2 text-sm font-normal text-foreground outline-none focus:border-primary"
            />
          </label>
        </div>
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          rows={3}
          placeholder="Type the candidate's answer…"
          className="w-full resize-none rounded-xl border border-border bg-[#F9F9F9] px-3 py-2 text-sm outline-none focus:border-primary"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={askPanel}
            disabled={!answer.trim() || reactingId !== null}
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {reactingId ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Submit to panel
          </button>
          <button
            type="button"
            onClick={runDeliberation}
            disabled={deliberating || transcript.length === 0}
            className="inline-flex items-center gap-2 rounded-xl border border-border px-4 py-2 text-sm font-semibold transition hover:bg-[#F9F9F9] disabled:opacity-50"
          >
            {deliberating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Gavel className="h-4 w-4" />
            )}
            Deliberate &amp; vote
          </button>
          <span className="text-xs text-muted-foreground">
            {transcript.length} answer{transcript.length === 1 ? "" : "s"} on record
          </span>
        </div>
        {error && <p className="text-xs font-medium text-destructive">{error}</p>}
      </div>

      {/* Deliberation */}
      <AnimatePresence>
        {deliberation && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4 rounded-2xl border border-border bg-white p-5 shadow-sm"
          >
            <div className="flex items-center gap-2">
              <Gavel className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-extrabold">Panel Deliberation</h3>
              <Sparkles className="h-4 w-4 text-primary" />
            </div>

            <div className="space-y-3">
              {deliberation.members.map((m, i) => {
                const meta = VOTE_META[m.vote] ?? VOTE_META.borderline;
                return (
                  <motion.div
                    key={m.persona_id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.25 }}
                    className="rounded-xl border border-border bg-[#F9F9F9] p-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg" aria-hidden>
                        {m.emoji}
                      </span>
                      <span className="text-sm font-bold">{m.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {m.role}
                      </span>
                      <span
                        className={`ml-auto inline-flex items-center gap-1 text-sm font-bold ${meta.className}`}
                      >
                        <meta.Icon className="h-4 w-4" />
                        {meta.label}
                        <span className="text-xs font-medium text-muted-foreground">
                          ({m.confidence}%)
                        </span>
                      </span>
                    </div>
                    <p className="mt-1.5 text-sm leading-snug text-foreground">
                      “{m.argument}”
                    </p>
                  </motion.div>
                );
              })}
            </div>

            {/* Verdict */}
            <motion.div
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: deliberation.members.length * 0.25 + 0.1 }}
              className="rounded-2xl border-2 border-primary/20 bg-primary/5 p-4 text-center"
            >
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Verdict
              </div>
              <div
                className={`mt-1 text-3xl font-black tracking-tight ${decisionTone(
                  deliberation.verdict.decision,
                )}`}
              >
                {deliberation.verdict.decision}
              </div>
              <div className="mt-1 text-sm text-muted-foreground">
                {deliberation.verdict.hire_votes}/
                {deliberation.verdict.total_votes} lean hire · panel confidence{" "}
                <span className="font-bold text-foreground">
                  {deliberation.verdict.confidence}%
                </span>{" "}
                · avg answer score {deliberation.average_score}/100
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
