import { useState } from "react";
import { m as motion } from "framer-motion";
import {
  Upload,
  FileText,
  Trash2,
  Zap,
  Brain,
  Target,
  MessageSquare,
  Award,
  Settings2,
  EyeOff,
  ScanSearch,
  ArrowRight,
  Clock,
  ListChecks,
  BarChart3,
  Gauge,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import Loading from "@/components/Loading";
import {
  uploadResume,
  generateQuestions,
  type AuthenticityReport,
  type AtsReport,
} from "@/lib/api";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import type { GeneratedQuestion } from "@/pages/Index";

interface ParsedResume {
  name: string;
  email: string;
  phone: string;
  location: string;
  summary: string;
  experience: {
    title: string;
    company: string;
    duration: string;
    responsibilities: string[];
  }[];
  skills: string[];
  education: { degree: string; school: string; year: string }[];
  projects: { name: string; description: string; techs: string[] }[];
  certifications: string[];
}

const MOCK_RESUME: ParsedResume = {
  name: "Alex Chen",
  email: "alex.chen@email.com",
  phone: "+1 (555) 987-6543",
  location: "San Francisco, CA",
  summary:
    "Senior full-stack engineer with 6+ years building scalable web applications. Passionate about system design, developer tooling, and clean architecture.",
  experience: [
    {
      title: "Senior Software Engineer",
      company: "TechCorp · 2021 – Present",
      duration: "3 years",
      responsibilities: [
        "Led migration of monolith to microservices, reducing deploy times by 70%",
        "Architected real-time data pipeline processing 2M+ events/day",
        "Mentored team of 5 junior engineers",
      ],
    },
    {
      title: "Software Engineer",
      company: "StartupXYZ · 2018 – 2021",
      duration: "3 years",
      responsibilities: [
        "Built customer-facing dashboard used by 50K+ users",
        "Implemented CI/CD pipeline reducing release cycle from 2 weeks to 2 days",
      ],
    },
  ],
  skills: [
    "TypeScript",
    "React",
    "Node.js",
    "Python",
    "PostgreSQL",
    "AWS",
    "Docker",
    "Kubernetes",
    "GraphQL",
    "Redis",
    "System Design",
    "CI/CD",
  ],
  education: [
    { degree: "B.S. Computer Science", school: "UC Berkeley", year: "2018" },
  ],
  projects: [
    {
      name: "OpenTrace",
      description:
        "Distributed tracing tool for microservices with real-time visualization",
      techs: ["Go", "React", "gRPC", "Jaeger"],
    },
    {
      name: "CodeReview Bot",
      description: "AI-powered code review assistant for GitHub PRs",
      techs: ["Python", "OpenAI", "GitHub API"],
    },
  ],
  certifications: ["AWS Solutions Architect", "Kubernetes CKAD"],
};

type Stage = "upload" | "processing" | "generating" | "results";

const QUICK_ACTIONS = [
  {
    title: "New Interview",
    desc: "Upload your resume and start a personalized mock interview.",
    icon: <MessageSquare className="w-5 h-5" />,
    color: "text-primary",
  },
  {
    title: "History",
    desc: "Review past interview sessions and track how your scores improve over time.",
    icon: <ListChecks className="w-5 h-5" />,
    color: "text-success",
    href: "/app/history",
  },
  {
    title: "View Analytics",
    desc: "Track your interview readiness score, pacing, and overall progress.",
    icon: <BarChart3 className="w-5 h-5" />,
    color: "text-info",
    href: "/app/analytics",
  },
];

export default function UploadPage({
  onStartInterview,
}: {
  onStartInterview: (
    resume: ParsedResume,
    questions: GeneratedQuestion[],
  ) => void;
}) {
  const [stage, setStage] = useState<Stage>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [difficulty, setDifficulty] = useState<string>("");
  const [numQuestions, setNumQuestions] = useState<number>(15);
  const [selectedCats, setSelectedCats] = useState<string[]>([
    "T",
    "P",
    "B",
    "C",
    "R",
  ]);
  const [biasFree, setBiasFree] = useState<boolean>(false);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [dragover, setDragover] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeStep, setActiveStep] = useState(0);
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null);
  const [generatedQs, setGeneratedQs] = useState<GeneratedQuestion[]>([]);
  const [generationDone, setGenerationDone] = useState(false);
  const [plagiarismReport, setPlagiarismReport] =
    useState<AuthenticityReport | null>(null);
  const [atsReport, setAtsReport] = useState<AtsReport | null>(null);

  const steps = [
    "Extracting text content",
    "Identifying sections",
    "Parsing structured data",
    "Running AI analysis",
    "Generating profile",
    "Generating interview questions",
  ];

  const handleFile = (f: File) => {
    setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragover(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const [parseTime, setParseTime] = useState<number | null>(null);
  const [confidenceFromApi, setConfidenceFromApi] = useState<number>(94);

  const startProcessing = async () => {
    if (!file) return;

    setStage("processing");
    setGenerationDone(false);
    setProgress(0);
    setActiveStep(0);

    const stepDuration = 600;

    // Animate first 5 steps
    for (let i = 0; i < 5; i++) {
      setTimeout(
        () => {
          setActiveStep(i);
          setProgress(((i + 1) / steps.length) * 100);
        },
        stepDuration * (i + 1),
      );
    }

    try {
      // Step 1: Parse resume
      const result = await uploadResume(file, jobDescription);
      setParseTime(result.parse_time);
      setConfidenceFromApi(Math.round(result.confidence_score));
      setParsedResume(result.data);
      setPlagiarismReport(result.plagiarism_report);
      setAtsReport(result.ats_report);

      // Step 2: Generate questions from parsed resume
      const waitForSteps = Math.max(0, stepDuration * 5 - 500);
      await new Promise((r) => setTimeout(r, waitForSteps));
      setActiveStep(5);
      setProgress(90);
      setStage("generating");

      toast.info("Generating personalized interview questions...");
      const questionsResult = await generateQuestions(
        file,
        jobDescription,
        difficulty,
        selectedCats.join(","),
        biasFree,
        numQuestions,
      );
      const rawQuestions = questionsResult.questions?.questions || [];
      const mappedQuestions: GeneratedQuestion[] = rawQuestions.map((q) => ({
        id: q.id,
        text: q.question,
        category: q.category,
        difficulty: q.difficulty,
      }));
      setGeneratedQs(mappedQuestions);
      setProgress(100);
      setGenerationDone(true);
      setStage("results");

      toast.success(`Generated ${mappedQuestions.length} interview questions!`);

    } catch (err) {
      console.error("Processing failed:", err);
      toast.error(
        "Failed to process resume or generate questions. Check backend connection.",
      );
      setStage("upload");
    }
  };

  const removeFile = () => {
    setFile(null);
    setStage("upload");
    setPlagiarismReport(null);
  };

  const confidenceScore = confidenceFromApi;
  const circumference = 2 * Math.PI * 34;
  const offset = circumference - (confidenceScore / 100) * circumference;

  return (
    <div className="mx-auto w-full max-w-5xl">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3">
          New <span className="bg-gradient-to-r from-brand to-[hsl(var(--chart-3))] bg-clip-text text-transparent">Interview</span>
        </h1>
        <p className="text-muted-foreground text-base max-w-lg mx-auto leading-relaxed">
          Configure your mock interview context data to get started.
        </p>
      </motion.div>



      {/* Upload zone */}
      {stage === "upload" && !file && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mx-auto max-w-5xl"
        >
          <div className="w-full">
              <label
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragover(true);
                }}
                onDragLeave={() => setDragover(false)}
                onDrop={handleDrop}
                className={`bg-card shadow-sm border border-border block w-full rounded-xl p-8 hover:bg-accent/30 text-center cursor-pointer transition-all duration-200 ${
                  dragover
                    ? "border-primary ring-1 ring-primary"
                    : ""
                }`}
              >
              <input
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.webp"
                onChange={handleInputChange}
              />
               <div className="w-12 h-12 rounded-xl bg-accent/50 mx-auto mb-3 flex items-center justify-center border border-border">
                <Upload className="w-5 h-5 text-foreground" />
              </div>
              <p className="text-sm font-semibold mb-1 text-foreground">
                Upload context data (Resume/CV)
              </p>
              <p className="text-xs text-muted-foreground">
                PDF, DOCX, or Image (OCR) files up to 10MB
              </p>
            </label>
          </div>

          {/* Advanced Settings */}
          <div className="mt-8 w-full space-y-4 text-left">
            <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2 mb-4">Configuration Settings</h3>

            <div className="p-5 bg-card shadow-sm border border-border rounded-xl space-y-6">
                <div>
                  <label className="text-sm font-semibold mb-2 block text-foreground">
                    Number of Questions:{" "}
                    <span className="text-primary font-mono">
                      {numQuestions}
                    </span>
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="30"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(Number(e.target.value))}
                    className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold mb-2 block text-foreground">
                    Difficulty Override
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full bg-card border border-border p-2.5 rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  >
                    <option value="">Auto (Based on Resume)</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-semibold mb-2 block text-foreground">
                    Focus Categories
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {[
                      { id: "T", label: "Technical" },
                      { id: "P", label: "Project" },
                      { id: "B", label: "Behavioral" },
                      { id: "C", label: "Conceptual" },
                      { id: "R", label: "Role-Fit" },
                    ].map((c) => (
                      <label
                        key={c.id}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs cursor-pointer transition-colors select-none ${selectedCats.includes(c.id) ? "bg-primary/20 border-primary/50 text-foreground font-medium" : "bg-accent/50 border-transparent text-muted-foreground hover:bg-accent/80"}`}
                      >
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={selectedCats.includes(c.id)}
                          onChange={(e) => {
                            if (e.target.checked)
                              setSelectedCats([...selectedCats, c.id]);
                            else
                              setSelectedCats(
                                selectedCats.filter((x) => x !== c.id),
                              );
                          }}
                        />
                        {c.label}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="pt-4 border-t border-border flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold flex items-center gap-2 text-foreground">
                      <EyeOff className="w-4 h-4 text-warning" /> Bias-Free Mode
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Masks personal identifiers for impartial evaluation
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer mb-2">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={biasFree}
                      onChange={(e) => setBiasFree(e.target.checked)}
                    />
                    <div className="w-9 h-5 bg-muted peer-focus:outline-none rounded-xl peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-xl after:h-4 after:w-4 after:transition-all peer-checked:bg-success shadow-[inset_0_1px_2px_rgba(0,0,0,0.1)]"></div>
                  </label>
                </div>
            </div>

            <div className="pt-2">
              <label className="text-sm font-semibold text-foreground mb-2 block">
                Target Job Description (Optional)
              </label>
               <textarea
                className="w-full bg-card border border-border rounded-xl p-4 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all resize-none text-foreground"
                rows={4}
                placeholder="Paste the job description here. The AI will tailor interview questions to verify your fit for this specific role."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
              />
            </div>
          </div>
        </motion.div>
      )}

      {/* File preview */}
      {stage === "upload" && file && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-card shadow-sm border border-border mx-auto max-w-5xl rounded-2xl p-5"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm truncate">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={startProcessing} className="flex-1 bg-foreground text-background hover:bg-foreground/90 shadow-none h-11 font-semibold rounded-xl">
              Generate Interview
            </Button>
            <Button
              variant="ghost"
              onClick={removeFile}
              className="text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </motion.div>
      )}

      {/* Processing */}
      {stage === "processing" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-auto max-w-5xl rounded-2xl border border-border bg-card p-6"
        >
          <div className="h-1 bg-muted rounded-xl mb-5 overflow-hidden">
            <div
              className="h-full rounded-xl transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: "var(--gradient-accent)",
              }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            {steps.map((step, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all ${
                  i === activeStep
                    ? "bg-primary/10 text-primary"
                    : i < activeStep
                      ? "text-success"
                      : "text-muted-foreground"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-xl flex items-center justify-center text-xs font-bold border ${
                    i === activeStep
                      ? "border-primary bg-primary/10 text-primary"
                      : i < activeStep
                        ? "border-success bg-success/10 text-success"
                        : "border-border bg-muted text-muted-foreground"
                  }`}
                >
                  {i < activeStep ? "✓" : i + 1}
                </div>
                {step}
                {i === activeStep && (
                  <div className="w-4 h-4 border-2 border-border border-t-primary rounded-xl animate-spin ml-auto" />
                )}
              </div>
            ))}
          </div>
          <p className="text-right text-xs text-muted-foreground mt-3 font-mono">
            {Math.round(progress)}%
          </p>
        </motion.div>
      )}

      {/* Results */}
      {/* Generating questions stage */}
      {stage === "generating" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-auto max-w-5xl rounded-2xl border border-border bg-card p-6 text-center"
        >
          <Loading size="lg" className="mx-auto mb-4" />
          <p className="font-semibold text-base mb-1">
            Generating Interview Questions
          </p>
          <p className="text-sm text-muted-foreground">
            AI is creating personalized questions based on your resume...
          </p>
          <p className="text-xs text-muted-foreground mt-3 font-mono">
            Generating {numQuestions} questions • Personalized to your
            experience
          </p>
          {generationDone && (
            <p className="text-sm text-success mt-3 font-semibold">
              ✅ {generatedQs.length} questions generated. Launching
              interview...
            </p>
          )}
        </motion.div>
      )}

      {stage === "results" && parsedResume && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mx-auto max-w-5xl"
        >
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <span className="text-xs text-muted-foreground font-mono">
              Parsed in {parseTime ? `${parseTime.toFixed(1)}s` : "2.4s"} •{" "}
              {generatedQs.length} questions generated
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={removeFile}>
                Upload New
              </Button>
              <Button
                size="sm"
                onClick={() => onStartInterview(parsedResume, generatedQs)}
              >
                <Target className="w-4 h-4" /> Start Interview
              </Button>
            </div>
          </div>

          {plagiarismReport && (
            <div className="bg-card shadow-sm border border-border rounded-2xl p-5 mb-5 bg-[linear-gradient(135deg,rgba(217,119,6,0.08),rgba(15,23,42,0.02))]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-bold flex items-center gap-2 mb-1">
                    <ScanSearch className="w-4 h-4 text-warning" /> Resume
                    Originality Report
                  </p>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {plagiarismReport.summary}
                  </p>
                </div>
                <div className="rounded-xl border border-warning/30 bg-warning/10 px-3 py-2 text-right">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                    Risk
                  </p>
                  <p className="text-lg font-extrabold text-warning">
                    {Math.round(plagiarismReport.score || 0)}%
                  </p>
                  <p className="text-[11px] text-muted-foreground capitalize">
                    {plagiarismReport.label || "low"}
                  </p>
                </div>
              </div>
              {typeof plagiarismReport.ai_generated_score === "number" && (
                <div className="mt-3 flex items-center justify-between gap-3 rounded-xl border border-border bg-card/60 px-3 py-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-foreground/80">
                    AI-generated likelihood
                  </span>
                  <span className="text-sm font-bold capitalize text-warning">
                    {Math.round(plagiarismReport.ai_generated_score)}%
                    {plagiarismReport.verdict
                      ? ` · ${String(plagiarismReport.verdict).replace(/_/g, " ")}`
                      : ""}
                  </span>
                </div>
              )}
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-foreground/80 mb-2">
                    What We Detected
                  </p>
                  <div className="space-y-2">
                    {(plagiarismReport.highlights || []).map((item) => (
                      <p
                        key={item}
                        className="text-sm text-muted-foreground rounded-lg bg-card/60 border border-border px-3 py-2"
                      >
                        {item}
                      </p>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-foreground/80 mb-2">
                    How To Improve
                  </p>
                  <div className="space-y-2">
                    {(plagiarismReport.suggestions || []).map((item) => (
                      <p
                        key={item}
                        className="text-sm text-muted-foreground rounded-lg bg-primary/5 border border-primary/15 px-3 py-2"
                      >
                        {item}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {atsReport && (
            <div className="bg-card shadow-sm border border-border rounded-2xl p-5 mb-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-bold flex items-center gap-2 mb-1">
                    <Gauge className="w-4 h-4 text-brand" /> ATS Readiness Score
                  </p>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {atsReport.summary}
                  </p>
                </div>
                <div className="rounded-xl border border-brand/30 bg-brand/10 px-3 py-2 text-right">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                    Score
                  </p>
                  <p className="text-lg font-extrabold text-brand">
                    {Math.round(atsReport.score || 0)}
                  </p>
                  <p className="text-[11px] text-muted-foreground capitalize">
                    {(atsReport.label || "").replace(/_/g, " ")}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                {[
                  { label: "Keyword Match", value: atsReport.sub_scores?.keyword_match },
                  { label: "Structure", value: atsReport.sub_scores?.structure },
                  { label: "Impact", value: atsReport.sub_scores?.impact },
                  { label: "Parse Quality", value: atsReport.sub_scores?.parse_quality },
                ].map((sub) => (
                  <div
                    key={sub.label}
                    className="rounded-xl border border-border bg-card/60 px-3 py-2 text-center"
                  >
                    <p className="text-lg font-extrabold text-foreground">
                      {typeof sub.value === "number" ? Math.round(sub.value) : "—"}
                    </p>
                    <p className="text-[11px] text-muted-foreground">{sub.label}</p>
                  </div>
                ))}
              </div>

              {(atsReport.keyword_match?.missing?.length ?? 0) > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-foreground/80 mb-2">
                    Missing Keywords
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(atsReport.keyword_match?.missing || []).map((kw) => (
                      <span
                        key={kw}
                        className="text-xs rounded-lg bg-warning/10 border border-warning/20 px-2.5 py-1 text-foreground/80"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {(atsReport.suggestions?.length ?? 0) > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-foreground/80 mb-2">
                    How To Improve Your ATS Score
                  </p>
                  <div className="space-y-2">
                    {(atsReport.suggestions || []).map((item) => (
                      <p
                        key={item}
                        className="text-sm text-muted-foreground rounded-lg bg-primary/5 border border-primary/15 px-3 py-2"
                      >
                        {item}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Confidence */}
          <div className="flex items-center gap-6 bg-card shadow-sm border border-border rounded-2xl p-5 mb-5">
            <div className="relative w-20 h-20">
              <svg viewBox="0 0 80 80" className="-rotate-90 w-full h-full">
                <circle
                  cx="40"
                  cy="40"
                  r="34"
                  className="fill-none stroke-border"
                  strokeWidth="6"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="34"
                  className="fill-none stroke-primary"
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                  style={{ transition: "stroke-dashoffset 1.2s ease" }}
                />
              </svg>
              <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-xl font-extrabold font-mono">
                {confidenceScore}%
              </span>
            </div>
            <div>
              <p className="font-bold text-base mb-1">Parse Confidence</p>
              <p className="text-sm text-muted-foreground">
                High-quality resume with well-structured sections and clear
                formatting.
              </p>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            {[
              {
                icon: "💼",
                value: `${parsedResume.experience.length}`,
                label: "Positions",
                color: "text-primary",
              },
              {
                icon: "🛠",
                value: `${parsedResume.skills.length}`,
                label: "Skills",
                color: "text-success",
              },
              {
                icon: "🚀",
                value: `${parsedResume.projects.length}`,
                label: "Projects",
                color: "text-info",
              },
              {
                icon: "📜",
                value: `${parsedResume.certifications.length}`,
                label: "Certs",
                color: "text-warning",
              },
            ].map((s, i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-3.5 rounded-lg bg-card shadow-sm border border-border"
              >
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm bg-card border border-border ${s.color}`}
                >
                  {s.icon}
                </div>
                <div>
                  <span className="text-base font-bold block">{s.value}</span>
                  <span className="text-xs text-muted-foreground">
                    {s.label}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Cards grid */}
          <div className="grid md:grid-cols-2 gap-3.5">
            {/* Personal Info */}
            <div className="bg-card shadow-sm border border-border rounded-2xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <span className="text-primary">👤</span> Personal Info
                </h3>
              </div>
              <div className="p-4 space-y-2">
                {[
                  ["Name", parsedResume.name],
                  ["Email", parsedResume.email],
                  ["Phone", parsedResume.phone],
                  ["Location", parsedResume.location],
                ].map(([l, v]) => (
                  <div key={l} className="flex justify-between text-sm">
                    <span className="text-muted-foreground text-xs">{l}</span>
                    <span className="font-medium text-xs">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Skills */}
            <div className="bg-card shadow-sm border border-border rounded-2xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <span className="text-primary">🛠</span> Skills
                </h3>
                <span className="px-2 py-0.5 rounded-xl text-xs font-semibold bg-primary/10 text-primary">
                  {parsedResume.skills.length}
                </span>
              </div>
              <div className="p-4">
                <div className="flex flex-wrap gap-1.5">
                  {parsedResume.skills.map((s) => (
                    <span
                      key={s}
                      className="px-2.5 py-1 rounded-xl text-xs font-medium bg-muted border border-border"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Experience */}
            <div className="bg-card shadow-sm border border-border rounded-2xl overflow-hidden md:col-span-2">
              <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <span className="text-primary">💼</span> Experience
                </h3>
              </div>
              <div className="p-4">
                {parsedResume.experience.map((exp, i) => (
                  <div
                    key={i}
                    className={`py-3 ${i < parsedResume.experience.length - 1 ? "border-b border-border" : ""}`}
                  >
                    <p className="text-sm font-semibold">{exp.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {exp.company}
                    </p>
                    <div className="mt-2 space-y-1">
                      {exp.responsibilities.map((r, j) => (
                        <p
                          key={j}
                          className="text-xs text-muted-foreground pl-3 border-l-2 border-border"
                        >
                          {r}
                        </p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Projects */}
            <div className="bg-card shadow-sm border border-border rounded-2xl overflow-hidden">
              <div className="px-4 py-3 border-b border-border">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <span className="text-primary">🚀</span> Projects
                </h3>
              </div>
              <div className="p-4">
                {parsedResume.projects.map((p, i) => (
                  <div
                    key={i}
                    className={`py-3 ${i < parsedResume.projects.length - 1 ? "border-b border-border" : ""}`}
                  >
                    <p className="text-sm font-semibold">{p.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {p.description}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {p.techs.map((t) => (
                        <span
                          key={t}
                          className="px-2 py-0.5 rounded-xl text-[10px] bg-primary/10 text-primary border border-primary/20 font-mono"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Certifications */}
            <div className="bg-card shadow-sm border border-border rounded-2xl overflow-hidden">
              <div className="px-4 py-3 border-b border-border">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <span className="text-primary">📜</span> Certifications
                </h3>
              </div>
              <div className="p-4 space-y-2">
                {parsedResume.certifications.map((c, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <span className="text-warning text-sm">🏆</span>
                    <span className="text-sm font-medium">{c}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Quick Actions */}
      {stage === "upload" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mt-10 mx-auto max-w-5xl"
        >
          <h2 className="text-lg font-bold mb-1">Quick Actions</h2>
          <p className="text-sm text-muted-foreground mb-5">
            Jump into your next session or review past performances
          </p>

          <div className="grid md:grid-cols-3 gap-4 mb-8">
            {QUICK_ACTIONS.map((action, i) => (
              <div
                key={i}
                className="group relative p-5 rounded-2xl bg-card shadow-sm border border-border hover:border-primary/40 hover:-translate-y-1 transition-all duration-300"
              >
                <div
                  className={`mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 ${action.color} transition-colors group-hover:bg-primary group-hover:text-primary-foreground`}
                >
                  {action.icon}
                </div>
                <h3 className="text-base font-bold mb-1">{action.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {action.desc}
                </p>
                {action.href && (
                  <Link
                    to={action.href}
                    className="inline-flex items-center gap-1 mt-3 text-xs font-semibold text-primary hover:text-primary/80 transition-colors"
                  >
                    Go <ArrowRight className="w-3 h-3" />
                  </Link>
                )}
              </div>
            ))}
          </div>

          {/* Evaluation Criteria preview */}
          <div className="bg-card shadow-sm border border-border rounded-2xl p-5 shadow-sm">
            <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
              <Award className="w-4 h-4 text-primary" /> How You'll Be Evaluated
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                {
                  label: "Technical Correctness",
                  desc: "Factual accuracy of answers",
                  score: "0–100",
                },
                {
                  label: "Depth & Completeness",
                  desc: "Coverage of key concepts",
                  score: "0–100",
                },
                {
                  label: "Clarity & Communication",
                  desc: "Well-structured responses",
                  score: "0–100",
                },
                {
                  label: "Relevance",
                  desc: "Addresses the question asked",
                  score: "0–100",
                },
              ].map((e, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg bg-accent/30 border border-border"
                >
                  <p className="text-xs font-semibold mb-0.5">{e.label}</p>
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    {e.desc}
                  </p>

                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
