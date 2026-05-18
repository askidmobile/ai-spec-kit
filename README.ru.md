# ai-spec-kit

[English version](./README.md)

Переносимый набор команд и скилов, который приносит **spec-driven workflow**
(`brief → spec → plan → implement → review`) и несколько полезных утилит
(`tasks`, `commit`, `wiki-*`) в любой markdown-совместимый AI CLI —
**Claude Code**, **OpenCode**, **Codex**.

> Положи пакет куда угодно, запусти `./install.sh` — получишь одинаковый
> набор `/команд` и скилов во всех своих AI-инструментах.

## Что внутри

### Команды (`commands/`)

Полный пайплайн от идеи до зафиксированной фичи:

| Команда | Назначение |
|---|---|
| `/create-brief` | Верхнеуровневый бриф проекта (видение, roadmap, стейкхолдеры) |
| `/create-spec` | Спецификация фичи — *что* и *зачем*, без деталей реализации |
| `/create-spec-plan` | Детальный план реализации на основе спеки — *как* |
| `/create-spec-implement` | Реализация плана по фазам |
| `/create-spec-review` | Ретроспектива: план vs реальность, уроки, статусы |
| `/tasks` | Управление `TASKS.md` через скил `task-tracker` |
| `/commit` | Conventional commit с автогенерируемым сообщением |
| `/wiki-init`, `/wiki-compile`, `/wiki-search`, … | Сборка и поиск по wiki проекта |

### Скилы (`skills/`)

| Скил | Что делает |
|---|---|
| `task-tracker` | Парсит и обновляет `TASKS.md` через `tasks.py`. Синхронизирует список задач с IDE. |
| `wiki-compiler` | Компилирует документацию/код в topic-based wiki (`docs/wiki/`). |

### Шаблоны (`templates/`)

- `TASKS.md` — стартовый трекер с правильной структурой таблиц
- `wiki-compiler.example.json` — пример конфигурации wiki-компилятора

## Требования

- **bash** ≥ 3.2 (стандартный на macOS подходит)
- **Python 3.8+** — только для скила `task-tracker`
- Один из: Claude Code, OpenCode, Codex

## Установка

### Интерактивно (рекомендуется)

```bash
git clone https://github.com/askidmobile/ai-spec-kit.git
cd ai-spec-kit
./install.sh
```

Скрипт спросит:

1. В какой AI CLI: Claude Code / OpenCode / Codex / все три
2. Scope: **user** (`~/.claude/`, `~/.config/opencode/`, `~/.codex/`) или
   **project** (`<твой-проект>/.claude/`, и т.д.)
3. Симлинки (рекомендуется — обновления через `git pull` подхватываются автоматически) или копии

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

> У Codex нет slash-команд, поэтому они кладутся как **prompts**, плюс
> в `AGENTS.md` добавляется короткая ссылка — агент находит их сам при старте сессии.

## Использование пайплайна

```bash
# 1. Greenfield проект — видение и roadmap
/create-brief my-saas-app

# 2. Выбрал элемент из roadmap → спека
/create-spec auth-with-magic-link

# 3. План реализации
/create-spec-plan auth-with-magic-link

# 4. Реализация по фазам
/create-spec-implement auth-with-magic-link
# (повторяй для каждой фазы)

# 5. Ретроспектива по завершении
/create-spec-review auth-with-magic-link
```

### Задачи

```bash
/tasks                          # активные задачи
/tasks add "Починить логин" "docs/plans/fix-login.md"
/tasks update T-001 "🔄 В работе"
/tasks archive T-001
```

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

Результат — topic-based markdown wiki в `docs/wiki/` (путь конфигурируется),
с `INDEX.md`, `topics/` и `concepts/`. Работает и для **knowledge mode**
(markdown-заметки), и для **codebase mode** (исходники проекта).

## Удаление

```bash
./uninstall.sh                # интерактивно
./uninstall.sh --target=all --scope=user
./uninstall.sh --target=claude --scope=project --project-dir=.
```

Деинсталлер удаляет только то, что было поставлено из пакета (по имени файла
и таргету симлинка). Твои собственные команды/скилы в этих директориях не трогает.

## Структура

```
ai-spec-kit/
├── README.md / README.ru.md
├── LICENSE
├── install.sh / uninstall.sh
├── commands/                  # markdown-файлы команд
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

## Как это работает

Весь пакет — это **markdown + один Python-скрипт**. Каждый файл команды —
самодостаточный системный промпт, который любой markdown-совместимый AI CLI
подхватывает автоматически, как только он оказывается в нужной директории.
Скилы — это папки с `SKILL.md` плюс опциональные скрипты и шаблоны.

Следствия:

- Нет рантайма, демона или плагинного API, который нужно сопровождать.
- Обновление пакета = `git pull` в этом репозитории (для симлинков) или
  повторный запуск `install.sh --force` (для копий).
- Любую команду можно отредактировать под свой процесс — это просто текст.

## Языки

Промпты команд написаны на **русском** (под автора пакета). В англоязычных
сессиях они тоже работают — AI следует структуре независимо от языка промпта.
Перевод любого файла приветствуется через PR.

## Происхождение

- Команды spec-driven workflow выросли из личного `~/.claude/commands/`.
- `task-tracker` и `wiki-compiler` взяты из проекта Yttri и обобщены.

## Лицензия

[MIT](./LICENSE)
