"""Tests for the coding sandbox and grading harnesses.

The central property under test is negative: no code path may report a passing
test for code that was not actually executed. The previous implementation
string-matched source for keywords like ``for`` and ``length`` and copied
``expected`` into ``actual``, so boilerplate passed and correct-but-unusual
solutions failed. These tests pin that behaviour shut.

The Docker-backed tests are skipped when no sandbox is available; the logic
tests always run.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

from app.services import code_runners
from app.services.code_executor_service import (
    CURATED_PROBLEMS,
    CodeExecutorService,
    _entry_point_from_starter,
    _parse_json_ish,
    _problem_bank_index,
)
from app.services import static_harness
from app.services import problem_enrichment
from app.services.static_harness import infer_signature
from app.services.code_sandbox import (
    ContainerSandbox,
    Judge0Sandbox,
    LayeredSandbox,
    PistonSandbox,
    SandboxResult,
    SandboxUnavailable,
    get_sandbox,
)

BOILERPLATE = {
    "java": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n",
    "cpp": "#include <vector>\nusing namespace std;\nclass Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {};\n    }\n};\n",
    "go": "package main\n\nfunc twoSum(nums []int, target int) []int {\n    return []int{}\n}\n",
    "rust": "pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {\n    vec![]\n}\n",
    "haskell": "twoSum :: [Int] -> Int -> [Int]\ntwoSum nums target = []\n",
}

sandbox_required = pytest.mark.skipif(
    not get_sandbox().available(),
    reason="Docker sandbox unavailable",
)


def _service() -> CodeExecutorService:
    return CodeExecutorService()


# ── Never fake a pass ────────────────────────────────────────────────────────


@pytest.mark.parametrize("language", sorted(BOILERPLATE))
def test_boilerplate_never_reports_pass(language: str) -> None:
    """The core regression: empty stubs used to pass every test case.

    `_run_compiled_fallback` searched the source for any of `for`, `while`,
    `map`, `length`, `size`… and on a hit copied `expected` into `actual` and set
    passed=True without compiling anything. Several of these stubs contain such
    a token in a type name or signature.
    """
    result = _service().execute_code("two-sum", language, BOILERPLATE[language])
    assert result["passed"] is False
    assert not any(r.get("passed") for r in result.get("test_results", []))


def test_unavailable_sandbox_reports_error_not_pass(monkeypatch) -> None:
    """With no backend, execution must fail loudly rather than fabricate a pass.

    The old JS runner returned `passed: True` with a full set of passing test
    results when Node was missing — which is the state of the production image.
    """
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: False)

    result = svc.execute_code("two-sum", "python", "def two_sum(nums, target):\n    return [0, 1]\n")

    assert result["success"] is False
    assert result["passed"] is False
    assert result["test_results"] == []
    assert "unavailable" in result["error"].lower()


def test_missing_image_reports_error_not_pass(monkeypatch) -> None:
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: False)

    result = svc.execute_code("two-sum", "go", BOILERPLATE["go"])

    assert result["success"] is False
    assert result["passed"] is False
    assert result["test_results"] == []


def test_untypeable_problem_is_not_graded(monkeypatch) -> None:
    """A problem whose tests cannot be typed must compile, not claim a verdict.

    Static languages are graded through a signature inferred from the test data
    (see :mod:`app.services.static_harness`). Where that inference declines —
    floats in the return, tree nodes encoded as nulls, mixed lists — the answer
    has to be "compiled, not graded" rather than a guess at the binding.
    """
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    class _Ok:
        exit_code, stdout, stderr, timed_out, duration_ms = 0, "", "", False, 5.0
        compile_ok = True

    monkeypatch.setattr(svc.sandbox, "run", lambda *a, **k: _Ok())

    untypeable = next(
        pid
        for pid, p in _problem_bank_index().items()
        if p.get("grading") not in ("design", "unsupported")
        and not p.get("sql_schema")
        and infer_signature(p["test_cases"]) is None
    )
    result = svc.execute_code(untypeable, "java", "class Solution {}")

    assert result["success"] is False
    assert result["passed"] is False
    assert result["test_results"] == []
    assert "not graded" in result["error"].lower()


def test_no_verdict_line_is_a_failure(monkeypatch) -> None:
    """A program that prints nothing must not be graded as passing."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    class _Silent:
        exit_code, stdout, stderr = 1, "", "Traceback: boom"
        timed_out, duration_ms = False, 5.0

    monkeypatch.setattr(svc.sandbox, "run", lambda *a, **k: _Silent())

    result = svc.execute_code("two-sum", "python", "def two_sum(a, b):\n    return []\n")

    assert result["success"] is False
    assert result["passed"] is False
    assert "boom" in result["error"]


def test_result_count_mismatch_is_rejected(monkeypatch) -> None:
    """A harness reporting fewer results than tests must not pass.

    Guards against a submission printing its own RESULTS_JSON line to forge a
    verdict; a truncated or padded list is refused rather than trusted.
    """
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    forged = json.dumps([{"passed": True, "actual": 1, "expected": 1}])

    class _Forged:
        exit_code, stdout = 0, "RESULTS_JSON:" + forged
        stderr, timed_out, duration_ms = "", False, 5.0

    monkeypatch.setattr(svc.sandbox, "run", lambda *a, **k: _Forged())

    result = svc.execute_code("two-sum", "python", "print('hi')")

    assert result["success"] is False
    assert result["passed"] is False


def test_timeout_reports_failure(monkeypatch) -> None:
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    class _Timeout:
        exit_code, stdout, stderr = 124, "", "Time Limit Exceeded (10s)"
        timed_out, duration_ms = True, 10_000.0

    monkeypatch.setattr(svc.sandbox, "run", lambda *a, **k: _Timeout())

    result = svc.execute_code("two-sum", "python", "while True: pass")

    assert result["success"] is False
    assert result["passed"] is False


def test_sandbox_unavailable_exception_is_not_a_pass(monkeypatch) -> None:
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    def _boom(*args, **kwargs):
        raise SandboxUnavailable("daemon died mid-run")

    monkeypatch.setattr(svc.sandbox, "run", _boom)

    result = svc.execute_code("two-sum", "python", "def two_sum(a, b): return [0, 1]")

    assert result["success"] is False
    assert result["passed"] is False
    assert result["test_results"] == []


# ── Problem lookup ───────────────────────────────────────────────────────────


def test_unknown_problem_is_not_a_stub_pass() -> None:
    """Unknown IDs used to yield a stub whose only test asserted "passed"."""
    result = _service().execute_code("no-such-problem-xyz", "python", "print(1)")

    assert result["success"] is False
    assert result["passed"] is False
    assert "unknown problem" in result["error"].lower()


def test_problem_bank_ids_resolve() -> None:
    """The 1000-problem bank must be reachable, not fall through to a stub."""
    svc = _service()
    assert svc.get_problem_by_id("1") is not None
    problem = svc.get_problem_by_id("1")
    assert problem["test_cases"], "bank problem should carry real test cases"
    # Inputs arrive as JSON strings in the bank and must be decoded to values.
    assert problem["test_cases"][0]["input"] == [[2, 7, 11, 15], 9]
    assert problem["test_cases"][0]["expected"] == [0, 1]


# ── Statement enrichment ──────────────────────────────────────────────────────


def test_enriched_examples_match_graded_test_cases() -> None:
    """A statement must never show an example the grader does not assert.

    Examples are replayed from ``test_cases`` rather than authored, so a
    generated statement cannot drift from what is actually run. This is the
    invariant that makes the LLM layer safe to enable.
    """
    svc = _service()
    for pid in ("1", "2", "57", "300"):
        problem = svc.get_problem_by_id(pid)
        cases = problem["test_cases"][:3]
        assert len(problem["examples"]) == len(cases), pid
        for example, case in zip(problem["examples"], cases):
            assert str(case["expected"]) in example["output"] or example[
                "output"
            ] == problem_enrichment._render_value(case["expected"]), pid


def test_enrichment_adds_bounds_the_bank_omitted() -> None:
    """Every bank problem ships one constraint line; a judge states several."""
    problem = _service().get_problem_by_id("1")
    lines = [line for line in problem["constraints"].split("\n") if line.strip()]

    assert len(lines) >= 2, f"expected several constraints, got {lines}"
    # The bank's own line is trustworthy and must survive verbatim.
    assert any("nums.length" in line for line in lines)
    # The value bound it never stated must now be present.
    assert any("nums[i]" in line for line in lines)


def test_enrichment_keeps_existing_constraint_and_does_not_duplicate() -> None:
    """A dimension the bank already bounded is not restated in other words."""
    problem = _service().get_problem_by_id("2")
    lines = [line for line in problem["constraints"].split("\n") if line.strip()]

    length_bounds = [line for line in lines if "nums.length" in line]
    assert len(length_bounds) == 1, f"length bound stated twice: {lines}"


def test_topic_is_derived_from_tags_not_the_banks_field() -> None:
    """The bank's own topic field is mis-assigned and must not be trusted.

    Two Sum ships ``topic="Tries"`` and Contains Duplicate ``"Segment Tree"``.
    The tags are accurate, so the topic is re-derived from them.
    """
    svc = _service()
    assert svc.get_problem_by_id("1")["category"] == "Arrays & Hashing"
    assert svc.get_problem_by_id("2")["category"] == "Arrays & Hashing"

    assert problem_enrichment.topic_for(["array", "dp"]) == "Dynamic Programming"
    assert problem_enrichment.topic_for(["binary-search"]) == "Binary Search"
    assert problem_enrichment.topic_for([]) == "Arrays & Hashing"


