# Plannotator integration (spike)

Tested 2026-09-26 against opencode 1.18.32 with `@plannotator/opencode@0.27.20`.

## What it is

Local, browser-based review surface for coding agents: plan review (intercepts the
plan step), code review of diffs/PRs with line annotations, and annotate-any-file.
Feedback returns to the agent as structured Markdown.

## Compatibility findings

- The npm package supports both OpenCode generations by design
  (`package.json` comment: OpenCode 1 loads `main` → `dist/index.js`,
  OpenCode 2 loads `exports[.]` → `dist/server.js`). Our build is OpenCode 1.
- Plugin hooks used: `tool.definition`, `experimental.chat.system.transform`,
  `experimental.chat.messages.transform`, `command.execute.before`.
  All four exist in opencode 1.18.32 (checked against the binary's plugin hook surface).
- `engines: bun >= 1.0.0`; the opencode binary is Bun-hosted, so the plugin uses its
  embedded runtime (bundled UI: `plannotator.html`, `review-editor.html`).
  The `plannotator` CLI is only needed for the slash commands on hosts without
  native command execution.
- Known upstream history: v0.27.11 fixed an opencode `serve` process leak — the
  pinned 0.27.20 includes the fix.

## Headless verification (temp HOME + mock model)

- Plugin loads with a clean server log; no hook errors.
- `submit_plan` appears in `GET /experimental/tool/ids` → plan review tool registered.
- `opencode run -m mock/mock "hi"` still returns `mock-ok` with the plugin enabled.
- Container e2e (`docker/e2e.sh`) also passes with the plugin enabled.

## Slash commands

`/plannotator-review`, `/plannotator-annotate`, `/plannotator-last` are installed as
markdown stubs in `config/commands/` (model-mediated path). They call the CLI:

```bash
curl -fsSL https://plannotator.ai/install.sh | bash -s -- --minimal   # binary -> ~/.local/bin
```

On hosts whose plugin API has native command execution, the plugin registers the
commands itself and the stubs are shadowed. Capability is detected at runtime.

## Workflow modes

Enabled with `"plugin": ["@plannotator/opencode@0.27.20"]` in `config/opencode.json`
(workflow `plan-agent` by default: `submit_plan` is available to the `plan` agent).
Other modes: `manual` (no tool, commands only), `user-managed`, `all-agents`.

## Local data

Reviews/plans stay on the machine: `~/.plannotator/` (feedback archive is local-only;
disable with `PLANNOTATOR_FEEDBACK_HISTORY=0`).

## Remaining (needs a browser, interactive)

- Click-through: open a plan review, annotate, approve/deny, verify the revision loop.
- Micro-diff code review: several line comments, confirm the agent processes each one.
  Tracked as a follow-up issue (see `bd list`).
