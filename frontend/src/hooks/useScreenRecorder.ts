import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchProctorConfig,
  recordProctorEvent,
  uploadScreenChunk,
  type ProctorConfigDto,
  type ProctorSurface,
} from "@/lib/api";

export type ScreenRecorderStatus =
  | "unsupported"
  | "idle"
  | "requesting"
  | "recording"
  | "stopped"
  | "denied"
  | "error";

export interface UseScreenRecorderOptions {
  sessionId: string;
  /** Which part of the sitting this recorder belongs to. */
  surface: ProctorSurface;
  /**
   * Fired when capture ends without `stop()` being called — the candidate hit
   * the browser's own "Stop sharing" button, or unplugged the display. The
   * caller decides whether to re-prompt or block the round.
   */
  onShareEnded?: () => void;
}

export interface UseScreenRecorderResult {
  status: ScreenRecorderStatus;
  isRecording: boolean;
  /** Null until `/proctor/config` answers; treat as "not loaded yet", not "off". */
  config: ProctorConfigDto | null;
  /** False when the candidate shared a single tab/window instead of the display. */
  isWholeScreen: boolean;
  elapsedSeconds: number;
  chunksUploaded: number;
  uploadedBytes: number;
  /** Non-null once an upload has failed; recording continues regardless. */
  uploadError: string | null;
  error: string | null;
  /** Must be called from a user gesture — `getDisplayMedia` requires one. */
  start: () => Promise<boolean>;
  stop: () => Promise<void>;
}

/** Preference order: VP9 is the smallest of the widely supported screen codecs. */
const MIME_CANDIDATES = [
  "video/webm;codecs=vp9",
  "video/webm;codecs=vp8",
  "video/webm",
  "video/mp4",
];

const FALLBACK_CHUNK_INTERVAL_MS = 5000;

/**
 * A proctoring screen recorder: `getDisplayMedia` → `MediaRecorder` with a
 * timeslice → chunks uploaded to `/proctor/screen/chunk` as they arrive.
 *
 * Chunks are uploaded during the sitting rather than as one blob at the end, so
 * a candidate who kills the tab still leaves behind everything up to that
 * moment. The server appends them, which makes ordering load-bearing: uploads
 * are serialised through a promise chain instead of fired in parallel.
 *
 * Teardown stops every track, not just the recorder. Stopping a `MediaRecorder`
 * does not release capture — the share stays live and the browser keeps showing
 * its sharing indicator until the tracks themselves are stopped.
 */
