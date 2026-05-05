#!/bin/sh
# Create the 'hypervaults' project in Harbor via the Harbor v2 API.
# Run this once after Harbor is up and before pushing the debug image.
set -e

HARBOR_HOST="${HARBOR_HOST:-localhost}"
HARBOR_PORT="${HARBOR_PORT:-8090}"
PROJECT="${PROJECT:-hypervaults}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

read_env_file_value() {
  env_name="$1"
  env_file="${ENV_FILE:-${REPO_ROOT}/.env}"
  if [ -f "$env_file" ]; then
    grep -E "^${env_name}=" "$env_file" | tail -n 1 | cut -d= -f2-
  fi
}

read_env_or_default() {
  env_name="$1"
  default_value="$2"
  eval "env_value=\${$env_name:-}"
  if [ -n "$env_value" ]; then
    printf '%s' "$env_value"
  else
    file_value="$(read_env_file_value "$env_name")"
    if [ -n "$file_value" ]; then
      printf '%s' "$file_value"
    else
      printf '%s' "$default_value"
    fi
  fi
}

HARBOR_USER="$(read_env_or_default HARBOR_ADMIN_USER admin)"
HARBOR_PASS="$(read_env_or_default HARBOR_ADMIN_PASSWORD Harbor12345)"

BASE_URL="http://${HARBOR_HOST}:${HARBOR_PORT}"

echo "Creating project '${PROJECT}' in Harbor at ${BASE_URL} ..."

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${HARBOR_USER}:${HARBOR_PASS}" \
  -X POST "${BASE_URL}/api/v2.0/projects" \
  -H "Content-Type: application/json" \
  -d "{\"project_name\": \"${PROJECT}\", \"public\": false}")

case "$HTTP_STATUS" in
  201) echo "Project '${PROJECT}' created." ;;
  409) echo "Project '${PROJECT}' already exists — continuing." ;;
  *)   echo "Unexpected status ${HTTP_STATUS}. Check Harbor is running at ${BASE_URL}." ; exit 1 ;;
esac