def test_enriched_statement_gains_the_sections_a_judge_prints() -> None:
    """The complaint being fixed: bare 131-character statements.

    Asserts *structure*, not length. Length is the wrong measure here — the
    derived layer earlier padded statements with a labelled Input/Output/
    Function-signature block that made them longer and worse, and removing it
    made them shorter and better. What it can honestly guarantee is that every
    problem states its bounds, its return, its optimal complexity, and shows a
    figure where the input has a drawable shape.

    Full narrative depth — LeetCode's "where the width of each bar is 1" — is
    domain knowledge no amount of test data reveals. That comes from the
    generated layer in ``data/problem_enrichment.json``; see
    ``scripts/enrich_problems.py``.
    """
    svc = _service()
    for pid in ("1", "2", "53", "57"):
        problem = svc.get_problem_by_id(pid)

        assert problem["description"].strip(), pid
        assert problem["follow_up"], f"{pid}: no complexity follow-up"
        assert len(problem["examples"]) >= 2, pid
        constraints = [c for c in problem["constraints"].split("\n") if c.strip()]
        assert len(constraints) >= 2, f"{pid}: only {constraints}"


# These two exercise the *derived* layer, so they call build_baseline on the
# pre-enrichment source rather than reading the finished problem. Both ids now
# carry an authored statement, and going through get_problem_by_id would test
# the hand-written prose instead of the derivation it is meant to cover.


def test_statement_does_not_restate_what_the_source_already_says() -> None:
    """The derived opener must not duplicate a body that already names its args.

    Two Sum's own text starts "Given an array of integers `nums` and an integer
    `target`, …". Prepending a generated "You are given …" printed the same
    sentence twice.
    """
    source = _service().get_problem_source("1")
    description = problem_enrichment.build_baseline(source)["description"]

    assert description.count("`target`") <= 2, description
    assert not description.startswith("You are given"), description
    # It already says "return indices…", so no second return sentence.
    assert "Return array of integers" not in description


def test_statement_adds_an_opener_when_the_source_lacks_one() -> None:
    """A body that dives straight into the rule does get the derived opener."""
    source = _service().get_problem_source("53")  # histogram
    description = problem_enrichment.build_baseline(source)["description"]

    assert description.startswith("You are given an integer array `heights`"), description


# ── Figures ───────────────────────────────────────────────────────────────────


def test_histogram_problem_is_drawn_as_bars() -> None:
    """A histogram is illustrated with a histogram, as a real judge does."""
    problem = _service().get_problem_by_id("53")
    diagram = problem["examples"][0]["diagram"]

    assert diagram["kind"] == "bars"
    assert diagram["label"] == "heights"
    # The figure is the example's own input, so it cannot contradict the text.
    assert diagram["values"] == problem["test_cases"][0]["input"][0]


def test_only_the_first_example_carries_a_figure() -> None:
    """Drawing all three pushes the constraints off the bottom of the pane."""
    for pid in ("1", "53"):
        examples = _service().get_problem_by_id(pid)["examples"]
        assert examples[0].get("diagram")
        assert all(not e.get("diagram") for e in examples[1:]), pid


def test_matrix_problem_is_drawn_as_a_grid() -> None:
    svc = _service()
    found = None
    for pid in list(_problem_bank_index())[:400]:
        problem = svc.get_problem_by_id(pid)
        diagram = problem["examples"][0].get("diagram") if problem["examples"] else None
        if diagram and diagram["kind"] == "grid":
            found = diagram
            break

    assert found, "no matrix problem produced a grid figure"
    widths = {len(row) for row in found["rows"]}
    assert len(widths) == 1, "a ragged grid is not a grid"


def test_oversized_inputs_get_no_figure() -> None:
    """A 60-bar chart in a 380px pane is a grey smear — text is better."""
    from app.services import problem_diagrams

    problem = {"tags": [], "title": "Big"}
    assert problem_diagrams.build_diagram(problem, [list(range(200))], ["nums"]) is None
    assert problem_diagrams.build_diagram(problem, [[[1] * 40] * 40], ["grid"]) is None


def test_tree_problem_is_drawn_as_a_tree() -> None:
    """A level-order encoding with nulls gets a tree picture, not nothing.

    The bank stores trees as flat arrays where `null` marks a missing child
    (`[3,9,20,null,null,15,7]`), the same encoding LeetCode prints. Before the
    tree kind existed those nulls failed the int-cell check and the problem
    rendered no figure at all.
    """
    problem = _service().get_problem_by_id("72")  # Maximum Depth of Binary Tree
    diagram = problem["examples"][0]["diagram"]

    assert diagram["kind"] == "tree"
    # Nulls make the encoding untypeable, so the starter's parameter name is
    # unrecoverable — the figure must fall back to "root" rather than "input".
    assert diagram["label"] == "root"
    # The figure is the example's own input, so it cannot contradict the text.
    assert diagram["values"] == problem["test_cases"][0]["input"][0]
    assert diagram["values"] == [3, 9, 20, None, None, 15, 7]


def test_level_order_problem_is_drawn_as_a_tree() -> None:
    """The other canonical tree problem — same encoding, same figure."""
    problem = _service().get_problem_by_id("77")
    diagram = problem["examples"][0]["diagram"]

    assert diagram["kind"] == "tree"
    assert diagram["values"] == [3, 9, 20, None, None, 15, 7]


def test_all_int_tree_encoding_is_still_a_tree() -> None:
    """A complete tree like `[4,2,7,1,3,6,9]` carries no nulls but is a tree.

    Invert Binary Tree's first example is a full binary tree, so every slot is
    occupied. It must be promoted to a tree figure by its root-named parameter
    (and its perfect-tree length), not demoted to a plain cell strip.
    """
    problem = _service().get_problem_by_id("74")  # Invert Binary Tree
    diagram = problem["examples"][0]["diagram"]

    assert diagram["kind"] == "tree"
    assert diagram["values"] == [4, 2, 7, 1, 3, 6, 9]


def test_sorted_inorder_array_is_not_drawn_as_a_tree() -> None:
    """Validate BST in this bank is a sorted-array check (param `inorder`).

    Its input `[1,2,3,4,5]` is a flat increasing list, not a level-order
    encoding. Drawing it as a heap would misread a sorted list as a tree.
    """
    problem = _service().get_problem_by_id("78")
    diagram = problem["examples"][0].get("diagram")

    assert diagram is None or diagram["kind"] != "tree"


def test_tree_diagram_respects_param_name_and_perfect_length() -> None:
    """The promotion rule: nulls ⇒ tree, else root-named param or 2^k-1 length."""
    from app.services import problem_diagrams

    tree_problem = {"tags": ["tree", "recursion"], "title": "Maximum Depth of Binary Tree"}
    diagram = problem_diagrams.build_diagram(
        tree_problem, [[3, 9, 20, None, None, 15, 7]], ["root"]
    )
    assert diagram == {"kind": "tree", "values": [3, 9, 20, None, None, 15, 7], "label": "root"}

    # A complete tree under a non-root name is still a tree (length 3 = 2^2-1).
    assert problem_diagrams.build_diagram(
        tree_problem, [[1, 2, 3]], ["p"]
    )["kind"] == "tree"

    # A sorted array under a non-root name must not be promoted.
    array_problem = {"tags": ["tree", "bst", "recursion"], "title": "Validate Binary Search Tree"}
    not_tree = problem_diagrams.build_diagram(array_problem, [[1, 2, 3, 4, 5]], ["inorder"])
    assert not_tree is None or not_tree["kind"] != "tree"


def test_oversized_tree_encodings_get_no_figure() -> None:
    """A 16-slot tree is past what reads at pane width — text is better."""
    from app.services import problem_diagrams

    problem = {"tags": ["tree"], "title": "Big Tree"}
    # One null keeps it out of the int-cell strip, so a 16-slot encoding must
    # produce no figure at all rather than a degraded one.
    encoding = list(range(15)) + [None]
    assert len(encoding) == 16
    assert problem_diagrams.build_diagram(problem, [encoding], ["root"]) is None


def test_figures_never_invent_values() -> None:
    """Whatever is drawn must be present in the graded input, verbatim."""
    svc = _service()
    checked = 0
    for pid in list(_problem_bank_index())[:250]:
        problem = svc.get_problem_by_id(pid)
        if not problem["examples"]:
            continue
        diagram = problem["examples"][0].get("diagram")
        if not diagram:
            continue
        raw = problem["test_cases"][0]["input"]
        first = (raw if isinstance(raw, list) else [raw])[0]
        if diagram["kind"] == "grid":
            assert [[str(c) for c in row] for row in first] == diagram["rows"], pid
        elif diagram["kind"] == "bars":
            assert list(first) == diagram["values"], pid
        else:
            assert [str(v) for v in first] == [str(v) for v in diagram["values"]], pid
        checked += 1
    assert checked > 50, f"only {checked} figures checked — coverage too low"


