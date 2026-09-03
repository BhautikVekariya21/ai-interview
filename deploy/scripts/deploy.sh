#!/usr/bin/env bash
set -euo pipefail

DEPLOY_ROOT="${HOME}/ai-interview"
COMPOSE_FILE="${DEPLOY_ROOT}/production/docker-compose.prod.yml"
ENV_FILE="${DEPLOY_ROOT}/production/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy deploy/production/.env.example to .env and fill in secrets."
  exit 1
fi

echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin

mkdir -p "${DEPLOY_ROOT}/production"
cd "${DEPLOY_ROOT}/production"

export BACKEND_IMAGE_REPOSITORY="${BACKEND_IMAGE_REPOSITORY:-}"
export FRONTEND_IMAGE_REPOSITORY="${FRONTEND_IMAGE_REPOSITORY:-}"
export IMAGE_TAG="${IMAGE_TAG:-latest}"

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --remove-orphans
docker image prune -f
