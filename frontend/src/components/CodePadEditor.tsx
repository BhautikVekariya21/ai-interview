import { useEffect, useMemo, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { vscodeDark, vscodeLight } from "@uiw/codemirror-theme-vscode";
import { keymap } from "@codemirror/view";
import {
  indentWithTab,
  toggleComment,
  moveLineUp,
  moveLineDown,
  copyLineUp,
  copyLineDown,
  deleteLine,
  indentMore,
  indentLess,
} from "@codemirror/commands";
import { selectNextOccurrence } from "@codemirror/search";

/* VS Code-style keybindings on top of the defaults: Tab indents,
   Ctrl+/ comments, Alt+↑/↓ moves lines, Shift+Alt+↑/↓ copies lines,
   Ctrl+Shift+K deletes the line, Ctrl+D selects the next occurrence. */
const vsCodeKeymap = keymap.of([
  indentWithTab,
  { key: "Mod-/", run: toggleComment },
  { key: "Alt-ArrowUp", run: moveLineUp },
  { key: "Alt-ArrowDown", run: moveLineDown },
  { key: "Shift-Alt-ArrowUp", run: copyLineUp },
  { key: "Shift-Alt-ArrowDown", run: copyLineDown },
  { key: "Mod-Shift-k", run: deleteLine },
  { key: "Mod-d", run: selectNextOccurrence, preventDefault: true },
  { key: "Mod-]", run: indentMore },
  { key: "Mod-[", run: indentLess },
]);

interface CodePadEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  /** Proctoring guards — invoked with capture priority so CodeMirror never sees the event. */
  onBlockedKeyDown?: (e: React.KeyboardEvent<HTMLElement>) => void;
  onBlockedPaste?: (e: React.ClipboardEvent<HTMLElement>) => void;
  onBlockedCopyCut?: (e: React.ClipboardEvent<HTMLElement>) => void;
}

/** Tracks the Tailwind `dark` class on <html> so the editor theme follows the site theme. */
function useIsDarkMode(): boolean {
  const [isDark, setIsDark] = useState(
    () => typeof document !== "undefined" && document.documentElement.classList.contains("dark"),
  );

  useEffect(() => {
    const root = document.documentElement;
    const observer = new MutationObserver(() =>
      setIsDark(root.classList.contains("dark")),
    );
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return isDark;
}

/**
 * VS Code-style Python editor for the interview code pad: syntax highlighting,
 * autocompletion, bracket matching, and line numbers via CodeMirror.
 */
export default function CodePadEditor({
  value,
  onChange,
  placeholder,
  autoFocus,
  onBlockedKeyDown,
  onBlockedPaste,
  onBlockedCopyCut,
}: CodePadEditorProps) {
  const isDark = useIsDarkMode();
  const extensions = useMemo(() => [python(), vsCodeKeymap], []);

  return (
    <div
      className="flex-1 min-h-0 overflow-hidden [&_.cm-editor]:h-full [&_.cm-scroller]:overflow-auto text-sm [&_.cm-scroller]:!font-sans [&_.cm-content]:!font-sans [&_.cm-tooltip]:!font-sans"
      onKeyDownCapture={onBlockedKeyDown}
      onPasteCapture={(e) => {
        if (onBlockedPaste) {
          e.stopPropagation();
          onBlockedPaste(e);
        }
      }}
      onCopyCapture={(e) => {
        if (onBlockedCopyCut) {
          e.stopPropagation();
          onBlockedCopyCut(e);
        }
      }}
      onCutCapture={(e) => {
        if (onBlockedCopyCut) {
          e.stopPropagation();
          onBlockedCopyCut(e);
        }
      }}
      onDrop={(e) => e.preventDefault()}
    >
      <CodeMirror
        value={value}
        onChange={onChange}
        height="100%"
        theme={isDark ? vscodeDark : vscodeLight}
        extensions={extensions}
        placeholder={placeholder}
        autoFocus={autoFocus}
        basicSetup={{
          lineNumbers: true,
          foldGutter: true,
          autocompletion: true,
          bracketMatching: true,
          closeBrackets: true,
          highlightActiveLine: true,
          indentOnInput: true,
        }}
      />
    </div>
  );
}