export function useScreenRecorder({
  sessionId,
  surface,
  onShareEnded,
}: UseScreenRecorderOptions): UseScreenRecorderResult {
  const supported =
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getDisplayMedia === "function" &&
    typeof MediaRecorder !== "undefined";

  const [status, setStatus] = useState<ScreenRecorderStatus>(
    supported ? "idle" : "unsupported",
  );
  const [config, setConfig] = useState<ProctorConfigDto | null>(null);
  const [isWholeScreen, setIsWholeScreen] = useState(true);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [chunksUploaded, setChunksUploaded] = useState(0);
  const [uploadedBytes, setUploadedBytes] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chunkIndexRef = useRef(0);
  // Serialises uploads: the server appends chunks, so order is the file.
  const uploadChainRef = useRef<Promise<void>>(Promise.resolve());
  const stopResolveRef = useRef<(() => void) | null>(null);
  // Distinguishes "we stopped it" from "the candidate stopped sharing".
  const intentionalStopRef = useRef(false);
  const mountedRef = useRef(true);
  const onShareEndedRef = useRef(onShareEnded);
  onShareEndedRef.current = onShareEnded;

  const logEvent = useCallback(
    (kind: Parameters<typeof recordProctorEvent>[0]["kind"], detail?: string) => {
      void recordProctorEvent({ sessionId, surface, kind, detail });
    },
    [sessionId, surface],
  );

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Chunk interval comes from the server so the cadence is one setting, not two.
  useEffect(() => {
    let cancelled = false;
    fetchProctorConfig()
      .then((c) => {
        if (!cancelled) setConfig(c);
      })
      .catch(() => {
        // Unreachable config is not a reason to skip recording.
        if (!cancelled) {
          setConfig({
            enabled: true,
            required: false,
            chunk_interval_ms: FALLBACK_CHUNK_INTERVAL_MS,
            max_chunk_bytes: 25 * 1024 * 1024,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const teardown = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => {
        t.onended = null;
        t.stop();
      });
      streamRef.current = null;
    }
    recorderRef.current = null;
  }, []);

  useEffect(() => teardown, [teardown]);

  const queueUpload = useCallback(
    (blob: Blob) => {
      const index = chunkIndexRef.current++;
      uploadChainRef.current = uploadChainRef.current
        .then(async () => {
          const res = await uploadScreenChunk({
            sessionId,
            surface,
            chunkIndex: index,
            blob,
          });
          if (!mountedRef.current) return;
          setChunksUploaded((n) => n + 1);
          setUploadedBytes(res.total_bytes);
          setUploadError(null);
        })
        .catch((e: unknown) => {
          const message = e instanceof Error ? e.message : "Chunk upload failed";
          if (mountedRef.current) setUploadError(message);
          logEvent("upload_failed", `chunk ${index}: ${message}`);
          // Swallowed so one failed chunk cannot break the chain for the rest.
        });
    },
    [logEvent, sessionId, surface],
  );

  const start = useCallback(async (): Promise<boolean> => {
    if (!supported) {
      setError("This browser cannot record the screen.");
      setStatus("unsupported");
      return false;
    }
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      return true;
    }

    setError(null);
    setUploadError(null);
    setStatus("requesting");

    let stream: MediaStream;
    try {
      // `monitorTypeSurfaces` and `displaySurface` are hints — a candidate can
      // still pick a single tab, which is why the surface is verified below
      // rather than assumed.
      stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: "monitor",
          frameRate: { ideal: 5, max: 10 },
          width: { max: 1920 },
          height: { max: 1080 },
        },
        audio: false,
        // @ts-expect-error - not in every lib.dom.d.ts yet
        monitorTypeSurfaces: "include",
        selfBrowserSurface: "include",
        surfaceSwitching: "exclude",
      } as DisplayMediaStreamOptions);
    } catch (e: unknown) {
      const message =
        e instanceof Error ? e.message : "Screen share was not granted";
      setError(message);
      setStatus("denied");
      logEvent("screen_share_denied", message);
      return false;
    }

    streamRef.current = stream;
    const [videoTrack] = stream.getVideoTracks();
    if (!videoTrack) {
      teardown();
      setError("No screen video track was returned.");
      setStatus("error");
      logEvent("recorder_error", "getDisplayMedia returned no video track");
      return false;
    }

    const displaySurface = (
      videoTrack.getSettings() as MediaTrackSettings & { displaySurface?: string }
    ).displaySurface;
    const wholeScreen = displaySurface === "monitor" || displaySurface === undefined;
    setIsWholeScreen(wholeScreen);
    if (!wholeScreen) {
      // Recording continues: a tab-only share is still evidence, and refusing it
      // outright would just push the candidate to share nothing at all.
      logEvent(
        "screen_share_wrong_surface",
        `shared "${displaySurface}" instead of the whole screen`,
      );
    }

    let chosenMime = "";
    if (typeof MediaRecorder.isTypeSupported === "function") {
      chosenMime = MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m)) || "";
    }

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, {
        ...(chosenMime ? { mimeType: chosenMime } : {}),
        videoBitsPerSecond: 800_000,
      });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "MediaRecorder failed to start";
      teardown();
      setError(message);
      setStatus("error");
      logEvent("recorder_error", message);
      return false;
    }

    recorderRef.current = recorder;
    chunkIndexRef.current = 0;
    uploadChainRef.current = Promise.resolve();
    intentionalStopRef.current = false;
    setChunksUploaded(0);
    setUploadedBytes(0);
    setElapsedSeconds(0);

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) queueUpload(e.data);
    };
    recorder.onerror = () => {
      logEvent("recorder_error", "MediaRecorder error event");
      if (mountedRef.current) {
        setError("Screen recording stopped unexpectedly.");
        setStatus("error");
      }
      teardown();
    };
    recorder.onstop = () => {
      teardown();
      if (mountedRef.current) setStatus("stopped");
      stopResolveRef.current?.();
      stopResolveRef.current = null;
    };

    // The browser's own "Stop sharing" button ends the track without touching
    // the recorder, so this is the only place that can catch it.
    videoTrack.onended = () => {
      if (intentionalStopRef.current) return;
      logEvent("screen_share_stopped", "candidate ended the screen share");
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      } else {
        teardown();
        if (mountedRef.current) setStatus("stopped");
      }
      onShareEndedRef.current?.();
    };

    timerRef.current = setInterval(() => {
      if (mountedRef.current) setElapsedSeconds((s) => s + 1);
    }, 1000);

    recorder.start(config?.chunk_interval_ms ?? FALLBACK_CHUNK_INTERVAL_MS);
    setStatus("recording");
    logEvent(
      "screen_share_granted",
      `surface=${displaySurface ?? "unknown"} mime=${recorder.mimeType || "default"}`,
    );
    return true;
  }, [config, logEvent, queueUpload, supported, teardown]);

  const stop = useCallback((): Promise<void> => {
    intentionalStopRef.current = true;
    return new Promise((resolve) => {
      const recorder = recorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        teardown();
        if (mountedRef.current) setStatus("stopped");
        resolve();
        return;
      }
      stopResolveRef.current = resolve;
      // Flush whatever is buffered before the final chunk boundary.
      recorder.stop();
    }).then(() => uploadChainRef.current);
  }, [teardown]);

  return {
    status,
    isRecording: status === "recording",
    config,
    isWholeScreen,
    elapsedSeconds,
    chunksUploaded,
    uploadedBytes,
    uploadError,
    error,
    start,
    stop,
  };
}
