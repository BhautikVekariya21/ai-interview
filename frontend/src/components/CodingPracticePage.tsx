import { useState, useEffect, useMemo, useCallback } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import Editor, { loader } from "@monaco-editor/react";
import {
  Code2,
  Play,
  Send,
  RotateCcw,
  ChevronLeft,
  ChevronsLeft,
  ChevronRight,
  ChevronsRight,
  Check,
  X,
  Search,
  Filter,
  Lightbulb,
  Eye,
  Trophy,
  Flame,
  Target,
  BarChart3,
  Clock,
  Building2,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Mic,
  Square,
  MessageCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  CODING_PROBLEMS,
  CODING_TOPICS,
  DIFFICULTY_COLORS,
  type CodingProblem,
} from "./codingProblemsData";
import {
  executeCodingSolution,
  fetchCodingProblems,
  fetchCodingProblem,
  fetchCodingLanguages,
  fetchCodingProgress,
  submitCodingSolution,
  reviewCodingSolution,
  resetCodingProgress,
  transcribeAudio,
  rubberDuck,
  type CodingExecutionResponse,
  type CodingLanguageOption,
  type CodingProblemSummary,
  type CodingProblemDetail,
  type CodingProgressEntry,
  type CodeReview,
} from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { toast } from "sonner";

/* ─── LocalStorage persistence ──────────────────────── */
const LS_KEY = "coding_practice_progress";
const DEFAULT_LANGUAGE = "python";
const LANGUAGE_LABELS: Record<string, string> = {
  python: "Python",
  javascript: "JavaScript",
  java: "Java",
  cpp: "C++",
  c: "C",
  rust: "Rust",
};
const FALLBACK_LANGUAGE_OPTIONS: CodingLanguageOption[] = [
  { id: "python", label: "Python", enabled: true, providers: [] },
  { id: "javascript", label: "JavaScript", enabled: true, providers: ["browser"] },
  { id: "java", label: "Java", enabled: true, providers: [] },
  { id: "cpp", label: "C++", enabled: true, providers: [] },
  { id: "c", label: "C", enabled: true, providers: [] },
  { id: "rust", label: "Rust", enabled: true, providers: [] },
];

interface LocalProgress {
  solved: Record<number, { code: string; language: string; timestamp: string; attempts: number }>;
  streak: number;
  lastSolvedDate: string | null;
}

function loadLocalProgress(): LocalProgress {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as LocalProgress;
      for (const entry of Object.values(parsed.solved || {})) {
        if (!entry.language) entry.language = DEFAULT_LANGUAGE;
      }
      return parsed;
    }
  } catch {}
  return { solved: {}, streak: 0, lastSolvedDate: null };
}

function saveLocalProgress(p: LocalProgress) {
  localStorage.setItem(LS_KEY, JSON.stringify(p));
}

/* ─── Test Runner (in-browser) ──────────────────────── */
interface TestResult {
  input: string;
  expected: string;
  actual: string;
  passed: boolean;
  error?: string;
  time?: number;
}

function runTests(code: string, testCases: { input: string; expected: string }[]): TestResult[] {
  const results: TestResult[] = [];

  for (const tc of testCases) {
    const start = performance.now();
    try {
      // Parse input args
      const args = JSON.parse(tc.input);
      // Build function from user code. Support both function declarations and class based
      const wrappedCode = `
        ${code}
        const __args = ${JSON.stringify(args)};
        const __fnNames = [];
        ${code.includes("class ") ? `
          // Handle class-based problems
          const __className = "${code.match(/class\s+(\w+)/)?.[1] || "Solution"}";
          const __cls = eval(__className);
          if (__args.length === 2 && Array.isArray(__args[0]) && Array.isArray(__args[1])) {
            const methods = __args[0];
            const params = __args[1];
            const results = [];
            let instance;
            for (let i = 0; i < methods.length; i++) {
              if (i === 0 || methods[i] === __className) {
                instance = new __cls(...(params[i] || []));
                results.push(null);
              } else {
                results.push(instance[methods[i]](...(params[i] || [])));
              }
            }
            return JSON.stringify(results);
          }
        ` : `
          // Get the first function declared
          const __match = \`${code.replace(/`/g, "\\`")}\`.match(/function\\s+(\\w+)/);
          const __solMatch = \`${code.replace(/`/g, "\\`")}\`.match(/(?:const|let|var)\\s+(\\w+)\\s*=/);
          const __fnName = __match ? __match[1] : (__solMatch ? __solMatch[1] : "solution");
          const __fn = eval(__fnName);
          return JSON.stringify(__fn(...__args));
        `}
      `;

      const fn = new Function(wrappedCode);
      const result = fn();
      const elapsed = performance.now() - start;

      // Normalize comparison
      const actualStr = result ?? "undefined";
      const expectedNorm = tc.expected.trim();
      const actualNorm = String(actualStr).trim();

      // Deep comparison for arrays/objects
      let passed = false;
      try {
        const expParsed = JSON.parse(expectedNorm);
        const actParsed = JSON.parse(actualNorm);
        passed = JSON.stringify(sortDeep(expParsed)) === JSON.stringify(sortDeep(actParsed));
      } catch {
        passed = actualNorm === expectedNorm;
      }

      results.push({
        input: tc.input,
        expected: tc.expected,
        actual: actualStr,
        passed,
        time: elapsed,
      });
    } catch (e: any) {
      results.push({
        input: tc.input,
        expected: tc.expected,
        actual: "Error",
        passed: false,
        error: e.message || "Runtime error",
        time: performance.now() - start,
      });
    }
  }
  return results;
}

function sortDeep(val: any): any {
  if (Array.isArray(val)) {
    const sorted = val.map(sortDeep);
    // For arrays of arrays, sort by stringified value
    if (sorted.length > 0 && Array.isArray(sorted[0])) {
      return sorted.sort((a: any, b: any) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
    }
    return sorted;
  }
  return val;
}

/**
 * Convert a JS starter code snippet into the equivalent starter for another language.
 * Used as a fallback when the backend's starterTemplates are not available.
 */
function _convertJsStarter(jsStarter: string, language: string): string {
  // Extract function name and params from JS: function foo(a, b) { ... }
  const fnMatch = jsStarter.match(/function\s+(\w+)\s*\(([^)]*)\)/);
  const fnName = fnMatch?.[1] ?? "solve";
  const params = fnMatch?.[2]?.split(",").map((p) => p.trim()).filter(Boolean) ?? [];

  switch (language) {
    case "python":
      return `def ${fnName}(${params.join(", ")}):\n    # Your code here\n    pass`;
    case "java":
      return `public static void ${fnName}(${params.map((p) => `Object ${p}`).join(", ")}) {\n    // Your code here\n}`;
    case "cpp":
      return `void ${fnName}(${params.map((p) => `auto ${p}`).join(", ")}) {\n    // Your code here\n}`;
    case "c":
      return `void ${fnName}(const char *input_json) {\n    /* Parse input_json and print JSON-compatible output. */\n}`;
    case "rust":
      return `fn ${fnName}(${params.map((p) => `${p}: String`).join(", ")}) {\n    // Your code here\n}`;
    default:
      return jsStarter;
  }
}

