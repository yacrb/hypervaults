#!/bin/sh
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
: "${MINIO_BUCKET:?MINIO_BUCKET is required}"

ENABLE_PUBLIC_MINIO_BUCKET="${ENABLE_PUBLIC_MINIO_BUCKET:-false}"

read_env_or_default() {
  env_name="$1"
  default_value="$2"
  eval "env_value=\${$env_name:-}"
  if [ -n "$env_value" ]; then
    printf '%s' "$env_value"
  else
    printf '%s' "$default_value"
  fi
}

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

if mc ls "local/$MINIO_BUCKET" >/dev/null 2>&1; then
  echo "Bucket $MINIO_BUCKET already exists"
else
  mc mb "local/$MINIO_BUCKET"
fi

if [ "$ENABLE_PUBLIC_MINIO_BUCKET" = "true" ]; then
  FLAG_MINIO_PUBLIC_BUCKET_VALUE="$(read_env_or_default FLAG_MINIO_PUBLIC_BUCKET '')"
  if [ -z "$FLAG_MINIO_PUBLIC_BUCKET_VALUE" ]; then
    echo "FLAG_MINIO_PUBLIC_BUCKET is required in public bucket challenge mode" >&2
    exit 1
  fi

  # INTENTIONAL CHALLENGE VULNERABILITY (third branch — OWASP A02):
  # Bucket is set to public read+list, making every uploaded user file
  # accessible to anyone who knows (or discovers) the object key.
  # Combined with the /objects/ gateway in nginx.conf.challenge, the entire
  # bucket becomes anonymously browsable and downloadable.
  echo "CHALLENGE MODE: applying public read/list policy to $MINIO_BUCKET"
  mc anonymous set public "local/$MINIO_BUCKET"

  # Seed the flag at the bucket root so players find it while browsing.
  printf '%s\n' "$FLAG_MINIO_PUBLIC_BUCKET_VALUE" \
    | mc pipe "local/$MINIO_BUCKET/flag.txt"

  # Seed a hint file that explains how the bucket was exposed.
  printf 'This bucket was temporarily opened during a migration sprint and never locked down again.\n' \
    | mc pipe "local/$MINIO_BUCKET/support/old-export-note.txt"

  # Seed a small, fake object set to make the listing look credible.
  printf 'Welcome to HyperVaults. Your files are stored in our private vault.\n' \
    | mc pipe "local/$MINIO_BUCKET/users/1/welcome.txt"
  printf 'Onboarding checklist\n- create staging user\n- verify upload limits\n- confirm object policies\n' \
    | mc pipe "local/$MINIO_BUCKET/users/1/onboarding-checklist.txt"
  printf 'Invoice sample for staging upload/download validation. No customer data.\n' \
    | mc pipe "local/$MINIO_BUCKET/users/2/invoice-sample.txt"
  printf 'Q2 security review draft\n\nCheck proxy headers, mail diagnostics, and object storage policy before launch.\n' \
    | mc pipe "local/$MINIO_BUCKET/users/3/q2-security-review-draft.txt"
  printf 'Support export note: old staging export retained for migration validation only.\n' \
    | mc pipe "local/$MINIO_BUCKET/support/support-export-note.txt"
  printf 'Migration note: verify bucket policy after gateway testing.\n' \
    | mc pipe "local/$MINIO_BUCKET/migration/readme.txt"
  printf 'Migration README\n\nTemporary public gateway testing must be reverted before release.\n' \
    | mc pipe "local/$MINIO_BUCKET/migration/migration-readme.txt"

  echo "Challenge files seeded into $MINIO_BUCKET"
else
  # Secure mode: enforce private policy on every run so switching back from
  # challenge mode re-locks the bucket without manual intervention.
  echo "Secure mode: keeping $MINIO_BUCKET private (no anonymous access)"
  mc anonymous set none "local/$MINIO_BUCKET"
fi
