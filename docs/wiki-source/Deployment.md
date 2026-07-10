# Deployment

## Local development

## Docker compose

Run app + MySQL + Valkey using the provided compose file:

```bash
docker-compose up --build
```

The local compose stack also includes an `mlflow` tracking server and a Prometheus/Grafana monitoring stack, so MySQL persistence, caching, MLOps tracking, and metrics dashboards can all run against real supporting infrastructure as needed.
The production stack now also includes Loki and Promtail for centralized log aggregation, and the repo ships an Argo CD application manifest for GitOps-based Kubernetes sync.

Default mapped ports:

- Backend: `http://localhost:8000` (container internal port `7860`)
- Valkey: `localhost:6379`
- MySQL: `localhost:3306`

Stop:

```bash
docker-compose down
```

The production container now builds the React frontend inside the Docker image and serves the compiled assets from FastAPI, so the backend image is self-contained for deployment.

---

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

## AWS Deployment

AWS is now a first-class deployment target in this repo.

Included AWS deployment assets:

- Terraform for VPC, EKS, ECR, S3, EFS, and CloudWatch under `deploy/aws/terraform/`
- A Terraform usage guide at `deploy/aws/terraform/README.md`
- An EKS deploy script under `deploy/aws/scripts/deploy-eks.sh`
- An AWS-specific Kubernetes overlay under `k8s/overlays/aws/`
- An Argo CD application for the AWS overlay at `deploy/argocd/ai-interview-aws-application.yaml`
- A GitHub Actions CD job that can deploy to EKS when AWS secrets are configured

Planned AWS service mapping in this repo:

- `Amazon EKS` for the Kubernetes control plane
- `Amazon ECR` for backend and frontend container images
- `Amazon S3` for MLflow artifact storage
- `Amazon EFS` for shared persistent filesystem workloads
- `Amazon CloudWatch` for workload logs and observability integration
- `Amazon ElastiCache for Valkey` for managed low-latency caching
- `Amazon RDS for PostgreSQL` for managed relational storage
- `Amazon OpenSearch Service` for managed search and indexing
- `Amazon SQS` for asynchronous queue-based processing
- `Amazon SNS` for notifications and event fan-out
- `Amazon EventBridge` for event routing and integration workflows
- `AWS Glue` and `Amazon Athena` for S3-native analytics
- `AWS KMS` for managed encryption keys
- `AWS Secrets Manager` for runtime secret storage
- `AWS Certificate Manager (ACM)` for TLS certificates
- `Amazon Route53` for DNS-backed certificate validation and domain management
- `AWS Load Balancer Controller` / `ALB Ingress` via the AWS overlay

Bootstrap flow:

```bash
cd deploy/aws/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Then deploy the app to EKS with:

```bash
AWS_REGION=ap-south-1 AWS_ACCOUNT_ID=123456789012 EKS_CLUSTER_NAME=ai-interview-eks IMAGE_TAG=latest deploy/aws/scripts/deploy-eks.sh
```

Before applying the AWS overlay, replace placeholder values like the IRSA role ARN and hostname in:

- `k8s/overlays/aws/backend-serviceaccount.yaml`
- `k8s/overlays/aws/ingress-aws-alb.yaml`

The AWS database layout now supports a primary/replica topology through Terraform, which is the modern AWS equivalent of a traditional master/slave deployment pattern for relational workloads.
