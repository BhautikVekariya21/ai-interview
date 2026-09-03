locals {
  name = "${var.project_name}-${var.environment}"
  azs  = length(var.availability_zones) > 0 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, 3)

  private_subnets = [
    for index, _ in local.azs :
    cidrsubnet(var.vpc_cidr, 4, index)
  ]

  public_subnets = [
    for index, _ in local.azs :
    cidrsubnet(var.vpc_cidr, 4, index + 8)
  ]

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )

  acm_validation_records = var.enable_route53_acm ? {
    for dvo in aws_acm_certificate.app[0].domain_validation_options :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_route53_zone" "primary" {
  count        = var.enable_route53_acm ? 1 : 0
  name         = var.hosted_zone_name
  private_zone = false
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = local.name
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = local.private_subnets
  public_subnets  = local.public_subnets

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb"                 = 1
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"        = 1
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  tags = local.common_tags
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = {}
    aws-ebs-csi-driver     = {}
    aws-efs-csi-driver     = {}
    amazon-cloudwatch-observability = {}
  }

  eks_managed_node_groups = {
    default = {
      instance_types = ["m6i.large"]
      desired_size   = 2
      min_size       = 2
      max_size       = 6

      subnet_ids = module.vpc.private_subnets

      labels = {
        workload = "general"
      }
    }
  }

  tags = local.common_tags
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent 30 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent 30 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "${local.name}-mlflow-artifacts"

  tags = local.common_tags
}

resource "aws_s3_bucket" "application_data" {
  bucket = "${local.name}-app-data"

  tags = local.common_tags
}

