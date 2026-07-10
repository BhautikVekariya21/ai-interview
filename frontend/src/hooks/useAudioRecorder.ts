import { useCallback, useEffect, useRef, useState } from "react";

export interface UseAudioRecorderResult {
  isRecording: boolean;
  elapsedSeconds: number;
  volumeLevel: number; // 0-1
  start: () => Promise<boolean>;
  stop: () => Promise<Blob | null>;
  error: string | null;
}

const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
];

/**
 * Reusable microphone recorder: elapsed-time tracking + a live volume
 * meter via AnalyserNode. Resolves with the recorded Blob on stop().
 */
export function useAudioRecorder(): UseAudioRecorderResult {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string>("audio/webm");
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stopResolveRef = useRef<((blob: Blob | null) => void) | null>(null);

  const teardown = useCallback(() => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => teardown, [teardown]);

  const monitorVolume = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteTimeDomainData(data);
      let sumSquares = 0;
      for (let i = 0; i < data.length; i++) {
        const normalized = (data[i] - 128) / 128;
        sumSquares += normalized * normalized;
      }
      const rms = Math.sqrt(sumSquares / data.length);
      setVolumeLevel(Math.min(1, rms * 4));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const start = useCallback(async (): Promise<boolean> => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      let chosenMime = "";
      if (typeof MediaRecorder !== "undefined" && typeof MediaRecorder.isTypeSupported === "function") {
        chosenMime = MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m)) || "";
      }
      const mediaRecorder = chosenMime
        ? new MediaRecorder(stream, { mimeType: chosenMime })
        : new MediaRecorder(stream);
      mimeTypeRef.current = mediaRecorder.mimeType || chosenMime || "audio/webm";
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeTypeRef.current });
        teardown();
        setIsRecording(false);
        stopResolveRef.current?.(blob);
        stopResolveRef.current = null;
      };

      try {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        const audioContext = new AudioCtx();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);
        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        monitorVolume();
      } catch {
        // Volume meter is best-effort; recording still works without it.
      }

      setElapsedSeconds(0);
      timerRef.current = setInterval(() => {
        setElapsedSeconds((s) => s + 1);
      }, 1000);

      mediaRecorder.start();
      setIsRecording(true);
      return true;
    } catch (e: any) {
      setError(e?.message || "Microphone access denied");
      teardown();
      return false;
    }
  }, [monitorVolume, teardown]);

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;
      if (!mediaRecorder || mediaRecorder.state === "inactive") {
        teardown();
        setIsRecording(false);
        resolve(null);
        return;
      }
      stopResolveRef.current = resolve;
      mediaRecorder.stop();
    });
  }, [teardown]);

  return { isRecording, elapsedSeconds, volumeLevel, start, stop, error };
}
