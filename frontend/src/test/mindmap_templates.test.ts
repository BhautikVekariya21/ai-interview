import { describe, expect, it } from "vitest";
import {
  createMindMapFromTemplate,
  getDefaultMindMapName,
  type MindMapTemplateId,
  type SavedMindMap,
} from "@/lib/mindMap";

const TEMPLATE_EXPECTATIONS: Array<{
  id: MindMapTemplateId;
  name: string;
  nodeTitles: string[];
  edgeCount: number;
}> = [
  {
    id: "star-story",
    name: "STAR Story Map",
    nodeTitles: ["Situation", "Task", "Actions", "Results", "Reflection"],
    edgeCount: 5,
  },
  {
    id: "system-design",
    name: "System Design Map",
    nodeTitles: [
      "Problem",
      "Requirements",
      "APIs",
      "Data Model",
      "High-Level Design",
      "Deep Dives",
      "Tradeoffs",
    ],
    edgeCount: 7,
  },
  {
    id: "coding-problem",
    name: "Coding Problem Map",
    nodeTitles: [
      "Clarify",
      "Examples",
      "Brute Force",
      "Optimal Approach",
      "Complexity",
      "Edge Cases",
      "Tests",
    ],
    edgeCount: 7,
  },
  {
    id: "company-prep",
    name: "Company Prep Map",
    nodeTitles: [
      "Company",
      "Role",
      "Product",
      "Signals",
      "Questions to Ask",
      "30 / 60 / 90",
    ],
    edgeCount: 6,
  },
];

describe("mind map templates", () => {
  it.each(TEMPLATE_EXPECTATIONS)(
    "creates the expected starter graph for $id",
    ({ id, name, nodeTitles, edgeCount }) => {
      const map = createMindMapFromTemplate(id, []);

      expect(map.templateId).toBe(id);
      expect(map.name).toBe(name);
      expect(map.nodes.map((node) => node.data.title)).toEqual(nodeTitles);
      expect(map.edges).toHaveLength(edgeCount);
      expect(new Set(map.nodes.map((node) => node.id)).size).toBe(map.nodes.length);
    },
  );

  it("appends numeric suffixes for duplicate default names", () => {
    const existingMaps = [
      { name: "STAR Story Map" },
      { name: "STAR Story Map 2" },
    ] as SavedMindMap[];

    expect(getDefaultMindMapName("star-story", existingMaps)).toBe("STAR Story Map 3");
  });
});