def test_derived_bounds_are_not_tightened_to_the_sample_data() -> None:
    """A bound must not be read straight off the tests.

    The recorded cases are a sample, not the boundary. Snapping to exactly what
    they contain would licence solutions that are wrong on the real problem —
    an O(max_value) bucket sort looks correct under ``-15 <= nums[i] <= 15``.
    """
    problem = _service().get_problem_by_id("742")  # trap(), heights 0..3
    values = [v for case in problem["test_cases"] for v in case["input"][0]]
    assert max(values) < 100, "fixture assumption: sample values are small"

    bound = [line for line in problem["constraints"].split("\n") if "height[i]" in line]
    assert bound, problem["constraints"]
    assert "10^4" in bound[0], f"bound tightened to the sample: {bound[0]}"


def test_enrichment_survives_a_missing_store() -> None:
    """With no generated file the derived baseline must still stand alone."""
    problem = _service().get_problem_by_id("1")
    assert problem["description"]
    assert problem["constraints"]
    assert problem["examples"]
    assert problem["follow_up"], "follow-up is derived, not generated"


def test_malformed_store_entry_is_ignored(monkeypatch) -> None:
    """A bad generated record must not blank out a working statement."""
    monkeypatch.setattr(
        problem_enrichment,
        "_store",
        lambda: {"1": {"statement": "too short", "explanations": "not a list"}},
    )
    problem = _service().get_problem_by_id("1")
    # Below the length floor, so the baseline is kept instead.
    assert "too short" not in problem["description"]
    assert problem["description"].startswith("Given an array of integers")
    assert problem["examples"]


def test_generated_statement_replaces_the_baseline(monkeypatch) -> None:
    """A well-formed record is used, and its explanations reach the examples."""
    statement = (
        "You are given an array of integers and a target value. " * 6
    ).strip()
    monkeypatch.setattr(
        problem_enrichment,
        "_store",
        lambda: {
            "1": {
                "statement": statement,
                "explanations": ["2 + 7 = 9, so the answer is [0, 1]."],
                "constraints": ["Exactly one valid answer exists."],
                "follow_up": "Can you do it in one pass?",
            }
        },
    )
    problem = _service().get_problem_by_id("1")

    assert problem["description"] == statement
    assert problem["examples"][0]["explanation"] == "2 + 7 = 9, so the answer is [0, 1]."
    assert "Exactly one valid answer exists." in problem["constraints"]
    assert problem["follow_up"] == "Can you do it in one pass?"
    # Examples still come from the graded cases, never from the record.
    assert problem["examples"][0]["output"] == "[0, 1]"


def test_exact_constraints_replace_the_widened_derived_ones(monkeypatch) -> None:
    """An authored entry knows the real bounds; the derived ones only guess wide.

    ``_snap`` deliberately rounds up off the sample data, so the derived clause
    for Two Sum is a non-negative ``0 <= nums[i] <= 10^4``. The real problem
    allows negatives. ``constraints_exact`` must therefore override rather than
    append — appending would leave two clauses that contradict each other.
    """
    monkeypatch.setattr(
        problem_enrichment,
        "_store",
        lambda: {
            "1": {
                "constraints_exact": [
                    "2 <= nums.length <= 10^4",
                    "-10^9 <= nums[i] <= 10^9",
                ]
            }
        },
    )
    problem = _service().get_problem_by_id("1")

    assert problem["constraints"] == "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9"
    assert "0 <= nums[i]" not in problem["constraints"], "derived bound was not replaced"


def test_empty_exact_constraints_leave_the_derived_bounds_alone(monkeypatch) -> None:
    """An override that overrides nothing must not blank the constraints out."""
    monkeypatch.setattr(
        problem_enrichment, "_store", lambda: {"1": {"constraints_exact": []}}
    )
    problem = _service().get_problem_by_id("1")
    assert "nums.length" in problem["constraints"]


def test_authored_hints_reach_the_problem(monkeypatch) -> None:
    monkeypatch.setattr(
        problem_enrichment,
        "_store",
        lambda: {"1": {"hints": ["Use a hash map.", "  ", ""]}},
    )
    problem = _service().get_problem_by_id("1")
    assert problem["hints"] == ["Use a hash map."], "blank hints should be dropped"


# ── The authored overlay that actually ships ─────────────────────────────────


def _authored_ids() -> list:
    """Ids in the shipped overlay that were hand-written, not LLM-generated."""
    return [
        pid
        for pid, entry in problem_enrichment._store().items()
        if isinstance(entry, dict) and entry.get("source") == "authored"
    ]


def test_authored_overlay_is_present() -> None:
    """`data/problem_enrichment.json` ships with the hand-written statements.

    If this fails, run ``python scripts/build_authored_statements.py``.
    """
    assert len(_authored_ids()) >= 30


def test_authored_statements_never_contradict_the_graded_cases() -> None:
    """The invariant the whole enrichment design rests on.

    A statement may not write its own worked example. Examples are replayed
    from ``test_cases``, so an authored one could disagree with what the grader
    asserts, and a candidate reading the pane would have no way to tell which
    is authoritative. Authored prose may only *annotate* recorded values.
    """
    service = _service()
    for pid in _authored_ids():
        problem = service.get_problem_by_id(pid)
        source = service.get_problem_source(pid)
        assert problem and source

        for marker in ("Example 1:", "\nInput:", "\nOutput:", "\nConstraints:"):
            assert marker not in problem["description"], (
                f"problem {pid} spells out its own example block; those are "
                f"rendered from the recorded test cases"
            )

        # Every rendered example is still the graded one.
        cases = (source.get("test_cases") or [])[:3]
        assert len(problem["examples"]) == len(cases)
        for example, case in zip(problem["examples"], cases):
            assert example["output"] == problem_enrichment._render_value(case.get("expected"))
            assert example.get("explanation"), (
                f"problem {pid} has an unannotated example — authored entries "
                f"must explain every case that renders"
            )


def test_authored_problems_carry_the_full_judge_furniture() -> None:
    """Statement, bounds, follow-up and hints — the four things a judge prints."""
    service = _service()
    for pid in _authored_ids():
        problem = service.get_problem_by_id(pid)
        assert len(problem["description"]) >= 120, f"problem {pid} statement is thin"
        assert len(problem["constraints"].split("\n")) >= 1
        assert problem["follow_up"], f"problem {pid} has no follow-up"
        assert len(problem["hints"] or []) >= 2, f"problem {pid} has fewer than 2 hints"


def test_the_histogram_statement_states_the_rule_leetcode_states() -> None:
    """The specific gap that motivated the authored layer.

    "Find the largest rectangular area in a histogram" is not a specification —
    it never says the bars have width 1, which is the fact the whole problem
    turns on. No derivation recovers that from test data; it has to be written.
    """
    problem = _service().get_problem_by_id("53")
    assert "width of each bar is 1" in problem["description"]
    assert problem["examples"][0]["diagram"]["kind"] == "bars"
    assert problem["examples"][0]["diagram"]["values"] == [2, 1, 5, 6, 2, 3]


def test_curated_problems_declare_entry_points() -> None:
    """Coding problems name the function the harness calls; database problems
    answer with a query, so they declare no entry point by design."""
    for problem in CURATED_PROBLEMS:
        if problem.get("sql_schema"):
            continue
        assert problem.get("entry_point"), f"{problem['id']} has no entry_point"


def test_problem_bank_entry_points_recovered() -> None:
    index = _problem_bank_index()
    assert index, "problem bank should not be empty"
    missing = [
        pid
        for pid, p in index.items()
        if not p.get("entry_point") and not p.get("sql_schema")
    ]
    assert not missing, f"no entry point recovered for {missing[:5]}"


def test_parse_json_ish_keeps_plain_strings() -> None:
    assert _parse_json_ish("[[1,2],3]") == [[1, 2], 3]
    assert _parse_json_ish("true") is True
    assert _parse_json_ish("hello") == "hello"
    assert _parse_json_ish(7) == 7


def test_entry_point_from_starter_offers_snake_case() -> None:
    names = _entry_point_from_starter("function twoSum(nums, target) {}")
    assert "twoSum" in names
    assert "two_sum" in names


def test_entry_point_prefers_driver_over_helpers() -> None:
    """A multi-function starter must grade its driver, not its first helper.

    "Encode and Decode Strings" declares encode + decode + solution. Grading
    ``encode`` compares the encoded intermediate ("5#hello5#world") against the
    round-tripped expectation and fails a correct submission.
    """
    starter = (
        "function encode(strs) {\n  // encode\n}\n"
        "function decode(s) {\n  // decode\n}\n"
        "function solution(strs) {\n  return decode(encode(strs));\n}\n"
    )
    names = _entry_point_from_starter(starter)
    assert names[0] == "solution"
    assert "encode" in names


def test_single_function_starter_keeps_its_name_first() -> None:
    assert _entry_point_from_starter("function intersect(a, b) {}")[0] == "intersect"


# ── Problem bank integrity ───────────────────────────────────────────────────


