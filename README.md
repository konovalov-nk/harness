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
  tools/                   custom tools: rtmate (SSH/tmate), gitlab-feedback
scripts/bootstrap.sh       copy config/ -> ~/.config/opencode (with backup)
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

- `GITLAB_NPM_TOKEN`, `GITLAB_API_URL` — gitlab-feedback tool
- `REMOTE_*` — rtmate, via `~/.config/opencode/remote.env`

## Secrets policy

- Auth lives outside the repo: `~/.local/share/opencode/auth.json`, `mcp-auth.json`, env vars.
- `remote.env` and `opencode.json.bak` are excluded on purpose (`*.bak` contained tokens).
- Never commit `*.env`, API keys, or auth dumps; run gitleaks before publishing.

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
