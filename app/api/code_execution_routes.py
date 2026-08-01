"""
Code Execution API Routes — Module 16.

Endpoints:
    GET  /coding/problems       — list curated coding problems
    GET  /coding/problems/{id}  — problem detail & starter code
    POST /coding/run            — run sample tests (no history recorded)
    POST /coding/submit         — submit full test suite & return AI review
    GET  /coding/submissions    — submission history for one interview session
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from app.api.auth_routes import get_current_user
from app.core.config import settings
from app.repositories.coding_submission_repository import CodingSubmissionRepository
from app.services import rate_limit_service
from app.services.code_executor_service import get_code_executor_service
from app.services.mysql_service import MySQLService, get_mysql

coding_router = APIRouter(prefix="/coding", tags=["Code Execution Sandbox"])

# ── DTO Schemas ──────────────────────────────────────────────────────────────


class RunCodeRequest(BaseModel):
    problem_id: str
    language: str = Field("python", description="'python', 'javascript', or 'rust'")
    code: str = Field(..., min_length=1, max_length=10000)


class SubmitCodeRequest(RunCodeRequest):
    # Scopes the recorded history to one interview sitting. Optional so the
    # sandbox still works when opened standalone outside an interview.
    session_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Interview session this submission belongs to",
    )


class RunCodeResponse(BaseModel):
    success: bool
    passed: bool
    runtime_ms: float = 0.0
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


class SubmitCodeResponse(BaseModel):
    success: bool
    passed: bool
    runtime_ms: float = 0.0
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    ai_analysis: str = ""
    error: Optional[str] = None
    submission_id: Optional[str] = None
    session_id: Optional[str] = None


class SubmissionSummary(BaseModel):
    id: str
    session_id: str
    problem_id: str
    problem_title: str
    language: str
    passed: bool
    tests_passed: int
    tests_total: int
    runtime_ms: float
    created_at: Optional[str] = None


class SubmissionListResponse(BaseModel):
    session_id: str
    items: List[SubmissionSummary] = Field(default_factory=list)


# ── Routes ───────────────────────────────────────────────────────────────────


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce_exec_quota(request: Request) -> None:
    """Cap executions per IP — each one spawns a real process on this host."""
    decision = rate_limit_service.check_quota(
        "code_exec",
        _client_ip(request),
        settings.CODE_EXEC_RATELIMIT_PER_MINUTE,
        60,
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many code executions. Please wait a moment and try again.",
            headers={"Retry-After": str(decision.retry_after)},
        )


def get_submission_repository(
    db: MySQLService = Depends(get_mysql),
) -> CodingSubmissionRepository:
    return CodingSubmissionRepository(db)


def optional_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: MySQLService = Depends(get_mysql),
) -> Optional[Any]:
    """The signed-in user's id, or None.

    The sandbox is usable signed out — it always has been — so authentication
    attributes a submission rather than gating it.
    """
    try:
        current = get_current_user(request=request, authorization=authorization, db=db)
    except Exception:
        return None
    user = (current or {}).get("user")
    return getattr(user, "id", None)


def _iso(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


@coding_router.get("/problems")
async def list_problems():
    """List curated coding problems (full detail, six hand-written entries)."""
    service = get_code_executor_service()
    return {"problems": service.get_curated_problems()}


@coding_router.get("/problems/catalog")
async def list_problem_catalog(
    search: str = Query("", max_length=120),
    difficulty: str = Query("", max_length=16),
    topic: str = Query("", max_length=64),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Browsable index of every problem — curated set plus the full bank.

    Separate from ``/problems`` because that returns full detail for six
    problems, which is the wrong shape for a LeetCode-style list of ~1000.
    Returns listing metadata only; open a problem to get its description,
    examples and starter code.
    """
    service = get_code_executor_service()
    return service.get_problem_catalog(
        search=search, difficulty=difficulty, topic=topic, offset=offset, limit=limit
    )


@coding_router.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    """Retrieve problem detail with Python, JS, and Rust starter code."""
    service = get_code_executor_service()
    problem = service.get_problem_by_id(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found")
    return problem


@coding_router.post("/run", response_model=RunCodeResponse)
async def run_code(body: RunCodeRequest, request: Request):
    """Run candidate code against sample test suite."""
    _enforce_exec_quota(request)
    service = get_code_executor_service()
    res = service.execute_code(body.problem_id, body.language, body.code)
    return RunCodeResponse(
        success=res.get("success", False),
        passed=res.get("passed", False),
        runtime_ms=res.get("runtime_ms", 0.0),
        test_results=res.get("test_results", []),
        stdout=res.get("stdout", ""),
        stderr=res.get("stderr", ""),
        error=res.get("error"),
    )


@coding_router.post("/submit", response_model=SubmitCodeResponse)
async def submit_code(
    body: SubmitCodeRequest,
    request: Request,
    user_id: Optional[Any] = Depends(optional_user),
    repo: CodingSubmissionRepository = Depends(get_submission_repository),
):
    """Submit a solution, record it against the interview session, and review it."""
    _enforce_exec_quota(request)
    service = get_code_executor_service()
    exec_res = service.execute_code(body.problem_id, body.language, body.code)
    problem = service.get_problem_by_id(body.problem_id)
    title = problem["title"] if problem else body.problem_id

    # Bounded by CODE_REVIEW_TIMEOUT_SECONDS — the verdict must not wait on it.
    ai_res = service.evaluate_ai_code_quality(title, body.language, body.code)

    results = exec_res.get("test_results", []) or []
    submission_id: Optional[str] = None
    if body.session_id:
        submission_id = str(uuid.uuid4())
        try:
            repo.insert(
                submission_id=submission_id,
                session_id=body.session_id,
                user_id=user_id,
                problem_id=body.problem_id,
                problem_title=title,
                language=body.language,
                code=body.code,
                passed=bool(exec_res.get("passed", False)),
                tests_passed=sum(1 for r in results if r.get("passed")),
                tests_total=len(results),
                runtime_ms=float(exec_res.get("runtime_ms", 0.0) or 0.0),
                created_at=datetime.now(timezone.utc),
            )
        except Exception as exc:  # pragma: no cover - history is best-effort
            # A database that is down must not swallow the candidate's verdict.
            logger.warning(f"Could not record coding submission: {exc}")
            submission_id = None

    return SubmitCodeResponse(
        success=exec_res.get("success", False),
        passed=exec_res.get("passed", False),
        runtime_ms=exec_res.get("runtime_ms", 0.0),
        test_results=results,
        ai_analysis=ai_res.get("analysis", ""),
        error=exec_res.get("error"),
        submission_id=submission_id,
        session_id=body.session_id,
    )


@coding_router.get("/submissions", response_model=SubmissionListResponse)
async def list_submissions(
    session_id: str = Query(..., max_length=64),
    limit: int = Query(100, ge=1, le=200),
    repo: CodingSubmissionRepository = Depends(get_submission_repository),
):
    """Submission history for one interview session, newest first."""
    try:
        rows = repo.list_for_session(session_id, limit)
    except Exception as exc:
        logger.warning(f"Could not read coding submissions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Submission history is unavailable right now.",
        )

    return SubmissionListResponse(
        session_id=session_id,
        items=[
            SubmissionSummary(
                id=row.id,
                session_id=row.session_id,
                problem_id=row.problem_id or "",
                problem_title=row.problem_title or "",
                language=row.language or "",
                passed=bool(row.passed),
                tests_passed=row.tests_passed or 0,
                tests_total=row.tests_total or 0,
                runtime_ms=float(row.runtime_ms or 0.0),
                created_at=_iso(row.created_at),
            )
            for row in rows
        ],
    )
