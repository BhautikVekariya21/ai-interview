"""
Filler Word Detector — Analyzes speech for filler words.
"""

import re
from typing import List, Dict, Optional
from loguru import logger

from app.core.config import settings
from app.schemas.asr_schemas import FillerAnalysis, FillerWordInstance


class FillerWordDetector:
    """Detects and analyzes filler words in transcribed speech."""

    # Default filler patterns
    DEFAULT_FILLERS = [
        # Hesitation sounds
        r"\bum+\b", r"\buh+\b", r"\berm+\b", r"\bahh*\b", r"\behh*\b",
        r"\bhmm+\b", r"\bumm+\b",
        # Discourse markers
        r"\blike\b", r"\byou know\b", r"\bbasically\b", r"\bactually\b",
        r"\bliterally\b", r"\bsort of\b", r"\bkind of\b",
        # Connectors used as fillers
        r"\bso\b", r"\bwell\b", r"\bi mean\b", r"\bright\b",
        r"\bokay so\b", r"\byeah\b", r"\bokay\b",
    ]

    def __init__(self, custom_fillers: Optional[List[str]] = None):
        """
        Initialize filler detector.
        
        Args:
            custom_fillers: Additional filler patterns to detect
        """
        self.filler_patterns: List[re.Pattern] = []
        
        # Compile default patterns
        for pattern in self.DEFAULT_FILLERS:
            try:
                self.filler_patterns.append(
                    re.compile(pattern, re.IGNORECASE)
                )
            except re.error as e:
                logger.warning(f"Invalid filler pattern '{pattern}': {e}")

        # Add custom fillers from settings
        for word in settings.FILLER_WORDS:
            try:
                pattern = rf"\b{re.escape(word)}\b"
                self.filler_patterns.append(
                    re.compile(pattern, re.IGNORECASE)
                )
            except re.error as e:
                logger.warning(f"Invalid custom filler '{word}': {e}")

        # Add additional custom fillers
        if custom_fillers:
            for word in custom_fillers:
                try:
                    pattern = rf"\b{re.escape(word)}\b"
                    self.filler_patterns.append(
                        re.compile(pattern, re.IGNORECASE)
                    )
                except re.error as e:
                    logger.warning(f"Invalid filler '{word}': {e}")

        logger.info(f"FillerWordDetector initialized with {len(self.filler_patterns)} patterns")

    def analyze(
        self,
        text: str,
        duration_seconds: float = 0.0
    ) -> FillerAnalysis:
        """
        Analyze text for filler words.
        
        Args:
            text: Transcribed text to analyze
            duration_seconds: Duration of speech for rate calculation
            
        Returns:
            FillerAnalysis with detected fillers and statistics
        """
        if not text or not text.strip():
            return FillerAnalysis(
                total_fillers=0,
                filler_percentage=0.0,
                fillers_per_minute=0.0,
                filler_words=[],
                clean_text="",
                severity="low",
                suggestions=[]
            )

        text_lower = text.lower()
        word_count = len(text.split())
        filler_counts: Dict[str, FillerWordInstance] = {}
        
        # Find all filler occurrences
        for pattern in self.filler_patterns:
            for match in pattern.finditer(text_lower):
                word = match.group().lower().strip()
                position = match.start()
                
                if word not in filler_counts:
                    filler_counts[word] = FillerWordInstance(
                        word=word,
                        count=0,
                        positions=[]
                    )
                filler_counts[word].count += 1
                filler_counts[word].positions.append(position)

        # Calculate statistics
        total_fillers = sum(f.count for f in filler_counts.values())
        filler_percentage = (total_fillers / word_count * 100) if word_count > 0 else 0.0
        
        # Calculate fillers per minute
        fillers_per_minute = 0.0
        if duration_seconds > 0:
            fillers_per_minute = (total_fillers / duration_seconds) * 60

        # Generate clean text (remove fillers)
        clean_text = text
        for pattern in self.filler_patterns:
            clean_text = pattern.sub("", clean_text)
        # Clean up extra spaces
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Determine severity
        severity = self._calculate_severity(filler_percentage, fillers_per_minute)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            filler_counts, severity, filler_percentage
        )

        # Sort filler words by count
        filler_list = sorted(
            filler_counts.values(),
            key=lambda x: x.count,
            reverse=True
        )

        return FillerAnalysis(
            total_fillers=total_fillers,
            filler_percentage=round(filler_percentage, 2),
            fillers_per_minute=round(fillers_per_minute, 2),
            filler_words=filler_list,
            clean_text=clean_text,
            severity=severity,
            suggestions=suggestions
        )

    def _calculate_severity(
        self,
        filler_percentage: float,
        fillers_per_minute: float
    ) -> str:
        """Calculate severity level based on filler frequency."""
        if filler_percentage > 10 or fillers_per_minute > 8:
            return "high"
        elif filler_percentage > 5 or fillers_per_minute > 4:
            return "medium"
        return "low"

    def _generate_suggestions(
        self,
        filler_counts: Dict[str, FillerWordInstance],
        severity: str,
        filler_percentage: float
    ) -> List[str]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []

        if severity == "high":
            suggestions.append(
                "Consider pausing briefly instead of using filler words."
            )
            suggestions.append(
                "Practice speaking slower to reduce reliance on fillers."
            )
        elif severity == "medium":
            suggestions.append(
                "You're using fillers moderately. Try to be more aware of them."
            )

        # Specific suggestions for common fillers
        top_fillers = sorted(
            filler_counts.values(),
            key=lambda x: x.count,
            reverse=True
        )[:3]

        for filler in top_fillers:
            if filler.count >= 3:
                if filler.word in ["um", "uh", "uhh", "umm", "erm"]:
                    suggestions.append(
                        f"Replace '{filler.word}' with a brief pause."
                    )
                elif filler.word in ["like", "you know"]:
                    suggestions.append(
                        f"Reduce '{filler.word}' - it can seem informal."
                    )
                elif filler.word in ["basically", "literally", "actually"]:
                    suggestions.append(
                        f"'{filler.word.capitalize()}' is often unnecessary - try removing it."
                    )

        return suggestions[:5]  # Limit to 5 suggestions

    def remove_fillers(self, text: str) -> str:
        """Remove all filler words from text."""
        result = text
        for pattern in self.filler_patterns:
            result = pattern.sub("", result)
        return re.sub(r'\s+', ' ', result).strip()


# Singleton instance
_detector_instance: Optional[FillerWordDetector] = None


def get_filler_detector() -> FillerWordDetector:
    """Get singleton filler detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FillerWordDetector()
    return _detector_instance