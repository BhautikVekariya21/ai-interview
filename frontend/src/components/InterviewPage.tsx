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
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import ScratchPad from "./ScratchPad";
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
  type EvaluationResult,
  type EvaluateAnswerRequest,
  type BatchEvaluationResult,
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
  const [cameraActive, setCameraActive] = useState(false);
  const [hintText, setHintText] = useState<string | null>(null);
  const [isHintLoading, setIsHintLoading] = useState(false);
  const [isObscured, setIsObscured] = useState(false);
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [answerStartTimer, setAnswerStartTimer] = useState<number | null>(null);
  const [wpmHistory, setWpmHistory] = useState<WpmSnapshot[]>([]);
  const [currentTime, setCurrentTime] = useState(() => new Date());

  const chatRef = useRef<HTMLDivElement>(null);
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
  const wpmSnapshotRef = useRef<ReturnType<typeof setInterval>>();

  const questionTexts = (questions || []).map((q) => q.text);
  const currentQuestionText = questionTexts[questionIndex] || "";
  const currentAnswerWordCount = countInterviewWords(input);
  const currentAnswerElapsedSeconds =
    answerStartTimer === null ? 0 : Math.max(timer - answerStartTimer, 0);
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
  }, [questionIndex]);

  useEffect(() => {
    if (currentAnswerWordCount === 0) {
      if (answerStartTimer !== null) {
        setAnswerStartTimer(null);
      }
      return;
    }

    setAnswerStartTimer((prev) => prev ?? timer);
  }, [currentAnswerWordCount, answerStartTimer, timer]);

  /* ── Snapshot WPM every 5 seconds while typing ───────── */
  useEffect(() => {
    if (wpmSnapshotRef.current) {
      clearInterval(wpmSnapshotRef.current);
      wpmSnapshotRef.current = undefined;
    }

    if (liveWpm !== null && liveWpm > 0) {
      wpmSnapshotRef.current = setInterval(() => {
        const words = countInterviewWords(input);
        const elapsed = answerStartTimer === null ? 0 : Math.max(timer - answerStartTimer, 0);
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

  const startTimer = useCallback(() => {
    if (!timerStarted) setTimerStarted(true);
  }, [timerStarted]);

  const resetCurrentAnswerDraft = useCallback(() => {
    setInput("");
    setAnswerStartTimer(null);
    browserTranscriptRef.current = "";
    browserFinalTranscriptRef.current = "";
    inputBeforeRecordingRef.current = "";
    if (textareaRef.current) {
      textareaRef.current.style.height = "42px";
    }
  }, []);

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
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        }, 50);
      } catch (err) {
        toast.error("Failed to access camera. Check permissions.");
      }
    }
  };

  useEffect(() => {
    onStateChange?.(messages, questionIndex, timer);
  }, [messages, questionIndex, timer, onStateChange]);

  useEffect(() => {
    const handler = () => onStateChange?.(messages, questionIndex, timer);
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [messages, questionIndex, timer, onStateChange]);

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
        startTimer();
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
    startTimer,
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
      });
    },
    [
      isFinishing,
      answers,
      addAiMessage,
      candidateName,
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
      className="flex flex-col relative"
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
      <div className="flex flex-wrap items-center justify-between gap-3 py-3 border-b border-border mb-2">
        <div className="flex flex-wrap items-center gap-3 md:gap-4">
          {/* REC indicator */}
          <div className="font-mono text-[10px] font-bold px-3 py-1 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive inline-flex items-center gap-1.5 animate-pulse">
            <div className="w-2 h-2 rounded-full bg-destructive" />
            REC
          </div>
          <div className="font-mono text-sm font-semibold px-3 py-1 rounded-xl bg-muted border border-border text-foreground">
            <Clock className="w-3.5 h-3.5 inline mr-1.5" />
            {formatTime(timer)}
          </div>
          <div className="font-mono text-xs px-3 py-1 rounded-xl bg-muted border border-border text-muted-foreground inline-flex items-center gap-1.5">
            <Globe className="w-3 h-3" />
            {currentTime.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            <span className="text-[9px] text-muted-foreground/60 font-semibold">
              {Intl.DateTimeFormat().resolvedOptions().timeZone.split("/").pop()?.replace(/_/g, " ") ?? ""}
            </span>
          </div>
          <div
            aria-live="polite"
            data-testid="live-wpm"
            title={formatPaceLabel(livePaceLabel)}
            className={`font-mono text-sm font-semibold px-3 py-1 rounded-xl border inline-flex items-center gap-1.5 ${getWpmToneClasses(livePaceLabel)}`}
          >
            <Gauge className="w-3.5 h-3.5" />
            {liveWpmText}
          </div>
          <span className="text-sm text-muted-foreground">
            <User className="w-3.5 h-3.5 inline mr-1" />
            {candidateName}
          </span>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          {/* Proctoring status */}
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-xl bg-info/10 border border-info/20 text-info inline-flex items-center gap-1">
            <ShieldAlert className="w-3 h-3" /> Proctored
          </span>
          <span className="text-xs text-muted-foreground">
            Q{Math.min(questionIndex + 1, questionTexts.length)}/
            {questionTexts.length}
          </span>
          {isSpeaking && (
            <span className="text-xs text-primary">Speaking...</span>
          )}
          {tabSwitchCount > 0 && (
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-xl bg-destructive/15 border border-destructive/25 text-destructive">
              ⚠ {tabSwitchCount} violation{tabSwitchCount !== 1 ? "s" : ""}
            </span>
          )}
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
            variant="outline"
            size="sm"
            onClick={() =>
              setRightPanelMode(rightPanelMode === "code" ? "none" : "code")
            }
          >
            <Code className="w-4 h-4 mr-1" /> Code Pad
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
          >
            <StopCircle className="w-4 h-4 mr-1" /> End
          </Button>
        </div>
      </div>

      {/* ── WPM & Filler Panel ─────────────────────────── */}
      <div className="mb-2">
        <WpmPanel
          liveWpm={liveWpm}
          paceLabel={livePaceLabel}
          wpmHistory={wpmHistory}
          fillerWords={liveFillerWords}
          totalWords={currentAnswerWordCount}
        />
      </div>

      <div className="px-3 py-2 rounded-lg border border-success/30 bg-success/10 text-xs text-success mb-2">
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
          <span className="ml-auto font-mono font-semibold text-xs">LIVE</span>
        </motion.div>
      )}

      <div
        className={`flex-1 overflow-hidden flex ${rightPanelMode !== "none" ? "flex-col md:flex-row gap-4" : ""}`}
      >
        <div
          className={`flex flex-col flex-1 h-full min-w-0 ${rightPanelMode !== "none" ? "md:w-1/2" : "w-full"}`}
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
                    <Bot className="w-4 h-4" />
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
                  <Bot className="w-4 h-4" />
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
              onChange={(e) => setInput(e.target.value)}
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

        {/* Right Panel Area */}
        <div
          className={`flex-1 h-[40vh] md:h-full md:w-1/2 flex-col border border-border rounded-xl overflow-hidden bg-card shadow-sm relative ${rightPanelMode === "code" ? "flex" : "hidden"}`}
        >
          <div className="px-4 py-2 border-b border-border bg-muted/30 flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Code className="w-4 h-4 text-primary" /> Integrated Code Pad
            </span>
            <span className="text-xs text-muted-foreground">
              Will be evaluated with your answer
            </span>
          </div>
          <textarea
            className="flex-1 w-full bg-transparent p-4 font-mono text-sm text-foreground resize-none focus:outline-none focus:ring-inset focus:ring-1 focus:ring-primary/50 placeholder:text-muted-foreground"
            value={codeContext}
            onChange={(e) => setCodeContext(e.target.value)}
            onKeyDown={onKeyboardShortcutBlocked}
            onPaste={onPasteBlocked}
            onCopy={onCopyCutBlocked}
            onCut={onCopyCutBlocked}
            onDrop={(e) => {
              e.preventDefault();
              toast.warning("Dropping text is disabled during interview.");
            }}
            placeholder="// Write your code, queries, or pseudocode here..."
          />
        </div>

        <div
          className={`flex-1 h-[40vh] md:h-full md:w-1/2 flex-col border border-border rounded-xl overflow-hidden bg-card shadow-sm relative ${rightPanelMode === "scratch" ? "flex" : "hidden"}`}
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

        {cameraActive && (
          <div className="absolute top-4 right-4 md:bottom-20 md:top-auto w-48 h-36 bg-black rounded-xl overflow-hidden border border-border shadow-lg z-[100] transition-transform hover:scale-105 cursor-default group">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover scale-x-[-1]"
            />
            {/* Live proctoring badge */}
            <div className="absolute bottom-2 left-2 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-black/60 text-white text-[9px] font-mono font-bold">
              <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              LIVE
            </div>
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                size="icon"
                variant="ghost"
                className="h-6 w-6 rounded-xl bg-black/50 text-white hover:bg-destructive"
                onClick={toggleCamera}
              >
                <CameraOff className="w-3 h-3" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
