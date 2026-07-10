import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { useSessionStorage } from "@/hooks/useSessionStorage";
import { createMindMapFromTemplate } from "@/lib/mindMap";
import { getReferenceMindMaps } from "@/lib/referenceMindMaps";

const mocks = vi.hoisted(() => ({
  getStoredAuthToken: vi.fn(),
  loadCloudSession: vi.fn(),
  saveCloudSession: vi.fn(),
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}));

const {
  getStoredAuthToken,
  loadCloudSession,
  saveCloudSession,
  getItem,
  setItem,
  removeItem,
} = mocks;

vi.mock("@/lib/auth", () => ({
  getStoredAuthToken: mocks.getStoredAuthToken,
}));

vi.mock("@/lib/api", () => ({
  loadCloudSession: mocks.loadCloudSession,
  saveCloudSession: mocks.saveCloudSession,
}));

vi.mock("@/lib/indexedDB", () => ({
  getItem: mocks.getItem,
  setItem: mocks.setItem,
  removeItem: mocks.removeItem,
}));

function SessionHarness() {
  const { session, updateSession } = useSessionStorage();

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          const nextMap = createMindMapFromTemplate("system-design", session.mindMaps);
          updateSession({
            mindMaps: [...session.mindMaps, nextMap],
            activeMindMapId: nextMap.id,
          });
        }}
      >
        add mind map
      </button>
      <pre data-testid="session-json">{JSON.stringify(session)}</pre>
    </div>
  );
}

describe("useSessionStorage mind maps", () => {
  beforeEach(() => {
    getStoredAuthToken.mockReturnValue(null);
    loadCloudSession.mockResolvedValue({ session: null });
    saveCloudSession.mockResolvedValue({});
    getItem.mockResolvedValue(null);
    setItem.mockResolvedValue(undefined);
    removeItem.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("rehydrates the saved mind map library and active map from the session snapshot", async () => {
    const storedMap = createMindMapFromTemplate("coding-problem", []);
    getItem.mockResolvedValueOnce({
      activePage: "interview-toolkit",
      candidateName: "Jordan",
      generatedQuestions: [],
      mindMaps: [storedMap],
      activeMindMapId: storedMap.id,
    });

    render(<SessionHarness />);

    await waitFor(() =>
      expect(screen.getByTestId("session-json")).toHaveTextContent('"candidateName":"Jordan"'),
    );

    const snapshot = JSON.parse(screen.getByTestId("session-json").textContent || "{}");
    expect(snapshot.mindMaps).toHaveLength(1);
    expect(snapshot.mindMaps[0].templateId).toBe("coding-problem");
    expect(snapshot.activeMindMapId).toBe(storedMap.id);
  });

  it("preserves unrelated session fields when mind maps update and syncs the full snapshot", async () => {
    getItem.mockResolvedValueOnce({
      activePage: "interview-toolkit",
      candidateName: "Morgan",
      generatedQuestions: [
        { id: 1, text: "Explain debounce", category: "frontend", difficulty: "medium" },
      ],
      mindMaps: [],
    });

    render(<SessionHarness />);

    await waitFor(() =>
      expect(screen.getByTestId("session-json")).toHaveTextContent('"candidateName":"Morgan"'),
    );

    // An empty stored mindMaps array is seeded with reference/example mind
    // maps on load, so the count after adding one is refCount + 1.
    const expectedCount = getReferenceMindMaps().length + 1;

    fireEvent.click(screen.getByRole("button", { name: /add mind map/i }));

    await waitFor(() => {
      const snapshot = JSON.parse(screen.getByTestId("session-json").textContent || "{}");
      expect(snapshot.mindMaps).toHaveLength(expectedCount);
      expect(snapshot.candidateName).toBe("Morgan");
      expect(snapshot.generatedQuestions).toHaveLength(1);
    });

    await waitFor(() => {
      expect(setItem).toHaveBeenCalledWith(
        "interviewer_session",
        expect.objectContaining({
          candidateName: "Morgan",
          mindMaps: expect.arrayContaining([
            expect.objectContaining({ templateId: "system-design" }),
          ]),
        }),
      );
      expect(saveCloudSession).toHaveBeenCalled();
    }, { timeout: 2000 });

    const latestCloudPayload = saveCloudSession.mock.calls.at(-1)?.[1];
    expect(latestCloudPayload).toEqual(
      expect.objectContaining({
        candidateName: "Morgan",
        generatedQuestions: [
          { id: 1, text: "Explain debounce", category: "frontend", difficulty: "medium" },
        ],
        mindMaps: expect.arrayContaining([
          expect.objectContaining({ templateId: "system-design" }),
        ]),
      }),
    );
  });
});
