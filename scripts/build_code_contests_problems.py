"""Turn the cached CodeContests records into bank problems.

Reads ``data/code_contests_raw.jsonl`` (written by ``fetch_code_contests.py``)
and writes ``app/services/code_contests_problems.py``.

What this buys: the generated bank's statements average ~134 characters — one
sentence and an inline example. These average ~900, with the Input, Output,
Constraints and Example sections a real judge ships. That is the gap this
import exists to close.

What it costs: these are *whole-program* problems. The candidate reads stdin
and writes stdout instead of filling in a function body, so they are graded by
``grading: "stdio"`` rather than by calling an entry point. Compiled languages
degrade to compile-only on them.

Ids start at 2000 to stay clear of the generated bank (1..1000) and the SQL
problems (1001..1013).

Usage:
    python scripts/build_code_contests_problems.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "code_contests_raw.jsonl"
OUT = ROOT / "app" / "services" / "code_contests_problems.py"

ID_BASE = 2000

# CodeContests encodes provenance as an integer. Naming it keeps the
# attribution readable on the problem itself rather than as a magic number.
# Verified against the cached rows rather than taken from the schema docs:
# source 1 carries CodeChef-style slugs ("comm3", "gcd2") and source 2 carries
# Codeforces-style indexed names ("1012_E. Cycle sort") with CF ratings
# attached, which is the opposite of the order the enum is usually quoted in.
_SOURCES = {
    0: "Unknown",
    1: "CodeChef",
    2: "Codeforces",
    3: "HackerEarth",
    4: "Codeforces",
    5: "AtCoder",
    6: "Aizu",
}

# The dataset's ``difficulty`` is not a 0-5 scale — the cached rows run 0..21.
# Measured against the rows that also carry a Codeforces rating, levels 7 and
# up track it monotonically (7≈1140, 8≈1613, 9≈1940, 10≈2058, 11≈2416), while
# 0..6 is a separate bucket used by the non-Codeforces sources with scales of
# their own. So the rating is preferred wherever it exists, and the level is
# only consulted as a fallback with each range read on its own terms.
def _difficulty(record: Dict[str, Any]) -> str:
    rating = record.get("cf_rating") or 0
    if rating:
        # Conventional reading of Codeforces ratings: under 1200 is a beginner
        # problem, 1200-1900 the contest middle, above that genuinely hard.
        if rating < 1200:
            return "Easy"
        if rating < 1900:
            return "Medium"
        return "Hard"

    level = record.get("difficulty") or 0
    if level >= 7:
        if level == 7:
            return "Easy"
        if level <= 9:
            return "Medium"
        return "Hard"
    if 1 <= level <= 2:
        return "Easy"
    if level >= 5:
        return "Hard"
    # Level 0 means "not rated by anyone". Default to the middle tier rather
    # than flattering an unknown problem as Easy.
    return "Medium"


_TAG_MAP = {
    "dp": "dp",
    "greedy": "greedy",
    "math": "math",
    "graphs": "graph",
    "dfs and similar": "dfs",
    "trees": "tree",
    "strings": "string",
    "sortings": "sorting",
    "binary search": "binary-search",
    "two pointers": "two-pointers",
    "data structures": "array",
    "implementation": "array",
    "brute force": "array",
    "number theory": "math",
    "combinatorics": "math",
    "bitmasks": "bit-manipulation",
    "constructive algorithms": "greedy",
    "shortest paths": "graph",
    "dsu": "union-find",
    "geometry": "math",
    "probabilities": "math",
}


def _tags(record: Dict[str, Any]) -> List[str]:
    """Map CF tags onto the vocabulary ``topic_for()`` already understands.

    An unmapped tag is dropped rather than passed through: the topic is derived
    from these, and a tag the mapper does not know would silently land the
    problem in the default bucket anyway.
    """
    out: List[str] = []
    for tag in record.get("cf_tags") or []:
        mapped = _TAG_MAP.get(tag.strip().lower())
        if mapped and mapped not in out:
            out.append(mapped)
    return out or ["array"]


# "1012_E. Cycle sort" and "p02120 Cluster Network" both carry a contest index
# in front of the real title. Anchored so it only strips a leading identifier,
# never a title that happens to begin with a number.
_TITLE_PREFIX = re.compile(r"^(?:[A-Za-z]?\d+_?[A-Za-z]?\d*\.?)\s+|^[a-z]?\d+[_\s]+")


def _title(record: Dict[str, Any]) -> Optional[str]:
    """A human title from the dataset's contest-indexed name.

    Roughly 15% of rows (CodeChef and HackerEarth) are named by slug alone —
    "brcktsrm", "prpaln" — with no title anywhere in the row and no title line
    at the head of the statement. Title-casing the slug produces "Brcktsrm",
    which tells a candidate nothing, so those return None and the caller skips
    them. Dropping a sixth of the corpus is the cheaper mistake: the statements
    are the point of this import, and a problem nobody can identify in a list
    is not usable however good its statement is.
    """
    raw = (record.get("name") or "").strip()
    cleaned = _TITLE_PREFIX.sub("", raw).strip()
    cleaned = re.sub(r"^[A-Z]\.\s*", "", cleaned).strip()

    # No spaces and no capitals means there was never a prose title here.
    if not cleaned or (" " not in cleaned and cleaned.islower()):
        return None
    return cleaned


def _clean_description(text: str) -> str:
    """Normalise the statement's whitespace without rewriting its content.

    The statements are plain text with section headings on their own lines.
    Runs of three or more blank lines are collapsed so the rendered problem
    does not open with half a screen of nothing, but the wording, the headings
    and the sample blocks are left exactly as the source has them — this is a
    licensed corpus, not a draft to edit.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Codeforces delimits inline maths with $$$…$$$. The corpus keeps the
    # delimiters as literal text, so "$$$n \\le 10^5$$$" renders with the dollar
    # signs showing. Dropping just the delimiters leaves the expression readable.
    text = re.sub(r"\$\$\$(.+?)\$\$\$", r"\1", text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# The sample block that closes almost every statement (1083 of the first 1194
# cached rows use a bare "Example"/"Examples" heading, another 126 use
# "Sample Input"). It is cut out because the same cases are shipped as
# ``test_cases`` and rendered as proper Example panels — leaving it in the prose
# would show the candidate each sample twice, once as a wall of text.
_EXAMPLE_HEADING = re.compile(
    r"^[ \t]*(?:-+\s*)?(?:Examples?|Sample\s+Input|SAMPLE\s+INPUT|Sample\s+Test(?:\s*Cases?)?)"
    r"[ \t]*:?[ \t]*$",
    re.M,
)

# What follows the samples is prose *about* them, and it is the most valuable
# paragraph in the statement — it is where the rule gets worked through on real
# input. It survives the cut and is reattached to the first example.
_NOTE_HEADING = re.compile(
    r"^[ \t]*(?:-+\s*)?(?:Notes?|Explanations?|SAMPLE\s+EXPLANATION)[ \t]*:?[ \t]*$",
    re.M,
)


def _split_samples(description: str) -> tuple[str, Optional[str]]:
    """Statement without its inline sample block, plus the note that followed it.

    Conservative on purpose. The heading has to sit alone on its own line, and
    the cut is only taken when what remains is still a substantial statement —
    a match in the opening paragraph ("Example: the string 7477447 is
    balanced") would otherwise amputate the problem. When anything looks off the
    statement is returned whole, which costs a duplicated sample and loses
    nothing.
    """
    match = None
    for candidate in _EXAMPLE_HEADING.finditer(description):
        # The *last* such heading: a statement that says "Examples" mid-prose and
        # again above the samples should be cut at the samples.
        match = candidate
    if match is None:
        return description, None

    head = description[: match.start()].rstrip()
    tail = description[match.end():]
    if len(head) < 200:
        return description, None

    note_match = _NOTE_HEADING.search(tail)
    note = None
    if note_match:
        body = tail[note_match.end():].strip()
        # A bare heading with nothing under it, or a one-word stub, is not worth
        # promoting to an explanation panel.
        if len(body) >= 20:
            note = _clean_description(body)
    return head, note


_STARTERS = {
    "python": (
        "import sys\n\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    # Your code here\n\n\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    ),
    "javascript": (
        'const data = require("fs").readFileSync(0, "utf8").split(/\\s+/);\n'
        "// Your code here\n"
    ),
    "ruby": "data = STDIN.read.split\n# Your code here\n",
    "php": "<?php\n$data = preg_split('/\\s+/', trim(file_get_contents('php://stdin')));\n// Your code here\n",
}


# A "Constraints" section, where the statement has one on its own line. Roughly
# a fifth of rows do; the rest state their bounds inside the Input section's
# prose, where they cannot be lifted out without rewriting the sentence.
_CONSTRAINTS_HEADING = re.compile(
    r"^[ \t]*(?:-+\s*)?Constraints?[ \t]*:?[ \t]*$", re.M
)


def _split_constraints(statement: str) -> tuple[str, List[str]]:
    """Statement without its Constraints section, plus that section's lines.

    The bounds belong in the constraints panel, not buried at the foot of the
    prose — that panel is the first thing a candidate checks to size their
    solution. Only taken when the section runs to the end of the statement (it
    does, once the sample block has been cut) and is short enough to actually be
    a bounds list rather than the back half of the problem.
    """
    match = None
    for candidate in _CONSTRAINTS_HEADING.finditer(statement):
        match = candidate
    if match is None:
        return statement, []

    head = statement[: match.start()].rstrip()
    section = statement[match.end():].strip()
    if len(head) < 200 or not section or len(section) > 800:
        return statement, []

    lines = [line.strip() for line in section.split("\n")]
    return head, [line for line in lines if line]


def _constraints(record: Dict[str, Any], stated: List[str]) -> str:
    """The statement's own bounds, then the judge limits it never mentions."""
    parts: List[str] = list(stated)
    seconds = record.get("time_limit_seconds")
    if seconds:
        parts.append(f"Time limit: {seconds} second{'s' if seconds != 1 else ''}")
    memory = record.get("memory_limit_bytes")
    if memory:
        parts.append(f"Memory limit: {memory // (1024 * 1024)} MB")
    parts.append("Read input from standard input and write to standard output")
    return "\n".join(parts)


def convert(record: Dict[str, Any], pid: int) -> Optional[Dict[str, Any]]:
    tests = record.get("public_tests") or {}
    inputs = tests.get("input") or []
    outputs = tests.get("output") or []
    if not inputs or len(inputs) != len(outputs):
        return None

    description = _clean_description(record.get("description") or "")
    if len(description) < 120:
        # Too short to be the improvement this import exists to deliver.
        return None

    # CodeContests strips the statements' figures and leaves a literal "<image>"
    # behind. That is about a quarter of the corpus, and there is no way to
    # recover the picture — it was never in the dataset. Many of those problems
    # are not merely uglier without it but unanswerable: the figure is where the
    # grid, the tree or the sample layout was defined. Shipping a problem that
    # points at a diagram nobody can see is worse than shipping fewer problems,
    # so these are dropped rather than imported with a hole in them.
    if "<image>" in description:
        return None

    title = _title(record)
    if title is None:
        return None

    description, note = _split_samples(description)
    description, stated_bounds = _split_constraints(description)
    if note:
        # Re-attached as a section rather than as example 1's explanation: these
        # notes routinely walk through several samples at once ("In the first
        # example… In the second example…"), so pinning one to the first case
        # would caption it with prose about the others. The net effect of the
        # split is then exactly what was wanted — the duplicated sample I/O
        # goes, everything the source wrote about it stays.
        description = f"{description}\n\n**Note**\n\n{note}"

    cases = [
        {"input": i, "expected": o} for i, o in zip(inputs, outputs)
    ]
    source_name = _SOURCES.get(record.get("source") or 0, "Unknown")

    return {
        "id": pid,
        "title": title,
        "difficulty": _difficulty(record),
        "topic": "Arrays & Hashing",  # re-derived from tags when served
        "tags": _tags(record),
        "description": description,
        "constraints": _constraints(record, stated_bounds),
        "grading": "stdio",
        "starterCode": _STARTERS["javascript"],
        "starter_code": dict(_STARTERS),
        "testCases": cases,
        "test_cases": cases,
        "hints": [],
        "companiesAsked": [],
        "timeComplexity": "",
        "spaceComplexity": "",
        "source_attribution": (
            f"{source_name} via DeepMind CodeContests (CC BY 4.0)"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if not CACHE.exists():
        raise SystemExit(f"no cache at {CACHE}; run fetch_code_contests.py first")

    problems: List[Dict[str, Any]] = []
    seen_titles = set()
    with CACHE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            converted = convert(record, ID_BASE + len(problems))
            if converted is None:
                continue
            # Titles are shown in the catalogue and searched against, so two
            # problems with the same one are indistinguishable to a candidate.
            key = converted["title"].lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            problems.append(converted)
            if args.limit and len(problems) >= args.limit:
                break

    body = json.dumps(problems, indent=4, ensure_ascii=False)
    OUT.write_text(
        '"""CodeContests problems — imported statements, graded on stdin/stdout.\n'
        "\n"
        "Generated by ``scripts/build_code_contests_problems.py``. Do not edit by\n"
        "hand: a re-import overwrites the file.\n"
        "\n"
        "Source: DeepMind CodeContests (https://github.com/google-deepmind/code_contests).\n"
        "Code is Apache 2.0; the statements are CC BY 4.0, and each problem carries\n"
        "its own ``source_attribution``.\n"
        "\n"
        "These are whole-program problems: the solution reads stdin and writes\n"
        'stdout, so they are graded with ``grading: "stdio"`` rather than by\n'
        "calling an entry point.\n"
        '"""\n\n'
        f"CODE_CONTESTS_PROBLEMS = {body}\n",
        encoding="utf-8",
    )
    print(f"wrote {len(problems)} problems to {OUT}")


if __name__ == "__main__":
    main()
