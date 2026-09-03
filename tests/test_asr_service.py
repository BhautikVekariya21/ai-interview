"""
Unit tests for ASRService orchestration.
"""

import pytest

from app.schemas.asr_schemas import FillerAnalysis, FillerWordInstance, RecordingSession, RecordingStatus, TranscriptionResult
from app.services.asr_service import ASRService


class _DummyPreprocessor:
    def __init__(self):
        self.convert_calls = []
        self.is_available = True

    def preprocess(self, audio_data, input_format, reduce_noise, normalize):
        return audio_data, {"output_format": "wav", "step": "ok"}

    def get_audio_duration(self, audio_data, input_format):
        return 1.5

    def convert_to_wav_16k(self, audio_data, input_format):
        self.convert_calls.append((audio_data, input_format))
        return b"wav-bytes"

    def save_recording(self, audio_data, session_id, question_id, recording_number):
        return f"recordings/{session_id}_{question_id}_{recording_number}.wav"


class _DummyFillerDetector:
    def analyze(self, text, word_timestamps=None):
        return FillerAnalysis(
            total_fillers=1,
            filler_words=[FillerWordInstance(word="um", count=1)],
            filler_percentage=10.0,
            feedback="good",
        )


class _DummySessionManager:
    def __init__(self):
        self.active_sessions_count = 0
        self.sessions = []

    def create_session(self, **kwargs):
        return RecordingSession(
            session_id=kwargs["session_id"],
            question_id=kwargs["question_id"],
            question_number=kwargs["question_number"],
            question_text=kwargs["question_text"],
            question_category=kwargs.get("question_category", "T"),
            status=RecordingStatus.IDLE,
        )

    def start_recording(self, session_id, question_id):
        return None

    def stop_recording(self, *args, **kwargs):
        return None

    def get_session(self, *args, **kwargs):
        return None

    def set_transcription(self, *args, **kwargs):
        return None

    def correct_transcription(self, *args, **kwargs):
        return None

    def re_record(self, *args, **kwargs):
        return None

    def submit(self, *args, **kwargs):
        return None

    def get_all_submitted(self, session_id):
        return self.sessions

    def get_stats(self):
        return {"active_interviews": 0}


@pytest.fixture
def bare_service():
    service = ASRService.__new__(ASRService)
    service.preprocessor = _DummyPreprocessor()
    service.filler_detector = _DummyFillerDetector()
    service.session_manager = _DummySessionManager()

    service.openai_whisper = None
    service.deepgram = None
    service.google = None
    service.whisper_local = None
    service.vosk = None

    service.available_providers = []
    service.cloud_providers = []
    service.local_providers = []
    service.active_provider = None
    service.streaming_available = False

    service._total_transcriptions = 0
    service._total_audio_seconds = 0.0
    service._provider_usage = {}
    return service


def test_get_provider_order_with_preferred(bare_service):
    bare_service.available_providers = ["openai-whisper", "google", "vosk"]

    order = bare_service._get_provider_order("google")

    assert order == ["google", "openai-whisper", "vosk"]


def test_transcribe_returns_error_when_no_provider(bare_service):
    result = bare_service.transcribe(audio_data=b"abc", preprocess=False)

    assert result.success is False
    assert result.error == "No ASR provider available"
    assert result.provider_used == "none"


def test_transcribe_fallback_to_second_provider(bare_service, monkeypatch):
    bare_service.available_providers = ["openai-whisper", "google"]

    calls = []

    def fake_dispatch(provider, audio_data, language, input_format):
        calls.append(provider)
        if provider == "openai-whisper":
            return {"error": "rate limit"}
        return {
            "text": "hello world",
            "confidence": 0.8,
            "segments": [{"text": "hello world", "start": 0.0, "end": 1.0, "confidence": 0.8}],
            "language": "en",
        }

    monkeypatch.setattr(bare_service, "_dispatch", fake_dispatch)

    result = bare_service.transcribe(audio_data=b"audio", preprocess=False, detect_fillers=True)

    assert result.success is True
    assert result.provider_used == "google"
    assert result.word_count == 2
    assert result.filler_analysis is not None
    assert calls == ["openai-whisper", "google"]


def test_dispatch_google_converts_non_wav_and_maps_language(bare_service):
    captured = {}

    class GoogleStub:
        is_available = True

        def transcribe(self, wav_audio, language):
            captured["audio"] = wav_audio
            captured["language"] = language
            return {"text": "ok", "confidence": 1.0}

    bare_service.google = GoogleStub()

    result = bare_service._dispatch("google", b"src", "hi", input_format="webm")

    assert result["text"] == "ok"
    assert captured["audio"] == b"wav-bytes"
    assert captured["language"] == "hi-IN"


@pytest.mark.asyncio
async def test_transcribe_stream_calls_error_callback_when_unavailable(bare_service):
    errors = []

    async def on_error(msg):
        errors.append(msg)

    await bare_service.transcribe_stream(audio_queue=None, on_transcript=lambda *_: None, on_error=on_error)

    assert errors
    assert "Streaming not available" in errors[0]


def test_get_all_answers_maps_sessions(bare_service):
    transcription = TranscriptionResult(
        success=True,
        text="final text",
        confidence=0.77,
        filler_analysis=FillerAnalysis(total_filler_count=0, filler_words=[]),
    )
    session = RecordingSession(
        session_id="s1",
        question_id="q1",
        question_number=1,
        question_text="Tell me",
        question_category="T",
        status=RecordingStatus.SUBMITTED,
        transcription=transcription,
        final_text="final text",
        corrected_text="final text",
        duration_seconds=2.1,
        recording_number=2,
        submitted=True,
    )
    bare_service.session_manager.sessions = [session]

    answers = bare_service.get_all_answers("s1")

    assert len(answers) == 1
    assert answers[0]["question_id"] == "q1"
    assert answers[0]["was_corrected"] is True
    assert answers[0]["filler_analysis"] is not None
