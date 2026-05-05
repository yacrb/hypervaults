#!/bin/sh
# Build the staging-debug challenge image and push it to Harbor.
# Run setup-harbor-project.sh first to create the 'hypervaults' project.
set -e

HARBOR_HOST="${HARBOR_HOST:-localhost}"
HARBOR_PORT="${HARBOR_PORT:-8090}"
PROJECT="${PROJECT:-hypervaults}"
IMAGE_NAME="${IMAGE_NAME:-hypervaults-api}"
IMAGE_TAG="${IMAGE_TAG:-staging-debug}"

REGISTRY="${HARBOR_HOST}:${HARBOR_PORT}"
FULL_IMAGE="${REGISTRY}/${PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_DIR="${SCRIPT_DIR}/../challenge-image"
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

FLAG_HARBOR_DEBUG_IMAGE_VALUE="$(read_env_or_default \
  FLAG_HARBOR_DEBUG_IMAGE \
  'Securinets{debug_images_should_not_reach_prod_registries}')"
HARBOR_USER="$(read_env_or_default HARBOR_ADMIN_USER admin)"
HARBOR_PASS="$(read_env_or_default HARBOR_ADMIN_PASSWORD Harbor12345)"

echo "Building ${FULL_IMAGE} ..."
docker build \
  --build-arg "FLAG_HARBOR_DEBUG_IMAGE=${FLAG_HARBOR_DEBUG_IMAGE_VALUE}" \
  -t "$FULL_IMAGE" \
  "$IMAGE_DIR"

echo "Logging in to ${REGISTRY} ..."
echo "$HARBOR_PASS" | docker login "$REGISTRY" -u "$HARBOR_USER" --password-stdin

echo "Pushing ${FULL_IMAGE} ..."
docker push "$FULL_IMAGE"

echo ""
echo "Done. Verify with:"
echo "  docker pull ${FULL_IMAGE}"
echo "  docker run --rm ${FULL_IMAGE}"
echo ""
echo "Or read just the build notes:"
echo "  docker run --rm --entrypoint cat ${FULL_IMAGE} /app/build-notes.txt"
