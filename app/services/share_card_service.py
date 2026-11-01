"""
Share Card Renderer — service.

Pure Pillow rendering of a 1200×630 interview scorecard PNG (open-graph
size) for social sharing. No FastAPI import here, so the renderer is
directly testable without the HTTP layer (useful for local, CI, and a
future CLI/Streamlit share flow).
"""

from __future__ import annotations

import math
import os
import re
import sys
from io import BytesIO
from typing import Any, List, Optional, Tuple

from loguru import logger

CANVAS_W = 1200
CANVAS_H = 630

_SCORE_LEVELS: List[Tuple[int, str]] = [
    (85, "Interview Ready"),
    (70, "Getting Close"),
    (50, "Building Up"),
    (1, "Keep Practicing"),
    (0, "No Score Yet"),
]


def _clamp_text(value: Optional[str], max_len: int, fallback: str = "") -> str:
    """Strip control characters and cap the length of user-provided text."""
    if not value:
        return fallback
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", str(value)).strip()
    return cleaned[:max_len]


def level_for_score(score: int) -> str:
    """Map a 0-100 score to a friendly label shown on the card."""
    try:
        value = int(score)
    except (TypeError, ValueError):
        return "No Score Yet"
    if 0 <= value <= 100:
        for threshold, label in _SCORE_LEVELS:
            if value >= threshold:
                return label
    return "No Score Yet"


def _load_font(size: int, bold: bool = False) -> Any:
    """Load the best TrueType font available; fall back to PIL's default."""
    names = (
        ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"]
        if bold
        else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
    )
    roots = [
        os.path.join(sys.prefix, "Fonts"),
        "/usr/share/fonts/truetype/dejavu",
        "/System/Library/Fonts",
        "C:/Windows/Fonts",
    ]
    for name in names:
        for root in roots:
            path = os.path.join(root, name)
            try:
                if os.path.exists(path):
                    from PIL import ImageFont

                    return ImageFont.truetype(path, size=size)
            except Exception:  # noqa: BLE001 - font loading is best-effort
                continue
    from PIL import ImageFont

    return ImageFont.load_default()


def _draw_backdrop(image: Any) -> None:
    """Aurora-style gradient: deep slate → indigo with a soft violet glow."""
    from PIL import ImageDraw

    top = (15, 23, 42)      # slate-900
    mid = (30, 41, 59)      # slate-800
    bottom = (49, 46, 129)  # indigo-900
    draw = ImageDraw.Draw(image)
    for y in range(CANVAS_H):
        t = y / (CANVAS_H - 1)
        if t < 0.55:
            tt = t / 0.55
        else:
            tt = (t - 0.55) / 0.45
        if t < 0.55:
            r = top[0] + (mid[0] - top[0]) * tt
            g = top[1] + (mid[1] - top[1]) * tt
            b = top[2] + (mid[2] - top[2]) * tt
        else:
            r = mid[0] + (bottom[0] - mid[0]) * tt
            g = mid[1] + (bottom[1] - mid[1]) * tt
            b = mid[2] + (bottom[2] - mid[2]) * tt
        draw.line([(0, y), (CANVAS_W, y)], fill=(int(r), int(g), int(b)))

    try:
        from PIL import ImageFilter

        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.ellipse(
            [CANVAS_W - 380, -260, CANVAS_W + 180, 220],
            fill=(139, 92, 246, 70),
        )
        ov_draw.ellipse(
            [-260, CANVAS_H - 300, 260, CANVAS_H + 140],
            fill=(56, 189, 248, 55),
        )
        overlay = overlay.filter(ImageFilter.GaussianBlur(90))
        image.paste(overlay, (0, 0), overlay)
    except Exception:  # pragma: no cover - cosmetics only
        pass


