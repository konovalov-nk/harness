---
name: git-commit
description: Conventional commits format and best practices for commit messages
---

# Git commits & review-friendly history (AI-friendly)

## Scope / activation (important)

These instructions are **opt-in** for AI assistants.

Only do commit planning / history rewriting when the user explicitly says one of:

- **`COMMIT PLAN MODE: PLAN`** (create/refresh a commit plan)
- **`COMMIT PLAN MODE: EXECUTE`** (rewrite commits from an approved plan)

Only do commit *review* (audit history against this guide) when the user says:

- **`COMMIT REVIEW MODE: REVIEW`** (review commits and report issues)
- **`COMMIT REVIEW MODE: FIX PLAN`** (propose a concrete fix plan)
- **`COMMIT REVIEW MODE: FIX EXECUTE`** (apply the fix plan)

If neither phrase is present:
- Use this doc as general guidance only.
- Do **not** rewrite history, do **not** soft-reset, do **not** force-push.

---

## Goals

- Make PRs easier to review by splitting work into **logical, complete commits**.
- Make `git log -p` useful (history tells a story and preserves context).
- Avoid “WIP soup” at merge time.

---

## Commit message format

Every commit message:

```

<Title (max 50 chars)>

# Context

1–3 sentences that explain the situation in simple terms.

Then a short list (when helpful):
- 1–4 bullets, concrete, no filler

Optional: add a small subsection if reviewers need a key concept:

### <Important detail>
Short explanation.

# Why

1–2 sentences explaining the intent and the tradeoff.

Then bullets (when helpful):
- 1–4 bullets, concrete, no filler

```

Rules:
- Title: imperative (“Add…”, “Fix…”, “Refactor…”), no trailing period.
- Wrap body at ~72 chars when practical.
- Keep Context/Why **short**. If it needs a novel, it belongs in the PR description.
- Prefer a mix of short prose + bullets over "only bullets" or "one long essay".

### “Good” example (short, actionable)

```

Add audit log for token rotations

# Context

* Token rotations were not recorded, making incident review harder.

# Why

* Persisting rotations enables traceability during auth investigations.
* Low risk: append-only writes behind existing service boundary.

```

### “AI slop” anti-example (don’t do this)

```

Implement improvements for authentication and other fixes

# Context

This commit introduces a comprehensive set of improvements that enhance
the overall quality and maintainability of the authentication system...

# Why

This is important because it improves the codebase and follows best
practices, ensuring future scalability and robustness...

```

Avoid phrases like:
- “This commit introduces…”
- “In order to…”
- “Best practices…”
- “Comprehensive / robust / scalable…” (unless you name the mechanism)

---

## What a “good commit” is

A good commit is:
- **Logically complete** (tests pass, no broken intermediate state).
- Reviewable in one sitting (aim small; avoid 500-line monsters).
- Coherent: one purpose, one “why”.

Avoid:
- “misc fixes”, “wip”, “stuff”
- mixing refactor + feature + formatting + drive-bys in one commit
- micro-commits that change 1 line without a story

---

## Commit review checklist

Use this checklist in **`COMMIT REVIEW MODE: REVIEW`**.

### Message quality

- Title is imperative, <= 50 chars, no trailing period
- Has `# Context` and `# Why`
- Context explains situation in simple terms (1–3 sentences)
- Why explains intent and tradeoffs (1–2 sentences)
- Bullets are concrete; no filler words ("robust", "best practices", etc)

### Change quality

- Commit is logically complete (build/tests pass or at least runnable)
- Scope is coherent (one purpose)
- Size is reviewable (avoid huge mixed commits)
- No obvious drive-bys (formatting, unrelated renames)

### Dependency / narrative

- Commit order is bottom-up (helpers first, usage later)
- Early commits do not rely on later commits
- Commit message does not name tools/files introduced only later

### Safety / hygiene

- No secrets committed
- No accidental generated files

---

## Common problems and how to fix them

Use this section in **`COMMIT REVIEW MODE: FIX PLAN`**.

### Problem: commit message references future code

- Fix: reword message to be self-contained
- Or: reorder commits so the referenced tool lands first

### Problem: mixed concerns in one commit

- Fix (preferred): split into multiple commits by whole files
- If one file mixes concerns: sequence edits so each commit touches the file
  coherently, or refactor into smaller files first

### Problem: commit too large

- Fix: split by layers (foundation -> wiring -> UI/docs/tests)

### Problem: message is "AI slop"

- Fix: replace vague prose with concrete facts:
  - what changed that matters?
  - what pain did it remove?
  - what behavior can reviewers verify?

### Problem: history needs rewriting but interactive tools unavailable

