"""
Language detection from resume text.
Stretch goal: detect candidate's language and respond accordingly.
Uses langdetect library with heuristic fallback.
"""

import re
from typing import Tuple, Dict, List
from loguru import logger


# Human-readable language names
LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English", "es": "Spanish", "fr": "French",
    "de": "German", "it": "Italian", "pt": "Portuguese",
    "hi": "Hindi", "ja": "Japanese", "ko": "Korean",
    "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "ar": "Arabic", "ru": "Russian", "nl": "Dutch",
    "sv": "Swedish", "pl": "Polish", "tr": "Turkish",
    "vi": "Vietnamese", "th": "Thai", "id": "Indonesian",
    "ta": "Tamil", "te": "Telugu", "gu": "Gujarati",
    "mr": "Marathi", "bn": "Bengali", "kn": "Kannada",
    "ml": "Malayalam", "uk": "Ukrainian", "cs": "Czech",
    "ro": "Romanian", "da": "Danish", "fi": "Finnish",
    "no": "Norwegian", "hu": "Hungarian",
}


class LanguageDetector:
    """
    Detect the primary language of resume/candidate text.
    
    Strategy:
      1. Try langdetect library (statistical n-gram based)
      2. Fall back to keyword heuristic matching
      3. Default to English if uncertain
    """

    # Common words in each language that appear in resumes
    LANGUAGE_HINTS: Dict[str, List[str]] = {
        "en": [
            "experience", "education", "skills", "summary",
            "university", "bachelor", "master", "developed",
            "managed", "implemented", "projects", "achievements",
        ],
        "hi": [
            "अनुभव", "शिक्षा", "कौशल", "विश्वविद्यालय",
            "परियोजना", "प्रमाण", "तकनीकी",
        ],
        "es": [
            "experiencia", "educación", "habilidades",
            "universidad", "desarrollar", "proyectos",
            "certificaciones", "logros",
        ],
        "fr": [
            "expérience", "éducation", "compétences",
            "université", "développer", "projets",
            "certifications", "réalisations",
        ],
        "de": [
            "erfahrung", "ausbildung", "fähigkeiten",
            "universität", "entwickeln", "projekte",
            "zertifizierungen", "leistungen",
        ],
        "pt": [
            "experiência", "educação", "habilidades",
            "universidade", "desenvolver", "projetos",
        ],
        "ja": ["経験", "教育", "スキル", "大学", "プロジェクト"],
        "zh-cn": ["经验", "教育", "技能", "大学", "项目"],
        "ko": ["경험", "교육", "기술", "대학교", "프로젝트"],
        "ta": ["அனுபவம்", "கல்வி", "திறன்கள்", "பல்கலைக்கழகம்"],
        "te": ["అనుభవం", "విద్య", "నైపుణ్యాలు", "విశ్వవిద్యాలయం"],
        "gu": ["અનુભવ", "શિક્ષણ", "કૌશલ્ય", "યુનિવર્સિટી"],
        "mr": ["अनुभव", "शिक्षण", "कौशल्ये", "विद्यापीठ"],
        "bn": ["অভিজ্ঞতা", "শিক্ষা", "দক্ষতা", "বিশ্ববিদ্যালয়"],
        "ru": ["опыт", "образование", "навыки", "университет"],
        "ar": ["خبرة", "تعليم", "مهارات", "جامعة"],
    }

    def __init__(self):
        self._langdetect_available: bool = False
        self._initialize()

    def _initialize(self):
        """Check langdetect availability."""
        try:
            import langdetect  # noqa: F401
            self._langdetect_available = True
            logger.debug("langdetect library available")
        except ImportError:
            logger.debug(
                "langdetect not installed — "
                "using heuristic fallback. "
                "Install: pip install langdetect"
            )

    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text.

        Args:
            text: Input text (minimum ~20 chars for accuracy)

        Returns:
            (language_code, confidence)
            e.g., ("en", 0.95), ("hi", 0.78)
        """
        if not text or len(text.strip()) < 20:
            return "en", 0.5

        # Strategy 1: langdetect library
        if self._langdetect_available:
            result = self._detect_with_langdetect(text)
            if result:
                return result

        # Strategy 2: keyword heuristic
        return self._detect_with_heuristic(text)

    def _detect_with_langdetect(self, text: str):
        """Detect using langdetect library."""
        try:
            import langdetect
            langdetect.DetectorFactory.seed = 0

            results = langdetect.detect_langs(text)
            if results:
                top = results[0]
                lang_code = str(top.lang)
                confidence = float(top.prob)

                logger.debug(
                    f"langdetect: {lang_code} "
                    f"(confidence: {confidence:.2f})"
                )
                return lang_code, confidence

        except Exception as e:
            logger.debug(f"langdetect failed: {e}")

        return None

    def _detect_with_heuristic(self, text: str) -> Tuple[str, float]:
        """
        Keyword-based language detection fallback.
        Counts matching language-specific keywords.
        """
        text_lower = text.lower()
        scores: Dict[str, int] = {}

        for lang, keywords in self.LANGUAGE_HINTS.items():
            score = sum(
                1 for kw in keywords
                if kw.lower() in text_lower
            )
            if score > 0:
                scores[lang] = score

        if not scores:
            return "en", 0.3

        best_lang = max(scores, key=scores.get)
        max_score = scores[best_lang]
        total_keywords = len(
            self.LANGUAGE_HINTS.get(best_lang, [])
        )

        confidence = min(max_score / max(total_keywords * 0.5, 1), 1.0)

        logger.debug(
            f"Heuristic detect: {best_lang} "
            f"(score: {max_score}, confidence: {confidence:.2f})"
        )
        return best_lang, round(confidence, 2)

    def get_tts_language(self, resume_text: str) -> str:
        """
        Get best TTS language code for the resume text.
        Returns language code suitable for TTS engines.
        """
        lang, conf = self.detect(resume_text)

        if conf < 0.5:
            logger.debug(
                f"Low confidence ({conf:.2f}) for '{lang}', "
                f"defaulting to English"
            )
            return "en"

        # Normalize language codes for TTS compatibility
        lang_map = {
            "zh-cn": "zh",
            "zh-tw": "zh",
        }
        return lang_map.get(lang, lang)

    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name."""
        return LANGUAGE_NAMES.get(
            lang_code,
            LANGUAGE_NAMES.get(lang_code[:2], "Unknown")
        )