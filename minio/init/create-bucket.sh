#!/bin/sh
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"

ENABLE_PUBLIC_MINIO_BUCKET="${ENABLE_PUBLIC_MINIO_BUCKET:-false}"

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

if mc ls "local/$MINIO_BUCKET" >/dev/null 2>&1; then
  echo "Bucket $MINIO_BUCKET already exists"
else
  mc mb "local/$MINIO_BUCKET"
fi

if [ "$ENABLE_PUBLIC_MINIO_BUCKET" = "true" ]; then
  # INTENTIONAL CHALLENGE VULNERABILITY (third branch — OWASP A02):
  # Bucket is set to public read+list, making every uploaded user file
  # accessible to anyone who knows (or discovers) the object key.
  # Combined with the /objects/ gateway in nginx.conf.challenge, the entire
  # bucket becomes anonymously browsable and downloadable.
  echo "CHALLENGE MODE: applying public read/list policy to $MINIO_BUCKET"
  mc anonymous set public "local/$MINIO_BUCKET"

  # Seed the flag at the bucket root so players find it while browsing.
  printf 'flag{public_buckets_make_private_uploads_public}\n' \
    | mc pipe "local/$MINIO_BUCKET/flag.txt"

  # Seed a hint file that explains how the bucket was exposed.
  printf 'This bucket was temporarily opened during a migration sprint and never locked down again.\n' \
    | mc pipe "local/$MINIO_BUCKET/support/old-export-note.txt"

  # Seed a realistic-looking user file to make the listing look credible.
  printf 'Welcome to HyperVaults. Your files are stored in our private vault.\n' \
    | mc pipe "local/$MINIO_BUCKET/users/1/welcome.txt"

  echo "Challenge files seeded into $MINIO_BUCKET"
else
  # Secure mode: enforce private policy on every run so switching back from
  # challenge mode re-locks the bucket without manual intervention.
  echo "Secure mode: keeping $MINIO_BUCKET private (no anonymous access)"
  mc anonymous set none "local/$MINIO_BUCKET"
fi
