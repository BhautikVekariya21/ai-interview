"""
Coding practice service helpers.

This module backs the Coding Practice API with:
- problem listing/detail access from the local curated dataset
- language-specific starter templates
- code execution through Judge0 CE with local Python/Node fallback
- lightweight AI/heuristic code review
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from app.core.config import settings
from app.services.coding_problems_data import PROBLEMS


@dataclass(frozen=True)
class TypeDesc:
    kind: str
    item: Optional["TypeDesc"] = None


SUPPORTED_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "python": {
        "label": "Python",
        "judge0_language_id": 71,
        "extension": ".py",
        "supports_local": True,
    },
    "javascript": {
        "label": "JavaScript",
        "judge0_language_id": 63,
        "extension": ".js",
        "supports_local": True,
    },
    "java": {
        "label": "Java",
        "judge0_language_id": 62,
        "extension": ".java",
        "supports_local": True,
    },
    "cpp": {
        "label": "C++",
        "judge0_language_id": 54,
        "extension": ".cpp",
        "supports_local": True,
    },
    "c": {
        "label": "C",
        "judge0_language_id": 50,
        "extension": ".c",
        "supports_local": True,
    },
    "rust": {
        "label": "Rust",
        "judge0_language_id": 73,
        "extension": ".rs",
        "supports_local": True,
    },
}

TOPICS: List[str] = list(dict.fromkeys(problem["topic"] for problem in PROBLEMS))
PROBLEMS_BY_ID: Dict[int, Dict[str, Any]] = {problem["id"]: problem for problem in PROBLEMS}


def _canonical_language(language: str) -> str:
    normalized = (language or "").strip().lower()
    aliases = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "node": "javascript",
        "nodejs": "javascript",
        "cpp": "cpp",
        "c++": "cpp",
    }
    return aliases.get(normalized, normalized)


def _problem_summary(problem: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": problem["id"],
        "title": problem["title"],
        "difficulty": problem["difficulty"],
        "topic": problem["topic"],
        "tags": list(problem["tags"]),
        "companiesAsked": list(problem["companiesAsked"]),
        "timeComplexity": problem["timeComplexity"],
        "spaceComplexity": problem["spaceComplexity"],
    }


def get_all_problems(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = PROBLEMS
    if topic:
        items = [problem for problem in items if problem["topic"] == topic]
    if difficulty:
        items = [problem for problem in items if problem["difficulty"] == difficulty]
    if search:
        needle = search.strip().lower()
        items = [
            problem
            for problem in items
            if needle in problem["title"].lower()
            or needle in problem["topic"].lower()
            or any(needle in tag.lower() for tag in problem["tags"])
        ]
    return [_problem_summary(problem) for problem in items]


def get_problem(problem_id: int) -> Optional[Dict[str, Any]]:
    problem = PROBLEMS_BY_ID.get(problem_id)
    if not problem:
        return None

    detail = copy.deepcopy(problem)
    detail["starterTemplates"] = build_starter_templates(problem)
    detail["solutionsByLanguage"] = build_solution_templates(problem)
    detail["supportedLanguages"] = list(SUPPORTED_LANGUAGES.keys())
    detail["solutionLanguage"] = "javascript"
    detail["executionContract"] = (
        "Implement solve(...) in the selected language and print the final answer "
        "as JSON-compatible output. Hidden tests will call solve(...) for each case."
    )
    return detail


def _detect_local_compilers() -> Dict[str, bool]:
    """Check which language compilers/interpreters are available locally."""
    return {
        "python": True,  # Always available (we're running Python)
        "javascript": shutil.which("node") is not None,
        "java": shutil.which("javac") is not None and shutil.which("java") is not None,
        "cpp": shutil.which("g++") is not None,
        "c": shutil.which("gcc") is not None,
        "rust": shutil.which("rustc") is not None,
    }


def get_supported_languages() -> List[Dict[str, Any]]:
    judge0_available = bool(settings.JUDGE0_ENABLED and settings.JUDGE0_BASE_URL)
    local_available = _detect_local_compilers()

    rows: List[Dict[str, Any]] = []
    for lang_id, config in SUPPORTED_LANGUAGES.items():
        providers: List[str] = []
        if judge0_available:
            providers.append("judge0")
        if config["supports_local"] and settings.CODE_EXECUTION_LOCAL_FALLBACK:
            if local_available.get(lang_id, False):
                providers.append("local")
        rows.append(
            {
                "id": lang_id,
                "label": config["label"],
                "enabled": bool(providers),
                "providers": providers,
            }
        )
    return rows


def _extract_function_signature(problem: Dict[str, Any]) -> tuple[list[str], bool]:
    starter = str(problem.get("starterCode", ""))
    solution = str(problem.get("solutionCode", ""))

    if "class " in starter or "class " in solution:
        return ["operations", "parameters"], True

    for source in (solution, starter):
        solution_match = re.search(r"function\s+solution\s*\(([^)]*)\)", source)
        if solution_match:
            params = [p.strip() for p in solution_match.group(1).split(",") if p.strip()]
            return params, False

        fn_match = re.search(r"function\s+\w+\s*\(([^)]*)\)", source)
        if fn_match:
            params = [p.strip() for p in fn_match.group(1).split(",") if p.strip()]
            if params:
                return params, False

    first_case = json.loads(problem["testCases"][0]["input"])
    return [f"arg{i + 1}" for i in range(len(first_case))], False


def _infer_type(value: Any) -> TypeDesc:
    if value is None:
        return TypeDesc("null")
    if isinstance(value, bool):
        return TypeDesc("bool")
    if isinstance(value, int) and not isinstance(value, bool):
        return TypeDesc("int")
    if isinstance(value, float):
        return TypeDesc("float")
    if isinstance(value, str):
        return TypeDesc("string")
    if isinstance(value, list):
        item_type = TypeDesc("any")
        for item in value:
            item_type = _merge_types(item_type, _infer_type(item))
        return TypeDesc("array", item_type)
    return TypeDesc("any")


def _merge_types(left: TypeDesc, right: TypeDesc) -> TypeDesc:
    if left.kind == "any":
        return right
    if right.kind == "any":
        return left
    if left == right:
        return left
    if left.kind == "null":
        return TypeDesc("nullable", right)
    if right.kind == "null":
        return TypeDesc("nullable", left)
    if left.kind == "nullable":
        return TypeDesc("nullable", _merge_types(left.item or TypeDesc("any"), right))
    if right.kind == "nullable":
        return TypeDesc("nullable", _merge_types(left, right.item or TypeDesc("any")))
    if {left.kind, right.kind} == {"int", "float"}:
        return TypeDesc("float")
    if left.kind == "array" and right.kind == "array":
        return TypeDesc("array", _merge_types(left.item or TypeDesc("any"), right.item or TypeDesc("any")))
    return TypeDesc("any")


def _infer_argument_types(problem: Dict[str, Any]) -> List[TypeDesc]:
    cases = [json.loads(test_case["input"]) for test_case in problem["testCases"]]
    if not cases:
        return []

    arity = len(cases[0])
    arg_types = [TypeDesc("any") for _ in range(arity)]
    for case in cases:
        for index, value in enumerate(case):
            arg_types[index] = _merge_types(arg_types[index], _infer_type(value))
    return arg_types


def _java_type(type_desc: TypeDesc) -> str:
    if type_desc.kind == "nullable":
        inner = _java_type(type_desc.item or TypeDesc("any"))
        return {
            "long": "Long",
            "double": "Double",
            "boolean": "Boolean",
            "String": "String",
        }.get(inner, inner)
    if type_desc.kind == "int":
        return "long"
    if type_desc.kind == "float":
        return "double"
    if type_desc.kind == "bool":
        return "boolean"
    if type_desc.kind == "string":
        return "String"
    if type_desc.kind == "array":
        return f"{_java_type(type_desc.item or TypeDesc('any'))}[]"
    return "Object"


def _cpp_type(type_desc: TypeDesc) -> str:
    if type_desc.kind == "nullable":
        return f"std::optional<{_cpp_type(type_desc.item or TypeDesc('any'))}>"
    if type_desc.kind == "int":
        return "long long"
    if type_desc.kind == "float":
        return "double"
    if type_desc.kind == "bool":
        return "bool"
    if type_desc.kind == "string":
        return "std::string"
    if type_desc.kind == "array":
        return f"std::vector<{_cpp_type(type_desc.item or TypeDesc('any'))}>"
    return "std::string"


def _rust_type(type_desc: TypeDesc) -> str:
    if type_desc.kind == "nullable":
        return f"Option<{_rust_type(type_desc.item or TypeDesc('any'))}>"
    if type_desc.kind == "int":
        return "i64"
    if type_desc.kind == "float":
        return "f64"
    if type_desc.kind == "bool":
        return "bool"
    if type_desc.kind == "string":
        return "String"
    if type_desc.kind == "array":
        return f"Vec<{_rust_type(type_desc.item or TypeDesc('any'))}>"
    return "String"


def _python_literal(value: Any) -> str:
    return repr(value)


def _javascript_literal(value: Any) -> str:
    return json.dumps(value)


def _java_literal(value: Any, type_desc: TypeDesc) -> str:
    if value is None:
        return "null"
    if type_desc.kind == "nullable":
        return _java_literal(value, type_desc.item or TypeDesc("any"))
    if type_desc.kind == "int":
        return f"{int(value)}L"
    if type_desc.kind == "float":
        return repr(float(value))
    if type_desc.kind == "bool":
        return "true" if value else "false"
    if type_desc.kind == "string":
        return json.dumps(value)
    if type_desc.kind == "array":
        inner = type_desc.item or TypeDesc("any")
        values = ", ".join(_java_literal(item, inner) for item in value)
        return f"new {_java_type(inner)}[]{{{values}}}"
    return json.dumps(value)


def _cpp_literal(value: Any, type_desc: TypeDesc) -> str:
    if value is None:
        return "std::nullopt"
    if type_desc.kind == "nullable":
        return _cpp_literal(value, type_desc.item or TypeDesc("any"))
    if type_desc.kind == "int":
        return f"{int(value)}LL"
    if type_desc.kind == "float":
        return repr(float(value))
    if type_desc.kind == "bool":
        return "true" if value else "false"
    if type_desc.kind == "string":
        return json.dumps(value)
    if type_desc.kind == "array":
        inner = type_desc.item or TypeDesc("any")
        values = ", ".join(_cpp_literal(item, inner) for item in value)
        return f"{_cpp_type(type_desc)}{{{values}}}"
    return json.dumps(value)


def _rust_literal(value: Any, type_desc: TypeDesc) -> str:
    if value is None:
        return "None"
    if type_desc.kind == "nullable":
        inner = type_desc.item or TypeDesc("any")
        return f"Some({_rust_literal(value, inner)})"
    if type_desc.kind == "int":
        return f"{int(value)}_i64"
    if type_desc.kind == "float":
        return f"{float(value)}_f64"
    if type_desc.kind == "bool":
        return "true" if value else "false"
    if type_desc.kind == "string":
        return f"String::from({json.dumps(value)})"
    if type_desc.kind == "array":
        inner = type_desc.item or TypeDesc("any")
        values = ", ".join(_rust_literal(item, inner) for item in value)
        return f"vec![{values}]"
    return f"String::from({json.dumps(json.dumps(value))})"


def build_starter_templates(problem: Dict[str, Any]) -> Dict[str, str]:
    arg_names, is_design_problem = _extract_function_signature(problem)
    arg_types = _infer_argument_types(problem)
    zipped = list(zip(arg_names, arg_types))
    joined_names = ", ".join(arg_names)

    if is_design_problem:
        extra_note = (
            "Design problem: simulate the operations and print a JSON array of outputs "
            "(use null where the operation returns nothing)."
        )
    else:
        extra_note = "Print the final answer once as JSON-compatible output."

    python_args = ", ".join(arg_names)
    javascript_args = ", ".join(arg_names)
    java_args = ", ".join(f"{_java_type(type_desc)} {name}" for name, type_desc in zipped)
    cpp_args = ", ".join(f"{_cpp_type(type_desc)} {name}" for name, type_desc in zipped)
    rust_args = ", ".join(f"{name}: {_rust_type(type_desc)}" for name, type_desc in zipped)

    return {
        "python": textwrap.dedent(
            f"""\
            import json

            def solve({python_args}):
                # {extra_note}
                # You may either return the result or print json.dumps(result).
                pass
            """
        ).rstrip(),
        "javascript": textwrap.dedent(
            f"""\
            function solve({javascript_args}) {{
              // {extra_note}
              // You may either return the result or console.log(JSON.stringify(result)).
            }}
            """
        ).rstrip(),
        "java": textwrap.dedent(
            f"""\
            public static void solve({java_args}) {{
                // {extra_note}
                // Example: System.out.print("[0,1]");
            }}
            """
        ).rstrip(),
        "cpp": textwrap.dedent(
            f"""\
            void solve({cpp_args}) {{
                // {extra_note}
                // Example: std::cout << "[0,1]";
            }}
            """
        ).rstrip(),
        "c": textwrap.dedent(
            """\
            void solve(const char *input_json) {
                /* Parse input_json and print JSON-compatible output.
                   Example: printf("[0,1]"); */
            }
            """
        ).rstrip(),
        "rust": textwrap.dedent(
            f"""\
            fn solve({rust_args}) {{
                // {extra_note}
                // Example: println!("[0,1]");
            }}
            """
        ).rstrip(),
    }


def _transpile_js_to_python(js_code: str) -> str:
    """Best-effort conversion of a JS solution to Python."""
    lines = js_code.split("\n")
    result: List[str] = []
    indent_stack: List[int] = [0]
    i = 0

    def current_indent() -> str:
        return "    " * indent_stack[-1]

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        i += 1

        # Skip empty lines
        if not stripped:
            result.append("")
            continue

        # Skip pure closing braces (we handle indent via stack)
        if stripped == "}" or stripped == "};":
            if len(indent_stack) > 1:
                indent_stack.pop()
            continue

        # Handle '} else if' / '} else' on same line
        if stripped.startswith("} else if") or stripped.startswith("}else if"):
            if len(indent_stack) > 1:
                indent_stack.pop()
            cond = re.search(r"else\s+if\s*\((.+)\)\s*\{?", stripped)
            cond_text = _js_expr_to_py(cond.group(1)) if cond else "True"
            result.append(f"{current_indent()}elif {cond_text}:")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        if stripped.startswith("} else") or stripped.startswith("}else"):
            if len(indent_stack) > 1:
                indent_stack.pop()
            result.append(f"{current_indent()}else:")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        # Function declaration
        fn_match = re.match(r"function\s+(\w+)\s*\(([^)]*)\)\s*\{?", stripped)
        if fn_match:
            name = fn_match.group(1)
            args = fn_match.group(2).strip()
            result.append(f"{current_indent()}def {name}({args}):")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        # Class declaration
        cls_match = re.match(r"class\s+(\w+)\s*\{?", stripped)
        if cls_match:
            result.append(f"{current_indent()}class {cls_match.group(1)}:")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        # Constructor
        if stripped.startswith("constructor") and "{" in stripped:
            ctor_match = re.match(r"constructor\s*\(([^)]*)\)\s*\{?", stripped)
            args = ctor_match.group(1).strip() if ctor_match else ""
            self_args = f"self, {args}" if args else "self"
            result.append(f"{current_indent()}def __init__({self_args}):")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        # Method declaration
        method_match = re.match(r"(\w+)\s*\(([^)]*)\)\s*\{?", stripped)
        if method_match and not any(
            stripped.startswith(kw)
            for kw in ("if", "else", "while", "for", "switch", "return", "const", "let", "var")
        ):
            name = method_match.group(1)
            args = method_match.group(2).strip()
            self_args = f"self, {args}" if args else "self"
            result.append(f"{current_indent()}def {name}({self_args}):")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        # For loop: for (let i = 0; i < n; i++)
        for_match = re.match(
            r"for\s*\((?:let|var|const)\s+(\w+)\s*=\s*(\d+);\s*\1\s*<\s*(.+?);\s*\1\+\+\)\s*\{?",
            stripped,
        )
        if for_match:
            var = for_match.group(1)
            start = for_match.group(2)
            end = _js_expr_to_py(for_match.group(3))
            range_expr = f"range({end})" if start == "0" else f"range({start}, {end})"
            result.append(f"{current_indent()}for {var} in {range_expr}:")
            if "{" in stripped:
                indent_stack.append(indent_stack[-1] + 1)
            continue

        # For loop: decrementing for (let i = n-1; i >= 0; i--)
        for_dec_match = re.match(
            r"for\s*\((?:let|var|const)\s+(\w+)\s*=\s*(.+?);\s*\1\s*>=\s*(\d+);\s*\1--\)\s*\{?",
            stripped,
        )
        if for_dec_match:
            var = for_dec_match.group(1)
            start = _js_expr_to_py(for_dec_match.group(2))
            end = for_dec_match.group(3)
            end_val = f"{int(end) - 1}" if end.isdigit() else f"{end}-1"
            result.append(f"{current_indent()}for {var} in range({start}, {end_val}, -1):")
            if "{" in stripped:
                indent_stack.append(indent_stack[-1] + 1)
            continue

        # For-of loop: for (const x of arr)
        forof_match = re.match(
            r"for\s*\((?:const|let|var)\s+(.+?)\s+of\s+(.+?)\)\s*\{?", stripped
        )
        if forof_match:
            var = forof_match.group(1)
            arr = _js_expr_to_py(forof_match.group(2))
            result.append(f"{current_indent()}for {var} in {arr}:")
            if "{" in stripped:
                indent_stack.append(indent_stack[-1] + 1)
            continue

        # While loop
        while_match = re.match(r"while\s*\((.+?)\)\s*\{?", stripped)
        if while_match:
            cond = _js_expr_to_py(while_match.group(1))
            result.append(f"{current_indent()}while {cond}:")
            if "{" in stripped:
                indent_stack.append(indent_stack[-1] + 1)
            continue

        # If statement
        if_match = re.match(r"if\s*\((.+?)\)\s*\{?", stripped)
        if if_match and not stripped.startswith("if (") is False:
            cond = _js_expr_to_py(if_match.group(1))
            # Check for single-line if: if (cond) return x;
            rest = stripped[if_match.end():].strip().rstrip("{")
            if rest and not rest.startswith("//"):
                body = _js_line_to_py(rest)
                result.append(f"{current_indent()}if {cond}: {body}")
            else:
                result.append(f"{current_indent()}if {cond}:")
                if "{" in stripped:
                    indent_stack.append(indent_stack[-1] + 1)
            continue

        # Else
        if stripped == "else {" or stripped == "else{":
            result.append(f"{current_indent()}else:")
            indent_stack.append(indent_stack[-1] + 1)
            continue

        # Regular statement
        py_line = _js_line_to_py(stripped)
        result.append(f"{current_indent()}{py_line}")

    # Ensure non-empty
    text = "\n".join(result).strip()
    return text if text else "# Solution conversion not available"


def _js_expr_to_py(expr: str) -> str:
    """Convert a JS expression to Python."""
    e = expr.strip().rstrip(";")

    # Boolean / null
    e = re.sub(r"\btrue\b", "True", e)
    e = re.sub(r"\bfalse\b", "False", e)
    e = re.sub(r"\bnull\b", "None", e)
    e = re.sub(r"\bundefined\b", "None", e)

    # Strict equality
    e = e.replace("===", "==").replace("!==", "!=")

    # Logical operators
    e = re.sub(r"\s&&\s", " and ", e)
    e = re.sub(r"\s\|\|\s", " or ", e)
    e = re.sub(r"(?<!\w)!(?!=)", "not ", e)

    # Math functions
    e = re.sub(r"Math\.max\(", "max(", e)
    e = re.sub(r"Math\.min\(", "min(", e)
    e = re.sub(r"Math\.abs\(", "abs(", e)
    e = re.sub(r"Math\.floor\(", "int(", e)
    e = re.sub(r"Math\.ceil\((.+?)\)", r"(-(-\1 // 1))", e)
    e = re.sub(r"Math\.pow\((.+?),\s*(.+?)\)", r"(\1 ** \2)", e)
    e = re.sub(r"Math\.trunc\(", "int(", e)
    e = re.sub(r"Math\.sqrt\(", "math.sqrt(", e)
    e = re.sub(r"Math\.log\(", "math.log(", e)
    e = re.sub(r"\bInfinity\b", "float('inf')", e)
    e = re.sub(r"-Infinity\b", "float('-inf')", e)

    # String/array length
    e = re.sub(r"(\w+)\.length", r"len(\1)", e)

    # parseInt / Number
    e = re.sub(r"parseInt\((.+?)\)", r"int(\1)", e)
    e = re.sub(r"Number\((.+?)\)", r"int(\1)", e)

    # String methods
    e = re.sub(r"\.charAt\((.+?)\)", r"[\1]", e)
    e = re.sub(r"\.charCodeAt\((.+?)\)-97", r") - ord('a')", e)  # approx
    e = re.sub(r"\.substring\((.+?),\s*(.+?)\)", r"[\1:\2]", e)
    e = re.sub(r"\.slice\((.+?)\)", r"[\1:]", e)
    e = re.sub(r"\.toLowerCase\(\)", r".lower()", e)
    e = re.sub(r"\.toUpperCase\(\)", r".upper()", e)
    e = re.sub(r"\.includes\((.+?)\)", r".__contains__(\1)", e)  # simplified
    e = re.sub(r"\.indexOf\((.+?)\)", r".index(\1) if \1 in ", e)  # approx
    e = re.sub(r"\.split\((.+?)\)", r".split(\1)", e)
    e = re.sub(r"\.join\((.+?)\)", r".join(\1)", e)
    e = re.sub(r"\.trim\(\)", r".strip()", e)

    # Array methods
    e = re.sub(r"\.push\((.+?)\)", r".append(\1)", e)
    e = re.sub(r"\.pop\(\)", r".pop()", e)
    e = re.sub(r"\.shift\(\)", r".pop(0)", e)
    e = re.sub(r"\.unshift\((.+?)\)", r".insert(0, \1)", e)
    e = re.sub(r"\.reverse\(\)", r".reverse()", e)

    # new Set / new Map
    e = re.sub(r"new Set\(([^)]*)\)", lambda m: f"set({m.group(1)})" if m.group(1) else "set()", e)
    e = re.sub(r"new Map\(([^)]*)\)", lambda m: f"dict({m.group(1)})" if m.group(1) else "{}", e)
    e = re.sub(r"new Map\(\[\[(.+?)\]\]\)", r"{\1}", e)

    # Map/Set methods
    e = re.sub(r"(\w+)\.has\((.+?)\)", r"\2 in \1", e)
    e = re.sub(r"(\w+)\.set\((.+?),\s*(.+?)\)", r"\1[\2] = \3", e)
    e = re.sub(r"(\w+)\.get\((.+?)\)", r"\1.get(\2)", e)
    e = re.sub(r"(\w+)\.add\((.+?)\)", r"\1.add(\2)", e)
    e = re.sub(r"(\w+)\.delete\((.+?)\)", r"\1.discard(\2)", e)
    e = re.sub(r"(\w+)\.size", r"len(\1)", e)

    # Array.from
    e = re.sub(r"Array\.from\((.+?)\)", r"list(\1)", e)
    e = re.sub(r"Array\((\w+)\)\.fill\((.+?)\)", r"[\2] * \1", e)
    e = re.sub(r"Object\.keys\((.+?)\)", r"list(\1.keys())", e)
    e = re.sub(r"Object\.values\((.+?)\)", r"list(\1.values())", e)
    e = re.sub(r"Object\.entries\((.+?)\)", r"list(\1.items())", e)

    # JSON
    e = re.sub(r"JSON\.stringify\((.+?)\)", r"json.dumps(\1)", e)
    e = re.sub(r"JSON\.parse\((.+?)\)", r"json.loads(\1)", e)

    # console.log
    e = re.sub(r"console\.log\((.+?)\)", r"print(\1)", e)

    # Ternary: keep as Python inline if
    ternary = re.match(r"^(.+?)\s*\?\s*(.+?)\s*:\s*(.+)$", e)
    if ternary:
        cond_part = ternary.group(1).strip()
        true_part = ternary.group(2).strip()
        false_part = ternary.group(3).strip()
        e = f"{true_part} if {cond_part} else {false_part}"

    return e


def _js_line_to_py(line: str) -> str:
    """Convert a single JS statement line to Python."""
    s = line.strip().rstrip(";")

    # Variable declarations
    s = re.sub(r"^(?:const|let|var)\s+", "", s)

    # Destructuring: [a, b] = [b, a]  (keep as-is, works in Python)
    # Spread: ...arr → *arr
    s = s.replace("...", "*")

    # Increment / decrement
    inc_match = re.match(r"^(\w+)\+\+$", s)
    if inc_match:
        return f"{inc_match.group(1)} += 1"
    dec_match = re.match(r"^(\w+)--$", s)
    if dec_match:
        return f"{dec_match.group(1)} -= 1"

    # this. → self.
    s = re.sub(r"\bthis\.", "self.", s)

    s = _js_expr_to_py(s)
    return s


def _transpile_to_typed_language(
    js_code: str,
    language: str,
    problem: Dict[str, Any],
) -> str:
    """Create a solution in a typed language based on the JS solution.

    For Java, C++, C, and Rust we provide the algorithm adapted with
    proper type annotations derived from the existing type-inference
    system.  The conversion is best-effort; complex lambda / higher-order
    patterns may remain as pseudocode comments.
    """
    arg_names, is_design = _extract_function_signature(problem)
    arg_types = _infer_argument_types(problem)

    # Infer return type from expected output
    ret_type = TypeDesc("any")
    for tc in problem.get("testCases", []):
        try:
            val = json.loads(tc["expected"])
            ret_type = _merge_types(ret_type, _infer_type(val))
        except Exception:
            pass

    if language == "java":
        return _adapt_solution_java(js_code, arg_names, arg_types, ret_type)
    if language == "cpp":
        return _adapt_solution_cpp(js_code, arg_names, arg_types, ret_type)
    if language == "rust":
        return _adapt_solution_rust(js_code, arg_names, arg_types, ret_type)
    if language == "c":
        return (
            "/* C solution — adapted from JavaScript reference. */\n"
            "/* Implement using standard C equivalents of the algorithm below. */\n\n"
            + _comment_block(js_code, "// ")
        )
    return js_code


def _comment_block(code: str, prefix: str = "// ") -> str:
    """Return code as commented-out lines with the given prefix."""
    return "\n".join(f"{prefix}{line}" for line in code.split("\n"))


def _adapt_solution_java(
    js_code: str,
    arg_names: List[str],
    arg_types: List[TypeDesc],
    ret_type: TypeDesc,
) -> str:
    """Adapt JS solution to Java syntax."""
    java_ret = _java_type(ret_type)
    if java_ret in ("long", "double", "boolean"):
        java_ret_boxed = {"long": "Long", "double": "Double", "boolean": "Boolean"}.get(java_ret, java_ret)
    else:
        java_ret_boxed = java_ret
    args_str = ", ".join(f"{_java_type(t)} {n}" for n, t in zip(arg_names, arg_types))

    body = js_code
    # Basic syntax adaptations
    body = re.sub(r"(?:const|let|var)\s+", "", body)
    body = re.sub(r"function\s+\w+\s*\([^)]*\)\s*\{", "", body, count=1)
    body = body.replace("===", "==").replace("!==", "!=")
    body = re.sub(r"\btrue\b", "true", body)
    body = re.sub(r"\bfalse\b", "false", body)
    body = re.sub(r"\bnull\b", "null", body)
    body = body.replace("console.log", "System.out.println")

    fn_match = re.search(r"function\s+(\w+)", js_code)
    fn_name = fn_match.group(1) if fn_match else "solve"

    return (
        f"// Java solution for: {fn_name}\n"
        f"// Adapted from JavaScript reference — may need minor adjustments.\n\n"
        f"import java.util.*;\n\n"
        f"public static {java_ret_boxed} {fn_name}({args_str}) {{\n"
        f"    {_indent_body(body, 4)}\n"
        f"}}"
    )


def _adapt_solution_cpp(
    js_code: str,
    arg_names: List[str],
    arg_types: List[TypeDesc],
    ret_type: TypeDesc,
) -> str:
    """Adapt JS solution to C++ syntax."""
    cpp_ret = _cpp_type(ret_type)
    args_str = ", ".join(f"{_cpp_type(t)} {n}" for n, t in zip(arg_names, arg_types))

    body = js_code
    body = re.sub(r"(?:const|let|var)\s+", "auto ", body)
    body = re.sub(r"function\s+\w+\s*\([^)]*\)\s*\{", "", body, count=1)
    body = body.replace("===", "==").replace("!==", "!=")
    body = re.sub(r"\btrue\b", "true", body)
    body = re.sub(r"\bfalse\b", "false", body)
    body = re.sub(r"\bnull\b", "nullptr", body)
    body = body.replace("console.log", "cout <<")
    body = body.replace(".length", ".size()")
    body = body.replace(".push(", ".push_back(")

    fn_match = re.search(r"function\s+(\w+)", js_code)
    fn_name = fn_match.group(1) if fn_match else "solve"

    return (
        f"// C++ solution for: {fn_name}\n"
        f"// Adapted from JavaScript reference — may need minor adjustments.\n\n"
        f"#include <bits/stdc++.h>\n"
        f"using namespace std;\n\n"
        f"{cpp_ret} {fn_name}({args_str}) {{\n"
        f"    {_indent_body(body, 4)}\n"
        f"}}"
    )


def _adapt_solution_rust(
    js_code: str,
    arg_names: List[str],
    arg_types: List[TypeDesc],
    ret_type: TypeDesc,
) -> str:
    """Adapt JS solution to Rust syntax."""
    rust_ret = _rust_type(ret_type)
    args_str = ", ".join(f"{n}: {_rust_type(t)}" for n, t in zip(arg_names, arg_types))

    body = js_code
    body = re.sub(r"(?:const|let|var)\s+", "let ", body)
    body = re.sub(r"function\s+\w+\s*\([^)]*\)\s*\{", "", body, count=1)
    body = body.replace("===", "==").replace("!==", "!=")
    body = re.sub(r"\btrue\b", "true", body)
    body = re.sub(r"\bfalse\b", "false", body)
    body = re.sub(r"\bnull\b", "None", body)
    body = body.replace("console.log", "println!")
    body = body.replace(".length", ".len()")
    body = body.replace(".push(", ".push(")

    fn_match = re.search(r"function\s+(\w+)", js_code)
    fn_name = fn_match.group(1) if fn_match else "solve"

    return (
        f"// Rust solution for: {fn_name}\n"
        f"// Adapted from JavaScript reference — may need minor adjustments.\n\n"
        f"fn {fn_name}({args_str}) -> {rust_ret} {{\n"
        f"    {_indent_body(body, 4)}\n"
        f"}}"
    )


def _indent_body(code: str, indent: int) -> str:
    """Remove outer function wrapper and re-indent the body."""
    lines = code.strip().split("\n")
    # Remove trailing closing brace if present
    if lines and lines[-1].strip() in ("}", "};"):
        lines = lines[:-1]
    # Strip common leading whitespace
    stripped_lines = []
    for line in lines:
        stripped_lines.append(line)
    body = "\n".join(stripped_lines)
    return body.strip()


def build_solution_templates(problem: Dict[str, Any]) -> Dict[str, str]:
    """Build solution code in all supported languages from the JS solution."""
    js_solution = str(problem.get("solutionCode", ""))
    if not js_solution.strip():
        return {lang: "// No solution available" for lang in SUPPORTED_LANGUAGES}

    solutions: Dict[str, str] = {
        "javascript": js_solution,
    }

    # Python — full transpilation
    try:
        solutions["python"] = _transpile_js_to_python(js_solution)
    except Exception:
        solutions["python"] = (
            "# Python solution — adapted from JavaScript reference\n"
            + _comment_block(js_solution, "# ")
        )

    # Typed languages — best-effort adaptation
    for lang in ("java", "cpp", "rust", "c"):
        try:
            solutions[lang] = _transpile_to_typed_language(js_solution, lang, problem)
        except Exception:
            prefix = "// " if lang != "c" else "/* "
            solutions[lang] = f"{prefix}Solution — see JavaScript reference\n" + _comment_block(
                js_solution, "// "
            )

    return solutions


def _build_wrapped_source(problem: Dict[str, Any], language: str, user_code: str, test_input: str) -> str:
    canonical = _canonical_language(language)
    args = json.loads(test_input)
    arg_names, _ = _extract_function_signature(problem)
    arg_types = _infer_argument_types(problem)

    if canonical == "python":
        return (
            "import json\n\n"
            f"{user_code.rstrip()}\n\n"
            f"__args = json.loads(r'''{test_input}''')\n"
            "__result = solve(*__args)\n"
            "if __result is not None:\n"
            "    print(json.dumps(__result))\n"
        )

    if canonical == "javascript":
        return (
            f"{user_code.rstrip()}\n\n"
            f"const __args = JSON.parse(String.raw`{test_input}`);\n"
            "const __result = solve(...__args);\n"
            "if (__result !== undefined) {\n"
            "  console.log(JSON.stringify(__result));\n"
            "}\n"
        )

    if canonical == "java":
        arg_declarations = []
        call_parts = []
        for index, (name, type_desc, value) in enumerate(zip(arg_names, arg_types, args)):
            decl_name = f"arg{index}"
            arg_declarations.append(
                f"        {_java_type(type_desc)} {decl_name} = {_java_literal(value, type_desc)};"
            )
            call_parts.append(decl_name)
        indented_user = textwrap.indent(user_code.rstrip(), "    ")
        return (
            "import java.util.*;\n\n"
            "public class Main {\n"
            f"{indented_user}\n\n"
            "    public static void main(String[] args) {\n"
            + "\n".join(arg_declarations)
            + ("\n" if arg_declarations else "")
            + f"        solve({', '.join(call_parts)});\n"
            "    }\n"
            "}\n"
        )

    if canonical == "cpp":
        arg_declarations = []
        call_parts = []
        for index, (type_desc, value) in enumerate(zip(arg_types, args)):
            decl_name = f"arg{index}"
            arg_declarations.append(
                f"    {_cpp_type(type_desc)} {decl_name} = {_cpp_literal(value, type_desc)};"
            )
            call_parts.append(decl_name)
        return (
            "#include <bits/stdc++.h>\n"
            "#include <optional>\n"
            "using namespace std;\n\n"
            f"{user_code.rstrip()}\n\n"
            "int main() {\n"
            + "\n".join(arg_declarations)
            + ("\n" if arg_declarations else "")
            + f"    solve({', '.join(call_parts)});\n"
            "    return 0;\n"
            "}\n"
        )

    if canonical == "rust":
        arg_declarations = []
        call_parts = []
        for index, (type_desc, value) in enumerate(zip(arg_types, args)):
            decl_name = f"arg{index}"
            arg_declarations.append(
                f"    let {decl_name}: {_rust_type(type_desc)} = {_rust_literal(value, type_desc)};"
            )
            call_parts.append(decl_name)
        return (
            "#![allow(unused)]\n\n"
            f"{user_code.rstrip()}\n\n"
            "fn main() {\n"
            + "\n".join(arg_declarations)
            + ("\n" if arg_declarations else "")
            + f"    solve({', '.join(call_parts)});\n"
            "}\n"
        )

    if canonical == "c":
        escaped = json.dumps(test_input)
        return (
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n"
            "#include <string.h>\n\n"
            f"{user_code.rstrip()}\n\n"
            "int main(void) {\n"
            f"    const char *input_json = {escaped};\n"
            "    solve(input_json);\n"
            "    return 0;\n"
            "}\n"
        )

    raise ValueError(f"Unsupported language: {language}")


def _normalize_output(value: Any) -> Any:
    if isinstance(value, list):
        normalized = [_normalize_output(item) for item in value]
        if normalized and all(isinstance(item, list) for item in normalized):
            return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))
        return normalized
    if isinstance(value, dict):
        return {key: _normalize_output(value[key]) for key in sorted(value)}
    return value


def _compare_output(expected: str, actual: str) -> bool:
    expected_clean = (expected or "").strip()
    actual_clean = (actual or "").strip()
    try:
        expected_obj = json.loads(expected_clean)
        actual_obj = json.loads(actual_clean)
        return _normalize_output(expected_obj) == _normalize_output(actual_obj)
    except Exception:
        return actual_clean == expected_clean


def _execute_with_judge0(language: str, source_code: str) -> Dict[str, Any]:
    if not settings.JUDGE0_ENABLED or not settings.JUDGE0_BASE_URL:
        raise RuntimeError("Judge0 execution is not configured")

    language_id = SUPPORTED_LANGUAGES[language]["judge0_language_id"]
    url = f"{settings.JUDGE0_BASE_URL.rstrip('/')}/submissions?wait=true&base64_encoded=false"
    response = requests.post(
        url,
        json={
            "language_id": language_id,
            "source_code": source_code,
            "stdin": "",
            "redirect_stderr_to_stdout": False,
        },
        timeout=settings.CODE_EXECUTION_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    status = payload.get("status") or {}
    return {
        "provider": "judge0",
        "stdout": payload.get("stdout") or "",
        "stderr": payload.get("stderr") or "",
        "compile_output": payload.get("compile_output") or "",
        "message": payload.get("message") or "",
        "status": status.get("description") or "Unknown",
        "status_id": status.get("id"),
        "time_ms": float(payload.get("time", 0) or 0) * 1000,
    }


def _compile_and_run(
    compile_cmd: List[str],
    run_cmd: List[str],
    cwd: str,
    timeout: int,
) -> Dict[str, Any]:
    """Compile (if needed) then run, returning a standardised result dict."""
    # Compile step
    if compile_cmd:
        try:
            comp = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "provider": "local",
                "stdout": "",
                "stderr": "",
                "compile_output": "Compilation timed out",
                "message": "Compilation timed out",
                "status": "Compilation Error",
                "status_id": 6,
                "time_ms": timeout * 1000,
            }
        if comp.returncode != 0:
            return {
                "provider": "local",
                "stdout": "",
                "stderr": comp.stderr or "",
                "compile_output": (comp.stderr or "") + (comp.stdout or ""),
                "message": "Compilation failed",
                "status": "Compilation Error",
                "status_id": 6,
                "time_ms": None,
            }

    # Run step
    try:
        completed = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "provider": "local",
            "stdout": "",
            "stderr": "",
            "compile_output": "",
            "message": "Execution timed out",
            "status": "Time Limit Exceeded",
            "status_id": 5,
            "time_ms": timeout * 1000,
        }

    run_status = "Accepted" if completed.returncode == 0 else "Runtime Error"
    return {
        "provider": "local",
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "compile_output": "",
        "message": "",
        "status": run_status,
        "status_id": 3 if completed.returncode == 0 else 11,
        "time_ms": None,
    }


def _execute_locally(language: str, source_code: str) -> Dict[str, Any]:
    """Execute source code locally for any supported language."""
    local_temp_root = Path("scratch") / "coding_practice"
    local_temp_root.mkdir(parents=True, exist_ok=True)
    timeout = settings.CODE_EXECUTION_TIMEOUT_SECONDS

    # On Windows the compiled binary has .exe extension
    exe_ext = ".exe" if sys.platform == "win32" else ""

    with tempfile.TemporaryDirectory(prefix="coding_practice_", dir=local_temp_root) as temp_dir:
        td = Path(temp_dir)

        if language == "python":
            src = td / "solution.py"
            src.write_text(source_code, encoding="utf-8")
            return _compile_and_run([], [sys.executable, str(src)], temp_dir, timeout)

        if language == "javascript":
            node = shutil.which("node")
            if not node:
                raise RuntimeError("Node.js is not installed for local JavaScript execution")
            src = td / "solution.js"
            src.write_text(source_code, encoding="utf-8")
            return _compile_and_run([], [node, str(src)], temp_dir, timeout)

        if language == "java":
            javac = shutil.which("javac")
            java = shutil.which("java")
            if not javac or not java:
                raise RuntimeError("JDK (javac/java) is not installed for local Java execution")
            src = td / "Main.java"
            src.write_text(source_code, encoding="utf-8")
            return _compile_and_run(
                [javac, str(src)],
                [java, "-cp", temp_dir, "Main"],
                temp_dir,
                timeout,
            )

        if language == "cpp":
            gpp = shutil.which("g++")
            if not gpp:
                raise RuntimeError("g++ is not installed for local C++ execution")
            src = td / "solution.cpp"
            out = td / f"solution{exe_ext}"
            src.write_text(source_code, encoding="utf-8")
            return _compile_and_run(
                [gpp, str(src), "-o", str(out), "-std=c++17"],
                [str(out)],
                temp_dir,
                timeout,
            )

        if language == "c":
            gcc = shutil.which("gcc")
            if not gcc:
                raise RuntimeError("gcc is not installed for local C execution")
            src = td / "solution.c"
            out = td / f"solution{exe_ext}"
            src.write_text(source_code, encoding="utf-8")
            return _compile_and_run(
                [gcc, str(src), "-o", str(out)],
                [str(out)],
                temp_dir,
                timeout,
            )

        if language == "rust":
            rustc = shutil.which("rustc")
            if not rustc:
                raise RuntimeError("rustc is not installed for local Rust execution")
            src = td / "solution.rs"
            out = td / f"solution{exe_ext}"
            src.write_text(source_code, encoding="utf-8")
            return _compile_and_run(
                [rustc, str(src), "-o", str(out)],
                [str(out)],
                temp_dir,
                timeout,
            )

    raise RuntimeError(f"Local execution is not supported for {language}")


def _execute_source(language: str, source_code: str) -> Dict[str, Any]:
    canonical = _canonical_language(language)
    errors: List[str] = []

    if settings.JUDGE0_ENABLED and settings.JUDGE0_BASE_URL:
        try:
            return _execute_with_judge0(canonical, source_code)
        except Exception as exc:
            logger.warning(f"Judge0 execution failed for {canonical}: {exc}")
            errors.append(str(exc))

    supports_local = SUPPORTED_LANGUAGES[canonical]["supports_local"]
    if supports_local and settings.CODE_EXECUTION_LOCAL_FALLBACK:
        try:
            return _execute_locally(canonical, source_code)
        except Exception as exc:
            logger.warning(f"Local execution failed for {canonical}: {exc}")
            errors.append(str(exc))

    raise RuntimeError("; ".join(errors) or f"No execution provider available for {canonical}")


def execute_problem(problem_id: int, code: str, language: str) -> Dict[str, Any]:
    problem = PROBLEMS_BY_ID.get(problem_id)
    if not problem:
        raise ValueError("Problem not found")

    canonical = _canonical_language(language)
    if canonical not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    results: List[Dict[str, Any]] = []
    provider = "unknown"
    hard_failure = None

    for index, test_case in enumerate(problem["testCases"]):
        if hard_failure is not None:
            results.append(
                {
                    "input": test_case["input"],
                    "expected": test_case["expected"],
                    "actual": "",
                    "passed": False,
                    "error": hard_failure,
                    "time_ms": None,
                    "status": "Skipped",
                }
            )
            continue

        source_code = _build_wrapped_source(problem, canonical, code, test_case["input"])
        execution = _execute_source(canonical, source_code)
        provider = execution.get("provider", provider)
        actual = (execution.get("stdout") or "").strip()
        stderr = (execution.get("stderr") or "").strip()
        compile_output = (execution.get("compile_output") or "").strip()
        message = (execution.get("message") or "").strip()
        error = compile_output or stderr or message or None

        passed = execution.get("status_id") == 3 and _compare_output(test_case["expected"], actual)
        results.append(
            {
                "input": test_case["input"],
                "expected": test_case["expected"],
                "actual": actual,
                "passed": passed,
                "error": error,
                "time_ms": execution.get("time_ms"),
                "status": execution.get("status"),
            }
        )

        if execution.get("status_id") != 3 and not passed:
            hard_failure = error or execution.get("status") or "Execution failed"

    passed_tests = sum(1 for result in results if result["passed"])
    total_tests = len(problem["testCases"])
    return {
        "success": True,
        "language": canonical,
        "provider": provider,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "all_passed": passed_tests == total_tests,
        "results": results,
    }


def _extract_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None
    raw_text = raw_text.strip()
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


async def review_code(problem_id: int, code: str, language: str = "javascript") -> Dict[str, Any]:
    problem = PROBLEMS_BY_ID.get(problem_id)
    if not problem:
        raise ValueError("Problem not found")

    try:
        from app.services.llm_service import get_llm

        llm = get_llm()
    except Exception as exc:
        logger.warning(f"LLM unavailable for coding review: {exc}")
        llm = None

    if llm:
        prompt = textwrap.dedent(
            f"""\
            Review this {language} solution for the coding interview problem below.

            Problem: {problem['title']}
            Difficulty: {problem['difficulty']}
            Topic: {problem['topic']}
            Description:
            {problem['description']}

            Candidate code:
            ```{language}
            {code}
            ```

            Return strict JSON with this shape only:
            {{
              "correctness": "correct|partially_correct|incorrect",
              "correctness_notes": "short note",
              "time_complexity": "Big-O",
              "time_complexity_optimal": true,
              "space_complexity": "Big-O",
              "space_complexity_optimal": true,
              "code_quality_score": 0,
              "suggestions": ["short suggestion"],
              "overall_feedback": "2-3 sentence summary"
            }}
            """
        )

        try:
            raw = llm.generate(
                prompt=prompt,
                system_prompt="You are a precise code reviewer. Return JSON only.",
                max_tokens=700,
                temperature=0.2,
            )
            parsed = _extract_json_object(raw or "")
            if parsed:
                return {"success": True, "review": parsed}
        except Exception as exc:
            logger.warning(f"LLM coding review failed: {exc}")

    review = {
        "correctness": "partially_correct" if code.strip() else "incorrect",
        "correctness_notes": (
            "Run the hidden tests to confirm correctness. The reviewer fell back to "
            "heuristics because no LLM provider was available."
        ),
        "time_complexity": "Unknown",
        "time_complexity_optimal": False,
        "space_complexity": "Unknown",
        "space_complexity_optimal": False,
        "code_quality_score": 55 if code.strip() else 0,
        "suggestions": [
            "Handle edge cases shown in the sample tests before submitting.",
            "Print JSON-compatible output exactly once from solve(...).",
            "Add brief variable names only where they improve clarity.",
        ],
        "overall_feedback": (
            "The review service is running in heuristic mode. Once an LLM provider "
            "is configured, this panel can give deeper correctness and complexity feedback."
        ),
    }
    return {"success": True, "review": review}


async def rubber_duck(
    problem_id: int, transcript: str, current_code: str, language: str = "javascript"
) -> Dict[str, Any]:
    """
    Socratic pair-programmer: given what the user just said out loud about
    their approach and their current code, ask ONE probing follow-up
    question or flag ONE specific gap. Never reveal the solution.
    """
    problem = PROBLEMS_BY_ID.get(problem_id)
    if not problem:
        raise ValueError("Problem not found")

    try:
        from app.services.llm_service import get_llm

        llm = get_llm()
    except Exception as exc:
        logger.warning(f"LLM unavailable for rubber duck: {exc}")
        llm = None

    if llm:
        prompt = textwrap.dedent(
            f"""\
            You are an AI rubber duck for a coding interview candidate. They are
            solving the problem below and just explained their approach out loud.
            Act like a thoughtful pair-programming partner using the Socratic
            method: ask exactly ONE short follow-up question that probes a gap,
            edge case, or complexity concern in their reasoning. Do NOT provide
            the solution, do NOT write code for them, and do NOT confirm whether
            their approach is fully correct — just ask the question a good
            interviewer would ask next.

            Problem: {problem['title']}
            Difficulty: {problem['difficulty']}
            Description:
            {problem['description']}

            Candidate's current code ({language}):
            ```{language}
            {current_code or "(no code yet)"}
            ```

            What the candidate just said out loud:
            "{transcript}"

            Return strict JSON with this shape only:
            {{
              "question": "one short Socratic follow-up question",
              "focus_area": "correctness|edge_case|time_complexity|space_complexity|clarity"
            }}
            """
        )

        try:
            raw = llm.generate(
                prompt=prompt,
                system_prompt=(
                    "You are a Socratic coding interview coach. Never reveal solutions. "
                    "Return JSON only."
                ),
                max_tokens=250,
                temperature=0.4,
            )
            parsed = _extract_json_object(raw or "")
            if parsed and parsed.get("question"):
                return {"success": True, "question": parsed["question"], "focus_area": parsed.get("focus_area", "clarity")}
        except Exception as exc:
            logger.warning(f"LLM rubber duck failed: {exc}")

    return {
        "success": True,
        "question": "Can you walk through what happens with an empty or single-element input?",
        "focus_area": "edge_case",
    }
