# Architecture

## Architecture and runtime flow

```text
Frontend (React/Vite) ─────────────┐
                                   ├──> FastAPI backend (app/main.py)
Streamlit UI (optional) ───────────┘            |
                                                |
                                                +--> Resume parser services
                                                +--> Question generator + LLM routing
                                                +--> TTS services
                                                +--> ASR services
                                                +--> Evaluator services
                                                +--> MySQL user/session/history storage
```

Typical flow:

1. Upload resume (`/parse-resume`).
2. Generate interview questions (`/generate-questions` or start interview endpoints).
3. Run interview with TTS + ASR support.
4. Evaluate answers (single or batch).
5. Persist final outcome to MySQL-backed history APIs and review it in the dashboard.

---

## Tech stack

## Production Microservices and Kubernetes

Production is now set up as a microservice-oriented deployment topology:

- `frontend` service for the React SPA
- `api` service for the FastAPI backend
- `nginx` edge gateway for routing
- `valkey` cache service
- `mysql` persistence service
- `mlflow` experiment tracking service
- `grafana loki` centralized log storage
- `promtail` log shipping agent
- `jaeger` distributed tracing backend
- `alertmanager` alert routing and notification hub
- `prometheus` monitoring service
- `grafana` dashboard service

Docker production files:

- `docker/backend.Dockerfile`
- `docker/frontend.Dockerfile`
- `docker/frontend-nginx.conf`
- `deploy/production/docker-compose.prod.yml`

Grafana Loki and Promtail are included for centralized log aggregation. That gives the stack a log pipeline that complements Prometheus metrics and Grafana dashboards, instead of relying only on raw container logs.

Argo CD is included as a GitOps entry point through a ready-to-apply application manifest under `deploy/argocd/`, so Kubernetes sync can be managed declaratively from the repo.

For AWS specifically, the repo also ships an EKS-ready overlay and ALB ingress annotations so the same application manifests can be deployed cleanly behind AWS-native ingress.

Jaeger and OpenTelemetry are included for distributed tracing, so request flow visibility is no longer limited to logs and metrics.

Alertmanager is included so Prometheus can route real alerts instead of only displaying raw timeseries data.

SonarQube support is included through `sonar-project.properties`, an optional local compose stack, and a CI quality-gate step when Sonar secrets are configured.

Kubernetes manifests live in:

- `k8s/`

Apply the base manifests with:

```bash
kubectl apply -k k8s
```

Important note:
The runtime topology is now split into deployable services, but the application logic itself is still one FastAPI backend codebase. That means this is a production microservice-style deployment architecture, not yet a full domain-level backend refactor into independently owned business microservices.