def test_problem_bank_ids_are_unique() -> None:
    """Duplicate IDs made the backend serve a different problem than the UI showed.

    ``generate_1000_problems.py`` numbered themed variants with
    ``len(NEW_PROBLEMS)+1`` while keeping the originals that already held those
    IDs. 1000 problems collapsed to 918 and 82 IDs resolved to the wrong
    problem — id 132 displayed "Min Stack" but graded "Optimal Ticket Movies"
    against a matrix test suite.
    """
    from app.services.coding_problems_data import PROBLEMS

    ids = [p["id"] for p in PROBLEMS]
    assert len(ids) == len(set(ids)), f"{len(ids) - len(set(ids))} duplicate IDs"
    assert len(_problem_bank_index()) == len(PROBLEMS)


def test_no_problem_ships_its_own_solution_as_starter_code() -> None:
    """Six problems shipped a complete prefix-sum solution as starter code.

    A themed variant copies its base problem's starterCode verbatim, so one
    leaky base problem meant untouched boilerplate passed every test case.
    """
    from app.services.coding_problems_data import PROBLEMS

    leaked = [
        p["id"] for p in PROBLEMS
        if p["starterCode"].strip() == p["solutionCode"].strip()
    ]
    assert not leaked, f"starterCode equals solutionCode for {leaked[:10]}"


def test_design_problems_are_graded_or_declared_ungraded() -> None:
    """Class-based problems must route to the design harness, not be called as
    functions — doing so raised "Class constructor cannot be invoked without
    'new'" and failed every correct submission."""
    index = _problem_bank_index()
    design = [p for p in index.values() if p.get("grading") == "design"]
    assert design, "expected class-based design problems in the bank"
    for problem in design:
        for case in problem["test_cases"]:
            assert set(case) == {"ctor", "ops", "expected"}
            assert len(case["ops"]) == len(case["expected"])


@pytest.mark.parametrize("language", ["java", "go", "rust"])
def test_design_problem_is_not_graded_for_unsupported_language(
    monkeypatch, language: str
) -> None:
    """Design grading replays an op sequence, which needs a dynamic runtime."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    class _Ok:
        exit_code, stdout, stderr, timed_out, duration_ms = 0, "", "", False, 5.0
        compile_ok = True

    monkeypatch.setattr(svc.sandbox, "run", lambda *a, **k: _Ok())

    design_id = next(
        pid for pid, p in _problem_bank_index().items() if p.get("grading") == "design"
    )
    result = svc.execute_code(design_id, language, "class Foo {}")

    assert result["passed"] is False
    assert "not graded" in result["error"].lower()



# ── Language resolution ──────────────────────────────────────────────────────


def test_language_aliases_resolve() -> None:
    assert code_runners.resolve_language("Python3") == "python"
    assert code_runners.resolve_language("JS") == "javascript"
    assert code_runners.resolve_language("c++") == "cpp"
    assert code_runners.resolve_language("C#") == "csharp"
    assert code_runners.resolve_language("klingon") is None


def test_every_frontend_language_is_known() -> None:
    """The UI offers 15 languages; each must resolve to a real spec.

    Previously ten of them routed to a keyword-matching simulator.
    """
    offered = [
        "python", "javascript", "typescript", "java", "cpp", "csharp", "go",
        "rust", "ruby", "php", "swift", "objectivec", "erlang", "haskell",
        "sql",
    ]
    for lang in offered:
        assert code_runners.get_spec(lang) is not None, lang


def test_sql_language_resolves_and_is_gradeable() -> None:
    """SQL is a first-class language: aliases resolve, the spec runs through the
    python image (sqlite3 is stdlib), and it must never fall through to the
    function-call harnesses."""
    assert code_runners.resolve_language("SQL") == "sql"
    assert code_runners.resolve_language("sqlite") == "sql"
    assert code_runners.resolve_language("mysql") == "sql"
    spec = code_runners.get_spec("sql")
    assert spec is not None
    assert spec.name == "SQL"
    # The harness is a Python program (sqlite3 is part of the stdlib), so it
    # needs no compiler and no extra image beyond the shared python one.
    assert spec.compile_cmd is None
    assert spec.dynamic is True
    assert code_runners.HARNESS_BUILDERS.get("sql") is None


def test_sql_language_is_not_in_harness_builders() -> None:
    """SQL must not be graded as a function call — the SQL branch is explicit."""
    assert "sql" not in code_runners.HARNESS_BUILDERS
    assert "sql" not in code_runners.DESIGN_HARNESS_BUILDERS


# ── SQL (database) grading ───────────────────────────────────────────────────


def _sql_problems() -> list:
    """The curated problems that are graded by running a query, not a function."""
    return [p for p in CURATED_PROBLEMS if p.get("sql_schema")]


def _grade_sql_with_python(problem: dict, query: str) -> list | None:
    """Run the SQL harness under the local interpreter.

    The harness is pure stdlib (json + sqlite3), so it executes anywhere Python
    runs — no container required. Mirrors ``_grade_with_node`` for the bank.
    """
    harness = code_runners.build_sql_harness(
        query, problem["test_cases"], problem["sql_schema"]
    )
    with tempfile.TemporaryDirectory() as workdir:
        script = pathlib.Path(workdir) / "main.py"
        script.write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-I", str(script)], capture_output=True, text=True, timeout=30
        )
    if "RESULTS_JSON:" not in proc.stdout:
        return None
    tail = proc.stdout.rpartition("RESULTS_JSON:")[2].strip()
    return json.loads(tail.splitlines()[0])


def test_curated_database_problems_exist_at_all_levels() -> None:
    """The user-facing ladder: Basic, Intermediate and Advanced must each be
    represented, so the practice list never collapses to one tier."""
    problems = _sql_problems()
    assert problems, "no curated database problems"
    levels = {p["difficulty"] for p in problems}
    assert {"Easy", "Medium", "Hard"} <= levels, f"missing a tier: {levels}"
    # Every one must ship a schema, seed + expected rows, and a SQL starter.
    for problem in problems:
        assert problem["sql_schema"], f"{problem['id']}: no schema"
        assert problem["starter_code"].get("sql"), f"{problem['id']}: no SQL starter"
        for case in problem["test_cases"]:
            assert case.get("seed"), f"{problem['id']}: case has no seed"
            assert isinstance(case.get("expected"), list), f"{problem['id']}: bad expected"


def test_every_database_reference_solution_passes_its_own_tests() -> None:
    """A shipped reference query that fails its own suite is a misgraded problem.

    Mirrors the bank's reference-solution sweep, but graded through sqlite3 —
    the actual engine the sandbox harness drives.
    """
    failures = []
    for problem in _sql_problems():
        results = _grade_sql_with_python(problem, problem["solution_sql"])
        if results is None:
            failures.append((problem["id"], "no verdict line"))
        elif not (results and all(r.get("passed") is True for r in results)):
            bad = next(r for r in results if r.get("passed") is not True)
            failures.append(
                (problem["id"], f"got {bad.get('actual')!r} want {bad.get('expected')!r}")
            )
    assert not failures, f"{len(failures)} reference queries fail: {failures}"


def test_no_sql_starter_passes_its_own_tests() -> None:
    """The starter is a comment + placeholder SELECT — it must never pass."""
    passing = []
    for problem in _sql_problems():
        results = _grade_sql_with_python(problem, problem["starter_code"]["sql"])
        if results and all(r.get("passed") is True for r in results):
            passing.append(problem["id"])
    assert not passing, f"SQL starter passes for {passing}"


def test_sql_harness_orders_results_as_sets_not_sequences() -> None:
    """Result order is unspecified without an ORDER BY, so the harness must
    compare rows as sets — a query returning the right rows in a different
    order is a pass, not a failure."""
    problem = next(p for p in _sql_problems() if p["id"] == "duplicate-emails")
    query = problem["solution_sql"]
    results = _grade_sql_with_python(problem, query)
    assert results and all(r.get("passed") for r in results)

    # The same query with the rows reversed in the *expected* data must still
    # match — the harness sorts both sides before comparing. ``expected`` is
    # already the row list, so it is reversed in place; wrapping it in another
    # list would compare a row list against a list of row lists and fail for a
    # reason that has nothing to do with ordering.
    #
    # The shipped case expects a single row, and reversing a one-row list is a
    # no-op that would pass however the harness compared. A second duplicated
    # address is seeded so the reversal is a real permutation.
    seed = problem["test_cases"][0]["seed"] + [
        "INSERT INTO Person (id, email) VALUES (4, 'z@y.com');",
        "INSERT INTO Person (id, email) VALUES (5, 'z@y.com');",
    ]
    flipped = list(reversed([["a@b.com"], ["z@y.com"]]))
    assert flipped == [["z@y.com"], ["a@b.com"]], "the reversal must permute"
    harness = code_runners.build_sql_harness(
        query,
        [{"seed": seed, "expected": flipped}],
        problem["sql_schema"],
    )
    with tempfile.TemporaryDirectory() as workdir:
        script = pathlib.Path(workdir) / "main.py"
        script.write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-I", str(script)], capture_output=True, text=True, timeout=30
        )
    tail = proc.stdout.rpartition("RESULTS_JSON:")[2].strip()
    results = json.loads(tail.splitlines()[0])
    assert results and results[0]["passed"] is True, "row sets must be order-insensitive"


def test_wrong_sql_query_fails() -> None:
    """A query returning different rows is a failure, not a pass."""
    problem = next(p for p in _sql_problems() if p["id"] == "duplicate-emails")
    results = _grade_sql_with_python(problem, "SELECT * FROM Person;")
    assert results
    assert all(r.get("passed") is False for r in results)


def test_sql_syntax_error_is_a_failure_not_a_pass() -> None:
    """A malformed query reports the SQLite error as the failure reason."""
    problem = next(p for p in _sql_problems() if p["id"] == "duplicate-emails")
    results = _grade_sql_with_python(problem, "SELECT FROM WHERE;")
    assert results
    assert results[0]["passed"] is False
    # SQLite's parser diagnoses it: ``near "FROM": syntax error``.
    actual = str(results[0].get("actual")).lower()
    assert "syntax error" in actual or "near" in actual, actual


def test_sql_execute_path_is_taken_before_function_harnesses(monkeypatch) -> None:
    """A database problem in SQL must go through the query harness, never a
    function-call harness — the call-site and the query disagree otherwise."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    verdicts = [{"passed": True, "actual": [["a@b.com"]], "expected": [["a@b.com"]]}]

    class _Ran:
        exit_code, timed_out, duration_ms, compile_ok = 0, False, 8.0, True
        stdout = "RESULTS_JSON:" + json.dumps(verdicts) + "\n"
        stderr = ""

    captured = {}

    def _run(spec, files, **kwargs):
        captured["source"] = files[spec.source_name]
        return _Ran()

    monkeypatch.setattr(svc.sandbox, "run", _run)

    result = svc.execute_code("duplicate-emails", "sql", "SELECT email FROM Person;")

    assert result["success"] is True
    assert result["passed"] is True
    # The graded program is the SQL harness — it builds a sqlite3 database, it
    # is not a Python function-call wrapper.
    assert "sqlite3" in captured["source"]
    assert "RESULTS_JSON" in captured["source"]


