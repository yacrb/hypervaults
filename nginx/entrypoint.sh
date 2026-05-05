#!/bin/sh
set -e

# Write the htpasswd file for Mailpit UI basic auth.
# The {SHA} format uses a precomputed base64(sha1("devmail2026")) value so this
# script has no dependency on openssl or any other hash utility — nginx:alpine
# is a minimal image and the sha1 subcommand is not reliably available there.
# Credentials are intentionally weak and are leaked by the TRACE diagnostics
# endpoint in challenge mode — this is not meant to be guessed.
mkdir -p /etc/nginx/auth
printf 'devmail:{SHA}G5mTZuWlOhreEhNXaqzsthmcwrg=\n' > /etc/nginx/auth/mailpit.htpasswd

exec nginx -g 'daemon off;'
