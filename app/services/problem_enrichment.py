"""LeetCode-depth statements for the 1000-problem bank.

The bank ships descriptions averaging 131 characters and a single-line
constraint averaging 23 — Two Sum is one sentence plus
``2 <= nums.length <= 10^4``. A real judge (LeetCode, CodeChef, HackerRank,
HackerEarth) frames the problem in several hundred words, walks every example,
and bounds *every* input dimension.

Two layers close that gap:

1. A deterministic baseline computed from what each problem already carries —
   its recorded test cases, its inferred signature, its declared complexities.
   It needs no API key, costs nothing, and every claim it makes is derived from
   the data rather than invented.
2. An LLM upgrade that writes the narrative framing and the per-example
   explanations, persisted to ``data/problem_enrichment.json`` so the cost is
   paid once. Without that file the baseline still stands on its own.

The LLM is never allowed to author example inputs or outputs. Those are the
same values the grader asserts against, so a hallucinated example would be a
statement that contradicts the tests. It may only explain values it is handed.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.services import problem_diagrams, static_harness

# Written by scripts/enrich_problems.py, read here. Kept out of the 1.4 MB
# generated data module so a regeneration of the bank does not discard it.
STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "problem_enrichment.json"


# ── Topic ────────────────────────────────────────────────────────────────────

# The bank's own ``topic`` field is unusable: Two Sum is filed under "Tries" and
# Contains Duplicate under "Segment Tree". The ``tags`` are accurate, so the
# topic is re-derived from them. First match wins, so the list runs from the
# most specific technique to the most general container.
_TAG_TO_TOPIC: Tuple[Tuple[str, str], ...] = (
    # SQL problems are graded as queries against a schema, so the topic they
    # exercise is the database itself, not a function technique. First match
    # wins, so this must sit ahead of any generic fallback.
    ("sql", "Database"),
    ("database", "Database"),
    ("union-find", "Disjoint Set (Union-Find)"),
    ("topological-sort", "Topological Sort"),
    ("sliding-window", "Sliding Window"),
    ("backtracking", "Backtracking"),
    ("dp", "Dynamic Programming"),
    ("fibonacci", "Dynamic Programming"),
    ("divide-and-conquer", "Divide & Conquer"),
    ("monotonic-stack", "Stack"),
    ("heap", "Heap / Priority Queue"),
    ("quickselect", "Heap / Priority Queue"),
    ("bst", "Trees"),
    ("tree", "Trees"),
    ("linked-list", "Linked List"),
    ("graph", "Graphs"),
    ("bfs", "Graphs"),
    ("dfs", "Graphs"),
    ("binary-search", "Binary Search"),
    ("two-pointers", "Two Pointers"),
    ("bit-manipulation", "Bit Manipulation"),
    ("sieve", "Math & Geometry"),
    ("math", "Math & Geometry"),
    ("stack", "Stack"),
    ("queue", "Stack"),
    ("greedy", "Greedy"),
)


def topic_for(tags: List[str], fallback: str = "Arrays & Hashing") -> str:
    """The technique a problem actually exercises, read off its tags."""
    present = {t.lower() for t in tags or []}
    for tag, topic in _TAG_TO_TOPIC:
        if tag in present:
            return topic
    return fallback


# ── Type rendering ───────────────────────────────────────────────────────────

_TYPE_WORDS = {"int": "integer", "float": "number", "str": "string", "bool": "boolean"}


def _type_name(t: static_harness.Type) -> str:
    """A language-neutral spelling, e.g. ``int[]`` or ``string[][]``."""
    if t.kind == "list":
        return f"{_type_name(t.item)}[]" if t.item else "array"
    return {"int": "int", "float": "float", "str": "string", "bool": "boolean"}.get(
        t.kind, t.kind
    )


def _type_phrase(t: static_harness.Type) -> str:
    """A spelling that reads inside a sentence, e.g. ``array of integers``."""
    if t.kind == "list":
        if t.item is None:
            return "array"
        if t.item.kind == "list":
            return f"2D array of {_TYPE_WORDS.get(t.item.item.kind, 'value')}s" if t.item.item else "2D array"
        return f"array of {_TYPE_WORDS.get(t.item.kind, 'value')}s"
    return _TYPE_WORDS.get(t.kind, t.kind)


# ── Bound derivation ─────────────────────────────────────────────────────────

# Bounds a judge would actually print. Derived bounds snap to this ladder so
# they read like a problem statement rather than like a dump of the test data.
_LADDER = (100, 1000, 10**4, 10**5, 10**6, 10**9, 2**31 - 1)


def _snap(magnitude: int, floor: int) -> int:
    """The smallest ladder rung above `magnitude`, then one rung wider.

    Deliberately generous. The recorded tests are a sample of the input space,
    not its boundary, so a bound tightened to exactly what the tests contain
    would licence a solution that is wrong on the real problem — an O(max_value)
    bucket sort looks correct against ``-15 <= nums[i] <= 15``. Overstating is
    the safe direction; understating actively misleads.
    """
    for index, rung in enumerate(_LADDER):
        if magnitude <= rung:
            widened = _LADDER[min(index + 1, len(_LADDER) - 1)]
            return max(widened, floor)
    return _LADDER[-1]


def _pow_notation(value: int) -> str:
    """``100000`` → ``10^5``; leaves non-powers alone."""
    if value == 2**31 - 1:
        return "2^31 - 1"
    for exponent in range(2, 10):
        if value == 10**exponent:
            return f"10^{exponent}"
    return str(value)


def _walk(value: Any, ints: List[int], floats: List[float], strings: List[str],
          lengths: List[int], depth: int = 0) -> None:
    """Collect every scalar and every container length reachable from a value."""
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        ints.append(value)
    elif isinstance(value, float):
        floats.append(value)
    elif isinstance(value, str):
        strings.append(value)
        lengths.append(len(value))
    elif isinstance(value, list) and depth < 4:
        lengths.append(len(value))
        for element in value:
            _walk(element, ints, floats, strings, lengths, depth + 1)


def _charset_clause(name: str, samples: List[str]) -> Optional[str]:
    """What alphabet the strings are drawn from — observed, never guessed."""
    joined = "".join(samples)
    if not joined:
        return None
    if all(c.islower() and c.isalpha() for c in joined):
        return f"`{name}` consists of lowercase English letters"
    if all(c.isupper() and c.isalpha() for c in joined):
        return f"`{name}` consists of uppercase English letters"
    if all(c.isalpha() for c in joined):
        return f"`{name}` consists of English letters"
    if all(c.isdigit() for c in joined):
        return f"`{name}` consists of digits"
    if all(c.isalnum() for c in joined):
        return f"`{name}` consists of English letters and digits"
    if joined.isascii() and joined.isprintable():
        return f"`{name}` consists of printable ASCII characters"
    return None


def _param_constraints(
    name: str, param_type: static_harness.Type, values: List[Any], covered: str
) -> List[str]:
    """Bounds for one parameter, skipping dimensions already stated.

    `covered` is the problem's existing constraint text. A bank constraint is
    nearly always the length bound and it is trustworthy — it matches the real
    judge — so it is kept and only the dimensions it omits get filled in.
    """
    out: List[str] = []
    ints: List[int] = []
    floats: List[float] = []
    strings: List[str] = []
    lengths: List[int] = []
    for value in values:
        _walk(value, ints, floats, strings, lengths)

    mentions_length = bool(re.search(rf"\b{re.escape(name)}\s*\.?\s*(length|len|size)", covered, re.I))
    mentions_name = bool(re.search(rf"\b{re.escape(name)}\b", covered))

    if param_type.kind == "list" and lengths and not mentions_length:
        upper = _snap(max(lengths), floor=1000)
        lower = 1 if min(lengths) >= 1 else 0
        out.append(f"{lower} <= {name}.length <= {_pow_notation(upper)}")

    if param_type.kind == "str" and lengths and not mentions_length:
        upper = _snap(max(lengths), floor=1000)
        out.append(f"1 <= {name}.length <= {_pow_notation(upper)}")

    element = f"{name}[i]" if param_type.kind == "list" else name
    scalar_kind = param_type.item.kind if param_type.kind == "list" and param_type.item else param_type.kind

    if scalar_kind == "int" and ints and not (mentions_name and param_type.kind != "list"):
        upper = _snap(max(abs(v) for v in ints), floor=10**4)
        if min(ints) >= 0:
            out.append(f"0 <= {element} <= {_pow_notation(upper)}")
        else:
            out.append(f"-{_pow_notation(upper)} <= {element} <= {_pow_notation(upper)}")

    if scalar_kind == "str" and strings:
        clause = _charset_clause(name, strings)
        if clause:
            out.append(clause)

    return out


def _derive_constraints(problem: Dict[str, Any], signature, names: Optional[List[str]]) -> List[str]:
    """The problem's own constraint line, plus every bound it left unstated."""
    existing = (problem.get("constraints") or "").strip()
    lines = [line.strip() for line in existing.split("\n") if line.strip()]
    if not signature:
        return lines

    cases = problem.get("test_cases") or []
    columns: List[List[Any]] = [[] for _ in signature.params]
    for case in cases:
        raw = case.get("input")
        args = raw if isinstance(raw, list) else [raw]
        for index, value in enumerate(args[: len(columns)]):
            columns[index].append(value)

    covered = existing
    for index, param in enumerate(signature.params):
        name = names[index] if names and index < len(names) else param.name
        for clause in _param_constraints(name, param.type, columns[index], covered):
            if clause not in lines:
                lines.append(clause)
                covered += "\n" + clause
    return lines


