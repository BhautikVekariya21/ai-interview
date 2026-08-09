import { useState, useEffect } from "react";
import { MessageSquare, Trophy, Sun, Moon, ListChecks, Home, Settings, Menu, X, Search, BarChart3, FileText, Video, VideoOff, Mic, Square, BookOpen, PhoneOff, Code2, Building2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/AuthProvider";
import { AppPage, pageRouteMap } from "@/lib/navigation";
import { useHudState, requestInterviewAction, formatElapsed } from "@/lib/interviewHud";
import LogoStack from "@/components/LogoStack";

interface NavbarProps {
  activePage: AppPage;
  onPageChange: (page: AppPage) => void;
}

const MAIN_LINKS: { id: AppPage; label: string; icon: React.ReactNode }[] = [
  { id: "upload", label: "Dashboard", icon: <Home className="w-4 h-4" /> },
  { id: "interview", label: "Interview", icon: <MessageSquare className="w-4 h-4" /> },
  { id: "coding", label: "Practice", icon: <Code2 className="w-4 h-4" /> },
  { id: "results", label: "Results", icon: <Trophy className="w-4 h-4" /> },
  { id: "analytics", label: "Analytics", icon: <BarChart3 className="w-4 h-4" /> },
  { id: "exams", label: "Exams", icon: <Building2 className="w-4 h-4" /> },
  { id: "history", label: "History", icon: <ListChecks className="w-4 h-4" /> },
  { id: "news", label: "News", icon: <FileText className="w-4 h-4" /> },
];

const UTIL_LINKS: { id: AppPage; label: string; icon: React.ReactNode }[] = [
  { id: "account", label: "Account", icon: <Settings className="w-4 h-4" /> },
];

export default function Navbar({ activePage, onPageChange }: NavbarProps) {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("theme") as "dark" | "light") || "dark";
    }
    return "light";
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const hud = useHudState();

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("dark", "light");
    root.classList.add(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [activePage]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  const toggleTheme = () => {
    setTheme(t => t === "dark" ? "light" : "dark");
  };

  const handleNav = (page: AppPage) => {
    onPageChange(page);
    navigate(pageRouteMap[page]);
    setMobileOpen(false);
  };

  const openSearch = () =>
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }));

  return (
    <>
      <nav className="sticky top-0 z-50 flex h-14 items-center justify-between border-b px-4 bg-background/70 backdrop-blur-xl border-border md:px-6">
        {/* Left: Logo */}
        <div className="flex items-center gap-2.5">
          <Link to="/" className="flex items-center gap-2.5">
            <LogoStack badge className="h-7 w-7" />
            <span className="font-bold text-base tracking-tight text-foreground hidden sm:inline">interviewer.ai</span>
          </Link>
        </div>

        {/* Center: Desktop nav links */}
        <div className="hidden lg:flex items-center justify-center gap-0.5 px-1">
          {MAIN_LINKS.map(link => (
            <button
              key={link.id}
              onClick={() => handleNav(link.id)}
              className={cn(
                "flex items-center gap-1 rounded-lg border px-2 py-1 text-xs xl:px-2.5 xl:py-1.5 xl:text-xs 2xl:px-3 2xl:text-sm font-semibold transition-colors duration-200 cursor-pointer whitespace-nowrap",
                activePage === link.id
                  ? "border-brand/20 bg-brand/10 text-brand"
                  : "border-transparent text-foreground/70 hover:bg-accent hover:text-foreground"
              )}
            >
              {link.icon} <span className="hidden xl:inline">{link.label}</span>
            </button>
          ))}

          {/* Billing & Account */}
          {UTIL_LINKS.map(link => (
            <button
              key={link.id}
              onClick={() => handleNav(link.id)}
              className={cn(
                "flex items-center gap-1 rounded-lg border px-2 py-1 text-xs xl:px-2.5 xl:py-1.5 xl:text-xs 2xl:px-3 2xl:text-sm font-semibold transition-colors duration-200 cursor-pointer whitespace-nowrap",
                activePage === link.id
                  ? "border-brand/20 bg-brand/10 text-brand"
                  : "border-transparent text-foreground/70 hover:bg-accent hover:text-foreground"
              )}
            >
              {link.icon} <span className="hidden xl:inline">{link.label}</span>
            </button>
          ))}
        </div>

        {/* Live interview HUD — visible only during an active interview */}
        {hud.active && (
          <div className="hidden sm:flex items-center gap-1.5 rounded-lg border border-brand/20 bg-brand/5 px-2 py-1">
            <span className="flex items-center gap-1 font-mono text-xs font-semibold tabular-nums text-brand">
              <span className={cn("h-1.5 w-1.5 rounded-full", hud.recording ? "bg-destructive animate-pulse" : "bg-brand")} />
              {formatElapsed(hud.elapsed)}
            </span>
            <button
              onClick={() => requestInterviewAction("toggle-record")}
              aria-label={hud.recording ? "Stop recording" : "Start recording"}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-md border transition-colors",
                hud.recording
                  ? "border-destructive bg-destructive/10 text-destructive"
                  : "border-border text-foreground/70 hover:bg-accent hover:text-foreground"
              )}
            >
              {hud.recording ? <Square className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
            </button>
            <button
              onClick={() => requestInterviewAction("toggle-camera")}
              aria-label={hud.cameraOn ? "Turn camera off" : "Turn camera on"}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded-md border transition-colors",
                hud.cameraOn
                  ? "border-brand/30 bg-brand/10 text-brand"
                  : "border-border text-foreground/70 hover:bg-accent hover:text-foreground"
              )}
            >
              {hud.cameraOn ? <Video className="h-3.5 w-3.5" /> : <VideoOff className="h-3.5 w-3.5" />}
            </button>
            <button
              onClick={() => requestInterviewAction("end")}
              className="flex items-center gap-1 rounded-md bg-destructive px-2 py-1 text-xs font-semibold text-destructive-foreground transition-colors hover:bg-destructive/90"
            >
              <PhoneOff className="h-3.5 w-3.5" /> <span className="hidden xl:inline">End</span>
            </button>
          </div>
        )}

        {/* Right: User controls */}
        <div className="flex items-center gap-2">
          {/* Blog / Insights & Resources */}
          <button
            onClick={() => navigate("/blog")}
            className="hidden sm:flex items-center gap-1 rounded-lg border border-border bg-muted/50 px-2 py-1.5 text-xs font-semibold text-foreground/70 cursor-pointer hover:bg-accent/20 hover:text-foreground transition-colors"
          >
            <BookOpen className="h-4 w-4" /> <span className="hidden xl:inline">Blog</span>
          </button>

          {/* Cmd+K search hint (desktop only) */}
          <button
            onClick={openSearch}
            className="hidden md:flex items-center gap-1 rounded-lg border border-border bg-muted/50 px-2 py-1 text-xs text-muted-foreground cursor-pointer hover:bg-accent/20 hover:text-foreground transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden xl:inline">Search</span>
            <kbd className="hidden xl:inline-flex ml-1 pointer-events-none rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-mono font-bold">⌘K</kbd>
          </button>

          {isAuthenticated ? (
            <>
              <Button variant="outline" size="sm" className="hidden sm:inline-flex bg-background/50 text-foreground" onClick={() => void logout()}>
                Sign out
              </Button>
            </>
          ) : (
            <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex bg-background/50">
              <Link to="/auth">Sign in</Link>
            </Button>
          )}
          <button
            onClick={toggleTheme}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-muted/50 text-foreground/70 transition-all duration-200 cursor-pointer hover:bg-accent/10 hover:text-primary"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-muted/50 text-foreground/70 lg:hidden cursor-pointer hover:bg-accent/10 hover:text-primary transition-colors"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={() => setMobileOpen(false)}
          />

          {/* Drawer */}
          <div className="absolute top-14 right-0 bottom-0 w-[300px] max-w-[85vw] bg-background border-l border-border shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-300">
            <div className="p-4 space-y-1">
              {/* User info for mobile */}
              {isAuthenticated && (
                <div className="flex items-center gap-3 p-3 mb-3 rounded-xl bg-muted/30 border border-border">
                  <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
                    {(user?.full_name || user?.email || "U").charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground truncate">Signed in</p>
                  </div>
                </div>
              )}

              {/* Quick links + live interview actions */}
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground px-3 pt-2 pb-1">Quick links</p>
              {hud.active && (
                <button
                  onClick={() => { requestInterviewAction("end"); setMobileOpen(false); }}
                  className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-semibold bg-destructive/10 text-destructive border border-destructive/20 transition-all cursor-pointer"
                >
                  <PhoneOff className="w-4 h-4" /> End interview · {formatElapsed(hud.elapsed)}
                </button>
              )}
              <button
                onClick={() => { navigate("/blog"); setMobileOpen(false); }}
                className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-semibold text-foreground/80 hover:bg-accent hover:text-foreground border border-transparent transition-all cursor-pointer"
              >
                <BookOpen className="w-4 h-4" /> Blog · Insights & Resources
              </button>

              {/* Main navigation */}
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground px-3 pt-2 pb-1">Navigation</p>
              {MAIN_LINKS.map(link => (
                <button
                  key={link.id}
                  onClick={() => handleNav(link.id)}
                  className={cn(
                    "flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer",
                    activePage === link.id
                      ? "bg-brand/10 text-brand border border-brand/20"
                      : "text-foreground/80 hover:bg-accent hover:text-foreground border border-transparent"
                  )}
                >
                  {link.icon}
                  {link.label}
                </button>
              ))}

              {/* Utilities */}
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground px-3 pt-3 pb-1">Account</p>
              {UTIL_LINKS.map(link => (
                <button
                  key={link.id}
                  onClick={() => handleNav(link.id)}
                  className={cn(
                    "flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer",
                    activePage === link.id
                      ? "bg-brand/10 text-brand border border-brand/20"
                      : "text-foreground/80 hover:bg-accent hover:text-foreground border border-transparent"
                  )}
                >
                  {link.icon}
                  {link.label}
                </button>
              ))}

              {/* Auth for mobile */}
              <div className="pt-4 mt-2 border-t border-border space-y-2">
                {isAuthenticated ? (
                  <Button variant="outline" size="sm" className="w-full" onClick={() => { void logout(); setMobileOpen(false); }}>
                    Sign out
                  </Button>
                ) : (
                  <Button asChild size="sm" className="w-full">
                    <Link to="/auth">Sign in</Link>
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
