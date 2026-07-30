"""Per-language execution specs and generic test harnesses.

Every runner here obeys one contract: the program prints a single line
``RESULTS_JSON:[...]`` holding one ``{passed, actual, expected}`` object per test
case. If that line is absent, the run *failed* — there is no code path that
invents a passing result.

Two classes of language:

- **Dynamic** (Python, JavaScript, TypeScript, Ruby, PHP). Arguments can be
  bound from JSON and the entry point looked up by name at runtime, so one
  generic harness per language covers every problem.
- **Static** (Java, C++, C#, Go, Rust, Swift, Haskell, Erlang). Binding JSON to
  a typed signature needs per-problem type information that no problem in this
  repo declares. These compile for real and report real compiler diagnostics,
  but cannot be auto-graded — see ``VERIFY_UNSUPPORTED``. They report
  ``success=False``, never a pass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

VERIFY_UNSUPPORTED = (
    "Automated test-case verification is not available for {lang} yet: the "
    "problem definition does not declare per-language argument types, so test "
    "inputs cannot be bound to a typed signature. Your code was compiled and "
    "syntax-checked, but not graded."
)


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


# Images are pinned and must be pulled ahead of time (see docs/coding-sandbox).
# They are only consulted by the Docker backend; Piston needs the `piston` name
# instead. A language with neither a pulled image nor a Piston runtime surfaces
# as unavailable rather than as a wrong verdict.
LANGUAGES: Dict[str, LanguageSpec] = {
    "python": LanguageSpec(
        name="Python",
        image="python:3.12-alpine",
        source_name="main.py",
        run_cmd=["python", "-I", "/build/main.py"],
        aliases=("python3", "py"),
        piston="python",
    ),
    "javascript": LanguageSpec(
        name="JavaScript",
        image="node:22-alpine",
        source_name="main.js",
        run_cmd=["node", "/build/main.js"],
        aliases=("js", "node"),
        piston="javascript",
    ),
    "typescript": LanguageSpec(
        name="TypeScript",
        image="node:22-alpine",
        source_name="main.js",  # types are stripped before writing
        run_cmd=["node", "/build/main.js"],
        aliases=("ts",),
        # Types are stripped before submission, so this runs as plain JS.
        piston="javascript",
    ),
    "ruby": LanguageSpec(
        name="Ruby",
        image="ruby:3.3-alpine",
        source_name="main.rb",
        run_cmd=["ruby", "/build/main.rb"],
        aliases=("rb",),
        piston="ruby",
    ),
    "php": LanguageSpec(
        name="PHP",
        image="php:8.3-cli-alpine",
        source_name="main.php",
        run_cmd=["php", "/build/main.php"],
        aliases=(),
        piston="php",
    ),
    # ── Compile-only: real compiler, no auto-grading ──────────────────────
    "java": LanguageSpec(
        name="Java",
        image="eclipse-temurin:21-jdk-alpine",
        source_name="Solution.java",
        compile_cmd=["javac", "-d", "/build", "/build/Solution.java"],
        run_cmd=["java", "-cp", "/build", "Solution"],
        dynamic=False,
        piston="java",
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
    ),
    "csharp": LanguageSpec(
        name="C#",
        image="mcr.microsoft.com/dotnet/sdk:8.0-alpine",
        source_name="Program.cs",
        run_cmd=["dotnet", "run", "--project", "/build"],
        dynamic=False,
        aliases=("c#", "cs"),
        piston="csharp",
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
    ),
    "swift": LanguageSpec(
        name="Swift",
        image="swift:5.10",
        source_name="main.swift",
        compile_cmd=["swiftc", "-o", "/build/main", "/build/main.swift"],
        run_cmd=["/build/main"],
        dynamic=False,
        piston="swift",
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
    ),
    "erlang": LanguageSpec(
        name="Erlang",
        image="erlang:27-alpine",
        source_name="solution.erl",
        compile_cmd=["erlc", "-o", "/build", "/build/solution.erl"],
        run_cmd=["escript", "/build/solution.beam"],
        dynamic=False,
        piston="erlang",
    ),
    "objectivec": LanguageSpec(
        name="Objective-C",
        image="gcc:14",
        source_name="main.m",
        compile_cmd=["gcc", "-o", "/build/main", "/build/main.m"],
        run_cmd=["/build/main"],
        dynamic=False,
        aliases=("objc",),
        # Piston ships no Objective-C runtime; Docker handles it.
        piston="",
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
