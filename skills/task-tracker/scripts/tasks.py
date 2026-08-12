#!/usr/bin/env python3
"""
Parser and manager for TASKS.md.

Reads markdown tables, returns JSON. Updates statuses, adds and archives tasks.

Completed tasks move out to TASKS_ARCHIVE.md (next to TASKS.md) so the
working file stays small.

Usage:
    python3 tasks.py list                          # All tasks (active + backlog)
    python3 tasks.py active                        # Active only
    python3 tasks.py backlog                       # Backlog only
    python3 tasks.py show T-001                    # Task details
    python3 tasks.py update T-001 "✅ Done"        # Update status
    python3 tasks.py add "Title" "path.md"         # Add to Active
    python3 tasks.py add-backlog "Title" "path.md" "Note"
    python3 tasks.py archive T-001 [T-002 ...]     # Move to TASKS_ARCHIVE.md
    python3 tasks.py archive-done                  # Archive every ✅ Done task
    python3 tasks.py migrate-archive               # Move in-file archive sections out
    python3 tasks.py rotate-archive                # Split past years into TASKS_ARCHIVE_YYYY.md
    python3 tasks.py next-id                       # Next free ID
"""

from __future__ import annotations

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


ARCHIVE_NAME = "TASKS_ARCHIVE.md"

# Overflow limits — past these the working file is too big to keep in context
# comfortably, and `archive-done` should be offered.
MAX_ACTIVE_ROWS = 40
MAX_DONE_ROWS = 10
MAX_BYTES = 100_000


def archive_md_path(tasks_path: str, year: str = "") -> str:
    """TASKS_ARCHIVE.md (or a rotated TASKS_ARCHIVE_YYYY.md) next to TASKS.md."""
    name = f"TASKS_ARCHIVE_{year}.md" if year else ARCHIVE_NAME
    return os.path.join(os.path.dirname(os.path.abspath(tasks_path)), name)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_archive(tasks_path: str) -> str:
    """The current archive only — what `archive` appends to."""
    path = archive_md_path(tasks_path)
    return read_file(path) if os.path.isfile(path) else ""


def read_archive_all(tasks_path: str) -> str:
    """Current archive plus every rotated year — the full ID history."""
    folder = os.path.dirname(os.path.abspath(tasks_path))
    names = sorted(
        f
        for f in os.listdir(folder)
        if f.startswith("TASKS_ARCHIVE") and f.endswith(".md")
    )
    return "\n".join(read_file(os.path.join(folder, f)) for f in names)


def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def esc_cell(s: str) -> str:
    """Escape pipes so user text can't break the table structure."""
    return s.replace("|", "\\|")


def parse_table_row(row: str) -> list[str]:
    """Parse a markdown table row into a list of cells (unescapes \\|)."""
    cells = re.split(r"(?<!\\)\|", row.strip().strip("|"))
    return [c.strip().replace("\\|", "|") for c in cells]


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
    # Sections are matched by their emoji only — the heading text is free-form
    # and often localized ("## 🚀 Активные задачи").
    _, active_rows, _, _ = parse_section(content, ACTIVE_SECTION)

    _, backlog_rows, _, _ = parse_section(content, BACKLOG_SECTION)

    def row_to_task(row: list[str], section: str) -> dict:
        # Columns are read by position, not by header name: the layout is fixed
        # (and assumed by add_task/update_task_status), while header text is
        # free-form and localized in real projects ("Задача", "Статус").
        cell = lambda i: row[i] if i < len(row) else ""
        plan = cell(3)
        link = re.search(r"\[.*?\]\((.*?)\)", plan)
        task = {
            "section": section,
            "id": cell(0),
            "date": cell(1),
            "title": cell(2),
            "plan": plan,
            "plan_path": link.group(1) if link else "",
        }
        # Last column is Status in Active, Note in Backlog.
        task["status" if section == "active" else "note"] = cell(4)
        return task

    active = [row_to_task(r, "active") for r in active_rows]
    backlog = [row_to_task(r, "backlog") for r in backlog_rows]

    return {
        "active": active,
        "backlog": backlog,
        "total_active": len(active),
        "total_backlog": len(backlog),
        "in_progress": [t for t in active if "🔄" in t.get("status", "")],
        "completed": [t for t in active if "✅" in t.get("status", "")],
    }


def get_next_id(content: str, archive_content: str = "") -> str:
    """Find the next free ID.

    The archive must be scanned too — once a task moves to TASKS_ARCHIVE.md its
    ID is gone from TASKS.md, and ignoring it would hand out a duplicate.
    """
    ids = re.findall(r"T-(\d+)", content + "\n" + archive_content)
    if not ids:
        return "T-001"
    max_id = max(int(i) for i in ids)
    return f"T-{max_id + 1:03d}"