# ── Statement assembly ───────────────────────────────────────────────────────

# The bank crams a one-line worked example onto the end of the prose. Examples
# now render as their own blocks, so the inline copy is stripped to avoid
# printing every example twice.
_INLINE_EXAMPLE = re.compile(r"\n*\*\*Example:?\*\*.*$", re.S)

# Several hundred entries open with "**Domain: Logistics**." — a framing label,
# not a sentence. Kept, but promoted out of the prose body.
_DOMAIN_PREFIX = re.compile(r"^\*\*Domain:\s*([^*]+)\*\*\.?\s*")


def _split_description(description: str) -> Tuple[Optional[str], str]:
    """Separate the domain label from the statement body."""
    text = _INLINE_EXAMPLE.sub("", (description or "").strip()).strip()
    match = _DOMAIN_PREFIX.match(text)
    if not match:
        return None, text
    return match.group(1).strip(), text[match.end():].strip()


def _signature_line(problem: Dict[str, Any], signature, names: Optional[List[str]]) -> Optional[str]:
    """``twoSum(nums: int[], target: int) -> int[]`` — read off the real tests."""
    if not signature:
        return None
    entries = problem.get("entry_point") or []
    entry = entries[0] if entries else "solve"
    params = ", ".join(
        f"{(names[i] if names and i < len(names) else p.name)}: {_type_name(p.type)}"
        for i, p in enumerate(signature.params)
    )
    return f"{entry}({params}) -> {_type_name(signature.ret)}"



