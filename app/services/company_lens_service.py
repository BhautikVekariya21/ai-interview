"""Company Lens — employer-published interview exams with standardized scorecards.

The idea: an employer pastes a job description, the platform generates a
custom, standardized interview exam from it, and a share link lets candidates
take the same exam so every result is directly comparable. This module owns
the two pure pieces of that pipeline:

1. ``generate_exam_questions`` — JD-grounded question authoring. The LLM writes
   the questions with the JD in context; when no provider is available a
   deterministic fallback derives questions from keywords extracted from the
   JD, so an exam can always be produced.

2. ``build_scorecard`` — standardized grading. Answers are scored through the
   existing answer evaluator (LLM-grounded); if it cannot run, a deterministic
   fallback still yields the same scorecard shape so candidates always get a
   verdict. ``generated_by`` marks which path produced the scores.

Neither function has side effects — persistence lives in the repository.
"""

from __future__ import annotations

import re
import secrets
from collections import Counter
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.llm_service import get_llm

# Categories mirror the rest of the platform (T/P/B/C/R).
CATEGORY_LABELS = {
    "T": "Technical",
    "P": "Project",
    "B": "Behavioral",
    "C": "Conceptual",
    "R": "Role Fit",
}

_CATEGORY_DESCRIPTIONS = {
    "T": "T (Technical depth — internals, edge cases, debugging, performance)",
    "P": "P (Project/experience — architecture, decisions, failures, scale)",
    "B": "B (Behavioral — real situations, STAR method, growth, conflict)",
    "C": "C (Conceptual — theory applied to the role's domain)",
    "R": "R (Role-fit — motivation, learning, trajectory, values)",
}

_DIFFICULTIES = ("easy", "medium", "hard", "expert")

MIN_QUESTIONS = 3
MAX_QUESTIONS = 20

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

# Words too common to be useful JD keywords.
_STOPWORDS = {
    "the", "and", "for", "with", "you", "will", "your", "our", "are", "that",
    "this", "have", "from", "what", "who", "when", "where", "why", "how",
    "has", "had", "was", "were", "been", "being", "can", "could", "should",
    "would", "may", "might", "must", "not", "but", "also", "within", "across",
    "about", "into", "over", "under", "between", "through", "during", "than",
    "then", "they", "them", "their", "there", "these", "those", "other",
    "such", "able", "well", "work", "working", "role", "team", "candidate",
    "experience", "job", "position", "company", "responsibilities",
    "responsibility", "requirements", "requirement", "skills", "plus",
    "minimum", "preferred", "years", "year", "including", "including",
    "related", "etc", "via", "per", "one", "two", "three", "new", "using",
}

# Category weight used for the deterministic generation and scorecard math.
_CATEGORY_WEIGHTS = {"T": 0.30, "P": 0.20, "B": 0.20, "C": 0.20, "R": 0.10}


# ══════════════════════════════════════════════════════════════════════
#  Token helpers
# ══════════════════════════════════════════════════════════════════════


def mint_share_token() -> str:
    """An unguessable, URL-safe token for share links."""
    return secrets.token_urlsafe(16)


def is_valid_token(token: str) -> bool:
    return bool(token) and bool(_TOKEN_RE.match(token))


# ══════════════════════════════════════════════════════════════════════
#  Exam generation
# ══════════════════════════════════════════════════════════════════════


def clamp_question_count(count: Any) -> int:
    try:
        value = int(count or 0)
    except (TypeError, ValueError):
        value = MIN_QUESTIONS
    return max(MIN_QUESTIONS, min(MAX_QUESTIONS, value))


def _normalize_difficulty(difficulty: Any) -> str:
    value = str(difficulty or "medium").strip().lower()
    return value if value in _DIFFICULTIES else "medium"


def _jd_keywords(job_description: str, limit: int = 8) -> List[str]:
    """Top distinctive terms from a JD, for the deterministic fallback."""
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", job_description or "")
    counts = Counter(
        token.lower().strip(".#+-") for token in tokens
        if token.lower().strip(".#+-") not in _STOPWORDS
    )
    keywords = [word for word, _ in counts.most_common(limit) if word]
    return keywords or ["the role's core skills"]


