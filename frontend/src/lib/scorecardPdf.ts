/**
 * interviewer.ai interview scorecard PDF generator (ResultsPage "Download PDF
 * Scorecard"). Extracted from ResultsPage.tsx so the exact drawing code is
 * unit-testable (see pdfSnapshots.test.ts) and the component stays a thin
 * wrapper. Same brand language as the scorecard's sibling PDFs — see
 * lib/pdfBranding.ts.
 */
import { jsPDF } from "jspdf";
import { createPdfBranding } from "@/lib/pdfBranding";

export interface ScorecardEvaluation {
  question_number?: number;
  question?: string;
  score: number;
  grade: string;
  feedback?: string;
  strengths?: string[];
  improvements?: string[];
}

export interface ScorecardPdfData {
  candidateName: string;
  overall: number;
  grade: string;
  label: string;
  technicalScore: number;
  communicationScore: number;
  clarityScore: number;
  depthScore: number;
  feedback: string;
  duration: number;
  answeredQuestions: number;
  totalQuestions: number;
  plagiarismSummary?: {
    average_ai_generated_score?: number;
    average_plagiarism_score?: number;
    summary?: string;
  } | null;
  evaluations: ScorecardEvaluation[];
  /** ISO date shown in the header; pass a fixed value in tests. */
  issuedDate?: string;
}