def _follow_up(problem: Dict[str, Any]) -> Optional[str]:
    """The optimal-complexity nudge every judge closes with.

    Built from the problem's own ``timeComplexity``/``spaceComplexity`` fields,
    which the bank fills in for all 1000 entries.
    """
    time = (problem.get("time_complexity") or "").strip()
    space = (problem.get("space_complexity") or "").strip()
    if not time:
        return None
    if space and space != time:
        return f"Can you solve it in {time} time using {space} extra space?"
    return f"Can you solve it in {time} time?"


def _return_sentence(signature, problem: Dict[str, Any]) -> Optional[str]:
    """State what to hand back, in the terms the return type implies.

    A bank statement stops at "return indices of the two numbers" and never says
    what shape that is or what happens when nothing qualifies. The return type
    is known from the recorded outputs, so the shape can at least be stated
    exactly even when the degenerate case cannot be.
    """
    if not signature:
        return None

    ret = signature.ret
    outputs = [case.get("expected") for case in (problem.get("test_cases") or [])]

    if ret.kind == "bool":
        return (
            "Return `true` if the condition described above holds, and `false` "
            "otherwise."
        )
    if ret.kind == "list":
        base = f"Return {_type_phrase(ret)}"
        # An empty output in the recorded data proves the empty case is
        # reachable, so it is worth stating; absence proves nothing either way.
        if any(isinstance(o, list) and not o for o in outputs):
            return f"{base}. Return an empty array when no answer exists."
        return f"{base} holding the answer."
    if ret.kind in ("int", "float"):
        if outputs and all(isinstance(o, (int, float)) and o >= 0 for o in outputs):
            return f"Return the resulting {_TYPE_WORDS.get(ret.kind, 'value')}."
        return f"Return the resulting {_TYPE_WORDS.get(ret.kind, 'value')}."
    if ret.kind == "str":
        return "Return the resulting string."
    return None


