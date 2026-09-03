/**
 * Game Tape share links.
 *
 * Replay documents are persisted server-side under an unguessable token (the
 * transcript is far too large for a self-contained URL), so the link is a
 * short hash fragment: `/replay#<token>`. The public ReplayPage reads the
 * token and fetches the document.
 */
export function replayShareUrl(token: string): string {
  return `${window.location.origin}/replay#${encodeURIComponent(token)}`;
}
