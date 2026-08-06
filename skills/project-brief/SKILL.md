---
name: project-brief
description: >-
  Coverage-driven project brief engine. Deep-interviews the user until every
  category is closed, then generates a docs/brief/ folder — main brief, full
  interview log, decision log, research notes. Called by /create-brief.
  Also activates on: "plan a new project", "project vision", "давай спланируем
  проект", "help me think through this product idea".
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
  - TodoWrite
  - AskUserQuestion
  - WebSearch
  - WebFetch
---

# Project Brief Engine

Mission: extract the **maximum** from the user's head — what they think, how
they see it, what they know but haven't said — and turn it into a durable
foundation for the whole project. Coach, don't quiz. The ideas come from the
user; you bring structure, pushback, and memory.

File templates for every output live in `templates/` in this skill's directory.

---

## Output: the brief is a folder

```
docs/brief/
├── PROJECT-BRIEF.md      # main document, 2-4 pages, links to everything below
├── interview-log.md      # full Q&A journal — nothing the user said is lost
├── decisions.md          # BD-NNN decision log, grows for the project's life
├── open-questions.md     # consciously deferred questions only
├── research.md           # research-loop findings (analogs, tech comparisons)
└── details/              # created ONLY when a topic outgrows the main doc:
    personas.md, competitors.md, user-journeys.md, ...
```

The main document stays short and readable; the extracted depth is never lost —
it lives in the companion files, linked from the main one.

**Legacy:** if a single-file `docs/PROJECT-BRIEF.md` exists, offer to migrate it
into `docs/brief/` (move content, split decisions/open questions into their
files) before doing anything else.

---

## Hard rules

1. **Never generate documents until every relevant coverage category is ✅
   closed or explicitly deferred by the user** (deferred → `open-questions.md`
   with rationale). This is the core of the skill. No exceptions for "seems
   like enough".
2. **Never write after 3-5 questions.** Minimum 2 questions per relevant
   category. At least one research loop for any non-trivial project.
3. **Nothing is lost.** Everything meaningful the user says lands in
   `interview-log.md`. Every decision lands in `decisions.md` as BD-NNN.
4. **Push back on thin answers.** "Basic login" is not an answer until "basic"
   is defined. "Everyone" is not a target audience.
5. **Ease off on fatigue.** Short answers, "let's move on", visible irritation —
   drop laddering, batch the remaining gaps, offer Fast mode.
6. **One AskUserQuestion call = one question** (`questions` array of length 1),
   2-4 options plus the automatic "Other"; recommended option first with
   `(Recommended)`; `description` states the trade-off of each option.

---

## Phase 0: Recon (SILENT)

1. `docs/brief/` exists → **Update mode** (see below). Single-file
   `docs/PROJECT-BRIEF.md` exists → offer migration.
2. Existing codebase? Stack markers, README, docs/ — read what's there; the
   brief must document reality, not fantasy.
3. `--validate` argument → **Validate mode**. `--fast` → note Fast pace for
   Phase 2. Date via `date +%Y-%m-%d`.

## Phase 1: Brain dump

Open with free-form extraction, not questions:

> "Tell me about the project the way you see it — stream of thought, any order,
> any length. And share anything that already exists: notes, README, chat
> transcripts, links, competitor products you admire or hate."

- Read every material the user points to. Extract selectively into the
  coverage map (below) — mark which categories the dump already touched.
- Then always: **"What else? What did you think about at night but haven't
  written anywhere?"** — one more pass surfaces what structured questions miss.
- Log the dump's essence into `interview-log.md` (create the folder on first
  write).

**Raw idea?** If the user has a fuzzy one-liner and visibly hasn't thought it
through — offer a short brainstorm before interviewing (Phase 1.5). Otherwise
skip 1.5.

## Phase 1.5: Brainstorm (optional)

Coach mode, 3-5 rounds max. Ideas must come from the user — facilitate, don't
generate for them. Rotate probes: *"What if the main constraint disappeared?"*,
*"What existing product is this most like, and what's the one difference?"*,
*"Describe the day of a person whose problem is solved."* Capture everything
in `interview-log.md`, then continue to Phase 2.

## Phase 2: Pace selection

Ask via AskUserQuestion:

- **Interview (Recommended)** — one question at a time, full depth, laddering
  and pushback. Best foundation.
- **Fast** — remaining gaps batched into 2-3 grouped messages; the draft is
  generated with `[ASSUMPTION]` tags where answers were thin; every assumption
  is listed by name at approval. The coverage gate still applies.

