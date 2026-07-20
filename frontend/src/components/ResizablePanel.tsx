import { useCallback, useRef, useState } from "react";

type Handle = "top" | "bottom" | "left" | "right" | "tl" | "tr" | "bl" | "br";

interface ResizablePanelProps {
  children: React.ReactNode;
  className?: string;
  /** Initial size; if omitted the panel starts at its CSS/flex size until first drag. */
  defaultWidth?: number;
  defaultHeight?: number;
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
}

/**
 * A panel the user can resize from every edge and corner (not just the
 * bottom-right, which is all native CSS `resize` allows). Dragging the top or
 * left edges grows the box toward that side; corners resize both axes at once.
 */
export default function ResizablePanel({
  children,
  className = "",
  defaultWidth,
  defaultHeight,
  minWidth = 320,
  minHeight = 240,
  maxWidth = Infinity,
  maxHeight = Infinity,
}: ResizablePanelProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ width?: number; height?: number }>({
    width: defaultWidth,
    height: defaultHeight,
  });

  const clamp = (v: number, min: number, max: number) =>
    Math.min(max, Math.max(min, v));

  const startResize = useCallback(
    (handle: Handle) => (e: React.PointerEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const el = ref.current;
      if (!el) return;

      const rect = el.getBoundingClientRect();
      const startX = e.clientX;
      const startY = e.clientY;
      const startW = rect.width;
      const startH = rect.height;
      const capMaxW = Math.min(maxWidth, window.innerWidth - rect.left - 8);
      const movesLeft = handle === "left" || handle === "tl" || handle === "bl";
      const movesTop = handle === "top" || handle === "tl" || handle === "tr";
      const movesRight = handle === "right" || handle === "tr" || handle === "br";
      const movesBottom = handle === "bottom" || handle === "bl" || handle === "br";

      const onMove = (ev: PointerEvent) => {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;
        let width = startW;
        let height = startH;
        if (movesRight) width = startW + dx;
        if (movesLeft) width = startW - dx;
        if (movesBottom) height = startH + dy;
        if (movesTop) height = startH - dy;
        setSize({
          width: clamp(width, minWidth, capMaxW),
          height: clamp(height, minHeight, maxHeight),
        });
      };
      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
      };
      document.body.style.userSelect = "none";
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [minWidth, minHeight, maxWidth, maxHeight],
  );

  const edge =
    "absolute z-20 touch-none select-none opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity";
  const grip = "bg-primary/60 rounded-full";

  return (
    <div
      ref={ref}
      className={`group relative ${className}`}
      style={{ width: size.width, height: size.height }}
    >
      {children}

      {/* Edge handles */}
      <div
        onPointerDown={startResize("top")}
        className={`${edge} top-0 left-3 right-3 h-3 cursor-ns-resize flex items-start justify-center pt-0.5`}
      >
        <span className={`${grip} h-1 w-10`} />
      </div>
      <div
        onPointerDown={startResize("bottom")}
        className={`${edge} bottom-0 left-3 right-3 h-3 cursor-ns-resize flex items-end justify-center pb-0.5`}
      >
        <span className={`${grip} h-1 w-10`} />
      </div>
      <div
        onPointerDown={startResize("left")}
        className={`${edge} left-0 top-3 bottom-3 w-3 cursor-ew-resize flex items-center justify-start pl-0.5`}
      >
        <span className={`${grip} w-1 h-10`} />
      </div>
      <div
        onPointerDown={startResize("right")}
        className={`${edge} right-0 top-3 bottom-3 w-3 cursor-ew-resize flex items-center justify-end pr-0.5`}
      >
        <span className={`${grip} w-1 h-10`} />
      </div>

      {/* Corner handles */}
      <div
        onPointerDown={startResize("tl")}
        className={`${edge} top-0 left-0 w-3 h-3 cursor-nwse-resize`}
      />
      <div
        onPointerDown={startResize("tr")}
        className={`${edge} top-0 right-0 w-3 h-3 cursor-nesw-resize`}
      />
      <div
        onPointerDown={startResize("bl")}
        className={`${edge} bottom-0 left-0 w-3 h-3 cursor-nesw-resize`}
      />
      <div
        onPointerDown={startResize("br")}
        className={`${edge} bottom-0 right-0 w-4 h-4 cursor-nwse-resize opacity-100`}
      >
        {/* Always-visible corner grip so users can find the resize affordance */}
        <span className="absolute bottom-1 right-1 w-2.5 h-2.5 border-b-2 border-r-2 border-muted-foreground/50 rounded-br-sm" />
      </div>
    </div>
  );
}
