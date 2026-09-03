"""Grade each problem's own solutionCode. A correct solution that FAILS reveals
a false-negative bug in the harness (wrong entry point, bad arg binding)."""
import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from app.services.code_executor_service import _entry_point_from_starter, _parse_json_ish
from app.services.code_runners import build_js_harness
from app.services.coding_problems_data import PROBLEMS

seen = set()
rows = []
for p in PROBLEMS:
    if p["id"] in seen:
        continue
    seen.add(p["id"])
    rows.append(p)

buckets = Counter()
failures = []

for p in rows:
    tests = [
        {"input": _parse_json_ish(tc["input"]), "expected": _parse_json_ish(tc["expected"])}
        for tc in p["testCases"]
    ]
    names = _entry_point_from_starter(p["starterCode"]) + ["solve", "solution"]
    harness = build_js_harness(p["solutionCode"], tests, names)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "main.js"
        f.write_text(harness, encoding="utf-8")
        try:
            proc = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            buckets["timeout"] += 1
            failures.append((p["id"], p["title"], "TIMEOUT", names[:3]))
            continue
    if "RESULTS_JSON:" not in proc.stdout:
        buckets["no_verdict"] += 1
        failures.append((p["id"], p["title"], (proc.stderr or "")[:90], names[:3]))
        continue
    res = json.loads(proc.stdout.rpartition("RESULTS_JSON:")[2].strip().splitlines()[0])
    if res and all(r.get("passed") is True for r in res):
        buckets["pass"] += 1
    else:
        buckets["wrong_answer"] += 1
        bad = next(r for r in res if r.get("passed") is not True)
        failures.append((p["id"], p["title"], f"got={str(bad.get('actual'))[:40]} want={str(bad.get('expected'))[:40]}", names[:3]))

print("unique_problems", len(rows))
print(dict(buckets))
print("\n--- first 25 failures ---")
for row in failures[:25]:
    print(row)
