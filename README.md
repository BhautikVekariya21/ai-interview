<div align="center">

# interviewer.ai

An end-to-end AI interview platform that parses resumes, generates role-aware questions, runs voice-enabled interview flows, evaluates answers, maps interview evidence back to the resume, and stores interview history — wrapped in a modern aurora-themed React frontend with a painterly hero, dedicated marketing pages, and a Forbes-style newsroom.

[![Python 3.14.3](https://img.shields.io/badge/Python-3.14.3-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Frontend-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-Bundler-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-UI-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![TanStack Query](https://img.shields.io/badge/TanStack%20Query-Data%20Fetching-FF4154?logo=reactquery&logoColor=white)](https://tanstack.com/query)
[![Streamlit](https://img.shields.io/badge/Streamlit-Optional%20UI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2?logo=mlflow&logoColor=white)](https://mlflow.org/)
[![DVC](https://img.shields.io/badge/DVC-Data%20Pipelines-945DD6?logo=dvc&logoColor=white)](https://dvc.org/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Valkey](https://img.shields.io/badge/Valkey-Cache-2A6DB0?logo=valkey&logoColor=white)](https://valkey.io/)
[![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Orchestration-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-EKS%20%2B%20ECR%20%2B%20S3-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Argo CD](https://img.shields.io/badge/Argo%20CD-GitOps-EF7B4D?logo=argo&logoColor=white)](https://argo-cd.readthedocs.io/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-Dashboards-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![Grafana Loki](https://img.shields.io/badge/Grafana%20Loki-Logs-F46800?logo=grafana&logoColor=white)](https://grafana.com/oss/loki/)
[![Jaeger](https://img.shields.io/badge/Jaeger-Tracing-66CFE3?logo=jaeger&logoColor=white)](https://www.jaegertracing.io/)
[![Trivy](https://img.shields.io/badge/Trivy-Security-1904DA?logo=aquasecurity&logoColor=white)](https://trivy.dev/)
[![CodeQL](https://img.shields.io/badge/CodeQL-Code%20Scanning-2088FF?logo=github&logoColor=white)](https://codeql.github.com/)
[![SonarQube](https://img.shields.io/badge/SonarQube-Quality-4E9BCD?logo=sonarqube&logoColor=white)](https://www.sonarsource.com/products/sonarqube/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)

</div>

---

## Screenshots

| Landing Page | Features Section | Free Plan / Forever Free |
|:---:|:---:|:---:|
| ![Landing Page](docs/screenshots/landing-page.png) | ![Features](docs/screenshots/features-section.png) | ![Free Plan](docs/screenshots/pricing-page.png) |

> **interviewer.ai** — a hyper-realistic AI mock-interview platform with resume parsing, speech confidence analytics, code complexity grading, and strict anti-cheat proctoring.

---

## Table of Contents

- [What is in this repo](#what-is-in-this-repo)
- [Feature modules](#feature-modules)
- [Coding practice & problem bank](#coding-practice--problem-bank)
- [AI Confidence Pulse & Resume Proof Map](#ai-confidence-pulse--resume-proof-map)
- [Post-Interview Growth Tools](#post-interview-growth-tools)
- [Company Lens and competitive practice](#company-lens-and-competitive-practice)
- [Architecture and runtime flow](#architecture-and-runtime-flow)
- [Tech stack](#tech-stack)
- [Local development](#local-development)
- [Docker compose](#docker-compose)
- [DevOps and CI/CD](#devops-and-cicd)
- [AWS Deployment](#aws-deployment)
- [Production Microservices and Kubernetes](#production-microservices-and-kubernetes)
- [Observability and SEO](#observability-and-seo)
- [Environment variables](#environment-variables)
- [API reference (implemented routes)](#api-reference-implemented-routes)
- [Frontend scripts](#frontend-scripts)
- [Testing](#testing)
- [Confidential data & security](#confidential-data--security)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)

---

## What is in this repo

This repository contains three runnable surfaces:

1. **FastAPI backend** (`app/`) — core APIs for parsing resumes, generating interview questions, auth/account management, ASR/TTS integrations, evaluation, code execution, RAG-grounded scoring, and MySQL-backed user data/history.
2. **React + TypeScript frontend** (`frontend/`) — the interviewer.ai web app: an aurora-themed landing page with a painterly hero, dedicated `/features` and `/how-it-works` marketing pages, a Forbes-style newsroom, a full-screen code sandbox with 15-language grading, and the upload-to-results interview UI including auth, account settings, history export, and the Resume Proof Map.
3. **Streamlit app** (`streamlit_app.py`) — optional Python-only UI for simpler workflows and demos.

Primary backend entry points:

- `app.main:app` for Uvicorn (`uvicorn app.main:app ...`)
- `app.py` for Hugging Face Spaces-style root launch
- `run.py` for an optional local launcher (supports `--ngrok`)

Secondary accelerator surfaces:

- **Rust** (`rust/ai_interview_accel/`) — optional native extension for resume-parsing hot paths (falls back to pure Python when absent).
- **MLflow** — experiment tracking for the NER training pipeline.
- **DVC** — reproducible data pipeline for model training.

---

## Feature modules

The backend is organized around ten practical modules, plus a set of newer product features layered on top of the core interview loop.

### Module 1 — Resume parsing

- Accepts PDF, DOCX, and TXT uploads.
- Extracts structured candidate information (skills, experience, projects, impact metrics).
- Exposes health and status metadata.

### Module 2 — Question generation

- Generates interview questions from parsed resume context.
- Supports interview session bootstrap endpoints.
- Supports follow-up question generation.
- RAG-grounded generation references real resume/JD context (see Module 10).

### Module 3 — Text-to-speech (TTS)

- Converts prompts/questions to audio.
- Supports provider fallback and cached generation.
- Includes specialized interview intro/outro, encouragement, and full-sequence endpoints.
- Multi-persona accents for the AI Panel Interview.

### Module 4 — Speech recognition (ASR)

- Primary path: browser transcript ingestion.
- Fallback path: backend audio transcription (Whisper, Deepgram, Vosk, etc.).
- Includes session lifecycle operations (start/upload/correct/re-record/submit).
- Frontend microphone capture is handled by a reusable `useAudioRecorder` hook (`frontend/src/hooks/useAudioRecorder.ts`) that tracks recording state, elapsed time, and live volume level.

### Module 5 — Answer evaluation

- Single-answer scoring endpoint.
- Batch evaluation endpoint for full interview summary.
- Rubric and health endpoints.
- Plagiarism / authenticity detection (`app/services/plagiarism_service.py`).

### Module 6 — Interview history and replay

- Persists completed interview summaries plus detailed evaluation payloads.
- Supports list, clear, export, and detail/review workflows in the frontend.

### Module 7 — Authentication and account management

- Cookie-backed and bearer-token-backed authentication.
- Sign up, sign in, Google/GitHub OAuth, profile updates, and account deletion.
- Forgot-password flow that emails a real reset link over SMTP; falls back to on-screen tokens in DEBUG when SMTP is not configured.
- MySQL-backed session snapshots and user-scoped history.

### Module 8 — Daily challenge

- **Daily Challenge** — a rotating practice prompt (DSA, system design, behavioral) to encourage regular use, with streak tracking.

### Module 9 — OpenTelemetry tracing

- Exports distributed traces through OpenTelemetry when enabled.
- Uses Jaeger as the standard open-source trace backend in the provided deployment stack.
- Falls back cleanly when tracing packages or exporters are not configured.

### Module 10 — Retrieval-Augmented Generation (RAG)

- Grounds every LLM call in retrieved context (candidate resume/JD chunks, a role reference Q&A bank, and optional per-company docs) so questions and scores cite real evidence rather than model priors.
- Powers grounded question generation, rubric-based answer scoring, near-duplicate ("copied answer") proctoring, adaptive difficulty, per-company context, and grounded final reports (`/rag/*` routes).
- FAISS-backed vector store (`app/services/rag/faiss_store.py`) with per-session, per-company, reference-bank, and answer namespaces persisted under `RAG_INDEX_DIR`.
- See `app/services/rag/README.md` for full architecture, namespaces, config, and the offline quality/CI eval gate.

### Module 11 — AI Panel Interview

- Simulates a multi-interviewer panel with distinct personas (`app/services/panel_service.py`, `/api/v1/panel` routes).
- `personas` lists the available interviewer personas; `react` returns per-persona reactions to an answer; `deliberate` produces a combined panel deliberation/verdict.
- Pairs with multi-persona TTS accents so each panelist has a distinct voice.

### Module 12 — Company Lens exams

- Create company- and role-specific exams from resume and job-description context.
- Publish candidate-facing exams through share tokens and collect attempts with stored scorecards.

### Module 13 — Evidence coaching

- Compare interview evidence with resume claims and produce targeted gap reports.
- Generate between-question coaching tips through `/api/v1/evidence`.

### Module 14 — Gauntlet and league practice

- Run multi-persona interview gauntlets with configurable challenge prompts.
- Track ratings and leaderboards through the `/league` routes.

### Module 15 — Replay and Game Tape

- Build shareable interview replays with question, answer, score, and coaching events.
- Persist replay artifacts and render a timeline-based review experience.

---

## Coding practice & problem bank

The platform ships a rich coding-practice catalogue in the full-screen code sandbox (`/coding`):

- **Curated set** — hand-written LeetCode-style problems with multi-language starters (Python, JavaScript, Rust, SQL, and more).
- **SQL database problems** — schema + seeded tables graded by running the candidate's query against an in-memory SQLite database.
- **Imported CodeContests corpus** — ~7,600 whole-program problems sourced from DeepMind CodeContests (CodeChef, Codeforces, AtCoder, HackerEarth, Aizu). These are stdin/stdout problems graded against hidden judge suites.
- **Server-side catalogue** — search, difficulty/topic/source filters, and paging via `/coding/problems/catalog`.

**Languages supported for grading:** Python 3, JavaScript, TypeScript, Java, C++, C#, Go, Rust, Ruby, PHP, Swift, Objective-C, Erlang, Haskell, and SQL.

**Anti-cheat in the sandbox:** screen recording, tab-switch detection, focus-loss proctoring, and clipboard lockdown.

> **Note on problem counts:** the raw `data/code_contests_raw.jsonl` corpus contains 13,505 records, but the import pipeline deliberately filters it to the ~7,600 problems that are actually gradeable and readable (dropped: statements with missing figures `<image>`, multiple-answer/interactive problems, slug-only titles, and true duplicates). See `scripts/build_code_contests_problems.py` for the exact filters.

---

## AI Confidence Pulse & Resume Proof Map

Two of the most differentiated features in the product — both live entirely in the frontend, layered on top of existing ASR/evaluation data with no new backend dependency required to demo them.

### AI Confidence Pulse (`frontend/src/components/ConfidencePulse.tsx`)

A real-time communication-quality readout that runs alongside the voice interview, not just a post-hoc score:

- **Filler-word detection** — flags "um", "uh", "like", "you know" style filler patterns as the candidate speaks (backed by `app/services/filler_word_detector.py`).
- **Words-per-minute (WPM) pacing** — a live `WpmPanel` (`frontend/src/components/WpmPanel.tsx`) shows whether the candidate is speaking too fast, too slow, or in a comfortable range.
- **Confidence trend line** — an animated pulse visualization so the candidate can see confidence rise/fall across the interview instead of one aggregate number.
- Surfaces in both the live interview screen and post-interview results/history review.

**Why it matters:** most mock-interview tools only grade *content*. This grades *delivery* — the thing that actually tanks real interviews even when the answer is technically correct.

### Resume Proof Map (`frontend/src/components/ResumeProofMap.tsx`)

Cross-references claims made on the uploaded resume against what the candidate actually said during the interview:

- Extracts claim-worthy statements from the parsed resume (skills, projects, impact metrics).
- Matches each claim against interview transcript evidence collected during the session.
- Visually flags claims that were **substantiated** vs. **unsubstantiated**.
- Pairs with `app/services/plagiarism_service.py` for a fuller resume-vs-reality picture.

**Why it matters:** it turns the interview from "did they answer this question well" into "does the resume hold up under actual questioning."

Both features are pure frontend consumers of existing evaluation/ASR data — they light up automatically once the frontend runs against a backend with ASR/evaluation configured.

---

## Post-Interview Growth Tools

Three candidate-facing features, all shipped in the frontend on top of data the app already collects — no new provider keys required.

### PDF scorecard export (`frontend/src/components/ResultsPage.tsx`)

- A "Download PDF Scorecard" button renders the candidate's overall score, grade, category breakdown, authenticity coaching, and full per-question feedback into a polished, shareable PDF (via `jspdf`).
- Sits alongside the existing Markdown export.

### Interview readiness score & practice streak (`frontend/src/components/AnalyticsDashboard.tsx`)

- A single rolling 0–100 "Interview Readiness Score" widget blending recent interview performance and consistency.
- Pairs with a daily-challenge practice streak to encourage the daily-practice habit.

### Company Lens, Gauntlet, and Replay tools

- **Company Lens** (`/exams`, `/lens/:token`) turns a role brief into a structured exam with a shareable candidate link.
- **Gauntlet Meter** and panel personas add pressure-tested, multi-round practice.
- **Game Tape / Replay Timeline** (`/replay`) reviews questions, answers, scoring, and coaching moments.
- **Gap Report** and **Coach Whisper** surface actionable improvements from resume-vs-interview evidence.
- **League Leaderboard** adds ratings and competitive progress tracking.

---

## Architecture and runtime flow

```text
Frontend (React/Vite) ─────────────┐
                                   ├──> FastAPI backend (app/main.py)
Streamlit UI (optional) ───────────┘            |
                                                 |
                                                 +--> Resume parser services
                                                 +--> Question generator + LLM routing
                                                 +--> RAG / FAISS retrieval
                                                 +--> TTS services
                                                 +--> ASR services
                                                 +--> Code execution sandbox
                                                 +--> Evaluator services
                                                 +--> MySQL user/session/history storage
```

Typical flow:

1. Upload resume (`/parse-resume`).
2. Generate interview questions (`/generate-questions` or RAG-grounded `/rag/generate-question`).
3. Run interview with TTS + ASR support, with live Confidence Pulse feedback.
4. For coding rounds, open `/coding` in the sandbox — run and submit against the hidden judge suites.
5. Evaluate answers (single or batch) with RAG-grounded scoring.
6. Persist final outcome to MySQL-backed history APIs; review it in the dashboard, including the Resume Proof Map.

---

## Tech stack

### Backend

- Python 3.14.3
- FastAPI + Uvicorn
- Pydantic + pydantic-settings
- MySQL for user, session, history, and account state
- Loguru
- MLflow experiment tracking for NER training
- DVC pipeline orchestration for reproducible model runs
- FAISS for RAG vector retrieval
- Optional Rust accelerator for preprocessing hot paths

### Frontend

- React 18 + TypeScript
- Vite
- Tailwind CSS + Radix UI ecosystem
- React Router
- TanStack Query
- Framer Motion (with `LazyMotion`/`m` and `MotionConfig` for reduced-motion support)

### Product highlights in the current UI

- Aurora design system (deep slate-indigo palette, glass surfaces, SF Pro typography) with a painterly CSS-only hero background
- Dedicated `/features` and `/how-it-works` marketing pages
- Forbes-style newsroom
- Resume-tailored question generation
- Voice interview flow with TTS/ASR fallback
- AI Confidence Pulse live communication analytics
- Resume Proof Map for validating resume claims against interview evidence
- RAG-grounded question generation and answer scoring
- Full-screen code sandbox with 15-language grading, SQL problems, and a server-side catalogue of ~7,600 problems
- Daily Challenge practice streak
- History export in JSON, Markdown, and PDF
- Account settings, email-based password reset, and account deletion
- Clerk-hosted authentication with Google/GitHub sign-in, email sign-up, and Clerk-managed email verification
- Company Lens exams, share links, candidate scorecards, replay timelines, gauntlet practice, and league rankings

### Optional AI/Provider integrations

- **LLM providers:** xAI, Claude, AIMLAPI, Mistral, OpenRouter, Gemini, Groq, Hugging Face
- **ASR providers:** OpenAI Whisper API, Deepgram, Google, Vosk, local Whisper route
- **TTS providers:** ElevenLabs, gTTS, offline fallback
- **Code execution:** Docker sandbox, subprocess (rlimit-confined), Judge0, Piston

> You can run the app with partial provider configuration; unavailable providers are skipped/fallback logic applies.

---

## Local development

### Prerequisites

- Python 3.14.3
- Node.js 18+ (Node 20 recommended)
- npm

### 1) Clone and set up Python environment

> This repository is private. Cloning requires GitHub access (SSH key or a PAT with `repo` scope).

```bash
git clone <repo-url> ai-interview
cd ai-interview
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2) Set up environment variables

```bash
# Create your local environment file. NEVER commit real secrets.
cp .env.example .env
# Then edit .env with your real keys (LLM providers, DB, etc.)
```

The `.env` file is git-ignored. See [Environment variables](#environment-variables) for the full list.

### 3) Run backend (FastAPI)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend URLs:

- API root: `http://localhost:8000/`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

### 4) Run frontend (Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

### 5) Optional Streamlit interface

```bash
streamlit run streamlit_app.py
```

### 6) Optional launcher with ngrok helper

```bash
python run.py
# or
python run.py --ngrok
```

### 7) Reproducible NER training with DVC + MLflow

```bash
dvc repro train_ner
```

This stage reads `params.yaml`, writes the trained model to `saved_models/ner_bilstm_crf/`, and stores run metrics in `reports/ner_training_metrics.json`.

To enable MLflow tracking locally:

```bash
MLFLOW_ENABLED=true
MLFLOW_TRACKING_URI=file:./mlruns
MLFLOW_EXPERIMENT_NAME=resume-ner
```

### 8) Optional Rust acceleration

```bash
make build-rust-accel
```

The extension source lives in `rust/ai_interview_accel/` and is loaded automatically when available. The pure-Python implementation remains the fallback.

### 9) (Optional) Rebuild the CodeContests import

The committed artefact `app/services/code_contests_problems.py` is generated from the raw corpus. To regenerate it:

```bash
python scripts/fetch_code_contests.py   # ~35 min; downloads the 490 MB corpus
python scripts/build_code_contests_problems.py
```

---

## Docker compose

Run app + MySQL + Valkey using the provided compose file:

```bash
docker-compose up --build
```

Default mapped ports:

- Backend: `http://localhost:8000` (container internal port `7860`)
- Valkey: `localhost:6379`
- MySQL: `localhost:3306`

Stop:

```bash
docker-compose down
```

The production container builds the React frontend inside the Docker image and serves the compiled assets from FastAPI, so the backend image is self-contained for deployment.

---

## DevOps and CI/CD

This repository includes a practical baseline CI/CD setup. There is **no Dependabot and no repo-automation bot layer** — those were removed after bot-authored PRs/commits caused problems on this project, so all dependency and workflow changes are made and reviewed by hand.

- GitHub Actions CI at `.github/workflows/ci.yml`
- GitHub Actions CD at `.github/workflows/cd.yml`
- Release drafting, infrastructure checks, repo hygiene workflows (labeler, stale, greetings)
- CodeQL, dependency review/audit, hadolint, gitleaks, OpenSSF Scorecards
- GitHub Pages frontend deploy
- Optional AWS EKS deployment automation
- MLflow tracking server, production Dockerfiles, and production compose stack

### CI pipeline

The CI workflow runs:

- Backend pytest suite with Valkey-compatible cache and MySQL service containers
- Frontend lint, tests, and production build
- Lightweight NER training smoke test with MLflow file-backed tracking
- Docker image build validation
- `docker compose config` sanity checks

The infrastructure workflow adds Terraform fmt/init/validate, `kubeconform`, and `Checkov` checks.

### CD pipeline

The CD workflow:

1. Builds and pushes separate backend and frontend images to GitHub Container Registry (`ghcr.io`)
2. Tags them with `latest` and the commit SHA
3. Publishes build provenance and SBOM metadata
4. Optionally deploys to a remote Docker host over SSH
5. Optionally deploys to AWS EKS
6. Runs post-deploy smoke checks when health-check URLs are configured

### Required GitHub secrets for deployment

```bash
DEPLOY_HOST=
DEPLOY_USER=
DEPLOY_SSH_KEY=
```

For the optional AWS deployment job:

```bash
AWS_ROLE_TO_ASSUME=
AWS_REGION=
AWS_ACCOUNT_ID=
EKS_CLUSTER_NAME=
ECR_REPOSITORY_PREFIX=ai-interview-prod
```

---

## AWS Deployment

AWS is a first-class deployment target in this repo.

Included AWS deployment assets:

- Terraform for VPC, EKS, ECR, S3, EFS, and CloudWatch under `deploy/aws/terraform/`
- An EKS deploy script under `deploy/aws/scripts/deploy-eks.sh`
- An AWS-specific Kubernetes overlay under `k8s/overlays/aws/`
- An Argo CD application for the AWS overlay

Planned AWS service mapping:

- `Amazon EKS`, `Amazon ECR`, `Amazon S3`, `Amazon EFS`, `Amazon CloudWatch`, `Amazon ElastiCache for Valkey`, `Amazon RDS for PostgreSQL`, `Amazon OpenSearch Service`, `Amazon SQS`, `Amazon SNS`, `Amazon EventBridge`, `AWS Glue`, `Amazon Athena`, `AWS KMS`, `AWS Secrets Manager`, `AWS Certificate Manager (ACM)`, `Amazon Route53`, `AWS Load Balancer Controller`

Bootstrap flow:

```bash
cd deploy/aws/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Then deploy the app to EKS:

```bash
AWS_REGION=ap-south-1 AWS_ACCOUNT_ID=123456789012 EKS_CLUSTER_NAME=ai-interview-eks IMAGE_TAG=latest deploy/aws/scripts/deploy-eks.sh
```

Before applying the AWS overlay, replace placeholder values like the IRSA role ARN and hostname in `k8s/overlays/aws/backend-serviceaccount.yaml` and `k8s/overlays/aws/ingress-aws-alb.yaml`.

---

## Production Microservices and Kubernetes

Production is set up as a microservice-oriented deployment topology:

- `frontend` service for the React SPA
- `api` service for the FastAPI backend
- `nginx` edge gateway for routing
- `valkey` cache service
- `grafana loki` centralized log storage
- `promtail` log shipping agent
- `jaeger` distributed tracing backend
- `alertmanager` alert routing and notification hub
- `prometheus` monitoring service
- `grafana` dashboard service

Apply the base manifests with:

```bash
kubectl apply -k k8s
```

> **Note:** the runtime topology is split into deployable services, but the application logic itself is still one FastAPI backend codebase — a production microservice-*style* deployment, not yet a full domain-level backend refactor.

### Helpful local ops commands

```bash
make lint-backend
make format-backend
make security-backend
make precommit
make build-rust-accel
make test-backend
make train-ner-smoke
make test-frontend
make lint-frontend
make build-frontend
make docker-build
make compose-config
make dev-up
make dev-down
make mlflow-up
make mlflow-down
make tf-fmt
make tf-validate
```

---

## Observability and SEO

The production deployment includes:

- `nginx` as the public reverse proxy
- `prometheus` for application metrics scraping
- `grafana` with a provisioned Prometheus datasource
- `grafana loki` for centralized logs
- `promtail` for log collection
- `jaeger` for distributed tracing
- `alertmanager` for alert routing
- `trivy` in CI for vulnerability scanning
- `sonarqube` support for code-quality gates
- a FastAPI `/metrics` endpoint for Prometheus scraping

Default production ports: Nginx `80`, Loki `3100`, Promtail `9080`, Alertmanager `9093`, Jaeger UI `16686`, Jaeger OTLP gRPC `4317`, Prometheus `9090`, Grafana `3000`.

SEO improvements included: canonical URL tags, Open Graph and Twitter metadata, `robots.txt` sitemap reference, and `sitemap.xml`.

> Before production launch, replace placeholder URLs like `https://interviewer.ai/` with your real domain.

---

## Environment variables

Create a `.env` file in the repository root (or export in your shell). The `.env` file and every `.env.*` variant (except `.env.example`) are git-ignored — **never commit real secrets**.

### Core app settings

```bash
APP_NAME="AI Interview System"
APP_VERSION="2.0.0"
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### LLM provider keys (set whichever providers you use)

```bash
XAI_API_KEY=
CLAUDE_API_KEY=
AIML_API_KEY=
MISTRAL_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
HUGGINGFACE_API_KEY=
```

### TTS settings

```bash
ELEVENLABS_API_KEY=
TTS_PROVIDER=gtts
TTS_LANGUAGE=en
TTS_CACHE_ENABLED=true
TTS_CACHE_DIR=audio_cache
```

### ASR settings

```bash
OPENAI_API_KEY=
DEEPGRAM_API_KEY=
ASSEMBLYAI_API_KEY=
ASR_PROVIDER=
ASR_STREAM_ENABLED=true
WHISPER_MODEL_SIZE=tiny
```

### Cache / Valkey

```bash
CACHE_ENABLED=true
CACHE_DEFAULT_TTL_SECONDS=3600
VALKEY_URL=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/0
```

### MySQL persistence

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=change-me-in-prod
MYSQL_DATABASE=ai_interview
```

### Auth / session settings

```bash
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=30
FRONTEND_BASE_URL=http://localhost:5173
```

### Email (SMTP) for password reset

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=          # for Gmail, use an App Password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=
SMTP_FROM_NAME="AI Interview"
```

Leave these blank to skip real email sending — in DEBUG mode the reset link is returned in the API response instead.

### Code execution sandbox

```bash
CODE_EXEC_BACKENDS=docker,subprocess,judge0,piston
JUDGE0_URL=https://ce.judge0.com
JUDGE0_TIMEOUT_SECONDS=20
PISTON_TIMEOUT_SECONDS=20
CODE_EXEC_RATELIMIT_PER_MINUTE=30
```

> **Production warning:** do not ship the public Judge0 instance — candidate code would leave your machine on a shared rate limit. Self-host it or set `JUDGE0_URL=` to disable.

### Frontend config

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=
```

Clerk email verification, social providers, bot protection, and email delivery are configured in the Clerk Dashboard. The hosted React `<SignUp />` and `<SignIn />` components handle the authentication flow and redirect to `/app` after sign-in. Never place Clerk secret keys in frontend environment variables.

---

## API reference (implemented routes)

> Prefixes below are exactly as defined in backend route files. For request/response schemas, use the live docs at `/docs`.

### Root + app-level health

| Method | Path      | Purpose                            |
| ------ | --------- | ----------------------------------- |
| GET    | `/`       | Root service info                  |
| GET    | `/health` | App-level health and module status |
| GET    | `/status` | Core status                        |
| GET    | `/tracing/status` | OpenTelemetry tracing status |

### Core interview routes

| Method | Path                      |
| ------ | ------------------------- |
| POST   | `/parse-resume`           |
| POST   | `/generate-questions`     |
| POST   | `/questions/generate`     |
| POST   | `/start-interview`        |
| POST   | `/start-interview-stream` |
| POST   | `/follow-up-question`     |
| POST   | `/tts`                    |
| GET    | `/supported-skills`       |
| GET    | `/ner-tags`               |
| GET    | `/llm-status`             |

### Coding routes (`/coding`)

| Method | Path                     | Purpose |
| ------ | ------------------------ | ------- |
| GET    | `/coding/problems`       | Default practice list (metadata) |
| GET    | `/coding/problems/{id}`  | Problem detail & starter code |
| GET    | `/coding/problems/catalog` | Searchable/paged catalogue |
| POST   | `/coding/run`            | Run sample tests (no history) |
| POST   | `/coding/submit`         | Submit for grading + AI analysis |

### TTS routes (`/tts`)

| Method | Path                                    |
| ------ | ---------------------------------------- |
| POST   | `/speak`                                |
| GET    | `/speak`                                |
| POST   | `/stream`                               |
| POST   | `/interview/question/{question_number}` |
| POST   | `/interview/full-sequence`              |
| GET    | `/voices`                               |
| GET    | `/voices/presets`                       |
| POST   | `/voices/preview/{voice_id}`            |
| POST   | `/detect-language`                      |
| GET    | `/config` / `/usage` / `/stats` / `/cache/status` |
| DELETE | `/cache/clear`                          |
| GET    | `/health`                               |
| POST   | `/interview/intro` / `/intro/with-resume` / `/outro` / `/outro/with-evaluation` / `/encouragement` / `/followup-intro` |
| GET    | `/interview/script-status`              |

### ASR routes (`/asr`)

| Method | Path                                         |
| ------ | --------------------------------------------- |
| POST   | `/transcript`                                |
| POST   | `/browser-transcript`                        |
| POST   | `/transcribe`                                |
| POST   | `/transcribe-simple`                         |
| POST   | `/session/upload` / `/start` / `/correct` / `/re-record` / `/submit` |
| GET    | `/session/{session_id}/{question_id}/status` |
| GET    | `/session/{session_id}/all-answers`          |
| POST   | `/analyze-fillers`                           |
| GET    | `/config` / `/stats` / `/providers` / `/health` / `/recordings` |

### Evaluation routes (`/evaluation`)

| Method | Path               |
| ------ | ------------------ |
| POST   | `/evaluate`        |
| POST   | `/evaluate-batch`  |
| POST   | `/evaluate-simple` |
| GET    | `/rubric`          |
| GET    | `/health`          |

### Auth routes (`/auth`)

| Method | Path               |
| ------ | ------------------ |
| GET    | `/health`          |
| POST   | `/signup`          |
| POST   | `/login`           |
| GET    | `/me`              |
| PATCH  | `/profile`         |
| DELETE | `/account`         |
| POST   | `/logout`          |
| POST   | `/forgot-password` |
| POST   | `/reset-password`  |
| POST   | `/oauth/{provider}` |

### History routes (`/history`)

| Method | Path |
| ------ | ---- |
| POST   | `/`  |
| GET    | `/`  |
| DELETE | `/`  |

### User data routes (`/user-data`)

| Method | Path       |
| ------ | ---------- |
| GET    | `/health`  |
| GET    | `/session` |
| PUT    | `/session` |

### RAG routes (`/rag`)

| Method | Path                  |
| ------ | --------------------- |
| POST   | `/build-index`        |
| POST   | `/generate-question`  |
| POST   | `/evaluate-answer`    |
| POST   | `/detect-similarity`  |
| POST   | `/adjust-difficulty`  |
| POST   | `/company-context`    |
| POST   | `/generate-report`    |
| GET    | `/health`             |

### AI Panel routes (`/api/v1/panel`)

| Method | Path          |
| ------ | ------------- |
| GET    | `/personas`   |
| POST   | `/react`      |
| POST   | `/deliberate` |

### Confidence routes (`/confidence`)

| Method | Path       |
| ------ | ---------- |
| POST   | `/analyze` |
| POST   | `/heatmap` |
| GET    | `/health`  |

### Blog routes (`/blog`)

| Method | Path                        |
| ------ | --------------------------- |
| GET    | `/posts`                    |
| POST   | `/posts`                    |
| GET    | `/posts/{post_id}`          |
| GET    | `/posts/{post_id}/feedback` |
| POST   | `/posts/{post_id}/feedback` |
| POST   | `/subscribe`                |

### Review routes (`/reviews`)

| Method | Path |
| ------ | ---- |
| GET    | `/`  |
| POST   | `/`  |

Other feature routers: contact form submissions (`/contact`). See `/docs` for the full, live route list per router.

---

## Frontend scripts

From `frontend/`:

```bash
npm run dev           # start Vite dev server
npm run build         # verify API client + production build
npm run build:dev     # development-mode build
npm run lint          # ESLint
npm run test          # Vitest (run once)
npm run test:watch    # Vitest watch mode
```

---

## Testing

Backend:

```bash
make lint-backend
make security-backend   # high-severity Bandit findings
pytest
```

Pre-commit hooks:

```bash
pre-commit install
make precommit
```

NER training pipeline:

```bash
dvc repro train_ner
cat reports/ner_training_metrics.json
```

Frontend:

```bash
cd frontend
npm test
```

---

## Confidential data & security

This project handles candidate résumés, interview transcripts, recordings, and provider credentials. Follow these rules — they are also encoded in `.gitignore`:

**Never commit:**
- `.env`, `.env.*` (except `.env.example`) — all API keys, DB passwords, JWT secrets
- `scratch/coding_practice/` — candidate practice sessions
- `*.pem`, `*.key`, `*.p12`, `*.pfx` — key material
- `credentials.json`, `service-account.json`, `google-credentials.json` — service accounts
- `proctor_recordings/`, `recordings/`, `uploads/`, `audio_cache/`, `rag_index/` — user-generated and runtime data
- `data/code_contests_raw.jsonl` — 490 MB raw download, re-creatable via script
- Any `.jwt`, `.token`, `.auth`, `.credential` files

**Before committing, always run:**
```bash
git status                    # confirm no unexpected files are staged
git diff --cached --stat      # review exactly what will be committed
```

**Gitleaks is enforced in CI** (`.github/workflows/gitleaks.yml`) and will fail the pipeline on committed secrets. If you ever commit a real secret, rotate it and rewrite history (`git filter-repo` / `BFG`) — do not just delete the file.

---

## Troubleshooting

### `ModuleNotFoundError: torch`

PyTorch wheels may lag on the newest CPython versions. The backend starts in a degraded mode when PyTorch-backed parser dependencies are unavailable, but resume parsing endpoints will return `503` until PyTorch support is present.

If a compatible wheel exists for your platform and Python runtime, install it manually:

```bash
pip install torch
```

### Frontend cannot reach backend or auth does not persist

- Confirm backend is running on `http://localhost:8000`.
- Verify frontend env/config points to the same base URL.
- Confirm `FRONTEND_BASE_URL` and CORS origins are aligned with the frontend origin.
- Check browser console/network tab for CORS or 4xx/5xx errors.

### TTS/ASR provider failures

- Verify provider API keys are set.
- Use `/tts/health` and `/asr/health` for diagnostics.
- Inspect `/asr/providers` and `/llm-status` to verify active providers.

### Code execution reports "no sandbox backend"

- Confirm `CODE_EXEC_BACKENDS` includes at least one reachable backend.
- Docker sandbox needs the Docker socket; `subprocess` needs the language toolchain installed on the host.
- `judge0` / `piston` need their URLs reachable and (for Judge0) not rate-limited.

### "Sandbox unavailable" when grading a language

Compiled languages on `stdio` problems require a local toolchain (or a self-hosted Judge0/Piston). See the `CODE_EXEC_BACKENDS` comment in `.env.example`.

---

## Project structure

```text
.
├── app/
│   ├── api/                 # FastAPI routers (core + auth + coding + ASR/TTS/evaluation/history/RAG)
│   ├── core/                # settings, DB, exceptions
│   ├── models/              # Pydantic + DB models
│   ├── schemas/             # schema modules
│   ├── services/            # parser, LLM, ASR, TTS, evaluator, code executor, RAG, problem bank
│   │   ├── coding_problems_data.py       # 1000-problem generated bank
│   │   ├── coding_sql_problems_data.py   # SQL coverage layer (ids 1001+)
│   │   ├── code_contests_problems.py     # imported CodeContests corpus (~7,600; generated)
│   │   └── rag/             # FAISS store, embedder, retrieval
│   ├── prompts/             # prompt templates
│   ├── ml/                  # ML helper/training code
│   ├── static/              # static assets
│   └── main.py              # FastAPI app entry
├── frontend/                # React + TypeScript app (sandbox, dashboard, auth, account, results, analytics)
├── tests/                   # pytest suite
├── scripts/                 # data pipelines (fetch/build CodeContests, NER, authored statements)
├── data/                    # raw datasets (git-ignored)
├── deploy/aws/              # AWS Terraform + EKS deployment automation
├── k8s/                     # Kubernetes manifests + overlays
├── docker/                  # production Dockerfiles + observability configs
├── rust/ai_interview_accel/ # optional Rust accelerator
├── app.py                   # HF Spaces-friendly entry point
├── run.py                   # optional local launcher
├── streamlit_app.py         # optional Streamlit app
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
