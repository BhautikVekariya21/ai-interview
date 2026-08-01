"""
Code Executor Service — Subprocess execution sandbox & AI Code Evaluator.

Supports Python 3, JavaScript (Node.js), and Rust code execution against
curated test suites with memory, execution time (ms), and AI Big-O analysis.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from functools import lru_cache
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.services import problem_enrichment, static_harness
from app.services.code_runners import (
    DESIGN_HARNESS_BUILDERS,
    DESIGN_UNSUPPORTED,
    HARNESS_BUILDERS,
    VERIFY_UNTYPEABLE,
    get_spec,
    resolve_language,
)
from app.services.code_sandbox import SandboxUnavailable, get_sandbox
from app.services.llm_service import get_llm

# ── Curated Problem Registry ──────────────────────────────────────────────────

CURATED_PROBLEMS: List[Dict[str, Any]] = [
    {
        "id": "two-sum",
        "entry_point": ["two_sum", "twoSum"],
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Arrays & Hashing",
        "tags": ["array", "hash-map"],
        "companies": ["Google", "Amazon", "Meta", "Apple", "Microsoft"],
        "description": (
            "Given an array of integers `nums` and an integer `target`, return "
            "indices of the two numbers such that they add up to `target`.\n\n"
            "Assume each input has **exactly one solution**, and you may not use the same element twice."
        ),
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9",
        "examples": [
            {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]"},
            {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]"},
        ],
        "starter_code": {
            "python": "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Your solution here\n    pass\n",
            "javascript": "function twoSum(nums, target) {\n  // Your solution here\n}\n",
            "rust": "pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {\n    // Your solution here\n    vec![]\n}\n",
        },
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
            {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1]},
        ],
    },
    {
        "id": "valid-anagram",
        "entry_point": ["is_anagram", "isAnagram"],
        "title": "Valid Anagram",
        "difficulty": "Easy",
        "category": "Arrays & Hashing",
        "tags": ["string", "hash-table"],
        "companies": ["Amazon", "Google", "Microsoft"],
        "description": (
            "Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise."
        ),
        "constraints": "1 <= s.length, t.length <= 5 * 10^4",
        "examples": [
            {"input": 's = "anagram", t = "nagaram"', "output": "true"},
            {"input": 's = "rat", t = "car"', "output": "false"},
        ],
        "starter_code": {
            "python": "def is_anagram(s: str, t: str) -> bool:\n    # Your solution here\n    pass\n",
            "javascript": "function isAnagram(s, t) {\n  // Your solution here\n}\n",
            "rust": "pub fn is_anagram(s: String, t: String) -> bool {\n    // Your solution here\n    false\n}\n",
        },
        "test_cases": [
            {"input": {"s": "anagram", "t": "nagaram"}, "expected": True},
            {"input": {"s": "rat", "t": "car"}, "expected": False},
        ],
    },
    {
        "id": "valid-parentheses",
        "entry_point": ["is_valid", "isValid"],
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stack",
        "tags": ["string", "stack"],
        "companies": ["Amazon", "Meta", "Google", "Bloomberg"],
        "description": (
            "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', "
            "determine if the input string is valid."
        ),
        "constraints": "1 <= s.length <= 10^4",
        "examples": [
            {"input": 's = "()"', "output": "true"},
            {"input": 's = "()[]{}"', "output": "true"},
            {"input": 's = "(]"', "output": "false"},
        ],
        "starter_code": {
            "python": "def is_valid(s: str) -> bool:\n    # Your solution here\n    pass\n",
            "javascript": "function isValid(s) {\n  // Your solution here\n}\n",
            "rust": "pub fn is_valid(s: String) -> bool {\n    // Your solution here\n    false\n}\n",
        },
        "test_cases": [
            {"input": {"s": "()"}, "expected": True},
            {"input": {"s": "()[]{}"}, "expected": True},
            {"input": {"s": "(]"}, "expected": False},
        ],
    },
    {
        "id": "binary-search",
        "entry_point": ["search", "binary_search", "binarySearch"],
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Binary Search",
        "tags": ["array", "binary-search"],
        "companies": ["Apple", "Google", "Microsoft"],
        "description": (
            "Given an array of integers `nums` sorted in ascending order, and an integer `target`, "
            "write a function to search `target` in `nums`. If target exists, return its index; otherwise, return -1."
        ),
        "constraints": "1 <= nums.length <= 10^4",
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"},
        ],
        "starter_code": {
            "python": "def search(nums: list[int], target: int) -> int:\n    # Your solution here\n    pass\n",
            "javascript": "function search(nums, target) {\n  // Your solution here\n}\n",
            "rust": "pub fn search(nums: Vec<i32>, target: i32) -> i32 {\n    // Your solution here\n    -1\n}\n",
        },
        "test_cases": [
            {"input": {"nums": [-1, 0, 3, 5, 9, 12], "target": 9}, "expected": 4},
            {"input": {"nums": [-1, 0, 3, 5, 9, 12], "target": 2}, "expected": -1},
        ],
    },
    {
        "id": "maximum-subarray",
        "entry_point": ["max_sub_array", "maxSubArray"],
        "title": "Maximum Subarray",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "tags": ["array", "divide-and-conquer", "dp"],
        "companies": ["Amazon", "Microsoft", "Apple", "Cisco"],
        "description": (
            "Given an integer array `nums`, find the subarray with the largest sum, and return its sum."
        ),
        "constraints": "1 <= nums.length <= 10^5",
        "examples": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6"},
            {"input": "nums = [1]", "output": "1"},
        ],
        "starter_code": {
            "python": "def max_sub_array(nums: list[int]) -> int:\n    # Your solution here\n    pass\n",
            "javascript": "function maxSubArray(nums) {\n  // Your solution here\n}\n",
            "rust": "pub fn max_sub_array(nums: Vec<i32>) -> i32 {\n    // Your solution here\n    0\n}\n",
        },
        "test_cases": [
            {"input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected": 6},
            {"input": {"nums": [1]}, "expected": 1},
            {"input": {"nums": [5, 4, -1, 7, 8]}, "expected": 23},
        ],
    },
    {
        "id": "lru-cache",
        "entry_point": ["LRUCache"],
        # Stateful design problem: the test case is a sequence of operations
        # against a class instance, not a pure function call, so the generic
        # function harness cannot grade it. Marked explicitly so it reports
        # "not graded" instead of being misgraded by an argument-binding guess.
        "grading": "unsupported",
        "grading_reason": (
            "Stateful design problems are executed but not auto-graded yet: the "
            "test case is an operation sequence against a class instance rather "
            "than a single function call."
        ),
        "title": "LRU Cache",
        "difficulty": "Hard",
        "category": "Design",
        "tags": ["hash-table", "linked-list", "design"],
        "companies": ["Amazon", "Google", "Meta", "Apple", "Microsoft"],
        "description": (
            "Design a data structure that follows the constraints of a **Least Recently Used (LRU) Cache**.\n\n"
            "Implement `get(key)` and `put(key, value)` in `O(1)` average time complexity."
        ),
        "constraints": "1 <= capacity <= 3000",
        "examples": [
            {"input": '["LRUCache", "put", "put", "get", "put", "get"]', "output": "[null, null, null, 1, null, -1]"},
        ],
        "starter_code": {
            "python": "class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n    def get(self, key: int) -> int:\n        return -1\n    def put(self, key: int, value: int) -> None:\n        pass\n",
            "javascript": "class LRUCache {\n  constructor(capacity) {}\n  get(key) { return -1; }\n  put(key, value) {}\n}\n",
            "rust": "pub struct LRUCache {\n    capacity: usize,\n}\nimpl LRUCache {\n    pub fn new(capacity: i32) -> Self { LRUCache { capacity: capacity as usize } }\n    pub fn get(&mut self, key: i32) -> i32 { -1 }\n    pub fn put(&mut self, key: i32, value: i32) {}\n}\n",
        },
        "test_cases": [
            {"input": {"capacity": 2, "ops": [["put", 1, 1], ["put", 2, 2], ["get", 1], ["put", 3, 3], ["get", 2]]}, "expected": [None, None, 1, None, -1]},
        ],
    },
]

# ── Problem Bank Adapter ──────────────────────────────────────────────────────
#
# `coding_problems_data.PROBLEMS` uses a different schema than CURATED_PROBLEMS:
# numeric `id`, camelCase `testCases`, JSON-*string* inputs/expected values, and
# a single JavaScript-only `starterCode`. Normalize it into the curated shape so
# one execution path serves both sources.


def _parse_json_ish(raw: Any) -> Any:
    """Decode a test-case value that may be a JSON string or already typed."""
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    if not text:
        return text
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        # Not JSON — treat as a plain string literal (e.g. a word answer).
        return raw


def _param_names_from_starter(starter: str, arity: int) -> Optional[List[str]]:
    """Recover parameter names from the bank's JavaScript starter.

    Bank test-case inputs are positional, so inference can only call the
    parameters ``arg0``/``arg1``. The starter names them properly — ``prices``,
    ``nums``, ``target`` — and a candidate reads those names as part of the
    problem statement. Returns None unless exactly `arity` plain identifiers are
    found, so a destructured or defaulted parameter list is left alone rather
    than mis-mapped.
    """
    match = re.search(r"function\s+[A-Za-z_$][\w$]*\s*\(([^)]*)\)", starter or "")
    if not match:
        return None
    raw = match.group(1).strip()
    if not raw:
        return None
    names = [part.strip() for part in raw.split(",")]
    if len(names) != arity:
        return None
    if not all(re.fullmatch(r"[A-Za-z_$][\w$]*", n) for n in names):
        return None
    return names


def _entry_point_from_starter(starter: str) -> List[str]:
    """Recover the expected function name from starter code.

    The bank never declares an entry point, but its starter code always
    contains exactly one signature, so the name is recoverable rather than
    guessed. Both the JS name and its snake_case form are offered so a
    candidate writing idiomatic Python still resolves.
    """
    names: List[str] = []
    for pattern in (
        r"function\s+([A-Za-z_$][\w$]*)\s*\(",
        r"def\s+([A-Za-z_][\w]*)\s*\(",
        r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:function|\()",
        r"class\s+([A-Za-z_$][\w$]*)",
    ):
        names.extend(re.findall(pattern, starter or ""))

    expanded: List[str] = []
    for name in names:
        if name not in expanded:
            expanded.append(name)
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        if snake not in expanded:
            expanded.append(snake)

    # When a starter declares several helpers plus a `solution`/`solve` driver
    # (e.g. encode + decode + solution), the driver is what produces the final
    # answer. Grading the first-declared helper instead compares an intermediate
    # value against the expected output and fails a correct submission.
    if len(names) > 1:
        drivers = [n for n in expanded if n in ("solution", "solve")]
        if drivers:
            expanded = drivers + [n for n in expanded if n not in drivers]
    return expanded


def _is_class_starter(starter: str) -> bool:
    """True when the starter's solution entity is a class, not a function."""
    return bool(re.match(r"\s*class\s+[A-Za-z_$][\w$]*", starter or ""))