def _given_clause(signature, names: Optional[List[str]]) -> Optional[str]:
    """"Given an integer array `nums` and an integer `target`, …".

    LeetCode opens by naming its arguments in a sentence. The previous version
    of this module emitted a labelled **Input** list instead, which reads like a
    HackerRank submission form rather than a problem statement.
    """
    if not signature or not signature.params:
        return None

    parts: List[str] = []
    for index, param in enumerate(signature.params):
        name = names[index] if names and index < len(names) else param.name
        parts.append(f"{_article_phrase(param.type)} `{name}`")

    if len(parts) == 1:
        listed = parts[0]
    elif len(parts) == 2:
        listed = f"{parts[0]} and {parts[1]}"
    else:
        listed = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    return f"You are given {listed}."


def _article_phrase(t: static_harness.Type) -> str:
    """"an integer array", "a string", "a 2D integer matrix"."""
    if t.kind == "list":
        if t.item is None:
            return "an array"
        if t.item.kind == "list":
            inner = _TYPE_WORDS.get(t.item.item.kind, "value") if t.item.item else "value"
            return f"a 2D {inner} matrix"
        return f"an {_TYPE_WORDS.get(t.item.kind, 'value')} array" if t.item.kind == "int" else (
            f"a {_TYPE_WORDS.get(t.item.kind, 'value')} array"
        )
    word = _TYPE_WORDS.get(t.kind, t.kind)
    return f"an {word}" if word[0] in "aeiou" else f"a {word}"


def _names_already_introduced(body: str, signature, names: Optional[List[str]]) -> bool:
    """True when the body already opens by naming its arguments.

    Most bank statements start "Given an array of integers `nums` and an integer
    `target`, …". Prepending a derived "You are given …" to those produces the
    same sentence twice. Only statements that dive straight into the rule
    ("Find the largest rectangular area in a histogram.") need the opener.
    """
    if not signature or not signature.params:
        return True

    head = body[:160].lower()
    if not head.startswith(("given ", "you are given ", "given,")):
        return False

    # It opens with "Given", but check it actually names the parameters rather
    # than saying something vague like "Given a histogram".
    return any(
        (names[i] if names and i < len(names) else p.name).lower() in head
        for i, p in enumerate(signature.params)
    )


def _is_database_problem(problem: Dict[str, Any]) -> bool:
    """True when the problem is graded as SQL against a schema and seed rows.

    Database problems carry ``sql_schema`` (CREATE TABLE statements) and their
    test cases seed the tables rather than passing positional arguments, so the
    generic typed-signature derivation must not touch them — there is no
    function to infer a signature for.
    """
    return bool(problem.get("sql_schema")) or (
        (problem.get("category") or "").lower() == "database"
    )


def _render_sql_seed(seed: List[str]) -> str:
    """The INSERT statements that populate the example's tables."""
    return "\n".join(seed) if seed else "—"


