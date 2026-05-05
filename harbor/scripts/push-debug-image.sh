#!/bin/sh
# Build the staging-debug challenge image and push it to Harbor.
# Run setup-harbor-project.sh first to create the 'hypervaults' project.
set -e

HARBOR_HOST="${HARBOR_HOST:-localhost}"
HARBOR_PORT="${HARBOR_PORT:-8090}"
HARBOR_USER="${HARBOR_USER:-admin}"
HARBOR_PASS="${HARBOR_PASS:-Harbor12345}"
PROJECT="${PROJECT:-hypervaults}"
IMAGE_NAME="${IMAGE_NAME:-hypervaults-api}"
IMAGE_TAG="${IMAGE_TAG:-staging-debug}"

REGISTRY="${HARBOR_HOST}:${HARBOR_PORT}"
FULL_IMAGE="${REGISTRY}/${PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_DIR="${SCRIPT_DIR}/../challenge-image"

echo "Building ${FULL_IMAGE} ..."
docker build -t "$FULL_IMAGE" "$IMAGE_DIR"

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
