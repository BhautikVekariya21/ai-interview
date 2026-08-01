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

import type {
  DiagramSpec,
  SchemaTableSpec,
} from "@/lib/api";

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
  values: Array<string | number | null>;
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

interface TreeNode {
  value: string | number;
  /** A `null` in the encoding: a hollow placeholder with no value of its own. */
  isNull: boolean;
  left: TreeNode | null;
  right: TreeNode | null;
  x: number;
  depth: number;
}

/** Rebuild a binary tree from its level-order encoding.

    The bank stores trees the way LeetCode does: a flat BFS array read in queue
    order — each node consumes two values for its children, and `null` marks a
    missing child. The queue reading matters for skewed trees: with slot
    indexing (`2i+1`/`2i+2`), `[1,null,2,3]` would orphan the 3 under the null
    at index 1, whereas the queue reading makes it 2's left child — exactly
    how LeetCode's own deserializer reads the same array. A `null` becomes a
    hollow placeholder node so the layout can sit it on the column where a
    real child would land. */
export function buildTree(
  values: Array<string | number | null>,
): TreeNode | null {
  if (!values.length || values[0] === null || values[0] === undefined) {
    return null;
  }

  const mk = (v: string | number | null): TreeNode => ({
    value: v === null || v === undefined ? 0 : v,
    isNull: v === null || v === undefined,
    left: null,
    right: null,
    x: 0,
    depth: 0,
  });

  const root = mk(values[0]);
  const queue: TreeNode[] = [root];
  let i = 1;
  while (queue.length && i < values.length) {
    const node = queue.shift();
    if (!node || node.isNull) continue;
    node.left = mk(values[i++]);
    if (!node.left.isNull) queue.push(node.left);
    if (i < values.length) {
      node.right = mk(values[i++]);
      if (!node.right.isNull) queue.push(node.right);
    }
  }
  return root;
}

/** Number of column units a subtree spans (a node or placeholder counts as one). */
function subtreeWidth(node: TreeNode | null): number {
  if (!node) return 0;
  return 1 + subtreeWidth(node.left) + subtreeWidth(node.right);
}

/** Give every node a column so each parent sits centered over its children. */
function assignColumns(node: TreeNode | null, offset: number, depth: number): void {
  if (!node) return;
  const leftWidth = subtreeWidth(node.left);
  node.x = offset + leftWidth;
  node.depth = depth;
  assignColumns(node.left, offset, depth + 1);
  assignColumns(node.right, offset + leftWidth + 1, depth + 1);
}

function Tree({ values }: { values: Array<string | number | null> }) {
  const root = buildTree(values);
  if (!root) return null;
  assignColumns(root, 0, 0);

  const H = 44; // horizontal spacing between columns
  const V = 52; // vertical spacing between depths
  const R = 15; // node radius
  const PAD = 22;

  const nodes: Array<{ cx: number; cy: number; value: string | number }> = [];
  const edges: Array<{ x1: number; y1: number; x2: number; y2: number }> = [];
  const nulls: Array<{ cx: number; cy: number }> = [];
  let maxCol = 0;
  let maxDepth = 0;

  const visit = (node: TreeNode, px: number | null, py: number | null) => {
    const cx = PAD + node.x * H;
    const cy = PAD + node.depth * V;
    maxCol = Math.max(maxCol, node.x);
    maxDepth = Math.max(maxDepth, node.depth);
    if (node.isNull) {
      // A missing child is a hollow placeholder on its own column — exactly
      // where a real child would be drawn, so the picture matches the array.
      nulls.push({ cx, cy });
      return;
    }
    nodes.push({ cx, cy, value: node.value });
    if (px !== null && py !== null) {
      edges.push({ x1: px, y1: py + R, x2: cx, y2: cy - R });
    }
    visit(node.left, cx, cy);
    visit(node.right, cx, cy);
  };
  visit(root, null, null);

  const width = PAD * 2 + (maxCol + 1) * H;
  const height = PAD * 2 + (maxDepth + 1) * V;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-auto w-full max-w-[440px]"
      role="presentation"
      aria-hidden="true"
    >
      {edges.map((e, i) => (
        <line
          key={`e${i}`}
          x1={e.x1}
          y1={e.y1}
          x2={e.x2}
          y2={e.y2}
          stroke={STROKE}
          strokeWidth={1.5}
        />
      ))}
      {nulls.map((n, i) => (
        <circle
          key={`n${i}`}
          cx={n.cx}
          cy={n.cy}
          r={7}
          fill="none"
          stroke={MUTED}
          strokeDasharray="2 2"
        />
      ))}
      {nodes.map((n, i) => (
        <g key={`t${i}`}>
          <circle cx={n.cx} cy={n.cy} r={R} fill={FILL} stroke={STROKE} />
          <text x={n.cx} y={n.cy + 4} textAnchor="middle" fontSize="11" fill={TEXT}>
            {String(n.value)}
          </text>
        </g>
      ))}
    </svg>
  );
}

