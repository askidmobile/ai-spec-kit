#!/usr/bin/env python3
"""
Parser and manager for TASKS.md.

Reads markdown tables, returns JSON. Updates statuses, adds and archives tasks.

Usage:
    python3 tasks.py list                          # All tasks (active + backlog)
    python3 tasks.py active                        # Active only
    python3 tasks.py backlog                       # Backlog only
    python3 tasks.py show T-001                    # Task details
    python3 tasks.py update T-001 "✅ Done"        # Update status
    python3 tasks.py add "Title" "path.md"         # Add to Active
    python3 tasks.py add-backlog "Title" "path.md" "Note"
    python3 tasks.py archive T-001                 # Move to archive
    python3 tasks.py next-id                       # Next free ID
"""

import json
import re
import sys
import os
from datetime import date
from typing import Optional


def find_tasks_md() -> str:
    """Find TASKS.md — walks up from the current directory."""
    current = os.getcwd()
    while True:
        candidate = os.path.join(current, "TASKS.md")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    # Fallback: next to the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # scripts/ -> task-tracker/ -> skills/ -> .claude/ -> project root
    root = os.path.normpath(os.path.join(script_dir, "..", "..", "..", ".."))
    candidate = os.path.join(root, "TASKS.md")
    if os.path.isfile(candidate):
        return candidate
    print(json.dumps({"error": "TASKS.md not found"}))
    sys.exit(1)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def parse_table_row(row: str) -> list[str]:
    """Parse a markdown table row into a list of cells."""
    cells = row.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def parse_section(
    content: str, header_pattern: str
) -> tuple[list[str], list[list[str]], int, int]:
    """
    Parse a markdown table section.
    Returns: (headers, data_rows, start_line_index, end_line_index)
    """
    lines = content.split("\n")
    headers = []
    rows = []
    in_section = False
    table_started = False
    start_idx = -1
    end_idx = -1
    separator_skipped = False

    for i, line in enumerate(lines):
        if re.search(header_pattern, line, re.IGNORECASE):
            in_section = True
            continue

        if in_section:
            stripped = line.strip()
            # New ## section — end of current
            if stripped.startswith("## ") and table_started:
                end_idx = i
                break

            # Table row
            if stripped.startswith("|"):
                if not table_started:
                    # First line — headers
                    headers = parse_table_row(stripped)
                    table_started = True
                    start_idx = i
                    continue
                elif not separator_skipped:
                    # Second line — separator (|---|---|)
                    separator_skipped = True
                    continue
                else:
                    # Data rows
                    row = parse_table_row(stripped)
                    rows.append(row)
                    end_idx = i + 1
            elif table_started and stripped == "":
                # Blank line after the table — end
                end_idx = i
                break

    return headers, rows, start_idx, end_idx


def parse_tasks(content: str) -> dict:
    """Parse all sections of TASKS.md."""
    # Active tasks
    active_headers, active_rows, _, _ = parse_section(
        content, r"^##\s+🚀\s+Active tasks"
    )

    # Backlog
    backlog_headers, backlog_rows, _, _ = parse_section(content, r"^##\s+📦\s+Backlog")

    def row_to_task(row: list[str], headers: list[str], section: str) -> dict:
        task = {"section": section}
        for idx, header in enumerate(headers):
            key = header.lower().strip()
            val = row[idx] if idx < len(row) else ""
            if key == "id":
                task["id"] = val
            elif key == "date":
                task["date"] = val
            elif key == "task":
                task["title"] = val
            elif key == "plan":
                task["plan"] = val
                # Extract path from a markdown link
                link_match = re.search(r"\[.*?\]\((.*?)\)", val)
                task["plan_path"] = link_match.group(1) if link_match else ""
            elif key == "status":
                task["status"] = val
            elif key == "note":
                task["note"] = val
        return task

    active = [row_to_task(r, active_headers, "active") for r in active_rows]
    backlog = [row_to_task(r, backlog_headers, "backlog") for r in backlog_rows]

    return {
        "active": active,
        "backlog": backlog,
        "total_active": len(active),
        "total_backlog": len(backlog),
        "in_progress": [t for t in active if "🔄" in t.get("status", "")],
        "completed": [t for t in active if "✅" in t.get("status", "")],
    }


