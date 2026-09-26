# wl-copy (Wayland clipboard)

`wl-copy` forks and keeps stderr open → pipes hang. Fix: **always** `2>/dev/null`.

## Patterns

```bash
# File content
timeout 3 wl-copy 2>/dev/null < file.txt

# Inline text
echo "text" | timeout 3 wl-copy 2>/dev/null

# Command output → intermediate (e.g. temp file, jq format) → clipboard
# Dolt DB: first compile if needed, then pipe
cargo run -p coherence-core-db --bin coherence-core-db -- spec show SPEC-xxx \
  2>&1 | timeout 3 wl-copy 2>/dev/null

# Faster: reuse pre-built binary
target/debug/coherence-core-db spec show SPEC-xxx \
  2>&1 | timeout 3 wl-copy 2>/dev/null

# JSON intermediate via jq
cargo run -p coherence-core-db --bin coherence-core-db -- spec list \
  2>&1 | jq -r '.[] | .slug' | timeout 3 wl-copy 2>/dev/null
```

## Check

```bash
wl-paste
```
