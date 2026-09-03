variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project prefix used for naming AWS resources."
  type        = string
  default     = "ai-interview"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "ai-interview-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.31"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use. Leave empty to auto-select the first three."
  type        = list(string)
  default     = []
}

variable "domain_name" {
  description = "Public app hostname used by the AWS ALB ingress."
  type        = string
  default     = "interviewer.example.com"
}

variable "hosted_zone_name" {
  description = "Route53 hosted zone name used for ACM DNS validation."
  type        = string
  default     = "example.com"
}

variable "enable_route53_acm" {
  description = "When true, create ACM certificate resources validated through Route53."
  type        = bool
  default     = false
}

variable "kubernetes_namespace" {
  description = "Kubernetes namespace where the app is deployed."
  type        = string
  default     = "ai-interview"
}

variable "backend_service_account_name" {
  description = "Service account name used by the API deployment for IRSA."
  type        = string
  default     = "ai-interview-api"
}

variable "valkey_node_type" {
  description = "ElastiCache Valkey node type."
  type        = string
  default     = "cache.t4g.small"
}

variable "valkey_num_cache_clusters" {
  description = "Number of cache nodes in the ElastiCache Valkey replication group."
  type        = number
  default     = 2
}

variable "create_app_secrets_manager_secret" {
  description = "When true, create a Secrets Manager secret container for app configuration."
  type        = bool
  default     = true
}

variable "enable_rds_postgres" {
  description = "When true, provision an RDS PostgreSQL instance."
  type        = bool
  default     = false
}

variable "rds_instance_class" {
  description = "Instance class for RDS PostgreSQL."
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GiB for RDS PostgreSQL."
  type        = number
  default     = 20
}

variable "rds_multi_az" {
  description = "When true, run the primary RDS PostgreSQL instance in Multi-AZ mode."
  type        = bool
  default     = true
}

variable "create_rds_read_replica" {
  description = "When true, create a read replica for the RDS PostgreSQL primary instance."
  type        = bool
  default     = false
}

variable "rds_read_replica_instance_class" {
  description = "Instance class for the RDS PostgreSQL read replica."
  type        = string
  default     = "db.t4g.micro"
}

variable "enable_opensearch" {
  description = "When true, provision an OpenSearch domain."
  type        = bool
  default     = false
}

variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch data nodes."
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch data nodes."
  type        = number
  default     = 2
}

variable "enable_msk" {
  description = "When true, provision an Amazon MSK cluster for Kafka workloads."
  type        = bool
  default     = false
}

variable "msk_broker_instance_type" {
  description = "Broker instance type for the MSK cluster."
  type        = string
  default     = "kafka.t3.small"
}

variable "msk_number_of_broker_nodes" {
  description = "Number of broker nodes in the MSK cluster."
  type        = number
  default     = 3
}

variable "enable_glue_athena" {
  description = "When true, provision Glue catalog and Athena workgroup resources."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags applied to AWS resources."
  type        = map(string)
  default     = {}
}
