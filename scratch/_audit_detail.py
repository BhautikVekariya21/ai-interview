import json

from app.services.coding_problems_data import PROBLEMS

by_id = {}
for p in PROBLEMS:
    by_id.setdefault(p["id"], p)

for pid in (19, 68, 238, 239, 65, 8):
    p = by_id[pid]
    print("=" * 72)
    print(pid, p["title"])
    print("desc:", p["description"][:220].replace("\n", " "))
    print("starter:", p["starterCode"])
    print("solution:", p["solutionCode"])
    for tc in p["testCases"]:
        print("   in :", tc["input"])
        print("   exp:", tc["expected"])
