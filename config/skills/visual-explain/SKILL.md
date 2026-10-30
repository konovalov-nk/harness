---
name: visual-explain
description: Turn a diagnosis, architecture, or unfamiliar technical behavior into an interactive browser explanation. Use for /visual-explain, requests to draw objects and interfaces, or requests to expand an existing explanation with more detail.
---

# Visual explain

Build a spatial mental model before explaining the failure. Assume the user does
not know the names of the components. Use the user's language in the visual.

## Workflow

1. Reuse the conversation's observations and diagnostics. Read relevant code,
   configuration, manuals, or official docs to resolve uncertain interfaces.
   Keep new diagnosis read-only; creating an explanation does not authorize fixes.
2. Identify concrete entities and distinguish them from interfaces. Give each
   entity a plain-language role before its technical name. Put protocols, APIs,
   paths, payloads, and direction on the connections. Include feedback/control
   paths when relevant. Do not turn an API into an imaginary process.
3. Read `references/model.md`. Write a model JSON with stable IDs, a small graph
   (usually 3–7 entities), source-backed edges, and event steps. Use a component
   graph for structure and state changes on that SAME graph for behavior.
4. Store `model.json` and `index.html` in
   `${XDG_DATA_HOME:-$HOME/.local/share}/opencode/visual-explain/<topic-slug>/`.
   Use an ASCII slug. Resolve the skill's base directory from the loaded skill;
   do not assume it lives in the current project.
5. Run `python3 <skill-base>/scripts/render.py <model-path> --open` with the shell
   tool. The helper validates the model, writes standalone HTML beside it, and
   detaches the platform browser opener. Never start a server for this workflow.
6. Check the result when a browser tool is available: select both an entity and an
   interface, change an event step, and check a narrow layout. Otherwise state
   that rendering passed but browser behavior was not checked. Return the file
   path and one sentence about the useful interaction. Do not paste an essay.

## Content rules

- Start with the whole system visible. Keep entity positions stable across steps.
- Use short labels on the canvas; reveal role, mechanism, and sources on selection.
- Label each entity, interface, and event as `observed`, `documented`, `inferred`,
  or `unknown`. Cite source IDs. A manual establishes behavior in general; a log
  or measurement establishes what happened in this session. Do not confuse them.
- Show each causal event where it happens: active/stalled links, waiting objects,
  and concise state labels. Avoid detached dashboards or paragraphs replacing
  the drawing. Never animate made-up measurements as if they were observations.
- Keep uncertainty visible. The existence of a connection and the hypothesized
  reason it stalls may have different evidence. State that distinction in details.
- Use the bundled renderer first. It has entity/interface selection, event steps,
  sources, and a copyable follow-up request. Extend it only if the subject needs
  an interaction it cannot express. Do not depend on effectivehtml.com, a CDN,
  hosted assets, or ChatGPT-specific rendering APIs.

## Drill down

The browser's **Ask OpenCode** action prepares a request; it does not call an LLM.
The user copies it into the same TUI session. On a request like
`/visual-explain expand /absolute/path/model.json edge-id`, read that model and
the selected object, research the missing detail, update its explanation/sources,
and render the SAME output path again. Preserve IDs, surrounding entities, and
the graph's orientation. Add internal entities only when they clarify the request.
Do not silently replace an explanation with a new unrelated canvas.

## Opening and recovery

On a local Linux graphical session the helper uses `xdg-open` (then `gio open`);
on macOS it uses `open`. It returns immediately and always prints the file URI.
An opener launch is not proof that the browser displayed the page. On SSH or a
headless host, give the path and explain how to copy the containing directory to
the desktop machine. Do not invent display variables or expose a web server.