---

## Phase 3: Coverage-driven interview

### Coverage map

Pick relevant categories by project type; ✅ requires the exit criterion, not
just "was asked about".

| # | Category | Closed when… | Relevant for |
|---|----------|--------------|--------------|
| C1 | Problem & motivation | Pain named; who feels it; how they cope today; cost of the status quo | all |
| C2 | Users | ≥1 concrete persona with a job-to-be-done — not "everyone" | all |
| C3 | Solution vision | User described the core scenario in their own words; echo-back confirmed | all |
| C4 | Differentiation | Answer to "why won't they just use existing X?" | all |
| C5 | Scope (v1) | Every capability tagged Must/Should/Out; each Must survived "is MVP dead without it?" | all |
| C6 | Data & privacy | What's stored, where from, who owns it; PII / compliance named or ruled out | backend, web, mobile, full-stack |
| C7 | Integrations | External systems listed; failure behavior for each critical one | backend, web, mobile, automation |
| C8 | Scale & load | Order of magnitude of users/requests; read- vs write-heavy | backend, web, full-stack |
| C9 | Security & roles | Who can do what; how users authenticate | all except pure CLI/library |
| C10 | Constraints | Timeline, budget, team, stack preferences, platform limits | all |
| C11 | Success criteria | ≥2 measurable MVP criteria | all |
| C12 | Risks | ≥2 top risks with mitigation (mini pre-mortem counts) | all |

CLI tools and libraries: C6-C9 shrink to "ergonomics / API surface /
versioning" questions — adapt, don't skip thinking.

### Tracker

Keep internal state per category: ✅ closed / 🔶 touched but thin / ⬜ untouched.
After each category (or each batch in Fast mode) show compact progress:

```
Coverage: 7/12 ✅  [C1 ✅ C2 ✅ C3 ✅ C4 🔶 C5 ✅ C6 ⬜ …]
```

The 🔶 list is your work queue. Generation is blocked while any relevant
category is not ✅ or explicitly deferred.

### Extraction techniques (apply throughout)

- **Laddering / 5 Whys**: on every key answer ask "why does that matter?"
  until you reach a motivation, not a feature. Stop at motivation; stop earlier
  on fatigue signals.
- **Echo-back**: at the end of each category, restate what you understood in
  your own words and get an explicit "yes, that's it" (or a correction — log it).
- **"What else?"**: close each category with "what didn't I ask about here
  that I should have?"
- **Research loop**: on a knowledge-gap signal, offer:
  *"Want me to research the options before we decide?"* → WebSearch/WebFetch →
  summarize findings in plain language into `research.md` → return with
  informed options, not open questions.
- **Conflict surfacing**: when two wishes contradict, name the trade-off
  explicitly and make the user choose (or defer consciously).

### Knowledge-gap signals

| Signal | Reaction |
|--------|----------|
| "I think…", "maybe…", "probably" | Probe deeper; offer research |
| "Just a simple/basic X" | Define what simple means concretely |
| Technology buzzword without context | Ask what they expect it to do; educate if needed |
| "Whatever is standard" | Explain there's no universal standard; give 2-3 options with trade-offs |
| "That sounds good" to your suggestion | Verify they understand the implications |
| Describes a solution instead of a problem | Ladder back up: "what problem does that solve?" |

### Typical conflicts to watch for

"Simple AND feature-rich" · "Real-time AND cheap infra" · "Secure AND
frictionless" · "Flexible AND performant" · "Fast to build AND future-proof" ·
"Offline-first AND always-fresh data"

---

## Phase 4: Draft + elicitation menu (per section)

Draft `PROJECT-BRIEF.md` section by section from the interview material
(template: `templates/PROJECT-BRIEF.md`; sections are advisory — merge or drop
for small projects, then renumber the remaining ones sequentially, no gaps;
use mermaid only where a diagram genuinely clarifies).

After showing each drafted section, offer an elicitation menu — 3-4 methods
picked for that section from the catalog:

```
Section "Scope (v1)" drafted above. Pressure-test it?
  1. Pre-mortem — "the MVP failed 6 months in. Why?"
  2. Subtraction — which Must feature could we cut to ship twice as fast?
  3. Stakeholder rotation — reread scope as the payer / the end user / support
  x. Looks right — next section
```

Loop: apply chosen method → show findings → user confirms what to change →
re-offer the menu → `x` moves on. In Fast mode run the menu only for **Scope**
and **Risks** (highest-value sections).

