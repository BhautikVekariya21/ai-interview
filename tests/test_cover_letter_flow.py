import pytest

import app.services.cover_letter_service as cover_letter_module
import app.services.resume_roaster as resume_roaster_module
from app.schemas.cover_letter_schemas import CoverLetterResponse


class DummyLLM:
    def __init__(self, available: bool):
        self.is_available = available

    def generate_json(self, *args, **kwargs):
        return None


def build_cover_letter_service(llm):
    service = cover_letter_module.CoverLetterService.__new__(cover_letter_module.CoverLetterService)
    service.llm = llm
    return service


def build_resume_roaster_service(llm):
    service = resume_roaster_module.ResumeRoasterService.__new__(resume_roaster_module.ResumeRoasterService)
    service.llm = llm
    return service


class TestCoverLetterService:
    def test_raises_configuration_error_when_llm_unavailable(self):
        service = build_cover_letter_service(DummyLLM(available=False))

        with pytest.raises(ValueError, match="No LLM API keys configured"):
            service.generate_cover_letter("Backend engineer role")

    def test_raises_generation_error_when_llm_returns_no_json(self):
        service = build_cover_letter_service(DummyLLM(available=True))

        with pytest.raises(ValueError, match="Failed to generate cover letter from AI"):
            service.generate_cover_letter("Backend engineer role")


class TestResumeRoasterService:
    def test_raises_configuration_error_when_llm_unavailable(self):
        service = build_resume_roaster_service(DummyLLM(available=False))

        with pytest.raises(ValueError, match="No LLM API keys configured"):
            service.roast_resume(b"Resume text with enough detail to parse.", "resume.txt")

    def test_raises_generation_error_when_llm_returns_no_json(self):
        service = build_resume_roaster_service(DummyLLM(available=True))

        with pytest.raises(ValueError, match="Failed to generate roast from AI"):
            service.roast_resume(b"Resume text with enough detail to parse.", "resume.txt")


class TestCoverLetterApi:
    @pytest.mark.asyncio
    async def test_generate_cover_letter_endpoint_accepts_form_and_file(self, async_client, monkeypatch):
        class StubService:
            def __init__(self):
                self.calls = []

            def generate_cover_letter(self, job_description, file_content=None, filename=None):
                self.calls.append((job_description, file_content, filename))
                return CoverLetterResponse(success=True, cover_letter="Tailored letter")

        stub = StubService()
        monkeypatch.setattr(cover_letter_module, "get_cover_letter_service", lambda: stub)

        response = await async_client.post(
            "/cover-letter/generate",
            data={"job_description": "Need a Python engineer"},
            files={"file": ("resume.txt", b"Resume body", "text/plain")},
        )

        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "cover_letter": "Tailored letter",
            "message": None,
        }
        assert stub.calls == [("Need a Python engineer", b"Resume body", "resume.txt")]
