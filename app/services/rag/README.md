# RAG Service (Module 14)

Retrieval-Augmented Generation for grounded interview question generation,
rubric-based answer scoring, near-duplicate ("copied answer") proctoring,
adaptive difficulty, per-company context, and grounded final reports.

Every LLM call is grounded in retrieved context (candidate resume/JD chunks, a
role reference Q&A bank, and optional per-company docs) so questions and scores
cite real evidence rather than model priors.

---

## Architecture (text diagram)

```
                         ┌──────────────────────────────────────────┐
   HTTP (FastAPI)        │            app/api/rag_routes.py          │
   /rag/*  ─────────────▶│  request schemas · track_endpoint metrics │
                         └───────────────────┬──────────────────────┘
                                             │ asyncio.to_thread
                                             ▼
                         ┌──────────────────────────────────────────┐
                         │        app/services/rag_service.py        │
                         │  RAGService (singleton, get_rag_service)  │
                         │  build_session_index · generate_question  │
                         │  evaluate_answer · detect_similarity      │
                         │  adjust_difficulty · add_company_docs     │
                         │  generate_report                          │
                         └───┬───────────┬───────────┬──────────┬────┘
                             │           │           │          │
              embedder.py ◀──┘           │           │          └──▶ llm_service.get_llm()
        (SentenceTransformer,            │           │                (multi-provider router)
         section chunking)               │           │
                                         ▼           ▼
                          faiss_store.py            audit_log.py
                     (VectorStore impl:          (retrieval trail →
                      IndexFlatL2 / IndexFlatIP)   MySQL/SQLite,
                             │                      PII-redacted)
                             ▼
                   rag_index/ on disk  ──────▶  metrics.py (Prometheus:
              (per-session / per-company /       retrieval_latency_seconds,
               _reference_bank / _answers /      retrieval_top_k_score,
               _canned / _company namespaces)    rag_endpoint_request_count)
```

Key seams:
- **`vector_store.py`** defines the `VectorStore` protocol (`add/search/save/load`)
  plus `Chunk` / `RetrievedChunk`. The service depends only on this protocol.
- **`faiss_store.py`** is the one concrete backend today.
- **`llm_service.get_llm()`** is injected — swap or stub it without touching RAG.

---

## FAISS indices: built, persisted, versioned

**Backends & metrics.** `FaissVectorStore` supports two index types:
- `IndexFlatL2` (default) — Euclidean distance for resume/JD/rubric retrieval.
- `IndexFlatIP` over L2-normalized vectors (`metric="cosine"`) — exact cosine
  similarity, used for near-duplicate answer detection where a true `>0.9`
  threshold is required.

Both are **exact/brute-force** — correct and fast up to ~100k vectors per store.
Beyond that (a large company doc corpus), switch `_make_index()` to `IndexIVFFlat`
with a trained coarse quantizer. `tests/test_rag_retrieval.py::test_flat_index_is_exact`
pins the exact-search assumption so a silent swap fails CI.

**Persistence.** Each store lives in its own directory under `RAG_INDEX_DIR`
(default `rag_index/`, `/data/rag_index` in the container) as two files:
- `index.faiss` — the serialized FAISS index
- `metadata.json` — `{dim, metric, model_name, extra:{seed_hash?}, chunks:[{chunk_id, source_text, source_type, metadata}]}`

Row *i* of the FAISS index aligns 1:1 with `chunks[i]`.

**Atomic, concurrency-safe writes.** `save()` writes each file to a sibling
temp path and `os.replace()`s it into place. Each rename is atomic, but the two
are separate calls, so a lock-free `load()` can momentarily catch the new index
beside the old metadata (or vice versa). `load()` closes that window by checking
the row-count invariant (`index.ntotal == len(chunks)`) and **retrying the read**
until the pair is consistent — a torn write is never returned to a caller. Beyond
that, writers that do a load-modify-save cycle (or a one-time cold build) serialize
through `namespace_lock(dir)`, a **process-safe** `filelock` that holds across
`gunicorn --workers N`, not just threads in one process. `load()` is also
corruption-tolerant: a genuinely broken/partial index logs a warning and rebuilds
empty rather than crashing.

**Namespaces** (directory = isolation boundary):

