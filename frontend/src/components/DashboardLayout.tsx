import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import type { AppPage } from "@/lib/navigation";

interface DashboardLayoutProps {
  children: React.ReactNode;
  activePage: AppPage;
  onPageChange: (page: AppPage) => void;
}

export default function DashboardLayout({ children, activePage, onPageChange }: DashboardLayoutProps) {
  return (
    <div className="relative min-h-[100dvh] flex flex-col bg-background text-foreground font-sans selection:bg-foreground selection:text-background">
      {/* App wrapper */}

      <Navbar activePage={activePage} onPageChange={onPageChange} isOnline={true} />

      <main className="flex-1 px-4 md:px-6 py-6 max-w-[1280px] mx-auto w-full">
        {children}
      </main>

      <Footer />
    </div>
  );
}
