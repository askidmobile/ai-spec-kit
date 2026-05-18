#!/usr/bin/env python3
"""
Парсер и менеджер задач для TASKS.md.
Читает markdown-таблицы, возвращает JSON.
Обновляет статусы, добавляет и архивирует задачи.

Использование:
    python3 tasks.py list                          # Все задачи (active + backlog)
    python3 tasks.py active                        # Только активные
    python3 tasks.py backlog                       # Только backlog
    python3 tasks.py show T-001                    # Детали задачи
    python3 tasks.py update T-001 "✅ Готово"      # Обновить статус
    python3 tasks.py add "Название" "path.md"      # Добавить задачу в Active
    python3 tasks.py add-backlog "Название" "path.md" "Примечание"
    python3 tasks.py archive T-001                 # Переместить в архив
    python3 tasks.py next-id                       # Показать следующий свободный ID
"""

import json
import re
import sys
import os
from datetime import date
from typing import Optional


def find_tasks_md() -> str:
    """Находит TASKS.md — ищет от текущей директории вверх."""
    current = os.getcwd()
    while True:
        candidate = os.path.join(current, "TASKS.md")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    # Фоллбэк: рядом со скриптом
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Поднимаемся: scripts/ -> task-tracker/ -> skills/ -> .claude/ -> корень
    root = os.path.normpath(os.path.join(script_dir, "..", "..", "..", ".."))
    candidate = os.path.join(root, "TASKS.md")
    if os.path.isfile(candidate):
        return candidate
    print(json.dumps({"error": "TASKS.md не найден"}))
    sys.exit(1)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def parse_table_row(row: str) -> list[str]:
    """Парсит строку markdown-таблицы в список ячеек."""
    cells = row.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def parse_section(
    content: str, header_pattern: str
) -> tuple[list[str], list[list[str]], int, int]:
    """
    Парсит секцию таблицы из markdown.
    Возвращает: (заголовки, строки_данных, start_line_index, end_line_index)
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
            # Новая секция ## — конец текущей
            if stripped.startswith("## ") and table_started:
                end_idx = i
                break

            # Строка таблицы
            if stripped.startswith("|"):
                if not table_started:
                    # Первая строка — заголовки
                    headers = parse_table_row(stripped)
                    table_started = True
                    start_idx = i
                    continue
                elif not separator_skipped:
                    # Вторая строка — разделитель (|---|---|)
                    separator_skipped = True
                    continue
                else:
                    # Строки данных
                    row = parse_table_row(stripped)
                    rows.append(row)
                    end_idx = i + 1
            elif table_started and stripped == "":
                # Пустая строка после таблицы — конец
                end_idx = i
                break

    return headers, rows, start_idx, end_idx


def parse_tasks(content: str) -> dict:
    """Парсит все секции TASKS.md."""
    # Активные задачи
    active_headers, active_rows, _, _ = parse_section(
        content, r"^##\s+🚀\s+Активные задачи"
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
            elif key == "дата":
                task["date"] = val
            elif key == "задача":
                task["title"] = val
            elif key == "план":
                task["plan"] = val
                # Извлекаем путь из markdown ссылки
                link_match = re.search(r"\[.*?\]\((.*?)\)", val)
                task["plan_path"] = link_match.group(1) if link_match else ""
            elif key == "статус":
                task["status"] = val
            elif key == "примечание":
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
    """Находит следующий свободный ID."""
    ids = re.findall(r"T-(\d+)", content)
    if not ids:
        return "T-001"
    max_id = max(int(i) for i in ids)
    return f"T-{max_id + 1:03d}"


def update_task_status(content: str, task_id: str, new_status: str) -> str:
    """Обновляет статус задачи по ID."""
    lines = content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if f"| {task_id} |" in line or f"| {task_id.strip()} |" in line:
            cells = parse_table_row(line)
            # Определяем секцию по количеству колонок и наличию "Статус"
            # Active: ID | Дата | Задача | План | Статус
            # Backlog: ID | Дата | Задача | План | Примечание
            # Статус — последняя колонка в Active (индекс 4)
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
    """Добавляет новую задачу в указанную секцию."""
    next_id = get_next_id(content)
    today = date.today().strftime("%Y-%m-%d")

    if plan_path and plan_path != "—":
        plan_name = os.path.basename(plan_path)
        plan_cell = f"[`{plan_name}`]({plan_path})"
    else:
        plan_cell = "—"

    if section == "active":
        new_row = f"| {next_id} | {today} | {title} | {plan_cell} | 📝 Планирование |"
        # Ищем конец таблицы активных задач
        pattern = r"^##\s+🚀\s+Активные задачи"
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
    """Перемещает задачу из Active в архив текущей даты."""
    # Находим задачу
    lines = content.split("\n")
    task_line = None
    task_line_idx = -1
    task_title = ""

    for i, line in enumerate(lines):
        if f"| {task_id} |" in line:
            cells = parse_table_row(line)
            if len(cells) >= 4:
                task_title = cells[2]  # Задача
                task_line = line
                task_line_idx = i
            break

    if task_line_idx < 0:
        return "", ""

    # Удаляем строку из таблицы
    lines.pop(task_line_idx)

    # Находим или создаём секцию архива с текущей датой
    today = date.today().strftime("%Y-%m-%d")
    archive_header = f"## ✅ Архивировано {today}"

    # Ищем существующую секцию архива с этой датой
    archive_idx = -1
    for i, line in enumerate(lines):
        if archive_header in line:
            archive_idx = i
            break

    if archive_idx < 0:
        # Ищем первую секцию "✅ Архивировано" и вставляем перед ней
        for i, line in enumerate(lines):
            if line.strip().startswith("## ✅ Архивировано"):
                archive_idx = i
                # Вставляем новую секцию перед существующей
                archive_entry = f"\n{archive_header}\n\n- {task_title} ({task_id})\n"
                lines.insert(archive_idx, archive_entry)
                break

    else:
        # Секция уже есть — добавляем запись после заголовка
        # Ищем конец списка в этой секции
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
        print(json.dumps({"error": f"Задача {task_id} не найдена"}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(found[0], ensure_ascii=False, indent=2))


def cmd_update(tasks_path: str, task_id: str, new_status: str):
    content = read_file(tasks_path)
    updated = update_task_status(content, task_id, new_status)

    if not updated:
        print(json.dumps({"error": f"Задача {task_id} не найдена"}, ensure_ascii=False))
        sys.exit(1)

    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "task_id": task_id,
                "new_status": new_status,
                "message": f"Статус {task_id} обновлён на: {new_status}",
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
                "message": f"Задача {new_id} добавлена в {section}: {title}",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_archive(tasks_path: str, task_id: str):
    content = read_file(tasks_path)
    updated, title = archive_task(content, task_id)

    if not updated:
        print(json.dumps({"error": f"Задача {task_id} не найдена"}, ensure_ascii=False))
        sys.exit(1)

    write_file(tasks_path, updated)
    print(
        json.dumps(
            {
                "success": True,
                "task_id": task_id,
                "title": title,
                "message": f"Задача {task_id} перемещена в архив",
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
                    "error": "Укажите команду: list, active, backlog, show, update, add, add-backlog, archive, next-id"
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
                    {"error": "Укажите ID задачи: show T-001"}, ensure_ascii=False
                )
            )
            sys.exit(1)
        cmd_show(tasks_path, sys.argv[2])

    elif command == "update":
        if len(sys.argv) < 4:
            print(
                json.dumps(
                    {"error": "Укажите ID и статус: update T-001 '✅ Готово'"},
                    ensure_ascii=False,
                )
            )
            sys.exit(1)
        cmd_update(tasks_path, sys.argv[2], " ".join(sys.argv[3:]))

    elif command == "add":
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {"error": "Укажите название: add 'Название' ['plan.md']"},
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
                        "error": "Укажите название: add-backlog 'Название' ['plan.md'] ['Примечание']"
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
                    {"error": "Укажите ID задачи: archive T-001"}, ensure_ascii=False
                )
            )
            sys.exit(1)
        cmd_archive(tasks_path, sys.argv[2])

    elif command == "next-id":
        cmd_next_id(tasks_path)

    else:
        print(
            json.dumps({"error": f"Неизвестная команда: {command}"}, ensure_ascii=False)
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
