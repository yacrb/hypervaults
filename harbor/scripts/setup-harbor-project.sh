#!/bin/sh
# Create the 'hypervaults' project in Harbor via the Harbor v2 API.
# Run this once after Harbor is up and before pushing the debug image.
set -e

HARBOR_HOST="${HARBOR_HOST:-localhost}"
HARBOR_PORT="${HARBOR_PORT:-8090}"
SECRETS_DIR="${SECRETS_DIR:-./secrets.example}"
PROJECT="${PROJECT:-hypervaults}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

read_secret_or_env() {
  secret_file="$1"
  env_name="$2"
  default_value="$3"
  secret_path="${REPO_ROOT}/${SECRETS_DIR#./}/${secret_file}"
  if [ -s "$secret_path" ]; then
    sed -e 's/[[:space:]]*$//' "$secret_path"
  else
    eval "env_value=\${$env_name:-}"
    if [ -n "$env_value" ]; then
      printf '%s' "$env_value"
    else
      printf '%s' "$default_value"
    fi
  fi
}

HARBOR_USER="$(read_secret_or_env harbor_admin_user.txt HARBOR_USER '')"
HARBOR_PASS="$(read_secret_or_env harbor_admin_password.txt HARBOR_PASS '')"

if [ -z "$HARBOR_USER" ] || [ -z "$HARBOR_PASS" ]; then
  echo "Harbor credentials must be set through SECRETS_DIR or environment variables." >&2
  exit 1
fi

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
