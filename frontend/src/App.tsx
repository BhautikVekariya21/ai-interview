import { lazy, Suspense } from "react";
import { LazyMotion, domMax, MotionConfig } from "framer-motion";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import { AuthProvider } from "./components/AuthProvider";
import PublicNavbar from "./components/PublicNavbar";
import Footer from "./components/Footer";
import Loading from "./components/Loading";

/* Route-level code splitting — everything except the first-paint Landing page
   is lazy-loaded so the heavy dashboard (PDF/canvas libs) stays out of the
   initial bundle. */
const Index = lazy(() => import("./pages/Index"));
const Auth = lazy(() => import("./pages/Auth"));
const NotFound = lazy(() => import("./pages/NotFound"));
const NewsPage = lazy(() => import("./components/NewsPage"));
const ResourcesPage = lazy(() => import("./components/ResourcesPage"));
const FeaturesPage = lazy(() => import("./pages/FeaturesPage"));
const HowItWorksPage = lazy(() => import("./pages/HowItWorksPage"));

/* Legal Pages */
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"));
const TermsOfService = lazy(() => import("./pages/TermsOfService"));
const CookiePolicy = lazy(() => import("./pages/CookiePolicy"));
const SecurityPage = lazy(() => import("./pages/SecurityPage"));

/* Company Pages */
const AboutPage = lazy(() => import("./pages/AboutPage"));
const CareersPage = lazy(() => import("./pages/CareersPage"));
const BlogPage = lazy(() => import("./pages/BlogPage"));
const ContactPage = lazy(() => import("./pages/ContactPage"));
const FeedbackPage = lazy(() => import("./pages/FeedbackPage"));
const SupportPage = lazy(() => import("./pages/SupportPage"));
const PanelInterview = lazy(() => import("./components/PanelInterview"));

const queryClient = new QueryClient();
const routerBasename = import.meta.env.BASE_URL.replace(/\/$/, "");

/**
 * Public page wrapper — PublicNavbar + Footer around content pages
 * that are accessible without logging in (News, Resources).
 */
function PublicPage({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen flex flex-col bg-background text-foreground">
      <PublicNavbar />
      <main className="mx-auto w-full max-w-[1100px] flex-1 px-6 pb-12 pt-28 lg:px-10">
        {children}
      </main>
      <Footer />
    </div>
  );
}

const App = () => (
  <LazyMotion features={domMax}>
    <MotionConfig reducedMotion="user">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter basename={routerBasename}>
              <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-background"><Loading size="lg" /></div>}>
                <Routes>
                  {/* Marketing / public pages */}
                  <Route path="/" element={<Landing />} />
                  <Route path="/auth" element={<Auth />} />
                  <Route path="/features" element={<PublicPage><FeaturesPage /></PublicPage>} />
                  <Route path="/how-it-works" element={<PublicPage><HowItWorksPage /></PublicPage>} />
                  <Route path="/panel" element={<PublicPage><PanelInterview /></PublicPage>} />
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
                  <Route path="/feedback" element={<FeedbackPage />} />
                  <Route path="/support" element={<SupportPage />} />

                  {/* App dashboard — all /app/* routes */}
                  <Route path="/app" element={<Index />} />
                  <Route path="/app/interview" element={<Index />} />
                  <Route path="/app/results" element={<Index />} />
                  <Route path="/app/history" element={<Index />} />
                  <Route path="/app/account" element={<Index />} />
                  <Route path="/app/analytics" element={<Index />} />

                  {/* Catch-all */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </TooltipProvider>
        </AuthProvider>
      </QueryClientProvider>
    </MotionConfig>
  </LazyMotion>
);

export default App;