def render_share_card(
    name: str,
    score: int,
    grade: str,
    tagline: str,
    brand: str = "interviewer.ai",
) -> bytes:
    """Render a 1200×630 result card PNG and return its bytes.

    Pure function of its inputs so routes and tests can share it.
    """
    from PIL import Image, ImageDraw

    name = _clamp_text(name, 40, "Candidate") or "Candidate"
    grade = _clamp_text(grade, 24, "") or level_for_score(score)
    tagline = _clamp_text(tagline, 70, "")
    brand = _clamp_text(brand, 30, "interviewer.ai") or "interviewer.ai"
    score = int(max(0, min(100, int(score))))

    image = Image.new("RGB", (CANVAS_W, CANVAS_H), (15, 23, 42))
    _draw_backdrop(image)
    draw = ImageDraw.Draw(image)

    font_brand = _load_font(26)
    font_name = _load_font(64, bold=True)
    font_score = _load_font(190, bold=True)
    font_label = _load_font(40, bold=True)
    font_tag = _load_font(28)

    accent = (167, 139, 250)   # violet-400
    text_main = (241, 245, 249)
    text_dim = (148, 163, 184)

    # Brand chip
    chip_w = 14 * len(brand) + 40
    draw.rounded_rectangle(
        [56, 48, 56 + chip_w, 104],
        radius=28,
        fill=(30, 27, 75),
        outline=accent,
        width=2,
    )
    draw.text((76, 58), brand, font=font_brand, fill=accent)

    # Tagline under the brand chip
    if tagline:
        draw.text((58, 130), tagline, font=font_tag, fill=text_dim)

    # Candidate name
    draw.text((56, 170), name, font=font_name, fill=text_main)

    # Big score with a progress bar
    draw.text((56, 300), str(score), font=font_score, fill=text_main)
    draw.text((56 + 340, 380), "/ 100", font=font_label, fill=text_dim)

    bar_y = 520
    bar_h = 18
    draw.rounded_rectangle(
        [56, bar_y, CANVAS_W - 56, bar_y + bar_h],
        radius=bar_h // 2,
        fill=(51, 65, 85),
    )
    fill_w = max(int((CANVAS_W - 112) * (score / 100)), 24)
    draw.rounded_rectangle(
        [56, bar_y, 56 + fill_w, bar_y + bar_h],
        radius=bar_h // 2,
        fill=accent,
    )

    # Grade sits right after the bar fill
    draw.text(
        (56 + fill_w + 24, bar_y - 64),
        grade,
        font=font_label,
        fill=accent,
    )

    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_repo_banner(
    title: str,
    subtitle: str,
    feature_chips: List[str],
    brand: str = "interviewer.ai",
) -> bytes:
    """Render the 1200×630 repo hero banner (README / og:image) in brand style.

    Same aurora backdrop as scorecards, but text-first: title, one-line
    subtitle, and a row of feature chips. Pure function of its inputs.
    """
    from PIL import Image, ImageDraw

    title = _clamp_text(title, 30, "interviewer.ai") or "interviewer.ai"
    subtitle = _clamp_text(subtitle, 180, "")
    brand = _clamp_text(brand, 30, "interviewer.ai") or "interviewer.ai"
    chips = [_clamp_text(c, 26) for c in feature_chips][:4]
    chips = [c for c in chips if c]

    image = Image.new("RGB", (CANVAS_W, CANVAS_H), (15, 23, 42))
    _draw_backdrop(image)
    draw = ImageDraw.Draw(image)

    font_brand = _load_font(26)
    font_title = _load_font(96, bold=True)
    font_sub = _load_font(30)
    font_chip = _load_font(24, bold=True)

    accent = (167, 139, 250)
    text_main = (241, 245, 249)
    text_dim = (148, 163, 184)

    # Brand chip
    chip_w = 14 * len(brand) + 40
    draw.rounded_rectangle(
        [56, 56, 56 + chip_w, 112], radius=28, fill=(30, 27, 75), outline=accent, width=2
    )
    draw.text((76, 66), brand, font=font_brand, fill=accent)

    # Title + subtitle (subtitle wraps to at most 2 fitting lines)
    draw.text((56, 190), title, font=font_title, fill=text_main)
    if subtitle:
        words = subtitle.split()
        lines: List[str] = []
        current = ""
        max_w = CANVAS_W - 120
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and draw.textlength(candidate, font=font_sub) > max_w:
                lines.append(current)
                current = word
                if len(lines) == 2:
                    break
            else:
                current = candidate
        if current and len(lines) < 2:
            lines.append(current)
        for line_no, line in enumerate(lines[:2]):
            draw.text((60, 320 + line_no * 44), line, font=font_sub, fill=text_dim)

    # Feature chip row
    x = 56
    chip_y = 420
    for chip in chips:
        w = int(draw.textlength(chip, font=font_chip)) + 44
        draw.rounded_rectangle(
            [x, chip_y, x + w, chip_y + 56], radius=28, fill=(30, 41, 59), outline=accent, width=2
        )
        draw.text((x + 22, chip_y + 14), chip, font=font_chip, fill=text_main)
        x += w + 18

    # Footer tag
    foot = "End-to-end AI interview platform · FastAPI + React + RAG + MLflow/DVC"
    draw.text((60, 562), foot, font=_load_font(22), fill=(99, 102, 241))

    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def make_embed_url(base_url: str, name: str, score: int, grade: str, tagline: str) -> str:
    """Build the public card.png URL for frontend `og:image` tags."""
    from urllib.parse import quote

    params = "&".join(
        f"{key}={quote(str(val), safe='')}"
        for key, val in (
            ("name", name),
            ("score", score),
            ("grade", grade),
            ("tagline", tagline),
        )
    )
    return f"{base_url.rstrip('/')}/share/card.png?{params}"


logger.debug("Share card renderer loaded")
