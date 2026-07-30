"""Does a duplicate id serve one problem's description with another's tests?"""
from app.services.coding_problems_data import PROBLEMS
from app.services.code_executor_service import _problem_bank_index

bank = _problem_bank_index()

first_seen = {}
for p in PROBLEMS:
    first_seen.setdefault(p["id"], p)

mismatched = []
for pid, p in first_seen.items():
    served = bank.get(str(pid))
    if served and served["title"] != p["title"]:
        mismatched.append((pid, p["title"], served["title"]))

print("ids_where_backend_serves_a_different_problem", len(mismatched))
for row in mismatched[:8]:
    print(" ", row)

# Concrete: do the test cases differ too?
pid = "132"
orig = first_seen[132]
served = bank[pid]
print("\nid 132 UI-first title:", orig["title"])
print("id 132 backend title :", served["title"])
print("orig tests:", orig["testCases"][:2])
print("served tests:", served["test_cases"][:2])
print("orig starter:", repr(orig["starterCode"][:80]))
print("served starter:", repr(served["starter_code"]["javascript"][:80]))
