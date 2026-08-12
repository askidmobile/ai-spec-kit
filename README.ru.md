# ai-spec-kit

[English version](./README.md)

Переносимый набор slash-команд и скилов, который приносит **spec-driven
workflow** — `brief → spec → plan → implement → review` — плюс несколько
полезных утилит (`tasks`, `commit`, `wiki-*`) в любой markdown-совместимый
AI CLI: **Claude Code**, **OpenCode**, **Codex**, **Warp**.

> Положи пакет куда угодно, запусти `./install.sh` — получишь одинаковый
> набор `/команд` и скилов во всех своих AI-инструментах.

## Зачем это нужно

Работа с AI-ассистентом приятна на мелких задачах ("напиши функцию") и
ломается на масштабе фичи. Типовые проблемы:

- **Контекст теряется между сессиями.** Объяснил фичу, модель сделала
  половину, следующая сессия начинается с чистого листа.
- **«Vibe coding».** Модель сразу пишет код, не согласовав, что это
  вообще за фича, что в scope, а что нет, и как она интегрируется.
- **Нет бумажного следа.** Через неделю никто (включая тебя) не помнит,
  *почему* было принято такое-то решение.
- **Разные CLI — разная мышечная память.** Claude Code, OpenCode и
  Codex поддерживают markdown-команды и скилы, но в каждом проекте свой
  костыльный набор.

`ai-spec-kit` — небольшой opinionated ответ:

1. **Повторяемый пайплайн.** До того как модель пишет код, проходим
   `brief → spec → plan`. Каждый шаг ложится в `docs/` markdown-файлом,
   и следующая сессия подхватывает с того места, где остановилась.
2. **Трекер задач, который AI читает и обновляет.** `TASKS.md` — источник
   правды по «что в работе»; скил `task-tracker` держит его в синхроне
   с todo-панелью IDE.
3. **Компилятор wiki.** Периодически пакет схлопывает весь `docs/` (или
   сам исходный код) в topic-based базу знаний. Следующая сессия читает
   wiki вместо повторного сканирования 200 файлов.
4. **Одна установка под любой AI CLI.** Те же команды работают в Claude
   Code, OpenCode, Codex и Warp — один `./install.sh`.

## Чем именно помогает

| Хочется… | Без пакета | С пакетом |
|---|---|---|
| Стартовать новый проект | На словах, надеясь на лучшее | `/create-brief` — глубокое интервью с картой покрытия → `docs/brief/` (бриф + журнал решений + ресёрч) |
| Сделать нетривиальную фичу | "Добавь авторизацию" → 600 строк нагаданного кода | `/create-spec` → `/create-spec-plan` → `/create-spec-implement` (авто-проход по фазам) → `/create-spec-review` |
| Продолжить после сброса контекста | Пересказывать всё по памяти | AI читает `docs/specs/<feature>.md` + `docs/plans/<feature>.md` и продолжает |
| Отслеживать что в работе | TODO разбросаны по комментариям | `TASKS.md` парсится `task-tracker`, синхронизирован с todo-листом IDE |
| Онбордить коллегу (или новую сессию) | «Прочти всё в docs/» | `/wiki-compile` → topic-based wiki с coverage-тегами |
| Коммитить | Руками сочинять сообщение | `/commit` — conventional, в стиле твоего репо |

## Типичный день

```
Пн  /create-brief         → docs/brief/                ─ видение, решения, roadmap
Пн  /create-spec auth     → docs/specs/auth.md         ─ что и зачем
Вт  /create-spec-plan auth → docs/plans/auth.md        ─ как, фазы, чеклист
Ср  /create-spec-implement auth   ─ все фазы, каждая: реализация →
                                    валидация → self code review → commit
Чт  /create-spec-review auth      ─ что отгружено, уроки, архив
Пт  /wiki-compile         → docs/wiki/                 ─ обновлённая база знаний
```

Реализация сама переходит от фазы к фазе; некритичные замечания ревью
не останавливают поток — они записываются в секцию **Tech Debt** плана
как `TD-NNN`. Нужна контрольная точка между фазами — добавь `--pause`.

Каждый артефакт — обычный markdown. Любой (человек или модель) может его
прочесть, отредактировать, грепнуть, дифнуть.

