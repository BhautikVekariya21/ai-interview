import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, Sun, Moon, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/AuthProvider";
import LogoStack from "@/components/LogoStack";
import { m as motion, AnimatePresence } from "framer-motion";

const navLinks = [
  { label: "Features", href: "/features" },
  { label: "How it works", href: "/how-it-works" },
  { label: "Resources", href: "/resources" },
  { label: "Company", href: "/about" },
];

const EASE = [0.16, 1, 0.3, 1] as const;

export default function PublicNavbar({ overHero = false }: { overHero?: boolean } = {}) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") return (localStorage.getItem("theme") as "dark" | "light") || "light";
    return "light";
  });

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.classList.remove("dark", "light");
    document.documentElement.classList.add(next);
    localStorage.setItem("theme", next);
  };

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  // Close mobile menu on navigate
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <>
      <nav
        className={cn(
          "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
          scrolled ? "py-3" : "py-5"
        )}
      >
        <div
          className={cn(
            "mx-auto flex items-center justify-between transition-all duration-500",
            scrolled
              ? "max-w-[860px] nav-pill px-5 py-2"
              : "max-w-[1200px] px-6 lg:px-10"
          )}
        >
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <LogoStack badge className="h-7 w-7" />
            <span className={cn(
              "text-[17px] font-semibold tracking-tight transition-all duration-300",
              scrolled ? "text-foreground" : overHero ? "text-foreground" : "text-foreground"
            )}>
              interviewer.ai
            </span>
          </Link>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                to={link.href}
                className={cn(
                  "px-3.5 py-2 text-[14px] font-medium rounded-full transition-colors",
                  location.pathname === link.href
                    ? "text-foreground bg-foreground/5"
                    : "text-foreground/65 hover:text-foreground hover:bg-foreground/5"
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* CTA */}
          <div className="hidden items-center gap-2 md:flex">
            <button
              onClick={toggleTheme}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-background/60 text-foreground/60 hover:text-foreground hover:bg-foreground/5 transition-all"
            >
              {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            </button>
            {isAuthenticated ? (
              <Link
                to="/app"
                className="inline-flex h-9 items-center justify-center rounded-full bg-foreground px-5 text-[13px] font-semibold text-background transition-all hover:opacity-90"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/auth"
                  className="px-3.5 py-2 text-[13px] font-medium text-foreground/65 hover:text-foreground transition-colors"
                >
                  Log in
                </Link>
                <Link
                  to="/auth?mode=signup"
                  className="inline-flex h-9 items-center justify-center rounded-full bg-foreground px-5 text-[13px] font-semibold text-background transition-all hover:opacity-90 hover:scale-[1.02]"
                >
                  Get started free
                </Link>
              </>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-foreground/5 text-foreground md:hidden transition-colors"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25, ease: EASE }}
            className="fixed inset-0 z-40 bg-background pt-24 md:hidden"
          >
            <div className="flex flex-col px-6 py-4">
              {navLinks.map((link) => (
                <Link
                  key={link.label}
                  to={link.href}
                  className="block w-full py-4 text-xl font-medium text-foreground border-b border-border"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                to="/app"
                className="block w-full py-4 text-xl font-medium text-foreground border-b border-border"
              >
                App
              </Link>
              <div className="flex flex-col gap-3 pt-8">
                <Link
                  to="/auth"
                  className="flex h-12 items-center justify-center rounded-full border border-border text-base font-semibold text-foreground transition-colors hover:bg-foreground/5"
                >
                  Log in
                </Link>
                <Link
                  to="/auth?mode=signup"
                  className="flex h-12 items-center justify-center rounded-full bg-foreground text-base font-semibold text-background transition-colors hover:opacity-90"
                >
                  Get Started Free
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
