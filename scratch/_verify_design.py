"""Design harness must pass a correct class and fail a stub, in JS and Python."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from app.services.code_executor_service import _problem_bank_index
from app.services.code_runners import DESIGN_HARNESS_BUILDERS
from app.services.coding_problems_data import PROBLEMS

bank = _problem_bank_index()
raw = {str(p["id"]): p for p in PROBLEMS}

design = [pid for pid, p in bank.items() if p.get("grading") == "design"]
print("design_problems", len(design))
titles = sorted({bank[p]["title"] for p in design})
print("sample_titles", titles[:6])


def run_js(src, tests, names):
    h = DESIGN_HARNESS_BUILDERS["javascript"](src, tests, names)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "main.js"
        f.write_text(h, encoding="utf-8")
        proc = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=20)
    return proc


ok = fail = 0
for pid in design:
    p = bank[pid]
    names = list(p["entry_point"]) + ["solve", "solution"]
    proc = run_js(raw[pid]["solutionCode"], p["test_cases"], names)
    if "RESULTS_JSON:" not in proc.stdout:
        print("NO VERDICT", pid, p["title"], proc.stderr[:90])
        fail += 1
        continue
    res = json.loads(proc.stdout.rpartition("RESULTS_JSON:")[2].strip().splitlines()[0])
    if all(r["passed"] for r in res):
        ok += 1
    else:
        fail += 1
        print("FAIL", pid, p["title"], res[0])

print(f"design solutions: pass={ok} fail={fail}")

# Stubs must NOT pass
stub_pass = 0
for pid in design:
    p = bank[pid]
    names = list(p["entry_point"]) + ["solve", "solution"]
    proc = run_js(raw[pid]["starterCode"], p["test_cases"], names)
    if "RESULTS_JSON:" in proc.stdout:
        res = json.loads(proc.stdout.rpartition("RESULTS_JSON:")[2].strip().splitlines()[0])
        if res and all(r["passed"] for r in res):
            stub_pass += 1
            print("STUB PASSED", pid, p["title"])
print("design stubs that falsely pass:", stub_pass)

# Python design harness sanity check
pid = design[0]
p = bank[pid]
py_min_stack = """
class MinStack:
    def __init__(self):
        self.s = []
        self.m = []
    def push(self, val):
        self.s.append(val)
        self.m.append(val if not self.m else min(val, self.m[-1]))
    def pop(self):
        self.s.pop(); self.m.pop()
    def top(self):
        return self.s[-1]
    def getMin(self):
        return self.m[-1]
"""
target = next(
    (q for q in design if bank[q]["title"] == "Min Stack"),
    None,
)
if target:
    p = bank[target]
    h = DESIGN_HARNESS_BUILDERS["python"](py_min_stack, p["test_cases"], list(p["entry_point"]))
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "main.py"
        f.write_text(h, encoding="utf-8")
        proc = subprocess.run([sys.executable, "-I", str(f)], capture_output=True, text=True, timeout=20)
    print("\npython MinStack stdout:", proc.stdout.strip()[:200] or proc.stderr[:200])
