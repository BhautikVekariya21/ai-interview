"""Tests for the Game Tape replay document builder.

Every assertion pins exact expected values hand-derived from the merge rules:
transcript entries are emitted question-then-answer, heatmap segments attach to
their answer by question_number, proctor events with a question_index sit right
after that answer, and events without one trail the tape.
"""

from __future__ import annotations

from app.services.replay_service import (
    build_replay_document,
    event_label,
    event_severity,
)

META = {
    "candidate_name": "Alex Chen",
    "overall_score": 70,
    "overall_grade": "B+",
    "duration_seconds": 420,
    "total_questions": 2,
    "answered_questions": 2,
}


def _qa_pairs():
    return [
        {
            "question_number": 1,
            "question": "Walk me through your Kafka migration.",
            "answer": "I designed a dual-write path...",
            "score": 80,
            "grade": "B+",
            "feedback": "Clear structure.",
        },
        {
            "question_number": 2,
            "question": "How do you handle backpressure?",
            "answer": "Backpressure is about queues...",
            "score": 60,
            "grade": "C",
            "feedback": "Needs more depth.",
        },
    ]


def test_merges_transcript_heatmap_and_proctor_into_ordered_timeline():
    document = build_replay_document(
        meta=META,
        qa_pairs=_qa_pairs(),
        heatmap={
            "questions": [
                {
                    "question_number": 1,
                    "segments": [
                        {"text": "opening", "score": 70, "start_pct": 0, "end_pct": 50},
                        {"text": "core", "score": 92, "start_pct": 50, "end_pct": 100},
                    ],
                }
            ]
        },
        proctor_events=[
            {"kind": "tab_switch", "detail": "switched away", "question_index": 1},
            {"kind": "copy_blocked", "detail": "copy attempt", "question_index": 2},
            {"kind": "recorder_error", "detail": "chunk lost"},
        ],
    )

    types = [entry["type"] for entry in document["timeline"]]
    assert types == [
        "question",
        "answer",
        "proctor",
        "question",
        "answer",
        "proctor",
        "proctor",
    ]

    # Question/answer pairs carry their numbers.
    assert document["timeline"][0] == {
        "type": "question",
        "question_number": 1,
        "text": "Walk me through your Kafka migration.",
    }
    assert document["timeline"][1]["type"] == "answer"
    assert document["timeline"][1]["question_number"] == 1
    assert document["timeline"][1]["score"] == 80.0
    assert document["timeline"][1]["grade"] == "B+"

    # Heatmap segments attach to the answer with the same question_number.
    assert len(document["timeline"][1]["segments"]) == 2
    assert document["timeline"][1]["segments"][1]["score"] == 92.0

    # Proctor events with an index land right after that question's answer.
    assert document["timeline"][2]["kind"] == "tab_switch"
    assert document["timeline"][2]["severity"] == "flag"
    assert document["timeline"][5]["kind"] == "copy_blocked"
    assert document["timeline"][6]["kind"] == "recorder_error"

    # The answer without a heatmap entry gets an empty segments list.
    assert document["timeline"][4]["segments"] == []

    stats = document["stats"]
    assert stats["average_score"] == 70.0
    assert stats["answered_questions"] == 2
    assert stats["total_questions"] == 2
    assert stats["proctor_events_total"] == 3
    assert stats["violations"] == 2  # tab_switch (flag) + copy_blocked (warn)
    assert stats["weakest_question"] == {"question_number": 2, "score": 60.0}


def test_events_without_question_index_trail_the_tape():
    document = build_replay_document(
        meta=META,
        qa_pairs=_qa_pairs(),
        proctor_events=[
            {"kind": "window_blur", "detail": "blurred", "question_index": 1},
            {"kind": "screen_share_granted", "detail": "granted"},
        ],
    )
    types = [entry["type"] for entry in document["timeline"]]
    assert types == ["question", "answer", "proctor", "question", "answer", "proctor"]
    assert document["timeline"][2]["kind"] == "window_blur"
    assert document["timeline"][5]["kind"] == "screen_share_granted"


def test_severity_and_label_classification():
    assert event_severity("tab_switch") == "flag"
    assert event_severity("copy_blocked") == "warn"
    assert event_severity("screen_share_granted") == "info"
    assert event_severity("mystery_kind") == "info"
    assert event_severity(None) == "info"

    assert event_label("tab_switch") == "Tab switch detected"
    assert event_label("screen_share_wrong_surface") == "Wrong screen shared"
    assert event_label("mystery_kind") == "Mystery kind"


def test_empty_inputs_produce_minimal_document():
    document = build_replay_document(meta={}, qa_pairs=[], heatmap=None, proctor_events=None)
    assert document["version"] == 1
    assert document["timeline"] == []
    assert document["stats"]["average_score"] is None
    assert document["stats"]["proctor_events_total"] == 0
    assert document["stats"]["violations"] == 0


def test_score_parsing_tolerates_junk():
    document = build_replay_document(
        meta=META,
        qa_pairs=[
            {"question_number": 1, "question": "Q", "answer": "A", "score": "85"},
            {"question_number": 2, "question": "Q", "answer": "A", "score": "oops"},
            {"question_number": 3, "question": "Q", "answer": "A", "score": None},
        ],
    )
    scores = [entry["score"] for entry in document["timeline"] if entry["type"] == "answer"]
    assert scores == [85.0, None, None]
    assert document["stats"]["average_score"] == 85.0
    assert document["stats"]["answered_questions"] == 3


def test_segment_values_are_clamped():
    document = build_replay_document(
        meta=META,
        qa_pairs=_qa_pairs(),
        heatmap={
            "questions": [
                {
                    "question_number": 1,
                    "segments": [
                        {"text": "wild", "score": 150, "start_pct": -10, "end_pct": 200}
                    ],
                }
            ]
        },
    )
    segment = document["timeline"][1]["segments"][0]
    assert segment["score"] == 100.0
    assert segment["start_pct"] == 0.0
    assert segment["end_pct"] == 100.0


def test_deterministic_for_same_inputs():
    kwargs = {"meta": META, "qa_pairs": _qa_pairs(), "proctor_events": [
        {"kind": "tab_switch", "question_index": 1},
    ]}
    assert build_replay_document(**kwargs) == build_replay_document(**kwargs)
