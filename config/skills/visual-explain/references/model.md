# Explanation model (version 1)

Write UTF-8 JSON. Keep every ID stable when expanding an existing model. Labels
and details are plain text, never HTML. The renderer treats them as text.

```json
{
  "version": 1,
  "title": "Why the picture is late",
  "summary": "A model of the diagnosis, with uncertainty attached to the links.",
  "sources": [
    {"id": "manual", "label": "Official manual, option X", "url": "https://example.com/manual"},
    {"id": "measurement", "label": "Local measurement at 12:20; capture log"}
  ],
  "entities": [
    {"id": "source", "label": "Video source", "technical": "Capture device",
     "kind": "hardware", "row": 0, "column": 0,
     "summary": "Produces images.", "details": "Its role in this problem.",
     "evidence": "observed", "sources": ["measurement"]},
    {"id": "player", "label": "Video player", "technical": "mpv",
     "kind": "process", "row": 0, "column": 1,
     "summary": "Receives and displays the images.", "details": "Explain unfamiliar terms here.",
     "evidence": "observed", "sources": ["measurement"]}
  ],
  "interfaces": [
    {"id": "frames", "from": "source", "to": "player", "label": "Images + timestamps",
     "technical": "Actual API or protocol; verify it first",
     "details": "Who calls whom, what crosses the boundary, and what can wait.",
     "feedback": false, "evidence": "inferred", "sources": ["measurement"]}
  ],
  "steps": [
    {"id": "normal", "label": "Watching", "details": "Both components advance together.",
     "evidence": "observed", "sources": ["measurement"],
     "entities": {"source": "Capturing", "player": "Showing"},
     "interfaces": {"frames": "flowing"}}
  ]
}
```

- Required top-level fields: `version` (1), `title`, `sources`, `entities`,
  `interfaces`, `steps`. Optional: `summary`.
- Entity fields: `id`, `label`, `technical`, `kind`, `row`, `column`, `summary`,
  `details`, `evidence`, `sources`. Use unique cells, 0-based consecutive rows and
  columns; at most 3 columns. On phones, the graph becomes one column.
- Interface fields: `id`, `from`, `to`, `label`, `technical`, `details`,
  `evidence`, `sources`; optional `feedback` (boolean). Feedback edges take a
  separate curved route. Keep labels short (roughly 2–4 words).
- Step fields: `id`, `label`, `details`, `evidence`, `sources`, `entities`
  (entity ID → short state label), `interfaces` (interface ID → state).
  Interface states: `flowing`, `waiting`, `idle`, `uncertain`.
  Include at least a normal and a failure step for a diagnosis; add a fix step
  only if it was tested or explicitly label its expected effect as inferred.
- Evidence values: `observed`, `documented`, `inferred`, `unknown`.
  `observed` and `documented` require at least one source ID.
- Source fields: `id`, `label`, optional `url` (`https://` or `http://` only).
  Record log/command names and relevant values in source labels. Do not embed
  secrets, full environment dumps, or unrelated screenshots.
- All IDs are unique across the model and match `[a-z0-9]+(-[a-z0-9]+)*`.
- The model's absolute path is embedded by the renderer for copyable follow-ups.
  Keep that path current when moving or sharing an explanation.

See `examples/workspace-delay.json` for the capture/player/compositor case.
The example contains user-reported measurements and a causal hypothesis, not a
freshly reproduced diagnosis. Follow its evidence distinctions.
