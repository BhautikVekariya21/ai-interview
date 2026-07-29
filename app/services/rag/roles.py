"""Role vocabulary normalization for RAG retrieval.

Two different vocabularies for "role" meet in the RAG layer and did not agree:

- ``ResumeParser._infer_domain`` produces a *domain*: ``backend``, ``frontend``,
  ``fullstack``, ``ml_ai``, ``data_science``, ``devops``, ``mobile`` (or ``None``,
  which callers default to the free-text ``"software engineering"``).
- ``app/data/rag_reference_bank.json`` is keyed by *role*: ``backend_engineer``,
  ``frontend_engineer``, ``data_scientist``, ``ml_engineer``, ``devops_engineer``.

The two sets are disjoint, so the rubric filter in ``RAGService`` compared a
domain against a role and matched nothing — 100% of the time. Because that filter
falls back to "use whatever was retrieved" on an empty match, the failure was
silent: answers were graded against an arbitrary role's rubric rather than their
own. Normalizing here keeps the parser and the seed bank untouched.
"""

from __future__ import annotations

import re
from typing import Optional

# Roles that exist as sections in the reference bank. Anything not reachable from
# a value in this set means "no rubric for this role".
CANONICAL_ROLES = frozenset(
    {
        "backend_engineer",
        "frontend_engineer",
        "data_scientist",
        "ml_engineer",
        "devops_engineer",
    }
)

# Parser domain (and common free-text spellings) -> reference-bank role.
# `fullstack` and `mobile` have no dedicated bank section; they map to the
# nearest rubric that shares most of their competency surface rather than
# dropping to no-filter, which would grade them against a random role.
_ROLE_ALIASES = {
    "backend": "backend_engineer",
    "backend_developer": "backend_engineer",
    "frontend": "frontend_engineer",
    "frontend_developer": "frontend_engineer",
    "devops": "devops_engineer",
    "sre": "devops_engineer",
    "platform": "devops_engineer",
    "ml_ai": "ml_engineer",
    "ml": "ml_engineer",
    "machine_learning": "ml_engineer",
    "mlops": "ml_engineer",
    "data_science": "data_scientist",
    "data": "data_scientist",
    "fullstack": "backend_engineer",
    "full_stack": "backend_engineer",
    "mobile": "frontend_engineer",
}


def _slug(role: str) -> str:
    """Lowercase and collapse spaces/hyphens/dots to single underscores."""
    return re.sub(r"_+", "_", re.sub(r"[\s\-.]+", "_", (role or "").strip().lower())).strip("_")


def normalize_role(role: Optional[str]) -> Optional[str]:
    """Map a parser domain or free-text role onto a reference-bank role key.

    Returns ``None`` when the input cannot be mapped confidently — notably the
    generic ``"software engineering"`` default, which names no particular
    rubric. Callers treat ``None`` as "do not filter by role", which is the same
    cross-role behaviour as before, but now a deliberate, logged decision rather
    than the accidental result of comparing two vocabularies that never match.
    """
    slug = _slug(role or "")
    if not slug:
        return None
    if slug in CANONICAL_ROLES:  # already a bank key — pass through
        return slug
    if slug in _ROLE_ALIASES:
        return _ROLE_ALIASES[slug]
    # Tolerate decorated variants ("senior_backend_engineer_ii", "data science eng").
    # Match on underscore token boundaries, not raw substrings: a bare `in` test
    # would let the short "ml" alias fire on "html_developer". Longest alias first
    # so `data_science` wins over `data` and `full_stack` is not shadowed.
    padded = f"_{slug}_"
    for alias in sorted(_ROLE_ALIASES, key=len, reverse=True):
        if f"_{alias}_" in padded:
            return _ROLE_ALIASES[alias]
    for canonical in sorted(CANONICAL_ROLES, key=len, reverse=True):
        if f"_{canonical}_" in padded:
            return canonical
    return None
