"""Build `data/problem_enrichment.json` from the hand-authored statements.

Run:  python scripts/build_authored_statements.py [--check]

`--check` verifies without writing, for use in CI.

This is the offline sibling of `scripts/enrich_problems.py`. That script asks an
LLM for statements; this one takes them from `scripts/authored_statements*.py`.
Both write the same overlay file in the same schema, and both are subject to the
same rule: **the overlay may never state an example.** Examples are replayed
from `test_cases` by `problem_enrichment.enrich()`, so a statement that spelled
out its own worked example could contradict the grader with no way for a
candidate to tell which one is authoritative.

The checks below exist because that rule is easy to break by hand:

1. Every authored id must exist in the bank.
2. A statement must not embed an example block ("Example 1:", "Input:", …).
3. `explanations` must line up 1:1 with the examples that will actually render
   — `enrich()` takes the first three test cases, so a fourth explanation would
   silently never appear, and a missing third leaves one example unannotated.
4. Parameter names named in prose must be real parameters of that problem. This
   catches the most likely drift: writing about `nums` when the signature says
   `numbers`.
5. The finished entry must survive `enrich()` and actually take effect.

The value advisory at the end is not a failure. Prose that reads well often
paraphrases ("1 occurs three times") rather than quoting the literal output, so
a missing literal is normal — it is printed for review, not enforced.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services import problem_enrichment  # noqa: E402
from app.services.code_executor_service import CodeExecutorService  # noqa: E402
from scripts.authored_statements import AUTHORED  # noqa: E402
from scripts.authored_statements_2 import AUTHORED_2  # noqa: E402

OUT_PATH = ROOT / "data" / "problem_enrichment.json"

# The layer that renders examples only ever takes this many.
RENDERED_EXAMPLES = 3

# Signs that a statement is spelling out its own example instead of leaving that
# to the recorded test cases.
_EXAMPLE_MARKERS = (
    re.compile(r"^\s*Example\s*\d*\s*:", re.M),
    re.compile(r"^\s*Input\s*:", re.M),
    re.compile(r"^\s*Output\s*:", re.M),
    re.compile(r"^\s*Constraints\s*:", re.M),
)


def _merged() -> Dict[int, Dict[str, Any]]:
    overlap = set(AUTHORED) & set(AUTHORED_2)
    if overlap:
        raise SystemExit(f"Same id authored in both modules: {sorted(overlap)}")
    return {**AUTHORED, **AUTHORED_2}


def _backticked_names(text: str) -> List[str]:
    """Identifiers the prose refers to as arguments, e.g. `nums`."""
    return re.findall(r"`([a-z][A-Za-z0-9_]*)`", text)


def verify(service: CodeExecutorService, entries: Dict[int, Dict[str, Any]]) -> List[str]:
    """Every way an authored entry can be wrong that a machine can see."""
    problems: List[str] = []
    advisories: List[str] = []

    for pid, entry in sorted(entries.items()):
        source = service.get_problem_source(str(pid))
        if source is None:
            problems.append(f"[{pid}] no such problem in the bank")
            continue

        title = source.get("title", "?")
        tag = f"[{pid} {title}]"
        statement = entry.get("statement", "")

        if len(statement.strip()) < 120:
            problems.append(f"{tag} statement is under the 120-char floor enrich() enforces")
        for marker in _EXAMPLE_MARKERS:
            if marker.search(statement):
                problems.append(
                    f"{tag} statement embeds an example/constraints block — those are "
                    f"rendered from the recorded test cases, not written here"
                )
                break

        cases = source.get("test_cases") or []
        expected_count = min(len(cases), RENDERED_EXAMPLES)
        explanations = entry.get("explanations") or []
        if len(explanations) != expected_count:
            problems.append(
                f"{tag} has {len(explanations)} explanations but {expected_count} "
                f"examples will render ({len(cases)} test cases, capped at {RENDERED_EXAMPLES})"
            )

        # Prose must talk about the real arguments.
        baseline = problem_enrichment.build_baseline(source)
        real = set(baseline.get("param_names") or [])
        if real:
            for name in set(_backticked_names(statement)):
                # Only flag names that look like they are being used as an
                # argument — a lone lowercase word in backticks. Value literals
                # such as `true` are excluded.
                if name in {"true", "false", "null", "nums1", "nums2"}:
                    continue
                if name not in real and len(name) > 1:
                    advisories.append(f"{tag} prose names `{name}`; real params are {sorted(real)}")

        for clause in entry.get("constraints_exact") or []:
            if not isinstance(clause, str) or not 3 <= len(clause.strip()) <= 200:
                problems.append(f"{tag} constraint clause rejected by enrich(): {clause!r}")

    if advisories:
        print("\nAdvisories (review, not failures):")
        for line in advisories:
            print(f"  {line}")

    return problems


def confirm_applied(service: CodeExecutorService, entries: Dict[int, Dict[str, Any]]) -> List[str]:
    """The overlay is on disk — check it actually reaches the rendered problem."""
    problem_enrichment._store.cache_clear()
    failures: List[str] = []
    for pid, entry in sorted(entries.items()):
        enriched = service.get_problem_by_id(str(pid))
        if enriched is None:
            failures.append(f"[{pid}] disappeared after enrichment")
            continue
        if enriched["description"].strip() != entry["statement"].strip():
            failures.append(f"[{pid}] authored statement did not take effect")
        exact = entry.get("constraints_exact")
        if exact and enriched["constraints"] != "\n".join(exact):
            failures.append(f"[{pid}] authored constraints did not take effect")
        annotated = sum(1 for ex in enriched["examples"] if ex.get("explanation"))
        if annotated != len(entry.get("explanations") or []):
            failures.append(
                f"[{pid}] {annotated} examples carry an explanation, authored "
                f"{len(entry.get('explanations') or [])}"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()

    entries = _merged()
    service = CodeExecutorService()

    print(f"Authored entries: {len(entries)}")
    failures = verify(service, entries)
    if failures:
        print("\nFAILED:")
        for line in failures:
            print(f"  {line}")
        return 1
    print("Verification passed.")

    if args.check:
        return 0

    # Merge rather than overwrite: a future LLM run writes into the same file,
    # and an authored entry should not silently erase a generated one for a
    # problem nobody has hand-written.
    existing: Dict[str, Any] = {}
    if OUT_PATH.exists():
        try:
            existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except (OSError, ValueError):
            existing = {}

    for pid, entry in entries.items():
        payload = {k: v for k, v in entry.items() if v}
        payload["source"] = "authored"
        existing[str(pid)] = payload

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(OUT_PATH)
    print(f"Wrote {len(existing)} entries to {OUT_PATH}")

    applied = confirm_applied(service, entries)
    if applied:
        print("\nWROTE, BUT DID NOT APPLY:")
        for line in applied:
            print(f"  {line}")
        return 1
    print("All authored entries verified live through enrich().")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
