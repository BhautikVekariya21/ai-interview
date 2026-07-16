"""
FastAPI routes - ALL API endpoints for all modules.
"""

import io
import hashlib
import asyncio
import contextlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Query,
    Form,
)
from fastapi.responses import StreamingResponse
from loguru import logger

from app.core.config import settings
from app.schemas.schemas import (
    ResumeUploadResponse,
    ParsedResume,
    HealthCheckResponse,
    PersonalInfo,
    Skill,
    TracingStatusResponse,
)
from app.schemas.orchestration_schemas import (
    OrchestrationPlanRequest,
    OrchestrationStatusResponse,
)
from app.services.cache_service import get_cache
from app.core.exceptions import (
    ResumeParserBaseException,
    UnsupportedFileFormatError,
    FileSizeLimitError,
    EmptyResumeError,
)
from app.schemas.question_schemas import QuestionGenerationRequest
from app.services.faq_service import (
    fetch_faq_for_technology,
    list_supported_technologies,
)
from app.services.plagiarism_service import analyze_resume_plagiarism
from app.services.news_service import fetch_technology_news
from app.services.interview_orchestration import get_interview_orchestrator
from app.services.tracing_service import get_tracing_service

router = APIRouter(tags=["AI Interview System"])

_parser: Optional[Any] = None
_question_generator: Optional[Any] = None
_start_time = time.time()

_resume_parser_import_error: Optional[str] = None
try:
    from app.services.resume_parser import ResumeParser
except Exception as import_error:  # pragma: no cover - runtime env dependent
    ResumeParser = None  # type: ignore[assignment]
    _resume_parser_import_error = str(import_error)
    logger.warning(
        "Resume parser module unavailable. Module 1 endpoints will return 503. "
        f"Import error: {_resume_parser_import_error}"
    )

_question_generator_import_error: Optional[str] = None
try:
    from app.services.question_generator import QuestionGenerator
except Exception as import_error:  # pragma: no cover - runtime env dependent
    QuestionGenerator = None  # type: ignore[assignment]
    _question_generator_import_error = str(import_error)
    logger.warning(
        "Question generator module unavailable. Module 2 endpoints will return 503. "
        f"Import error: {_question_generator_import_error}"
    )


class _FallbackParserEngine:
    is_loaded: bool = False


class _FallbackResumeParser:
    """Lightweight parser used when ML-heavy parser dependencies are unavailable."""

    def __init__(self):
        self.ner_engine = _FallbackParserEngine()

    async def parse(self, file_content: bytes, filename: str, progress_callback=None):
        text = file_content.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        email = email_match.group(0) if email_match else None

        full_name = lines[0] if lines else None
        if full_name and "@" in full_name:
            full_name = None

        skill_names: list[str] = []
        skill_block_match = re.search(r"SKILLS?\s*[:\n](.*?)(\n[A-Z][A-Z\s]{2,}|$)", text, re.IGNORECASE | re.DOTALL)
        if skill_block_match:
            raw = skill_block_match.group(1)
            candidates = re.split(r"[,|/•\n]", raw)
            skill_names = [c.strip(" .:-") for c in candidates if c.strip()]

        if not skill_names:
            known = ["Python", "Java", "Go", "JavaScript", "React", "FastAPI", "PyTorch", "AWS", "Docker", "Kubernetes"]
            text_lower = text.lower()
            skill_names = [s for s in known if s.lower() in text_lower]

        skills = [Skill(name=s, category="other", confidence=0.6) for s in skill_names[:30]]

        return ParsedResume(
            personal_info=PersonalInfo(full_name=full_name, email=email),
            skills=skills,
            top_skills=[s.name for s in skills[:10]],
            primary_domain="software engineering",
            source_file_name=filename,
            source_file_type=Path(filename).suffix.lower().lstrip(".") or "txt",
            raw_text_length=len(text),
            overall_parse_confidence=0.6,
            parse_timestamp=datetime.now(timezone.utc).isoformat(),
            warnings=[
                "Fallback parser active: ML model dependencies unavailable."
            ],
        )


