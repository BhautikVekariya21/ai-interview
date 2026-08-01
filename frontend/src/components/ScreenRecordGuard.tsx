import { useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { MonitorUp, ShieldAlert, AlertTriangle, CircleDot } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useScreenRecorder } from "@/hooks/useScreenRecorder";
import type { ProctorSurface } from "@/lib/api";

export interface ScreenRecordGuardProps {
  sessionId: string;
  surface: ProctorSurface;
  /** Shown in the consent overlay so the candidate knows what is being recorded. */
  label?: string;
}

function formatElapsed(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

/**
 * Screen-recording gate and live indicator for a proctored surface.
 *
 * `getDisplayMedia` cannot be called silently — it needs a user gesture and the
 * browser draws its own picker. So the consent step is the UI: when the server
 * marks recording as required, a blocking overlay covers the surface until the
 * candidate shares their screen. That overlay is both the gesture source and the
 * thing that stops them working un-recorded.
 *
 * Everything else is deliberately non-blocking. A tab-only share, a failed chunk
 * upload, or a browser that cannot record at all is surfaced as a warning and
 * logged server-side rather than used to lock a candidate out of their own
 * interview — a human reviews the evidence afterwards.
 */
export default function ScreenRecordGuard({
  sessionId,
  surface,
  label,
}: ScreenRecordGuardProps) {
  const [shareEnded, setShareEnded] = useState(false);
  const [dismissedSurfaceWarning, setDismissedSurfaceWarning] = useState(false);

  const handleShareEnded = useCallback(() => {
    // The candidate hit the browser's own "Stop sharing". Re-raise the gate.
    setShareEnded(true);
  }, []);

  const {
    status,
    isRecording,
    config,
    isWholeScreen,
    elapsedSeconds,
    chunksUploaded,
    uploadError,
    error,
    start,
  } = useScreenRecorder({ sessionId, surface, onShareEnded: handleShareEnded });

  const handleStart = useCallback(async () => {
    setShareEnded(false);
    setDismissedSurfaceWarning(false);
    await start();
  }, [start]);

  // Recording off by configuration: render nothing at all, no indicator, no gate.
  if (config && !config.enabled) return null;

  const unsupported = status === "unsupported";
  const required = Boolean(config?.required) && !unsupported;
  // `config === null` means /proctor/config has not answered yet — don't flash a
  // gate that might not be needed, and don't let the candidate start un-gated.
  const gateOpen =
    required && !isRecording && status !== "requesting" && config !== null;

  const surfaceLabel = surface === "coding" ? "coding round" : "interview";

  return (
    <>
      {gateOpen &&
        createPortal(
          <div className="fixed inset-0 z-[10000] bg-background/95 backdrop-blur-md flex flex-col items-center justify-center text-center p-6">
            <ShieldAlert className="w-14 h-14 text-primary mb-4" />
            <h2 className="text-2xl font-bold text-foreground">
              {shareEnded ? "Screen sharing stopped" : "Screen recording required"}
            </h2>
            <p className="text-muted-foreground mt-2 max-w-md text-sm leading-relaxed">
              {shareEnded ? (
                <>
                  Your screen share ended, and this has been recorded. Share your
                  entire screen again to continue the {label || surfaceLabel}.
                </>
              ) : (
                <>
                  This {label || surfaceLabel} is proctored. Your screen is
                  recorded for review while it is open. Choose{" "}
                  <strong className="text-foreground">Entire Screen</strong> in
                  the prompt your browser shows next — sharing a single tab is
                  logged as an integrity event.
                </>
              )}
            </p>

            {(error || status === "denied") && (
              <p className="mt-4 text-sm text-destructive max-w-md">
                {error || "Screen share was not granted."}
              </p>
            )}

            <Button
              className="mt-6"
              onClick={handleStart}
              disabled={status === "requesting"}
            >
              <MonitorUp className="w-4 h-4 mr-2" />
              {status === "requesting"
                ? "Waiting for permission…"
                : shareEnded
                  ? "Resume screen sharing"
                  : "Share your entire screen"}
            </Button>

            <p className="mt-4 text-[11px] text-muted-foreground max-w-sm">
              Nothing else on your machine is captured, and the recording is only
              available to the reviewer of this session.
            </p>
          </div>,
          document.body,
        )}

      {/* Live state. Compact by design — it sits inside pages that already have
          their own dense header rows. */}
      <div className="flex flex-wrap items-center gap-1.5">
        {isRecording && (
          <span
            title={`Screen recording — ${chunksUploaded} chunk${chunksUploaded === 1 ? "" : "s"} uploaded`}
            className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-destructive/15 border border-destructive/25 text-destructive inline-flex items-center gap-1"
          >
            <CircleDot className="w-3 h-3 animate-pulse" />
            REC {formatElapsed(elapsedSeconds)}
          </span>
        )}

        {isRecording && !isWholeScreen && !dismissedSurfaceWarning && (
          <span className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-warning/15 border border-warning/25 text-warning inline-flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            Only one tab shared — recorded
            <button
              type="button"
              onClick={() => setDismissedSurfaceWarning(true)}
              className="ml-1 underline underline-offset-2"
            >
              Dismiss
            </button>
          </span>
        )}

        {isRecording && uploadError && (
          <span
            title={uploadError}
            className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-warning/15 border border-warning/25 text-warning inline-flex items-center gap-1"
          >
            <AlertTriangle className="w-3 h-3" />
            Upload retrying
          </span>
        )}

        {/* Recording is possible but not required and not running: offer it
            rather than silently skipping it. */}
        {!required && !isRecording && !unsupported && config !== null && (
          <Button
            variant="outline"
            size="sm"
            className="h-6 px-2 text-[10px]"
            onClick={handleStart}
            disabled={status === "requesting"}
          >
            <MonitorUp className="w-3 h-3 mr-1" />
            {status === "requesting" ? "Waiting…" : "Record screen"}
          </Button>
        )}

        {unsupported && (
          <span
            title="This browser cannot capture the screen. The session continues unrecorded and the reviewer is told."
            className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-muted border border-border text-muted-foreground inline-flex items-center gap-1"
          >
            <AlertTriangle className="w-3 h-3" />
            Screen recording unavailable
          </span>
        )}
      </div>
    </>
  );
}