/**
 * Convert a JS solution into an equivalent stub for another language.
 * Used when solutionsByLanguage is not available from the backend.
 */
function _convertJsSolution(jsSolution: string, language: string): string {
  if (language === "javascript") return jsSolution;
  const header = `// Solution converted to ${LANGUAGE_LABELS[language] || language}\n// Note: This is an auto-converted version. Refer to JavaScript solution for logic.\n\n`;
  switch (language) {
    case "python": {
      let py = jsSolution;
      py = py.replace(/function\s+(\w+)\s*\(([^)]*)\)\s*\{/g, 'def $1($2):');
      py = py.replace(/\/\/.*/g, (m) => '# ' + m.slice(2).trim());
      py = py.replace(/const |let |var /g, '');
      py = py.replace(/===?/g, '==');
      py = py.replace(/!==?/g, '!=');
      py = py.replace(/null/g, 'None');
      py = py.replace(/true/g, 'True');
      py = py.replace(/false/g, 'False');
      py = py.replace(/&&/g, 'and');
      py = py.replace(/\|\|/g, 'or');
      py = py.replace(/return /g, 'return ');
      return header + py;
    }
    case "java":
    case "cpp":
    case "c":
    case "rust": {
      let code = jsSolution;
      code = code.replace(/function\s+(\w+)\s*\(([^)]*)\)\s*\{/g, (match, name, args) => {
        const params = args.split(',').map(p => p.trim()).filter(Boolean);
        if (language === 'java') return `public static Object ${name}(${params.map(p => `Object ${p}`).join(", ")}) {`;
        if (language === 'cpp') return `auto ${name}(${params.map(p => `auto ${p}`).join(", ")}) {`;
        if (language === 'c') return `void ${name}(const char *input_json) {\n  /* Parse input_json */`;
        if (language === 'rust') return `fn ${name}(${params.map(p => `${p}: String`).join(", ")}) {`;
        return match;
      });
      code = code.replace(/const |let |var /g, () => {
        if (language === 'java') return 'Object ';
        if (language === 'cpp') return 'auto ';
        if (language === 'c') return '/* type */ ';
        if (language === 'rust') return 'let mut ';
        return 'auto ';
      });
      code = code.replace(/===?/g, '==');
      code = code.replace(/!==?/g, '!=');
      
      if (language === 'rust') {
        code = code.replace(/null/g, 'None');
        code = code.replace(/console\.log/g, 'println!');
      } else if (language === 'cpp') {
        code = code.replace(/null/g, 'nullptr');
        code = code.replace(/console\.log/g, 'cout <<');
      } else if (language === 'c') {
        code = code.replace(/null/g, 'NULL');
        code = code.replace(/console\.log/g, 'printf');
      } else if (language === 'java') {
        code = code.replace(/console\.log/g, 'System.out.println');
      }
      return header + code;
    }
    default:
      return jsSolution;
  }
}

/**
 * Get the solution code for a specific language.
 */
function getSolutionForLanguage(
  problem: (CodingProblemDetail | CodingProblem) | null,
  language: string,
): string {
  if (!problem) return "";
  // Prefer backend-provided per-language solutions
  const solutions = (problem as CodingProblemDetail).solutionsByLanguage;
  if (solutions?.[language]) return solutions[language];
  // If language is JS, use the original solutionCode
  if (language === "javascript") return problem.solutionCode;
  // Otherwise convert from JS
  return _convertJsSolution(problem.solutionCode, language);
}

function getStarterForLanguage(
  problem: (CodingProblemDetail | CodingProblem) | null,
  language: string,
) {
  if (!problem) return "";
  // Prefer backend-provided per-language templates
  const templates = (problem as CodingProblemDetail).starterTemplates;
  if (templates?.[language]) return templates[language];
  // If language is JS, use the original starterCode directly
  if (language === "javascript") return problem.starterCode;
  // Otherwise generate from the JS starter
  return _convertJsStarter(problem.starterCode, language);
}

const MONACO_LANGUAGE_MAP: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  java: "java",
  cpp: "cpp",
  c: "c",
  rust: "rust",
};

// Initialize and define custom Monaco editor themes globally to prevent background mismatches during load.
if (typeof window !== "undefined") {
  loader.init().then((monaco) => {
    monaco.editor.defineTheme("custom-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#0f0f0f",
      },
    });
    monaco.editor.defineTheme("custom-light", {
      base: "vs",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#ffffff",
      },
    });
  });
}

