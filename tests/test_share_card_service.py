"""Tests for the share-card renderer (pure service — no FastAPI needed)."""

import struct
import zlib

import pytest

from app.services.share_card_service import (
    CANVAS_H,
    CANVAS_W,
    level_for_score,
    make_embed_url,
)


def decode_png_dimensions(png_bytes: bytes) -> tuple:
    """Read the IHDR chunk to verify PNG geometry without PIL."""
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    length = struct.unpack(">I", png_bytes[8:12])[0]
    assert png_bytes[12:16] == b"IHDR"
    ihdr = png_bytes[16 : 16 + length]
    width, height = struct.unpack(">II", ihdr[:8])
    return width, height


def test_render_returns_valid_png_geometry():
    from app.services.share_card_service import render_share_card

    png = render_share_card(
        name="Ada Lovelace",
        score=87,
        grade="Interview Ready",
        tagline="Backend · Behavioral",
    )
    assert isinstance(png, bytes) and len(png) > 5000
    assert decode_png_dimensions(png) == (CANVAS_W, CANVAS_H)


def test_render_is_deterministic_for_same_inputs():
    from app.services.share_card_service import render_share_card

    first = render_share_card("Ada", 87, "Interview Ready", "")
    second = render_share_card("Ada", 87, "Interview Ready", "")
    assert zlib.crc32(first) == zlib.crc32(second)


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "No Score Yet"),
        (30, "Keep Practicing"),
        (50, "Building Up"),
        (70, "Getting Close"),
        (85, "Interview Ready"),
        (100, "Interview Ready"),
    ],
)
def test_level_for_score(score, expected):
    assert level_for_score(score) == expected


def test_level_for_score_out_of_range():
    assert level_for_score(-5) == "No Score Yet"
    assert level_for_score(300) == "No Score Yet"
    assert level_for_score("abc") == "No Score Yet"


def test_render_clamps_long_and_control_strings():
    from app.services.share_card_service import render_share_card

    png = render_share_card(
        name="A" * 200 + "\n\x0b" + "B" * 200,
        score=150,
        grade="G" * 400,
        tagline="T" * 500,
    )
    assert decode_png_dimensions(png) == (CANVAS_W, CANVAS_H)


def test_render_repo_banner_geometry_and_content():
    from app.services.share_card_service import render_repo_banner

    banner = render_repo_banner(
        title="interviewer.ai",
        subtitle="An end-to-end AI interview platform in one repo — "
        "voice interviews, RAG-grounded scoring, 7.6k-problem coding sandbox",
        feature_chips=["AI Panel", "STAR Coach", "Peer Play", "Game Tape"],
    )
    assert isinstance(banner, bytes) and len(banner) > 10000
    assert decode_png_dimensions(banner) == (CANVAS_W, CANVAS_H)

    # Long subtitle must not crash the wrap, and chips end up drawn.
    wide = render_repo_banner(
        title="interviewer.ai",
        subtitle="word " * 80,
        feature_chips=["A" * 40, "B" * 40, "C" * 40, "D" * 40, "E" * 40, "F" * 40],
    )
    assert decode_png_dimensions(wide) == (CANVAS_W, CANVAS_H)


def test_make_embed_url_encodes_parameters():
    url = make_embed_url(
        "https://api.interviewer.ai",
        "Ada Lovelace",
        87,
        "Interview Ready",
        "Backend · Behavioral",
    )
    assert url.startswith("https://api.interviewer.ai/share/card.png?")
    assert "score=87" in url
    assert " " not in url  # fully encoded
    assert "80%95" in url or "%C2%B7" in url  # the '·' separator is percent-encoded
