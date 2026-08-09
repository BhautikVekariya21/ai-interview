import { useEffect, useState } from "react";
import { m as motion } from "framer-motion";
import {
  Trophy,
  Loader2,
  Crown,
  Medal,
  Swords,
  TrendingUp,
  TrendingDown,
  Minus,
  Info,
  Gamepad2,
} from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import {
  getLeagueLeaderboard,
  getLeagueRating,
  type LeaderboardEntry,
  type LeagueRatingResult,
} from "@/lib/api";

const TIER_MEDALS: Record<string, React.ReactNode> = {
  Diamond: <Crown className="w-3.5 h-3.5" />,
  Platinum: <Medal className="w-3.5 h-3.5" />,
  Gold: <Medal className="w-3.5 h-3.5" />,
  Silver: <Medal className="w-3.5 h-3.5" />,
  Bronze: <Medal className="w-3.5 h-3.5" />,
};

function RankIcon({ rank }: { rank: number }) {
  if (rank === 1)
    return (
      <span className="w-6 h-6 rounded-lg bg-amber-400/15 text-amber-500 border border-amber-400/30 flex items-center justify-center text-[11px] font-extrabold">
        <Crown className="w-3 h-3" />
      </span>
    );
  if (rank === 2)
    return (
      <span className="w-6 h-6 rounded-lg bg-slate-300/15 text-slate-400 border border-slate-300/30 flex items-center justify-center text-[11px] font-extrabold">
        2
      </span>
    );
  if (rank === 3)
    return (
      <span className="w-6 h-6 rounded-lg bg-orange-400/15 text-orange-500 border border-orange-400/30 flex items-center justify-center text-[11px] font-extrabold">
        3
      </span>
    );
  return (
    <span className="w-6 h-6 rounded-lg bg-muted border border-border flex items-center justify-center text-[11px] font-bold text-muted-foreground">
      {rank}
    </span>
  );
}

export default function LeagueLeaderboard() {
  const { isAuthenticated } = useAuth();
  const [myRating, setMyRating] = useState<LeagueRatingResult | null>(null);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([
      getLeagueRating().catch(() => null),
      getLeagueLeaderboard(10).catch(() => null),
    ])
      .then(([rating, board]) => {
        if (cancelled) return;
        setMyRating(rating);
        setEntries(board?.entries ?? []);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  if (!isAuthenticated) return null;

  // Per-submission rating deltas, oldest first (the backend sends the last 10).
  // The final entry is how the rating moved after the most recent submission.
  const lastDeltas = myRating?.last_deltas ?? [];
  const lastDelta =
    lastDeltas.length > 0 ? lastDeltas[lastDeltas.length - 1] : null;

  const deltaTone =
    lastDelta === null
      ? "bg-muted text-muted-foreground border border-border"
      : lastDelta > 0
        ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/25"
        : lastDelta < 0
          ? "bg-rose-500/10 text-rose-600 border border-rose-500/25"
          : "bg-muted text-muted-foreground border border-border";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="rounded-2xl border border-border bg-card p-5 shadow-sm"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold flex items-center gap-2 text-foreground">
          <Swords className="w-4 h-4 text-brand" /> Interview League
        </h3>
        <span className="text-[11px] text-muted-foreground">
          ELO over graded coding problems
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin text-brand" />
          Computing league ratings…
        </div>
      )}

      {!loading && !myRating && entries.length === 0 && (
        <div className="text-center py-6">
          <Trophy className="w-8 h-8 text-muted-foreground/50 mx-auto mb-3" />
          <p className="text-sm font-semibold text-foreground mb-1">
            No league data yet
          </p>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto leading-relaxed">
            Submit solutions in the code sandbox and your ELO rating will be
            computed automatically — every pass or fail moves you against the
            difficulty of the problem.
          </p>
        </div>
      )}

      {!loading && myRating && (
        <div className="flex items-center gap-4 rounded-xl border border-border bg-muted/20 p-4 mb-4">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0"
            style={{
              background: `${myRating.tier.color}1A`,
              border: `1px solid ${myRating.tier.color}40`,
            }}
          >
            <TrendingUp className="w-6 h-6" style={{ color: myRating.tier.color }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-2xl font-extrabold font-mono text-foreground leading-none">
                {myRating.rating}
              </p>
              <span
                className="px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wide"
                style={{
                  color: myRating.tier.color,
                  background: `${myRating.tier.color}1A`,
                }}
              >
                {myRating.tier.tier} · {myRating.tier.label}
              </span>
              {myRating.provisional && (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-muted border border-border text-muted-foreground text-[10px] font-bold uppercase tracking-wide"
                  title="Provisional rating — fewer than 3 graded submissions, so this number can still swing a lot. It stabilises after your third submission."
                >
                  <Info className="w-3 h-3" /> Provisional
                </span>
              )}
              {lastDelta !== null && (
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[11px] font-extrabold font-mono ${deltaTone}`}
                  title="Rating change from your last graded submission"
                >
                  {lastDelta > 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : lastDelta < 0 ? (
                    <TrendingDown className="w-3 h-3" />
                  ) : (
                    <Minus className="w-3 h-3" />
                  )}
                  {lastDelta > 0
                    ? `+${lastDelta}`
                    : lastDelta === 0
                      ? "±0"
                      : `${lastDelta}`}
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {myRating.games} submission{myRating.games !== 1 ? "s" : ""} ·{" "}
              {myRating.wins} win{myRating.wins !== 1 ? "s" : ""} ·{" "}
              {myRating.win_rate}% win rate
            </p>
            {lastDeltas.length > 1 && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Recent form
                </span>
                <div className="flex items-end gap-[3px] h-5" title="Last 10 submissions' rating deltas">
                  {lastDeltas.map((delta, index) => (
                    <span
                      key={index}
                      title={
                        delta > 0 ? `+${delta}` : delta === 0 ? "±0" : `${delta}`
                      }
                      className={`w-1 rounded-sm ${
                        delta > 0
                          ? "bg-emerald-500/80"
                          : delta < 0
                            ? "bg-rose-500/80"
                            : "bg-muted-foreground/40"
                      }`}
                      style={{
                        height: `${Math.max(4, Math.min(20, Math.abs(delta) * 0.6))}px`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {entries.length > 0 && (
        <div className="space-y-1.5">
          {entries.map((entry) => (
            <div
              key={entry.user_id}
              className="flex items-center gap-3 rounded-lg border border-border bg-card/60 px-3 py-2"
            >
              <RankIcon rank={entry.rank} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground truncate">
                  {entry.name}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {entry.games} games · {entry.win_rate}% wins
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-extrabold font-mono text-foreground">
                  {entry.rating}
                  {entry.provisional && (
                    <span
                      className="ml-0.5 text-[10px] font-bold text-muted-foreground align-super"
                      title="Provisional rating — fewer than 3 graded submissions"
                    >
                      ?
                    </span>
                  )}
                </p>
                <span
                  className="text-[10px] font-bold uppercase tracking-wide"
                  style={{ color: entry.tier.color }}
                >
                  {TIER_MEDALS[entry.tier.tier] ?? <Gamepad2 className="w-3 h-3 inline -mt-0.5" />}{" "}
                  {entry.tier.tier}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
