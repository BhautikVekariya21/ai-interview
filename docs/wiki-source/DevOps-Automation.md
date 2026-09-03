# DevOps Automation

## DevOps and CI/CD

This repository includes a practical baseline CI/CD setup. There is no Dependabot and no repo-automation bot layer — those were removed after bot-authored PRs/commits caused problems on this project, so all dependency and workflow changes are made and reviewed by hand.

- GitHub Actions CI at `.github/workflows/ci.yml`
- GitHub Actions CD at `.github/workflows/cd.yml`
- Release drafting at `.github/workflows/release-drafter.yml`
- Dedicated infrastructure checks at `.github/workflows/infra.yml`
- Repository label sync at `.github/workflows/repo-labels.yml`
- Issue forms under `.github/ISSUE_TEMPLATE/`
- PR labeling automation at `.github/workflows/labeler.yml` and `.github/workflows/pr-size-labeler.yml`
- Contributor/issue hygiene at `.github/workflows/greetings.yml`, `.github/workflows/auto-assign.yml`, `.github/workflows/assign-to-me.yml`, and `.github/workflows/lock-threads.yml`
- Stale thread cleanup at `.github/workflows/stale.yml`
- Markdown link checking at `.github/workflows/check-links.yml`
- GitHub workflow linting at `.github/workflows/actionlint.yml`
- CodeQL code scanning at `.github/workflows/codeql.yml`
- Dependency review at `.github/workflows/dependency-review.yml`
- Dependency vulnerability auditing at `.github/workflows/dependency-audit.yml`
- Manual redeploy workflow at `.github/workflows/manual-redeploy.yml`
- Scheduled smoke tests at `.github/workflows/smoke-tests.yml`
- Secret scanning at `.github/workflows/gitleaks.yml`
- OpenSSF Scorecards at `.github/workflows/scorecards.yml`
- Optional AWS EKS deployment automation via `deploy/aws/scripts/deploy-eks.sh`
- MLflow tracking server via `docker/mlflow.Dockerfile`
- dedicated backend and frontend production Dockerfiles under `docker/`
- Production compose stack at `deploy/production/docker-compose.prod.yml`
- Remote deploy helper at `deploy/scripts/deploy.sh`
- Root `.env.example` and production `deploy/production/.env.example`
- `.dockerignore` for smaller, safer image builds

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

## Troubleshooting
