---
description: Create or update a project brief via a deep coverage-driven interview. Produces docs/brief/ — main brief, interview log, decision log, research notes.
argument-hint: <project-name> [--fast | --update | --validate]
---

# Project Brief (BRIEF)

Activate the **project-brief** skill and run it for: **$ARGUMENTS**

> The brief describes WHY the project exists, WHAT it looks like at the top
> level and WHERE it's going. It's the foundation every `/create-spec` builds on.

## Modes

- **(default)** — full interview: one question at a time, laddering, pushback,
  research loops. The skill will not generate documents until every coverage
  category is closed or explicitly deferred — expect a real interview, not a form.
- `--fast` — remaining gaps batched into grouped messages; draft carries
  `[ASSUMPTION]` tags, listed by name at approval. Coverage gate still applies.
- `--update` — evolve an existing `docs/brief/` with a change signal;
  reversals of past decisions are logged as overrides, never rewritten.
- `--validate` — honest critique of an existing brief against its own goals.

## Output

`docs/brief/` folder: `PROJECT-BRIEF.md` (2-4 pages) + `interview-log.md`,
`decisions.md`, `open-questions.md`, `research.md`, optional `details/*`.

Next step after approval: `/create-spec <first-roadmap-feature>`.
