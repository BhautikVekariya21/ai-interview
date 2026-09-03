/**
 * One id for one interview sitting.
 *
 * The interview and the code sandbox are separate routes, so without a shared
 * id a candidate's coding submissions could not be attributed to the interview
 * they were made during — and a second interview would read as a continuation
 * of the first.
 *
 * Stored in `sessionStorage`: it survives a reload and route changes within the
 * tab, but a new tab or a new sitting mints a fresh id. A `?session=` query
 * parameter overrides it so an interviewer can hand out a specific id.
 */

const STORAGE_KEY = "ai-interview:session-id";

function mintId(): string {
  const cryptoObj = globalThis.crypto;
  if (cryptoObj?.randomUUID) return `s_${cryptoObj.randomUUID()}`;
  return `s_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36)}`;
}

function readStorage(): string | null {
  try {
    return window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    // Private browsing or a blocked storage partition — fall back to a fresh id.
    return null;
  }
}

function writeStorage(id: string): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, id);
  } catch {
    /* non-fatal: the id still holds for this page's lifetime */
  }
}

let inMemoryId: string | null = null;

/** The current interview session id, creating one on first use. */
export function getInterviewSessionId(): string {
  const fromQuery = new URLSearchParams(window.location.search).get("session");
  if (fromQuery) {
    writeStorage(fromQuery);
    inMemoryId = fromQuery;
    return fromQuery;
  }

  const stored = readStorage();
  if (stored) {
    inMemoryId = stored;
    return stored;
  }

  if (!inMemoryId) inMemoryId = mintId();
  writeStorage(inMemoryId);
  return inMemoryId;
}

/** Start a new sitting — call when an interview begins, not when one resumes. */
export function resetInterviewSessionId(): string {
  inMemoryId = mintId();
  writeStorage(inMemoryId);
  return inMemoryId;
}
