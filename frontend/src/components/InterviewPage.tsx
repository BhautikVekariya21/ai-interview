import { useState, useRef, useEffect, useCallback } from "react";
import { m as motion } from "framer-motion";
import {
  Send,
  Mic,
  MicOff,
  Clock,
  Gauge,
  User,
  Bot,
  StopCircle,
  SkipForward,
  RotateCcw,
  Code,
  Camera,
  CameraOff,
  PenTool,
  Lightbulb,
  ShieldAlert,
  Play,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ScratchPad from "./ScratchPad";
import CodePadEditor from "./CodePadEditor";
import ResizablePanel from "./ResizablePanel";
import { getStarterCode } from "@/lib/starterCode";
import {
  textToSpeech,
  playAudioWithFeedback,
  transcribeAudio,
  evaluateAndNext,
  evaluateAnswer,
  evaluateBatch,
  fetchInterviewIntroSpeech,
  fetchQuestionSpeech,
  fetchInterviewOutroSpeech,
  fetchVoicePresets,
  detectAnswerSimilarity,
  adjustQuestionDifficulty,
  generateRagReport,
  runCode,
  type CodeRunResult,
  type EvaluationResult,
  type EvaluateAnswerRequest,
  type BatchEvaluationResult,
  type RagReportResult,
  type AuthenticityReport,
} from "@/lib/api";
import { toast } from "sonner";
import type { GeneratedQuestion } from "@/pages/Index";
import {
  calculateLiveWpm,
  countInterviewWords,
  countFillerWords,
  getPaceLabel,
  type PaceLabel,
  type WpmSnapshot,
} from "@/lib/interviewPace";
import WpmPanel from "./WpmPanel";
import LogoStack from "./LogoStack";
import { publishHudState, onInterviewAction } from "@/lib/interviewHud";

interface ChatMessage {
  role: "ai" | "user";
  text: string;
  timestamp: string;
}

interface AnswerRecord {
  question_id: string;
  question: string;
  category: string;
  answer: string;
  evaluation?: EvaluationResult;
}

interface InterviewPageProps {
  candidateName: string;
  resumeData?: Record<string, unknown>;
  questions: GeneratedQuestion[];
  savedMessages?: ChatMessage[];
  savedQuestionIndex?: number;
  savedTimer?: number;
  onStateChange?: (
    messages: ChatMessage[],
    questionIndex: number,
    timer: number,
  ) => void;
  onInterviewComplete?: (data: {
    messages: { role: "ai" | "user"; text: string }[];
    totalQuestions: number;
    answeredQuestions: number;
    duration: number;
    overallScore?: number;
    overallGrade?: string;
    summary?: string;
    evaluations?: BatchEvaluationResult["evaluations"];
    plagiarismSummary?: BatchEvaluationResult["plagiarism_summary"];
    ragReport?: RagReportResult;
  }) => void;
}

function getWpmToneClasses(label: PaceLabel) {
  if (label === "ideal") {
    return "bg-success/10 border-success/20 text-success";
  }
  if (label === "slightly_fast" || label === "slightly_slow") {
    return "bg-amber-500/10 border-amber-500/20 text-amber-600";
  }
  if (label === "too_fast" || label === "too_slow") {
    return "bg-destructive/10 border-destructive/20 text-destructive";
  }
  return "bg-muted border-border text-muted-foreground";
}

function formatPaceLabel(label: PaceLabel) {
  if (label === "ideal") return "Ideal pace";
  if (label === "slightly_fast") return "Slightly fast";
  if (label === "slightly_slow") return "Slightly slow";
  if (label === "too_fast") return "Too fast";
  if (label === "too_slow") return "Too slow";
  return "Waiting for answer";
}

/**
 * Heuristic: does this question expect a code answer?
 * There is no dedicated "coding" category (categories are T/P/B/C/R), so we
 * detect intent from the question text. Used to auto-open the code editor and
 * require a code submission for evaluation.
 */
const CODING_QUESTION_PATTERN =
  /\b(write|implement|code|coding|function|algorithm|program|snippet|pseudocode|time complexity|space complexity|big[- ]?o|leetcode|data structure|recursion|iterate|sort|traverse|optimi[sz]e (?:the )?(?:code|function|query)|sql query|regex)\b/i;

function isCodingQuestion(text: string): boolean {
  return CODING_QUESTION_PATTERN.test(text || "");
}

export default function InterviewPage({
  candidateName,
  resumeData,
  questions,
  savedMessages,
  savedQuestionIndex,
  savedTimer,
  onStateChange,
  onInterviewComplete,
}: InterviewPageProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(savedMessages || []);
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [questionIndex, setQuestionIndex] = useState(savedQuestionIndex || 0);
  const [timer, setTimer] = useState(savedTimer || 0);
  const [timerStarted, setTimerStarted] = useState(
    (savedMessages && savedMessages.length > 0) || false,
  );
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<string>("gtts_en");
  const [answers, setAnswers] = useState<AnswerRecord[]>([]);
  const [batchResult, setBatchResult] = useState<BatchEvaluationResult | null>(
    null,
  );
  const [questionReadyMessage, setQuestionReadyMessage] = useState<string>(
    "Initializing interview questions...",
  );
  const [rightPanelMode, setRightPanelMode] = useState<
    "none" | "code" | "scratch"
  >("none");
  const [codeContext, setCodeContext] = useState("");
  const [runResult, setRunResult] = useState<CodeRunResult | null>(null);
  const [isRunningCode, setIsRunningCode] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [hintText, setHintText] = useState<string | null>(null);
  const [recommendedDifficulty, setRecommendedDifficulty] = useState<
    string | null
  >(null);
  const [isHintLoading, setIsHintLoading] = useState(false);
  const [isObscured, setIsObscured] = useState(false);
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [answerStartTimer, setAnswerStartTimer] = useState<number | null>(null);
  const [answerEndTimer, setAnswerEndTimer] = useState<number | null>(null);
  const [wpmHistory, setWpmHistory] = useState<WpmSnapshot[]>([]);
  const [currentTime, setCurrentTime] = useState(() => new Date());
  /* Draggable editor/chat split (percentage width of the left column on lg+). */
  const [splitPct, setSplitPct] = useState(50);
  const [isLgScreen, setIsLgScreen] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(min-width: 1024px)").matches,
  );

  const chatRef = useRef<HTMLDivElement>(null);
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const isDraggingSplitRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setInterval>>();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordedMimeTypeRef = useRef<string>("audio/webm");
  const browserRecRef = useRef<any>(null);
  const browserTranscriptRef = useRef<string>("");
  const browserFinalTranscriptRef = useRef<string>("");
  const inputBeforeRecordingRef = useRef<string>("");
  const sessionIdRef = useRef<string>(
    `s_${Math.random().toString(36).slice(2, 10)}`,
  );
  const introStartedRef = useRef(false);
  const wasRecordingRef = useRef(false);
  const wpmSnapshotRef = useRef<ReturnType<typeof setInterval>>();

  const questionTexts = (questions || []).map((q) => q.text);
  const currentQuestionText = questionTexts[questionIndex] || "";
  const currentQuestionIsCoding = isCodingQuestion(currentQuestionText);
  const currentAnswerWordCount = countInterviewWords(input);
  const answerClockNow =
    answerEndTimer !== null ? answerEndTimer : currentTime.getTime();
  const currentAnswerElapsedSeconds =
    answerStartTimer === null
      ? 0
      : Math.max((answerClockNow - answerStartTimer) / 1000, 0);
  const liveWpm = calculateLiveWpm(
    currentAnswerWordCount,
    currentAnswerElapsedSeconds,
  );
  const livePaceLabel = getPaceLabel(liveWpm);
  const liveWpmText = liveWpm === null ? "-- WPM" : `${liveWpm} WPM`;
  const liveFillerWords = countFillerWords(input);

  const now = () =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const onPasteBlocked = useCallback((e: React.ClipboardEvent<HTMLElement>) => {
    e.preventDefault();
    toast.warning("Copy and paste is disabled during interview.");
  }, []);

  const onCopyCutBlocked = useCallback(
    (e: React.ClipboardEvent<HTMLElement>) => {
      e.preventDefault();
      toast.warning("Copy/Cut is disabled during interview.");
    },
    [],
  );

  const onKeyboardShortcutBlocked = useCallback(
    (e: React.KeyboardEvent<HTMLElement>) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        ["c", "x", "v", "a"].includes(e.key.toLowerCase())
      ) {
        e.preventDefault();
        toast.warning("Keyboard shortcuts are disabled during interview.");
      }
    },
    [],
  );

  const onQuestionInteractionBlocked = useCallback(
    (e: React.SyntheticEvent<HTMLElement>) => {
      e.preventDefault();
      toast.warning("Question copying is disabled during interview.");
    },
    [],
  );

  const handleGetHint = async () => {
    if (!currentQuestionText || isHintLoading || hintText) return;
    setIsHintLoading(true);
    try {
      const { getQuestionHint } = await import("@/lib/api");
      const res = await getQuestionHint(currentQuestionText);
      setHintText(res.hint);
    } catch {
      toast.error("Failed to load hint.");
    } finally {
      setIsHintLoading(false);
    }
  };

  useEffect(() => {
    fetchVoicePresets().then((v) => {
      const cached = localStorage.getItem("tts_voice_id") || "";
      if (cached && v.some((x) => x.id === cached)) {
        setSelectedVoice(cached);
      } else if (v.length > 0) {
        setSelectedVoice(v[0].id);
      } else {
        setSelectedVoice("gtts_en");
      }
    });
  }, []);

  useEffect(() => {
    if (selectedVoice) localStorage.setItem("tts_voice_id", selectedVoice);
  }, [selectedVoice]);

  useEffect(() => {
    setAnswerStartTimer(null);
    setAnswerEndTimer(null);
  }, [questionIndex]);

  useEffect(() => {
    if (currentAnswerWordCount === 0) {
      if (answerStartTimer !== null) {
        setAnswerStartTimer(null);
      }
      if (answerEndTimer !== null) {
        setAnswerEndTimer(null);
      }
      return;
    }

    setAnswerStartTimer((prev) => prev ?? Date.now());
  }, [currentAnswerWordCount, answerStartTimer, answerEndTimer]);

  /* Freeze the pace clock the moment recording stops, so WPM stops drifting
     while transcribed text (or background voice) sits in the input. Only acts
     on a real recording→stopped transition, not plain typing. */
  useEffect(() => {
    const wasRecording = wasRecordingRef.current;
    wasRecordingRef.current = isRecording;
    if (wasRecording && !isRecording && answerStartTimer !== null) {
      setAnswerEndTimer(Date.now());
    }
    if (isRecording && answerEndTimer !== null) {
      setAnswerEndTimer(null);
    }
  }, [isRecording, answerStartTimer, answerEndTimer]);

  /* ── Snapshot WPM every 5 seconds while typing ───────── */
  useEffect(() => {
    if (wpmSnapshotRef.current) {
      clearInterval(wpmSnapshotRef.current);
      wpmSnapshotRef.current = undefined;
    }

    if (liveWpm !== null && liveWpm > 0) {
      wpmSnapshotRef.current = setInterval(() => {
        if (answerEndTimer !== null) return;
        const words = countInterviewWords(input);
        const elapsed =
          answerStartTimer === null
            ? 0
            : Math.max((Date.now() - answerStartTimer) / 1000, 0);
        const wpm = calculateLiveWpm(words, elapsed);
        if (wpm !== null && wpm > 0) {
          const fillers = countFillerWords(input).reduce((s, f) => s + f.count, 0);
          setWpmHistory((prev) => [
            ...prev.slice(-39), // keep last 40
            { wpm, timestamp: timer, fillerCount: fillers },
          ]);
        }
      }, 5000);
    }

    return () => {
      if (wpmSnapshotRef.current) {
        clearInterval(wpmSnapshotRef.current);
        wpmSnapshotRef.current = undefined;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveWpm !== null && liveWpm > 0]);

  /* ── Live local clock ─────────────────────────────────── */
  useEffect(() => {
    const clockInterval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clockInterval);
  }, []);

  /* Track the lg breakpoint so the draggable split only applies on wide screens
     (below lg the panels stack vertically and the divider is hidden). */
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setIsLgScreen(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  /* Drag the divider between the chat column and the right panel (code/scratch).
     Clamped to 25–75% so neither side collapses. */
  const startSplitDrag = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    isDraggingSplitRef.current = true;
    const onMove = (ev: PointerEvent) => {
      const container = splitContainerRef.current;
      if (!container || !isDraggingSplitRef.current) return;
      const rect = container.getBoundingClientRect();
      const pct = ((ev.clientX - rect.left) / rect.width) * 100;
      setSplitPct(Math.min(75, Math.max(25, pct)));
    };
    const onUp = () => {
      isDraggingSplitRef.current = false;
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      document.body.style.userSelect = "";
    };
    document.body.style.userSelect = "none";
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }, []);

  const startTimer = useCallback(() => {
    if (!timerStarted) setTimerStarted(true);
  }, [timerStarted]);

  const resetCurrentAnswerDraft = useCallback(() => {
    setInput("");
    setCodeContext("");
    setRunResult(null);
    setAnswerStartTimer(null);
    setAnswerEndTimer(null);
    browserTranscriptRef.current = "";
    browserFinalTranscriptRef.current = "";
    inputBeforeRecordingRef.current = "";
    if (textareaRef.current) {
      textareaRef.current.style.height = "42px";
    }
  }, []);

  /* Seed a LeetCode-style starter template whenever a coding question
     appears with an empty pad, so candidates begin from runnable code. */
  useEffect(() => {
    if (!currentQuestionIsCoding || !currentQuestionText) return;
    setCodeContext((prev) => (prev.trim() ? prev : getStarterCode(currentQuestionText)));
  }, [currentQuestionText, currentQuestionIsCoding]);

  const handleRunCode = useCallback(async () => {
    if (!codeContext.trim() || isRunningCode) return;
    setIsRunningCode(true);
    setRunResult(null);
    try {
      const result = await runCode(codeContext);
      setRunResult(result);
    } catch (e) {
      setRunResult({
        success: false,
        stdout: "",
        stderr: e instanceof Error ? e.message : "Failed to reach the code runner.",
        exit_code: null,
        timed_out: false,
      });
    } finally {
      setIsRunningCode(false);
    }
  }, [codeContext, isRunningCode]);

  useEffect(() => {
    if (timerStarted && !timerRef.current) {
      timerRef.current = setInterval(() => setTimer((t) => t + 1), 1000);
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = undefined;
      }
    };
  }, [timerStarted]);

  useEffect(() => {
    return () => {
      if (cameraStreamRef.current) {
        cameraStreamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const toggleCamera = async () => {
    if (cameraActive) {
      if (cameraStreamRef.current) {
        cameraStreamRef.current.getTracks().forEach((track) => track.stop());
        cameraStreamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setCameraActive(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        cameraStreamRef.current = stream;
        setCameraActive(true);
      } catch (err) {
        toast.error("Failed to access camera. Check permissions.");
      }
    }
  };

  useEffect(() => {
    onStateChange?.(messages, questionIndex, timer);
  }, [messages, questionIndex, timer, onStateChange]);

  // Attach the camera stream once the <video> element is actually mounted.
  // Using an effect (instead of a setTimeout after setCameraActive) avoids a
  // race where the timer fired before the ref was attached, leaving a black box.
  useEffect(() => {
    const el = videoRef.current;
    const stream = cameraStreamRef.current;
    if (!cameraActive || !el || !stream) return;
    if (el.srcObject !== stream) {
      el.srcObject = stream;
    }
    el.play().catch(() => {
      /* autoplay may reject until a user gesture; muted+autoplay covers the common case */
    });
  }, [cameraActive, rightPanelMode, currentQuestionIsCoding]);

  useEffect(() => {
    const handler = () => onStateChange?.(messages, questionIndex, timer);
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [messages, questionIndex, timer, onStateChange]);

  // Publish live interview state to the navbar HUD.
  useEffect(() => {
    publishHudState({ active: true, recording: isRecording, cameraOn: cameraActive, elapsed: timer });
  }, [isRecording, cameraActive, timer]);

  useEffect(() => {
    return () => publishHudState({ active: false, recording: false, cameraOn: false, elapsed: 0 });
  }, []);

  // Route navbar HUD actions back to the in-page handlers.
  useEffect(() => {
    return onInterviewAction((type) => {
      if (type === "toggle-camera") void toggleCamera();
      else if (type === "toggle-record") void toggleRecording();
      else if (type === "end") void finalizeInterview(true);
    });
  }, [cameraActive, isRecording, isFinishing]);

  useEffect(() => {
    const el = chatRef.current;
    if (!el) return;
    if (typeof el.scrollTo === "function") {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    } else {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const addAiMessage = useCallback((text: string) => {
    setMessages((prev) => [...prev, { role: "ai", text, timestamp: now() }]);
  }, []);

  const browserSpeak = useCallback((text: string) => {
    return new Promise<void>((resolve) => {
      try {
        if (!("speechSynthesis" in window)) {
          resolve();
          return;
        }
        const u = new SpeechSynthesisUtterance(String(text || ""));
        const voices = window.speechSynthesis.getVoices();
        const english = voices.find((v) => /^en(-|_|$)/i.test(v.lang));
        if (english) u.voice = english;
        u.lang = english?.lang || "en-US";
        u.rate = 0.96;
        u.pitch = 1.0;
        u.volume = 1.0;
        u.onend = () => resolve();
        u.onerror = () => resolve();
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      } catch {
        resolve();
      }
    });
  }, []);

  const speakText = useCallback(
    async (
      text: string,
      opts?: { questionNumber?: number; totalQuestions?: number },
    ) => {
      setIsSpeaking(true);
      startTimer();
      try {
        const blob = opts?.questionNumber
          ? await fetchQuestionSpeech(
              text,
              opts.questionNumber,
              opts.totalQuestions || questionTexts.length,
              selectedVoice || undefined,
            )
          : await textToSpeech(text, selectedVoice || undefined);
        await playAudioWithFeedback(blob);
      } catch {
        toast.warning(
          "Audio playback unavailable. Using browser voice fallback.",
        );
        await browserSpeak(text);
      } finally {
        setIsSpeaking(false);
      }
    },
    [startTimer, selectedVoice, browserSpeak, questionTexts.length],
  );

  useEffect(() => {
    if (questionTexts.length === 0) return;
    if (savedMessages && savedMessages.length > 0) return;
    if (introStartedRef.current) return;

    const timeout = setTimeout(() => {
      if (introStartedRef.current) return;
      introStartedRef.current = true;

      const introFallbackText = `Good day ${candidateName}, and welcome. Thank you for taking the time to join this interview. I will guide you through ${questionTexts.length} personalized questions based on your resume. Please answer at your own pace, and feel free to think out loud.`;
      (async () => {
        setIsSpeaking(true);
        try {
          const { blob, scriptText } = await fetchInterviewIntroSpeech(
            candidateName,
            questionTexts.length,
            resumeData,
            selectedVoice || undefined,
          );
          addAiMessage(scriptText || introFallbackText);
          await Promise.race([
            playAudioWithFeedback(blob),
            new Promise((resolve) => setTimeout(resolve, 10000)),
          ]);
        } catch {
          addAiMessage(introFallbackText);
          await speakText(introFallbackText);
        }

        const firstQ = questionTexts[0];
        addAiMessage(firstQ);
        await speakText(firstQ, {
          questionNumber: 1,
          totalQuestions: questionTexts.length,
        });
      })();
    }, 80);

    return () => clearTimeout(timeout);
  }, [
    questionTexts,
    savedMessages,
    questionIndex,
    answers.length,
    candidateName,
    resumeData,
    selectedVoice,
    addAiMessage,
    speakText,
  ]);

  useEffect(() => {
    if (!questionTexts.length) {
      setQuestionReadyMessage("No questions generated yet.");
      return;
    }
    setQuestionReadyMessage(
      `✅ ${questionTexts.length} questions generated. Current question ${Math.min(questionIndex + 1, questionTexts.length)} of ${questionTexts.length}.`,
    );
  }, [questionTexts.length, questionIndex]);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  };

  const finalizeInterview = useCallback(
    async (manual = false) => {
      if (isFinishing) return;
      setIsFinishing(true);
      setIsThinking(true);
      setAnswerStartTimer(null);
      clearInterval(timerRef.current);
      timerRef.current = undefined;

      const qaPairs = answers.map((a) => ({
        question: a.question,
        answer: a.answer,
        category: a.category || "T",
        question_id: a.question_id,
      }));

      let batch: BatchEvaluationResult | null = null;
      if (qaPairs.length > 0) {
        try {
          batch = await evaluateBatch(sessionIdRef.current, qaPairs);
          setBatchResult(batch);
        } catch {
          batch = null;
        }
      }

      setIsThinking(false);

      const newMessages: ChatMessage[] = [];
      const addLocalMessage = (text: string) => {
        newMessages.push({ role: "ai", text, timestamp: now() });
        addAiMessage(text);
      };

      addLocalMessage(manual ? "Interview ended early." : "Interview complete.");
      if (batch) {
        addLocalMessage(
          `Overall Score: ${batch.overall_score}/100 (${batch.overall_grade})`,
        );
        addLocalMessage(batch.summary || "Final evaluation generated.");
        if (batch.plagiarism_summary) {
          addLocalMessage(
            `Authenticity Review: AI-likeness ${batch.plagiarism_summary.average_ai_generated_score}/100, plagiarism risk ${batch.plagiarism_summary.average_plagiarism_score}/100.`,
          );
        }

        (batch.evaluations || []).forEach((ev, i) => {
          const strengths =
            Array.isArray(ev.strengths) && ev.strengths.length
              ? ev.strengths.join(" | ")
              : "-";
          const improvements =
            Array.isArray(ev.improvements) && ev.improvements.length
              ? ev.improvements.join(" | ")
              : "-";
          const follow =
            ev.followup_question || ev.follow_up_question
              ? `\nFollow-up: ${ev.followup_question || ev.follow_up_question}`
              : "";
          const authenticity = ev.authenticity_report as
            | AuthenticityReport
            | undefined;
          const authenticityLine = authenticity
            ? `\nAuthenticity: AI-likeness ${Math.round(authenticity.ai_generated_score || 0)}/100, plagiarism risk ${Math.round(authenticity.plagiarism_score || 0)}/100`
            : "";
          addLocalMessage(
            `Q${i + 1}\nScore: ${ev.score}/100\nGrade: ${ev.grade}\nStrengths: ${strengths}\nAreas for improvement: ${improvements}\nAI feedback: ${ev.feedback}${authenticityLine}${follow}`,
          );
        });
      }

      // RAG grounded report: cite specific answers per score. Best-effort —
      // a failure here must never block interview completion.
      let ragReport: Awaited<ReturnType<typeof generateRagReport>> | null = null;
      if (qaPairs.length > 0) {
        const role =
          (resumeData?.primary_domain as string | undefined) || "general";
        const scoreById = new Map(
          (batch?.evaluations || []).map((ev, i) => [
            String(ev.question_id ?? i),
            typeof ev.score === "number" ? (ev.score as number) : undefined,
          ]),
        );
        try {
          ragReport = await generateRagReport({
            session_id: sessionIdRef.current,
            role,
            candidate_name: candidateName,
            qa_pairs: answers.map((a) => ({
              question: a.question,
              answer: a.answer,
              score: a.evaluation?.score ?? scoreById.get(a.question_id),
            })),
          });
          if (ragReport?.summary) {
            addLocalMessage(`Grounded report: ${ragReport.summary}`);
            if (ragReport.recommendation) {
              addLocalMessage(`Recommendation: ${ragReport.recommendation}`);
            }
          }
        } catch {
          ragReport = null;
        }
      }

      const outroText = batch
        ? `Thank you ${candidateName}. Your interview is complete with overall grade ${batch.overall_grade}.`
        : `Thank you ${candidateName}. Your interview is complete.`;

      try {
        const blob = await fetchInterviewOutroSpeech(
          candidateName,
          questionTexts.length,
          batch ? (batch as unknown as Record<string, unknown>) : undefined,
          selectedVoice || undefined,
        );
        await playAudioWithFeedback(blob);
      } catch {
        await browserSpeak(outroText);
      }

      const finalMessages = [...messages, ...newMessages];
      onInterviewComplete?.({
        messages: finalMessages.map((m) => ({ role: m.role, text: m.text })),
        totalQuestions: questionTexts.length,
        answeredQuestions: answers.length,
        duration: timer,
        overallScore: batch?.overall_score,
        overallGrade: batch?.overall_grade,
        summary: batch?.summary,
        evaluations: batch?.evaluations,
        plagiarismSummary: batch?.plagiarism_summary,
        ragReport: ragReport ?? undefined,
      });
    },
    [
      isFinishing,
      answers,
      addAiMessage,
      candidateName,
      resumeData,
      questionTexts.length,
      selectedVoice,
      browserSpeak,
      messages,
      onInterviewComplete,
      timer,
    ],
  );

  const sendMessage = async () => {
    if (isFinishing || isThinking) return;
    const text = input.trim();
    const codeSnippet = codeContext.trim()
      ? `\n\n[Candidate Code Submission]:\n\`\`\`\n${codeContext}\n\`\`\``
      : "";

    if (!text && !codeContext.trim()) return;

    /* Capture final WPM snapshot for this answer before resetting */
    if (liveWpm !== null && liveWpm > 0) {
      const fillers = countFillerWords(text).reduce((s, f) => s + f.count, 0);
      setWpmHistory((prev) => [
        ...prev.slice(-39),
        { wpm: liveWpm, timestamp: timer, fillerCount: fillers },
      ]);
    }

    const displayUserText = [text, codeContext.trim() ? "[Submitted Code]" : ""]
      .filter(Boolean)
      .join("\n");
    setMessages((prev) => [
      ...prev,
      { role: "user", text: displayUserText, timestamp: now() },
    ]);
    resetCurrentAnswerDraft();

    const currentQ = questions[questionIndex];
    const nextQ = questionIndex + 1;

    const payloadText = `${text}${codeSnippet}`;

    const payload: EvaluateAnswerRequest = {
      session_id: sessionIdRef.current,
      question_id: String(currentQ?.id ?? `q_${questionIndex + 1}`),
      question_number: questionIndex + 1,
      question_text: currentQ?.text || "",
      question_category: currentQ?.category || "T",
      answer_text: payloadText,
      resume_context: resumeData,
    };

    setIsThinking(true);
    let evalResult: EvaluationResult | null = null;
    try {
      evalResult = await evaluateAndNext(payload);
    } catch {
      try {
        evalResult = await evaluateAnswer(payload);
      } catch {
        evalResult = null;
      }
    }
    setIsThinking(false);

    setAnswers((prev) => [
      ...prev,
      {
        question_id: payload.question_id,
        question: payload.question_text,
        category: payload.question_category,
        answer: text,
        evaluation: evalResult || undefined,
      },
    ]);

    // RAG proctoring: flag answers that closely match past/canned answers.
    // Best-effort — a failure here must never interrupt the interview.
    if (text.length >= 20) {
      const role =
        (resumeData?.primary_domain as string | undefined) ||
        (payload.question_category as string) ||
        "general";
      detectAnswerSimilarity({
        answer: text,
        role,
        candidate_id: sessionIdRef.current,
      })
        .then((res) => {
          if (res.flagged && res.violation) {
            toast.error(res.violation.message, { duration: 8000 });
          }
        })
        .catch(() => {
          /* proctoring is non-blocking; ignore transient failures */
        });

      // RAG adaptive difficulty: recommend the next question's tier from the
      // candidate's recent answers. Best-effort — surfaced as a hint only, since
      // the question list is pre-generated.
      const recentAnswers = [...answers.map((a) => a.answer), text].slice(-3);
      adjustQuestionDifficulty({
        role,
        recent_answers: recentAnswers,
        current_difficulty: recommendedDifficulty || undefined,
      })
        .then((res) => {
          if (res.recommended_difficulty) {
            setRecommendedDifficulty(res.recommended_difficulty);
          }
        })
        .catch(() => {
          /* adaptive difficulty is non-blocking; ignore transient failures */
        });
    }

    if (evalResult) {
      addAiMessage(`Score: ${evalResult.score}/100 (${evalResult.grade})`);
      addAiMessage(evalResult.feedback || "Evaluation completed.");
      if (evalResult.authenticity_report) {
        addAiMessage(
          `Authenticity check: AI-likeness ${Math.round(evalResult.authenticity_report.ai_generated_score || 0)}/100, plagiarism risk ${Math.round(evalResult.authenticity_report.plagiarism_score || 0)}/100.`,
        );
      }
      const followUp =
        evalResult.followup_question || evalResult.follow_up_question;
      if (followUp) addAiMessage(`Follow-up: ${followUp}`);
    }

    if (nextQ < questionTexts.length) {
      setTimeout(() => {
        const nextText = questionTexts[nextQ];
        addAiMessage(nextText);
        void speakText(nextText, {
          questionNumber: nextQ + 1,
          totalQuestions: questionTexts.length,
        });
        setQuestionIndex(nextQ);
        setHintText(null);
      }, 900);
      return;
    }

    await finalizeInterview(false);
  };

  const startBrowserRecognition = () => {
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SR) {
      return false;
    }

    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = true;

    browserTranscriptRef.current = "";
    browserFinalTranscriptRef.current = "";
    browserRecRef.current = rec;

    rec.onresult = (ev: any) => {
      let interim = "";

      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const chunk = String(ev.results[i][0]?.transcript || "").trim();
        if (!chunk) continue;

        if (ev.results[i].isFinal) {
          browserFinalTranscriptRef.current =
            `${browserFinalTranscriptRef.current} ${chunk}`.trim();
        } else {
          interim = `${interim} ${chunk}`.trim();
        }
      }

      const transcript =
        `${browserFinalTranscriptRef.current} ${interim}`.trim();
      browserTranscriptRef.current = transcript;
      const baseInput = inputBeforeRecordingRef.current.trim();
      const merged = [baseInput, transcript].filter(Boolean).join(" ").trim();
      setInput(merged);
    };

    rec.onend = () => {
      browserRecRef.current = null;
      browserTranscriptRef.current = browserTranscriptRef.current.trim();
      if (
        !mediaRecorderRef.current ||
        mediaRecorderRef.current.state === "inactive"
      ) {
        setIsRecording(false);
      }
    };

    rec.onerror = () => {
      browserRecRef.current = null;
    };

    try {
      rec.start();
      return true;
    } catch {
      browserRecRef.current = null;
      return false;
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      const hadMedia =
        !!mediaRecorderRef.current &&
        mediaRecorderRef.current.state !== "inactive";
      const hadBrowser = !!browserRecRef.current;
      if (hadBrowser) {
        try {
          browserRecRef.current.stop();
        } catch {
          // ignore
        }
      }
      if (hadMedia) {
        mediaRecorderRef.current?.stop();
      } else {
        setIsRecording(false);
      }
      return;
    }

    try {
      inputBeforeRecordingRef.current = input;
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeCandidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg;codecs=opus",
      ];
      let chosenMime = "";
      if (
        typeof MediaRecorder !== "undefined" &&
        typeof MediaRecorder.isTypeSupported === "function"
      ) {
        chosenMime =
          mimeCandidates.find((m) => MediaRecorder.isTypeSupported(m)) || "";
      }
      const mediaRecorder = chosenMime
        ? new MediaRecorder(stream, { mimeType: chosenMime })
        : new MediaRecorder(stream);
      recordedMimeTypeRef.current =
        mediaRecorder.mimeType || chosenMime || "audio/webm";
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, {
          type: recordedMimeTypeRef.current,
        });
        let backendText = "";
        const browserText = (browserTranscriptRef.current || "").trim();
        if (!browserText) {
          try {
            const result = await transcribeAudio(
              audioBlob,
              recordedMimeTypeRef.current,
            );
            backendText = String(result?.text || "").trim();
          } catch {
            backendText = "";
          }
        }
        await new Promise((r) => setTimeout(r, 250));
        const finalText = browserText || backendText;
        if (finalText) {
          const baseInput = inputBeforeRecordingRef.current.trim();
          const merged = [baseInput, finalText]
            .filter(Boolean)
            .join(" ")
            .trim();
          setInput(merged);
        } else {
          toast.error("No speech captured");
        }
        setIsRecording(false);
      };

      const browserStarted = startBrowserRecognition();
      mediaRecorder.start();
      setIsRecording(true);
      toast.info(
        browserStarted
          ? "Recording started with live transcription"
          : "Recording started",
      );
      if (!browserStarted) {
        toast.warning(
          "Live transcription is not available in this environment",
        );
      }
    } catch {
      inputBeforeRecordingRef.current = input;
      const browserStarted = startBrowserRecognition();
      if (browserStarted) {
        setIsRecording(true);
      } else {
        toast.error("Unable to access microphone");
      }
    }
  };

  const handleSkip = () => {
    if (isFinishing) return;
    resetCurrentAnswerDraft();
    const currentQ = questions[questionIndex];
    setAnswers((prev) => [
      ...prev,
      {
        question_id: String(currentQ?.id ?? `q_${questionIndex + 1}`),
        question: currentQ?.text || "",
        category: currentQ?.category || "T",
        answer: "[SKIPPED]",
      },
    ]);

    const nextQ = questionIndex + 1;
    if (nextQ < questionTexts.length) {
      setQuestionIndex(nextQ);
      setHintText(null);
      const nextText = questionTexts[nextQ];
      addAiMessage("Question skipped.");
      addAiMessage(nextText);
      void speakText(nextText, {
        questionNumber: nextQ + 1,
        totalQuestions: questionTexts.length,
      });
    } else {
      void finalizeInterview(true);
    }
  };

  const handleRepeat = () => {
    if (!currentQuestionText) return;
    void speakText(currentQuestionText, {
      questionNumber: questionIndex + 1,
      totalQuestions: questionTexts.length,
    });
  };

  const handleEndInterview = () => {
    if (isFinishing) return;
    setAnswerStartTimer(null);
    void finalizeInterview(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  const handleTextareaInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "42px";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    const attemptFullscreen = async () => {
      try {
        if (!document.fullscreenElement) {
          await document.documentElement.requestFullscreen();
        }
      } catch (err) {
        // Silent catch for elements rejecting un-prompted fullscreen request
      }
    };
    attemptFullscreen();

    const firstClickHandler = () => {
      attemptFullscreen();
      document.removeEventListener("click", firstClickHandler);
    };
    document.addEventListener("click", firstClickHandler);

    // ── Tab switch / visibility detection ─────────────────
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitchCount((prev) => {
          const next = prev + 1;
          toast.error(
            `⚠️ Tab switch #${next} detected! This violation has been recorded.`,
            { duration: 5000 },
          );
          return next;
        });
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // ── Window blur/focus (obscure content) ───────────────
    const handleBlur = () => setIsObscured(true);
    const handleFocus = () => setIsObscured(false);
    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);

    // ── Fullscreen exit detection ─────────────────────────
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        toast.warning(
          "Fullscreen mode is required during the interview. Click anywhere to re-enter.",
          { duration: 6000 },
        );
        // Re-enter on next click
        const reEnter = () => {
          attemptFullscreen();
          document.removeEventListener("click", reEnter);
        };
        document.addEventListener("click", reEnter);
      }
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);

    // ── Right-click context menu blocking ─────────────────
    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      toast.warning("Right-click is disabled during interview.");
    };
    document.addEventListener("contextmenu", handleContextMenu);

    // ── Keyboard: screenshots, DevTools, select-all ──────
    const handleKeyDown = (e: KeyboardEvent) => {
      // PrintScreen
      if (e.key === "PrintScreen") {
        e.preventDefault();
        toast.error("Screenshots are disabled during interview.");
      }
      // macOS screenshots
      if (
        e.metaKey &&
        e.shiftKey &&
        ["3", "4", "5", "s", "S"].includes(e.key)
      ) {
        e.preventDefault();
        toast.error("Screenshots are disabled during interview.");
      }
      // DevTools: F12
      if (e.key === "F12") {
        e.preventDefault();
        toast.error("Developer tools are disabled during interview.");
      }
      // DevTools: Ctrl+Shift+I / Ctrl+Shift+J / Ctrl+Shift+C
      if (
        (e.ctrlKey || e.metaKey) &&
        e.shiftKey &&
        ["i", "I", "j", "J", "c", "C"].includes(e.key)
      ) {
        e.preventDefault();
        toast.error("Developer tools are disabled during interview.");
      }
      // Ctrl+U (view source)
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "u" || e.key === "U") &&
        !e.shiftKey
      ) {
        e.preventDefault();
        toast.error("View source is disabled during interview.");
      }
      // Ctrl+S (save page)
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "s" || e.key === "S") &&
        !e.shiftKey
      ) {
        e.preventDefault();
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    // ── Prevent text selection on question bubbles ────────
    const handleSelectStart = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.closest(".select-none")) {
        e.preventDefault();
      }
    };
    document.addEventListener("selectstart", handleSelectStart);

    return () => {
      document.removeEventListener("click", firstClickHandler);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener("contextmenu", handleContextMenu);
      window.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("selectstart", handleSelectStart);
      // Exit fullscreen cleanly when interview unmounts
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      }
    };
  }, []);

  return (
    <div
      className="flex flex-col relative overflow-x-hidden"
      style={{ height: "calc(100vh - 130px)" }}
    >
      {isObscured && (
        <div className="absolute inset-0 z-[9999] bg-background/95 backdrop-blur-md flex flex-col items-center justify-center text-center p-6 border border-destructive/20 rounded-lg">
          <ShieldAlert className="w-16 h-16 text-destructive mb-4" />
          <h2 className="text-2xl font-bold text-foreground">Content Hidden</h2>
          <p className="text-muted-foreground mt-2 max-w-md">
            The interview window has lost focus. Screenshots and tab changes are
            strictly prohibited. Please return focus to continue.
          </p>
        </div>
      )}
      <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-sm shadow-sm mb-3 overflow-hidden">
        {/* Row 1: live metrics */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex flex-wrap items-center gap-2.5">
            {/* REC / status pill */}
            <div
              className={`text-[10px] font-bold tracking-tight px-3 py-1.5 rounded-full inline-flex items-center gap-1.5 ${
                timerStarted
                  ? "bg-destructive/10 border border-destructive/20 text-destructive"
                  : "bg-muted border border-border text-muted-foreground"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${timerStarted ? "bg-destructive animate-pulse" : "bg-muted-foreground/40"}`}
              />
              {timerStarted ? "REC" : "READY"}
            </div>

            {/* Elapsed timer */}
            <div className="text-base font-semibold tracking-tight px-3.5 py-1.5 rounded-full bg-foreground text-background inline-flex items-center gap-2 tabular-nums">
              <Clock className="w-4 h-4" />
              {formatTime(timer)}
            </div>

            {/* Local clock */}
            <div className="text-xs font-semibold tracking-tight px-3 py-1.5 rounded-full bg-muted border border-border text-muted-foreground inline-flex items-center gap-1.5 tabular-nums">
              {currentTime.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              <span className="text-[9px] text-muted-foreground/60 font-semibold">
                Mumbai
              </span>
            </div>

            {/* Live WPM — hidden during coding questions (typing, not speaking) */}
            {!currentQuestionIsCoding && (
              <div
                aria-live="polite"
                data-testid="live-wpm"
                title={formatPaceLabel(livePaceLabel)}
                className={`text-sm font-semibold tracking-tight px-3 py-1.5 rounded-full border inline-flex items-center gap-1.5 tabular-nums ${getWpmToneClasses(livePaceLabel)}`}
              >
                <Gauge className="w-3.5 h-3.5" />
                {liveWpmText}
              </div>
            )}
          </div>

          {/* Candidate + progress */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/60 border border-border">
              <div className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                <User className="w-3.5 h-3.5" />
              </div>
              <span className="text-sm font-medium text-foreground max-w-[140px] truncate">
                {candidateName}
              </span>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                Question
              </div>
              <div className="text-sm font-semibold tracking-tight text-foreground tabular-nums">
                {Math.min(questionIndex + 1, questionTexts.length)}
                <span className="text-muted-foreground font-normal">
                  {" "}/ {questionTexts.length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1 w-full bg-muted">
          <div
            className="h-full bg-primary transition-all duration-500 ease-out"
            style={{
              width: `${questionTexts.length ? (Math.min(questionIndex, questionTexts.length) / questionTexts.length) * 100 : 0}%`,
            }}
          />
        </div>

        {/* Row 2: status chips + actions */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-t border-border bg-muted/20">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-info/10 border border-info/20 text-info inline-flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> Proctored
            </span>
            {recommendedDifficulty && (
              <span
                title="RAG-recommended difficulty for the next question"
                className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary capitalize"
              >
                Next: {recommendedDifficulty}
              </span>
            )}
            {isSpeaking && (
              <span className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary inline-flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                Speaking
              </span>
            )}
            {tabSwitchCount > 0 && (
              <span className="text-[10px] font-semibold tracking-tight px-2.5 py-1 rounded-full bg-destructive/15 border border-destructive/25 text-destructive">
                ⚠ {tabSwitchCount} violation{tabSwitchCount !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button variant="outline" size="sm" onClick={toggleCamera}>
              {cameraActive ? (
                <CameraOff className="w-4 h-4 mr-1 text-destructive" />
              ) : (
                <Camera className="w-4 h-4 mr-1 text-primary" />
              )}
              Camera
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleGetHint}
              disabled={isHintLoading || !!hintText || isFinishing}
            >
              <Lightbulb
                className={`w-4 h-4 mr-1 ${isHintLoading ? "animate-pulse text-amber-500" : "text-amber-500"}`}
              />{" "}
              Hint
            </Button>
            <Button
              variant={currentQuestionIsCoding && rightPanelMode !== "code" ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setRightPanelMode(rightPanelMode === "code" ? "none" : "code")
              }
            >
              <Code className="w-4 h-4 mr-1" />
              {currentQuestionIsCoding ? "Code Answer" : "Code Pad"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setRightPanelMode(
                  rightPanelMode === "scratch" ? "none" : "scratch",
                )
              }
            >
              <PenTool className="w-4 h-4 mr-1" /> Drawing
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleEndInterview}
              disabled={isFinishing}
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
            >
              <StopCircle className="w-4 h-4 mr-1" /> End
            </Button>
          </div>
        </div>
      </div>

      {/* ── WPM & Filler Panel — hidden during coding questions ── */}
      {!currentQuestionIsCoding && (
        <div className="mb-2">
          <WpmPanel
            liveWpm={liveWpm}
            paceLabel={livePaceLabel}
            wpmHistory={wpmHistory}
            fillerWords={liveFillerWords}
            totalWords={currentAnswerWordCount}
          />
        </div>
      )}

      <div className="px-3.5 py-2 rounded-xl border border-success/20 bg-success/5 text-xs font-medium text-success mb-2 inline-flex items-center gap-2 self-start">
        <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
        {questionReadyMessage}
      </div>

      {hintText && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-4 py-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-sm text-amber-600 mb-3 flex items-start gap-3"
        >
          <Lightbulb className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold mb-1">Hint from AI</div>
            <div className="leading-relaxed">{hintText}</div>
          </div>
        </motion.div>
      )}

      {isRecording && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="flex items-center gap-2.5 px-4 py-2.5 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive mb-2"
        >
          <div className="w-2 h-2 rounded-xl bg-destructive animate-pulse" />
          Recording... speak your answer
          <span className="ml-auto font-semibold tracking-tight text-xs">LIVE</span>
        </motion.div>
      )}

      {currentQuestionIsCoding && !isFinishing ? (
        /* ── Coding question mode: webcam + question on the left, editor on the right ── */
        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row gap-5 min-w-0">
          {/* Left: live webcam with question overlay */}
          <div className="relative flex-1 lg:w-2/5 min-w-0 min-h-[240px] rounded-xl overflow-hidden border border-border bg-muted">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover scale-x-[-1] ${cameraActive ? "block" : "hidden"}`}
            />
            {!cameraActive && (
              <div
                className="absolute inset-0 bg-cover bg-center"
                style={{
                  backgroundImage:
                    "url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80')",
                }}
              >
                <div className="absolute inset-0 bg-black/40" />
              </div>
            )}

            {/* LIVE badge */}
            <div className="absolute top-3 left-3 z-10 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-destructive/90 text-white text-[11px] font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              LIVE
            </div>
            {/* AI Interviewer badge */}
            <div className="absolute top-3 right-3 z-10 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/70 text-white text-[11px] font-semibold">
              <Bot className="w-3 h-3" /> AI Interviewer
            </div>

            {/* Current question overlay */}
            <div className="absolute bottom-3 left-3 right-3 z-10 rounded-xl bg-neutral-700/80 backdrop-blur-sm p-4 select-none">
              <div className="text-[10px] font-bold tracking-widest uppercase text-white/60 mb-1.5">
                Current Question
              </div>
              <div className="text-sm font-semibold text-white leading-relaxed">
                {currentQuestionText}
              </div>
            </div>
          </div>

          {/* Right: code editor — drag the bottom-right corner to resize width & height */}
          {/* Right: code editor — drag any edge or corner to resize */}
          <ResizablePanel
            minWidth={320}
            minHeight={280}
            className="w-full h-[50vh] lg:w-[55%] lg:h-full lg:shrink-0 flex flex-col border border-border rounded-xl overflow-hidden bg-card shadow-sm"
          >
            <div className="px-4 py-2.5 border-b border-border bg-muted/30 flex items-center justify-between">
              <span className="text-sm font-semibold text-foreground flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-success inline-block" />
                editor.py
              </span>
              <span className="text-xs font-medium text-muted-foreground px-2 py-0.5 rounded-md border border-border bg-card">
                Python 3.10
              </span>
            </div>
            <CodePadEditor
              value={codeContext}
              onChange={setCodeContext}
              autoFocus
              placeholder={
                "class Solution:\n    def solve(self):\n        # Write your code here\n        pass"
              }
              onBlockedKeyDown={onKeyboardShortcutBlocked}
              onBlockedPaste={onPasteBlocked}
              onBlockedCopyCut={onCopyCutBlocked}
            />
            {(runResult || isRunningCode) && (
              <div className="h-40 min-h-[3rem] max-h-[70%] resize-y overflow-auto border-t border-border bg-muted/20 px-4 py-2.5">
                <div className="mb-1.5 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                  Output
                  {isRunningCode ? (
                    <span className="text-muted-foreground normal-case tracking-normal font-medium">Running…</span>
                  ) : runResult?.timed_out ? (
                    <span className="text-destructive normal-case tracking-normal font-medium">Timed out</span>
                  ) : runResult?.success ? (
                    <span className="text-success normal-case tracking-normal font-medium">Success</span>
                  ) : (
                    <span className="text-destructive normal-case tracking-normal font-medium">Error</span>
                  )}
                </div>
                {runResult?.stdout && (
                  <pre className="whitespace-pre-wrap font-sans text-sm text-foreground/90 leading-relaxed">{runResult.stdout}</pre>
                )}
                {runResult?.stderr && (
                  <pre className="whitespace-pre-wrap font-sans text-sm text-destructive leading-relaxed">{runResult.stderr}</pre>
                )}
                {runResult && !runResult.stdout && !runResult.stderr && !isRunningCode && (
                  <p className="text-sm text-foreground/70 font-medium leading-relaxed">No output — add a print() to see results.</p>
                )}
              </div>
            )}
            <div className="px-4 py-2.5 border-t border-border bg-muted/20 flex items-center justify-between gap-3 text-xs text-muted-foreground">
              <span className="tabular-nums">
                Lines: {codeContext ? codeContext.split("\n").length : 0} Chars:{" "}
                {codeContext.length}
              </span>
              <div className="flex items-center gap-2">
                <span className="font-semibold tracking-tight px-2 py-0.5 rounded-md bg-success/10 border border-success/20 text-success">
                  {codeContext.trim() ? "Auto-saving…" : "Ready"}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void handleRunCode()}
                  disabled={!codeContext.trim() || isRunningCode}
                  title="Run your code and check the output before submitting"
                >
                  <Play className="w-3.5 h-3.5 mr-1.5" />
                  {isRunningCode ? "Running…" : "Run"}
                </Button>
                <Button
                  variant="surface"
                  size="sm"
                  onClick={handleSkip}
                  disabled={isFinishing}
                >
                  <SkipForward className="w-3.5 h-3.5 mr-1.5" /> Skip
                </Button>
                <Button
                  size="sm"
                  onClick={() => void sendMessage()}
                  disabled={!codeContext.trim() || isFinishing || isThinking}
                  title="Submit your code for AI evaluation"
                >
                  <Send className="w-3.5 h-3.5 mr-1.5" />
                  {isThinking ? "Evaluating…" : "Submit Code"}
                </Button>
              </div>
            </div>
          </ResizablePanel>
        </div>
      ) : (
      <div
        ref={splitContainerRef}
        className="flex-1 overflow-hidden flex flex-col lg:flex-row gap-5 min-w-0"
      >
        {/* Visual Sidebar removed in favor of draggable PiP widget */}

        <div
          className={`flex flex-col flex-1 h-full min-w-0 ${rightPanelMode !== "none" ? "lg:w-1/2" : ""}`}
          style={
            rightPanelMode !== "none" && isLgScreen
              ? { flex: `0 0 ${splitPct}%` }
              : undefined
          }
        >
          <div
            ref={chatRef}
            className="flex-1 overflow-y-auto py-3 flex flex-col gap-3"
            onCopy={onCopyCutBlocked}
            onCut={onCopyCutBlocked}
          >
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-2.5 max-w-[85%] ${msg.role === "user" ? "self-end flex-row-reverse" : "self-start"}`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center text-sm flex-shrink-0 ${msg.role === "ai" ? "bg-primary/10 text-primary" : "bg-success/10 text-success"}`}
                >
                  {msg.role === "ai" ? (
                    <LogoStack className="w-4 h-4" />
                  ) : (
                    <User className="w-4 h-4" />
                  )}
                </div>
                <div
                  className={`px-4 py-3 rounded-2xl text-sm leading-relaxed border ${msg.role === "ai" ? "bg-muted/50 border-border rounded-tl-sm select-none" : "bg-success/5 border-success/15 rounded-tr-sm"}`}
                  onCopy={
                    msg.role === "ai" ? onQuestionInteractionBlocked : undefined
                  }
                  onCut={
                    msg.role === "ai" ? onQuestionInteractionBlocked : undefined
                  }
                  onContextMenu={
                    msg.role === "ai" ? onQuestionInteractionBlocked : undefined
                  }
                  onDragStart={
                    msg.role === "ai" ? onQuestionInteractionBlocked : undefined
                  }
                >
                  <span className="text-foreground">{msg.text}</span>
                  <div className="text-[10px] text-muted-foreground/60 mt-1.5">
                    {msg.timestamp}
                  </div>
                </div>
              </motion.div>
            ))}

            {isThinking && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-2.5 self-start"
              >
                <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                  <LogoStack className="w-4 h-4" />
                </div>
                <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-muted/50 border border-border text-foreground">
                  Thinking...
                </div>
              </motion.div>
            )}
          </div>

          {batchResult && (
            <div className="text-xs text-muted-foreground border border-border rounded-md p-2 mb-2 bg-muted/30">
              Final: {batchResult.overall_score}/100 (
              {batchResult.overall_grade})
            </div>
          )}

          <div className="flex gap-2 py-3 border-t border-border items-end mt-auto">
            <Button
              aria-label="Repeat question"
              variant="surface"
              size="icon"
              onClick={handleRepeat}
              disabled={!currentQuestionText || isFinishing}
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
            <Button
              aria-label="Skip question"
              variant="surface"
              size="icon"
              onClick={handleSkip}
              disabled={isFinishing}
            >
              <SkipForward className="w-4 h-4" />
            </Button>

            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                if (answerEndTimer !== null) setAnswerEndTimer(null);
                setInput(e.target.value);
              }}
              onKeyDown={(e) => {
                onKeyboardShortcutBlocked(e);
                handleKeyDown(e);
              }}
              onInput={handleTextareaInput}
              onPaste={onPasteBlocked}
              onCopy={onCopyCutBlocked}
              onCut={onCopyCutBlocked}
              onDrop={(e) => {
                e.preventDefault();
                toast.warning("Dropping text is disabled during interview.");
              }}
              placeholder="Type your spoken answer..."
              className="flex-1 resize-none border border-border rounded-lg px-3.5 py-2.5 text-sm bg-muted/50 text-foreground outline-none transition-all duration-200 focus:border-primary focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground min-h-[42px] max-h-[120px]"
              rows={1}
              disabled={isFinishing}
            />

            <Button
              aria-label={isRecording ? "Stop recording" : "Start recording"}
              variant="surface"
              size="icon"
              onClick={toggleRecording}
              className={
                isRecording
                  ? "bg-destructive text-destructive-foreground border-destructive"
                  : ""
              }
              disabled={isFinishing}
            >
              {isRecording ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </Button>

            <Button
              aria-label="Send answer"
              size="icon"
              onClick={() => void sendMessage()}
              disabled={(!input.trim() && !codeContext.trim()) || isFinishing || isThinking}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Draggable divider — only meaningful on lg+ when a right panel is open */}
        {rightPanelMode !== "none" && (
          <div
            onPointerDown={startSplitDrag}
            role="separator"
            aria-orientation="vertical"
            title="Drag to resize"
            className="hidden lg:flex items-center justify-center w-2 shrink-0 cursor-col-resize group"
          >
            <div className="h-16 w-1 rounded-full bg-border transition-colors group-hover:bg-primary" />
          </div>
        )}

        {/* Right Panel Area */}
        <div
          className={`flex-1 h-[40vh] md:h-full md:w-1/2 min-w-0 flex-col border border-border rounded-xl overflow-hidden bg-card shadow-sm relative ${rightPanelMode === "code" ? "flex" : "hidden"}`}
        >
          <div className="px-4 py-2.5 border-b border-border bg-muted/30 flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-success inline-block" />
              editor.py
            </span>
            <span className="text-xs font-medium text-muted-foreground px-2 py-0.5 rounded-md border border-border bg-card">
              Python 3.10
            </span>
          </div>
          <CodePadEditor
            value={codeContext}
            onChange={setCodeContext}
            placeholder={"class Solution:\n    def solve(self):\n        # Write your code here\n        pass"}
            onBlockedKeyDown={onKeyboardShortcutBlocked}
            onBlockedPaste={onPasteBlocked}
            onBlockedCopyCut={onCopyCutBlocked}
          />
          {(runResult || isRunningCode) && (
            <div className="h-32 min-h-[3rem] max-h-[70%] resize-y overflow-auto border-t border-border bg-muted/20 px-4 py-2.5">
              <div className="mb-1.5 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Output
                {isRunningCode ? (
                  <span className="text-muted-foreground normal-case tracking-normal font-medium">Running…</span>
                ) : runResult?.timed_out ? (
                  <span className="text-destructive normal-case tracking-normal font-medium">Timed out</span>
                ) : runResult?.success ? (
                  <span className="text-success normal-case tracking-normal font-medium">Success</span>
                ) : (
                  <span className="text-destructive normal-case tracking-normal font-medium">Error</span>
                )}
              </div>
              {runResult?.stdout && (
                <pre className="whitespace-pre-wrap font-sans text-sm text-foreground/90 leading-relaxed">{runResult.stdout}</pre>
              )}
              {runResult?.stderr && (
                <pre className="whitespace-pre-wrap font-sans text-sm text-destructive leading-relaxed">{runResult.stderr}</pre>
              )}
              {runResult && !runResult.stdout && !runResult.stderr && !isRunningCode && (
                <p className="text-sm text-foreground/70 font-medium leading-relaxed">No output — add a print() to see results.</p>
              )}
            </div>
          )}
          <div className="px-4 py-2.5 border-t border-border bg-muted/20 flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <span className="tabular-nums">
              Lines: {codeContext ? codeContext.split("\n").length : 0} Chars:{" "}
              {codeContext.length}
            </span>
            <div className="flex items-center gap-2">
              <span className="font-semibold tracking-tight px-2 py-0.5 rounded-md bg-success/10 border border-success/20 text-success">
                {codeContext.trim() ? "Auto-saving…" : "Ready"}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void handleRunCode()}
                disabled={!codeContext.trim() || isRunningCode}
                title="Run your code and check the output before submitting"
              >
                <Play className="w-3.5 h-3.5 mr-1.5" />
                {isRunningCode ? "Running…" : "Run"}
              </Button>
              <Button
                size="sm"
                onClick={() => void sendMessage()}
                disabled={!codeContext.trim() || isFinishing || isThinking}
                title="Submit your code for AI evaluation"
              >
                <Send className="w-3.5 h-3.5 mr-1.5" />
                Submit Code
              </Button>
            </div>
          </div>
        </div>

        <div
          className={`flex-1 h-[40vh] md:h-full md:w-1/2 min-w-0 flex-col border border-border rounded-xl overflow-hidden bg-card shadow-sm relative ${rightPanelMode === "scratch" ? "flex" : "hidden"}`}
        >
          <div className="px-4 py-2 border-b border-border bg-muted/30 flex items-center justify-between z-20 shadow-sm">
            <span className="text-sm font-semibold text-foreground flex items-center gap-2">
              <PenTool className="w-4 h-4 text-primary" /> Notes & Drawing
            </span>
            <span className="text-xs text-muted-foreground">
              Notes or draw formulas
            </span>
          </div>
          <div className="flex-1 relative w-full h-full overflow-hidden">
            <ScratchPad defaultTab="note" />
          </div>
        </div>

        {/* Draggable Unified Interview Widget (Granola-style Picture-in-Picture) */}
        <motion.div
          drag
          dragMomentum={false}
          dragElastic={0.05}
          initial={{ x: 0, y: 0 }}
          className="fixed z-50 bottom-6 right-6 w-[240px] rounded-2xl border border-border/80 bg-background/95 backdrop-blur-md shadow-2xl p-3 flex flex-col gap-3 cursor-grab active:cursor-grabbing hover:shadow-brand/10 transition-shadow select-none overflow-hidden"
        >
          {/* Widget Top Bar / Drag Handle */}
          <div className="flex items-center justify-between border-b border-border pb-1.5 text-[9px] font-medium text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="font-bold tracking-wider uppercase">Proctor Feed</span>
            </div>
            <span className="text-[8px] bg-card border border-border/60 px-1.5 py-0.5 rounded uppercase tracking-wider text-muted-foreground select-none">
              Drag to Move
            </span>
          </div>

          {/* Video feed container */}
          <div className="relative aspect-[4/3] w-full rounded-xl overflow-hidden border border-border/60 bg-muted">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover scale-x-[-1] ${cameraActive ? "block" : "hidden"}`}
            />
            {!cameraActive && (
              <div 
                className="absolute inset-0 bg-cover bg-center" 
                style={{ backgroundImage: "url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=400&q=80')" }}
              >
                <div className="absolute inset-0 bg-black/60 backdrop-blur-[0.5px]" />
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-3">
                  <span className="text-white/80 text-[10px] font-semibold">Webcam Inactive</span>
                  <span className="text-[8px] text-white/40 mt-0.5 max-w-[160px]">Camera required for validation</span>
                </div>
              </div>
            )}

            {/* Candidate Badge */}
            <div className="absolute bottom-2 left-2 z-10 flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-black/70 text-white text-[8px] font-semibold tracking-tight">
              <div className={`w-1.5 h-1.5 rounded-full ${cameraActive ? "bg-green-500 animate-pulse" : "bg-white/40"}`} />
              {candidateName}
            </div>
          </div>

          {/* AI Waveform & State Indicator */}
          <div className="bg-card border border-border/60 rounded-xl p-2.5 flex flex-col items-center justify-center gap-1.5">
            {/* Speaking Waveform */}
            {isSpeaking ? (
              <div className="flex items-center gap-1 h-6">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <motion.div
                    key={i}
                    animate={{ height: [6, 18, 6] }}
                    transition={{
                      duration: 0.6 + i * 0.05,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    className="w-1 rounded-full bg-[hsl(var(--brand))]"
                  />
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-1 h-6">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <div key={i} className="w-1 h-1.5 rounded-full bg-muted-foreground/30" />
                ))}
              </div>
            )}

            <div className="flex items-center justify-between w-full text-[9px] font-medium text-muted-foreground pt-1 border-t border-border/40">
              <span>AI Status:</span>
              <span className={`font-semibold ${isSpeaking ? "text-brand" : "text-muted-foreground"}`}>
                {isSpeaking ? "Speaking..." : "Listening..."}
              </span>
            </div>
          </div>
        </motion.div>
      </div>
      )}
    </div>
  );
}
