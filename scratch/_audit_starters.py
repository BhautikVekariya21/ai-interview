"""Group bank problems by their starterCode to find solution leaks."""
import re
from collections import defaultdict

from app.services.coding_problems_data import PROBLEMS

print("PROBLEMS", len(PROBLEMS))

groups = defaultdict(list)
for p in PROBLEMS:
    groups[p.get("starterCode", "")].append(p["id"])


def has_logic(src: str) -> bool:
    body = re.sub(r"//.*", "", src)
    if "{" in body:
        body = body[body.find("{") + 1 :]
    return bool(re.search(r"\breturn\b|\bfor\b|\bwhile\b|\.map\(|\.reduce\(|\.sort\(", body))


leaky = {s: ids for s, ids in groups.items() if has_logic(s)}
print("distinct_starters", len(groups), "| leaky_distinct", len(leaky),
      "| leaky_problems", sum(len(v) for v in leaky.values()))

for src, ids in sorted(leaky.items(), key=lambda kv: -len(kv[1])):
    print("=" * 70)
    print(f"count={len(ids)} ids={ids[:8]}{'...' if len(ids) > 8 else ''}")
    print(src)
