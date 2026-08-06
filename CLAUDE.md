# ai-spec-kit — contributor notes

A portable pack of slash-commands and skills for Claude Code / OpenCode /
Codex. Everything is markdown prompts plus one Python script — no build step.

## Layout

- `commands/*.md` — slash-command definitions. Self-contained prompts with
  `description` / `argument-hint` frontmatter. Edit them as prose.
- `skills/*/SKILL.md` — skills. `task-tracker/scripts/tasks.py` is the only
  executable code in the kit (plus the zero-dependency
  `wiki-compiler/visualize/server.js`).
- `templates/` — starter files users copy into their projects.
- `install.sh` / `uninstall.sh` — symlink or copy the above into CLI config
  directories (see README for the target matrix).

## Rules

- Kit content is English. `README.ru.md` mirrors `README.md` — update both.
- Keep commands CLI-agnostic: no Claude-only variables like
  `${CLAUDE_PLUGIN_ROOT}`. For paths into installed skills use the
  `<SKILL_DIR>` placeholder, defined where it's used.
- `tasks.py`: stdlib only, Python 3.8+ (keep
  `from __future__ import annotations`).
- Tests: `python3 skills/task-tracker/scripts/test_tasks.py` must pass; add a
  case when changing tasks.py parsing. CI also runs `bash -n` on the shell
  scripts.
- Check installer changes with
  `./install.sh --target=all --scope=user --dry-run`.
