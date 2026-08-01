/**
 * Figures for problem statements.
 *
 * LeetCode illustrates a histogram problem with a picture of the histogram and
 * a matrix problem with the grid. We cannot use theirs — those are copyrighted
 * assets — so the backend emits a spec computed from example 1's actual input
 * (`app/services/problem_diagrams.py`) and this draws it.
 *
 * Everything is real SVG elements, never a generated markup string, so problem
 * data cannot inject anything into the DOM. A figure is decorative: the example
 * values are printed as text directly beneath it, so screen readers get the
 * data from there and the SVG is hidden from them rather than read out as a
 * meaningless list of numbers.
 */

export interface DiagramSpec {
  kind: "bars" | "array" | "grid" | "linked" | "string";
  values?: Array<string | number>;
  rows?: string[][];
  label?: string;
}

/** Matches the pane's borders and the emerald the examples already use. */
const STROKE = "#3A3A3A";
const FILL = "#252525";
const TEXT = "#D1D5DB";
const MUTED = "#6B7280";
const ACCENT = "#34D399";

function Bars({ values, label }: { values: number[]; label?: string }) {
  const width = 26;
  const gap = 3;
  const height = 104;
  const max = Math.max(...values, 1);
  const total = values.length * (width + gap) - gap;

  return (
    <svg
      viewBox={`0 0 ${total} ${height + 22}`}
      className="h-auto w-full max-w-[380px]"
      role="presentation"
      aria-hidden="true"
    >
      {values.map((value, i) => {
        // A zero bar still needs a visible baseline tick, hence the floor of 1.
        const barHeight = Math.max((value / max) * height, value === 0 ? 1 : 4);
        const x = i * (width + gap);
        return (
          <g key={i}>
            <rect
              x={x}
              y={height - barHeight}
              width={width}
              height={barHeight}
              fill={FILL}
              stroke={STROKE}
            />
            <text
              x={x + width / 2}
              y={height - barHeight - 4}
              textAnchor="middle"
              fontSize="10"
              fill={ACCENT}
            >
              {value}
            </text>
            <text
              x={x + width / 2}
              y={height + 14}
              textAnchor="middle"
              fontSize="9"
              fill={MUTED}
            >
              {i}
            </text>
          </g>
        );
      })}
      <line x1={0} y1={height} x2={total} y2={height} stroke={STROKE} />
    </svg>
  );
}

function Cells({
  values,
  label,
  showIndices = true,
}: {
  values: Array<string | number>;
  label?: string;
  showIndices?: boolean;
}) {
  const cell = 34;
  const gap = 2;
  const total = values.length * (cell + gap) - gap;

  return (
    <svg
      viewBox={`0 0 ${total} ${cell + (showIndices ? 18 : 4)}`}
      className="h-auto w-full max-w-[400px]"
      role="presentation"
      aria-hidden="true"
    >
      {values.map((value, i) => {
        const x = i * (cell + gap);
        return (
          <g key={i}>
            <rect x={x} y={0} width={cell} height={cell} fill={FILL} stroke={STROKE} />
            <text
              x={x + cell / 2}
              y={cell / 2 + 4}
              textAnchor="middle"
              fontSize="12"
              fill={TEXT}
            >
              {String(value)}
            </text>
            {showIndices && (
              <text
                x={x + cell / 2}
                y={cell + 13}
                textAnchor="middle"
                fontSize="9"
                fill={MUTED}
              >
                {i}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function Grid({ rows }: { rows: string[][] }) {
  const cell = 32;
  const gap = 2;
  const width = rows[0].length * (cell + gap) - gap;
  const height = rows.length * (cell + gap) - gap;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-auto w-full max-w-[320px]"
      role="presentation"
      aria-hidden="true"
    >
      {rows.map((row, r) =>
        row.map((value, c) => (
          <g key={`${r}-${c}`}>
            <rect
              x={c * (cell + gap)}
              y={r * (cell + gap)}
              width={cell}
              height={cell}
              fill={FILL}
              stroke={STROKE}
            />
            <text
              x={c * (cell + gap) + cell / 2}
              y={r * (cell + gap) + cell / 2 + 4}
              textAnchor="middle"
              fontSize="12"
              fill={TEXT}
            >
              {value}
            </text>
          </g>
        )),
      )}
    </svg>
  );
}

function Linked({ values }: { values: string[] }) {
  const node = 36;
  const arrow = 22;
  const step = node + arrow;
  const total = values.length * step + 18;
  const mid = node / 2;

  return (
    <svg
      viewBox={`0 0 ${total} ${node + 4}`}
      className="h-auto w-full max-w-[420px]"
      role="presentation"
      aria-hidden="true"
    >
      {values.map((value, i) => {
        const x = i * step;
        return (
          <g key={i}>
            <rect
              x={x}
              y={2}
              width={node}
              height={node}
              rx={4}
              fill={FILL}
              stroke={STROKE}
            />
            <text
              x={x + mid}
              y={mid + 6}
              textAnchor="middle"
              fontSize="12"
              fill={TEXT}
            >
              {value}
            </text>
            <line
              x1={x + node}
              y1={mid + 2}
              x2={x + node + arrow - 5}
              y2={mid + 2}
              stroke={STROKE}
            />
            <polygon
              points={`${x + node + arrow - 5},${mid - 1} ${x + node + arrow},${mid + 2} ${
                x + node + arrow - 5
              },${mid + 5}`}
              fill={STROKE}
            />
          </g>
        );
      })}
      {/* The null terminator is part of what makes the picture a linked list. */}
      <text
        x={values.length * step + 2}
        y={mid + 6}
        fontSize="10"
        fill={MUTED}
      >
        null
      </text>
    </svg>
  );
}

export default function ProblemDiagram({ spec }: { spec: DiagramSpec }) {
  let figure: JSX.Element | null = null;

  if (spec.kind === "bars" && spec.values?.length) {
    figure = <Bars values={spec.values.map(Number)} label={spec.label} />;
  } else if (spec.kind === "grid" && spec.rows?.length) {
    figure = <Grid rows={spec.rows} />;
  } else if (spec.kind === "linked" && spec.values?.length) {
    figure = <Linked values={spec.values.map(String)} />;
  } else if (spec.kind === "string" && spec.values?.length) {
    // Characters are the cells; their positions are the indices.
    figure = <Cells values={spec.values} label={spec.label} />;
  } else if (spec.kind === "array" && spec.values?.length) {
    figure = <Cells values={spec.values} label={spec.label} />;
  }

  if (!figure) return null;

  return (
    <div className="min-w-0 overflow-x-auto rounded-[4px] border border-gray-800 bg-[#1A1A1A] px-3 py-3">
      {spec.label && (
        <div className="mb-2 font-sans text-[11.5px] text-gray-500">{spec.label}</div>
      )}
      {figure}
    </div>
  );
}
