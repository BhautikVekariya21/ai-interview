from app.services.code_executor_service import _problem_bank_index
from app.services.coding_problems_data import PROBLEMS

raw = {str(p["id"]): p for p in PROBLEMS}["429"]
p = _problem_bank_index()["429"]
print(p["title"], "| grading:", p.get("grading"))
print("desc:", raw["description"][:200].replace("\n", " "))
print("starter:", raw["starterCode"])
print("solution:", raw["solutionCode"])
for tc in raw["testCases"]:
    print("  in :", tc["input"][:120])
    print("  exp:", tc["expected"][:120])
print("entry_point:", p["entry_point"])