def get_parser() -> Any:
    global _parser
    if ResumeParser is None:
        if _parser is None:
            logger.warning(
                "Using fallback resume parser because full parser is unavailable. "
                f"Import error: {_resume_parser_import_error}"
            )
            _parser = _FallbackResumeParser()
        return _parser
    if _parser is None:
        _parser = ResumeParser()
    return _parser


def get_question_generator() -> Any:
    global _question_generator
    if QuestionGenerator is None:
        detail = (
            "Question generator is unavailable in this runtime. "
            f"Import error: {_question_generator_import_error}"
        )
        raise HTTPException(status_code=503, detail=detail)
    if _question_generator is None:
        _question_generator = QuestionGenerator()
    return _question_generator


def _sanitize_filename(name: str) -> str:
    stem = Path(name or "resume").stem
    ext = Path(name or "resume.pdf").suffix.lower() or ".pdf"
    safe_stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", stem).strip("._-")
    if not safe_stem:
        safe_stem = "resume"
    return f"{safe_stem}{ext}"


def _save_uploaded_resume(content: bytes, original_filename: str) -> str:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique = uuid.uuid4().hex[:8]
    safe_name = _sanitize_filename(original_filename)
    final_name = f"{ts}_{unique}_{safe_name}"
    final_path = upload_dir / final_name

    final_path.write_bytes(content)
    logger.info(
        f"Uploaded resume persisted: {final_path} ({len(content)} bytes)"
    )
    print(
        f"[upload] saved file: {final_path} ({len(content)} bytes)",
        flush=True,
    )
    return str(final_path)


async def _emit_progress(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def _map_parser_step_to_ui(
    parser_step: int, parser_total_steps: int, message: str
) -> dict:
    if parser_step <= 4:
        ui_step = parser_step
        progress = {1: 16, 2: 32, 3: 48, 4: 66}[ui_step]
    else:
        ui_step = 5
        progress = {5: 76, 6: 84, 7: 90}.get(parser_step, 90)

    return {
        "type": "progress",
        "step": ui_step,
        "total_steps": 6,
        "progress_percent": progress,
        "message": message,
        "real_step": parser_step,
        "real_total_steps": parser_total_steps,
    }


def _build_start_interview_payload(
    parsed: ParsedResume,
    question_set,
    elapsed_ms: float,
    workflow_plan: Optional[dict] = None,
) -> dict:
    cat_names = {
        "T": "Technical",
        "P": "Project",
        "B": "Behavioral",
        "C": "Conceptual",
        "R": "Role-fit",
    }

    # Get LLM provider info safely — NEVER from QuestionSet
    # (QuestionSet intentionally excludes internal provider details)
    llm_provider_info = "unknown"
    try:
        from app.services.llm_service import get_llm
        llm = get_llm()
        llm_provider_info = llm.active_provider or "unknown"
    except Exception:
        pass

    payload = {
        "success": True,
        "processing_time_ms": round(elapsed_ms, 1),
        "interview_session": {
            "candidate": {
                "name": parsed.personal_info.full_name,
                "email": parsed.personal_info.email,
                "level": parsed.experience_level.value,
                "domain": parsed.primary_domain,
                "years": parsed.total_experience_years,
            },
            "config": {
                "total_questions": question_set.total_questions,
                "estimated_duration_minutes": question_set.estimated_duration_minutes,
                "difficulty": question_set.base_difficulty,
                "categories": question_set.categories_distribution,
                "llm_provider": llm_provider_info,
                "fallback_chain": get_llm_fallback_info(),
            },
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "category": q.category.value,
                    "category_name": cat_names.get(
                        q.category.value, "Other"
                    ),
                    "difficulty": q.difficulty.value,
                    "time_limit": q.time_limit_seconds,
                    "context": q.context,
                    "resume_reference": q.resume_reference,
                    "expected_topics": q.expected_topics,
                    "follow_up_questions": q.follow_up_questions,
                }
                for q in question_set.questions
            ],
        },
        "parsed_resume": parsed.model_dump(),
    }
    if workflow_plan:
        payload["workflow_plan"] = workflow_plan
    return payload


