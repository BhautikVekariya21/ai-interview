"""
ASR Pydantic Schemas — Module 4.
Defines all request/response models for ASR endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class RecordingState(str, Enum):
    """Recording session states."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    TRANSCRIBED = "completed"  # backward-compatible alias
    CORRECTED = "completed"    # backward-compatible alias
    SUBMITTED = "submitted"
    ERROR = "error"


# Backward-compatible alias used in legacy tests/callers.
RecordingStatus = RecordingState


# ─── FILLER ANALYSIS ───────────────────────────────────────────


class FillerWordInstance(BaseModel):
    """Single filler word occurrence."""
    word: str
    count: int
    positions: List[int] = Field(default_factory=list)


class FillerAnalysis(BaseModel):
    """Filler word analysis result."""
    total_fillers: int = 0
    filler_percentage: float = 0.0
    fillers_per_minute: float = 0.0
    filler_words: List[FillerWordInstance] = Field(default_factory=list)
    clean_text: str = ""
    severity: str = "low"  # low, medium, high
    suggestions: List[str] = Field(default_factory=list)


# ─── TRANSCRIPTION ─────────────────────────────────────────────


class TranscriptionSegment(BaseModel):
    """Single transcription segment with timing."""
    text: str
    start_time: float = 0.0
    end_time: float = 0.0
    confidence: float = 0.0
    speaker: Optional[str] = None


class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    success: bool = True
    text: str = ""
    transcript: str = ""  # Alias for compatibility
    segments: List[TranscriptionSegment] = Field(default_factory=list)
    language: str = "en"
    language_detected: Optional[str] = None
    confidence: float = 0.0
    duration_seconds: float = 0.0
    word_count: int = 0
    provider_used: str = "browser"
    attempted_providers: List[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    filler_analysis: Optional[FillerAnalysis] = None
    error: Optional[str] = None
    audio_path: Optional[str] = None

    def model_post_init(self, __context):
        """Ensure transcript alias is set."""
        if self.text and not self.transcript:
            object.__setattr__(self, 'transcript', self.text)
        elif self.transcript and not self.text:
            object.__setattr__(self, 'text', self.transcript)


# ─── RECORDING SESSION ─────────────────────────────────────────


class RecordingSession(BaseModel):
    """Recording session state."""
    session_id: str
    question_id: str
    question_number: int = 0
    question_text: str = ""
    question_category: str = "T"
    state: RecordingState = RecordingState.IDLE
    status: RecordingState = RecordingState.IDLE
    recording_number: int = 1
    max_recordings: int = 3
    
    # Audio data
    audio_path: Optional[str] = None
    audio_size_bytes: int = 0
    duration_seconds: float = 0.0
    
    # Transcription
    raw_text: Optional[str] = None
    corrected_text: Optional[str] = None
    final_text: Optional[str] = None
    transcription: Optional[TranscriptionResult] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    
    # Metadata
    word_count: int = 0
    confidence: float = 0.0
    provider_used: str = "browser"

    @property
    def submitted(self) -> bool:
        """Backward-compatible flag used by legacy tests/callers."""
        return self.state == RecordingState.SUBMITTED

    @submitted.setter
    def submitted(self, value: bool) -> None:
        if value:
            self.state = RecordingState.SUBMITTED

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        data["status"] = self.state.value
        return data

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "state":
            super().__setattr__("status", value)
        elif name == "status":
            super().__setattr__("state", value)

    @property
    def is_submitted(self) -> bool:
        return self.state == RecordingState.SUBMITTED

    @property
    def can_re_record(self) -> bool:
        return self.recording_number < self.max_recordings and not self.is_submitted


# ─── REQUEST MODELS ────────────────────────────────────────────


class BrowserTranscriptRequest(BaseModel):
    """Request for browser-based transcript submission."""
    session_id: str
    question_id: str
    question_number: int = 1
    question_text: str = ""
    question_category: str = "T"
    transcript: str
    duration_seconds: float = 0.0
    word_count: int = 0
    confidence: float = 0.85


class StartRecordingRequest(BaseModel):
    """Request to start a recording session."""
    session_id: str
    question_id: str
    question_number: int = 1
    question_text: str = ""
    question_category: str = "T"


class SubmitTranscriptionRequest(BaseModel):
    """Request to submit final transcription."""
    session_id: str
    question_id: str
    final_text: Optional[str] = None


class CorrectionRequest(BaseModel):
    """Request to correct transcription."""
    session_id: str
    question_id: str
    corrected_text: str


class ReRecordRequest(BaseModel):
    """Request to re-record answer."""
    session_id: str
    question_id: str


# ─── RESPONSE MODELS ───────────────────────────────────────────


class RecordingSessionResponse(BaseModel):
    """Response for recording session operations."""
    success: bool
    message: str
    session: Optional[RecordingSession] = None
    can_re_record: bool = True
    can_correct: bool = False
    can_submit: bool = False


class ASRConfigResponse(BaseModel):
    """ASR configuration response."""
    active_provider: str = "browser"
    available_providers: List[str] = Field(default_factory=list)
    fallback_order: List[str] = Field(default_factory=list)
    browser_asr_enabled: bool = True
    whisper_model_size: str = "tiny"
    sample_rate: int = 16000
    silence_threshold_db: float = -40.0
    silence_duration_seconds: float = 1.5
    noise_reduction: bool = True
    filler_detection: bool = True
    max_recording_seconds: int = 300
    auto_submit: bool = False
    allow_re_record: bool = True
    max_re_records: int = 3


class ASRHealthResponse(BaseModel):
    """ASR health check response."""
    status: str = "healthy"
    active_provider: str = "browser"
    available_providers: List[str] = Field(default_factory=list)
    fallback_chain: str = ""
    browser_asr_available: bool = True
    cloud_providers: List[str] = Field(default_factory=list)
    local_providers: List[str] = Field(default_factory=list)
    recordings_dir: str = "recordings"
    total_recordings: int = 0


class SimpleTranscriptResponse(BaseModel):
    """Simple transcript response for Streamlit compatibility."""
    success: bool = True
    transcript: str = ""
    text: str = ""  # Alias
    word_count: int = 0
    confidence: float = 0.0
    duration_seconds: float = 0.0
    provider: str = "browser"
    attempted_providers: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    audio_path: Optional[str] = None
    filler_analysis: Optional[Dict[str, Any]] = None
