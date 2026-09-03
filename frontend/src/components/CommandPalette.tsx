import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { m as motion, AnimatePresence } from "framer-motion";
import {
  Search, Home, MessageSquare, Trophy, ListChecks, FileText,
  Settings, ArrowRight, Command, Zap, Code2
} from "lucide-react";
import { pageRouteMap, type AppPage } from "@/lib/navigation";

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ReactNode;
  action: () => void;
  category: string;
  keywords?: string[];
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const nav = useCallback((page: AppPage) => {
    navigate(pageRouteMap[page]);
    setOpen(false);
  }, [navigate]);

  const items: CommandItem[] = useMemo(() => [
    // Navigation
    { id: "dashboard", label: "Dashboard", description: "Upload resume & start interview", icon: <Home className="w-4 h-4" />, action: () => nav("upload"), category: "Navigation", keywords: ["home", "upload"] },
    { id: "interview", label: "Interview", description: "Active interview session", icon: <MessageSquare className="w-4 h-4" />, action: () => nav("interview"), category: "Navigation" },
    { id: "coding", label: "Practice Problems", description: "Browse and solve all coding problems", icon: <Code2 className="w-4 h-4" />, action: () => nav("coding"), category: "Navigation", keywords: ["leetcode", "code", "editor", "problems", "practice", "dsa"] },
    { id: "results", label: "Results", description: "View interview evaluation", icon: <Trophy className="w-4 h-4" />, action: () => nav("results"), category: "Navigation" },
    { id: "history", label: "History", description: "Past interview sessions", icon: <ListChecks className="w-4 h-4" />, action: () => nav("history"), category: "Navigation" },
    { id: "news", label: "News", description: "Latest tech news", icon: <FileText className="w-4 h-4" />, action: () => nav("news"), category: "Navigation", keywords: ["tech", "articles"] },

    // Account
    { id: "account", label: "Account Settings", description: "Profile & preferences", icon: <Settings className="w-4 h-4" />, action: () => nav("account"), category: "Account", keywords: ["profile", "settings"] },

    // Quick Actions
    { id: "theme-toggle", label: "Toggle Dark / Light Mode", description: "Switch theme", icon: <Zap className="w-4 h-4" />, action: () => {
      const root = document.documentElement;
      const current = root.classList.contains("dark") ? "dark" : "light";
      const next = current === "dark" ? "light" : "dark";
      root.classList.remove("dark", "light");
      root.classList.add(next);
      localStorage.setItem("theme", next);
      setOpen(false);
    }, category: "Quick Actions", keywords: ["dark", "light", "theme", "mode"] },
  ], [nav]);

  const filteredItems = useMemo(() => {
    if (!query.trim()) return items;
    const q = query.toLowerCase();
    return items.filter(item => {
      const searchable = `${item.label} ${item.description || ""} ${(item.keywords || []).join(" ")}`.toLowerCase();
      return searchable.includes(q);
    });
  }, [query, items]);

  const groupedItems = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    for (const item of filteredItems) {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push(item);
    }
    return groups;
  }, [filteredItems]);

  // Flatten for keyboard nav
  const flatItems = useMemo(() => filteredItems, [filteredItems]);

  // Open/close with Cmd+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(prev => !prev);
        setQuery("");
        setSelectedIndex(0);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(i => Math.min(i + 1, flatItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(i => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      flatItems[selectedIndex]?.action();
    }
  };

  // Scroll selected into view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`);
    if (el) el.scrollIntoView({ block: "nearest" });
  }, [selectedIndex]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[100]">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="relative mx-auto mt-[15vh] w-[95vw] max-w-[580px] rounded-2xl border border-border bg-card shadow-2xl overflow-hidden"
          >
            {/* Search input */}
            <div className="flex items-center gap-3 border-b border-border px-4 py-3">
              <Search className="w-5 h-5 text-muted-foreground shrink-0" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search pages, tools, actions..."
                className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
              />
              <kbd className="shrink-0 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono font-bold text-muted-foreground">ESC</kbd>
            </div>

            {/* Results */}
            <div ref={listRef} className="max-h-[50vh] overflow-y-auto p-2">
              {flatItems.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-sm text-muted-foreground">No results for "{query}"</p>
                </div>
              ) : (
                Object.entries(groupedItems).map(([category, categoryItems]) => (
                  <div key={category} className="mb-1">
                    <p className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                      {category}
                    </p>
                    {categoryItems.map((item) => {
                      const globalIdx = flatItems.indexOf(item);
                      return (
                        <button
                          key={item.id}
                          data-index={globalIdx}
                          onClick={item.action}
                          onMouseEnter={() => setSelectedIndex(globalIdx)}
                          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-left transition-colors cursor-pointer ${
                            globalIdx === selectedIndex
                              ? "bg-primary/10 text-primary"
                              : "text-foreground hover:bg-accent/20"
                          }`}
                        >
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                            globalIdx === selectedIndex
                              ? "bg-primary/20 text-primary"
                              : "bg-muted text-muted-foreground"
                          }`}>
                            {item.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold truncate">{item.label}</p>
                            {item.description && (
                              <p className="text-xs text-muted-foreground truncate">{item.description}</p>
                            )}
                          </div>
                          <ArrowRight className={`w-3.5 h-3.5 shrink-0 transition-opacity ${
                            globalIdx === selectedIndex ? "opacity-100 text-primary" : "opacity-0"
                          }`} />
                        </button>
                      );
                    })}
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-border px-4 py-2.5 text-[11px] text-muted-foreground">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1"><kbd className="rounded border border-border bg-muted px-1 font-mono text-[10px]">↑↓</kbd> Navigate</span>
                <span className="flex items-center gap-1"><kbd className="rounded border border-border bg-muted px-1 font-mono text-[10px]">↵</kbd> Select</span>
              </div>
              <span className="flex items-center gap-1"><Command className="w-3 h-3" /><kbd className="rounded border border-border bg-muted px-1 font-mono text-[10px]">K</kbd> Toggle</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
