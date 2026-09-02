/**
 * Shared brand language for every interviewer.ai PDF (scorecard, replay
 * exports, …). Centralises the palette, page frame, logo glyph and type
 * helpers so each generator draws the same chrome and only worries about
 * its own content.
 *
 * Everything here is pure jsPDF drawing — no DOM access — so it is safe to
 * exercise from unit tests.
 */
import type { jsPDF } from "jspdf";

/** RGB triple usable with the spread operator in jsPDF colour setters. */
export type Rgb = [number, number, number];

export interface PdfBranding {
  /** Body text colour. */
  ink: Rgb;
  /** Primary brand colour (matches the app logo mark). */
  brand: Rgb;
  /** Secondary text colour. */
  muted: Rgb;
  /** Tertiary / caption text colour. */
  faint: Rgb;
  /** Positive accent (strengths). */
  green: Rgb;
  /** Warning accent (improvements). */
  amber: Rgb;
  /** Hairline rules and frame strokes. */
  rule: Rgb;
  /** Set letter spacing in points (0 resets). */
  setCharSpace: (space: number) => void;
  /** Switch between the bold and regular sans face. */
  font: (bold: boolean) => void;
  /** Draw the double page frame used on every page. */
  drawFrame: () => void;
  /** Draw the logo glyph centred at (cx, cy) with the given size in points. */
  drawLogo: (cx: number, cy: number, size: number) => void;
  /**
   * Draw a centred, bold, letter-spaced title at baseline `y`, shrinking the
   * font size until it fits inside `maxWidth`.
   */
  fitTitle: (text: string, y: number, maxWidth: number) => void;
}

const INK: Rgb = [17, 24, 39];
const BRAND: Rgb = [124, 58, 237];
const MUTED: Rgb = [71, 85, 105];
const FAINT: Rgb = [148, 163, 184];
const GREEN: Rgb = [22, 163, 74];
const AMBER: Rgb = [217, 119, 6];
const RULE: Rgb = [226, 232, 240];
const WHITE: Rgb = [255, 255, 255];

/** Outer and inner frame insets from the page edge, in points. */
const FRAME_OUTER = 28;
const FRAME_INNER = 38;

export function createPdfBranding(
  doc: jsPDF,
  pageWidth: number,
  pageHeight: number,
): PdfBranding {
  const setCharSpace = (space: number) => {
    // Guarded because some jsPDF builds only expose this on the runtime object.
    const api = doc as jsPDF & { setCharSpace?: (s: number) => jsPDF };
    if (typeof api.setCharSpace === "function") api.setCharSpace(space);
  };

  const font = (bold: boolean) => {
    doc.setFont("helvetica", bold ? "bold" : "normal");
  };

  const drawFrame = () => {
    doc.setDrawColor(...RULE);
    doc.setLineWidth(1.2);
    doc.rect(
      FRAME_OUTER,
      FRAME_OUTER,
      pageWidth - FRAME_OUTER * 2,
      pageHeight - FRAME_OUTER * 2,
    );
    doc.setLineWidth(0.6);
    doc.rect(
      FRAME_INNER,
      FRAME_INNER,
      pageWidth - FRAME_INNER * 2,
      pageHeight - FRAME_INNER * 2,
    );
  };

  const drawLogo = (cx: number, cy: number, size: number) => {
    // Mirrors components/LogoMark.tsx: rounded square with a white "target"
    // (two rings, a centre dot and four ticks).
    const half = size / 2;
    const radius = size * 0.19;
    doc.setFillColor(...BRAND);
    doc.roundedRect(cx - half, cy - half, size, size, radius, radius, "F");

    const stroke = Math.max(1, size * 0.0625);
    doc.setDrawColor(...WHITE);
    doc.setLineWidth(stroke);
    doc.circle(cx, cy, size * 0.234, "S");
    doc.circle(cx, cy, size * 0.125, "S");
    doc.setFillColor(...WHITE);
    doc.circle(cx, cy, size * 0.055, "F");

    const tickStart = size * 0.3125;
    const tickEnd = size * 0.21875;
    doc.setLineCap("round");
    doc.line(cx, cy - tickStart, cx, cy - tickEnd);
    doc.line(cx, cy + tickEnd, cx, cy + tickStart);
    doc.line(cx - tickStart, cy, cx - tickEnd, cy);
    doc.line(cx + tickEnd, cy, cx + tickStart, cy);
    doc.setLineCap("butt");
  };

  const fitTitle = (text: string, y: number, maxWidth: number) => {
    const letterSpacing = 1.5;
    let size = 24;
    font(true);
    setCharSpace(letterSpacing);
    doc.setFontSize(size);
    while (size > 10 && doc.getTextWidth(text) > maxWidth) {
      size -= 0.5;
      doc.setFontSize(size);
    }
    doc.setTextColor(...INK);
    doc.text(text, pageWidth / 2, y, { align: "center" });
    setCharSpace(0);
  };

  return {
    ink: INK,
    brand: BRAND,
    muted: MUTED,
    faint: FAINT,
    green: GREEN,
    amber: AMBER,
    rule: RULE,
    setCharSpace,
    font,
    drawFrame,
    drawLogo,
    fitTitle,
  };
}
