#!/bin/sh
# Create the 'hypervaults' project in Harbor via the Harbor v2 API.
# Run this once after Harbor is up and before pushing the debug image.
set -e

HARBOR_HOST="${HARBOR_HOST:-localhost}"
HARBOR_PORT="${HARBOR_PORT:-8090}"
HARBOR_USER="${HARBOR_USER:-admin}"
HARBOR_PASS="${HARBOR_PASS:-Harbor12345}"
PROJECT="${PROJECT:-hypervaults}"

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
