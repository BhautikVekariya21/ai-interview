"""Compatibility and degraded-mode tests for Python 3.14 runtime paths."""

import pytest
from fastapi import HTTPException

from app.api import routes
from app.services.question_generator import DifficultyClassifier, DifficultyLevel


def test_get_parser_degraded_uses_fallback_parser(monkeypatch):
    monkeypatch.setattr(routes, "_parser", None)
    monkeypatch.setattr(routes, "ResumeParser", None)
    monkeypatch.setattr(routes, "_resume_parser_import_error", "torch missing")

    parser = routes.get_parser()
    assert parser is not None
    assert hasattr(parser, "parse")
    assert getattr(parser.ner_engine, "is_loaded", None) is False


def test_get_question_generator_degraded_raises_503(monkeypatch):
    monkeypatch.setattr(routes, "QuestionGenerator", None)
    monkeypatch.setattr(routes, "_question_generator_import_error", "torch missing")

    with pytest.raises(HTTPException) as exc:
        routes.get_question_generator()

    assert exc.value.status_code == 503
    assert "torch missing" in str(exc.value.detail)


def test_difficulty_classifier_heuristic_fallback():
    classifier = DifficultyClassifier()
    classifier.model = None

    level, conf = classifier.predict({"total_experience_years": 0.5})
    assert level == DifficultyLevel.EASY
    assert conf == pytest.approx(0.65)

    level, _ = classifier.predict({"total_experience_years": 3})
    assert level == DifficultyLevel.MEDIUM

    level, _ = classifier.predict({"total_experience_years": 6})
    assert level == DifficultyLevel.HARD

    level, _ = classifier.predict({"total_experience_years": 12})
    assert level == DifficultyLevel.EXPERT
