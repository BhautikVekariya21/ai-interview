import { useState, useMemo } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  ChevronDown,
  ChevronRight,
  Clock,
  Bookmark,
  ExternalLink,
  Target,
  Users,
  MessageSquare,
  DollarSign,
  BookOpen,
  Shield,
  BarChart3,
  Lightbulb,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
} from "recharts";
import { COMPANY_PROFILES, type CompanyProfile } from "./companyPrepData";

/* ──────────────────────────────────────────── */
/*  Accordion section                           */
/* ──────────────────────────────────────────── */
function Accordion({
  title,
  icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2.5 px-4 py-3 text-sm font-semibold text-foreground hover:bg-accent/20 transition-colors cursor-pointer"
      >
        {icon}
        <span className="flex-1 text-left">{title}</span>
        <ChevronDown
          className={`w-4 h-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Company tab button                          */
/* ──────────────────────────────────────────── */
function CompanyTab({
  company,
  active,
  onClick,
}: {
  company: CompanyProfile;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2.5 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all cursor-pointer whitespace-nowrap ${
        active
          ? "border-primary/30 bg-primary/10 text-primary scale-[1.02] ring-1 ring-primary/10"
          : "border-transparent text-muted-foreground hover:border-border hover:bg-accent/30 hover:text-foreground"
      }`}
    >
      <span className="text-lg">{company.logo}</span>
      <span>{company.name}</span>
    </button>
  );
}

