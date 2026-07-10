import { useEffect, useRef, useState, useMemo } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Handle,
  Position,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  reconnectEdge,
  MarkerType,
  type Connection,
  type EdgeChange,
  type NodeChange,
  type NodeProps,
  type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  FilePlus2,
  GitBranchPlus,
  Map,
  Pencil,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  MIND_MAP_TEMPLATES,
  createMindMapFromTemplate,
  getMindMapTemplate,
  getRootMindMapNodeId,
  type MindMapEdge,
  type MindMapNode,
  type MindMapTemplateId,
  type SavedMindMap,
} from "@/lib/mindMap";
import { getReferenceMindMaps } from "@/lib/referenceMindMaps";
import { generateGeniusMindMap } from "@/lib/api";

interface MindMapToolProps {
  mindMaps: SavedMindMap[];
  activeMindMapId?: string;
  onChange: (mindMaps: SavedMindMap[], activeMindMapId?: string) => void;
}

function useIsDarkMode(): boolean {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === "undefined") return true;
    const hasDarkClass = document.documentElement.classList.contains("dark");
    if (hasDarkClass) return true;
    const savedTheme = localStorage.getItem("theme");
    return savedTheme === "dark" || !savedTheme;
  });
  useEffect(() => {
    const target = document.documentElement;
    const observer = new MutationObserver(() => {
      setIsDark(target.classList.contains("dark"));
    });
    observer.observe(target, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);
  return isDark;
}

function MindMapCanvasNode({ data, selected }: NodeProps<MindMapNode>) {
  return (
    <div
      className={`min-w-[220px] max-w-[260px] rounded-2xl border bg-card px-4 py-3 shadow-sm transition-all ${
        selected
          ? "border-primary shadow-[0_4px_20px_rgba(var(--primary),0.2)]"
          : "border-border hover:border-primary/30"
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-2 !border-card !bg-muted-foreground"
      />
      <div className="space-y-1.5">
        <div className="text-sm font-semibold text-foreground">
          {data.title.trim() || "Untitled node"}
        </div>
        <div className="text-xs leading-relaxed text-muted-foreground">
          {data.note.trim() || "Add a note for prompts, examples, or talking points."}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-2 !border-card !bg-primary"
      />
    </div>
  );
}

const nodeTypes = {
  mindmap: MindMapCanvasNode,
};

const createRuntimeId = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

function getMeaningfulNodeChange(changes: NodeChange<MindMapNode>[]) {
  return changes.some((change) => change.type !== "select" && change.type !== "dimensions");
}

function getMeaningfulEdgeChange(changes: EdgeChange<MindMapEdge>[]) {
  return changes.some((change) => change.type !== "select");
}

export default function MindMapTool({
  mindMaps,
  activeMindMapId,
  onChange,
}: MindMapToolProps) {
  const [templatePickerOpen, setTemplatePickerOpen] = useState(false);
  const [editingMapId, setEditingMapId] = useState<string | null>(null);
  const [geniusPrompt, setGeniusPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [editingMapName, setEditingMapName] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const flowRef = useRef<ReactFlowInstance<MindMapNode, MindMapEdge> | null>(null);
  const isDarkMode = useIsDarkMode();

  const activeMap =
    mindMaps.find((map) => map.id === activeMindMapId) ?? mindMaps[0] ?? null;
  const selectedNode =
    activeMap?.nodes.find((node) => node.id === selectedNodeId) ?? null;

  const syncedNodes = useMemo(() => {
    if (!activeMap) return [];
    return activeMap.nodes.map((node) => {
      const isSelected = node.id === selectedNodeId;
      if (!!node.selected === isSelected) {
        return node;
      }
      return { ...node, selected: isSelected };
    });
  }, [activeMap?.nodes, selectedNodeId]);

  useEffect(() => {
    if (!mindMaps.length) {
      if (activeMindMapId) {
        onChange([], undefined);
      }
      return;
    }

    if (!activeMindMapId || !mindMaps.some((map) => map.id === activeMindMapId)) {
      onChange(mindMaps, mindMaps[0].id);
    }
  }, [activeMindMapId, mindMaps, onChange]);

  useEffect(() => {
    if (!activeMap) {
      setSelectedNodeId(null);
      return;
    }

    if (selectedNodeId && activeMap.nodes.some((node) => node.id === selectedNodeId)) {
      return;
    }

    setSelectedNodeId(getRootMindMapNodeId(activeMap));
  }, [activeMap, selectedNodeId]);

  useEffect(() => {
    if (!activeMap || !flowRef.current) return;

    const frame = window.requestAnimationFrame(() => {
      void flowRef.current?.fitView({ duration: 250, padding: 0.2 });
    });

    return () => window.cancelAnimationFrame(frame);
  }, [activeMap?.id]);

  function updateActiveMap(
    updater: (map: SavedMindMap) => SavedMindMap,
    nextActiveId: string | undefined = activeMap?.id,
  ) {
    if (!activeMap) return;

    const nextMaps = mindMaps.map((map) =>
      map.id === activeMap.id ? updater(map) : map,
    );
    onChange(nextMaps, nextActiveId);
  }

  function openRename(map: SavedMindMap) {
    setEditingMapId(map.id);
    setEditingMapName(map.name);
  }

  function commitRename(mapId: string) {
    const trimmedName = editingMapName.trim();
    const original = mindMaps.find((map) => map.id === mapId);
    if (!original) {
      setEditingMapId(null);
      setEditingMapName("");
      return;
    }

    const nextName = trimmedName || original.name;
    const nextMaps = mindMaps.map((map) =>
      map.id === mapId
        ? {
            ...map,
            name: nextName,
            updatedAt: nextName === map.name ? map.updatedAt : Date.now(),
          }
        : map,
    );

    onChange(nextMaps, activeMap?.id);
    setEditingMapId(null);
    setEditingMapName("");
  }

  function handleCreateMap(templateId: MindMapTemplateId) {
    const nextMap = createMindMapFromTemplate(templateId, mindMaps);
    const nextMaps = [...mindMaps, nextMap];
    onChange(nextMaps, nextMap.id);
    setSelectedNodeId(getRootMindMapNodeId(nextMap));
    setTemplatePickerOpen(false);
    setEditingMapId(null);
    setEditingMapName("");
  }

  async function handleGeniusGenerate() {
    if (!geniusPrompt.trim()) return;
    setIsGenerating(true);
    try {
      const response = await generateGeniusMindMap(geniusPrompt);
      if (response && response.success) {
        const nextMap: SavedMindMap = {
          id: createRuntimeId("map"),
          name: geniusPrompt.trim(),
          templateId: "genius-mind",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          nodes: response.nodes.map(n => ({
            id: n.id,
            type: "mindmap",
            position: { x: n.x, y: n.y },
            data: { title: n.title, note: n.note }
          })),
          edges: response.edges.map(e => ({
            id: createRuntimeId("edge"),
            source: e.source,
            target: e.target,
            type: "smoothstep",
            markerEnd: { type: MarkerType.ArrowClosed },
          }))
        };
        const nextMaps = [...mindMaps, nextMap];
        onChange(nextMaps, nextMap.id);
        setSelectedNodeId(nextMap.nodes[0]?.id ?? null);
        setTemplatePickerOpen(false);
        setEditingMapId(null);
        setEditingMapName("");
        setGeniusPrompt("");
      }
    } catch (err) {
      console.error("Genius map generation failed:", err);
      alert("Genius map generation failed. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  }

  function handleDeleteMap(mapId: string) {
    const map = mindMaps.find((candidate) => candidate.id === mapId);
    if (!map) return;

    const confirmed = window.confirm(`Delete "${map.name}"? This cannot be undone.`);
    if (!confirmed) return;

    const nextMaps = mindMaps.filter((candidate) => candidate.id !== mapId);
    const nextActiveId =
      activeMap?.id === mapId ? nextMaps[0]?.id : activeMindMapId ?? nextMaps[0]?.id;

    onChange(nextMaps, nextActiveId);

    if (activeMap?.id === mapId) {
      const nextSelectedMap = nextMaps.find((candidate) => candidate.id === nextActiveId);
      setSelectedNodeId(nextSelectedMap ? getRootMindMapNodeId(nextSelectedMap) : null);
    }
  }

  function handleNodesChange(changes: NodeChange<MindMapNode>[]) {
    if (!activeMap) return;

    const shouldTouch = getMeaningfulNodeChange(changes);
    const nextNodes = applyNodeChanges(changes, syncedNodes);

    updateActiveMap((map) => ({
      ...map,
      nodes: nextNodes,
      updatedAt: shouldTouch ? Date.now() : map.updatedAt,
    }));
  }

  function handleEdgesChange(changes: EdgeChange<MindMapEdge>[]) {
    if (!activeMap) return;

    const shouldTouch = getMeaningfulEdgeChange(changes);
    const nextEdges = applyEdgeChanges(changes, activeMap.edges);

    updateActiveMap((map) => ({
      ...map,
      edges: nextEdges,
      updatedAt: shouldTouch ? Date.now() : map.updatedAt,
    }));
  }

  function handleConnect(connection: Connection) {
    if (!activeMap) return;

    updateActiveMap((map) => ({
      ...map,
      edges: addEdge(
        {
          ...connection,
          id: createRuntimeId("edge"),
          type: "smoothstep",
          markerEnd: { type: MarkerType.ArrowClosed },
        },
        map.edges,
      ),
      updatedAt: Date.now(),
    }));
  }

  function handleReconnect(oldEdge: MindMapEdge, connection: Connection) {
    if (!activeMap) return;

    updateActiveMap((map) => ({
      ...map,
      edges: reconnectEdge(
        oldEdge,
        {
          ...connection,
          type: "smoothstep",
          markerEnd: { type: MarkerType.ArrowClosed },
        },
        map.edges,
      ),
      updatedAt: Date.now(),
    }));
  }

  function handleSelectedNodeChange(field: "title" | "note", value: string) {
    if (!activeMap || !selectedNode) return;

    updateActiveMap((map) => ({
      ...map,
      nodes: map.nodes.map((node) =>
        node.id === selectedNode.id
          ? {
              ...node,
              data: {
                ...node.data,
                [field]: value,
              },
            }
          : node,
      ),
      updatedAt: Date.now(),
    }));
  }

  function handleAddChildNode() {
    if (!activeMap || !selectedNode) return;

    const siblingCount = activeMap.edges.filter(
      (edge) => edge.source === selectedNode.id,
    ).length;
    const childNodeId = createRuntimeId("node");
    const childNode: MindMapNode = {
      id: childNodeId,
      type: "mindmap",
      position: {
        x: selectedNode.position.x + 260,
        y: selectedNode.position.y + siblingCount * 120 - 40,
      },
      data: {
        title: "New node",
        note: "Capture examples, metrics, or follow-up prompts.",
      },
    };
    const childEdge: MindMapEdge = {
      id: createRuntimeId("edge"),
      source: selectedNode.id,
      target: childNodeId,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed },
    };

    updateActiveMap((map) => ({
      ...map,
      nodes: [...map.nodes, childNode],
      edges: [...map.edges, childEdge],
      updatedAt: Date.now(),
    }));
    setSelectedNodeId(childNodeId);
  }

  function handleDeleteSelectedNode() {
    if (!activeMap || !selectedNode || activeMap.nodes.length <= 1) return;

    const nextNodes = activeMap.nodes.filter((node) => node.id !== selectedNode.id);
    const nextEdges = activeMap.edges.filter(
      (edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id,
    );
    const nextSelectedId = nextNodes[0]?.id ?? null;

    updateActiveMap((map) => ({
      ...map,
      nodes: nextNodes,
      edges: nextEdges,
      updatedAt: Date.now(),
    }));
    setSelectedNodeId(nextSelectedId);
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      <div className="grid min-h-[760px] grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[280px_minmax(0,1fr)_320px]">
        <aside className="border-b border-border bg-card p-4 lg:border-b-0 lg:border-r">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-foreground">Mind Maps</div>
              <div className="text-xs text-muted-foreground">
                {mindMaps.length} saved map{mindMaps.length === 1 ? "" : "s"}
              </div>
            </div>
            <Button
              size="sm"
              className="h-8 px-3"
              onClick={() => setTemplatePickerOpen(true)}
            >
              <FilePlus2 className="h-4 w-4" />
              New map
            </Button>
          </div>

          <div className="space-y-2">
            {mindMaps.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border bg-muted/20 px-4 py-5 space-y-3">
                <div className="text-sm text-muted-foreground">
                  Start from a structured template, then drag, connect, and refine your ideas.
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => {
                    const refs = getReferenceMindMaps();
                    onChange(refs, refs[0].id);
                  }}
                >
                  <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                  Load Examples
                </Button>
              </div>
            ) : (
              mindMaps.map((map) => {
                const template = getMindMapTemplate(map.templateId);
                const isActive = activeMap?.id === map.id;
                const isEditing = editingMapId === map.id;

                return (
                  <div
                    key={map.id}
                    className={`rounded-2xl border p-3 transition-colors ${
                      isActive
                        ? "border-primary/30 bg-primary/5"
                        : "border-border bg-background hover:border-primary/20"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="min-w-0 flex-1">
                        {isEditing ? (
                          <input
                            aria-label="Map name"
                            autoFocus
                            value={editingMapName}
                            onChange={(event) => setEditingMapName(event.target.value)}
                            onBlur={() => commitRename(map.id)}
                            onKeyDown={(event) => {
                              if (event.key === "Enter") {
                                commitRename(map.id);
                              }
                              if (event.key === "Escape") {
                                setEditingMapId(null);
                                setEditingMapName("");
                              }
                            }}
                            className="w-full rounded-lg border border-border bg-background px-2.5 py-2 text-sm font-medium text-foreground outline-none ring-0 transition focus:border-primary"
                          />
                        ) : (
                          <button
                            type="button"
                            onClick={() => onChange(mindMaps, map.id)}
                            className="w-full text-left"
                          >
                            <div className="truncate text-sm font-semibold text-foreground">
                              {map.name}
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">
                              {template.label} · {map.nodes.length} nodes
                            </div>
                          </button>
                        )}
                      </div>
                      <button
                        type="button"
                        aria-label={`Rename ${map.name}`}
                        onClick={() => openRename(map)}
                        className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        aria-label={`Delete ${map.name}`}
                        onClick={() => handleDeleteMap(map.id)}
                        className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        <section className="flex min-h-[540px] flex-col bg-background">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-card/70 px-4 py-3 backdrop-blur">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-foreground">
                {activeMap ? activeMap.name : "Interview Mind Map"}
              </div>
              <div className="text-xs text-muted-foreground">
                {activeMap
                  ? `${getMindMapTemplate(activeMap.templateId).label} template`
                  : "Create a map from one of the interview starter templates."}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8"
                onClick={handleAddChildNode}
                disabled={!selectedNode}
              >
                <GitBranchPlus className="h-4 w-4" />
                Add child
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-8"
                onClick={handleDeleteSelectedNode}
                disabled={!selectedNode || activeMap?.nodes.length === 1}
              >
                <Trash2 className="h-4 w-4" />
                Delete node
              </Button>
            </div>
          </div>

          <div className="relative flex-1">
            {!activeMap ? (
              <div className="flex h-full flex-col items-center justify-center px-6 py-12 text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-muted shadow-sm">
                  <Map className="h-8 w-8 text-foreground/80" />
                </div>
                <h3 className="text-xl font-semibold text-foreground">
                  Build your first interview map
                </h3>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                  Choose a starter template for behavioral stories, system design,
                  coding walkthroughs, or company prep. Everything stays editable
                  after creation.
                </p>
                <Button
                  className="mt-5"
                  onClick={() => setTemplatePickerOpen(true)}
                >
                  <Sparkles className="h-4 w-4" />
                  Create your first map
                </Button>
              </div>
            ) : (
              <div className="absolute inset-0">
                <ReactFlow<MindMapNode, MindMapEdge>
                  nodes={syncedNodes}
                  edges={activeMap.edges}
                  nodeTypes={nodeTypes}
                  onInit={(instance) => {
                    flowRef.current = instance;
                  }}
                  onNodesChange={handleNodesChange}
                  onEdgesChange={handleEdgesChange}
                  onConnect={handleConnect}
                  onReconnect={handleReconnect}
                  onSelectionChange={({ nodes }) => {
                    setSelectedNodeId(nodes[0]?.id ?? null);
                  }}
                  onPaneClick={() => setSelectedNodeId(null)}
                  fitView
                  fitViewOptions={{ padding: 0.2 }}
                  edgesReconnectable
                  defaultEdgeOptions={{
                    type: "smoothstep",
                    markerEnd: { type: MarkerType.ArrowClosed },
                  }}
                  className="bg-background/40"
                >
                  <Background
                    variant={BackgroundVariant.Dots}
                    gap={18}
                    size={1}
                    color={isDarkMode ? "#334155" : "#CBD5E1"}
                  />
                  <MiniMap
                    pannable
                    zoomable
                    nodeColor={(node) =>
                      node.id === selectedNodeId ? "var(--primary)" : (isDarkMode ? "#334155" : "#CBD5E1")
                    }
                    maskColor={isDarkMode ? "rgba(0, 0, 0, 0.4)" : "rgba(255, 255, 255, 0.4)"}
                  />
                  <Controls />
                </ReactFlow>
              </div>
            )}

            {templatePickerOpen && (
              <div className="absolute inset-0 z-10 overflow-y-auto bg-background/95 p-6 backdrop-blur-sm">
                <div className="mx-auto max-w-4xl">
                  <div className="mb-4 flex items-start justify-between gap-4">
                    <div>
                      <div className="text-lg font-semibold text-foreground">
                        Choose a starter template
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Start structured, then drag and edit everything freely.
                      </p>
                    </div>
                    <button
                      type="button"
                      aria-label="Close template picker"
                      onClick={() => setTemplatePickerOpen(false)}
                      className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {/* FREE GENIUS AI GENERATION */}
                  <div className="mb-8 rounded-3xl border border-primary/20 bg-primary/5 p-5 shadow-sm">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-semibold text-primary">Genius Mind (Free)</h3>
                    </div>
                    <p className="mb-4 text-sm text-foreground/80">Type any topic and our Genius AI will instantly generate a cohesive mind map. Blow your mind within seconds!</p>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <input 
                        value={geniusPrompt}
                        onChange={(e) => setGeniusPrompt(e.target.value)}
                        placeholder="e.g. React Architecture, Behavioral System Design"
                        disabled={isGenerating}
                        className="flex-1 rounded-xl border border-border bg-background px-4 py-2.5 text-sm text-foreground outline-none transition focus:border-primary"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleGeniusGenerate();
                        }}
                      />
                      <Button onClick={handleGeniusGenerate} disabled={isGenerating || !geniusPrompt.trim()}>
                        {isGenerating ? "Mind is thinking..." : "Blow my mind"}
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2">
                    {MIND_MAP_TEMPLATES.filter(t => t.id !== "genius-mind").map((template) => (
                      <button
                        key={template.id}
                        type="button"
                        onClick={() => handleCreateMap(template.id)}
                        className="rounded-3xl border border-border bg-card p-5 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
                      >
                        <div className="text-base font-semibold text-foreground">
                          {template.label}
                        </div>
                        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                          {template.description}
                        </p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          {template.steps.map((step) => (
                            <span
                              key={step}
                              className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground"
                            >
                              {step}
                            </span>
                          ))}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        <aside className="border-t border-border bg-card p-4 xl:border-t-0 xl:border-l">
          <div className="mb-4">
            <div className="text-sm font-semibold text-foreground">Node Inspector</div>
            <div className="text-xs text-muted-foreground">
              Edit the selected node and keep the canvas structure flexible.
            </div>
          </div>

          {!activeMap ? (
            <div className="rounded-2xl border border-dashed border-border bg-muted/20 px-4 py-5 text-sm text-muted-foreground">
              Create a map to unlock the editor and inspector.
            </div>
          ) : !selectedNode ? (
            <div className="rounded-2xl border border-dashed border-border bg-muted/20 px-4 py-5 text-sm text-muted-foreground">
              Select a node on the canvas to edit its title, notes, or add a child.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="mindmap-node-title"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  Node title
                </label>
                <input
                  id="mindmap-node-title"
                  value={selectedNode.data.title}
                  onChange={(event) =>
                    handleSelectedNodeChange("title", event.target.value)
                  }
                  className="w-full rounded-xl border border-border bg-background px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-primary"
                />
              </div>

              <div>
                <label
                  htmlFor="mindmap-node-note"
                  className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  Node notes
                </label>
                <textarea
                  id="mindmap-node-note"
                  value={selectedNode.data.note}
                  onChange={(event) =>
                    handleSelectedNodeChange("note", event.target.value)
                  }
                  rows={8}
                  className="w-full resize-none rounded-xl border border-border bg-background px-3 py-2.5 text-sm leading-relaxed text-foreground outline-none transition focus:border-primary"
                />
              </div>

              <div className="rounded-2xl border border-border bg-muted/20 px-4 py-4 text-xs text-muted-foreground">
                Changes save into your synced session snapshot automatically, so
                switching tabs or refreshing keeps your map library intact.
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
