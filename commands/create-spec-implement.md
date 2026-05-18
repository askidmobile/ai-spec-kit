---
description: Phase-by-phase plan implementation. Takes one phase, implements it, validates, records progress. Describes DOING — one phase at a time.
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, TodoWrite, AskUserQuestion
argument-hint: <path-to-plan-or-name> [phase N]
---

# Phase-by-phase Plan Implementer (IMPLEMENT)

You are a senior engineer. Your task is to implement one phase of the plan: **$ARGUMENTS**

> **Implementation = one phase at a time. Write code, verify, record.**
> Input is an approved plan from `docs/plans/`.

---

## PHASE 1: Recon (SILENT, no output)

### 1.1. Find the plan

If `$ARGUMENTS` contains a file path → read it.
If `$ARGUMENTS` is a name → find it:
```
Glob: docs/plans/*$ARGUMENTS*
```
If not found → show the list: `ls docs/plans/` and suggest `/create-spec-plan <name>`.

### 1.2. Determine progress

Read the plan in full. For each phase, determine status:
- ✅ **Completed** — all `[x]` in the checklist
- 🔄 **In progress** — some `[x]`, some `[ ]`
- ⬜ **Not started** — all `[ ]`

### 1.3. Find the linked spec

Read the `**Specification:**` field in the plan → load the linked spec from `docs/specs/`.

### 1.4. Check for unresolved questions

Read the "Deferred questions" section in both the plan and the spec. For each entry:

- If `When the answer is needed` points to the CURRENT plan phase or earlier → that question **blocks** implementation. Add to the queue.
- If the entry concerns a phase that's NOT selected right now — skip, you'll deal with it on the next `/create-spec-implement` call for that phase.

If the queue is non-empty — ask the questions **one at a time** via `AskUserQuestion` (see [interactive questions rules](#interactive-questions-rules-shared-block)). After each answer:

1. Open the source file (plan or spec) and move the entry from "Deferred" to "Plan decisions" / "Spec decisions".
2. If the answer changes the phase's tasks — update the phase's checklist in the plan.

Don't advance to Phase 2 until the queue is empty.

---

## PHASE 2: Phase selection

Show the user **in a single message**:

```
📋 Plan: [Plan name]
📄 Spec: [path to spec]

Phase progress:
  ✅ Phase 1: [Name] — completed
  🔄 Phase 2: [Name] — in progress (3/5 tasks)
  ⬜ Phase 3: [Name] — not started
  ⬜ Phase 4: [Name] — not started

→ Proposing: Phase N — [Name] (estimate: X h)
  Tasks:
  - [ ] Task 1
  - [ ] Task 2
  - ...
```

If the user specified a phase number in `$ARGUMENTS` → propose that one.
Otherwise → propose the next unfinished one (the first ⬜ or 🔄).

**DO NOT MOVE ON until the user confirms the phase.**

---

## PHASE 3: Loading context (SILENT, no output)

After phase confirmation:

### 3.1. Phase files
Read ALL files listed in the selected phase's tasks (paths from the checklist `→ path/to/file`).

### 3.2. Related requirements
In the "Traceability: Requirements → Tasks" table, find which FR-XXX this phase covers.
Read those requirements in the spec.

### 3.3. Project patterns
Study analogous implementations in the codebase — how similar modules, error handling, tests are organized.

---

## PHASE 4: Approval checkpoint

Show the user **in a single message** the attack plan:

```
🎯 Phase N: [Name]

Covers requirements: FR-001, FR-002, ...

Tasks:
1. [Task] → `path/to/file`
   Approach: [brief description of what and how we change]

2. [Task] → `path/to/file`
   Approach: [brief description]

...

Validation after implementation:
- [ ] cargo check / tsc --noEmit (compilation)
- [ ] [Relevant tests]
- [ ] [Manual check if needed]
```

**DO NOT MOVE ON until the user confirms the attack plan.**

---

## PHASE 5: Implementation

Execute the phase's tasks **strictly in order**.

### Implementation rules:

1. **One task at a time** — finish the current one, then move to the next
2. **Follow the project's patterns** — don't invent your own architecture, copy the style from analogous modules
3. **Mini-check after every task** — if the task modifies Rust code → `cargo check` afterwards. If TypeScript → `tsc --noEmit`. If it adds a test → run it
4. **Issues → report immediately** — if a task is impossible or requires changing the plan, stop implementation and tell the user
5. **Don't exceed the phase's scope** — don't do tasks from other phases, don't "improve" code outside the plan
6. **Ambiguity → ask via `AskUserQuestion`**. If a fork appears during implementation that isn't covered by the plan/spec (API choice, data shape, error text, edge-case behavior) — **don't guess**. Ask a question per the shared block rules, wait for the answer, record the decision in the plan (section "Plan decisions", `PD-NNN`), and only then continue.

---

## Interactive questions rules (shared block)

When closing questions via `AskUserQuestion`:

- **One question = one tool call** (`questions` array of length 1).
- **2-4 options** + automatic Other.
- **Context in the question**: 1-2 sentences on why you're asking and how the answer affects the current task.
- **Short label** (1-5 words), **description** explains the consequences.
- **Recommendation** — first option with `(Recommended)`, if there is a justified one.
- **header** — 1-3 words, chip-style topic label.
- **After the answer** — update the plan/spec file (record in "Decisions"), then continue implementation.

### After each task (brief):
```
✅ Task N: [description] — done
   Files: path/to/file (+XX/-YY lines)
```

---

## PHASE 6: Validation

After completing all phase tasks, run full validation:

### 6.1. Compilation
- Rust: `cargo check` (whole project)
- TypeScript: `tsc --noEmit`
- Other stack: adapt to the project

### 6.2. Tests
- Run tests related to the changed modules
- If the phase included writing tests — run them separately

### 6.3. Linting (if configured)
- `cargo clippy`, `eslint`, `prettier` — whatever is set up in the project

### Validation result:
```
🔍 Phase N validation:
  ✅ Compilation — OK
  ✅ Tests — 12 passed, 0 failed
  ⚠️ Clippy — 1 warning (not critical)
```

If validation fails → fix the errors and re-run validation.

---

## PHASE 7: Recording

### 7.1. Update the plan
Open the plan file and mark completed tasks: `[ ]` → `[x]`

### 7.2. Update TASKS.md (if any)
If the task is registered in TASKS.md — update progress.

### 7.3. Propose a commit
Suggest the user make a commit with the description:
```
Suggested commit:
  feat(<module>): <brief phase description> (T-XXX)

  Phase N of M of plan [name]:
  - [What was implemented — by task]
```

### 7.4. Final output

```
📊 Phase N completed!

Tasks done: X/X
Files changed: Y
Validation: ✅ OK

Plan progress:
  ✅ Phase 1: [Name]
  ✅ Phase 2: [Name]  ← current
  ⬜ Phase 3: [Name]
  ⬜ Phase 4: [Name]

→ Next step: /create-spec-implement <path-to-plan> phase N+1
```

If this was the last phase:
```
🎉 All plan phases implemented!

→ Next step: /create-spec-review <path-to-plan>
```
