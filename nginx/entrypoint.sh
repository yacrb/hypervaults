#!/bin/sh
set -e

# Generate the htpasswd file for Mailpit UI basic auth.
# The SHA1 format is supported by nginx and can be created using openssl,
# which is available in the nginx:alpine image.
# Credentials are intentionally weak and are leaked by the TRACE diagnostics
# endpoint in challenge mode — this is not meant to be guessed.
mkdir -p /etc/nginx/auth
HASH=$(printf '%s' 'devmail2026' | openssl sha1 -binary | openssl base64)
printf 'devmail:{SHA}%s\n' "$HASH" > /etc/nginx/auth/mailpit.htpasswd

exec nginx -g 'daemon off;'
