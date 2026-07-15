"""
Configuration — All settings with ASR cloud providers.
API keys from .env — NEVER exposed to frontend.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application-wide settings loaded from environment."""

    # ═══════════════════ APPLICATION ═══════════════════
    APP_NAME: str = "AI Interview System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000", "http://localhost:7860"],
        description="List of allowed CORS origins"
    )

    # ═══════════════════ AUTH / JWT ═══════════════════
    JWT_SECRET_KEY: str = Field(default="super-secret-jwt-key!123", description="Secret key for signing JWTs")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 30

    # ═══════════════════ FILE UPLOAD ═══════════════════
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".webp"]
    UPLOAD_DIR: str = "uploads"

    # ═══════════════════ OCR (Image Resume Scanning) ═══════════════════
    TESSERACT_CMD: Optional[str] = Field(default=None, description="Path to tesseract binary (auto-detected if on PATH)")
    OCR_LANGUAGE: str = "eng"
    OCR_DPI: int = 300

    # ═══════════════════ NER MODEL (Module 1) ═══════════════════
    NER_MODEL_PATH: str = "saved_models/ner_bilstm_crf"
    EMBEDDING_DIM: int = 128
    LSTM_UNITS: int = 256
    DROPOUT_RATE: float = 0.3
    MAX_SEQUENCE_LENGTH: int = 150
    BATCH_SIZE: int = 32
    EPOCHS: int = 50
    LEARNING_RATE: float = 0.001
    NER_TRAINING_METRICS_PATH: str = "reports/ner_training_metrics.json"

    # ML experiment tracking
    MLFLOW_ENABLED: bool = False
    MLFLOW_TRACKING_URI: str = "file:./mlruns"
    MLFLOW_EXPERIMENT_NAME: str = "resume-ner"
    MLFLOW_ARTIFACT_PATH: str = "artifacts"

    # ═══════════════════ DATA PATHS ═══════════════════
    SKILL_TAXONOMY_PATH: str = "app/data/skill_taxonomy.json"
    JOB_TITLES_PATH: str = "app/data/job_titles.json"
    INSTITUTIONS_PATH: str = "app/data/institutions.json"

    # ═══════════════════ EXTRACTION THRESHOLDS ═══════════════════
    MIN_CONFIDENCE_THRESHOLD: float = 0.6
    SKILL_MATCH_THRESHOLD: float = 0.75
    RUST_ACCELERATION_ENABLED: bool = True

    # ═══════════════════ XAI GROK (PRIMARY LLM) ═══════════════════
    XAI_API_KEY: Optional[str] = Field(default=None, description="xAI API key")
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_MODEL_QUEUE: List[str] = [
        "grok-3-mini-beta",
        "grok-3-beta",
        "grok-2-latest",
    ]


    # ═══════════════════ THIRD-PARTY PRIORITY LLMs ═══════════════════
    CLAUDE_API_KEY: Optional[str] = Field(default=None, description="Anthropic Claude API key")
    CLAUDE_MODEL_QUEUE: List[str] = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]

    AIML_API_KEY: Optional[str] = Field(default=None, description="AIMLAPI key")
    AIML_BASE_URL: str = "https://api.aimlapi.com/v1"
    AIML_MODEL_QUEUE: List[str] = ["gpt-4o-mini", "claude-3-5-sonnet", "mistral-large-latest"]

    MISTRAL_API_KEY: Optional[str] = Field(default=None, description="Mistral API key")
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"
    MISTRAL_MODEL_QUEUE: List[str] = ["mistral-large-latest", "ministral-8b-latest"]

    OPENROUTER_API_KEY: Optional[str] = Field(default=None, description="OpenRouter API key")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL_QUEUE: List[str] = [
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mistral-large",
    ]

    # ═══════════════════ GEMINI (SECONDARY LLM) ═══════════════════
    GEMINI_API_KEY: str = Field(default="", description="Google AI Studio API key")
    GEMINI_MODEL_QUEUE: List[str] = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

    # ═══════════════════ GROQ (FREE FALLBACK POOL) ═══════════════════
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    GROQ_MODEL_QUEUE: List[str] = [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama-3.1-8b-instant",
    ]

    # ═══════════════════ HUGGINGFACE (LAST RESORT) ═══════════════════
    HUGGINGFACE_API_KEY: str = Field(default="", description="HuggingFace token")
    HF_MODEL_QUEUE: List[str] = [
        "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "google/gemma-7b-it",
    ]

    # ═══════════════════ LLM PARAMETERS ═══════════════════
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE_MIN: float = 0.70
    LLM_TEMPERATURE_MAX: float = 0.95
    LLM_TOP_P: float = 0.90
    LLM_TIMEOUT_SECONDS: int = 90
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_DELAY_SECONDS: float = 2.0
    LLM_REPETITION_PENALTY: float = 1.15
    LLM_MAX_FAILURES_BEFORE_SKIP: int = 3
    LLM_FAILURE_COOLDOWN_SECONDS: int = 300

    # ═══════════════════ QUESTION GENERATION ═══════════════════
    DEFAULT_NUM_QUESTIONS: int = 15
    MIN_QUESTIONS: int = 10
    MAX_QUESTIONS: int = 30
    FOLLOW_UP_ENABLED: bool = True
    DIFFICULTY_CLASSIFIER_EPOCHS: int = 50
    DIFFICULTY_CLASSIFIER_BATCH_SIZE: int = 64
    DIFFICULTY_CLASSIFIER_VALIDATION_SPLIT: float = 0.15
    DIFFICULTY_TRAINING_SAMPLES: int = 5000

    # ═══════════════════ OAUTH SETTINGS ═══════════════════
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # ═══════════════════ TTS (Module 3) ═══════════════════
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"
    TTS_PROVIDER: Optional[str] = "gtts"
    TTS_SPEECH_RATE: float = 1.0
    TTS_VOICE_GENDER: str = "female"
    TTS_LANGUAGE: str = "en"
    TTS_CACHE_ENABLED: bool = True
    TTS_CACHE_DIR: str = "audio_cache"
    ELEVENLABS_VOICES: Dict[str, str] = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",
        "adam": "pNInz6obpgDQGcFmaJgB",
        "bella": "EXAVITQu4vr4xnSDxMaL",
    }
    INTERVIEW_INTRO_TEMPLATE: str = "Hello {name}! Welcome to your AI interview."
    INTERVIEW_OUTRO_TEMPLATE: str = "Thank you, {name}, for completing this interview!"
    QUESTION_TRANSITION_TEMPLATES: List[str] = [
        "Moving on to question {num}.",
        "Question {num} of {total}.",
    ]

    # ═══════════════════ ASR MODULE 4 — CLOUD PROVIDERS ═══════════════════
    # OpenAI Whisper API (Primary — most accurate)
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key for Whisper cloud API"
    )
    OPENAI_WHISPER_MODEL: str = "whisper-1"
    
    # Deepgram (Real-time streaming)
    DEEPGRAM_API_KEY: Optional[str] = Field(
        default=None,
        description="Deepgram API key for streaming ASR"
    )
    DEEPGRAM_MODEL: str = "nova-2"
    
    # AssemblyAI (Alternative streaming)
    ASSEMBLYAI_API_KEY: Optional[str] = Field(
        default=None,
        description="AssemblyAI API key"
    )

    # ASR Provider Selection
    ASR_PROVIDER: Optional[str] = Field(
        default=None,
        description="Force specific provider: openai-whisper | deepgram | google | vosk"
    )
    ASR_PROVIDER_PRIORITY: List[str] = [
        "whisper-local",   # Local/offline first when available
        "openai-whisper",  # Cloud Whisper
        "deepgram",        # Cloud fallback
        "google",          # Free fallback
        "vosk",            # Offline fallback
    ]

    # Streaming Configuration
    ASR_STREAM_ENABLED: bool = True
    ASR_STREAM_PROVIDER: str = "deepgram"  # deepgram | assemblyai
    ASR_STREAM_INTERIM_RESULTS: bool = True
    ASR_STREAM_PUNCTUATE: bool = True
    ASR_STREAM_FILLER_WORDS: bool = True

    # Local Whisper (fallback only)
    WHISPER_MODEL_SIZE: str = "tiny"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_LANGUAGE: str = "en"
    WHISPER_FP16: bool = False

    # Google Speech (free fallback)
    GOOGLE_SPEECH_CREDENTIALS_PATH: Optional[str] = None
    GOOGLE_SPEECH_LANGUAGE: str = "en-US"

    # Audio Processing
    ASR_SAMPLE_RATE: int = 16000
    ASR_CHANNELS: int = 1
    ASR_BITRATE: str = "128k"
    ASR_CHUNK_DURATION_MS: int = 500
    ASR_MAX_RECORDING_SECONDS: int = 300
    ASR_MIN_RECORDING_SECONDS: int = 2

    # WebM to WAV Conversion
    CONVERT_WEBM_TO_WAV: bool = True
    WEBM_OPUS_CODEC: bool = True

    # Voice Activity Detection
    SILENCE_THRESHOLD_DB: float = -40.0
    SILENCE_DURATION_SECONDS: float = 1.5  # Reduced for streaming
    VAD_AGGRESSIVENESS: int = 2

    # Audio Enhancement
    NOISE_REDUCTION_ENABLED: bool = True
    NORMALIZE_AUDIO: bool = True
    HIGH_PASS_FILTER_HZ: int = 80
    LOW_PASS_FILTER_HZ: int = 8000

    # Filler Word Detection
    FILLER_DETECTION_ENABLED: bool = True
    FILLER_WORDS: List[str] = [
        "um", "uh", "uhh", "umm", "erm",
        "like", "you know", "basically",
        "actually", "literally", "right",
        "so", "well", "I mean",
    ]

    # Session Management
    ASR_RECORDINGS_DIR: str = "recordings"
    ASR_ALLOW_RE_RECORD: bool = True
    ASR_MAX_RE_RECORDS: int = 3
    ASR_AUTO_SUBMIT: bool = False


    # ═══════════════════ CACHE / REDIS ═══════════════════
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL_SECONDS: int = 3600
    VALKEY_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Valkey URL for shared cache (falls back to in-memory cache if unavailable)",
    )
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Legacy Redis-compatible cache URL fallback",
    )

    # MySQL / user data
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "ai_interview"

    # OpenTelemetry / tracing
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "ai-interview-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_INSECURE: bool = True
    OTEL_SAMPLE_RATIO: float = 1.0

    FRONTEND_BASE_URL: str = Field(
        default="http://localhost:5173",
        description="Frontend base URL used for password-reset links",
    )
    BACKEND_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Publicly reachable backend base URL used for OAuth redirect URIs",
    )

    # ═══════════════════ SECTION KEYWORDS ═══════════════════
    SECTION_KEYWORDS: dict = {
        "personal": [
            "personal", "contact", "info", "summary",
            "about me", "profile", "bio", "objective",
        ],
        "education": [
            "education", "academic", "qualification",
            "university", "degree", "school", "college",
        ],
        "experience": [
            "experience", "employment", "work history",
            "professional", "career", "job",
        ],
        "skills": [
            "skills", "skill", "technical", "competencies", "competency",
            "technologies", "technology", "proficiencies", "proficiency", "tools",
            "languages", "frameworks", "tech stack", "expertise", "toolkit",
            "areas of expertise", "core competencies",
        ],
        "projects": [
            "projects", "project", "portfolio", "works",
            "personal projects", "academic projects", "key projects",
            "notable projects", "selected projects",
        ],
        "certifications": [
            "certifications", "certification", "certificates", "certificate",
            "licenses", "license", "accreditations", "accreditation",
            "credentials", "credential", "courses", "course",
            "online courses", "trainings", "training", "badges", "certified",
        ],
        "publications": [
            "publications", "publication", "papers", "paper", "research",
            "journal", "journals", "conference", "conferences",
        ],
        "achievements": [
            "achievements", "achievement", "awards", "award", "honors", "honours",
            "honor", "honour", "accomplishments", "accomplishment", "recognition",
            "recognitions", "extracurricular", "extra curricular", "activities",
            "highlights", "key achievements", "positions of responsibility",
        ],
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        """Accept common non-boolean env values like 'release'."""
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "debug", "dev", "development"}:
            return True
        if text in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return False

    @field_validator("GROQ_MODEL_QUEUE", mode="before")
    @classmethod
    def normalize_groq_model_queue(cls, value):
        """Filter out decommissioned Groq models from defaults or env overrides."""
        fallback_queue = [
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "llama-3.1-8b-instant",
        ]
        deprecated_models = {"llama-3.1-70b-versatile"}

        if value is None:
            return fallback_queue

        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                try:
                    value = json.loads(text)
                except json.JSONDecodeError:
                    value = [item.strip() for item in text.split(",") if item.strip()]
            else:
                value = [item.strip() for item in text.split(",") if item.strip()]

        if not isinstance(value, list):
            return fallback_queue

        cleaned_queue = [model for model in value if model not in deprecated_models]
        return cleaned_queue or fallback_queue


settings = Settings()

# Create necessary directories
for _dir in [
    settings.UPLOAD_DIR,
    settings.TTS_CACHE_DIR,
    settings.ASR_RECORDINGS_DIR,
    Path(settings.NER_MODEL_PATH).parent,
    Path(settings.NER_TRAINING_METRICS_PATH).parent,
]:
    Path(_dir).mkdir(parents=True, exist_ok=True)
