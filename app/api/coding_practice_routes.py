"""
Coding Practice API Routes - problem listing, execution, progress persistence,
and AI code review.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.api.auth_routes import get_current_user
from app.services.coding_problems_service import (
    TOPICS,
    execute_problem,
    get_all_problems,
    get_problem,
    get_supported_languages,
    review_code,
    rubber_duck,
)

coding_practice_router = APIRouter(prefix="/coding-practice", tags=["Coding Practice"])


# ─── Schemas ──────────────────────────────────────────────

class ProblemSummary(BaseModel):
    id: int
    title: str
    difficulty: str
    topic: str
    tags: List[str]
    companiesAsked: List[str]
    timeComplexity: str
    spaceComplexity: str


class ProblemDetail(BaseModel):
    id: int
    title: str
    difficulty: str
    topic: str
    tags: List[str]
    description: str
    constraints: str
    testCases: list
    starterCode: str
    solutionCode: str
    hints: List[str]
    timeComplexity: str
    spaceComplexity: str
    companiesAsked: List[str]
    starterTemplates: Dict[str, str] = Field(default_factory=dict)
    solutionsByLanguage: Dict[str, str] = Field(default_factory=dict)
    supportedLanguages: List[str] = Field(default_factory=list)
    solutionLanguage: str = "javascript"
    executionContract: str = ""


class SubmitRequest(BaseModel):
    code: str
    language: str = "javascript"
    passed_tests: int
    total_tests: int
    solved: bool


class ProgressEntry(BaseModel):
    problem_id: int
    solved: bool
    code: str
    language: str = "javascript"
    attempts: int
    passed_tests: int
    total_tests: int
    last_submitted: Optional[str] = None


class ReviewRequest(BaseModel):
    code: str
    language: str = "javascript"


class RubberDuckRequest(BaseModel):
    transcript: str = Field(..., min_length=1)
    current_code: str = ""
    language: str = "javascript"


class ExecuteRequest(BaseModel):
    code: str
    language: str = "javascript"


class ExecuteResult(BaseModel):
    input: str
    expected: str
    actual: str
    passed: bool
    error: Optional[str] = None
    time_ms: Optional[float] = None
    status: Optional[str] = None


class ExecuteResponse(BaseModel):
    success: bool
    language: str
    provider: str
    total_tests: int
    passed_tests: int
    all_passed: bool
    results: List[ExecuteResult]


class LanguageOption(BaseModel):
    id: str
    label: str
    enabled: bool
    providers: List[str]


# ─── In-memory progress store ────


# Simple in-memory store keyed by user_id
_progress_store: dict[str, dict[int, dict]] = {}
_streak_store: dict[str, dict] = {}


def _get_user_progress(user_id: str) -> dict[int, dict]:
    if user_id not in _progress_store:
        _progress_store[user_id] = {}
    return _progress_store[user_id]


def _get_user_streak(user_id: str) -> dict:
    if user_id not in _streak_store:
        _streak_store[user_id] = {
            "current_streak": 0,
            "max_streak": 0,
            "last_solved_date": None,
            "total_solved": 0,
        }
    return _streak_store[user_id]


# ─── Endpoints ────────────────────────────────────────────

@coding_practice_router.get("/topics", response_model=List[str])
def list_topics():
    """Return all available problem topics."""
    return TOPICS


@coding_practice_router.get("/languages", response_model=List[LanguageOption])
def list_languages():
    """Return supported execution languages and provider availability."""
    return get_supported_languages()


@coding_practice_router.get("/problems", response_model=List[ProblemSummary])
def list_problems(
    topic: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List problems with optional filtering."""
    return get_all_problems(topic=topic, difficulty=difficulty, search=search)