| Path under `RAG_INDEX_DIR`     | Contents                                  | Metric |
|--------------------------------|-------------------------------------------|--------|
| `<candidate_id>/`              | one session's resume chunks + JD          | l2     |
| `_reference_bank/`             | role Q&A bank (process-wide, built once)  | l2     |
| `_company/<company_id>/`       | per-company docs (feature 7)              | l2     |
| `_answers/<role>/`             | cross-session past answers (dup check)    | cosine |
| `_canned/`                     | canonical reference answers (dup check)   | cosine |

**Versioning & auto-rebuild.** Indices are content-derived: rebuild from the
source resume/JD/seed bank at any time — they are a cache, not a source of truth.
Two staleness guards are now automatic (no manual cache clearing required):

- **Seed changes.** `metadata.json` stores a `extra.seed_hash` (sha256 of
  `rag_reference_bank.json`). When `_reference_bank`/`_canned` load, a hash
  mismatch logs a warning and rebuilds from the current seed.
- **Embedding-model changes.** `metadata.json` stores `model_name`. On load, an
  index whose stored model differs from the configured `RAG_EMBEDDING_MODEL` is
  rejected (like a dimension mismatch) and rebuilt — so a *same-dimension* model
  swap can no longer silently load and return meaningless similarity scores.

There is no in-file schema version beyond these stamps. For a persistent volume,
a model or seed change is now self-healing on next use; you no longer need to
delete namespace dirs by hand.

**Persistence in prod.** Mount `RAG_INDEX_DIR` on a durable volume (PVC / EFS /
Filestore or an S3-backed CSI driver) — see `k8s/rag-deployment.yaml`. Never use
ephemeral pod storage: indices must survive restarts.

---

## Embedding throughput under concurrent load

Embedding is the CPU-bound hot path (`embedder.py`): a single process-wide
`SentenceTransformer`, invoked from request handlers via `asyncio.to_thread`.
Three mitigations keep it from serializing under concurrent sessions:

- **Query-embed cache.** `Embedder.embed_one()` is memoized with a bounded
  exact-match LRU (`_QUERY_CACHE_SIZE`, 1000 entries). Retrieval frequently
  re-embeds identical text — e.g. `detect_similarity` checks the same answer
  against both the past-answer and canned indices — and those repeats now skip
  the encode entirely. The cache is **per-`Embedder` instance**, so it can't leak
  across a `RAG_EMBEDDING_MODEL` change: a model swap builds a fresh `Embedder`
  (via the `get_embedder` singleton) with an empty cache, consistent with the
  index `model_name` versioning guard. Only exact string matches hit — there is
  no semantic caching. Batch `embed()` is **not** cached (session-init/doc-ingest
  batches are large and unique).

- **Bounded torch threads.** `torch.set_num_threads()` is capped at init to
  `min(4, os.cpu_count())` (override via `RAG_TORCH_NUM_THREADS`). Left at torch's
  default, *every* concurrent encode fans out across *every* core, so N concurrent
  requests oversubscribe the CPU and each runs slower. **Tradeoff:** a lower cap
  raises the latency ceiling of a single isolated encode (fewer cores per call)
  but substantially improves aggregate throughput when many sessions embed at
  once — the realistic production shape. Tune upward only if you run one session
  at a time on a many-core box.

- **Batch encoding at session init.** `build_session_index` embeds all resume +
  JD chunks in a single `encode(list_of_texts)` call, not a per-chunk loop —
  significantly cheaper per vector on both CPU and GPU. The `_canned`,
  `_reference_bank`, and company-doc builds batch the same way.

**Observability.** Two Prometheus metrics (in `app/core/metrics.py`, exposed on
the existing `/metrics` endpoint) make this visible in Grafana:
- `embedding_cache_events_total{result="hit|miss"}` — cache hit rate is
  `hit / (hit + miss)`.
- `embedding_duration_seconds{operation="embed_one|embed_batch"}` — encode
  wall-time (cache misses only).

**Measuring the saturation point.** `scripts/rag_load_test.py` simulates N
concurrent sessions hitting `/rag/generate-question` so the crossover point
(sessions before latency saturates) can be measured on the target host. See the
script header for usage. It is a manual tool — not wired into CI.

---

## Adding a new role's reference Q&A bank

The role bank is seeded from `app/data/rag_reference_bank.json`
(`RAG_SEED_DATA_PATH`). Structure:

