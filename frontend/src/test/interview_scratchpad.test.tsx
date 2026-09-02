import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import InterviewPage from "@/components/InterviewPage";

vi.mock("@/lib/api", () => ({
  textToSpeech: vi.fn(async () => new Blob()),
  playAudioWithFeedback: vi.fn(async () => undefined),
  transcribeAudio: vi.fn(async () => ({ success: true, text: "" })),
  evaluateAndNext: vi.fn(),
  evaluateAnswer: vi.fn(),
  evaluateBatch: vi.fn(),
  fetchInterviewIntroSpeech: vi.fn(async () => new Blob()),
  fetchQuestionSpeech: vi.fn(async () => new Blob()),
  fetchInterviewOutroSpeech: vi.fn(async () => new Blob()),
  fetchVoicePresets: vi.fn(async () => [{ id: "gtts_en", label: "gTTS" }]),
  fetchProctorConfig: vi.fn(async () => ({
    enabled: false,
    required: false,
    chunk_interval_ms: 5000,
    max_chunk_bytes: 1_000_000,
  })),
}));

describe("InterviewPage scratch pad", () => {
  it("opens scratch pad panel and keeps theme token classes", async () => {
    render(
      <InterviewPage
        candidateName="Jane"
        resumeData={{}}
        questions={[{ id: 1, text: "Tell me about React", category: "T", difficulty: "easy" }]}
        savedMessages={[{ role: "ai", text: "Question", timestamp: "10:00" }]}
        savedQuestionIndex={1}
        savedTimer={5}
      />
    );

    const drawingButton = screen.getAllByRole("button", { name: /drawing/i })[0];
    fireEvent.click(drawingButton);

    expect(await screen.findByText(/notes & drawing/i)).toBeInTheDocument();
    const input = screen.getByPlaceholderText(/type your spoken answer/i);
    expect(input.className).toContain("bg-muted/50");
    expect(input.className).toContain("focus:ring-primary/20");
  });
});
