"""
Module 12 — AI Confidence Pulse: Speech Intelligence Analyzer.

Analyzes interview answers to produce a comprehensive speech intelligence
report covering confidence trajectory, filler words, vocabulary richness,
speaking pace, response momentum, and personalized coaching.

This is a UNIQUE feature — no competitor platform offers this.
"""

import re
import math
from typing import Dict, Any, Optional, List
from loguru import logger

from app.services.filler_word_detector import get_filler_detector


# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Hedging / uncertainty markers
HEDGE_WORDS = [
    r"\bmaybe\b", r"\bperhaps\b", r"\bpossibly\b", r"\bi think\b",
    r"\bi guess\b", r"\bprobably\b", r"\bnot sure\b", r"\bkind of\b",
    r"\bsort of\b", r"\bmight\b", r"\bcould be\b", r"\bi believe\b",
    r"\bdon'?t know\b", r"\bnot certain\b",
]

# Confidence / assertion markers
ASSERTION_WORDS = [
    r"\bdefinitely\b", r"\bcertainly\b", r"\babsolutely\b",
    r"\bwithout a doubt\b", r"\bi am confident\b", r"\bclearly\b",
    r"\bin my experience\b", r"\bi have\b", r"\bi built\b",
    r"\bi led\b", r"\bi designed\b", r"\bi implemented\b",
    r"\bspecifically\b", r"\bfor example\b", r"\bthe result was\b",
    r"\bthe outcome\b", r"\bsuccessfully\b", r"\bachieved\b",
]

# Technical depth markers
TECHNICAL_MARKERS = [
    r"\bapi\b", r"\bdatabase\b", r"\barchitecture\b", r"\bscalability\b",
    r"\blatency\b", r"\bthroughput\b", r"\bcache\b", r"\bindex\b",
    r"\boptimiz\w*\b", r"\balgorithm\b", r"\bcomplexity\b",
    r"\bdeployment\b", r"\bcontainer\b", r"\bmicroservice\b",
    r"\bpipeline\b", r"\bci/cd\b", r"\btesting\b", r"\bmonitoring\b",
    r"\btrade-?off\b", r"\bfailover\b", r"\brollback\b",
]

# Ideal speaking pace (WPM) bounds
PACE_TOO_SLOW = 100
PACE_IDEAL_LOW = 120
PACE_IDEAL_HIGH = 160
PACE_TOO_FAST = 180

# Average reading/speaking time per question (seconds) — used for WPM estimation
AVG_ANSWER_DURATION_SECONDS = 90


