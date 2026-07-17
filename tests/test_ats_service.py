"""Tests for the ATS scoring service."""

from app.schemas.schemas import ParsedResume, PersonalInfo, Skill, WorkExperience
from app.services.ats_service import compute_ats_score


def _sample_resume() -> ParsedResume:
    return ParsedResume(
        personal_info=PersonalInfo(email="a@b.com", github_url="gh", phone="123"),
        skills=[
            Skill(name="Python", category="language"),
            Skill(name="FastAPI", category="framework"),
            Skill(name="Docker", category="tool"),
        ],
        work_experience=[
            WorkExperience(
                company="X",
                role="Engineer",
                responsibilities=["Built API reducing latency by 40%", "Led team of 5"],
            )
        ],
        overall_parse_confidence=0.9,
    )


def test_ats_score_with_job_description():
    resume = _sample_resume()
    report = compute_ats_score(
        resume,
        "Python FastAPI Docker built led",
        "Looking for a Python FastAPI Kubernetes engineer",
    )
    assert report["report_type"] == "ats_score"
    assert 0 <= report["score"] <= 100
    assert report["has_job_description"] is True
    assert report["sub_scores"]["keyword_match"] is not None
    # Kubernetes is in the JD but not the resume.
    assert "kubernetes" in report["keyword_match"]["missing"]


def test_ats_score_without_job_description():
    resume = _sample_resume()
    report = compute_ats_score(resume, "Python FastAPI Docker built led", None)
    assert report["has_job_description"] is False
    assert report["sub_scores"]["keyword_match"] is None
    assert 0 <= report["score"] <= 100
    assert report["suggestions"]


def test_ats_penalizes_missing_sections():
    thin = ParsedResume(overall_parse_confidence=0.3)
    report = compute_ats_score(thin, "", None)
    assert report["score"] < 50
    assert report["structure"]["missing_sections"]
