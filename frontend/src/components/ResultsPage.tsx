import { useEffect, useState } from "react";
import { m as motion } from "framer-motion";
import { Trophy, Target, Brain, MessageSquare, Clock, TrendingUp, BarChart3, ArrowRight, RotateCcw, Download, Lightbulb, ScanSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip as RechartsTooltip } from "recharts";
import { saveInterviewHistory } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import ConfidencePulse from "@/components/ConfidencePulse";
import ResumeProofMap from "@/components/ResumeProofMap";
import type { AuthenticityReport, BatchAuthenticitySummary } from "@/lib/api";
import type { GeneratedQuestion } from "@/pages/Index";

export interface Module5Evaluation {
  question_number?: number;
  question?: string;
  score: number;
  grade: string;
  strengths: string[];
  improvements: string[];
  feedback: string;
  ideal_answer?: string;
  follow_up_question?: string;
  followup_question?: string;
  authenticity_report?: AuthenticityReport;
}

export interface InterviewResult {
  candidateName: string;
  totalQuestions: number;
  answeredQuestions: number;
  duration: number; // seconds
  messages: { role: "ai" | "user"; text: string }[];
  overallScore?: number;
  overallGrade?: string;
  summary?: string;
  evaluations?: Module5Evaluation[];
  plagiarismSummary?: BatchAuthenticitySummary;
}

interface ResultsPageProps {
  result: InterviewResult;
  onRestart: () => void;
  resumeData?: Record<string, unknown>;
  questions?: GeneratedQuestion[];
}

function getScores(result: InterviewResult) {
  const answered = result.answeredQuestions;
  const total = result.totalQuestions;
  const completionRate = total > 0 ? Math.round((answered / total) * 100) : 0;
  const evaluations = Array.isArray(result.evaluations) ? result.evaluations : [];

  const evaluationAverage = evaluations.length > 0
    ? Math.round(evaluations.reduce((sum, ev) => sum + (Number(ev.score) || 0), 0) / evaluations.length)
    : undefined;

  const overall = typeof result.overallScore === "number"
    ? Math.round(result.overallScore)
    : (evaluationAverage ?? completionRate);

  const strengthsCount = evaluations.reduce((sum, ev) => sum + (Array.isArray(ev.strengths) ? ev.strengths.length : 0), 0);
  const improvementsCount = evaluations.reduce((sum, ev) => sum + (Array.isArray(ev.improvements) ? ev.improvements.length : 0), 0);
  const feedbackCoverage = evaluations.reduce((sum, ev) => sum + (ev.feedback ? 1 : 0), 0);
  const followUps = evaluations.reduce((sum, ev) => sum + ((ev.follow_up_question || ev.followup_question) ? 1 : 0), 0);

  const depthScore = evaluations.length > 0
    ? Math.min(100, Math.round((overall * 0.7) + ((strengthsCount / Math.max(evaluations.length, 1)) * 10)))
    : completionRate;
  const technicalScore = evaluations.length > 0
    ? Math.min(100, Math.round((overall * 0.85) + (feedbackCoverage / Math.max(evaluations.length, 1)) * 15))
    : completionRate;
  const clarityScore = evaluations.length > 0
    ? Math.min(100, Math.round((overall * 0.8) + (followUps / Math.max(evaluations.length, 1)) * 20))
    : completionRate;
  const communicationScore = evaluations.length > 0
    ? Math.min(100, Math.round((overall * 0.75) + ((evaluations.length - improvementsCount / 3) / Math.max(evaluations.length, 1)) * 25))
    : completionRate;

  return { overall, completionRate, depthScore, clarityScore, technicalScore, communicationScore, evaluations };
}

