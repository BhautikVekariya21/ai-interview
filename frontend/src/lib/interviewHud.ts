import { useEffect, useState } from "react";

export interface HudState {
  active: boolean;
  recording: boolean;
  cameraOn: boolean;
  elapsed: number;
}

export type InterviewActionType = "toggle-camera" | "toggle-record" | "end";

const HUD_STATE_EVENT = "interview:hud-state";
const ACTION_EVENT = "interview:action";

const IDLE_STATE: HudState = { active: false, recording: false, cameraOn: false, elapsed: 0 };

export function publishHudState(state: HudState) {
  window.dispatchEvent(new CustomEvent<HudState>(HUD_STATE_EVENT, { detail: state }));
}

export function requestInterviewAction(type: InterviewActionType) {
  window.dispatchEvent(new CustomEvent<InterviewActionType>(ACTION_EVENT, { detail: type }));
}

export function onInterviewAction(handler: (type: InterviewActionType) => void) {
  const listener = (e: Event) => handler((e as CustomEvent<InterviewActionType>).detail);
  window.addEventListener(ACTION_EVENT, listener);
  return () => window.removeEventListener(ACTION_EVENT, listener);
}

export function useHudState(): HudState {
  const [state, setState] = useState<HudState>(IDLE_STATE);
  useEffect(() => {
    const listener = (e: Event) => setState((e as CustomEvent<HudState>).detail);
    window.addEventListener(HUD_STATE_EVENT, listener);
    return () => window.removeEventListener(HUD_STATE_EVENT, listener);
  }, []);
  return state;
}

export function formatElapsed(s: number): string {
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}
