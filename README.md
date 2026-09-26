# harness

Personal [opencode](https://opencode.ai) harness: pinned config (skills, custom tools),
beads (`bd`) task tracking, and (soon) an e2e test container + review workflow with Plannotator.

## Layout

```
config/                    snapshot of ~/.config/opencode (sanitized)
  opencode.json            providers (local llama.cpp/vLLM), permissions
  tui.json                 keybinds
  AGENTS.md                global agent rules (wl-copy etc.)
  skills/                  base, git-commit, pfs-tfs, test-* ...
  tools/                   custom tools: rtmate (SSH/tmate)
  agents/                  implement, review-guide
  commands/                /plannotator-* slash command stubs
docs/                      report-card.md, plannotator.md, token-budget.md, research/
scripts/bootstrap.sh       copy config/ -> ~/.config/opencode (with backup)
docker/                    e2e container: Dockerfile, e2e.sh, test-in-container.sh
tests/mock-openai.py       mock OpenAI-compatible server for e2e (stdlib only)
.beads/                    bd database + git hooks (bd init)
AGENTS.md, CLAUDE.md       beads workflow instructions for agents
```

## Versions

| component | version |
|---|---|
| opencode | 1.18.32 |
| @opencode-ai/plugin | 1.4.9 |
| bd (beads) | 1.0.3 |

## Quickstart

```bash
./scripts/bootstrap.sh          # install config into ~/.config/opencode
$EDITOR ~/.config/opencode/remote.env   # fill from remote.env.example (rtmate)
```

Environment variables used by tools (never committed):

- `REMOTE_*` — rtmate, via `~/.config/opencode/remote.env`

## E2E container

```bash
docker/e2e.sh                  # or: ENGINE=podman docker/e2e.sh
```

Builds a Debian image with pinned opencode 1.18.32, mounts the repo read-only, copies
`config/` into the container HOME, removes host-dependent tools (rtmate),
starts `tests/mock-openai.py` and asserts `opencode run -m mock/mock "hi"` returns
`mock-ok`. The host `~/.config/opencode` is never touched.

To test against real local models, start the container with `--network=host` and use any
`local-llm-*` provider from the config (their `baseURL` points at `localhost:1000x`).

## Review workflow (Plannotator)

`@plannotator/opencode@0.27.20` is pinned in `config/opencode.json`. Plan review opens in
the browser when the `plan` agent calls `submit_plan`. `/plannotator-review` and
`/plannotator-annotate` (stubs in `config/commands/`) need the CLI:

```bash
curl -fsSL https://plannotator.ai/install.sh | bash -s -- --minimal
```

Compatibility notes and the headless spike results: [docs/plannotator.md](docs/plannotator.md).

## Agents

Two custom primary agents live in `config/agents/`:

- `implement` — makes the change and runs the project's checks; ends with a report card.
- `review-guide` — read-only (edit/write disabled); walks you through a finished change
  step by step, stops after each step, and collects numbered feedback items.

Report card format: [docs/report-card.md](docs/report-card.md).

## Token budget

Per-request cost measurements and the applied trims (−1,201 wire tokens, −11.4%):
[docs/token-budget.md](docs/token-budget.md).

## Secrets policy

- Auth lives outside the repo: `~/.local/share/opencode/auth.json`, `mcp-auth.json`, env vars.
- `remote.env` and `opencode.json.bak` are excluded on purpose (`*.bak` contained tokens).
- Never commit `*.env`, API keys, or auth dumps.
- gitleaks: pre-commit scans staged changes, pre-push scans the full history, CI runs on
  push/PR. Install the binary in `~/.local/bin` (<https://github.com/gitleaks/gitleaks>).
  Hooks print a warning and skip when the binary is missing.

## bd workflow

```bash
bd ready                 # available work
bd show <id>             # issue details
bd update <id> --claim   # claim
bd close <id>            # complete
```

## Roadmap

- [ ] e2e test container (opencode without touching host; local models via host network)
- [ ] Plannotator spike + review loop (annotate diffs, return comments to agent)
- [ ] Agent profiles: `implement` / `review-guide` + report card format
- [ ] ASD-STE100 translation of research notes (docs/research/)
- [ ] Token-efficiency: trim tool descriptions, per-agent tool sets
