"""Typed grading harnesses for statically typed languages.

The dynamic languages in :mod:`app.services.code_runners` are graded by binding
JSON test inputs to a function looked up by name at runtime. A statically typed
language cannot do that: it needs a declared signature to call and typed values
to call it with, and no problem in this repo declares per-language types.

This module derives both from the test data itself. ``infer_signature`` reads the
recorded inputs and expected outputs and produces a concrete signature; the same
signature then generates *both* the candidate's starter code and the harness's
call site, so the two agree by construction rather than by convention.

Two design decisions keep the generated code small and portable:

- **Literals are emitted into the source**, not parsed at runtime. Judge0's
  toolchains give us no JSON parser for Java, C++, Rust or Haskell (bare
  ``rustc`` has no serde, ``javac`` has no stdlib JSON), and hand-rolling one per
  language would dwarf everything else here.
- **Verdicts compare rendered JSON strings.** Every harness already has to render
  ``actual`` to report it, and the expected value is a compile-time constant, so
  ``passed`` reduces to a string comparison. That removes the need for a deep
  equality routine in nine languages.

Anything the inference cannot type exactly returns ``None``, and the caller falls
back to compiling without grading. Guessing at a binding would risk reporting a
verdict against the wrong call — the one thing this pipeline must never do.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Nesting beyond a matrix does not appear in the problem bank, and each extra
# level costs another renderer branch in nine languages.
_MAX_LIST_DEPTH = 2
_INT32_MIN, _INT32_MAX = -(2 ** 31), 2 ** 31 - 1


# ── Type lattice ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Type:
    """``int``/``float``/``str``/``bool``, or ``list`` with an element type.

    A ``list`` whose ``item`` is None came from an empty list — the element type
    is not yet known and must be resolved by unifying with another test case.
    """

    kind: str
    item: Optional["Type"] = None

    def __str__(self) -> str:
        if self.kind == "list":
            return f"list[{self.item if self.item else '?'}]"
        return self.kind


INT = Type("int")
FLOAT = Type("float")
STR = Type("str")
BOOL = Type("bool")


def _list_of(item: Optional[Type]) -> Type:
    return Type("list", item)


@dataclass(frozen=True)
class Param:
    name: str
    type: Type


@dataclass(frozen=True)
class Signature:
    params: Tuple[Param, ...]
    ret: Type


# ── Inference ─────────────────────────────────────────────────────────────────


def _infer_value(value: Any, depth: int = 0) -> Optional[Type]:
    """Type of one recorded value, or None if it is outside the lattice."""
    # bool first: in Python ``bool`` is a subclass of ``int``.
    if isinstance(value, bool):
        return BOOL
    if isinstance(value, int):
        return INT if _INT32_MIN <= value <= _INT32_MAX else None
    if isinstance(value, float):
        # inf/nan have no portable literal spelling across nine languages.
        return FLOAT if value == value and abs(value) != float("inf") else None
    if isinstance(value, str):
        # Non-ASCII would need a different escape spelling per language
        # (``\uXXXX`` in Java, ``\u{XXXX}`` in Rust, raw bytes in C).
        return STR if value.isascii() else None
    if isinstance(value, list):
        if depth >= _MAX_LIST_DEPTH:
            return None
        if not value:
            return _list_of(None)
        item: Optional[Type] = None
        for element in value:
            element_type = _infer_value(element, depth + 1)
            if element_type is None:
                return None
            item = element_type if item is None else _unify(item, element_type)
            if item is None:
                return None
        return _list_of(item)
    # None, dict, and everything else.
    return None


def _unify(a: Optional[Type], b: Optional[Type]) -> Optional[Type]:
    """Least type covering both, or None when they genuinely disagree."""
    if a is None or b is None:
        return None
    if a == b:
        return a
    # An int seen alongside a float is a float; bool never widens, because a
    # column of true/false graded as numbers would report nonsense.
    if {a.kind, b.kind} == {"int", "float"}:
        return FLOAT
    if a.kind == "list" and b.kind == "list":
        if a.item is None:
            return b
        if b.item is None:
            return a
        item = _unify(a.item, b.item)
        return _list_of(item) if item else None
    return None


def _resolved(t: Optional[Type]) -> bool:
    """False when an empty list left an element type undetermined."""
    if t is None:
        return False
    if t.kind == "list":
        return t.item is not None and _resolved(t.item)
    return True


def _case_arguments(raw_input: Any) -> Optional[List[Tuple[str, Any]]]:
    """Ordered (name, value) pairs for one test case's input."""
    if isinstance(raw_input, dict):
        return list(raw_input.items())
    if isinstance(raw_input, list):
        return [(f"arg{i}", v) for i, v in enumerate(raw_input)]
    if raw_input is None:
        return None
    return [("arg0", raw_input)]


def infer_signature(test_cases: Sequence[Dict[str, Any]]) -> Optional[Signature]:
    """Derive one concrete signature covering every test case, or None.

    Every case must agree on arity, parameter names and types. Disagreement
    means the recorded data does not describe a single typed function, so there
    is nothing safe to generate.
    """
    if not test_cases:
        return None

    names: Optional[List[str]] = None
    param_types: List[Optional[Type]] = []
    ret: Optional[Type] = None

    for index, case in enumerate(test_cases):
        arguments = _case_arguments(case.get("input"))
        if not arguments:
            return None

        case_names = [name for name, _ in arguments]
        if names is None:
            names = case_names
            param_types = [None] * len(case_names)
        elif case_names != names:
            return None

        for position, (_, value) in enumerate(arguments):
            value_type = _infer_value(value)
            if value_type is None:
                return None
            param_types[position] = (
                value_type
                if param_types[position] is None
                else _unify(param_types[position], value_type)
            )
            if param_types[position] is None:
                return None

        expected_type = _infer_value(case.get("expected"))
        if expected_type is None:
            return None
        ret = expected_type if index == 0 else _unify(ret, expected_type)
        if ret is None:
            return None

    if names is None or ret is None:
        return None
    if not all(_resolved(t) for t in param_types) or not _resolved(ret):
        return None
    # Floating-point returns are excluded deliberately: the verdict compares
    # rendered text, and nine languages do not agree on how to print a double.
    if _contains_float(ret):
        return None

    return Signature(
        params=tuple(Param(_safe_name(n), t) for n, t in zip(names, param_types)),  # type: ignore[arg-type]
        ret=ret,
    )


def _contains_float(t: Type) -> bool:
    if t.kind == "float":
        return True
    return bool(t.kind == "list" and t.item and _contains_float(t.item))


_RESERVED = {
    "int", "float", "double", "char", "bool", "boolean", "string", "str", "class",
    "struct", "return", "if", "else", "for", "while", "new", "var", "let", "func",
    "function", "def", "type", "case", "switch", "default", "public", "private",
    "static", "void", "main", "map", "range", "len", "list", "array", "object",
    "true", "false", "null", "nil", "none", "and", "or", "not", "in", "is", "do",
    "end", "then", "where", "data", "module", "import", "package", "use", "mut",
}


