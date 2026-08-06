# ai-spec-kit

[Русская версия](./README.ru.md)

A portable pack of slash-commands and skills that bring a **spec-driven
workflow** — `brief → spec → plan → implement → review` — plus a few
productivity utilities (`tasks`, `commit`, `wiki-*`) to any markdown-based
AI CLI: **Claude Code**, **OpenCode**, **Codex**.

> Drop the kit anywhere, run `./install.sh`, get the same set of `/commands`
> and skills in every AI tool you use.

## Why does this exist

Working with an AI coding assistant feels great in the small ("write me a
function") but breaks down at feature scale. Common problems:

- **Lost context between sessions.** You explain the feature, the model
  builds half of it, the next session starts from a blank slate.
- **"Vibe coding."** The model jumps straight to writing code without
  agreeing on what the feature even is, what's in/out of scope, and how
  it should integrate.
- **No paper trail.** A week later nobody (you included) remembers *why*
  you made a particular decision.
- **Different CLI, different muscle memory.** Claude Code, OpenCode and
  Codex all support markdown command/skill files, but each project ends
  up with its own ad-hoc set.

`ai-spec-kit` is a small, opinionated answer:

1. **A repeatable pipeline.** Before the model writes code, you go through
   `brief → spec → plan`. Each step lands in `docs/` as a markdown file,
   so the next session can pick up exactly where the last one stopped.
2. **A task tracker that the AI can read and update.** `TASKS.md` is the
   source of truth for "what's in flight"; the `task-tracker` skill keeps
   it in sync with the IDE's todo panel.
3. **A wiki compiler.** Periodically the kit collapses all your `docs/` (or
   the codebase itself) into a topic-based knowledge base. The next session
   reads the wiki instead of re-scanning 200 files.
4. **One install for any AI CLI.** Same commands work across Claude Code,
   OpenCode and Codex with a single `./install.sh`.

## What it helps with

| You want to… | Without the kit | With the kit |
|---|---|---|
| Start a new project from scratch | Verbal pitch, hope for the best | `/create-brief` — coverage-driven deep interview → `docs/brief/` (brief + decision log + research) |
| Build a non-trivial feature | "Hey can you add auth?" → 600 lines of guessed code | `/create-spec` → `/create-spec-plan` → `/create-spec-implement` (auto-advances through phases) → `/create-spec-review` |
| Pick up after a context reset | Re-explain everything from memory | The AI reads `docs/specs/<feature>.md` + `docs/plans/<feature>.md` and resumes |
| Track what's in flight | Scattered TODOs in code comments | `TASKS.md` parsed by `task-tracker`, in sync with the IDE todo list |
| Onboard a teammate (or a new session) | "Read everything in docs/" | `/wiki-compile` → topic-based wiki with coverage tags |
| Commit | Hand-craft a message | `/commit` — conventional, in your repo's style |

## A typical day

```
Mon  /create-brief        → docs/brief/                 ─ vision, decisions, roadmap
Mon  /create-spec auth    → docs/specs/auth.md          ─ what & why
Tue  /create-spec-plan auth → docs/plans/auth.md        ─ how, phases, checklist
Wed  /create-spec-implement auth   ─ all phases, each one: implement →
                                     validate → self code review → commit
Thu  /create-spec-review auth      ─ what shipped, lessons, archive
Fri  /wiki-compile        → docs/wiki/                  ─ refreshed knowledge base
```

Implementation auto-advances from phase to phase; non-critical review
findings don't block the flow — they land in the plan's **Tech Debt**
ledger as `TD-NNN` entries. Prefer a checkpoint between phases? Add
`--pause`.

Every artefact is plain markdown. Anyone — human or model — can read it,
edit it, grep it, diff it.

## What's inside

### Commands (`commands/`)

| Command | Purpose |
|---|---|
| `/create-brief` | Deep coverage-driven interview → `docs/brief/` folder: brief, interview log, decision log, research. Won't generate until every category is closed. `--fast`, `--update`, `--validate` |
| `/create-spec` | Per-feature spec — *what* and *why*: coverage-scanned interview, testable Given/When/Then criteria, pressure-test menu |
| `/create-spec-plan` | Implementation plan — *how*: phases as independent increments, FR→task traceability, principles gate, Tech Debt ledger |
| `/create-spec-implement` | Executes phases with auto-advance: validate → acceptance criteria → self code review → commit; deviation protocol pauses on plan conflicts (`--pause` between phases) |
| `/create-spec-review` | Retrospective: plan vs reality, Definition-of-Done check, tech-debt harvest to backlog, brief/roadmap sync |
| `/tasks` | Manage `TASKS.md` via the `task-tracker` skill |
| `/commit` | Conventional commit with auto-generated message |
| `/wiki-init`, `/wiki-compile`, `/wiki-search`, `/wiki-query`, … | Build and query a project knowledge wiki |

### Skills (`skills/`)

| Skill | What it does |
|---|---|
| `project-brief` | Brief engine behind `/create-brief`: coverage map with exit criteria, laddering, research loops, per-section elicitation menu, `docs/brief/` folder output. |
| `task-tracker` | Parses and updates `TASKS.md` via `tasks.py`. Keeps the in-IDE todo list in sync. Auto-restores context after compaction. |
| `wiki-compiler` | Compiles documentation/code into a topic-based knowledge wiki with coverage tags and cross-cutting concept articles. |

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
git clone https://github.com/askidmobile/ai-spec-kit.git
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

> Codex doesn't have native slash commands, so we store them as **prompts**
> and append a short pointer to `AGENTS.md` so the agent discovers them on
> session start.

## Make the AI actually suggest these commands

Installing the files makes the commands **available**, but the model still
needs a hint to *prefer* them over ad-hoc code generation. Add a short
section to your `CLAUDE.md` / `AGENTS.md` (project or user-global):

```markdown
## Spec-driven workflow

For non-trivial features, use:
`/create-spec` → `/create-spec-plan` → `/create-spec-implement` → `/create-spec-review`.

For task tracking — `/tasks` (TASKS.md is the source of truth).
For the project knowledge base — `/wiki-compile` and `/wiki-search`.
```

Without this nudge the AI knows the commands exist but may still default
to "just write the code." With it, the model proactively offers to spec
out anything bigger than a one-liner.

On greenfield projects `/create-brief` offers to seed `CLAUDE.md` /
`AGENTS.md` (principles, stack, workflow pointers) automatically as part
of project initialization.

## Using the pipeline

```bash
# 1. Greenfield project — vision and roadmap
/create-brief my-saas-app

# 2. Pick something from the roadmap and spec it
/create-spec auth-with-magic-link

# 3. Plan the implementation
/create-spec-plan auth-with-magic-link

# 4. Execute — runs all phases, committing after each
/create-spec-implement auth-with-magic-link
# (add --pause to stop between phases)

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
# Interactive setup
/wiki-init

# Or copy the example config and edit
cp templates/wiki-compiler.example.json .wiki-compiler.json

# Compile
/wiki-compile
```

The output is a topic-based markdown wiki under `docs/wiki/` (path
configurable), with `INDEX.md`, `topics/`, and `concepts/` directories.
Works equally well for **knowledge mode** (existing markdown notes) and
**codebase mode** (your source tree). Coverage tags per section tell you
which articles to trust vs. when to fall back to raw files.

## Uninstall

```bash
./uninstall.sh                # interactive
./uninstall.sh --target=all --scope=user
./uninstall.sh --target=claude --scope=project --project-dir=.
```

The uninstaller only removes files that came from the kit (matched by
name and symlink target). Your own commands/skills in those directories
are left alone.

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
│   ├── project-brief/
│   │   ├── SKILL.md
│   │   └── templates/
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

## How it works under the hood

The kit is **just markdown + a Python script**. Every command file is a
self-contained system prompt that any markdown-aware AI CLI picks up
automatically once it's in the right directory. Skills are folders with
a `SKILL.md` plus optional scripts/templates.

This means:

- No runtime, no daemon, no plugin API to keep up with.
- Updating the kit = `git pull` in this repo (symlink install) or re-run
  `install.sh --force` (copy install).
- Anyone can edit a command file to fit their team's process — it's just prose.

## FAQ

**Why not just one big "build me a feature" prompt?**
Because the model is great at the *what* and the *how* — but you'll get
much better results if those two phases are forced to be separate
artefacts. The spec ends up shorter, sharper, and reviewable by humans;
the plan stays focused on implementation. When something goes wrong in
phase 4, you go back to the plan, not back to the original prompt.

**Do I need all the commands?**
No. The pipeline is opt-in. `/create-spec` + `/create-spec-implement`
alone is already a big win. `/create-brief` matters only for greenfield;
`/create-spec-review` matters only if you care about lessons learned.

**Does it lock me in to a specific tool?**
No. The kit installs into Claude Code, OpenCode, or Codex (or all three).
The artefacts it produces — `docs/specs/*.md`, `docs/plans/*.md`,
`TASKS.md`, `docs/wiki/` — are plain markdown that any tool, including
plain text editors, can read.

**Where does my `TASKS.md` live?**
Project root. The `tasks.py` script walks upward from `cwd` until it
finds one. Use `templates/TASKS.md` as a starter.

**Does the wiki compiler delete my source files?**
No. It only writes into the configured `output` directory (default
`docs/wiki/`). Source files are read-only to the compiler — see the
safety rule in `skills/wiki-compiler/SKILL.md`.

## Languages

The kit — commands, skills, installer — is in English; the README also
comes in Russian ([README.ru.md](./README.ru.md)). Earlier Russian
variants of the prompts are preserved in git history. PRs for other
languages welcome.

## Credits

- Spec-driven workflow commands originated in a personal
  `~/.claude/commands/` setup.
- `task-tracker` and `wiki-compiler` were extracted from the Yttri
  project and generalised.

## License

[MIT](./LICENSE)
