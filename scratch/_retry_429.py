import json
import subprocess
import tempfile
from pathlib import Path

from app.services.code_executor_service import _problem_bank_index
from app.services.code_runners import HARNESS_BUILDERS
from app.services.coding_problems_data import PROBLEMS

raw = {str(p["id"]): p for p in PROBLEMS}["429"]
p = _problem_bank_index()["429"]
names = list(p["entry_point"]) + ["solve", "solution"]
h = HARNESS_BUILDERS["javascript"](raw["solutionCode"], p["test_cases"], names)

for attempt in range(3):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "main.js"
        f.write_text(h, encoding="utf-8")
        try:
            proc = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print(attempt, "TIMEOUT")
            continue
    out = proc.stdout
    if "RESULTS_JSON:" in out:
        res = json.loads(out.rpartition("RESULTS_JSON:")[2].strip().splitlines()[0])
        print(attempt, "ok all_pass =", all(r["passed"] for r in res))
    else:
        print(attempt, "no verdict", proc.stderr[:120])
