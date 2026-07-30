from collections import Counter

from app.services.coding_problems_data import PROBLEMS

ids = [p["id"] for p in PROBLEMS]
dupes = {i: c for i, c in Counter(ids).items() if c > 1}
print("total", len(ids), "unique", len(set(ids)), "dupe_ids", len(dupes))
print("sample_dupes", sorted(dupes.items())[:10])

# Which titles collide on the same id?
from collections import defaultdict

by_id = defaultdict(list)
for p in PROBLEMS:
    by_id[p["id"]].append(p["title"])
for i, titles in sorted(by_id.items())[:0]:
    pass
for i in sorted(dupes)[:5]:
    print(i, by_id[i])
