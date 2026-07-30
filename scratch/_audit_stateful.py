from app.services.coding_problems_data import PROBLEMS

by_id = {}
for p in PROBLEMS:
    by_id.setdefault(p["id"], p)

for pid in (132, 136, 504):
    p = by_id[pid]
    print("=" * 72)
    print(pid, p["title"])
    print("desc:", p["description"][:200].replace("\n", " "))
    print("starter:", p["starterCode"])
    print("solution:", p["solutionCode"])
    for tc in p["testCases"]:
        print("   in :", tc["input"])
        print("   exp:", tc["expected"])

print("\n\n### in-place scaffold starters: do they pass? (already know overall=6) ###")
for pid in (460, 11, 70, 30, 459, 20, 29):
    p = by_id[pid]
    print("-" * 60)
    print(pid, p["title"], "|", p["testCases"][0]["input"], "->", p["testCases"][0]["expected"])
    print(p["starterCode"])