def get_next_id(content: str) -> str:
    """Find the next free ID."""
    ids = re.findall(r"T-(\d+)", content)
    if not ids:
        return "T-001"
    max_id = max(int(i) for i in ids)
    return f"T-{max_id + 1:03d}"


def update_task_status(content: str, task_id: str, new_status: str) -> str:
    """Update a task's status by ID."""
    lines = content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if f"| {task_id} |" in line or f"| {task_id.strip()} |" in line:
            cells = parse_table_row(line)
            # Identify by column count.
            # Active: ID | Date | Task | Plan | Status
            # Backlog: ID | Date | Task | Plan | Note
            # Status is the last column in Active (index 4).
            if len(cells) >= 5:
                cells[4] = new_status
                lines[i] = "| " + " | ".join(cells) + " |"
                updated = True
                break

    if not updated:
        return ""
    return "\n".join(lines)


def add_task(
    content: str, title: str, plan_path: str, section: str = "active", note: str = ""
) -> tuple[str, str]:
    """Add a new task to the given section."""
    next_id = get_next_id(content)
    today = date.today().strftime("%Y-%m-%d")

    if plan_path and plan_path != "—":
        plan_name = os.path.basename(plan_path)
        plan_cell = f"[`{plan_name}`]({plan_path})"
    else:
        plan_cell = "—"

    if section == "active":
        new_row = f"| {next_id} | {today} | {title} | {plan_cell} | 📝 Planning |"
        pattern = r"^##\s+🚀\s+Active tasks"
    else:
        note_text = note if note else ""
        new_row = f"| {next_id} | {today} | {title} | {plan_cell} | {note_text} |"
        pattern = r"^##\s+📦\s+Backlog"

    lines = content.split("\n")
    in_section = False
    last_table_row = -1
    separator_seen = False

    for i, line in enumerate(lines):
        if re.search(pattern, line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith("|"):
                if not separator_seen and re.match(r"^\|[\s\-|]+\|$", stripped):
                    separator_seen = True
                last_table_row = i
            elif stripped.startswith("## ") and last_table_row > 0:
                break
            elif stripped == "" and last_table_row > 0:
                break

    if last_table_row > 0:
        lines.insert(last_table_row + 1, new_row)

    return "\n".join(lines), next_id


def archive_task(content: str, task_id: str) -> tuple[str, str]:
    """Move a task from Active to today's archive section."""
    lines = content.split("\n")
    task_line = None
    task_line_idx = -1
    task_title = ""

    for i, line in enumerate(lines):
        if f"| {task_id} |" in line:
            cells = parse_table_row(line)
            if len(cells) >= 4:
                task_title = cells[2]  # Task title
                task_line = line
                task_line_idx = i
            break

    if task_line_idx < 0:
        return "", ""

    lines.pop(task_line_idx)

    today = date.today().strftime("%Y-%m-%d")
    archive_header = f"## ✅ Archived {today}"

    archive_idx = -1
    for i, line in enumerate(lines):
        if archive_header in line:
            archive_idx = i
            break

    if archive_idx < 0:
        # Find the first "✅ Archived" section and insert before it
        for i, line in enumerate(lines):
            if line.strip().startswith("## ✅ Archived"):
                archive_idx = i
                archive_entry = f"\n{archive_header}\n\n- {task_title} ({task_id})\n"
                lines.insert(archive_idx, archive_entry)
                break

    else:
        # Section exists — append below its header
        insert_at = archive_idx + 1
        while insert_at < len(lines):
            stripped = lines[insert_at].strip()
            if stripped.startswith("- "):
                insert_at += 1
            elif stripped == "":
                insert_at += 1
            else:
                break
        lines.insert(insert_at, f"- {task_title} ({task_id})")

    return "\n".join(lines), task_title


def cmd_list(tasks_path: str, filter_section: Optional[str] = None):
    content = read_file(tasks_path)
    result = parse_tasks(content)

    if filter_section == "active":
        output = {
            "tasks": result["active"],
            "total": result["total_active"],
            "in_progress": len(result["in_progress"]),
            "completed": len(result["completed"]),
        }
    elif filter_section == "backlog":
        output = {
            "tasks": result["backlog"],
            "total": result["total_backlog"],
        }
    else:
        output = {
            "active": result["active"],
            "backlog": result["backlog"],
            "summary": {
                "total_active": result["total_active"],
                "total_backlog": result["total_backlog"],
                "in_progress": len(result["in_progress"]),
                "completed": len(result["completed"]),
            },
        }

    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_show(tasks_path: str, task_id: str):
    content = read_file(tasks_path)
    result = parse_tasks(content)

    all_tasks = result["active"] + result["backlog"]
    found = [t for t in all_tasks if t.get("id") == task_id]

    if not found:
        print(json.dumps({"error": f"Task {task_id} not found"}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(found[0], ensure_ascii=False, indent=2))


def cmd_update(tasks_path: str, task_id: str, new_status: str):
    content = read_file(tasks_path)
    updated = update_task_status(content, task_id, new_status)

    if not updated:
        print(json.dumps({"error": f"Task {task_id} not found"}, ensure_ascii=False))
        sys.exit(1)

    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "task_id": task_id,
                "new_status": new_status,
                "message": f"Status of {task_id} updated to: {new_status}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_add(
    tasks_path: str,
    title: str,
    plan_path: str = "—",
    section: str = "active",
    note: str = "",
):
    content = read_file(tasks_path)
    updated, new_id = add_task(content, title, plan_path, section, note)
    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "task_id": new_id,
                "title": title,
                "section": section,
                "message": f"Task {new_id} added to {section}: {title}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_archive(tasks_path: str, task_id: str):
    content = read_file(tasks_path)
    updated, title = archive_task(content, task_id)

    if not updated:
        print(json.dumps({"error": f"Task {task_id} not found"}, ensure_ascii=False))
        sys.exit(1)

    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "task_id": task_id,
                "title": title,
                "message": f"Task {task_id} moved to archive",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_next_id(tasks_path: str):
    content = read_file(tasks_path)
    next_id = get_next_id(content)
    print(json.dumps({"next_id": next_id}, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "Specify a command: list, active, backlog, show, update, add, add-backlog, archive, next-id"
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    tasks_path = find_tasks_md()
    command = sys.argv[1]

    if command in ("list", "active", "backlog"):
        filter_map = {"list": None, "active": "active", "backlog": "backlog"}
        cmd_list(tasks_path, filter_map[command])

    elif command == "show":
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {"error": "Specify a task ID: show T-001"}, ensure_ascii=False
                )
            )
            sys.exit(1)
        cmd_show(tasks_path, sys.argv[2])

    elif command == "update":
        if len(sys.argv) < 4:
            print(
                json.dumps(
                    {"error": "Specify ID and status: update T-001 '✅ Done'"},
                    ensure_ascii=False,
                )
            )
            sys.exit(1)
        cmd_update(tasks_path, sys.argv[2], " ".join(sys.argv[3:]))

    elif command == "add":
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {"error": "Specify a title: add 'Title' ['plan.md']"},
                    ensure_ascii=False,
                )
            )
            sys.exit(1)
        title = sys.argv[2]
        plan = sys.argv[3] if len(sys.argv) > 3 else "—"
        cmd_add(tasks_path, title, plan, "active")

    elif command == "add-backlog":
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {
                        "error": "Specify a title: add-backlog 'Title' ['plan.md'] ['Note']"
                    },
                    ensure_ascii=False,
                )
            )
            sys.exit(1)
        title = sys.argv[2]
        plan = sys.argv[3] if len(sys.argv) > 3 else "—"
        note = sys.argv[4] if len(sys.argv) > 4 else ""
        cmd_add(tasks_path, title, plan, "backlog", note)

    elif command == "archive":
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {"error": "Specify a task ID: archive T-001"}, ensure_ascii=False
                )
            )
            sys.exit(1)
        cmd_archive(tasks_path, sys.argv[2])

    elif command == "next-id":
        cmd_next_id(tasks_path)

    else:
        print(
            json.dumps({"error": f"Unknown command: {command}"}, ensure_ascii=False)
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
