import { useState, useEffect } from "react";
import { MessageSquare, Trophy, Sun, Moon, ListChecks, Home, Settings, Flame, Menu, X, Search, BarChart3, ChevronDown, HelpCircle, FileText } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/AuthProvider";
import { AppPage, pageRouteMap } from "@/lib/navigation";

interface NavbarProps {
  activePage: AppPage;
  onPageChange: (page: AppPage) => void;
  isOnline: boolean;
}

const MAIN_LINKS: { id: AppPage; label: string; icon: React.ReactNode }[] = [
  { id: "upload", label: "Dashboard", icon: <Home className="w-4 h-4" /> },
  { id: "daily-challenge", label: "Daily Challenge", icon: <Flame className="w-4 h-4 text-orange-500" /> },
  { id: "interview", label: "Interview", icon: <MessageSquare className="w-4 h-4" /> },
  { id: "results", label: "Results", icon: <Trophy className="w-4 h-4" /> },
  { id: "analytics", label: "Analytics", icon: <BarChart3 className="w-4 h-4" /> },
];

const UTIL_LINKS: { id: AppPage; label: string; icon: React.ReactNode }[] = [
  { id: "account", label: "Account", icon: <Settings className="w-4 h-4" /> },
];

export default function Navbar({ activePage, onPageChange, isOnline }: NavbarProps) {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("theme") as "dark" | "light") || "dark";
    }
    return "light";
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    if (!dropdownOpen) return;
    const closeDropdown = () => setDropdownOpen(false);
    window.addEventListener("click", closeDropdown);
    return () => window.removeEventListener("click", closeDropdown);
  }, [dropdownOpen]);

  const handleDropdownClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDropdownOpen(!dropdownOpen);
  };

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

  return (
    <>
      <nav className="sticky top-0 z-50 flex h-14 items-center justify-between border-b px-4 bg-background shadow-sm border-border md:px-6">
        {/* Left: Logo */}
        <div className="flex items-center gap-2.5">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-foreground">
              <div className="h-3 w-3 rounded-sm bg-background" />
            </div>
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
                "flex items-center gap-1 rounded-lg border px-2 py-1 text-xs xl:px-2.5 xl:py-1.5 xl:text-xs 2xl:px-3 2xl:text-sm font-semibold transition-all duration-300 cursor-pointer whitespace-nowrap",
                activePage === link.id
                  ? "scale-[1.02] border-primary/25 bg-primary/12 text-primary ring-1 ring-primary/10"
                  : "border-transparent text-foreground/70 hover:scale-[1.02] hover:border-primary/15 hover:bg-accent/10 hover:text-foreground"
              )}
            >
              {link.icon} <span className="hidden xl:inline">{link.label}</span>
            </button>
          ))}

          {/* Dropdown for Others */}
          <div className="relative">
            <button
              onClick={handleDropdownClick}
              className={cn(
                "flex items-center gap-1 rounded-lg border px-2 py-1 text-xs xl:px-2.5 xl:py-1.5 xl:text-xs 2xl:px-3 2xl:text-sm font-semibold transition-all duration-300 cursor-pointer whitespace-nowrap",
                ["history", "faq", "news"].includes(activePage)
                  ? "scale-[1.02] border-primary/25 bg-primary/12 text-primary ring-1 ring-primary/10"
                  : "border-transparent text-foreground/70 hover:scale-[1.02] hover:border-primary/15 hover:bg-accent/10 hover:text-foreground"
              )}
            >
              Others <ChevronDown className={cn("w-3.5 h-3.5 transition-transform duration-200", dropdownOpen && "rotate-180")} />
            </button>

            {dropdownOpen && (
              <div className="absolute left-0 mt-1.5 w-44 rounded-xl border border-border bg-popover p-1 shadow-md z-50 animate-in fade-in-0 slide-in-from-top-1 duration-200">
                <button
                  onClick={() => handleNav("history")}
                  className={cn(
                    "flex items-center gap-2 w-full px-2.5 py-2 rounded-lg text-xs font-semibold cursor-pointer text-left transition-colors",
                    activePage === "history"
                      ? "bg-accent text-accent-foreground"
                      : "text-foreground/80 hover:bg-accent/50 hover:text-foreground"
                  )}
                >
                  <ListChecks className="w-4 h-4 text-success" /> History
                </button>
                <button
                  onClick={() => handleNav("faq")}
                  className={cn(
                    "flex items-center gap-2 w-full px-2.5 py-2 rounded-lg text-xs font-semibold cursor-pointer text-left transition-colors",
                    activePage === "faq"
                      ? "bg-accent text-accent-foreground"
                      : "text-foreground/80 hover:bg-accent/50 hover:text-foreground"
                  )}
                >
                  <HelpCircle className="w-4 h-4 text-info" /> FAQ
                </button>
                <button
                  onClick={() => handleNav("news")}
                  className={cn(
                    "flex items-center gap-2 w-full px-2.5 py-2 rounded-lg text-xs font-semibold cursor-pointer text-left transition-colors",
                    activePage === "news"
                      ? "bg-accent text-accent-foreground"
                      : "text-foreground/80 hover:bg-accent/50 hover:text-foreground"
                  )}
                >
                  <FileText className="w-4 h-4 text-primary" /> Tech News
                </button>
              </div>
            )}
          </div>

          {/* Billing & Account */}
          {UTIL_LINKS.map(link => (
            <button
              key={link.id}
              onClick={() => handleNav(link.id)}
              className={cn(
                "flex items-center gap-1 rounded-lg border px-2 py-1 text-xs xl:px-2.5 xl:py-1.5 xl:text-xs 2xl:px-3 2xl:text-sm font-semibold transition-all duration-300 cursor-pointer whitespace-nowrap",
                activePage === link.id
                  ? "scale-[1.02] border-primary/25 bg-primary/12 text-primary ring-1 ring-primary/10"
                  : "border-transparent text-foreground/70 hover:scale-[1.02] hover:border-primary/15 hover:bg-accent/10 hover:text-foreground"
              )}
            >
              {link.icon} <span className="hidden xl:inline">{link.label}</span>
            </button>
          ))}
        </div>

        {/* Right: User controls */}
        <div className="flex items-center gap-2">
          {/* Cmd+K search hint (desktop only) */}
          <button
            onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
            className="hidden md:flex items-center gap-1 rounded-lg border border-border bg-muted/50 px-2 py-1 text-xs text-muted-foreground cursor-pointer hover:bg-accent/20 hover:text-foreground transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden xl:inline">Search</span>
            <kbd className="hidden xl:inline-flex ml-1 pointer-events-none rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-mono font-bold">⌘K</kbd>
          </button>

          {isAuthenticated ? (
            <>
              <div className="hidden items-center gap-2 xl:flex">
                <div className="rounded-xl border border-border bg-background/60 px-3 py-1 text-xs text-muted-foreground truncate max-w-[140px]">
                  {user?.full_name || user?.email}
                </div>
              </div>
              <Button variant="outline" size="sm" className="hidden sm:inline-flex bg-background/50 text-foreground" onClick={() => void logout()}>
                Sign out
              </Button>
            </>
          ) : (
            <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex bg-background/50">
              <Link to="/auth">Sign in</Link>
            </Button>
          )}
          <div className="hidden sm:flex items-center gap-1 text-xs text-muted-foreground px-2 py-1 rounded-xl bg-muted border border-border">
            <div className={cn("w-1.5 h-1.5 rounded-xl", isOnline ? "bg-success" : "bg-destructive")} />
            <span className="hidden xl:inline">{isOnline ? "Online" : "Offline"}</span>
          </div>
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
                    <p className="text-sm font-semibold text-foreground truncate">{user?.full_name || user?.email}</p>
                  </div>
                </div>
              )}

              {/* Main navigation */}
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground px-3 pt-2 pb-1">Navigation</p>
              {MAIN_LINKS.map(link => (
                <button
                  key={link.id}
                  onClick={() => handleNav(link.id)}
                  className={cn(
                    "flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer",
                    activePage === link.id
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "text-foreground/80 hover:bg-accent/20 hover:text-foreground border border-transparent"
                  )}
                >
                  {link.icon}
                  {link.label}
                </button>
              ))}

              {/* Others section in mobile menu */}
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground px-3 pt-3 pb-1">Others</p>
              {[
                { id: "history", label: "History", icon: <ListChecks className="w-4 h-4 text-success" /> },
                { id: "faq", label: "FAQ", icon: <HelpCircle className="w-4 h-4 text-info" /> },
                { id: "news", label: "Tech News", icon: <FileText className="w-4 h-4 text-primary" /> },
              ].map(link => (
                <button
                  key={link.id}
                  onClick={() => handleNav(link.id as AppPage)}
                  className={cn(
                    "flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-semibold transition-all cursor-pointer",
                    activePage === link.id
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "text-foreground/80 hover:bg-accent/20 hover:text-foreground border border-transparent"
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
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "text-foreground/80 hover:bg-accent/20 hover:text-foreground border border-transparent"
                  )}
                >
                  {link.icon}
                  {link.label}
                </button>
              ))}

              {/* Online status + auth for mobile */}
              <div className="pt-4 mt-2 border-t border-border space-y-2">
                <div className="flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground">
                  <div className={cn("w-2 h-2 rounded-full", isOnline ? "bg-success" : "bg-destructive")} />
                  {isOnline ? "Online" : "Offline"}
                </div>
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
