import { useEffect } from "react";
import Navbar from "@/components/Navbar";
import type { AppPage } from "@/lib/navigation";
import { recordActiveToday } from "@/lib/activityLog";

interface DashboardLayoutProps {
  children: React.ReactNode;
  activePage: AppPage;
  onPageChange: (page: AppPage) => void;
}

export default function DashboardLayout({ children, activePage, onPageChange }: DashboardLayoutProps) {
  useEffect(() => {
    recordActiveToday();
  }, []);

  return (
    <div className="relative min-h-[100dvh] flex flex-col bg-background text-foreground font-sans selection:bg-brand selection:text-brand-foreground">
      {/* Ambient aurora glow — matches the marketing hero */}
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute left-[-10%] top-[-12%] h-[560px] w-[560px] rounded-full bg-[radial-gradient(closest-side,hsl(var(--brand)/0.16),transparent)] blur-[120px]" />
        <div className="absolute right-[-8%] top-[20%] h-[480px] w-[480px] rounded-full bg-[radial-gradient(closest-side,hsl(var(--chart-3)/0.14),transparent)] blur-[130px]" />
      </div>

      <Navbar activePage={activePage} onPageChange={onPageChange} />

      <main className="flex-1 px-4 md:px-6 py-6 max-w-[1280px] mx-auto w-full">
        {children}
      </main>
    </div>
  );
}
