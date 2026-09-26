# Token budget

Measured 2026-09-26 on opencode 1.18.32, model `opencode-go/deepseek-v4.1-flash`.

## Method

- Clean HOME with this repo's `config/`, mock-free real provider, cwd `/tmp/oc-tok/work`.
- Scenario: `opencode run -m opencode-go/deepseek-v4.1-flash "hi"` (one user message).
- Wire numbers: provider usage from `opencode export` (`input + cache.read`).
- Breakdown: probe plugin (`experimental.chat.system.transform`, `tool.definition`) plus
  `GET /experimental/tool`; token counts with `cl100k_base` (estimate only).

## Result (same run, before and after the trims)

| Metric | before | after | delta |
|---|---|---|---|
| Provider wire prompt (input + cache read) | 10,571 | 9,370 | **−1,201 (−11.4%)** |
| Tool descriptions (cl100k) | 4,890 | 3,803 | −1,087 |
| `rtmate_rtmateStatus` description | 1,331 | 400 | −931 |
| System prompt (cl100k) | 2,636 | 2,636 | 0 |

System prompt structure (unchanged): base `default.txt` 1,771 + env/AGENTS.md 358 +
skills block 507.

## What was changed

- `config/tools/rtmate.txt`: the tool description was compressed from 87 lines to the
  essential rules (tool roles, sudo trick, interactive handoff, one-line sends). All
  workflows and warnings are kept.
- The `gitlab-feedback` tool was later removed from the public repo (it needs a private
  package registry); it was worth about 300-360 cl100k tokens in the full tool JSON.

## Remaining cost (after)

| Item | cl100k |
|---|---|
| `bash` description (built-in, cannot trim) | 1,051 |
| `task` / `edit` / `read` / `websearch` / `webfetch` | 491 / 286 / 258 / 216 / 166 |
| skills block, 7 advertised skills | 507 |
| test fixtures: `example-skill`, `test-allowed`, `test-ask` | 171 |

Options not applied: deny the unused test skills (saves ~171), per-agent tool sets
(already done for `review-guide`: edit/write are off).

## Notes

- Compare `input + cache.read`: the cache read split moves between runs.
- Numbers are one-shot, not averages; repeat before trusting small deltas.
- `submit_plan` (Plannotator) and `invalid` appear in registry dumps but are not part of
  the build-agent request, so the cl100k tool sum overcounts by ~300.
