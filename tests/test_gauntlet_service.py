"""Tests for The Gauntlet adaptive pressure engine.

The engine is a deterministic state machine, so every assertion below pins
exact expected values that were hand-computed from the level heuristic.
"""

from __future__ import annotations

from app.services.gauntlet_service import (
    evaluate_step,
    level_info,
    personas,
)


def test_escalates_with_interrupt_on_hot_streak():
    # avg 88 → target 5, strong streak of 3 → interrupt (odd salt).
    result = evaluate_step(
        recent_scores=[85, 88, 92],
        current_level=2,
        answered_count=3,
    )
    assert result["level"] == 5
    assert result["level_name"] == "Full Gauntlet"
    assert result["action"] == "interrupt"
    assert result["escalated"] is True
    assert result["persona"] is None
    assert result["message"]


def test_escalates_followup_on_clean_improvement():
    # avg 50 → target 2 (level holds), then a modest improvement at level 1.
    result = evaluate_step(
        recent_scores=[60, 62],
        current_level=1,
        answered_count=2,
    )
    # avg 61 → (61-30)/15 = 2.07 → target 3.
    assert result["level"] == 3
    assert result["action"] == "escalate_followup"
    assert result["escalated"] is True


def test_deescalates_when_struggling_at_elevated_level():
    # avg 41 → weak; at level 4 a cold streak pulls back to 3.
    result = evaluate_step(
        recent_scores=[40, 38, 45],
        current_level=4,
        answered_count=6,
    )
    assert result["level"] == 3
    assert result["level_name"] == "Heating Up"
    assert result["action"] == "deescalate"
    assert result["escalated"] is False


def test_stays_steady_at_low_level():
    # avg 50 → target 2 == current 2 → steady.
    result = evaluate_step(
        recent_scores=[48, 52],
        current_level=2,
        answered_count=2,
    )
    assert result["level"] == 2
    assert result["action"] == "steady"
    assert result["escalated"] is False


def test_time_pressure_when_holding_a_high_level():
    # avg 71 → target 4 == current 4; salt 9 is divisible by 3 → time pressure.
    result = evaluate_step(
        recent_scores=[70, 72],
        current_level=4,
        answered_count=9,
    )
    assert result["level"] == 4
    assert result["action"] == "time_pressure"


def test_persona_shift_on_big_jump():
    # avg 91 → target 5 from level 1 with an even salt → The Griller.
    result = evaluate_step(
        recent_scores=[90, 92],
        current_level=1,
        answered_count=4,
    )
    assert result["action"] == "persona_shift"
    assert result["persona"] is not None
    assert result["persona"]["id"] == "gauntlet_griller"
    assert result["level"] == 5


def test_level_capped_by_max_level():
    result = evaluate_step(
        recent_scores=[95, 96],
        current_level=1,
        answered_count=2,
        max_level=3,
    )
    assert result["level"] == 3
    assert result["action"] == "escalate_followup"


def test_no_evidence_stays_courteous():
    result = evaluate_step(recent_scores=[], current_level=1, answered_count=0)
    assert result["level"] == 1
    assert result["action"] == "steady"
    assert result["message"]
    assert result["evidence"]["average_score"] is None


def test_momentum_rising_keeps_heat_on():
    # avg 65 → target 3 == current 3; a rising arc with a strong recent
    # answer pushes to 4 instead of holding steady.
    rising = evaluate_step(
        recent_scores=[50, 80],
        current_level=3,
        answered_count=2,
        momentum="rising",
    )
    stable = evaluate_step(
        recent_scores=[50, 80],
        current_level=3,
        answered_count=2,
        momentum="stable",
    )
    assert rising["level"] == 4
    assert stable["level"] == 3
    assert stable["action"] == "steady"


def test_engine_is_deterministic():
    kwargs = {
        "recent_scores": [70, 85, 90, 60],
        "current_level": 2,
        "answered_count": 7,
    }
    first = evaluate_step(**kwargs)
    second = evaluate_step(**kwargs)
    assert first == second


def test_persona_pool_shape():
    pool = personas()
    assert len(pool) >= 3
    for persona in pool:
        assert {"id", "name", "emoji", "temperament"} <= set(persona)


def test_level_info_clamps():
    assert level_info(99)["level"] == 5
    assert level_info(0)["level"] == 1
    assert level_info(3)["name"] == "Heating Up"
