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
import pathlib
import shutil
import subprocess
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
from app.services.code_sandbox import ContainerSandbox, SandboxUnavailable, get_sandbox

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
    """With no Docker, execution must fail loudly rather than fabricate a pass.

    The old JS runner returned `passed: True` with a full set of passing test
    results when Node was missing — which is the state of the production image.
    """
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: False)

    result = svc.execute_code("two-sum", "python", "def two_sum(nums, target):\n    return [0, 1]\n")

    assert result["success"] is False
    assert result["passed"] is False
    assert result["test_results"] == []
    assert "docker" in result["error"].lower()


def test_missing_image_reports_error_not_pass(monkeypatch) -> None:
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: False)

    result = svc.execute_code("two-sum", "go", BOILERPLATE["go"])

    assert result["success"] is False
    assert result["passed"] is False
    assert result["test_results"] == []


def test_static_language_is_not_graded(monkeypatch) -> None:
    """Compile-only languages must not claim a verdict either way."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)

    class _Ok:
        exit_code, stdout, stderr, timed_out, duration_ms = 0, "", "", False, 5.0

    monkeypatch.setattr(svc.sandbox, "run", lambda *a, **k: _Ok())

    result = svc.execute_code("two-sum", "java", "class Solution {}")

    assert result["success"] is False
    assert result["passed"] is False
    assert "not graded" in result["error"].lower()


def test_no_verdict_line_is_a_failure(monkeypatch) -> None:
    """A program that prints nothing must not be graded as passing."""
    svc = _service()
    monkeypatch.setattr(svc.sandbox, "available", lambda: True)
    monkeypatch.setattr(svc.sandbox, "image_present", lambda image: True)

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


def test_curated_problems_declare_entry_points() -> None:
    for problem in CURATED_PROBLEMS:
        assert problem.get("entry_point"), f"{problem['id']} has no entry_point"


def test_problem_bank_entry_points_recovered() -> None:
    index = _problem_bank_index()
    assert index, "problem bank should not be empty"
    missing = [pid for pid, p in index.items() if not p["entry_point"]]
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

    class _Ok:
        exit_code, stdout, stderr, timed_out, duration_ms = 0, "", "", False, 5.0

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
    """The UI offers 14 languages; each must resolve to a real spec.

    Previously ten of them routed to a keyword-matching simulator.
    """
    offered = [
        "python", "javascript", "typescript", "java", "cpp", "csharp", "go",
        "rust", "ruby", "php", "swift", "objectivec", "erlang", "haskell",
    ]
    for lang in offered:
        assert code_runners.get_spec(lang) is not None, lang


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
        sandbox.run("python:3.12-alpine", {"main.py": "print(1)"}, ["python", "/build/main.py"])
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
    if not svc.sandbox.image_present(spec.image):
        pytest.skip(f"image {spec.image} not pulled")

    good = svc.execute_code("two-sum", language, correct)
    assert good["success"] is True, good.get("error")
    assert good["passed"] is True, good

    bad = svc.execute_code("two-sum", language, wrong)
    assert bad["passed"] is False


@sandbox_required
def test_real_execution_has_no_network() -> None:
    """Candidate code must not be able to reach the network."""
    svc = _service()
    spec = code_runners.get_spec("python")
    if not svc.sandbox.image_present(spec.image):
        pytest.skip("python image not pulled")

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
        try:
            proc = subprocess.run(
                [_node, str(script)], capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
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
