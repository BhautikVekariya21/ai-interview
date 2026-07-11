import DashboardLayout from "@/components/DashboardLayout";
import UploadPage from "@/components/UploadPage";
import InterviewPage from "@/components/InterviewPage";
import ResultsPage, { type InterviewResult } from "@/components/ResultsPage";
import HistoryPage from "@/components/HistoryPage";
import AccountPage from "@/components/AccountPage";
import ScratchPad from "@/components/ScratchPad";
import DailyChallengePage from "@/components/DailyChallengePage";
import AnalyticsDashboard from "@/components/AnalyticsDashboard";
import StudyTimer from "@/components/StudyTimer";
import CommandPalette from "@/components/CommandPalette";
import { PenTool, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useSessionStorage, type SessionData } from "@/hooks/useSessionStorage";
import { getPageFromPathname, pageRouteMap } from "@/lib/navigation";
import { useLocation, useNavigate } from "react-router-dom";

export interface GeneratedQuestion {
  id: number;
  text: string;
  category: string;
  difficulty: string;
}

const Index = () => {
  const { session, updateSession, clearSession } = useSessionStorage();
  const [globalScratchOpen, setGlobalScratchOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const activePage = getPageFromPathname(location.pathname);
  const candidateName = session.candidateName;
  const resumeData = session.resumeData;
  const interviewResult = session.interviewResult as unknown as InterviewResult | undefined;
  const generatedQuestions = session.generatedQuestions;

  useEffect(() => {
    if (session.activePage !== activePage) {
      updateSession({ activePage });
    }
  }, [activePage, session.activePage, updateSession]);

  return (
    <DashboardLayout activePage={activePage} onPageChange={(p) => updateSession({ activePage: p })}>
      {activePage === "upload" && (
        <UploadPage
          onStartInterview={(resume, questions) => {
            updateSession({
              candidateName: resume.name,
              resumeData: resume as unknown as Record<string, unknown>,
              generatedQuestions: questions,
              activePage: "interview",
              interviewMessages: [],
              interviewQuestionIndex: 0,
              interviewTimer: 0,
            });
            navigate(pageRouteMap.interview);
          }}
        />
      )}
      {activePage === "interview" && (
        <InterviewPage
          candidateName={candidateName}
          resumeData={resumeData}
          questions={generatedQuestions}
          savedMessages={session.interviewMessages}
          savedQuestionIndex={session.interviewQuestionIndex}
          savedTimer={session.interviewTimer}
          onStateChange={(messages, questionIndex, timer) => {
            updateSession({
              interviewMessages: messages,
              interviewQuestionIndex: questionIndex,
              interviewTimer: timer,
            });
          }}
          onInterviewComplete={(data) => {
            updateSession({
              interviewResult: {
                candidateName,
                ...data,
              } as unknown as SessionData["interviewResult"],
              activePage: "results",
            });
            navigate(pageRouteMap.results);
          }}
        />
      )}
      {activePage === "results" && interviewResult && (
        <ResultsPage
          result={interviewResult}
          resumeData={resumeData}
          questions={generatedQuestions}
          onRestart={() => {
            clearSession();
            navigate(pageRouteMap.upload);
          }}
        />
      )}
      {activePage === "history" && (
        <HistoryPage />
      )}
      {activePage === "account" && (
        <AccountPage />
      )}
      {activePage === "daily-challenge" && (
        <DailyChallengePage />
      )}
      {activePage === "analytics" && (
        <AnalyticsDashboard />
      )}

      {/* Global Quick Note Toggle */}
      {!globalScratchOpen ? (
        <button
          onClick={() => setGlobalScratchOpen(true)}
          className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-border bg-card shadow-lg text-primary transition-all z-50 group hover:scale-105 hover:bg-primary hover:text-primary-foreground"
          title="Quick Note"
        >
          <PenTool className="h-5 w-5 transition-transform group-hover:rotate-6" />
        </button>
      ) : (
        <div className="fixed bottom-4 left-4 right-4 h-[420px] overflow-hidden rounded-2xl border border-border bg-card shadow-xl flex flex-col z-50 animate-in slide-in-from-bottom-8 md:bottom-6 md:left-auto md:right-6 md:h-[550px] md:w-[430px]">
          <div className="flex items-center justify-between border-b border-border bg-card/80 backdrop-blur-md px-4 py-3 shadow-sm">
            <span className="flex items-center gap-2 text-sm font-semibold text-foreground"><PenTool className="h-4 w-4 text-primary" /> Quick Note</span>
            <button onClick={() => setGlobalScratchOpen(false)} className="text-muted-foreground transition-colors hover:text-destructive">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 relative w-full h-full overflow-hidden">
            <ScratchPad defaultTab="note" />
          </div>
        </div>
      )}

      {/* Study Timer */}
      <StudyTimer />

      {/* Command Palette */}
      <CommandPalette />
    </DashboardLayout>
  );
};

export default Index;
