export type PaceLabel =
  | "waiting"
  | "too_slow"
  | "slightly_slow"
  | "ideal"
  | "slightly_fast"
  | "too_fast";

export interface WpmSnapshot {
  wpm: number;
  timestamp: number;
  fillerCount: number;
}

export interface FillerWordCount {
  word: string;
  count: number;
}

const FILLER_WORDS = [
  "um",
  "uh",
  "er",
  "ah",
  "like",
  "actually",
  "basically",
  "literally",
  "honestly",
  "so",
  "well",
  "right",
  "okay",
  "you know",
  "i mean",
  "sort of",
  "kind of",
];

export function countInterviewWords(text: string): number {
  if (!text) return 0;
  const matches = text.trim().match(/\S+/g);
  return matches ? matches.length : 0;
}

export function calculateLiveWpm(
  wordCount: number,
  elapsedSeconds: number,
): number | null {
  if (!wordCount || wordCount <= 0) return null;
  if (!elapsedSeconds || elapsedSeconds < 3) return null;
  const minutes = elapsedSeconds / 60;
  if (minutes <= 0) return null;
  return Math.round(wordCount / minutes);
}

export function getPaceLabel(wpm: number | null): PaceLabel {
  if (wpm === null || wpm <= 0) return "waiting";
  if (wpm < 90) return "too_slow";
  if (wpm < 110) return "slightly_slow";
  if (wpm <= 150) return "ideal";
  if (wpm <= 170) return "slightly_fast";
  return "too_fast";
}

export function countFillerWords(text: string): FillerWordCount[] {
  if (!text) return [];
  const normalized = ` ${text.toLowerCase().replace(/[^\w\s']/g, " ").replace(/\s+/g, " ")} `;
  const counts: FillerWordCount[] = [];

  for (const filler of FILLER_WORDS) {
    const pattern = new RegExp(`(?<=\\s)${filler.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?=\\s)`, "g");
    const matches = normalized.match(pattern);
    if (matches && matches.length > 0) {
      counts.push({ word: filler, count: matches.length });
    }
  }

  return counts.sort((a, b) => b.count - a.count);
}
