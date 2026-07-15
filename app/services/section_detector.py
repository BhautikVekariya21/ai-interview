"""
Section detection service.
Identifies and segments resume sections using heuristics
and a lightweight PyTorch classifier.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

try:
    import torch
    from torch import nn
    HAS_TORCH = True
except Exception as import_error:  # pragma: no cover - env dependent
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    HAS_TORCH = False
    logger.warning(
        "PyTorch unavailable for section classifier; "
        "using heuristic section detection only. "
        f"Import error: {import_error}"
    )

from app.core.config import settings


class SectionDetector:
    """
    Detects and classifies resume sections.
    Uses a combination of:
    1. Keyword matching
    2. Formatting heuristics (caps, colons, short lines)
    3. A small PyTorch classifier for ambiguous sections
    """

    SECTION_TYPES = [
        "personal", "education", "experience", "skills",
        "projects", "certifications", "publications",
        "achievements", "summary", "unknown",
    ]

    def __init__(self):
        self.section_classifier: Optional[nn.Module] = None if nn is not None else None
        self.device = "cpu"
        self._build_section_classifier()
        logger.info("SectionDetector initialized")

    def _build_section_classifier(self):
        if not HAS_TORCH or torch is None or nn is None:
            return

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        num_features = len(settings.SECTION_KEYWORDS) + 5
        self.section_classifier = nn.Sequential(
            nn.Linear(num_features, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, len(self.SECTION_TYPES)),
        ).to(self.device)
        self._train_section_classifier()

    def _train_section_classifier(self):
        if self.section_classifier is None or torch is None or nn is None:
            return

        x_train = []
        y_train = []
        for sec_idx, sec_type in enumerate(self.SECTION_TYPES):
            keywords = settings.SECTION_KEYWORDS.get(sec_type, [])
            for keyword in keywords:
                for variant in [
                    keyword,
                    keyword.upper(),
                    keyword.title(),
                    f"{keyword}:",
                    f"{keyword.upper()}:",
                ]:
                    x_train.append(self._extract_header_features(variant))
                    y_train.append(sec_idx)

        if not x_train:
            return

        features = torch.as_tensor(
            np.array(x_train, dtype=np.float32),
            dtype=torch.float32,
            device=self.device,
        )
        labels = torch.as_tensor(
            np.array(y_train, dtype=np.int64),
            dtype=torch.long,
            device=self.device,
        )

        optimizer = torch.optim.Adam(self.section_classifier.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        for _ in range(20):
            self.section_classifier.train()
            optimizer.zero_grad()
            logits = self.section_classifier(features)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

        self.section_classifier.eval()
        logger.debug("Section classifier trained")

    def _extract_header_features(self, line: str) -> np.ndarray:
        line_clean = line.strip().lower()
        line_stripped = re.sub(r"[^a-z\s]", "", line_clean).strip()
        features = []

        for _, keywords in settings.SECTION_KEYWORDS.items():
            match_score = (
                max((1.0 if kw in line_stripped else 0.0) for kw in keywords)
                if keywords
                else 0.0
            )
            features.append(match_score)

        features.append(1.0 if line.strip().isupper() else 0.0)
        features.append(1.0 if line.strip().endswith(":") else 0.0)
        features.append(min(len(line.strip().split()) / 5.0, 1.0))
        features.append(min(len(line.strip()) / 50.0, 1.0))
        features.append(1.0 if re.match(r"^[A-Z\s:&\-/]+$", line.strip()) else 0.0)
        return np.array(features, dtype=np.float32)

    def detect_sections(self, lines: List[str]) -> List[Dict]:
        if not lines:
            return []

        header_candidates = []
        for i, line in enumerate(lines):
            score, sec_type = self._score_as_header(line)
            if score > 0.5:
                header_candidates.append(
                    {
                        "line_idx": i,
                        "text": line.strip(),
                        "section_type": sec_type,
                        "score": score,
                    }
                )

        if not header_candidates:
            logger.warning("No section headers detected")
            return [{
                "type": "unknown",
                "start_line": 0,
                "end_line": len(lines) - 1,
                "header": "",
                "content_lines": lines,
                "confidence": 0.3,
            }]

        sections = []
        for i, header in enumerate(header_candidates):
            start = header["line_idx"]
            end = (
                header_candidates[i + 1]["line_idx"] - 1
                if i + 1 < len(header_candidates)
                else len(lines) - 1
            )
            sections.append(
                {
                    "type": header["section_type"],
                    "start_line": start,
                    "end_line": end,
                    "header": header["text"],
                    "content_lines": lines[start + 1: end + 1],
                    "confidence": header["score"],
                }
            )

        if header_candidates[0]["line_idx"] > 0:
            sections.insert(
                0,
                {
                    "type": "personal",
                    "start_line": 0,
                    "end_line": header_candidates[0]["line_idx"] - 1,
                    "header": "",
                    "content_lines": lines[: header_candidates[0]["line_idx"]],
                    "confidence": 0.7,
                },
            )

        logger.info(f"Detected {len(sections)} sections: {[s['type'] for s in sections]}")
        return sections

    def _score_as_header(self, line: str) -> Tuple[float, str]:
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) > 80:
            return 0.0, "unknown"

        words = line_stripped.split()
        if len(words) > 6:
            return 0.0, "unknown"

        # Content lines (cert entries, awards, project bullets) often contain a
        # keyword but also a year/date or trailing description. Real section
        # headers almost never carry a 4-digit year or end with punctuation like
        # a comma/period followed by more text. Reject those so entries such as
        # "AWS Certified Solutions Architect - 2022" are not treated as headers.
        if re.search(r"\b(19|20)\d{2}\b", line_stripped):
            return 0.0, "unknown"
        if re.search(r"[,.](?:\s|$)", line_stripped) and not line_stripped.endswith(":"):
            return 0.0, "unknown"

        line_alpha = re.sub(r"[^a-z\s]", "", line_stripped.lower()).strip()
        best_score = 0.0
        best_type = "unknown"

        for sec_type, keywords in settings.SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw in line_alpha:
                    score = 0.6
                    if line_stripped.isupper():
                        score += 0.15
                    if line_stripped.endswith(":"):
                        score += 0.1
                    if len(words) <= 3:
                        score += 0.1
                    if re.match(r"^[A-Z]", line_stripped):
                        score += 0.05
                    if score > best_score:
                        best_score = score
                        best_type = sec_type

        if 0.4 < best_score < 0.7 and self.section_classifier is not None and torch is not None:
            features = torch.as_tensor(
                self._extract_header_features(line_stripped)[None, :],
                dtype=torch.float32,
                device=self.device,
            )
            self.section_classifier.eval()
            with torch.no_grad():
                probs = torch.softmax(self.section_classifier(features), dim=1)[0]
            cls_idx = int(torch.argmax(probs).item())
            cls_confidence = float(probs[cls_idx].item())
            if cls_confidence > 0.6:
                best_type = self.SECTION_TYPES[cls_idx]
                best_score = max(best_score, cls_confidence)

        return min(best_score, 1.0), best_type
