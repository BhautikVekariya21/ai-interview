import { useCallback, useEffect, useState } from "react";
import { Loader2, Swords, Copy, Check, Plus, Search, Trophy } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Seo from "@/components/Seo";
import {
  createPeerMatch,
  fetchPeerMatch,
  joinPeerMatch,
  submitPeerScore,
  type PeerMatchView,
} from "@/lib/api";

const MODES = [
  { id: "behavioral", label: "Behavioral" },
  { id: "coding", label: "Coding" },
  { id: "mixed", label: "Mixed" },
] as const;

/** Where each player's secret token + side for a match lives between visits. */
const TOKEN_STORE_KEY = "peer-play-tokens";

function loadTokens(): Record<string, { token: string; side: "p1" | "p2" }> {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_STORE_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveToken(code: string, token: string, side: "p1" | "p2") {
  const tokens = {
    ...loadTokens(),
    [code.toUpperCase()]: { token, side },
  };
  localStorage.setItem(TOKEN_STORE_KEY, JSON.stringify(tokens));
}

export default function PeerPlayPage() {
  const [name, setName] = useState("");
  const [mode, setMode] = useState<string>("mixed");
  const [joinCode, setJoinCode] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return (params.get("code") || "").toUpperCase();
  });
  const [creating, setCreating] = useState(false);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [match, setMatch] = useState<PeerMatchView | null>(null);
  const [myToken, setMyToken] = useState<string | null>(null);
  const [mySide, setMySide] = useState<"p1" | "p2" | null>(null);
  const [myScore, setMyScore] = useState<number | "">("");
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);

  const refreshMatch = useCallback(async (code: string) => {
    try {
      const view = await fetchPeerMatch(code);
      setMatch(view);
    } catch {
      setError("Match not found or expired. Matches last 6 hours.");
      setMatch(null);
    }
  }, []);

  // Restore my token + fetch state when a code is known.
  useEffect(() => {
    if (!joinCode) return;
    const mine = loadTokens()[joinCode];
    setMyToken(mine?.token ?? null);
    setMySide(mine?.side ?? null);
    refreshMatch(joinCode);
  }, [joinCode, refreshMatch]);

  const create = async () => {
    setCreating(true);
    setError(null);
    try {
      const result = await createPeerMatch(name || "Player 1", mode);
      saveToken(result.code, result.player_token, "p1");
      setJoinCode(result.code);
      setMyToken(result.player_token);
      setMySide("p1");
      await refreshMatch(result.code);
    } catch {
      setError("Could not create the match. Is the backend running?");
    } finally {
      setCreating(false);
    }
  };

  const join = async () => {
    setJoining(true);
    setError(null);
    try {
      const result = await joinPeerMatch(joinCode, name || "Player 2");
      saveToken(result.code, result.player_token, "p2");
      setMyToken(result.player_token);
      setMySide("p2");
      await refreshMatch(result.code);
    } catch (e) {
      setError(e instanceof Error && e.message.includes("400") ? "Open match not found — it may already be full or expired." : "Could not join the match.");
    } finally {
      setJoining(false);
    }
  };

  const submit = async () => {
    if (!match || !myToken || myScore === "") return;
    setSubmitting(true);
    setError(null);
    try {
      await submitPeerScore(match.code, myToken, Number(myScore));
      await refreshMatch(match.code);
    } catch {
      setError("Score submit failed — check your score is 0-100 and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const copyCode = async () => {
    if (!match) return;
    try {
      await navigator.clipboard.writeText(match.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard unavailable
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Seo
        title="Peer Play — mock interview vs a friend"
        description="Challenge a friend to a head-to-head mock interview. Submit scores, get an Elo-style verdict with rating deltas for both sides."
      />
      <main className="mx-auto w-full max-w-[760px] px-6 pb-16 pt-28">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-brand mb-3">
            <Swords className="w-3.5 h-3.5" /> interviewer.ai · Peer Play
          </div>
          <h1 className="text-3xl md:text-4xl font-sans font-bold tracking-tight mb-3">
            Mock interview vs. a friend
          </h1>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Create a match, share the code in chat, both run the same interview, then
            submit your scores. Get an Elo-style verdict with rating deltas for both of you.
          </p>
        </div>

        {error && (
          <p className="rounded-xl border border-destructive/40 bg-destructive/10 text-destructive text-sm px-4 py-3 mb-6">
            {error}
          </p>
        )}

        {!match ? (
          <div className="grid gap-6 md:grid-cols-2 items-start">
            {/* Create */}
            <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h2 className="flex items-center gap-2 font-semibold mb-3">
                <Plus className="w-4 h-4 text-brand" /> Create a match
              </h2>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                maxLength={64}
                className="w-full rounded-xl border border-border bg-background p-3 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <div className="flex gap-2 mb-4">
                {MODES.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setMode(m.id)}
                    className={`rounded-full border px-3 py-1.5 text-xs transition ${
                      mode === m.id
                        ? "border-brand bg-brand/10 text-brand font-semibold"
                        : "border-border text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <Button className="w-full" onClick={create} disabled={creating}>
                {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create & get code"}
              </Button>
            </div>

            {/* Join */}
            <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h2 className="flex items-center gap-2 font-semibold mb-3">
                <Search className="w-4 h-4 text-brand" /> Join with a code
              </h2>
              <input
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="6-character code"
                maxLength={8}
                className="w-full rounded-xl border border-border bg-background p-3 text-sm font-mono tracking-widest uppercase mb-3 focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <Button className="w-full" variant="outline" onClick={join} disabled={joining || joinCode.length < 6}>
                {joining ? <Loader2 className="w-4 h-4 animate-spin" /> : "Join match"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            {match.status !== "complete" && (
              <div className="flex items-center justify-between mb-5">
                <div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Match code — share it with your friend
                  </div>
                  <div className="text-3xl font-mono font-bold tracking-widest text-brand">
                    {match.code}
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={copyCode}>
                  {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                  {copied ? "Copied" : "Copy"}
                </Button>
              </div>
            )}

            {/* Players + scores */}
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-4 mb-2">
              {[0, 1].map((idx) => {
                const side = idx === 0 ? "p1" : "p2";
                const name = match.players[side] ?? "—";
                const score = match.scores[side];
                const isMe = mySide === side;
                const delta = match.verdict
                  ? side === "p1"
                    ? match.verdict.p1_delta
                    : match.verdict.p2_delta
                  : null;
                return (
                  <div
                    key={side}
                    className={`rounded-xl border p-4 text-center ${
                      match.verdict?.winner === side
                        ? "border-brand bg-brand/5"
                        : "border-border"
                    }`}
                  >
                    <div className="font-semibold text-sm truncate">{name}</div>
                    <div className="text-4xl font-bold mt-2">{score ?? "–"}</div>
                    {delta != null && (
                      <div
                        className={`text-xs mt-1 font-semibold ${
                          delta >= 0 ? "text-emerald-500" : "text-rose-500"
                        }`}
                      >
                        {delta >= 0 ? "+" : ""}
                        {delta} rating
                      </div>
                    )}
                    <div className="text-[10px] text-muted-foreground mt-2">
                      {isMe ? "you" : ""}
                    </div>
                  </div>
                );
              })}
              <Swords className="w-5 h-5 text-muted-foreground" />
            </div>

            <div className="text-center text-xs text-muted-foreground mb-5">
              format: {match.mode} · expires in {match.expires_hours}h
            </div>

            {match.status === "complete" && match.verdict ? (
              <div className="rounded-xl bg-brand/5 border border-brand/30 p-4 text-center">
                <Trophy className="w-6 h-6 mx-auto text-brand mb-2" />
                <div className="font-bold">{match.verdict.headline}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {match.verdict.winner === "tie"
                    ? "Evenly matched — run a rematch to break the tie."
                    : `Decided by ${match.verdict.margin} points.`}
                </div>
              </div>
            ) : (
              <div className="rounded-xl bg-muted/40 border border-border p-4">
                {match.status === "waiting" && (
                  <p className="text-sm text-muted-foreground text-center mb-3">
                    Waiting for your friend to join with code{" "}
                    <span className="font-mono font-bold text-brand">{match.code}</span>
                  </p>
                )}
                {mySide && match.status !== "waiting" && (
                  <div className="flex items-end gap-3">
                    <div className="flex-1">
                      <label className="text-xs text-muted-foreground block mb-1">
                        Your interview score (0-100)
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={myScore}
                        onChange={(e) =>
                          setMyScore(e.target.value === "" ? "" : Number(e.target.value))
                        }
                        placeholder="e.g. 82"
                        className="w-full rounded-lg border border-border bg-background p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                    </div>
                    <Button onClick={submit} disabled={submitting || myScore === ""}>
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Submit score"}
                    </Button>
                  </div>
                )}
                {match.status !== "waiting" && !mySide && match.joined && (
                  <p className="text-sm text-muted-foreground text-center">
                    Match is full — waiting for both players to submit scores.
                  </p>
                )}
              </div>
            )}

            <div className="text-center mt-5">
              <button
                type="button"
                className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
                onClick={() => {
                  setMatch(null);
                  setJoinCode("");
                  setMyToken(null);
                  setMyScore("");
                  setError(null);
                }}
              >
                ← start / join another match
              </button>
            </div>
          </div>
        )}

        <p className="text-center text-xs text-muted-foreground mt-8">
          Tip: pair this with the live interview on{" "}
          <Link to="/app/interview" className="underline underline-offset-2 hover:text-foreground">
            /app/interview
          </Link>{" "}
          — run the same questions, then compare scores here.
        </p>
      </main>
    </div>
  );
}
