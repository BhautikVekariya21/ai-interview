"""Game Tape — replay documents for finished interviews.

A finished interview is a pile of disconnected evidence: the per-question
transcript, the per-answer confidence heatmap segments, and the proctoring
event log. ``build_replay_document`` merges those three into one ordered,
typed timeline that the Replay Studio (results page) and the public share page
render identically.

The merge is a pure function of its inputs — no RNG, no LLM, no hidden state —
so the studio preview, the persisted share, and the unit tests always agree.
Severity is classified by event *kind* (a tab switch is a flag, a blocked copy
is a warning, a granted share is information) so the UI can color the tape
without re-implementing policy.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

REPLAY_VERSION = 1

# How serious each proctor event kind is, for tape colouring and the
# violation count shown in the header.
_EVENT_SEVERITY: Dict[str, str] = {
    "tab_switch": "flag",
    "window_blur": "flag",
    "fullscreen_exit": "flag",
    "screen_share_stopped": "warn",
    "screen_share_denied": "warn",
    "screen_share_wrong_surface": "warn",
    "devtools_blocked": "warn",
    "copy_blocked": "warn",
    "paste_blocked": "warn",
    "recorder_error": "info",
    "upload_failed": "info",
    "screen_share_granted": "info",
}

_EVENT_LABELS: Dict[str, str] = {
    "tab_switch": "Tab switch detected",
    "window_blur": "Interview window lost focus",
    "fullscreen_exit": "Fullscreen exited",
    "screen_share_stopped": "Screen sharing stopped",
    "screen_share_denied": "Screen sharing denied",
    "screen_share_wrong_surface": "Wrong screen shared",
    "devtools_blocked": "DevTools attempt blocked",
    "copy_blocked": "Copy attempt blocked",
    "paste_blocked": "Paste attempt blocked",
    "recorder_error": "Recorder error",
    "upload_failed": "Recording upload failed",
    "screen_share_granted": "Screen sharing granted",
}


def event_severity(kind: Any) -> str:
    """Severity for an event kind — ``flag`` | ``warn`` | ``info``."""
    return _EVENT_SEVERITY.get(str(kind or ""), "info")


def event_label(kind: Any) -> str:
    """Human-readable label for an event kind, falling back to a title-cased id."""
    return _EVENT_LABELS.get(
        str(kind or ""), str(kind or "proctor_event").replace("_", " ").capitalize()
    )


def _score_of(entry: Dict[str, Any]) -> Optional[float]:
    try:
        score = entry.get("score")
        if score is None:
            return None
        return float(score)
    except (TypeError, ValueError):
        return None


def _clamp_score(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return None


def _clamp_pct(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _proctor_entry(event: Dict[str, Any]) -> Dict[str, Any]:
    """One typed timeline entry for a proctoring event."""
    kind = str(event.get("kind") or "")
    return {
        "type": "proctor",
        "kind": kind,
        "label": event_label(kind),
        "severity": event_severity(kind),
        "detail": event.get("detail"),
        "occurred_at": event.get("occurred_at") or event.get("recorded_at"),
    }


def build_replay_document(
    *,
    meta: Optional[Dict[str, Any]] = None,
    qa_pairs: Optional[List[Dict[str, Any]]] = None,
    heatmap: Optional[Dict[str, Any]] = None,
    proctor_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Merge transcript + heatmap + proctor events into a replay document.

    Args:
        meta: Display metadata (candidate_name, overall_score, overall_grade,
            duration_seconds, total/answered questions, created_at, target_role).
        qa_pairs: Per-question records with question_number, question, answer,
            score, grade, feedback.
        heatmap: The confidence heatmap response (``{questions: [...]}``) keyed
            by question_number, carrying per-answer text segments with scores.
        proctor_events: Raw proctoring events. Those with a ``question_index``
            are placed right after that question's answer; the rest trail the
            tape so nothing is ever hidden.

    Returns a versioned document with a typed ``timeline`` and a ``stats``
    summary for the header.
    """
    meta = dict(meta or {})
    qa = [q for q in (qa_pairs or []) if isinstance(q, dict)]

    # Index heatmap questions by question_number so segments can be attached
    # to their answer regardless of the order the client sent them.
    heat = heatmap or {}
    heat_by_number: Dict[int, Dict[str, Any]] = {}
    for question in heat.get("questions") or []:
        if not isinstance(question, dict):
            continue
        number = question.get("question_number")
        if isinstance(number, (int, float)):
            heat_by_number[int(number)] = question

    # Group proctor events by the question they occurred during.
    events_by_question: Dict[int, List[Dict[str, Any]]] = {}
    trailing_events: List[Dict[str, Any]] = []
    for event in (proctor_events or []):
        if not isinstance(event, dict):
            continue
        index = event.get("question_index")
        if isinstance(index, (int, float)) and int(index) >= 1:
            events_by_question.setdefault(int(index), []).append(event)
        else:
            trailing_events.append(event)

    timeline: List[Dict[str, Any]] = []
    scores: List[float] = []
    weakest: Optional[Dict[str, Any]] = None

    for q in qa:
        number = int(q.get("question_number") or 0)
        timeline.append(
            {
                "type": "question",
                "question_number": number,
                "text": str(q.get("question") or ""),
            }
        )

        score = _score_of(q)
        answer_entry: Dict[str, Any] = {
            "type": "answer",
            "question_number": number,
            "text": str(q.get("answer") or ""),
            "score": score,
            "grade": q.get("grade"),
            "feedback": q.get("feedback"),
            "segments": [],
        }

        heat_question = heat_by_number.get(number)
        if heat_question:
            segments: List[Dict[str, Any]] = []
            for segment in heat_question.get("segments") or []:
                if not isinstance(segment, dict):
                    continue
                segments.append(
                    {
                        "text": str(segment.get("text") or ""),
                        "score": _clamp_score(segment.get("score")),
                        "start_pct": _clamp_pct(segment.get("start_pct")),
                        "end_pct": _clamp_pct(segment.get("end_pct")),
                        "flags": [
                            str(flag)
                            for flag in (segment.get("flags") or [])
                            if flag
                        ],
                    }
                )
            answer_entry["segments"] = segments

        if score is not None:
            scores.append(score)
            if weakest is None or score < weakest["score"]:
                weakest = {"question_number": number, "score": score}

        timeline.append(answer_entry)
        timeline.extend(_proctor_entry(e) for e in events_by_question.get(number, []))

    timeline.extend(_proctor_entry(e) for e in trailing_events)

    event_count = sum(len(v) for v in events_by_question.values()) + len(trailing_events)

    stats: Dict[str, Any] = {
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        # Every qa_pair is a recorded answer (skips included), so the count
        # is the transcript length, not the number of scored answers.
        "answered_questions": len(qa),
        "total_questions": meta.get("total_questions") or len(qa),
        "proctor_events_total": event_count,
        "violations": sum(
            1
            for event in (proctor_events or [])
            if isinstance(event, dict)
            and event_severity(event.get("kind")) in {"flag", "warn"}
        ),
        "weakest_question": weakest,
    }

    return {
        "version": REPLAY_VERSION,
        "meta": meta,
        "timeline": timeline,
        "stats": stats,
    }
