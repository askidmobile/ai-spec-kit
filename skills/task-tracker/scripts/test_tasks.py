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
        updated, legacy = tasks.extract_sections(content, tasks.ARCHIVE_HEADER)
        self.assertNotIn("Архивировано", updated)
        self.assertNotIn("## ✅", updated)
        self.assertIn("| T-001 |", updated)  # active table untouched
        self.assertIn("- Old (T-000)", legacy)
        self.assertIn("- Older (T-000)", legacy)

    def test_nothing_to_migrate(self):
        _, legacy = tasks.extract_sections(BASE, tasks.ARCHIVE_HEADER)
        self.assertEqual(legacy, "")


ARCHIVE = """# Archived tasks

> Intro line.

## ✅ Archived 2026-08-12

| T-003 | 2026-08-12 | This year | — | ✅ Done |

## ✅ Архивировано 2025-11-02

| T-002 | 2025-11-02 | Last year | — | ✅ Done |

## ✅ Archived 2024-01-09

| T-001 | 2024-01-09 | Ancient | — | ✅ Done |
"""


class RotateTests(unittest.TestCase):
    def test_splits_past_years_out(self):
        kept, moved = tasks.split_archive_by_year(ARCHIVE, "2026")
        self.assertEqual(sorted(moved), ["2024", "2025"])
        self.assertIn("| T-003 |", kept)
        self.assertNotIn("| T-002 |", kept)
        self.assertIn("# Archived tasks", kept)  # intro survives
        self.assertIn("| T-002 |", moved["2025"])
        # Localized headings rotate too — the date is what matters.
        self.assertIn("Архивировано", moved["2025"])

    def test_undated_section_stays(self):
        content = "# Archived tasks\n\n## ✅ Archived\n\n- No date here\n"
        kept, moved = tasks.split_archive_by_year(content, "2026")
        self.assertEqual(moved, {})
        self.assertIn("No date here", kept)

    def test_nothing_to_rotate_when_single_year(self):
        kept, moved = tasks.split_archive_by_year(ARCHIVE, "2024")
        self.assertEqual(sorted(moved), ["2025", "2026"])
        self.assertEqual(tasks.stale_archive_years(ARCHIVE, "2020"), ["2024", "2025", "2026"])
        self.assertIn("| T-001 |", kept)

    def test_year_file_gets_intro_and_keeps_existing(self):
        _, moved = tasks.split_archive_by_year(ARCHIVE, "2026")
        first = tasks.year_archive("", moved["2025"], "2025")
        self.assertIn("# Archived tasks — 2025", first)
        self.assertIn("| T-002 |", first)
        # A second rotation into the same year must not drop what's there.
        again = tasks.year_archive(first, "## ✅ Archived 2025-01-01\n\n| T-000 | … |", "2025")
        self.assertIn("| T-002 |", again)
        self.assertIn("| T-000 |", again)
        self.assertEqual(again.count("# Archived tasks — 2025"), 1)


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


class BacklogSplitTests(unittest.TestCase):
    def test_section_moves_out_whole(self):
        kept, section = tasks.extract_sections(BASE, tasks.BACKLOG_HEADER)
        self.assertNotIn("📦", kept)
        self.assertIn("| T-001 |", kept)  # Active untouched
        self.assertTrue(section.startswith("## 📦 Backlog"))
        self.assertIn("| ID | Date | Task | Plan | Note |", section)

    def test_parsed_from_the_other_file(self):
        kept, section = tasks.extract_sections(BASE, tasks.BACKLOG_HEADER)
        external = section + "\n| T-009 | 2026-08-01 | Someday | — | maybe |\n"
        parsed = tasks.parse_tasks(kept, external)
        self.assertEqual(parsed["total_active"], 1)
        self.assertEqual([t["id"] for t in parsed["backlog"]], ["T-009"])
        self.assertEqual(parsed["backlog"][0]["note"], "maybe")

    def test_localized_backlog_heading_moves(self):
        content = BASE.replace("## 📦 Backlog", "## 📦 Backlog (Future)")
        _, section = tasks.extract_sections(content, tasks.BACKLOG_HEADER)
        self.assertIn("(Future)", section)


class PromoteTests(unittest.TestCase):
    def test_note_column_becomes_status(self):
        row = "| T-009 | 2026-08-01 | Someday | [`p.md`](docs/p.md) | maybe later |"
        promoted = tasks.promote_row(row)
        self.assertIn("| T-009 |", promoted)
        self.assertIn("[`p.md`](docs/p.md)", promoted)  # plan link kept
        self.assertIn("📝 Planning", promoted)
        self.assertNotIn("maybe later", promoted)

    def test_short_row_is_padded(self):
        # Backlog rows often leave the Note cell off entirely.
        promoted = tasks.promote_row("| T-009 | 2026-08-01 | Someday | — |")
        self.assertEqual(len(tasks.parse_table_row(promoted)), 5)

    def test_row_lands_in_the_active_table(self):
        kept, section = tasks.extract_sections(BASE, tasks.BACKLOG_HEADER)
        external = section + "\n| T-009 | 2026-08-01 | Someday | — | maybe |\n"
        stripped, rows, found = tasks.pop_task_rows(external, ["T-009"])
        self.assertEqual(found, ["T-009"])
        updated = tasks.insert_row(kept, tasks.promote_row(rows[0]), tasks.ACTIVE_SECTION)
        parsed = tasks.parse_tasks(updated, stripped)
        self.assertEqual([t["id"] for t in parsed["active"]], ["T-001", "T-009"])
        self.assertEqual(parsed["active"][1]["status"], "📝 Planning")
        self.assertEqual(parsed["backlog"], [])


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
