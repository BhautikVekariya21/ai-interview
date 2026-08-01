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
    label = (param_names or ["input"])[0] if param_names else "input"
    tags = {t.lower() for t in (problem.get("tags") or [])}
    title = (problem.get("title") or "").lower()

    if isinstance(first, str):
        return _string(first, label)

    if not isinstance(first, list) or not first:
        return None

    # 2-D first: a matrix of rows must not be mistaken for a flat array.
    if all(isinstance(row, list) for row in first):
        return _grid(first, label)

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
