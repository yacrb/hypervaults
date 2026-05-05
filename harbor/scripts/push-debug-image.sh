#!/bin/sh
# Build the staging-debug challenge image and push it to Harbor.
# Run setup-harbor-project.sh first to create the 'hypervaults' project.
set -e

HARBOR_HOST="${HARBOR_HOST:-localhost}"
HARBOR_PORT="${HARBOR_PORT:-8090}"
SECRETS_DIR="${SECRETS_DIR:-./secrets.example}"
PROJECT="${PROJECT:-hypervaults}"
IMAGE_NAME="${IMAGE_NAME:-hypervaults-api}"
IMAGE_TAG="${IMAGE_TAG:-staging-debug}"

REGISTRY="${HARBOR_HOST}:${HARBOR_PORT}"
FULL_IMAGE="${REGISTRY}/${PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_DIR="${SCRIPT_DIR}/../challenge-image"
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

FLAG_HARBOR_DEBUG_IMAGE_VALUE="$(read_secret_or_env \
  flag_harbor_debug_image.txt \
  FLAG_HARBOR_DEBUG_IMAGE \
  '')"
HARBOR_USER="$(read_secret_or_env harbor_admin_user.txt HARBOR_USER '')"
HARBOR_PASS="$(read_secret_or_env harbor_admin_password.txt HARBOR_PASS '')"

if [ -z "$FLAG_HARBOR_DEBUG_IMAGE_VALUE" ] || [ -z "$HARBOR_USER" ] || [ -z "$HARBOR_PASS" ]; then
  echo "Harbor flag and credentials must be set through SECRETS_DIR or environment variables." >&2
  exit 1
fi

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