def test_sql_on_non_database_problem_is_rejected(monkeypatch) -> None:
    """A coding problem has no schema, so SQL grading must say so, not guess."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    result = svc.execute_code("two-sum", "sql", "SELECT 1;")
    assert result["success"] is False
    assert result["passed"] is False
    assert "not a database problem" in result["error"].lower()


def test_database_problem_in_a_function_language_fails_honestly(monkeypatch) -> None:
    """A database problem must be answered with SQL. Trying a function language
    is a clear error, not a harness-driven KeyError the candidate can't parse."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    result = svc.execute_code("duplicate-emails", "python", "def solve(): pass")
    assert result["success"] is False
    assert result["passed"] is False
    assert "must be answered with SQL" in result["error"]


# ── Bank SQL coverage ────────────────────────────────────────────────────────
#
# The 1000-problem bank ships a hand-authored database set
# (``coding_sql_problems_data``), merged into the bank at import time. These
# sweep it exactly the way the curated SQL suite does — through real sqlite3,
# no container required.


def _sql_bank_problems() -> list:
    """The bank problems graded by running a query, not a function."""
    from app.services.coding_problems_data import PROBLEMS

    return [p for p in PROBLEMS if p.get("sql_schema")]


def test_bank_database_problems_exist_at_all_levels() -> None:
    """The bank's SQL coverage spans Basic, Intermediate and Advanced."""
    problems = _sql_bank_problems()
    assert problems, "no bank SQL problems"
    levels = {p["difficulty"] for p in problems}
    assert {"Easy", "Medium", "Hard"} <= levels, f"missing a tier: {levels}"
    for problem in problems:
        assert problem["sql_schema"], f"{problem['id']}: no schema"
        starter = (
            problem.get("starter_code", {}).get("sql") or problem.get("starterCode") or ""
        )
        assert starter, f"{problem['id']}: no SQL starter"
        assert problem["test_cases"], f"{problem['id']}: no test cases"
        for case in problem["test_cases"]:
            assert case.get("seed"), f"{problem['id']}: case has no seed"
            assert isinstance(case.get("expected"), list), f"{problem['id']}: bad expected"


def test_every_bank_database_reference_solution_passes_its_own_tests() -> None:
    """A bank SQL problem whose reference query fails its own suite is a
    misgraded problem — the same property the curated sweep pins."""
    failures = []
    for problem in _sql_bank_problems():
        results = _grade_sql_with_python(problem, problem["solution_sql"])
        if results is None:
            failures.append((problem["id"], "no verdict line"))
        elif not (results and all(r.get("passed") is True for r in results)):
            bad = next(r for r in results if r.get("passed") is not True)
            failures.append(
                (problem["id"], f"got {bad.get('actual')!r} want {bad.get('expected')!r}")
            )
    assert not failures, f"{len(failures)} bank reference queries fail: {failures}"


def test_no_bank_sql_starter_passes_its_own_tests() -> None:
    """The bank's SQL starter is a comment + placeholder SELECT — it must
    never pass."""
    passing = []
    for problem in _sql_bank_problems():
        starter = (
            problem.get("starter_code", {}).get("sql") or problem.get("starterCode") or ""
        )
        results = _grade_sql_with_python(problem, starter)
        if results and all(r.get("passed") is True for r in results):
            passing.append(problem["id"])
    assert not passing, f"SQL starter passes for {passing}"


def test_bank_sql_reference_is_never_served_to_candidates() -> None:
    """The bank's database answers are authoring artifacts — serving one would
    ship the answer with the question."""
    svc = _service()
    for problem in _sql_bank_problems():
        served = svc.get_problem_by_id(str(problem["id"]))
        assert served, f"{problem['id']} not found in the bank"
        assert "solution_sql" not in served, f"{problem['id']} leaks its answer"
        assert "solutionCode" not in served, f"{problem['id']} leaks its answer"


def test_bank_sql_problem_serves_schema_and_seed() -> None:
    """A served bank database problem carries what the grader and editor need:
    the schema, per-case seeds, and replayed examples."""
    served = _service().get_problem_by_id("1001")
    assert served["sql_schema"], "no schema served"
    assert served["test_cases"], "no test cases served"
    assert served["test_cases"][0]["seed"], "no seed served"
    assert served["examples"], "no examples served"


