# AI Interview System

An end-to-end interview platform that parses resumes, generates role-aware questions, runs voice-enabled interview flows, evaluates answers, maps interview evidence back to the resume, and stores interview history.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14.3](https://img.shields.io/badge/Python-3.14.3-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/React-Vite-61DAFB?logo=react)](https://vitejs.dev/)
[![AWS](https://img.shields.io/badge/AWS-EKS%20%2B%20ECR%20%2B%20S3-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Grafana Loki](https://img.shields.io/badge/Grafana%20Loki-Logs-F46800?logo=grafana&logoColor=white)](https://grafana.com/oss/loki/)
[![Trivy](https://img.shields.io/badge/Trivy-Security-1904DA?logo=aquasecurity&logoColor=white)](https://trivy.dev/)
[![Argo%20CD](https://img.shields.io/badge/Argo%20CD-GitOps-EF7B4D?logo=argo&logoColor=white)](https://argo-cd.readthedocs.io/)
[![Jaeger](https://img.shields.io/badge/Jaeger-Tracing-66CFE3?logo=jaeger&logoColor=white)](https://www.jaegertracing.io/)
[![Alertmanager](https://img.shields.io/badge/Alertmanager-Alerts-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/docs/alerting/latest/alertmanager/)
[![SonarQube](https://img.shields.io/badge/SonarQube-Quality-4E9BCD?logo=sonarqube&logoColor=white)](https://www.sonarsource.com/products/sonarqube/)

</div>

---

## What is in this repo

This repository contains three runnable surfaces:

1. **FastAPI backend** (`app/`) — core APIs for parsing resumes, generating interview questions, auth/account management, ASR/TTS integrations, evaluation, and MySQL-backed user data/history.
2. **React + TypeScript frontend** (`frontend/`) — upload-to-results interview UI, including auth, billing, account settings, history export, and the Resume Proof Map.
3. **Streamlit app** (`streamlit_app.py`) — optional Python-only UI for simpler workflows and demos.

Primary backend entry points:

- `app.main:app` for Uvicorn (`uvicorn app.main:app ...`)
- `app.py` for Hugging Face Spaces-style root launch
- `run.py` for an optional local launcher (supports `--ngrok`)

---

## Feature modules

The backend is organized around nine practical modules:
