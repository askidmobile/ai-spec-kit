---
name: task-tracker
description: >-
  Manage project tasks in TASKS.md. Parses markdown tables, returns JSON,
  updates statuses, adds tasks, and archives completed ones out to
  TASKS_ARCHIVE.md when the file overflows. Syncs with TodoWrite.
  Activates on: "tasks", "task status", "what's left", "update TASKS",
  "show tasks", "next task", "task tracker", and after context compaction.
  Does NOT activate for: regular code discussions, git operations, builds.
allowed-tools:
  - Read
  - Edit
  - Bash
  - Write
---

# Task Tracker — Managing tasks in TASKS.md

Script: `<SKILL_DIR>/scripts/tasks.py`, where `<SKILL_DIR>` is this skill's
installed directory — e.g. `~/.claude/skills/task-tracker` (user scope) or
`.claude/skills/task-tracker` (project scope). Substitute the real path in
every command below.

Two files, both in the project root:

| File | Holds | Written by |
|------|-------|------------|
| `TASKS.md` | Active tasks (and Backlog, until it's split off) | `add`, `update`, `promote` |
| `TASKS_BACKLOG.md` | Backlog — someday/maybe, once `split-backlog` ran | `add-backlog`, `promote` |
| `TASKS_ARCHIVE.md` | Everything finished this year, in dated sections, newest on top | `archive`, `archive-done`, `migrate-archive` |

**A status is closed only when its marker LEADS the cell.** Real statuses are
long and quote per-phase progress inside the text — «🔄 In progress — phases
1-5/7 ✅», «👀 In review — all 7 phases ✅». Matching ✅ anywhere in the cell
files live work into the archive (caught in Yttri on 2026-08-20, two active
tasks one command away from being archived). `is_done_status` /
`is_cancelled_status` / `is_in_progress_status` in `tasks.py` are the single
place that decides this; tests in `StatusMarkerTests` hold the line.
| `TASKS_ARCHIVE_YYYY.md` | Past years, split off once the year turns | `rotate-archive` |

`TASKS.md` is the file that gets read into context on every session, so it has
to stay small. Completed tasks belong in the archive file, not in it.

## When to activate

- The user asks: "tasks", "status", "what's left", "show tasks"
- The user requests: "update TASKS.md", "mark task as done"
- **After context compaction** — if the user continues work on a task
- When a new plan is created (to register it in TASKS.md)
- When a task is completed (to update its status)

## Script commands

All commands return JSON. Run from the project root.

### Reading

```bash
# All tasks (active + backlog) with a summary
python3 <SKILL_DIR>/scripts/tasks.py list

# Active tasks only
python3 <SKILL_DIR>/scripts/tasks.py active

# Backlog only
python3 <SKILL_DIR>/scripts/tasks.py backlog

# Details of a single task
python3 <SKILL_DIR>/scripts/tasks.py show T-001

# Next free ID
python3 <SKILL_DIR>/scripts/tasks.py next-id
```

### Writing

```bash
# Update task status (Active tasks only — Backlog has no Status column)
python3 <SKILL_DIR>/scripts/tasks.py update T-001 "✅ Done"

# Add a task to Active
python3 <SKILL_DIR>/scripts/tasks.py add "Task title" "docs/plans/plan.md"

# Add a task to Backlog
python3 <SKILL_DIR>/scripts/tasks.py add-backlog "Title" "docs/plans/plan.md" "Note"

# Backlog → Active (keeps the ID, the Note column becomes 📝 Planning)
python3 <SKILL_DIR>/scripts/tasks.py promote T-009
```

### Splitting the backlog off

```bash
# One-shot: move the "## 📦 Backlog" section into TASKS_BACKLOG.md
python3 <SKILL_DIR>/scripts/tasks.py split-backlog
```

Worth doing when the backlog is a meaningful share of `TASKS.md` — it's
someday/maybe work that isn't needed in context for today's task. Every
backlog command routes through the file automatically, so a project that
never splits keeps working exactly as before.

### Archiving (moves rows out to `TASKS_ARCHIVE.md`)

```bash
# One or several tasks
python3 <SKILL_DIR>/scripts/tasks.py archive T-001 T-002

# Every CLOSED task at once (✅ done and ❌ cancelled) — the usual answer to
# overflow. The marker is read from the START of the status cell, so a live
# task reporting "🔄 In progress — phases 1-5/7 ✅" is never swept up.
python3 <SKILL_DIR>/scripts/tasks.py archive-done

# One-shot for older projects: pull the in-file "## ✅ Archived …" sections
# out of TASKS.md into TASKS_ARCHIVE.md
python3 <SKILL_DIR>/scripts/tasks.py migrate-archive

# Keep the archive to the current year — past years get TASKS_ARCHIVE_YYYY.md
python3 <SKILL_DIR>/scripts/tasks.py rotate-archive
```

The whole table row travels, so the plan link and the final status survive.
IDs are never reused — `next-id` scans every archive file, rotated ones too.

## Workflow: Show tasks

When the user asks to show tasks:

1. Run `python3 <SKILL_DIR>/scripts/tasks.py active`
2. Get the JSON with tasks
3. Output to the user in a readable format:
   - 🔄 In progress tasks — highlight as current
   - ✅ Done tasks — mark as completed
   - Show an overall summary (how many in progress, how many done)
4. **If TodoWrite/task tool is available**: sync 🔄 tasks to track them in the UI.
5. **Check the `overflow` block** in the JSON — see below.

## Workflow: Overflow

`list` and `active` return an `overflow` block:

```json
"overflow": {"active_rows": 99, "done_rows": 30, "bytes": 423660, "over_limit": true, "hint": "..."}
```

`over_limit` trips past 40 active rows, 10 ✅ rows, or 100 KB. When it's true:

1. Show the user the numbers and the `hint`.
2. If `done_rows > 0` — offer `archive-done`; it moves every closed task
   (✅ done, ❌ cancelled) out in one go. Don't run it silently, archiving is
   the user's call.
3. If the file still has `## ✅ …` sections inside it (a project that predates
   `TASKS_ARCHIVE.md`) — offer `migrate-archive` first.
4. If `done_rows` is 0 and it's still over — nothing to archive; the active
   rows need triage (close, split, or drop to Backlog).

Never trim `TASKS.md` by hand to make it fit — archiving is how it shrinks.

The same responses carry an `archive` block once the archive file exists:

```json
"archive": {"file": "TASKS_ARCHIVE.md", "bytes": 293171, "stale_years": ["2025"], "hint": "..."}
```

`stale_years` lists years the archive is still holding — offer
`rotate-archive`, which moves each one into its own `TASKS_ARCHIVE_YYYY.md`.
An empty list means there's nothing to rotate; don't run it then.

## Workflow: After context compaction

**CRITICAL.** If you notice the context was compacted and you were working on a task:

1. Run `python3 <SKILL_DIR>/scripts/tasks.py active`
2. Find tasks in 🔄 status
3. Recreate task tracker / TodoWrite with those tasks if available
4. Tell the user which tasks are currently in progress
5. Ask which task to continue

## Workflow: Creating a plan

When a new plan is created (Plan mode):

1. Create the plan file in `docs/plans/YYYY-MM-DD-name.md`
2. Run: `python3 <SKILL_DIR>/scripts/tasks.py add "Task description" "docs/plans/YYYY-MM-DD-name.md"`
3. Show the user the new task's ID

## Workflow: Starting work on a task

When you take a task into work (Build mode):

1. Run: `python3 <SKILL_DIR>/scripts/tasks.py update T-XXX "🔄 In progress"`
2. Create a TodoWrite with subtasks from the plan

## Workflow: Completing a task

When a task is done:

1. Run: `python3 <SKILL_DIR>/scripts/tasks.py update T-XXX "✅ Done"`
2. Update TodoWrite — mark the task as completed
3. Once the result is confirmed (tests pass, change shipped), move the row out:
   `python3 <SKILL_DIR>/scripts/tasks.py archive T-XXX`. A ✅ row left in
   Active is what makes the file overflow later.

## Task ID format

- Format: `T-XXX` (T-001, T-002, ...)
- ID auto-increments
- Use `next-id` to learn the next free one

## Statuses

| Emoji | Status | When to use |
|-------|--------|-------------|
| 📝 | Planning | Plan created, work not started |
| 🔄 | In progress | Active development |
| 👀 | In review | Code review / testing |
| ✅ | Done | Completed |

When updating status you can add a note: `"✅ Done (v0.38.0)"`, `"🔄 Phases 1-2 done"`.

## Optional: Yttri app integration

If the IDE is connected to the Yttri desktop app's MCP server, its task tools
can be used alongside `tasks.py` — see `YTTRI.md` in this skill's directory.

## Rules

1. **Don't edit any of the TASKS*.md files by hand** — always use `tasks.py`
   (moving a task between them is `promote` / `archive`, not cut-and-paste)
2. **Always sync TodoWrite** with the current tasks in TASKS.md
3. **After compaction** — first thing, reread tasks via `tasks.py active`
4. **New plan = new entry** in TASKS.md via `tasks.py add`
5. **Completion = status update** via `tasks.py update`, then `archive`
6. **`over_limit` = report it** and offer `archive-done` — don't ignore it and
   don't archive without asking
