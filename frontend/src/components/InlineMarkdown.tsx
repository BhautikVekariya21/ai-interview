/**
 * Minimal inline-markdown renderer for coding problem prose.
 *
 * Every problem in the bank writes its statement in light markdown — bold
 * (`**one solution**`) and code spans (`` `nums` ``) — and none of it is
 * fenced or nested. Rendering that raw put literal asterisks and backticks in
 * front of the candidate on all 1000 problems.
 *
 * This builds React nodes by tokenizing, so nothing is ever handed to
 * `dangerouslySetInnerHTML` and problem text cannot inject markup.
 */

/** `**bold**` or `` `code` `` — whichever comes first, left to right. */
const TOKEN = /(\*\*[^*]+\*\*|`[^`]+`)/g;

/** Split one line into bold / code / plain runs. */
function renderInline(line: string, keyPrefix: string) {
  return line.split(TOKEN).map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return (
        <strong key={key} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      // Kept sans-serif on purpose: the whole editor is sans by request, so a
      // code span is marked by its chip, not by a monospace face.
      return (
        <code
          key={key}
          className="rounded-[3px] bg-[#2A2A2A] px-1 py-0.5 text-[0.94em] text-emerald-300 break-all"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return <span key={key}>{part}</span>;
  });
}

/** A run of consecutive `- ` lines becomes one list; anything else is prose. */
type Block =
  | { kind: "prose"; lines: string[] }
  | { kind: "list"; items: string[] };

/**
 * Group a paragraph's lines into prose and bullet runs.
 *
 * Enriched statements carry `**Input**` headings followed by `- name — type`
 * lines. Rendering those as prose put a literal dash in front of every item and
 * collapsed the list onto one line, so bullet runs are split out here.
 */
function toBlocks(paragraph: string): Block[] {
  const blocks: Block[] = [];
  for (const line of paragraph.split("\n")) {
    const bullet = /^\s*[-*•]\s+(.*)$/.exec(line);
    const last = blocks[blocks.length - 1];
    if (bullet) {
      if (last?.kind === "list") last.items.push(bullet[1]);
      else blocks.push({ kind: "list", items: [bullet[1]] });
    } else {
      if (last?.kind === "prose") last.lines.push(line);
      else blocks.push({ kind: "prose", lines: [line] });
    }
  }
  return blocks;
}

export default function InlineMarkdown({
  text,
  className = "",
}: {
  text: string;
  className?: string;
}) {
  // Blank lines separate paragraphs; single newlines are soft breaks.
  const paragraphs = (text || "").split(/\n{2,}/).filter((p) => p.trim().length > 0);

  return (
    <div className={`space-y-3 font-sans ${className}`}>
      {paragraphs.map((para, pi) =>
        toBlocks(para).map((block, bi) =>
          block.kind === "list" ? (
            <ul key={`${pi}-${bi}`} className="space-y-1.5 font-sans min-w-0">
              {block.items.map((item, ii) => (
                <li key={ii} className="flex gap-2 font-sans min-w-0">
                  <span className="mt-[2px] shrink-0 font-sans text-gray-600">•</span>
                  <span className="min-w-0 font-sans break-words">
                    {renderInline(item, `${pi}-${bi}-${ii}`)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p key={`${pi}-${bi}`} className="font-sans break-words">
              {block.lines.map((line, li) => (
                <span key={li} className="font-sans">
                  {li > 0 && <br />}
                  {renderInline(line, `${pi}-${bi}-${li}`)}
                </span>
              ))}
            </p>
          ),
        ),
      )}
    </div>
  );
}