def _safe_name(name: str) -> str:
    """A parameter name that is a legal identifier in all nine languages."""
    cleaned = re.sub(r"\W", "_", str(name)) or "arg"
    if cleaned[0].isdigit():
        cleaned = f"a_{cleaned}"
    if cleaned.lower() in _RESERVED:
        cleaned = f"{cleaned}_"
    return cleaned


# ── Entry-point naming ────────────────────────────────────────────────────────


def _to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest if part)


def entry_name(candidates: Sequence[str], style: str) -> str:
    """Pick one entry-point spelling in the target language's convention.

    The generated starter and the generated call site both come from here, so
    whatever this returns is what the candidate is given to write.
    """
    base = next((c for c in candidates if c), "solve")
    if style == "snake":
        return _to_snake(base)
    camel = _to_camel(base)
    if style == "pascal":
        return camel[:1].upper() + camel[1:]
    return camel[:1].lower() + camel[1:]


# ── Shared literal helpers ────────────────────────────────────────────────────


def _json_text(value: Any) -> str:
    """The exact text a correct harness must produce for this value."""
    return json.dumps(value, separators=(",", ":"))


def _c_string(value: str) -> str:
    """A double-quoted literal valid in C, Java, C#, Go, Rust, Swift."""
    return json.dumps(value)


# ── Renderers ─────────────────────────────────────────────────────────────────
#
# One class per language. Each turns a Signature into three things: the starter
# the candidate edits, a complete program that runs every case, and a standalone
# wrapper used by the compile-only fallback so a function-shaped submission still
# reaches the compiler.
#
# Only the *return* type needs JSON rendering — arguments are emitted as literals
# and the expected value is a precomputed constant string.


class _Renderer:
    key = ""
    style = "camel"          # entry-point naming convention
    prefix = "zzJ"           # helper-name prefix, per language identifier rules

    # -- type-directed pieces, implemented per language ------------------------

    def type_name(self, t: Type) -> str:
        raise NotImplementedError

    def literal(self, value: Any, t: Type) -> str:
        raise NotImplementedError

    def zero(self, t: Type) -> str:
        raise NotImplementedError

    def scalar_json(self, expr: str, t: Type) -> str:
        raise NotImplementedError

    def list_helper(self, name: str, t: Type) -> str:
        raise NotImplementedError

    def quote_helper(self) -> str:
        raise NotImplementedError

    # -- shared plumbing -------------------------------------------------------

    def helper_name(self, t: Type) -> str:
        return self.prefix + str(t).replace("list[", "_L").replace("]", "")

    def json_expr(self, expr: str, t: Type) -> str:
        if t.kind == "list":
            return f"{self.helper_name(t)}({expr})"
        return self.scalar_json(expr, t)

    def helpers(self, ret: Type) -> str:
        """Every helper the return type needs, innermost first."""
        parts: List[str] = []
        if _contains_str(ret):
            parts.append(self.quote_helper())
        for t in _list_types(ret):
            parts.append(self.list_helper(self.helper_name(t), t))
        return "\n".join(parts)

    def call(self, entry: str, sig: Signature, values: Sequence[Any]) -> str:
        args = ", ".join(
            self.literal(v, p.type) for v, p in zip(values, sig.params)
        )
        return f"{entry}({args})"

    def params(self, sig: Signature) -> str:
        return ", ".join(f"{self.type_name(p.type)} {p.name}" for p in sig.params)

    # -- outputs ---------------------------------------------------------------

    def starter(self, entry: str, sig: Signature) -> str:
        raise NotImplementedError

    def program(
        self, entry: str, sig: Signature, cases: Sequence[Dict[str, Any]], user_code: str
    ) -> str:
        raise NotImplementedError

    def standalone(self, user_code: str) -> str:
        """Wrap a function-only submission so it can be compiled on its own."""
        return user_code


def _contains_str(t: Type) -> bool:
    if t.kind == "str":
        return True
    return bool(t.kind == "list" and t.item and _contains_str(t.item))


def _list_types(t: Type) -> List[Type]:
    """List types inside ``t``, innermost first, so helpers define in order."""
    if t.kind != "list" or t.item is None:
        return []
    return _list_types(t.item) + [t]


def _case_values(case: Dict[str, Any], sig: Signature) -> List[Any]:
    raw = case.get("input")
    if isinstance(raw, dict):
        return list(raw.values())
    if isinstance(raw, list):
        return list(raw)
    return [raw]


# ── Java ──────────────────────────────────────────────────────────────────────

_JAVA_TEMPLATE = """import java.util.*;

@@USER@@

public class Main {
@@HELPERS@@
    static String zzCase(String a, String e) {
        return "{\\"passed\\":" + (a.equals(e) ? "true" : "false")
            + ",\\"actual\\":" + a + ",\\"expected\\":" + e + "}";
    }

    public static void main(String[] zzArgv) {
        Solution zzSol = new Solution();
        String[] zzR = new String[] {
@@CASES@@
        };
        StringBuilder zzB = new StringBuilder("RESULTS_JSON:[");
        for (int i = 0; i < zzR.length; i++) {
            if (i > 0) zzB.append(',');
            zzB.append(zzR[i]);
        }
        System.out.println(zzB.append(']').toString());
    }
}
"""

_JAVA_PUBLIC_CLASS = re.compile(r"\bpublic\s+((?:final\s+|abstract\s+)?class\s+)")


