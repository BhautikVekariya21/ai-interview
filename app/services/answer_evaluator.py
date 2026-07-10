"""
Module 5 — Answer Evaluation Engine.
FIXED: Properly handles all data types in strengths/improvements.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.services.cache_service import get_cache
from app.services.plagiarism_service import (
    analyze_answer_authenticity,
    summarize_batch_authenticity,
)


class AnswerEvaluator:
    """
    Evaluates interview answers using LLM.
    """

    def __init__(self):
        self._llm = None
        self._cache = get_cache()
        self._initialize_llm()
        logger.info("  ✓ Answer Evaluator initialized")

    def _initialize_llm(self):
        """Initialize LLM service."""
        try:
            from app.services.llm_service import get_llm

            self._llm = get_llm()
            if self._llm:
                logger.debug(f"  Evaluator using LLM provider: {self._llm.active_provider}")
            else:
                logger.warning("  LLM service returned None")
        except ImportError as e:
            logger.warning(f"LLM service not available: {e}")
        except Exception as e:
            logger.warning(f"LLM service init failed: {e}")

    def _ensure_string_list(self, items: Any) -> List[str]:
        """
        Convert any input to a list of strings.
        Handles: strings, lists of strings, lists of dicts, None, etc.
        """
        if items is None:
            return []

        if isinstance(items, str):
            return [items] if items.strip() else []

        if not isinstance(items, list):
            return [str(items)] if items else []

        result = []
        for item in items:
            if item is None:
                continue
            elif isinstance(item, str):
                if item.strip():
                    result.append(item.strip())
            elif isinstance(item, dict):
                # Extract text from dict - try common keys
                text = (
                    item.get("text")
                    or item.get("point")
                    or item.get("strength")
                    or item.get("improvement")
                    or item.get("message")
                    or item.get("description")
                    or item.get("value")
                    or ""
                )
                if isinstance(text, str) and text.strip():
                    result.append(text.strip())
                elif not text:
                    # Last resort: convert first string value found
                    for v in item.values():
                        if isinstance(v, str) and v.strip():
                            result.append(v.strip())
                            break
            else:
                # Convert to string
                text = str(item).strip()
                if text and text not in ["None", "null", "{}", "[]"]:
                    result.append(text)

        return result

    def generate_hint(self, question: str) -> str:
        """Generate a supportive, contextual hint for a question."""
        if not self._llm:
            return "Consider breaking down the problem into smaller parts and explaining your thought process step by step."

        prompt = f"The candidate is struggling to answer this interview question: '{question}'. Provide a brief, supportive 1-2 sentence hint that points them in the right direction without giving away the direct answer. DO NOT use markdown, return just plain text."

        try:
            hint = self._llm.generate(
                prompt=prompt,
                system_prompt="You are a supportive, expert technical interviewer.",
                max_tokens=60,
                temperature=0.6,
            )
            return hint.strip() if hint else "Think about how you would approach this practically."
        except Exception as e:
            logger.warning(f"Hint generation failed: {e}")
            return "Think about this from the perspective of core principles and best practices."

    def evaluate(
        self,
        question: str,
        answer: str,
        question_category: str = "T",
        resume_context: Optional[Dict[str, Any]] = None,
        generate_followup: bool = True,
    ) -> Dict[str, Any]:
        """Evaluate a candidate's answer."""
        start_time = time.time()

        # Handle empty/short answers
        if not answer or len(answer.strip()) < 10:
            authenticity_report = analyze_answer_authenticity(answer or "", question)
            return {
                "success": True,
                "score": 0,
                "grade": "Insufficient",
                "strengths": ["No answer provided"],
                "improvements": ["Please provide a detailed response"],
                "feedback": "Please provide a more detailed response to demonstrate your knowledge.",
                "followup_question": None,
                "authenticity_report": authenticity_report,
                "word_count": len(answer.split()) if answer else 0,
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        # Check cache
        cache_payload = json.dumps(
            {
                "question": question[:200],
                "answer": answer[:500],
                "category": question_category,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        cache_key = self._cache.make_key("eval:answer", cache_payload)
        cached = self._cache.get(cache_key)
        if isinstance(cached, dict) and cached.get("score") is not None:
            cached = dict(cached)
            cached["word_count"] = len(answer.split())
            cached["processing_time_ms"] = (time.time() - start_time) * 1000
            cached["success"] = True
            cached["authenticity_report"] = analyze_answer_authenticity(answer, question)
            # Ensure cached strengths/improvements are strings
            cached["strengths"] = self._ensure_string_list(cached.get("strengths"))
            cached["improvements"] = self._ensure_string_list(cached.get("improvements"))
            return cached

        # Try LLM evaluation
        if self._llm:
            try:
                prompt = self._build_evaluation_prompt(
                    question=question,
                    answer=answer,
                    category=question_category,
                    resume_context=resume_context,
                    generate_followup=generate_followup,
                )

                response_text = self._llm.generate(
                    prompt=prompt,
                    system_prompt="You are a technical interview evaluator. Return strict JSON only.",
                    max_tokens=1024,
                    temperature=0.3,
                )

                if response_text and isinstance(response_text, str):
                    evaluation = self._parse_evaluation(response_text)
                    evaluation["authenticity_report"] = analyze_answer_authenticity(
                        answer, question
                    )
                    evaluation["word_count"] = len(answer.split())
                    evaluation["processing_time_ms"] = (time.time() - start_time) * 1000
                    evaluation["success"] = True

                    logger.info(
                        f"LLM Evaluation: score={evaluation.get('score', 0)}, "
                        f"grade={evaluation.get('grade', 'Unknown')}"
                    )

                    self._cache.set(cache_key, evaluation, ttl_seconds=3600)
                    return evaluation

            except Exception as e:
                logger.warning(f"LLM evaluation failed: {e}")

        # Fallback to heuristic evaluation
        logger.info("Using heuristic evaluation fallback")
        fallback = self._heuristic_evaluation(
            question=question,
            answer=answer,
            category=question_category,
        )
        fallback["authenticity_report"] = analyze_answer_authenticity(answer, question)
        fallback["word_count"] = len(answer.split())
        fallback["processing_time_ms"] = (time.time() - start_time) * 1000
        fallback["success"] = True

        self._cache.set(cache_key, fallback, ttl_seconds=900)
        return fallback

    def _build_evaluation_prompt(
        self,
        question: str,
        answer: str,
        category: str,
        resume_context: Optional[Dict[str, Any]] = None,
        generate_followup: bool = True,
    ) -> str:
        """Build the evaluation prompt for LLM."""

        category_context = {
            "T": "Technical depth question - evaluate technical accuracy and depth",
            "P": "Project-based question - evaluate practical experience and outcomes",
            "B": "Behavioral question - evaluate situation handling and soft skills",
            "C": "Conceptual question - evaluate theoretical understanding",
            "R": "Role-fit question - evaluate motivation and career alignment",
        }

        context = category_context.get(category, "General interview question")

        prompt = f"""Evaluate this interview answer.

QUESTION TYPE: {context}

QUESTION:
"{question}"

ANSWER:
"{answer}"

Return EXACTLY one valid JSON object (no markdown, no extra text):
{{
  "score": <integer 0-100>,
  "grade": "<Exceptional|Strong|Adequate|Needs Work|Insufficient>",
  "strengths": ["<strength 1 as plain string>", "<strength 2 as plain string>"],
  "improvements": ["<improvement 1 as plain string>", "<improvement 2 as plain string>"],
  "feedback": "<3-4 sentence constructive feedback as plain string>",
  "ideal_answer": "<a 3-4 sentence perfect, expert-level answer as plain string>",
  "followup_question": "<1 follow-up question as plain string>"
}}

IMPORTANT: strengths and improvements MUST be arrays of plain strings, NOT objects.

SCORING:
- 90-100: Exceptional - comprehensive, expert-level
- 75-89: Strong - good understanding with details
- 60-74: Adequate - basic understanding, limited depth
- 40-59: Needs Work - incomplete or partially incorrect
- 0-39: Insufficient - does not address the question
"""
        return prompt

    def _parse_evaluation(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into evaluation dict."""

        cleaned = llm_response.strip()

        # Remove markdown code blocks
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            json_match = re.search(r"\{[\s\S]*\}", cleaned)

            if json_match:
                evaluation = json.loads(json_match.group())

                score = evaluation.get("score", 50)
                if isinstance(score, str):
                    match = re.search(r"\d+", score)
                    score = int(match.group()) if match else 50

                return self._normalize_evaluation(
                    {
                        "score": min(100, max(0, int(score))),
                        "grade": str(evaluation.get("grade", "Adequate")),
                        "strengths": evaluation.get("strengths", []),
                        "improvements": evaluation.get("improvements", []),
                        "feedback": str(evaluation.get("feedback", "")),
                        "ideal_answer": evaluation.get("ideal_answer"),
                        "followup_question": evaluation.get("followup_question")
                        or evaluation.get("follow_up_question"),
                    }
                )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse evaluation JSON: {e}")
        except Exception as e:
            logger.warning(f"Error parsing evaluation: {e}")

        # Fallback parsing
        score = 50
        score_match = re.search(r'"score"\s*:\s*(\d+)', cleaned)
        if score_match:
            score = min(100, max(0, int(score_match.group(1))))

        return self._normalize_evaluation(
            {
                "score": score,
                "grade": "Adequate",
                "strengths": ["Attempted to answer the question"],
                "improvements": ["Add more specific details"],
                "feedback": "Your answer has been recorded.",
                "ideal_answer": None,
                "followup_question": None,
            }
        )

    def _normalize_evaluation(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize evaluation fields - ensure all lists contain strings."""

        # Normalize grade
        valid_grades = {
            "exceptional": "Exceptional",
            "strong": "Strong",
            "adequate": "Adequate",
            "needs work": "Needs Work",
            "insufficient": "Insufficient",
        }
        g = str(ev.get("grade", "Adequate")).strip().lower()
        ev["grade"] = valid_grades.get(g, "Adequate")

        # CRITICAL: Convert strengths and improvements to string lists
        strengths = self._ensure_string_list(ev.get("strengths"))
        improvements = self._ensure_string_list(ev.get("improvements"))

        # Ensure we have at least some content
        if not strengths:
            strengths = ["Attempted to answer the question"]
        if not improvements:
            improvements = ["Consider adding more specific examples"]

        ev["strengths"] = strengths[:3]
        ev["improvements"] = improvements[:3]

        # Ensure feedback is a string
        fb = ev.get("feedback", "")
        if isinstance(fb, dict):
            fb = fb.get("text", "") or fb.get("message", "") or str(fb)
        fb = str(fb).strip()
        if not fb:
            fb = "Your response has been evaluated. Focus on providing more specific examples."
        ev["feedback"] = fb

        # Ensure followup_question is a string or None
        fq = ev.get("followup_question")
        if isinstance(fq, dict):
            fq = fq.get("question", "") or fq.get("text", "") or None
        if fq:
            ev["followup_question"] = str(fq).strip()
        else:
            ev["followup_question"] = None

        # Ensure ideal_answer is a string or None
        ia = ev.get("ideal_answer")
        if isinstance(ia, dict):
            ia = ia.get("answer", "") or ia.get("text", "") or None
        if ia:
            ev["ideal_answer"] = str(ia).strip()
        else:
            ev["ideal_answer"] = None

        return ev

    def _normalize_evaluation_fields(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        """Backward-compatible helper retained for older tests and callers."""
        normalized = self._normalize_evaluation(ev)
        while len(normalized["strengths"]) < 2:
            normalized["strengths"].append("Shows baseline engagement with the question")
        while len(normalized["improvements"]) < 2:
            normalized["improvements"].append("Add more concrete evidence and depth")
        if len(normalized["feedback"]) <= 20:
            normalized["feedback"] = (
                "Your response was reviewed successfully. Add more concrete detail, reasoning, "
                "and examples to make the answer stronger."
            )
        return normalized

    def _heuristic_evaluation(
        self,
        question: str,
        answer: str,
        category: str,
    ) -> Dict[str, Any]:
        """Rule-based fallback when LLM is unavailable."""
        words = answer.split()
        wc = len(words)
        score = 35

        if wc >= 15:
            score += 15
        if wc >= 35:
            score += 15
        if wc >= 70:
            score += 10

        lower = answer.lower()

        tech_markers = [
            "because",
            "trade-off",
            "latency",
            "throughput",
            "testing",
            "monitor",
            "failure",
            "rollback",
            "cache",
            "index",
            "api",
            "architecture",
            "database",
            "server",
            "client",
            "protocol",
        ]
        score += min(25, sum(1 for m in tech_markers if m in lower) * 4)

        if category in ("B", "R"):
            if any(k in lower for k in ["situation", "task", "action", "result"]):
                score += 8

        score = int(max(0, min(100, score)))

        if score >= 90:
            grade = "Exceptional"
        elif score >= 75:
            grade = "Strong"
        elif score >= 60:
            grade = "Adequate"
        elif score >= 40:
            grade = "Needs Work"
        else:
            grade = "Insufficient"

        # Generate string lists
        strengths = []
        if wc >= 25:
            strengths.append("Provided a reasonably detailed response")
        if any(k in lower for k in ["example", "for instance", "project"]):
            strengths.append("Included relevant examples")
        if any(k in lower for k in ["first", "then", "finally", "step"]):
            strengths.append("Used structured explanation")
        if not strengths:
            strengths.append("Attempted to answer the question")
        if len(strengths) < 2:
            strengths.append("Used at least one concrete troubleshooting or explanation step")

        improvements = []
        if wc < 25:
            improvements.append("Provide more detail in your response")
        if not any(k in lower for k in ["because", "since", "therefore"]):
            improvements.append("Explain your reasoning more clearly")
        if not any(k in lower for k in ["example", "instance", "project"]):
            improvements.append("Include specific examples from experience")
        if not improvements:
            improvements.append("Consider adding technical depth")
        if len(improvements) < 2:
            improvements.append("Tie the answer more closely to impact, trade-offs, or outcomes")

        return {
            "score": score,
            "grade": grade,
            "strengths": strengths[:3],
            "improvements": improvements[:3],
            "feedback": (
                f"Your answer scored {score}/100. "
                f"To improve, focus on providing specific examples and explaining your reasoning. "
                f"Structure your responses clearly and relate them to real experience."
            ),
            "ideal_answer": (
                "An ideal answer would directly address the question using the STAR method (Situation, Task, Action, Result). "
                "It would include specific technical details, explain the 'why' behind decisions, "
                "and conclude with clear, measurable outcomes."
            ),
            "followup_question": "Can you provide a specific example from your experience?",
        }

    def evaluate_batch(
        self,
        qa_pairs: List[Dict[str, Any]],
        resume_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evaluate multiple Q&A pairs and generate overall assessment."""
        evaluations = []
        total_score = 0
        category_scores: Dict[str, List[int]] = {}

        for i, qa in enumerate(qa_pairs):
            logger.info(f"Evaluating answer {i + 1}/{len(qa_pairs)}")

            # Access dict with .get()
            question = qa.get("question", "") if isinstance(qa, dict) else ""
            answer = qa.get("answer", "") if isinstance(qa, dict) else ""
            category = qa.get("category", "T") if isinstance(qa, dict) else "T"

            if not answer.strip():
                # No answer provided
                evaluation = {
                    "success": True,
                    "score": 0,
                    "grade": "Insufficient",
                    "strengths": ["Question was presented"],
                    "improvements": ["No answer was provided"],
                    "feedback": "This question was not answered.",
                    "followup_question": None,
                    "authenticity_report": analyze_answer_authenticity("", question),
                    "word_count": 0,
                    "processing_time_ms": 0,
                }
            else:
                evaluation = self.evaluate(
                    question=question,
                    answer=answer,
                    question_category=category,
                    resume_context=resume_context,
                    generate_followup=False,
                )

            # Ensure strengths/improvements are string lists
            evaluation["strengths"] = self._ensure_string_list(evaluation.get("strengths"))
            evaluation["improvements"] = self._ensure_string_list(evaluation.get("improvements"))

            # Build evaluation entry
            eval_entry = {
                "question_number": qa.get("question_number", i + 1)
                if isinstance(qa, dict)
                else i + 1,
                "question": question,
                "answer": answer,
                "category": category,
                "success": evaluation.get("success", True),
                "score": evaluation.get("score", 0),
                "grade": evaluation.get("grade", "Insufficient"),
                "strengths": evaluation.get("strengths", []),
                "improvements": evaluation.get("improvements", []),
                "feedback": str(evaluation.get("feedback", "")),
                "ideal_answer": evaluation.get("ideal_answer"),
                "followup_question": evaluation.get("followup_question"),
                "authenticity_report": evaluation.get("authenticity_report"),
                "word_count": evaluation.get("word_count", 0),
            }

            evaluations.append(eval_entry)

            _raw_score = evaluation.get("score", 0)
            score = int(_raw_score) if isinstance(_raw_score, (int, float)) else 0
            total_score += score

            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(score)

        num_questions = len(evaluations)
        avg_score = total_score / num_questions if num_questions > 0 else 0

        # Determine overall grade
        if avg_score >= 90:
            overall_grade = "Exceptional"
            recommendation = "Highly recommended for the position"
        elif avg_score >= 75:
            overall_grade = "Strong"
            recommendation = "Recommended for the position"
        elif avg_score >= 60:
            overall_grade = "Adequate"
            recommendation = "Consider with some reservations"
        elif avg_score >= 40:
            overall_grade = "Needs Work"
            recommendation = "May need additional screening"
        else:
            overall_grade = "Insufficient"
            recommendation = "Does not meet requirements"

        # Category breakdown
        category_breakdown = {}
        category_names = {
            "T": "Technical",
            "P": "Projects",
            "B": "Behavioral",
            "C": "Conceptual",
            "R": "Role Fit",
        }

        for cat, scores in category_scores.items():
            cat_avg = sum(scores) / len(scores) if scores else 0
            category_breakdown[category_names.get(cat, cat)] = {
                "average_score": round(cat_avg, 1),
                "questions_count": len(scores),
            }

        # Generate summary with ONLY strings
        summary = self._generate_summary(evaluations, avg_score, overall_grade)
        authenticity_summary = summarize_batch_authenticity(
            [
                {
                    **(ev.get("authenticity_report") or {}),
                    "question_number": ev.get("question_number"),
                }
                for ev in evaluations
                if isinstance(ev.get("authenticity_report"), dict)
            ]
        )

        return {
            "success": True,
            "session_id": qa_pairs[0].get("session_id", "")
            if qa_pairs and isinstance(qa_pairs[0], dict)
            else "",
            "total_questions": num_questions,
            "overall_score": round(avg_score, 1),
            "overall_grade": overall_grade,
            "recommendation": recommendation,
            "category_breakdown": category_breakdown,
            "evaluations": evaluations,
            "summary": summary,
            "plagiarism_summary": authenticity_summary,
        }

    def _generate_summary(
        self,
        evaluations: List[Dict[str, Any]],
        avg_score: float,
        overall_grade: str,
    ) -> str:
        """Generate overall interview summary - ensures all items are strings."""

        all_strengths: List[str] = []
        all_improvements: List[str] = []

        for ev in evaluations:
            if ev.get("score", 0) >= 75:
                # Get strengths and ensure they are strings
                strengths = self._ensure_string_list(ev.get("strengths", []))
                if strengths:
                    all_strengths.append(strengths[0])

            if ev.get("score", 0) < 60:
                # Get improvements and ensure they are strings
                improvements = self._ensure_string_list(ev.get("improvements", []))
                if improvements:
                    all_improvements.append(improvements[0])

        # Build summary - all items are guaranteed to be strings now
        summary = (
            f"Interview completed with an overall score of {avg_score:.0f}/100 ({overall_grade}). "
        )

        if all_strengths:
            unique_strengths = list(dict.fromkeys(all_strengths))[:3]
            # Double-check all are strings before joining
            unique_strengths = [str(s) for s in unique_strengths]
            summary += f"Key strengths: {'; '.join(unique_strengths)}. "

        if all_improvements:
            unique_improvements = list(dict.fromkeys(all_improvements))[:3]
            # Double-check all are strings before joining
            unique_improvements = [str(i) for i in unique_improvements]
            summary += f"Areas for development: {'; '.join(unique_improvements)}."

        if not all_strengths and not all_improvements:
            summary += "The candidate showed consistent performance across all questions."

        return summary


# Singleton instance
_evaluator: Optional[AnswerEvaluator] = None


def get_evaluator() -> AnswerEvaluator:
    """Get singleton AnswerEvaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = AnswerEvaluator()
    return _evaluator