def _normalize_design_tests(tests: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Convert LeetCode design test cases into ``{ctor, ops, expected}`` form.

    The bank stores design cases in the two-parallel-array shape
    ``[["push", "getMin"], [[-2], []]]``: method names beside their argument
    lists. Returns None when a case does not match that shape, so the caller
    reports "not graded" rather than guessing at a binding.
    """
    normalized: List[Dict[str, Any]] = []
    for tc in tests:
        raw, expected = tc.get("input"), tc.get("expected")
        if not (isinstance(raw, list) and len(raw) == 2):
            return None
        op_names, op_args = raw
        if not (isinstance(op_names, list) and isinstance(op_args, list)):
            return None
        if len(op_names) != len(op_args) or not isinstance(expected, list):
            return None
        if len(expected) != len(op_names):
            return None

        ops: List[List[Any]] = []
        for name, args in zip(op_names, op_args):
            if not isinstance(name, str):
                return None
            ops.append([name] + (list(args) if isinstance(args, list) else [args]))
        # The bank's sequences begin at the first method call; the constructor
        # takes no arguments in every design problem present.
        normalized.append({"ctor": [], "ops": ops, "expected": expected})
    return normalized


@lru_cache(maxsize=1)
def _problem_bank_index() -> Dict[str, Dict[str, Any]]:
    """Index the 1000-problem bank by string ID, normalized to curated shape."""
    try:
        from app.services.coding_problems_data import PROBLEMS
    except Exception as exc:  # pragma: no cover - data module is static
        logger.warning(f"Coding problem bank unavailable: {exc}")
        return {}

    index: Dict[str, Dict[str, Any]] = {}
    for raw in PROBLEMS:
        starter = raw.get("starterCode", "") or ""
        tests = [
            {
                "input": _parse_json_ish(tc.get("input")),
                "expected": _parse_json_ish(tc.get("expected")),
            }
            for tc in raw.get("testCases", []) or []
        ]
        problem = {
            "id": str(raw.get("id")),
            "entry_point": _entry_point_from_starter(starter),
            "title": raw.get("title", "Untitled"),
            "difficulty": raw.get("difficulty", "Medium"),
            # NOT raw["topic"]: the bank's own topic field is mis-assigned —
            # "Two Sum" is filed under Tries, "Contains Duplicate" under
            # Segment Tree. The tags are accurate, so the topic is re-derived.
            "category": problem_enrichment.topic_for(raw.get("tags", [])),
            "tags": raw.get("tags", []),
            "companies": raw.get("companiesAsked", []),
            "description": raw.get("description", ""),
            "constraints": raw.get("constraints", ""),
            "examples": [
                {"input": str(tc.get("input", "")), "output": str(tc.get("expected", ""))}
                for tc in (raw.get("testCases") or [])[:2]
            ],
            # The bank only ships JavaScript starter code; other languages fall
            # back to the frontend's generic template.
            "starter_code": {"javascript": starter},
            "test_cases": tests,
            "hints": raw.get("hints", []),
            "time_complexity": raw.get("timeComplexity", ""),
            "space_complexity": raw.get("spaceComplexity", ""),
        }
        if _is_class_starter(starter):
            design_tests = _normalize_design_tests(tests)
            if design_tests is None:
                problem["grading"] = "unsupported"
                problem["grading_reason"] = (
                    f"'{problem['title']}' is a design problem whose test cases are "
                    "not in a replayable operation-sequence form, so it is executed "
                    "but not auto-graded."
                )
            else:
                problem["grading"] = "design"
                problem["test_cases"] = design_tests
        index[problem["id"]] = problem
    return index


def _lookup_problem_bank(problem_id: str) -> Optional[Dict[str, Any]]:
    return _problem_bank_index().get(str(problem_id))


def _entry_candidates(problem: Dict[str, Any]) -> List[str]:
    """Entry-point names declared for a problem, most specific first."""
    declared = problem.get("entry_point") or []
    if isinstance(declared, str):
        declared = [declared]
    # Generic names last, so a declared name always wins.
    return list(declared) + ["solve", "solution"]


def _with_static_starters(problem: Dict[str, Any]) -> Dict[str, Any]:
    """Fill in starter code for every language the signature can be typed in.

    Generated from the same inferred signature the grading harness calls, so the
    starter a candidate is shown always matches what the harness invokes. Only
    languages the problem does not already ship are filled — a hand-written
    starter is never overwritten by an inferred one.
    """
    if problem.get("grading") in ("design", "unsupported"):
        return problem

    cases = problem.get("test_cases") or []
    existing = problem.get("starter_code") or {}
    entries = _entry_candidates(problem)
    # Bank inputs are positional, so the readable parameter names live only in
    # the JavaScript starter. Reuse them across every generated language.
    signature = static_harness.infer_signature(cases)
    names = (
        _param_names_from_starter(existing.get("javascript", ""), len(signature.params))
        if signature
        else None
    )

    generated = {}
    for language in static_harness.starter_languages():
        if existing.get(language):
            continue
        starter = static_harness.build_starter(language, cases, entries, names)
        if starter:
            generated[language] = starter

    if not generated:
        return problem
    return {**problem, "starter_code": {**existing, **generated}}


_REVIEW_UNAVAILABLE = (
    "Automated code review is unavailable right now. Your test results above "
    "are unaffected."
)


# ── Code Execution Engine ──────────────────────────────────────────────────────


class CodeExecutorService:
    """Multi-language code execution engine backed by an isolated sandbox.

    Candidate code always runs through :mod:`app.services.code_sandbox`, which
    picks the first backend able to run the language (Piston, Docker, or — only
    with an explicit opt-in — a local subprocess). If no backend can run it, the
    request fails with an explanation; there is no simulated result.
    """

    def __init__(self) -> None:
        self.sandbox = get_sandbox()
        logger.info(
            f"CodeExecutorService initialised | sandbox backends: {self.sandbox.describe()}"
        )

    def get_curated_problems(self) -> List[Dict[str, Any]]:
        """Return curated coding problems with metadata."""
        return [
            {
                "id": p["id"],
                "title": p["title"],
                "difficulty": p["difficulty"],
                "category": p["category"],
                "tags": p["tags"],
                "companies": p["companies"],
                "description": p["description"],
                "constraints": p["constraints"],
                "examples": p["examples"],
                "follow_up": p.get("follow_up"),
                "hints": p.get("hints", []),
                "starter_code": _with_static_starters(p)["starter_code"],
            }
            for p in (problem_enrichment.enrich(c) for c in CURATED_PROBLEMS)
        ]

    def get_problem_catalog(
        self,
        search: str = "",
        difficulty: str = "",
        topic: str = "",
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """A browsable index of every problem: the curated set plus the bank.

        Deliberately *not* built on :meth:`get_curated_problems`, which returns
        six hand-written problems — a practice list needs the whole catalogue.
        Only listing metadata is returned; descriptions, examples and starter
        code are large and are fetched per problem on open.

        Filtering happens here rather than client-side because the full bank is
        ~1000 entries and shipping all of them on every list render is wasteful.
        """
        rows = self._catalog_rows()

        needle = (search or "").strip().lower()
        want_difficulty = (difficulty or "").strip().lower()
        want_topic = (topic or "").strip().lower()

        if needle or want_difficulty or want_topic:
            filtered = []
            for row in rows:
                if want_difficulty and row["difficulty"].lower() != want_difficulty:
                    continue
                if want_topic and row["category"].lower() != want_topic:
                    continue
                if needle and needle not in row["_haystack"]:
                    continue
                filtered.append(row)
            rows = filtered

        total = len(rows)
        start = max(offset, 0)
        window = rows[start : start + max(min(limit, 500), 1)]
        return {
            "problems": [{k: v for k, v in r.items() if not k.startswith("_")} for r in window],
            "total": total,
            "offset": start,
            "limit": limit,
            "topics": self._catalog_topics(),
        }

    @staticmethod
    @lru_cache(maxsize=1)
    def _catalog_rows() -> List[Dict[str, Any]]:
        """Listing metadata for curated + bank problems, curated first.

        A bank entry whose id collides with a curated one is dropped, so the
        hand-written version (which has multi-language starters and real
        examples) wins.
        """
        rows: List[Dict[str, Any]] = []
        seen: set[str] = set()

        def add(pid: str, title: str, difficulty: str, category: str,
                tags: List[str], companies: List[str], source: str) -> None:
            if pid in seen:
                return
            seen.add(pid)
            rows.append({
                "id": pid,
                "title": title,
                "difficulty": difficulty,
                "category": category,
                "tags": tags or [],
                "companies": companies or [],
                "source": source,
                "_haystack": " ".join(
                    [title, category, " ".join(tags or []), " ".join(companies or [])]
                ).lower(),
            })

        for p in CURATED_PROBLEMS:
            add(str(p["id"]), p["title"], p["difficulty"], p["category"],
                p.get("tags", []), p.get("companies", []), "curated")

        for pid, p in _problem_bank_index().items():
            add(pid, p["title"], p["difficulty"], p["category"],
                p.get("tags", []), p.get("companies", []), "bank")

        return rows

    @staticmethod
    @lru_cache(maxsize=1)
    def _catalog_topics() -> List[str]:
        """Distinct topics across the catalogue, for the practice-list filter."""
        return sorted({r["category"] for r in CodeExecutorService._catalog_rows() if r["category"]})

    def get_problem_by_id(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """Find a problem by ID in the curated set, then the 1000-problem bank.

        Returns None for an unknown ID so the caller can 404. This used to
        fabricate a stub problem whose single test case was
        ``{"input": "test_input_1", "expected": "passed"}`` — every unknown ID,
        including all 1000 numeric IDs in the problem bank, therefore reported a
        pass against a test that asserted nothing.
        """
        for p in CURATED_PROBLEMS:
            if p["id"] == problem_id:
                return problem_enrichment.enrich(_with_static_starters(p))
        found = _lookup_problem_bank(problem_id)
        return problem_enrichment.enrich(_with_static_starters(found)) if found else None

    def get_problem_source(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """The normalized problem *before* enrichment is applied.

        The batch statement generator needs this: feeding it the enriched
        description would make each rerun expand its own previous output
        instead of the original one-line source.
        """
        for p in CURATED_PROBLEMS:
            if p["id"] == problem_id:
                return _with_static_starters(p)
        found = _lookup_problem_bank(problem_id)
        return _with_static_starters(found) if found else None

    def _strip_ts_types(self, ts_code: str) -> str:
        """Strip TypeScript annotations so Node can run the source directly.

        Regex type-stripping is approximate; it covers the shapes that appear in
        starter code. A construct it mangles produces a real Node syntax error,
        which is reported as such rather than being silently graded.
        """
        clean = re.sub(
            r":\s*(?:number|string|boolean|any|void|unknown|never|object|Array<[^>]+>|[\w\[\]]+)(?=[,\)\s=;{])",
            "",
            ts_code,
        )
        clean = re.sub(r"interface\s+\w+\s*\{[^}]*\}", "", clean)
        clean = re.sub(r"type\s+\w+\s*=[^;]+;", "", clean)
        return clean

    def execute_code(
        self,
        problem_id: str,
        language: str,
        code: str,
    ) -> Dict[str, Any]:
        """Execute candidate code against a problem's test suite, in a sandbox.

        Every outcome is grounded in a real container run. When a language can
        be graded, results come from the program's own ``RESULTS_JSON`` line;
        when it can only be compiled, ``success`` is False and the reason says
        so. Nothing here reports a pass for code that did not run.
        """
        problem = self.get_problem_by_id(problem_id)
        if problem is None:
            return self._error(f"Unknown problem '{problem_id}'.")

        lang_key = resolve_language(language)
        spec = get_spec(language) if lang_key else None
        if not spec:
            return self._error(f"Unsupported language '{language}'.")

        if not code.strip():
            return self._error("No code submitted.")

        if not self.sandbox.available():
            return self._error(
                "Code execution is unavailable: no sandbox backend is reachable "
                "on this host. No tests were run."
            )

        if not self.sandbox.supports(spec):
            return self._error(
                f"{spec.name} execution is not provisioned on this host: no "
                f"available sandbox backend can run it. No tests were run."
            )

        test_cases = problem.get("test_cases") or []
        if not test_cases:
            return self._error(f"Problem '{problem_id}' has no test cases defined.")

        # Stateful/design problems have no generic grading strategy.
        if problem.get("grading") == "unsupported":
            return self._compile_only(
                spec, lang_key, code,
                reason=problem.get("grading_reason")
                or f"'{problem.get('title')}' is not auto-graded.",
            )

        if problem.get("grading") == "design":
            design_builder = DESIGN_HARNESS_BUILDERS.get(lang_key)
            if design_builder is None:
                return self._compile_only(
                    spec, lang_key, code,
                    reason=DESIGN_UNSUPPORTED.format(lang=spec.name),
                )
            source = self._strip_ts_types(code) if lang_key == "typescript" else code
            harness = design_builder(source, test_cases, self._entry_points(problem))
            return self._run_graded(spec, harness, test_cases)

        entry_points = self._entry_points(problem)

        builder = HARNESS_BUILDERS.get(lang_key)
        if builder is None:
            # Statically typed language. static_harness infers a signature from
            # the test data and generates a typed program around the submission;
            # it returns None when the data cannot be typed exactly, and we
            # compile without grading rather than guess at a binding.
            harness = static_harness.build_program(
                lang_key, test_cases, entry_points, code
            )
            if harness is not None:
                return self._run_graded(spec, harness, test_cases)
            return self._compile_only(
                spec, lang_key, code, reason=VERIFY_UNTYPEABLE.format(lang=spec.name)
            )

        source = self._strip_ts_types(code) if lang_key == "typescript" else code
        harness = builder(source, test_cases, entry_points)
        return self._run_graded(spec, harness, test_cases)

    @staticmethod
    def _entry_points(problem: Dict[str, Any]) -> List[str]:
        """Candidate function names for this problem, most specific first."""
        return _entry_candidates(problem)

    @staticmethod
    def _error(message: str) -> Dict[str, Any]:
        """A failure with no test results — never a pass."""
        return {
            "success": False,
            "passed": False,
            "runtime_ms": 0.0,
            "test_results": [],
            "stdout": "",
            "stderr": "",
            "error": message,
        }

    def _run_graded(
        self,
        spec: Any,
        harness: str,
        test_cases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run a harnessed program and parse its RESULTS_JSON verdict."""
        files = {spec.source_name: harness}
        try:
            result = self.sandbox.run(spec, files)
        except SandboxUnavailable as exc:
            return self._error(str(exc))
        except Exception as exc:
            logger.exception("Sandbox run failed")
            return self._error(f"Execution failed: {exc}")

        if result.timed_out:
            return {**self._error(result.stderr), "runtime_ms": result.duration_ms}

        stderr = result.stderr

        marker = "RESULTS_JSON:"
        if marker not in result.stdout:
            # No verdict line ⇒ compilation failed, the program crashed, the
            # entry point was missing, or it was killed. Report the diagnostic,
            # never a grade.
            detail = (stderr or result.stdout or "").strip()
            if spec.compile_cmd and not result.compile_ok:
                message = f"Compilation Error:\n{detail}"
            else:
                message = detail or "Execution produced no test results."
            return {
                **self._error(message),
                "stdout": result.stdout,
                "stderr": stderr,
                "runtime_ms": result.duration_ms,
            }

        # rpartition, not partition: candidate code could print a forged
        # RESULTS_JSON line of its own, but the harness always prints after every
        # test has run, so the *last* occurrence is the harness's verdict.
        head, _, tail = result.stdout.rpartition(marker)
        try:
            results = json.loads(tail.strip().splitlines()[0])
        except (ValueError, IndexError) as exc:
            return {
                **self._error(f"Could not parse test results: {exc}"),
                "stdout": result.stdout,
                "stderr": stderr,
                "runtime_ms": result.duration_ms,
            }

        if not isinstance(results, list) or len(results) != len(test_cases):
            # A submission can print its own RESULTS_JSON line to forge a
            # verdict. We can't stop it printing, but we refuse to accept a
            # result set that doesn't match the suite we asked it to run.
            return {
                **self._error(
                    f"Harness reported {len(results) if isinstance(results, list) else 'invalid'} "
                    f"results for {len(test_cases)} test cases."
                ),
                "stdout": head.strip(),
                "stderr": stderr,
                "runtime_ms": result.duration_ms,
            }

        return {
            "success": True,
            "passed": bool(results) and all(r.get("passed") is True for r in results),
            "runtime_ms": result.duration_ms,
            "test_results": results,
            "stdout": head.strip(),
            "stderr": stderr,
            "error": None,
        }

    def _compile_only(
        self,
        spec: Any,
        lang_key: str,
        code: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Compile (or syntax-check) without grading, and say so explicitly.

        Used for statically typed languages and stateful design problems. The
        response is deliberately ``success=False`` with an empty
        ``test_results``: a green checkmark here would be the same lie this
        module previously told.

        The submission is wrapped in its language's prelude first. Starter code
        for these languages is function-only — the harness normally supplies the
        ``package`` clause, imports and ``main`` — so compiling it verbatim would
        fail on the harness's conventions rather than on the candidate's code.
        """
        files = {spec.source_name: static_harness.wrap_standalone(lang_key, code)}
        try:
            if spec.compile_cmd:
                built = self.sandbox.run(spec, files, compile_only=True)
                if not built.compile_ok or built.exit_code != 0:
                    return {
                        **self._error(f"Compilation Error:\n{built.stderr.strip()}"),
                        "stderr": built.stderr,
                        "runtime_ms": built.duration_ms,
                    }
                note = "Compiled successfully. "
                elapsed = built.duration_ms
            else:
                note = ""
                elapsed = 0.0
        except SandboxUnavailable as exc:
            return self._error(str(exc))
        except Exception as exc:
            logger.exception("Sandbox compile failed")
            return self._error(f"Execution failed: {exc}")

        return {
            "success": False,
            "passed": False,
            "runtime_ms": elapsed,
            "test_results": [],
            "stdout": "",
            "stderr": "",
            "error": note + reason,
        }

    def evaluate_ai_code_quality(
        self,
        problem_title: str,
        language: str,
        code: str,
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Use LLM to generate Big-O complexity & code quality feedback.

        Bounded by `timeout_seconds` (default `CODE_REVIEW_TIMEOUT_SECONDS`).
        The review is the optional half of a submission — the test verdict is
        the part the candidate is waiting on — so an LLM that is slow, down, or
        unconfigured must not hold the response. It previously could: a submit
        took 65 seconds to come back and then reported no review anyway.
        """
        prompt = (
            f"Analyze the following {language.capitalize()} code for the problem '{problem_title}':\n\n"
            f"```\n{code}\n```\n\n"
            "Provide a brief evaluation with:\n"
            "1. Time Complexity (Big-O)\n"
            "2. Space Complexity (Big-O)\n"
            "3. Code Readability score (0-100)\n"
            "4. Two actionable optimization / clean code suggestions."
        )

        def _ask() -> Optional[str]:
            return get_llm().generate(
                prompt=prompt,
                system_prompt="You are an expert technical interviewer evaluating candidate code.",
                temperature=0.3,
                max_tokens=500,
            )

        budget = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.CODE_REVIEW_TIMEOUT_SECONDS
        )
        # A daemon pool so an overrunning call is abandoned rather than joined
        # at shutdown; the future is left to finish and discarded.
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="code-review")
        try:
            reply = executor.submit(_ask).result(timeout=budget)
            if reply:
                return {"analysis": reply}
            return {"analysis": _REVIEW_UNAVAILABLE}
        except FuturesTimeout:
            logger.warning(f"AI code evaluation exceeded {budget}s; returning verdict without it")
            return {"analysis": _REVIEW_UNAVAILABLE}
        except Exception as exc:
            # The old fallback asserted a fixed O(N)/O(N), a score of 88, and
            # "Code passes structural test cases" for code it had never seen
            # analysed and tests it had not consulted. Say nothing instead of
            # something invented.
            logger.warning(f"AI code evaluation unavailable: {exc}")
            return {"analysis": _REVIEW_UNAVAILABLE}
        finally:
            executor.shutdown(wait=False)


_code_executor_instance: Optional[CodeExecutorService] = None


def get_code_executor_service() -> CodeExecutorService:
    global _code_executor_instance
    if _code_executor_instance is None:
        _code_executor_instance = CodeExecutorService()
    return _code_executor_instance
