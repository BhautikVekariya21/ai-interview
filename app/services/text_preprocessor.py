"""
Text preprocessing pipeline for resume text.
Handles cleaning, normalization, and segmentation before NER.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.services.rust_accelerator import get_rust_accelerator


class TextPreprocessor:
    """
    Preprocess raw resume text into a normalized format suitable for NER.
    """

    UNICODE_MAP = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "\u2022",
        "\u2026": "...",
        "\u00a0": " ",
        "\uf0b7": "\u2022",
        "\uf0a7": "\u2022",
    }

    BULLET_PATTERNS = re.compile(
        r"^[\s]*[\u2022\u25cf\u25cb\u25aa\u25b8\u25ba\u27a4\u27a2\-–—\*\+>]\s*",
        re.MULTILINE,
    )

    def __init__(self):
        self._rust = get_rust_accelerator()
        logger.info("TextPreprocessor initialized")

    def preprocess(self, raw_text: str | None) -> Dict[str, Any]:
        """Run the full preprocessing pipeline."""
        if not raw_text:
            return {
                "cleaned_text": "",
                "lines": [],
                "sentences": [],
                "tokens": [],
                "line_count": 0,
                "word_count": 0,
            }

        text = self._normalize_unicode(raw_text)
        text = self._clean_artifacts(text)
        text = self._normalize_whitespace(text)
        text = self._standardize_bullets(text)

        lines = self._extract_lines(text)
        sentences = self._segment_sentences(text)
        tokens = [self._tokenize(line) for line in lines]

        result = {
            "cleaned_text": text,
            "lines": lines,
            "sentences": sentences,
            "tokens": tokens,
            "line_count": len(lines),
            "word_count": sum(len(token_list) for token_list in tokens),
        }

        logger.info(
            f"Preprocessed: {result['line_count']} lines, {result['word_count']} words"
        )
        return result

    def _normalize_unicode(self, text: str) -> str:
        if self._rust and hasattr(self._rust, "normalize_unicode"):
            return self._rust.normalize_unicode(text)

        for unicode_char, replacement in self.UNICODE_MAP.items():
            text = text.replace(unicode_char, replacement)
        return unicodedata.normalize("NFKD", text)

    def _clean_artifacts(self, text: str) -> str:
        text = re.sub(
            r"\n\s*(?:Page\s+)?\d+\s*(?:of\s+\d+)?\s*\n",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

        lines = text.split("\n")
        if len(lines) > 10:
            line_counts = Counter(line.strip() for line in lines if line.strip())
            repeated = {
                line for line, count in line_counts.items() if count >= 3 and len(line) < 80
            }
            lines = [line for line in lines if line.strip() not in repeated]
            text = "\n".join(lines)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        if self._rust and hasattr(self._rust, "normalize_whitespace"):
            return self._rust.normalize_whitespace(text)

        text = text.replace("\t", "    ")
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r" +\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _standardize_bullets(self, text: str) -> str:
        if self._rust and hasattr(self._rust, "standardize_bullets"):
            return self._rust.standardize_bullets(text)

        return self.BULLET_PATTERNS.sub("\u2022 ", text)

    def _extract_lines(self, text: str) -> List[str]:
        if self._rust and hasattr(self._rust, "extract_lines"):
            return self._rust.extract_lines(text)

        return [line.strip() for line in text.split("\n") if line.strip()]

    def _segment_sentences(self, text: str) -> List[str]:
        if self._rust and hasattr(self._rust, "split_sentences"):
            return self._rust.split_sentences(text)

        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _tokenize(self, text: str) -> List[str]:
        if self._rust and hasattr(self._rust, "tokenize_preprocessor"):
            return self._rust.tokenize_preprocessor(text)

        return re.findall(r"\b[\w+#.]+\b|[^\w\s]", text)

    def identify_potential_sections(self, lines: List[str]) -> List[Tuple[int, str, str]]:
        """Identify lines that are likely section headers."""
        from app.core.config import settings

        section_indicators: List[Tuple[int, str, str]] = []

        for index, line in enumerate(lines):
            line_clean = line.strip().lower()
            line_stripped = re.sub(r"[^a-z\s]", "", line_clean).strip()
            words = line_stripped.split()
            is_header = False
            section_type = "unknown"

            if 1 <= len(words) <= 5:
                for sec_type, keywords in settings.SECTION_KEYWORDS.items():
                    if any(keyword in line_stripped for keyword in keywords):
                        is_header = True
                        section_type = sec_type
                        break

            if (
                not is_header
                and line.strip().isupper()
                and len(words) <= 5
                and len(line.strip()) > 2
            ):
                is_header = True
                for sec_type, keywords in settings.SECTION_KEYWORDS.items():
                    if any(keyword in line_stripped for keyword in keywords):
                        section_type = sec_type
                        break

            if not is_header and line.strip().endswith(":") and len(words) <= 5:
                is_header = True
                for sec_type, keywords in settings.SECTION_KEYWORDS.items():
                    if any(keyword in line_stripped for keyword in keywords):
                        section_type = sec_type
                        break

            if is_header:
                section_indicators.append((index, line.strip(), section_type))

        logger.debug(f"Identified {len(section_indicators)} potential sections")
        return section_indicators
