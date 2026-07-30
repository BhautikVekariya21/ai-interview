/**
 * CodeSandbox — Professional Full-Screen Resizable IDE with VS Code Syntax Highlighting & Autocompletion.
 *
 * Supported Languages (14):
 * Python 3, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift, Objective-C, Erlang, Haskell
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Terminal,
  Code2,
  Cpu,
  ArrowLeft,
  Upload,
  AlertTriangle,
  GripVertical,
  GripHorizontal,
} from "lucide-react";
import {
  fetchCodingProblems,
  runCodingSolution,
  submitCodingSolution,
  type CodingProblem,
  type RunCodeResponseDto,
  type SubmitCodeResponseDto,
} from "@/lib/api";

import CodeMirror from "@uiw/react-codemirror";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { java } from "@codemirror/lang-java";
import { cpp } from "@codemirror/lang-cpp";
import { go } from "@codemirror/lang-go";
import { rust } from "@codemirror/lang-rust";
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
  | "haskell";

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
};

export default function CodeSandbox() {
  const [problems, setProblems] = useState<CodingProblem[]>([]);
  const [selectedId, setSelectedId] = useState<string>("two-sum");
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

  const [loading, setLoading] = useState<boolean>(false);
  const [running, setRunning] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<RunCodeResponseDto | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitCodeResponseDto | null>(null);
  const [showAiModal, setShowAiModal] = useState<boolean>(false);

  // Security & Proctoring State
  const [proctorWarning, setProctorWarning] = useState<string | null>(null);
  const [tabSwitchCount, setTabSwitchCount] = useState<number>(0);
  const lastInternalCopiedTextRef = useRef<string>("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load problem dataset
  useEffect(() => {
    setLoading(true);
    fetchCodingProblems()
      .then((data) => {
        setProblems(data);
        if (data.length > 0) {
          const first = data[0];
          setSelectedId(first.id);
          setCode((first.starter_code as any)[language] || defaultStarterCodes[language]);
        }
      })
      .catch((err) => console.error("Failed to load coding problems:", err))
      .finally(() => setLoading(false));
  }, []);

  const activeProblem = problems.find((p) => p.id === selectedId) || problems[0];

  // Update code on problem or language change
  useEffect(() => {
    if (activeProblem) {
      setCode((activeProblem.starter_code as any)[language] || defaultStarterCodes[language]);
      setRunResult(null);
      setSubmitResult(null);
      setActiveTestCaseTab(0);
    }
  }, [activeProblem, language]);

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
        const offsetX = e.clientX - rect.left;
        const newPercent = Math.min(Math.max((offsetX / rect.width) * 100, 20), 80);
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

  // Quiet Background Proctoring & Tab Switch Detection
  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ video: true, audio: true })
        .then((stream) => {
          const recorder = new MediaRecorder(stream);
          recorder.start();
          mediaRecorderRef.current = recorder;
        })
        .catch(() => {});
    }

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
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // In-Editor Copy/Paste Security
  const handleCopyInEditor = () => {
    const selection = window.getSelection()?.toString() || "";
    if (selection) {
      lastInternalCopiedTextRef.current = selection;
    }
  };

  const handlePasteInEditor = (e: ClipboardEvent) => {
    const pastedText = e.clipboardData?.getData("text");
    if (pastedText && pastedText === lastInternalCopiedTextRef.current) {
      return;
    }
    e.preventDefault();
    setProctorWarning("External paste disabled. Only code copied within this editor can be pasted.");
  };

  const handleResetCode = () => {
    if (activeProblem) {
      setCode((activeProblem.starter_code as any)[language] || defaultStarterCodes[language]);
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
      const res = await runCodingSolution(activeProblem.id, language as any, code);
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

  const handleSubmit = useCallback(async () => {
    if (!activeProblem || submitting) return;
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const res = await submitCodingSolution(activeProblem.id, language as any, code);
      setSubmitResult(res);
      setShowAiModal(true);
    } catch (err) {
      alert("Submission error: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setSubmitting(false);
    }
  }, [activeProblem, language, code, submitting]);

  // CodeMirror Language Extension Provider
  const getLanguageExtension = () => {
    const auto = autocompletion();
    switch (language) {
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
      default:
        return [python(), auto];
    }
  };

  if (loading || !activeProblem) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#141414] text-gray-300 font-sans">
        <div className="flex items-center gap-3 font-medium text-sm font-sans">
          <Cpu className="h-5 w-5 animate-spin text-emerald-500 font-sans" />
          Loading Coding Environment…
        </div>
      </div>
    );
  }

  const testCasesList = activeProblem.examples || [];

  const getExt = () => {
    switch (language) {
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
          <Link
            to="/"
            title="Back to Dashboard"
            className="flex h-7 w-7 items-center justify-center rounded-[4px] border border-gray-700 bg-[#252526] text-gray-300 hover:text-white hover:border-gray-600 transition-colors font-sans"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
          </Link>

          <div className="flex items-center gap-2 font-bold text-emerald-400 font-sans">
            <Code2 className="h-4 w-4" />
            <span className="text-white font-sans">AI Code Editor</span>
          </div>

          <span className="text-gray-600 font-sans">/</span>

          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="bg-transparent font-semibold font-sans text-white focus:outline-none cursor-pointer border border-gray-700 rounded-[4px] px-2 py-0.5"
          >
            {problems.map((p) => (
              <option key={p.id} value={p.id} className="bg-[#1E1E1E] text-white font-sans">
                {p.title} ({p.difficulty})
              </option>
            ))}
          </select>
        </div>

        {/* Right: 14 Languages Selector & Controls */}
        <div className="flex items-center gap-4 font-sans">
          <div className="flex items-center gap-2 font-sans">
            <span className="text-gray-400 font-sans">Language</span>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as SupportedLang)}
              className="rounded-[4px] border border-gray-700 bg-[#252526] px-2.5 py-1 text-xs font-semibold font-sans text-white focus:outline-none cursor-pointer"
            >
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
            </select>
          </div>

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
        {/* Left Column: Problem Description Pane */}
        <div
          style={{ width: `${leftWidthPercent}%` }}
          className="border-r border-gray-800 bg-[#171717] overflow-y-auto p-6 space-y-6 text-gray-300 text-xs font-sans leading-relaxed shrink-0"
        >
          <div>
            <h1 className="text-xl font-bold font-sans text-white mb-2">{activeProblem.title}</h1>
            <div className="flex items-center gap-2 font-sans">
              <span className="rounded-[4px] bg-emerald-950/80 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-bold font-sans text-emerald-400">
                {activeProblem.difficulty}
              </span>
              <span className="text-gray-500 font-sans">•</span>
              <span className="text-gray-400 font-sans">Category: {activeProblem.category}</span>
            </div>
          </div>

          {/* Problem Statement */}
          <div className="space-y-3 whitespace-pre-line text-gray-300 font-sans">
            <p className="font-sans">{activeProblem.description}</p>
          </div>

          {/* Function Description */}
          <div className="space-y-2 border-t border-gray-800 pt-4 font-sans">
            <h3 className="text-sm font-bold font-sans text-white">Function Description</h3>
            <p className="text-gray-400 font-sans">
              Complete the function in the code editor on the right.
            </p>
          </div>

          {/* Constraints */}
          <div className="space-y-2 border-t border-gray-800 pt-4 font-sans">
            <h3 className="text-sm font-bold font-sans text-white">Constraints</h3>
            <div className="rounded-[4px] bg-[#222222] p-3 font-sans text-gray-300 text-[11px] border border-gray-800">
              {activeProblem.constraints}
            </div>
          </div>

          {/* Sample Input & Output */}
          <div className="space-y-3 border-t border-gray-800 pt-4 font-sans">
            <h3 className="text-sm font-bold font-sans text-white">Sample Input & Output</h3>
            {testCasesList.map((ex, i) => (
              <div key={i} className="grid grid-cols-2 gap-3 font-sans">
                <div className="space-y-1 font-sans">
                  <span className="font-semibold font-sans text-gray-400 text-[11px]">Sample Input #{i}</span>
                  <div className="rounded-[4px] bg-[#222222] p-3 font-sans text-gray-200 text-[11px] border border-gray-800 font-mono">
                    {typeof ex.input === "object" ? JSON.stringify(ex.input) : ex.input}
                  </div>
                </div>
                <div className="space-y-1 font-sans">
                  <span className="font-semibold font-sans text-gray-400 text-[11px]">Sample Output #{i}</span>
                  <div className="rounded-[4px] bg-[#222222] p-3 font-sans text-emerald-400 font-bold text-[11px] border border-gray-800 font-mono">
                    {typeof ex.output === "object" ? JSON.stringify(ex.output) : ex.output}
                  </div>
                </div>
              </div>
            ))}
          </div>
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
            <span className="text-[10px] text-gray-500 font-sans">VS Code Dark+ Syntax & Autocomplete</span>
          </div>

          {/* VS Code CodeMirror Editor Window */}
          <div
            onCopy={handleCopyInEditor}
            onPaste={(e) => handlePasteInEditor(e.nativeEvent)}
            className="flex-1 overflow-auto bg-[#1E1E1E] font-sans text-xs"
          >
            <CodeMirror
              value={code}
              height="100%"
              theme={vscodeDark}
              extensions={getLanguageExtension()}
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

              {/* Overall Run Result Status Header */}
              {runResult && (
                <div className="flex items-center gap-3 font-sans text-xs">
                  <span className="text-gray-400 font-sans font-medium">Compiler Message:</span>
                  <span
                    className={`font-bold font-sans ${
                      runResult.passed ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {runResult.passed
                      ? "Congratulations! All Test Cases Passed"
                      : runResult.error
                      ? `Execution Error: ${runResult.error}`
                      : "Wrong Answer"}
                  </span>
                  <span className="text-gray-500 font-sans">•</span>
                  <span className="text-gray-400 font-sans font-mono">{runResult.runtime_ms} ms</span>
                </div>
              )}
            </div>

            {/* Selected Test Case Content Box */}
            <div className="p-4 overflow-y-auto flex-1 space-y-3 font-sans text-xs">
              {runResult?.error && (
                <div className="rounded-[4px] bg-rose-950/40 border border-rose-500/30 p-3 space-y-1 font-sans">
                  <span className="font-bold text-rose-400 text-xs font-sans">Compiler / Runtime Error:</span>
                  <pre className="text-rose-300 font-mono text-[11px] whitespace-pre-wrap">
                    {runResult.error}
                  </pre>
                </div>
              )}

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
                      <div className="rounded-[4px] bg-[#222222] p-2.5 font-sans text-gray-200 text-[11px] border border-gray-800 font-mono">
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
                      <div className="rounded-[4px] bg-[#222222] p-2.5 font-sans text-emerald-400 font-bold text-[11px] border border-gray-800 font-mono">
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
                  <div className="font-mono text-gray-100 text-[11px] rounded bg-[#1A1A1A] p-2 border border-gray-800/80">
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
                  <pre className="font-mono text-gray-300 text-[11px] whitespace-pre-wrap">
                    {runResult.stdout}
                  </pre>
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
                accept=".py,.js,.ts,.java,.cpp,.cs,.go,.rs,.rb,.php,.swift,.m,.erl,.hs,.txt"
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

      {/* AI Review Modal */}
      {showAiModal && submitResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 font-sans">
          <div className="w-full max-w-lg rounded-[4px] border border-gray-800 bg-[#1E1E1E] p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in duration-200 font-sans">
            <div className="flex items-center justify-between font-sans">
              <div className="flex items-center gap-2 font-sans">
                <div className="flex h-8 w-8 items-center justify-center rounded-[4px] bg-emerald-950 text-emerald-400 border border-emerald-500/30 font-sans">
                  <Terminal className="h-4 w-4" />
                </div>
                <h3 className="text-base font-bold font-sans text-white">
                  AI Code Review & Big-O Report
                </h3>
              </div>
              <button
                onClick={() => setShowAiModal(false)}
                className="rounded-[4px] p-1 text-gray-400 hover:bg-gray-800 hover:text-white font-sans"
              >
                ✕
              </button>
            </div>

            <div className="rounded-[4px] border border-gray-800 bg-[#141414] p-4 text-xs leading-relaxed whitespace-pre-wrap text-gray-200 font-sans">
              {submitResult.ai_analysis}
            </div>

            <div className="flex justify-end font-sans">
              <button
                onClick={() => setShowAiModal(false)}
                className="rounded-[4px] bg-emerald-600 px-5 py-2 text-xs font-bold font-sans text-white shadow-md hover:bg-emerald-500"
              >
                Continue Practice
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
