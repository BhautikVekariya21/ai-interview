import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import InterviewPage from "@/components/InterviewPage";

/* CodeMirror needs real DOM measurement APIs that jsdom lacks —
   swap the editor for a plain textarea with the same contract. */
vi.mock("@/components/CodePadEditor", () => ({
  default: ({
    value,
    onChange,
    placeholder,
  }: {
    value: string;
    onChange: (v: string) => void;
    placeholder?: string;
  }) => (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  ),
}));

vi.mock("@/lib/api", () => ({
  runCode: vi.fn(async () => ({
    success: true,
    stdout: "",
    stderr: "",
    exit_code: 0,
    timed_out: false,
  })),
  textToSpeech: vi.fn(async () => new Blob()),
  playAudioWithFeedback: vi.fn(async () => undefined),
  transcribeAudio: vi.fn(async () => ({ success: true, text: "" })),
  evaluateAndNext: vi.fn(),
  evaluateAnswer: vi.fn(),
  evaluateBatch: vi.fn(),
  fetchInterviewIntroSpeech: vi.fn(async () => ({
    blob: new Blob(),
    scriptText: "Welcome",
  })),
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

const questions = [
  { id: 1, text: "Tell me about React", category: "T", difficulty: "easy" },
  { id: 2, text: "How do you debug a slow API?", category: "T", difficulty: "medium" },
];

const savedMessages = [
  { role: "ai" as const, text: "Tell me about React", timestamp: "10:00" },
];

function renderInterview() {
  const utils = render(
    <InterviewPage
      candidateName="Jane"
      resumeData={{}}
      questions={questions}
      savedMessages={savedMessages}
      savedQuestionIndex={0}
      savedTimer={10}
    />,
  );
  return act(async () => {
    await Promise.resolve();
    return utils;
  });
}

class MockSpeechRecognition extends EventTarget implements SpeechRecognitionLike {
  static lastInstance: MockSpeechRecognition | null = null;

  lang = "en-US";
  interimResults = false;
  continuous = false;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null = null;
  onend: (() => void) | null = null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null = null;

  constructor() {
    super();
    MockSpeechRecognition.lastInstance = this;
  }

  start() {}

  stop() {
    this.onend?.();
  }

  abort() {}
}

/** Build a minimal `onresult` payload the way the browser would. */
function speechResult(transcript: string, isFinal = true): SpeechRecognitionEventLike {
  const alternative = { transcript, confidence: 1 };
  const result = { 0: alternative, isFinal, length: 1 };
  return { resultIndex: 0, results: { 0: result, length: 1 } } as unknown as SpeechRecognitionEventLike;
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.clearAllMocks();
  MockSpeechRecognition.lastInstance = null;
  delete window.webkitSpeechRecognition;
  delete (navigator as Navigator & { mediaDevices?: unknown }).mediaDevices;
});

describe("InterviewPage live WPM", () => {
  it("shows a placeholder before the current answer starts", async () => {
    await renderInterview();

    expect(screen.getByTestId("live-wpm")).toHaveTextContent("-- WPM");
  });

  it("updates from typed input and ignores code pad text", async () => {
    await renderInterview();

    const answerInput = screen.getByPlaceholderText(/type your spoken answer/i);
    fireEvent.change(answerInput, {
      target: { value: "one two three four five six seven eight nine ten" },
    });

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(screen.getByTestId("live-wpm")).toHaveTextContent("120 WPM");

    fireEvent.click(screen.getByRole("button", { name: /code pad/i }));

    const codeInput = screen.getByPlaceholderText(/Write your code here/i);
    fireEvent.change(codeInput, {
      target: {
        value: Array.from({ length: 40 }, (_, index) => `token${index}`).join(" "),
      },
    });

    expect(screen.getByTestId("live-wpm")).toHaveTextContent("120 WPM");
  });

  it("updates from live transcription and resets after skipping", async () => {
    window.webkitSpeechRecognition = MockSpeechRecognition;

    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: {
        getUserMedia: vi.fn(async () => {
          throw new Error("Microphone unavailable");
        }),
      },
    });

    await renderInterview();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /start recording/i }));
      await Promise.resolve();
    });

    await act(async () => {
      MockSpeechRecognition.lastInstance?.onresult?.(
        speechResult("transcribed answer from browser"),
      );
      await Promise.resolve();
    });

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(screen.getByTestId("live-wpm")).toHaveTextContent("48 WPM");

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /skip question/i }));
      await Promise.resolve();
    });

    expect(screen.getByTestId("live-wpm")).toHaveTextContent("-- WPM");
  });
});
