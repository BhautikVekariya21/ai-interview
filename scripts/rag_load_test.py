#!/usr/bin/env python3
"""Concurrent load test for the RAG embedding hot path (Module 14 audit, item 5).

Simulates N concurrent interview sessions, each building a session index once and
then repeatedly hitting POST /rag/generate-question. The goal is to find the
*crossover point* on a target host — how many concurrent sessions the single,
CPU-bound, process-wide embedder can serve before per-request latency saturates.

This is a MANUAL measurement tool. It is intentionally NOT wired into CI (results
are host-specific) and is pure client-side load generation — it provisions no
infra and mutates only the RAG index namespaces of the synthetic candidate ids
it creates (default prefix ``loadtest-``), which are safe to delete afterwards.

--------------------------------------------------------------------------------
Usage
--------------------------------------------------------------------------------
1. Start the API against the host you want to measure, e.g.:

       uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

   Measure with --workers 1 first to characterize a single embedder; then raise
   worker count to see how gunicorn/uvicorn workers change the crossover.

2. Install the client dep (not in requirements.txt — this is a dev tool):

       pip install aiohttp

3. Run a sweep of concurrency levels:

       python scripts/rag_load_test.py --base-url http://localhost:8000 \
           --concurrency 1,2,4,8,16,32 --requests-per-session 10

   Or a single level:

       python scripts/rag_load_test.py --concurrency 8 --requests-per-session 20

--------------------------------------------------------------------------------
Reading the output
--------------------------------------------------------------------------------
For each concurrency level it prints throughput (req/s) and latency percentiles
(p50/p95/p99) for /rag/generate-question. Walk the concurrency up: throughput
climbs, then plateaus while p95/p99 climb sharply — that knee is the saturation
point for this host + worker count. Cross-reference with the Prometheus metrics
``embedding_duration_seconds`` and ``embedding_cache_events_total`` on /metrics
to confirm whether embedding (not the LLM call) is the bottleneck.

Note: /rag/generate-question also makes an LLM router call. To isolate embedding
cost, point the router at a stub/local model (or expect LLM latency to dominate
and interpret results accordingly).
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from typing import List

try:
    import aiohttp
except ImportError:  # pragma: no cover - dev-only tool
    raise SystemExit(
        "aiohttp is required for the load test. Install it with: pip install aiohttp"
    )


_SAMPLE_RESUME = (
    "Summary: Senior backend engineer with 8 years building distributed systems.\n"
    "Experience: Led migration of a monolith to event-driven microservices on "
    "Kubernetes; owned the payments ledger service handling 5k rps.\n"
    "Skills: Python, Go, PostgreSQL, Kafka, Redis, gRPC, Terraform, observability.\n"
    "Projects: Built a real-time fraud-scoring pipeline with sub-100ms p99.\n"
    "Education: BSc Computer Science."
)
_SAMPLE_JD = (
    "We are hiring a backend engineer to design low-latency APIs, own data "
    "consistency across services, and improve platform reliability."
)


async def _build_index(session: aiohttp.ClientSession, base_url: str, candidate_id: str, role: str) -> None:
    payload = {
        "candidate_id": candidate_id,
        "resume_text": _SAMPLE_RESUME,
        "job_description": _SAMPLE_JD,
        "role": role,
    }
    async with session.post(f"{base_url}/rag/build-index", json=payload) as resp:
        resp.raise_for_status()
        await resp.read()


async def _generate_question(
    session: aiohttp.ClientSession, base_url: str, candidate_id: str, role: str, turn: int
) -> float:
    """POST /rag/generate-question once; return wall-clock latency in seconds."""
    payload = {
        "candidate_id": candidate_id,
        "role": role,
        # Vary last_answer per turn so the query text (and thus the embed) differs,
        # exercising cache misses the way a real multi-turn interview would.
        "last_answer": f"On turn {turn} I would use keyset pagination and a bounded queue.",
        "asked_questions": [f"Prior question {i}" for i in range(turn)],
    }
    start = time.perf_counter()
    async with session.post(f"{base_url}/rag/generate-question", json=payload) as resp:
        resp.raise_for_status()
        await resp.read()
    return time.perf_counter() - start


async def _run_session(
    session: aiohttp.ClientSession,
    base_url: str,
    candidate_id: str,
    role: str,
    requests_per_session: int,
    latencies: List[float],
) -> None:
    await _build_index(session, base_url, candidate_id, role)
    for turn in range(requests_per_session):
        latencies.append(await _generate_question(session, base_url, candidate_id, role, turn))


async def _run_level(
    base_url: str, concurrency: int, requests_per_session: int, role: str
) -> None:
    latencies: List[float] = []
    timeout = aiohttp.ClientTimeout(total=120)
    connector = aiohttp.TCPConnector(limit=concurrency)
    wall_start = time.perf_counter()
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [
            _run_session(
                session,
                base_url,
                f"loadtest-{concurrency}-{i}",
                role,
                requests_per_session,
                latencies,
            )
            for i in range(concurrency)
        ]
        await asyncio.gather(*tasks)
    wall = time.perf_counter() - wall_start

    total = len(latencies)
    if not total:
        print(f"concurrency={concurrency}: no successful requests")
        return
    ordered = sorted(latencies)

    def pct(p: float) -> float:
        idx = min(len(ordered) - 1, int(round(p / 100 * (len(ordered) - 1))))
        return ordered[idx]

    print(
        f"concurrency={concurrency:>4}  "
        f"requests={total:>5}  "
        f"throughput={total / wall:8.1f} req/s  "
        f"p50={pct(50) * 1000:7.1f}ms  "
        f"p95={pct(95) * 1000:7.1f}ms  "
        f"p99={pct(99) * 1000:7.1f}ms  "
        f"mean={statistics.mean(ordered) * 1000:7.1f}ms"
    )


async def _main_async(args: argparse.Namespace) -> None:
    levels = [int(x) for x in args.concurrency.split(",") if x.strip()]
    base_url = args.base_url.rstrip("/")
    print(
        f"RAG load test → {base_url}  "
        f"(requests/session={args.requests_per_session}, role={args.role})\n"
        f"{'-' * 100}"
    )
    for level in levels:
        await _run_level(base_url, level, args.requests_per_session, args.role)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--concurrency",
        default="1,2,4,8,16",
        help="Comma-separated concurrent-session counts to sweep (e.g. 1,2,4,8,16,32)",
    )
    parser.add_argument(
        "--requests-per-session",
        type=int,
        default=10,
        help="generate-question calls each simulated session makes after building its index",
    )
    parser.add_argument("--role", default="backend_engineer", help="Role label passed to the API")
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
