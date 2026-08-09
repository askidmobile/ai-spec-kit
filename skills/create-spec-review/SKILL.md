---
name: create-spec-review
description: Post-implementation retrospective. Compares plan vs reality, generates a Retrospective section in the plan, updates spec and TASKS.md statuses. Describes WHAT WE ENDED UP WITH.
---


# Implementation Retrospective (REVIEW)

You are a tech lead running a retrospective. Your task is to compare the plan with reality and record the results: **$ARGUMENTS**

> **Retrospective = plan vs reality. What was achieved, what diverged, what lessons.**
> This skill does NOT change code — only documentation.


## PHASE 1: Recon (SILENT, no output)

### 1.1. Find the plan

If `$ARGUMENTS` is a file path → read it.
If `$ARGUMENTS` is a name → find it:
```
Glob: docs/plans/*$ARGUMENTS*
```
If not found → show the list: `ls docs/plans/` and let the user pick.

### 1.2. Find the linked spec

Read the `**Specification:**` field in the plan → load the spec from `docs/specs/`.

### 1.3. Find the task tracker

Check TASKS.md — are there entries related to this plan/spec.

### 1.4. Final check of unresolved questions

Read the "Deferred questions" sections in both the plan and the spec. For each entry determine the status:

- **Can be closed now** — implementation gave the answer (it became clear from how the code works in practice) → ask via `AskUserQuestion` to confirm "close as X?" with 2-3 options (see [interactive questions rules](#interactive-questions-rules-shared-block)). After the answer — move to "Decisions".
- **Genuinely still deferred** — the answer is still not needed (e.g. `When the answer is needed` = "v2"). Keep in "Deferred", record it in the retrospective.
- **Should have been closed but was forgotten** — this is **process debt**. Ask the user:
  - option A: close it now (with your recommendation);
  - option B: explicitly carry over to the next cycle (create an entry in TASKS.md / a new spec);
  - option C: mark as "no longer relevant".

Reflect all changes in the plan/spec files **before** generating the retrospective.


## PHASE 2: Implementation analysis (SILENT, no output)

### 2.1. Commits

Find the commits related to implementation:
- By the T-XXX task tag: `git log --oneline --grep="T-XXX"`
- By files from the plan: `git log --oneline -- path/to/file`
- By time range: from the plan's date to now

For key commits — `git show --stat <hash>` to see changed files.

### 2.2. Planned vs actual files

Compare:
- **Planned files** — all `path/to/file` entries from phase checklists
- **Actual files** — files from commits

Determine:
- Which planned files were changed ✅
- Which planned files were NOT touched ❌
- Which files were changed CONTRARY to the plan (unplanned) ⚠️

### 2.3. Checklist status

Walk through every plan phase, count: `[x]` vs `[ ]` per phase.


## PHASE 3: Comparison (SILENT, no output)

### 3.1. Deviations table

For each phase:
- Hour estimate vs actual time (if determinable from commits)
- Planned tasks vs tasks actually done
- Added tasks (not in the plan)
- Skipped tasks (in the plan, not done)

### 3.2. Requirements coverage

By the "Traceability: Requirements → Tasks" table from the plan:
- Which FR-XXX are fully implemented
- Which FR-XXX are partially implemented
- Which FR-XXX are not implemented

### 3.3. Patterns

Identify recurring patterns:
- Systematic under/over-estimates
- Typical causes of deviations (include the plan's `- deviated:` lines logged during implementation)
- Unplanned work — what caused it

### 3.4. Consistency sweep

Cross-check the artifacts before writing the retrospective:
- Spec ↔ plan terminology drift (same entity under different names)?
- Statuses agree (spec criteria ticks vs plan checklists vs TASKS.md)?
- Any principle bent during implementation but never justified in the plan's "Complexity & principle deviations"?
- Brief roadmap: is this feature's item still unticked in `docs/brief/PROJECT-BRIEF.md`?

Findings feed the Lessons/Recommendations sections and Phase 6 updates.


## Interactive questions rules (shared block)

When closing questions via `AskUserQuestion` in Phase 1.4:

- **One question = one tool call** (`questions` array of length 1).
- **2-4 options** + automatic Other.
- **Context in the question**: quote the wording from "Deferred questions" + a brief note of what actually got implemented.
- **Short label** (1-5 words), **description** explains how the answer will affect status and where it will be recorded (in "Decisions", in TASKS.md, or stays deferred).
- **Recommendation** — first option with `(Recommended)`, if the answer is obvious based on the actual implementation.


## PHASE 4: Retrospective generation

Append a new section at the end of the plan file:

```markdown

## Retrospective

**Review date:** YYYY-MM-DD
**Status:** ✅ Implemented / ⚠️ Partially implemented / ❌ Not implemented

### Summary

| Metric | Plan | Actual |
|--------|------|--------|
| Phases | N | N |
| Tasks | XX | YY |
| Files | XX | YY |
| Estimate (hours) | XX | ~YY |
| Commits | — | ZZ |

### Implementation commits

| Hash | Description | Files |
|------|-------------|-------|
| `abc1234` | feat: description | N |
| `def5678` | fix: description | N |

### Deviations from the plan

#### Added (not in the plan)
- [What was added and why]

#### Skipped (in the plan, not done)
- [What was skipped and why]

#### Changed (done differently)
- [What was done differently and why]

### Requirements coverage

| Requirement | Status | Comment |
|-------------|--------|---------|
| FR-001 | ✅ Implemented | |
| FR-002 | ⚠️ Partial | [what is not covered] |
| FR-003 | ❌ Not implemented | [reason] |

### Lessons

1. **[Lesson]** — [Description and recommendation]
2. **[Lesson]** — [Description and recommendation]

### Recommendations

- [What to improve in future iterations]
- [Tech debt, if it appeared]

### Closing deferred questions

> Outcome of review Phase 1.4: what happened to the entries from the "Deferred questions" of the plan/spec.

| Question | Decision | Where it was recorded |
|----------|----------|-----------------------|
| [Question quote] | Closed: [answer] | Plan → "Plan decisions" PD-NNN |
| [Question quote] | Moved to v2 | TASKS.md → T-XXX |
| [Question quote] | Stayed deferred | Plan → "Deferred questions" (unchanged) |
```


## PHASE 5: Approval

Show the user **in a single message**:

```
📊 Retrospective: [Plan name]

Status: ✅/⚠️/❌
Tasks done: X/Y
Commits: Z
Requirements covered: A/B

Deferred questions:
  - Closed in light of facts: N
  - Moved to backlog: M
  - Still deferred: K

Key deviations:
- [Briefly — what went off plan]

Definition of Done:
  Acceptance criteria passed: A/B
  Must-FRs uncovered: [list or "none"]

Proposed updates:
1. Plan → add "Retrospective" section + status "✅ Implemented"
2. Spec → mark fulfilled success criteria
3. TASKS.md → status "✅ Done"
4. Brief → tick the roadmap item (+ BD overrides, if implementation reversed a decision)
5. Tech Debt (TD-NNN) → move to TASKS.md backlog

Accept the updates?
```

Proceed to status updates automatically after displaying this summary. If the user wants to adjust — they will interrupt.


## PHASE 6: Status updates

After confirmation:

### 6.1. Plan
- Add the "Retrospective" section (from Phase 4)
- Change `**Status:**` → `✅ Implemented` (or `⚠️ Partially implemented`)

### 6.2. Spec
- Walk through "Success criteria" — mark `[x]` for fulfilled
- Walk through "Acceptance criteria" in scenarios — mark `[x]` for fulfilled

### 6.3. TASKS.md
- If the task is in TASKS.md — update status to "✅ Done"

### 6.4. Brief (if `docs/brief/` exists)
- Tick the feature's roadmap item in `PROJECT-BRIEF.md`
- If implementation reversed a brief decision → append an "overrides BD-XXX" row to `docs/brief/decisions.md` (never edit old rows)

### 6.5. Tech Debt harvest
If the plan's "Tech Debt" section has TD-NNN entries — offer to move them to
the Backlog via the task-tracker script, so debt survives outside the plan file:
```bash
python3 <SKILL_DIR>/scripts/tasks.py add-backlog "TD-NNN: <description>" "docs/plans/<plan>.md"
```
(`<SKILL_DIR>` — the installed `task-tracker` skill directory)

### 6.6. Commit changes

```bash
git add <changed files>
git commit -m "docs(<plan-name>): retrospective — Phase N complete (T-XXX)"
```

Output the commit hash:
```
✅ Committed: abc1234 — docs(auth-plan): retrospective complete (T-042)
```

### 6.7. Final output

```
📋 Retrospective completed!

Updated:
  ✅ Plan: docs/plans/[file] → status "Implemented" + "Retrospective" section
  ✅ Spec: docs/specs/[file] → success criteria marked
  ✅ TASKS.md → task T-XXX "Done"

Pipeline complete:
  ✅ /create-spec → specification
  ✅ /create-spec-plan → implementation plan
  ✅ /create-spec-implement → implementation
  ✅ /create-spec-review → retrospective
```