# ==================== HEALTH ====================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    parser_loaded = False
    if ResumeParser is not None:
        try:
            parser = get_parser()
            parser_loaded = bool(parser.ner_engine.is_loaded)
        except Exception:
            parser_loaded = False
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        ner_model_loaded=parser_loaded,
        uptime_seconds=time.time() - _start_time,
    )


@router.get("/status")
async def detailed_status():
    """Detailed system status including LLM providers and fallback chain."""
    parser_loaded = False
    parser_error = _resume_parser_import_error
    if ResumeParser is not None:
        try:
            parser = get_parser()
            parser_loaded = bool(parser.ner_engine.is_loaded)
            parser_error = None
        except Exception as err:
            parser_error = str(err)
    from app.services.llm_service import get_llm

    llm = get_llm()
    llm_status = llm.get_status()

    question_generator_ready = QuestionGenerator is not None
    return {
        "server": "running",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "modules": {
            "module_1_parser": {
                "status": "ready" if parser_loaded else "degraded",
                "ner_model": parser_loaded,
                "error": parser_error,
            },
            "module_2_questions": {
                "status": "ready" if question_generator_ready else "degraded",
                "llm": llm_status,
                "error": _question_generator_import_error,
            },
            "module_10_tracing": get_tracing_service().get_status(),
            "module_11_orchestration": (
                get_interview_orchestrator().get_status().model_dump()
            ),
        },
    }



@router.get("/tracing/status", response_model=TracingStatusResponse)
async def tracing_status():
    """Return OpenTelemetry tracing status."""
    return TracingStatusResponse(**get_tracing_service().get_status())


@router.get(
    "/orchestration/status",
    response_model=OrchestrationStatusResponse,
)
async def orchestration_status():
    """Return advanced interview orchestration module status."""
    return get_interview_orchestrator().get_status()


@router.get("/orchestration/tools")
async def orchestration_tools():
    """List advanced interview tools available to workflow planners."""
    tools = get_interview_orchestrator().list_tools()
    return {
        "success": True,
        "total_tools": len(tools),
        "items": [tool.model_dump() for tool in tools],
    }


@router.get("/orchestration/workflows")
async def orchestration_workflows():
    """List advanced interview workflow blueprints."""
    workflows = get_interview_orchestrator().list_workflows()
    return {
        "success": True,
        "total_workflows": len(workflows),
        "items": [workflow.model_dump() for workflow in workflows],
    }


@router.post("/orchestration/plan")
async def orchestration_plan(request: OrchestrationPlanRequest):
    """Build a personalized interview workflow plan from parsed resume data."""
    return get_interview_orchestrator().build_plan(
        resume_data=request.resume_data,
        workflow_ids=request.workflow_ids,
        target_role=request.target_role,
        job_description=request.job_description,
    )



# ==================== MODULE 1: RESUME PARSER ====================


