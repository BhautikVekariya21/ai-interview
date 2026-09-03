from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

# ─────────────────────────────── RAG metrics ────────────────────────────────
# Exposed via the existing /metrics endpoint, so they surface in the current
# Grafana dashboards without new scrape config.

RETRIEVAL_LATENCY_SECONDS = Histogram(
    "retrieval_latency_seconds",
    "FAISS retrieval latency in seconds",
    ["operation"],  # e.g. generate_question, evaluate_answer, detect_similarity
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)
RETRIEVAL_TOP_K_SCORE = Histogram(
    "retrieval_top_k_score",
    "Similarity score of the top retrieved chunk (0-1)",
    ["operation"],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0),
)
RAG_ENDPOINT_REQUEST_COUNT = Counter(
    "rag_endpoint_request_count",
    "RAG endpoint invocations",
    ["endpoint", "status"],  # status: success | error
)

# Embedding is the CPU-bound hot path under concurrent load. These make the
# query-embed cache and per-call encode cost visible in Grafana.
EMBEDDING_DURATION_SECONDS = Histogram(
    "embedding_duration_seconds",
    "Wall-clock seconds spent in a model encode() call (cache misses only)",
    ["operation"],  # embed_one | embed_batch
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
EMBEDDING_CACHE_EVENTS = Counter(
    "embedding_cache_events_total",
    "Query-embedding cache lookups by result (hit rate = hit / (hit + miss))",
    ["result"],  # hit | miss
)


