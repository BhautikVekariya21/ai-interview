"""Pick the live-coding problems for an interview from the real problem bank.

Why the LLM does not *write* these problems
-------------------------------------------
A coding question is only useful if the candidate's answer can be graded, and
grading needs concrete test cases — inputs paired with known-correct expected
outputs. An LLM asked to invent a problem returns prose and a starter stub; the
test cases it invents alongside them are frequently wrong, which marks a correct
submission as failed. That is worse than not grading at all.

So the LLM *selects* rather than authors. It is shown a catalogue of real bank
problems (title, topic, difficulty) and picks the ones that fit the candidate's
stack and level. The problem body, its test cases, its starter code in all
fourteen languages and its grading all come from the bank, which is verified
data. The LLM's contribution is the choice and the personalised framing that
explains why this problem was put in front of this candidate.

Selection prefers problems the static harness can actually type — 918 of the
1000 — so a Java or Haskell submission gets a real verdict rather than a
"compiled, but not graded" message.
"""

from __future__ import annotations

import random
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger


# Bank difficulty labels are capitalised; interview difficulty levels are not.
# EXPERT has no bank equivalent — the hardest thing the bank holds is Hard.
_DIFFICULTY_FOR_LEVEL = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
    "expert": "Hard",
}

# Resume skills rarely name a data structure outright, so map the vocabulary a
# candidate actually writes down onto the bank's 19 topics. A candidate whose
# resume is all React and Node should not be handed a segment-tree problem.
_TOPIC_AFFINITY: Dict[str, Sequence[str]] = {
    "Arrays & Hashing": ("python", "javascript", "typescript", "java", "c#", "go", "ruby", "php"),
    "Two Pointers": ("c", "c++", "rust", "go"),
    "Sliding Window": ("streaming", "kafka", "spark", "analytics", "time series"),
    "Stack": ("compiler", "parser", "interpreter", "vm"),
    "Binary Search": ("database", "sql", "postgres", "mysql", "index", "search"),
    "Linked List": ("c", "c++", "embedded", "systems"),
    "Trees": ("dom", "react", "angular", "vue", "xml", "json", "hierarch"),
    "Tries": ("search", "elasticsearch", "autocomplete", "nlp", "text"),
    "Heap / Priority Queue": ("scheduler", "queue", "celery", "rabbitmq", "kafka", "os"),
    "Backtracking": ("solver", "constraint", "optimi"),
    "Graphs": ("network", "distributed", "microservice", "dependency", "graph", "neo4j"),
    "Topological Sort": ("build", "ci", "pipeline", "airflow", "dag", "dependency"),
    "Dynamic Programming": ("algorithm", "machine learning", "optimi", "research"),
    "Greedy": ("scheduling", "allocation", "resource"),
    "Bit Manipulation": ("embedded", "firmware", "c", "rust", "protocol", "codec"),
    "Math & Geometry": ("graphics", "game", "unity", "opengl", "simulation", "ml"),
    "Divide & Conquer": ("parallel", "concurren", "mapreduce", "spark"),
    "Disjoint Set (Union-Find)": ("cluster", "network", "graph"),
    "Segment Tree": ("analytics", "time series", "range", "olap"),
}

# How many bank titles to show the LLM. The whole bank would not fit in a
# prompt, and a large random slice is enough for a well-matched pick.
_CATALOGUE_PER_DIFFICULTY = 40

# Re-skinned problems in the bank wear a domain flavour over an unchanged
# statement — "Maximum Delivery Inventorys" is Best Time to Buy and Sell Stock
# with an e-commerce preamble, filed under a different topic. Stripping the
# flavour line exposes the shared statement so the same puzzle is not asked
# twice in one interview.
_DOMAIN_FLAVOUR = re.compile(r"^\s*\*\*Domain:[^*]*\*\*\.?\s*", re.IGNORECASE)


