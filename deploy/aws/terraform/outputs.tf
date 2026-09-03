output "cluster_name" {
  value       = module.eks.cluster_name
  description = "EKS cluster name."
}

output "cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "EKS API server endpoint."
}

output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "VPC ID used by the platform."
}

output "backend_ecr_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "ECR URL for the backend image."
}

output "frontend_ecr_repository_url" {
  value       = aws_ecr_repository.frontend.repository_url
  description = "ECR URL for the frontend image."
}

output "mlflow_artifacts_bucket" {
  value       = aws_s3_bucket.mlflow_artifacts.bucket
  description = "S3 bucket for MLflow artifacts."
}

output "application_data_bucket" {
  value       = aws_s3_bucket.application_data.bucket
  description = "S3 bucket for application uploads and shared object data."
}

output "valkey_primary_endpoint" {
  value       = aws_elasticache_replication_group.valkey.primary_endpoint_address
  description = "Primary endpoint address for the ElastiCache Valkey replication group."
}

output "valkey_reader_endpoint" {
  value       = aws_elasticache_replication_group.valkey.reader_endpoint_address
  description = "Reader endpoint address for the ElastiCache Valkey replication group."
}

output "rds_postgres_endpoint" {
  value       = var.enable_rds_postgres ? aws_db_instance.postgres[0].address : null
  description = "Primary RDS PostgreSQL endpoint address."
}

output "rds_postgres_master_secret_arn" {
  value       = var.enable_rds_postgres ? aws_db_instance.postgres[0].master_user_secret[0].secret_arn : null
  description = "Secrets Manager ARN for the RDS PostgreSQL master credentials."
}

output "rds_postgres_read_replica_endpoint" {
  value       = var.enable_rds_postgres && var.create_rds_read_replica ? aws_db_instance.postgres_read_replica[0].address : null
  description = "Read replica endpoint for the RDS PostgreSQL primary/replica topology."
}

output "opensearch_domain_endpoint" {
  value       = var.enable_opensearch ? aws_opensearch_domain.app[0].endpoint : null
  description = "OpenSearch domain HTTPS endpoint."
}

output "events_queue_url" {
  value       = aws_sqs_queue.events.url
  description = "Primary SQS queue URL for backend async events."
}

output "events_dead_letter_queue_url" {
  value       = aws_sqs_queue.events_dlq.url
  description = "Dead-letter SQS queue URL for backend async events."
}

output "ops_alerts_topic_arn" {
  value       = aws_sns_topic.ops_alerts.arn
  description = "SNS topic ARN for operational alerts and notifications."
}

output "eventbridge_bus_name" {
  value       = aws_cloudwatch_event_bus.app.name
  description = "EventBridge custom event bus name for platform events."
}

output "platform_kms_key_arn" {
  value       = aws_kms_key.platform.arn
  description = "KMS key ARN for platform encryption use cases."
}

output "msk_bootstrap_brokers_sasl_iam" {
  value       = var.enable_msk ? aws_msk_cluster.app[0].bootstrap_brokers_sasl_iam : null
  description = "Amazon MSK bootstrap brokers using SASL/IAM."
}

output "glue_catalog_database_name" {
  value       = var.enable_glue_athena ? aws_glue_catalog_database.analytics[0].name : null
  description = "Glue catalog database for analytics datasets."
}

output "athena_workgroup_name" {
  value       = var.enable_glue_athena ? aws_athena_workgroup.analytics[0].name : null
  description = "Athena workgroup name for analytics queries."
}

output "athena_results_bucket" {
  value       = var.enable_glue_athena ? aws_s3_bucket.athena_results[0].bucket : null
  description = "S3 bucket for Athena query results."
}

output "shared_efs_file_system_id" {
  value       = aws_efs_file_system.shared.id
  description = "EFS file system ID for shared persistent storage."
}

output "cloudwatch_log_group_name" {
  value       = aws_cloudwatch_log_group.application.name
  description = "CloudWatch log group for platform workloads."
}

output "api_irsa_role_arn" {
  value       = aws_iam_role.api_irsa.arn
  description = "IRSA IAM role ARN for the backend Kubernetes service account."
}

output "app_secrets_manager_secret_arn" {
  value       = var.create_app_secrets_manager_secret ? aws_secretsmanager_secret.app[0].arn : null
  description = "Secrets Manager ARN for the application secret container."
}

output "acm_certificate_arn" {
  value       = var.enable_route53_acm ? aws_acm_certificate_validation.app[0].certificate_arn : null
  description = "ACM certificate ARN for the public app domain."
}

output "route53_zone_id" {
  value       = var.enable_route53_acm ? data.aws_route53_zone.primary[0].zone_id : null
  description = "Route53 hosted zone ID used for certificate validation."
}

output "aws_account_id" {
  value       = data.aws_caller_identity.current.account_id
  description = "AWS account ID used for this Terraform deployment."
}