### Elicitation catalog

| Method | Essence | Best for |
|--------|---------|----------|
| 5 Whys / laddering | Drill from feature to motivation | Problem, Users |
| Pre-mortem | "It failed — why?" then work backwards | Scope, Risks, Roadmap |
| Inversion | "What would guarantee failure?" | Risks, Principles |
| Red team | Attack the section as a hostile skeptic | Differentiation, Architecture |
| Stakeholder rotation | Reread as payer / user / support / ops | Scope, Users, Success |
| What-if scenarios | Remove a constraint, double the load, change the market | Architecture, Vision |
| Subtraction | Improve by removing, not adding | Scope |
| SCAMPER (lite) | Substitute / combine / adapt / eliminate passes | Solution, Scope |
| First principles | Strip assumptions, rebuild from fundamentals | Architecture, Differentiation |
| Feynman | Explain it to a smart 12-year-old | Executive summary, Vision |
| Assumption audit | List assumptions, rate confidence × impact | whole brief, before approval |
| Second-order thinking | "And what happens after that succeeds?" | Vision, Roadmap |

---

## Phase 5: Completeness gate + generation

1. **Gate** (SILENT): every relevant category ✅ or deferred with rationale;
   every `[ASSUMPTION]` (Fast mode) either confirmed or listed for approval;
   no conflict left unresolved-and-unlogged. Anything failing → back to
   Phase 3, tell the user what's still open and why it matters.
2. Generate the folder from `templates/`: `PROJECT-BRIEF.md` (with links to
   companions), `decisions.md` (all BD-NNN from the interview),
   `open-questions.md`, `research.md` (if loops ran), finalize
   `interview-log.md`. Create `details/*` only for topics that outgrew the
   main doc (many personas, deep competitor analysis, long user journeys).
3. `PROJECT-BRIEF.md` targets 2-4 pages. Overflow goes to `details/`, never
   deleted.
4. **Language**: write all output files in the language the user spoke during
   the interview (templates are English scaffolding, not a language mandate).

## Phase 6: Approval

Show a summary: vision in one sentence, coverage recap (N categories closed,
M deferred), decisions count, assumptions (Fast mode) by name, top risks.
Then: **"Brief is ready. Accept, or want changes?"** After acceptance show the
pipeline pointer:

```
✅ Brief saved: docs/brief/

  ✅ /create-brief → docs/brief/ (vision + decisions + roadmap) ← YOU ARE HERE
  ⬜ /create-spec <feature>       (per roadmap item)
  ⬜ /create-spec-plan → /create-spec-implement → /create-spec-review
```

Greenfield: offer to initialize the project skeleton — only after confirmation:

- `docs/specs/`, `docs/plans/`, `.gitignore` for the chosen stack
- `README.md` seeded from the brief (pitch, stack, status)
- **`CLAUDE.md` + `AGENTS.md`** seeded from the brief, so every future AI
  session starts with the right context: one-line pitch, the Principles
  section, stack, pointers to `docs/brief/PROJECT-BRIEF.md` and
  `docs/brief/decisions.md` as binding context, and the pipeline nudge
  (`/create-spec` → `/create-spec-plan` → `/create-spec-implement` →
  `/create-spec-review`, `/tasks` for tracking). Make `AGENTS.md` a short
  pointer to `CLAUDE.md` (single source, no divergence).

---

## Update mode

When `docs/brief/` already exists:

1. Read `PROJECT-BRIEF.md`, `decisions.md`, the tail of `interview-log.md`.
2. Ask what changed (new insight, market shift, pivot, scope pressure).
3. Interview only the affected categories — same techniques, same gate.
4. Conflicts with existing BD-NNN decisions are called out explicitly; a
   reversal becomes a new BD row marked "overrides BD-XXX", never an edit of
   history.
5. Bump the version in `PROJECT-BRIEF.md`, append the session to
   `interview-log.md` under a new date heading.

## Validate mode

Honest critique of an existing brief against its own stated goals — not
against taste:

1. Read the full folder first (including log and decisions — context matters).
2. Per section: is it concrete enough to act on? Is anything asserted without
   having been asked? Do scope, success criteria and roadmap agree with each
   other? Cite specific sections when criticizing.
3. Deliverable: a short findings list (❗ blocking / ⚠️ weak / ✅ solid per
   section) — then offer to roll fixes into an Update session.
