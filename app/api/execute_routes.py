"""
Code execution routes — run candidate code from the interview code pad.

Executes Python in a subprocess on this server (no third-party execution
API) with a hard timeout and output cap so runaway code can't hang the app.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

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


@execute_router.post("/run", response_model=CodeRunResponse)
def run_code(payload: CodeRunRequest) -> CodeRunResponse:
    """Run Python code and return stdout/stderr, LeetCode-playground style."""
    if not payload.code.strip():
        return CodeRunResponse(success=False, stderr="No code to run.")

    with tempfile.TemporaryDirectory(prefix="codepad_") as workdir:
        script_path = Path(workdir) / "main.py"
        script_path.write_text(payload.code, encoding="utf-8")

        try:
            # -I: isolated mode — ignores env vars, user site-packages, and
            # keeps the script's directory out of sys.path surprises.
            proc = subprocess.run(
                [sys.executable, "-I", str(script_path)],
                input=payload.stdin,
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT_SECONDS,
                cwd=workdir,
            )
        except subprocess.TimeoutExpired as exc:
            partial_out = exc.stdout if isinstance(exc.stdout, str) else ""
            return CodeRunResponse(
                success=False,
                stdout=_truncate(partial_out or ""),
                stderr=f"Execution timed out after {RUN_TIMEOUT_SECONDS} seconds.",
                timed_out=True,
            )

    return CodeRunResponse(
        success=proc.returncode == 0,
        stdout=_truncate(proc.stdout),
        stderr=_truncate(proc.stderr),
        exit_code=proc.returncode,
    )