@router.post("/parse-resume", response_model=ResumeUploadResponse)
async def parse_resume(
    file: UploadFile = File(...),
    include_raw_text: bool = Query(False),
):
    """Upload resume -> get structured JSON."""
    start_time = time.time()
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
            
        size_limit_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > size_limit_bytes:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB."
            )
        
        incoming_name = file.filename or "resume.pdf"
        ext = Path(incoming_name).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file extension '{ext}'. "
                f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        print(
            f"[parse-resume] start: {incoming_name} ({len(content)} bytes)",
            flush=True,
        )
        _save_uploaded_resume(content, incoming_name)

        cache = get_cache()
        file_hash = hashlib.sha256(content).hexdigest()
        cache_key = cache.make_key(
            "resume:parse",
            json.dumps({"h": file_hash, "name": incoming_name}, sort_keys=True),
        )
        cached = cache.get(cache_key)
        if isinstance(cached, dict) and cached.get("data"):
            return ResumeUploadResponse(**cached)

        parser = get_parser()
        parsed = await parser.parse(content, incoming_name)
        plagiarism_report = analyze_resume_plagiarism(
            content.decode("utf-8", errors="ignore")
        )

        elapsed_ms = (time.time() - start_time) * 1000

        print(
            f"[parse-resume] done in {elapsed_ms:.0f}ms", flush=True
        )
        response = ResumeUploadResponse(
            success=True,
            message=f"Resume parsed in {elapsed_ms:.0f}ms",
            data=parsed,
            plagiarism_report=plagiarism_report,
            processing_time_ms=elapsed_ms,
        )
        cache.set(cache_key, response.model_dump(), ttl_seconds=3600)
        return response
    except HTTPException:
        raise
    except UnsupportedFileFormatError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except FileSizeLimitError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except EmptyResumeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ResumeParserBaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Parse error: {e}")
        print(f"[parse-resume] error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MODULE 2: QUESTION GENERATOR ====================


@router.post("/generate-questions")
async def generate_questions(
    file: UploadFile = File(...),
    num_questions: int = Query(default=15, ge=10, le=30),
    job_description: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    categories: Optional[str] = Form(None),
    bias_free: bool = Form(False),
):
    """Upload resume -> parse -> generate personalized interview questions."""
    start_time = time.time()
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
            
        size_limit_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > size_limit_bytes:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB."
            )

        parser = get_parser()
        parsed = await parser.parse(content, file.filename)

        cache = get_cache()
        file_hash = hashlib.sha256(content).hexdigest()
        q_cache_key = cache.make_key(
            "questions:generate",
            json.dumps({"h": file_hash, "nq": num_questions}, sort_keys=True),
        )
        cached_q = cache.get(q_cache_key)
        if isinstance(cached_q, dict) and cached_q.get("success"):
            return cached_q

        from app.services.question_generator import get_question_generator

        qgen = get_question_generator()
        
        # Parse categories string -> List of Enums if present
        cat_list = None
        if categories:
            from app.schemas.question_schemas import QuestionCategory
            cat_list = [QuestionCategory(c.strip()) for c in categories.split(",") if c.strip()]
            
        question_set = qgen.generate(
            resume_data=parsed.model_dump(), 
            num_questions=num_questions, 
            job_description=job_description,
            difficulty_override=difficulty,
            categories=cat_list,
            bias_free=bias_free
        )
        for q in question_set.questions:
            logger.info(
                f"[questions] Q{q.id} [{q.category.value}/{q.difficulty.value}] {q.question}"
            )

        elapsed_ms = (time.time() - start_time) * 1000
        workflow_plan = get_interview_orchestrator().build_plan(
            resume_data=parsed.model_dump(),
            target_role=parsed.primary_domain,
            job_description=job_description,
        )
        payload = {
            "success": True,
            "processing_time_ms": round(elapsed_ms, 1),
            "resume_summary": {
                "name": parsed.personal_info.full_name,
                "email": parsed.personal_info.email,
                "experience_level": parsed.experience_level.value,
                "total_experience_years": parsed.total_experience_years,
                "top_skills": parsed.top_skills[:8],
                "domain": parsed.primary_domain,
            },
            "questions": question_set.model_dump(),
            "workflow_plan": workflow_plan.model_dump(),
        }
        cache.set(q_cache_key, payload, ttl_seconds=1800)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Question generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/questions/generate")
