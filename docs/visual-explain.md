# Visual explanations from the OpenCode 2 TUI

Run `/visual-explain` after discussing or diagnosing a problem. The agent uses
the current conversation to draw the objects involved, their interfaces, and
event steps. Select an object or connection to see its role, mechanism, and
sources. Evidence labels distinguish reported observations, documentation,
hypotheses, and unknowns.

## Install without replacing your current configuration

From this checkout:

```bash
python3 scripts/install-visual-explain.py
```

This copies only `commands/visual-explain.md` and `skills/visual-explain/` into
`~/.config/opencode`. It backs up existing versions of those files and leaves
providers, agents, plugins, permissions, and the rest of your config intact.
Use `--config-dir /path/to/opencode` for a different active config directory.
Requires Python 3.9+; automatic opening on Linux uses `xdg-open` (package
`xdg-utils`) or `gio`. macOS uses `open`.

The rest of this repository is still a V1 snapshot. Do not use the full
`scripts/bootstrap.sh` to install this feature over your working V2 config.
This feature uses Markdown command/skill discovery, not the V1 custom-tool SDK.
If an already-running session does not list the command, open a new TUI session.
Use a build-capable agent; the read-only Plan agent cannot create the output.

## Daily flow

```text
Explain why switching workspaces adds video delay.
...agent collects evidence and diagnoses...
/visual-explain
```

Or supply a topic explicitly:

```text
/visual-explain show how frames move from the capture card to the screen
```

The command stays in the current session. It loads the skill, writes a small
JSON model, renders a self-contained page, and launches the default browser.
The shell tool returns immediately after launching the opener; the TUI remains
available. No local HTTP server, port, JavaScript build, or external service is
needed. Sources link to manuals, but loading and using the page works offline.

Default output:

```text
~/.local/share/opencode/visual-explain/<topic>/model.json
~/.local/share/opencode/visual-explain/<topic>/index.html
```

The skill honors `XDG_DATA_HOME` when choosing that location. Generated
explanations live outside the repository and are not committed automatically.
The static file does not watch the system or continue diagnosing it.

## More detail about an object or interface

Select an object or connection and click **Углубить в OpenCode**. Paste the
prepared request into the same TUI session. If the browser denies clipboard
access for `file://`, the page reveals a selected text field for manual copy.

```text
/visual-explain expand "/absolute/path/model.json" capture-api
```

The agent reads that model, investigates the selected part, and rerenders the
same page while preserving IDs and surrounding context. Browser clicks reveal
existing details immediately; generating new details requires the TUI request.
There is no browser-to-agent API bridge or model credential in the page.
Reopening the output may create another browser tab; it is not live reload.

## Try the included example without a model call

```bash
demo="${XDG_DATA_HOME:-$HOME/.local/share}/opencode/visual-explain/workspace-demo"
mkdir -p "$demo"
cp -f config/skills/visual-explain/examples/workspace-delay.json "$demo/model.json"
python3 config/skills/visual-explain/scripts/render.py "$demo/model.json" --open
```

The example illustrates the supplied capture/mpv/Hyprland report. Measurements
are explicitly attributed to that report. The exact driver, transport, and
point where video output blocks are not claimed as independently verified.
V4L2 is drawn as an interface, and feedback appears as a separate connection.

## Opening failures and remote sessions

The renderer always prints the absolute output path and `file://` URI. It
detaches the opener with stdin/stdout/stderr redirected, so browser processes
cannot hold the shell tool's pipes open. Opener failures do not discard the
generated page. A successful launch does not verify display in the browser.

Run OpenCode in the logged-in desktop user's environment so it inherits the
graphical session variables. On SSH/headless hosts, transfer the output
directory to the desktop machine and open `index.html` there. Regenerate it
with the local `model.json` to update the embedded follow-up path. Opening a
browser on the remote machine does not open one on the client machine.

## Validation and compatibility

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_visual_explain.py' -v
python3 config/skills/visual-explain/scripts/render.py \
  config/skills/visual-explain/examples/workspace-delay.json --check
```

The renderer rejects dangling endpoints, unknown source IDs, invalid event
states, duplicate IDs/cells, and unsupported source URL schemes. Text is
inserted as text; embedded JSON escapes HTML delimiters. The page's CSP blocks
network requests. This validates structure, not the truth of a diagnosis.

OpenCode 2 command and skill formats were checked against the official docs:

- [Commands](https://dev.opencode.ai/v2/docs/commands/): global `commands/`,
  `$ARGUMENTS`, and `subagent: false` to keep the current session.
- [Skills](https://dev.opencode.ai/v2/docs/skills/): global skill directories,
  relative supporting files, and the `skill` tool's `id` parameter.

The existing Docker smoke test pins OpenCode 1.18.32; it does not validate a V2
TUI session. Test this command once in the actual V2 installation before
assuming model-driven tool calls work with every configured provider.
