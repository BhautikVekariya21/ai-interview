"""
Pydantic schemas for question generation.
Frontend-safe — NO tokens, NO API keys, NO model details.
"""

from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field


class QuestionCategory(str, Enum):
    TECHNICAL = "T"
    PROJECT = "P"
    BEHAVIORAL = "B"
    CONCEPTUAL = "C"
    ROLE_FIT = "R"
    CODING = "CODING"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class InterviewQuestion(BaseModel):
    """Single interview question — safe to send to frontend."""
    id: int
    question: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    context: str = ""
    resume_reference: str = ""
    expected_topics: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    time_limit_seconds: int = 120
    scoring_rubric: Dict[str, str] = Field(default_factory=dict)
    problem_id: Optional[str] = None
    starter_code: Optional[Dict[str, str]] = None


class QuestionSet(BaseModel):
    """
    Complete question set for frontend.
    EXCLUDED: token_counts, raw_output, api_keys.
    """
    candidate_name: str = "Candidate"
    experience_level: str = "junior"
    primary_domain: Optional[str] = None
    base_difficulty: str = "medium"
    total_questions: int = 0
    questions: List[InterviewQuestion] = Field(default_factory=list)
    categories_distribution: Dict[str, int] = Field(
        default_factory=dict
    )
    estimated_duration_minutes: int = 0
    llm_provider: Optional[str] = None
    generated_at: str = ""
    generator_version: str = "2.0"


class QuestionGenerationRequest(BaseModel):
    """Request body for question generation."""
    resume_data: Dict
    num_questions: int = Field(default=15, ge=10, le=30)
    categories: Optional[List[QuestionCategory]] = None
    session_id: Optional[str] = None
    job_description: Optional[str] = None


class FollowUpRequest(BaseModel):
    """Request body for follow-up generation."""
    original_question: str
    candidate_answer: str
    resume_data: Dict = Field(default_factory=dict)


class FollowUpResponse(BaseModel):
    """Follow-up response — frontend-safe."""
    question: InterviewQuestion
    based_on_answer: str = ""
