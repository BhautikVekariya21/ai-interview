#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${AWS_ACCOUNT_ID:?AWS_ACCOUNT_ID is required}"
: "${EKS_CLUSTER_NAME:?EKS_CLUSTER_NAME is required}"

IMAGE_TAG="${IMAGE_TAG:-latest}"
REPOSITORY_PREFIX="${ECR_REPOSITORY_PREFIX:-ai-interview-prod}"
BACKEND_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_PREFIX}-backend"
FRONTEND_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_PREFIX}-frontend"

ensure_repo() {
  local repo_name="$1"
  aws ecr describe-repositories --repository-names "${repo_name}" --region "${AWS_REGION}" >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name "${repo_name}" --image-scanning-configuration scanOnPush=true --region "${AWS_REGION}" >/dev/null
}

echo "Ensuring ECR repositories exist..."
ensure_repo "${REPOSITORY_PREFIX}-backend"
ensure_repo "${REPOSITORY_PREFIX}-frontend"

echo "Logging into ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building and pushing backend image..."
docker build -f docker/backend.Dockerfile -t "${BACKEND_REPO}:${IMAGE_TAG}" .
docker push "${BACKEND_REPO}:${IMAGE_TAG}"

echo "Building and pushing frontend image..."
docker build -f docker/frontend.Dockerfile --build-arg VITE_API_BASE_URL=/ -t "${FRONTEND_REPO}:${IMAGE_TAG}" .
docker push "${FRONTEND_REPO}:${IMAGE_TAG}"

echo "Updating kubeconfig for EKS..."
aws eks update-kubeconfig --name "${EKS_CLUSTER_NAME}" --region "${AWS_REGION}"

echo "Applying AWS EKS overlay..."
kubectl apply -k k8s/overlays/aws

echo "Updating deployment images..."
kubectl -n ai-interview set image deployment/api api="${BACKEND_REPO}:${IMAGE_TAG}"
kubectl -n ai-interview set image deployment/frontend frontend="${FRONTEND_REPO}:${IMAGE_TAG}"

echo "Waiting for rollouts..."
kubectl -n ai-interview rollout status deployment/api --timeout=5m
kubectl -n ai-interview rollout status deployment/frontend --timeout=5m
kubectl -n ai-interview rollout status deployment/gateway --timeout=5m

echo "AWS EKS deployment complete."