resource "aws_s3_bucket" "athena_results" {
  count  = var.enable_glue_athena ? 1 : 0
  bucket = "${local.name}-athena-results"

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "application_data" {
  bucket = aws_s3_bucket.application_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "application_data" {
  bucket = aws_s3_bucket.application_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "application_data" {
  bucket = aws_s3_bucket.application_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "athena_results" {
  count  = var.enable_glue_athena ? 1 : 0
  bucket = aws_s3_bucket.athena_results[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  count  = var.enable_glue_athena ? 1 : 0
  bucket = aws_s3_bucket.athena_results[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  count  = var.enable_glue_athena ? 1 : 0
  bucket = aws_s3_bucket.athena_results[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_kms_key" "platform" {
  description             = "Platform KMS key for ${local.name}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.common_tags
}

resource "aws_kms_alias" "platform" {
  name          = "alias/${local.name}-platform"
  target_key_id = aws_kms_key.platform.key_id
}

resource "aws_efs_file_system" "shared" {
  creation_token = "${local.name}-shared"
  encrypted      = true

  tags = merge(local.common_tags, {
    Name = "${local.name}-efs"
  })
}

resource "aws_security_group" "efs" {
  name        = "${local.name}-efs"
  description = "Allow EKS nodes to mount EFS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "NFS from EKS nodes"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_efs_mount_target" "shared" {
  for_each = {
    for index, subnet_id in module.vpc.private_subnets :
    index => subnet_id
  }

  file_system_id  = aws_efs_file_system.shared.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs.id]
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/${var.cluster_name}/ai-interview"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_event_bus" "app" {
  name = "${local.name}-bus"

  tags = local.common_tags
}

resource "aws_acm_certificate" "app" {
  count             = var.enable_route53_acm ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "certificate_validation" {
  for_each = local.acm_validation_records

  zone_id = data.aws_route53_zone.primary[0].zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "app" {
  count = var.enable_route53_acm ? 1 : 0

  certificate_arn         = aws_acm_certificate.app[0].arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation : record.fqdn]
}

resource "aws_elasticache_subnet_group" "valkey" {
  name       = "${local.name}-valkey"
  subnet_ids = module.vpc.private_subnets

  tags = local.common_tags
}

resource "aws_security_group" "valkey" {
  name        = "${local.name}-valkey"
  description = "Allow EKS nodes to connect to ElastiCache Valkey"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Valkey from EKS nodes"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_elasticache_replication_group" "valkey" {
  replication_group_id       = replace("${local.name}-valkey", "-", "")
  description                = "Valkey cache for ${local.name}"
  engine                     = "valkey"
  engine_version             = "7.2"
  node_type                  = var.valkey_node_type
  port                       = 6379
  parameter_group_name       = "default.valkey7"
  subnet_group_name          = aws_elasticache_subnet_group.valkey.name
  security_group_ids         = [aws_security_group.valkey.id]
  num_cache_clusters         = var.valkey_num_cache_clusters
  automatic_failover_enabled = var.valkey_num_cache_clusters > 1
  multi_az_enabled           = var.valkey_num_cache_clusters > 1
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = local.common_tags
}

resource "aws_secretsmanager_secret" "app" {
  count       = var.create_app_secrets_manager_secret ? 1 : 0
  name        = "${local.name}/application"
  description = "Application runtime secrets for ${local.name}"

  tags = local.common_tags
}

resource "aws_security_group" "msk" {
  count       = var.enable_msk ? 1 : 0
  name        = "${local.name}-msk"
  description = "Allow EKS nodes to connect to Amazon MSK"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Kafka TLS from EKS nodes"
    from_port       = 9094
    to_port         = 9094
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_msk_configuration" "app" {
  count            = var.enable_msk ? 1 : 0
  kafka_versions   = ["3.7.x"]
  name             = "${local.name}-msk-config"
  server_properties = <<-EOT
    auto.create.topics.enable=true
    default.replication.factor=3
    min.insync.replicas=2
    num.partitions=3
  EOT
}

resource "aws_msk_cluster" "app" {
  count                  = var.enable_msk ? 1 : 0
  cluster_name           = "${local.name}-msk"
  kafka_version          = "3.7.x"
  number_of_broker_nodes = var.msk_number_of_broker_nodes

  broker_node_group_info {
    instance_type   = var.msk_broker_instance_type
    client_subnets  = slice(module.vpc.private_subnets, 0, min(length(module.vpc.private_subnets), max(2, length(module.vpc.private_subnets))))
    security_groups = [aws_security_group.msk[0].id]

    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.app[0].arn
    revision = aws_msk_configuration.app[0].latest_revision
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.platform.arn

    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  client_authentication {
    unauthenticated = false

    sasl {
      iam = true
    }
  }

  tags = local.common_tags
}

resource "aws_glue_catalog_database" "analytics" {
  count = var.enable_glue_athena ? 1 : 0
  name  = replace("${local.name}_analytics", "-", "_")

  tags = local.common_tags
}

resource "aws_athena_workgroup" "analytics" {
  count = var.enable_glue_athena ? 1 : 0
  name  = "${local.name}-analytics"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results[0].bucket}/results/"
    }
  }

  tags = local.common_tags
}

resource "aws_db_subnet_group" "postgres" {
  count      = var.enable_rds_postgres ? 1 : 0
  name       = "${local.name}-postgres"
  subnet_ids = module.vpc.private_subnets

  tags = local.common_tags
}

resource "aws_security_group" "postgres" {
  count       = var.enable_rds_postgres ? 1 : 0
  name        = "${local.name}-postgres"
  description = "Allow EKS nodes to connect to RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_db_instance" "postgres" {
  count                       = var.enable_rds_postgres ? 1 : 0
  identifier                  = "${local.name}-postgres"
  engine                      = "postgres"
  engine_version              = "16.3"
  instance_class              = var.rds_instance_class
  allocated_storage           = var.rds_allocated_storage
  storage_type                = "gp3"
  db_name                     = "aiinterview"
  username                    = "appuser"
  manage_master_user_password = true
  db_subnet_group_name        = aws_db_subnet_group.postgres[0].name
  vpc_security_group_ids      = [aws_security_group.postgres[0].id]
  backup_retention_period     = 7
  deletion_protection         = true
  skip_final_snapshot         = false
  multi_az                    = var.rds_multi_az
  publicly_accessible         = false
  storage_encrypted           = true

  tags = local.common_tags
}

resource "aws_db_instance" "postgres_read_replica" {
  count                   = var.enable_rds_postgres && var.create_rds_read_replica ? 1 : 0
  identifier              = "${local.name}-postgres-replica"
  replicate_source_db     = aws_db_instance.postgres[0].identifier
  instance_class          = var.rds_read_replica_instance_class
  publicly_accessible     = false
  auto_minor_version_upgrade = true
  copy_tags_to_snapshot   = true
  skip_final_snapshot     = true

  tags = merge(local.common_tags, {
    Role = "read-replica"
  })
}

resource "aws_security_group" "opensearch" {
  count       = var.enable_opensearch ? 1 : 0
  name        = "${local.name}-opensearch"
  description = "Allow EKS nodes to connect to OpenSearch"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "HTTPS from EKS nodes"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_opensearch_domain" "app" {
  count         = var.enable_opensearch ? 1 : 0
  domain_name   = replace("${local.name}-search", "-", "")
  engine_version = "OpenSearch_2.17"

  cluster_config {
    instance_type  = var.opensearch_instance_type
    instance_count = var.opensearch_instance_count
    zone_awareness_enabled = var.opensearch_instance_count > 1

    dynamic "zone_awareness_config" {
      for_each = var.opensearch_instance_count > 1 ? [1] : []
      content {
        availability_zone_count = min(length(local.azs), 3)
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 20
    volume_type = "gp3"
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  vpc_options {
    subnet_ids         = slice(module.vpc.private_subnets, 0, min(length(module.vpc.private_subnets), max(1, var.opensearch_instance_count)))
    security_group_ids = [aws_security_group.opensearch[0].id]
  }

  tags = local.common_tags
}

resource "aws_sqs_queue" "events_dlq" {
  name                      = "${local.name}-events-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = local.common_tags
}

resource "aws_sqs_queue" "events" {
  name                    = "${local.name}-events"
  visibility_timeout_seconds = 60
  message_retention_seconds   = 345600
  sqs_managed_sse_enabled     = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.events_dlq.arn
    maxReceiveCount     = 5
  })

  tags = local.common_tags
}

resource "aws_sns_topic" "ops_alerts" {
  name = "${local.name}-ops-alerts"

  tags = local.common_tags
}

data "aws_iam_policy_document" "api_irsa_assume_role" {
  statement {
    effect = "Allow"

    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.kubernetes_namespace}:${var.backend_service_account_name}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "api_access" {
  statement {
    sid    = "MlflowArtifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.mlflow_artifacts.arn,
      "${aws_s3_bucket.mlflow_artifacts.arn}/*",
    ]
  }

  statement {
    sid    = "ApplicationData"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.application_data.arn,
      "${aws_s3_bucket.application_data.arn}/*",
    ]
  }

  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = ["${aws_cloudwatch_log_group.application.arn}:*"]
  }

  statement {
    sid    = "EventBridgePutEvents"
    effect = "Allow"
    actions = [
      "events:PutEvents",
    ]
    resources = [aws_cloudwatch_event_bus.app.arn]
  }

  dynamic "statement" {
    for_each = var.create_app_secrets_manager_secret ? [1] : []

    content {
      sid    = "SecretsManagerRead"
      effect = "Allow"
      actions = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
      ]
      resources = [aws_secretsmanager_secret.app[0].arn]
    }
  }

  statement {
    sid    = "SqsEvents"
    effect = "Allow"
    actions = [
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:SendMessage",
      "sqs:ChangeMessageVisibility",
    ]
    resources = [
      aws_sqs_queue.events.arn,
      aws_sqs_queue.events_dlq.arn,
    ]
  }

  statement {
    sid    = "SnsAlerts"
    effect = "Allow"
    actions = [
      "sns:Publish",
    ]
    resources = [aws_sns_topic.ops_alerts.arn]
  }

  dynamic "statement" {
    for_each = var.enable_opensearch ? [1] : []

    content {
      sid    = "OpenSearchHttp"
      effect = "Allow"
      actions = [
        "es:ESHttpGet",
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpDelete",
        "es:ESHttpHead",
      ]
      resources = ["${aws_opensearch_domain.app[0].arn}/*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_glue_athena ? [1] : []

    content {
      sid    = "AthenaGlueAccess"
      effect = "Allow"
      actions = [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_msk ? [1] : []

    content {
      sid    = "MskAccess"
      effect = "Allow"
      actions = [
        "kafka:GetBootstrapBrokers",
        "kafka:DescribeCluster",
        "kafka-cluster:Connect",
        "kafka-cluster:AlterGroup",
        "kafka-cluster:DescribeGroup",
        "kafka-cluster:ReadData",
        "kafka-cluster:WriteData",
        "kafka-cluster:DescribeTopic",
        "kafka-cluster:CreateTopic",
      ]
      resources = ["*"]
    }
  }

  statement {
    sid    = "KmsPlatformKey"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [aws_kms_key.platform.arn]
  }
}

resource "aws_iam_role" "api_irsa" {
  name               = "${local.name}-api-irsa"
  assume_role_policy = data.aws_iam_policy_document.api_irsa_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_policy" "api_access" {
  name   = "${local.name}-api-access"
  policy = data.aws_iam_policy_document.api_access.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "api_access" {
  role       = aws_iam_role.api_irsa.name
  policy_arn = aws_iam_policy.api_access.arn
}