class ConfidenceAnalyzer:
    """
    Analyzes interview answers to produce a speech intelligence report.
    No ML models required — works purely on text analysis of existing answers.
    """

    def __init__(self):
        self._filler_detector = get_filler_detector()
        self._hedge_patterns = [re.compile(p, re.IGNORECASE) for p in HEDGE_WORDS]
        self._assertion_patterns = [re.compile(p, re.IGNORECASE) for p in ASSERTION_WORDS]
        self._technical_patterns = [re.compile(p, re.IGNORECASE) for p in TECHNICAL_MARKERS]
        logger.info("  ✓ Confidence Analyzer (Module 12) initialized")

    def analyze(
        self,
        qa_pairs: List[Dict[str, Any]],
        interview_duration_seconds: int = 0,
    ) -> Dict[str, Any]:
        """
        Analyze all Q&A pairs and produce a speech intelligence report.

        Args:
            qa_pairs: List of {question, answer, category, question_number}
            interview_duration_seconds: Total interview duration for pace calc

        Returns:
            Full confidence pulse report
        """
        if not qa_pairs:
            return self._empty_report()

        per_question: List[Dict[str, Any]] = []
        all_answers_text = ""
        total_words = 0
        total_fillers = 0
        all_filler_breakdown: Dict[str, int] = {}

        for i, qa in enumerate(qa_pairs):
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            category = qa.get("category", "T")
            q_num = qa.get("question_number", i + 1)

            # Skip unanswered / skipped
            if not answer or answer.strip().upper() in ["[SKIPPED]", ""]:
                per_question.append({
                    "question_number": q_num,
                    "confidence_score": 0,
                    "word_count": 0,
                    "filler_count": 0,
                    "filler_percentage": 0,
                    "vocab_richness": 0,
                    "hedge_count": 0,
                    "assertion_count": 0,
                    "technical_density": 0,
                    "estimated_wpm": 0,
                    "skipped": True,
                })
                continue

            analysis = self._analyze_single_answer(answer, category, q_num)
            per_question.append(analysis)

            all_answers_text += " " + answer
            total_words += analysis["word_count"]
            total_fillers += analysis["filler_count"]

            # Aggregate filler breakdown
            for word, count in analysis.get("filler_breakdown", {}).items():
                all_filler_breakdown[word] = all_filler_breakdown.get(word, 0) + count

        # ── Overall metrics ──────────────────────────────────
        answered = [q for q in per_question if not q.get("skipped")]
        num_answered = len(answered)

        # Overall confidence
        overall_confidence = 0
        if num_answered > 0:
            overall_confidence = round(
                sum(q["confidence_score"] for q in answered) / num_answered, 1
            )

        # Overall vocab richness
        overall_vocab = self._calc_vocab_richness(all_answers_text) if all_answers_text.strip() else 0

        # Overall WPM
        if interview_duration_seconds > 0:
            overall_wpm = round(total_words / (interview_duration_seconds / 60))
        elif num_answered > 0:
            overall_wpm = round(total_words / (num_answered * AVG_ANSWER_DURATION_SECONDS / 60))
        else:
            overall_wpm = 0

        # Overall filler percentage
        overall_filler_pct = round((total_fillers / total_words * 100), 1) if total_words > 0 else 0

        # Momentum — trend of confidence across questions
        momentum = self._calc_momentum(answered)

        # Confidence trajectory — array of scores for charting
        trajectory = [q["confidence_score"] for q in per_question]

        # Pace assessment
        pace_label = self._pace_label(overall_wpm)

        # Top filler words (sorted by count)
        top_fillers = sorted(all_filler_breakdown.items(), key=lambda x: x[1], reverse=True)[:6]

        # AI coaching tips
        coaching = self._generate_coaching(
            overall_confidence=overall_confidence,
            overall_wpm=overall_wpm,
            overall_filler_pct=overall_filler_pct,
            overall_vocab=overall_vocab,
            momentum=momentum,
            top_fillers=top_fillers,
            per_question=per_question,
        )

        # Confidence label
        confidence_label = self._confidence_label(overall_confidence)

        return {
            "success": True,
            "overall": {
                "confidence_score": overall_confidence,
                "confidence_label": confidence_label,
                "vocabulary_richness": overall_vocab,
                "speaking_pace_wpm": overall_wpm,
                "pace_label": pace_label,
                "filler_percentage": overall_filler_pct,
                "total_fillers": total_fillers,
                "total_words": total_words,
                "momentum": momentum,
                "questions_answered": num_answered,
                "questions_total": len(per_question),
            },
            "trajectory": trajectory,
            "per_question": per_question,
            "filler_breakdown": [
                {"word": w, "count": c} for w, c in top_fillers
            ],
            "coaching": coaching,
        }

    def analyze_heatmap(self, qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Break each answer into sentence-level segments and score each one,
        so users can see *where inside an answer* their confidence dipped.

        Segment position is expressed as start_pct/end_pct (0-1) along the
        answer, proportional to cumulative word count — we don't have real
        audio timestamps, so this is a text-proportional stand-in for a
        timeline, not wall-clock time.
        """
        results: List[Dict[str, Any]] = []

        for i, qa in enumerate(qa_pairs):
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            category = qa.get("category", "T")
            q_num = qa.get("question_number", i + 1)

            if not answer or answer.strip().upper() in ["[SKIPPED]", ""]:
                results.append({
                    "question_number": q_num,
                    "question": question,
                    "segments": [],
                    "weakest_segment_index": None,
                    "skipped": True,
                })
                continue

            sentences = self._segment_answer_text(answer)
            total_words = sum(len(s.split()) for s in sentences) or 1

            segments: List[Dict[str, Any]] = []
            cumulative_words = 0
            for sentence in sentences:
                seg_analysis = self._analyze_single_answer(sentence, category, q_num)
                word_count = seg_analysis["word_count"]
                start_pct = round(cumulative_words / total_words, 4)
                cumulative_words += word_count
                end_pct = round(cumulative_words / total_words, 4)

                flags: List[str] = []
                if seg_analysis["hedge_count"] > 0:
                    flags.append("hedge")
                if seg_analysis["filler_percentage"] > 10:
                    flags.append("filler_spike")
                if seg_analysis["confidence_score"] < 40:
                    flags.append("low_confidence")

                segments.append({
                    "text": sentence,
                    "score": seg_analysis["confidence_score"],
                    "start_pct": start_pct,
                    "end_pct": end_pct,
                    "filler_words": list(seg_analysis["filler_breakdown"].keys()),
                    "flags": flags,
                })

            weakest_index = None
            if segments:
                weakest_index = min(range(len(segments)), key=lambda idx: segments[idx]["score"])

            results.append({
                "question_number": q_num,
                "question": question,
                "segments": segments,
                "weakest_segment_index": weakest_index,
                "skipped": False,
            })

        return results

    def _segment_answer_text(self, text: str) -> List[str]:
        """Split an answer into sentence-level segments for heatmap scoring."""
        raw_segments = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in raw_segments if s.strip()]

    def _analyze_single_answer(
        self, answer: str, category: str, q_num: int
    ) -> Dict[str, Any]:
        """Analyze a single answer for all speech intelligence metrics."""
        words = answer.split()
        word_count = len(words)
        lower = answer.lower()

        # Filler words (reuse existing service)
        filler_analysis = self._filler_detector.analyze(answer)
        filler_count = filler_analysis.total_fillers
        filler_pct = round(filler_analysis.filler_percentage, 1)
        filler_breakdown = {
            fw.word: fw.count for fw in filler_analysis.filler_words
        }

        # Hedging markers
        hedge_count = sum(
            len(p.findall(lower)) for p in self._hedge_patterns
        )

        # Assertion markers
        assertion_count = sum(
            len(p.findall(lower)) for p in self._assertion_patterns
        )

        # Technical density
        tech_count = sum(
            len(p.findall(lower)) for p in self._technical_patterns
        )
        technical_density = round((tech_count / max(word_count, 1)) * 100, 1)

        # Vocabulary richness (TTR — Type Token Ratio)
        vocab_richness = self._calc_vocab_richness(answer)

        # Estimated WPM (based on avg answer duration)
        estimated_wpm = round(word_count / (AVG_ANSWER_DURATION_SECONDS / 60))

        # ── Confidence score (composite) ──────────────────────
        # Higher is better (0-100)
        confidence = self._calc_confidence_score(
            word_count=word_count,
            filler_pct=filler_pct,
            hedge_count=hedge_count,
            assertion_count=assertion_count,
            technical_density=technical_density,
            vocab_richness=vocab_richness,
            category=category,
        )

        return {
            "question_number": q_num,
            "confidence_score": confidence,
            "word_count": word_count,
            "filler_count": filler_count,
            "filler_percentage": filler_pct,
            "filler_breakdown": filler_breakdown,
            "vocab_richness": vocab_richness,
            "hedge_count": hedge_count,
            "assertion_count": assertion_count,
            "technical_density": technical_density,
            "estimated_wpm": estimated_wpm,
            "skipped": False,
        }

    def _calc_vocab_richness(self, text: str) -> float:
        """Type-Token Ratio — unique words / total words (0-100 scale)."""
        words = re.findall(r"[a-zA-Z]+", text.lower())
        if len(words) < 5:
            return 0
        unique = len(set(words))
        # TTR naturally decreases with longer texts, so use root TTR
        root_ttr = unique / math.sqrt(len(words))
        # Normalize to 0-100 (root TTR typically ranges 3-15)
        score = min(100, max(0, round((root_ttr / 12) * 100, 1)))
        return score

    def _calc_confidence_score(
        self,
        word_count: int,
        filler_pct: float,
        hedge_count: int,
        assertion_count: int,
        technical_density: float,
        vocab_richness: float,
        category: str,
    ) -> int:
        """
        Compute confidence from multiple signals.
        Returns 0-100.
        """
        score = 50.0  # Base

        # Length bonus (up to +15)
        if word_count >= 80:
            score += 15
        elif word_count >= 40:
            score += 10
        elif word_count >= 20:
            score += 5
        elif word_count < 10:
            score -= 15

        # Filler penalty (up to -20)
        if filler_pct > 10:
            score -= 20
        elif filler_pct > 5:
            score -= 12
        elif filler_pct > 2:
            score -= 5

        # Hedging penalty (up to -15)
        hedge_norm = min(hedge_count, 5)
        score -= hedge_norm * 3

        # Assertion bonus (up to +15)
        assertion_norm = min(assertion_count, 5)
        score += assertion_norm * 3

        # Technical depth bonus (up to +10)
        if category in ("T", "C"):
            if technical_density > 3:
                score += 10
            elif technical_density > 1.5:
                score += 5

        # Vocab richness bonus (up to +10)
        if vocab_richness > 60:
            score += 10
        elif vocab_richness > 40:
            score += 5

        return int(max(0, min(100, round(score))))

    def _calc_momentum(self, answered: List[Dict[str, Any]]) -> str:
        """
        Determine if confidence is trending up, stable, or down.
        """
        if len(answered) < 3:
            return "stable"

        # Compare first half avg to second half avg
        mid = len(answered) // 2
        first_half = [q["confidence_score"] for q in answered[:mid]]
        second_half = [q["confidence_score"] for q in answered[mid:]]

        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        diff = avg_second - avg_first
        if diff > 8:
            return "rising"
        elif diff < -8:
            return "declining"
        return "stable"

    def _pace_label(self, wpm: int) -> str:
        if wpm == 0:
            return "unknown"
        if wpm < PACE_TOO_SLOW:
            return "too_slow"
        if wpm < PACE_IDEAL_LOW:
            return "slightly_slow"
        if wpm <= PACE_IDEAL_HIGH:
            return "ideal"
        if wpm <= PACE_TOO_FAST:
            return "slightly_fast"
        return "too_fast"

    def _confidence_label(self, score: float) -> str:
        if score >= 85:
            return "Very Confident"
        if score >= 70:
            return "Confident"
        if score >= 55:
            return "Moderate"
        if score >= 40:
            return "Somewhat Uncertain"
        return "Needs Practice"

    def _generate_coaching(
        self,
        overall_confidence: float,
        overall_wpm: int,
        overall_filler_pct: float,
        overall_vocab: float,
        momentum: str,
        top_fillers: List[tuple],
        per_question: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Generate personalized AI coaching tips based on analysis."""
        tips: List[Dict[str, str]] = []

        # Confidence tips
        if overall_confidence >= 80:
            tips.append({
                "category": "confidence",
                "icon": "trophy",
                "title": "Excellent Confidence",
                "tip": "You communicate with strong conviction and authority. Your assertive language and structured responses project professionalism.",
            })
        elif overall_confidence >= 60:
            tips.append({
                "category": "confidence",
                "icon": "trending_up",
                "title": "Good Foundation",
                "tip": "You show solid confidence overall. To reach the next level, replace hedging phrases like 'I think' or 'maybe' with definitive statements backed by examples.",
            })
        else:
            tips.append({
                "category": "confidence",
                "icon": "lightbulb",
                "title": "Build Your Confidence",
                "tip": "Practice the 'Claim → Evidence → Impact' framework: make a clear claim, back it with a specific example, and explain the outcome. This structure projects confidence naturally.",
            })

        # Filler word tips
        if overall_filler_pct > 5:
            top_word = top_fillers[0][0] if top_fillers else "um"
            tips.append({
                "category": "fillers",
                "icon": "mic_off",
                "title": "Reduce Filler Words",
                "tip": f"Your most frequent filler is \"{top_word}\". Try the 'Power Pause' technique: instead of filling silence, pause for 1-2 seconds. Recruiters perceive purposeful silence as thoughtfulness.",
            })
        elif overall_filler_pct > 2:
            tips.append({
                "category": "fillers",
                "icon": "check",
                "title": "Minimal Filler Usage",
                "tip": "Your filler word usage is within acceptable range. Keep practicing — being aware of them is half the battle.",
            })
        else:
            tips.append({
                "category": "fillers",
                "icon": "star",
                "title": "Clean Speech",
                "tip": "Excellent! You use virtually no filler words. Your speech comes across as polished and prepared.",
            })

        # Pace tips
        if overall_wpm > PACE_TOO_FAST:
            tips.append({
                "category": "pace",
                "icon": "slow_down",
                "title": "Slow Down a Bit",
                "tip": "You're speaking quite fast — a sign of nerves. Aim for 130-150 WPM. Try taking a breath between key points to let your answers land better.",
            })
        elif overall_wpm < PACE_TOO_SLOW and overall_wpm > 0:
            tips.append({
                "category": "pace",
                "icon": "speed_up",
                "title": "Pick Up the Pace",
                "tip": "Your answers are quite brief or slow. Practice expanding with the 'What → How → Why' framework: explain what you did, how you did it, and why it mattered.",
            })
        else:
            tips.append({
                "category": "pace",
                "icon": "check_circle",
                "title": "Great Speaking Pace",
                "tip": "Your speaking pace is within the ideal 120-160 WPM range — communicating clearly without rushing.",
            })

        # Vocabulary tips
        if overall_vocab < 35:
            tips.append({
                "category": "vocabulary",
                "icon": "book",
                "title": "Expand Your Vocabulary",
                "tip": "Try to use more varied terminology. Instead of repeating the same words, use synonyms and domain-specific vocabulary to demonstrate deeper expertise.",
            })
        elif overall_vocab > 60:
            tips.append({
                "category": "vocabulary",
                "icon": "sparkles",
                "title": "Rich Vocabulary",
                "tip": "You use diverse, sophisticated vocabulary — a strong sign of expertise. Keep it up!",
            })

        # Momentum tips
        if momentum == "declining":
            tips.append({
                "category": "momentum",
                "icon": "battery_low",
                "title": "Watch for Fatigue",
                "tip": "Your confidence dipped in later questions — common interview fatigue. Try energy management: take micro-pauses, sit up straight, and treat each question as a fresh start.",
            })
        elif momentum == "rising":
            tips.append({
                "category": "momentum",
                "icon": "rocket",
                "title": "Strong Finish",
                "tip": "Your confidence grew throughout the interview — you gained momentum as you warmed up. Great adaptability!",
            })

        return tips

    def _empty_report(self) -> Dict[str, Any]:
        """Return an empty report for edge cases."""
        return {
            "success": True,
            "overall": {
                "confidence_score": 0,
                "confidence_label": "No Data",
                "vocabulary_richness": 0,
                "speaking_pace_wpm": 0,
                "pace_label": "unknown",
                "filler_percentage": 0,
                "total_fillers": 0,
                "total_words": 0,
                "momentum": "stable",
                "questions_answered": 0,
                "questions_total": 0,
            },
            "trajectory": [],
            "per_question": [],
            "filler_breakdown": [],
            "coaching": [],
        }


# ── Singleton ─────────────────────────────────────────────────
_analyzer: Optional[ConfidenceAnalyzer] = None


def get_confidence_analyzer() -> ConfidenceAnalyzer:
    """Get singleton ConfidenceAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ConfidenceAnalyzer()
    return _analyzer
