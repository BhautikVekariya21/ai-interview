"""
Pydantic schemas for answer evaluation (Module 5).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvaluateAnswerRequest(BaseModel):
    """Request to evaluate a single answer."""
    session_id: str = Field(..., description="Interview session ID")
    question_id: str = Field(..., description="Question ID")
    question_number: int = Field(..., ge=1, description="Question number (1-based)")
    question_text: str = Field(..., min_length=5, description="The interview question")
    question_category: str = Field(
        default="T", 
        description="Category: T=Technical, P=Project, B=Behavioral, C=Conceptual, R=Role-fit"
    )
    answer_text: str = Field(..., min_length=1, description="Candidate's answer")
    resume_context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional resume data for context"
    )


class EvaluationResult(BaseModel):
    """Single answer evaluation result."""
    success: bool = Field(default=True)
    score: int = Field(ge=0, le=100, description="Score out of 100")
    grade: str = Field(description="Grade: Exceptional/Strong/Adequate/Needs Work/Insufficient")
    strengths: List[str] = Field(default_factory=list, description="List of strengths")
    improvements: List[str] = Field(default_factory=list, description="Areas for improvement")
    feedback: str = Field(description="Detailed feedback paragraph")
    authenticity_report: Optional[Dict[str, Any]] = Field(default=None, description="AI-likeness and plagiarism coaching report")
    followup_question: Optional[str] = Field(
        default=None, 
        description="Optional follow-up question"
    )
    word_count: int = Field(default=0, description="Word count of the answer")
    processing_time_ms: float = Field(default=0, description="Processing time in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if any")


class NextQuestionResponse(BaseModel):
    """Response with evaluation and next question info."""
    evaluation: EvaluationResult
    has_next_question: bool = Field(description="Whether there are more questions")
    next_question: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Next question data if available"
    )
    questions_remaining: int = Field(default=0, description="Number of questions remaining")
    interview_complete: bool = Field(default=False, description="Whether interview is complete")


class BatchEvaluationRequest(BaseModel):
    """Request to evaluate all answers at once."""
    session_id: str = Field(..., description="Interview session ID")
    qa_pairs: List[Dict[str, Any]] = Field(
        ..., 
        description="List of {question, answer, category} objects"
    )
    resume_context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Resume data for context"
    )


class CategoryBreakdown(BaseModel):
    """Score breakdown by category."""
    average_score: float
    questions_count: int


class BatchEvaluationResult(BaseModel):
    """Complete interview evaluation result."""
    success: bool = Field(default=True)
    session_id: Optional[str] = Field(default=None)
    total_questions: int = Field(description="Total number of questions evaluated")
    overall_score: float = Field(description="Average score across all questions")
    overall_grade: str = Field(description="Overall grade")
    recommendation: str = Field(description="Hiring recommendation")
    category_breakdown: Dict[str, CategoryBreakdown] = Field(
        default_factory=dict,
        description="Score breakdown by question category"
    )
    evaluations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Individual question evaluations"
    )
    summary: str = Field(description="Overall interview summary")
    plagiarism_summary: Dict[str, Any] = Field(default_factory=dict)


class QuickEvaluateRequest(BaseModel):
    """Simplified evaluation request for real-time use."""
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=1)
    category: str = Field(default="T")


class InterviewResultsRequest(BaseModel):
    """Request for final interview results."""
    session_id: str
    candidate_name: Optional[str] = None
    position: Optional[str] = None
    answers: List[Dict[str, Any]] = Field(
        ...,
        description="List of {question, answer, category, score} objects"
    )