/* ──────────────────────────────────────────── */
/*  Company detail view                         */
/* ──────────────────────────────────────────── */
function CompanyDetail({
  company,
  focusMode,
}: {
  company: CompanyProfile;
  focusMode: boolean;
}) {
  const radarData = [
    {
      subject: "Technical",
      score: company.difficultyRating.technical * 10,
      fullMark: 100,
    },
    {
      subject: "Behavioral",
      score: company.difficultyRating.behavioral * 10,
      fullMark: 100,
    },
    {
      subject: "System Design",
      score: company.difficultyRating.systemDesign * 10,
      fullMark: 100,
    },
  ];

  return (
    <motion.div
      key={company.id}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Hero */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-start gap-4 flex-wrap">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl text-2xl border border-border bg-accent/30">
            {company.logo}
          </div>
          <div className="flex-1 min-w-[200px]">
            <h2 className="text-2xl font-bold text-foreground mb-1">
              {company.name}
            </h2>
            <p className="text-sm text-muted-foreground italic">
              "{company.tagline}"
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-center">
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Difficulty
              </p>
              <p className="text-2xl font-bold font-mono text-foreground">
                {company.difficultyRating.overall}/10
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Focus Mode: Top 3 tips */}
      {focusMode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl border-2 border-primary/30 bg-primary/5 p-5"
        >
          <h3 className="text-sm font-bold flex items-center gap-2 mb-3 text-primary">
            <Zap className="w-4 h-4" /> Focus Mode — 3 Things to Remember
          </h3>
          <div className="space-y-2">
            {company.tipsToStandOut.slice(0, 3).map((tip, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-xl bg-card border border-border"
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary text-primary-foreground text-xs font-bold shrink-0">
                  {i + 1}
                </span>
                <p className="text-sm text-foreground leading-relaxed">{tip}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Difficulty radar */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
        <h3 className="text-sm font-bold mb-3 flex items-center gap-2 text-foreground">
          <BarChart3 className="w-4 h-4 text-primary" /> Interview Difficulty
          Profile
        </h3>
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
              <PolarGrid stroke="hsl(var(--border))" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{
                  fill: "hsl(var(--foreground))",
                  fontSize: 12,
                  fontWeight: 500,
                }}
              />
              <PolarRadiusAxis
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              />
              <Radar
                name={company.name}
                dataKey="score"
                stroke={`hsl(${company.color})`}
                fill={`hsl(${company.color})`}
                fillOpacity={0.3}
              />
              <RechartsTooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Interview Rounds */}
      <Accordion
        title={`Interview Process (${company.interviewRounds.length} rounds)`}
        icon={<Clock className="w-4 h-4 text-info" />}
        defaultOpen
      >
        <div className="space-y-3">
          {company.interviewRounds.map((round, i) => (
            <div
              key={i}
              className="flex items-start gap-3 p-3 rounded-xl bg-accent/20 border border-border"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-info/10 border border-info/20 text-info text-xs font-bold shrink-0">
                {i + 1}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-semibold text-foreground">
                    {round.name}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-mono">
                    {round.duration}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {round.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Accordion>

      {/* Culture Values */}
      <Accordion
        title="Culture & Values"
        icon={<Shield className="w-4 h-4 text-success" />}
      >
        <div className="space-y-2">
          {company.cultureValues.map((val, i) => (
            <div
              key={i}
              className="flex items-start gap-2 text-sm text-foreground"
            >
              <ChevronRight className="w-3.5 h-3.5 text-success mt-0.5 shrink-0" />
              {val}
            </div>
          ))}
        </div>
      </Accordion>

      {/* Question Themes */}
      <Accordion
        title="Common Question Themes"
        icon={<MessageSquare className="w-4 h-4 text-warning" />}
      >
        <div className="flex flex-wrap gap-2">
          {company.questionThemes.map((theme, i) => (
            <span
              key={i}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-warning/10 border border-warning/20 text-foreground"
            >
              {theme}
            </span>
          ))}
        </div>
      </Accordion>

      {/* Interviewer Style */}
      <Accordion
        title="What Interviewers Look For"
        icon={<Users className="w-4 h-4 text-primary" />}
      >
        <p className="text-sm text-foreground leading-relaxed">
          {company.interviewerStyle}
        </p>
      </Accordion>

      {/* Tips */}
      <Accordion
        title="Tips to Stand Out"
        icon={<Lightbulb className="w-4 h-4 text-amber-500" />}
      >
        <ul className="space-y-2">
          {company.tipsToStandOut.map((tip, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-sm text-foreground"
            >
              <span className="flex h-5 w-5 items-center justify-center rounded bg-primary/10 text-primary text-[10px] font-bold shrink-0 mt-0.5">
                {i + 1}
              </span>
              {tip}
            </li>
          ))}
        </ul>
      </Accordion>

      {/* Salary */}
      <Accordion
        title="Compensation Ranges (Public Data)"
        icon={<DollarSign className="w-4 h-4 text-success" />}
      >
        <div className="space-y-2">
          {company.salaryRange.map((s, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 rounded-xl bg-accent/20 border border-border"
            >
              <span className="text-sm font-medium text-foreground">
                {s.role}
              </span>
              <span className="text-sm font-bold font-mono text-success">
                {s.range}
              </span>
            </div>
          ))}
        </div>
      </Accordion>

      {/* Reading List */}
      <Accordion
        title="Recommended Reading"
        icon={<BookOpen className="w-4 h-4 text-info" />}
      >
        <div className="space-y-2">
          {company.readingList.map((item, i) => (
            <a
              key={i}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-xl bg-accent/20 border border-border hover:border-primary/30 transition-colors group"
            >
              <span className="text-sm text-foreground group-hover:text-primary transition-colors">
                {item.title}
              </span>
              <ExternalLink className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary shrink-0" />
            </a>
          ))}
        </div>
      </Accordion>
    </motion.div>
  );
}

/* ──────────────────────────────────────────── */
/*  Comparison radar chart                      */
/* ──────────────────────────────────────────── */
function ComparisonChart() {
  const radarData = [
    {
      subject: "Technical",
      ...Object.fromEntries(
        COMPANY_PROFILES.map((c) => [c.name, c.difficultyRating.technical * 10]),
      ),
    },
    {
      subject: "Behavioral",
      ...Object.fromEntries(
        COMPANY_PROFILES.map((c) => [c.name, c.difficultyRating.behavioral * 10]),
      ),
    },
    {
      subject: "System Design",
      ...Object.fromEntries(
        COMPANY_PROFILES.map((c) => [
          c.name,
          c.difficultyRating.systemDesign * 10,
        ]),
      ),
    },
  ];

  const colors = ["#3B82F6", "#333333", "#F59E0B", "#EF4444", "#22C55E", "#3B82F6"];

  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
      <h3 className="text-sm font-bold mb-3 flex items-center gap-2 text-foreground">
        <BarChart3 className="w-4 h-4 text-primary" /> Company Difficulty
        Comparison
      </h3>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{
                fill: "hsl(var(--foreground))",
                fontSize: 12,
                fontWeight: 500,
              }}
            />
            <PolarRadiusAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            />
            {COMPANY_PROFILES.map((c, i) => (
              <Radar
                key={c.id}
                name={c.name}
                dataKey={c.name}
                stroke={colors[i % colors.length]}
                fill={colors[i % colors.length]}
                fillOpacity={0.08}
                strokeWidth={2}
              />
            ))}
            <RechartsTooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: 12,
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-3 mt-3 justify-center">
        {COMPANY_PROFILES.map((c, i) => (
          <span
            key={c.id}
            className="flex items-center gap-1.5 text-xs text-muted-foreground"
          >
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: colors[i % colors.length] }}
            />
            {c.name}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────── */
/*  Main page                                   */
/* ──────────────────────────────────────────── */
export default function CompanyPrepPage() {
  const [activeCompanyId, setActiveCompanyId] = useState<string>(
    COMPANY_PROFILES[0].id,
  );
  const [focusMode, setFocusMode] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  const activeCompany = COMPANY_PROFILES.find((c) => c.id === activeCompanyId)!;

  return (
    <div className="max-w-5xl mx-auto py-6">
      <>
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
            <Building2 className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Company Prep Profiles
            </h1>
            <p className="text-sm text-muted-foreground">
              Inside intelligence for MAANG interviews • 6 companies
            </p>
          </div>
        </div>
      </motion.div>

      {/* Company tabs */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2 hidden-scrollbar">
        {COMPANY_PROFILES.map((c) => (
          <CompanyTab
            key={c.id}
            company={c}
            active={c.id === activeCompanyId}
            onClick={() => setActiveCompanyId(c.id)}
          />
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 mb-6 flex-wrap">
        <Button
          variant={focusMode ? "default" : "outline"}
          size="sm"
          onClick={() => setFocusMode(!focusMode)}
          className="gap-1.5 text-xs"
        >
          <Zap className="w-3.5 h-3.5" />
          {focusMode ? "Focus Mode ON" : "Focus Mode"}
        </Button>
        <Button
          variant={showComparison ? "default" : "outline"}
          size="sm"
          onClick={() => setShowComparison(!showComparison)}
          className="gap-1.5 text-xs"
        >
          <BarChart3 className="w-3.5 h-3.5" />
          {showComparison ? "Hide Comparison" : "Compare All"}
        </Button>
      </div>

      {/* Comparison chart */}
      <AnimatePresence>
        {showComparison && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <ComparisonChart />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Company detail */}
      <AnimatePresence mode="wait">
        <CompanyDetail
          key={activeCompany.id}
          company={activeCompany}
          focusMode={focusMode}
        />
      </AnimatePresence>
        </>
    </div>
  );
}
