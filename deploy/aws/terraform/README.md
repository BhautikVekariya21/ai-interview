# AWS Terraform

This directory provisions the AWS foundation for running the platform on EKS.

Provisioned resources:

- `VPC` with public and private subnets
- `EKS` cluster with a managed node group
- `ECR` repositories for backend and frontend images
- `S3` buckets for MLflow artifacts and app object storage
- `ElastiCache for Valkey` for managed cache infrastructure
- `RDS PostgreSQL` for managed relational data and scheduler metadata
- `EFS` for shared filesystem workloads
- `CloudWatch` log group for platform logs
- `OpenSearch` for managed search and log-style indexing workloads
- `SQS` queues for async background event processing
- `SNS` topic for operational notifications and fan-out integrations
- `EventBridge` custom bus for event routing and integrations
- `AWS Glue` catalog and `Athena` workgroup for analytics over S3 datasets
- `AWS KMS` for platform-managed encryption keys
- `ACM` certificate with optional `Route53` DNS validation
- `Secrets Manager` secret container for application runtime secrets
- `IAM` IRSA role for the backend Kubernetes service account

## Files

- `providers.tf`: Terraform and AWS provider configuration
- `variables.tf`: configurable inputs
- `main.tf`: AWS resources
- `outputs.tf`: useful values for deployment wiring
- `terraform.tfvars.example`: starter variables
- `backend.hcl.example`: starter remote-state backend config

## Usage

Initialize Terraform:

```bash
cd deploy/aws/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
```

To use an S3 backend for Terraform state:

```bash
cp backend.hcl.example backend.hcl
terraform init -backend-config=backend.hcl
```

Plan and apply:

```bash
terraform plan -out tfplan
terraform apply tfplan
```

## Important outputs

After apply, capture these:

- `cluster_name`
- `backend_ecr_repository_url`
- `frontend_ecr_repository_url`
- `mlflow_artifacts_bucket`
- `application_data_bucket`
- `valkey_primary_endpoint`
- `rds_postgres_endpoint`
- `rds_postgres_read_replica_endpoint`
- `opensearch_domain_endpoint`
- `events_queue_url`
- `ops_alerts_topic_arn`
- `eventbridge_bus_name`
- `platform_kms_key_arn`
- `glue_catalog_database_name`
- `athena_workgroup_name`
- `shared_efs_file_system_id`
- `api_irsa_role_arn`
- `app_secrets_manager_secret_arn`
- `acm_certificate_arn`

## Kubernetes wiring

Update the AWS overlay with the Terraform outputs:

- Put `api_irsa_role_arn` into `k8s/overlays/aws/backend-serviceaccount.yaml`
- Replace the hostname in `k8s/overlays/aws/ingress-aws-alb.yaml`
- Optionally put `acm_certificate_arn` into the ALB ingress annotations

Update your runtime config to use managed AWS services where appropriate:

- Point `VALKEY_URL` / `REDIS_URL` at the ElastiCache Valkey endpoint
- Point Airflow or app relational metadata at the RDS PostgreSQL endpoint when enabled
- Use the RDS read replica output for read-heavy/reporting workloads when you enable the primary/replica database topology
- Use OpenSearch for search, indexing, or centralized app-side retrieval workloads when enabled
- Use SQS/SNS outputs for background workers, notifications, and async event fan-out
- Use EventBridge for cross-service event routing and downstream AWS integrations
- Use Glue/Athena for analytics over data stored in S3 without standing up extra query services
- Reuse the KMS key for application-side encryption needs where appropriate
- Store production secrets in Secrets Manager instead of plain `.env` files
- Use the S3 bucket outputs for MLflow artifacts and shared object storage

Then deploy with:

```bash
deploy/aws/scripts/deploy-eks.sh
```

## Optional cluster tooling

The repo also includes opt-in DevOps tooling manifests that pair well with this AWS setup:

- `k8s/optional-tools/external-secrets/` for syncing AWS Secrets Manager values into Kubernetes Secrets
- `k8s/optional-tools/keda/` for autoscaling from SQS queue depth
- `k8s/optional-tools/argo-rollouts/` for progressive canary-style releases

These are kept outside the base kustomization on purpose, since they require their own CRDs and controllers to be installed in the cluster first.
