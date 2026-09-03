"""Offline RAG quality evaluation (Module 14, item 12).

Runs a fixed set of labeled test cases (sample resumes + JDs) against the real
FAISS + sentence-transformers pipeline and reports:

  a) retrieval precision@k  — vs a manually labeled "correct chunk" set
  b) answer groundedness    — keyword overlap between retrieved chunks and the
                              LLM's generated question (baseline signal for
                              "did the model actually use what we retrieved?")
  c) latency percentiles    — p50/p95/p99 for the full retrieve+generate pipeline

Results are written to CSV + JSON. The script exits non-zero when any metric
falls below its threshold, so it can gate a deploy as a CI smoke test:

    python -m app.services.rag.rag_eval --out-dir reports/rag_eval
    # CI: fails the job if precision@k / groundedness dip or latency regresses.

LLM: by default the shared router (get_llm) is used. Pass --offline to use the
service's deterministic grounded fallback instead — no provider calls, fully
reproducible, still exercises retrieval + the grounding path end-to-end.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence


# ─────────────────────────────── labeled fixtures ───────────────────────────
# Each case: a candidate resume + JD, a query intent, and the set of chunk_ids
# we consider correct for that query. chunk_ids are deterministic from the
# embedder's chunking scheme: "{candidate_id}:resume:{section}".


@dataclass(frozen=True)
class EvalCase:
    candidate_id: str
    role: str
    resume_text: str
    job_description: str
    query_last_answer: str
    relevant_chunk_ids: frozenset  # manually labeled "correct" chunks
    expect_keywords: frozenset     # terms a grounded question should plausibly hit


_BACKEND_RESUME = (
    "Alex Rivera\n"
    "Summary\nBackend engineer specializing in high-throughput payment APIs.\n"
    "Skills\nPython, FastAPI, PostgreSQL, Kafka, Redis, Docker.\n"
    "Experience\nBuilt a payments API at 10k rps; cut p99 latency 40% via caching and keyset pagination.\n"
    "Projects\nDesigned a cursor-paginated feed and an idempotent event-consumer pipeline.\n"
)

_DS_RESUME = (
    "Priya Sharma\n"
    "Summary\nData scientist focused on production model reliability.\n"
    "Skills\nPython, scikit-learn, PyTorch, SQL, MLflow.\n"
    "Experience\nDiagnosed train/serve skew and class imbalance on a fraud model, lifting recall 25%.\n"
    "Projects\nBuilt a leakage-safe time-series feature pipeline with in-fold scaling.\n"
)


EVAL_CASES: List[EvalCase] = [
    EvalCase(
        candidate_id="eval_backend",
        role="backend_engineer",
        resume_text=_BACKEND_RESUME,
        job_description="Seeking a Python backend engineer with Kafka and PostgreSQL experience.",
        query_last_answer="I used keyset pagination to keep the feed stable under writes.",
        relevant_chunk_ids=frozenset(
            {"eval_backend:resume:experience", "eval_backend:resume:projects"}
        ),
        expect_keywords=frozenset({"pagination", "cursor", "latency", "payments", "idempotent", "kafka"}),
    ),
    EvalCase(
        candidate_id="eval_ds",
        role="data_scientist",
        resume_text=_DS_RESUME,
        job_description="Looking for a data scientist experienced with model monitoring and drift.",
        query_last_answer="I noticed accuracy was high but recall was poor in production.",
        relevant_chunk_ids=frozenset(
            {"eval_ds:resume:experience", "eval_ds:resume:projects"}
        ),
        expect_keywords=frozenset({"leakage", "skew", "imbalance", "drift", "recall", "feature"}),
    ),
]


# ─────────────────────────────── metric helpers ─────────────────────────────


def precision_at_k(retrieved_ids: Sequence[str], relevant: frozenset, k: int) -> float:
    """Fraction of the top-k retrieved chunks that are in the labeled relevant set."""
    if k <= 0:
        return 0.0
    top = retrieved_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for cid in top if cid in relevant)
    return hits / len(top)


_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set:
    return set(_WORD.findall((text or "").lower()))


def groundedness_overlap(retrieved_texts: Sequence[str], llm_output: str) -> float:
    """Baseline groundedness: fraction of the LLM output's content words that also
    appear in the retrieved context. High overlap ⇒ the model used what we gave it;
    ~0 overlap ⇒ it likely ignored retrieval and answered from priors."""
    out = _tokens(llm_output) - _STOPWORDS
    if not out:
        return 0.0
    ctx = set()
    for t in retrieved_texts:
        ctx |= _tokens(t)
    return len(out & ctx) / len(out)


_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "your",
    "you", "how", "what", "would", "do", "did", "is", "are", "this", "that", "it",
    "as", "at", "by", "be", "can", "we", "our", "explain", "describe", "walk",
    "me", "through", "specific", "decision", "trade", "off", "from",
}


def percentiles(values: Sequence[float], ps=(50, 95, 99)) -> Dict[str, float]:
    """Nearest-rank percentiles (no numpy dependency needed for the report)."""
    if not values:
        return {f"p{p}": 0.0 for p in ps}
    ordered = sorted(values)
    out: Dict[str, float] = {}
    for p in ps:
        rank = max(1, int(round(p / 100.0 * len(ordered))))
        out[f"p{p}"] = round(ordered[min(rank, len(ordered)) - 1], 4)
    return out


# ─────────────────────────────── stub LLM (offline) ─────────────────────────


class _GroundedStubLLM:
    """Deterministic offline LLM: builds a question from the retrieved context so
    the pipeline runs with no provider calls. Groundedness will be high by design
    — this validates plumbing/latency, not model quality. Use the real router
    (default) to measure whether a real model actually grounds on retrieval."""

    def generate_json(self, prompt, system_prompt=None, max_tokens=None):
        # Pull the first retrieved context line out of the prompt to echo a term.
        m = re.search(r"\[(?:resume|job_description|company)\][^\n]*", prompt)
        snippet = m.group(0)[:120] if m else "your background"
        return {
            "question": f"Tell me more about: {snippet}",
            "grounded_on": snippet,
            "topic": "eval",
        }


# ───────────────────────────────── runner ───────────────────────────────────


@dataclass
class CaseResult:
    candidate_id: str
    role: str
    precision_at_k: float
    groundedness: float
    latency_s: float
    retrieved_ids: List[str] = field(default_factory=list)


def run_eval(top_k: int, offline: bool, index_dir: str | None = None) -> List[CaseResult]:
    # Imports are local so `--help` works even without the heavy deps installed.
    from app.core import config
    from app.services.rag_service import RAGService

    llm = _GroundedStubLLM() if offline else None  # None ⇒ RAGService uses get_llm()
    # Isolate eval indices from the real RAG_INDEX_DIR (avoids polluting prod/dev
    # data and lets CI run against a throwaway temp dir).
    if index_dir:
        config.settings.RAG_INDEX_DIR = index_dir
    svc = RAGService(llm=llm)
    config.settings.RAG_TOP_K = top_k  # honor the requested k for this run

    results: List[CaseResult] = []
    for case in EVAL_CASES:
        svc.build_session_index(
            candidate_id=case.candidate_id,
            resume_text=case.resume_text,
            job_description=case.job_description,
            role=case.role,
        )

        start = time.perf_counter()
        out = svc.generate_question(
            candidate_id=case.candidate_id,
            role=case.role,
            last_answer=case.query_last_answer,
            asked_questions=[],
        )
        latency = time.perf_counter() - start

        retrieved = out.get("retrieved_chunks", [])
        retrieved_ids = [c["chunk_id"] for c in retrieved]
        retrieved_texts = [c["text"] for c in retrieved]

        results.append(
            CaseResult(
                candidate_id=case.candidate_id,
                role=case.role,
                precision_at_k=round(precision_at_k(retrieved_ids, case.relevant_chunk_ids, top_k), 4),
                groundedness=round(groundedness_overlap(retrieved_texts, out.get("question", "")), 4),
                latency_s=round(latency, 4),
                retrieved_ids=retrieved_ids,
            )
        )
    return results


def summarize(results: Sequence[CaseResult]) -> Dict[str, Any]:
    n = len(results) or 1
    return {
        "cases": len(results),
        "mean_precision_at_k": round(sum(r.precision_at_k for r in results) / n, 4),
        "mean_groundedness": round(sum(r.groundedness for r in results) / n, 4),
        "latency_seconds": percentiles([r.latency_s for r in results]),
    }


def write_reports(results: Sequence[CaseResult], summary: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "rag_eval.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate_id", "role", "precision_at_k", "groundedness", "latency_s", "retrieved_ids"])
        for r in results:
            w.writerow([r.candidate_id, r.role, r.precision_at_k, r.groundedness, r.latency_s, ";".join(r.retrieved_ids)])
    (out_dir / "rag_eval.json").write_text(
        json.dumps({"summary": summary, "cases": [vars(r) for r in results]}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {csv_path} and {out_dir / 'rag_eval.json'}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline RAG quality eval + CI smoke gate")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--out-dir", type=Path, default=Path("reports/rag_eval"))
    parser.add_argument(
        "--index-dir",
        default=None,
        help="Override RAG_INDEX_DIR for this run (use a temp dir in CI to avoid touching prod indices)",
    )
    parser.add_argument("--offline", action="store_true", help="Use deterministic stub LLM (no provider calls)")
    parser.add_argument("--min-precision", type=float, default=0.5, help="CI gate: min mean precision@k")
    parser.add_argument("--min-groundedness", type=float, default=0.15, help="CI gate: min mean groundedness overlap")
    parser.add_argument("--max-p95-latency", type=float, default=5.0, help="CI gate: max p95 pipeline latency (s)")
    args = parser.parse_args(argv)

    results = run_eval(top_k=args.top_k, offline=args.offline, index_dir=args.index_dir)
    summary = summarize(results)
    write_reports(results, summary, args.out_dir)

    print(json.dumps(summary, indent=2))

    # CI gate — exit non-zero on regression so a deploy pipeline can block.
    failures: List[str] = []
    if summary["mean_precision_at_k"] < args.min_precision:
        failures.append(f"precision@k {summary['mean_precision_at_k']} < {args.min_precision}")
    if summary["mean_groundedness"] < args.min_groundedness:
        failures.append(f"groundedness {summary['mean_groundedness']} < {args.min_groundedness}")
    p95 = summary["latency_seconds"]["p95"]
    if p95 > args.max_p95_latency:
        failures.append(f"p95 latency {p95}s > {args.max_p95_latency}s")

    if failures:
        print("RAG EVAL FAILED:\n  - " + "\n  - ".join(failures), file=sys.stderr)
        return 1
    print("RAG eval passed all gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