## Что внутри

### Команды (`commands/`)

| Команда | Назначение |
|---|---|
| `/create-brief` | Глубокое интервью с картой покрытия → папка `docs/brief/`: бриф, журнал интервью, журнал решений, ресёрч. Не генерирует, пока не закрыты все категории. `--fast`, `--update`, `--validate` |
| `/create-spec` | Спека фичи — *что* и *зачем*: скан покрытия, проверяемые Given/When/Then критерии, pressure-test меню |
| `/create-spec-plan` | План — *как*: фазы как независимые инкременты, трассируемость FR→задачи, гейт принципов, реестр Tech Debt |
| `/create-spec-implement` | Реализация фаз с авто-продвижением: валидация → критерии приёмки → self code review → commit; протокол отклонений останавливает поток при конфликте с планом (`--pause` — пауза между фазами) |
| `/create-spec-review` | Ретроспектива: план vs реальность, проверка Definition of Done, сбор техдолга в бэклог, синк брифа/roadmap |
| `/tasks` | Управление `TASKS.md` через скил `task-tracker` |
| `/commit` | Conventional commit с автогенерируемым сообщением |
| `/wiki-init`, `/wiki-compile`, `/wiki-search`, `/wiki-query`, … | Сборка и поиск по wiki проекта |

### Скилы (`skills/`)

| Скил | Что делает |
|---|---|
| `project-brief` | Движок брифа за `/create-brief`: карта покрытия с критериями закрытия, laddering, research-петли, elicitation-меню по секциям, вывод в папку `docs/brief/`. |
| `task-tracker` | Парсит и обновляет `TASKS.md` через `tasks.py`. Синхронизирует с IDE-todo. Восстанавливает контекст после сжатия. |
| `wiki-compiler` | Компилирует документацию/код в topic-based wiki с coverage-тегами и cross-cutting concept-статьями. |

> **Warp:** у Warp нет директории для slash-команд — он загружает только
> скилы. Поэтому для каждой команды из `commands/` пакет генерирует
> skill-обёртку (`skills/<name>/SKILL.md`), которую Warp вызывает как
> `/<name>`. Скрипт `scripts/generate-skills.sh` обновляет их после правки
> `commands/*.md`.

### Шаблоны (`templates/`)

- `TASKS.md` — стартовый трекер с правильной структурой таблиц (архивный
  `TASKS_ARCHIVE.md` и `TASKS_BACKLOG.md` создаются по требованию командами
  `/tasks archive` и `/tasks split-backlog`)
- `wiki-compiler.example.json` — пример конфигурации wiki-компилятора

## Требования

- **bash** ≥ 3.2 (стандартный macOS подходит)
- **Python 3.8+** — только для скила `task-tracker`
- **Node.js** — только для `wiki-visualize` (визуализация графа wiki)
- Один из: Claude Code, OpenCode, Codex, Warp

## Установка

### Интерактивно (рекомендуется)

```bash
git clone https://github.com/askidmobile/ai-spec-kit.git
cd ai-spec-kit
./install.sh
```

Скрипт спросит:

1. В какой AI CLI: Claude Code / OpenCode / Codex / Warp / все четыре
2. Scope: **user** (`~/.claude/`, `~/.config/opencode/`, `~/.codex/`,
   `~/.warp/`) или **project** (`<твой-проект>/.claude/`, и т.д.)
3. Симлинки (рекомендуется — `git pull` здесь обновляет все цели) или копии

### Без интерактива

```bash
# Глобально во все три CLI симлинками
./install.sh --target=all --scope=user

# Только Claude Code в текущий проект
./install.sh --target=claude --scope=project --project-dir=.

# OpenCode + Codex, копированием вместо симлинков
./install.sh --target=opencode,codex --scope=user --copy

# Предпросмотр без изменений
./install.sh --target=all --scope=user --dry-run
```

### Куда что попадает

