"""
ASR API endpoint tests with mocked ASR service.
"""

import pytest

from app.models.asr_schemas import RecordingSession, RecordingStatus, TranscriptionResult


class _ProviderStub:
    def __init__(self, available=True, info=None):
        self.is_available = available
        self._info = info or {}

    def get_info(self):
        return self._info


class FakeASR:
    def __init__(self):
        self.available_providers = ["openai-whisper", "google"]
        self.active_provider = "openai-whisper"
        self.streaming_available = False

        self.openai_whisper = _ProviderStub(info={"model": "whisper-1"})
        self.deepgram = _ProviderStub(available=False)
        self.google = _ProviderStub(info={"engine": "speech-recognition"})
        self.whisper_local = None
        self.vosk = None

        self.transcribe_calls = []
        self.started = {}
        self.uploaded = {}

    def transcribe(self, **kwargs):
        self.transcribe_calls.append(kwargs)
        return TranscriptionResult(
            success=True,
            text="hello world",
            provider_used="openai-whisper",
            confidence=0.92,
            duration_seconds=1.4,
            word_count=2,
            processing_time_ms=12.5,
        )

    def start_recording_session(self, **kwargs):
        session = RecordingSession(
            session_id=kwargs["session_id"],
            question_id=kwargs["question_id"],
            question_number=kwargs["question_number"],
            question_text=kwargs["question_text"],
            question_category=kwargs["question_category"],
            status=RecordingStatus.RECORDING,
            recording_number=1,
            max_re_records=3,
        )
        self.started[(session.session_id, session.question_id)] = session
        return session

    def get_session_status(self, session_id, question_id):
        return self.started.get((session_id, question_id)) or self.uploaded.get((session_id, question_id))

    def process_recording(self, session_id, question_id, audio_data, input_format, language):
        session = self.started[(session_id, question_id)]
        session.status = RecordingStatus.TRANSCRIBED
        session.final_text = "hello world"
        session.transcription = self.transcribe(
            audio_data=audio_data,
            input_format=input_format,
            language=language,
        )
        self.uploaded[(session_id, question_id)] = session
        return session.transcription

    def correct_transcription(self, session_id, question_id, corrected_text):
        session = self.get_session_status(session_id, question_id)
        if not session:
            return None
        session.final_text = corrected_text
        session.status = RecordingStatus.CORRECTED
        return session

    def re_record(self, session_id, question_id):
        session = self.get_session_status(session_id, question_id)
        if not session:
            return None
        session.recording_number += 1
        session.status = RecordingStatus.IDLE
        return session

    def submit_answer(self, session_id, question_id, final_text=None):
        session = self.get_session_status(session_id, question_id)
        if not session:
            return None
        if final_text:
            session.final_text = final_text
        if not session.final_text:
            return None
        session.submitted = True
        session.status = RecordingStatus.SUBMITTED
        return session

    def get_all_answers(self, session_id):
        result = []
        for (sid, qid), s in self.uploaded.items():
            if sid == session_id and s.submitted:
                result.append({"question_id": qid, "answer_text": s.final_text})
        return result

    def get_config(self):
        return {
            "active_provider": "openai-whisper",
            "available_providers": ["openai-whisper"],
            "fallback_order": ["openai-whisper"],
            "whisper_model_size": "base",
            "sample_rate": 16000,
            "silence_threshold_db": -40.0,
            "silence_duration_seconds": 1.5,
            "noise_reduction": True,
            "filler_detection": True,
            "max_recording_seconds": 300,
            "auto_submit": False,
            "allow_re_record": True,
            "max_re_records": 3,
            "streaming_enabled": False,
            "streaming_provider": None,
        }

    def get_stats(self):
        return {"total_transcriptions": len(self.transcribe_calls)}

    def get_health(self):
        return {
            "status": "healthy",
            "active_provider": "openai-whisper",
            "available_providers": ["openai-whisper"],
            "fallback_chain": "openai-whisper",
            "cloud_providers": ["openai-whisper"],
            "local_providers": [],
            "recordings_dir": "recordings",
            "total_recordings": 0,
            "streaming_available": False,
        }


@pytest.fixture
def fake_asr(monkeypatch):
    import app.api.asr_routes as asr_routes

    fake = FakeASR()
    monkeypatch.setattr(asr_routes, "get_asr", lambda: fake)
    return fake


@pytest.mark.asyncio
async def test_transcribe_rejects_small_audio(async_client, fake_asr):
    response = await async_client.post(
        "/asr/transcribe",
        files={"file": ("tiny.webm", b"x" * 50, "audio/webm")},
    )

    assert response.status_code == 400
    assert fake_asr.transcribe_calls == []


@pytest.mark.asyncio
async def test_transcribe_maps_format_and_returns_result(async_client, fake_asr):
    response = await async_client.post(
        "/asr/transcribe?language=en&provider=google&enable_filler_detection=false&enable_noise_reduction=false",
        files={"file": ("answer.mp3", b"x" * 500, "audio/mpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["provider_used"] == "openai-whisper"
    assert fake_asr.transcribe_calls[0]["input_format"] == "mp3"
    assert fake_asr.transcribe_calls[0]["provider"] == "google"
    assert fake_asr.transcribe_calls[0]["preprocess"] is False
    assert fake_asr.transcribe_calls[0]["detect_fillers"] is False


@pytest.mark.asyncio
async def test_session_start_upload_correct_submit_flow(async_client, fake_asr):
    start_resp = await async_client.post(
        "/asr/session/start",
        json={
            "session_id": "s1",
            "question_id": "q1",
            "question_number": 1,
            "question_text": "Tell me about Python.",
            "question_category": "T",
        },
    )
    assert start_resp.status_code == 200

    upload_resp = await async_client.post(
        "/asr/session/upload?session_id=s1&question_id=q1&format=webm&language=en",
        files={"file": ("answer.webm", b"x" * 1200, "audio/webm")},
    )
    assert upload_resp.status_code == 200
    upload_payload = upload_resp.json()
    assert upload_payload["success"] is True
    assert upload_payload["can_submit"] is True

    correct_resp = await async_client.post(
        "/asr/session/correct",
        json={"session_id": "s1", "question_id": "q1", "corrected_text": "updated answer"},
    )
    assert correct_resp.status_code == 200
    assert correct_resp.json()["session"]["final_text"] == "updated answer"

    submit_resp = await async_client.post(
        "/asr/session/submit",
        json={
            "session_id": "s1",
            "question_id": "q1",
            "final_text": "updated answer",
            "was_corrected": True,
        },
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["session"]["status"] == RecordingStatus.SUBMITTED.value


@pytest.mark.asyncio
async def test_session_upload_missing_session_returns_404(async_client, fake_asr):
    response = await async_client.post(
        "/asr/session/upload?session_id=missing&question_id=q1",
        files={"file": ("answer.webm", b"x" * 1200, "audio/webm")},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_providers(async_client, fake_asr):
    response = await async_client.get("/asr/providers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_provider"] == "openai-whisper"
    assert isinstance(payload["providers"], list)
    assert any(p["name"] == "openai-whisper" for p in payload["providers"])
