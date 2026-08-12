#!/usr/bin/env python3
"""Smoke tests for tasks.py. Run: python3 test_tasks.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks

BASE = """# Project tasks

## 🚀 Active tasks

| ID | Date | Task | Plan | Status |
|----|------|------|------|--------|
| T-001 | 2026-08-01 | First task | — | 📝 Planning |

## 📦 Backlog

| ID | Date | Task | Plan | Note |
|----|------|------|------|------|
"""


class ArchiveTests(unittest.TestCase):
    def test_row_leaves_tasks_md_verbatim(self):
        updated, rows, found = tasks.pop_task_rows(BASE, ["T-001"])
        self.assertEqual(found, ["T-001"])
        self.assertNotIn("| T-001 |", updated)
        # The whole row travels — plan link and status included, no data loss.
        self.assertIn("First task", rows[0])
        self.assertIn("📝 Planning", rows[0])

    def test_creates_archive_body_when_file_missing(self):
        _, rows, _ = tasks.pop_task_rows(BASE, ["T-001"])
        archive = tasks.append_to_archive("", rows)
        self.assertIn("# Archived tasks", archive)
        self.assertIn("## ✅ Archived", archive)
        self.assertIn("| ID | Date | Task | Plan | Status |", archive)
        self.assertIn("| T-001 |", archive)

    def test_appends_to_existing_dated_section(self):
        _, rows, _ = tasks.pop_task_rows(BASE, ["T-001"])
        archive = tasks.append_to_archive(tasks.append_to_archive("", rows), rows)
        self.assertEqual(archive.count("## ✅ Archived"), 1)
        self.assertEqual(archive.count("| T-001 |"), 2)

    def test_new_section_goes_on_top(self):
        old = "# Archived tasks\n\n## ✅ Archived 2020-01-01\n\n- Ancient (T-000)\n"
        _, rows, _ = tasks.pop_task_rows(BASE, ["T-001"])
        archive = tasks.append_to_archive(old, rows)
        self.assertLess(
            archive.index("| T-001 |"), archive.index("## ✅ Archived 2020-01-01")
        )

    def test_unknown_id(self):
        updated, rows, found = tasks.pop_task_rows(BASE, ["T-999"])
        self.assertEqual((rows, found), ([], []))
        self.assertEqual(updated, BASE)

    def test_archive_done_selects_only_completed(self):
        content = BASE.replace(
            "| T-001 | 2026-08-01 | First task | — | 📝 Planning |",
            "| T-001 | 2026-08-01 | First task | — | 📝 Planning |\n"
            "| T-002 | 2026-08-01 | Shipped | — | ✅ Done |\n"
            "| T-003 | 2026-08-01 | Running | — | 🔄 In progress |",
        )
        done = [t["id"] for t in tasks.parse_tasks(content)["completed"]]
        self.assertEqual(done, ["T-002"])


class LegacyMigrationTests(unittest.TestCase):
    def test_moves_localized_in_file_sections(self):
        content = (
            BASE
            + "\n## ✅ Архивировано 2026-08-01\n\n- Old (T-000)\n"
            + "\n## ✅ Archived 2026-07-01\n\n- Older (T-000)\n"
        )
        updated, legacy = tasks.extract_legacy_archive(content)
        self.assertNotIn("Архивировано", updated)
        self.assertNotIn("## ✅", updated)
        self.assertIn("| T-001 |", updated)  # active table untouched
        self.assertIn("- Old (T-000)", legacy)
        self.assertIn("- Older (T-000)", legacy)

    def test_nothing_to_migrate(self):
        _, legacy = tasks.extract_legacy_archive(BASE)
        self.assertEqual(legacy, "")


class OverflowTests(unittest.TestCase):
    def test_quiet_when_small(self):
        report = tasks.overflow_report(BASE, tasks.parse_tasks(BASE))
        self.assertFalse(report["over_limit"])
        self.assertNotIn("hint", report)

    def test_flags_too_many_done(self):
        rows = "\n".join(
            f"| T-{i:03d} | 2026-08-01 | Task {i} | — | ✅ Done |"
            for i in range(2, 2 + tasks.MAX_DONE_ROWS + 1)
        )
        content = BASE.replace(
            "| T-001 | 2026-08-01 | First task | — | 📝 Planning |",
            "| T-001 | 2026-08-01 | First task | — | 📝 Planning |\n" + rows,
        )
        report = tasks.overflow_report(content, tasks.parse_tasks(content))
        self.assertTrue(report["over_limit"])
        self.assertIn("archive-done", report["hint"])


class LocalizedHeadingTests(unittest.TestCase):
    def test_russian_headings_and_columns_parse(self):
        # Regression: sections and columns were matched by English text, so a
        # localized TASKS.md parsed as empty (or status-less) and overflow /
        # archive-done could never see a single ✅ task.
        content = (
            BASE.replace("## 🚀 Active tasks", "## 🚀 Активные задачи")
            .replace("## 📦 Backlog", "## 📦 Бэклог (Future)")
            .replace("| ID | Date | Task | Plan | Status |", "| ID | Дата | Задача | План | Статус |")
            .replace("| 📝 Planning |", "| ✅ Реализовано 2026-08-11 |")
        )
        parsed = tasks.parse_tasks(content)
        self.assertEqual(parsed["total_active"], 1)
        self.assertEqual(parsed["active"][0]["title"], "First task")
        self.assertEqual([t["id"] for t in parsed["completed"]], ["T-001"])
        updated, new_id = tasks.add_task(content, "Новая", "—")
        self.assertIn(f"| {new_id} |", updated)


class AddTests(unittest.TestCase):
    def test_add_active(self):
        updated, new_id = tasks.add_task(BASE, "New task", "—")
        self.assertEqual(new_id, "T-002")
        self.assertIn("| T-002 |", updated)

    def test_add_backlog(self):
        updated, new_id = tasks.add_task(BASE, "Idea", "—", "backlog", "someday")
        self.assertIn(f"| {new_id} |", updated)
        self.assertIn("someday", updated)

    def test_pipe_in_title_survives_round_trip(self):
        # Regression: a "|" in user text used to break the table into
        # extra cells, shifting columns on the next read/update.
        updated, new_id = tasks.add_task(BASE, "Fix a | b", "—")
        self.assertIn("Fix a \\| b", updated)
        task = [t for t in tasks.parse_tasks(updated)["active"] if t["id"] == new_id][0]
        self.assertEqual(task["title"], "Fix a | b")
        self.assertEqual(task["status"], "📝 Planning")

        status, updated2 = tasks.update_task_status(updated, new_id, "✅ Done")
        self.assertEqual(status, "updated")
        task = [t for t in tasks.parse_tasks(updated2)["active"] if t["id"] == new_id][0]
        self.assertEqual(task["title"], "Fix a | b")
        self.assertEqual(task["status"], "✅ Done")

    def test_missing_section_fails(self):
        # Regression: used to report success while inserting nothing.
        no_backlog = (
            "# Tasks\n\n## 🚀 Active tasks\n\n"
            "| ID | Date | Task | Plan | Status |\n|----|------|------|------|--------|\n"
        )
        self.assertEqual(tasks.add_task(no_backlog, "Idea", "—", "backlog"), ("", ""))


class UpdateTests(unittest.TestCase):
    def test_update_status(self):
        status, updated = tasks.update_task_status(BASE, "T-001", "🔄 In progress")
        self.assertEqual(status, "updated")
        self.assertIn("| 🔄 In progress |", updated)

    def test_backlog_task_rejected(self):
        content = BASE.replace(
            "|----|------|------|------|------|",
            "|----|------|------|------|------|\n| T-002 | 2026-08-01 | Someday | — | note |",
        )
        self.assertEqual(tasks.update_task_status(content, "T-002", "x")[0], "backlog")

    def test_unknown_id(self):
        self.assertEqual(tasks.update_task_status(BASE, "T-999", "x")[0], "not_found")


class NextIdTests(unittest.TestCase):
    def test_next_id(self):
        self.assertEqual(tasks.get_next_id(BASE), "T-002")
        self.assertEqual(tasks.get_next_id("# empty\n"), "T-001")

    def test_archived_ids_are_not_reused(self):
        # Regression: IDs live on in TASKS_ARCHIVE.md after archiving; ignoring
        # that file hands out an ID that already exists.
        archive = "# Archived tasks\n\n| T-042 | 2026-08-01 | Old | — | ✅ Done |\n"
        self.assertEqual(tasks.get_next_id(BASE, archive), "T-043")


if __name__ == "__main__":
    unittest.main()