function formatDuration(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}m ${sec}s`;
}

export function buildScorecardPdf(data: ScorecardPdfData): jsPDF {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 56;
  const centerX = pageWidth / 2;

  // Same brand language as every interviewer.ai PDF — palette, frame, logo
  // glyph, all-sans helvetica type (see lib/pdfBranding.ts).
  const {
    ink,
    brand,
    muted,
    faint,
    green,
    amber,
    rule,
    setCharSpace,
    font,
    drawFrame,
    drawLogo,
    fitTitle,
  } = createPdfBranding(doc, pageWidth, pageHeight);

  let y = margin;
  let pageNo = 1;

  const drawFooter = () => {
    // Keep the rule + text inside the inner frame line (pageHeight - 38).
    doc.setDrawColor(...rule);
    doc.setLineWidth(1);
    doc.line(margin, pageHeight - 56, pageWidth - margin, pageHeight - 56);
    font(false);
    doc.setFontSize(8);
    doc.setTextColor(...faint);
    doc.text("interviewer.ai · AI-powered interview practice", centerX, pageHeight - 44, {
      align: "center",
    });
  };

  const newPage = () => {
    doc.addPage();
    pageNo += 1;
    drawFrame();
    drawFooter();
    // Compact brand strip
    drawLogo(66, 64, 24);
    font(true);
    doc.setFontSize(11);
    doc.setTextColor(...brand);
    doc.text("interviewer.ai", 88, 70);
    font(false);
    doc.setFontSize(8);
    doc.setTextColor(...muted);
    doc.text("Interview Evaluation Report", 88, 82);
    doc.setTextColor(...faint);
    doc.text(`Page ${pageNo}`, pageWidth - margin, 70, { align: "right" });
    y = 102;
  };

  const ensure = (needed: number) => {
    if (y + needed > pageHeight - 74) newPage();
  };

  const body = (text: string, size = 10, color: [number, number, number] = ink, indent = 0) => {
    font(false);
    doc.setFontSize(size);
    doc.setTextColor(...color);
    const lines = doc.splitTextToSize(text, pageWidth - margin * 2 - indent);
    for (const line of lines) {
      ensure(size * 1.4);
      doc.text(line, margin + indent, y);
      y += size * 1.4;
    }
  };

  const section = (title: string) => {
    ensure(44);
    y += 12;
    font(true);
    doc.setFontSize(13);
    doc.setTextColor(...brand);
    doc.text(title.toUpperCase(), margin, y);
    doc.setDrawColor(...brand);
    doc.setLineWidth(1.2);
    doc.line(margin, y + 6, margin + 64, y + 6);
    y += 22;
  };

  const labeled = (label: string, value: string, color: [number, number, number] = ink) => {
    ensure(30);
    font(true);
    doc.setFontSize(9.5);
    doc.setTextColor(...color);
    doc.text(label, margin, y);
    y += 12;
    body(value, 9.5, ink, 14);
    y += 3;
  };

  // ---------- PAGE 1 — BRANDED HEADER ----------
  drawFrame();
  drawFooter();

  drawLogo(centerX, 104, 48);
  font(true);
  doc.setFontSize(22);
  doc.setTextColor(...brand);
  doc.text("interviewer.ai", centerX, 156, { align: "center" });
  setCharSpace(2.5);
  font(false);
  doc.setFontSize(8.5);
  doc.setTextColor(...faint);
  doc.text("AI-POWERED INTERVIEW PRACTICE", centerX, 174, { align: "center" });
  setCharSpace(0);

  // Title — measured and self-fitting so it always stays inside the frame
  // (portrait pages are narrow, so the title shrinks to fit).
  fitTitle("INTERVIEW EVALUATION REPORT", 216, pageWidth - margin * 2 - 8);

  // Ornament rule + diamond
  doc.setDrawColor(...rule);
  doc.setLineWidth(1);
  doc.line(centerX - 140, 234, centerX + 140, 234);
  doc.setFillColor(...brand);
  doc.lines([[5, 5], [-5, 5], [-5, -5], [5, -5]], centerX - 5, 229, [1, 1], "F");

  font(true);
  doc.setFontSize(13);
  doc.setTextColor(...ink);
  doc.text(data.candidateName, centerX, 266, { align: "center" });
  font(false);
  doc.setFontSize(9);
  doc.setTextColor(...faint);
  // Locale pinned so snapshots are stable across machines.
  doc.text(
    `Issued ${new Date(data.issuedDate ?? new Date()).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })}`,
    centerX,
    284,
    { align: "center" },
  );

  // Overall score pill
  const pillText = `Overall ${data.overall}%  ·  Grade ${data.grade} (${data.label})`;
  font(true);
  doc.setFontSize(13);
  const pillW = doc.getTextWidth(pillText) + 48;
  doc.setFillColor(...brand);
  doc.roundedRect(centerX - pillW / 2, 300, pillW, 36, 18, 18, "F");
  doc.setTextColor(255, 255, 255);
  doc.text(pillText, centerX, 322, { align: "center" });

  font(false);
  doc.setFontSize(9.5);
  doc.setTextColor(...muted);
  doc.text(
    `${data.answeredQuestions}/${data.totalQuestions} questions answered  ·  ${formatDuration(data.duration)}`,
    centerX,
    348,
    { align: "center" },
  );

  y = 384;

  // ---------- SUMMARY ----------
  section("Summary");
  body(data.feedback, 10, ink);

  // ---------- PERFORMANCE CATEGORIES ----------
  section("Performance Categories");
  const categories = [
    { label: "Technical Depth", score: data.technicalScore },
    { label: "Communication", score: data.communicationScore },
    { label: "Clarity", score: data.clarityScore },
    { label: "Answer Depth", score: data.depthScore },
  ];
  const trackW = pageWidth - margin * 2 - 64;
  for (const c of categories) {
    ensure(44);
    font(true);
    doc.setFontSize(10);
    doc.setTextColor(...ink);
    doc.text(c.label, margin, y);
    font(true);
    doc.setFontSize(10);
    doc.setTextColor(...brand);
    doc.text(`${c.score}%`, pageWidth - margin, y, { align: "right" });
    doc.setFillColor(241, 245, 249);
    doc.roundedRect(margin, y + 8, trackW, 7, 3.5, 3.5, "F");
    doc.setFillColor(...brand);
    doc.roundedRect(margin, y + 8, Math.max(8, (c.score / 100) * trackW), 7, 3.5, 3.5, "F");
    y += 38;
  }

  // ---------- AUTHENTICITY COACHING ----------
  if (data.plagiarismSummary) {
    section("Authenticity Coaching");
    const boxW = (pageWidth - margin * 2 - 16) / 2;
    const boxH = 56;
    ensure(boxH + 46);
    doc.setFillColor(255, 255, 255);
    doc.setDrawColor(...rule);
    doc.setLineWidth(1);
    doc.roundedRect(margin, y, boxW, boxH, 10, 10, "FD");
    font(true);
    doc.setFontSize(7.5);
    doc.setTextColor(...faint);
    doc.text("AVERAGE AI-LIKENESS", margin + boxW / 2, y + 18, { align: "center" });
    font(true);
    doc.setFontSize(14);
    doc.setTextColor(...ink);
    doc.text(
      `${Math.round(data.plagiarismSummary.average_ai_generated_score || 0)}/100`,
      margin + boxW / 2,
      y + 40,
      { align: "center" },
    );
    doc.roundedRect(margin + boxW + 16, y, boxW, boxH, 10, 10, "FD");
    font(true);
    doc.setFontSize(7.5);
    doc.setTextColor(...faint);
    doc.text(
      "AVERAGE PLAGIARISM RISK",
      margin + boxW + 16 + boxW / 2,
      y + 18,
      { align: "center" },
    );
    font(true);
    doc.setFontSize(14);
    doc.setTextColor(...ink);
    doc.text(
      `${Math.round(data.plagiarismSummary.average_plagiarism_score || 0)}/100`,
      margin + boxW + 16 + boxW / 2,
      y + 40,
      { align: "center" },
    );
    y += boxH + 12;
    body(data.plagiarismSummary.summary || "No authenticity summary available.", 9.5, muted);
  }

  // ---------- DETAILED Q&A ----------
  section("Detailed Q&A");
  data.evaluations.forEach((ev, i) => {
    ensure(64);
    font(true);
    doc.setFontSize(10.5);
    doc.setTextColor(...ink);
    const qLines = doc.splitTextToSize(
      `Q${ev.question_number || i + 1}: ${ev.question || ""}`,
      pageWidth - margin * 2,
    );
    for (const line of qLines) {
      ensure(14);
      doc.text(line, margin, y);
      y += 14;
    }
    font(true);
    doc.setFontSize(9.5);
    doc.setTextColor(...muted);
    doc.text(`Score: ${ev.score}/100 · Grade: ${ev.grade}`, margin, y);
    y += 14;
    if (ev.feedback) labeled("Feedback", ev.feedback);
    if (ev.strengths?.length) labeled("Strengths", ev.strengths.join("; "), green);
    if (ev.improvements?.length) labeled("Improvements", ev.improvements.join("; "), amber);
    y += 8;
  });

  return doc;
}
