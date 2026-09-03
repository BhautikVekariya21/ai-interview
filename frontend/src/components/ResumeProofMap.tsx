import { m as motion } from "framer-motion";
import { BadgeCheck, Briefcase, FileSearch, FolderKanban, ShieldCheck, Sparkles, Target } from "lucide-react";

type ResumeSkill = string;

type ResumeExperience = {
  title?: string;
  company?: string;
  duration?: string;
  responsibilities?: string[];
};

type ResumeProject = {
  name?: string;
  description?: string;
  techs?: string[];
};

export type ResumeShape = {
  skills?: ResumeSkill[];
  experience?: ResumeExperience[];
  projects?: ResumeProject[];
  certifications?: string[];
};

type EvaluationShape = {
  question_number?: number;
  question?: string;
  score: number;
  grade?: string;
  strengths?: string[];
  improvements?: string[];
  feedback?: string;
};

type QuestionShape = {
  id: number;
  text: string;
  category: string;
  difficulty: string;
};

interface ResumeProofMapProps {
  resumeData?: Record<string, unknown>;
  evaluations?: EvaluationShape[];
  questions?: QuestionShape[];
}

type SignalKind = "skill" | "project" | "experience" | "certification";

export type ResumeSignal = {
  label: string;
  kind: SignalKind;
  keywords: string[];
  context?: string;
};

export type SignalAssessment = ResumeSignal & {
  matchedQuestions: number[];
  matchCount: number;
  averageScore: number | null;
  bestScore: number | null;
  status: "validated" | "explored" | "fragile" | "untested";
};

const STOP_WORDS = new Set([
  "and", "the", "with", "from", "into", "that", "this", "your", "have", "for", "using",
  "used", "build", "built", "over", "plus", "role", "team", "work", "years", "year",
  "engineer", "engineering", "developer", "development", "software",
]);

function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9+#.\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractKeywords(...values: Array<string | undefined>): string[] {
  const bucket = new Set<string>();
  for (const value of values) {
    const normalized = normalizeText(value || "");
    if (!normalized) continue;
    bucket.add(normalized);
    for (const token of normalized.split(" ")) {
      if (token.length < 3 || STOP_WORDS.has(token)) continue;
      bucket.add(token);
    }
  }
  return Array.from(bucket);
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export function buildSignals(resumeData?: Record<string, unknown>): ResumeSignal[] {
  if (!resumeData) return [];

  const data = resumeData as ResumeShape;
  const signals: ResumeSignal[] = [];

  for (const skill of asArray<string>(data.skills).slice(0, 12)) {
    if (!skill) continue;
    signals.push({
      label: skill,
      kind: "skill",
      keywords: extractKeywords(skill),
    });
  }

  for (const project of asArray<ResumeProject>(data.projects).slice(0, 6)) {
    if (!project?.name) continue;
    signals.push({
      label: project.name,
      kind: "project",
      context: project.description,
      keywords: extractKeywords(project.name, project.description, ...(project.techs || [])),
    });
  }

  for (const role of asArray<ResumeExperience>(data.experience).slice(0, 6)) {
    const label = [role.title, role.company].filter(Boolean).join(" at ");
    if (!label) continue;
    signals.push({
      label,
      kind: "experience",
      context: role.duration,
      keywords: extractKeywords(label, ...(role.responsibilities || []).slice(0, 3)),
    });
  }

  for (const cert of asArray<string>(data.certifications).slice(0, 6)) {
    if (!cert) continue;
    signals.push({
      label: cert,
      kind: "certification",
      keywords: extractKeywords(cert),
    });
  }

  return signals;
}