def _fingerprint(description: str) -> str:
    """Identity of the underlying puzzle, ignoring re-skinned framing."""
    body = _DOMAIN_FLAVOUR.sub("", description or "")
    return re.sub(r"[^a-z0-9]+", "", body.lower())[:160]


@lru_cache(maxsize=1)
def _catalogue() -> Dict[str, List[Dict[str, Any]]]:
    """Bank problems grouped by difficulty, gradeable ones first.

    Built once. Each entry is the small descriptor the LLM sees and the
    selector matches on — never the full problem, which stays in the bank.
    """
    try:
        from app.services.code_executor_service import _problem_bank_index
        from app.services import static_harness
    except Exception as exc:  # pragma: no cover - import-time environment issue
        logger.warning(f"Coding problem bank unavailable for selection: {exc}")
        return {}

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for problem_id, problem in _problem_bank_index().items():
        # Design problems ("implement an LRU cache") have no typed signature and
        # cannot be auto-graded, so they never become an interview question.
        if problem.get("grading") in ("design", "unsupported"):
            continue
        gradeable = bool(static_harness.infer_signature(problem.get("test_cases") or []))
        grouped.setdefault(problem.get("difficulty", "Medium"), []).append(
            {
                "id": problem_id,
                "title": problem.get("title", "Untitled"),
                "topic": problem.get("category", "Algorithms"),
                "tags": list(problem.get("tags") or []),
                "difficulty": problem.get("difficulty", "Medium"),
                "gradeable": gradeable,
                "fingerprint": _fingerprint(problem.get("description", "")),
            }
        )

    for entries in grouped.values():
        # Gradeable first: a problem the harness can type gives a real verdict in
        # all fourteen languages, not just the five dynamic ones.
        entries.sort(key=lambda e: (not e["gradeable"], e["title"]))
    return grouped


def _difficulty_plan(count: int, base_level: str) -> List[str]:
    """Bank difficulties for `count` problems, ramping around the base level.

    A candidate is not served three problems of identical difficulty: the first
    is a warm-up one notch below, the rest sit at and above the base. This is
    the same shape the verbal questions use.
    """
    base = _DIFFICULTY_FOR_LEVEL.get((base_level or "medium").lower(), "Medium")
    ladder = ["Easy", "Medium", "Hard"]
    base_index = ladder.index(base)

    plan: List[str] = []
    for position in range(count):
        if position == 0 and count > 1:
            offset = -1  # warm-up
        elif position >= 2:
            offset = 1  # stretch
        else:
            offset = 0
        plan.append(ladder[min(len(ladder) - 1, max(0, base_index + offset))])
    return plan


def _resume_text(resume_data: Dict[str, Any], skills: Sequence[str]) -> str:
    """One lowercase haystack of everything the candidate has worked on."""
    parts = list(skills)
    parts.append(str(resume_data.get("primary_domain") or ""))
    for project in (resume_data.get("projects") or [])[:8]:
        if isinstance(project, dict):
            parts.append(str(project.get("title") or ""))
            parts.append(str(project.get("description") or "")[:200])
            parts.extend(str(t) for t in (project.get("technologies") or [])[:6])
    for job in (resume_data.get("work_experience") or [])[:6]:
        if isinstance(job, dict):
            parts.append(str(job.get("role") or ""))
            parts.extend(str(t) for t in (job.get("technologies") or [])[:6])
    return " ".join(parts).lower()


def _topic_ranking(resume_data: Dict[str, Any], skills: Sequence[str]) -> List[str]:
    """Bank topics ordered by how well they match this résumé."""
    haystack = _resume_text(resume_data, skills)
    scored = [
        (sum(1 for keyword in keywords if keyword in haystack), topic)
        for topic, keywords in _TOPIC_AFFINITY.items()
    ]
    # Ties break alphabetically so the same résumé ranks topics the same way
    # twice; the per-session shuffle below supplies the variety instead.
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [topic for _, topic in scored]


