# INTENTIONAL CHALLENGE VULNERABILITY (fourth branch):
# Minimal fake HyperVaults API debug image used in the Harbor challenge.
# Contains build-notes.txt with the flag and a staging .env for realism.
# This image has no real application code — it exists only as a challenge artifact.
FROM alpine:3.20

LABEL org.opencontainers.image.title="hypervaults-api" \
      org.opencontainers.image.description="HyperVaults API staging debug image" \
      org.opencontainers.image.version="0.1.0-staging-debug"

WORKDIR /app

COPY build-notes.txt .
COPY .env.staging .

# Default entrypoint shows the build notes so players see the flag immediately
# when they run: docker run --rm <image>
CMD ["cat", "/app/build-notes.txt"]