async def generate_questions_from_resume_data(
    request: QuestionGenerationRequest,
):
    """Generate personalized interview questions from parsed resume data."""
    try:
        qgen = get_question_generator()
        question_set = qgen.generate(
            resume_data=request.resume_data,
            num_questions=request.num_questions,
            categories=request.categories,
            session_id=request.session_id,
            job_description=request.job_description,
            # For this endpoint, we'll respect existing overrides if we add them to the schema later
        )
        return question_set
    except Exception as e:
        logger.exception(f"Question generation from resume data failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate questions")


@router.post("/start-interview")
async def start_interview(
    file: UploadFile = File(...),
    num_questions: int = Query(default=15, ge=10, le=30),
    job_description: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    categories: Optional[str] = Form(None),
    bias_free: bool = Form(False),
):
    """Full interview init: parse resume + generate questions."""
    start_time = time.time()
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
            
        size_limit_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > size_limit_bytes:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB."
            )
            
        incoming_name = file.filename or "resume.pdf"

        print(
            f"[start-interview] start: {incoming_name} ({len(content)} bytes)",
            flush=True,
        )
        _save_uploaded_resume(content, incoming_name)

        cache = get_cache()
        file_hash = hashlib.sha256(content).hexdigest()
        start_cache_key = cache.make_key(
            "interview:start",
            json.dumps({"h": file_hash, "nq": num_questions}, sort_keys=True),
        )
        cached_payload = cache.get(start_cache_key)
        if isinstance(cached_payload, dict) and cached_payload.get("success"):
            logger.info("start-interview cache HIT")
            return cached_payload

        parser = get_parser()
        parsed = await parser.parse(content, incoming_name)

        from app.services.question_generator import get_question_generator

        print("[start-interview] generating interview questions", flush=True)
        qgen = get_question_generator()
        
        cat_list = None
        if categories:
            from app.schemas.question_schemas import QuestionCategory
            cat_list = [QuestionCategory(c.strip()) for c in categories.split(",") if c.strip()]
            
        question_set = qgen.generate(
            resume_data=parsed.model_dump(), 
            num_questions=num_questions, 
            job_description=job_description,
            difficulty_override=difficulty,
            categories=cat_list,
            bias_free=bias_free
        )
        for q in question_set.questions:
            logger.info(
                f"[start-interview/questions] Q{q.id} [{q.category.value}/{q.difficulty.value}] {q.question}"
            )

        elapsed_ms = (time.time() - start_time) * 1000
        workflow_plan = get_interview_orchestrator().build_plan(
            resume_data=parsed.model_dump(),
            target_role=parsed.primary_domain,
            job_description=job_description,
        )
        print(
            f"[start-interview] done in {elapsed_ms:.0f}ms", flush=True
        )

        payload = _build_start_interview_payload(
            parsed=parsed,
            question_set=question_set,
            elapsed_ms=elapsed_ms,
            workflow_plan=workflow_plan.model_dump(),
        )
        cache.set(start_cache_key, payload, ttl_seconds=1800)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Interview start failed: {e}")
        print(f"[start-interview] error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-interview-stream")
