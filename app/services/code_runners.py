"""Per-language execution specs and generic test harnesses.

Every runner here obeys one contract: the program prints a single line
``RESULTS_JSON:[...]`` holding one ``{passed, actual, expected}`` object per test
case. If that line is absent, the run *failed* — there is no code path that
invents a passing result.

Two classes of language:

- **Dynamic** (Python, JavaScript, TypeScript, Ruby, PHP). Arguments can be
  bound from JSON and the entry point looked up by name at runtime, so one
  generic harness per language covers every problem.
- **Static** (Java, C++, C#, Go, Rust, Swift, Haskell, Erlang, Objective-C). No
  problem declares per-language types, so :mod:`app.services.static_harness`
  infers a signature from the test data and generates a typed program around the
  submission. When the data cannot be typed exactly it declines, and the caller
  compiles without grading — see ``VERIFY_UNTYPEABLE``, which reports
  ``success=False``, never a pass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

VERIFY_UNTYPEABLE = (
    "This problem cannot be auto-graded in {lang}. Grading a statically typed "
    "language needs a signature, and this problem's recorded test cases do not "
    "agree on one — they use a value shape (a null, an object, a mixed list, or "
    "nesting deeper than a matrix) that does not map to a single typed "
    "function. Your code was compiled and syntax-checked, but not graded. "
    "Python, JavaScript, TypeScript, Ruby and PHP grade this problem normally."
)

# Kept under the old name so existing imports keep working.
VERIFY_UNSUPPORTED = VERIFY_UNTYPEABLE


@dataclass(frozen=True)
class LanguageSpec:
    """How to build and run one language inside the sandbox."""

    name: str
    image: str
    source_name: str
    run_cmd: List[str]
    compile_cmd: Optional[List[str]] = None
    dynamic: bool = True
    aliases: tuple = field(default_factory=tuple)
    # Piston's own language identifier (see GET /api/v2/runtimes). Piston
    # compiles and runs from the source file alone, so it needs no command —
    # only this name. Empty means the language is unavailable on Piston, which
    # surfaces as an unsupported language rather than a wrong verdict.
    piston: str = ""
    # Judge0 names a language as "Ruby (2.7.0)" — version and all — so this is
    # matched as a prefix and the highest-numbered match wins, which keeps the
    # newest runtime without pinning IDs that drift between instances. The
    # trailing " (" matters: without it "Java" would also match "JavaScript".
    judge0: str = ""


# Images are pinned and must be pulled ahead of time (see docs/coding-sandbox).
# They are only consulted by the Docker backend; the HTTP backends use the
# `piston` / `judge0` names instead. A language that no backend claims surfaces
# as unavailable rather than as a wrong verdict.
LANGUAGES: Dict[str, LanguageSpec] = {
    "python": LanguageSpec(
        name="Python",
        image="python:3.12-alpine",
        source_name="main.py",
        run_cmd=["python", "-I", "/build/main.py"],
        aliases=("python3", "py"),
        piston="python",
        judge0="Python (",
    ),
    "javascript": LanguageSpec(
        name="JavaScript",
        image="node:22-alpine",
        source_name="main.js",
        run_cmd=["node", "/build/main.js"],
        aliases=("js", "node"),
        piston="javascript",
        judge0="JavaScript (",
    ),
    "typescript": LanguageSpec(
        name="TypeScript",
        image="node:22-alpine",
        # Must be `.ts`: Node only strips types from a file it recognises as
        # TypeScript. Writing this as `main.js` — as it was — made every
        # annotated submission die on a SyntaxError at the first colon.
        source_name="main.ts",
        # Node 22.6+ strips types behind this flag and 23+ does it by default,
        # where the flag is still accepted. No `tsc` install is needed, and no
        # type *checking* happens — erasable syntax only, so `enum` and
        # `namespace` are out.
        run_cmd=["node", "--experimental-strip-types", "/build/main.ts"],
        aliases=("ts",),
        # Piston has no TypeScript-with-stripping runtime; its `typescript`
        # entry is a real tsc, which the JS harness also suits.
        piston="typescript",
        judge0="TypeScript (",
    ),
    "ruby": LanguageSpec(
        name="Ruby",
        image="ruby:3.3-alpine",
        source_name="main.rb",
        run_cmd=["ruby", "/build/main.rb"],
        aliases=("rb",),
        piston="ruby",
        judge0="Ruby (",
    ),
    "php": LanguageSpec(
        name="PHP",
        image="php:8.3-cli-alpine",
        source_name="main.php",
        run_cmd=["php", "/build/main.php"],
        aliases=(),
        piston="php",
        judge0="PHP (",
    ),
    # ── Compile-only: real compiler, no auto-grading ──────────────────────
    "java": LanguageSpec(
        name="Java",
        image="eclipse-temurin:21-jdk-alpine",
        # `Main.java`, not `Solution.java`: the generated harness owns the file
        # and puts its driver in `public class Main`, which Java requires to
        # match the filename. Judge0 writes every submission to `Main.<ext>`
        # anyway, so this also makes the Docker and Judge0 backends agree.
        source_name="Main.java",
        compile_cmd=["javac", "-d", "/build", "/build/Main.java"],
        run_cmd=["java", "-cp", "/build", "Main"],
        dynamic=False,
        piston="java",
        judge0="Java (",
    ),
    "cpp": LanguageSpec(
        name="C++",
        image="gcc:14",
        source_name="main.cpp",
        compile_cmd=["g++", "-std=c++20", "-O1", "-o", "/build/main", "/build/main.cpp"],
        run_cmd=["/build/main"],
        dynamic=False,
        aliases=("c++",),
        piston="c++",
        judge0="C++ (",
    ),
    "csharp": LanguageSpec(
        name="C#",
        image="mcr.microsoft.com/dotnet/sdk:8.0-alpine",
        source_name="Program.cs",
        run_cmd=["dotnet", "run", "--project", "/build"],
        dynamic=False,
        aliases=("c#", "cs"),
        piston="csharp",
        judge0="C# (",
    ),
    "go": LanguageSpec(
        name="Go",
        image="golang:1.23-alpine",
        source_name="main.go",
        compile_cmd=["go", "build", "-o", "/build/main", "/build/main.go"],
        run_cmd=["/build/main"],
        dynamic=False,
        aliases=("golang",),
        piston="go",
        judge0="Go (",
    ),
    "rust": LanguageSpec(
        name="Rust",
        image="rust:1.82-alpine",
        source_name="main.rs",
        compile_cmd=["rustc", "-O", "-o", "/build/main", "/build/main.rs"],
        run_cmd=["/build/main"],
        dynamic=False,
        aliases=("rs",),
        piston="rust",
        judge0="Rust (",
    ),
    "swift": LanguageSpec(
        name="Swift",
        image="swift:5.10",
        source_name="main.swift",
        compile_cmd=["swiftc", "-o", "/build/main", "/build/main.swift"],
        run_cmd=["/build/main"],
        dynamic=False,
        piston="swift",
        judge0="Swift (",
    ),
    "haskell": LanguageSpec(
        name="Haskell",
        image="haskell:9.6-slim",
        source_name="Main.hs",
        compile_cmd=["ghc", "-o", "/build/main", "-outputdir", "/build", "/build/Main.hs"],
        run_cmd=["/build/main"],
        dynamic=False,
        aliases=("hs",),
        piston="haskell",
        judge0="Haskell (",
    ),
    "erlang": LanguageSpec(
        name="Erlang",
        image="erlang:27-alpine",
        # Module `main`, matching the filename Judge0 uses — an Erlang module
        # name must equal its file's basename, so `solution.erl` here and
        # `main.erl` there could not both compile the same source.
        source_name="main.erl",
        compile_cmd=["erlc", "-o", "/build", "/build/main.erl"],
        run_cmd=["escript", "/build/main.beam"],
        dynamic=False,
        piston="erlang",
        judge0="Erlang (",
    ),
    "objectivec": LanguageSpec(
        name="Objective-C",
        image="gcc:14",
        source_name="main.m",
        compile_cmd=["gcc", "-o", "/build/main", "/build/main.m"],
        run_cmd=["/build/main"],
        dynamic=False,
        aliases=("objc",),
        # Piston ships no Objective-C runtime, and `gcc main.m` needs the
        # GNUstep headers that only the Docker image has — so off-Docker this
        # is the one backend that can build it.
        piston="",
        judge0="Objective-C (",
    ),
    # SQL is graded by building an in-memory SQLite database from the problem's
    # schema and seed data, running the candidate's query, and comparing the
    # resulting rows. sqlite3 is part of the Python standard library, so the
    # ``python`` image and subprocess toolchain both run it with no extra
    # infrastructure — the harness is a Python program, not a query runner.
    "sql": LanguageSpec(
        name="SQL",
        image="python:3.12-alpine",
        source_name="main.py",
        run_cmd=["python", "-I", "/build/main.py"],
        aliases=("sqlite", "sqlite3", "mysql", "postgres", "postgresql", "database"),
        # Piston has no SQL runtime we can rely on, and Judge0's SQL dialects
        # differ per instance; the Docker and subprocess backends cover it.
        piston="",
        judge0="",
    ),
}

_ALIAS_INDEX: Dict[str, str] = {}
for _key, _spec in LANGUAGES.items():
    _ALIAS_INDEX[_key] = _key
    for _alias in _spec.aliases:
        _ALIAS_INDEX[_alias] = _key


def resolve_language(language: str) -> Optional[str]:
    """Map a user-supplied language string to a canonical key."""
    if not language:
        return None
    return _ALIAS_INDEX.get(language.strip().lower().replace("-", "").replace(" ", ""))


def get_spec(language: str) -> Optional[LanguageSpec]:
    key = resolve_language(language)
    return LANGUAGES[key] if key else None


# ── Harness builders ──────────────────────────────────────────────────────────
#
# Each harness receives the candidate source, the normalized test cases, and the
# candidate entry-point names to try. If none resolves, the harness exits
# non-zero with a diagnostic — it does NOT substitute the expected value.

_PY_HARNESS = '''
# ── grading harness (appended) ───────────────────────────────────────────────
import json as _json, sys as _sys

_TESTS = _json.loads({tests!r})
_NAMES = _json.loads({names!r})

_fn = None
for _n in _NAMES:
    _c = globals().get(_n)
    if callable(_c):
        _fn = _c
        break

if _fn is None:
    # Last resort: a single user-defined function in the module. Never guess
    # among several — calling the wrong one would silently misgrade.
    _cands = [
        v for k, v in list(globals().items())
        if callable(v) and not k.startswith("_") and getattr(v, "__module__", None) == "__main__"
    ]
    if len(_cands) == 1:
        _fn = _cands[0]

if _fn is None:
    _sys.stderr.write(
        "Could not find your solution function. Expected one of: "
        + ", ".join(_NAMES) + "\\n"
    )
    raise SystemExit(3)

_results = []
for _tc in _TESTS:
    _inp, _exp = _tc["input"], _tc["expected"]
    try:
        if isinstance(_inp, dict):
            try:
                _res = _fn(**_inp)
            except TypeError:
                _res = _fn(*_inp.values())
        elif isinstance(_inp, list):
            _res = _fn(*_inp)
        else:
            _res = _fn(_inp)
        _results.append({{"passed": _res == _exp, "actual": _res, "expected": _exp}})
    except Exception as _e:
        _results.append({{
            "passed": False,
            "actual": "{{}}: {{}}".format(type(_e).__name__, _e),
            "expected": _exp,
        }})

print("RESULTS_JSON:" + _json.dumps(_results, default=str))
'''


def build_python_harness(user_code: str, tests: List[Dict[str, Any]], names: List[str]) -> str:
    return user_code + "\n\n" + _PY_HARNESS.format(
        tests=json.dumps(tests), names=json.dumps(names)
    )


_JS_HARNESS = '''
// ── grading harness (appended) ──────────────────────────────────────────────
const _TESTS = {tests};
const _NAMES = {names};

let _fn = null;
for (const _n of _NAMES) {{
  try {{
    const _c = eval(_n);
    if (typeof _c === "function") {{ _fn = _c; break; }}
  }} catch (_e) {{ /* not declared — keep looking */ }}
}}

if (!_fn) {{
  process.stderr.write(
    "Could not find your solution function. Expected one of: " + _NAMES.join(", ") + "\\n"
  );
  process.exit(3);
}}

const _deepEq = (a, b) => {{
  if (a === b) return true;
  if (typeof a === "number" && typeof b === "number") return a === b;
  if (Array.isArray(a) && Array.isArray(b)) {{
    return a.length === b.length && a.every((v, i) => _deepEq(v, b[i]));
  }}
  if (a && b && typeof a === "object" && typeof b === "object") {{
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length === kb.length && ka.every((k) => _deepEq(a[k], b[k]));
  }}
  return false;
}};

const _results = [];
for (const _tc of _TESTS) {{
  const _exp = _tc.expected;
  try {{
    const _inp = _tc.input;
    let _res;
    if (Array.isArray(_inp)) _res = _fn(..._inp);
    else if (_inp !== null && typeof _inp === "object") _res = _fn(...Object.values(_inp));
    else _res = _fn(_inp);
    _results.push({{ passed: _deepEq(_res, _exp), actual: _res === undefined ? null : _res, expected: _exp }});
  }} catch (_e) {{
    _results.push({{ passed: false, actual: String((_e && _e.message) || _e), expected: _exp }});
  }}
}}

console.log("RESULTS_JSON:" + JSON.stringify(_results));
'''


def build_js_harness(user_code: str, tests: List[Dict[str, Any]], names: List[str]) -> str:
    return user_code + "\n\n" + _JS_HARNESS.format(
        tests=json.dumps(tests), names=json.dumps(names)
    )


_RUBY_HARNESS = '''
# ── grading harness (appended) ───────────────────────────────────────────────
require "json"

_tests = JSON.parse({tests!r})
_names = JSON.parse({names!r})

_fn = _names.find {{ |n| respond_to?(n, true) }}
if _fn.nil?
  warn "Could not find your solution function. Expected one of: #{{_names.join(", ")}}"
  exit 3
end

_results = _tests.map do |tc|
  exp = tc["expected"]
  begin
    inp = tc["input"]
    res =
      if inp.is_a?(Array) then send(_fn, *inp)
      elsif inp.is_a?(Hash) then send(_fn, *inp.values)
      else send(_fn, inp)
      end
    {{ "passed" => res == exp, "actual" => res, "expected" => exp }}
  rescue => e
    {{ "passed" => false, "actual" => "#{{e.class}}: #{{e.message}}", "expected" => exp }}
  end
end

puts "RESULTS_JSON:" + JSON.generate(_results)
'''


def build_ruby_harness(user_code: str, tests: List[Dict[str, Any]], names: List[str]) -> str:
    return user_code + "\n\n" + _RUBY_HARNESS.format(
        tests=json.dumps(tests), names=json.dumps(names)
    )


_PHP_HARNESS = '''
// ── grading harness (appended) ──────────────────────────────────────────────
$_tests = json_decode({tests!r}, true);
$_names = json_decode({names!r}, true);

$_fn = null;
foreach ($_names as $_n) {{
    if (function_exists($_n)) {{ $_fn = $_n; break; }}
}}
if ($_fn === null) {{
    fwrite(STDERR, "Could not find your solution function. Expected one of: "
        . implode(", ", $_names) . "\\n");
    exit(3);
}}

$_results = [];
foreach ($_tests as $_tc) {{
    $_exp = $_tc["expected"];
    try {{
        $_inp = $_tc["input"];
        $_args = is_array($_inp) ? array_values($_inp) : [$_inp];
        $_res = call_user_func_array($_fn, $_args);
        $_results[] = ["passed" => $_res == $_exp, "actual" => $_res, "expected" => $_exp];
    }} catch (Throwable $_e) {{
        $_results[] = ["passed" => false, "actual" => get_class($_e) . ": " . $_e->getMessage(), "expected" => $_exp];
    }}
}}

echo "RESULTS_JSON:" . json_encode($_results) . "\\n";
'''


def build_php_harness(user_code: str, tests: List[Dict[str, Any]], names: List[str]) -> str:
    body = user_code.strip()
    if body.startswith("<?php"):
        body = body[len("<?php"):]
    body = body.replace("?>", "")
    return "<?php\n" + body + "\n\n" + _PHP_HARNESS.format(
        tests=json.dumps(tests), names=json.dumps(names)
    )


# ── stdin/stdout (competitive-programming) harness ───────────────────────────
#
# A CodeContests-style problem is a whole program, not a function: it reads a
# case from standard input and writes the answer to standard output. That makes
# it the one problem class where the submission cannot simply be *called* — so
# the driver re-executes it once per case, feeding stdin and capturing stdout,
# rather than appending a harness to the same source file.
#
# The comparison is deliberately whitespace-lenient. Judges for this format
# accept any run of spaces or newlines between tokens, and rejecting an answer
# for a trailing newline would fail submissions that are correct by the rules
# of the format the problem was written for.

_STDIO_HARNESS = '''
# ── stdin/stdout grading harness ─────────────────────────────────────────────
import json as _json, subprocess as _sp, sys as _sys, tempfile as _tf, os as _os

_CASES = _json.loads({cases!r})
_SOURCE = _json.loads({source!r})
_ARGV = _json.loads({argv!r})
_TIMEOUT = {timeout}


def _norm(text):
    """Token sequence, ignoring how the tokens were spaced.

    ``1 2\\n3`` and ``1\\n2 3\\n`` are the same answer in this format; only a
    difference in the tokens themselves is a wrong answer.
    """
    return (text or "").split()


_dir = _tf.mkdtemp()
_path = _os.path.join(_dir, {filename!r})
with open(_path, "w", encoding="utf-8") as _fh:
    _fh.write(_SOURCE)

_results = []
for _case in _CASES:
    _expected = _case.get("output", "")
    try:
        _proc = _sp.run(
            _ARGV + [_path],
            input=_case.get("input", ""),
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        if _proc.returncode != 0:
            # A crash is a failure with the diagnostic, never a pass. The
            # stderr tail is what the candidate needs to see; the full text can
            # be megabytes for a runaway loop.
            _detail = (_proc.stderr or "").strip()[-800:]
            _results.append({{
                "passed": False,
                "actual": _detail or ("exited with status %d" % _proc.returncode),
                "expected": _expected,
            }})
            continue
        _actual = _proc.stdout
        _results.append({{
            "passed": _norm(_actual) == _norm(_expected),
            "actual": _actual.strip()[:2000],
            "expected": _expected,
        }})
    except _sp.TimeoutExpired:
        _results.append({{
            "passed": False,
            "actual": "Timed out after %s seconds" % _TIMEOUT,
            "expected": _expected,
        }})
    except Exception as _e:
        _results.append({{
            "passed": False,
            "actual": "{{}}: {{}}".format(type(_e).__name__, _e),
            "expected": _expected,
        }})

print("RESULTS_JSON:" + _json.dumps(_results, default=str))
'''


# Only interpreted languages can be driven this way: the harness itself is a
# Python program, so it can re-run a script but cannot invoke a compiler that
# may not exist in the sandbox image. A compiled language on a stdio problem
# falls back to compile-only, which reports success=False rather than a pass.
_STDIO_INTERPRETERS: Dict[str, Dict[str, Any]] = {
    # ``python3`` by name, not sys.executable: the harness resolves the
    # interpreter inside the sandbox, where this process's path is meaningless.
    "python": {"argv": ["python3"], "filename": "sol.py"},
    "javascript": {"argv": ["node"], "filename": "sol.js"},
    "ruby": {"argv": ["ruby"], "filename": "sol.rb"},
    "php": {"argv": ["php"], "filename": "sol.php"},
}


def stdio_supports(lang_key: str) -> bool:
    """Whether a stdin/stdout problem can be graded by the in-sandbox driver.

    Only the interpreted languages: that driver is itself a Python program that
    re-executes the submission with ``subprocess``, so it needs an interpreter
    present in the image. A compiled language is graded natively instead — see
    ``code_executor_service._run_stdio_native`` — by running the program once
    per case through the sandbox's own ``stdin``.
    """
    return lang_key in _STDIO_INTERPRETERS


def stdio_tokens(text: str) -> List[str]:
    """The answer as a token sequence, ignoring how the tokens were spaced.

    ``1 2\\n3`` and ``1\\n2 3\\n`` are the same answer in this format; only a
    difference in the tokens themselves is a wrong answer. Shared with the
    in-sandbox driver's ``_norm`` so a submission is judged identically whether
    it was graded natively or through that driver — the same program must not
    pass in Python and fail in Java on spacing alone.
    """
    return (text or "").split()


def build_stdio_harness(
    lang_key: str,
    user_code: str,
    cases: List[Dict[str, Any]],
    timeout: int = 10,
) -> Optional[str]:
    """Grade a whole-program submission against stdin/stdout cases.

    ``cases`` are ``{{input: str, output: str}}``. Returns None when the
    language has no interpreter in the sandbox, so the caller can degrade to
    compile-only rather than emit a harness that cannot run.
    """
    config = _STDIO_INTERPRETERS.get(lang_key)
    if config is None:
        return None
    return _STDIO_HARNESS.format(
        cases=json.dumps(cases),
        source=json.dumps(user_code),
        argv=json.dumps(config["argv"]),
        filename=config["filename"],
        timeout=int(timeout),
    )


# Whole-program skeletons for the languages the imported cache does not ship.
# They are not read by the grader — stdin/stdout problems are graded by running
# the submission with the case as stdin, whatever language it is in — so each is
# just a read-everything, do-nothing program the candidate fills in, matching
# the idiom of the shipped skeletons above.
STDIO_STARTERS: Dict[str, str] = {
    "typescript": (
        "const data = require(\"fs\").readFileSync(0, \"utf8\").split(/\\s+/);\n"
        "// Your code here\n"
    ),
    "java": (
        "import java.util.*;\n"
        "\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        // Your code here\n"
        "    }\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <vector>\n"
        "#include <string>\n"
        "using namespace std;\n"
        "\n"
        "int main() {\n"
        "    string line;\n"
        "    while (getline(cin, line)) {\n"
        "        // Your code here\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    ),
    "csharp": (
        "using System;\n"
        "\n"
        "class Program {\n"
        "    static void Main() {\n"
        "        string line;\n"
        "        while ((line = Console.ReadLine()) != null) {\n"
        "            // Your code here\n"
        "        }\n"
        "    }\n"
        "}\n"
    ),
    "go": (
        "package main\n"
        "\n"
        "import (\n"
        "    \"bufio\"\n"
        "    \"os\"\n"
        ")\n"
        "\n"
        "func main() {\n"
        "    scanner := bufio.NewScanner(os.Stdin)\n"
        "    for scanner.Scan() {\n"
        "        // Your code here\n"
        "    }\n"
        "}\n"
    ),
    "rust": (
        "use std::io::{self, BufRead};\n"
        "\n"
        "fn main() {\n"
        "    for line in io::stdin().lock().lines() {\n"
        "        // Your code here\n"
        "    }\n"
        "}\n"
    ),
    "swift": (
        "import Foundation\n"
        "\n"
        "while let line = readLine() {\n"
        "    // Your code here\n"
        "}\n"
    ),
    "haskell": (
        "import System.IO\n"
        "\n"
        "main :: IO ()\n"
        "main = do\n"
        "    contents <- getContents\n"
        "    -- Your code here\n"
        "    return ()\n"
    ),
    "erlang": (
        "-module(main).\n"
        "-export([main/1]).\n"
        "\n"
        "main(_) ->\n"
        "    case io:get_line(\"\") of\n"
        "        eof -> ok;\n"
        "        _ -> ok\n"
        "    end.\n"
    ),
    # Plain C stdio, not Foundation's NSFileHandle, and no ``@autoreleasepool``:
    # the toolchain that builds this predates the pool syntax (see the note in
    # ``static_harness``), and reading stdin with ``scanf`` needs nothing from
    # Foundation at all.
    "objectivec": (
        "#import <Foundation/Foundation.h>\n"
        "#include <stdio.h>\n"
        "\n"
        "int main(void) {\n"
        "    int n;\n"
        "    while (scanf(\"%d\", &n) == 1) {\n"
        "        // Your code here\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    ),
}


# ── SQL (database) harness ───────────────────────────────────────────────────
#
# A database problem is answered with a query, not a function call. Each test
# case carries the INSERT statements that seed the schema plus the expected
# result rows. The harness builds an in-memory SQLite database from the
# problem's schema, runs the candidate's query against each seed, and compares
# the resulting rows. SQL result order is unspecified without an ORDER BY, so
# both sides are compared as sorted row sets rather than in emitted order.

_SQL_HARNESS = '''
# ── SQL grading harness (appended) ───────────────────────────────────────────
import json as _json, sqlite3 as _sqlite3

_SCHEMA = _json.loads({schema!r})
_CASES = _json.loads({cases!r})
_QUERY = _json.loads({query!r})


def _row_key(row):
    return _json.dumps(list(row), default=str)


_results = []
for _tc in _CASES:
    _exp = _tc.get("expected", [])
    try:
        _conn = _sqlite3.connect(":memory:")
        _cur = _conn.cursor()
        for _stmt in _SCHEMA:
            _cur.execute(_stmt)
        for _stmt in _tc.get("seed", []):
            _cur.execute(_stmt)
        _cur.execute(_QUERY)
        _rows = [list(_r) for _r in _cur.fetchall()]
        _conn.close()
        _results.append({{
            "passed": sorted(_rows, key=_row_key) == sorted(_exp, key=_row_key),
            "actual": _rows,
            "expected": _exp,
        }})
    except Exception as _e:
        _results.append({{
            "passed": False,
            "actual": "{{}}: {{}}".format(type(_e).__name__, _e),
            "expected": _exp,
        }})

print("RESULTS_JSON:" + _json.dumps(_results, default=str))
'''


def build_sql_harness(
    user_query: str,
    cases: List[Dict[str, Any]],
    schema: List[str],
) -> str:
    """Grade a candidate's SQL query against schema + per-case seed data.

    ``cases`` are ``{{seed: [INSERT ...], expected: [[row], ...]}}`` dicts. A
    query that errors on a case is a failure with the SQLite message, never a
    pass — the RESULTS_JSON contract is unchanged.
    """
    return _SQL_HARNESS.format(
        schema=json.dumps(schema),
        cases=json.dumps(cases),
        query=json.dumps(user_query),
    )


HARNESS_BUILDERS = {
    "python": build_python_harness,
    "javascript": build_js_harness,
    "typescript": build_js_harness,
    "ruby": build_ruby_harness,
    "php": build_php_harness,
}


# ── Design (stateful class) harnesses ────────────────────────────────────────
#
# Design problems grade an *operation sequence* against a class instance rather
# than one function call. Each normalized test case carries ``ctor`` (constructor
# arguments), ``ops`` (``[method, *args]`` per step) and ``expected`` (one value
# per op, null for methods that return nothing). The same
# ``RESULTS_JSON`` contract applies: no verdict line means the run failed.

_PY_DESIGN_HARNESS = '''
# ── design grading harness (appended) ────────────────────────────────────────
import json as _json, sys as _sys

_TESTS = _json.loads({tests!r})
_NAMES = _json.loads({names!r})

_cls = None
for _n in _NAMES:
    _c = globals().get(_n)
    if isinstance(_c, type):
        _cls = _c
        break

if _cls is None:
    _sys.stderr.write(
        "Could not find your solution class. Expected one of: " + ", ".join(_NAMES) + "\\n"
    )
    raise SystemExit(3)

_results = []
for _tc in _TESTS:
    _exp = _tc["expected"]
    try:
        _inst = _cls(*_tc["ctor"])
        _actual = []
        for _op in _tc["ops"]:
            _name, _args = _op[0], _op[1:]
            _m = getattr(_inst, _name, None)
            if not callable(_m):
                raise AttributeError("missing method: " + str(_name))
            _actual.append(_m(*_args))
        _results.append({{"passed": _actual == _exp, "actual": _actual, "expected": _exp}})
    except Exception as _e:
        _results.append({{
            "passed": False,
            "actual": "{{}}: {{}}".format(type(_e).__name__, _e),
            "expected": _exp,
        }})

print("RESULTS_JSON:" + _json.dumps(_results, default=str))
'''


def build_python_design_harness(
    user_code: str, tests: List[Dict[str, Any]], names: List[str]
) -> str:
    return user_code + "\n\n" + _PY_DESIGN_HARNESS.format(
        tests=json.dumps(tests), names=json.dumps(names)
    )


_JS_DESIGN_HARNESS = '''
// ── design grading harness (appended) ───────────────────────────────────────
const _TESTS = {tests};
const _NAMES = {names};

let _Cls = null;
for (const _n of _NAMES) {{
  try {{
    const _c = eval(_n);
    if (typeof _c === "function") {{ _Cls = _c; break; }}
  }} catch (_e) {{ /* not declared — keep looking */ }}
}}

if (!_Cls) {{
  process.stderr.write(
    "Could not find your solution class. Expected one of: " + _NAMES.join(", ") + "\\n"
  );
  process.exit(3);
}}

const _deepEq = (a, b) => {{
  if (a === b) return true;
  if (a == null || b == null) return a == null && b == null;
  if (Array.isArray(a) && Array.isArray(b)) {{
    return a.length === b.length && a.every((v, i) => _deepEq(v, b[i]));
  }}
  if (typeof a === "object" && typeof b === "object") {{
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length === kb.length && ka.every((k) => _deepEq(a[k], b[k]));
  }}
  return false;
}};

const _results = [];
for (const _tc of _TESTS) {{
  const _exp = _tc.expected;
  try {{
    const _inst = new _Cls(..._tc.ctor);
    const _actual = [];
    for (const _op of _tc.ops) {{
      const _name = _op[0], _args = _op.slice(1);
      if (typeof _inst[_name] !== "function") {{
        throw new Error("missing method: " + _name);
      }}
      const _r = _inst[_name](..._args);
      _actual.push(_r === undefined ? null : _r);
    }}
    _results.push({{ passed: _deepEq(_actual, _exp), actual: _actual, expected: _exp }});
  }} catch (_e) {{
    _results.push({{ passed: false, actual: String((_e && _e.message) || _e), expected: _exp }});
  }}
}}

console.log("RESULTS_JSON:" + JSON.stringify(_results));
'''


def build_js_design_harness(
    user_code: str, tests: List[Dict[str, Any]], names: List[str]
) -> str:
    return user_code + "\n\n" + _JS_DESIGN_HARNESS.format(
        tests=json.dumps(tests), names=json.dumps(names)
    )


DESIGN_HARNESS_BUILDERS = {
    "python": build_python_design_harness,
    "javascript": build_js_design_harness,
    "typescript": build_js_design_harness,
}

DESIGN_UNSUPPORTED = (
    "This is a design problem graded by replaying an operation sequence against "
    "your class. That is supported for Python, JavaScript, and TypeScript; {lang} "
    "code is compiled and syntax-checked, but not graded."
)