- Fix: use the non-interactive workflow described in this doc:
  - create a safety snapshot commit
  - `git reset --soft <base>`
  - re-create commits from a plan using whole-file staging

---

## Staging granularity

**Default: stage whole files only.**
- Use `git add path/to/file` (or a small set of files).
- Do **not** use hunks (`git add -p`) unless the user explicitly asks.

If one file contains changes that “should belong” to multiple commits:
- Prefer to **sequence edits** so each commit touches the file in one
  coherent way, or
- Split code into smaller files/modules so whole-file staging still maps
  cleanly to one logical step.

---

## Commit planning (review before approval)

When a PR is non-trivial or the history needs cleanup, create a **commit plan**
first so reviewers can comment on structure *before* you rewrite history.

Create:

```

commits/
MR.description.md
01.short-description.md
02.another-short-description.md
...

````

### `commits/MR.description.md` (PR description draft)

Keep this reviewer-facing and practical:

- What is changing (high-level)
- Why (business/tech reason)
- How to test
- How to validate (what evidence/outputs confirm it)
- Risks / rollout notes
- Things to pay attention to (edge cases, weirdness)

Template:

```md
# Context
- ...

# Why
- ...

## For reviewers

### How to test
1. ...

### How to validate
- ...

### Considerations
- ...

## Commits overview
1. 01.short-description — <one-liner>
2. 02.another-short-description — <one-liner>
...
````

### Per-commit plan file format

Each `commits/NN.*.md`:

```md
<Commit title (<= 50 chars)>

# Context
- ...

# Why
- ...

# Files
- path/to/file_a
- path/to/file_b

# Notes (optional)
- How to test this commit
- Review tips / gotchas
```

Rules:

* `# Files` lists **whole file paths** to stage together.
* Numbering (`01`, `02`, `03`) is the intended narrative order.

### Commit ordering principles (useful defaults)

1. Bottom-up: foundations first (schemas, utilities), then composition.
2. Tests with implementation: keep them in the same commit when possible.
3. Dependency order: don’t reference code that “arrives” in later commits.
4. Keep each commit green (build/tests pass).

Practical interpretation:

- Avoid referencing tools/commands in early commit messages if those tools are
  introduced only in later commits.
- If you need to mention them, do it generically ("later commits add a sweep")
  rather than naming specific scripts that do not exist yet.

---

## Executing a commit plan (history rewrite)

Only do this when the user says: **`COMMIT PLAN MODE: EXECUTE`**.

> Safety rules:
>
> * Prefer `--force-with-lease`, not `--force`.
> * Never rewrite commits that are already merged to the base branch.
> * If anything looks off, stop and ask for confirmation (don’t guess).

### 0) Status + safety snapshot

```bash
git status
git log --oneline --decorate -n 20
```

If you are about to rewrite history, create a recovery anchor:

```bash
git add -A
git commit -m "WIP: snapshot before rewrite"
```

### 1) Identify base branch (prefer remote)

Default base: `trunk`.

If unsure (or `trunk` doesn’t exist), check remotes and pick one:

* `origin/trunk` (preferred)
* `origin/main`

```bash
git fetch origin
git branch -r
```

Set `<BASE>` accordingly in the commands below.

### 2) Soft reset to base (keep changes)

```bash
git reset --soft origin/<BASE>
```

### 3) Assert state is correct

No commits ahead of base:

```bash
git log --oneline origin/<BASE>..HEAD
```

Expected: **no output**.

Working tree shows your changes preserved:

```bash
git status
```

### 4) Apply commit plan in order (whole files)

For each `commits/NN.*.md` in numerical order:

1. Unstage everything (keep changes):

```bash
git reset
```

2. Stage exactly the files listed in the plan file:

```bash
git add path/to/file_a path/to/file_b
```

3. Commit using the editor (avoid multi-line `-m` quoting issues):

```bash
git commit
```

Paste:

```
<Title>

# Context
- ...

# Why
- ...
```

4. Quick verify:

```bash
git show --stat
```

Repeat for the next plan file.

### 5) Verify + push safely

```bash
git log --oneline --decorate origin/<BASE>..HEAD
git status
```

Run tests/checks as appropriate.

Because history changed:

```bash
git push --force-with-lease origin HEAD
```

### About `commits/` cleanup

Do **not** auto-delete `commits/`.

Options:

* Keep it but add to `.gitignore` so it never ships, and copy/paste
  `MR.description.md` into the PR description.
* Or delete it **only if the user explicitly asks**.

---

## Review ergonomics

Reviewers can filter PR changes “by commit”.
Small, logically separated commits let people:

* review in chunks
* take breaks without losing context
* comment earlier (and avoid late-stage surprises)
