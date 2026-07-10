"""Lightweight plagiarism and AI-authorship heuristics for coaching feedback."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List

from app.services.rust_accelerator import get_rust_accelerator


GENERIC_RESUME_PHRASES = [
    "results-driven professional",
    "highly motivated",
    "team player",
    "detail-oriented",
    "proven track record",
    "fast-paced environment",
    "hard-working",
    "dynamic professional",
    "excellent communication skills",
    "self-starter",
]

AI_STYLE_PHRASES = [
    "in conclusion",
    "it is important to note",
    "delve into",
    "furthermore",
    "moreover",
    "additionally",
    "leveraging",
    "robust",
    "seamless",
    "multifaceted",
]

PERSONAL_EXPERIENCE_MARKERS = [
    "i built",
    "i worked",
    "i designed",
    "i improved",
    "i debugged",
    "my project",
    "my team",
    "we shipped",
    "we reduced",
    "i learned",
]


def _normalize_text(text: str) -> str:
    rust = get_rust_accelerator()
    if rust and hasattr(rust, "normalize_whitespace"):
        return rust.normalize_whitespace(text or "")
    return re.sub(r"\s+", " ", (text or "")).strip()


def _tokenize(text: str) -> List[str]:
    rust = get_rust_accelerator()
    if rust and hasattr(rust, "tokenize_words"):
        return rust.tokenize_words(text)
    return re.findall(r"[a-zA-Z0-9+#.-]+", text.lower())


def _split_sentences(text: str) -> List[str]:
    rust = get_rust_accelerator()
    if rust and hasattr(rust, "split_sentences"):
        return rust.split_sentences(text)
    return [part.strip() for part in re.split(r"[.!?\n]+", text) if part.strip()]


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _label_for_score(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _confidence_from_length(word_count: int) -> str:
    if word_count >= 80:
        return "high"
    if word_count >= 30:
        return "medium"
    return "low"


def _ngram_repetition_ratio(tokens: List[str], size: int = 3) -> float:
    if len(tokens) < size:
        return 0.0
    ngrams = [" ".join(tokens[i:i + size]) for i in range(len(tokens) - size + 1)]
    counts = Counter(ngrams)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return repeated / max(len(ngrams), 1)


def _sentence_length_variation(sentences: List[str]) -> float:
    lengths = [len(_tokenize(sentence)) for sentence in sentences if sentence.strip()]
    if len(lengths) < 2:
        return 0.0
    mean = sum(lengths) / len(lengths)
    variance = sum((length - mean) ** 2 for length in lengths) / len(lengths)
    return math.sqrt(variance)


def _matched_phrases(text: str, phrases: List[str]) -> List[str]:
    lower = text.lower()
    return [phrase for phrase in phrases if phrase in lower]


def analyze_resume_plagiarism(text: str) -> Dict[str, Any]:
    normalized = _normalize_text(text)
    tokens = _tokenize(normalized)
    sentences = _split_sentences(normalized)
    word_count = len(tokens)

    unique_ratio = len(set(tokens)) / max(word_count, 1)
    repetition_ratio = _ngram_repetition_ratio(tokens, size=3)
    generic_matches = _matched_phrases(normalized, GENERIC_RESUME_PHRASES)
    bullet_lines = [line.strip("-* ").strip() for line in text.splitlines() if line.strip().startswith(("-", "*"))]
    duplicate_bullets = len(bullet_lines) - len(set(line.lower() for line in bullet_lines))
    number_density = sum(1 for token in tokens if re.search(r"\d", token)) / max(word_count, 1)

    risk_score = 0.0
    risk_score += max(0.0, (0.45 - unique_ratio) * 120)
    risk_score += repetition_ratio * 140
    risk_score += min(len(generic_matches) * 8, 28)
    risk_score += min(duplicate_bullets * 12, 24)
    if number_density < 0.01:
        risk_score += 10

    score = round(_clamp(risk_score), 1)
    label = _label_for_score(score)

    highlights: List[str] = []
    if generic_matches:
        highlights.append("Several common resume-template phrases were detected.")
    if repetition_ratio > 0.08:
        highlights.append("Repeated wording suggests parts of the resume may be copied or over-reused.")
    if duplicate_bullets:
        highlights.append("Some bullet points are duplicated or nearly duplicated.")
    if not highlights:
        highlights.append("The resume reads fairly original and specific to the candidate.")

    suggestions: List[str] = []
    if generic_matches:
        suggestions.append("Replace generic phrases with concrete achievements, metrics, and named tools.")
    if number_density < 0.01:
        suggestions.append("Add measurable outcomes like percentages, scale, latency, or cost impact.")
    if repetition_ratio > 0.08 or duplicate_bullets:
        suggestions.append("Rewrite repeated bullet points so each one shows a distinct contribution.")
    if not suggestions:
        suggestions.append("Keep using specific project details and quantified outcomes to preserve originality.")

    return {
        "report_type": "resume_plagiarism",
        "score": score,
        "label": label,
        "confidence": _confidence_from_length(word_count),
        "summary": highlights[0],
        "highlights": highlights,
        "suggestions": suggestions[:3],
        "metrics": {
            "word_count": word_count,
            "unique_word_ratio": round(unique_ratio, 3),
            "repeated_phrase_ratio": round(repetition_ratio, 3),
            "generic_phrase_matches": generic_matches[:5],
            "duplicate_bullets": duplicate_bullets,
        },
    }


def analyze_answer_authenticity(text: str, question: str = "") -> Dict[str, Any]:
    normalized = _normalize_text(text)
    tokens = _tokenize(normalized)
    sentences = _split_sentences(normalized)
    word_count = len(tokens)
    unique_ratio = len(set(tokens)) / max(word_count, 1)
    repetition_ratio = _ngram_repetition_ratio(tokens, size=3)
    style_matches = _matched_phrases(normalized, AI_STYLE_PHRASES)
    personal_matches = _matched_phrases(normalized, PERSONAL_EXPERIENCE_MARKERS)
    sentence_variation = _sentence_length_variation(sentences)
    number_count = sum(1 for token in tokens if re.search(r"\d", token))
    question_terms = {token for token in _tokenize(question) if len(token) > 3}
    answer_terms = set(tokens)
    overlap = len(question_terms & answer_terms) / max(len(question_terms), 1)

    ai_likelihood = 0.0
    ai_likelihood += max(0.0, (0.48 - unique_ratio) * 110)
    ai_likelihood += repetition_ratio * 130
    ai_likelihood += min(len(style_matches) * 7, 28)
    if sentence_variation < 4 and len(sentences) >= 3:
        ai_likelihood += 16
    if not personal_matches:
        ai_likelihood += 12
    if number_count == 0 and word_count >= 40:
        ai_likelihood += 10
    if overlap < 0.15 and question_terms:
        ai_likelihood += 8

    score = round(_clamp(ai_likelihood), 1)
    label = _label_for_score(score)

    plagiarism_risk = score
    if number_count > 0:
        plagiarism_risk = max(0.0, plagiarism_risk - 8)
    if personal_matches:
        plagiarism_risk = max(0.0, plagiarism_risk - 12)

    highlights: List[str] = []
    if style_matches:
        highlights.append("The answer uses several polished stock phrases often seen in AI-generated text.")
    if not personal_matches:
        highlights.append("The response would feel more authentic with first-hand project details.")
    if sentence_variation < 4 and len(sentences) >= 3:
        highlights.append("Sentence lengths are very uniform, which can make the answer sound synthetic.")
    if not highlights:
        highlights.append("The answer shows signs of personal, experience-based wording.")

    suggestions: List[str] = []
    if not personal_matches:
        suggestions.append("Add what you personally built, decided, fixed, or learned.")
    if number_count == 0:
        suggestions.append("Include concrete numbers, scale, latency, users, or timeline details.")
    if style_matches or sentence_variation < 4:
        suggestions.append("Use simpler, more natural phrasing instead of polished filler transitions.")
    if overlap < 0.15 and question_terms:
        suggestions.append("Anchor the answer more directly to the exact technologies or trade-offs in the question.")

    return {
        "report_type": "answer_authenticity",
        "ai_generated_score": score,
        "ai_generated_label": label,
        "plagiarism_score": round(_clamp(plagiarism_risk), 1),
        "plagiarism_label": _label_for_score(plagiarism_risk),
        "confidence": _confidence_from_length(word_count),
        "summary": highlights[0],
        "highlights": highlights[:3],
        "suggestions": suggestions[:3],
        "metrics": {
            "word_count": word_count,
            "unique_word_ratio": round(unique_ratio, 3),
            "repeated_phrase_ratio": round(repetition_ratio, 3),
            "question_overlap_ratio": round(overlap, 3),
            "personal_experience_markers": len(personal_matches),
            "ai_style_markers": style_matches[:5],
            "numeric_detail_count": number_count,
        },
    }


def summarize_batch_authenticity(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not reports:
        return {
            "average_ai_generated_score": 0.0,
            "average_plagiarism_score": 0.0,
            "highest_risk_question": None,
            "summary": "No answers were available for authenticity analysis.",
            "suggestions": [],
        }

    avg_ai = round(sum(float(report.get("ai_generated_score", 0)) for report in reports) / len(reports), 1)
    avg_plagiarism = round(sum(float(report.get("plagiarism_score", 0)) for report in reports) / len(reports), 1)
    highest = max(reports, key=lambda report: float(report.get("ai_generated_score", 0)))

    suggestions = []
    for report in reports:
        for suggestion in report.get("suggestions", []):
            if suggestion not in suggestions:
                suggestions.append(suggestion)

    return {
        "average_ai_generated_score": avg_ai,
        "average_ai_generated_label": _label_for_score(avg_ai),
        "average_plagiarism_score": avg_plagiarism,
        "average_plagiarism_label": _label_for_score(avg_plagiarism),
        "highest_risk_question": {
            "question_number": highest.get("question_number"),
            "ai_generated_score": highest.get("ai_generated_score", 0),
            "summary": highest.get("summary", ""),
        },
        "summary": (
            "This report estimates how generic or AI-assisted the answers sound so the candidate can make them more personal and interview-ready."
        ),
        "suggestions": suggestions[:4],
    }
