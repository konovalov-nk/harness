#!/usr/bin/env bash
# Copy this repo's config/ into ~/.config/opencode (with backup).
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)/config"
DST="${HOME}/.config/opencode"
STAMP="$(date +%Y%m%d-%H%M%S)"

if ! command -v opencode >/dev/null 2>&1; then
  echo "opencode is not installed (expected version 1.18.32)" >&2
  exit 1
fi
ver="$(opencode --version 2>/dev/null || echo unknown)"
[[ "$ver" == "1.18.32" ]] || echo "warning: opencode ${ver}, snapshot targets 1.18.32"

mkdir -p "$DST"
if [[ -d "$DST" && -n "$(ls -A "$DST" 2>/dev/null || true)" ]]; then
  backup="${DST}.backup-${STAMP}"
  cp -a "$DST" "$backup"
  echo "backup: ${backup}"
fi

tar -C "$SRC" --exclude=node_modules --exclude=.venv -cf - . | tar -C "$DST" -xf -
[[ -f "$DST/remote.env" ]] || cp "$SRC/remote.env.example" "$DST/remote.env"

if [[ -d "$DST/tools/gitlab-feedback" && ! -d "$DST/tools/gitlab-feedback/node_modules" ]]; then
  echo "note: gitlab-feedback deps are not vendored. Install them with:"
  echo "      (cd \"$DST/tools/gitlab-feedback\" && npm ci)"
  echo "      (needs access to the gitlab.example.com npm registry)"
fi

echo "done: config -> ${DST}"