```json
{
  "backend_engineer": [
    {
      "topic": "api_design",
      "question": "How do you design a paginated REST endpoint ...?",
      "reference_answer": "Prefer cursor/keyset pagination ...",
      "rubric": "10: cursor pagination, consistency ... 6: ... 3: ..."
    }
  ],
  "your_new_role": [ { "topic": "...", "question": "...", "reference_answer": "...", "rubric": "..." } ]
}
```

To add a role:
1. Add a top-level key (the role label used in API calls) with a list of entries.
   Each entry needs `topic`, `question`, `reference_answer`, `rubric`.
2. That's it — the change to the seed file changes its sha256, so the
   `_reference_bank` and `_canned` indices detect the mismatch on next use and
   rebuild automatically. (Manual `rm -rf` is no longer required; delete the dirs
   only if you want to force an immediate rebuild rather than a lazy one.)
3. `evaluate_answer`, `adjust_difficulty`, and `generate_report` retrieve
   role-matching rubric chunks automatically (they filter retrieved hits by
   `metadata.role == role`, falling back to cross-role hits when none match).

No code change is required to add a role.

---

## Swapping FAISS for pgvector / Qdrant later

The `VectorStore` protocol is the only contract the service depends on. To swap
backends, touch **3 files**:

1. **`app/services/rag/<new>_store.py`** (new) — implement a class with the four
   `VectorStore` methods (`add`, `search`, `save`, `load`) plus `__len__`,
   returning `RetrievedChunk` objects. This is where all backend-specific code lives.
2. **`app/services/rag_service.py`** — change the single factory `_new_store()`
   (one line) to construct the new backend. Nothing else in the service changes;
   all retrieval flows through `_new_store()` + `_retrieve()`.
3. **`requirements.txt`** — swap `faiss-cpu` for the new client
   (`pgvector`/`psycopg`, or `qdrant-client`).

Persistence semantics differ (a DB-backed store may make `save()`/`load()` no-ops
and persist on `add()`), but the service never assumes file layout — only the
protocol. Keep the namespace keys (session / `_company/<id>` / `_answers/<role>`)
as a table/collection discriminator so per-tenant isolation is preserved.

---

## Privacy & security

- **Per-session scope.** Resume/JD chunks live under `<candidate_id>/`; there is
  no cross-candidate read path (`generate_question` refuses an unindexed candidate).
- **Per-company isolation.** Company docs are keyed by `company_id` directory;
  `test_rag_privacy.py::test_company_namespaces_are_isolated` asserts one company's
  docs can never surface in another's retrieval.
- **PII-redacted audit.** `audit_log.py` stores a SHA-256 hash of the query
  (`sha256:<digest>:len=<n>`) and only `chunk_id` + scores — never raw resume text.
- **Retention.** Session and answer namespaces are safe to delete once an interview
  cycle ends; deleting the directory fully removes the embeddings. Wire this into
  your retention job against `RAG_INDEX_DIR`.

---

## Offline quality eval / CI gate

`app/services/rag/rag_eval.py` runs labeled cases through the real pipeline and
reports precision@k, groundedness (retrieved↔output keyword overlap), and
latency p50/p95/p99 to CSV + JSON, exiting non-zero on regression:

```bash
python -m app.services.rag.rag_eval --offline --out-dir reports/rag_eval
```

Use `--offline` in CI (deterministic stub LLM, no provider calls); drop it to
measure a real model's groundedness. Pass `--index-dir <tmp>` in CI so eval
indices never touch the real `RAG_INDEX_DIR`. Gates: `--min-precision`,
`--min-groundedness`, `--max-p95-latency`.

---

## Config (`app/core/config.py`)

| Setting               | Default                              | Purpose                          |
|-----------------------|--------------------------------------|----------------------------------|
| `RAG_INDEX_DIR`       | `rag_index`                          | Root for all index namespaces    |
| `RAG_EMBEDDING_MODEL` | `all-MiniLM-L6-v2`                   | SentenceTransformer model        |
| `RAG_TOP_K`           | `3`                                  | Default retrieval depth          |
| `RAG_SEED_DATA_PATH`  | `app/data/rag_reference_bank.json`   | Role reference Q&A bank          |
| `RAG_AUDIT_ENABLED`   | `True`                               | Toggle retrieval audit writes    |

## Tests

```bash
python -m pytest tests/test_rag_service.py tests/test_rag_retrieval.py tests/test_rag_privacy.py -q
```
