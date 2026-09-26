# Report card

One card per task. The card is the short surface that makes a mental model cheap;
details stay collapsed until needed.

## Template

### <task id / title> — done | partial | blocked

- **Changed:** 1-3 bullets (areas and behavior, not file lists)
- **Why:** 1-2 sentences (intent and tradeoff)
- **Verified:** command(s) and result (e.g. `bun test` — 42 passed)
- **Open:** unresolved issues or follow-ups ("none" if none)

<details>
<summary>Details</summary>

- Problems found / solved / unresolved (with why and how)
- Key files and hunks to review (anchors, not full diffs)
- How to verify manually, step by step
- Review feedback collected (paste Plannotator items with file/line anchors)

</details>

## Rules

- No filler: numbers instead of adjectives, facts instead of "improved".
- Every claim has evidence (a command, a diff anchor, a test result).
- A blocked card says exactly what is blocked and what is needed.
- For multi-task runs, one card per task, in task order; the full set doubles as
  the end-of-run summary.