function buildQuestionCorpus(evaluations?: EvaluationShape[], questions?: QuestionShape[]) {
  const fallbackQuestions = (questions || []).map((question, index) => ({
    questionNumber: index + 1,
    text: question.text,
    score: null as number | null,
    blob: normalizeText(question.text),
  }));

  if (!evaluations || evaluations.length === 0) return fallbackQuestions;

  return evaluations.map((evaluation, index) => {
    const questionNumber = evaluation.question_number || index + 1;
    const blob = normalizeText([
      evaluation.question,
      evaluation.feedback,
      ...(evaluation.strengths || []),
      ...(evaluation.improvements || []),
    ].filter(Boolean).join(" "));

    return {
      questionNumber,
      text: evaluation.question || `Question ${questionNumber}`,
      score: Number.isFinite(evaluation.score) ? evaluation.score : null,
      blob,
    };
  });
}

function matchesSignal(signal: ResumeSignal, blob: string): boolean {
  if (!blob) return false;
  return signal.keywords.some((keyword) => {
    if (keyword.length < 3) return false;
    if (keyword.includes(" ")) {
      return blob.includes(keyword);
    }
    return blob.split(" ").includes(keyword);
  });
}

export function assessSignals(
  signals: ResumeSignal[],
  evaluations?: EvaluationShape[],
  questions?: QuestionShape[],
): SignalAssessment[] {
  const corpus = buildQuestionCorpus(evaluations, questions);

  return signals.map((signal) => {
    const matched = corpus.filter((entry) => matchesSignal(signal, entry.blob));
    const scoredMatches = matched
      .map((entry) => entry.score)
      .filter((score): score is number => typeof score === "number");
    const averageScore = scoredMatches.length
      ? Math.round(scoredMatches.reduce((sum, score) => sum + score, 0) / scoredMatches.length)
      : null;
    const bestScore = scoredMatches.length ? Math.max(...scoredMatches) : null;

    let status: SignalAssessment["status"] = "untested";
    if (matched.length > 0 && averageScore !== null) {
      status = averageScore >= 80 ? "validated" : averageScore >= 60 ? "explored" : "fragile";
    } else if (matched.length > 0) {
      status = "explored";
    }

    return {
      ...signal,
      matchedQuestions: matched.map((entry) => entry.questionNumber),
      matchCount: matched.length,
      averageScore,
      bestScore,
      status,
    };
  });
}

function statusStyles(status: SignalAssessment["status"]) {
  if (status === "validated") {
    return {
      label: "Validated",
      pill: "border-success/30 bg-success/10 text-success",
      card: "border-success/20 bg-success/5",
    };
  }
  if (status === "explored") {
    return {
      label: "Explored",
      pill: "border-primary/30 bg-primary/10 text-primary",
      card: "border-primary/20 bg-primary/5",
    };
  }
  if (status === "fragile") {
    return {
      label: "Needs Work",
      pill: "border-warning/30 bg-warning/10 text-warning",
      card: "border-warning/20 bg-warning/5",
    };
  }
  return {
    label: "Untested",
    pill: "border-border bg-muted text-muted-foreground",
    card: "border-border bg-card",
  };
}

function kindIcon(kind: SignalKind) {
  if (kind === "skill") return <Sparkles className="w-4 h-4" />;
  if (kind === "project") return <FolderKanban className="w-4 h-4" />;
  if (kind === "experience") return <Briefcase className="w-4 h-4" />;
  return <ShieldCheck className="w-4 h-4" />;
}

function kindLabel(kind: SignalKind) {
  if (kind === "skill") return "Skill";
  if (kind === "project") return "Project";
  if (kind === "experience") return "Experience";
  return "Certification";
}

