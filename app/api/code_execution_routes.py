"""
Code Execution API Routes — Module 16.

Endpoints:
    GET  /coding/problems       — list curated coding problems
    GET  /coding/problems/{id}  — problem detail & starter code
    POST /coding/run            — run sample tests (Python, JS, Rust)
    POST /coding/submit         — submit full test suite & return AI review
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.services.code_executor_service import get_code_executor_service

coding_router = APIRouter(prefix="/coding", tags=["Code Execution Sandbox"])

# ── DTO Schemas ──────────────────────────────────────────────────────────────


class RunCodeRequest(BaseModel):
    problem_id: str
    language: str = Field("python", description="'python', 'javascript', or 'rust'")
    code: str = Field(..., min_length=1, max_length=10000)


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


# ── Routes ───────────────────────────────────────────────────────────────────


@coding_router.get("/problems")
async def list_problems():
    """List curated coding problems."""
    service = get_code_executor_service()
    return {"problems": service.get_curated_problems()}


@coding_router.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    """Retrieve problem detail with Python, JS, and Rust starter code."""
    service = get_code_executor_service()
    problem = service.get_problem_by_id(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{problem_id}' not found")
    return problem


@coding_router.post("/run", response_model=RunCodeResponse)
async def run_code(body: RunCodeRequest):
    """Run candidate code against sample test suite."""
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
async def submit_code(body: RunCodeRequest):
    """Submit solution against hidden test suite and return AI review."""
    service = get_code_executor_service()
    exec_res = service.execute_code(body.problem_id, body.language, body.code)
    problem = service.get_problem_by_id(body.problem_id)
    title = problem["title"] if problem else body.problem_id

    ai_res = service.evaluate_ai_code_quality(title, body.language, body.code)

    return SubmitCodeResponse(
        success=exec_res.get("success", False),
        passed=exec_res.get("passed", False),
        runtime_ms=exec_res.get("runtime_ms", 0.0),
        test_results=exec_res.get("test_results", []),
        ai_analysis=ai_res.get("analysis", ""),
        error=exec_res.get("error"),
    )
