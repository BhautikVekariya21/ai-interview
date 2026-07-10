"""
Pydantic schemas for TTS Module 3.
All request/response models for text-to-speech endpoints.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class TTSProvider(str, Enum):
    """Available TTS engine providers."""
    ELEVENLABS = "elevenlabs"
    GTTS = "gtts"
    OFFLINE = "offline"


class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"


class AudioFormat(str, Enum):
    """Supported audio output formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


# ─── Request Models ───────────────────────────────────────────


class TTSRequest(BaseModel):
    """Request to convert text to speech."""
    text: str = Field(..., min_length=1, max_length=5000,
                      description="Text to convert to speech")
    language: str = Field(default="en", description="Language code")
    voice_id: Optional[str] = Field(
        default=None,
        description="ElevenLabs voice ID or preset name"
    )
    speech_rate: float = Field(
        default=1.0, ge=0.5, le=2.0,
        description="Speech speed multiplier"
    )
    provider: Optional[TTSProvider] = Field(
        default=None,
        description="Force specific TTS provider"
    )
    format: AudioFormat = Field(
        default=AudioFormat.MP3,
        description="Audio output format"
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached audio if available"
    )


class InterviewSpeechRequest(BaseModel):
    """Request to generate full interview audio sequence."""
    candidate_name: str = Field(
        default="Candidate",
        description="Candidate name for personalized intro/outro"
    )
    questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of question dicts from Module 2"
    )
    include_intro: bool = Field(
        default=True,
        description="Generate introduction speech"
    )
    include_outro: bool = Field(
        default=True,
        description="Generate closing speech"
    )
    include_transitions: bool = Field(
        default=True,
        description="Add transition phrases between questions"
    )
    voice_id: Optional[str] = Field(
        default=None,
        description="ElevenLabs voice ID"
    )
    speech_rate: float = Field(
        default=1.0, ge=0.5, le=2.0,
        description="Speech speed"
    )
    score: int = Field(
        default=0, ge=0, le=100,
        description="Interview score for outro"
    )


class LanguageDetectRequest(BaseModel):
    """Request to detect language from text."""
    text: str = Field(..., min_length=20, max_length=50000,
                      description="Text to detect language from")


# ─── Response Models ──────────────────────────────────────────


class TTSResponse(BaseModel):
    """Metadata response for TTS generation."""
    success: bool
    provider_used: str
    voice_id: Optional[str] = None
    text_length: int
    audio_duration_estimate_seconds: float
    audio_size_bytes: int
    cached: bool = False
    language: str = "en"
    message: Optional[str] = None


class VoiceInfo(BaseModel):
    """Information about a single available voice."""
    voice_id: str
    name: str
    gender: str = "unknown"
    language: str = "en"
    provider: str
    preview_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class VoiceListResponse(BaseModel):
    """Response listing available voices."""
    total_voices: int
    active_provider: Optional[str]
    voices: List[VoiceInfo]


class TTSConfigResponse(BaseModel):
    """Current TTS configuration status."""
    active_provider: Optional[str]
    available_providers: List[str]
    fallback_order: List[str]
    voice_id: Optional[str]
    speech_rate: float
    language: str
    cache_enabled: bool
    cache_dir: str
    cache_size_mb: float


class AudioQueueItem(BaseModel):
    """Single item in the audio playback queue."""
    id: str
    text: str
    audio_type: str  # intro, transition, question, followup, outro
    question_number: Optional[int] = None
    question_category: Optional[str] = None
    duration_estimate_seconds: float = 0.0
    audio_size_bytes: int = 0
    status: str = "pending"  # pending, generating, ready, failed
    provider_used: Optional[str] = None
    cached: bool = False


class AudioQueueResponse(BaseModel):
    """Full interview audio queue."""
    success: bool
    candidate_name: str
    total_segments: int
    estimated_total_duration_seconds: float
    provider: Optional[str]
    segments: List[AudioQueueItem]


class LanguageDetectResponse(BaseModel):
    """Language detection result."""
    detected_language: str
    confidence: float
    tts_language_code: str
    language_name: str
    supported_for_tts: bool


class CacheStatusResponse(BaseModel):
    """Audio cache status."""
    enabled: bool
    directory: str
    total_files: int
    total_size_mb: float


class TTSUsageResponse(BaseModel):
    """ElevenLabs API usage stats."""
    provider: str
    characters_used: int = 0
    characters_limit: int = 0
    characters_remaining: int = 0
    tier: str = "unknown"
    usage_percent: float = 0.0


class TTSHealthResponse(BaseModel):
    """TTS module health check."""
    status: str
    active_provider: Optional[str]
    available_providers: List[str]
    fallback_chain: str
    cache_enabled: bool
    cache_size_mb: float