function ScoreRing({ score, size = 100, strokeWidth = 7, label }: { score: number; size?: number; strokeWidth?: number; label: string }) {
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? "var(--success-color)" : score >= 60 ? "var(--warning-color)" : "var(--destructive-color)";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox={`0 0 ${size} ${size}`} className="-rotate-90 w-full h-full">
          <circle cx={size / 2} cy={size / 2} r={r} className="fill-none stroke-muted" strokeWidth={strokeWidth} />
          <circle
            cx={size / 2} cy={size / 2} r={r}
            className="fill-none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1.5s ease" }}
          />
        </svg>
        <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-lg font-extrabold font-mono">
          {score}%
        </span>
      </div>
      <span className="text-xs font-semibold text-muted-foreground">{label}</span>
    </div>
  );
}

function formatDuration(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}m ${sec}s`;
}

function getGrade(score: number) {
  if (score >= 90) return { grade: "A+", label: "Exceptional", color: "text-success" };
  if (score >= 80) return { grade: "A", label: "Strong", color: "text-success" };
  if (score >= 70) return { grade: "B+", label: "Good", color: "text-primary" };
  if (score >= 60) return { grade: "B", label: "Solid", color: "text-primary" };
  return { grade: "C", label: "Needs Work", color: "text-warning" };
}

const FEEDBACK = [
  { threshold: 80, text: "Evaluation indicates strong performance across technical correctness, depth, and clarity." },
  { threshold: 60, text: "Evaluation suggests adequate foundations with room to improve depth and structure in answers." },
  { threshold: 0, text: "Evaluation suggests focusing on technical accuracy and response completeness." },
];

export default function ResultsPage({ result, onRestart, resumeData, questions }: ResultsPageProps) {
  const { isAuthenticated } = useAuth();
  const [expandedIdealAnswers, setExpandedIdealAnswers] = useState<Record<number, boolean>>({});
  const scores = getScores(result);
  const { grade, label, color } = getGrade(scores.overall);
  const feedback = result.summary || FEEDBACK.find(f => scores.overall >= f.threshold)!.text;

  const toggleIdealAnswer = (idx: number) => {
    setExpandedIdealAnswers(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    try {
      const entry = {
        candidateName: result.candidateName || "Candidate",
        totalQuestions: result.totalQuestions || 0,
        finalGrade: grade,
        finalScores: {
          overall: scores.overall || 0,
          completionRate: scores.completionRate || 0
        },
        plagiarismSummary: result.plagiarismSummary || null,
        date: new Date().toISOString(),
        details_json: JSON.stringify({
          candidateName: result.candidateName || "Candidate",
          duration: result.duration || 0,
          summary: result.summary || feedback,
          overallScore: scores.overall || 0,
          overallGrade: grade,
          totalQuestions: result.totalQuestions || 0,
          answeredQuestions: result.answeredQuestions || 0,
          evaluations: result.evaluations || [],
          plagiarismSummary: result.plagiarismSummary || null,
        }),
      };
      
      saveInterviewHistory(entry)
        .catch(e => console.error("Failed to save history to DB:", e));
        
    } catch (e) {
      console.error("History formatting error:", e);
    }
  }, [isAuthenticated, result.candidateName, result.totalQuestions, grade, scores.overall, scores.completionRate]);

  const downloadReport = () => {
    const md = `# Interview Evaluation Report: ${result.candidateName}
Date: ${new Date().toLocaleDateString()}
Overall Score: ${scores.overall}%
Grade: ${grade}

## Summary
${feedback}

## Authenticity Coaching
- Average AI-likeness: ${Math.round(result.plagiarismSummary?.average_ai_generated_score || 0)}/100
- Average plagiarism risk: ${Math.round(result.plagiarismSummary?.average_plagiarism_score || 0)}/100
- Guidance: ${result.plagiarismSummary?.summary || "No authenticity summary available."}

## Performance Categories
- Technical Depth: ${scores.technicalScore}%
- Communication: ${scores.communicationScore}%
- Clarity: ${scores.clarityScore}%
- Answer Depth: ${scores.depthScore}%

