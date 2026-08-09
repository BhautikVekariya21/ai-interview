"""The Gauntlet — adaptive interview pressure engine.

The Gauntlet turns a mock interview into an escalating-stakes simulation.
While a normal interview stays neutral, The Gauntlet watches the candidate's
recent scores and *reacts*: strong answers are rewarded with tougher follow-ups,
interruptions, time pressure, and colder personas; struggling answers ease the
pressure back so the candidate can recover.

The engine is a deterministic state machine (no RNG, no LLM call in the hot
path) — the same evidence always produces the same next move, which keeps it
fast, cheap, and unit-testable. Escalation messaging is delivered through the
existing chat/TTS flow; the engine only decides *what* happens next.

Pressure levels (1-5):
    1 Warm-up        — courteous opening
    2 Steady         — neutral professional
    3 Heating Up     — probing starts
    4 Under Pressure — aggressive digging
    5 Full Gauntlet  — every answer is a fight
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

MAX_LEVEL = 5
MIN_LEVEL = 1

# A score at/above this counts as a "strong" answer for streak logic.
STRONG_SCORE = 75

# Consecutive strong answers before escalation actions kick in.
ESCALATE_STREAK = 2

LEVELS: List[Dict[str, Any]] = [
    {"level": 1, "name": "Warm-up", "flavor": "Courteous and encouraging."},
    {"level": 2, "name": "Steady", "flavor": "Neutral, professional probing."},
    {"level": 3, "name": "Heating Up", "flavor": "Follow-ups get sharper."},
    {"level": 4, "name": "Under Pressure", "flavor": "Aggressive digging begins."},
    {"level": 5, "name": "Full Gauntlet", "flavor": "Every answer is a fight."},
]

# Personas The Gauntlet shifts into as pressure climbs.
GAUNTLET_PERSONAS: List[Dict[str, str]] = [
    {
        "id": "gauntlet_veteran",
        "name": "The Veteran",
        "emoji": "🎖️",
        "temperament": "impassive",
        "voice_hint": "calm, measured, unsmiling",
    },
    {
        "id": "gauntlet_skeptic",
        "name": "The Skeptic",
        "emoji": "🕵️",
        "temperament": "distrustful",
        "voice_hint": "slow, doubting, raising one eyebrow",
    },
    {
        "id": "gauntlet_griller",
        "name": "The Griller",
        "emoji": "🔥",
        "temperament": "aggressive",
        "voice_hint": "fast, cutting, no mercy",
    },
    {
        "id": "gauntlet_silent",
        "name": "The Silent Judge",
        "emoji": "🧊",
        "temperament": "cold",
        "voice_hint": "flat, unhurried, letting silences hang",
    },
]

# ── Message pools (one per action, escalating with level) ──────────────

_ESCALATE_LINES: Dict[int, List[str]] = {
    2: [
        "Solid so far. Let's raise the bar slightly — think out loud on this one.",
        "Good. The questions are about to get a little sharper.",
    ],
    3: [
        "You're handling these well. That's exactly when I start digging.",
        "Comfortable so far? Good — let's change that.",
    ],
    4: [
        "Impressive. Now let's see what happens under real pressure.",
        "You've earned a harder interview. No more softballs.",
    ],
    5: [
        "I'm done being polite. This is the gauntlet now.",
        "Every answer from here is a fight. Show me you can win them.",
    ],
}

_INTERRUPT_LINES = [
    "Hold on — before you finish that thought, defend that assumption.",
    "Stop right there. Why did you choose that trade-off first?",
    "Let me cut in: what breaks if we remove that constraint entirely?",
    "Wait — you said that confidently. Prove it to me in one sentence.",
]

_TOUGH_FOLLOWUP_LINES = [
    "Now defend that approach at 10x scale — what breaks first?",
    "Good answer. Now tell me what you'd do if the requirements changed mid-flight.",
    "Interesting. Walk me through the failure case of that design.",
    "Convince me that wasn't luck. What's the second-best option and why did you reject it?",
]

_TIME_PRESSURE_LINES = [
    "You have thirty seconds to commit to an answer on this one.",
    "No time to think — first instinct. How do you solve it?",
    "Clock's running. Answer in under twenty seconds.",
]

_DEESCALATE_LINES = [
    "Take a breath — you're clearly capable. Let's reset and talk this through calmly.",
    "It's okay to pause. Recover your footing and answer in your own words.",
    "No pressure on this one. Just walk me through it at your own pace.",
]

_STEADY_LINES: Dict[int, List[str]] = {
    1: ["Keep it up — next question.", "Nice. Let's continue."],
    2: ["Solid. Next question.", "Noted. Moving on."],
    3: ["Hmm. Interesting answer. Next question.", "Let's keep going — the bar isn't coming down."],
    4: ["Noted. The pressure stays on.", "Careful now. Next question."],
    5: ["No rest here. Next.", "The gauntlet continues."],
}

_PERSONA_LINES: Dict[str, str] = {
    "gauntlet_skeptic": "Let me switch hats. I'm The Skeptic now — assume nothing you say is true until you prove it.",
    "gauntlet_griller": "I'm going to stop being gentle. I'm The Griller now, and I won't let a vague answer slide.",
    "gauntlet_silent": "From here on I'll be The Silent Judge. I'll let long silences do the talking.",
}


def level_info(level: int) -> Dict[str, Any]:
    """Level metadata, clamped to the valid range."""
    level = max(MIN_LEVEL, min(MAX_LEVEL, int(level)))
    return next(item for item in LEVELS if item["level"] == level)


def personas() -> List[Dict[str, str]]:
    """The persona pool The Gauntlet can shift into."""
    return [dict(persona) for persona in GAUNTLET_PERSONAS]


def _streak(scores: List[float]) -> int:
    """Consecutive strong answers at the tail of the score list."""
    streak = 0
    for score in reversed(scores):
        if score >= STRONG_SCORE:
            streak += 1
        else:
            break
    return streak


def _pick(lines: List[str], salt: int) -> str:
    """Deterministic pick from a pool (salt keeps variety without RNG)."""
    if not lines:
        return ""
    return lines[salt % len(lines)]


def evaluate_step(
    *,
    recent_scores: List[float],
    current_level: int = MIN_LEVEL,
    answered_count: int = 0,
    momentum: str = "stable",
    max_level: int = MAX_LEVEL,
) -> Dict[str, Any]:
    """Compute the next pressure move from the candidate's recent evidence.

    Args:
        recent_scores: Evaluation scores for answered questions (0-100).
        current_level: The level the interview is currently at (1-5).
        answered_count: Total questions answered so far (variety salt).
        momentum: "rising" | "stable" | "declining" (informational).
        max_level: Cap on the pressure level (default 5).

    Returns a dict with: level, level_name, action, message, escalated,
    persona (when the interviewer shifts), and the input evidence used.
    """
    scores = [
        float(score)
        for score in (recent_scores or [])
        if isinstance(score, (int, float))
    ]
    current = max(MIN_LEVEL, min(int(current_level or MIN_LEVEL), MAX_LEVEL))
    cap = max(MIN_LEVEL, min(int(max_level or MAX_LEVEL), MAX_LEVEL))
    answered = max(0, int(answered_count or 0))

    avg = (sum(scores) / len(scores)) if scores else None
    streak = _streak(scores)

    # ── Target level heuristic ──────────────────────────────────────────
    if not scores:
        target = MIN_LEVEL
    else:
        # Linear-ish mapping: 90+ ≈ 5, 75 ≈ 4, 60 ≈ 3, 45 ≈ 2, <35 ≈ 1.
        target = max(MIN_LEVEL, min(cap, round(1 + (avg - 30) / 15)))
        # A hot streak pushes one level higher.
        if streak >= ESCALATE_STREAK and target < cap:
            target += 1
        # A rising arc with recent strong answers keeps the heat on even
        # when the score average alone would hold the current level.
        if momentum == "rising" and streak >= 1 and target == current and target < cap:
            target += 1
        # A cold streak at an elevated level pulls back so the candidate
        # can recover (The Gauntlet rewards recovery, not collapse).
        if streak == 0 and avg is not None and avg < 55 and current > 2:
            target = max(MIN_LEVEL, current - 1)

    # ── Choose the action for the transition ────────────────────────────
    action: str
    persona: Optional[Dict[str, str]] = None
    salt = answered

    if target > current:
        action = "escalate_followup"
        if streak >= ESCALATE_STREAK and salt % 2 == 1:
            action = "interrupt"
        if target >= 4 and salt % 2 == 0:
            action = "persona_shift"
    elif target < current:
        action = "deescalate"
    else:
        # Holding the same level: add pressure variety at high levels.
        if current >= 4 and salt % 3 == 0:
            action = "time_pressure"
        elif current >= 3 and streak >= ESCALATE_STREAK and salt % 2 == 1:
            action = "interrupt"
        else:
            action = "steady"

    # ── Message + persona for the action ────────────────────────────────
    if action == "persona_shift":
        # Shift into a persona suited to the pressure level.
        persona = _persona_for_level(target)
        message = _PERSONA_LINES.get(persona["id"]) or (
            f"I'm {persona['name']} now. The pressure isn't going anywhere."
        )
    elif action == "interrupt":
        message = _pick(_INTERRUPT_LINES, salt)
    elif action == "escalate_followup":
        message = _pick(_TOUGH_FOLLOWUP_LINES + _ESCALATE_LINES.get(target, _ESCALATE_LINES[3]), salt)
    elif action == "time_pressure":
        message = _pick(_TIME_PRESSURE_LINES, salt)
    elif action == "deescalate":
        message = _pick(_DEESCALATE_LINES, salt)
    else:
        message = _pick(_STEADY_LINES.get(current, _STEADY_LINES[2]), salt)

    escalated = action in {"escalate_followup", "interrupt", "persona_shift", "time_pressure"}

    return {
        "level": target,
        "level_name": level_info(target)["name"],
        "action": action,
        "message": message,
        "escalated": escalated,
        "persona": persona,
        "evidence": {
            "average_score": round(avg, 1) if avg is not None else None,
            "strong_streak": streak,
            "answered_count": answered,
            "momentum": momentum,
        },
    }


def _persona_for_level(level: int) -> Dict[str, str]:
    """Pick a copy of the persona pool entry for a pressure level."""
    if level >= 5:
        persona_id = "gauntlet_griller"
    elif level == 4:
        persona_id = "gauntlet_skeptic"
    else:
        persona_id = "gauntlet_veteran"
    return dict(next(p for p in GAUNTLET_PERSONAS if p["id"] == persona_id))
