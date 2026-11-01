"""
STAR Analyzer — Behavioral answer structure coach (Service).

Scores spoken/written behavioral answers against the STAR framework:

* S — Situation: the story's context ("what was going on").
* T — Task: the candidate's responsibility in that context.
* A — Action: the concrete steps they took.
* R — Result: quantified or stated impact.

Each dimension is scored 0-100 from deterministic signal phrases
(situation-setup verbs, responsibility ownership, action verbs, and
metrics/outcome markers). No LLM call is required — it lights up with zero
provider configuration, which makes it demoable out of the box.

Also emits targeted coaching for the weakest dimensions so the frontend can
render an actionable panel instead of a bare score.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

from loguru import logger

# ─── Signal patterns ─────────────────────────────────────────────────────────

# Setup markers: context/scene setting ("we were migrating", "at my last job").
SITUATION_PATTERNS = [
    r"\b(?:at|during|in)\s+(?:my|our|the)\s+",
    r"\b(?:last|previous|current|previous)\s+(?:job|role|team|company|position)\b",
    r"\b(?:when|while|once)\s+(?:we|I)\b",
    r"\b(?:context|background|situation|challenge|problem|issue)\b",
    r"\bwas\s+(?:working|facing|responsible|leading|handling)\b",
    r"\b(?:we|our team)\s+(?:were|hadd?|was|faced|needed|planned)\b",
    r"\b(?:there)\s+was\b",
    r"\b(?:project|migration|launch|outage|incident|deadline|redesign)\b",
]

# Responsibility markers: the candidate's own task/mandate.
TASK_PATTERNS = [
    r"\b(?:I|my)\s+(?:was|were|had|got|needed|was\s+asked|was\s+responsible)\b",
    r"\b(?:my|the)\s+(?:task|goal|mission|remit|responsibility|mandate|objective)\b",
    r"\bI\s+(?:had\s+to|was\s+tasked\s+with|needed\s+to|was\s+responsible\s+for)\b",
    r"\b(?:owner|owner\s+of|in\s+charge|accountable)\b",
    r"\bmy\s+(?:first|next|main|top|key)\s+(?:priority|job|goal|goal\s+was)\b",
    r"\bI\s+(?:had|was\s+responsible)\s+for\b",
]

# Action markers: concrete verbs describing what the candidate did.
ACTION_PATTERNS = [
    r"\b(?:led|drove|built|designed|implemented|migrated|refactored|automated)\b",
    r"\b(?:wrote|coded|shipped|deployed|debugged|fixed|patched|reviewed)\b",
    r"\b(?:coordinated|organised|organized|negotiated|partnered|paired|mentored)\b",
    r"\b(?:decided|chose|proposed|outlined|analysed|analyzed|prioritised|prioritized)\b",
    r"\b(?:first|then|after\s+that|next|finally|as\s+a\s+result)\b",
    r"\bI\s+(?:ran|took|started|created|set\s+up|spun\s+up|rolled\s+out)\b",
]

# Result markers: outcomes, quantified impact, feedback.
RESULT_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:percent|pct)\b",
    r"\b(?:\d+[\d,]*(?:\.\d+)?)\s*(?:ms|s|seconds|minutes|hours|days|users|requests|usr|rps|qps)\b",
    r"\b(?:reduced|cut|improved|increased|decreased|doubled|tripled|saved|dropped)\b",
    r"\b(?:by\s+|to\s+)9?\d+(?:\.\d+)?\s*%?",
    r"\b(?:result|outcome|impact|win|success|achievement|learned|takeaway)\b",
    r"\b(?:zero|no)\s+(?:downtime|incidents|bugs|regressions|negative\s+feedback)\b",
    r"\b(?:shipped|landed|launched|completed|delivered)\s+(?:on|ahead\s+of|the)\b",
    r"\b(?:positive|great|excellent|strong|promoted)\s+(?:feedback|review|result)\b",
]


def _count_signals(text_lower: str, patterns: List[str]) -> int:
    count = 0
    for pattern in patterns:
        try:
            count += len(re.findall(pattern, text_lower))
        except re.error:  # pragma: no cover - patterns above are pre-validated
            continue
    return count


class STARAnalyzer:
    """Heuristic STAR analyzer for behavioral interview answers."""

    def __init__(self, min_words: int = 12):
        self.min_words = min_words
        self.compile_patterns()

    def compile_patterns(self) -> None:
        """Pre-compile all signal regexes for repeated calls."""
        self._situation = [re.compile(p, re.IGNORECASE) for p in SITUATION_PATTERNS]
        self._task = [re.compile(p, re.IGNORECASE) for p in TASK_PATTERNS]
        self._action = [re.compile(p, re.IGNORECASE) for p in ACTION_PATTERNS]
        self._result = [re.compile(p, re.IGNORECASE) for p in RESULT_PATTERNS]

    # ─── Core scoring ────────────────────────────────────────────────────

    def _score_dimension(
        self,
        text_lower: str,
        patterns: List[re.Pattern[str]],
        word_count: int,
    ) -> float:
        """Turn signal-phrase density into a bounded 0-100 dimension score."""
        if word_count < self.min_words:
            return 0.0
        hits = sum(len(p.findall(text_lower)) for p in patterns)
        # ~4 signal hits per dimension is a realistic textbook STAR answer
        # (~80 words) and should land in the mid-80s; one-off mentions sit in
        # the high-50s. Scaling by words/40 keeps rambling answers from
        # winning points by keyword-stuffing.
        density = hits / max(1.0, word_count / 40.0)
        raw = 100.0 * (1.0 - math.exp(-0.9 * density))
        return round(min(100.0, raw), 1)

    def analyze_answer(
        self,
        answer: str,
        question: Optional[str] = None,
        question_number: int = 1,
    ) -> Dict[str, Any]:
        """Score a single behavioral answer for STAR structure."""
        text_clean = (answer or "").strip()
        if not text_clean or text_clean.upper().startswith("[SKIPPED"):
            return {
                "question_number": question_number,
                "question": question or "",
                "skipped": True,
                "star": {"S": 0, "T": 0, "A": 0, "R": 0},
                "structure_score": 0,
                "grade": "No Data",
                "missing": ["S", "T", "A", "R"],
                "coaching": ["STAR Coach unavailable: no answer text was captured."],
                "highlights": {},
                "words": 0,
            }

        word_count = len(text_clean.split())
        text_lower = text_clean.lower()
        star_raw = {
            "S": self._score_dimension(text_lower, self._situation, word_count),
            "T": self._score_dimension(text_lower, self._task, word_count),
            "A": self._score_dimension(text_lower, self._action, word_count),
            "R": self._score_dimension(text_lower, self._result, word_count),
        }

        try:
            structure_score = round(sum(star_raw.values()) / 4)
        except Exception:  # pragma: no cover - values are numeric by construction
            structure_score = 0

        missing = [key for key, val in star_raw.items() if val < 50]
        grade = self._grade(structure_score)
        highlights = self._highlights(star_raw)
        coaching = self._coaching(missing, star_raw, word_count)

        return {
            "question_number": question_number,
            "question": question or "",
            "skipped": False,
            "star": {k: round(v) for k, v in star_raw.items()},
            "structure_score": structure_score,
            "grade": grade,
            "missing": missing,
            "coaching": coaching,
            "highlights": highlights,
            "words": word_count,
        }

    # ─── Interview-shape helpers ─────────────────────────────────────────

    def analyze_session(self, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze a whole behavioral session, one report per answer."""
        reports: List[Dict[str, Any]] = []
        for index, qa in enumerate(qa_pairs):
            reports.append(
                self.analyze_answer(
                    str(qa.get("answer", "")),
                    str(qa.get("question", "")),
                    int(qa.get("question_number", index + 1)),
                )
            )
        return reports

    def summarize(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate a set of per-answer reports into one session summary."""
        analyzed = [r for r in reports if not r["skipped"]]
        if not analyzed:
            return {
                "answers_total": len(reports),
                "answers_analyzed": 0,
                "avg_structure_score": 0,
                "grade": "No Data",
                "weakest_dimension": None,
                "strongest_dimension": None,
            }
        avg = round(
            sum(r["structure_score"] for r in analyzed) / len(analyzed)
        )
        weakest = min("STAR", key=lambda k: min(x["star"].get(k, 0) for x in analyzed))
        strongest = max("STAR", key=lambda k: max(x["star"].get(k, 0) for x in analyzed))
        return {
            "answers_total": len(reports),
            "answers_analyzed": len(analyzed),
            "avg_structure_score": avg,
            "grade": self._grade(avg),
            "weakest_dimension": weakest,
            "strongest_dimension": strongest,
        }

    # ─── Internals ───────────────────────────────────────────────────────

    def _grade(self, score: int) -> str:
        if score >= 85:
            return "Structured Pro"
        if score >= 70:
            return "Solid"
        if score >= 50:
            return "Emerging"
        if score > 0:
            return "Drifting"
        return "No Data"

    def _highlights(self, star_raw: Dict[str, float]) -> Dict[str, Optional[str]]:
        """One-line explanations of which signals fired per dimension."""
        def level(v: float) -> str:
            if v >= 70:
                return "strong"
            if v >= 40:
                return "partial"
            return "missing"
        return {k: level(v) for k, v in star_raw.items()}

    def _coaching(
        self,
        missing: List[str],
        star_raw: Dict[str, float],
        word_count: int,
    ) -> List[str]:
        tips: List[str] = []
        dimension_tips = {
            "S": "Open with one line of context: where you were, what was at stake — a single sentence is enough.",
            "T": "State your specific responsibility. 'I owned X' beats 'we did X' when an interviewer asks what *you* contributed.",
            "A": "Name the concrete actions you took using strong verbs — led, built, shipped — and keep them in order.",
            "R": "Close with a measured outcome. Numbers (%, latency, users) land hardest; if none exist, state the qualitative win.",
        }
        for dim in ["S", "T", "A", "R"]:
            if dim in missing:
                tips.append(dimension_tips[dim])
            elif star_raw.get(dim, 0) < 70 and dim == "R":
                tips.append(
                    "Your result is mentionable but thin — try to attach one quantified metric to it."
                )
        if word_count > 450:
            tips.append("Answer is long — aim for 150–300 words so the interviewer can track S/T/A/R on one pass.")
        if word_count < 40:
            tips.append("Answers this short won't let you show structure — aim for at least a paragraph.")
        return tips[:4]


# ─── Singleton access ────────────────────────────────────────────────────────

_analyzer_instance: Optional[STARAnalyzer] = None


def get_star_analyzer() -> STARAnalyzer:
    """Get the singleton star analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = STARAnalyzer()
        logger.debug("STARAnalyzer initialized")
    return _analyzer_instance
