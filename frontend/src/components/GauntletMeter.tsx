import { m as motion } from "framer-motion";
import { Flame, ShieldAlert } from "lucide-react";
import type { GauntletPersona } from "@/lib/api";

const LEVEL_LABELS = [
  "",
  "Warm-up",
  "Steady",
  "Heating Up",
  "Under Pressure",
  "Full Gauntlet",
];

const LEVEL_TONES = [
  "",
  "bg-slate-400",
  "bg-brand",
  "bg-amber-500",
  "bg-orange-500",
  "bg-destructive",
];

const LEVEL_TEXT = [
  "",
  "text-slate-400",
  "text-brand",
  "text-amber-500",
  "text-orange-500",
  "text-destructive",
];

export interface GauntletMeterProps {
  level: number;
  persona?: GauntletPersona | null;
  enabled: boolean;
}

export default function GauntletMeter({
  level,
  persona,
  enabled,
}: GauntletMeterProps) {
  if (!enabled) return null;

  const clamped = Math.min(5, Math.max(1, level));

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-2 flex flex-wrap items-center gap-3 rounded-xl border border-orange-500/20 bg-gradient-to-r from-orange-500/5 via-card to-card px-4 py-2.5 shadow-sm"
    >
      <div className="flex items-center gap-1.5">
        <Flame
          className={`w-4 h-4 ${LEVEL_TEXT[clamped]} transition-colors`}
        />
        <div className="flex items-end gap-1">
          {[1, 2, 3, 4, 5].map((segment) => (
            <motion.div
              key={segment}
              initial={{ scaleY: 0.3 }}
              animate={{ scaleY: 1 }}
              transition={{ delay: segment * 0.05, duration: 0.25 }}
              className={`w-1.5 rounded-full origin-bottom transition-colors duration-500 ${
                segment <= clamped
                  ? LEVEL_TONES[clamped]
                  : "bg-muted-foreground/20"
              }`}
              style={{ height: 6 + segment * 3 }}
            />
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2 min-w-0">
        <span
          className={`text-[11px] font-bold uppercase tracking-wider ${LEVEL_TEXT[clamped]}`}
        >
          Gauntlet · {LEVEL_LABELS[clamped]}
        </span>
        {persona && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-card border border-border text-[11px] text-muted-foreground">
            {persona.emoji} {persona.name}
          </span>
        )}
      </div>

      {clamped >= 4 && (
        <span className="ml-auto hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold text-destructive/80">
          <ShieldAlert className="w-3 h-3" /> No mercy from here
        </span>
      )}
    </motion.div>
  );
}