| CLI | User scope | Project scope |
|---|---|---|
| Claude Code | `~/.claude/{commands,skills}/` | `.claude/{commands,skills}/` |
| OpenCode | `~/.config/opencode/{commands,skills}/` | `.opencode/{commands,skills}/` |
| Codex | `~/.codex/{prompts,skills}/` + строка в `~/.codex/AGENTS.md` | `.codex/{prompts,skills}/` + строка в `./AGENTS.md` |
| Warp | `~/.warp/skills/` (только скилы) | `.warp/skills/` (только скилы) |
| Antigravity (Gemini) | `~/.gemini/config/skills/` | `.gemini/config/skills/` |

> У Codex нет slash-команд, поэтому они кладутся как **prompts**, плюс
> в `AGENTS.md` добавляется короткая ссылка — агент находит их сам при
> старте сессии.
>
> У Warp нет директории slash-команд — он сканирует только `skills/`.
> Поэтому инсталлер ставит туда skill-обёртки, сгенерированные из
> `commands/*.md` скриптом `scripts/generate-skills.sh`. Вызываются через
> `/<skill-name>` (например `/commit`, `/wiki-search`).

## Как заставить AI реально предлагать эти команды

Установка кладёт файлы в правильные директории — команды становятся
**доступны**. Но модели нужен короткий намёк, чтобы она *предпочитала*
их генерации кода с нуля. Добавь блок в свой `CLAUDE.md` / `AGENTS.md`
(проектный или глобальный):

```markdown
## Spec-driven workflow

Для нетривиальных фич используй:
`/create-spec` → `/create-spec-plan` → `/create-spec-implement` → `/create-spec-review`.

Для отслеживания задач — `/tasks` (TASKS.md — источник правды).
Для базы знаний проекта — `/wiki-compile` и `/wiki-search`.
```

Без этой подсказки AI знает, что команды существуют, но всё равно может
по умолчанию «просто написать код». С подсказкой модель проактивно
предлагает заспекать всё, что больше однострочника.

В greenfield-проектах `/create-brief` сам предлагает создать `CLAUDE.md` /
`AGENTS.md` (принципы, стек, указатели на workflow) при инициализации
структуры проекта.

## Использование пайплайна

```bash
# 1. Greenfield проект — видение и roadmap
/create-brief my-saas-app

# 2. Выбрал элемент из roadmap → спека
/create-spec auth-with-magic-link

# 3. План реализации
/create-spec-plan auth-with-magic-link

# 4. Реализация — все фазы подряд, коммит после каждой
/create-spec-implement auth-with-magic-link
# (--pause — останавливаться между фазами)

# 5. Ретроспектива по завершении
/create-spec-review auth-with-magic-link
```

### Задачи

```bash
/tasks                          # активные задачи
/tasks add "Починить логин" "docs/plans/fix-login.md"
/tasks update T-001 "🔄 В работе"
/tasks archive T-001             # строка уезжает в TASKS_ARCHIVE.md
/tasks archive-done              # все ✅ задачи разом
```

`TASKS.md` попадает в контекст каждую сессию, поэтому обязан оставаться
небольшим. `/tasks` сообщает о переполнении (40+ активных строк, 10+
завершённых или 100 КБ) и предлагает `archive-done`; завершённые задачи живут
в `TASKS_ARCHIVE.md`, который создаётся при первом архивировании. Со сменой
года `/tasks rotate-archive` разносит прошлые годы по `TASKS_ARCHIVE_YYYY.md`,
чтобы ни один файл не рос бесконечно. `/tasks split-backlog` делает то же с
бэклогом — «когда-нибудь»-задачами, которые сегодня в контексте не нужны, —
а `/tasks promote T-XXX` возвращает задачу в активные. Для проекта,
заведённого раньше: `/tasks migrate-archive` разово выносит старые секции
`## ✅ …` из самого файла.

Если `TASKS.md` ещё нет:

```bash
cp templates/TASKS.md ./TASKS.md
```

### Wiki

```bash
# Интерактивная настройка
/wiki-init

# Или скопируй пример конфига и поправь под себя
cp templates/wiki-compiler.example.json .wiki-compiler.json

# Сборка
/wiki-compile
```

Результат — topic-based markdown wiki в `docs/wiki/` (путь
конфигурируется), с `INDEX.md`, `topics/` и `concepts/`. Работает и для
**knowledge mode** (markdown-заметки), и для **codebase mode** (исходники).
Coverage-теги в каждой секции подсказывают, какой статье можно верить
без оглядки на сырые файлы, а какую лучше перечитать.

