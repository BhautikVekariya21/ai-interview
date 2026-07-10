import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("@/components/DashboardLayout", () => ({
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/hooks/useSessionStorage", () => ({
  useSessionStorage: () => ({
    session: {
      activePage: "upload",
      candidateName: "Candidate",
      generatedQuestions: [],
      mindMaps: [],
    },
    updateSession: vi.fn(),
    clearSession: vi.fn(),
  }),
}));

vi.mock("@/components/UploadPage", () => ({ default: () => <div>Upload Page</div> }));
vi.mock("@/components/InterviewPage", () => ({ default: () => <div>Interview Page</div> }));
vi.mock("@/components/ResultsPage", () => ({ default: () => <div>Results Page</div> }));
vi.mock("@/components/HistoryPage", () => ({ default: () => <div>History Page</div> }));
vi.mock("@/components/AccountPage", () => ({ default: () => <div>Account Page</div> }));
vi.mock("@/components/ScratchPad", () => ({ default: () => <div>Scratch Pad</div> }));
vi.mock("@/components/FlashcardsPage", () => ({ default: () => <div>Flashcards Page</div> }));
vi.mock("@/components/SystemDesignPage", () => ({ default: () => <div>System Design Page</div> }));
vi.mock("@/components/StarBuilderPage", () => ({ default: () => <div>STAR Builder Page</div> }));
vi.mock("@/components/CompanyPrepPage", () => ({ default: () => <div>Company Prep Page</div> }));
vi.mock("@/components/CodingPracticePage", () => ({ default: () => <div>Coding Practice Page</div> }));
vi.mock("@/components/InterviewToolkitPage", () => ({ default: () => <div>Interview Toolkit Page</div> }));
vi.mock("@/components/ResumeRoasterPage", () => ({ default: () => <div>Resume Roaster Page</div> }));
vi.mock("@/components/CoverLetterGeneratorPage", () => ({
  default: () => <div>AI Cover Letter Generator</div>,
}));

import Index from "@/pages/Index";


describe("Index cover letter route", () => {
  it("renders the cover letter page for /app/cover-letter-generator", () => {
    render(
      <MemoryRouter initialEntries={["/app/cover-letter-generator"]}>
        <Routes>
          <Route path="/app/cover-letter-generator" element={<Index />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("AI Cover Letter Generator")).toBeInTheDocument();
  });
});
