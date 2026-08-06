# Yttri integration via MCP (optional)

Applies only if the IDE is connected to the Yttri desktop app's MCP server
(`http://localhost:9315/mcp`). It adds tools for working with tasks **in the
Yttri app**, alongside the `tasks.py`-managed `TASKS.md`.

## Available MCP tools (tasks domain)

| MCP Tool | tasks.py equivalent | What it does |
|----------|---------------------|--------------|
| `list_tasks(status?, limit?)` | `active` / `list` | List Yttri tasks. Filter: `todo`, `in_progress`, `done`, `all` |
| `get_task(uid)` | `show T-XXX` | Task details by uid (title, description, status, priority, due_date, subtasks) |
| `create_task(title, description?, priority?, due_date?)` | `add` | Create a task in Yttri. Appears in the Tasks UI |
| `update_task(uid, status?, title?, priority?)` | `update` | Update status: `todo`, `in_progress`, `done` |
| `delete_task(uid)` | `archive` (close) | Delete a task from Yttri |

## Two systems — two purposes

| | TASKS.md (`tasks.py`) | Yttri Tasks (MCP) |
|---|---|---|
| **Purpose** | Project development task tracker (plan → build) | User tasks in Yttri desktop |
| **ID** | `T-XXX` (T-001, T-213...) | UUID |
| **Storage** | Markdown file in the repository | SQLite inside Yttri |
| **Visibility** | Git, IDE | Yttri desktop UI |
| **Access** | Always (file) | Only when Yttri is running |

## When to use MCP tools

- The user asks to create a **user task** in Yttri (not a dev task)
- You need to see Yttri tasks without switching to the app
- The user is working on a feature and wants to see the task in the Yttri UI
- The user explicitly says "create a task in Yttri" / "show my tasks"

## When to use tasks.py

- Managing project **development** tasks (plan → implementation → retrospective)
- Working with the plan/build/review pipeline
- Updating task statuses for traceability in the repo
- After context compaction (TASKS.md is always available)

## Example: parallel work

```
# 1. Create a dev task in TASKS.md (plan tracking; <SKILL_DIR> — see SKILL.md)
python3 <SKILL_DIR>/scripts/tasks.py add "Refactor auth module" "docs/plans/auth-refactor.md"

# 2. Simultaneously create a task in Yttri (visible in UI)
# → MCP tool: create_task(title="Refactor auth module", description="Plan: docs/plans/auth-refactor.md, T-216")
```

## Connection requirements

1. Yttri desktop is running
2. MCP server is enabled (Settings → Integrations → MCP Server)
3. The `tasks` domain is enabled with `read_write` access
4. An API key is created and added to the IDE configuration

**Rule of thumb:** the MCP tools are an optional channel for Yttri UI tasks;
`TASKS.md` remains the primary dev tracker.