ACTIVE_HEADER = "## 🚀"
BACKLOG_HEADER = "## 📦"
ARCHIVE_HEADER = "## ✅"
ACTIVE_SECTION = r"^##\s+🚀"
BACKLOG_SECTION = r"^##\s+📦"


def update_task_status(
    content: str, task_id: str, new_status: str
) -> tuple[str, str]:
    """Update an Active task's status by ID.

    Returns (status, content) where status is one of:
      "updated"    — status column updated, content is the new file text
      "not_found"  — no row with this task_id, content is ""
      "backlog"    — task lives in Backlog (no Status column), content is ""
    """
    lines = content.split("\n")
    current_section = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Track which section we're inside.
        if stripped.startswith(ACTIVE_HEADER):
            current_section = "active"
            continue
        if stripped.startswith(BACKLOG_HEADER):
            current_section = "backlog"
            continue
        # A new ## section outside both ends the active/backlog context.
        if stripped.startswith("## ") and current_section in ("active", "backlog"):
            current_section = None
            continue

        if f"| {task_id} |" in line or f"| {task_id.strip()} |" in line:
            if current_section == "backlog":
                return "backlog", ""
            if current_section != "active":
                continue
            cells = parse_table_row(line)
            # Active: ID | Date | Task | Plan | Status (index 4).
            if len(cells) >= 5:
                cells[4] = new_status
                lines[i] = "| " + " | ".join(esc_cell(c) for c in cells) + " |"
                return "updated", "\n".join(lines)

    return "not_found", ""


def add_task(
    content: str,
    title: str,
    plan_path: str,
    section: str = "active",
    note: str = "",
    archive_content: str = "",
) -> tuple[str, str]:
    """Add a new task to the given section."""
    next_id = get_next_id(content, archive_content)
    today = date.today().strftime("%Y-%m-%d")
    title = esc_cell(title)
    note = esc_cell(note)

    if plan_path and plan_path != "—":
        plan_name = os.path.basename(plan_path)
        plan_cell = f"[`{plan_name}`]({plan_path})"
    else:
        plan_cell = "—"

    if section == "active":
        new_row = f"| {next_id} | {today} | {title} | {plan_cell} | 📝 Planning |"
        pattern = ACTIVE_SECTION
    else:
        note_text = note if note else ""
        new_row = f"| {next_id} | {today} | {title} | {plan_cell} | {note_text} |"
        pattern = BACKLOG_SECTION

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

    if last_table_row < 1:
        # Section (or its table) not found — report failure instead of
        # silently returning the file unchanged.
        return "", ""
    lines.insert(last_table_row + 1, new_row)

    return "\n".join(lines), next_id


ARCHIVE_INTRO = (
    "# Archived tasks\n"
    "\n"
    "> Written by the `task-tracker` skill (`tasks.py archive` / `archive-done`).\n"
    "> Append-only, newest section on top. Active work lives in `TASKS.md`.\n"
)
ARCHIVE_TABLE = ["| ID | Date | Task | Plan | Status |", "|----|------|------|------|--------|"]


def pop_task_rows(content: str, task_ids: list[str]) -> tuple[str, list[str], list[str]]:
    """Cut the table rows of the given IDs out of TASKS.md.

    Returns (content_without_rows, rows, found_ids). Rows are returned verbatim
    so nothing (plan link, status, note) is lost on the way to the archive.
    """
    wanted = set(task_ids)
    kept: list[str] = []
    rows: list[str] = []
    found: list[str] = []

    for line in content.split("\n"):
        if line.strip().startswith("|"):
            cells = parse_table_row(line)
            if cells and cells[0] in wanted:
                rows.append(line.strip())
                found.append(cells[0])
                continue
        kept.append(line)

    return "\n".join(kept), rows, found


def append_to_archive(archive_content: str, rows: list[str]) -> str:
    """Insert rows into today's section of TASKS_ARCHIVE.md, creating what's missing."""
    today = date.today().strftime("%Y-%m-%d")
    header = f"## ✅ Archived {today}"

    if not archive_content.strip():
        archive_content = ARCHIVE_INTRO
    lines = archive_content.rstrip("\n").split("\n")

    idx = next((i for i, l in enumerate(lines) if l.strip() == header), -1)
    if idx < 0:
        # New dated section goes above the previous ones — newest first.
        at = next(
            (i for i, l in enumerate(lines) if l.strip().startswith("## ")), len(lines)
        )
        lines[at:at] = ["", header, "", *ARCHIVE_TABLE, *rows, ""]
    else:
        # Existing section — append after its last row, before the blank tail.
        at = idx + 1
        while at < len(lines) and not lines[at].strip().startswith("## "):
            at += 1
        while at > idx and lines[at - 1].strip() == "":
            at -= 1
        lines[at:at] = rows

    return "\n".join(lines).strip("\n") + "\n"