def test_bank_sql_execute_path_is_taken_before_function_harnesses(monkeypatch) -> None:
    """A bank database problem in SQL must go through the query harness — and
    the SQL branch must win over any 'not graded' verdict the bank index would
    infer for a query-only problem (no function signature to type)."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    verdicts = [
        {"passed": True, "actual": [["John", None]], "expected": [["John", None]]}
    ]

    class _Ran:
        exit_code, timed_out, duration_ms, compile_ok = 0, False, 8.0, True
        stdout = "RESULTS_JSON:" + json.dumps(verdicts) + "\n"
        stderr = ""

    captured = {}

    def _run(spec, files, **kwargs):
        captured["source"] = files[spec.source_name]
        return _Ran()

    monkeypatch.setattr(svc.sandbox, "run", _run)

    result = svc.execute_code(
        "1002",
        "sql",
        "SELECT e.name, b.bonus FROM Employee e LEFT JOIN Bonus b "
        "ON e.empId = b.empId WHERE b.bonus < 1000 OR b.bonus IS NULL;",
    )

    assert result["success"] is True
    assert result["passed"] is True
    # The graded program is the SQL harness — it builds a sqlite3 database, it
    # is not a Python function-call wrapper.
    assert "sqlite3" in captured["source"]
    assert "RESULTS_JSON" in captured["source"]


# ── Database schema figures ──────────────────────────────────────────────────


def test_reference_solution_is_never_served_to_candidates() -> None:
    """The reference query is an authoring artifact — every endpoint that
    serves a database problem to a candidate must strip it, or the answer
    ships with the question."""
    svc = _service()
    for problem in _sql_problems():
        served = svc.get_problem_by_id(problem["id"])
        assert "solution_sql" not in served, f"{problem['id']} leaks its answer"
        listed = next(
            p for p in svc.get_curated_problems() if p["id"] == problem["id"]
        )
        assert "solution_sql" not in listed, f"{problem['id']} leaks in the list"


def test_database_problem_enriches_with_a_table_figure() -> None:
    """A database example is drawn as the tables it seeds and the table the
    query must return — not an array strip, and not raw INSERT text.

    ``sql_example`` supersedes the older ``schema`` figure for examples: a
    schema alone shows the shape of the data but not the case being worked,
    which is the half the candidate actually reads.
    """
    svc = _service()
    for pid in ("combine-two-tables", "trips-and-users", "human-traffic-of-stadium"):
        problem = svc.get_problem_by_id(pid)
        assert problem["sql_schema"], pid
        diagram = problem["examples"][0].get("diagram")
        assert diagram and diagram["kind"] == "sql_example", pid
        tables = diagram["tables"]
        assert tables, pid
        # Every table card names its columns and shows the seeded rows, so the
        # picture cannot disagree with the seed the grader runs.
        for table in tables:
            assert table["name"]
            assert table["columns"]
            assert table["rows"], f"{pid}: table {table['name']} has no seed rows"


def test_every_database_example_carries_its_own_figure() -> None:
    """Not just the first. For a database question the figure *is* the example,
    so a later case left as raw INSERT text beside a JSON array of arrays would
    be strictly harder to read than the one above it."""
    for pid in ("combine-two-tables", "department-top-three-salaries"):
        examples = _service().get_problem_by_id(pid)["examples"]
        assert examples, pid
        for i, example in enumerate(examples):
            diagram = example.get("diagram")
            assert diagram and diagram["kind"] == "sql_example", f"{pid} example {i}"


def test_result_columns_are_named_or_omitted_never_guessed() -> None:
    """The result table's headers come from the SELECT list. Parsing it is
    all-or-nothing on purpose: a mislabelled column is worse than none, because
    it silently tells the candidate to return the wrong shape."""
    svc = _service()
    named = svc.get_problem_by_id("combine-two-tables")["examples"][0]["diagram"]
    assert named["result"]["columns"] == ["firstName", "lastName", "city", "state"]

    # ``trips-and-users`` selects a computed, aliased expression the parser
    # declines to name — it must fall back to no headers, not invent them.
    other = svc.get_problem_by_id("trips-and-users")["examples"][0]["diagram"]
    assert other["result"]["columns"] == []
    assert other["result"]["rows"], "rows must still be shown without headers"


def test_schema_diagram_parses_columns_keys_and_seed_rows() -> None:
    """The parser must read CREATE TABLE into named typed columns with key
    badges, and the INSERTs into row values — NULL stays NULL."""
    from app.services import problem_diagrams

    problem = {
        "sql_schema": [
            "CREATE TABLE Employee (id INT PRIMARY KEY, name VARCHAR(255), salary INT, managerId INT);",
        ],
        "sql_seed": [],
        "test_cases": [
            {
                "seed": [
                    "INSERT INTO Employee (id, name, salary, managerId) VALUES (1, 'Joe', 70000, NULL);",
                ],
                "expected": [],
            }
        ],
    }
    spec = problem_diagrams.build_schema_diagram(problem)
    assert spec and spec["kind"] == "schema"
    table = spec["tables"][0]
    assert table["name"] == "Employee"
    cols = {c["name"]: c for c in table["columns"]}
    assert cols["id"]["key"] == "PK"
    assert cols["name"]["type"].startswith("VARCHAR")
    assert table["rows"] == [[1, "Joe", 70000, None]]


def test_schema_diagram_handles_multiline_and_decimal_types() -> None:
    from app.services import problem_diagrams

    problem = {
        "sql_schema": [
            "CREATE TABLE Scores (id INT PRIMARY KEY, score DECIMAL(3, 2));",
        ],
        "sql_seed": [],
        "test_cases": [
            {
                "seed": ["INSERT INTO Scores (id, score) VALUES (1, 3.50);"],
                "expected": [],
            }
        ],
    }
    spec = problem_diagrams.build_schema_diagram(problem)
    cols = {c["name"]: c for c in spec["tables"][0]["columns"]}
    assert cols["score"]["type"].replace(" ", "") == "DECIMAL(3,2)"


def test_unsupported_language_rejected() -> None:
    result = _service().execute_code("two-sum", "brainfuck", "+++")
    assert result["success"] is False
    assert result["passed"] is False


def test_empty_code_rejected() -> None:
    result = _service().execute_code("two-sum", "python", "   \n  ")
    assert result["success"] is False
    assert result["passed"] is False


# ── Harness construction ─────────────────────────────────────────────────────


def test_python_harness_has_no_expected_substitution() -> None:
    """The JS runner used to assign `res = tc.expected` when no function was
    found, turning a missing solution into a perfect score. Neither harness may
    contain such a fallback."""
    tests = [{"input": {"a": 1}, "expected": 2}]
    py = code_runners.build_python_harness("def f(a):\n    return a + 1\n", tests, ["f"])
    js = code_runners.build_js_harness("function f(a){return a+1;}", tests, ["f"])

    assert "res = tc.expected" not in js
    assert "_res = _tc.expected" not in js
    # Both must bail out loudly instead.
    assert "exit(3)" in js
    assert "SystemExit(3)" in py


def test_judge0_renames_java_class_to_match_its_filename() -> None:
    """Judge0 writes every submission to `Main.<ext>`, and Java demands the
    public class match the file. Without the rename a perfectly good
    `public class Solution` fails to compile on Judge0 alone."""
    spec = code_runners.get_spec("java")
    adapted = Judge0Sandbox._adapt_source(
        spec, "public class Solution {\n  static int f(){ return new Solution().g(); }\n}"
    )

    assert "public class Main" in adapted
    assert "new Main()" in adapted, "every reference must move, not just the declaration"
    assert "Solution" not in adapted


def test_judge0_leaves_other_languages_alone() -> None:
    """The rename is a Java filename workaround, not a general rewrite."""
    source = "class Solution:\n    pass\n"
    assert Judge0Sandbox._adapt_source(code_runners.get_spec("python"), source) == source


def test_judge0_compile_only_ignores_a_nonzero_run() -> None:
    """Judge0 always runs the program. When the caller only asked whether it
    builds, a missing `main` must not be reported as a compilation error."""
    sandbox = Judge0Sandbox(base_url="http://judge0.invalid")
    body = {"status": {"id": 11}, "stderr": "Error: Main method not found", "exit_code": 1}

    result = sandbox._to_result(body, compile_only=True, timeout=10, elapsed=1.0)

    assert result.compile_ok is True
    assert result.exit_code == 0


def test_judge0_compile_error_is_reported_as_one() -> None:
    sandbox = Judge0Sandbox(base_url="http://judge0.invalid")
    body = {"status": {"id": 6}, "compile_output": "error: illegal start of type"}

    result = sandbox._to_result(body, compile_only=False, timeout=10, elapsed=1.0)

    assert result.compile_ok is False
    assert "illegal start of type" in result.stderr


def test_judge0_timeout_is_not_a_pass() -> None:
    sandbox = Judge0Sandbox(base_url="http://judge0.invalid")
    body = {"status": {"id": 5}, "stdout": "partial"}

    result = sandbox._to_result(body, compile_only=False, timeout=10, elapsed=1.0)

    assert result.timed_out is True
    assert result.exit_code == 124


def test_piston_accepts_both_url_shapes() -> None:
    """Self-hosted Piston serves /api/v2 at the root; the public one is mounted
    under a path. One setting has to handle both."""
    assert PistonSandbox._api_root("http://piston:2000") == "http://piston:2000/api/v2"
    assert PistonSandbox._api_root("http://piston:2000/") == "http://piston:2000/api/v2"
    assert (
        PistonSandbox._api_root("https://emkc.org/api/v2/piston")
        == "https://emkc.org/api/v2/piston"
    )
    assert PistonSandbox._api_root("") == ""


def test_layered_sandbox_falls_through_to_a_working_backend() -> None:
    """A backend can claim a language and still be unusable right now — a rate
    limit, a pruned image. That must cost a slower run, not a failed one."""
    spec = code_runners.get_spec("python")
    calls = []

    class _Broken:
        name = "broken"

        def available(self) -> bool:
            return True

        def supports(self, spec) -> bool:
            return True

        def run(self, spec, files, **kwargs):
            calls.append("broken")
            raise SandboxUnavailable("rate limited")

    class _Works:
        name = "works"

        def available(self) -> bool:
            return True

        def supports(self, spec) -> bool:
            return True

        def run(self, spec, files, **kwargs):
            calls.append("works")
            return SandboxResult(0, "ok", "", False, 1.0)

    result = LayeredSandbox([_Broken(), _Works()]).run(spec, {spec.source_name: "x"})

    assert calls == ["broken", "works"]
    assert result.stdout == "ok"


def test_layered_sandbox_raises_when_every_backend_fails() -> None:
    """Falling through must not become a way to lose the failure entirely."""
    spec = code_runners.get_spec("python")

    class _Broken:
        name = "broken"

        def available(self) -> bool:
            return True

        def supports(self, spec) -> bool:
            return True

        def run(self, spec, files, **kwargs):
            raise SandboxUnavailable("nope")

    with pytest.raises(SandboxUnavailable):
        LayeredSandbox([_Broken(), _Broken()]).run(spec, {spec.source_name: "x"})


def test_sandbox_flags_are_locked_down() -> None:
    """Isolation flags are the whole point of the sandbox; pin them."""
    captured = {}

    class _Recorder(ContainerSandbox):
        def available(self) -> bool:
            return True

    sandbox = _Recorder(docker_path="docker")

    import subprocess as _sp

    def _fake_run(argv, **kwargs):
        captured["argv"] = argv

        class _R:
            returncode, stdout, stderr = 0, "RESULTS_JSON:[]", ""

        return _R()

    original = _sp.run
    _sp.run = _fake_run
    try:
        sandbox.run(code_runners.get_spec("python"), {"main.py": "print(1)"})
    finally:
        _sp.run = original

    argv = captured["argv"]
    assert "--rm" in argv
    assert "none" in argv, "container must have no network"
    assert "--read-only" in argv
    assert "ALL" in argv, "capabilities must be dropped"
    assert "no-new-privileges" in argv
    assert "65534:65534" in argv, "must not run as root"
    assert "--pids-limit" in argv
    assert any(a.endswith(":/sandbox:ro") for a in argv), "source mount must be read-only"


# ── End-to-end, real containers ──────────────────────────────────────────────


@sandbox_required
@pytest.mark.parametrize(
    "language,correct,wrong",
    [
        (
            "python",
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        if target - n in seen:\n"
            "            return [seen[target - n], i]\n"
            "        seen[n] = i\n"
            "    return []\n",
            "def two_sum(nums, target):\n    return []\n",
        ),
        (
            "javascript",
            "function twoSum(nums, target) {\n"
            "  const m = new Map();\n"
            "  for (let i = 0; i < nums.length; i++) {\n"
            "    if (m.has(target - nums[i])) return [m.get(target - nums[i]), i];\n"
            "    m.set(nums[i], i);\n"
            "  }\n"
            "  return [];\n"
            "}\n",
            "function twoSum(nums, target) {\n  return [];\n}\n",
        ),
    ],
)
def test_real_execution_distinguishes_correct_from_wrong(
    language: str, correct: str, wrong: str
) -> None:
    """The property the old implementation could not deliver."""
    svc = _service()
    spec = code_runners.get_spec(language)
    if not svc.sandbox.supports(spec):
        pytest.skip(f"no backend can run {language}")

    good = svc.execute_code("two-sum", language, correct)
    assert good["success"] is True, good.get("error")
    assert good["passed"] is True, good

    bad = svc.execute_code("two-sum", language, wrong)
    assert bad["passed"] is False


@sandbox_required
def test_real_execution_has_no_network() -> None:
    """Container-isolated candidate code must not reach the network.

    Scoped to the container backend on purpose: the subprocess backend bounds
    CPU, memory and processes via rlimits, but cannot block a socket. That is
    the documented isolation gap, so asserting it here would fail by design
    rather than catch a regression.
    """
    svc = _service()
    spec = code_runners.get_spec("python")
    backend = svc.sandbox.backend_for(spec)
    if backend is None or backend.name != "docker":
        pytest.skip("network isolation is only enforced by the container backend")

    probe = (
        "import socket\n"
        "def two_sum(nums, target):\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
        "    return [0, 1]\n"
    )
    result = svc.execute_code("two-sum", "python", probe)
    assert result["passed"] is False


# ── Bank gradeability, checked against Node directly ─────────────────────────
#
# These run the generated harness under a local `node` rather than the Docker
# sandbox, so they exercise every problem in CI without pulling images. They are
# the tests that catch a misgraded suite: a reference solution that fails, or a
# starter stub that passes.

_node = shutil.which("node")
node_required = pytest.mark.skipif(_node is None, reason="node not installed")


def _grade_with_node(problem: dict, source: str) -> list | None:
    """Return the harness's per-case verdicts, or None if it produced none."""
    builder = (
        code_runners.DESIGN_HARNESS_BUILDERS["javascript"]
        if problem.get("grading") == "design"
        else code_runners.HARNESS_BUILDERS["javascript"]
    )
    names = list(problem["entry_point"]) + ["solve", "solution"]
    harness = builder(source, problem["test_cases"], names)

    with tempfile.TemporaryDirectory() as workdir:
        script = pathlib.Path(workdir) / "main.js"
        script.write_text(harness, encoding="utf-8")
        # Retried once: these sweeps spawn a node process per bank problem, and
        # on a loaded machine an interpreter start occasionally stalls past the
        # timeout. A real hang fails both attempts; a scheduling blip does not.
        for attempt in range(2):
            try:
                proc = subprocess.run(
                    [_node, str(script)], capture_output=True, text=True, timeout=30
                )
                break
            except subprocess.TimeoutExpired:
                if attempt:
                    return None

    if "RESULTS_JSON:" not in proc.stdout:
        return None
    tail = proc.stdout.rpartition("RESULTS_JSON:")[2].strip()
    return json.loads(tail.splitlines()[0])