@coding_practice_router.get("/problems/{problem_id}", response_model=ProblemDetail)
def get_problem_detail(problem_id: int):
    """Get full problem details including test cases and solution."""
    problem = get_problem(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@coding_practice_router.post("/execute/{problem_id}", response_model=ExecuteResponse)
def execute_solution(problem_id: int, req: ExecuteRequest):
    """Compile/run a candidate solution against the problem test cases."""
    try:
        return execute_problem(problem_id=problem_id, code=req.code, language=req.language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@coding_practice_router.get("/progress")
def get_progress(current=Depends(get_current_user)):
    """Get user's coding practice progress."""
    user_id = str(current["user"].id)
    progress = _get_user_progress(user_id)
    streak = _get_user_streak(user_id)

    entries = []
    for pid, data in progress.items():
        entries.append(ProgressEntry(
            problem_id=pid,
            solved=data.get("solved", False),
            code=data.get("code", ""),
            language=data.get("language", "javascript"),
            attempts=data.get("attempts", 0),
            passed_tests=data.get("passed_tests", 0),
            total_tests=data.get("total_tests", 0),
            last_submitted=data.get("last_submitted"),
        ))

    return {
        "progress": [e.model_dump() for e in entries],
        "streak": streak,
    }


@coding_practice_router.post("/progress/{problem_id}", status_code=status.HTTP_201_CREATED)
def submit_solution(
    problem_id: int,
    req: SubmitRequest,
    current=Depends(get_current_user),
):
    """Submit a solution and update progress."""
    user_id = str(current["user"].id)
    progress = _get_user_progress(user_id)
    streak = _get_user_streak(user_id)

    now = datetime.now(timezone.utc)
    existing = progress.get(problem_id, {})
    attempts = existing.get("attempts", 0) + 1

    progress[problem_id] = {
        "solved": req.solved or existing.get("solved", False),
        "code": req.code,
        "language": req.language or existing.get("language", "javascript"),
        "attempts": attempts,
        "passed_tests": req.passed_tests,
        "total_tests": req.total_tests,
        "last_submitted": now.isoformat(),
    }

    # Update streak
    if req.solved and not existing.get("solved", False):
        streak["total_solved"] = streak.get("total_solved", 0) + 1
        today = now.date().isoformat()
        last_date = streak.get("last_solved_date")

        if last_date == today:
            pass  # Already counted today
        elif last_date and (now.date() - datetime.fromisoformat(last_date).date()).days == 1:
            streak["current_streak"] = streak.get("current_streak", 0) + 1
        elif last_date and (now.date() - datetime.fromisoformat(last_date).date()).days > 1:
            streak["current_streak"] = 1
        else:
            streak["current_streak"] = streak.get("current_streak", 0) + 1

        streak["last_solved_date"] = today
        streak["max_streak"] = max(streak.get("max_streak", 0), streak["current_streak"])


    return {
        "success": True,
        "problem_id": problem_id,
        "solved": progress[problem_id]["solved"],
        "attempts": attempts,
    }


@coding_practice_router.delete("/progress")
def reset_progress(current=Depends(get_current_user)):
    """Reset all coding practice progress for the user."""
    user_id = str(current["user"].id)
    _progress_store[user_id] = {}
    _streak_store[user_id] = {
        "current_streak": 0,
        "max_streak": 0,
        "last_solved_date": None,
        "total_solved": 0,
    }
    return {"success": True, "message": "Progress reset"}


@coding_practice_router.post("/review/{problem_id}")
async def review_solution(
    problem_id: int,
    req: ReviewRequest,
    current=Depends(get_current_user),
):
    """AI-powered code review for a submitted solution."""
    result = await review_code(problem_id, req.code, req.language)
    return result


@coding_practice_router.post("/rubber-duck/{problem_id}")
async def rubber_duck_followup(
    problem_id: int,
    req: RubberDuckRequest,
):
    """AI rubber duck: ask one Socratic follow-up question, never reveal the solution."""
    try:
        return await rubber_duck(
            problem_id=problem_id,
            transcript=req.transcript,
            current_code=req.current_code,
            language=req.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@coding_practice_router.get("/stats")
def get_stats(current=Depends(get_current_user)):
    """Aggregated stats for the user's coding practice."""
    user_id = str(current["user"].id)
    progress = _get_user_progress(user_id)
    streak = _get_user_streak(user_id)

    # Per-topic and per-difficulty breakdown
    all_problems = get_all_problems()
    topic_counts = {}
    difficulty_counts = {"Easy": {"total": 0, "solved": 0}, "Medium": {"total": 0, "solved": 0}, "Hard": {"total": 0, "solved": 0}}

    for p in all_problems:
        topic = p["topic"]
        diff = p["difficulty"]
        if topic not in topic_counts:
            topic_counts[topic] = {"total": 0, "solved": 0}
        topic_counts[topic]["total"] += 1
        difficulty_counts[diff]["total"] += 1

        if p["id"] in progress and progress[p["id"]].get("solved"):
            topic_counts[topic]["solved"] += 1
            difficulty_counts[diff]["solved"] += 1

    return {
        "total_problems": len(all_problems),
        "total_solved": streak.get("total_solved", 0),
        "current_streak": streak.get("current_streak", 0),
        "max_streak": streak.get("max_streak", 0),
        "topic_breakdown": topic_counts,
        "difficulty_breakdown": difficulty_counts,
    }
