import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import InterviewPage from "@/components/InterviewPage";
import ResultsPage, { type InterviewResult } from "@/components/ResultsPage";
import { generateQuestionsFromResumeData } from "@/lib/api";
import { getItem, setItem } from "@/lib/indexedDB";
import type { GeneratedQuestion } from "./Index";
import { toast } from "sonner";

const TRY_KEY = "interviewer_try_interview_questions";

type TryStage = "idle" | "loading" | "ready" | "results";

const MOCK_RESUME_CONTEXT: Record<string, unknown> = {
  name: "Try Candidate",
  summary: "Full-stack engineer focused on React, TypeScript, and Python backend systems.",
  experience: [
    {
      title: "Software Engineer",
      company: "Demo Corp",
      duration: "3 years",
      responsibilities: [
        "Built production web features with React and TypeScript",
        "Designed backend APIs with Python and FastAPI",
      ],
    },
  ],
  skills: ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL", "Docker"],
  projects: [
    {
      name: "Interview Assistant",
      description: "An AI-powered interview simulator with speech support",
      techs: ["React", "FastAPI", "LLM"],
    },
  ],
};

async function loadTryQuestions() {
  try {
    const raw = await getItem<GeneratedQuestion[]>(TRY_KEY);
    if (!raw) return [] as GeneratedQuestion[];
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [] as GeneratedQuestion[];
  }
}

export default function TryInterview() {
  const [searchParams] = useSearchParams();
  const isTryInterview = searchParams.get("try") === "interview";

  const [stage, setStage] = useState<TryStage>("idle");
  const [questions, setQuestions] = useState<GeneratedQuestion[]>([]);
  const [result, setResult] = useState<InterviewResult | null>(null);

  const candidateName = useMemo(() => String(MOCK_RESUME_CONTEXT.name || "Candidate"), []);

  useEffect(() => {
    if (!isTryInterview) {
      setStage("idle");
      return;
    }

    const boot = async () => {
      setStage("loading");
      const cachedQuestions = await loadTryQuestions();
      if (cachedQuestions.length === 15) {
        setQuestions(cachedQuestions);
        setStage("ready");
        toast.success("Loaded 15 cached test questions from IndexedDB.");
        return;
      }

      try {
        const generated = await generateQuestionsFromResumeData(MOCK_RESUME_CONTEXT, 15);
        const nextQuestions = generated.questions.slice(0, 15);

        if (nextQuestions.length < 15) {
          toast.warning(`LLM returned ${nextQuestions.length} questions (expected 15).`);
        }

        await setItem(TRY_KEY, nextQuestions);
        setQuestions(nextQuestions);
        setStage("ready");
        toast.success(`Generated ${nextQuestions.length} test questions and saved to IndexedDB.`);
      } catch (error) {
        setStage("idle");
        console.error("[try=interview] failed to generate questions", error);
        toast.error("Try interview mode failed to initialize. Check /questions/generate backend logs.");
      }
    };

    void boot();
  }, [isTryInterview]);

  if (!isTryInterview) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 text-center">
        <div className="max-w-xl rounded-2xl border border-black/10 bg-white p-6">
          <h1 className="text-xl font-semibold">Try interview mode</h1>
          <p className="text-sm text-black/50 mt-2">
            Open this route with <code className="font-mono">?try=interview</code> to run the interview page in isolated test mode.
          </p>
        </div>
      </div>
    );
  }

  if (stage === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 text-center">
        <div className="max-w-xl rounded-2xl border border-black/10 bg-white p-6">
          <h1 className="text-xl font-semibold">Preparing test interview</h1>
          <p className="text-sm text-black/50 mt-2">
            Requesting 15 questions from LLM and caching them in IndexedDB ({TRY_KEY}).
          </p>
        </div>
      </div>
    );
  }

  if (stage === "results" && result) {
    return (
      <ResultsPage
        result={result}
        resumeData={MOCK_RESUME_CONTEXT}
        questions={questions}
        onRestart={() => window.location.reload()}
      />
    );
  }

  if (stage === "ready") {
    return (
      <InterviewPage
        candidateName={candidateName}
        resumeData={MOCK_RESUME_CONTEXT}
        questions={questions}
        onInterviewComplete={(data) => {
          setResult({
            candidateName,
            ...data,
          });
          setStage("results");
        }}
      />
    );
  }

  return null;
}