async def start_interview_stream(
    file: UploadFile = File(...),
    num_questions: int = Query(default=15, ge=10, le=30),
    job_description: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    categories: Optional[str] = Form(None),
    bias_free: bool = Form(False),
):
    """Streaming variant of interview init with NDJSON progress events."""

    async def event_stream():
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        async def push_event(event: dict) -> None:
            await queue.put(await _emit_progress(event))

        async def worker() -> None:
            start_time = time.time()
            try:
                content = await file.read()
                if not content:
                    await push_event(
                        {
                            "type": "error",
                            "step": 0,
                            "total_steps": 6,
                            "progress_percent": 0,
                            "message": "Empty file",
                            "status_code": 400,
                        }
                    )
                    return

                print(
                    f"[start-interview-stream] start: "
                    f"{file.filename or 'resume.pdf'} "
                    f"({len(content)} bytes)",
                    flush=True,
                )
                incoming_name = file.filename or "resume.pdf"
                _save_uploaded_resume(content, incoming_name)

                parser = get_parser()

                async def parser_progress(
                    step: int, total_steps: int, message: str
                ) -> None:
                    await push_event(
                        _map_parser_step_to_ui(
                            step, total_steps, message
                        )
                    )

                parsed = await parser.parse(
                    content,
                    incoming_name,
                    progress_callback=parser_progress,
                )

                from app.services.question_generator import get_question_generator

                print(
                    "[start-interview-stream] generating interview "
                    "questions",
                    flush=True,
                )
                await push_event(
                    {
                        "type": "progress",
                        "step": 6,
                        "total_steps": 6,
                        "progress_percent": 96,
                        "message": "Generating personalized "
                        "interview questions",
                    }
                )

                qgen = get_question_generator()
                
                cat_list = None
                if categories:
                    from app.schemas.question_schemas import QuestionCategory
                    try:
                        cat_list = [QuestionCategory(c.strip()) for c in categories.split(",") if c.strip()]
                    except Exception:
                        cat_list = None

                question_set = qgen.generate(
                    resume_data=parsed.model_dump(), 
                    num_questions=num_questions, 
                    job_description=job_description,
                    difficulty_override=difficulty,
                    categories=cat_list,
                    bias_free=bias_free
                )
                for q in question_set.questions:
                    logger.info(
                        f"[start-interview-stream/questions] Q{q.id} [{q.category.value}/{q.difficulty.value}] {q.question}"
                    )

                elapsed_ms = (time.time() - start_time) * 1000
                workflow_plan = get_interview_orchestrator().build_plan(
                    resume_data=parsed.model_dump(),
                    target_role=parsed.primary_domain,
                    job_description=job_description,
                )
                payload = _build_start_interview_payload(
                    parsed=parsed,
                    question_set=question_set,
                    elapsed_ms=elapsed_ms,
                    workflow_plan=workflow_plan.model_dump(),
                )

                print(
                    f"[start-interview-stream] done in "
                    f"{elapsed_ms:.0f}ms",
                    flush=True,
                )
                await push_event(
                    {
                        "type": "complete",
                        "step": 6,
                        "total_steps": 6,
                        "progress_percent": 100,
                        "message": "Interview ready",
                        "data": payload,
                    }
                )
            except UnsupportedFileFormatError as e:
                await push_event(
                    {
                        "type": "error",
                        "step": 0,
                        "total_steps": 6,
                        "progress_percent": 0,
                        "message": str(e),
                        "status_code": 415,
                    }
                )
            except FileSizeLimitError as e:
                await push_event(
                    {
                        "type": "error",
                        "step": 0,
                        "total_steps": 6,
                        "progress_percent": 0,
                        "message": str(e),
                        "status_code": 413,
                    }
                )
            except EmptyResumeError as e:
                await push_event(
                    {
                        "type": "error",
                        "step": 0,
                        "total_steps": 6,
                        "progress_percent": 0,
                        "message": str(e),
                        "status_code": 422,
                    }
                )
            except ResumeParserBaseException as e:
                await push_event(
                    {
                        "type": "error",
                        "step": 0,
                        "total_steps": 6,
                        "progress_percent": 0,
                        "message": str(e),
                        "status_code": 500,
                    }
                )
            except Exception as e:
                logger.exception(f"Interview stream failed: {e}")
                print(
                    f"[start-interview-stream] error: {e}",
                    flush=True,
                )
                await push_event(
                    {
                        "type": "error",
                        "step": 0,
                        "total_steps": 6,
                        "progress_percent": 0,
                        "message": str(e),
                        "status_code": 500,
                    }
                )
            finally:
                await queue.put(None)

        worker_task = asyncio.create_task(worker())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            if not worker_task.done():
                worker_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await worker_task

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache"},
    )


