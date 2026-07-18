"""RAG service — retrieval-augmented question generation and answer scoring.

Ties together the embedder, a swappable vector store (FAISS today), the seed
reference bank, the existing multi-provider LLM router, and audit logging.

Design notes:
- One FAISS index per interview session, persisted under RAG_INDEX_DIR/<session>.
  A session's index holds the candidate's resume chunks + JD chunk. The role
  reference Q/A bank is a separate, process-wide index built once and reused.
- The vector store is referenced only through the VectorStore protocol, so a
  later pgvector/Qdrant backend drops in without touching this file's logic.
- Callers use it in-process via get_rag_service(), matching how other services
  (panel_service, confidence_analyzer) are invoked by the orchestrator.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.services.rag import audit_log
from app.services.rag.embedder import (
    chunk_job_description,
    chunk_resume,
    get_embedder,
)
from app.services.rag.faiss_store import FaissVectorStore, namespace_lock
from app.services.rag.metrics import observe_retrieval
from app.services.rag.vector_store import Chunk, RetrievedChunk, VectorStore


def _safe_session_name(candidate_id: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in candidate_id)[:120] or "session"


class RAGService:
    """Retrieval + grounded generation. Constructed once as a singleton."""

    def __init__(self, llm: Optional[Any] = None) -> None:
        # Injected dep defaulting to the shared router, matching panel_service.
        from app.services.llm_service import get_llm

        self._llm = llm or get_llm()
        self._embedder = get_embedder()
        self.dim = self._embedder.dim
        self._model_name = self._embedder.model_name
        self._reference_store: Optional[VectorStore] = None

    # ────────────────────────────── index building ──────────────────────────

    def _session_dir(self, candidate_id: str) -> Path:
        return Path(settings.RAG_INDEX_DIR) / _safe_session_name(candidate_id)

    def _new_store(
        self,
        session_dir: Path,
        metric: str = "l2",
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> VectorStore:
        """Single place that picks the backend — swap FAISS here for pgvector/Qdrant.

        Stamps the embedding model name so a later same-dimension model swap is
        rejected on load() instead of silently scoring garbage. ``extra_meta``
        carries provenance such as the seed-file hash for staleness checks.
        """
        return FaissVectorStore(
            session_dir=session_dir,
            dim=self.dim,
            metric=metric,
            model_name=self._model_name,
            extra_meta=extra_meta,
        )

    def _seed_hash(self) -> str:
        """SHA-256 of the current seed bank file content ('' if absent).

        Stamped into the reference-bank / canned index metadata so a changed seed
        file is detected on load and the index auto-rebuilt — no manual cache
        clearing required.
        """
        path = Path(settings.RAG_SEED_DATA_PATH)
        if not path.exists():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def build_session_index(
        self,
        candidate_id: str,
        resume_text: str,
        job_description: str = "",
        role: str = "",
    ) -> int:
        """Embed + persist the candidate's resume (chunked) and JD. Returns chunk count."""
        chunks: List[Chunk] = chunk_resume(resume_text, candidate_id)
        chunks.extend(chunk_job_description(job_description, role))
        if not chunks:
            logger.warning(f"No indexable content for candidate {candidate_id}")
            return 0

        embeddings = self._embedder.embed([c.source_text for c in chunks])
        session_dir = self._session_dir(candidate_id)
        with namespace_lock(session_dir):
            store = self._new_store(session_dir)
            store.add(embeddings, chunks)
            store.save()
        logger.info(f"Built session index for {candidate_id}: {len(chunks)} chunks")
        return len(chunks)

    def _load_session_store(self, candidate_id: str) -> Optional[VectorStore]:
        store = self._new_store(self._session_dir(candidate_id))
        return store if store.load() else None

    def _reference_bank_store(self) -> VectorStore:
        """Process-wide index of the role reference Q/A bank, built once, cached.

        Auto-rebuilds when the seed file changes: the seed's sha256 is stamped in
        the index metadata, and a mismatch on load triggers a rebuild from the
        current seed — no manual cache clearing required.
        """
        if self._reference_store is not None:
            return self._reference_store

        ref_dir = Path(settings.RAG_INDEX_DIR) / "_reference_bank"
        seed_hash = self._seed_hash()
        # Serialize the cold build across workers so two processes don't both
        # rebuild and overwrite each other into the shared namespace.
        with namespace_lock(ref_dir):
            store = self._new_store(ref_dir, extra_meta={"seed_hash": seed_hash})
            if store.load() and store.loaded_extra_meta.get("seed_hash") == seed_hash:
                self._reference_store = store
                return store
            if store.loaded_extra_meta and store.loaded_extra_meta.get("seed_hash") != seed_hash:
                logger.warning(
                    "Reference bank seed changed (hash mismatch) — rebuilding _reference_bank index."
                )

            chunks = self._load_reference_chunks()
            # Fresh store so a stale-but-loaded index is fully replaced, not appended to.
            store = self._new_store(ref_dir, extra_meta={"seed_hash": seed_hash})
            if chunks:
                embeddings = self._embedder.embed([c.source_text for c in chunks])
                store.add(embeddings, chunks)
                store.save()
        self._reference_store = store
        return store

    def _load_reference_chunks(self) -> List[Chunk]:
        path = Path(settings.RAG_SEED_DATA_PATH)
        if not path.exists():
            logger.warning(f"RAG seed data not found at {path}")
            return []
        data: Dict[str, List[Dict[str, Any]]] = json.loads(path.read_text(encoding="utf-8"))
        chunks: List[Chunk] = []
        for role, entries in data.items():
            for i, entry in enumerate(entries):
                # Index the question + reference answer + rubric together so a
                # topic query retrieves the full scoring context.
                text = (
                    f"Q: {entry.get('question', '')}\n"
                    f"Reference answer: {entry.get('reference_answer', '')}\n"
                    f"Rubric: {entry.get('rubric', '')}"
                )
                chunks.append(
                    Chunk(
                        chunk_id=f"ref:{role}:{entry.get('topic', i)}",
                        source_text=text,
                        source_type="reference_qa",
                        metadata={
                            "role": role,
                            "topic": entry.get("topic"),
                            "question": entry.get("question"),
                            "rubric": entry.get("rubric"),
                        },
                    )
                )
        return chunks

    # ────────────────────────────── retrieval ───────────────────────────────

    def _retrieve(
        self, store: VectorStore, query_text: str, top_k: Optional[int] = None, operation: str = "retrieve"
    ) -> List[RetrievedChunk]:
        if len(store) == 0:
            return []
        query_vec = self._embedder.embed_one(query_text)
        with observe_retrieval(operation) as record:
            hits = store.search(query_vec, top_k or settings.RAG_TOP_K)
            record(hits)
        return hits

    # ────────────────────────────── endpoints ───────────────────────────────

    def generate_question(
        self,
        candidate_id: str,
        role: str,
        last_answer: Optional[str] = None,
        asked_questions: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        company_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve resume/JD context and generate a grounded, non-repetitive question.

        When `company_id` is set, company docs (tech stack/standards) are retrieved
        as an additional grounding source. `difficulty` (easy/medium/hard/expert),
        typically supplied by /rag/adjust-difficulty, steers the target tier.
        """
        store = self._load_session_store(candidate_id)
        if store is None:
            raise ValueError(
                f"No session index for candidate '{candidate_id}'. "
                "Call build_session_index() first."
            )

        query_text = " ".join(
            part for part in [f"Role: {role}", f"Recent answer: {last_answer}" if last_answer else ""] if part
        )
        retrieved = self._retrieve(store, query_text, operation="generate_question")
        audit_log.log_retrieval(candidate_id, role, "generate_question", query_text, retrieved)

        # Optionally fold in company-specific context as an extra grounding source.
        company_retrieved: List[RetrievedChunk] = []
        if company_id:
            company_store = self._load_company_store(company_id)
            if company_store is not None:
                company_retrieved = self._retrieve(company_store, query_text)
                audit_log.log_retrieval(
                    candidate_id, role, "generate_question:company", query_text, company_retrieved
                )

        grounding = "\n".join(
            f"- [{rc.chunk.source_type}] {rc.chunk.source_text}" for rc in retrieved
        ) or "(no retrieved context)"
        company_grounding = "\n".join(
            f"- [company] {rc.chunk.source_text}" for rc in company_retrieved
        )
        avoid = "\n".join(f"- {q}" for q in (asked_questions or [])) or "(none yet)"
        difficulty_line = f"TARGET DIFFICULTY: {difficulty}\n\n" if difficulty else ""

        system_prompt = (
            "You are a senior technical interviewer. Generate ONE interview question that is "
            "grounded strictly in the candidate's actual claimed skills and experience from the "
            "retrieved context. The question must be specific, non-repetitive, and probe genuine "
            "understanding — not something answerable by anyone. If a target difficulty is given, "
            "calibrate the depth to that tier. If company context is provided, prefer questions "
            "relevant to that company's tech stack and standards."
        )
        user_prompt = (
            f"ROLE: {role}\n\n"
            f"{difficulty_line}"
            f"RETRIEVED CANDIDATE CONTEXT (resume + job description):\n{grounding}\n\n"
            + (f"COMPANY CONTEXT (tech stack / standards):\n{company_grounding}\n\n" if company_grounding else "")
            + f"QUESTIONS ALREADY ASKED (do not repeat or rephrase these):\n{avoid}\n\n"
            + (f"CANDIDATE'S LAST ANSWER (probe deeper if relevant):\n{last_answer}\n\n" if last_answer else "")
            + 'Return JSON: {"question": "...", "grounded_on": "which retrieved detail this uses", '
            '"topic": "short topic label"}'
        )

        result = self._llm.generate_json(user_prompt, system_prompt=system_prompt, max_tokens=500)
        if not isinstance(result, dict) or not result.get("question"):
            # LLM unavailable / malformed — surface a deterministic grounded fallback.
            top = retrieved[0].chunk.source_text[:160] if retrieved else "your background"
            result = {
                "question": f"Walk me through a specific decision or trade-off from: {top}",
                "grounded_on": top,
                "topic": role,
            }

        return {
            "candidate_id": candidate_id,
            "role": role,
            "question": result.get("question"),
            "topic": result.get("topic", role),
            "grounded_on": result.get("grounded_on"),
            "difficulty": difficulty,
            "retrieved_chunks": [_chunk_view(rc) for rc in retrieved],
        }

    def evaluate_answer(
        self,
        question: str,
        candidate_answer: str,
        role: str,
        candidate_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """Retrieve role rubric chunks and score the answer 0-10 with cited justification."""
        store = self._reference_bank_store()
        query_text = f"{role} {question}"
        retrieved = self._retrieve(store, query_text, operation="evaluate_answer")
        # Prefer rubric chunks for the same role when available.
        role_hits = [rc for rc in retrieved if rc.chunk.metadata.get("role") == role]
        retrieved = role_hits or retrieved
        audit_log.log_retrieval(candidate_id, role, "evaluate_answer", query_text, retrieved)

        rubric_context = "\n".join(
            f"- {rc.chunk.source_text}" for rc in retrieved
        ) or "(no rubric retrieved — score on general merit)"

        system_prompt = (
            "You are a strict but fair technical grader. Score the candidate's answer from 0 to 10 "
            "using ONLY the retrieved reference rubric as your standard. Justify the score by citing "
            "which rubric criteria were met or missed. Do not invent criteria beyond the rubric."
        )
        user_prompt = (
            f"ROLE: {role}\n\nQUESTION:\n{question}\n\n"
            f"RETRIEVED REFERENCE RUBRIC(S):\n{rubric_context}\n\n"
            f"CANDIDATE ANSWER:\n{candidate_answer}\n\n"
            'Return JSON: {"score": <int 0-10>, "justification": "...", '
            '"criteria_met": ["..."], "criteria_missed": ["..."]}'
        )

        result = self._llm.generate_json(user_prompt, system_prompt=system_prompt, max_tokens=600)

        # LLM outage / malformed output: return an explicit UNSCORED state rather
        # than a real 0. A 0 is indistinguishable from a genuinely-poor answer and
        # would pollute report averages; `unscored` lets downstream exclude it.
        if not isinstance(result, dict) or "score" not in result:
            # Still record the answer for duplicate detection (best-effort) before returning.
            try:
                self.record_answer(role, question, candidate_answer, candidate_id)
            except Exception as exc:  # indexing is best-effort, never fail scoring
                logger.warning(f"record_answer failed (non-fatal): {exc}")
            return {
                "role": role,
                "question": question,
                "score": None,
                "unscored": True,
                "justification": "Automated scoring unavailable; manual review required.",
                "criteria_met": [],
                "criteria_missed": [],
                "rubric_snippets": [_chunk_view(rc) for rc in retrieved],
            }

        try:
            score = max(0, min(10, int(round(float(result.get("score", 0))))))
        except (TypeError, ValueError):
            score = 0

        # Record the answer into the per-role cross-session index so future
        # candidates can be checked for near-duplicate (copied) responses.
        try:
            self.record_answer(role, question, candidate_answer, candidate_id)
        except Exception as exc:  # indexing is best-effort, never fail scoring
            logger.warning(f"record_answer failed (non-fatal): {exc}")

        return {
            "role": role,
            "question": question,
            "score": score,
            "unscored": False,
            "justification": result.get("justification", ""),
            "criteria_met": result.get("criteria_met", []) or [],
            "criteria_missed": result.get("criteria_missed", []) or [],
            "rubric_snippets": [_chunk_view(rc) for rc in retrieved],
        }

    # ─────────────────────── cross-session answer index ─────────────────────

    def _answer_index_dir(self, role: str) -> Path:
        return Path(settings.RAG_INDEX_DIR) / "_answers" / _safe_session_name(role or "general")

    def record_answer(self, role: str, question: str, answer: str, candidate_id: str) -> None:
        """Append a candidate's answer to the per-role cosine index for later
        cross-session similarity checks. Best-effort; append-then-save.

        The load-modify-save cycle runs under the namespace lock so two
        candidates finishing an answer for the same role serialize instead of
        lost-updating each other's appended history.
        """
        answer = (answer or "").strip()
        if len(answer) < 20:  # too short to be a meaningful duplicate signal
            return
        answer_dir = self._answer_index_dir(role)
        with namespace_lock(answer_dir):
            store = self._new_store(answer_dir, metric="cosine")
            store.load()  # append to existing history if present
            chunk = Chunk(
                chunk_id=f"ans:{_safe_session_name(candidate_id)}:{uuid.uuid4().hex[:8]}",
                source_text=answer[:2000],
                source_type="past_answer",
                metadata={"role": role, "candidate_id": candidate_id, "question": question[:400]},
            )
            store.add([self._embedder.embed_one(answer)], [chunk])
            store.save()

    def _canned_store(self) -> VectorStore:
        """Cosine index over the reference bank's canonical answers (canned set).

        Like the reference bank, this is stamped with the seed hash and rebuilt
        automatically when the seed file changes.
        """
        canned_dir = Path(settings.RAG_INDEX_DIR) / "_canned"
        seed_hash = self._seed_hash()
        with namespace_lock(canned_dir):
            store = self._new_store(canned_dir, metric="cosine", extra_meta={"seed_hash": seed_hash})
            if store.load() and store.loaded_extra_meta.get("seed_hash") == seed_hash:
                return store
            if store.loaded_extra_meta and store.loaded_extra_meta.get("seed_hash") != seed_hash:
                logger.warning("Canned answer seed changed (hash mismatch) — rebuilding _canned index.")

            chunks: List[Chunk] = []
            for rc in self._load_reference_chunks():
                # Index the reference answer text alone for duplicate detection.
                chunks.append(
                    Chunk(
                        chunk_id=f"canned:{rc.chunk_id}",
                        source_text=rc.source_text,
                        source_type="canned_answer",
                        metadata=rc.metadata,
                    )
                )
            # Fresh store so a stale-but-loaded index is fully replaced, not appended to.
            store = self._new_store(canned_dir, metric="cosine", extra_meta={"seed_hash": seed_hash})
            if chunks:
                store.add(self._embedder.embed([c.source_text for c in chunks]), chunks)
                store.save()
            return store

    def detect_similarity(
        self,
        answer: str,
        role: str,
        candidate_id: str = "anonymous",
        threshold: float = 0.9,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Flag answers that closely match past candidates' answers or canned answers.

        Returns a violation payload (frontend renders it via the existing sonner
        toast proctoring pattern) when max cosine similarity exceeds `threshold`.
        """
        answer = (answer or "").strip()
        query_vec = self._embedder.embed_one(answer) if answer else None
        matches: List[RetrievedChunk] = []

        if query_vec is not None:
            past_store = self._new_store(self._answer_index_dir(role), metric="cosine")
            if past_store.load() and len(past_store) > 0:
                matches.extend(
                    rc
                    for rc in past_store.search(query_vec, top_k or settings.RAG_TOP_K)
                    # Exclude this candidate's own previously-recorded answers.
                    if rc.chunk.metadata.get("candidate_id") != candidate_id
                )
            canned = self._canned_store()
            if len(canned) > 0:
                matches.extend(canned.search(query_vec, top_k or settings.RAG_TOP_K))

        matches.sort(key=lambda rc: rc.similarity, reverse=True)
        matches = matches[: (top_k or settings.RAG_TOP_K)]
        audit_log.log_retrieval(candidate_id, role, "detect_similarity", answer[:500], matches)

        max_similarity = matches[0].similarity if matches else 0.0
        flagged = max_similarity >= threshold

        violation = None
        if flagged:
            top = matches[0]
            source = "a canned/reference answer" if top.chunk.source_type == "canned_answer" else "another candidate's answer"
            violation = {
                "type": "answer_similarity",
                "severity": "high",
                "message": (
                    f"⚠️ Answer is {round(max_similarity * 100)}% similar to {source}. "
                    "This has been flagged for review."
                ),
                "similarity": round(max_similarity, 4),
                "matched_source_type": top.chunk.source_type,
            }

        return {
            "flagged": flagged,
            "threshold": threshold,
            "max_similarity": round(max_similarity, 4),
            "matches": [_chunk_view(rc) for rc in matches],
            "violation": violation,
        }

    # ─────────────────────────── difficulty adjustment ──────────────────────

    _DIFFICULTY_ORDER = ["easy", "medium", "hard", "expert"]

    def adjust_difficulty(
        self,
        role: str,
        recent_answers: List[str],
        current_difficulty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Recommend the next question difficulty from the retrieved graded
        reference answers closest to the candidate's recent answers."""
        joined = " ".join(a for a in recent_answers if a).strip()
        if not joined:
            recommended = current_difficulty or "medium"
            return {
                "recommended_difficulty": recommended,
                "reason": "No recent answers to assess; keeping current tier.",
                "retrieved": [],
            }

        store = self._reference_bank_store()
        retrieved = self._retrieve(store, f"{role} {joined}")
        role_hits = [rc for rc in retrieved if rc.chunk.metadata.get("role") == role]
        retrieved = role_hits or retrieved
        audit_log.log_retrieval(role, role, "adjust_difficulty", joined[:500], retrieved)

        rubric_context = "\n".join(f"- {rc.chunk.source_text}" for rc in retrieved) or "(none)"
        system_prompt = (
            "You are an adaptive interview difficulty controller. Given the candidate's recent "
            "answers and the closest graded reference material, recommend the next question's "
            "difficulty tier: easy, medium, hard, or expert. Raise the tier when answers are strong "
            "and complete; lower it when they are weak or incomplete."
        )
        user_prompt = (
            f"ROLE: {role}\n"
            f"CURRENT DIFFICULTY: {current_difficulty or 'unknown'}\n\n"
            f"CANDIDATE RECENT ANSWERS:\n{joined[:2000]}\n\n"
            f"CLOSEST GRADED REFERENCE MATERIAL:\n{rubric_context}\n\n"
            'Return JSON: {"recommended_difficulty": "easy|medium|hard|expert", "reason": "..."}'
        )
        result = self._llm.generate_json(user_prompt, system_prompt=system_prompt, max_tokens=250)

        recommended = None
        reason = ""
        if isinstance(result, dict):
            recommended = str(result.get("recommended_difficulty", "")).lower().strip()
            reason = result.get("reason", "")
        if recommended not in self._DIFFICULTY_ORDER:
            recommended = current_difficulty if current_difficulty in self._DIFFICULTY_ORDER else "medium"
            reason = reason or "Defaulted difficulty; recommendation unavailable."

        return {
            "recommended_difficulty": recommended,
            "reason": reason,
            "retrieved": [_chunk_view(rc) for rc in retrieved],
        }

    # ─────────────────────────── company context ────────────────────────────

    def _company_dir(self, company_id: str) -> Path:
        return Path(settings.RAG_INDEX_DIR) / "_company" / _safe_session_name(company_id)

    def _load_company_store(self, company_id: str) -> Optional[VectorStore]:
        store = self._new_store(self._company_dir(company_id))
        return store if store.load() else None

    def add_company_docs(self, company_id: str, documents: List[str], role: str = "") -> int:
        """Embed and store company docs (tech stack, standards) under a per-company
        namespace, appending to any existing company index. Returns total chunk count."""
        docs = [d.strip() for d in documents if d and d.strip()]
        if not docs:
            return 0
        company_dir = self._company_dir(company_id)
        with namespace_lock(company_dir):
            store = self._new_store(company_dir)
            store.load()  # append to existing company docs
            chunks = [
                Chunk(
                    chunk_id=f"company:{_safe_session_name(company_id)}:{uuid.uuid4().hex[:8]}",
                    source_text=doc[:2000],
                    source_type="company_doc",
                    metadata={"company_id": company_id, "role": role},
                )
                for doc in docs
            ]
            store.add(self._embedder.embed([c.source_text for c in chunks]), chunks)
            store.save()
            total = len(store)
        logger.info(f"Indexed {len(chunks)} company docs for {company_id} (total {total})")
        return total

    # ─────────────────────────── final report ───────────────────────────────

    def generate_report(
        self,
        session_id: str,
        role: str,
        qa_pairs: List[Dict[str, Any]],
        candidate_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a grounded final report from the session's Q&A + scores.

        Accepts the same qa_pairs shape the frontend sends to /evaluation/evaluate-batch,
        retrieves matching rubric evidence per answer, and asks the LLM router for a
        report that cites specific answers and the rubric standard behind each score.
        """
        if not qa_pairs:
            raise ValueError("qa_pairs cannot be empty")

        ref_store = self._reference_bank_store()
        evidence_blocks: List[str] = []
        per_question: List[Dict[str, Any]] = []

        for i, qa in enumerate(qa_pairs, start=1):
            question = str(qa.get("question", ""))
            answer = str(qa.get("answer", ""))
            score = qa.get("score")
            retrieved = self._retrieve(ref_store, f"{role} {question}")
            role_hits = [rc for rc in retrieved if rc.chunk.metadata.get("role") == role]
            retrieved = role_hits or retrieved
            audit_log.log_retrieval(session_id, role, "generate_report", question[:300], retrieved)

            rubric = "; ".join(rc.chunk.source_text[:200] for rc in retrieved) or "(no rubric)"
            score_str = f"{score}" if score is not None else "unscored"
            evidence_blocks.append(
                f"Q{i}: {question}\nAnswer: {answer[:600]}\nScore: {score_str}\nRubric evidence: {rubric}"
            )
            per_question.append(
                {"question_number": i, "question": question, "score": score,
                 "rubric_snippets": [_chunk_view(rc) for rc in retrieved]}
            )

        evidence = "\n\n".join(evidence_blocks)
        system_prompt = (
            "You are writing a final interview evaluation report. Ground every claim in the "
            "provided Q&A evidence and rubric snippets — cite specific answers by their question "
            "number when justifying a score or observation. Be concrete and fair; do not invent "
            "facts not present in the evidence."
        )
        user_prompt = (
            f"CANDIDATE: {candidate_name or 'the candidate'}\nROLE: {role}\n\n"
            f"INTERVIEW EVIDENCE (questions, answers, scores, retrieved rubric):\n{evidence}\n\n"
            'Return JSON: {"summary": "...", "strengths": ["..."], "weaknesses": ["..."], '
            '"per_question_notes": [{"question_number": 1, "note": "cites the answer"}], '
            '"recommendation": "one of: strong hire, hire, maybe, no hire"}'
        )
        result = self._llm.generate_json(user_prompt, system_prompt=system_prompt, max_tokens=1200)

        # Exclude unscored answers (score is None or explicitly flagged unscored)
        # from the average — counting an LLM-outage answer as 0 would understate
        # the candidate. Surface the count so the omission is visible, not silent.
        def _is_unscored(qa: Dict[str, Any]) -> bool:
            return qa.get("unscored") is True or not isinstance(qa.get("score"), (int, float))

        scores = [float(qa["score"]) for qa in qa_pairs if not _is_unscored(qa)]
        unscored_count = sum(1 for qa in qa_pairs if _is_unscored(qa))
        overall = round(sum(scores) / len(scores), 2) if scores else None

        if not isinstance(result, dict):
            result = {
                "summary": "Automated report generation unavailable; manual review required.",
                "strengths": [], "weaknesses": [], "per_question_notes": [],
                "recommendation": "maybe",
            }

        return {
            "session_id": session_id,
            "role": role,
            "candidate_name": candidate_name,
            "overall_score": overall,
            "scored_count": len(scores),
            "unscored_count": unscored_count,
            "summary": result.get("summary", ""),
            "strengths": result.get("strengths", []) or [],
            "weaknesses": result.get("weaknesses", []) or [],
            "recommendation": result.get("recommendation", ""),
            "per_question_notes": result.get("per_question_notes", []) or [],
            "evidence": per_question,
        }


def _chunk_view(rc: RetrievedChunk) -> Dict[str, Any]:
    """Compact, JSON-serializable view of a retrieval hit for API responses."""
    return {
        "chunk_id": rc.chunk.chunk_id,
        "source_type": rc.chunk.source_type,
        "text": rc.chunk.source_text[:400],
        "similarity": rc.similarity,
        "distance": round(rc.distance, 4),
    }


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """Process-wide singleton, matching get_llm()/get_confidence_analyzer()."""
    return RAGService()
