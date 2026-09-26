#!/usr/bin/env bash
# Runs inside the container (see e2e.sh). Proves that:
#   - pinned opencode starts
#   - repo config/ loads (opencode debug config)
#   - a chat round-trip works against the local mock model
# Assumes: repo mounted at /harness:ro, python3 available, network on.
set -euo pipefail

export HOME=/root
rm -rf "$HOME/.config/opencode" "$HOME/.local/share/opencode"
mkdir -p "$HOME/.config"
cp -a /harness/config "$HOME/.config/opencode"

# Custom tools that need host resources (SSH/tmate, GitLab API) are off for e2e.
rm -f "$HOME/.config/opencode/tools/rtmate.ts" "$HOME/.config/opencode/tools/rtmate.txt"
rm -rf "$HOME/.config/opencode/tools/gitlab-feedback" "$HOME/.config/opencode/tools/gitlab-feedback.ts"

# Add a mock provider (OpenAI-compatible) serving 127.0.0.1:19000.
python3 - <<'PY'
import json
import pathlib

path = pathlib.Path.home() / ".config/opencode/opencode.json"
cfg = json.loads(path.read_text())
cfg.setdefault("provider", {})["mock"] = {
    "npm": "@ai-sdk/openai-compatible",
    "name": "Mock (e2e)",
    "options": {"baseURL": "http://127.0.0.1:19000/v1"},
    "models": {"mock": {"name": "Mock", "limit": {"context": 8000, "output": 1000}}},
}
path.write_text(json.dumps(cfg, indent=2) + "\n")
PY

python3 /harness/tests/mock-openai.py &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 50); do
  curl -sf http://127.0.0.1:19000/v1/models >/dev/null 2>&1 && break
  sleep 0.2
done
curl -sf http://127.0.0.1:19000/v1/models >/dev/null

echo "--- versions ---"
opencode --version
echo "--- config resolves ---"
opencode debug config >/dev/null
echo "ok"

echo "--- opencode run ---"
out="$(opencode run -m mock/mock "hi" 2>&1)"
echo "$out"

grep -q "mock-ok" <<<"$out"
echo "E2E OK: container config loads and model round-trip works"
