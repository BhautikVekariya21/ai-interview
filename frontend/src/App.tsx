import { LazyMotion, domAnimation, MotionConfig } from "framer-motion";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import TryInterview from "./pages/TryInterview";
import Auth from "./pages/Auth";
import { AuthProvider } from "./components/AuthProvider";
import PublicNavbar from "./components/PublicNavbar";
import Footer from "./components/Footer";
import FAQPage from "./components/FAQPage";
import NewsPage from "./components/NewsPage";
import ResourcesPage from "./components/ResourcesPage";

/* Legal Pages */
import PrivacyPolicy from "./pages/PrivacyPolicy";
import TermsOfService from "./pages/TermsOfService";
import CookiePolicy from "./pages/CookiePolicy";
import SecurityPage from "./pages/SecurityPage";

/* Company Pages */
import AboutPage from "./pages/AboutPage";
import CareersPage from "./pages/CareersPage";
import BlogPage from "./pages/BlogPage";
import ContactPage from "./pages/ContactPage";

const queryClient = new QueryClient();

/**
 * Public page wrapper — PublicNavbar + Footer around content pages
 * that are accessible without logging in (FAQ, News, Resources).
 */
function PublicPage({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Ambient glows */}
      <div className="fixed top-[10%] left-[20%] w-[500px] h-[500px] rounded-xl blur-[120px] pointer-events-none opacity-40 bg-transparent" />
      <div className="fixed top-[-100px] right-[-100px] w-[500px] h-[500px] rounded-xl blur-[140px] pointer-events-none opacity-40 bg-transparent" />

      <PublicNavbar />
      <main className="flex-1 px-4 md:px-6 py-6 pt-24 max-w-[1280px] mx-auto w-full">
        {children}
      </main>
      <Footer />
    </div>
  );
}

const App = () => (
  <LazyMotion features={domAnimation}>
    <MotionConfig reducedMotion="user">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter basename={import.meta.env.BASE_URL}>
              <Routes>
                {/* Marketing / public pages */}
                <Route path="/" element={<Landing />} />
                <Route path="/auth" element={<Auth />} />
                <Route path="/try" element={<TryInterview />} />
                <Route path="/faq" element={<PublicPage><FAQPage /></PublicPage>} />
                <Route path="/news" element={<PublicPage><NewsPage /></PublicPage>} />
                <Route path="/resources" element={<PublicPage><ResourcesPage /></PublicPage>} />

                {/* Legal */}
                <Route path="/privacy" element={<PrivacyPolicy />} />
                <Route path="/terms" element={<TermsOfService />} />
                <Route path="/cookies" element={<CookiePolicy />} />
                <Route path="/security" element={<SecurityPage />} />

                {/* Company */}
                <Route path="/about" element={<AboutPage />} />
                <Route path="/careers" element={<CareersPage />} />
                <Route path="/blog" element={<BlogPage />} />
                <Route path="/contact" element={<ContactPage />} />

                {/* App dashboard — all /app/* routes */}
                <Route path="/app" element={<Index />} />
                <Route path="/app/interview" element={<Index />} />
                <Route path="/app/results" element={<Index />} />
                <Route path="/app/history" element={<Index />} />
                <Route path="/app/account" element={<Index />} />
                <Route path="/app/flashcards" element={<Index />} />
                <Route path="/app/system-design" element={<Index />} />
                <Route path="/app/star-builder" element={<Index />} />
                <Route path="/app/company-prep" element={<Index />} />
                <Route path="/app/coding-practice" element={<Index />} />
                <Route path="/app/interview-toolkit" element={<Index />} />
                <Route path="/app/resume-roaster" element={<Index />} />
                <Route path="/app/cover-letter-generator" element={<Index />} />
                <Route path="/app/daily-challenge" element={<Index />} />
                <Route path="/app/analytics" element={<Index />} />
                <Route path="/app/achievements" element={<Index />} />

                {/* Catch-all */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
          </TooltipProvider>
        </AuthProvider>
      </QueryClientProvider>
    </MotionConfig>
  </LazyMotion>
);

export default App;
