"""One-shot repair of app/services/coding_problems_data.py.

Fixes four defects found by auditing the bank against its own reference
solutions:

1. Duplicate IDs — generate_1000_problems.py numbered themed variants with
   `len(NEW_PROBLEMS)+1` while keeping the originals that already held those
   IDs, collapsing 1000 problems to 918 unique. 82 IDs served a different
   problem than the UI displayed. Renumbered sequentially.
2. Leaked solutions — 6 problems shipped a complete prefix-sum implementation
   as `starterCode`, so untouched boilerplate passed every test.
3. Wrong expectations — Two Sum II carried cases with no valid answer that
   still expected one; Sort Array By Parity / Intersection expected one
   specific ordering of an any-order result.
4. Buggy reference solutions — invertTree only swapped sibling leaves instead
   of whole subtrees; isSubtree used a substring hack that misfires.

Rewrites the module in place, preserving the original formatting.
"""

import json
import re

from app.services.coding_problems_data import PROBLEMS

OUT = "app/services/coding_problems_data.py"

# ── 1. Leaked solution → honest stub ─────────────────────────────────────────
LEAK_MARK = "const prefix = [0];"
PREFIX_STUB = "function solution(nums, queries) {\n  // Your code here\n}"
PREFIX_SOLUTION = (
    "function solution(nums, queries) {\n"
    "  const prefix = [0];\n"
    "  for (const n of nums) prefix.push(prefix[prefix.length-1]+n);\n"
    "  return queries.map(([l,r]) => prefix[r+1]-prefix[l]);\n"
    "}"
)

# ── 3. Any-order problems: pin expectations to the canonical algorithm ───────
# These are legitimately order-insensitive, but the grader compares strictly, so
# the stored expectation must match what a correct in-place solution produces.
ORDER_FIXES = {
    "sortArrayByParity": {"[[3,1,2,4]]": "[4,2,1,3]"},
    "intersect": {"[[4,9,5],[9,4,9,8,4]]": "[9,4]"},
}

# ── 3. Two Sum II: drop cases with no valid pair ─────────────────────────────
# [[-1,0],1] and [[-1,0],-1] both expected [1,2], but -1+0 = -1 ≠ 1, and the
# second is a duplicate of a case that is already correct. Keep only solvable
# cases.
TWOSUM_SORTED_DROP = {"[[-1,0],1]"}

# ── 4. Correct reference solutions ──────────────────────────────────────────
INVERT_TREE_FIXED = (
    "function invertTree(arr) {\n"
    "  if (!arr.length) return [];\n"
    "  const r = [];\n"
    "  let start = 0, width = 1;\n"
    "  while (start < arr.length) {\n"
    "    const level = arr.slice(start, start + width);\n"
    "    while (level.length < width) level.push(null);\n"
    "    r.push(...level.reverse());\n"
    "    start += width;\n"
    "    width *= 2;\n"
    "  }\n"
    "  return r.slice(0, arr.length);\n"
    "}"
)

IS_SUBTREE_FIXED = (
    "function isSubtree(s, t) {\n"
    "  const collect = (a, i, depth, out) => {\n"
    "    if (i >= a.length || a[i] === null || a[i] === undefined) return out;\n"
    "    out.push([depth, a[i]]);\n"
    "    collect(a, 2 * i + 1, depth + 1, out);\n"
    "    collect(a, 2 * i + 2, depth + 1, out);\n"
    "    return out;\n"
    "  };\n"
    "  const target = JSON.stringify(collect(t, 0, 0, []));\n"
    "  for (let i = 0; i < s.length; i++) {\n"
    "    if (s[i] === null || s[i] === undefined) continue;\n"
    "    if (JSON.stringify(collect(s, i, 0, [])) === target) return true;\n"
    "  }\n"
    "  return false;\n"
    "}"
)

stats = {
    "leak_stripped": 0,
    "order_fixed": 0,
    "cases_dropped": 0,
    "invert_fixed": 0,
    "subtree_fixed": 0,
    "renumbered": 0,
}

fixed = []
for new_id, p in enumerate(PROBLEMS, start=1):
    q = json.loads(json.dumps(p))  # deep copy

    if q["id"] != new_id:
        stats["renumbered"] += 1
    q["id"] = new_id

    starter = q.get("starterCode", "")

    # 2 — strip leaked solution, keep it as the reference answer
    if LEAK_MARK in starter:
        q["starterCode"] = PREFIX_STUB
        if LEAK_MARK not in q.get("solutionCode", ""):
            q["solutionCode"] = PREFIX_SOLUTION
        stats["leak_stripped"] += 1

    # 3 — correct any-order expectations
    for fn, mapping in ORDER_FIXES.items():
        if re.search(rf"function\s+{fn}\s*\(", starter):
            for tc in q["testCases"]:
                if tc["input"].replace(" ", "") in mapping:
                    want = mapping[tc["input"].replace(" ", "")]
                    if tc["expected"].replace(" ", "") != want:
                        tc["expected"] = want
                        stats["order_fixed"] += 1

    # 3 — drop unsatisfiable Two Sum II cases
    if re.search(r"function\s+twoSumSorted\s*\(", starter):
        before = len(q["testCases"])
        seen = set()
        kept = []
        for tc in q["testCases"]:
            key = tc["input"].replace(" ", "")
            if key in TWOSUM_SORTED_DROP or key in seen:
                continue
            seen.add(key)
            kept.append(tc)
        q["testCases"] = kept
        stats["cases_dropped"] += before - len(kept)

    # 4 — replace buggy reference solutions
    if re.search(r"function\s+invertTree\s*\(", starter):
        q["solutionCode"] = INVERT_TREE_FIXED
        stats["invert_fixed"] += 1
    if re.search(r"function\s+isSubtree\s*\(", starter):
        q["solutionCode"] = IS_SUBTREE_FIXED
        stats["subtree_fixed"] += 1

    fixed.append(q)

ids = [p["id"] for p in fixed]
assert len(ids) == len(set(ids)), "IDs still collide"
assert ids == list(range(1, len(fixed) + 1)), "IDs not sequential"

lines = ['"""', "Coding Problems Data — 1000 problems.", '"""', "", "PROBLEMS = ["]
for p in fixed:
    lines.append(f"    {json.dumps(p, indent=4).replace(chr(10), chr(10) + '    ')},")
lines.append("]")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("wrote", len(fixed), "problems to", OUT)
print(stats)
