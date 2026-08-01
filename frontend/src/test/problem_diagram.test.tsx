import { describe, expect, it } from "vitest";
import { buildTree } from "@/components/ProblemDiagram";

describe("buildTree — LeetCode queue-based level-order decoding", () => {
  it("decodes [1,null,2,3] as 1 → right 2 → left 3, not an orphaned slot", () => {
    // Slot indexing (2i+1/2i+2) would read index 3 as the child of the null at
    // index 1 and drop the 3. The queue reading makes it 2's left child.
    const root = buildTree([1, null, 2, 3]);
    expect(root?.value).toBe(1);
    // 1's explicit null left child is a placeholder slot.
    expect(root?.left?.isNull).toBe(true);
    expect(root?.right?.value).toBe(2);
    // 2's left child is the trailing 3 — the queue reading, not the slot map.
    expect(root?.right?.left?.value).toBe(3);
    // The array ends at 3, so 2 has no right child at all — absent, not a
    // placeholder (only explicit nulls in the array become hollow slots).
    expect(root?.right?.right).toBeNull();
  });

  it("turns every explicit null into a placeholder node", () => {
    const root = buildTree([3, 9, 20, null, null, 15, 7]);
    expect(root?.value).toBe(3);
    expect(root?.left?.value).toBe(9);
    expect(root?.left?.left?.isNull).toBe(true);
    expect(root?.left?.right?.isNull).toBe(true);
    expect(root?.right?.left?.value).toBe(15);
    expect(root?.right?.right?.value).toBe(7);
  });

  it("keeps a complete all-int tree intact", () => {
    const root = buildTree([4, 2, 7, 1, 3, 6, 9]);
    expect(root?.left?.left?.value).toBe(1);
    expect(root?.left?.right?.value).toBe(3);
    expect(root?.right?.left?.value).toBe(6);
    expect(root?.right?.right?.value).toBe(9);
    expect(root?.left?.isNull).toBe(false);
  });

  it("returns null for an empty or null-root encoding", () => {
    expect(buildTree([])).toBeNull();
    expect(buildTree([null])).toBeNull();
  });
});
