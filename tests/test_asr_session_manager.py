"""
Unit tests for ASR session lifecycle manager.
"""

from app.schemas.asr_schemas import RecordingStatus, TranscriptionResult
from app.services.asr_session_manager import ASRSessionManager


def _make_transcription(text="hello"):
    return TranscriptionResult(
        success=True,
        text=text,
        provider_used="stub",
        confidence=0.9,
        duration_seconds=1.0,
        word_count=len(text.split()),
        processing_time_ms=5.0,
    )


def test_create_start_stop_and_submit_flow():
    manager = ASRSessionManager()

    session = manager.create_session("s1", "q1", 1, "Tell me about yourself", "B")
    assert session.status == RecordingStatus.IDLE

    started = manager.start_recording("s1", "q1")
    assert started.status == RecordingStatus.RECORDING
    assert started.started_at is not None

    stopped = manager.stop_recording("s1", "q1", b"audio-bytes")
    assert stopped.status == RecordingStatus.PROCESSING
    assert stopped.audio_size_bytes == len(b"audio-bytes")

    manager.set_transcription("s1", "q1", _make_transcription("my answer"))
    ready = manager.get_session("s1", "q1")
    assert ready.status == RecordingStatus.TRANSCRIBED
    assert ready.final_text == "my answer"
    assert ready.duration_seconds == 1.0

    submitted = manager.submit("s1", "q1")
    assert submitted is not None
    assert submitted.status == RecordingStatus.SUBMITTED
    assert submitted.submitted is True


def test_re_record_resets_state_until_max_reached():
    manager = ASRSessionManager()
    manager.create_session("s2", "q1", 1, "Question", "T")
    manager.set_transcription("s2", "q1", _make_transcription("first"))

    first_retry = manager.re_record("s2", "q1")
    assert first_retry is not None
    assert first_retry.recording_number == 2
    assert first_retry.status == RecordingStatus.IDLE
    assert first_retry.final_text is None

    second_retry = manager.re_record("s2", "q1")
    assert second_retry is not None
    assert second_retry.recording_number == 3

    third_retry = manager.re_record("s2", "q1")
    assert third_retry is None


def test_get_audio_stats_and_cleanup():
    manager = ASRSessionManager()
    manager.create_session("s3", "q1", 1, "Question", "T")
    stopped = manager.stop_recording("s3", "q1", b"abcdef")

    assert stopped.audio_size_bytes == 6
    assert stopped.audio_path is not None

    stats = manager.get_stats()
    assert stats["total_sessions"] == 1
    assert stats["states"]["processing"] == 1

    removed = manager.cleanup_old_sessions(max_age_hours=0)
    assert removed == 0  # only submitted sessions are eligible for cleanup
