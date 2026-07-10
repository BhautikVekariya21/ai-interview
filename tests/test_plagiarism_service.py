from app.services.plagiarism_service import (
    analyze_answer_authenticity,
    analyze_resume_plagiarism,
    summarize_batch_authenticity,
)


def test_resume_plagiarism_flags_generic_template_language():
    text = """
    Results-driven professional with a proven track record in fast-paced environments.
    Highly motivated team player with excellent communication skills.
    Results-driven professional with a proven track record in fast-paced environments.
    """

    report = analyze_resume_plagiarism(text)

    assert report["report_type"] == "resume_plagiarism"
    assert report["score"] > 0
    assert report["highlights"]
    assert report["suggestions"]


def test_answer_authenticity_rewards_personal_specific_details():
    answer = """
    I built a FastAPI caching layer for our interview service and reduced repeated API calls by 42 percent.
    My team used Valkey for shared cache storage, and I debugged a serialization issue during rollout.
    """

    report = analyze_answer_authenticity(answer, "How did you improve backend performance?")

    assert report["report_type"] == "answer_authenticity"
    assert report["ai_generated_score"] < 70
    assert report["metrics"]["personal_experience_markers"] >= 1


def test_batch_authenticity_summary_aggregates_reports():
    summary = summarize_batch_authenticity([
        {
            "question_number": 1,
            "ai_generated_score": 62,
            "plagiarism_score": 48,
            "summary": "Generic wording",
            "suggestions": ["Add metrics"],
        },
        {
            "question_number": 2,
            "ai_generated_score": 28,
            "plagiarism_score": 20,
            "summary": "More personal",
            "suggestions": ["Add metrics", "Use a real project example"],
        },
    ])

    assert summary["average_ai_generated_score"] == 45.0
    assert summary["average_plagiarism_score"] == 34.0
    assert summary["highest_risk_question"]["question_number"] == 1
    assert "Add metrics" in summary["suggestions"]
