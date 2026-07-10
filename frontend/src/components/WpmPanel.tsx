import { useMemo } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import { Gauge } from "lucide-react";
import type { PaceLabel, WpmSnapshot, FillerWordCount } from "@/lib/interviewPace";

interface WpmPanelProps {
  liveWpm: number | null;
  paceLabel: PaceLabel;
  wpmHistory: WpmSnapshot[];
  fillerWords: FillerWordCount[];
  totalWords: number;
}

/* ── colour helpers ──────────────────────────────────────── */

function getBorderColor(label: PaceLabel) {
  if (label === "ideal") return "#22c55e";
  if (label === "slightly_fast" || label === "slightly_slow") return "#f59e0b";
  if (label === "too_fast" || label === "too_slow") return "#ef4444";
  return "#000";
}

function getCornerDotColor(label: PaceLabel) {
  if (label === "ideal") return "bg-green-400";
  if (label === "slightly_fast" || label === "slightly_slow")
    return "bg-amber-400";
  if (label === "too_fast" || label === "too_slow") return "bg-red-400";
  return "bg-black/30";
}

function getPaceLabelText(label: PaceLabel) {
  if (label === "ideal") return "Ideal pace";
  if (label === "slightly_fast") return "Slightly fast";
  if (label === "slightly_slow") return "Slightly slow";
  if (label === "too_fast") return "Too fast";
  if (label === "too_slow") return "Too slow";
  return "Waiting";
}

function barColor(snapshot: WpmSnapshot) {
  if (snapshot.fillerCount >= 2) return "bg-[#000]";
  if (snapshot.fillerCount === 1) return "bg-black/40";
  return "bg-black/10";
}

function barTooltip(snapshot: WpmSnapshot) {
  if (snapshot.fillerCount >= 2) return `${snapshot.wpm} WPM · ${snapshot.fillerCount} fillers`;
  if (snapshot.fillerCount === 1) return `${snapshot.wpm} WPM · 1 filler`;
  return `${snapshot.wpm} WPM`;
}

/* ── component ───────────────────────────────────────────── */

export default function WpmPanel({
  liveWpm,
  paceLabel,
  wpmHistory,
  fillerWords,
  totalWords,
}: WpmPanelProps) {
  const displayWpm = liveWpm ?? 0;
  const borderColor = getBorderColor(paceLabel);
  const cornerDot = getCornerDotColor(paceLabel);
  const paceLabelTxt = getPaceLabelText(paceLabel);

  /* take last 8 history snapshots for the bar chart */
  const bars = useMemo(() => {
    const slice = wpmHistory.slice(-8);
    if (slice.length === 0) return [];
    const maxWpm = Math.max(...slice.map((s) => s.wpm), 1);
    return slice.map((s) => ({
      ...s,
      heightPct: Math.max(15, Math.round((s.wpm / maxWpm) * 100)),
    }));
  }, [wpmHistory]);

  /* top 3 filler words for the bars */
  const topFillers = useMemo(() => fillerWords.slice(0, 3), [fillerWords]);

  const totalFillers = useMemo(
    () => fillerWords.reduce((s, f) => s + f.count, 0),
    [fillerWords],
  );

  const fillerRatio = totalWords > 0 ? Math.min(totalFillers / totalWords, 1) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-black/10 bg-white shadow-sm overflow-hidden select-none"
    >
      {/* Header row */}
      <div className="flex items-center gap-3 px-4 pt-4 pb-2">
        <div className="flex items-center gap-2">
          <Gauge className="w-3.5 h-3.5 text-black/40" />
          <span className="text-[10px] font-bold text-black/40 tracking-wider uppercase">
            Speech Pace
          </span>
        </div>
        <AnimatePresence mode="wait">
          <motion.span
            key={paceLabelTxt}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="ml-auto text-[9px] font-semibold px-2 py-0.5 rounded-lg"
            style={{
              backgroundColor: `${borderColor}18`,
              color: borderColor,
              border: `1px solid ${borderColor}30`,
            }}
          >
            {paceLabelTxt}
          </motion.span>
        </AnimatePresence>
      </div>

      {/* WPM box + bar chart */}
      <div className="flex gap-3 px-4 pb-3">
        {/* Big WPM counter */}
        <div
          className="w-14 h-14 rounded-xl flex flex-col items-center justify-center font-bold shrink-0 relative overflow-hidden bg-[#FAFAFA] transition-colors duration-300"
          style={{ border: `3px solid ${borderColor}` }}
        >
          <AnimatePresence mode="wait">
            <motion.span
              key={displayWpm}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              className="text-lg leading-none mb-0.5 text-black"
            >
              {liveWpm !== null ? displayWpm : "--"}
            </motion.span>
          </AnimatePresence>
          <span className="text-[7px] text-black/60 font-semibold tracking-widest">
            WPM
          </span>
          <div className={`absolute top-0 right-0 w-2 h-2 ${cornerDot} rounded-bl-lg transition-colors duration-300`} />
        </div>

        {/* Bars */}
        <div className="flex-1 flex gap-1 items-end h-14 pb-0.5">
          {bars.length > 0
            ? bars.map((b, i) => (
                <div
                  key={i}
                  className="relative w-full group"
                  style={{ height: "100%" }}
                >
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${b.heightPct}%` }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className={`w-full absolute bottom-0 rounded-t-sm transition-all ${barColor(b)} group-hover:opacity-80`}
                  />
                  {/* Tooltip */}
                  <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-[#000] text-white text-[8px] font-semibold px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-xl pointer-events-none z-10">
                    {barTooltip(b)}
                  </div>
                </div>
              ))
            : /* empty placeholder bars */
              Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="w-full h-full flex items-end"
                >
                  <div
                    className="w-full bg-black/5 rounded-t-sm"
                    style={{ height: `${15 + Math.random() * 25}%` }}
                  />
                </div>
              ))}
        </div>
      </div>

      {/* Filler word analysis */}
      <div className="bg-[#FAFAFA] border-t border-black/5 px-4 py-3 flex flex-col gap-2">
        <div className="text-[9px] font-bold text-black/40 tracking-wider">
          FILLER WORD ANALYSIS
        </div>

        {topFillers.length > 0 ? (
          topFillers.map((f) => (
            <div key={f.word} className="flex items-center gap-2">
              <span className="text-[10px] font-semibold text-black/60 w-16 truncate">
                "{f.word}"
              </span>
              <div className="flex-1 h-2 bg-black/5 rounded-xl overflow-hidden shadow-inner">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.min((f.count / Math.max(totalWords, 1)) * 100 * 10, 100)}%`,
                  }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className={`h-full rounded-r-xl ${f.count >= 3 ? "bg-[#000]" : "bg-black/40"}`}
                />
              </div>
              <span className="text-[9px] font-mono font-semibold text-black/50 w-6 text-right">
                {f.count}×
              </span>
            </div>
          ))
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-black/30 italic">
              No fillers detected yet
            </span>
            <div className="flex-1 h-2 bg-black/5 rounded-xl shadow-inner" />
          </div>
        )}

        {/* Total ratio bar */}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[9px] font-semibold text-black/40 w-16">
            Total
          </span>
          <div className="flex-1 h-2 bg-black/5 rounded-xl overflow-hidden shadow-inner">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.round(fillerRatio * 100)}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="h-full rounded-r-xl bg-black/20"
            />
          </div>
          <span className="text-[9px] font-mono font-semibold text-black/40 w-6 text-right">
            {totalFillers}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
