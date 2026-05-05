#!/bin/sh
set -u

BASE_URL="${BASE_URL:-http://localhost:8080}"
ENV_FILE="${ENV_FILE:-.env}"
PASS_COUNT=0
FAIL_COUNT=0

env_value() {
  name="$1"
  if [ -f "$ENV_FILE" ]; then
    grep -E "^${name}=" "$ENV_FILE" | tail -n 1 | sed "s/^${name}=//"
  fi
}

print_result() {
  name="$1"
  status="$2"
  detail="${3:-}"
  if [ "$status" = "PASS" ]; then
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  if [ -n "$detail" ]; then
    printf '%s %s - %s\n' "$status" "$name" "$detail"
  else
    printf '%s %s\n' "$status" "$name"
  fi
}

check_status() {
  name="$1"
  url="$2"
  expected="$3"
  shift 3
  code="$(curl -s -o /tmp/hypervaults_verify_body -w '%{http_code}' "$@" "$url" 2>/dev/null || printf '000')"
  if [ "$code" = "$expected" ]; then
    print_result "$name" PASS "HTTP $code"
  else
    print_result "$name" FAIL "expected HTTP $expected, got $code"
  fi
}

check_body_contains() {
  name="$1"
  url="$2"
  needle="$3"
  shift 3
  body="$(curl -s "$@" "$url" 2>/dev/null || true)"
  if printf '%s' "$body" | grep -q "$needle"; then
    print_result "$name" PASS
  else
    print_result "$name" FAIL "missing '$needle'"
  fi
}

CHALLENGE_MODE="$(env_value CHALLENGE_MODE)"
NGINX_CONFIG_FILE="$(env_value NGINX_CONFIG_FILE)"
ENABLE_XFF="$(env_value ENABLE_X_FORWARDED_DOCS_BYPASS)"
ENABLE_TRACE="$(env_value ENABLE_TRACE_MAIL_DIAGNOSTICS)"
ENABLE_MAILPIT="$(env_value ENABLE_MAILPIT_EXPOSURE)"
ENABLE_PUBLIC_MINIO="$(env_value ENABLE_PUBLIC_MINIO_BUCKET)"
ENABLE_OBJECTS="$(env_value ENABLE_OBJECTS_GATEWAY)"
ENABLE_HARBOR="$(env_value ENABLE_HARBOR_REGISTRY)"

printf 'HyperVaults verification\n'
printf 'Base URL: %s\n' "$BASE_URL"
printf 'Challenge mode: %s\n' "${CHALLENGE_MODE:-<unset>}"
printf 'Nginx config: %s\n' "${NGINX_CONFIG_FILE:-<unset>}"
printf 'Flags: XFF=%s TRACE=%s MAILPIT=%s PUBLIC_MINIO=%s OBJECTS=%s HARBOR=%s\n\n' \
  "${ENABLE_XFF:-<unset>}" \
  "${ENABLE_TRACE:-<unset>}" \
  "${ENABLE_MAILPIT:-<unset>}" \
  "${ENABLE_PUBLIC_MINIO:-<unset>}" \
  "${ENABLE_OBJECTS:-<unset>}" \
  "${ENABLE_HARBOR:-<unset>}"

if docker compose config >/tmp/hypervaults_compose_config 2>/tmp/hypervaults_compose_error; then
  print_result "docker compose config" PASS
else
  print_result "docker compose config" FAIL "$(cat /tmp/hypervaults_compose_error)"
fi

if docker compose ps >/tmp/hypervaults_compose_ps 2>/tmp/hypervaults_compose_ps_error; then
  print_result "docker compose ps" PASS
  cat /tmp/hypervaults_compose_ps
else
  print_result "docker compose ps" FAIL "$(cat /tmp/hypervaults_compose_ps_error)"
fi

check_status "backend health" "${BASE_URL}/api/health" 200
check_status "frontend route" "${BASE_URL}/" 200

if [ "$CHALLENGE_MODE" = "true" ]; then
  if [ "$ENABLE_XFF" = "true" ]; then
    check_status "docs denied without spoofed header" "${BASE_URL}/api/docs" 403
    check_status "docs allowed with spoofed header" "${BASE_URL}/api/docs" 200 -H "X-Forwarded-For: 127.0.0.1"
    check_body_contains "openapi contains internal docs description" "${BASE_URL}/api/openapi.json" "Internal documentation" -H "X-Forwarded-For: 127.0.0.1"
  else
    check_status "docs blocked" "${BASE_URL}/api/docs" 403
  fi

  if [ "$ENABLE_TRACE" = "true" ]; then
    check_body_contains "TRACE mail diagnostics" "${BASE_URL}/api/diagnostics/mail" "mailpit" -X TRACE -H "X-Forwarded-For: 127.0.0.1"
  else
    code="$(curl -s -o /tmp/hypervaults_verify_body -w '%{http_code}' -X TRACE "${BASE_URL}/api/diagnostics/mail" 2>/dev/null || printf '000')"
    case "$code" in
      404|405) print_result "TRACE diagnostics unavailable" PASS "HTTP $code" ;;
      *) print_result "TRACE diagnostics unavailable" FAIL "expected HTTP 404 or 405, got $code" ;;
    esac
  fi

  if [ "$ENABLE_MAILPIT" = "true" ]; then
    check_status "Mailpit requires Basic Auth" "${BASE_URL}/mailpit/" 401
  else
    check_status "Mailpit route present in challenge nginx config" "${BASE_URL}/mailpit/" 401
  fi

  if [ "$ENABLE_PUBLIC_MINIO" = "true" ] && [ "$ENABLE_OBJECTS" = "true" ]; then
    check_status "objects flag reachable" "${BASE_URL}/objects/hypervaults-files/flag.txt" 200
  else
    check_status "objects gateway present but bucket private or unseeded" "${BASE_URL}/objects/hypervaults-files/flag.txt" 403
  fi
else
  check_status "docs blocked" "${BASE_URL}/api/docs" 404
  check_status "openapi blocked" "${BASE_URL}/api/openapi.json" 404
  check_status "spoofed docs blocked" "${BASE_URL}/api/docs" 404 -H "X-Forwarded-For: 127.0.0.1"
  code="$(curl -s -o /tmp/hypervaults_verify_body -w '%{http_code}' -X TRACE "${BASE_URL}/api/diagnostics/mail" 2>/dev/null || printf '000')"
  case "$code" in
    404|405) print_result "TRACE diagnostics blocked" PASS "HTTP $code" ;;
    *) print_result "TRACE diagnostics blocked" FAIL "expected HTTP 404 or 405, got $code" ;;
  esac
  check_status "Mailpit blocked" "${BASE_URL}/mailpit/" 404
  check_status "objects blocked" "${BASE_URL}/objects/hypervaults-files/flag.txt" 404
fi

printf '\nSummary: %s passed, %s failed\n' "$PASS_COUNT" "$FAIL_COUNT"
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
