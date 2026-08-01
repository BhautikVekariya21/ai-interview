"""Figures for problem statements, drawn from the graded test data.

LeetCode illustrates a histogram problem with a picture of the histogram, a
matrix problem with the grid, a linked-list problem with the chain of nodes. We
cannot use theirs — those are copyrighted assets on their CDN — but we do not
need to: the values in the picture are exactly the values in example 1, and
those we already have.

Drawing them ourselves is also strictly better in one way. A static image can
drift from the text around it; a figure computed from ``test_cases`` is the
same data the grader asserts against, so the picture cannot disagree with the
example printed beneath it.

What is emitted here is a *spec* — a small dict of numbers and labels — not
markup. The frontend turns it into SVG with React elements, so no generated
string is ever interpolated into the DOM.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# A figure has to be readable at the width of the description pane. Past these
# sizes a picture is worse than none: 60 bars become a grey smear and a 20x20
# grid renders at two pixels a cell. Such problems keep the textual example.
_MAX_BARS = 24
_MAX_CELLS = 16
_MAX_GRID_ROWS = 8
_MAX_GRID_COLS = 8
_MAX_CHARS = 20
_MAX_NODES = 10
# Level-order tree encodings include nulls, so the array length can exceed the
# node count; 15 slots is roughly the biggest tree that reads at pane width.
_MAX_TREE_SLOTS = 15

# The bank's tags, plus the title words, that mark a problem as tree-shaped.
# Tags are the primary signal (they are accurate even where ``topic`` lies);
# the title fallback catches themed variants whose tag lists get renamed.
_TREE_TAGS = {"tree", "bst"}

# Parameter names that identify the *root of a tree*, not a plain array. The
# bank's "Validate Binary Search Tree" ships its in-order array under the name
# ``inorder`` — drawing that as a tree would misread a sorted list as a heap.
_TREE_ROOT_NAMES = {"root", "tree", "node", "head", "p", "q", "s", "t", "arr"}


def _tree_hinted(problem: Dict[str, Any]) -> bool:
    """True when the problem's tags or title say this is a tree problem.

    The title match is a word-boundary check ("tree" as its own word, not a
    substring), so a future problem named e.g. "Minimum Spanning Tree Cost"
    is not misread as a binary-tree problem by accident.
    """
    tags = {t.lower() for t in (problem.get("tags") or [])}
    if tags & _TREE_TAGS:
        return True
    words = set((problem.get("title") or "").lower().split())
    return bool(words & {"tree", "bst"})


def _tree(
    values: List[Any], label: str, problem: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """A level-order tree encoding → tree figure, or None.

    The bank encodes trees as flat arrays where ``null`` marks a missing
    child: ``[3,9,20,null,null,15,7]``. LeetCode illustrates those with a
    picture of the tree, so a null-carrying flat list is a tree, not a cell
    strip. An all-int flat list is ambiguous — ``[1,2,3,4,5]`` could be a
    level-order encoding or a sorted array — so only a root-named parameter
    (or a perfect-tree length) promotes it to a tree figure. That keeps the
    bank's "Validate BST" in-order array (param ``inorder``, length 5) out.
    """
    if not (1 <= len(values) <= _MAX_TREE_SLOTS):
        return None
    if any(isinstance(v, (list, dict)) for v in values):
        return None
    if not all(v is None or (isinstance(v, int) and not isinstance(v, bool)) for v in values):
        return None
    if all(v is None for v in values):
        return None
    if not _tree_hinted(problem):
        return None

    has_null = any(v is None for v in values)
    rootish = label.lower() in _TREE_ROOT_NAMES
    perfect = len(values) in (1, 3, 7, 15)
    if has_null or rootish or perfect:
        return {"kind": "tree", "values": list(values), "label": label}
    return None


# Parameter names and title words that mean "these integers are bar heights",
# where a bar chart is the right picture and an index-cell strip is not.
_BAR_PARAMS = {"heights", "height", "bars", "elevation", "buildings"}
_BAR_TITLE_WORDS = ("histogram", "rectangle", "water", "rain", "skyline", "container")


def _all_ints(values: List[Any]) -> bool:
    return bool(values) and all(
        isinstance(v, int) and not isinstance(v, bool) for v in values
    )


def _bars(values: List[int], label: str) -> Optional[Dict[str, Any]]:
    """A bar chart. Negative heights have no sensible baseline, so they opt out."""
    if not (1 <= len(values) <= _MAX_BARS) or any(v < 0 for v in values):
        return None
    return {"kind": "bars", "values": values, "label": label}


def _array(values: List[int], label: str) -> Optional[Dict[str, Any]]:
    """An indexed strip of cells — the shape LeetCode draws for `nums`."""
    if not (1 <= len(values) <= _MAX_CELLS):
        return None
    return {"kind": "array", "values": [str(v) for v in values], "label": label}


def _grid(rows: List[List[Any]], label: str) -> Optional[Dict[str, Any]]:
    """A matrix. Ragged rows are not a grid and are left to the text."""
    if not (1 <= len(rows) <= _MAX_GRID_ROWS):
        return None
    if not all(isinstance(r, list) for r in rows):
        return None
    width = len(rows[0])
    if not (1 <= width <= _MAX_GRID_COLS) or any(len(r) != width for r in rows):
        return None
    if any(isinstance(cell, (list, dict)) for row in rows for cell in row):
        return None
    return {
        "kind": "grid",
        "rows": [[str(cell) for cell in row] for row in rows],
        "label": label,
    }


def _linked(values: List[Any], label: str) -> Optional[Dict[str, Any]]:
    if not (1 <= len(values) <= _MAX_NODES):
        return None
    if any(isinstance(v, (list, dict)) for v in values):
        return None
    return {"kind": "linked", "values": [str(v) for v in values], "label": label}


def _string(text: str, label: str) -> Optional[Dict[str, Any]]:
    if not (1 <= len(text) <= _MAX_CHARS) or not text.isprintable():
        return None
    return {"kind": "string", "values": list(text), "label": label}


def build_diagram(
    problem: Dict[str, Any],
    example_input: Any,
    param_names: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """The figure for one example, or None when no shape fits.

    Only the first argument is drawn. A problem takes ``(nums, target)`` and the
    picture is of ``nums`` — a scalar alongside it is already legible in the
    example line and adds nothing as a graphic.
    """
    arguments = example_input if isinstance(example_input, list) else [example_input]
    if not arguments:
        return None

    first = arguments[0]
    # A null-carrying level-order encoding is untypeable (``infer_signature``
    # refuses nulls), so the starter's parameter names are never recovered and
    # the figure would otherwise be captioned "input". A tree-hinted problem
    # with no names is a tree problem — name the root.
    label = (
        (param_names or ["input"])[0]
        if param_names
        else ("root" if _tree_hinted(problem) else "input")
    )
    tags = {t.lower() for t in (problem.get("tags") or [])}
    title = (problem.get("title") or "").lower()

    if isinstance(first, str):
        return _string(first, label)

    if not isinstance(first, list) or not first:
        return None

    # 2-D first: a matrix of rows must not be mistaken for a flat array.
    if all(isinstance(row, list) for row in first):
        return _grid(first, label)

    # A flat int-or-null list from a tree problem is a level-order encoding.
    # Checked before ``_all_ints``: nulls fail that test, so without this
    # branch every tree problem would render no figure at all.
    tree = _tree(first, label, problem)
    if tree:
        return tree

    if not _all_ints(first):
        # A list of strings still reads well as cells (word lists, tokens).
        if all(isinstance(v, str) for v in first) and len(first) <= _MAX_CELLS:
            return {"kind": "array", "values": list(first), "label": label}
        return None

    if "linked-list" in tags:
        return _linked(first, label)

    wants_bars = label.lower() in _BAR_PARAMS or any(w in title for w in _BAR_TITLE_WORDS)
    if wants_bars:
        bars = _bars(first, label)
        if bars:
            return bars

    return _array(first, label)


# ── Database schema figures ──────────────────────────────────────────────────
#
# SQL problems ship CREATE TABLE / INSERT statements instead of a typed function
# signature, so none of the array/grid/tree builders above apply. The figure is
# the schema itself: one card per table, its columns with types and key badges,
# and a couple of seed rows so the candidate can see the data the query runs
# against. Values come from the problem's own seed data, so the picture cannot
# disagree with what the grader asserts.

_MAX_SQL_TABLES = 4
_MAX_SQL_COLUMNS = 8
_MAX_SQL_ROWS = 3
# An example's tables carry the case the grader actually replays, so they show
# more than the schema thumbnail does — enough to see the join line up, still
# short enough to read in the description pane.
_MAX_SQL_EXAMPLE_ROWS = 6

_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w]+)\s*\((.*)\)\s*;?",
    re.IGNORECASE | re.DOTALL,
)
# ``VALUES`` is captured greedily to the end of the statement. A lazy ``(.*?)``
# here silently matches the empty string — the trailing ``;`` is optional, so
# the whole pattern still succeeds and every seed row is dropped on the floor.
_INSERT_INTO = re.compile(
    r"INSERT\s+INTO\s+([\w]+)\s*(?:\(([^)]*)\))?\s*VALUES\s*(.+?)\s*;?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def _split_top_level(text: str, sep: str = ",") -> List[str]:
    """Split on ``sep`` at paren depth zero, respecting string quotes."""
    parts: List[str] = []
    depth = 0
    quote: Optional[str] = None
    current: List[str] = []
    for ch in text:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            current.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def _parse_column(raw: str) -> Optional[Dict[str, Any]]:
    """One column definition → name, type, key badge (PK/UQ/FK)."""
    raw = raw.strip()
    if not raw or raw.upper().startswith(
        ("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CONSTRAINT", "CHECK", "KEY", "INDEX")
    ):
        return None
    match = re.match(r"([\w]+)\s+([\w()]+(?:\s*,\s*[\w()]+)*)\s*(.*)$", raw)
    if not match:
        return None
    name, type_, rest = match.group(1), match.group(2), match.group(3).upper()
    if "PRIMARY KEY" in rest:
        key = "PK"
    elif "UNIQUE" in rest:
        key = "UQ"
    elif "FOREIGN KEY" in rest or "REFERENCES" in rest:
        key = "FK"
    elif "KEY" in rest:
        key = "KEY"
    else:
        key = ""
    return {"name": name, "type": type_, "key": key}


def _parse_value(raw: str) -> Any:
    """A SQL literal → its Python value (NULL → None, numbers, quoted strings)."""
    raw = raw.strip()
    if raw.upper() == "NULL":
        return None
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _parse_value_groups(text: str) -> List[List[Any]]:
    """``(1, 'Wang'), (2, 'Alice')`` → [[1, 'Wang'], [2, 'Alice']]."""
    rows: List[List[Any]] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] != "(":
            i += 1
            continue
        depth = 0
        buf: List[str] = []
        quote: Optional[str] = None
        while i < n:
            ch = text[i]
            if quote:
                buf.append(ch)
                if ch == quote:
                    quote = None
            elif ch in ("'", '"'):
                quote = ch
                buf.append(ch)
            elif ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth -= 1
                buf.append(ch)
                if depth == 0:
                    break
            else:
                buf.append(ch)
            i += 1
        inner = "".join(buf)[1:-1]
        row = [_parse_value(v) for v in _split_top_level(inner)]
        if row:
            rows.append(row)
        i += 1
    return rows


def _first_seed(problem: Dict[str, Any]) -> List[str]:
    """The seed statements for the first test case, or the problem-level seed."""
    cases = problem.get("test_cases") or []
    if cases and isinstance(cases[0], dict):
        seed = cases[0].get("seed") or []
        if seed:
            return seed
    return list(problem.get("sql_seed") or [])


def _rows_for_table(
    seed: List[str], table: str, columns: Optional[List[str]] = None
) -> List[List[Any]]:
    """Every row the seed inserts into `table`, aligned to `columns`.

    An ``INSERT INTO t (b, a) VALUES (1, 2)`` lists its values in *its own*
    column order, which need not be the table's. Rendering that row under the
    schema's headers without permuting it would put each value under the wrong
    column — a figure that quietly contradicts the data the grader seeds.

    Returns all rows; the caller decides how many fit and flags the remainder.
    """
    rows: List[List[Any]] = []
    for stmt in seed:
        match = _INSERT_INTO.match(stmt.strip())
        if not match or match.group(1).lower() != table.lower():
            continue
        named = [
            c.strip().strip('`"[]')
            for c in _split_top_level(match.group(2) or "")
            if c.strip()
        ]
        for row in _parse_value_groups(match.group(3)):
            if columns and named and len(named) == len(row):
                index = {name.lower(): value for name, value in zip(named, row)}
                row = [index.get(col.lower()) for col in columns]
            rows.append(row)
    return rows


# The reference query's SELECT list names the columns of the expected result.
# Those names are part of the problem statement on a real judge -- the output
# table has headers -- and naming them gives away no more than the expected rows
# already do. The parser is deliberately all-or-nothing: anything it cannot read
# cleanly (``SELECT *``, an expression it cannot name) yields no headers at all
# rather than a set that might mislabel a column.
_SELECT_LIST = re.compile(
    r"\bSELECT\s+(?:DISTINCT\s+)?(.*?)\s+FROM\b", re.IGNORECASE | re.DOTALL
)


def _result_columns(problem: Dict[str, Any], width: int) -> List[str]:
    """Headers for the expected-result table, read off the reference query."""
    query = problem.get("solution_sql") or problem.get("solutionCode") or ""
    if not isinstance(query, str):
        return []
    match = _SELECT_LIST.search(query)
    if not match:
        return []
    names: List[str] = []
    for part in _split_top_level(match.group(1)):
        part = part.strip()
        if not part:
            return []
        alias = re.search(r"\bAS\s+([\w'\"`\[\]]+)\s*$", part, re.IGNORECASE)
        name = (alias.group(1) if alias else part.rsplit(".", 1)[-1]).strip("'\"`[] ")
        if not re.fullmatch(r"\w+", name):
            return []
        names.append(name)
    return names if len(names) == width else []


def _schema_tables(schema: List[str]) -> List[Dict[str, Any]]:
    """Each CREATE TABLE → its name and typed, key-badged columns."""
    tables: List[Dict[str, Any]] = []
    for stmt in schema:
        match = _CREATE_TABLE.match(stmt.strip())
        if not match:
            continue
        name, body = match.group(1), match.group(2)
        columns = [
            column for part in _split_top_level(body) if (column := _parse_column(part))
        ]
        if not columns or len(tables) >= _MAX_SQL_TABLES:
            continue
        tables.append({"name": name, "columns": columns[: _MAX_SQL_COLUMNS]})
    return tables


def build_schema_diagram(problem: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """A spec for the problem's tables: columns with types and key badges.

    Returns None when the schema cannot be read — the problem then keeps the
    textual example instead of a figure.
    """
    schema = problem.get("sql_schema") or []
    if not schema:
        return None
    seed = _first_seed(problem)
    tables = _schema_tables(schema)
    if not tables:
        return None
    for table in tables:
        names = [c["name"] for c in table["columns"]]
        rows = _rows_for_table(seed, table["name"], names)
        table["rows"] = rows[:_MAX_SQL_ROWS]
        if len(rows) > _MAX_SQL_ROWS:
            table["more"] = len(rows) - _MAX_SQL_ROWS
    return {"kind": "schema", "tables": tables}


def build_sql_example_diagram(
    problem: Dict[str, Any], case: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """One example's figure: the tables as seeded, and the result table.

    This is what a judge shows for a database question — input tables with
    headers and rows, then the table the query must return. The alternative,
    printing the raw ``INSERT`` statements as the "input" and a JSON array of
    arrays as the "output", asks the candidate to parse SQL in their head to
    see data that is inherently tabular.

    Both halves come from the case the grader replays, so neither can disagree
    with it: the rows are parsed out of that case's own ``seed``, and the result
    is its ``expected`` verbatim. Only the result *headers* come from elsewhere
    (the reference query's SELECT list), and they are dropped entirely unless
    they can be read cleanly and match the row width.
    """
    schema = problem.get("sql_schema") or []
    if not schema:
        return None
    tables = _schema_tables(schema)
    if not tables:
        return None

    seed = list(case.get("seed") or []) or _first_seed(problem)
    populated: List[Dict[str, Any]] = []
    for table in tables:
        names = [c["name"] for c in table["columns"]]
        rows = _rows_for_table(seed, table["name"], names)
        # A table the case never seeds is still part of the schema and still
        # worth showing -- an empty side is often the point of a LEFT JOIN
        # problem -- but it renders as headers with no body.
        table["rows"] = rows[:_MAX_SQL_EXAMPLE_ROWS]
        if len(rows) > _MAX_SQL_EXAMPLE_ROWS:
            table["more"] = len(rows) - _MAX_SQL_EXAMPLE_ROWS
        populated.append(table)

    expected = case.get("expected")
    result: Optional[Dict[str, Any]] = None
    if isinstance(expected, list):
        rows = [row if isinstance(row, list) else [row] for row in expected]
        width = max((len(row) for row in rows), default=0)
        result = {
            "columns": _result_columns(problem, width) if width else [],
            "rows": rows[:_MAX_SQL_EXAMPLE_ROWS],
        }
        if len(rows) > _MAX_SQL_EXAMPLE_ROWS:
            result["more"] = len(rows) - _MAX_SQL_EXAMPLE_ROWS

    spec: Dict[str, Any] = {"kind": "sql_example", "tables": populated}
    if result is not None:
        spec["result"] = result
    return spec
