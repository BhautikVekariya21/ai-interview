"""Code execution routes — run candidate code from the interview code pad.

Candidate code is hostile input, so it goes through the shared sandbox in
``app.services.code_sandbox`` rather than a bare subprocess on the API server.
That keeps it off the server's interpreter and out of reach of the process
environment, which holds every API key the app is configured with.
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import rate_limit_service
from app.services.code_runners import get_spec
from app.services.code_sandbox import SandboxUnavailable, get_sandbox

execute_router = APIRouter(prefix="/execute", tags=["Code Execution"])

RUN_TIMEOUT_SECONDS = 8
MAX_OUTPUT_CHARS = 20_000
MAX_CODE_CHARS = 50_000


class CodeRunRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_CHARS)
    stdin: str = Field(default="", max_length=10_000)


class CodeRunResponse(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False


def _truncate(text: str) -> str:
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + "\n… [output truncated]"
    return text


def _client_ip(request: Request) -> str:
    return rate_limit_service.client_ip(request)


@execute_router.post("/run", response_model=CodeRunResponse)
def run_code(payload: CodeRunRequest, request: Request) -> CodeRunResponse:
    """Run Python code and return stdout/stderr, LeetCode-playground style."""
    if not payload.code.strip():
        return CodeRunResponse(success=False, stderr="No code to run.")

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

    spec = get_spec("python")
    try:
        result = get_sandbox().run(
            spec,
            {spec.source_name: payload.code},
            timeout=RUN_TIMEOUT_SECONDS,
            stdin=payload.stdin,
        )
    except SandboxUnavailable as exc:
        # Never dress an unavailable sandbox up as a program error — the
        # candidate would waste the interview debugging working code.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Code execution is unavailable: {exc}",
        ) from exc

    if result.timed_out:
        return CodeRunResponse(
            success=False,
            stdout=_truncate(result.stdout),
            stderr=f"Execution timed out after {RUN_TIMEOUT_SECONDS} seconds.",
            timed_out=True,
        )

    return CodeRunResponse(
        success=result.exit_code == 0,
        stdout=_truncate(result.stdout),
        stderr=_truncate(result.stderr),
        exit_code=result.exit_code,
    )