function useIsDarkMode(): boolean {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === "undefined") return true;
    const hasDarkClass = document.documentElement.classList.contains("dark");
    if (hasDarkClass) return true;
    const savedTheme = localStorage.getItem("theme");
    return savedTheme === "dark" || !savedTheme; // default to dark if not configured
  });
  useEffect(() => {
    const target = document.documentElement;
    const observer = new MutationObserver(() => {
      setIsDark(target.classList.contains("dark"));
    });
    observer.observe(target, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);
  return isDark;
}

function mapExecutionResults(response: CodingExecutionResponse): TestResult[] {
  return response.results.map((result) => ({
    input: result.input,
    expected: result.expected,
    actual: result.actual,
    passed: result.passed,
    error: result.error,
    time: result.time_ms ?? undefined,
  }));
}

/* ─── Main Component ────────────────────────────────── */
type View = "list" | "solve";

export default function CodingPracticePage() {
  const { isAuthenticated } = useAuth();

  // Data
  const [problems, setProblems] = useState<(CodingProblemSummary | CodingProblem)[]>(CODING_PROBLEMS);
  const [localProgress, setLocalProgress] = useState<LocalProgress>(loadLocalProgress);
  const [serverProgress, setServerProgress] = useState<Record<number, CodingProgressEntry>>({});
  const [serverStreak, setServerStreak] = useState(0);

  // View state
  const [view, setView] = useState<View>("list");
  const [activeProblem, setActiveProblem] = useState<(CodingProblemDetail | CodingProblem) | null>(null);

  // Filters
  const [topicFilter, setTopicFilter] = useState<string>("All");
  const [difficultyFilter, setDifficultyFilter] = useState<string>("All");
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);

  // Code editor state
  const [code, setCode] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState(DEFAULT_LANGUAGE);
  const [languageOptions, setLanguageOptions] = useState<CodingLanguageOption[]>(FALLBACK_LANGUAGE_OPTIONS);
  const [codeByLanguage, setCodeByLanguage] = useState<Record<string, string>>({});
  const [executionProvider, setExecutionProvider] = useState("judge0");
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [showSolution, setShowSolution] = useState(false);
  const [showHints, setShowHints] = useState(false);
  const [revealedHints, setRevealedHints] = useState(0);
  const [aiReview, setAiReview] = useState<CodeReview["review"] | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const isDarkMode = useIsDarkMode();

  // AI Rubber Duck
  type DuckMessage = { role: "user" | "duck"; text: string };
  const [duckMessages, setDuckMessages] = useState<DuckMessage[]>([]);
  const [isDuckThinking, setIsDuckThinking] = useState(false);
  const duckRecorder = useAudioRecorder();

  // Load problems from backend
  useEffect(() => {
    fetchCodingProblems()
      .then((data) => {
        if (data.length > 0) setProblems(data);
      })
      .catch(() => {
        // Use local fallback
      });
  }, []);

  useEffect(() => {
    fetchCodingLanguages()
      .then((data) => {
        if (data.length > 0) setLanguageOptions(data);
      })
      .catch(() => {
        // Use fallback language list
      });
  }, []);

  // Load progress from backend
  useEffect(() => {
    if (isAuthenticated) {
      fetchCodingProgress()
        .then(({ progress, streak }) => {
          const map: Record<number, CodingProgressEntry> = {};
          for (const p of progress) map[p.problem_id] = p;
          setServerProgress(map);
          setServerStreak(streak.current_streak);
        })
        .catch(() => {});
    }
  }, [isAuthenticated]);

  // Persist local progress
  useEffect(() => {
    saveLocalProgress(localProgress);
  }, [localProgress]);

  // Solved set (combined)
  const solvedSet = useMemo(() => {
    const s = new Set<number>();
    for (const id of Object.keys(localProgress.solved)) s.add(Number(id));
    for (const [id, entry] of Object.entries(serverProgress)) {
      if (entry.solved) s.add(Number(id));
    }
    return s;
  }, [localProgress.solved, serverProgress]);

  // Filtered problems
  const filteredProblems = useMemo(() => {
    return problems.filter((p) => {
      if (topicFilter !== "All" && p.topic !== topicFilter) return false;
      if (difficultyFilter !== "All" && p.difficulty !== difficultyFilter) return false;
      if (statusFilter === "Solved" && !solvedSet.has(p.id)) return false;
      if (statusFilter === "Unsolved" && solvedSet.has(p.id)) return false;
      if (searchQuery && !p.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [problems, topicFilter, difficultyFilter, statusFilter, searchQuery, solvedSet]);

  useEffect(() => {
    setCurrentPage(1);
  }, [topicFilter, difficultyFilter, statusFilter, searchQuery]);

  // Pagination computed variables
  const totalPages = Math.max(1, Math.ceil(filteredProblems.length / itemsPerPage));
  const paginatedProblems = useMemo(() => {
    return filteredProblems.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  }, [filteredProblems, currentPage, itemsPerPage]);

  // Stats
  const totalSolved = solvedSet.size;
  const totalProblems = problems.length;
  const streak = isAuthenticated ? serverStreak : localProgress.streak;
  const easyCount = problems.filter((p) => p.difficulty === "Easy").length;
  const easySolved = problems.filter((p) => p.difficulty === "Easy" && solvedSet.has(p.id)).length;
  const mediumCount = problems.filter((p) => p.difficulty === "Medium").length;
  const mediumSolved = problems.filter((p) => p.difficulty === "Medium" && solvedSet.has(p.id)).length;
  const hardCount = problems.filter((p) => p.difficulty === "Hard").length;
  const hardSolved = problems.filter((p) => p.difficulty === "Hard" && solvedSet.has(p.id)).length;

  // Open problem
  const openProblem = useCallback(async (id: number) => {
    const savedLanguage =
      serverProgress[id]?.language ||
      localProgress.solved[id]?.language ||
      DEFAULT_LANGUAGE;

    // Try fetching from backend first for full detail
    try {
      const detail = await fetchCodingProblem(id);
      setActiveProblem(detail);
      const savedCode =
        serverProgress[id]?.code ||
        localProgress.solved[id]?.code ||
        getStarterForLanguage(detail, savedLanguage);
      setSelectedLanguage(savedLanguage);
      setCodeByLanguage({ [savedLanguage]: savedCode });
      setCode(savedCode);
    } catch {
      // Fallback to local data
      const local = CODING_PROBLEMS.find((p) => p.id === id);
      if (local) {
        setActiveProblem(local);
        const fallbackLanguage = localProgress.solved[id]?.language || DEFAULT_LANGUAGE;
        const savedCode = localProgress.solved[id]?.code || local.starterCode;
        setSelectedLanguage(fallbackLanguage);
        setCodeByLanguage({ [fallbackLanguage]: savedCode });
        setCode(savedCode);
      }
    }
    setExecutionProvider("judge0");
    setTestResults([]);
    setShowSolution(false);
    setShowHints(false);
    setRevealedHints(0);
    setAiReview(null);
    setDuckMessages([]);
    setView("solve");
  }, [serverProgress, localProgress]);

  const executeAgainstBackend = useCallback(async () => {
    if (!activeProblem) return null;

    try {
      const response = await executeCodingSolution(activeProblem.id, {
        code,
        language: selectedLanguage,
      });
      setExecutionProvider(response.provider);
      return response;
    } catch (error) {
      if (selectedLanguage === "javascript") {
        const fallbackResults = runTests(code, activeProblem.testCases);
        const passedTests = fallbackResults.filter((result) => result.passed).length;
        setExecutionProvider("browser");
        return {
          success: true,
          language: selectedLanguage,
          provider: "browser",
          total_tests: fallbackResults.length,
          passed_tests: passedTests,
          all_passed: passedTests === fallbackResults.length,
          results: fallbackResults.map((result) => ({
            input: result.input,
            expected: result.expected,
            actual: result.actual,
            passed: result.passed,
            error: result.error,
            time_ms: result.time ?? null,
            status: result.passed ? "Accepted" : "Wrong Answer",
          })),
        } satisfies CodingExecutionResponse;
      }
      throw error;
    }
  }, [activeProblem, code, selectedLanguage]);

  // Run tests
  const handleRunTests = useCallback(async () => {
    if (!activeProblem) return;
    setIsRunning(true);
    setAiReview(null);

    try {
      const response = await executeAgainstBackend();
      if (!response) return;
      setTestResults(mapExecutionResults(response));
      if (response.provider === "browser") {
        toast.info("Backend judge was unavailable, so JavaScript ran in the browser fallback.");
      }
    } catch (error: any) {
      toast.error(error?.message || "Code execution failed. Please try again.");
    } finally {
      setIsRunning(false);
    }
  }, [activeProblem, executeAgainstBackend]);

  // Submit solution
  const handleSubmit = useCallback(async () => {
    if (!activeProblem) return;
    setIsRunning(true);

    try {
      const response = await executeAgainstBackend();
      if (!response) return;

      setTestResults(mapExecutionResults(response));
      const passed = response.passed_tests;
      const total = response.total_tests;

      if (response.all_passed) {
        // Update local progress
        setLocalProgress((prev) => {
          const existing = prev.solved[activeProblem.id];
          const today = new Date().toISOString().split("T")[0];
          let newStreak = prev.streak;
          if (prev.lastSolvedDate !== today) {
            if (prev.lastSolvedDate) {
              const last = new Date(prev.lastSolvedDate);
              const now = new Date(today);
              const diff = (now.getTime() - last.getTime()) / (1000 * 60 * 60 * 24);
              newStreak = diff <= 1 ? prev.streak + 1 : 1;
            } else {
              newStreak = 1;
            }
          }
          return {
            solved: {
              ...prev.solved,
              [activeProblem.id]: {
                code,
                language: selectedLanguage,
                timestamp: new Date().toISOString(),
                attempts: (existing?.attempts || 0) + 1,
              },
            },
            streak: newStreak,
            lastSolvedDate: today,
          };
        });

        // Submit to backend
        if (isAuthenticated) {
          try {
            await submitCodingSolution(activeProblem.id, {
              code,
              language: selectedLanguage,
              passed_tests: passed,
              total_tests: total,
              solved: true,
            });
            const { progress, streak: s } = await fetchCodingProgress();
            const map: Record<number, CodingProgressEntry> = {};
            for (const p of progress) map[p.problem_id] = p;
            setServerProgress(map);
            setServerStreak(s.current_streak);
          } catch {}
        }

        toast.success(`All ${total} test cases passed in ${selectedLanguage}.`);
      } else {
        toast.error(`${passed}/${total} test cases passed`);
      }
    } catch (error: any) {
      toast.error(error?.message || "Submission failed. Please try again.");
    } finally {
      setIsRunning(false);
    }
  }, [activeProblem, code, executeAgainstBackend, isAuthenticated, selectedLanguage]);

  // AI Review
  const handleAiReview = useCallback(async () => {
    if (!activeProblem || !isAuthenticated) {
      toast.error("Sign in to use AI code review");
      return;
    }
    setIsReviewing(true);
    try {
      const result = await reviewCodingSolution(activeProblem.id, code, selectedLanguage);
      setAiReview(result.review);
    } catch {
      toast.error("AI review failed. Try again.");
    }
    setIsReviewing(false);
  }, [activeProblem, code, isAuthenticated, selectedLanguage]);

  // AI Rubber Duck: record the candidate's spoken approach, transcribe it,
  // then ask one Socratic follow-up question without revealing the solution.
  const handleDuckToggle = useCallback(async () => {
    if (!activeProblem) return;

    if (duckRecorder.isRecording) {
      const blob = await duckRecorder.stop();
      if (!blob || blob.size === 0) {
        toast.error("No audio captured");
        return;
      }
      setIsDuckThinking(true);
      try {
        const transcription = await transcribeAudio(blob, "audio/webm");
        const transcript = String(transcription?.transcript || transcription?.text || "").trim();
        if (!transcript) {
          toast.error("Couldn't hear that — try again");
          return;
        }
        setDuckMessages((prev) => [...prev, { role: "user", text: transcript }]);
        const duckResponse = await rubberDuck(activeProblem.id, transcript, code, selectedLanguage);
        setDuckMessages((prev) => [...prev, { role: "duck", text: duckResponse.question }]);
      } catch {
        toast.error("Rubber duck couldn't process that. Try again.");
      } finally {
        setIsDuckThinking(false);
      }
      return;
    }

    const started = await duckRecorder.start();
    if (!started) {
      toast.error(duckRecorder.error || "Microphone access denied");
    }
  }, [activeProblem, code, selectedLanguage, duckRecorder]);

  const handleLanguageChange = useCallback((nextLanguage: string) => {
    if (!activeProblem || nextLanguage === selectedLanguage) return;

    const currentCache = {
      ...codeByLanguage,
      [selectedLanguage]: code,
    };
    const nextCode = currentCache[nextLanguage] || getStarterForLanguage(activeProblem, nextLanguage);

    setCodeByLanguage({
      ...currentCache,
      [nextLanguage]: nextCode,
    });
    setSelectedLanguage(nextLanguage);
    setCode(nextCode);
    setTestResults([]);
    setAiReview(null);
  }, [activeProblem, code, codeByLanguage, selectedLanguage]);

  // Reset handler
  const handleReset = useCallback(async () => {
    setLocalProgress({ solved: {}, streak: 0, lastSolvedDate: null });
    if (isAuthenticated) {
      try {
        await resetCodingProgress();
        setServerProgress({});
        setServerStreak(0);
      } catch {}
    }
    toast.success("Progress reset");
  }, [isAuthenticated]);

  /* ─── Render: Problem List View ──────────────────── */
  if (view === "list") {
    return (
      <div className="max-w-5xl mx-auto py-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3">
            Coding <span className="text-primary">Practice</span>
          </h1>
          <p className="text-muted-foreground text-base max-w-lg mx-auto leading-relaxed">
            Master DSA patterns with {totalProblems} curated NeetCode-style problems.
          </p>
        </motion.div>

        {/* Stats Row */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6"
        >
          {[
            { icon: <Target className="w-4 h-4" />, value: `${totalSolved}/${totalProblems}`, label: "Solved" },
            { icon: <Flame className="w-4 h-4" />, value: streak, label: "Day Streak", color: "text-warning" },
            { icon: <Check className="w-4 h-4" />, value: `${easySolved}/${easyCount}`, label: "Easy", color: "text-emerald-500" },
            { icon: <BarChart3 className="w-4 h-4" />, value: `${mediumSolved}/${mediumCount}`, label: "Medium", color: "text-amber-500" },
            { icon: <Trophy className="w-4 h-4" />, value: `${hardSolved}/${hardCount}`, label: "Hard", color: "text-red-500" },
          ].map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3.5 rounded-xl bg-card border border-border shadow-sm"
            >
              <div className="w-9 h-9 rounded-lg bg-accent/50 border border-border flex items-center justify-center text-foreground">
                {s.icon}
              </div>
              <div>
                <span className={`text-base font-bold block ${s.color || ""}`}>{s.value}</span>
                <span className="text-xs text-muted-foreground">{s.label}</span>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Progress Bar */}
        <div className="mb-6 px-1">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-muted-foreground">Overall Progress</span>
            <span className="text-xs font-bold font-mono text-foreground">
              {Math.round((totalSolved / totalProblems) * 100)}%
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(totalSolved / totalProblems) * 100}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="h-full rounded-full"
              style={{ background: "var(--gradient-accent)" }}
            />
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Filter Sidebar */}
          <div className="lg:w-56 shrink-0">
            <button
              className="lg:hidden flex items-center gap-2 text-sm font-semibold mb-3 text-foreground"
              onClick={() => setFilterOpen(!filterOpen)}
            >
              <Filter className="w-4 h-4" /> Filters {filterOpen ? "▲" : "▼"}
            </button>

            <div className={`space-y-4 ${filterOpen ? "" : "hidden lg:block"}`}>
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search problems..."
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-card text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Topic */}
              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2 font-semibold">
                  Topic
                </p>
                <div className="space-y-1 max-h-[300px] overflow-y-auto pr-1">
                  <button
                    onClick={() => setTopicFilter("All")}
                    className={`block w-full text-left rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      topicFilter === "All"
                        ? "bg-primary/10 text-primary border border-primary/20"
                        : "text-muted-foreground hover:bg-accent/30 border border-transparent"
                    }`}
                  >
                    All Topics ({totalProblems})
                  </button>
                  {CODING_TOPICS.map((t) => {
                    const count = problems.filter((p) => p.topic === t).length;
                    if (count === 0) return null;
                    const solved = problems.filter((p) => p.topic === t && solvedSet.has(p.id)).length;
                    return (
                      <button
                        key={t}
                        onClick={() => setTopicFilter(t)}
                        className={`flex items-center justify-between w-full rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                          topicFilter === t
                            ? "bg-primary/10 text-primary border border-primary/20"
                            : "text-muted-foreground hover:bg-accent/30 border border-transparent"
                        }`}
                      >
                        <span className="truncate">{t}</span>
                        <span className="font-mono text-[10px] opacity-60 ml-1">
                          {solved}/{count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Difficulty */}
              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2 font-semibold">
                  Difficulty
                </p>
                {(["All", "Easy", "Medium", "Hard"] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setDifficultyFilter(d)}
                    className={`block w-full text-left rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      difficultyFilter === d
                        ? "bg-primary/10 text-primary border border-primary/20"
                        : "text-muted-foreground hover:bg-accent/30 border border-transparent"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>

              {/* Status */}
              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2 font-semibold">
                  Status
                </p>
                {(["All", "Solved", "Unsolved"] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`block w-full text-left rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      statusFilter === s
                        ? "bg-primary/10 text-primary border border-primary/20"
                        : "text-muted-foreground hover:bg-accent/30 border border-transparent"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>

              {/* Reset */}
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start text-xs text-destructive hover:bg-destructive/10"
                onClick={handleReset}
              >
                <RotateCcw className="w-3.5 h-3.5 mr-2" />
                Reset Progress
              </Button>
            </div>
          </div>

          {/* Problem List */}
          <div className="flex-1 min-w-0">
            <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
              {/* Table Header */}
              <div className="grid grid-cols-[40px_1fr_90px_120px_60px] gap-2 px-4 py-2.5 bg-muted/50 border-b border-border text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                <span>#</span>
                <span>Title</span>
                <span>Difficulty</span>
                <span className="hidden md:block">Topic</span>
                <span className="text-center">Status</span>
              </div>

              {/* Problem rows */}
              {paginatedProblems.length === 0 ? (
                <div className="text-center py-12">
                  <Code2 className="w-10 h-10 mx-auto mb-3 text-muted-foreground opacity-40" />
                  <p className="text-sm text-muted-foreground">No problems match your filters</p>
                </div>
              ) : (
                paginatedProblems.map((problem) => {
                  const dc = DIFFICULTY_COLORS[problem.difficulty] || DIFFICULTY_COLORS.Easy;
                  const solved = solvedSet.has(problem.id);
                  return (
                    <button
                      key={problem.id}
                      onClick={() => openProblem(problem.id)}
                      className="grid grid-cols-[40px_1fr_90px_120px_60px] gap-2 px-4 py-3 w-full text-left border-b border-border/50 last:border-0 hover:bg-accent/20 transition-colors cursor-pointer group"
                    >
                      <span className="text-xs font-mono text-muted-foreground">{problem.id}</span>
                      <span className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                        {problem.title}
                      </span>
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded-lg w-fit ${dc.bg} ${dc.text} ${dc.border} border`}
                      >
                        {problem.difficulty}
                      </span>
                      <span className="text-xs text-muted-foreground truncate hidden md:block">
                        {problem.topic}
                      </span>
                      <span className="flex justify-center">
                        {solved ? (
                          <Check className="w-4 h-4 text-emerald-500" />
                        ) : (
                          <span className="w-4 h-4 rounded-full border border-border" />
                        )}
                      </span>
                    </button>
                  );
                })
              )}
              
              {/* Pagination Controls */}
              {filteredProblems.length > 0 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-4 py-3 bg-card border-t border-border mt-auto">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Rows per page:</span>
                    <select
                      value={itemsPerPage}
                      onChange={(e) => {
                        setItemsPerPage(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="rounded border border-border bg-background px-2 py-1 text-xs text-foreground focus:outline-none font-medium cursor-pointer"
                    >
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                      <option value={75}>75</option>
                      <option value={100}>100</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs font-medium">
                    <span className="text-muted-foreground tracking-wide">
                      {(currentPage - 1) * itemsPerPage + 1}-
                      {Math.min(currentPage * itemsPerPage, filteredProblems.length)} of {filteredProblems.length}
                    </span>
                    
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-accent/50 hover:text-foreground"
                        onClick={() => setCurrentPage(1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronsLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-accent/50 hover:text-foreground"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <div className="flex items-center gap-1.5 px-2">
                        <span className="text-muted-foreground uppercase tracking-wider text-[10px]">Page</span>
                        <input
                          type="number"
                          min={1}
                          max={totalPages}
                          value={currentPage}
                          onChange={(e) => {
                            let val = parseInt(e.target.value);
                            if (!isNaN(val)) {
                              val = Math.max(1, Math.min(totalPages, val));
                              setCurrentPage(val);
                            }
                          }}
                          className="w-10 rounded border border-border bg-background px-1 py-1 text-center text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                        />
                        <span className="text-muted-foreground uppercase tracking-wider text-[10px]">of {totalPages}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-accent/50 hover:text-foreground"
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 hover:bg-accent/50 hover:text-foreground"
                        onClick={() => setCurrentPage(totalPages)}
                        disabled={currentPage === totalPages}
                      >
                        <ChevronsRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Topic Mastery Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mt-10 bg-card border border-border rounded-2xl p-5 shadow-sm"
        >
          <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-foreground">
            <BarChart3 className="w-4 h-4 text-primary" /> Topic Mastery
          </h3>
          <div className="space-y-3">
            {CODING_TOPICS.map((t) => {
              const total = problems.filter((p) => p.topic === t).length;
              if (total === 0) return null;
              const solved = problems.filter((p) => p.topic === t && solvedSet.has(p.id)).length;
              const pct = Math.round((solved / total) * 100);
              return (
                <div key={t}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-muted-foreground">{t}</span>
                    <span className="text-xs font-bold font-mono text-foreground">
                      {solved}/{total}
                    </span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                      className="h-full rounded-full bg-primary"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    );
  }

  /* ─── Render: Problem Solve View ─────────────────── */
  if (!activeProblem) return null;

  const dc = DIFFICULTY_COLORS[activeProblem.difficulty] || DIFFICULTY_COLORS.Easy;
  const passedCount = testResults.filter((r) => r.passed).length;

  return (
    <div className="max-w-7xl mx-auto py-4">
      {/* Top Bar */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-4 gap-3 flex-wrap"
      >
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setView("list")}
            className="gap-1.5"
          >
            <ChevronLeft className="w-4 h-4" /> Back
          </Button>
          <div>
            <h2 className="text-lg font-bold text-foreground">
              {activeProblem.id}. {activeProblem.title}
            </h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={`text-[11px] font-bold px-2 py-0.5 rounded-lg ${dc.bg} ${dc.text} ${dc.border} border`}
              >
                {activeProblem.difficulty}
              </span>
              <span className="text-xs text-muted-foreground">{activeProblem.topic}</span>
              {solvedSet.has(activeProblem.id) && (
                <span className="text-[11px] font-bold text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-lg">
                  ✓ Solved
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono">
            {activeProblem.timeComplexity} / {activeProblem.spaceComplexity}
          </span>
        </div>
      </motion.div>

      {/* Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Problem Description */}
        <motion.div
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col"
          style={{ maxHeight: "calc(100vh - 180px)" }}
        >
          <div className="px-4 py-3 border-b border-border bg-muted/30 flex items-center gap-2">
            <Code2 className="w-4 h-4 text-primary" />
            <span className="text-sm font-bold text-foreground">Problem Description</span>
          </div>
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {/* Description */}
            <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap prose prose-sm max-w-none dark:prose-invert">
              {activeProblem.description.split("```").map((block, i) =>
                i % 2 === 0 ? (
                  <span key={i}>{block}</span>
                ) : (
                  <pre
                    key={i}
                    className="bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs font-mono overflow-x-auto my-2 text-foreground"
                  >
                    {block.replace(/^\n/, "")}
                  </pre>
                )
              )}
            </div>

            {/* Constraints */}
            <div className="rounded-lg border border-border bg-muted/30 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Constraints
              </p>
              <pre className="text-xs font-mono text-foreground whitespace-pre-wrap">
                {activeProblem.constraints}
              </pre>
            </div>

            {/* Company Tags */}
            {activeProblem.companiesAsked.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1">
                  <Building2 className="w-3 h-3" /> Asked at
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {activeProblem.companiesAsked.map((c) => (
                    <span
                      key={c}
                      className="px-2 py-0.5 text-[11px] font-medium rounded-md bg-accent/50 border border-border text-muted-foreground"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Hints */}
            <div>
              <button
                onClick={() => {
                  const next = !showHints;
                  setShowHints(next);
                  if (next && revealedHints === 0) setRevealedHints(1);
                }}
                className="flex items-center gap-2 text-xs font-semibold text-amber-500 hover:text-amber-400 transition-colors cursor-pointer"
              >
                <Lightbulb className="w-3.5 h-3.5" />
                {showHints ? "Hide Hints" : `Show Hints (${activeProblem.hints.length})`}
                {showHints ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              <AnimatePresence>
                {showHints && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-2 space-y-1.5">
                      {activeProblem.hints.slice(0, revealedHints).map((h, i) => (
                        <div
                          key={i}
                          className="text-xs text-muted-foreground bg-amber-500/5 border border-amber-500/10 rounded-lg px-3 py-2"
                        >
                          💡 {h}
                        </div>
                      ))}
                    </div>
                    {revealedHints < activeProblem.hints.length && (
                      <button
                        onClick={() => setRevealedHints((n) => n + 1)}
                        className="mt-1.5 text-[11px] font-medium text-amber-500 hover:text-amber-400 transition-colors cursor-pointer"
                      >
                        Reveal next hint ({revealedHints}/{activeProblem.hints.length})
                      </button>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Solution */}
            <div>
              <button
                onClick={() => setShowSolution(!showSolution)}
                className="flex items-center gap-2 text-xs font-semibold text-primary hover:text-primary/80 transition-colors cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5" />
                {showSolution
                  ? `Hide ${LANGUAGE_LABELS[selectedLanguage] || selectedLanguage} Solution`
                  : `Show ${LANGUAGE_LABELS[selectedLanguage] || selectedLanguage} Solution`}
                {showSolution ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              <AnimatePresence>
                {showSolution && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <pre className="mt-2 bg-muted/50 border border-border rounded-lg px-3 py-3 text-xs font-mono overflow-x-auto text-foreground whitespace-pre-wrap">
                      {getSolutionForLanguage(activeProblem, selectedLanguage)}
                    </pre>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* AI Rubber Duck */}
            <div className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="flex items-center gap-2 text-xs font-semibold text-foreground">
                  <MessageCircle className="w-3.5 h-3.5" />
                  AI Rubber Duck
                </span>
                <Button
                  variant={duckRecorder.isRecording ? "destructive" : "outline"}
                  size="sm"
                  className="text-xs gap-1 h-7"
                  onClick={handleDuckToggle}
                  disabled={isDuckThinking}
                >
                  {duckRecorder.isRecording ? (
                    <>
                      <Square className="w-3 h-3" /> Stop ({duckRecorder.elapsedSeconds}s)
                    </>
                  ) : (
                    <>
                      <Mic className="w-3 h-3" /> Explain your approach
                    </>
                  )}
                </Button>
              </div>

              {duckRecorder.isRecording && (
                <div className="mb-2 h-1.5 w-full rounded-full bg-border overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 transition-[width] duration-100"
                    style={{ width: `${Math.round(duckRecorder.volumeLevel * 100)}%` }}
                  />
                </div>
              )}

              {isDuckThinking && (
                <p className="text-[11px] text-muted-foreground italic">Thinking of a follow-up question…</p>
              )}

              {duckMessages.length === 0 && !isDuckThinking ? (
                <p className="text-[11px] text-muted-foreground">
                  Talk through your approach out loud — the duck will ask a follow-up question
                  without giving away the answer.
                </p>
              ) : (
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {duckMessages.map((m, i) => (
                    <div
                      key={i}
                      className={`text-[11px] rounded-lg px-2.5 py-1.5 ${
                        m.role === "duck"
                          ? "bg-primary/10 text-foreground"
                          : "bg-accent/40 text-muted-foreground ml-4"
                      }`}
                    >
                      <span className="font-semibold mr-1">{m.role === "duck" ? "🦆" : "You:"}</span>
                      {m.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Right: Code Editor + Test Results */}
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col"
          style={{ maxHeight: "calc(100vh - 180px)" }}
        >
          {/* Editor Header */}
          <div className="px-4 py-3 border-b border-border bg-muted/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <select
                value={selectedLanguage}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="rounded-md border border-border bg-card px-2 py-1 text-sm font-semibold text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
              >
                {languageOptions
                  .filter((option) => option.enabled)
                  .map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
              </select>
              <span className="text-xs text-muted-foreground uppercase tracking-[0.18em]">
                {executionProvider}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs gap-1"
                onClick={() => {
                  const starter = getStarterForLanguage(activeProblem, selectedLanguage);
                  setCode(starter);
                  setCodeByLanguage((prev) => ({ ...prev, [selectedLanguage]: starter }));
                }}
              >
                <RotateCcw className="w-3 h-3" /> Reset
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-xs gap-1 border-border text-foreground hover:bg-accent"
                onClick={handleRunTests}
                disabled={isRunning}
              >
                <Play className="w-3 h-3" /> Run
              </Button>
              <Button
                size="sm"
                className="text-xs gap-1 bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSubmit}
                disabled={isRunning}
              >
                <Send className="w-3 h-3" /> Submit
              </Button>
            </div>
          </div>

          {/* Code Editor */}
          <div className="flex-1 relative min-h-[280px]">
            <div className="border-b border-border bg-background/60 px-4 py-2 text-[11px] text-muted-foreground">
              {(activeProblem as CodingProblemDetail).executionContract ||
                "Implement solve(...) and print or return JSON-compatible output for the hidden tests."}
            </div>
            <Editor
              height="280px"
              language={MONACO_LANGUAGE_MAP[selectedLanguage] || "plaintext"}
              value={code}
              theme={isDarkMode ? "custom-dark" : "custom-light"}
              onChange={(value) => {
                const nextCode = value ?? "";
                setCode(nextCode);
                setCodeByLanguage((prev) => ({ ...prev, [selectedLanguage]: nextCode }));
              }}
              onMount={(editor, monaco) => {
                editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
                  handleRunTests();
                });
              }}
              options={{
                fontFamily:
                  'ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace',
                fontSize: 13,
                minimap: { enabled: false },
                tabSize: 2,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                wordWrap: "on",
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>

          {/* Test Results & AI Review */}
          <div className="border-t border-border max-h-[320px] overflow-y-auto">
            {/* Action buttons row */}
            <div className="px-4 py-2 border-b border-border bg-muted/20 flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground flex-1">
                {testResults.length > 0
                  ? `${passedCount}/${testResults.length} Test Cases Passed`
                  : "Test Results"}
              </span>
              {isAuthenticated && (
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs gap-1 h-7"
                  onClick={handleAiReview}
                  disabled={isReviewing}
                >
                  <Sparkles className="w-3 h-3" />
                  {isReviewing ? "Reviewing..." : "AI Review"}
                </Button>
              )}
            </div>

            {/* Console output */}
            {testResults.length > 0 && (
              <div className="px-4 py-2 border-b border-border bg-black/90">
                <div className="text-[10px] uppercase tracking-[0.14em] text-neutral-500 mb-1">Console</div>
                <pre className="text-[11px] font-mono text-neutral-200 whitespace-pre-wrap max-h-32 overflow-y-auto">
                  {testResults
                    .map((tr, i) =>
                      tr.error
                        ? `[Case ${i + 1}] ${tr.error}`
                        : `[Case ${i + 1}] ${tr.actual}`,
                    )
                    .join("\n") || "No output."}
                </pre>
              </div>
            )}

            {/* Test case results */}
            {testResults.length > 0 && (
              <div className="divide-y divide-border">
                {testResults.map((tr, i) => (
                  <div key={i} className="px-4 py-2.5 flex items-start gap-3">
                    <div className="mt-0.5">
                      {tr.passed ? (
                        <Check className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <X className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2 text-[11px]">
                        <span className="font-semibold text-muted-foreground">Case {i + 1}</span>
                        {tr.time !== undefined && (
                          <span className="text-muted-foreground font-mono flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {tr.time.toFixed(1)}ms
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block">Input</span>
                          <code className="text-foreground font-mono text-[11px] break-all">
                            {tr.input.length > 60 ? tr.input.slice(0, 60) + "..." : tr.input}
                          </code>
                        </div>
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block">Expected</span>
                          <code className="text-foreground font-mono text-[11px] break-all">{tr.expected}</code>
                        </div>
                        <div>
                          <span className="text-[10px] text-muted-foreground uppercase block">Actual</span>
                          <code
                            className={`font-mono text-[11px] break-all ${
                              tr.passed ? "text-emerald-500" : "text-red-500"
                            }`}
                          >
                            {tr.error || tr.actual}
                          </code>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* AI Review */}
            {aiReview && (
              <div className="px-4 py-4 border-t border-border bg-primary/5">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <span className="text-sm font-bold text-foreground">AI Code Review</span>
                </div>
                <div className="space-y-3 text-xs">
                  {aiReview.correctness && (
                    <div className="flex items-start gap-2">
                      <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                        aiReview.correctness === "correct"
                          ? "bg-emerald-500/10 text-emerald-500"
                          : aiReview.correctness === "partially_correct"
                          ? "bg-amber-500/10 text-amber-500"
                          : "bg-red-500/10 text-red-500"
                      }`}>
                        {aiReview.correctness?.replace("_", " ")}
                      </span>
                      {aiReview.correctness_notes && (
                        <span className="text-muted-foreground">{aiReview.correctness_notes}</span>
                      )}
                    </div>
                  )}
                  {aiReview.time_complexity && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <span className="font-semibold text-foreground">Time:</span>
                      <span className="font-mono">{aiReview.time_complexity}</span>
                      {aiReview.time_complexity_optimal !== undefined && (
                        <span className={aiReview.time_complexity_optimal ? "text-emerald-500" : "text-amber-500"}>
                          {aiReview.time_complexity_optimal ? "✓ Optimal" : "⚠ Not optimal"}
                        </span>
                      )}
                    </div>
                  )}
                  {aiReview.space_complexity && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <span className="font-semibold text-foreground">Space:</span>
                      <span className="font-mono">{aiReview.space_complexity}</span>
                      {aiReview.space_complexity_optimal !== undefined && (
                        <span className={aiReview.space_complexity_optimal ? "text-emerald-500" : "text-amber-500"}>
                          {aiReview.space_complexity_optimal ? "✓ Optimal" : "⚠ Can improve"}
                        </span>
                      )}
                    </div>
                  )}
                  {aiReview.suggestions && aiReview.suggestions.length > 0 && (
                    <div>
                      <p className="font-semibold text-foreground mb-1">Suggestions:</p>
                      <ul className="space-y-1">
                        {aiReview.suggestions.map((s, i) => (
                          <li key={i} className="text-muted-foreground pl-3 relative before:content-['→'] before:absolute before:left-0 before:text-primary">
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {aiReview.overall_feedback && (
                    <div className="bg-card rounded-lg p-3 border border-border text-muted-foreground">
                      {aiReview.overall_feedback}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Empty state */}
            {testResults.length === 0 && !aiReview && (
              <div className="px-4 py-8 text-center">
                <Play className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-30" />
                <p className="text-xs text-muted-foreground">
                  Click "Run" to execute hidden tests on the backend or "Submit" to save a passing solution.
                </p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