def _render_sql_expected(rows: List[List[Any]]) -> str:
    """Expected result rows, as a JSON array of arrays."""
    try:
        return json.dumps(rows, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(rows)


def _enrich_sql(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Judge-grade enrichment for a database problem.

    There is no typed function signature to derive bounds from, so the generic
    baseline machinery is skipped. The statement and constraints are authored at
    judge depth in the curated entry itself; what this derives is the schema
    figure (drawn from the problem's own CREATE TABLE / INSERT statements, so
    it cannot disagree with the grader) and the examples, replayed from the
    seed rows the grader actually asserts against.
    """
    cases = problem.get("test_cases") or []
    examples: List[Dict[str, Any]] = []
    for case in cases[:3]:
        example = {
            "input": _render_sql_seed(case.get("seed") or []),
            "output": _render_sql_expected(case.get("expected") or []),
        }
        # Every example gets its own figure, not just the first. For a database
        # question the figure *is* the example — the seeded tables and the table
        # the query must return — so dropping it on cases 2 and 3 would leave
        # them as raw INSERT statements beside a JSON array of arrays.
        diagram = problem_diagrams.build_sql_example_diagram(problem, case)
        if diagram:
            example["diagram"] = diagram
        examples.append(example)
    if not examples:
        examples = problem.get("examples") or []

    enriched = {
        **problem,
        "description": problem.get("description") or "",
        "constraints": problem.get("constraints") or "",
        "examples": examples,
        "follow_up": problem.get("follow_up"),
        "hints": problem.get("hints") or [],
        "time_complexity": problem.get("time_complexity"),
        "space_complexity": problem.get("space_complexity"),
    }
    # The reference query is an authoring/test artifact, not a problem field —
    # spreading the source dict would leak the answer through every endpoint
    # that serves the enriched problem to a candidate.
    enriched.pop("solution_sql", None)
    return enriched


def build_baseline(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Everything derivable without an LLM: bounds, signature, follow-up.

    Takes and returns the normalized (curated-shaped) problem dict.
    """
    if _is_database_problem(problem):
        return {
            "description": problem.get("description", ""),
            "constraints": problem.get("constraints") or "",
            "follow_up": None,
            "signature": None,
            "param_names": None,
        }
    # Imported lazily: code_executor_service imports this module, so a top-level
    # import here would close the cycle.
    from app.services.code_executor_service import _param_names_from_starter

    cases = problem.get("test_cases") or []
    signature = static_harness.infer_signature(cases) if cases else None
    names = (
        _param_names_from_starter(
            (problem.get("starter_code") or {}).get("javascript", ""), len(signature.params)
        )
        if signature
        else None
    )

    domain, body = _split_description(problem.get("description", ""))

    # LeetCode writes one flowing statement: the arguments are named in prose,
    # the rule follows, the return is the last sentence. The labelled
    # Input/Output/Function-signature blocks this used to emit read like a
    # submission form instead. The signature is dropped entirely — it is already
    # on screen in the editor, as the starter code the candidate types into.
    opening = (
        None
        if _names_already_introduced(body, signature, names)
        else _given_clause(signature, names)
    )
    returns = _return_sentence(signature, problem)
    # "…, return indices of the two numbers." already states the return; adding
    # "Return array of integers holding the answer." restates it worse.
    if returns and re.search(r"\breturns?\b", body, re.I):
        returns = None

    paragraph = " ".join(part for part in (opening, body) if part)
    sections: List[str] = []
    if domain:
        sections.append(f"**Domain:** {domain}")
    if paragraph:
        sections.append(paragraph)
    if returns:
        sections.append(returns)

    signature_line = _signature_line(problem, signature, names)

    return {
        "description": "\n\n".join(sections),
        "constraints": _derive_constraints(problem, signature, names),
        "follow_up": _follow_up(problem),
        "signature": signature_line,
        "param_names": names,
    }


# ── Persisted LLM layer ──────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _store() -> Dict[str, Dict[str, Any]]:
    """The generated statements on disk, or an empty overlay if absent."""
    if not STORE_PATH.exists():
        return {}
    try:
        with STORE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            logger.warning(f"Enrichment store is not an object: {STORE_PATH}")
            return {}
        logger.info(f"  Problem enrichment: {len(data)} generated statements loaded")
        return data
    except Exception as exc:
        logger.warning(f"Enrichment store unreadable ({exc}); using derived baseline only")
        return {}


def store_size() -> int:
    return len(_store())


def enrich(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Return `problem` with a judge-grade statement, examples and constraints.

    Falls back cleanly: a problem with no generated entry still gets the derived
    baseline, and a malformed entry is ignored rather than allowed to blank out
    a statement that already works.
    """
    if _is_database_problem(problem):
        return _enrich_sql(problem)

    baseline = build_baseline(problem)
    generated = _store().get(str(problem.get("id"))) or {}

    description = baseline["description"]
    constraints = list(baseline["constraints"])
    follow_up = baseline["follow_up"]

    statement = generated.get("statement")
    if isinstance(statement, str) and len(statement.strip()) >= 120:
        description = statement.strip()

    extra = generated.get("constraints")
    if isinstance(extra, list):
        for clause in extra:
            if isinstance(clause, str) and 3 <= len(clause.strip()) <= 200:
                text = clause.strip()
                if text not in constraints:
                    constraints.append(text)

    # ``constraints_exact`` overrides rather than appends. The derived bounds are
    # deliberately widened off the sample tests (see ``_snap``) because guessing
    # wide is the safe failure. An authored entry has the real bounds, so it is
    # allowed to state them exactly — including negative ranges the sample data
    # never happens to contain.
    exact = generated.get("constraints_exact")
    if isinstance(exact, list):
        stated = [
            clause.strip()
            for clause in exact
            if isinstance(clause, str) and 3 <= len(clause.strip()) <= 200
        ]
        if stated:
            constraints = stated

    if isinstance(generated.get("follow_up"), str) and generated["follow_up"].strip():
        follow_up = generated["follow_up"].strip()

    # Examples always come from the recorded tests — the LLM only annotates
    # them, so the statement can never disagree with what the grader asserts.
    explanations = generated.get("explanations")
    names = baseline["param_names"]
    examples = []
    for index, case in enumerate((problem.get("test_cases") or [])[:3]):
        example = {
            "input": _render_input(case.get("input"), names),
            "output": _render_value(case.get("expected")),
        }
        # A figure only on the first example. LeetCode illustrates the case that
        # teaches the rule and lets the rest stand as text; drawing all three
        # pushes the constraints off the bottom of the pane.
        if index == 0:
            diagram = problem_diagrams.build_diagram(problem, case.get("input"), names)
            if diagram:
                example["diagram"] = diagram
        if isinstance(explanations, list) and index < len(explanations):
            note = explanations[index]
            if isinstance(note, str) and note.strip():
                example["explanation"] = note.strip()
        examples.append(example)
    if not examples:
        examples = problem.get("examples") or []

    # Hints ship collapsed in the UI, so an authored list costs the candidate
    # nothing unless they ask for it.
    hints = problem.get("hints") or []
    authored_hints = generated.get("hints")
    if isinstance(authored_hints, list):
        stated = [h.strip() for h in authored_hints if isinstance(h, str) and h.strip()]
        if stated:
            hints = stated

    return {
        **problem,
        "description": description,
        "constraints": "\n".join(constraints),
        "examples": examples,
        "follow_up": follow_up,
        "hints": hints,
        "time_complexity": problem.get("time_complexity"),
        "space_complexity": problem.get("space_complexity"),
    }


def _render_value(value: Any) -> str:
    """Spell a recorded value the way a statement would print it."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def _render_input(raw: Any, names: Optional[List[str]]) -> str:
    """``nums = [2,7,11,15], target = 9`` rather than ``[[2,7,11,15],9]``.

    Bank inputs are positional arrays, which read as a nested literal with no
    indication of which argument is which. Naming them is how every judge
    prints an example. Falls back to the bare literal when the parameter names
    could not be recovered.
    """
    if isinstance(raw, list) and names and len(names) == len(raw):
        return ", ".join(f"{name} = {_render_value(value)}" for name, value in zip(names, raw))
    return _render_value(raw)