def _pick_from_bank(
    difficulty: str,
    preferred_topics: Sequence[str],
    taken: set,
    used_topics: set,
    used_puzzles: set,
    rng: random.Random,
) -> Optional[Dict[str, Any]]:
    """Best available problem at this difficulty, honouring topic preference.

    Topics already used in this interview are skipped on the first pass, so a
    candidate is not handed three graph problems in a row. If every preferred
    topic is exhausted the constraint is relaxed rather than returning nothing.
    """
    pool = [
        e
        for e in _catalogue().get(difficulty, [])
        if e["id"] not in taken and e["fingerprint"] not in used_puzzles
    ]
    if not pool:
        return None

    for require_fresh_topic in (True, False):
        for topic in preferred_topics:
            if require_fresh_topic and topic in used_topics:
                continue
            matching = [e for e in pool if e["topic"] == topic and e["gradeable"]]
            if matching:
                return rng.choice(matching)

    gradeable = [e for e in pool if e["gradeable"]]
    return rng.choice(gradeable or pool)


def _catalogue_for_prompt(
    difficulties: Sequence[str],
    preferred_topics: Sequence[str],
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """A shortlist of real bank problems to offer the LLM.

    Drawn round-robin across the best-matching topics rather than in strict
    affinity order — one topic holds hundreds of problems and would otherwise
    fill the entire shortlist, leaving the model nothing to choose between.
    """
    shortlist: List[Dict[str, Any]] = []
    offered: set = set()
    for difficulty in dict.fromkeys(difficulties):
        pool = [e for e in _catalogue().get(difficulty, []) if e["gradeable"]]
        if not pool:
            continue

        by_topic: Dict[str, List[Dict[str, Any]]] = {}
        for entry in pool:
            by_topic.setdefault(entry["topic"], []).append(entry)
        for entries in by_topic.values():
            rng.shuffle(entries)

        ordered_topics = [t for t in preferred_topics if t in by_topic]
        ordered_topics += [t for t in by_topic if t not in preferred_topics]

        picked: List[Dict[str, Any]] = []
        depth = 0
        while len(picked) < _CATALOGUE_PER_DIFFICULTY and depth < 8:
            for topic in ordered_topics:
                if depth >= len(by_topic[topic]):
                    continue
                candidate = by_topic[topic][depth]
                # Never offer the same puzzle twice, even under two titles.
                if candidate["fingerprint"] in offered:
                    continue
                offered.add(candidate["fingerprint"])
                picked.append(candidate)
                if len(picked) >= _CATALOGUE_PER_DIFFICULTY:
                    break
            depth += 1
        shortlist.extend(picked)
    return shortlist


def _by_id() -> Dict[str, Dict[str, Any]]:
    return {
        entry["id"]: entry
        for entries in _catalogue().values()
        for entry in entries
    }


def _match_title(title: str) -> Optional[Dict[str, Any]]:
    """Resolve an LLM-named title back to a bank entry.

    The model is asked to copy titles verbatim but sometimes reformats them, so
    matching is case- and punctuation-insensitive. An unresolvable title is
    dropped rather than approximated — a near-miss would hand the candidate a
    different problem than the one the question describes.
    """
    wanted = re.sub(r"[^a-z0-9]+", "", (title or "").lower())
    if not wanted:
        return None
    for entry in _by_id().values():
        if re.sub(r"[^a-z0-9]+", "", entry["title"].lower()) == wanted:
            return entry
    return None


def select_problems(
    count: int,
    resume_data: Dict[str, Any],
    skills: Sequence[str],
    base_level: str,
    llm: Any = None,
    session_seed: str = "",
) -> List[Dict[str, Any]]:
    """Choose `count` bank problems for this candidate.

    Asks the LLM to pick from a real shortlist; falls back to résumé topic
    affinity when the LLM is unavailable or answers with titles that do not
    exist. Either way every returned entry is a real bank problem with real
    test cases — the fallback degrades the personalisation, never the grading.
    """
    if count <= 0 or not _catalogue():
        return []

    rng = random.Random(f"{session_seed}:coding")
    plan = _difficulty_plan(count, base_level)
    topics = _topic_ranking(resume_data, skills)

    chosen: List[Dict[str, Any]] = []
    taken: set = set()
    used_topics: set = set()
    used_puzzles: set = set()

    if llm is not None and getattr(llm, "is_available", False):
        for entry in _ask_llm(llm, plan, topics, skills, resume_data, rng):
            # A re-skinned duplicate of an already-chosen puzzle is dropped even
            # if the LLM picked it — the titles and topics differ, the problem
            # does not.
            if entry["id"] in taken or entry["fingerprint"] in used_puzzles:
                continue
            taken.add(entry["id"])
            used_topics.add(entry["topic"])
            used_puzzles.add(entry["fingerprint"])
            chosen.append(entry)
            if len(chosen) >= count:
                break

    # Top up deterministically. Runs when the LLM is down, returned too few, or
    # named titles that could not be resolved.
    for difficulty in plan[len(chosen):]:
        entry = _pick_from_bank(difficulty, topics, taken, used_topics, used_puzzles, rng)
        if entry is None:
            continue
        taken.add(entry["id"])
        used_topics.add(entry["topic"])
        used_puzzles.add(entry["fingerprint"])
        chosen.append(entry)

    return chosen[:count]


def _ask_llm(
    llm: Any,
    plan: Sequence[str],
    topics: Sequence[str],
    skills: Sequence[str],
    resume_data: Dict[str, Any],
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """LLM's pick from the shortlist, as resolved bank entries."""
    shortlist = _catalogue_for_prompt(plan, topics, rng)
    if not shortlist:
        return []

    listing = "\n".join(
        f"  - [{e['difficulty']}] {e['title']}  (topic: {e['topic']})" for e in shortlist
    )
    wanted = ", ".join(plan)
    domain = resume_data.get("primary_domain") or "software engineering"

    system_prompt = (
        "You are a technical interviewer choosing live-coding problems for a "
        "specific candidate. You choose from a fixed catalogue — you never "
        "invent a problem. Return ONLY a JSON array."
    )
    user_prompt = f"""Choose exactly {len(plan)} problems from the CATALOGUE below for this candidate.

CANDIDATE
  Domain: {domain}
  Skills: {', '.join(list(skills)[:12]) or 'not specified'}

REQUIRED DIFFICULTIES, in order: {wanted}

CATALOGUE (choose only from these — copy each title EXACTLY as written):
{listing}

SELECTION RULES
  1. Pick one problem per required difficulty, in the order listed above.
  2. Prefer problems whose topic connects to the candidate's actual work. A
     backend candidate gets hashing/graph/search problems; an embedded
     candidate gets bit-manipulation and pointer problems.
  3. Never pick the same problem twice, and do not pick two problems from the
     same topic — the set should probe different skills.
  4. `reason` must name a concrete skill, project or role from the candidate's
     background — not a generic statement about the problem.

Return ONLY a JSON array of {len(plan)} objects:
[
  {{"title": "Exact Title From Catalogue", "reason": "why this problem suits this candidate's background"}}
]"""

    try:
        result = llm.generate_json(prompt=user_prompt, system_prompt=system_prompt)
    except Exception as exc:
        logger.warning(f"LLM coding-problem selection failed: {exc}")
        return []

    if isinstance(result, dict):
        for key in ("problems", "questions", "items", "selections"):
            if isinstance(result.get(key), list):
                result = result[key]
                break
    if not isinstance(result, list):
        return []

    resolved: List[Dict[str, Any]] = []
    for item in result:
        if isinstance(item, str):
            title, reason = item, ""
        elif isinstance(item, dict):
            title = str(item.get("title") or item.get("problem") or "")
            reason = str(item.get("reason") or "").strip()
        else:
            continue

        entry = _match_title(title)
        if entry is None:
            logger.debug(f"LLM named a problem outside the catalogue: {title!r}")
            continue
        resolved.append({**entry, "reason": reason})

    return resolved
