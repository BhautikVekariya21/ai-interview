#!/usr/bin/env python3
"""Generate judge-grade problem statements for the coding bank.

The bank ships one-sentence descriptions (131 characters on average). This
walks every problem, asks the configured LLM to expand it into a statement of
the depth LeetCode/CodeChef/HackerRank print, and writes the results to
``data/problem_enrichment.json``, which ``app.services.problem_enrichment``
overlays at read time.

This is a BATCH TOOL, run manually, not part of the request path. Statements
are generated once and committed; the API never waits on an LLM to render a
problem. Without the output file the app still serves the derived baseline, so
running this is an upgrade rather than a prerequisite.

--------------------------------------------------------------------------------
Usage
--------------------------------------------------------------------------------
Needs one working LLM provider in ``.env`` (OPENROUTER_API_KEY, GROQ_API_KEY,
CLAUDE_API_KEY, … — whatever ``llm_service`` can reach).

    python scripts/enrich_problems.py --limit 10        # try 10 first
    python scripts/enrich_problems.py                   # the whole bank
    python scripts/enrich_problems.py --ids 1,2,57      # named problems
    python scripts/enrich_problems.py --force           # redo existing entries

Progress is flushed to disk every ``--checkpoint`` problems, so an interrupted
run (rate limit, Ctrl-C) keeps everything it had already generated and a rerun
resumes where it stopped.

--------------------------------------------------------------------------------
What the model is and is not allowed to write
--------------------------------------------------------------------------------
It writes prose: the narrative framing, the restatement of the rule, the
explanation of why each example produces the answer it does, and any constraint
the recorded data cannot reveal (uniqueness, sortedness, guaranteed solvability).

It never writes example inputs or outputs. Those are replayed verbatim from the
test cases the grader asserts against — a model-authored example could disagree
with the tests and there would be no way for a candidate to tell which was
right. It is handed the real values and asked only to explain them.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from loguru import logger  # noqa: E402

from app.services import problem_enrichment  # noqa: E402
from app.services.code_executor_service import get_code_executor_service  # noqa: E402
from app.services.coding_problems_data import PROBLEMS  # noqa: E402
from app.services.llm_service import get_llm  # noqa: E402


SYSTEM_PROMPT = (
    "You are a problem setter for a competitive programming judge. You write "
    "problem statements with the depth and precision of LeetCode, CodeChef, "
    "HackerRank and HackerEarth. You are precise, never hand-wavy, and you "
    "never contradict the data you are given."
)


def build_prompt(problem: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Ask for prose only, with the ground truth pinned down in the prompt."""
    examples = []
    for case in (problem.get("test_cases") or [])[:3]:
        examples.append(
            {
                "input": case.get("input"),
                "output": case.get("expected"),
            }
        )

    facts = {
        "title": problem.get("title"),
        "difficulty": problem.get("difficulty"),
        "topic": problem.get("category"),
        "tags": problem.get("tags"),
        "current_one_line_description": problem.get("description"),
        "function_signature": baseline.get("signature"),
        "known_constraints": baseline.get("constraints"),
        "optimal_time_complexity": problem.get("time_complexity"),
        "optimal_space_complexity": problem.get("space_complexity"),
        "real_test_cases_do_not_change": examples,
    }

    return f"""Expand this into a full problem statement.

FACTS (ground truth — never contradict these):
{json.dumps(facts, indent=2, ensure_ascii=False)}

Write a statement a candidate could solve from cold, with no other context.

IMPORTANT — the title may not match the description. Several titles in this
bank were auto-generated with unrelated domain flavour (a stair-climbing
problem titled "Identify Port Routes"). The TEST CASES AND THE ONE-LINE
DESCRIPTION ARE THE TRUTH. If the title disagrees with them, write the
statement the test cases describe and ignore the title's theme.

Return JSON with exactly these keys:

"statement": the full problem statement in markdown, 5-10 sentences across
  2-4 paragraphs. Open by framing the task concretely, then state the rule
  precisely (define every term you use — what counts as a subarray, whether
  ties matter, what to return when nothing qualifies). Close by stating exactly
  what to return, including the degenerate case. Use `backticks` around
  variable names. Do NOT include the examples, the constraints, or the function
  signature — those are rendered separately. Do not start with the title.

"explanations": an array with one entry per test case above, in order,
  explaining why THAT input produces THAT output. Reference the actual values.
  One or two sentences each. This is where a candidate confirms they read the
  rule correctly, so be concrete: "the window `[2,3]` sums to 5, and no longer
  window stays under the limit" — not "the algorithm finds the answer".

"constraints": an array of any ADDITIONAL constraint lines not already in
  known_constraints — guarantees the test data cannot show, such as
  "exactly one valid answer exists", "`nums` is sorted in non-decreasing order",
  "all values are distinct", "the linked list has no cycle". Use standard judge
  notation. Return [] if the known constraints are already complete. Never
  repeat or contradict a known constraint.

"follow_up": one sentence pushing toward the optimal solution, in the voice
  judges use ("Can you solve it in O(n) time and O(1) space?"). Use the stated
  optimal complexities."""


