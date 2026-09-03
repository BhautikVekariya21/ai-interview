PYTHON ?= python
VENV_PYTHON ?= .venv/Scripts/python.exe
FRONTEND_DIR ?= frontend
COMPOSE ?= docker compose

.PHONY: test-backend test-frontend lint-backend format-backend security-backend precommit build-rust-accel lint-frontend build-frontend compose-config docker-build dev-up dev-down train-ner-smoke mlflow-up mlflow-down tf-fmt tf-validate

test-backend:
	$(VENV_PYTHON) -m pytest

lint-backend:
	$(VENV_PYTHON) -m ruff check app tests

format-backend:
	$(VENV_PYTHON) -m ruff format app tests

security-backend:
	$(VENV_PYTHON) -m bandit -c bandit.yaml -lll -r app

precommit:
	$(VENV_PYTHON) -m pre_commit run --all-files

build-rust-accel:
	cd rust/ai_interview_accel && ..\\..\\.venv\\Scripts\\python.exe -m maturin develop --release

test-frontend:
	cd $(FRONTEND_DIR) && npm test

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

build-frontend:
	cd $(FRONTEND_DIR) && npm run build

train-ner-smoke:
	MLFLOW_ENABLED=true MLFLOW_TRACKING_URI=file:./mlruns-local $(VENV_PYTHON) -m app.ml.train_ner --num-samples 64 --epochs 1 --batch-size 8 --validation-split 0.2 --model-path saved_models/local_ner_smoke --metrics-path reports/local_ner_smoke_metrics.json

compose-config:
	$(COMPOSE) config

docker-build:
	docker build -t ai-interview:local .

dev-up:
	$(COMPOSE) up --build

dev-down:
	$(COMPOSE) down

mlflow-up:
	$(COMPOSE) up -d --build mlflow

mlflow-down:
	$(COMPOSE) stop mlflow

tf-fmt:
	cd deploy/aws/terraform && terraform fmt -recursive

tf-validate:
	cd deploy/aws/terraform && terraform init -backend=false && terraform validate
