#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${AWS_ACCOUNT_ID:?AWS_ACCOUNT_ID is required}"
: "${EKS_CLUSTER_NAME:?EKS_CLUSTER_NAME is required}"

IMAGE_TAG="${IMAGE_TAG:?IMAGE_TAG is required}"
REPOSITORY_PREFIX="${ECR_REPOSITORY_PREFIX:-ai-interview-prod}"
BACKEND_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_PREFIX}-backend"
FRONTEND_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_PREFIX}-frontend"

echo "Updating kubeconfig for EKS..."
aws eks update-kubeconfig --name "${EKS_CLUSTER_NAME}" --region "${AWS_REGION}"

echo "Applying AWS EKS overlay..."
kubectl apply -k k8s/overlays/aws

echo "Redeploying existing images with tag ${IMAGE_TAG}..."
kubectl -n ai-interview set image deployment/api api="${BACKEND_REPO}:${IMAGE_TAG}"
kubectl -n ai-interview set image deployment/frontend frontend="${FRONTEND_REPO}:${IMAGE_TAG}"

echo "Waiting for rollouts..."
kubectl -n ai-interview rollout status deployment/api --timeout=5m
kubectl -n ai-interview rollout status deployment/frontend --timeout=5m
kubectl -n ai-interview rollout status deployment/gateway --timeout=5m

echo "AWS EKS redeploy complete."
