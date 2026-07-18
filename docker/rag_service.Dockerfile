# Multi-stage build for the RAG service (Module 14).
# Mirrors docker/backend.Dockerfile's base image + app layout, but adds a
# builder stage (wheels compiled once, copied into a slim runtime) and a
# non-root user, per the microservice deployment convention.

# ── Stage 1: builder — compile dependency wheels ────────────────────────────
FROM python:3.14.3-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Build deps for faiss / sentence-transformers native wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ── Stage 2: runtime — slim image, non-root ─────────────────────────────────
FROM python:3.14.3-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2 \
    RAG_INDEX_DIR=/data/rag_index

WORKDIR /app

# Install pre-built wheels only — no compiler in the runtime image.
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY app ./app

# Non-root user; /data is the mount point for the persistent FAISS volume
# (item 11: indices must survive pod restarts — see the PVC/S3 note in the
# deployment manifests, not ephemeral pod storage).
RUN useradd --create-home --uid 10001 raguser \
    && mkdir -p /data/rag_index \
    && chown -R raguser:raguser /app /data
USER raguser

VOLUME ["/data"]
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/rag/health', timeout=5)" || exit 1

# Single worker: FAISS indices are in-process and per-pod; scale horizontally
# with more replicas sharing the mounted /data volume, not with --workers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info", "--access-log"]
