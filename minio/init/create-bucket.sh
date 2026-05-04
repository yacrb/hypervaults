#!/bin/sh
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

if mc ls "local/$MINIO_BUCKET" >/dev/null 2>&1; then
  echo "Bucket $MINIO_BUCKET already exists"
else
  mc mb "local/$MINIO_BUCKET"
fi

# Keep the bucket private. Object access happens only through short-lived presigned URLs.
mc anonymous set none "local/$MINIO_BUCKET"