SECTION_DATE = re.compile(r"(\d{4})-\d{2}-\d{2}")


def split_archive_by_year(archive_content: str, keep_year: str) -> tuple[str, dict[str, str]]:
    """Split the archive into (kept_text, {year: text}) by section date.

    The intro and any section without a parseable date stay put — rotation
    must never guess where undated content belongs.
    """
    head: list[str] = []
    kept: list[str] = []
    moved: dict[str, list[str]] = {}
    section: Optional[list[str]] = None
    year: Optional[str] = None

    def flush():
        if section is None:
            return
        text = "\n".join(section).strip("\n")
        if year and year != keep_year:
            moved.setdefault(year, []).append(text)
        else:
            kept.append(text)

    for line in archive_content.split("\n"):
        if line.strip().startswith(ARCHIVE_HEADER):
            flush()
            found = SECTION_DATE.search(line)
            year = found.group(1) if found else None
            section = [line]
            continue
        (section if section is not None else head).append(line)
    flush()

    head_text = "\n".join(head).strip("\n")
    parts = [p for p in [head_text, *kept] if p]
    return "\n\n".join(parts) + "\n", {y: "\n\n".join(s) for y, s in moved.items()}


def year_archive(existing: str, sections: str, year: str) -> str:
    """Put rotated sections at the top of TASKS_ARCHIVE_YYYY.md, under its intro."""
    if not existing.strip():
        existing = (
            f"# Archived tasks — {year}\n"
            f"\n"
            f"> Rotated out of `{ARCHIVE_NAME}` by `tasks.py rotate-archive`.\n"
        )
    lines = existing.rstrip("\n").split("\n")
    at = next((i for i, l in enumerate(lines) if l.strip().startswith("## ")), len(lines))
    lines[at:at] = ["", *sections.split("\n"), ""]
    return "\n".join(lines).strip("\n") + "\n"


def stale_archive_years(archive_content: str, keep_year: str) -> list[str]:
    """Years sitting in TASKS_ARCHIVE.md that rotation would move out."""
    return sorted(split_archive_by_year(archive_content, keep_year)[1])


def extract_legacy_archive(content: str) -> tuple[str, str]:
    """Cut every '## ✅ …' section out of TASKS.md (the old in-file archive).

    Matches on the emoji alone — heading text is localized in real projects
    ("## ✅ Архивировано 2026-08-01").
    """
    kept: list[str] = []
    moved: list[str] = []
    in_archive = False

    for line in content.split("\n"):
        if line.strip().startswith("## "):
            in_archive = line.strip().startswith(ARCHIVE_HEADER)
        (moved if in_archive else kept).append(line)

    return "\n".join(kept).rstrip("\n") + "\n", "\n".join(moved).strip("\n")


