#!/usr/bin/env bash
set -euo pipefail

ACTION="${ACTION:?ACTION is required}"
DEPLOY_ROOT="${HOME}/ai-interview"
COMPOSE_FILE="${DEPLOY_ROOT}/production/docker-compose.prod.yml"
ENV_FILE="${DEPLOY_ROOT}/production/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy deploy/production/.env.example to .env and fill in secrets."
  exit 1
fi

mkdir -p "${DEPLOY_ROOT}/production"
cd "${DEPLOY_ROOT}/production"

export BACKEND_IMAGE_REPOSITORY="${BACKEND_IMAGE_REPOSITORY:-}"
export FRONTEND_IMAGE_REPOSITORY="${FRONTEND_IMAGE_REPOSITORY:-}"
export IMAGE_TAG="${IMAGE_TAG:-latest}"

if [[ -n "${GHCR_TOKEN:-}" && -n "${GHCR_USERNAME:-}" ]]; then
  echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
fi

run_compose() {
  docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

case "${ACTION}" in
  status)
    run_compose ps
    ;;
  redeploy)
    run_compose pull
    run_compose up -d --remove-orphans
    ;;
  restart-api)
    run_compose restart api
    ;;
  restart-frontend)
    run_compose restart frontend
    ;;
  restart-nginx)
    run_compose restart nginx
    ;;
  logs-api)
    run_compose logs --tail=200 api
    ;;
  logs-frontend)
    run_compose logs --tail=200 frontend
    ;;
  logs-nginx)
    run_compose logs --tail=200 nginx
    ;;
  prune)
    docker image prune -f
    ;;
  *)
    echo "Unsupported ACTION=${ACTION}"
    exit 1
    ;;
esac
