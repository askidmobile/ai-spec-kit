---
description: Manage project tasks in TASKS.md via the task-tracker skill. Shows active tasks, adds new ones, updates statuses, archives completed ones to TASKS_ARCHIVE.md.
allowed-tools: Read, Edit, Bash, TodoWrite, AskUserQuestion
argument-hint: "list | active | backlog | show T-XXX | update T-XXX <status> | add <title> | archive T-XXX | archive-done"
---

# Task Management (TASKS)

Activate the **task-tracker** skill and execute the action per the arguments: **$ARGUMENTS**

> All operations go through the `tasks.py` script (next to the skill).
> Don't edit `TASKS.md` by hand — use the commands.

---

## If no arguments are given

Show active tasks and a summary:

```bash
python3 <SKILL_DIR>/scripts/tasks.py active
```

Where `<SKILL_DIR>` is the path to the `task-tracker` skill (for Claude Code that's `.claude/skills/task-tracker/` or `~/.claude/skills/task-tracker/`).

Then:
1. Output the list in a human-readable format (🔄 in progress, ✅ done).
2. Create a TodoWrite with all tasks in 🔄 status.
3. If the response's `overflow.over_limit` is `true` — report the numbers and
   the `hint`, and put archiving first among the options below.
4. Ask the user what to do next (4 options via `AskUserQuestion`):
   - Continue work on the current 🔄 task
   - Create a new task
   - Archive completed ones (`archive-done`)
   - Show the backlog

## If arguments are given

Pass them straight to the script:

```bash
python3 <SKILL_DIR>/scripts/tasks.py $ARGUMENTS
```

Parse the JSON response and show the result to the user.

## Available subcommands

| Command | What it does |
|---------|--------------|
| `list` | All tasks (active + backlog) with a summary |
| `active` | Active tasks only |
| `backlog` | Backlog only |
| `show T-XXX` | Details of a single task |
| `update T-XXX "✅ Done"` | Update status |
| `add "Title" "path/to/plan.md"` | Add to Active |
| `add-backlog "Title" "path.md" "Note"` | Add to Backlog |
| `archive T-XXX [T-YYY ...]` | Move rows to `TASKS_ARCHIVE.md` |
| `archive-done` | Move every ✅ Done task to `TASKS_ARCHIVE.md` |
| `migrate-archive` | One-shot: pull old in-file `## ✅ …` sections out to `TASKS_ARCHIVE.md` |
| `next-id` | Get the next free ID |

## Overflow

`list`/`active` return an `overflow` block (`active_rows`, `done_rows`,
`bytes`, `over_limit`, `hint`). If `over_limit` is `true` — show it and offer
`archive-done`; never trim `TASKS.md` by hand. `TASKS_ARCHIVE.md` is created
automatically on the first archive, no template needed.

## If TASKS.md doesn't exist yet

Ask the user whether to create it from the template. If yes — copy from `templates/TASKS.md` in the `ai-spec-kit` package into the project root.

## After context compaction

Run `active` and recreate TodoWrite — this restores work context.
