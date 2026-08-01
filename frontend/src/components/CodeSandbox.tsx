/**
 * CodeSandbox — Professional Full-Screen Resizable IDE with VS Code Syntax Highlighting & Autocompletion.
 *
 * Supported Languages (15):
 * Python 3, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift, Objective-C, Erlang, Haskell, SQL
 */

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Terminal,
  Code2,
  ArrowLeft,
  Upload,
  AlertTriangle,
  GripVertical,
  GripHorizontal,
  History,
  ListChecks,
  Search,
  Clock,
  Check,
} from "lucide-react";
import {
  fetchCodingProblems,
  fetchCodingProblem,
  fetchCodingCatalog,
  fetchCodingSubmissions,
  runCodingSolution,
  submitCodingSolution,
  type CodingProblem,
  type CodingProblemSummary,
  type CodingSubmissionDto,
  type RunCodeResponseDto,
  type SubmitCodeResponseDto,
} from "@/lib/api";
import { getInterviewSessionId } from "@/lib/interviewSession";
import { loadSelectedProblemIds } from "@/hooks/useSessionStorage";
import Loading from "@/components/Loading";
import ScreenRecordGuard from "@/components/ScreenRecordGuard";
import InlineMarkdown from "@/components/InlineMarkdown";
import ProblemDiagram from "@/components/ProblemDiagram";

import CodeMirror from "@uiw/react-codemirror";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";
import { EditorView } from "@codemirror/view";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { java } from "@codemirror/lang-java";
import { cpp } from "@codemirror/lang-cpp";
import { go } from "@codemirror/lang-go";
import { rust } from "@codemirror/lang-rust";
import { sql } from "@codemirror/lang-sql";
import { autocompletion } from "@codemirror/autocomplete";

type SupportedLang =
  | "python"
  | "javascript"
  | "typescript"
  | "java"
  | "cpp"
  | "csharp"
  | "go"
  | "rust"
  | "ruby"
  | "php"
  | "swift"
  | "objectivec"
  | "erlang"
  | "haskell"
  | "sql";

/** Difficulty pill colors. Previously hardcoded emerald, so Hard read green. */
function difficultyPillClass(difficulty: string): string {
  switch ((difficulty || "").toLowerCase()) {
    case "easy":
      return "border-emerald-500/40 bg-emerald-950/60 text-emerald-400";
    case "medium":
      return "border-amber-500/40 bg-amber-950/60 text-amber-400";
    case "hard":
      return "border-rose-500/40 bg-rose-950/60 text-rose-400";
    default:
      return "border-gray-700 bg-[#222222] text-gray-300";
  }
}

