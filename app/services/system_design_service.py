"""
System Design AI Evaluation Service — provides AI-powered feedback
on system design answers using the existing LLM infrastructure.
"""
import json
from typing import Optional
from loguru import logger

_system_design_service = None

def get_system_design_service():
    global _system_design_service
    if _system_design_service is None:
        _system_design_service = SystemDesignService()
    return _system_design_service

class SystemDesignService:
    def __init__(self):
        from app.services.llm_service import get_llm
        self.llm = get_llm()

    def evaluate_answer(self, question: str, answer: str, topic: str = "") -> dict:
        prompt = f"""You are a senior system design interviewer at a top tech company.
Evaluate the following system design answer.

Question: {question}
Topic: {topic or 'General System Design'}
Candidate Answer: {answer}

Evaluate on these criteria (0-100 each):
1. Scalability — handles growth in users/data/traffic
2. Reliability — fault tolerance, redundancy, availability
3. Trade-offs — awareness of CAP theorem, consistency vs availability
4. Data Model — appropriate schema, storage choices
5. API Design — clean interfaces, proper REST/gRPC patterns
6. Communication — clarity and structure of the answer

Return ONLY valid JSON:
{{
    "overall_score": 75,
    "grade": "B+",
    "criteria": {{
        "scalability": {{"score": 80, "feedback": "..."}},
        "reliability": {{"score": 70, "feedback": "..."}},
        "tradeoffs": {{"score": 75, "feedback": "..."}},
        "data_model": {{"score": 80, "feedback": "..."}},
        "api_design": {{"score": 70, "feedback": "..."}},
        "communication": {{"score": 75, "feedback": "..."}}
    }},
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "follow_up_questions": ["question1", "question2"],
    "summary": "Overall feedback paragraph"
}}"""
        try:
            raw = self.llm.generate(prompt, max_tokens=900)
            result = self._parse_json(raw)
            if result:
                return {"success": True, **result}
        except Exception as e:
            logger.exception(f"System design evaluation failed: {e}")

        return {
            "success": True,
            "overall_score": 60,
            "grade": "B-",
            "criteria": {
                "scalability": {"score": 60, "feedback": "Consider discussing horizontal scaling strategies."},
                "reliability": {"score": 60, "feedback": "Add fault tolerance mechanisms like circuit breakers."},
                "tradeoffs": {"score": 55, "feedback": "Discuss CAP theorem trade-offs explicitly."},
                "data_model": {"score": 65, "feedback": "Schema design could be more detailed."},
                "api_design": {"score": 60, "feedback": "Define API contracts more precisely."},
                "communication": {"score": 65, "feedback": "Structure answer with clear sections."},
            },
            "strengths": ["Shows basic understanding of the problem"],
            "improvements": ["Add scalability numbers", "Discuss failure scenarios", "Include data flow diagrams"],
            "follow_up_questions": ["How would you handle a 10x traffic spike?"],
            "summary": "Evaluation could not be fully completed by AI. Review the general feedback above.",
        }

    def _parse_json(self, raw: str) -> Optional[dict]:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                logger.warning("Failed to parse system design JSON from LLM")
        return None
