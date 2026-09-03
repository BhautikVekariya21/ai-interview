"""Pydantic schemas for the RAG module (Module 14).

Single source of truth for the request/response models used by
`app/api/rag_routes.py`. These mirror exactly the dict shapes the service layer
(`app/services/rag_service.py`) already returns, so wiring them as `response_model=`
targets is pure centralization — no field is renamed, added, or dropped, and the
HTTP contract the frontend depends on (`frontend/src/lib/api.ts`) is unchanged.

Design note on embeddings: `RetrievalChunk` carries the raw vector for INTERNAL
use only (indexing, debugging). `RetrievedChunkView` is the API-facing hit view
and never includes an embedding vector.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SourceType = Literal["resume", "jd", "rubric", "company_doc", "past_answer", "canned_answer"]
DifficultyTier = Literal["easy", "medium", "hard", "expert"]


# ─────────────────────────── shared retrieval view ──────────────────────────


class RetrievedChunkView(BaseModel):
    """Compact, API-safe view of a single retrieval hit (no embedding vector).

    Matches `RAGService._chunk_view()` in app/services/rag_service.py 1:1.
    """

    chunk_id: str
    source_type: str
    text: str
    similarity: float
    distance: float


# ─────────────────────────────── build index ────────────────────────────────


class BuildIndexRequest(BaseModel):
    candidate_id: str = Field(..., description="Stable id for the interview session")
    resume_text: str = Field(..., description="Full resume text (chunked by section)")
    job_description: str = Field(default="", description="Target job description")
    role: str = Field(default="", description="Role label, e.g. backend_engineer")


class BuildIndexResponse(BaseModel):
    candidate_id: str
    chunks_indexed: int


# ─────────────────────────── question generation ────────────────────────────


class GenerateQuestionRequest(BaseModel):
    candidate_id: str
    role: str
    last_answer: Optional[str] = Field(default=None, description="Candidate's previous answer")
    asked_questions: List[str] = Field(
        default_factory=list, description="Questions already asked, to avoid repetition"
    )
    difficulty: Optional[str] = Field(
        default=None,
        description="Target tier: easy|medium|hard|expert (e.g. from /rag/adjust-difficulty)",
    )
    company_id: Optional[str] = Field(
        default=None, description="If set, fold company docs into retrieval grounding"
    )


class GenerateQuestionResponse(BaseModel):
    candidate_id: str
    role: str
    question: str
    topic: str
    grounded_on: Optional[str] = None
    difficulty: Optional[str] = None
    retrieved_chunks: List[RetrievedChunkView]


# ─────────────────────────── answer evaluation ──────────────────────────────


class EvaluateAnswerRequest(BaseModel):
    question: str
    candidate_answer: str
    role: str
    candidate_id: str = "anonymous"


class EvaluateAnswerResponse(BaseModel):
    role: str
    question: str
    score: Optional[int] = Field(
        default=None, ge=0, le=10, description="Rubric score 0-10; null when unscored (LLM outage)"
    )
    unscored: bool = Field(
        default=False,
        description="True when automated scoring was unavailable and manual review is required",
    )
    justification: str
    criteria_met: List[str]
    criteria_missed: List[str]
    rubric_snippets: List[RetrievedChunkView]


# ─────────────────────── similarity detection (proctoring) ───────────────────


class DetectSimilarityRequest(BaseModel):
    answer: str
    role: str
    candidate_id: str = "anonymous"
    threshold: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Cosine similarity flag threshold"
    )


class ViolationEvent(BaseModel):
    type: str
    severity: str
    message: str
    similarity: float
    matched_source_type: str


class DetectSimilarityResponse(BaseModel):
    flagged: bool
    threshold: float
    max_similarity: float
    matches: List[RetrievedChunkView]
    violation: Optional[ViolationEvent] = None


# ─────────────────────────── adaptive difficulty ────────────────────────────


class AdjustDifficultyRequest(BaseModel):
    role: str
    recent_answers: List[str] = Field(default_factory=list)
    current_difficulty: Optional[str] = None


class AdjustDifficultyResponse(BaseModel):
    recommended_difficulty: str
    reason: str
    retrieved: List[RetrievedChunkView]


# ───────────────────────────── company context ──────────────────────────────


class CompanyContextRequest(BaseModel):
    company_id: str
    documents: List[str] = Field(..., description="Role-specific docs: tech stack, standards, etc.")
    role: str = ""


class CompanyContextResponse(BaseModel):
    company_id: str
    chunks_indexed: int


# ───────────────────────────── final report ─────────────────────────────────


class QAPair(BaseModel):
    question: str
    answer: str = ""
    score: Optional[float] = None


class GenerateReportRequest(BaseModel):
    session_id: str
    role: str
    qa_pairs: List[QAPair]
    candidate_name: Optional[str] = None


class GenerateReportResponse(BaseModel):
    session_id: str
    role: str
    candidate_name: Optional[str] = None
    overall_score: Optional[float] = None
    scored_count: int = Field(default=0, description="Answers included in the average")
    unscored_count: int = Field(
        default=0, description="Answers excluded from the average (unscored / manual review)"
    )
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    per_question_notes: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]


# ─────────────────────── internal-only retrieval model ──────────────────────
# Not wired to any endpoint. Retained for internal use (indexing/debugging)
# where the dense vector must travel with the chunk; never serialize this in a
# response — project to `RetrievedChunkView` (which omits the vector) first.


class RetrievalChunk(BaseModel):
    """Internal retrieval unit that carries the embedding vector.

    INTERNAL ONLY — do NOT return this model from an endpoint. Use
    `to_public()` to project to the API-safe `RetrievedChunkView`.
    """

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(..., description="Stable id, e.g. 'ref:backend_engineer:pagination'")
    source_type: SourceType = Field(..., description="Provenance of the chunk")
    source_text: str = Field(..., description="Raw indexed text")
    embedding_vector: Optional[List[float]] = Field(
        default=None,
        description="INTERNAL ONLY — dense embedding; excluded from API responses.",
        exclude=True,  # belt-and-suspenders: never serialized even if this model leaks out
    )
    similarity: float = Field(
        default=0.0, ge=0.0, le=1.0, description="0-1 similarity to the query (1 = identical)"
    )
    distance: float = Field(default=0.0, description="Backend distance (lower = closer)")

    def to_public(self) -> "RetrievedChunkView":
        return RetrievedChunkView(
            chunk_id=self.chunk_id,
            source_type=self.source_type,
            text=self.source_text[:400],
            similarity=self.similarity,
            distance=self.distance,
        )
