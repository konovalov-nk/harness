---
name: pfs-tfs
description: Writing and maintaining PFS/TFS specs (product vs technical)
---

# PFS/TFS specs

This skill defines how to write and maintain two spec artifacts per feature:

- PFS: Product Feature Spec (user view: WHAT/WHY)
- TFS: Technical Feature Spec (engineering view: HOW/WHY)

Use these docs to preserve intent and decisions. Code explains "how"; the specs preserve "why".

## 1) Roles and ownership

### PFS

Purpose:

- Describes what the feature must do (user-visible behavior) and why it exists.
- Stable, decision-oriented.

Rules:

- User-owned: treat as read-only unless the user explicitly asks to change it.
- No implementation details (libraries, table schemas, exact endpoints) unless the user asks.

### TFS

Purpose:

- Describes how the system implements the PFS.
- Captures discoveries, tradeoffs, edge cases, operational notes.

Rules:

- Writable by the agent as we learn new constraints.
- It is normal for TFS to change as implementation evolves.

## 2) Allowed actions

Agents MAY:

- Read PFS/TFS any time.
- Update TFS to document decisions, constraints, and "why".

Agents MUST NOT:

- Change PFS unless the user explicitly requests it.
- "Adjust" requirements in PFS to match existing code.

## 3) Templates

### PFS template (minimal)

```md
# PFS: <Feature name>

## Goal
- <one sentence>

## Stories
- As a <persona>, I can <action> so that <outcome>.

## Acceptance Criteria
- Given/When/Then bullets.

## Non-goals
- Explicitly list what is out of scope.
```

### TFS template (minimal)

```md
# TFS: <Feature name>

## Overview
- Components/modules involved.

## API / Interfaces
- Endpoints/events/contracts.

## Data model (if relevant)
- Tables/fields/TTL/indexes.

## Security and abuse controls
- Threats + mitigations.

## Observability
- Metrics/logging/audit events.

## Test strategy
- Unit/integration/e2e focus.
```

## 4) Recommended file structure

Keep specs close to the feature they describe. Default layout:

- `docs/features/**` is feature-local specs (PFS + TFS).
- `docs/kb/**` is a shared knowledge base: reusable notes that multiple features can link to.

```
docs/
  kb/
    index.md
    <domain>/
      <topic>.md
  features/
    <feature-name>/
      pfs.md
      tfs/
        index.md
        <topic>/
          <specific-problem-we-solve-and-how>.md
```

Guidelines:

- `pfs.md`: stable product intent and acceptance criteria.
- `tfs/index.md`: a short technical overview plus links to deeper topics.
- `tfs/**`: one file per topic/problem; keep them small and link from `tfs/index.md`.

### Feature vs KB boundary

Keep `docs/features/<feature-name>/tfs/**` strictly feature-scoped:

- include only what is required to implement, review, and operate this feature
- prefer short "project-specific" notes, not general theory

Put reusable, cross-feature knowledge into `docs/kb/**` (knowledge base):

- minimal "just enough" references (e.g. "PipeWire basics", "Clipboard API notes")
- shared constraints and patterns used by multiple features

In feature TFS, link to KB files instead of duplicating them.

### Naming guidance

- `docs/kb/<domain>/<topic>.md`: use stable domains like `auth/`, `web/`, `audio/`, `time/`, `infra/`.
- `docs/features/<feature-name>/tfs/<topic>/...`: keep topics small and concrete (e.g. `security/`, `api/`, `ux/`, `ops/`, `data/`).

### When domain knowledge grows "too much"

It is normal for KB to grow over time. Domains tend to expand for predictable reasons:

- The problem is cross-cutting (auth, time, audio, payments): many features need the same rules.
- Edge cases accumulate (browser quirks, hardware differences, vendor behavior, timezones).
- "Tribal knowledge" gets written down for the first time, so hidden complexity becomes visible.
- The project scope silently expands (KB becomes a wiki for everything).

The goal is not to keep KB short at all costs. The goal is to keep the project maintainable.

#### What to do

If a KB topic keeps growing, treat it as a signal and pick the right response:

- Tighten scope: move broad background material out of the project (keep only "just enough" + links).
- Split by topic: add `docs/kb/<domain>/index.md` and break one long file into multiple focused ones.
- Productize repeated logic: when KB starts describing algorithms, invariants, or procedures you keep re-applying,
  encode it as code (a module/library/CLI) and keep KB as rationale + usage.
- Decouple via repos: if a large chunk becomes a standalone subsystem (e.g. a reusable library, a set of
  scripts, a micro-service), move it to a dedicated repository with its own PFS/TFS and versioning.

Practical heuristic:

- If multiple features link to the same KB file and it keeps changing, consider making a reusable module.
- If a KB section reads like a spec for a component, it probably is a component: give it its own repo.

## 5) Reference example in this skill

This skill directory includes a full worked example you can use as a style reference:

- `product-feature-specs.example.md` (Magic Link Sign-In)

When asked to produce a PFS/TFS example (or when unsure about structure), read
`product-feature-specs.example.md` and mirror its structure and depth.

How to use it:

- Treat it as a reference for structure and depth.
- Copy sections you need, then rewrite content to match the current feature.
- Do not inline the whole example into new specs; keep examples as separate files.

## Golden rule

- PFS answers WHAT/WHY (product view).
- TFS answers HOW/WHY (engineering view).

Never mix the two.