def get_llm_fallback_info() -> str:
    """Get human-readable fallback chain info."""
    from app.services.llm_service import get_llm

    llm = get_llm()
    if not llm.available_providers:
        return "none"
    return " -> ".join(llm.available_providers)


@router.post("/follow-up-question")
async def gen_follow_up(
    original_question: str = Query(...),
    candidate_answer: str = Query(...),
):
    """Generate adaptive follow-up question."""
    try:
        from app.services.question_generator import get_question_generator

        qgen = get_question_generator()
        follow_up = qgen.generate_follow_up(
            original_question=original_question,
            candidate_answer=candidate_answer,
            resume_data={},
        )
        return {"success": True, "follow_up": follow_up.model_dump()}
    except Exception as e:
        logger.exception(f"Follow-up failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MODULE 3: TTS ====================


@router.post("/tts")
async def text_to_speech(
    text: str = Query(..., description="Text to speak"),
    language: str = Query(default="en"),
    slow: bool = Query(default=False),
):
    """Convert text to speech audio (MP3)."""
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang=language, slow=slow)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            },
        )
    except ImportError:
        raise HTTPException(
            status_code=500, detail="pip install gTTS"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UTILITY ENDPOINTS ====================


@router.get("/supported-skills")
async def list_supported_skills():
    from app.services.skill_normalizer import DEFAULT_SKILL_TAXONOMY

    total = sum(len(s) for s in DEFAULT_SKILL_TAXONOMY.values())
    return {
        "total_skills": total,
        "categories": {
            c: list(s.keys())
            for c, s in DEFAULT_SKILL_TAXONOMY.items()
        },
    }


@router.get("/ner-tags")
async def list_ner_tags():
    try:
        from app.models.ner_model import NER_TAGS
    except Exception:
        NER_TAGS = [
            "O", "B-NAME", "I-NAME", "B-EMAIL", "I-EMAIL", "B-PHONE", "I-PHONE",
            "B-SKILL", "I-SKILL", "B-ORG", "I-ORG", "B-DEGREE", "I-DEGREE",
        ]

    return {
        "total_tags": len(NER_TAGS),
        "tags": NER_TAGS,
        "entity_types": list(
            set(t.split("-")[1] for t in NER_TAGS if "-" in t)
        ),
    }


@router.get("/llm-status")
async def llm_status():
    """Check LLM provider status and fallback chain."""
    from app.services.llm_service import get_llm

    llm = get_llm()
    status = llm.get_status()
    status["help"] = {
        "gemini": "FREE - Get key at: https://aistudio.google.com/apikey",
        "groq": "FREE - Get key at: https://console.groq.com/keys",
        "huggingface": "FREE - Get key at: https://huggingface.co/settings/tokens",
        "setup": "Add API key(s) to .env file in project root",
    }
    return status


@router.get("/faq/technologies")
async def faq_technologies():
    return {
        "success": True,
        "items": list_supported_technologies(),
        "source": {
            "name": "Stack Exchange API",
            "docs": "https://api.stackexchange.com/docs",
        },
    }


@router.get("/faq/{technology_id}")
async def technology_faq(technology_id: str):
    cache = get_cache()
    cache_key = cache.make_key("faq:technology", technology_id)
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("technology"):
        return cached

    try:
        payload = fetch_faq_for_technology(technology_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(f"FAQ fetch failed for {technology_id}: {exc}")
        raise HTTPException(status_code=502, detail="FAQ service temporarily unavailable") from exc

    cache.set(cache_key, payload, ttl_seconds=3600)
    return payload


@router.get("/news/technology")
async def technology_news(
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=18, ge=6, le=30),
):
    cache = get_cache()
    cache_key = cache.make_key(
        "news:technology",
        json.dumps({"category": category or "all", "limit": limit}, sort_keys=True),
    )
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("items"):
        return cached

    payload = fetch_technology_news(category=category, limit=limit)
    cache.set(cache_key, payload, ttl_seconds=900)
    return payload