def overflow_report(content: str, parsed: dict) -> dict:
    """How close TASKS.md is to being unmanageably large."""
    active = parsed["total_active"]
    done = len(parsed["completed"])
    size = len(content.encode("utf-8"))
    report = {
        "active_rows": active,
        "done_rows": done,
        "bytes": size,
        "over_limit": (
            active > MAX_ACTIVE_ROWS or done > MAX_DONE_ROWS or size > MAX_BYTES
        ),
    }
    if report["over_limit"]:
        size_note = f"{active} active rows, {done} done, {size // 1024} KB"
        report["hint"] = (
            f"TASKS.md is overflowing ({size_note}) — run `tasks.py archive-done` "
            f"to move ✅ tasks into {ARCHIVE_NAME}"
            if done
            # Nothing is done — archive-done would be a no-op, so don't send
            # the agent there; the rows themselves need triage.
            else f"TASKS.md is overflowing ({size_note}) and nothing is ✅ — "
            f"review the active rows: close, split, or drop to Backlog"
        )
    return report


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

    if filter_section != "backlog":
        output["overflow"] = overflow_report(content, result)
        archive = read_archive(tasks_path)
        if archive:
            stale = stale_archive_years(archive, date.today().strftime("%Y"))
            output["archive"] = {
                "file": ARCHIVE_NAME,
                "bytes": len(archive.encode("utf-8")),
                "stale_years": stale,
            }
            if stale:
                output["archive"]["hint"] = (
                    f"{ARCHIVE_NAME} still holds {', '.join(stale)} — run "
                    f"`tasks.py rotate-archive` to split past years into "
                    f"TASKS_ARCHIVE_YYYY.md"
                )

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
    result, updated = update_task_status(content, task_id, new_status)

    if result == "backlog":
        print(
            json.dumps(
                {
                    "error": (
                        f"{task_id} is in Backlog, which has no Status column "
                        f"(its last column is Note). Move it to Active first "
                        f"or edit the Note directly."
                    )
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)
    if result == "not_found":
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
    updated, new_id = add_task(
        content, title, plan_path, section, note, read_archive_all(tasks_path)
    )
    if not updated:
        header = "## 🚀 Active tasks" if section == "active" else "## 📦 Backlog"
        print(
            json.dumps(
                {
                    "error": (
                        f"Section '{header}' (with its table) not found in "
                        f"TASKS.md — copy the structure from templates/TASKS.md"
                    )
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)
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


def cmd_archive(tasks_path: str, task_ids: list[str]):
    content = read_file(tasks_path)
    updated, rows, found = pop_task_rows(content, task_ids)

    missing = [t for t in task_ids if t not in found]
    if not found:
        print(
            json.dumps(
                {"error": f"Task(s) not found: {', '.join(missing)}"},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    write_file(archive_md_path(tasks_path), append_to_archive(read_archive(tasks_path), rows))
    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "archived": found,
                "not_found": missing,
                "archive_file": ARCHIVE_NAME,
                "message": f"Moved {len(found)} task(s) to {ARCHIVE_NAME}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_archive_done(tasks_path: str):
    """Overflow relief: every ✅ task in Active goes to the archive file."""
    content = read_file(tasks_path)
    done_ids = [t["id"] for t in parse_tasks(content)["completed"]]

    if not done_ids:
        print(
            json.dumps(
                {"success": True, "archived": [], "message": "No ✅ tasks to archive"},
                ensure_ascii=False,
            )
        )
        return

    cmd_archive(tasks_path, done_ids)


def cmd_migrate_archive(tasks_path: str):
    """One-shot: pull the old in-file '## ✅ …' sections out into TASKS_ARCHIVE.md."""
    content = read_file(tasks_path)
    updated, legacy = extract_legacy_archive(content)

    if not legacy.strip():
        print(
            json.dumps(
                {"success": True, "moved_sections": 0, "message": "Nothing to migrate"},
                ensure_ascii=False,
            )
        )
        return

    archive = read_archive(tasks_path) or ARCHIVE_INTRO
    write_file(archive_md_path(tasks_path), archive.rstrip("\n") + "\n\n" + legacy + "\n")
    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "moved_sections": legacy.count("\n" + ARCHIVE_HEADER)
                + legacy.startswith(ARCHIVE_HEADER),
                "moved_lines": legacy.count("\n") + 1,
                "archive_file": ARCHIVE_NAME,
                "message": f"In-file archive moved to {ARCHIVE_NAME}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_rotate_archive(tasks_path: str):
    """Keep TASKS_ARCHIVE.md to the current year; older years get their own file."""
    archive = read_archive(tasks_path)
    this_year = date.today().strftime("%Y")
    kept, by_year = split_archive_by_year(archive, this_year)

    if not by_year:
        print(
            json.dumps(
                {"success": True, "rotated": {}, "message": "Nothing to rotate"},
                ensure_ascii=False,
            )
        )
        return

    written = {}
    for year, sections in sorted(by_year.items()):
        path = archive_md_path(tasks_path, year)
        existing = read_file(path) if os.path.isfile(path) else ""
        write_file(path, year_archive(existing, sections, year))
        written[year] = os.path.basename(path)

    write_file(archive_md_path(tasks_path), kept)
    print(
        json.dumps(
            {
                "success": True,
                "rotated": written,
                "message": f"Moved {len(written)} year(s) out of {ARCHIVE_NAME}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_next_id(tasks_path: str):
    content = read_file(tasks_path)
    next_id = get_next_id(content, read_archive_all(tasks_path))
    print(json.dumps({"next_id": next_id}, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "Specify a command: list, active, backlog, show, update, add, add-backlog, archive, archive-done, migrate-archive, rotate-archive, next-id"
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
                    {"error": "Specify a task ID: archive T-001 [T-002 ...]"},
                    ensure_ascii=False,
                )
            )
            sys.exit(1)
        cmd_archive(tasks_path, sys.argv[2:])

    elif command == "archive-done":
        cmd_archive_done(tasks_path)

    elif command == "migrate-archive":
        cmd_migrate_archive(tasks_path)

    elif command == "rotate-archive":
        cmd_rotate_archive(tasks_path)

    elif command == "next-id":
        cmd_next_id(tasks_path)

    else:
        print(
            json.dumps({"error": f"Unknown command: {command}"}, ensure_ascii=False)
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
