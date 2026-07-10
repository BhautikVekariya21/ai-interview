"""
Interview Script Generator — AI-powered speech scripts.
Uses the EXISTING LLM service (Gemini → Groq → HuggingFace).
NO separate OpenAI/Gemini clients — reuses llm_service.py.
"""

import random
from typing import Optional, List, Dict, Tuple
from loguru import logger


class InterviewScriptGenerator:
    """
    Generates natural, personalized speech scripts.
    
    Uses the shared LLM service (already configured with
    Gemini → Groq → HuggingFace fallback chain).
    Falls back to templates if LLM unavailable.
    """

    def __init__(self):
        self._llm = None
        self._active_llm: str = "none"
        # Backward-compatible test hooks
        self._gemini_client = None
        self._groq_client = None
        self._openai_client = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Connect to the shared LLM service."""
        try:
            from app.services.llm_service import get_llm
            self._llm = get_llm()
            if self._llm.is_available:
                self._active_llm = (
                    self._llm.active_provider or "llm"
                )
                ap = (self._active_llm or "").lower()
                if ap.startswith("gemini:"):
                    self._gemini_client = self._llm
                if ap.startswith("groq:"):
                    self._groq_client = self._llm
                logger.debug(
                    f"  Script generator using LLM: "
                    f"{self._active_llm}"
                )
            else:
                self._active_llm = "template"
                logger.debug(
                    "  Script generator: LLM unavailable, "
                    "using templates"
                )
        except Exception as e:
            self._active_llm = "template"
            logger.debug(
                f"  Script generator: LLM init failed "
                f"({e}), using templates"
            )

    @property
    def is_llm_available(self) -> bool:
        return (
            self._llm is not None
            and self._llm.is_available
        )

    # ════════════════════════════════════════════════
    #  INTRO
    # ════════════════════════════════════════════════

    def generate_intro(
        self,
        candidate_name: str,
        resume_data: Optional[Dict] = None,
        num_questions: int = 15,
        question_categories: Optional[List[str]] = None,
        duration_minutes: int = 30,
    ) -> Tuple[str, str]:
        """
        Generate interview introduction script.
        Returns: (script_text, source)
        """
        if self.is_llm_available and resume_data:
            try:
                script = self._llm_intro(
                    candidate_name, resume_data,
                    num_questions, duration_minutes,
                )
                if script and len(script) > 50:
                    return script, self._active_llm
            except Exception as e:
                logger.warning(
                    f"LLM intro failed: {e}"
                )

        return self._template_intro(
            candidate_name, num_questions,
            duration_minutes,
        ), "template"

    def _llm_intro(
        self, name, resume_data,
        num_questions, duration,
    ) -> Optional[str]:
        """Generate intro via shared LLM service."""
        skills = []
        for s in (resume_data.get("skills") or [])[:5]:
            if isinstance(s, dict):
                skills.append(s.get("name", ""))
            elif isinstance(s, str):
                skills.append(s)
        skills_text = ", ".join(s for s in skills if s)

        domain = resume_data.get(
            "primary_domain", "software engineering"
        )
        level = resume_data.get(
            "experience_level", "junior"
        )
        if hasattr(level, "value"):
            level = level.value

        prompt = (
            f"Generate a warm, professional interview "
            f"introduction speech (3-4 sentences, under "
            f"80 words) for:\n"
            f"- Candidate: {name}\n"
            f"- Domain: {domain}\n"
            f"- Level: {level}\n"
            f"- Key skills: {skills_text}\n"
            f"- Questions: {num_questions}\n"
            f"- Duration: ~{duration} minutes\n\n"
            f"The intro should:\n"
            f"1. Greet them by name warmly\n"
            f"2. Briefly mention their domain\n"
            f"3. Explain the interview format\n"
            f"4. Encourage them to take their time\n\n"
            f"Return ONLY the speech text. "
            f"No quotes, no labels, no markdown."
        )

        result = self._llm.generate(
            prompt=prompt,
            system_prompt=(
                "You are a friendly AI interview host. "
                "Generate natural, spoken interview "
                "scripts. Keep it concise and warm."
            ),
            max_tokens=200,
        )

        if result:
            result = result.strip().strip('"\'')
            for prefix in [
                "Introduction:", "Intro:",
                "Script:", "Speech:",
            ]:
                if result.startswith(prefix):
                    result = result[len(prefix):].strip()
            return result

        return None

    def _template_intro(
        self, name, num_questions, duration,
    ) -> str:
        """Template-based intro fallback."""
        templates = [
            (
                f"Hello {name}! Welcome to your "
                f"AI-powered technical interview. "
                f"I'll be asking you {num_questions} "
                f"questions over the next {duration} "
                f"minutes or so. The questions cover "
                f"technical depth, projects, and "
                f"behavioral scenarios based on your "
                f"resume. Take your time with each "
                f"answer. Let's get started!"
            ),
            (
                f"Welcome, {name}! Today we have "
                f"{num_questions} personalized questions "
                f"prepared just for you, based on your "
                f"resume. We'll explore your technical "
                f"skills, project experience, and "
                f"problem-solving approach. There are no "
                f"trick questions. Ready? Let's begin!"
            ),
            (
                f"Hi {name}, great to have you here! "
                f"This interview has {num_questions} "
                f"questions tailored to your background "
                f"covering technical topics, projects, "
                f"and scenarios. Take your time and "
                f"explain your thought process. "
                f"Let's dive in!"
            ),
        ]
        return random.choice(templates)

    # ════════════════════════════════════════════════
    #  OUTRO
    # ════════════════════════════════════════════════

    def generate_outro(
        self,
        candidate_name: str,
        resume_data: Optional[Dict] = None,
        num_questions: int = 15,
        num_answered: int = 15,
        overall_score: int = 0,
        grade: str = "Strong",
        category_scores: Optional[Dict[str, float]] = None,
        strengths: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """
        Generate interview closing script.
        Returns: (script_text, source)
        """
        if self.is_llm_available:
            try:
                script = self._llm_outro(
                    candidate_name, num_questions,
                    num_answered, overall_score,
                    grade, strengths, improvements,
                )
                if script and len(script) > 50:
                    return script, self._active_llm
            except Exception as e:
                logger.warning(
                    f"LLM outro failed: {e}"
                )

        return self._template_outro(
            candidate_name, num_questions,
        ), "template"

    def _llm_outro(
        self, name, num_questions, num_answered,
        score, grade, strengths, improvements,
    ) -> Optional[str]:
        """Generate outro via shared LLM service."""
        strengths_text = ""
        if strengths:
            strengths_text = (
                f"Strengths: "
                f"{', '.join(strengths[:3])}"
            )
        improvements_text = ""
        if improvements:
            improvements_text = (
                f"Improvements: "
                f"{', '.join(improvements[:3])}"
            )

        prompt = (
            f"Generate a warm interview closing speech "
            f"(3-4 sentences, under 80 words) for:\n"
            f"- Candidate: {name}\n"
            f"- Answered: {num_answered}/{num_questions}\n"
            f"- Grade: {grade}\n"
            f"{strengths_text}\n"
            f"{improvements_text}\n\n"
            f"Thank them, give brief positive feedback, "
            f"mention next steps. "
            f"Return ONLY the speech text."
        )

        result = self._llm.generate(
            prompt=prompt,
            system_prompt=(
                "You are a friendly AI interview host "
                "wrapping up. Be encouraging."
            ),
            max_tokens=200,
        )

        if result:
            result = result.strip().strip('"\'')
            for prefix in [
                "Outro:", "Closing:",
                "Script:", "Speech:",
            ]:
                if result.startswith(prefix):
                    result = result[len(prefix):].strip()
            return result

        return None

    def _template_outro(
        self, name, num_questions,
    ) -> str:
        """Template-based outro fallback."""
        templates = [
            (
                f"Thank you so much, {name}, for "
                f"completing this interview! You answered "
                f"all {num_questions} questions. Your "
                f"responses have been recorded and will "
                f"be evaluated. We appreciate your time. "
                f"Best of luck!"
            ),
            (
                f"That wraps up our interview, {name}! "
                f"Thank you for your detailed responses "
                f"to all {num_questions} questions. Your "
                f"answers showed great thought. We'll "
                f"review everything carefully. "
                f"Have a wonderful day!"
            ),
            (
                f"Excellent work, {name}! We've completed "
                f"all {num_questions} questions. Thank you "
                f"for sharing your experience and "
                f"knowledge. Your evaluation will be ready "
                f"shortly. Take care!"
            ),
        ]
        return random.choice(templates)

    # ════════════════════════════════════════════════
    #  TRANSITIONS
    # ════════════════════════════════════════════════

    def generate_transition(
        self,
        question_number: int,
        total_questions: int,
        current_category: str = "T",
        previous_category: Optional[str] = None,
        candidate_name: Optional[str] = None,
        previous_answer_quality: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate transition between questions.
        Returns: (script_text, source)
        """
        return self._template_transition(
            question_number, total_questions,
            current_category, previous_category,
            candidate_name, previous_answer_quality,
        ), "template"

    def _template_transition(
        self, q_num, total, category,
        prev_category, name, answer_quality,
    ) -> str:
        """Generate a natural transition phrase."""
        cat_names = {
            "T": "technical",
            "P": "project-based",
            "B": "behavioral",
            "C": "conceptual",
            "R": "role-fit",
        }
        cat_name = cat_names.get(category, "next")
        name_part = f", {name}" if name else ""

        if q_num == 1:
            return random.choice([
                f"Let's start with question one. "
                f"This is a {cat_name} question.",
                f"Here's your first question. "
                f"It's a {cat_name} question.",
                f"Alright, let's begin! "
                f"Question one, a {cat_name} question.",
            ])

        if q_num == total:
            return random.choice([
                f"And now for our final question, "
                f"question {q_num}.",
                f"Last question! Number {q_num} "
                f"of {total}.",
                f"We're at the final question now, "
                f"number {q_num}.",
            ])

        if (
            prev_category
            and prev_category != category
        ):
            return random.choice([
                f"Now let's switch to a {cat_name} "
                f"question. Question {q_num} of {total}.",
                f"Moving on to {cat_name} territory. "
                f"Question {q_num}.",
                f"Let's shift gears. Here's a "
                f"{cat_name} question, number {q_num} "
                f"of {total}.",
            ])

        if q_num == total // 2 + 1:
            return random.choice([
                f"Great progress{name_part}! "
                f"We're about halfway through. "
                f"Question {q_num}.",
                f"You're doing well{name_part}! "
                f"Halfway there. Question {q_num} "
                f"of {total}.",
            ])

        if answer_quality == "excellent":
            return random.choice([
                f"Excellent answer! "
                f"Question {q_num} of {total}.",
                f"Very well explained! "
                f"Moving to question {q_num}.",
            ])

        return random.choice([
            f"Question {q_num} of {total}.",
            f"Next up, question {q_num}.",
            f"Moving on. Question {q_num} of {total}.",
            f"Let's continue. Question {q_num}.",
            f"Alright, question {q_num}.",
            f"Here's question number {q_num}.",
        ])

    # ════════════════════════════════════════════════
    #  ENCOURAGEMENT
    # ════════════════════════════════════════════════

    def generate_encouragement(
        self,
        candidate_name: Optional[str] = None,
        context: str = "thinking",
    ) -> str:
        name_part = (
            f", {candidate_name}"
            if candidate_name else ""
        )
        prompts = {
            "thinking": [
                f"Take your time{name_part}. "
                f"There's no rush.",
                f"No worries{name_part}, "
                f"think it through.",
                f"Feel free to think out loud"
                f"{name_part}.",
            ],
            "repeat": [
                "Sure, let me repeat the question.",
                "Of course, here it is again.",
                "No problem, here's the question "
                "one more time.",
            ],
            "struggling": [
                f"That's a tough one{name_part}. "
                f"Try breaking it down.",
                f"Take a step back{name_part}. "
                f"What's the first thing you'd "
                f"consider?",
                f"It's okay{name_part}. "
                f"Start with what you know.",
            ],
            "good_answer": [
                "Great answer! Very thorough.",
                "Well explained! I can see your "
                "expertise.",
                "Excellent response! Very clear.",
                "Strong answer. Well done!",
            ],
            "halfway": [
                f"You're doing great{name_part}! "
                f"We're about halfway through.",
                f"Excellent progress{name_part}! "
                f"Keep it up.",
                f"You're halfway there{name_part}! "
                f"Going strong.",
            ],
        }
        return random.choice(
            prompts.get(context, prompts["thinking"])
        )

    # ════════════════════════════════════════════════
    #  FOLLOW-UP INTRO
    # ════════════════════════════════════════════════

    def generate_followup_intro(
        self,
        original_question: str,
        candidate_answer_summary: Optional[str] = None,
    ) -> str:
        return random.choice([
            "Based on your answer, I have a "
            "follow-up question.",
            "Interesting. Let me dig a bit "
            "deeper on that.",
            "Good point. I'd like to explore "
            "that further.",
            "Thank you. Here's a follow-up "
            "on what you just said.",
            "Let me probe a bit deeper on "
            "that topic.",
        ])


# ════════════════════════════════════════════════
#  SINGLETON
# ════════════════════════════════════════════════

_script_generator: Optional[
    InterviewScriptGenerator
] = None


def get_script_generator() -> InterviewScriptGenerator:
    global _script_generator
    if _script_generator is None:
        _script_generator = InterviewScriptGenerator()
    return _script_generator