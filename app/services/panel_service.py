"""
Module 13 — AI Panel Interview.

A live, multi-persona interview panel. Instead of one neutral interviewer, the
candidate faces THREE distinct AI personas, each with:

  · its own agenda and questioning angle,
  · its own reaction style to an answer, and
  · its own voice (a distinct gTTS accent, so the panel *sounds* like a panel).

After the answers are collected, the panel holds a visible DELIBERATION: each
persona argues its position and casts a hire / no-hire / borderline vote, then a
weighted verdict is produced with a confidence percentage.

This is a UNIQUE feature — no competitor platform runs a debating AI panel.

Reuses existing infrastructure only:
  · LLMService.generate_json  — persona reactions & deliberation
  · AnswerEvaluator.evaluate  — objective per-answer scoring signal
  · TTSService (accent param)  — distinct per-persona voices (handled client-side)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.llm_service import LLMService
from app.services.answer_evaluator import AnswerEvaluator


# ═══════════════════════════════════════════════════════════════
# PERSONA DEFINITIONS
# ═══════════════════════════════════════════════════════════════
#
# `accent` maps to gTTS ACCENT_MAP (us/uk/in/au/ca/ie/za) so each persona
# gets an audibly different voice for free. `vote_weight` biases the final
# verdict toward the persona whose judgement matters most for a hire.

PERSONAS: List[Dict[str, Any]] = [
    {
        "id": "hiring_manager",
        "name": "Diana Cross",
        "role": "Hiring Manager",
        "emoji": "🎭",
        "accent": "uk",
        "vote_weight": 1.2,
        "temperament": "stern, outcome-focused, slightly skeptical",
        "agenda": (
            "impact, ownership, and whether the candidate actually drove results "
            "versus merely participating. Probes vague claims and looks for "
            "quantified outcomes and accountability."
        ),
    },
    {
        "id": "tech_lead",
        "name": "Kenji Rao",
        "role": "Tech Lead",
        "emoji": "🧑‍💻",
        "accent": "us",
        "vote_weight": 1.3,
        "temperament": "deeply technical, curious, respectful but relentless on depth",
        "agenda": (
            "technical depth, correct tradeoffs, system-design reasoning, and "
            "whether the candidate understands WHY, not just WHAT. Rewards precise, "
            "first-principles answers and pushes on hand-wavy engineering."
        ),
    },
    {
        "id": "hr_partner",
        "name": "Aisha Nair",
        "role": "People & Culture",
        "emoji": "🤝",
        "accent": "in",
        "vote_weight": 1.0,
        "temperament": "warm, perceptive, emotionally intelligent",
        "agenda": (
            "communication, collaboration, growth mindset, and culture add. Reads "
            "how the candidate handles conflict, credit-sharing, and self-awareness."
        ),
    },
]

_PERSONA_BY_ID: Dict[str, Dict[str, Any]] = {p["id"]: p for p in PERSONAS}


def get_personas_public() -> List[Dict[str, Any]]:
    """Frontend-safe persona cards — NO internal prompt/agenda leakage."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "role": p["role"],
            "emoji": p["emoji"],
            "accent": p["accent"],
            "temperament": p["temperament"],
        }
        for p in PERSONAS
    ]