/** Sample inputs/outputs arrive as JSON strings, objects, or bare scalars. */
function formatSampleValue(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

const defaultStarterCodes: Record<SupportedLang, string> = {
  python: "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Write solution here\n    pass\n",
  javascript: "function twoSum(nums, target) {\n    // Write solution here\n}\n",
  typescript: "function twoSum(nums: number[], target: number): number[] {\n    // Write solution here\n    return [];\n}\n",
  java: "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
  cpp: "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {};\n    }\n};\n",
  csharp: "public class Solution {\n    public int[] TwoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
  go: "package main\n\nfunc twoSum(nums []int, target int) []int {\n    return []int{}\n}\n",
  rust: "pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {\n    vec![]\n}\n",
  ruby: "def two_sum(nums, target)\n    # Write solution here\nend\n",
  php: "<?php\nfunction twoSum($nums, $target) {\n    // Write solution here\n}\n",
  swift: "func twoSum(_ nums: [Int], _ target: Int) -> [Int] {\n    return []\n}\n",
  objectivec: "#import <Foundation/Foundation.h>\nNSArray* twoSum(NSArray* nums, NSInteger target) {\n    return @[];\n}\n",
  erlang: "-module(solution).\n-export([two_sum/2]).\ntwo_sum(_Nums, _Target) -> [].\n",
  haskell: "twoSum :: [Int] -> Int -> [Int]\ntwoSum nums target = []\n",
  sql: "-- Write your SQL query below\nSELECT\n    -- your columns here\nFROM\n    table_name;\n",
};

/** The candidate types code, but the page asks for one typeface throughout. */
const SANS_STACK =
  'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

// CodeMirror sets `font-family: monospace` on several nodes independently, so
// overriding `&` alone leaves the gutter, tooltips and panels monospaced. Every
// surface the editor can draw is listed here rather than relying on inheritance.
const sansEditorTheme = EditorView.theme({
  "&": { fontFamily: SANS_STACK },
  ".cm-scroller": { fontFamily: SANS_STACK },
  ".cm-content": { fontFamily: SANS_STACK },
  ".cm-line": { fontFamily: SANS_STACK },
  ".cm-gutters": { fontFamily: SANS_STACK },
  ".cm-lineNumbers": { fontFamily: SANS_STACK },
  ".cm-lineNumbers .cm-gutterElement": { fontFamily: SANS_STACK },
  ".cm-foldGutter": { fontFamily: SANS_STACK },
  ".cm-panels": { fontFamily: SANS_STACK },
  ".cm-panel": { fontFamily: SANS_STACK },
  ".cm-tooltip": { fontFamily: SANS_STACK },
  ".cm-tooltip-autocomplete": { fontFamily: SANS_STACK },
  ".cm-tooltip-autocomplete > ul > li": { fontFamily: SANS_STACK },
  ".cm-completionLabel": { fontFamily: SANS_STACK },
  ".cm-completionDetail": { fontFamily: SANS_STACK },
  ".cm-completionInfo": { fontFamily: SANS_STACK },
  ".cm-diagnostic": { fontFamily: SANS_STACK },
  ".cm-searchMatch": { fontFamily: SANS_STACK },
  ".cm-placeholder": { fontFamily: SANS_STACK },
});

export default function CodeSandbox() {
  const navigate = useNavigate();
  const location = useLocation();
  // React Router stamps the first entry of a session with key "default". If
  // that is where we are, there is no history to pop and going "back" would
  // leave the app, so send the candidate to the workspace instead.
  const canGoBack = location.key !== "default";
  const sessionId = useMemo(() => getInterviewSessionId(), []);
  // A coding question generated from the résumé names the bank problem it was
  // built from; the interview links here as /coding?problem=<id> so the
  // candidate lands on that problem rather than whatever the bank lists first.
  const requestedProblemId = useMemo(
    () => new URLSearchParams(location.search).get("problem") ?? "",
    [location.search],
  );
  // The same sandbox serves two flows. The interview links here as
  // /coding?mode=interview&problem=<id>, which turns on the question-number
  // rail; anything else (the "Code Editor" nav entry, a bookmark) is LeetCode
  // style practice, where a rail counting interview questions is meaningless.
  const requestedMode = useMemo(
    () => new URLSearchParams(location.search).get("mode") ?? "",
    [location.search],
  );

  const [problems, setProblems] = useState<CodingProblem[]>([]);
  /** Bank ids the generator picked for this sitting, in ask order — the rail. */
  const [interviewProblemIds, setInterviewProblemIds] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string>(requestedProblemId || "two-sum");
  const [showProblemList, setShowProblemList] = useState<boolean>(false);
  const [problemQuery, setProblemQuery] = useState<string>("");
  const [difficultyFilter, setDifficultyFilter] = useState<"All" | "Easy" | "Medium" | "Hard">("All");
  const [topicFilter, setTopicFilter] = useState<string>("All");
  // The catalogue is ~1000 problems, so it is searched and paged on the server
  // rather than shipped whole and filtered here.
  const [catalog, setCatalog] = useState<CodingProblemSummary[]>([]);
  const [catalogTotal, setCatalogTotal] = useState<number>(0);
  const [catalogTopics, setCatalogTopics] = useState<string[]>([]);
  const [catalogPage, setCatalogPage] = useState<number>(0);
  const [catalogLoading, setCatalogLoading] = useState<boolean>(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [clock, setClock] = useState<Date>(() => new Date());
  const [language, setLanguage] = useState<SupportedLang>("python");
  const [code, setCode] = useState<string>("");
  const [customInput, setCustomInput] = useState<string>("");
  const [useCustomInput, setUseCustomInput] = useState<boolean>(false);
  const [activeTestCaseTab, setActiveTestCaseTab] = useState<number>(0);

  // Resizable Panes State
  const [leftWidthPercent, setLeftWidthPercent] = useState<number>(45);
  const [testCasesHeightPx, setTestCasesHeightPx] = useState<number>(220);
  const isDraggingHorizontalRef = useRef<boolean>(false);
  const isDraggingVerticalRef = useRef<boolean>(false);
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const rightColumnRef = useRef<HTMLDivElement>(null);
  /** The interview question rail, when rendered — measured by the drag handler. */
  const railRef = useRef<HTMLElement>(null);
  /** Scrolled back to the top whenever the problem changes. */
  const problemPaneRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState<boolean>(false);
  // Picking a bank problem from the catalogue fetches its detail by id. The
  // full-screen `loading` branch would unmount ScreenRecordGuard — its
  // MediaRecorder is torn down, so the browser re-asks for screen share the
  // moment the sandbox remounts it. Picks use this inline flag instead so the
  // guard (and the running recording) survives the problem switch.
  const [pickingProblem, setPickingProblem] = useState<boolean>(false);
  const [running, setRunning] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<RunCodeResponseDto | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitCodeResponseDto | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showAiModal, setShowAiModal] = useState<boolean>(false);
  const [submissions, setSubmissions] = useState<CodingSubmissionDto[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);

  // Security & Proctoring State
  const [proctorWarning, setProctorWarning] = useState<string | null>(null);
  const [tabSwitchCount, setTabSwitchCount] = useState<number>(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load problem dataset
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const [curated, sessionProblemIds] = await Promise.all([
          fetchCodingProblems(),
          loadSelectedProblemIds().catch(() => [] as string[]),
        ]);
        // Preference order: an explicit ?problem= deep link, then whatever the
        // question generator picked for this candidate, then the bank listing.
        const wanted = [requestedProblemId, ...sessionProblemIds].filter(Boolean);        // /coding/problems lists only the curated set, but a generated coding
        // question names a problem from the 1000-entry bank. Those have to be
        // fetched by id, or the sandbox would quietly open a problem the
        // candidate was never asked. An id that 404s is dropped, not fatal.
        const missing = wanted.filter((id) => !curated.some((p) => p.id === id));
        const fetched = (
          await Promise.all(missing.map((id) => fetchCodingProblem(id).catch(() => null)))
        ).filter((p): p is CodingProblem => p !== null);
        if (cancelled) return;

        const merged = [...fetched, ...curated];
        setProblems(merged);
        // Kept, not discarded: the rail numbers the candidate's questions in the
        // order they were asked, and only ids that actually resolved to a
        // problem can be rendered as a step.
        setInterviewProblemIds(
          sessionProblemIds.filter((id) => merged.some((p) => p.id === id)),
        );
        const target =
          wanted.map((id) => merged.find((p) => p.id === id)).find(Boolean) ?? merged[0];
        if (target) {
          setSelectedId(target.id);
          // A database problem opens in SQL even when the editor defaulted to
          // Python, so the starter shown matches what the grader will run.
          if (target.sql_schema?.length) {
            setLanguage("sql");
            setCode(target.starter_code.sql || defaultStarterCodes.sql);
          } else {
            setCode(target.starter_code[language] || defaultStarterCodes[language]);
          }
        }
      } catch (err) {
        console.error("Failed to load coding problems:", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [requestedProblemId]);

  const activeProblem = problems.find((p) => p.id === selectedId) || problems[0];

  // Database problems are answered with a query, not a function call — the
  // grader only understands SQL, so the editor locks to it and the language
  // dropdown offers nothing else. Everything downstream (starter lookup, run,
  // submit, filename) uses the effective language so a stale `language` state
  // never sends a query through a function-call harness.
  const isDatabaseProblem = Boolean(activeProblem?.sql_schema?.length);
  const effectiveLang: SupportedLang = isDatabaseProblem ? "sql" : language;

  // Interview flow is what the URL says it is, but a sitting that never went
  // through the generator has nothing to number — an empty rail is worse than
  // no rail, so the ids have to be there too.
  const isInterviewFlow = requestedMode === "interview" && interviewProblemIds.length > 0;

  /** The rail: one step per generated coding question, in ask order. */
  const railSteps = useMemo(
    () =>
      interviewProblemIds.map((id, i) => {
        const problem = problems.find((p) => p.id === id);
        return {
          id,
          number: i + 1,
          title: problem?.title ?? id,
          // A question counts as solved once any submission for it was accepted.
          solved: submissions.some((s) => s.problem_id === id && s.passed),
          attempted: submissions.some((s) => s.problem_id === id),
        };
      }),
    [interviewProblemIds, problems, submissions],
  );
  const solvedCount = railSteps.filter((s) => s.solved).length;

  /** Wall clock in the editor header — candidates pace themselves by it. */
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const CATALOG_PAGE_SIZE = 100;

  /** Reset to the first page whenever the filters change under us. */
  useEffect(() => {
    setCatalogPage(0);
  }, [problemQuery, difficultyFilter, topicFilter]);

  /** Fetch the practice catalogue. Debounced so typing does not spam the API. */
  useEffect(() => {
    if (!showProblemList) return;
    let cancelled = false;
    setCatalogLoading(true);
    const handle = setTimeout(() => {
      fetchCodingCatalog({
        search: problemQuery.trim(),
        difficulty: difficultyFilter === "All" ? "" : difficultyFilter,
        topic: topicFilter === "All" ? "" : topicFilter,
        offset: catalogPage * CATALOG_PAGE_SIZE,
        limit: CATALOG_PAGE_SIZE,
      })
        .then((page) => {
          if (cancelled) return;
          setCatalog(page.problems);
          setCatalogTotal(page.total);
          // Topics are stable across pages; keep the first non-empty set.
          if (page.topics.length) setCatalogTopics(page.topics);
          setCatalogError(null);
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          setCatalog([]);
          setCatalogTotal(0);
          setCatalogError(err instanceof Error ? err.message : "Could not load problems");
        })
        .finally(() => {
          if (!cancelled) setCatalogLoading(false);
        });
    }, 220);
    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [showProblemList, problemQuery, difficultyFilter, topicFilter, catalogPage]);

  /**
   * Open a problem chosen from the catalogue. Most of the catalogue is not in
   * `problems` (that holds only the curated set plus this sitting's questions),
   * so an unknown id is fetched and merged before it is selected.
   */
  const handlePickProblem = useCallback(
    async (id: string) => {
      setShowProblemList(false);
      if (problems.some((p) => p.id === id)) {
        setSelectedId(id);
        return;
      }
      setPickingProblem(true);
      try {
        const detail = await fetchCodingProblem(id);
        setProblems((prev) => (prev.some((p) => p.id === id) ? prev : [detail, ...prev]));
        setSelectedId(id);
      } catch {
        setProctorWarning("That problem could not be loaded. Please pick another.");
      } finally {
        setPickingProblem(false);
      }
    },
    [problems],
  );

  // Update code on problem or language change. The effective language locks
  // to SQL while a database problem is open, and leaves it when the problem
  // changes back to a coding one — otherwise a stale `sql` selection would
  // load the generic SELECT template into a function problem's editor.
  useEffect(() => {
    if (!activeProblem) return;
    const isDb = Boolean(activeProblem.sql_schema?.length);
    if (isDb && language !== "sql") {
      setLanguage("sql");
      return;
    }
    if (!isDb && language === "sql") {
      setLanguage("python");
      return;
    }
    setCode(activeProblem.starter_code[language] || defaultStarterCodes[language]);
    setRunResult(null);
    setSubmitResult(null);
    setActiveTestCaseTab(0);
  }, [activeProblem, language]);

  // A new problem starts at the top of its statement, not wherever the reader
  // had scrolled the previous one.
  useEffect(() => {
    problemPaneRef.current?.scrollTo({ top: 0 });
  }, [activeProblem?.id]);

  // Drag & Resize Handlers
  const handleMouseDownHorizontal = (e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingHorizontalRef.current = true;
  };

  const handleMouseDownVertical = (e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingVerticalRef.current = true;
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDraggingHorizontalRef.current && mainContainerRef.current) {
        const rect = mainContainerRef.current.getBoundingClientRect();
        // The rail (when present) sits inside this container but ahead of the
        // description pane, so its width has to come off the cursor offset or
        // the divider drifts from the pointer by exactly the rail's width.
        const railWidth = railRef.current?.offsetWidth ?? 0;
        const offsetX = e.clientX - rect.left - railWidth;
        const usableWidth = rect.width - railWidth;
        const newPercent = Math.min(Math.max((offsetX / usableWidth) * 100, 20), 80);
        setLeftWidthPercent(newPercent);
      } else if (isDraggingVerticalRef.current && rightColumnRef.current) {
        const rect = rightColumnRef.current.getBoundingClientRect();
        const offsetY = rect.bottom - e.clientY;
        const newHeight = Math.min(Math.max(offsetY, 100), rect.height - 150);
        setTestCasesHeightPx(newHeight);
      }
    };

    const handleMouseUp = () => {
      isDraggingHorizontalRef.current = false;
      isDraggingVerticalRef.current = false;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  // Tab-switch / focus-loss detection.
  //
  // This deliberately does not touch the camera or microphone. It used to call
  // getUserMedia({video, audio}) on mount and start a MediaRecorder with no
  // ondataavailable handler and no upload target, so it captured the candidate
  // covertly and discarded every byte. Worse, the cleanup stopped only the
  // recorder — stopping a MediaRecorder does not release the hardware — so the
  // camera and mic stayed live after the candidate left the editor.
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitchCount((prev) => {
          const next = prev + 1;
          setProctorWarning(`Proctor Alert: Tab switch detected (${next} violation${next > 1 ? "s" : ""}). Activity logged.`);
          return next;
        });
      }
    };

    const handleWindowBlur = () => {
      setTabSwitchCount((prev) => {
        const next = prev + 1;
        setProctorWarning(`Proctor Alert: Focus lost from coding window (${next} violation${next > 1 ? "s" : ""}).`);
        return next;
      });
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleWindowBlur);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleWindowBlur);
    };
  }, []);

  // In-editor clipboard lockdown. The candidate must type their solution, so
  // copy, cut, paste and drag-drop are all refused inside the editor pane —
  // including the keyboard shortcuts, which never raise a clipboard event when
  // the browser has nothing selected to act on.
  const blockClipboard = useCallback(
    (action: "copy" | "cut" | "paste") => (e: React.ClipboardEvent | React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setProctorWarning(
        action === "paste"
          ? "Paste is disabled in the code editor. Please type your solution."
          : `${action === "copy" ? "Copying" : "Cutting"} code is disabled during the interview.`,
      );
    },
    [],
  );

  const handleEditorKeyDown = useCallback((e: React.KeyboardEvent) => {
    const mod = e.ctrlKey || e.metaKey;
    if (!mod) return;
    const key = e.key.toLowerCase();
    if (key === "c" || key === "v" || key === "x") {
      e.preventDefault();
      e.stopPropagation();
      setProctorWarning("Clipboard shortcuts are disabled in the code editor.");
    }
  }, []);

  const handleResetCode = () => {
    if (activeProblem) {
      setCode(
        (activeProblem.starter_code as any)[effectiveLang] ||
          defaultStarterCodes[effectiveLang],
      );
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        if (text) setCode(text);
      };
      reader.readAsText(file);
    }
  };

  const handleRunTests = useCallback(async () => {
    if (!activeProblem || running) return;
    setRunning(true);
    setRunResult(null);
    try {
      const res = await runCodingSolution(activeProblem.id, effectiveLang as any, code);
      setRunResult(res);
    } catch (err) {
      setRunResult({
        success: false,
        passed: false,
        runtime_ms: 0,
        test_results: [],
        stdout: "",
        stderr: err instanceof Error ? err.message : "Execution failed",
        error: "Execution error",
      });
    } finally {
      setRunning(false);
    }
  }, [activeProblem, language, code, running]);

  const refreshSubmissions = useCallback(async () => {
    try {
      setSubmissions(await fetchCodingSubmissions(sessionId));
    } catch {
      // History is a convenience; a store that is down must not break the page.
    }
  }, [sessionId]);

  useEffect(() => {
    void refreshSubmissions();
  }, [refreshSubmissions]);

  const handleSubmit = useCallback(async () => {
    if (!activeProblem || submitting) return;
    setSubmitting(true);
    setSubmitResult(null);
    setSubmitError(null);
    try {
      const res = await submitCodingSolution(activeProblem.id, effectiveLang as any, code, sessionId);
      setSubmitResult(res);
      setShowAiModal(true);
      void refreshSubmissions();
    } catch (err) {
      // Shown inline in the action bar rather than in an alert(), which the
      // candidate has to dismiss before they can see their own code again.
      setSubmitError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }, [activeProblem, language, code, submitting, sessionId, refreshSubmissions]);

  // CodeMirror Language Extension Provider
  const getLanguageExtension = useCallback(() => {
    const auto = autocompletion();
    switch (effectiveLang) {
      case "python":
        return [python(), auto];
      case "javascript":
      case "typescript":
        return [javascript({ typescript: language === "typescript" }), auto];
      case "java":
        return [java(), auto];
      case "cpp":
      case "csharp":
      case "objectivec":
        return [cpp(), auto];
      case "go":
        return [go(), auto];
      case "rust":
        return [rust(), auto];
      case "sql":
        return [sql(), auto];
      default:
        return [python(), auto];
    }
  }, [effectiveLang]);

  // CodeMirror binds clipboard handlers to its own content DOM and calls
  // preventDefault itself, so an outer React onCopy/onPaste never fires for
  // events that originate inside the editor. Refuse them at the source.
  const editorExtensions = useMemo(
    () => [
      ...getLanguageExtension(),
      sansEditorTheme,
      EditorView.domEventHandlers({
        copy: (event) => {
          event.preventDefault();
          setProctorWarning("Copying code is disabled during the interview.");
          return true;
        },
        cut: (event) => {
          event.preventDefault();
          setProctorWarning("Cutting code is disabled during the interview.");
          return true;
        },
        paste: (event) => {
          event.preventDefault();
          setProctorWarning("Paste is disabled in the code editor. Please type your solution.");
          return true;
        },
        drop: (event) => {
          event.preventDefault();
          setProctorWarning("Dropping text into the editor is disabled.");
          return true;
        },
        contextmenu: (event) => {
          event.preventDefault();
          return true;
        },
      }),
    ],
    [getLanguageExtension],
  );

  if (loading || !activeProblem) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#141414] text-gray-300 font-sans">
        {/* Brand mark, not a generic spinner — the sandbox is a full-screen
            route, so this is the app's own loading identity. Label is rendered
            here rather than passed to Loading because the sandbox forces its
            own dark palette instead of inheriting the theme tokens. */}
        <div className="flex flex-col items-center gap-4 font-sans">
          <Loading size="lg" className="text-brand" />
          <span className="font-medium text-sm text-gray-400 font-sans">
            Loading Coding Environment…
          </span>
        </div>
      </div>
    );
  }

  const testCasesList = activeProblem.examples || [];

  // Curated problems separate their constraints with newlines; bank problems
  // ship one line. Splitting on both gives a uniform bulleted list.
  const constraintsList = (activeProblem.constraints || "")
    .split("\n")
    .map((line) => line.replace(/^[-•*]\s*/, "").trim())
    .filter((line) => line.length > 0);

  const getExt = () => {
    switch (effectiveLang) {
      case "python": return "py";
      case "javascript": return "js";
      case "typescript": return "ts";
      case "java": return "java";
      case "cpp": return "cpp";
      case "csharp": return "cs";
      case "go": return "go";
      case "rust": return "rs";
      case "ruby": return "rb";
      case "php": return "php";
      case "swift": return "swift";
      case "objectivec": return "m";
      case "erlang": return "erl";
      case "haskell": return "hs";
      case "sql": return "sql";
      default: return "txt";
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#141414] text-gray-100 font-sans overflow-hidden">
      {/* Security Proctoring Alert Banner */}
      {proctorWarning && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-1.5 flex items-center justify-between text-amber-400 font-sans text-xs shrink-0">
          <div className="flex items-center gap-2 font-sans">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            <span className="font-sans font-medium">{proctorWarning}</span>
          </div>
          <button
            onClick={() => setProctorWarning(null)}
            className="text-amber-400/70 hover:text-amber-300 text-xs font-sans"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* HackerRank-Style Top Navigation Bar */}
      <header className="flex h-12 items-center justify-between border-b border-gray-800 bg-[#1E1E1E] px-4 text-xs font-sans shrink-0">
        {/* Left: Back & Problem Selector */}
        <div className="flex items-center gap-3 font-sans">
          <button
            onClick={() =>
              canGoBack
                ? navigate(-1)
                : navigate(isInterviewFlow ? "/app/interview" : "/app")
            }
            title={
              canGoBack
                ? "Back to previous page"
                : isInterviewFlow
                  ? "Back to interview"
                  : "Back to workspace"
            }
            className="flex h-7 w-7 items-center justify-center rounded-[4px] border border-gray-700 bg-[#252526] text-gray-300 hover:text-white hover:border-gray-600 transition-colors font-sans"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
          </button>

          <div className="flex items-center gap-2 font-bold text-emerald-400 font-sans">
            <Code2 className="h-4 w-4" />
            <span className="text-white font-sans">
              {isInterviewFlow ? "Interview · Coding Round" : "Practice · Code Editor"}
            </span>
          </div>

          <span className="text-gray-600 font-sans">/</span>

          {/* Only the current problem title — the old dropdown listed just the
              six curated problems, which read as if that were the whole
              catalogue. Browsing lives in the All Problems modal. */}
          <span className="font-semibold font-sans text-white">{activeProblem.title}</span>

          {!isInterviewFlow && (
            <button
              onClick={() => setShowProblemList(true)}
              title="Browse every problem"
              className="flex items-center gap-1.5 rounded-[4px] border border-gray-700 bg-[#252526] px-2.5 py-1 font-semibold font-sans text-gray-200 hover:border-gray-600 hover:text-white transition-colors"
            >
              <ListChecks className="h-3.5 w-3.5" />
              All Problems
            </button>
          )}
        </div>

        {/* Right: Languages Selector & Controls. Database problems restrict the
            picker to SQL (see `isDatabaseProblem` above); coding problems show
            the full set. */}
        <div className="flex items-center gap-4 font-sans">
          {/* Anti-cheat: the coding round is screen-recorded too, not just the
              interview tab. The guard raises its own full-viewport gate when the
              server marks recording as required, so all this slot holds is the
              live REC indicator. */}
          <ScreenRecordGuard sessionId={sessionId} surface="coding" />

          <div className="flex items-center gap-2 font-sans">
            <span className="text-gray-400 font-sans">Language</span>
            <select
              value={effectiveLang}
              onChange={(e) => setLanguage(e.target.value as SupportedLang)}
              className="rounded-[4px] border border-gray-700 bg-[#252526] px-2.5 py-1 text-xs font-semibold font-sans text-white focus:outline-none cursor-pointer"
            >
              {isDatabaseProblem ? (
                <option value="sql">SQL</option>
              ) : (
                <>
                  <option value="python">Python 3</option>
                  <option value="javascript">JavaScript</option>
                  <option value="typescript">TypeScript</option>
                  <option value="java">Java</option>
                  <option value="cpp">C++</option>
                  <option value="csharp">C#</option>
                  <option value="go">Go</option>
                  <option value="rust">Rust</option>
                  <option value="ruby">Ruby</option>
                  <option value="php">PHP</option>
                  <option value="swift">Swift</option>
                  <option value="objectivec">Objective-C</option>
                  <option value="erlang">Erlang</option>
                  <option value="haskell">Haskell</option>
                </>
              )}
            </select>
          </div>

          <button
            onClick={() => setShowHistory((open) => !open)}
            title={`Submissions in this interview (session ${sessionId})`}
            className={`flex items-center gap-1 font-sans transition-colors ${
              showHistory ? "text-white" : "text-gray-400 hover:text-white"
            }`}
          >
            <History className="h-3.5 w-3.5" />
            <span className="font-sans">Submissions ({submissions.length})</span>
          </button>

          <button
            onClick={handleResetCode}
            title="Reset code to starter template"
            className="flex items-center gap-1 text-gray-400 hover:text-white font-sans transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span className="font-sans">Reset</span>
          </button>
        </div>
      </header>

      {/* Main Full-Screen Resizable Split View */}
      <div ref={mainContainerRef} className="flex flex-1 overflow-hidden font-sans relative">
        {/* Inline pick feedback — deliberately not the full-screen loading
            branch, which would unmount ScreenRecordGuard and make the browser
            re-ask for screen sharing. */}
        {pickingProblem && (
          <div className="absolute inset-0 z-40 flex items-center justify-center bg-[#141414]/70 backdrop-blur-[2px]">
            <Loading size="lg" className="text-brand" />
          </div>
        )}
        {/* Interview-only question rail. Practice is a free browse of the whole
            bank, where "question 3 of 5" would be a number about nothing. */}
        {isInterviewFlow && (
          <nav
            ref={railRef}
            aria-label="Interview coding questions"
            className="flex w-14 shrink-0 flex-col items-center gap-3 border-r border-gray-800 bg-[#171717] py-4 font-sans"
          >
            <span className="text-[9px] font-bold uppercase tracking-widest text-gray-500 font-sans">
              Q
            </span>

            <ol className="flex flex-col items-center gap-2.5 overflow-y-auto font-sans">
              {railSteps.map((step) => {
                const current = step.id === selectedId;
                return (
                  <li key={step.id} className="font-sans">
                    <button
                      type="button"
                      onClick={() => setSelectedId(step.id)}
                      aria-current={current ? "step" : undefined}
                      title={`Question ${step.number}: ${step.title}${
                        step.solved ? " — solved" : step.attempted ? " — attempted" : ""
                      }`}
                      className={`flex h-8 w-8 items-center justify-center rounded-full border text-[11px] font-bold font-sans transition-colors ${
                        step.solved
                          ? // Solved: filled in the site's brand colour.
                            "border-brand bg-brand text-brand-foreground"
                          : current
                            ? "border-brand bg-brand/15 text-brand"
                            : step.attempted
                              ? "border-amber-500/50 bg-transparent text-amber-400 hover:border-amber-400"
                              : "border-gray-700 bg-transparent text-gray-400 hover:border-gray-500 hover:text-gray-200"
                      } ${current && !step.solved ? "ring-2 ring-brand/40" : ""}`}
                    >
                      {step.solved ? <Check className="h-4 w-4" /> : step.number}
                    </button>
                  </li>
                );
              })}
            </ol>

            <span
              title={`${solvedCount} of ${railSteps.length} coding questions solved`}
              className="mt-auto text-[10px] font-semibold text-gray-500 font-sans"
            >
              {solvedCount}/{railSteps.length}
            </span>
          </nav>
        )}

        {/* Left Column: Problem Description Pane

            min-w-0 + overflow-x-hidden are load-bearing: this is a shrink-0
            flex child with a percentage width, so its default min-width:auto
            lets a long unbreakable value (the widest sample input in the bank
            is a 258-char matrix literal) stretch it past the width we set and
            push the divider and editor off-screen. */}
        <div
          ref={problemPaneRef}
          style={{ width: `${leftWidthPercent}%` }}
          className="border-r border-gray-800 bg-[#171717] overflow-y-auto overflow-x-hidden min-w-0 p-6 space-y-5 text-gray-300 text-[13.5px] font-sans leading-[1.7] shrink-0"
        >
          <div className="space-y-2.5">
            <h1 className="text-[26px] font-bold font-sans text-white leading-snug break-words">
              {activeProblem.title}
            </h1>
            <div className="flex flex-wrap items-center gap-2 font-sans">
              <span
                className={`rounded-full border px-2.5 py-0.5 text-[11.5px] font-semibold font-sans ${difficultyPillClass(
                  activeProblem.difficulty,
                )}`}
              >
                {activeProblem.difficulty}
              </span>
              <span className="rounded-full border border-gray-700 bg-[#222222] px-2.5 py-0.5 text-[11.5px] font-sans text-gray-300">
                {activeProblem.category}
              </span>
              {(activeProblem.tags || []).slice(0, 4).map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-gray-800 bg-[#1E1E1E] px-2.5 py-0.5 text-[11.5px] font-sans text-gray-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Problem Statement */}
          <InlineMarkdown
            text={activeProblem.description}
            className="text-[13.5px] leading-[1.7] text-gray-300"
          />

          {/* Examples — stacked rather than side-by-side so a long array
              literal wraps down the pane instead of widening it. */}
          {testCasesList.length > 0 && (
            <div className="space-y-4 border-t border-gray-800 pt-4 font-sans">
              {testCasesList.map((ex, i) => (
                <div key={i} className="space-y-2 font-sans min-w-0">
                  <h3 className="text-[14px] font-bold font-sans text-white">
                    Example {i + 1}
                  </h3>
                  <div className="space-y-2 rounded-[4px] border border-gray-800 border-l-2 border-l-gray-600 bg-[#1C1C1C] px-3.5 py-3 font-sans min-w-0">
                    {ex.diagram && (
                      <div className="min-w-0 pb-1">
                        <ProblemDiagram spec={ex.diagram} />
                      </div>
                    )}
                    <div className="min-w-0 font-sans">
                      <span className="font-semibold font-sans text-gray-400">Input: </span>
                      <span className="font-sans text-gray-200 break-all">
                        {formatSampleValue(ex.input)}
                      </span>
                    </div>
                    <div className="min-w-0 font-sans">
                      <span className="font-semibold font-sans text-gray-400">Output: </span>
                      <span className="font-sans font-semibold text-emerald-300 break-all">
                        {formatSampleValue(ex.output)}
                      </span>
                    </div>
                    {ex.explanation && (
                      <div className="min-w-0 border-t border-gray-800 pt-2 font-sans">
                        <span className="font-semibold font-sans text-gray-400">
                          Explanation:{" "}
                        </span>
                        <InlineMarkdown
                          text={ex.explanation}
                          className="mt-1 text-[13px] text-gray-400"
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Constraints — curated problems pack several onto separate lines,
              bank problems ship a single line. Split so both read as a list. */}
          {constraintsList.length > 0 && (
            <div className="space-y-2 border-t border-gray-800 pt-4 font-sans">
              <h3 className="text-[14px] font-bold font-sans text-white">Constraints</h3>
              <ul className="space-y-1.5 font-sans min-w-0">
                {constraintsList.map((line, i) => (
                  <li key={i} className="flex gap-2 font-sans min-w-0">
                    <span className="mt-[2px] text-gray-600 font-sans shrink-0">•</span>
                    <InlineMarkdown text={line} className="min-w-0 text-gray-300" />
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Follow-up — the optimal-complexity nudge judges close with. */}
          {activeProblem.follow_up && (
            <div className="space-y-2 border-t border-gray-800 pt-4 font-sans">
              <h3 className="text-[14px] font-bold font-sans text-white">Follow-up</h3>
              <InlineMarkdown
                text={activeProblem.follow_up}
                className="text-[13.5px] text-gray-400"
              />
            </div>
          )}

          {/* Hints stay collapsed: a hint on screen by default is a spoiler. */}
          {(activeProblem.hints || []).length > 0 && (
            <div className="space-y-2 border-t border-gray-800 pt-4 font-sans">
              {activeProblem.hints!.map((hint, i) => (
                <details
                  key={i}
                  className="group rounded-[4px] border border-gray-800 bg-[#1C1C1C] font-sans"
                >
                  <summary className="cursor-pointer select-none px-3 py-2 text-[13px] font-semibold font-sans text-gray-400 hover:text-gray-200">
                    Hint {i + 1}
                  </summary>
                  <div className="border-t border-gray-800 px-3 py-2.5">
                    <InlineMarkdown text={hint} className="text-[13px] text-gray-300" />
                  </div>
                </details>
              ))}
            </div>
          )}

          {(activeProblem.companies || []).length > 0 && (
            <div className="space-y-2 border-t border-gray-800 pt-4 font-sans">
              <h3 className="text-[14px] font-bold font-sans text-white">Asked by</h3>
              <div className="flex flex-wrap gap-1.5 font-sans">
                {activeProblem.companies.map((company) => (
                  <span
                    key={company}
                    className="rounded-[4px] border border-gray-800 bg-[#222222] px-2 py-0.5 text-[11.5px] font-sans text-gray-400"
                  >
                    {company}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Horizontal Drag Handle */}
        <div
          onMouseDown={handleMouseDownHorizontal}
          className="w-1.5 bg-[#252526] hover:bg-emerald-500 cursor-col-resize flex items-center justify-center transition-colors z-20 shrink-0 select-none group"
          title="Drag to resize problem & editor panes"
        >
          <GripVertical className="h-4 w-3 text-gray-600 group-hover:text-white" />
        </div>

        {/* Right Column: Code Editor & Resizable Test Cases Pane */}
        <div ref={rightColumnRef} className="flex-1 flex flex-col bg-[#1E1E1E] font-sans min-w-0">
          {/* Editor Header Bar */}
          <div className="flex h-9 items-center justify-between border-b border-gray-800 bg-[#252526] px-4 text-[11px] text-gray-400 font-sans shrink-0">
            <span className="flex items-center gap-2 font-sans">
              <Terminal className="h-3.5 w-3.5 text-emerald-400" />
              solution.{getExt()}
            </span>
            <span className="flex items-center gap-3 font-sans">
              {/* Wall clock — candidates pace a timed round by it. */}
              <span
                title={clock.toLocaleDateString(undefined, {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
                className="flex items-center gap-1.5 text-[11px] text-gray-300 font-sans tabular-nums"
              >
                <Clock className="h-3.5 w-3.5 text-emerald-400" />
                {clock.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
              <span className="text-[10px] text-gray-500 font-sans">VS Code Dark+ Syntax & Autocomplete</span>
            </span>
          </div>

          {/* VS Code CodeMirror Editor Window.
              The React handlers cover the wrapper; CodeMirror installs its own
              clipboard listeners on .cm-content, so the editor is locked down
              from inside by `clipboardLockdown` in the extension list. */}
          <div
            onCopy={blockClipboard("copy")}
            onCut={blockClipboard("cut")}
            onPaste={blockClipboard("paste")}
            onDrop={blockClipboard("paste")}
            onKeyDown={handleEditorKeyDown}
            onContextMenu={(e) => e.preventDefault()}
            className="flex-1 overflow-auto bg-[#1E1E1E] font-sans text-xs"
          >
            <CodeMirror
              value={code}
              height="100%"
              theme={vscodeDark}
              extensions={editorExtensions}
              onChange={(val) => setCode(val)}
              className="h-full text-xs font-sans"
              basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightSpecialChars: true,
                history: true,
                drawSelection: true,
                dropCursor: true,
                allowMultipleSelections: true,
                indentOnInput: true,
                syntaxHighlighting: true,
                bracketMatching: true,
                closeBrackets: true,
                autocompletion: true,
                rectangularSelection: true,
                crosshairCursor: true,
                highlightActiveLine: true,
                highlightSelectionMatches: true,
                closeBracketsKeymap: true,
                defaultKeymap: true,
                searchKeymap: true,
                historyKeymap: true,
                foldKeymap: true,
                completionKeymap: true,
                lintKeymap: true,
              }}
            />
          </div>

          {/* Vertical Drag Handle */}
          <div
            onMouseDown={handleMouseDownVertical}
            className="h-1.5 bg-[#252526] hover:bg-emerald-500 cursor-row-resize flex items-center justify-center transition-colors z-20 shrink-0 select-none group border-t border-gray-800"
            title="Drag up/down to resize test cases panel"
          >
            <GripHorizontal className="h-3 w-4 text-gray-600 group-hover:text-white" />
          </div>

          {/* Test Cases Tabbed Box Section */}
          <div
            style={{ height: `${testCasesHeightPx}px` }}
            className="bg-[#171717] flex flex-col shrink-0 font-sans overflow-hidden border-t border-gray-800"
          >
            {/* Test Cases Tab Bar & Run Status */}
            <div className="flex items-center justify-between border-b border-gray-800 bg-[#222222] px-4 py-2 text-xs font-sans shrink-0">
              <div className="flex items-center gap-2 font-sans">
                <span className="font-bold text-gray-300 mr-2 font-sans">Test Cases:</span>
                {testCasesList.map((_, idx) => {
                  const tr = runResult?.test_results?.[idx];
                  return (
                    <button
                      key={idx}
                      onClick={() => setActiveTestCaseTab(idx)}
                      className={`flex items-center gap-1.5 rounded-[4px] px-3 py-1 text-xs font-semibold font-sans transition-all ${
                        activeTestCaseTab === idx
                          ? "bg-[#333333] text-white shadow-sm border border-gray-700 font-sans"
                          : "text-gray-400 hover:text-white font-sans"
                      }`}
                    >
                      <span className="font-sans font-semibold">Testcase {idx}</span>
                      {tr &&
                        (tr.passed ? (
                          <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                        ) : (
                          <XCircle className="h-3 w-3 text-rose-400" />
                        ))}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Selected Test Case Content Box */}
            <div className="p-4 overflow-y-auto flex-1 space-y-3 font-sans text-xs">
              {useCustomInput ? (
                <div className="space-y-1.5 font-sans">
                  <label className="text-[11px] font-semibold font-sans text-gray-400">
                    Custom Input (STDIN)
                  </label>
                  <textarea
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    placeholder="Enter custom input..."
                    className="w-full h-16 rounded-[4px] border border-gray-800 bg-[#141414] p-2 font-sans text-xs text-gray-200 focus:outline-none"
                  />
                </div>
              ) : (
                testCasesList[activeTestCaseTab] && (
                  <div className="grid grid-cols-2 gap-4 font-sans">
                    {/* Input (stdin) */}
                    <div className="space-y-1 font-sans">
                      <span className="font-semibold font-sans text-gray-400 text-[11px]">
                        Input (stdin)
                      </span>
                      <div className="rounded-[4px] bg-[#222222] p-2.5 font-sans text-gray-200 text-[11px] border border-gray-800">
                        {typeof testCasesList[activeTestCaseTab].input === "object"
                          ? JSON.stringify(testCasesList[activeTestCaseTab].input)
                          : testCasesList[activeTestCaseTab].input}
                      </div>
                    </div>

                    {/* Expected Output */}
                    <div className="space-y-1 font-sans">
                      <span className="font-semibold font-sans text-gray-400 text-[11px]">
                        Expected Output
                      </span>
                      <div className="rounded-[4px] bg-[#222222] p-2.5 font-sans text-emerald-400 font-bold text-[11px] border border-gray-800">
                        {typeof testCasesList[activeTestCaseTab].output === "object"
                          ? JSON.stringify(testCasesList[activeTestCaseTab].output)
                          : testCasesList[activeTestCaseTab].output}
                      </div>
                    </div>
                  </div>
                )
              )}

              {/* Your Output & Result */}
              {runResult && runResult.test_results?.[activeTestCaseTab] && (
                <div className="rounded-[4px] bg-[#222222] p-3 border border-gray-800 space-y-2 font-sans">
                  <div className="flex items-center justify-between font-sans">
                    <span className="font-semibold text-gray-400 font-sans text-[11px]">Your Output:</span>
                    <span
                      className={`font-bold font-sans text-xs ${
                        runResult.test_results[activeTestCaseTab].passed
                          ? "text-emerald-400"
                          : "text-rose-400"
                      }`}
                    >
                      {runResult.test_results[activeTestCaseTab].passed
                        ? "✓ Passed"
                        : "✕ Wrong Answer"}
                    </span>
                  </div>
                  <div className="font-sans text-gray-100 text-[11px] rounded bg-[#1A1A1A] p-2 border border-gray-800/80">
                    {typeof runResult.test_results[activeTestCaseTab].actual === "object"
                      ? JSON.stringify(runResult.test_results[activeTestCaseTab].actual)
                      : String(runResult.test_results[activeTestCaseTab].actual)}
                  </div>
                </div>
              )}

              {/* Console STDOUT Output */}
              {runResult?.stdout && (
                <div className="rounded-[4px] bg-[#1E1E1E] p-3 border border-gray-800 space-y-1 font-sans">
                  <span className="font-semibold text-gray-400 font-sans text-[11px]">Compiler stdout:</span>
                  <pre className="font-sans text-gray-300 text-[11px] whitespace-pre-wrap">
                    {runResult.stdout}
                  </pre>
                </div>
              )}

              {/* Compiler message. Lives here, below the cases, rather than in
                  the tab bar: a compiler diagnostic is many lines of text and
                  a one-line strip truncated it into uselessness. */}
              {runResult && (
                <div
                  className={`rounded-[4px] p-3 border space-y-1.5 font-sans ${
                    runResult.error
                      ? "bg-rose-950/40 border-rose-500/30"
                      : runResult.passed
                      ? "bg-emerald-950/30 border-emerald-500/30"
                      : "bg-[#222222] border-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between font-sans">
                    <span className="font-semibold text-gray-400 font-sans text-[11px]">
                      Compiler Message
                    </span>
                    <span className="text-gray-400 font-sans text-[11px]">
                      {runResult.runtime_ms} ms
                    </span>
                  </div>
                  <div
                    className={`font-bold font-sans text-xs ${
                      runResult.error
                        ? "text-rose-400"
                        : runResult.passed
                        ? "text-emerald-400"
                        : "text-rose-400"
                    }`}
                  >
                    {runResult.error
                      ? "Execution Error"
                      : runResult.passed
                      ? "Congratulations! All Test Cases Passed"
                      : "Wrong Answer"}
                  </div>
                  {runResult.error && (
                    <pre className="text-rose-300 font-sans text-[11px] whitespace-pre-wrap">
                      {runResult.error}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* HackerRank-Style Bottom Action Bar */}
          <div className="flex h-14 items-center justify-between border-t border-gray-800 bg-[#252526] px-4 shrink-0 font-sans">
            <div className="flex items-center gap-4 text-xs text-gray-400 font-sans">
              {/* Upload Code File Button */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".py,.js,.ts,.java,.cpp,.cs,.go,.rs,.rb,.php,.swift,.m,.erl,.hs,.sql,.txt"
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 rounded-[4px] border border-gray-700 bg-[#1E1E1E] px-3 py-1.5 text-xs font-sans text-gray-300 hover:text-white hover:border-gray-600 transition-colors"
              >
                <Upload className="h-3.5 w-3.5" />
                <span className="font-sans">Upload Code as File</span>
              </button>

              {/* Custom Input Checkbox */}
              <label className="flex items-center gap-2 cursor-pointer hover:text-white select-none font-sans">
                <input
                  type="checkbox"
                  checked={useCustomInput}
                  onChange={(e) => setUseCustomInput(e.target.checked)}
                  className="rounded-[2px] border-gray-700 bg-gray-800 text-emerald-500 focus:ring-0"
                />
                <span className="font-sans">Test against custom input</span>
              </label>
            </div>

            {/* Rectangular Plain-Text Run & Submit Buttons */}
            <div className="flex items-center gap-3 font-sans">
              {submitError && (
                <span className="text-rose-400 font-sans text-[11px] max-w-xs truncate" title={submitError}>
                  Submit failed: {submitError}
                </span>
              )}

              <button
                onClick={handleRunTests}
                disabled={running}
                className="rounded-[4px] bg-[#393939] px-5 py-2 text-xs font-semibold font-sans text-white hover:bg-[#454545] transition-colors disabled:opacity-50"
              >
                <span className="font-sans">{running ? "Running…" : "Run Code"}</span>
              </button>

              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="rounded-[4px] bg-emerald-600 px-6 py-2 text-xs font-bold font-sans text-white hover:bg-emerald-500 transition-colors shadow-md disabled:opacity-50"
              >
                <span className="font-sans">{submitting ? "Submitting…" : "Submit Code"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* LeetCode-style problem browser — practice only. The interview hands the
          candidate a fixed set of questions, so free browsing is not offered
          there. */}
      {showProblemList && !isInterviewFlow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-sans">
          <div className="flex w-full max-w-6xl h-[92vh] flex-col rounded-[4px] border border-gray-800 bg-[#1E1E1E] shadow-2xl font-sans">
            <div className="flex items-center justify-between border-b border-gray-800 p-5 font-sans">
              <div className="flex items-center gap-2 font-sans">
                <div className="flex h-8 w-8 items-center justify-center rounded-[4px] border border-emerald-500/30 bg-emerald-950 text-emerald-400 font-sans">
                  <ListChecks className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold font-sans text-white">All Problems</h3>
                  <p className="text-[11px] text-gray-500 font-sans">
                    {catalogLoading
                      ? "Loading…"
                      : `${catalogTotal.toLocaleString()} problem${catalogTotal === 1 ? "" : "s"}`}
                    {catalogTotal > CATALOG_PAGE_SIZE &&
                      ` · page ${catalogPage + 1} of ${Math.ceil(catalogTotal / CATALOG_PAGE_SIZE)}`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowProblemList(false)}
                className="rounded-[4px] p-1 text-gray-400 hover:bg-gray-800 hover:text-white font-sans"
              >
                ✕
              </button>
            </div>

            <div className="flex items-center gap-3 border-b border-gray-800 px-5 py-3 font-sans">
              <div className="flex flex-1 items-center gap-2 rounded-[4px] border border-gray-700 bg-[#141414] px-2.5 py-1.5 font-sans">
                <Search className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                <input
                  value={problemQuery}
                  onChange={(e) => setProblemQuery(e.target.value)}
                  placeholder="Search by title, topic or tag"
                  className="w-full bg-transparent text-xs text-white font-sans placeholder:text-gray-600 focus:outline-none"
                />
              </div>
              <div className="flex items-center gap-1 font-sans">
                {(["All", "Easy", "Medium", "Hard"] as const).map((level) => (
                  <button
                    key={level}
                    onClick={() => setDifficultyFilter(level)}
                    className={`rounded-[4px] border px-2.5 py-1.5 text-[11px] font-semibold font-sans transition-colors ${
                      difficultyFilter === level
                        ? "border-brand bg-brand/15 text-brand"
                        : "border-gray-700 bg-[#252526] text-gray-400 hover:text-white"
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
              {/* Topics come from the server so the list stays in step with the
                  catalogue instead of being hardcoded to the curated six. */}
              <select
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
                title="Filter by topic"
                className="max-w-[11rem] rounded-[4px] border border-gray-700 bg-[#252526] px-2 py-1.5 text-[11px] font-semibold font-sans text-gray-300 focus:border-brand focus:outline-none"
              >
                <option value="All">All topics</option>
                {catalogTopics.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1 overflow-y-auto font-sans">
              {catalogError ? (
                <p className="p-6 text-center text-xs text-rose-400 font-sans">{catalogError}</p>
              ) : catalogLoading && catalog.length === 0 ? (
                <p className="p-6 text-center text-xs text-gray-500 font-sans">Loading problems…</p>
              ) : catalog.length === 0 ? (
                <p className="p-6 text-center text-xs text-gray-500 font-sans">
                  No problems match that search.
                </p>
              ) : (
                <table className="w-full text-left text-[13px] text-gray-300 font-sans">
                  <thead className="sticky top-0 bg-[#252526] text-gray-400 font-sans">
                    <tr>
                      <th className="px-4 py-2 font-semibold font-sans">Status</th>
                      <th className="px-4 py-2 font-semibold font-sans">Title</th>
                      <th className="px-4 py-2 font-semibold font-sans">Topic</th>
                      <th className="px-4 py-2 font-semibold font-sans">Difficulty</th>
                    </tr>
                  </thead>
                  <tbody className="font-sans">
                    {catalog.map((p) => {
                      const solved = submissions.some((s) => s.problem_id === p.id && s.passed);
                      return (
                        <tr
                          key={p.id}
                          onClick={() => void handlePickProblem(p.id)}
                          className={`cursor-pointer border-t border-gray-800 font-sans transition-colors hover:bg-[#252526] ${
                            p.id === selectedId ? "bg-[#252526]" : ""
                          }`}
                        >
                          <td className="px-4 py-2.5 font-sans">
                            {solved ? (
                              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand text-brand-foreground">
                                <Check className="h-2.5 w-2.5" />
                              </span>
                            ) : (
                              <span className="block h-4 w-4 rounded-full border border-gray-700" />
                            )}
                          </td>
                          <td className="px-4 py-2.5 font-semibold text-white font-sans">{p.title}</td>
                          <td className="px-4 py-2.5 text-gray-400 font-sans">{p.category}</td>
                          <td
                            className={`px-4 py-2.5 font-semibold font-sans ${
                              p.difficulty === "Easy"
                                ? "text-emerald-400"
                                : p.difficulty === "Medium"
                                  ? "text-amber-400"
                                  : "text-rose-400"
                            }`}
                          >
                            {p.difficulty}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>

            {/* Paging — the catalogue is far larger than one page, so without
                this only the first CATALOG_PAGE_SIZE rows are reachable. */}
            {catalogTotal > CATALOG_PAGE_SIZE && (
              <div className="flex items-center justify-between gap-3 border-t border-gray-800 px-4 py-2.5 font-sans">
                <span className="text-[11px] text-gray-500 font-sans tabular-nums">
                  {(catalogPage * CATALOG_PAGE_SIZE + 1).toLocaleString()}–
                  {Math.min((catalogPage + 1) * CATALOG_PAGE_SIZE, catalogTotal).toLocaleString()}{" "}
                  of {catalogTotal.toLocaleString()}
                </span>
                <div className="flex items-center gap-2 font-sans">
                  <button
                    onClick={() => setCatalogPage((p) => Math.max(p - 1, 0))}
                    disabled={catalogPage === 0 || catalogLoading}
                    className="rounded-[4px] border border-gray-700 bg-[#252526] px-2.5 py-1 text-[11px] font-semibold font-sans text-gray-300 transition-colors hover:border-gray-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <button
                    onClick={() => setCatalogPage((p) => p + 1)}
                    disabled={
                      (catalogPage + 1) * CATALOG_PAGE_SIZE >= catalogTotal || catalogLoading
                    }
                    className="rounded-[4px] border border-gray-700 bg-[#252526] px-2.5 py-1 text-[11px] font-semibold font-sans text-gray-300 transition-colors hover:border-gray-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Submission History for this interview session */}
      {showHistory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-sans">
          <div className="w-full max-w-2xl rounded-[4px] border border-gray-800 bg-[#1E1E1E] p-6 shadow-2xl space-y-4 font-sans">
            <div className="flex items-center justify-between font-sans">
              <div className="flex items-center gap-2 font-sans">
                <div className="flex h-8 w-8 items-center justify-center rounded-[4px] bg-emerald-950 text-emerald-400 border border-emerald-500/30 font-sans">
                  <History className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold font-sans text-white">Submissions</h3>
                  <p className="text-[11px] text-gray-500 font-sans">
                    This interview only — session {sessionId}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowHistory(false)}
                className="rounded-[4px] p-1 text-gray-400 hover:bg-gray-800 hover:text-white font-sans"
              >
                ✕
              </button>
            </div>

            {submissions.length === 0 ? (
              <p className="rounded-[4px] border border-gray-800 bg-[#141414] p-4 text-xs text-gray-400 font-sans">
                No submissions recorded in this interview yet.
              </p>
            ) : (
              <div className="max-h-80 overflow-y-auto rounded-[4px] border border-gray-800 font-sans">
                <table className="w-full text-left text-[11px] text-gray-300 font-sans">
                  <thead className="bg-[#252526] text-gray-400 font-sans">
                    <tr>
                      <th className="px-3 py-2 font-semibold font-sans">Problem</th>
                      <th className="px-3 py-2 font-semibold font-sans">Language</th>
                      <th className="px-3 py-2 font-semibold font-sans">Tests</th>
                      <th className="px-3 py-2 font-semibold font-sans">Result</th>
                      <th className="px-3 py-2 font-semibold font-sans">When</th>
                    </tr>
                  </thead>
                  <tbody className="font-sans">
                    {submissions.map((s) => (
                      <tr key={s.id} className="border-t border-gray-800 font-sans">
                        <td className="px-3 py-2 font-sans">{s.problem_title || s.problem_id}</td>
                        <td className="px-3 py-2 font-sans">{s.language}</td>
                        <td className="px-3 py-2 font-sans">
                          {s.tests_passed}/{s.tests_total}
                        </td>
                        <td
                          className={`px-3 py-2 font-semibold font-sans ${
                            s.passed ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {s.passed ? "Accepted" : "Failed"}
                        </td>
                        <td className="px-3 py-2 text-gray-500 font-sans">
                          {s.created_at ? new Date(s.created_at).toLocaleString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Submission Result & AI Review Modal */}
      {showAiModal && submitResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-sans">
          <div className="w-full max-w-lg rounded-[4px] border border-gray-800 bg-[#1E1E1E] p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in duration-200 font-sans max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between font-sans">
              <div className="flex items-center gap-2 font-sans">
                <div className="flex h-8 w-8 items-center justify-center rounded-[4px] bg-emerald-950 text-emerald-400 border border-emerald-500/30 font-sans">
                  <Terminal className="h-4 w-4" />
                </div>
                <h3 className="text-base font-bold font-sans text-white">Submission Result</h3>
              </div>
              <button
                onClick={() => setShowAiModal(false)}
                className="rounded-[4px] p-1 text-gray-400 hover:bg-gray-800 hover:text-white font-sans"
              >
                ✕
              </button>
            </div>

            {/* The verdict, which is what the candidate pressed Submit for. It
                used to be missing here — the modal showed only the AI write-up,
                so a submission looked like it had done nothing. */}
            <div
              className={`rounded-[4px] border p-4 space-y-1 font-sans ${
                submitResult.error
                  ? "border-rose-500/30 bg-rose-950/30"
                  : submitResult.passed
                  ? "border-emerald-500/30 bg-emerald-950/30"
                  : "border-rose-500/30 bg-rose-950/20"
              }`}
            >
              <div
                className={`text-sm font-bold font-sans ${
                  submitResult.error
                    ? "text-rose-400"
                    : submitResult.passed
                    ? "text-emerald-400"
                    : "text-rose-400"
                }`}
              >
                {submitResult.error
                  ? "Execution Error"
                  : submitResult.passed
                  ? "Accepted — all test cases passed"
                  : "Wrong Answer"}
              </div>
              <div className="text-[11px] text-gray-400 font-sans">
                {submitResult.test_results.filter((t) => t.passed).length}/
                {submitResult.test_results.length} test cases passed ·{" "}
                {submitResult.runtime_ms} ms
                {submitResult.submission_id ? " · saved to this interview" : ""}
              </div>
              {submitResult.error && (
                <pre className="text-rose-300 font-sans text-[11px] whitespace-pre-wrap">
                  {submitResult.error}
                </pre>
              )}
            </div>

            <div>
              <h4 className="text-xs font-bold font-sans text-white mb-1.5">
                AI Code Review & Big-O Report
              </h4>
              <div className="rounded-[4px] border border-gray-800 bg-[#141414] p-4 text-xs leading-relaxed whitespace-pre-wrap text-gray-200 font-sans">
                {submitResult.ai_analysis}
              </div>
            </div>

            <div className="flex justify-end font-sans">
              <button
                onClick={() => setShowAiModal(false)}
                className="rounded-[4px] bg-emerald-600 px-5 py-2 text-xs font-bold font-sans text-white shadow-md hover:bg-emerald-500"
              >
                {isInterviewFlow ? "Back to Question" : "Continue Practice"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