def generate_exam_questions(
    *,
    job_description: str,
    target_role: str = "",
    question_count: int = 10,
    difficulty: str = "medium",
) -> List[Dict[str, Any]]:
    """Produce a JD-grounded question set for an exam.

    Returns a list of dicts with ``question``, ``category`` (T/P/B/C/R),
    ``difficulty``, and ``ideal_answer``. LLM-first, deterministic fallback.
    """
    count = clamp_question_count(question_count)
    difficulty = _normalize_difficulty(difficulty)

    llm = get_llm()
    questions: List[Dict[str, Any]] = []
    if llm.is_available:
        try:
            generated = _generate_from_llm(
                job_description=job_description,
                target_role=target_role,
                count=count,
                difficulty=difficulty,
                llm=llm,
            )
            if generated:
                questions = generated[:count]
            else:
                logger.warning("Company Lens: LLM returned no parseable questions")
        except Exception as exc:  # pragma: no cover - provider dependent
            logger.warning(f"Company Lens: LLM generation failed: {exc}")

    # Honor question_count even when the LLM under-delivers: pad with
    # deterministic JD-grounded questions (deduplicated by exact text).
    if len(questions) < count:
        logger.warning(
            f"Company Lens: {len(questions)} LLM questions, padding to {count}"
        )
        fallback = _fallback_exam_questions(
            job_description=job_description,
            target_role=target_role,
            count=count,
            difficulty=difficulty,
        )
        seen = {question["question"].strip().lower() for question in questions}
        for question in fallback:
            if len(questions) >= count:
                break
            key = question["question"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            questions.append(question)

    if not questions:
        logger.warning("Company Lens: using deterministic JD fallback questions")
        questions = _fallback_exam_questions(
            job_description=job_description,
            target_role=target_role,
            count=count,
            difficulty=difficulty,
        )
    return questions[:count]


def _generate_from_llm(
    *,
    job_description: str,
    target_role: str,
    count: int,
    difficulty: str,
    llm: Any,
) -> Optional[List[Dict[str, Any]]]:
    """Ask the LLM to author the exam from the JD. Returns parsed questions."""
    category_prompt = "; ".join(_CATEGORY_DESCRIPTIONS.values())
    system_prompt = (
        "You are an expert hiring assessor writing a standardized interview "
        "exam. The exam must be grounded in the job description so every "
        "candidate is measured against the same, role-specific bar. "
        "Return ONLY valid JSON — no prose, no markdown fences."
    )
    user_prompt = f"""Job title: {target_role or 'Not specified'}

Job description:
{job_description}

Write {count} interview questions for this role as a JSON array. Every object:

{{
  "question": "one specific, answerable interview question that references the job description's skills or responsibilities",
  "category": "T | P | B | C | R",
  "difficulty": "{difficulty}",
  "ideal_answer": "2-4 key points a strong answer must cover"
}}

Categories: {category_prompt}
Mix categories sensibly for the role (roughly 30% technical, 20% project, 20% behavioral, 20% conceptual, 10% role-fit). Questions must reference specifics from the job description. Start with ["""

    result = llm.generate_json(prompt=user_prompt, system_prompt=system_prompt)
    return _parse_generated(result)


def _parse_generated(result: Any) -> Optional[List[Dict[str, Any]]]:
    """Defensively parse the LLM's JSON into clean question dicts."""
    if result is None:
        return None
    items: List[Any] = []
    if isinstance(result, list):
        items = result
    elif isinstance(result, dict):
        for key in ("questions", "items", "data", "results"):
            if key in result and isinstance(result[key], list):
                items = result[key]
                break
        else:
            items = [result]

    questions: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = ""
        for key in ("question", "q", "text"):
            value = item.get(key)
            if isinstance(value, str) and len(value.strip()) >= 12:
                text = value.strip()
                break
        if not text:
            continue
        category = str(item.get("category", "T")).strip().upper()
        if category not in CATEGORY_LABELS:
            category = "T"
        difficulty = _normalize_difficulty(item.get("difficulty"))
        ideal = item.get("ideal_answer")
        questions.append(
            {
                "question": text,
                "category": category,
                "difficulty": difficulty,
                "ideal_answer": str(ideal).strip() if ideal else "",
            }
        )
    return questions or None


def _fallback_exam_questions(
    *,
    job_description: str,
    target_role: str,
    count: int,
    difficulty: str,
) -> List[Dict[str, Any]]:
    """Deterministic JD-grounded questions when no LLM is available."""
    keywords = _jd_keywords(job_description)
    role = (target_role or "this role").strip()

    builders = {
        "T": lambda kw: (
            f"The role centers on {kw}. Describe a production situation where "
            "you applied it, the hardest correctness problem you hit, and how "
            "you validated the result."
        ),
        "P": lambda kw: (
            f"Walk me through a project where you used {kw} end to end. What "
            "architecture did you choose, what trade-offs did you accept, and "
            "what would you rebuild differently?"
        ),
        "B": lambda kw: (
            "Tell me about a time you disagreed with a teammate's technical "
            "decision. How did you resolve it, and what did you learn about "
            "communicating under pressure?"
        ),
        "C": lambda kw: (
            f"Explain the underlying concept of {kw} well enough that a "
            "non-specialist understands it — and when you would deliberately "
            "avoid it in a design."
        ),
        "R": lambda kw: (
            f"Why {role}, and how does your experience with {kw} map to the "
            "responsibilities described in the job description?"
        ),
    }

    distribution = {}
    allocated = 0
    for category, weight in _CATEGORY_WEIGHTS.items():
        number = max(1, round(count * weight))
        distribution[category] = number
        allocated += number
    if allocated != count:
        distribution["T"] = max(1, distribution["T"] + (count - allocated))

    difficulties = _spread_difficulties(count, difficulty)

    questions: List[Dict[str, Any]] = []
    cursor = 0
    for category, number in distribution.items():
        for _ in range(number):
            keyword = keywords[cursor % len(keywords)]
            questions.append(
                {
                    "question": builders[category](keyword),
                    "category": category,
                    "difficulty": difficulties[cursor % len(difficulties)],
                    "ideal_answer": (
                        "Specific, concrete example tied to the job description; "
                        "clear reasoning about trade-offs; honest about failure."
                    ),
                }
            )
            cursor += 1
    return questions[:count]


def _spread_difficulties(count: int, base: str) -> List[str]:
    """Difficulty labels spread around the base, mirroring the platform's mix."""
    index = _DIFFICULTIES.index(base)
    lower = _DIFFICULTIES[max(0, index - 1)]
    higher = _DIFFICULTIES[min(len(_DIFFICULTIES) - 1, index + 1)]
    lower_n = max(0, round(count * 0.20))
    higher_n = max(0, count - lower_n - round(count * 0.55))
    base_n = count - lower_n - higher_n
    return [lower] * lower_n + [base] * base_n + [higher] * higher_n


# ══════════════════════════════════════════════════════════════════════
#  Scorecards
# ══════════════════════════════════════════════════════════════════════


def grade_for(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B+"
    if score >= 60:
        return "B"
    return "C"


def recommendation_for(score: float) -> str:
    if score >= 80:
        return "Strong recommend"
    if score >= 65:
        return "Recommend"
    if score >= 50:
        return "Neutral"
    return "Not recommended"


def hire_decision_for(score: float) -> str:
    if score >= 75:
        return "hire"
    if score >= 55:
        return "consider"
    return "no_hire"


def build_scorecard(
    *,
    qa_pairs: List[Dict[str, Any]],
    candidate_name: str,
    exam_title: str,
    evaluator: Any = None,
) -> Dict[str, Any]:
    """Score an exam attempt into a standardized scorecard document.

    The LLM-backed evaluator is preferred; ``_fallback_scorecard`` guarantees
    the same shape when it cannot run (or when a test injects ``evaluator=None``).
    """
    pairs = [q for q in (qa_pairs or []) if isinstance(q, dict)]
    if evaluator is not None:
        try:
            result = evaluator.evaluate_batch(qa_pairs=pairs, resume_context=None)
            if result:
                return _scorecard_from_evaluation(
                    result=result,
                    candidate_name=candidate_name,
                    exam_title=exam_title,
                )
        except Exception as exc:  # pragma: no cover - provider dependent
            logger.warning(f"Company Lens: evaluator failed, using fallback: {exc}")

    return _fallback_scorecard(
        qa_pairs=pairs,
        candidate_name=candidate_name,
        exam_title=exam_title,
    )


def _scorecard_from_evaluation(
    *,
    result: Dict[str, Any],
    candidate_name: str,
    exam_title: str,
) -> Dict[str, Any]:
    """Normalise the answer evaluator's batch output into the lens shape."""
    evaluations = result.get("evaluations") or []
    answers: List[Dict[str, Any]] = []
    for entry in evaluations:
        if not isinstance(entry, dict):
            continue
        authenticity = entry.get("authenticity_report")
        answers.append(
            {
                "question_number": entry.get("question_number"),
                "question": entry.get("question", ""),
                "category": entry.get("category", "T"),
                "answer": entry.get("answer", ""),
                "score": entry.get("score", 0),
                "grade": entry.get("grade", "Insufficient"),
                "feedback": entry.get("feedback", ""),
                "strengths": list(entry.get("strengths") or []),
                "improvements": list(entry.get("improvements") or []),
                "authenticity": authenticity if isinstance(authenticity, dict) else None,
            }
        )

    overall = result.get("overall_score")
    if not isinstance(overall, (int, float)):
        scored = [a for a in answers if isinstance(a["score"], (int, float))]
        overall = round(sum(a["score"] for a in scored) / len(scored)) if scored else 0

    return {
        "candidate_name": candidate_name,
        "exam_title": exam_title,
        "overall_score": int(round(float(overall))),
        "overall_grade": result.get("overall_grade") or grade_for(float(overall)),
        "recommendation": result.get("recommendation") or recommendation_for(float(overall)),
        "hire_decision": result.get("hire_decision") or hire_decision_for(float(overall)),
        "summary": result.get("summary") or "",
        "category_breakdown": dict(result.get("category_breakdown") or {}),
        "answered_questions": len(answers),
        "total_questions": len(answers),
        "answers": answers,
        "plagiarism_summary": (
            result.get("plagiarism_summary")
            if isinstance(result.get("plagiarism_summary"), dict)
            else None
        ),
        "generated_by": "evaluator",
    }


def _fallback_scorecard(
    *,
    qa_pairs: List[Dict[str, Any]],
    candidate_name: str,
    exam_title: str,
) -> Dict[str, Any]:
    """Deterministic scoring when no evaluator is available.

    Uses answer presence and depth as a proxy for quality: empty answers score
    zero, short answers score low, structured answers score higher. Honest,
    stable, and clearly labelled ``generated_by: fallback``.
    """
    answers: List[Dict[str, Any]] = []
    scores: List[float] = []
    category_scores: Dict[str, List[float]] = {}

    for i, qa in enumerate(qa_pairs):
        question = str(qa.get("question") or "")
        answer = str(qa.get("answer") or "").strip()
        category = str(qa.get("category") or "T").upper()
        words = len(answer.split())

        if not answer:
            score, grade, feedback = 0, "Insufficient", "This question was not answered."
        elif words < 15:
            score, grade, feedback = 35, "C", (
                "The answer is too brief to demonstrate depth — expand with a concrete example."
            )
        elif words < 40:
            score, grade, feedback = 55, "B", (
                "A reasonable start, but it needs a specific example and explicit reasoning."
            )
        elif words < 80:
            score, grade, feedback = 70, "B+", (
                "Solid answer with a concrete example — sharpen the trade-offs and outcome."
            )
        else:
            score, grade, feedback = 82, "A", (
                "Strong, structured answer with a clear example and reasoning."
            )

        scores.append(float(score))
        category_scores.setdefault(category, []).append(float(score))
        answers.append(
            {
                "question_number": qa.get("question_number", i + 1),
                "question": question,
                "category": category,
                "answer": answer,
                "score": score,
                "grade": grade,
                "feedback": feedback,
                "strengths": ["Answered with relevant content"] if answer else [],
                "improvements": (
                    ["Provide a concrete, detailed example"] if score < 70 and answer else []
                ),
                "authenticity": None,
            }
        )

    overall = round(sum(scores) / len(scores)) if scores else 0
    breakdown = {
        category: round(sum(values) / len(values))
        for category, values in category_scores.items()
    }
    summary = (
        f"{candidate_name} answered {len(answers)} questions with an average of "
        f"{overall}/100. "
        + (
            "Depth of answer is the limiting factor — expand brief responses with "
            "concrete examples and reasoning."
            if overall < 70
            else "Answers were consistently substantive and structured."
        )
    )

    return {
        "candidate_name": candidate_name,
        "exam_title": exam_title,
        "overall_score": overall,
        "overall_grade": grade_for(float(overall)),
        "recommendation": recommendation_for(float(overall)),
        "hire_decision": hire_decision_for(float(overall)),
        "summary": summary,
        "category_breakdown": breakdown,
        "answered_questions": len(answers),
        "total_questions": len(answers),
        "answers": answers,
        "plagiarism_summary": None,
        "generated_by": "fallback",
    }