def _gradeable_bank() -> list:
    from app.services.coding_problems_data import PROBLEMS

    raw = {str(p["id"]): p for p in PROBLEMS}
    return [
        (pid, problem, raw[pid])
        for pid, problem in _problem_bank_index().items()
        if problem.get("grading") != "unsupported"
        and not problem.get("sql_schema")
    ]


@node_required
def test_every_reference_solution_passes_its_own_tests() -> None:
    """A shipped solution that fails its own suite is a misgraded problem.

    This caught 53 of them: buggy references (invertTree swapped only sibling
    leaves; isSubtree used a substring hack), unsatisfiable expectations (Two Sum
    II asserted [1,2] for [[-1,0],1] where -1+0 != 1), any-order results compared
    strictly, class problems invoked as plain functions, and multi-function
    starters graded on a helper instead of the driver.
    """
    failures = []
    for pid, problem, raw in _gradeable_bank():
        results = _grade_with_node(problem, raw["solutionCode"])
        if results is None:
            failures.append((pid, problem["title"], "no verdict line"))
        elif not (results and all(r.get("passed") is True for r in results)):
            bad = next(r for r in results if r.get("passed") is not True)
            failures.append(
                (pid, problem["title"], f"got {bad.get('actual')!r} want {bad.get('expected')!r}")
            )

    assert not failures, f"{len(failures)} reference solutions fail: {failures[:8]}"


@node_required
def test_no_starter_code_passes_its_own_tests() -> None:
    """The headline bug: boilerplate reporting a full pass.

    Six problems shipped a finished prefix-sum implementation as their starter,
    so a candidate who submitted the untouched template scored 100%.
    """
    passing = []
    for pid, problem, raw in _gradeable_bank():
        results = _grade_with_node(problem, raw["starterCode"])
        if results and all(r.get("passed") is True for r in results):
            passing.append((pid, problem["title"]))

    assert not passing, f"starter code passes for {passing[:8]}"


# ── Static-language grading ──────────────────────────────────────────────────
#
# Java, C++, C#, Go, Rust, Swift, Haskell, Erlang and Objective-C are graded by
# inferring a signature from the test data and generating a typed program around
# the submission. These tests pin the inference's boundaries and check that the
# generated starter and the generated call site agree — a mismatch there would
# fail every correct solution with a compile error.

_STATIC_LANGUAGES = sorted(static_harness.RENDERERS)

