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
    def test_creates_missing_archive_section(self):
        # Regression: the task used to vanish when no "## ✅ Archived"
        # section existed — popped from Active, written nowhere.
        updated, title = tasks.archive_task(BASE, "T-001")
        self.assertEqual(title, "First task")
        self.assertNotIn("| T-001 |", updated)
        self.assertIn("## ✅ Archived", updated)
        self.assertIn("- First task (T-001)", updated)

    def test_appends_to_existing_dated_section(self):
        today = tasks.date.today().strftime("%Y-%m-%d")
        content = BASE + f"\n## ✅ Archived {today}\n\n- Old task (T-000)\n"
        updated, _ = tasks.archive_task(content, "T-001")
        self.assertEqual(updated.count("## ✅ Archived"), 1)
        self.assertIn("- Old task (T-000)", updated)
        self.assertIn("- First task (T-001)", updated)

    def test_inserts_dated_section_before_plain_header(self):
        content = BASE + "\n## ✅ Archived\n\n<!-- old entries -->\n"
        updated, _ = tasks.archive_task(content, "T-001")
        self.assertIn("- First task (T-001)", updated)

    def test_unknown_id(self):
        self.assertEqual(tasks.archive_task(BASE, "T-999"), ("", ""))


class AddTests(unittest.TestCase):
    def test_add_active(self):
        updated, new_id = tasks.add_task(BASE, "New task", "—")
        self.assertEqual(new_id, "T-002")
        self.assertIn("| T-002 |", updated)

    def test_add_backlog(self):
        updated, new_id = tasks.add_task(BASE, "Idea", "—", "backlog", "someday")
        self.assertIn(f"| {new_id} |", updated)
        self.assertIn("someday", updated)

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


if __name__ == "__main__":
    unittest.main()
