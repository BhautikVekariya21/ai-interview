import { useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import InterviewToolkitPage from "@/components/InterviewToolkitPage";
import MindMapTool from "@/components/MindMapTool";
import type { SavedMindMap } from "@/lib/mindMap";

vi.mock("@/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { plan: "free" },
  }),
}));

vi.mock("@xyflow/react", async () => {
  const React = await import("react");

  function MockReactFlow(props: {
    children?: React.ReactNode;
    nodes?: Array<{ id: string; data: { title: string } }>;
    onInit?: (instance: { fitView: () => void }) => void;
    onSelectionChange?: (params: { nodes: Array<{ id: string }>; edges: unknown[] }) => void;
  }) {
    React.useEffect(() => {
      props.onInit?.({
        fitView: () => undefined,
      });
    }, [props]);

    return (
      <div data-testid="react-flow-canvas">
        {props.nodes?.map((node) => (
          <button
            key={node.id}
            type="button"
            onClick={() => props.onSelectionChange?.({ nodes: [node], edges: [] })}
          >
            {node.data.title}
          </button>
        ))}
        {props.children}
      </div>
    );
  }

  function applyNodeChanges(
    changes: Array<{
      id: string;
      type: string;
      selected?: boolean;
      position?: { x: number; y: number };
    }>,
    nodes: Array<Record<string, unknown>>,
  ) {
    let nextNodes = [...nodes];

    for (const change of changes) {
      if (change.type === "remove") {
        nextNodes = nextNodes.filter((node) => node.id !== change.id);
      }
      if (change.type === "select") {
        nextNodes = nextNodes.map((node) =>
          node.id === change.id ? { ...node, selected: change.selected } : node,
        );
      }
      if (change.type === "position" && change.position) {
        nextNodes = nextNodes.map((node) =>
          node.id === change.id ? { ...node, position: change.position } : node,
        );
      }
    }

    return nextNodes;
  }

  function applyEdgeChanges(
    changes: Array<{ id: string; type: string; selected?: boolean }>,
    edges: Array<Record<string, unknown>>,
  ) {
    let nextEdges = [...edges];

    for (const change of changes) {
      if (change.type === "remove") {
        nextEdges = nextEdges.filter((edge) => edge.id !== change.id);
      }
      if (change.type === "select") {
        nextEdges = nextEdges.map((edge) =>
          edge.id === change.id ? { ...edge, selected: change.selected } : edge,
        );
      }
    }

    return nextEdges;
  }

  return {
    __esModule: true,
    default: MockReactFlow,
    ReactFlow: MockReactFlow,
    Background: () => null,
    Controls: () => null,
    MiniMap: () => null,
    Handle: () => null,
    Position: { Left: "left", Right: "right" },
    BackgroundVariant: { Dots: "dots" },
    MarkerType: { ArrowClosed: "arrowclosed" },
    addEdge: (connection: Record<string, unknown>, edges: Record<string, unknown>[]) => [
      ...edges,
      connection,
    ],
    reconnectEdge: (
      oldEdge: Record<string, unknown>,
      connection: Record<string, unknown>,
      edges: Record<string, unknown>[],
    ) => edges.map((edge) => (edge.id === oldEdge.id ? { ...edge, ...connection } : edge)),
    applyNodeChanges,
    applyEdgeChanges,
  };
});

function MindMapHarness() {
  const [mindMaps, setMindMaps] = useState<SavedMindMap[]>([]);
  const [activeMindMapId, setActiveMindMapId] = useState<string | undefined>();

  return (
    <div>
      <MindMapTool
        mindMaps={mindMaps}
        activeMindMapId={activeMindMapId}
        onChange={(nextMaps, nextActiveId) => {
          setMindMaps(nextMaps);
          setActiveMindMapId(nextActiveId);
        }}
      />
      <pre data-testid="mindmap-state">
        {JSON.stringify({ mindMaps, activeMindMapId })}
      </pre>
    </div>
  );
}

describe("MindMapTool", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the Mind Map tab in Interview Toolkit for free users", () => {
    render(
      <InterviewToolkitPage
        mindMaps={[]}
        activeMindMapId={undefined}
        onMindMapsChange={() => undefined}
      />,
    );

    expect(screen.getByRole("button", { name: /mind map/i })).toBeInTheDocument();
  });

  it("creates a template map, adds it to the library, and opens it", async () => {
    render(<MindMapHarness />);

    fireEvent.click(screen.getByRole("button", { name: /create your first map/i }));
    fireEvent.click(screen.getByRole("button", { name: /star story/i }));

    expect(await screen.findByDisplayValue("Situation")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /STAR Story Map STAR Story/i }),
    ).toBeInTheDocument();

    const snapshot = JSON.parse(screen.getByTestId("mindmap-state").textContent || "{}");
    expect(snapshot.mindMaps).toHaveLength(1);
    expect(snapshot.mindMaps[0].templateId).toBe("star-story");
    expect(snapshot.activeMindMapId).toBe(snapshot.mindMaps[0].id);
  });

  it("renames and deletes a map through synced state updates", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<MindMapHarness />);

    fireEvent.click(screen.getByRole("button", { name: /create your first map/i }));
    fireEvent.click(screen.getByRole("button", { name: /star story/i }));

    fireEvent.click(screen.getByRole("button", { name: /rename star story map/i }));
    const nameInput = await screen.findByLabelText("Map name");
    fireEvent.change(nameInput, { target: { value: "Behavioral Wins" } });
    fireEvent.blur(nameInput);

    await waitFor(() =>
      expect(screen.getByTestId("mindmap-state")).toHaveTextContent("Behavioral Wins"),
    );

    fireEvent.click(screen.getByRole("button", { name: /delete behavioral wins/i }));

    await waitFor(() => {
      const snapshot = JSON.parse(screen.getByTestId("mindmap-state").textContent || "{}");
      expect(snapshot.mindMaps).toHaveLength(0);
      expect(snapshot.activeMindMapId).toBeUndefined();
    });

    expect(confirmSpy).toHaveBeenCalled();
  });

  it("updates the active node text through the inspector", async () => {
    render(<MindMapHarness />);

    fireEvent.click(screen.getByRole("button", { name: /create your first map/i }));
    fireEvent.click(screen.getByRole("button", { name: /star story/i }));

    const titleInput = await screen.findByLabelText(/node title/i);
    const noteInput = screen.getByLabelText(/node notes/i);

    fireEvent.change(titleInput, { target: { value: "Context" } });
    fireEvent.change(noteInput, { target: { value: "Frame the stakes in one sentence." } });

    await waitFor(() => {
      const snapshot = JSON.parse(screen.getByTestId("mindmap-state").textContent || "{}");
      expect(snapshot.mindMaps[0].nodes[0].data.title).toBe("Context");
      expect(snapshot.mindMaps[0].nodes[0].data.note).toBe(
        "Frame the stakes in one sentence.",
      );
    });
  });

  it("switches between saved maps and restores the correct graph", async () => {
    render(<MindMapHarness />);

    fireEvent.click(screen.getByRole("button", { name: /create your first map/i }));
    fireEvent.click(screen.getByRole("button", { name: /star story/i }));

    fireEvent.click(screen.getByRole("button", { name: /new map/i }));
    fireEvent.click(screen.getByRole("button", { name: /system design/i }));

    expect(await screen.findByDisplayValue("Problem")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /STAR Story Map STAR Story/i }),
    );
    expect(await screen.findByDisplayValue("Situation")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /System Design Map System Design/i }),
    );
    expect(await screen.findByDisplayValue("Problem")).toBeInTheDocument();
  });
});
