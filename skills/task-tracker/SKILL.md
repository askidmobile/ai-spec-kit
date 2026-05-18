---
name: task-tracker
description: >-
  Manage project tasks in TASKS.md. Parses markdown tables, returns JSON,
  updates statuses, adds and archives tasks. Syncs with TodoWrite.
  Activates on: "tasks", "task status", "what's left", "update TASKS",
  "show tasks", "next task", "task tracker", and after context compaction.
  Does NOT activate for: regular code discussions, git operations, builds.
allowed-tools:
  - Read
  - Edit
  - Bash
  - TodoWrite
---

# Task Tracker — Managing tasks in TASKS.md

Script: `.claude/skills/task-tracker/scripts/tasks.py`
Tasks file: `TASKS.md` (in the project root)

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
python3 .claude/skills/task-tracker/scripts/tasks.py list

# Active tasks only
python3 .claude/skills/task-tracker/scripts/tasks.py active

# Backlog only
python3 .claude/skills/task-tracker/scripts/tasks.py backlog

# Details of a single task
python3 .claude/skills/task-tracker/scripts/tasks.py show T-001

# Next free ID
python3 .claude/skills/task-tracker/scripts/tasks.py next-id
```

### Writing

```bash
# Update task status
python3 .claude/skills/task-tracker/scripts/tasks.py update T-001 "✅ Done"

# Add a task to Active
python3 .claude/skills/task-tracker/scripts/tasks.py add "Task title" "docs/plans/plan.md"

# Add a task to Backlog
python3 .claude/skills/task-tracker/scripts/tasks.py add-backlog "Title" "docs/plans/plan.md" "Note"

# Move to archive
python3 .claude/skills/task-tracker/scripts/tasks.py archive T-001
```

## Workflow: Show tasks

When the user asks to show tasks:

1. Run `python3 .claude/skills/task-tracker/scripts/tasks.py active`
2. Get the JSON with tasks
3. Output to the user in a readable format:
   - 🔄 In progress tasks — highlight as current
   - ✅ Done tasks — mark as completed
   - Show an overall summary (how many in progress, how many done)
4. **Create a TodoWrite** with all 🔄 tasks — to track them in the UI

## Workflow: After context compaction

**CRITICAL.** If you notice the context was compacted and you were working on a task:

1. Run `python3 .claude/skills/task-tracker/scripts/tasks.py active`
2. Find tasks in 🔄 status
3. Recreate TodoWrite with those tasks
4. Tell the user which tasks are currently in progress
5. Ask which task to continue

## Workflow: Creating a plan

When a new plan is created (Plan mode):

1. Create the plan file in `docs/plans/YYYY-MM-DD-name.md`
2. Run: `python3 .claude/skills/task-tracker/scripts/tasks.py add "Task description" "docs/plans/YYYY-MM-DD-name.md"`
3. Show the user the new task's ID

## Workflow: Starting work on a task

When you take a task into work (Build mode):

1. Run: `python3 .claude/skills/task-tracker/scripts/tasks.py update T-XXX "🔄 In progress"`
2. Create a TodoWrite with subtasks from the plan

## Workflow: Completing a task

When a task is done:

1. Run: `python3 .claude/skills/task-tracker/scripts/tasks.py update T-XXX "✅ Done"`
2. Update TodoWrite — mark the task as completed
3. If the plan can be archived: `python3 .claude/skills/task-tracker/scripts/tasks.py archive T-XXX`

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

## Yttri integration via MCP

If the IDE is connected to the Yttri MCP server (`http://localhost:9315/mcp`), additional tools are available for working with tasks **in the Yttri app**:

### Available MCP tools (tasks domain)

| MCP Tool | tasks.py equivalent | What it does |
|----------|---------------------|--------------|
| `list_tasks(status?, limit?)` | `active` / `list` | List Yttri tasks. Filter: `todo`, `in_progress`, `done`, `all` |
| `get_task(uid)` | `show T-XXX` | Task details by uid (title, description, status, priority, due_date, subtasks) |
| `create_task(title, description?, priority?, due_date?)` | `add` | Create a task in Yttri. Appears in the Tasks UI |
| `update_task(uid, status?, title?, priority?)` | `update` | Update status: `todo`, `in_progress`, `done` |
| `delete_task(uid)` | `archive` (close) | Delete a task from Yttri |

### Two systems — two purposes

| | TASKS.md (`tasks.py`) | Yttri Tasks (MCP) |
|---|---|---|
| **Purpose** | Project development task tracker (plan → build) | User tasks in Yttri desktop |
| **ID** | `T-XXX` (T-001, T-213...) | UUID |
| **Storage** | Markdown file in the repository | SQLite inside Yttri |
| **Visibility** | Git, IDE | Yttri desktop UI |
| **Access** | Always (file) | Only when Yttri is running |

### When to use MCP tools

- The user asks to create a **user task** in Yttri (not a dev task)
- You need to see Yttri tasks without switching to the app
- The user is working on a feature and wants to see the task in the Yttri UI
- The user explicitly says "create a task in Yttri" / "show my tasks"

### When to use tasks.py

- Managing project **development** tasks (plan → implementation → retrospective)
- Working with the plan/build/review pipeline
- Updating task statuses for traceability in the repo
- After context compaction (TASKS.md is always available)

### Example: parallel work

```
# 1. Create a dev task in TASKS.md (plan tracking)
python3 .claude/skills/task-tracker/scripts/tasks.py add "Refactor auth module" "docs/plans/auth-refactor.md"

# 2. Simultaneously create a task in Yttri (visible in UI)
# → MCP tool: create_task(title="Refactor auth module", description="Plan: docs/plans/auth-refactor.md, T-216")
```

### Connection requirements

1. Yttri desktop is running
2. MCP server is enabled (Settings → Integrations → MCP Server)
3. The `tasks` domain is enabled with `read_write` access
4. An API key is created and added to the IDE configuration

## Rules

1. **Don't edit TASKS.md by hand** — always use the `tasks.py` script
2. **Always sync TodoWrite** with the current tasks in TASKS.md
3. **After compaction** — first thing, reread tasks via `tasks.py active`
4. **New plan = new entry** in TASKS.md via `tasks.py add`
5. **Completion = status update** via `tasks.py update`
6. **MCP tools are an optional channel** for Yttri UI tasks; TASKS.md remains the primary dev tracker
