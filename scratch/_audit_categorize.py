"""Categorize the 53 problems whose own reference solution fails grading."""
import json
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from app.services.code_executor_service import _entry_point_from_starter, _parse_json_ish
from app.services.code_runners import build_js_harness
from app.services.coding_problems_data import PROBLEMS

seen, rows = set(), []
for p in PROBLEMS:
    if p["id"] not in seen:
        seen.add(p["id"])
        rows.append(p)

cats = defaultdict(list)
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
            cats["timeout"].append((p["id"], p["title"]))
            continue
    if "RESULTS_JSON:" not in proc.stdout:
        cats["no_verdict"].append((p["id"], p["title"], (proc.stderr or "")[:70]))
        continue
    res = json.loads(proc.stdout.rpartition("RESULTS_JSON:")[2].strip().splitlines()[0])
    if res and all(r.get("passed") is True for r in res):
        continue

    bad = next(r for r in res if r.get("passed") is not True)
    actual = bad.get("actual")
    starter = p["starterCode"]
    n_funcs = len(re.findall(r"^function\s+\w+", starter, re.M))
    is_class = bool(re.match(r"\s*class\s+\w+", starter))

    if isinstance(actual, str) and "cannot be invoked without 'new'" in actual:
        key = "stateful_class"
    elif is_class:
        key = "stateful_class"
    elif n_funcs > 1:
        key = "multi_function"
    elif (
        isinstance(actual, list)
        and isinstance(bad.get("expected"), list)
        and sorted(map(str, actual)) == sorted(map(str, bad.get("expected")))
    ):
        key = "order_mismatch"
    else:
        key = "wrong_expected_data"
    cats[key].append((p["id"], p["title"], str(actual)[:44], str(bad.get("expected"))[:44]))

print(Counter({k: len(v) for k, v in cats.items()}))
for k, v in cats.items():
    print(f"\n===== {k} ({len(v)}) =====")
    for row in v:
        print("  ", row)