class _Java(_Renderer):
    key = "java"
    style = "camel"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return self.type_name(t.item) + "[]"  # type: ignore[arg-type]
        return {"int": "int", "float": "double", "bool": "boolean", "str": "String"}[t.kind]

    def literal(self, value: Any, t: Type, top: bool = True) -> str:
        if t.kind == "list":
            inner = ", ".join(self.literal(v, t.item, False) for v in value)  # type: ignore[arg-type]
            head = f"new {self.type_name(t)} " if top else ""
            return head + "{" + inner + "}"
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return f"new {self.type_name(t)} {{}}"
        return {"int": "0", "float": "0.0", "bool": "false", "str": '""'}[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zzQ({expr})"
        return f"String.valueOf({expr})"

    def quote_helper(self) -> str:
        return (
            '    static String zzQ(String s) {\n'
            '        StringBuilder b = new StringBuilder("\\"");\n'
            '        for (int i = 0; i < s.length(); i++) {\n'
            '            char c = s.charAt(i);\n'
            "            if (c == '\"' || c == '\\\\') b.append('\\\\').append(c);\n"
            "            else if (c == '\\n') b.append(\"\\\\n\");\n"
            "            else if (c == '\\r') b.append(\"\\\\r\");\n"
            "            else if (c == '\\t') b.append(\"\\\\t\");\n"
            '            else if (c < 32) b.append(String.format("\\\\u%04x", (int) c));\n'
            "            else b.append(c);\n"
            "        }\n"
            "        return b.append('\"').toString();\n"
            "    }\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        item = self.json_expr("a[i]", t.item)  # type: ignore[arg-type]
        return (
            f"    static String {name}({self.type_name(t)} a) {{\n"
            '        StringBuilder b = new StringBuilder("[");\n'
            "        for (int i = 0; i < a.length; i++) {\n"
            "            if (i > 0) b.append(',');\n"
            f"            b.append({item});\n"
            "        }\n"
            "        return b.append(']').toString();\n"
            "    }\n"
        )

    def starter(self, entry: str, sig: Signature) -> str:
        return (
            "class Solution {\n"
            f"    public {self.type_name(sig.ret)} {entry}({self.params(sig)}) {{\n"
            "        // Write your solution here.\n"
            f"        return {self.zero(sig.ret)};\n"
            "    }\n"
            "}\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"zzSol.{entry}({args})", sig.ret)
            rows.append(
                f"            zzCase({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            _JAVA_TEMPLATE.replace("@@USER@@", _java_demote_public(user_code.strip()))
            .replace("@@HELPERS@@", self.helpers(sig.ret))
            .replace("@@CASES@@", ",\n".join(rows))
        )

    def standalone(self, user_code: str) -> str:
        return "import java.util.*;\n\n" + _java_demote_public(user_code.strip()) + "\n"


def _java_demote_public(source: str) -> str:
    """Drop ``public`` from top-level classes so any name fits ``Main.java``.

    Java ties a public class to its filename. The harness owns the file (it holds
    ``public class Main``), and the compile-only path writes the same filename, so
    a submission that opens with ``public class Solution`` would otherwise fail to
    compile for a reason that has nothing to do with the candidate's logic.
    """
    return _JAVA_PUBLIC_CLASS.sub(r"\1", source)


# ── C++ ───────────────────────────────────────────────────────────────────────

_CPP_PRELUDE = """#include <algorithm>
#include <climits>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <iostream>
#include <map>
#include <numeric>
#include <queue>
#include <set>
#include <sstream>
#include <stack>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
using namespace std;
"""

_CPP_CASE_HELPER = """static string zzCase(const string& a, const string& e) {
    return string("{\\"passed\\":") + (a == e ? "true" : "false")
        + ",\\"actual\\":" + a + ",\\"expected\\":" + e + "}";
}
"""


class _Cpp(_Renderer):
    key = "cpp"
    style = "camel"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return f"vector<{self.type_name(t.item)}>"  # type: ignore[arg-type]
        return {"int": "int", "float": "double", "bool": "bool", "str": "string"}[t.kind]

    def literal(self, value: Any, t: Type, top: bool = True) -> str:
        if t.kind == "list":
            inner = ", ".join(self.literal(v, t.item, False) for v in value)  # type: ignore[arg-type]
            head = self.type_name(t) if top else ""
            return head + "{" + inner + "}"
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return f"string({_c_string(value)})"
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "{}"
        return {"int": "0", "float": "0.0", "bool": "false", "str": '""'}[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zzQ({expr})"
        if t.kind == "bool":
            return f'string(({expr}) ? "true" : "false")'
        return f"to_string({expr})"

    def quote_helper(self) -> str:
        return (
            "static string zzQ(const string& s) {\n"
            '    string r = "\\"";\n'
            "    for (size_t i = 0; i < s.size(); i++) {\n"
            "        char c = s[i];\n"
            "        if (c == '\"' || c == '\\\\') { r += '\\\\'; r += c; }\n"
            '        else if (c == \'\\n\') r += "\\\\n";\n'
            '        else if (c == \'\\r\') r += "\\\\r";\n'
            '        else if (c == \'\\t\') r += "\\\\t";\n'
            "        else if ((unsigned char) c < 32) {\n"
            "            char b[8];\n"
            '            snprintf(b, sizeof b, "\\\\u%04x", (unsigned) (unsigned char) c);\n'
            "            r += b;\n"
            "        }\n"
            "        else r += c;\n"
            "    }\n"
            "    return r + '\"';\n"
            "}\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        item = self.json_expr("a[i]", t.item)  # type: ignore[arg-type]
        return (
            f"static string {name}(const {self.type_name(t)}& a) {{\n"
            '    string r = "[";\n'
            "    for (size_t i = 0; i < a.size(); i++) {\n"
            "        if (i) r += ',';\n"
            f"        r += {item};\n"
            "    }\n"
            "    return r + ']';\n"
            "}\n"
        )

    def starter(self, entry: str, sig: Signature) -> str:
        return (
            f"{self.type_name(sig.ret)} {entry}({self.params(sig)}) {{\n"
            "    // Write your solution here.\n"
            f"    return {self.zero(sig.ret)};\n"
            "}\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"{entry}({args})", sig.ret)
            rows.append(
                f"        zzCase({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            _CPP_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\n"
            + _CPP_CASE_HELPER
            + "\nint main() {\n"
            + "    string zzR[] = {\n"
            + ",\n".join(rows)
            + "\n    };\n"
            + '    string zzOut = "RESULTS_JSON:[";\n'
            + "    for (size_t i = 0; i < sizeof(zzR) / sizeof(zzR[0]); i++) {\n"
            + "        if (i) zzOut += ',';\n"
            + "        zzOut += zzR[i];\n"
            + "    }\n"
            + '    cout << zzOut << "]" << endl;\n'
            + "    return 0;\n}\n"
        )

    def standalone(self, user_code: str) -> str:
        return _CPP_PRELUDE + "\n" + user_code.strip() + "\n\nint main() { return 0; }\n"


# ── C# ────────────────────────────────────────────────────────────────────────

_CSHARP_PRELUDE = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
"""


class _CSharp(_Renderer):
    key = "csharp"
    style = "pascal"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return self.type_name(t.item) + "[]"  # type: ignore[arg-type]
        return {"int": "int", "float": "double", "bool": "bool", "str": "string"}[t.kind]

    def literal(self, value: Any, t: Type) -> str:
        if t.kind == "list":
            # C# jagged arrays need the element type spelled out at every level.
            inner = ", ".join(self.literal(v, t.item) for v in value)  # type: ignore[arg-type]
            return f"new {self.type_name(t)} {{{inner}}}"
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return f"new {self.type_name(t)} {{}}"
        return {"int": "0", "float": "0.0", "bool": "false", "str": '""'}[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zzQ({expr})"
        if t.kind == "bool":
            # bool.ToString() yields "True"; JSON wants lowercase.
            return f'(({expr}) ? "true" : "false")'
        if t.kind == "float":
            return f"({expr}).ToString(System.Globalization.CultureInfo.InvariantCulture)"
        return f"({expr}).ToString()"

    def quote_helper(self) -> str:
        return (
            "    static string zzQ(string s) {\n"
            '        var b = new StringBuilder("\\"");\n'
            "        foreach (char c in s) {\n"
            "            if (c == '\"' || c == '\\\\') { b.Append('\\\\'); b.Append(c); }\n"
            '            else if (c == \'\\n\') b.Append("\\\\n");\n'
            '            else if (c == \'\\r\') b.Append("\\\\r");\n'
            '            else if (c == \'\\t\') b.Append("\\\\t");\n'
            '            else if (c < 32) b.Append("\\\\u").Append(((int) c).ToString("x4"));\n'
            "            else b.Append(c);\n"
            "        }\n"
            "        return b.Append('\"').ToString();\n"
            "    }\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        item = self.json_expr("a[i]", t.item)  # type: ignore[arg-type]
        return (
            f"    static string {name}({self.type_name(t)} a) {{\n"
            '        var b = new StringBuilder("[");\n'
            "        for (int i = 0; i < a.Length; i++) {\n"
            "            if (i > 0) b.Append(',');\n"
            f"            b.Append({item});\n"
            "        }\n"
            "        return b.Append(']').ToString();\n"
            "    }\n"
        )

    def starter(self, entry: str, sig: Signature) -> str:
        return (
            "public class Solution {\n"
            f"    public {self.type_name(sig.ret)} {entry}({self.params(sig)}) {{\n"
            "        // Write your solution here.\n"
            f"        return {self.zero(sig.ret)};\n"
            "    }\n"
            "}\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"zzSol.{entry}({args})", sig.ret)
            rows.append(
                f"            zzCase({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            _CSHARP_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\npublic class ZzMain {\n"
            + self.helpers(sig.ret)
            + "\n    static string zzCase(string a, string e) {\n"
            + '        return "{\\"passed\\":" + (a == e ? "true" : "false")\n'
            + '            + ",\\"actual\\":" + a + ",\\"expected\\":" + e + "}";\n'
            + "    }\n\n"
            + "    public static void Main() {\n"
            + "        var zzSol = new Solution();\n"
            + "        string[] zzR = new string[] {\n"
            + ",\n".join(rows)
            + "\n        };\n"
            + '        Console.WriteLine("RESULTS_JSON:[" + string.Join(",", zzR) + "]");\n'
            + "    }\n}\n"
        )

    def standalone(self, user_code: str) -> str:
        return (
            _CSHARP_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\npublic class ZzMain { public static void Main() { } }\n"
        )


# ── Go ────────────────────────────────────────────────────────────────────────
#
# Go rejects unused imports, and a candidate cannot add to the import block from
# inside a function body. So the prelude imports the packages a solution is
# likely to reach for and keeps each one referenced with a blank assignment.

_GO_PRELUDE = """package main

import (
\t"fmt"
\t"math"
\t"sort"
\t"strconv"
\t"strings"
)

// Keeps the imports above legal whether or not your solution uses them.
var _, _, _, _, _ = fmt.Sprint, math.Abs, sort.Ints, strconv.Itoa, strings.Join
"""


class _Go(_Renderer):
    key = "go"
    style = "camel"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return "[]" + self.type_name(t.item)  # type: ignore[arg-type]
        return {"int": "int", "float": "float64", "bool": "bool", "str": "string"}[t.kind]

    def literal(self, value: Any, t: Type, top: bool = True) -> str:
        if t.kind == "list":
            inner = ", ".join(self.literal(v, t.item, False) for v in value)  # type: ignore[arg-type]
            head = self.type_name(t) if top else ""
            return head + "{" + inner + "}"
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "nil"
        return {"int": "0", "float": "0", "bool": "false", "str": '""'}[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zzQ({expr})"
        if t.kind == "bool":
            return f"strconv.FormatBool({expr})"
        if t.kind == "float":
            return f'strconv.FormatFloat({expr}, \'g\', -1, 64)'
        return f"strconv.Itoa({expr})"

    def quote_helper(self) -> str:
        return (
            "func zzQ(s string) string {\n"
            '\tvar b strings.Builder\n'
            "\tb.WriteByte('\"')\n"
            "\tfor _, r := range s {\n"
            "\t\tswitch {\n"
            "\t\tcase r == '\"' || r == '\\\\':\n"
            "\t\t\tb.WriteByte('\\\\')\n"
            "\t\t\tb.WriteRune(r)\n"
            "\t\tcase r == '\\n':\n"
            '\t\t\tb.WriteString("\\\\n")\n'
            "\t\tcase r == '\\r':\n"
            '\t\t\tb.WriteString("\\\\r")\n'
            "\t\tcase r == '\\t':\n"
            '\t\t\tb.WriteString("\\\\t")\n'
            "\t\tcase r < 32:\n"
            '\t\t\tb.WriteString(fmt.Sprintf("\\\\u%04x", r))\n'
            "\t\tdefault:\n"
            "\t\t\tb.WriteRune(r)\n"
            "\t\t}\n"
            "\t}\n"
            "\tb.WriteByte('\"')\n"
            "\treturn b.String()\n"
            "}\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        item = self.json_expr("v", t.item)  # type: ignore[arg-type]
        return (
            f"func {name}(a {self.type_name(t)}) string {{\n"
            "\tparts := make([]string, 0, len(a))\n"
            "\tfor _, v := range a {\n"
            f"\t\tparts = append(parts, {item})\n"
            "\t}\n"
            '\treturn "[" + strings.Join(parts, ",") + "]"\n'
            "}\n"
        )

    def starter(self, entry: str, sig: Signature) -> str:
        return (
            f"func {entry}({self.params(sig)}) {self.type_name(sig.ret)} {{\n"
            "\t// Write your solution here.\n"
            f"\treturn {self.zero(sig.ret)}\n"
            "}\n"
        )

    def params(self, sig: Signature) -> str:
        return ", ".join(f"{p.name} {self.type_name(p.type)}" for p in sig.params)

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"{entry}({args})", sig.ret)
            rows.append(
                f"\t\tzzCase({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            _GO_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\nfunc zzCase(a string, e string) string {\n"
            '\tpassed := "false"\n'
            "\tif a == e {\n"
            '\t\tpassed = "true"\n'
            "\t}\n"
            '\treturn "{\\"passed\\":" + passed + ",\\"actual\\":" + a + ",\\"expected\\":" + e + "}"\n'
            "}\n\n"
            "func main() {\n"
            "\tzzR := []string{\n"
            + ",\n".join(rows)
            + ",\n\t}\n"
            + '\tfmt.Println("RESULTS_JSON:[" + strings.Join(zzR, ",") + "]")\n'
            + "}\n"
        )

    def standalone(self, user_code: str) -> str:
        return _GO_PRELUDE + "\n" + user_code.strip() + "\n\nfunc main() {}\n"


# ── Rust ──────────────────────────────────────────────────────────────────────

_RUST_PRELUDE = """#![allow(dead_code, unused_imports, unused_mut, unused_variables, non_snake_case)]
use std::cmp::{max, min, Ordering};
use std::collections::{BTreeMap, BTreeSet, BinaryHeap, HashMap, HashSet, VecDeque};
"""


class _Rust(_Renderer):
    key = "rust"
    style = "snake"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return f"Vec<{self.type_name(t.item)}>"  # type: ignore[arg-type]
        return {"int": "i32", "float": "f64", "bool": "bool", "str": "String"}[t.kind]

    def literal(self, value: Any, t: Type) -> str:
        if t.kind == "list":
            inner = ", ".join(self.literal(v, t.item) for v in value)  # type: ignore[arg-type]
            return f"vec![{inner}]"
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return f"String::from({_c_string(value)})"
        if t.kind == "float":
            return f"{float(value)!r}f64"
        return f"{int(value)}i32"

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "Vec::new()"
        return {
            "int": "0", "float": "0.0", "bool": "false", "str": "String::new()"
        }[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zz_q(&{expr})"
        return f"({expr}).to_string()"

    def quote_helper(self) -> str:
        return (
            "fn zz_q(s: &str) -> String {\n"
            '    let mut r = String::from("\\"");\n'
            "    for c in s.chars() {\n"
            "        match c {\n"
            "            '\"' | '\\\\' => { r.push('\\\\'); r.push(c); }\n"
            '            \'\\n\' => r.push_str("\\\\n"),\n'
            '            \'\\r\' => r.push_str("\\\\r"),\n'
            '            \'\\t\' => r.push_str("\\\\t"),\n'
            '            c if (c as u32) < 32 => r.push_str(&format!("\\\\u{:04x}", c as u32)),\n'
            "            c => r.push(c),\n"
            "        }\n"
            "    }\n"
            "    r.push('\"');\n"
            "    r\n"
            "}\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        item = self.json_expr("v.clone()", t.item)  # type: ignore[arg-type]
        return (
            f"fn {name}(a: &{self.type_name(t)}) -> String {{\n"
            f"    let parts: Vec<String> = a.iter().map(|v| {item}).collect();\n"
            '    format!("[{}]", parts.join(","))\n'
            "}\n"
        )

    def json_expr(self, expr: str, t: Type) -> str:
        if t.kind == "list":
            return f"{self.helper_name(t)}(&{expr})"
        return self.scalar_json(expr, t)

    def helper_name(self, t: Type) -> str:
        return "zz_j" + str(t).replace("list[", "_l").replace("]", "")

    def params(self, sig: Signature) -> str:
        return ", ".join(f"{p.name}: {self.type_name(p.type)}" for p in sig.params)

    def starter(self, entry: str, sig: Signature) -> str:
        return (
            f"fn {entry}({self.params(sig)}) -> {self.type_name(sig.ret)} {{\n"
            "    // Write your solution here.\n"
            f"    {self.zero(sig.ret)}\n"
            "}\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"{entry}({args})", sig.ret)
            rows.append(
                f"        zz_case({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            _RUST_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\nfn zz_case(a: String, e: &str) -> String {\n"
            '    format!("{{\\"passed\\":{},\\"actual\\":{},\\"expected\\":{}}}", a == e, a, e)\n'
            "}\n\n"
            "fn main() {\n"
            "    let zz_r: Vec<String> = vec![\n"
            + ",\n".join(rows)
            + ",\n    ];\n"
            + '    println!("RESULTS_JSON:[{}]", zz_r.join(","));\n'
            + "}\n"
        )

    def standalone(self, user_code: str) -> str:
        return _RUST_PRELUDE + "\n" + user_code.strip() + "\n\nfn main() {}\n"


# ── Swift ─────────────────────────────────────────────────────────────────────

_SWIFT_PRELUDE = "import Foundation\n"


class _Swift(_Renderer):
    key = "swift"
    style = "camel"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return f"[{self.type_name(t.item)}]"  # type: ignore[arg-type]
        return {"int": "Int", "float": "Double", "bool": "Bool", "str": "String"}[t.kind]

    def literal(self, value: Any, t: Type) -> str:
        if t.kind == "list":
            inner = ", ".join(self.literal(v, t.item) for v in value)  # type: ignore[arg-type]
            return f"[{inner}] as {self.type_name(t)}"
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "[]"
        return {"int": "0", "float": "0.0", "bool": "false", "str": '""'}[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zzQ({expr})"
        if t.kind == "bool":
            return f'(({expr}) ? "true" : "false")'
        return f"String({expr})"

    def quote_helper(self) -> str:
        return (
            "func zzQ(_ s: String) -> String {\n"
            '    var r = "\\""\n'
            "    for c in s.unicodeScalars {\n"
            '        if c == "\\"" || c == "\\\\" { r += "\\\\" + String(c) }\n'
            '        else if c == "\\n" { r += "\\\\n" }\n'
            '        else if c == "\\r" { r += "\\\\r" }\n'
            '        else if c == "\\t" { r += "\\\\t" }\n'
            '        else if c.value < 32 { r += String(format: "\\\\u%04x", c.value) }\n'
            "        else { r.unicodeScalars.append(c) }\n"
            "    }\n"
            '    return r + "\\""\n'
            "}\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        item = self.json_expr("v", t.item)  # type: ignore[arg-type]
        return (
            f"func {name}(_ a: {self.type_name(t)}) -> String {{\n"
            f"    return \"[\" + a.map {{ v in {item} }}.joined(separator: \",\") + \"]\"\n"
            "}\n"
        )

    def params(self, sig: Signature) -> str:
        return ", ".join(f"_ {p.name}: {self.type_name(p.type)}" for p in sig.params)

    def starter(self, entry: str, sig: Signature) -> str:
        return (
            f"func {entry}({self.params(sig)}) -> {self.type_name(sig.ret)} {{\n"
            "    // Write your solution here.\n"
            f"    return {self.zero(sig.ret)}\n"
            "}\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"{entry}({args})", sig.ret)
            rows.append(
                f"    zzCase({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            _SWIFT_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\nfunc zzCase(_ a: String, _ e: String) -> String {\n"
            '    return "{\\"passed\\":" + (a == e ? "true" : "false")\n'
            '        + ",\\"actual\\":" + a + ",\\"expected\\":" + e + "}"\n'
            "}\n\n"
            "let zzR: [String] = [\n"
            + ",\n".join(rows)
            + ",\n]\n"
            + 'print("RESULTS_JSON:[" + zzR.joined(separator: ",") + "]")\n'
        )

    def standalone(self, user_code: str) -> str:
        return _SWIFT_PRELUDE + "\n" + user_code.strip() + "\n"


# ── Haskell ───────────────────────────────────────────────────────────────────

_HASKELL_PRELUDE = """import Data.Char (ord)
import Data.List
import qualified Data.Map as Map
import qualified Data.Set as Set
import Text.Printf (printf)
"""


class _Haskell(_Renderer):
    key = "haskell"
    style = "camel"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return f"[{self.type_name(t.item)}]"  # type: ignore[arg-type]
        return {"int": "Int", "float": "Double", "bool": "Bool", "str": "String"}[t.kind]

    def literal(self, value: Any, t: Type) -> str:
        if t.kind == "list":
            return "[" + ", ".join(self.literal(v, t.item) for v in value) + "]"  # type: ignore[arg-type]
        if t.kind == "bool":
            return "True" if value else "False"
        if t.kind == "str":
            return _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        # Negatives must be parenthesised wherever they appear as an argument.
        return f"({value})" if value < 0 else str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "[]"
        return {"int": "0", "float": "0.0", "bool": "False", "str": '""'}[t.kind]

    def json_expr(self, expr: str, t: Type) -> str:
        """Haskell composes renderers instead of naming one helper per type."""
        return f"{self._render_fn(t)} ({expr})"

    def _render_fn(self, t: Type) -> str:
        if t.kind == "list":
            return f"(zzList ({self._render_fn(t.item)}))"  # type: ignore[arg-type]
        return {"int": "show", "float": "show", "bool": "zzBool", "str": "zzQ"}[t.kind]

    def helpers(self, ret: Type) -> str:
        parts = [
            "zzQ :: String -> String",
            'zzQ s = "\\"" ++ concatMap zzEsc s ++ "\\""',
            "",
            "zzEsc :: Char -> String",
            'zzEsc c',
            '  | c == \'"\' = "\\\\\\""',
            "  | c == '\\\\' = \"\\\\\\\\\"",
            '  | c == \'\\n\' = "\\\\n"',
            '  | c == \'\\r\' = "\\\\r"',
            '  | c == \'\\t\' = "\\\\t"',
            '  | ord c < 32 = printf "\\\\u%04x" (ord c)',
            "  | otherwise = [c]",
            "",
            "zzBool :: Bool -> String",
            'zzBool b = if b then "true" else "false"',
            "",
            "zzList :: (a -> String) -> [a] -> String",
            'zzList f xs = "[" ++ intercalate "," (map f xs) ++ "]"',
            "",
        ]
        return "\n".join(parts)

    def starter(self, entry: str, sig: Signature) -> str:
        arrow = " -> ".join(
            [self.type_name(p.type) for p in sig.params] + [self.type_name(sig.ret)]
        )
        names = " ".join(p.name for p in sig.params)
        return (
            f"{entry} :: {arrow}\n"
            f"{entry} {names} = {self.zero(sig.ret)}  -- Write your solution here.\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = " ".join(
                f"({self.literal(v, p.type)})"
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"{entry} {args}" if args else entry, sig.ret)
            rows.append(
                f"  zzCase ({actual}) {_c_string(_json_text(c['expected']))}"
            )
        return (
            _HASKELL_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\nzzCase :: String -> String -> String\n"
            'zzCase a e = "{\\"passed\\":" ++ (if a == e then "true" else "false")\n'
            '  ++ ",\\"actual\\":" ++ a ++ ",\\"expected\\":" ++ e ++ "}"\n'
            "\nmain :: IO ()\n"
            'main = putStrLn ("RESULTS_JSON:[" ++ intercalate "," zzR ++ "]")\n'
            "  where\n"
            "    zzR =\n"
            "      [\n"
            + ",\n".join("      " + r.strip() for r in rows)
            + "\n      ]\n"
        )

    def standalone(self, user_code: str) -> str:
        return (
            _HASKELL_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\nmain :: IO ()\nmain = return ()\n"
        )


# ── Erlang ────────────────────────────────────────────────────────────────────
#
# Erlang is dynamically typed, so no declarations are generated — but the harness
# still uses the inferred types to pick the right renderer for each value, since
# an Erlang string is indistinguishable from a list of integers at runtime.


class _Erlang(_Renderer):
    key = "erlang"
    style = "snake"

    def type_name(self, t: Type) -> str:  # unused; Erlang declares nothing
        return ""

    def literal(self, value: Any, t: Type) -> str:
        if t.kind == "list":
            return "[" + ", ".join(self.literal(v, t.item) for v in value) + "]"  # type: ignore[arg-type]
        if t.kind == "bool":
            return "true" if value else "false"
        if t.kind == "str":
            return _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "[]"
        return {"int": "0", "float": "0.0", "bool": "false", "str": '""'}[t.kind]

    def json_expr(self, expr: str, t: Type) -> str:
        return f"{self._render_fn(t)}({expr})"

    def _render_fn(self, t: Type, depth: int = 0) -> str:
        """A one-argument fun that renders a value of type ``t``.

        Spelled as an explicit ``fun(X) -> f(X) end`` rather than ``fun f/1``:
        ``escript`` interprets the module rather than compiling it, and a
        ``fun name/arity`` reference resolves against ``erl_eval`` there, which
        fails at run time with "undefined function erl_eval:zz_int/1".
        """
        var = f"Zz{depth}"
        if t.kind == "list":
            inner = self._render_fn(t.item, depth + 1)  # type: ignore[arg-type]
            return f"fun({var}) -> zz_list({inner}, {var}) end"
        name = {
            "int": "zz_int", "float": "zz_float", "bool": "zz_bool", "str": "zz_q"
        }[t.kind]
        return f"fun({var}) -> {name}({var}) end"

    def _apply(self, t: Type, expr: str) -> str:
        """Apply the renderer for ``t`` to ``expr`` at the top level."""
        if t.kind == "list":
            return f"zz_list({self._render_fn(t.item)}, {expr})"  # type: ignore[arg-type]
        return {
            "int": "zz_int", "float": "zz_float", "bool": "zz_bool", "str": "zz_q"
        }[t.kind] + f"({expr})"

    def helpers(self, ret: Type) -> str:
        return (
            "zz_int(N) -> integer_to_list(N).\n"
            "zz_float(F) -> lists:flatten(io_lib:format(\"~p\", [F])).\n"
            "zz_bool(true) -> \"true\";\n"
            "zz_bool(false) -> \"false\".\n"
            "zz_q(S) -> \"\\\"\" ++ lists:flatmap(fun(Zc) -> zz_esc(Zc) end, S) ++ \"\\\"\".\n"
            "zz_esc($\\\") -> \"\\\\\\\"\";\n"
            "zz_esc($\\\\) -> \"\\\\\\\\\";\n"
            "zz_esc($\\n) -> \"\\\\n\";\n"
            "zz_esc($\\r) -> \"\\\\r\";\n"
            "zz_esc($\\t) -> \"\\\\t\";\n"
            "zz_esc(C) when C < 32 -> lists:flatten(io_lib:format(\"\\\\u~4.16.0b\", [C]));\n"
            "zz_esc(C) -> [C].\n"
            "zz_list(F, L) -> \"[\" ++ lists:flatten(lists:join(\",\", lists:map(F, L))) ++ \"]\".\n"
            "zz_case(A, E) ->\n"
            "    P = case A =:= E of true -> \"true\"; false -> \"false\" end,\n"
            "    \"{\\\"passed\\\":\" ++ P ++ \",\\\"actual\\\":\" ++ A ++ \",\\\"expected\\\":\" ++ E ++ \"}\".\n"
        )

    def starter(self, entry: str, sig: Signature) -> str:
        names = ", ".join(p.name.capitalize() for p in sig.params)
        return (
            f"%% Erlang variables start with a capital letter.\n"
            f"{entry}({names}) ->\n"
            f"    {self.zero(sig.ret)}.  %% Write your solution here.\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self._apply(sig.ret, f"{entry}({args})")
            rows.append(
                f"        zz_case({actual}, {_c_string(_json_text(c['expected']))})"
            )
        return (
            "-module(main).\n"
            "-export([main/1]).\n\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\nmain(_) ->\n"
            "    ZzR = [\n"
            + ",\n".join(rows)
            + "\n    ],\n"
            + '    io:format("RESULTS_JSON:[~s]~n", [lists:flatten(lists:join(",", ZzR))]).\n'
        )

    def standalone(self, user_code: str) -> str:
        return (
            "-module(main).\n-export([main/1]).\n\n"
            + user_code.strip()
            + "\n\nmain(_) -> ok.\n"
        )


# ── Objective-C ───────────────────────────────────────────────────────────────
#
# Judge0's Objective-C toolchain predates object subscripting (``a[i]`` on an
# NSArray) and ``@autoreleasepool``, so everything below uses classic message
# syntax. That was found the hard way: the obvious spelling fails to compile
# there with "bad receiver type 'NSArray'".

_OBJC_PRELUDE = "#import <Foundation/Foundation.h>\n"


class _ObjectiveC(_Renderer):
    key = "objectivec"
    style = "camel"

    def type_name(self, t: Type) -> str:
        if t.kind == "list":
            return "NSArray *"
        return {"int": "int", "float": "double", "bool": "BOOL", "str": "NSString *"}[t.kind]

    def literal(self, value: Any, t: Type) -> str:
        if t.kind == "list":
            if not value:
                return "[NSArray array]"
            items = ", ".join(self._boxed(v, t.item) for v in value)  # type: ignore[arg-type]
            return f"[NSArray arrayWithObjects:{items}, nil]"
        if t.kind == "bool":
            return "YES" if value else "NO"
        if t.kind == "str":
            return "@" + _c_string(value)
        if t.kind == "float":
            return repr(float(value))
        return str(int(value))

    def _boxed(self, value: Any, t: Type) -> str:
        """NSArray holds objects, so scalars are boxed as NSNumber."""
        if t.kind == "list" or t.kind == "str":
            return self.literal(value, t)
        if t.kind == "bool":
            return f"[NSNumber numberWithBool:{'YES' if value else 'NO'}]"
        if t.kind == "float":
            return f"[NSNumber numberWithDouble:{float(value)!r}]"
        return f"[NSNumber numberWithInt:{int(value)}]"

    def zero(self, t: Type) -> str:
        if t.kind == "list":
            return "[NSArray array]"
        return {"int": "0", "float": "0.0", "bool": "NO", "str": '@""'}[t.kind]

    def scalar_json(self, expr: str, t: Type) -> str:
        if t.kind == "str":
            return f"zzQ({expr})"
        if t.kind == "bool":
            return f'(({expr}) ? @"true" : @"false")'
        if t.kind == "float":
            return f'[NSString stringWithFormat:@"%g", (double)({expr})]'
        return f'[NSString stringWithFormat:@"%d", (int)({expr})]'

    def _element_json(self, t: Type) -> str:
        """Render one boxed element of an NSArray, given its static type."""
        if t.kind == "list":
            return f"{self.helper_name(t)}((NSArray *)zzE)"
        if t.kind == "str":
            return "zzQ((NSString *)zzE)"
        if t.kind == "bool":
            return '([zzE boolValue] ? @"true" : @"false")'
        if t.kind == "float":
            return '[NSString stringWithFormat:@"%g", [zzE doubleValue]]'
        return "[zzE stringValue]"

    def quote_helper(self) -> str:
        return (
            "static NSString *zzQ(NSString *s) {\n"
            '    NSMutableString *r = [NSMutableString stringWithString:@"\\""];\n'
            "    NSUInteger n = [s length];\n"
            "    for (NSUInteger i = 0; i < n; i++) {\n"
            "        unichar c = [s characterAtIndex:i];\n"
            "        if (c == '\"' || c == '\\\\')\n"
            '            [r appendFormat:@"\\\\%C", c];\n'
            '        else if (c == \'\\n\') [r appendString:@"\\\\n"];\n'
            '        else if (c == \'\\r\') [r appendString:@"\\\\r"];\n'
            '        else if (c == \'\\t\') [r appendString:@"\\\\t"];\n'
            '        else if (c < 32) [r appendFormat:@"\\\\u%04x", (unsigned) c];\n'
            '        else [r appendFormat:@"%C", c];\n'
            "    }\n"
            '    [r appendString:@"\\""];\n'
            "    return r;\n"
            "}\n"
        )

    def list_helper(self, name: str, t: Type) -> str:
        return (
            f"static NSString *{name}(NSArray *a) {{\n"
            "    NSMutableArray *parts = [NSMutableArray array];\n"
            "    NSUInteger n = [a count];\n"
            "    for (NSUInteger i = 0; i < n; i++) {\n"
            "        id zzE = [a objectAtIndex:i];\n"
            f"        [parts addObject:{self._element_json(t.item)}];\n"  # type: ignore[arg-type]
            "    }\n"
            '    return [NSString stringWithFormat:@"[%@]",\n'
            '        [parts componentsJoinedByString:@","]];\n'
            "}\n"
        )

    def params(self, sig: Signature) -> str:
        return ", ".join(
            f"{self.type_name(p.type)}{'' if self.type_name(p.type).endswith('*') else ' '}{p.name}"
            for p in sig.params
        )

    def starter(self, entry: str, sig: Signature) -> str:
        ret = self.type_name(sig.ret)
        space = "" if ret.endswith("*") else " "
        return (
            f"{ret}{space}{entry}({self.params(sig)}) {{\n"
            "    // Write your solution here.\n"
            f"    return {self.zero(sig.ret)};\n"
            "}\n"
        )

    def program(self, entry, sig, cases, user_code):
        rows = []
        for c in cases:
            args = ", ".join(
                self.literal(v, p.type)
                for v, p in zip(_case_values(c, sig), sig.params)
            )
            actual = self.json_expr(f"{entry}({args})", sig.ret)
            expected = "@" + _c_string(_json_text(c["expected"]))
            rows.append(f"        zzCase({actual}, {expected})")
        return (
            _OBJC_PRELUDE
            + "\n"
            + user_code.strip()
            + "\n\n"
            + self.helpers(sig.ret)
            + "\nstatic NSString *zzCase(NSString *a, NSString *e) {\n"
            '    return [NSString stringWithFormat:@"{\\"passed\\":%@,\\"actual\\":%@,\\"expected\\":%@}",\n'
            '        [a isEqualToString:e] ? @"true" : @"false", a, e];\n'
            "}\n\n"
            "int main(void) {\n"
            "    NSAutoreleasePool *zzPool = [[NSAutoreleasePool alloc] init];\n"
            "    NSArray *zzR = [NSArray arrayWithObjects:\n"
            + ",\n".join(rows)
            + ", nil];\n"
            + '    printf("RESULTS_JSON:[%s]\\n",\n'
            + '        [[zzR componentsJoinedByString:@","] UTF8String]);\n'
            + "    [zzPool release];\n"
            + "    return 0;\n}\n"
        )

    def standalone(self, user_code: str) -> str:
        return _OBJC_PRELUDE + "\n" + user_code.strip() + "\n\nint main(void) { return 0; }\n"


RENDERERS: Dict[str, _Renderer] = {
    r.key: r
    for r in (
        _Java(), _Cpp(), _CSharp(), _Go(), _Rust(),
        _Swift(), _Haskell(), _Erlang(), _ObjectiveC(),
    )
}


# ── Dynamic-language starters ─────────────────────────────────────────────────
#
# These five languages need no harness — their graders in ``code_runners`` find
# the function by name at runtime and bind JSON directly. They still need a
# *starter*, because the name the grader looks for has to be the name the
# candidate was given. Without one they fall back to a generic ``two_sum`` stub,
# which no longer matches once the problem comes from the bank.

_DYNAMIC_STYLES = {
    "python": "snake",
    "javascript": "camel",
    "typescript": "camel",
    "ruby": "snake",
    "php": "camel",
}


def _ts_type(t: Type) -> str:
    if t.kind == "list":
        return f"{_ts_type(t.item) if t.item else 'unknown'}[]"
    return {"int": "number", "float": "number", "str": "string", "bool": "boolean"}[t.kind]


def _py_type(t: Type) -> str:
    if t.kind == "list":
        return f"list[{_py_type(t.item) if t.item else 'object'}]"
    return t.kind


def _dynamic_starter(language: str, entry: str, signature: Signature) -> Optional[str]:
    """A stub in a dynamically typed language, matching what the grader calls."""
    names = [p.name for p in signature.params]

    if language == "python":
        params = ", ".join(f"{p.name}: {_py_type(p.type)}" for p in signature.params)
        return (
            f"def {entry}({params}) -> {_py_type(signature.ret)}:\n"
            "    # Write your solution here\n"
            "    pass\n"
        )
    if language == "javascript":
        return (
            f"function {entry}({', '.join(names)}) {{\n"
            "    // Write your solution here\n"
            "}\n"
        )
    if language == "typescript":
        params = ", ".join(f"{p.name}: {_ts_type(p.type)}" for p in signature.params)
        return (
            f"function {entry}({params}): {_ts_type(signature.ret)} {{\n"
            "    // Write your solution here\n"
            "}\n"
        )
    if language == "ruby":
        return (
            f"def {entry}({', '.join(names)})\n"
            "    # Write your solution here\n"
            "end\n"
        )
    if language == "php":
        params = ", ".join(f"${n}" for n in names)
        return (
            "<?php\n"
            f"function {entry}({params}) {{\n"
            "    // Write your solution here\n"
            "}\n"
        )
    return None


# ── Public API ────────────────────────────────────────────────────────────────


def starter_languages() -> List[str]:
    """Every language ``build_starter`` can generate a stub for."""
    return list(RENDERERS) + list(_DYNAMIC_STYLES)


def supports(language: str) -> bool:
    """True when this language has a static harness renderer."""
    return language in RENDERERS


def build_program(
    language: str,
    test_cases: Sequence[Dict[str, Any]],
    entry_candidates: Sequence[str],
    user_code: str,
) -> Optional[str]:
    """A complete, gradeable program, or None if the problem cannot be typed."""
    renderer = RENDERERS.get(language)
    if renderer is None or not user_code.strip():
        return None
    signature = infer_signature(test_cases)
    if signature is None:
        return None
    entry = entry_name(entry_candidates, renderer.style)
    return renderer.program(entry, signature, list(test_cases), user_code)


def build_starter(
    language: str,
    test_cases: Sequence[Dict[str, Any]],
    entry_candidates: Sequence[str],
    param_names: Optional[Sequence[str]] = None,
) -> Optional[str]:
    """Starter code whose signature matches what the grader calls.

    Covers the nine statically typed languages via their renderers and the five
    dynamically typed ones directly — in both cases the entry-point name comes
    from :func:`entry_name`, so the stub the candidate is shown is the one the
    grader looks up.

    `param_names` renames the parameters for readability only. Every harness
    passes arguments positionally, so the names are cosmetic; a wrong-length
    list is ignored rather than applied partially.
    """
    signature = infer_signature(test_cases)
    if signature is None:
        return None

    if param_names and len(param_names) == len(signature.params):
        signature = Signature(
            params=tuple(
                Param(_safe_name(new), old.type)
                for new, old in zip(param_names, signature.params)
            ),
            ret=signature.ret,
        )

    style = _DYNAMIC_STYLES.get(language)
    if style is not None:
        return _dynamic_starter(
            language, entry_name(entry_candidates, style), signature
        )

    renderer = RENDERERS.get(language)
    if renderer is None:
        return None
    return renderer.starter(entry_name(entry_candidates, renderer.style), signature)


def wrap_standalone(language: str, user_code: str) -> str:
    """Make a function-only submission compilable on the ungraded path.

    Without this a Go submission has no ``package`` clause and a Rust one no
    ``main``, so the compile-only fallback would report an error about the
    harness's own conventions rather than about the candidate's code.
    """
    renderer = RENDERERS.get(language)
    return renderer.standalone(user_code) if renderer else user_code


def name_java_entry_class(source: str) -> str:
    """Rename a whole-program Java submission's entry class to ``Main``.

    Java ties a public class to its filename, and every backend writes the
    submission to ``Main.java`` — so ``public class Solution`` fails to compile.
    The function harnesses solve that by *demoting* the candidate's class, which
    works only because the harness itself supplies ``public class Main`` for
    ``java -cp /build Main`` to find. A whole-program submission has no such
    companion: demoting it would compile ``Solution.class`` and then fail to
    launch. So it is renamed instead — the same adaptation Judge0 already makes,
    and semantically inert for a single self-contained file.

    The class renamed is the one declaring ``main``, not the first one declared:
    a competitive submission often puts a helper or data class above its entry
    point, and renaming that would compile cleanly and then fail to launch for a
    reason nothing in the output would explain. A source that already declares
    ``Main`` is left exactly as written.
    """
    if re.search(r"\bclass\s+Main\b", source):
        return source
    entry = re.search(r"\bstatic\s+(?:public\s+)?void\s+main\s*\(", source)
    declarations = list(
        re.finditer(r"\b(?:public\s+)?(?:final\s+|abstract\s+)?class\s+(\w+)", source)
    )
    if not declarations:
        return source
    if entry is None:
        owner = declarations[0]
    else:
        before = [d for d in declarations if d.start() < entry.start()]
        owner = before[-1] if before else declarations[0]
    return re.sub(rf"\b{re.escape(owner.group(1))}\b", "Main", source)