## Detailed QA
${(result.evaluations || []).map((ev, i) => `### Q${ev.question_number || i+1}: ${ev.question || ''}\n- Score: ${ev.score}/100\n- Grade: ${ev.grade}\n- Feedback: ${ev.feedback}\n- Strengths: ${(ev.strengths || []).join(", ") || "-"}\n- Improvements: ${(ev.improvements || []).join(", ") || "-"}\n`).join("\n")}
`;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `interview_report_${result.candidateName.replace(/\\s+/g, '_')}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const categories = [
    { icon: <Brain className="w-4 h-4" />, label: "Technical Depth", score: scores.technicalScore },
    { icon: <MessageSquare className="w-4 h-4" />, label: "Communication", score: scores.communicationScore },
    { icon: <Target className="w-4 h-4" />, label: "Clarity", score: scores.clarityScore },
    { icon: <TrendingUp className="w-4 h-4" />, label: "Answer Depth", score: scores.depthScore },
  ];

  const stats = [
    { icon: <MessageSquare className="w-4 h-4" />, value: `${result.answeredQuestions}/${result.totalQuestions}`, label: "Questions" },
    { icon: <Clock className="w-4 h-4" />, value: formatDuration(result.duration), label: "Duration" },
    { icon: <BarChart3 className="w-4 h-4" />, value: `${scores.completionRate}%`, label: "Completion" },
    { icon: <Trophy className="w-4 h-4" />, value: grade, label: label },
  ];

  const radarData = [
    { subject: "Technical", score: scores.technicalScore, fullMark: 100 },
    { subject: "Communication", score: scores.communicationScore, fullMark: 100 },
    { subject: "Clarity", score: scores.clarityScore, fullMark: 100 },
    { subject: "Depth", score: scores.depthScore, fullMark: 100 },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center py-8">
        <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-primary/10 border border-primary/20 text-xs font-semibold text-primary mb-4">
          <Trophy className="w-3.5 h-3.5" /> Interview Complete
        </span>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3">
          Your <span className="text-foreground">Results</span>
        </h1>
        <p className="text-muted-foreground text-base max-w-lg mx-auto leading-relaxed">
          Here's how you performed, {result.candidateName}. Review your scores and feedback below.
        </p>
      </motion.div>

      {/* Overall Score */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center gap-6 bg-card border border-border shadow-sm rounded-2xl p-6 mb-5"
      >
        <ScoreRing score={scores.overall} size={100} label="Overall" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-2xl font-extrabold font-mono ${color}`}>{grade}</span>
            <span className="text-sm font-semibold text-muted-foreground">— {label} Performance</span>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">{feedback}</p>
        </div>
      </motion.div>


      {result.summary && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12 }}
          className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
        >
          <h3 className="text-sm font-bold mb-2 flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary" /> Module 5 AI Summary
          </h3>
          <p className="text-sm text-muted-foreground leading-relaxed">{result.summary}</p>
        </motion.div>
      )}

      {result.plagiarismSummary && (
        <motion.div
           initial={{ opacity: 0, y: 8 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.13 }}
           className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
         >
           <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
             <ScanSearch className="w-4 h-4 text-warning" /> Authenticity And Plagiarism Coaching
           </h3>
           <>
               <div className="grid md:grid-cols-3 gap-3 mb-4">
                 <div className="rounded-xl border border-warning/20 bg-warning/10 p-4">
                   <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Average AI-Likeness</p>
                   <p className="text-2xl font-extrabold text-warning mt-1">{Math.round(result.plagiarismSummary.average_ai_generated_score)}%</p>
                   <p className="text-xs text-muted-foreground capitalize">{result.plagiarismSummary.average_ai_generated_label}</p>
                 </div>
                 <div className="rounded-xl border border-primary/20 bg-primary/10 p-4">
                   <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Average Plagiarism Risk</p>
                   <p className="text-2xl font-extrabold text-primary mt-1">{Math.round(result.plagiarismSummary.average_plagiarism_score)}%</p>
                   <p className="text-xs text-muted-foreground capitalize">{result.plagiarismSummary.average_plagiarism_label}</p>
                 </div>
                 <div className="rounded-xl border border-border bg-muted/20 p-4">
                   <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Highest-Risk Answer</p>
                   <p className="text-sm font-semibold mt-1">
                     {result.plagiarismSummary.highest_risk_question?.question_number
                       ? `Question ${result.plagiarismSummary.highest_risk_question.question_number}`
                       : "Not available"}
                   </p>
                   <p className="text-xs text-muted-foreground mt-1">
                     {result.plagiarismSummary.highest_risk_question?.summary || "No standout risk detected."}
                   </p>
                 </div>
               </div>
               <p className="text-sm text-muted-foreground leading-relaxed mb-3">{result.plagiarismSummary.summary}</p>
               <div className="space-y-2">
                 {(result.plagiarismSummary.suggestions || []).map((item) => (
                   <p key={item} className="text-sm text-muted-foreground rounded-lg bg-card/60 border border-border px-3 py-2">
                     {item}
                   </p>
                 ))}
               </div>
             </>
         </motion.div>
       )}

      {/* Stats row */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5"
      >
        {stats.map((s, i) => (
          <div key={i} className="flex items-center gap-3 p-3.5 rounded-xl bg-card border border-border shadow-sm">
            <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center">{s.icon}</div>
            <div>
              <span className="text-base font-bold block">{s.value}</span>
              <span className="text-xs text-muted-foreground">{s.label}</span>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Category breakdowns */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
      >
        <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-primary" /> Performance Radar
        </h3>
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div className="space-y-4">
            {categories.map((cat, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-medium flex items-center gap-2 text-muted-foreground">
                    {cat.icon} {cat.label}
                  </span>
                  <span className="text-sm font-bold font-mono">{cat.score}%</span>
                </div>
                <div className="h-2 bg-muted rounded-xl overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${cat.score}%` }}
                    transition={{ delay: 0.3 + i * 0.1, duration: 0.8, ease: "easeOut" }}
                    className="h-full rounded-xl"
                    style={{ background: "var(--gradient-accent)" }}
                  />
                </div>
              </div>
            ))}
          </div>
          
          <div className="h-[250px] w-full flex items-center justify-center bg-muted/10 rounded-xl">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: "hsl(var(--foreground))", fontSize: 12, fontWeight: 500 }} />
                <Radar name="Candidate" dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.4} />
                <RechartsTooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>

      {/* Module 12: AI Confidence Pulse */}
      {Array.isArray(result.evaluations) && result.evaluations.length > 0 && (
        <ConfidencePulse
          evaluations={result.evaluations}
          duration={result.duration}
        />
      )}

      <ResumeProofMap
        resumeData={resumeData}
        evaluations={result.evaluations}
        questions={questions}
      />

      {/* Strengths & Improvements */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="grid md:grid-cols-2 gap-3.5 mb-5"
      >
        <div className="bg-card border border-border shadow-sm rounded-2xl p-5">
          <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
            <span className="text-success">✅</span> Strengths
          </h3>
          <ul className="space-y-2">
            {scores.technicalScore >= 70 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-success mt-0.5 flex-shrink-0" />
                Strong technical knowledge and problem-solving approach
              </li>
            )}
            {scores.communicationScore >= 70 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-success mt-0.5 flex-shrink-0" />
                Clear and articulate communication style
              </li>
            )}
            {scores.completionRate >= 80 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-success mt-0.5 flex-shrink-0" />
                Completed the majority of interview questions
              </li>
            )}
            {scores.depthScore >= 70 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-success mt-0.5 flex-shrink-0" />
                Provided detailed and thorough responses
              </li>
            )}
          </ul>
        </div>

        <div className="bg-card border border-border shadow-sm rounded-2xl p-5">
          <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
            <span className="text-warning">💡</span> Areas to Improve
          </h3>
          <ul className="space-y-2">
            {scores.technicalScore < 70 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-warning mt-0.5 flex-shrink-0" />
                Dive deeper into technical details and trade-offs
              </li>
            )}
            {scores.communicationScore < 70 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-warning mt-0.5 flex-shrink-0" />
                Structure answers more clearly with examples
              </li>
            )}
            {scores.completionRate < 80 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-warning mt-0.5 flex-shrink-0" />
                Try to answer all questions to show breadth
              </li>
            )}
            {scores.depthScore < 70 && (
              <li className="text-sm text-muted-foreground flex items-start gap-2">
                <ArrowRight className="w-3.5 h-3.5 text-warning mt-0.5 flex-shrink-0" />
                Elaborate more on your answers with real-world examples
              </li>
            )}
          </ul>
        </div>
      </motion.div>


      {Array.isArray(result.evaluations) && result.evaluations.length > 0 && (
        <motion.div
           initial={{ opacity: 0, y: 8 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.28 }}
           className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
         >
           <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
             <MessageSquare className="w-4 h-4 text-primary" /> Module 5 Per-Question Evaluation
           </h3>
           <div className="space-y-3">
               {result.evaluations.map((ev, idx) => (
                 <div key={idx} className="rounded-lg border border-border p-3 bg-muted/20">
                   <p className="text-xs text-muted-foreground mb-1">Q{ev.question_number || idx + 1}</p>
                   {ev.question && <p className="text-sm font-medium mb-2">{ev.question}</p>}
                   <p className="text-sm font-semibold mb-1">Score: {ev.score}/100 • Grade: {ev.grade}</p>
                   <p className="text-sm text-muted-foreground mb-1">Strengths: {(ev.strengths || []).slice(0,3).join("; ") || "-"}</p>
                   <p className="text-sm text-muted-foreground mb-1">Areas for improvement: {(ev.improvements || []).slice(0,3).join("; ") || "-"}</p>
                   <p className="text-sm text-muted-foreground mb-1">AI feedback: {ev.feedback || "-"}</p>
                   {ev.authenticity_report && (
                     <>
                       <p className="text-sm text-muted-foreground mb-1">
                         Authenticity: AI-likeness {Math.round(ev.authenticity_report.ai_generated_score || 0)}/100, plagiarism risk {Math.round(ev.authenticity_report.plagiarism_score || 0)}/100
                       </p>
                       <p className="text-sm text-muted-foreground mb-1">Authenticity note: {ev.authenticity_report.summary}</p>
                     </>
                   )}
                   <p className="text-sm text-muted-foreground">Follow-up: {ev.follow_up_question || ev.followup_question || "-"}</p>
                   
                   {ev.ideal_answer && (
                     <div className="mt-3 text-sm border-t border-border pt-2">
                       <button 
                         onClick={() => toggleIdealAnswer(idx)}
                         className="flex items-center gap-1.5 text-xs font-semibold text-primary/80 hover:text-primary transition-colors py-1"
                       >
                         <Lightbulb className="w-3.5 h-3.5" /> 
                         {expandedIdealAnswers[idx] ? "Hide Ideal Answer" : "Show Ideal Answer"}
                       </button>
                       {expandedIdealAnswers[idx] && (
                         <motion.div 
                           initial={{ opacity: 0, height: 0 }}
                           animate={{ opacity: 1, height: "auto" }}
                           className="mt-2 p-3 rounded-md bg-primary/10 border border-primary/20 leading-relaxed"
                         >
                           <p className="font-semibold text-xs mb-1.5 text-primary uppercase tracking-wider">Expert Reference Answer:</p>
                           <p className="text-sm text-foreground">{ev.ideal_answer}</p>
                         </motion.div>
                       )}
                     </div>
                   )}
                 </div>
               ))}
             </div>
         </motion.div>
       )}

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex justify-center gap-3 pb-8"
      >
        <Button variant="outline" onClick={onRestart}>
          <RotateCcw className="w-4 h-4" /> Try Again
        </Button>
        <Button onClick={downloadReport}>
          <Download className="w-4 h-4" /> Download Report
        </Button>
      </motion.div>
    </div>
  );
}
