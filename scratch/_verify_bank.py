"""Full verification: every problem's own solution must pass, no starter may pass."""
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from app.services.code_executor_service import _problem_bank_index
from app.services.code_runners import (
    DESIGN_HARNESS_BUILDERS,
    HARNESS_BUILDERS,
)
from app.services.coding_problems_data import PROBLEMS

bank = _problem_bank_index()
raw_by_id = {str(p["id"]): p for p in PROBLEMS}

print("PROBLEMS", len(PROBLEMS), "| indexed", len(bank))
ids = [p["id"] for p in PROBLEMS]
print("unique_ids", len(set(ids)), "| sequential", ids == list(range(1, len(ids) + 1)))


def run(source, problem, tests):
    kind = problem.get("grading")
    builder = (
        DESIGN_HARNESS_BUILDERS["javascript"] if kind == "design"
        else HARNESS_BUILDERS["javascript"]
    )
    names = list(problem["entry_point"]) + ["solve", "solution"]
    harness = builder(source, tests, names)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "main.js"
        f.write_text(harness, encoding="utf-8")
        try:
            proc = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            return None, "timeout"
    if "RESULTS_JSON:" not in proc.stdout:
        return None, (proc.stderr or "")[:80]
    res = json.loads(proc.stdout.rpartition("RESULTS_JSON:")[2].strip().splitlines()[0])
    return res, None


sol_stats = Counter()
sol_fail = []
start_stats = Counter()
start_pass = []
ungraded = []

for pid, p in bank.items():
    if p.get("grading") == "unsupported":
        ungraded.append((pid, p["title"]))
        continue
    tests = p["test_cases"]
    raw = raw_by_id[pid]

    res, err = run(raw["solutionCode"], p, tests)
    if res is None:
        sol_stats["no_verdict"] += 1
        sol_fail.append((pid, p["title"], err))
    elif res and all(r.get("passed") is True for r in res):
        sol_stats["pass"] += 1
    else:
        sol_stats["fail"] += 1
        bad = next(r for r in res if r.get("passed") is not True)
        sol_fail.append((pid, p["title"], f"got={str(bad.get('actual'))[:40]} want={str(bad.get('expected'))[:40]}"))

    res2, _ = run(raw["starterCode"], p, tests)
    if res2 and all(r.get("passed") is True for r in res2):
        start_stats["FALSE_PASS"] += 1
        start_pass.append((pid, p["title"]))
    else:
        start_stats["correctly_fails"] += 1

print("\nreference solutions:", dict(sol_stats))
print("starter code:", dict(start_stats))
print("ungraded (design, non-replayable):", len(ungraded))

print("\n--- solution failures ---")
for row in sol_fail[:25]:
    print(" ", row)
print("\n--- starter false passes ---")
for row in start_pass[:25]:
    print(" ", row)
