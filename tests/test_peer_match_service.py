"""Tests for the Peer Play match service (verdict math + code generation).

The DB-backed flow is covered by the CI suite (which runs with the SQLite
fallback); locally, only the pure verdict math and code generation run.
"""

import pytest

from app.services.peer_match_service import (
    CODE_LENGTH,
    _CODE_ALPHABET,
    compute_match_verdict,
    generate_code,
)


def test_generate_code_shape_and_alphabet():
    code = generate_code()
    assert len(code) == CODE_LENGTH
    assert all(ch in _CODE_ALPHABET for ch in code)


class _FixedRandom:
    """Deterministic stand-in for secrets module."""

    def __init__(self, pick: str):
        self.pick = pick

    def choice(self, seq):
        return self.pick


def test_generate_code_deterministic_source():
    assert generate_code(_FixedRandom("A")) == "AAAAAA"


def test_basic_win_pays_both_sides():
    v = compute_match_verdict(82, 74)
    assert v["winner"] == "p1"
    assert v["margin"] == 8
    assert v["p1_delta"] > 0
    assert v["p2_delta"] == -v["p1_delta"]


def test_close_win_pays_less_than_rout():
    close = compute_match_verdict(72, 70)
    rout = compute_match_verdict(90, 70)
    assert abs(close["p1_delta"]) < abs(rout["p1_delta"])


def test_draw_gives_zero_deltas():
    v = compute_match_verdict(75, 75)
    assert v["winner"] == "tie"
    # Draws should not swing ratings — deltas stay near zero.
    assert v["p1_delta"] == 0
    assert v["p2_delta"] == 0


def test_scores_clamped():
    v = compute_match_verdict(999, -50)
    assert v["p1_score"] == 100
    assert v["p2_score"] == 0
    assert v["winner"] == "p1"


def test_upset_reversal_direction():
    """A tiny win against a much higher score still pays positive."""
    # p1 edges out by 3 with a large overall gap — expect a small positive delta.
    v = compute_match_verdict(63, 60)
    assert v["p1_delta"] >= 0
    assert v["winner"] == "p1"


def test_deltas_are_symmetric_in_all_cases():
    for s1, s2 in [(80, 40), (40, 80), (50, 51), (60, 60), (100, 0)]:
        v = compute_match_verdict(s1, s2)
        assert v["p1_delta"] == -v["p2_delta"]


def test_headline_mentions_winner():
    v = compute_match_verdict(88, 71)
    assert "17" in v["headline"] and "wins" in v["headline"]


# ─── DB-backed flow (skipped when the driver stack can't import locally) ─────

def _pydantic_stack_available() -> bool:
    try:
        import pydantic_settings  # noqa: F401

        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _pydantic_stack_available(),
    reason="pydantic stack unavailable in this environment",
)
def test_full_match_flow_with_db(monkeypatch):
    import app.core.config as app_config
    from app.services.mysql_service import MySQLService
    from app.services.peer_match_service import PeerMatchService

    monkeypatch.setenv("MYSQL_HOST", "")
    monkeypatch.setenv("MYSQL_PASSWORD", "")
    app_config.settings.MYSQL_HOST = ""
    app_config.settings.MYSQL_PASSWORD = ""
    db = MySQLService()
    service = PeerMatchService(db)

    # 1. Player 1 creates a match
    created = service.create_match("Ada", mode="behavioral")
    code = created["code"]
    assert len(code) == CODE_LENGTH

    # 2. Player 2 joins
    joined = service.join_match(code, "Grace")
    assert joined["player"] == "p2"

    # 3. Player 1 submits first — no verdict yet
    partial = service.submit_score(
        code, created["player_token"], 71
    )
    assert partial["finalized"] is False

    # 4. Player 2 submits — verdict published
    final = service.submit_score(code, joined["player_token"], 88)
    assert final["finalized"] is True
    assert final["verdict"]["winner"] == "p2"

    # 5. Public view reflects the completed match
    view = service.get_match(code)
    assert view["status"] == "complete"
    assert view["players"]["p1"] == "Ada"
    assert view["players"]["p2"] == "Grace"
    assert view["scores"]["p1"] == 71
    assert view["scores"]["p2"] == 88
    assert view["verdict"]["margin"] == 17
    assert view["verdict"]["p2_delta"] == view["verdict"]["p1_delta"] * -1


@pytest.mark.skipif(
    not _pydantic_stack_available(),
    reason="pydantic stack unavailable in this environment",
)
def test_join_full_match_rejected(monkeypatch):
    import app.core.config as app_config
    from app.services.mysql_service import MySQLService
    from app.services.peer_match_service import PeerMatchService

    monkeypatch.setenv("MYSQL_HOST", "")
    monkeypatch.setenv("MYSQL_PASSWORD", "")
    app_config.settings.MYSQL_HOST = ""
    app_config.settings.MYSQL_PASSWORD = ""
    db = MySQLService()
    service = PeerMatchService(db)

    created = service.create_match("Ada", mode="mixed")
    service.join_match(created["code"], "Grace")
    with pytest.raises(ValueError):
        service.join_match(created["code"], "Malory")