export default function ResumeProofMap({
  resumeData,
  evaluations,
  questions,
}: ResumeProofMapProps) {
  const signals = buildSignals(resumeData);
  const assessments = assessSignals(signals, evaluations, questions);

  if (assessments.length === 0) return null;

  const validated = assessments.filter((item) => item.status === "validated");
  const explored = assessments.filter((item) => item.status === "explored");
  const fragile = assessments.filter((item) => item.status === "fragile");
  const untested = assessments.filter((item) => item.status === "untested");
  const testedCount = assessments.length - untested.length;
  const coverage = Math.round((testedCount / Math.max(assessments.length, 1)) * 100);

  const spotlight = [...validated, ...explored, ...fragile]
    .sort((a, b) => (b.bestScore || 0) - (a.bestScore || 0))
    .slice(0, 8);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.18 }}
      className="bg-card border border-border shadow-sm rounded-2xl p-5 mb-5"
    >
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between mb-5">
        <div>
          <h3 className="text-sm font-bold flex items-center gap-2">
            <FileSearch className="w-4 h-4 text-primary" /> Resume Proof Map
          </h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl leading-relaxed">
            This map shows which parts of the resume were actually challenged during the interview, which claims were strongly defended, and which areas still need targeted probing.
          </p>
        </div>
        <div className="rounded-xl border border-primary/20 bg-primary/10 px-4 py-3 min-w-[150px]">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Coverage</p>
          <p className="text-2xl font-extrabold text-primary">{coverage}%</p>
          <p className="text-xs text-muted-foreground">{testedCount}/{assessments.length} resume signals touched</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {[
          { label: "Validated", value: validated.length, tone: "text-success", icon: <BadgeCheck className="w-4 h-4" /> },
          { label: "Explored", value: explored.length, tone: "text-primary", icon: <Target className="w-4 h-4" /> },
          { label: "Needs Work", value: fragile.length, tone: "text-warning", icon: <Sparkles className="w-4 h-4" /> },
          { label: "Untested", value: untested.length, tone: "text-muted-foreground", icon: <FileSearch className="w-4 h-4" /> },
        ].map((stat) => (
          <div key={stat.label} className="rounded-xl border border-border bg-card p-3">
            <div className={`flex items-center gap-2 text-xs font-semibold ${stat.tone}`}>
              {stat.icon} {stat.label}
            </div>
            <p className="text-2xl font-extrabold mt-2">{stat.value}</p>
          </div>
        ))}
      </div>

      {spotlight.length > 0 && (
        <div className="mb-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
            Strongest Resume Evidence
          </h4>
          <div className="grid md:grid-cols-2 gap-3">
            {spotlight.map((item) => {
              const styles = statusStyles(item.status);
              return (
                <div key={`${item.kind}-${item.label}`} className={`rounded-xl border p-4 ${styles.card}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">{item.label}</p>
                      <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1.5">
                        {kindIcon(item.kind)} {kindLabel(item.kind)}
                      </p>
                    </div>
                    <span className={`px-2.5 py-1 rounded-xl text-[10px] font-semibold border ${styles.pill}`}>
                      {styles.label}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 mt-3 text-xs text-muted-foreground">
                    {item.bestScore !== null && (
                      <span className="rounded-xl border border-border bg-card/70 px-2.5 py-1">
                        Best score: {item.bestScore}/100
                      </span>
                    )}
                    {item.averageScore !== null && (
                      <span className="rounded-xl border border-border bg-card/70 px-2.5 py-1">
                        Avg score: {item.averageScore}/100
                      </span>
                    )}
                    {item.matchedQuestions.length > 0 && (
                      <span className="rounded-xl border border-border bg-card/70 px-2.5 py-1">
                        Seen in Q{item.matchedQuestions.join(", Q")}
                      </span>
                    )}
                  </div>

                  {item.context && (
                    <p className="text-xs text-muted-foreground mt-3 leading-relaxed">{item.context}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {untested.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
            Blind Spots For The Next Mock
          </h4>
          <div className="flex flex-wrap gap-2">
            {untested.slice(0, 10).map((item) => (
              <span
                key={`${item.kind}-${item.label}`}
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-muted px-3 py-1.5 text-xs text-muted-foreground"
              >
                {kindIcon(item.kind)}
                {item.label}
              </span>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-3 leading-relaxed">
            These resume claims were not meaningfully challenged yet. A stronger next-round interview can deliberately probe them so the final signal reflects the whole profile, not just the easiest talking points.
          </p>
        </div>
      )}
    </motion.div>
  );
}