def _valid(payload: Any, expected_examples: int) -> Optional[Dict[str, Any]]:
    """Accept only a well-formed response; a partial one is worse than none."""
    if not isinstance(payload, dict):
        return None

    statement = payload.get("statement")
    if not isinstance(statement, str) or len(statement.strip()) < 200:
        return None

    explanations = payload.get("explanations")
    if not isinstance(explanations, list):
        explanations = []
    explanations = [e.strip() for e in explanations if isinstance(e, str) and e.strip()]
    # Trailing explanations with no example to attach to would be dropped
    # silently downstream; truncate here so the stored record is honest.
    explanations = explanations[:expected_examples]

    constraints = payload.get("constraints")
    if not isinstance(constraints, list):
        constraints = []
    constraints = [
        c.strip() for c in constraints if isinstance(c, str) and 3 <= len(c.strip()) <= 200
    ]

    follow_up = payload.get("follow_up")
    follow_up = follow_up.strip() if isinstance(follow_up, str) else ""

    return {
        "statement": statement.strip(),
        "explanations": explanations,
        "constraints": constraints,
        "follow_up": follow_up,
    }


def load_store(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.error(f"Existing store unreadable ({exc}) — refusing to overwrite it")
        raise SystemExit(1)


def save_store(path: Path, store: Dict[str, Any]) -> None:
    """Write via a temp file so an interrupt cannot truncate the real store."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=1, ensure_ascii=False, sort_keys=True)
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="stop after N problems (0 = all)")
    parser.add_argument("--ids", type=str, default="", help="comma-separated problem ids")
    parser.add_argument("--force", action="store_true", help="regenerate existing entries")
    parser.add_argument("--checkpoint", type=int, default=10, help="flush to disk every N")
    parser.add_argument("--sleep", type=float, default=0.0, help="seconds between calls")
    parser.add_argument(
        "--out", type=str, default=str(problem_enrichment.STORE_PATH), help="output path"
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    store = load_store(out_path)
    logger.info(f"Store: {out_path} ({len(store)} existing entries)")

    llm = get_llm()
    if not llm.is_available:
        logger.error(
            "No LLM provider is reachable. Set OPENROUTER_API_KEY / GROQ_API_KEY "
            "(or another provider) in .env. The app still serves the derived "
            "baseline without this file."
        )
        return 1

    service = get_code_executor_service()

    wanted = {i.strip() for i in args.ids.split(",") if i.strip()} if args.ids else None
    targets: List[str] = []
    for raw in PROBLEMS:
        pid = str(raw.get("id"))
        if wanted is not None and pid not in wanted:
            continue
        if pid in store and not args.force:
            continue
        targets.append(pid)
        if args.limit and len(targets) >= args.limit:
            break

    if not targets:
        logger.info("Nothing to do — every requested problem is already generated.")
        return 0

    logger.info(f"Generating {len(targets)} statements")
    generated = failed = 0

    for index, pid in enumerate(targets, start=1):
        problem = service.get_problem_source(pid)
        if not problem:
            logger.warning(f"[{index}/{len(targets)}] {pid}: not found, skipping")
            failed += 1
            continue

        baseline = problem_enrichment.build_baseline(problem)
        example_count = len((problem.get("test_cases") or [])[:3])
        title = problem.get("title", "?")

        try:
            payload = llm.generate_json(
                prompt=build_prompt(problem, baseline),
                system_prompt=SYSTEM_PROMPT,
                max_tokens=2000,
            )
        except Exception as exc:
            logger.warning(f"[{index}/{len(targets)}] {pid} {title}: call failed ({exc})")
            failed += 1
            continue

        record = _valid(payload, example_count)
        if record is None:
            logger.warning(f"[{index}/{len(targets)}] {pid} {title}: unusable response, skipped")
            failed += 1
            continue

        store[pid] = record
        generated += 1
        logger.info(
            f"[{index}/{len(targets)}] {pid} {title}: "
            f"{len(record['statement'])} chars, "
            f"{len(record['explanations'])} explanations, "
            f"+{len(record['constraints'])} constraints"
        )

        if generated % args.checkpoint == 0:
            save_store(out_path, store)
            logger.info(f"  checkpoint — {len(store)} entries on disk")

        if args.sleep:
            time.sleep(args.sleep)

    save_store(out_path, store)
    logger.info(f"Done. generated={generated} failed={failed} total_on_disk={len(store)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted — progress up to the last checkpoint is saved.")
        raise SystemExit(130)