class PanelService:
    """Orchestrates the multi-persona panel: reactions + deliberation."""

    def __init__(
        self,
        llm: Optional[LLMService] = None,
        evaluator: Optional[AnswerEvaluator] = None,
    ) -> None:
        self._llm = llm or LLMService()
        self._evaluator = evaluator or AnswerEvaluator()

    # ─────────────────────────────────────────────────────────
    # REACTION — one persona reacts to one answer
    # ─────────────────────────────────────────────────────────
    def react(
        self,
        persona_id: str,
        question: str,
        answer: str,
        question_category: str = "T",
    ) -> Dict[str, Any]:
        """
        Produce a single persona's live reaction to an answer plus an optional
        sharp follow-up in that persona's voice.
        """
        persona = _PERSONA_BY_ID.get(persona_id)
        if persona is None:
            raise ValueError(f"Unknown persona: {persona_id}")

        # Objective scoring signal from the existing evaluator (persona-agnostic).
        try:
            eval_result = self._evaluator.evaluate(
                question=question,
                answer=answer,
                question_category=question_category,
                generate_followup=False,
            )
            base_score = int(eval_result.get("score", 0) or 0)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"Panel react: evaluator failed ({e}); defaulting score")
            base_score = 0

        system_prompt = (
            f"You are {persona['name']}, the {persona['role']} on a hiring panel. "
            f"Your temperament is {persona['temperament']}. "
            f"You care most about: {persona['agenda']} "
            "Stay fully in character. Never mention that you are an AI or a model."
        )

        user_prompt = (
            f"Interview question:\n\"{question}\"\n\n"
            f"Candidate's answer:\n\"{answer}\"\n\n"
            f"An objective rubric scored this answer {base_score}/100.\n\n"
            "React in character as this panelist. Return JSON with EXACTLY these keys:\n"
            "{\n"
            '  "reaction": "1-2 sentence spoken reaction, in your voice",\n'
            '  "follow_up": "one sharp follow-up question you would ask next (or empty string)",\n'
            '  "impression": "one of: impressed | neutral | unconvinced",\n'
            '  "lean": integer -2..+2 (how much THIS answer moves you toward hiring)\n'
            "}"
        )

        data = self._llm.generate_json(user_prompt, system_prompt=system_prompt)
        data = self._coerce_reaction(data, base_score)

        return {
            "persona_id": persona["id"],
            "name": persona["name"],
            "role": persona["role"],
            "emoji": persona["emoji"],
            "accent": persona["accent"],
            "base_score": base_score,
            **data,
        }

    # ─────────────────────────────────────────────────────────
    # DELIBERATION — the panel debates and votes
    # ─────────────────────────────────────────────────────────
    def deliberate(
        self,
        candidate_name: str,
        transcript: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run the closing deliberation.

        `transcript` is a list of {"question", "answer", "category"?} dicts.
        Returns each persona's argument + vote and a weighted final verdict.
        """
        if not transcript:
            raise ValueError("transcript is empty")

        # Build an objective per-answer score summary once, shared by all personas.
        scored: List[Dict[str, Any]] = []
        score_values: List[int] = []
        for i, qa in enumerate(transcript, start=1):
            q = str(qa.get("question", "")).strip()
            a = str(qa.get("answer", "")).strip()
            cat = str(qa.get("category", "T"))
            try:
                res = self._evaluator.evaluate(
                    question=q, answer=a, question_category=cat, generate_followup=False
                )
                s = int(res.get("score", 0) or 0)
            except Exception:
                s = 0
            score_values.append(s)
            scored.append({"n": i, "question": q, "score": s})

        avg_score = round(sum(score_values) / len(score_values)) if score_values else 0
        score_digest = "; ".join(f"Q{d['n']}={d['score']}/100" for d in scored)

        members: List[Dict[str, Any]] = []
        for persona in PERSONAS:
            member = self._persona_vote(persona, candidate_name, score_digest, avg_score)
            members.append(member)

        verdict = self._tally(members, avg_score)

        return {
            "candidate_name": candidate_name,
            "average_score": avg_score,
            "members": members,
            "verdict": verdict,
        }

    # ─────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────
    def _persona_vote(
        self,
        persona: Dict[str, Any],
        candidate_name: str,
        score_digest: str,
        avg_score: int,
    ) -> Dict[str, Any]:
        system_prompt = (
            f"You are {persona['name']}, the {persona['role']} on a hiring panel, "
            f"deliberating with two colleagues. Temperament: {persona['temperament']}. "
            f"You weigh most heavily: {persona['agenda']} "
            "Argue your honest position from YOUR lens only. Stay in character; "
            "never mention being an AI."
        )
        user_prompt = (
            f"Candidate: {candidate_name}\n"
            f"Objective per-answer scores: {score_digest}\n"
            f"Overall average: {avg_score}/100\n\n"
            "State your closing position to the panel. Return JSON with EXACTLY:\n"
            "{\n"
            '  "argument": "2-3 sentences arguing your view, in your voice",\n'
            '  "vote": "one of: hire | no_hire | borderline",\n'
            '  "confidence": integer 0..100,\n'
            '  "one_line": "a punchy one-line verdict for the UI"\n'
            "}"
        )
        data = self._llm.generate_json(user_prompt, system_prompt=system_prompt)
        data = self._coerce_vote(data, avg_score)
        return {
            "persona_id": persona["id"],
            "name": persona["name"],
            "role": persona["role"],
            "emoji": persona["emoji"],
            "accent": persona["accent"],
            **data,
        }

    def _tally(self, members: List[Dict[str, Any]], avg_score: int) -> Dict[str, Any]:
        """Weighted vote → final decision + confidence."""
        vote_score = {"hire": 1.0, "borderline": 0.0, "no_hire": -1.0}
        weighted_sum = 0.0
        weight_total = 0.0
        hire_votes = 0
        for m in members:
            persona = _PERSONA_BY_ID.get(m["persona_id"], {})
            w = float(persona.get("vote_weight", 1.0))
            # Blend the persona's stance with its own stated confidence.
            conf = max(0, min(100, int(m.get("confidence", 50)))) / 100.0
            weighted_sum += vote_score.get(m.get("vote", "borderline"), 0.0) * w * (0.5 + 0.5 * conf)
            weight_total += w
            if m.get("vote") == "hire":
                hire_votes += 1

        norm = (weighted_sum / weight_total) if weight_total else 0.0  # -1..+1

        if norm >= 0.25:
            decision = "HIRE"
        elif norm <= -0.25:
            decision = "NO HIRE"
        else:
            decision = "BORDERLINE"

        # Confidence: distance from the fence, tempered by objective average.
        confidence = round(min(99, 50 + abs(norm) * 45 + (avg_score - 50) * 0.1))
        confidence = max(1, confidence)

        return {
            "decision": decision,
            "hire_votes": hire_votes,
            "total_votes": len(members),
            "confidence": confidence,
            "summary": (
                f"{decision} — {hire_votes}/{len(members)} panelists lean hire "
                f"(panel confidence {confidence}%)."
            ),
        }

    # ── Coercion / validation ───────────────────────────────
    @staticmethod
    def _coerce_reaction(data: Any, base_score: int) -> Dict[str, Any]:
        if not isinstance(data, dict):
            data = {}
        impression = str(data.get("impression", "")).lower().strip()
        if impression not in {"impressed", "neutral", "unconvinced"}:
            impression = (
                "impressed" if base_score >= 70
                else "unconvinced" if base_score < 45
                else "neutral"
            )
        try:
            lean = int(data.get("lean", 0))
        except (TypeError, ValueError):
            lean = 0
        lean = max(-2, min(2, lean))
        return {
            "reaction": str(data.get("reaction", "")).strip()
            or "Let me note that and move on.",
            "follow_up": str(data.get("follow_up", "")).strip(),
            "impression": impression,
            "lean": lean,
        }

    @staticmethod
    def _coerce_vote(data: Any, avg_score: int) -> Dict[str, Any]:
        if not isinstance(data, dict):
            data = {}
        vote = str(data.get("vote", "")).lower().strip().replace("-", "_").replace(" ", "_")
        if vote not in {"hire", "no_hire", "borderline"}:
            vote = "hire" if avg_score >= 65 else "no_hire" if avg_score < 45 else "borderline"
        try:
            confidence = int(data.get("confidence", 50))
        except (TypeError, ValueError):
            confidence = 50
        confidence = max(0, min(100, confidence))
        return {
            "argument": str(data.get("argument", "")).strip()
            or "I'll base my call on the overall performance.",
            "vote": vote,
            "confidence": confidence,
            "one_line": str(data.get("one_line", "")).strip() or "Weighing the evidence.",
        }


# ── Lazy singleton ─────────────────────────────────────────────
_panel_service: Optional[PanelService] = None


def get_panel_service() -> PanelService:
    global _panel_service
    if _panel_service is None:
        _panel_service = PanelService()
    return _panel_service
