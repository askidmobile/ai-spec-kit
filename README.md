# ai-spec-kit

[Русская версия](./README.ru.md)

A portable pack of commands and skills that bring a **spec-driven workflow**
(`brief → spec → plan → implement → review`) and a few productivity utilities
(`tasks`, `commit`, `wiki-*`) to any markdown-based AI CLI — **Claude Code**,
**OpenCode**, **Codex**.

> Drop the kit anywhere, run `./install.sh`, get the same set of `/commands`
> and skills in every tool you use.

## What's inside

### Commands (`commands/`)

The full pipeline for going from idea to shipped feature:

| Command | Purpose |
|---|---|
| `/create-brief` | High-level project brief (vision, roadmap, stakeholders) |
| `/create-spec` | Per-feature technical spec — *what* and *why*, no implementation detail |
| `/create-spec-plan` | Detailed implementation plan based on the spec — *how* |
| `/create-spec-implement` | Phase-by-phase execution of the plan |
| `/create-spec-review` | Retrospective: plan vs reality, lessons, status updates |
| `/tasks` | Manage `TASKS.md` via the `task-tracker` skill |
| `/commit` | Conventional commit with auto-generated message |
| `/wiki-init`, `/wiki-compile`, `/wiki-search`, … | Build and query a project knowledge wiki |

### Skills (`skills/`)

| Skill | What it does |
|---|---|
| `task-tracker` | Parses and updates `TASKS.md` via `tasks.py`. Keeps the in-IDE todo list in sync. |
| `wiki-compiler` | Compiles documentation/code into a topic-based knowledge wiki (`docs/wiki/`). |

### Templates (`templates/`)

- `TASKS.md` — starter task tracker with the correct table structure
- `wiki-compiler.example.json` — example config for the wiki compiler

## Requirements

- **bash** ≥ 3.2 (macOS default works)
- **Python 3.8+** — only for the `task-tracker` skill
- One of: Claude Code, OpenCode, Codex

## Install

### Interactive (recommended)

```bash
git clone https://github.com/<your-username>/ai-spec-kit.git
cd ai-spec-kit
./install.sh
```

The installer will ask:

1. Which AI CLI: Claude Code / OpenCode / Codex / all three
2. Scope: **user** (`~/.claude/`, `~/.config/opencode/`, `~/.codex/`) or
   **project** (`<your-project>/.claude/`, etc.)
3. Symlinks (recommended — `git pull` here updates all targets) or copies

### Non-interactive

```bash
# Globally, into all three tools, using symlinks
./install.sh --target=all --scope=user

# Just Claude Code into the current project
./install.sh --target=claude --scope=project --project-dir=.

# OpenCode + Codex, copies instead of symlinks
./install.sh --target=opencode,codex --scope=user --copy

# Preview without changing anything
./install.sh --target=all --scope=user --dry-run
```

### Where files end up

| CLI | User scope | Project scope |
|---|---|---|
| Claude Code | `~/.claude/{commands,skills}/` | `.claude/{commands,skills}/` |
| OpenCode | `~/.config/opencode/{commands,skills}/` | `.opencode/{commands,skills}/` |
| Codex | `~/.codex/{prompts,skills}/` + line in `~/.codex/AGENTS.md` | `.codex/{prompts,skills}/` + line in `./AGENTS.md` |

> Codex doesn't have native slash commands, so we store them as **prompts** and
> append a short pointer to `AGENTS.md` so the agent discovers them on session start.

## Using the pipeline

```bash
# 1. Greenfield project — vision and roadmap
/create-brief my-saas-app

# 2. Pick something from the roadmap and spec it
/create-spec auth-with-magic-link

# 3. Plan the implementation
/create-spec-plan auth-with-magic-link

# 4. Execute phase by phase
/create-spec-implement auth-with-magic-link
# (repeat per phase)

# 5. Retrospective when done
/create-spec-review auth-with-magic-link
```

### Tasks

```bash
/tasks                          # show active tasks
/tasks add "Fix login bug" "docs/plans/fix-login.md"
/tasks update T-001 "🔄 In progress"
/tasks archive T-001
```

If `TASKS.md` doesn't exist yet:

```bash
cp templates/TASKS.md ./TASKS.md
```

### Wiki

```bash
# One-time setup (interactive)
/wiki-init

# Or copy the example config and edit
cp templates/wiki-compiler.example.json .wiki-compiler.json

# Compile
/wiki-compile
```

The output is a topic-based markdown wiki under `docs/wiki/` (path configurable),
with `INDEX.md`, `topics/`, and `concepts/` directories. Works equally well for
**knowledge mode** (existing markdown notes) and **codebase mode** (your source tree).

## Uninstall

```bash
./uninstall.sh                # interactive
./uninstall.sh --target=all --scope=user
./uninstall.sh --target=claude --scope=project --project-dir=.
```

The uninstaller only removes files that came from the kit (matched by name
and symlink target). Your own commands/skills in those directories are left alone.

## Layout

```
ai-spec-kit/
├── README.md / README.ru.md
├── LICENSE
├── install.sh / uninstall.sh
├── commands/                  # markdown command definitions
│   ├── create-brief.md
│   ├── create-spec.md
│   ├── create-spec-plan.md
│   ├── create-spec-implement.md
│   ├── create-spec-review.md
│   ├── tasks.md
│   ├── commit.md
│   └── wiki-*.md
├── skills/
│   ├── task-tracker/
│   │   ├── SKILL.md
│   │   └── scripts/tasks.py
│   └── wiki-compiler/
│       ├── SKILL.md
│       ├── templates/
│       └── visualize/
└── templates/
    ├── TASKS.md
    └── wiki-compiler.example.json
```

## How it works

The kit is **just markdown + a Python script**. Every command file is a
self-contained system prompt that any markdown-aware AI CLI will pick up
automatically once it's in the right directory. Skills are folders with a
`SKILL.md` plus optional scripts/templates.

This means:

- No runtime, no daemon, no plugin API to keep up with.
- Updating the kit = `git pull` in this repo (symlink install) or re-run
  `install.sh --force` (copy install).
- Anyone can edit a command file to fit their team's process — it's just prose.

## Languages

The command prompts inside this kit are written in **Russian** (the original
author works in Russian). They still work fine in English-speaking sessions —
the AI follows the structure regardless of prompt language. Feel free to
translate any command file; PRs welcome.

## Credits

- Spec-driven workflow commands originated in a personal `~/.claude/commands/` setup.
- `task-tracker` and `wiki-compiler` were extracted from the
  [Yttri](https://github.com/Yttri-app) project and generalised.

## License

[MIT](./LICENSE)
