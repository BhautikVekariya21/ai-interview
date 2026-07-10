import { useState, useEffect, useRef, useCallback } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import { Timer, Play, Pause, RotateCcw, Settings2, X, Coffee, Zap } from "lucide-react";
import { toast } from "sonner";

type Mode = "focus" | "break";

const DEFAULT_FOCUS = 25 * 60; // 25 min
const DEFAULT_BREAK = 5 * 60;  // 5 min

export default function StudyTimer() {
  const [isOpen, setIsOpen] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [mode, setMode] = useState<Mode>("focus");
  const [timeLeft, setTimeLeft] = useState(DEFAULT_FOCUS);
  const [focusDuration, setFocusDuration] = useState(DEFAULT_FOCUS);
  const [breakDuration, setBreakDuration] = useState(DEFAULT_BREAK);
  const [sessions, setSessions] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  // Tick
  useEffect(() => {
    if (isRunning && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(t => t - 1);
      }, 1000);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [isRunning, timeLeft]);

  // Timer completed
  useEffect(() => {
    if (timeLeft <= 0 && isRunning) {
      setIsRunning(false);
      if (mode === "focus") {
        setSessions(s => s + 1);
        toast.success("🎉 Focus session complete! Take a break.");
        setMode("break");
        setTimeLeft(breakDuration);
      } else {
        toast.info("Break's over! Ready for another focus session?");
        setMode("focus");
        setTimeLeft(focusDuration);
      }
    }
  }, [timeLeft, isRunning, mode, focusDuration, breakDuration]);

  const toggle = useCallback(() => setIsRunning(r => !r), []);
  const reset = useCallback(() => {
    setIsRunning(false);
    setTimeLeft(mode === "focus" ? focusDuration : breakDuration);
  }, [mode, focusDuration, breakDuration]);

  const switchMode = useCallback((m: Mode) => {
    setIsRunning(false);
    setMode(m);
    setTimeLeft(m === "focus" ? focusDuration : breakDuration);
  }, [focusDuration, breakDuration]);

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  const totalForMode = mode === "focus" ? focusDuration : breakDuration;
  const progress = totalForMode > 0 ? ((totalForMode - timeLeft) / totalForMode) * 100 : 0;

  // Minimized pill when running but collapsed
  if (!isOpen && isRunning) {
    return (
      <motion.button
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-24 right-6 z-50 flex items-center gap-2 rounded-full border border-primary/30 bg-card px-4 py-2 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
      >
        <div className={`w-2 h-2 rounded-full animate-pulse ${mode === "focus" ? "bg-primary" : "bg-success"}`} />
        <span className="text-sm font-bold font-mono text-foreground">
          {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
        </span>
      </motion.button>
    );
  }

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        className="fixed bottom-24 right-6 z-50 w-[280px] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Timer className="w-4 h-4 text-primary" />
            <span className="text-sm font-bold text-foreground">Study Timer</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-1.5 rounded-lg hover:bg-accent/20 text-muted-foreground hover:text-foreground transition-colors"
            >
              <Settings2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-lg hover:bg-accent/20 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {showSettings ? (
          /* Settings */
          <div className="p-4 space-y-3">
            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1 block">Focus Duration (min)</label>
              <input
                type="range" min={5} max={60} step={5}
                value={focusDuration / 60}
                onChange={e => { const v = parseInt(e.target.value) * 60; setFocusDuration(v); if (mode === "focus" && !isRunning) setTimeLeft(v); }}
                className="w-full accent-primary"
              />
              <span className="text-xs font-mono text-foreground">{focusDuration / 60} min</span>
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1 block">Break Duration (min)</label>
              <input
                type="range" min={1} max={15} step={1}
                value={breakDuration / 60}
                onChange={e => { const v = parseInt(e.target.value) * 60; setBreakDuration(v); if (mode === "break" && !isRunning) setTimeLeft(v); }}
                className="w-full accent-primary"
              />
              <span className="text-xs font-mono text-foreground">{breakDuration / 60} min</span>
            </div>
          </div>
        ) : (
          <div className="p-4">
            {/* Mode tabs */}
            <div className="flex gap-1 mb-4 p-1 rounded-xl bg-muted/50">
              <button
                onClick={() => switchMode("focus")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  mode === "focus" ? "bg-card shadow-sm text-primary" : "text-muted-foreground"
                }`}
              >
                <Zap className="w-3.5 h-3.5" /> Focus
              </button>
              <button
                onClick={() => switchMode("break")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  mode === "break" ? "bg-card shadow-sm text-success" : "text-muted-foreground"
                }`}
              >
                <Coffee className="w-3.5 h-3.5" /> Break
              </button>
            </div>

            {/* Timer display */}
            <div className="text-center mb-4">
              <div className="relative inline-block">
                <svg viewBox="0 0 100 100" className="w-32 h-32 -rotate-90">
                  <circle cx="50" cy="50" r="44" className="fill-none stroke-muted" strokeWidth="4" />
                  <circle
                    cx="50" cy="50" r="44"
                    className={`fill-none ${mode === "focus" ? "stroke-primary" : "stroke-success"}`}
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 44}
                    strokeDashoffset={2 * Math.PI * 44 * (1 - progress / 100)}
                    style={{ transition: "stroke-dashoffset 0.5s ease" }}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold font-mono text-foreground tracking-tight">
                    {String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
                  </span>
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${mode === "focus" ? "text-primary" : "text-success"}`}>
                    {mode}
                  </span>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={reset}
                className="p-2 rounded-xl border border-border bg-muted/50 text-muted-foreground hover:text-foreground hover:bg-accent/20 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={toggle}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${
                  isRunning
                    ? "bg-muted border border-border text-foreground"
                    : mode === "focus"
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                      : "bg-success text-white shadow-lg shadow-success/20"
                }`}
              >
                {isRunning ? (
                  <span className="flex items-center gap-1.5"><Pause className="w-4 h-4" /> Pause</span>
                ) : (
                  <span className="flex items-center gap-1.5"><Play className="w-4 h-4" /> Start</span>
                )}
              </button>
            </div>

            {/* Session count */}
            <p className="text-center text-[11px] text-muted-foreground mt-3">
              {sessions} focus sessions completed
            </p>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