_TWO_SUM_CASES = [
    {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
    {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
]


@pytest.mark.parametrize(
    "cases, expect",
    [
        # Accepted: the shapes the bank actually uses.
        ([{"input": {"n": 1}, "expected": 2}], "int"),
        ([{"input": {"s": "ab"}, "expected": True}], "bool"),
        ([{"input": {"a": [1, 2]}, "expected": [1]}], "list[int]"),
        ([{"input": {"g": [[1], [2]]}, "expected": [[1]]}], "list[list[int]]"),
        ([{"input": {"w": ["a"]}, "expected": ["a", "b"]}], "list[str]"),
        # An empty list in one case is resolved by another that is populated.
        (
            [
                {"input": {"a": []}, "expected": [1]},
                {"input": {"a": [1]}, "expected": [2]},
            ],
            "list[int]",
        ),
        # Rejected: no single typed signature describes these.
        ([{"input": {"n": None}, "expected": 1}], None),           # null argument
        ([{"input": {"n": 1}, "expected": None}], None),           # null result
        ([{"input": {"d": {"k": 1}}, "expected": 1}], None),       # object argument
        ([{"input": {"a": [1, "x"]}, "expected": 1}], None),       # mixed list
        ([{"input": {"a": [[[1]]]}, "expected": 1}], None),        # nesting past a matrix
        ([{"input": {"n": 1}, "expected": 1.5}], None),            # float result
        ([{"input": {"a": []}, "expected": [] }], None),           # element type unknown
        (                                                          # arity disagreement
            [
                {"input": {"a": 1}, "expected": 1},
                {"input": {"a": 1, "b": 2}, "expected": 1},
            ],
            None,
        ),
        (                                                          # type disagreement
            [
                {"input": {"a": 1}, "expected": 1},
                {"input": {"a": "x"}, "expected": 1},
            ],
            None,
        ),
        ([], None),
    ],
)
def test_signature_inference_accepts_only_what_it_can_type(cases, expect) -> None:
    signature = static_harness.infer_signature(cases)
    if expect is None:
        assert signature is None
    else:
        assert signature is not None
        assert str(signature.ret) == expect


def test_float_arguments_are_allowed_but_float_results_are_not() -> None:
    """Formatting a double is where nine languages stop agreeing.

    The verdict compares rendered JSON text, so a `0.1 + 0.2` that prints as
    `0.30000000000000004` in one runtime and `0.3` in another would fail a
    correct solution. Float *inputs* are only ever emitted as literals, so they
    carry no such risk.
    """
    assert static_harness.infer_signature(
        [{"input": {"x": 1.5}, "expected": 2}]
    ) is not None
    assert static_harness.infer_signature(
        [{"input": {"x": 2}, "expected": 1.5}]
    ) is None


@pytest.mark.parametrize("language", _STATIC_LANGUAGES)
def test_generated_starter_matches_the_generated_call_site(language: str) -> None:
    """The starter and the harness come from one inference, so they must agree.

    If they drift, every correct submission fails to compile against a call the
    candidate was never shown.
    """
    starter = static_harness.build_starter(language, _TWO_SUM_CASES, ["two_sum", "twoSum"])
    assert starter, f"no starter generated for {language}"

    entry = static_harness.entry_name(
        ["two_sum", "twoSum"], static_harness.RENDERERS[language].style
    )
    assert entry in starter

    program = static_harness.build_program(
        language, _TWO_SUM_CASES, ["two_sum", "twoSum"], starter
    )
    assert program is not None
    assert starter.strip() in program
    # One call site per test case, on top of the starter's own mentions. Counted
    # on the bare name because the call syntax differs — `twoSum(a, b)` in Java,
    # `twoSum (a) (b)` in Haskell.
    assert program.count(entry) == starter.count(entry) + len(_TWO_SUM_CASES)


@pytest.mark.parametrize("language", _STATIC_LANGUAGES)
def test_generated_starter_does_not_pass_the_tests(language: str) -> None:
    """A starter returns a zero value; it must never coincide with every answer.

    Checked without executing: the harness's verdict is a string comparison
    against the expected JSON, so a starter passes exactly when its zero value
    renders to that same text for every case.
    """
    renderer = static_harness.RENDERERS[language]
    signature = static_harness.infer_signature(_TWO_SUM_CASES)
    assert signature is not None
    zero = renderer.zero(signature.ret)
    assert not all(zero == json.dumps(c["expected"]) for c in _TWO_SUM_CASES)


def test_static_language_grades_from_real_output(monkeypatch) -> None:
    """A typeable problem in a static language yields real per-case verdicts."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    verdicts = [
        {"passed": True, "actual": [0, 1], "expected": [0, 1]},
        {"passed": False, "actual": [], "expected": [1, 2]},
        {"passed": True, "actual": [0, 1], "expected": [0, 1]},
    ]

    class _Ran:
        exit_code, timed_out, duration_ms, compile_ok = 0, False, 12.0, True
        stdout = "RESULTS_JSON:" + json.dumps(verdicts) + "\n"
        stderr = ""

    captured = {}

    def _run(spec, files, **kwargs):
        captured["source"] = files[spec.source_name]
        return _Ran()

    monkeypatch.setattr(svc.sandbox, "run", _run)

    result = svc.execute_code("two-sum", "java", BOILERPLATE["java"])

    assert result["success"] is True
    assert result["passed"] is False            # one case failed
    assert len(result["test_results"]) == 3
    # The submission really was wrapped, not compiled bare.
    assert "RESULTS_JSON" in captured["source"]
    assert BOILERPLATE["java"].strip() in captured["source"]


def test_curated_problems_ship_starters_for_every_static_language() -> None:
    """Otherwise the editor falls back to a generic template the harness
    cannot call, and the candidate sees a compile error on untouched code."""
    two_sum = _service().get_problem_by_id("two-sum")
    assert two_sum is not None
    missing = [
        language
        for language in _STATIC_LANGUAGES
        if not (two_sum["starter_code"].get(language) or "").strip()
    ]
    assert not missing, f"no starter code for {missing}"


def test_handwritten_starters_are_not_overwritten() -> None:
    """Two Sum ships a Rust starter by hand; inference must not replace it."""
    curated = next(p for p in CURATED_PROBLEMS if p["id"] == "two-sum")
    served = _service().get_problem_by_id("two-sum")
    assert served["starter_code"]["rust"] == curated["starter_code"]["rust"]


def test_compile_only_wraps_function_shaped_submissions(monkeypatch) -> None:
    """Starters for these languages are function-only.

    The graded path supplies the package clause, imports and `main`; the
    compile-only path has to do the same or it reports an error about the
    harness's conventions instead of the candidate's code.
    """
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)
    monkeypatch.setattr(svc.sandbox, "supports", lambda spec: True)

    class _Ok:
        exit_code, stdout, stderr, timed_out, duration_ms = 0, "", "", False, 5.0
        compile_ok = True

    captured = {}

    def _run(spec, files, **kwargs):
        captured["source"] = files[spec.source_name]
        return _Ok()

    monkeypatch.setattr(svc.sandbox, "run", _run)

    untypeable = next(
        pid
        for pid, p in _problem_bank_index().items()
        if p.get("grading") not in ("design", "unsupported")
        and static_harness.infer_signature(p["test_cases"]) is None
    )
    svc.execute_code(untypeable, "go", "func solve(n int) int { return n }")

    assert captured["source"].startswith("package main")
    assert "func main()" in captured["source"]


# ── Static-language grading, end to end ──────────────────────────────────────
#
# These compile and run real submissions on a real backend. `conftest` blanks
# JUDGE0_URL/PISTON_URL unless CODE_EXEC_TEST_REMOTE=1, so they are skipped by
# default: a test run must not depend on a third-party service. Opt in with
#     CODE_EXEC_TEST_REMOTE=1 pytest tests/test_code_execution.py -k end_to_end
# They are the only check that the generated programs actually build — the
# offline tests above pin the inference and the call site, not the compiler.

remote_required = pytest.mark.skipif(
    os.environ.get("CODE_EXEC_TEST_REMOTE") != "1" or not get_sandbox().available(),
    reason="set CODE_EXEC_TEST_REMOTE=1 with a reachable sandbox",
)

_TWO_SUM_SOLUTIONS = {
    "java": """
class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            Integer j = seen.get(target - nums[i]);
            if (j != null) return new int[] { j, i };
            seen.put(nums[i], i);
        }
        return new int[] {};
    }
}
""",
    "cpp": """
vector<int> twoSum(vector<int> nums, int target) {
    unordered_map<int, int> seen;
    for (int i = 0; i < (int) nums.size(); i++) {
        auto it = seen.find(target - nums[i]);
        if (it != seen.end()) return {it->second, i};
        seen[nums[i]] = i;
    }
    return {};
}
""",
    "csharp": """
public class Solution {
    public int[] TwoSum(int[] nums, int target) {
        var seen = new Dictionary<int, int>();
        for (int i = 0; i < nums.Length; i++) {
            if (seen.ContainsKey(target - nums[i])) return new int[] { seen[target - nums[i]], i };
            seen[nums[i]] = i;
        }
        return new int[] { };
    }
}
""",
    "go": """
func twoSum(nums []int, target int) []int {
	seen := map[int]int{}
	for i, n := range nums {
		if j, ok := seen[target-n]; ok {
			return []int{j, i}
		}
		seen[n] = i
	}
	return nil
}
""",
    "rust": """
fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
    let mut seen: HashMap<i32, i32> = HashMap::new();
    for (i, n) in nums.iter().enumerate() {
        if let Some(&j) = seen.get(&(target - n)) {
            return vec![j, i as i32];
        }
        seen.insert(*n, i as i32);
    }
    Vec::new()
}
""",
    "swift": """
func twoSum(_ nums: [Int], _ target: Int) -> [Int] {
    var seen = [Int: Int]()
    for (i, n) in nums.enumerated() {
        if let j = seen[target - n] { return [j, i] }
        seen[n] = i
    }
    return []
}
""",
    "haskell": """
twoSum :: [Int] -> Int -> [Int]
twoSum nums target = go (zip [0..] nums) Map.empty
  where
    go [] _ = []
    go ((i, n) : rest) seen =
      case Map.lookup (target - n) seen of
        Just j  -> [j, i]
        Nothing -> go rest (Map.insert n i seen)
""",
    "erlang": """
two_sum(Nums, Target) ->
    scan(Nums, Target, 0, #{}).

scan([], _, _, _) -> [];
scan([N | Rest], Target, I, Seen) ->
    case maps:find(Target - N, Seen) of
        {ok, J} -> [J, I];
        error -> scan(Rest, Target, I + 1, Seen#{N => I})
    end.
""",
    "objectivec": """
NSArray *twoSum(NSArray *nums, int target) {
    NSMutableDictionary *seen = [NSMutableDictionary dictionary];
    for (int i = 0; i < (int)[nums count]; i++) {
        int n = [[nums objectAtIndex:i] intValue];
        NSNumber *j = [seen objectForKey:[NSNumber numberWithInt:(target - n)]];
        if (j != nil) return [NSArray arrayWithObjects:j, [NSNumber numberWithInt:i], nil];
        [seen setObject:[NSNumber numberWithInt:i] forKey:[NSNumber numberWithInt:n]];
    }
    return [NSArray array];
}
""",
}


def test_every_static_language_has_an_end_to_end_solution() -> None:
    """A renderer added without a fixture would silently skip its own check."""
    assert sorted(_TWO_SUM_SOLUTIONS) == _STATIC_LANGUAGES


@remote_required
@pytest.mark.parametrize("language", _STATIC_LANGUAGES)
def test_correct_solution_passes_end_to_end(language: str) -> None:
    """The generated program compiles, runs, and grades every case as passing."""
    result = _service().execute_code("two-sum", language, _TWO_SUM_SOLUTIONS[language])

    assert result["success"] is True, result.get("error") or result.get("output")
    assert result["passed"] is True, result["test_results"]
    assert result["test_results"]
    assert all(case["passed"] for case in result["test_results"])


@remote_required
@pytest.mark.parametrize("language", _STATIC_LANGUAGES)
def test_untouched_starter_fails_end_to_end(language: str) -> None:
    """The negative half: the starter builds, so a failure here is a real verdict.

    A starter that fails to compile would also report `passed=False`, which is
    why the compile step is asserted separately.
    """
    starter = static_harness.build_starter(language, _TWO_SUM_CASES, ["two_sum", "twoSum"])
    result = _service().execute_code("two-sum", language, starter)

    assert result["success"] is True, result.get("error") or result.get("output")
    assert result["passed"] is False
    assert any(not case["passed"] for case in result["test_results"])
