import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import LogoMark from "@/components/LogoMark";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/AuthProvider";

const navLinks = [
  { label: "Features", href: "/#features" },
];

export default function PublicNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") return (localStorage.getItem("theme") as "dark" | "light") || "dark";
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
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  // Close mobile menu on navigate
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleAnchorClick = (href: string) => {
    if (href.startsWith("/#")) {
      const id = href.replace("/#", "");
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
        setMobileOpen(false);
        return;
      }
    }
  };

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-background/95 backdrop-blur-md border-b border-border py-2"
          : "bg-transparent py-4"
      )}
    >
      <div className="mx-auto flex h-14 w-full max-w-[1400px] items-center justify-between px-6 lg:px-12">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex flex-col items-center justify-center gap-[3px] w-8 h-8">
            <div className="w-[18px] h-[5px] bg-foreground rounded-xl" />
            <div className="w-[26px] h-[5px] bg-foreground rounded-xl" />
            <div className="w-[18px] h-[5px] bg-foreground rounded-xl" />
          </div>
          <span className="text-[20px] font-bold tracking-tight text-foreground">Prep deeper.</span>
        </Link>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) =>
            link.href.startsWith("/#") ? (
              <button
                key={link.label}
                onClick={() => handleAnchorClick(link.href)}
                className="text-sm font-semibold text-foreground/80 transition-colors hover:text-foreground"
              >
                {link.label}
              </button>
            ) : (
              <Link
                key={link.label}
                to={link.href}
                className="text-sm font-semibold text-foreground/80 transition-colors hover:text-foreground"
              >
                {link.label}
              </Link>
            )
          )}
        </div>

        {/* CTA */}
        <div className="hidden items-center gap-3 md:flex">
          <button
            onClick={toggleTheme}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-muted/50 text-foreground/70 transition-all hover:bg-accent/10 hover:text-foreground"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          {isAuthenticated ? (
            <Button asChild size="sm" className="rounded-xl bg-foreground text-background hover:bg-foreground/80 font-bold px-6">
              <Link to="/app">Go to Dashboard</Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm" className="font-semibold text-foreground/80 hover:bg-transparent hover:text-foreground">
                <Link to="/auth">Log in</Link>
              </Button>
              <Button asChild size="sm" className="rounded-xl bg-foreground text-background hover:bg-foreground/80 hover:scale-105 transition-all font-bold px-6 border-none shadow-none">
                <Link to="/auth?mode=signup">Start Free</Link>
              </Button>
            </>
          )}
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted/50 text-foreground md:hidden"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="absolute top-full left-0 right-0 border-t border-border bg-background shadow-xl animate-in slide-in-from-top-2 md:hidden">
          <div className="space-y-4 px-6 py-6 pb-8">
            {navLinks.map((link) =>
              link.href.startsWith("/#") ? (
                <button
                  key={link.label}
                  onClick={() => handleAnchorClick(link.href)}
                  className="block w-full text-left text-lg font-bold text-foreground"
                >
                  {link.label}
                </button>
              ) : (
                <Link
                  key={link.label}
                  to={link.href}
                  className="block w-full text-lg font-bold text-foreground"
                >
                  {link.label}
                </Link>
              )
            )}
            <div className="flex flex-col gap-3 pt-6 border-t border-border">
              <Button asChild variant="outline" className="w-full rounded-xl h-12 text-base font-bold">
                <Link to="/auth">Log in</Link>
              </Button>
              <Button asChild className="w-full rounded-xl h-12 text-base font-bold bg-foreground text-background shadow-none">
                <Link to="/auth?mode=signup">Start For Free</Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
