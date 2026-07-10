"""
STAR Builder Service — AI-powered STAR (Situation, Task, Action, Result)
story generation and improvement using the existing LLM infrastructure.
"""

import json
from typing import Optional
from loguru import logger


_star_service = None


def get_star_builder_service():
    global _star_service
    if _star_service is None:
        _star_service = StarBuilderService()
    return _star_service


class StarBuilderService:
    """Generate and improve STAR stories using AI."""

    def __init__(self):
        from app.services.llm_service import get_llm
        self.llm = get_llm()

    def generate_star_story(
        self,
        situation_context: str,
        role: Optional[str] = None,
        skills: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate a STAR story skeleton from a situation context.
        Returns a structured STAR breakdown.
        """
        role_hint = f" for a {role} role" if role else ""
        skills_hint = f" highlighting skills like {', '.join(skills)}" if skills else ""

        prompt = f"""You are an expert career coach. Generate a compelling STAR method story{role_hint}{skills_hint}.

Context provided by the candidate: {situation_context}

Generate a polished, detailed STAR story. Return ONLY valid JSON with this exact structure:
{{
    "situation": "2-3 sentences describing the context and background",
    "task": "2-3 sentences describing the specific challenge or responsibility",
    "action": "3-5 sentences describing the specific steps taken",
    "result": "2-3 sentences with quantifiable outcomes and impact",
    "title": "A short 3-6 word title for this story",
    "tags": ["skill1", "skill2", "skill3"],
    "improvement_tips": ["tip1", "tip2"]
}}"""

        try:
            raw = self.llm.generate(prompt, max_tokens=800)
            # Extract JSON from response
            result = self._parse_json(raw)
            if result:
                return {"success": True, **result}
        except Exception as e:
            logger.exception(f"STAR generation failed: {e}")

        # Fallback
        return {
            "success": True,
            "situation": f"In my role, I encountered a challenge related to: {situation_context}",
            "task": "I was responsible for addressing this challenge and finding a solution.",
            "action": "I analyzed the situation, developed a plan, and executed it step by step.",
            "result": "The outcome was positive, leading to measurable improvements.",
            "title": "Professional Achievement",
            "tags": ["problem-solving", "initiative"],
            "improvement_tips": [
                "Add specific metrics and numbers",
                "Include the team context and your specific role",
            ],
        }

    def improve_star_story(
        self,
        situation: str,
        task: str,
        action: str,
        result: str,
    ) -> dict:
        """
        Take a draft STAR story and return an improved version with suggestions.
        """
        prompt = f"""You are an expert career coach reviewing a STAR method interview story.

CURRENT STORY:
Situation: {situation}
Task: {task}
Action: {action}
Result: {result}

Improve this STAR story to be more compelling for interviews. Make it more specific,
add quantifiable metrics where possible, and ensure it demonstrates clear impact.

Return ONLY valid JSON:
{{
    "situation": "improved situation (2-3 sentences)",
    "task": "improved task (2-3 sentences)",
    "action": "improved action (3-5 sentences with specific details)",
    "result": "improved result (2-3 sentences with metrics/impact)",
    "score": 85,
    "feedback": "Brief overall feedback on the original story",
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}}"""

        try:
            raw = self.llm.generate(prompt, max_tokens=800)
            result_data = self._parse_json(raw)
            if result_data:
                return {"success": True, **result_data}
        except Exception as e:
            logger.exception(f"STAR improvement failed: {e}")

        return {
            "success": False,
            "error": "Failed to improve story. Please try again.",
        }

    def _parse_json(self, raw: str) -> Optional[dict]:
        """Extract JSON from LLM response, handling markdown fences."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1]
            text = text.split("```", 1)[0]

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                logger.warning("Failed to parse STAR JSON from LLM response")
        return None
