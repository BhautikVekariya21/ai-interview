"""
ASR Session Manager — Manages recording sessions and state.
"""

import time
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

from app.core.config import settings
from app.schemas.asr_schemas import (
    RecordingSession,
    RecordingState,
    TranscriptionResult,
    FillerAnalysis,
)


class ASRSessionManager:
    """
    Manages ASR recording sessions.
    
    Each session tracks:
    - Recording state (idle, recording, processing, completed, submitted)
    - Audio data and paths
    - Transcription results
    - User corrections
    - Re-recording attempts
    """

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, RecordingSession] = {}
        self._recordings_dir = Path(settings.ASR_RECORDINGS_DIR)
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ASR Session Manager initialized. Recordings: {self._recordings_dir}")

    def _session_key(self, session_id: str, question_id: str) -> str:
        """Generate unique session key."""
        return f"{session_id}:{question_id}"

    @property
    def active_sessions_count(self) -> int:
        """Count of active (non-submitted) sessions."""
        return sum(
            1 for s in self._sessions.values()
            if s.state not in [RecordingState.SUBMITTED, RecordingState.ERROR]
        )

    def create_session(
        self,
        session_id: str,
        question_id: str,
        question_number: int = 1,
        question_text: str = "",
        question_category: str = "T",
    ) -> RecordingSession:
        """Create a new recording session."""
        key = self._session_key(session_id, question_id)
        
        session = RecordingSession(
            session_id=session_id,
            question_id=question_id,
            question_number=question_number,
            question_text=question_text,
            question_category=question_category,
            state=RecordingState.IDLE,
            recording_number=1,
            max_recordings=settings.ASR_MAX_RE_RECORDS,
        )
        
        self._sessions[key] = session
        logger.debug(f"Session created: {key}")
        return session

    def get_session(
        self,
        session_id: str,
        question_id: str
    ) -> Optional[RecordingSession]:
        """Get existing session."""
        key = self._session_key(session_id, question_id)
        return self._sessions.get(key)

    def get_or_create_session(
        self,
        session_id: str,
        question_id: str,
        question_number: int = 1,
        question_text: str = "",
        question_category: str = "T",
    ) -> RecordingSession:
        """Get existing session or create new one."""
        session = self.get_session(session_id, question_id)
        if session is None:
            session = self.create_session(
                session_id=session_id,
                question_id=question_id,
                question_number=question_number,
                question_text=question_text,
                question_category=question_category,
            )
        return session

    def start_recording(
        self,
        session_id: str,
        question_id: str
    ) -> Optional[RecordingSession]:
        """Mark session as recording."""
        session = self.get_session(session_id, question_id)
        if session is None:
            return None
            
        session.state = RecordingState.RECORDING
        session.started_at = datetime.now(timezone.utc)
        logger.debug(f"Recording started: {session_id}/{question_id}")
        return session

    def stop_recording(
        self,
        session_id: str,
        question_id: str,
        audio_data: Optional[bytes] = None,
    ) -> Optional[RecordingSession]:
        """Stop recording and save audio."""
        session = self.get_session(session_id, question_id)
        if session is None:
            return None

        session.state = RecordingState.PROCESSING
        session.completed_at = datetime.now(timezone.utc)

        # Save audio if provided
        if audio_data:
            audio_path = self._save_audio(session_id, question_id, audio_data)
            session.audio_path = str(audio_path)
            session.audio_size_bytes = len(audio_data)

        logger.debug(f"Recording stopped: {session_id}/{question_id}")
        return session

    def _save_audio(
        self,
        session_id: str,
        question_id: str,
        audio_data: bytes,
        extension: str = "wav"
    ) -> Path:
        """Save audio to recordings directory."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{question_id}_{timestamp}.{extension}"
        filepath = self._recordings_dir / filename
        filepath.write_bytes(audio_data)
        logger.info(f"Audio saved: {filepath} ({len(audio_data):,} bytes)")
        return filepath

    def set_browser_transcript(
        self,
        session_id: str,
        question_id: str,
        transcript: str,
        duration_seconds: float = 0.0,
        word_count: int = 0,
        filler_analysis: Optional[FillerAnalysis] = None,
    ) -> Optional[RecordingSession]:
        """Set transcript from browser Web Speech API."""
        session = self.get_or_create_session(session_id, question_id)
        
        session.raw_text = transcript
        session.final_text = transcript
        session.duration_seconds = duration_seconds
        session.word_count = word_count if word_count > 0 else len(transcript.split())
        session.provider_used = "browser"
        session.confidence = 0.85
        session.state = RecordingState.COMPLETED

        # Create transcription result
        session.transcription = TranscriptionResult(
            success=True,
            text=transcript,
            transcript=transcript,
            duration_seconds=duration_seconds,
            word_count=session.word_count,
            provider_used="browser",
            confidence=0.85,
            filler_analysis=filler_analysis,
        )

        logger.debug(f"Browser transcript set: {session_id}/{question_id}")
        return session

    def set_transcription(
        self,
        session_id: str,
        question_id: str,
        transcription: TranscriptionResult,
    ) -> Optional[RecordingSession]:
        """Set transcription result from backend ASR."""
        session = self.get_session(session_id, question_id)
        if session is None:
            return None

        session.transcription = transcription
        session.raw_text = transcription.text
        session.final_text = transcription.text
        session.word_count = transcription.word_count
        session.confidence = transcription.confidence
        session.duration_seconds = transcription.duration_seconds
        session.provider_used = transcription.provider_used
        session.state = RecordingState.COMPLETED

        logger.debug(f"Transcription set: {session_id}/{question_id}")
        return session

    def correct_transcription(
        self,
        session_id: str,
        question_id: str,
        corrected_text: str
    ) -> Optional[RecordingSession]:
        """Apply user correction to transcription."""
        session = self.get_session(session_id, question_id)
        if session is None:
            return None

        session.corrected_text = corrected_text
        session.final_text = corrected_text
        session.word_count = len(corrected_text.split())

        logger.debug(f"Transcription corrected: {session_id}/{question_id}")
        return session

    def re_record(
        self,
        session_id: str,
        question_id: str
    ) -> Optional[RecordingSession]:
        """Reset session for re-recording."""
        session = self.get_session(session_id, question_id)
        if session is None:
            return None

        if not session.can_re_record:
            logger.warning(f"Cannot re-record: max attempts reached")
            return None

        # Increment recording number
        session.recording_number += 1
        
        # Reset state
        session.state = RecordingState.IDLE
        session.raw_text = None
        session.corrected_text = None
        session.final_text = None
        session.transcription = None
        session.audio_path = None
        session.audio_size_bytes = 0
        session.started_at = None
        session.completed_at = None

        logger.info(f"Re-record #{session.recording_number}: {session_id}/{question_id}")
        return session

    def submit(
        self,
        session_id: str,
        question_id: str
    ) -> Optional[RecordingSession]:
        """Submit final answer."""
        session = self.get_session(session_id, question_id)
        if session is None:
            return None

        if not session.final_text:
            logger.warning(f"Cannot submit: no transcript available")
            return None

        session.state = RecordingState.SUBMITTED
        session.submitted_at = datetime.now(timezone.utc)

        logger.info(f"Answer submitted: {session_id}/{question_id}")
        return session

    def get_all_submitted(self, session_id: str) -> List[RecordingSession]:
        """Get all submitted answers for a session."""
        return [
            s for s in self._sessions.values()
            if s.session_id == session_id and s.state == RecordingState.SUBMITTED
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        states = {}
        for session in self._sessions.values():
            state = session.state.value
            states[state] = states.get(state, 0) + 1

        return {
            "total_sessions": len(self._sessions),
            "states": states,
            "recordings_dir": str(self._recordings_dir),
            "recordings_count": len(list(self._recordings_dir.glob("*"))) if self._recordings_dir.exists() else 0,
        }

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Remove old sessions."""
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        removed = 0

        keys_to_remove = []
        for key, session in self._sessions.items():
            if session.submitted_at:
                if session.submitted_at.timestamp() < cutoff:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._sessions[key]
            removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old sessions")

        return removed


# Singleton instance
_session_manager_instance: Optional[ASRSessionManager] = None


def get_asr_session_manager() -> ASRSessionManager:
    """Get singleton session manager instance."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = ASRSessionManager()
    return _session_manager_instance
