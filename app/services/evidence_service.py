"""Evidence coaching service.

Generates two coaching surfaces over the evidence a session already collects —
answer evaluations, authenticity signals, and ATS keyword gaps:

* gap-report — a resume-vs-reality action plan: which claims the interview
               failed to substantiate (fragile/untested), plus ATS keyword
               gaps to close before the next application.
* coach-tip  — a short, in-the-moment delivery tip derived from speech
               signals (fillers, pace, confidence), used by the live
               "Coach Whisper" panel between questions.

Nothing here stores data. Every function is a pure, deterministic function of
the payload the frontend already holds, so the feature works even against a
read-only database and is trivially unit-testable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────
# Gap Report — resume-vs-reality action plan
# ─────────────────────────────────────────────────────────────────────────

# Claim statuses the Resume Proof Map emits, mapped to coaching tone.
_STATUS_LABEL = {
    "validated": "Strongly defended",
    "explored": "Discussed, not proven",
    "fragile": "Defended weakly",
    "untested": "Never probed",
}


def _fallback_gap_report(
    *,
    fragile: List[Dict[str, Any]],
    untested: List[Dict[str, Any]],
    ats_gaps: List[str],
    candidate_name: str,
) -> Dict[str, Any]:
    """Deterministic plan used when no LLM provider is available."""
    focus_areas: List[Dict[str, Any]] = []
    for claim in fragile[:6]:
        focus_areas.append({
            "claim": claim.get("label") or "A resume claim",
            "status": _STATUS_LABEL.get(claim.get("status", ""), claim.get("status", "")),
            "why": (
                "This claim came up but was defended weakly in the interview "
                "(average score below 60). An interviewer would walk away unconvinced."
            ),
            "actions": [
                "Rehearse a Claim → Evidence → Impact answer for this item.",
                "Add one concrete metric (scale, latency, users, cost) to the story.",
                "Have the next mock deliberately probe this claim first.",
            ],
        })
    for claim in untested[:6]:
        focus_areas.append({
            "claim": claim.get("label") or "A resume claim",
            "status": _STATUS_LABEL.get("untested", "Never probed"),
            "why": "This claim was never meaningfully challenged, so it proves nothing yet.",
            "actions": [
                "Ask the interviewer to probe this area in the next session.",
                "Prepare a two-minute answer with a real project example.",
                "Re-run the Resume Proof Map after the next mock to confirm it is validated.",
            ],
        })

    ats_gap_items = [
        {
            "keyword": keyword,
            "action": (
                f"Add '{keyword}' where it is genuinely true — a skills line, a "
                "project, or a quantified bullet."
            ),
        }
        for keyword in ats_gaps[:8]
    ]

    overview = (
        f"{candidate_name or 'This candidate'} has a solid base of validated "
        "claims, but several resume items need work before they survive real "
        "scrutiny. The plan below pairs each weak spot with a concrete practice "
        "target, and closes ATS keyword gaps so the resume and the interview "
        "tell the same story."
    )

    return {
        "overview": overview,
        "focus_areas": focus_areas,
        "ats_gaps": ats_gap_items,
        "next_round_probes": [
            claim.get("label") or "Untested claim"
            for claim in untested[:5]
        ],
        "resources": [
            "STAR method worksheet: Situation, Task, Action, Result for each project.",
            "Quantification drill: rewrite every bullet with a number.",
            "Peer mock sessions that specifically target untested claims.",
        ],
        "generated_by": "rules",
    }


def generate_gap_report(
    *,
    resume_data: Optional[Dict[str, Any]] = None,
    ats_report: Optional[Dict[str, Any]] = None,
    assessments: Optional[List[Dict[str, Any]]] = None,
    candidate_name: str = "",
    target_role: str = "",
) -> Dict[str, Any]:
    """Build a resume-vs-reality action plan from proof-map + ATS evidence.

    `assessments` mirrors the Resume Proof Map rows:
    [{label, kind, status, average_score, best_score, ...}].
    """
    assessments = [a for a in (assessments or []) if isinstance(a, dict)]
    fragile = [a for a in assessments if a.get("status") == "fragile"]
    untested = [a for a in assessments if a.get("status") == "untested"]
    validated = [a for a in assessments if a.get("status") == "validated"]

    ats = ats_report or {}
    keyword_match = ats.get("keyword_match") or {}
    ats_gaps = [
        str(kw) for kw in (keyword_match.get("missing") or [])
        if isinstance(kw, str) and kw.strip()
    ]
    if not ats_gaps and isinstance(ats.get("missing_keywords"), list):
        ats_gaps = [str(kw) for kw in ats["missing_keywords"] if isinstance(kw, str)]

    fallback = _fallback_gap_report(
        fragile=fragile,
        untested=untested,
        ats_gaps=ats_gaps,
        candidate_name=candidate_name,
    )

    # Nothing to coach → return the fallback immediately (no LLM call).
    if not fragile and not untested and not ats_gaps:
        return fallback

    llm_plan = _llm_gap_report(
        fragile=fragile,
        untested=untested,
        validated=validated,
        ats_gaps=ats_gaps,
        candidate_name=candidate_name,
        target_role=target_role,
    )
    if llm_plan:
        return llm_plan
    return fallback


def _llm_gap_report(
    *,
    fragile: List[Dict[str, Any]],
    untested: List[Dict[str, Any]],
    validated: List[Dict[str, Any]],
    ats_gaps: List[str],
    candidate_name: str,
    target_role: str,
) -> Optional[Dict[str, Any]]:
    """Ask the LLM to write the plan; return None when unavailable so the
    caller falls back to the deterministic builder."""
    try:
        from app.services.llm_service import get_llm
    except Exception:
        return None

    try:
        llm = get_llm()
        if not llm.is_available:
            return None
    except Exception:
        return None

    focus_input = "\n".join(
        f"- [{a.get('status')}] {a.get('label', 'Claim')}"
        for a in (fragile + untested)[:8]
    ) or "- none"
    validated_input = ", ".join(
        str(a.get("label", "")) for a in validated[:6]
    ) or "none"

    system_prompt = (
        "You are an expert interview coach. Turn evidence about a candidate's "
        "resume-vs-interview gap into a concrete, actionable improvement plan. "
        "Be specific, honest, and encouraging. Return ONLY JSON."
    )
    user_prompt = (
        f"Candidate: {candidate_name or 'Anonymous'}\n"
        f"Target role: {target_role or 'Not specified'}\n\n"
        "Resume Proof Map findings (status per claim):\n"
        f"{focus_input}\n\n"
        f"Claims strongly validated: {validated_input}\n\n"
        f"ATS keywords missing from the resume: {', '.join(ats_gaps[:12]) or 'none'}\n\n"
        "Return JSON with exactly these keys:\n"
        '{"overview": "2-3 sentences framing the plan", '
        '"focus_areas": [{"claim": "...", "status": "...", "why": "one sentence", '
        '"actions": ["3 concrete practice actions"]}], '
        '"ats_gaps": [{"keyword": "...", "action": "one sentence"}], '
        '"next_round_probes": ["3-5 questions to ask in the next mock"], '
        '"resources": ["3 practice resources or drills"]}'
    )
    try:
        result = llm.generate_json(user_prompt, system_prompt=system_prompt, max_tokens=900)
    except Exception:
        return None

    if not isinstance(result, dict):
        return None

    focus_areas = []
    for area in (result.get("focus_areas") or [])[:8]:
        if not isinstance(area, dict):
            continue
        actions = [
            str(a) for a in (area.get("actions") or []) if isinstance(a, str) and a.strip()
        ]
        focus_areas.append({
            "claim": str(area.get("claim") or "A resume claim"),
            "status": str(area.get("status") or "Needs work"),
            "why": str(area.get("why") or "This claim needs stronger evidence."),
            "actions": actions[:4] or [
                "Rehearse a Claim → Evidence → Impact answer for this item."
            ],
        })

    ats_items = []
    for gap in (result.get("ats_gaps") or [])[:8]:
        if isinstance(gap, dict):
            ats_items.append({
                "keyword": str(gap.get("keyword") or ""),
                "action": str(gap.get("action") or "Add this keyword where it is genuinely true."),
            })

    probes = [
        str(p) for p in (result.get("next_round_probes") or []) if isinstance(p, str) and p.strip()
    ]
    resources = [
        str(r) for r in (result.get("resources") or []) if isinstance(r, str) and r.strip()
    ]

    return {
        "overview": str(result.get("overview") or fallback_overview(candidate_name)),
        "focus_areas": focus_areas or _fallback_gap_report(
            fragile=fragile, untested=untested, ats_gaps=ats_gaps,
            candidate_name=candidate_name,
        )["focus_areas"],
        "ats_gaps": ats_items,
        "next_round_probes": probes,
        "resources": resources or [
            "STAR method worksheet: Situation, Task, Action, Result.",
            "Quantification drill: rewrite every bullet with a number.",
        ],
        "generated_by": "llm",
    }


def fallback_overview(candidate_name: str) -> str:
    return (
        f"{candidate_name or 'This candidate'} has a solid base of validated "
        "claims, but several resume items need work before they survive real "
        "scrutiny."
    )


# ─────────────────────────────────────────────────────────────────────────
# Coach Whisper — between-question delivery tip
# ─────────────────────────────────────────────────────────────────────────

def generate_coach_tip(
    *,
    answer_text: str = "",
    word_count: Optional[int] = None,
    filler_percentage: Optional[float] = None,
    filler_count: Optional[int] = None,
    wpm: Optional[int] = None,
    confidence_score: Optional[float] = None,
    momentum: str = "stable",
    question: str = "",
) -> Dict[str, str]:
    """One focused delivery tip from the speech signals of the last answer.

    Deterministic and instant (no LLM call) so the whisper can appear between
    questions without adding latency to the interview loop.
    """
    words = max(0, int(word_count) if isinstance(word_count, (int, float)) else len(
        [w for w in (answer_text or "").split() if w.strip()]
    ))
    filler_pct = float(filler_percentage) if isinstance(filler_percentage, (int, float)) else None
    fillers = int(filler_count) if isinstance(filler_count, (int, float)) else None
    pace = int(wpm) if isinstance(wpm, (int, float)) else None
    confidence = float(confidence_score) if isinstance(confidence_score, (int, float)) else None

    # 1 — Filler words are the loudest signal.
    if (filler_pct is not None and filler_pct > 5) or (fillers is not None and fillers >= 4):
        # The branch can be entered with only `fillers` set (filler_percentage
        # is optional on the request), so the percentage clause is conditional
        # rather than formatted unconditionally.
        pct_note = f" ({filler_pct:.0f}% of words)" if filler_pct is not None else ""
        return {
            "category": "fillers",
            "icon": "mic_off",
            "title": "Filler spike detected",
            "tip": (
                f"You used {fillers or 'several'} filler word(s) in that answer"
                f"{pct_note}. Next time, take a deliberate "
                "1-second pause instead of reaching for 'um' — recruiters read "
                "purposeful silence as confidence."
            ),
        }

    # 2 — Pace: too fast signals nerves, too slow signals underpreparation.
    if pace is not None:
        if pace > 180:
            return {
                "category": "pace",
                "icon": "slow_down",
                "title": "Slow down",
                "tip": (
                    f"You were speaking at ~{pace} WPM — well past the ideal "
                    "120–160 range. Breath between key points so each idea lands."
                ),
            }
        if pace < 100:
            return {
                "category": "pace",
                "icon": "speed_up",
                "title": "Pick up the pace",
                "tip": (
                    "That answer was very slow or thin. Use the What → How → Why "
                    "framework to expand it without rambling."
                ),
            }

    # 3 — Confidence / hedging.
    if confidence is not None and confidence < 40:
        return {
            "category": "confidence",
            "icon": "lightbulb",
            "title": "Sound more certain",
            "tip": (
                "That answer read as uncertain — hedge words like 'maybe' or "
                "'I think' crept in. Lead with a direct claim, then back it "
                "with one specific example."
            ),
        }

    # 4 — Too short to matter.
    if words < 15:
        return {
            "category": "depth",
            "icon": "expand",
            "title": "Go deeper next answer",
            "tip": (
                "That answer was under 15 words — too thin to leave an "
                "impression. Add what you did, how you did it, and the result."
            ),
        }

    # 5 — Momentum dip across the session.
    if momentum == "declining":
        return {
            "category": "momentum",
            "icon": "battery_low",
            "title": "Don't fade in the second half",
            "tip": (
                "Your delivery has dipped across the last few answers — common "
                "interview fatigue. Sit up, treat each question as a fresh start."
            ),
        }

    # 6 — Default reinforcement.
    return {
        "category": "reinforcement",
        "icon": "star",
        "title": "Keep this energy",
        "tip": (
            "Clean delivery on that answer — good pace, no filler spikes. "
            "Keep the same structure (claim → evidence → impact) for the "
            "questions ahead."
        ),
    }
