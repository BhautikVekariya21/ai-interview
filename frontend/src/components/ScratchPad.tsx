import { useRef, useEffect, useState, useCallback } from "react";
import {
  PenTool,
  Trash2,
  Eraser,
  StickyNote,
  Plus,
  Save,
  Edit3,
  X,
  Clock,
  Download,
  Copy,
  CheckCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";

/* ─── Note Types & Persistence ─────────────────────────── */
interface NoteItem {
  id: string;
  title: string;
  content: string;
  lastEdited: number; // timestamp ms
}

const NOTES_LS_KEY = "scratchpad_notes";

function loadNotes(): NoteItem[] {
  try {
    const raw = localStorage.getItem(NOTES_LS_KEY);
    if (raw) return JSON.parse(raw) as NoteItem[];
  } catch {
    // ignore corrupt/missing localStorage data
  }
  return [];
}

function saveNotesToStorage(notes: NoteItem[]) {
  localStorage.setItem(NOTES_LS_KEY, JSON.stringify(notes));
}

function formatTimestamp(ts: number): string {
  const date = new Date(ts);
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ─── Main Component ───────────────────────────────────── */
type TabMode = "note" | "scratch";

interface ScratchPadProps {
  defaultTab?: TabMode;
}

export default function ScratchPad({ defaultTab = "note" }: ScratchPadProps) {
  const [activeTab, setActiveTab] = useState<TabMode>(defaultTab);

  return (
    <div className="flex-1 w-full h-full flex flex-col bg-transparent relative overflow-hidden">
      {/* Tab Switcher */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-border bg-card/80 backdrop-blur-sm z-20 shrink-0">
        <button
          onClick={() => setActiveTab("note")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            activeTab === "note"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:bg-accent/50"
          }`}
        >
          <StickyNote className="w-3.5 h-3.5" />
          Notes
        </button>
        <button
          onClick={() => setActiveTab("scratch")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            activeTab === "scratch"
              ? "bg-primary text-primary-foreground shadow-sm"
              : "text-muted-foreground hover:bg-accent/50"
          }`}
        >
          <PenTool className="w-3.5 h-3.5" />
          Drawing
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 relative w-full h-full overflow-hidden">
        {activeTab === "note" ? <NotesPanel /> : <DrawingCanvas />}
      </div>
    </div>
  );
}

/* ─── Notes Panel ──────────────────────────────────────── */
function NotesPanel() {
  const [notes, setNotes] = useState<NoteItem[]>(loadNotes);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editContent, setEditContent] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const contentRef = useRef<HTMLTextAreaElement>(null);

  const persistNotes = useCallback((updated: NoteItem[]) => {
    setNotes(updated);
    saveNotesToStorage(updated);
  }, []);

  const handleCreate = () => {
    setIsCreating(true);
    setEditingId(null);
    setEditTitle("");
    setEditContent("");
    setTimeout(() => contentRef.current?.focus(), 50);
  };

  const handleEdit = (note: NoteItem) => {
    setEditingId(note.id);
    setIsCreating(false);
    setEditTitle(note.title);
    setEditContent(note.content);
    setTimeout(() => contentRef.current?.focus(), 50);
  };

  const handleSave = () => {
    const title = editTitle.trim() || "Untitled Note";
    const content = editContent.trim();
    if (!content && !title) return;

    if (isCreating) {
      const newNote: NoteItem = {
        id: `note_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        title,
        content,
        lastEdited: Date.now(),
      };
      persistNotes([newNote, ...notes]);
    } else if (editingId) {
      persistNotes(
        notes.map((n) =>
          n.id === editingId
            ? { ...n, title, content, lastEdited: Date.now() }
            : n
        )
      );
    }
    setIsCreating(false);
    setEditingId(null);
    setEditTitle("");
    setEditContent("");
  };

  const handleDelete = (id: string) => {
    persistNotes(notes.filter((n) => n.id !== id));
    if (editingId === id) {
      setEditingId(null);
      setEditTitle("");
      setEditContent("");
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingId(null);
    setEditTitle("");
    setEditContent("");
  };

  const isEditorOpen = isCreating || editingId !== null;

  return (
    <div className="flex flex-col h-full">
      {/* Notes Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-card/50 shrink-0">
        <span className="text-xs font-semibold text-muted-foreground">
          {notes.length} note{notes.length !== 1 ? "s" : ""}
        </span>
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs gap-1"
          onClick={handleCreate}
          disabled={isCreating}
        >
          <Plus className="w-3 h-3" /> New
        </Button>
      </div>

      {/* Editor (create/edit) */}
      {isEditorOpen && (
        <div className="border-b border-border bg-card p-3 space-y-2 shrink-0">
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            placeholder="Note title..."
            className="w-full px-2.5 py-1.5 rounded-lg border border-border bg-background text-sm font-semibold text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <textarea
            ref={contentRef}
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            placeholder="Write your note here..."
            className="w-full px-2.5 py-2 rounded-lg border border-border bg-background text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/30 min-h-[100px]"
            rows={4}
          />
          <div className="flex items-center gap-1.5 justify-end">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={handleCancel}
            >
              <X className="w-3 h-3 mr-1" /> Cancel
            </Button>
            <Button size="sm" className="h-7 text-xs gap-1" onClick={handleSave}>
              <Save className="w-3 h-3" /> Save
            </Button>
          </div>
        </div>
      )}

      {/* Notes List */}
      <div className="flex-1 overflow-y-auto">
        {notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <StickyNote className="w-10 h-10 text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground">No notes yet</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Click "New" to create your first note
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {notes.map((note) => (
              <div
                key={note.id}
                className={`group px-3 py-3 hover:bg-accent/30 transition-colors cursor-pointer ${
                  editingId === note.id ? "bg-primary/5 border-l-2 border-l-primary" : ""
                }`}
                onClick={() => {
                  if (editingId !== note.id) handleEdit(note);
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-foreground truncate">
                      {note.title || "Untitled"}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2 leading-relaxed">
                      {note.content || "Empty note"}
                    </p>
                  </div>
                  <NoteActions note={note} onEdit={handleEdit} onDelete={handleDelete} />
                </div>
                {/* Timestamp - bottom right */}
                <div className="flex items-center justify-end gap-1 mt-1.5">
                  <Clock className="w-2.5 h-2.5 text-muted-foreground/50" />
                  <span className="text-[10px] text-muted-foreground/60 font-mono">
                    {formatTimestamp(note.lastEdited)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Note Actions (copy / download / edit / delete) ──── */
function NoteActions({
  note,
  onEdit,
  onDelete,
}: {
  note: NoteItem;
  onEdit: (n: NoteItem) => void;
  onDelete: (id: string) => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const text = `${note.title}\n\n${note.content}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const content = `${note.title}\n${'='.repeat(note.title.length || 10)}\n\n${note.content}\n\nLast edited: ${new Date(note.lastEdited).toLocaleString()}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${note.title.replace(/[^a-z0-9]/gi, '_') || 'note'}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
      <button
        onClick={handleCopy}
        className="p-1 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
        title={copied ? 'Copied!' : 'Copy note'}
      >
        {copied ? <CheckCheck className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
      </button>
      <button
        onClick={handleDownload}
        className="p-1 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
        title="Download as .txt"
      >
        <Download className="w-3 h-3" />
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onEdit(note); }}
        className="p-1 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
        title="Edit"
      >
        <Edit3 className="w-3 h-3" />
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(note.id); }}
        className="p-1 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
        title="Delete"
      >
        <Trash2 className="w-3 h-3" />
      </button>
    </div>
  );
}

/* ─── Drawing Canvas ───────────────────────────────────── */
const DRAWING_LS_KEY = "scratchpad_drawing";

function DrawingCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [mode, setMode] = useState<"draw" | "erase">("draw");
  const [lastSaved, setLastSaved] = useState<number | null>(null);

  // Handle resizing so the canvas doesn't stretch and distort coordinates
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (!canvas || !container) return;

      if (container.clientWidth === 0 || container.clientHeight === 0) return; // Prevent losing state when hidden

      // Save the current drawing data before resizing
      const ctx = canvas.getContext("2d");
      let imageData: ImageData | null = null;
      if (ctx && canvas.width > 0 && canvas.height > 0) {
        imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      }

      // Update physical size natively if it actually changed
      if (canvas.width !== container.clientWidth || canvas.height !== container.clientHeight) {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;

        // Try to restore saved drawing from localStorage on first resize
        const saved = localStorage.getItem(DRAWING_LS_KEY);
        if (saved && ctx) {
          try {
            const parsed = JSON.parse(saved);
            const img = new Image();
            img.onload = () => ctx && ctx.drawImage(img, 0, 0);
            img.src = parsed.dataUrl;
            setLastSaved(parsed.ts);
          } catch {
            // ignore corrupt/missing saved canvas data
          }
        } else if (ctx && imageData) {
          ctx.putImageData(imageData, 0, 0);
        }

        // Default styles
        if (ctx) {
          ctx.lineCap = "round";
          ctx.lineJoin = "round";
        }
      }
    };

    handleResize();
    const observer = new ResizeObserver(() => {
      handleResize();
    });
    
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    
    return () => observer.disconnect();
  }, []);

  const getCoordinates = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const colorRef = useRef({ fg: "hsl(220 15% 95%)", bg: "hsl(230 25% 4%)" });

  const startDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Use pointer capture to keep tracking even if user mouse goes slightly off canvas quickly
    canvas.setPointerCapture(e.pointerId);

    // Compute active theme colors from DOM so canvas can render them robustly
    const rawFg = getComputedStyle(document.documentElement).getPropertyValue('--foreground');
    const rawBg = getComputedStyle(document.documentElement).getPropertyValue('--background');
    if (rawFg) colorRef.current.fg = `hsl(${rawFg.trim()})`;
    if (rawBg) colorRef.current.bg = `hsl(${rawBg.trim()})`;

    const { x, y } = getCoordinates(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.lineTo(x, y);
    if (mode === "erase") {
      // destination-out erases pixels to transparent — no color bias regardless of theme
      ctx.globalCompositeOperation = "destination-out";
      ctx.strokeStyle = "rgba(0,0,0,1)";
      ctx.lineWidth = 24;
    } else {
      ctx.globalCompositeOperation = "source-over";
      ctx.strokeStyle = colorRef.current.fg;
      ctx.lineWidth = 2.5;
    }
    ctx.stroke();
  };

  const stopDrawing = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.releasePointerCapture(e.pointerId);
    }
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    localStorage.removeItem(DRAWING_LS_KEY);
    setLastSaved(null);
  };

  const saveDrawing = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL("image/png");
    const ts = Date.now();
    localStorage.setItem(DRAWING_LS_KEY, JSON.stringify({ dataUrl, ts }));
    setLastSaved(ts);
  };

  const downloadDrawing = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `drawing_${new Date().toISOString().slice(0,10)}.png`;
    a.click();
  };

  return (
    <div className="flex-1 w-full h-full flex flex-col bg-transparent relative overflow-hidden" ref={containerRef}>
      
      {/* Top Toolbar overlay over canvas */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 p-2.5 bg-card border border-border rounded-xl shadow-lg">
        <Button 
          variant={mode === "draw" ? "default" : "ghost"} 
          size="icon" 
          className="h-8 w-8"
          onClick={() => setMode("draw")}
          title="Pen Tool"
        >
          <PenTool className="w-4 h-4" />
        </Button>
        <Button 
          variant={mode === "erase" ? "default" : "ghost"} 
          size="icon" 
          className="h-8 w-8"
          onClick={() => setMode("erase")}
          title="Eraser"
        >
          <Eraser className="w-4 h-4" />
        </Button>
        <div className="w-px h-6 bg-border mx-1" />
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 text-primary hover:bg-primary/10"
          onClick={saveDrawing}
          title="Save drawing"
        >
          <Save className="w-4 h-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8 hover:bg-accent/50"
          onClick={downloadDrawing}
          title="Download as PNG"
        >
          <Download className="w-4 h-4" />
        </Button>
        <div className="w-px h-6 bg-border mx-1" />
        <Button 
          variant="outline" 
          size="icon" 
          className="h-8 w-8 text-destructive hover:bg-destructive/10"
          onClick={clearCanvas}
          title="Clear Board"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Last saved badge */}
      {lastSaved && (
        <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 px-2.5 py-1 bg-card border border-border rounded-lg shadow text-[10px] text-muted-foreground font-mono">
          <Clock className="w-3 h-3" />
          Saved {formatTimestamp(lastSaved)}
        </div>
      )}

      <canvas
        ref={canvasRef}
        onPointerDown={startDrawing}
        onPointerMove={draw}
        onPointerUp={stopDrawing}
        onPointerCancel={stopDrawing}
        className="w-full h-full touch-none cursor-crosshair"
      />
    </div>
  );
}