## Удаление

```bash
./uninstall.sh                # интерактивно
./uninstall.sh --target=all --scope=user
./uninstall.sh --target=claude --scope=project --project-dir=.
```

Деинсталлер удаляет только то, что было поставлено из пакета (по имени
файла и таргету симлинка). Твои собственные команды/скилы в этих
директориях не трогает.

## Структура

```
ai-spec-kit/
├── README.md / README.ru.md
├── LICENSE
├── install.sh / uninstall.sh
├── scripts/
│   └── generate-skills.sh    # генератор skill-обёрток из commands/*.md
├── commands/                  # markdown-файлы команд
│   ├── create-brief.md
│   ├── create-spec.md
│   ├── create-spec-plan.md
│   ├── create-spec-implement.md
│   ├── create-spec-review.md
│   ├── tasks.md
│   ├── commit.md
│   └── wiki-*.md
├── skills/                    # core skills + skill-обёртки для Warp
│   ├── project-brief/
│   │   ├── SKILL.md
│   │   └── templates/
│   ├── task-tracker/
│   │   ├── SKILL.md
│   │   └── scripts/tasks.py
│   ├── wiki-compiler/
│   │   ├── SKILL.md
│   │   ├── templates/
│   │   └── visualize/
│   ├── commit/                # обёртка над commands/commit.md
│   ├── wiki-search/           # обёртка над commands/wiki-search.md
│   └── …                      # и т.д. для каждой команды
└── templates/
    ├── TASKS.md
    └── wiki-compiler.example.json
```

## Как это устроено

Весь пакет — **markdown + один Python-скрипт**. Каждый файл команды —
самодостаточный системный промпт, который любой markdown-совместимый AI
CLI подхватывает автоматически, как только он оказался в нужной
директории. Скилы — папки с `SKILL.md` плюс опциональные
скрипты/шаблоны.

Следствия:

- Нет рантайма, демона или плагинного API.
- Обновление пакета = `git pull` в этом репо (для симлинков) или
  `install.sh --force` (для копий).
- Любую команду можно поправить под свой процесс — это просто текст.

## FAQ

**Почему не один большой промпт «сделай фичу»?**
Потому что модель хороша и в *что*, и в *как* — но результат заметно
лучше, если эти две фазы разнесены в отдельные артефакты. Спека
выходит короче и острее, её можно ревьюить людьми; план остаётся
сфокусирован на реализации. Когда на 4-й фазе что-то идёт не так — ты
возвращаешься к плану, а не к исходному промпту.

**Нужны ли все команды?**
Нет. Пайплайн opt-in. `/create-spec` + `/create-spec-implement` —
уже большая победа. `/create-brief` нужен только в greenfield;
`/create-spec-review` — только если важна ретроспектива.

**Привязывает ли это к конкретному инструменту?**
Нет. Пакет ставится в Claude Code, OpenCode или Codex (или сразу во
все). Артефакты — `docs/specs/*.md`, `docs/plans/*.md`, `TASKS.md`,
`docs/wiki/` — обычный markdown, который читается любым инструментом
включая текстовый редактор.

**Где должен лежать `TASKS.md`?**
В корне проекта. Скрипт `tasks.py` идёт вверх от `cwd`, пока не найдёт
его. Стартовый шаблон — `templates/TASKS.md`.

**Wiki-компилятор не удалит мои исходники?**
Нет. Он пишет только в настроенную директорию `output` (по умолчанию
`docs/wiki/`). Исходные файлы для компилятора read-only — см. safety
rule в `skills/wiki-compiler/SKILL.md`.

## Языки

Весь комплект — команды, скилы, инсталлер — на английском; README есть и
на русском (этот файл). Ранние русские варианты промптов сохранены в
истории git. PR на другие языки приветствуются.

## Происхождение

- Команды spec-driven workflow выросли из личного `~/.claude/commands/`.
- `task-tracker` и `wiki-compiler` взяты из проекта Yttri и обобщены.

## Лицензия

[MIT](./LICENSE)
