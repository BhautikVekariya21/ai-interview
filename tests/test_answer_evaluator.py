"""
Unit tests for Module 5 answer evaluator.
"""

from app.services.answer_evaluator import AnswerEvaluator


class _FakeLLM:
    def __init__(self, payload):
        self.payload = payload
        self.active_provider = "test-provider"

    def generate(self, **kwargs):
        return self.payload


def _make_evaluator_without_init_llm():
    ev = AnswerEvaluator()
    ev._llm = None
    return ev


def test_parse_evaluation_supports_follow_up_question_alias():
    ev = _make_evaluator_without_init_llm()
    raw = """
    {
      "score": 84,
      "grade": "strong",
      "strengths": ["Good structure", "Relevant details"],
      "improvements": ["Add one metric", "Go deeper on trade-offs"],
      "feedback": "Solid response overall.",
      "follow_up_question": "What would you do differently at 10x scale?"
    }
    """
    parsed = ev._parse_evaluation(raw)
    assert parsed["score"] == 84
    assert parsed["grade"] == "Strong"
    assert parsed["followup_question"] == "What would you do differently at 10x scale?"


def test_normalize_evaluation_fields_enforces_contract():
    ev = _make_evaluator_without_init_llm()
    normalized = ev._normalize_evaluation_fields(
        {
            "score": 65,
            "grade": "unknown-grade",
            "strengths": ["Only one"],
            "improvements": [],
            "feedback": "",
            "followup_question": None,
        }
    )
    assert normalized["grade"] == "Adequate"
    assert len(normalized["strengths"]) >= 2
    assert len(normalized["improvements"]) >= 2
    assert len(normalized["feedback"]) > 20


def test_evaluate_uses_llm_json_and_returns_success():
    ev = _make_evaluator_without_init_llm()
    ev._llm = _FakeLLM(
        """
        {
          "score": 91,
          "grade": "Exceptional",
          "strengths": ["Deep technical reasoning", "Strong communication"],
          "improvements": ["Could add one concrete metric", "Mention testing strategy"],
          "feedback": "Excellent answer with clear technical depth and structure.",
          "followup_question": "How would you monitor this in production?"
        }
        """
    )
    res = ev.evaluate(
        question="Explain your API design choices.",
        answer="I used FastAPI, explicit schemas, and caching because latency mattered.",
        question_category="T",
    )
    assert res["success"] is True
    assert 0 <= res["score"] <= 100
    assert res["grade"] in {"Exceptional", "Strong", "Adequate", "Needs Work", "Insufficient"}
    assert len(res["strengths"]) >= 2
    assert len(res["improvements"]) >= 2
    assert isinstance(res["followup_question"], str)
    assert "authenticity_report" in res
    assert "ai_generated_score" in res["authenticity_report"]


def test_evaluate_falls_back_when_llm_fails():
    class _BrokenLLM:
        active_provider = "broken"

        def generate(self, **kwargs):
            raise RuntimeError("simulated failure")

    ev = _make_evaluator_without_init_llm()
    ev._llm = _BrokenLLM()
    res = ev.evaluate(
        question="Tell me about your debugging process.",
        answer="I start with logs, isolate hypotheses, and validate with targeted tests.",
        question_category="T",
    )
    assert res["success"] is True
    assert 0 <= res["score"] <= 100
    assert res["grade"] in {"Exceptional", "Strong", "Adequate", "Needs Work", "Insufficient"}
    assert len(res["strengths"]) >= 2
    assert len(res["improvements"]) >= 2
    assert isinstance(res["feedback"], str)
    assert "authenticity_report" in res