const KEY_COLORS: Record<string, string> = {
  PK: "text-amber-400 border-amber-500/40 bg-amber-950/60",
  UQ: "text-sky-400 border-sky-500/40 bg-sky-950/60",
  FK: "text-violet-400 border-violet-500/40 bg-violet-950/60",
  KEY: "text-gray-400 border-gray-600 bg-[#252525]",
};

/**
 * A database schema: one card per table, its columns with type and key badges,
 * and up to three seeded rows so the candidate can see the data the query runs
 * against. Rendered as real DOM, never a markup string — the column and row
 * values come from the backend spec, so they cannot inject anything.
 */
function Schema({ tables }: { tables: SchemaTableSpec[] }) {
  return (
    <div className="flex flex-col gap-3">
      {tables.map((table) => (
        <div
          key={table.name}
          className="overflow-hidden rounded-[4px] border border-gray-700 bg-[#141414]"
        >
          <div className="flex items-center justify-between border-b border-gray-700 bg-[#1F1F1F] px-3 py-1.5">
            <span className="font-sans text-[12px] font-bold text-gray-200">
              {table.name}
            </span>
            <span className="font-sans text-[9px] uppercase tracking-wider text-gray-500">
              table
            </span>
          </div>

          <div className="px-3 py-2">
            <div className="flex flex-wrap gap-1.5">
              {table.columns.map((col) => (
                <span
                  key={col.name}
                  className="inline-flex items-center gap-1.5 rounded-[3px] border border-gray-800 bg-[#1A1A1A] px-1.5 py-0.5 font-sans text-[10.5px]"
                >
                  <span className="font-semibold text-gray-100">{col.name}</span>
                  <span className="text-gray-500">{col.type}</span>
                  {col.key && (
                    <span
                      className={`rounded-[2px] border px-1 font-sans text-[8.5px] font-bold ${
                        KEY_COLORS[col.key] ?? KEY_COLORS.KEY
                      }`}
                    >
                      {col.key}
                    </span>
                  )}
                </span>
              ))}
            </div>

            {table.rows && table.rows.length > 0 && (
              <div className="mt-2 overflow-x-auto">
                <table className="w-full border-collapse font-sans text-[10px]">
                  <tbody>
                    {table.rows.map((row, r) => (
                      <tr key={r} className="border-t border-gray-800 first:border-t-0">
                        {row.map((cell, c) => (
                          <td
                            key={c}
                            className="max-w-[120px] truncate px-1.5 py-0.5 text-left align-top text-gray-400"
                            title={cell === null ? "NULL" : String(cell)}
                          >
                            {cell === null ? (
                              <span className="italic text-gray-600">NULL</span>
                            ) : (
                              <span className="text-gray-300">{String(cell)}</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
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
  } else if (spec.kind === "tree" && spec.values?.length) {
    figure = <Tree values={spec.values} />;
  } else if (spec.kind === "schema" && spec.tables?.length) {
    figure = <Schema tables={spec.tables} />;
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
