#!/usr/bin/env bash
# Build the e2e image and run the container smoke test.
# Host config is not touched: the repo is mounted read-only and copied
# into the container's HOME.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
ENGINE="${ENGINE:-docker}"
IMAGE="${IMAGE:-harness-e2e:1.18.32}"
OPENCODE_VERSION="${OPENCODE_VERSION:-1.18.32}"

"$ENGINE" build -t "$IMAGE" --build-arg "OPENCODE_VERSION=${OPENCODE_VERSION}" "$HERE"

"$ENGINE" run --rm \
  -v "$REPO":/harness:ro \
  "$IMAGE" bash /harness/docker/test-in-container.sh
