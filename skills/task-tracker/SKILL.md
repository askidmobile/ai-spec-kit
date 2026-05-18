---
name: task-tracker
description: >-
  Управление задачами проекта в TASKS.md. Парсит markdown-таблицы, возвращает JSON,
  обновляет статусы, добавляет и архивирует задачи. Синхронизирует с TodoWrite.
  Активируется при: "задачи", "статус задач", "что осталось", "обнови TASKS",
  "покажи задачи", "следующая задача", "task tracker", а также после сжатия контекста.
  НЕ активируется для: обычных обсуждений кода, git-операций, сборки.
allowed-tools:
  - Read
  - Edit
  - Bash
  - TodoWrite
---

# Task Tracker — Управление задачами в TASKS.md

Скрипт: `.claude/skills/task-tracker/scripts/tasks.py`
Файл задач: `TASKS.md` (в корне проекта)

## Когда активировать

- Пользователь спрашивает: "задачи", "статус", "что осталось", "покажи задачи"
- Пользователь просит: "обнови TASKS.md", "отметь задачу как готово"
- **После сжатия контекста (compaction)** — если пользователь продолжает работу над задачей
- При создании нового плана (для регистрации в TASKS.md)
- При завершении задачи (для обновления статуса)

## Команды скрипта

Все команды возвращают JSON. Запускать из корня проекта.

### Чтение

```bash
# Все задачи (active + backlog) со сводкой
python3 .claude/skills/task-tracker/scripts/tasks.py list

# Только активные задачи
python3 .claude/skills/task-tracker/scripts/tasks.py active

# Только backlog
python3 .claude/skills/task-tracker/scripts/tasks.py backlog

# Детали одной задачи
python3 .claude/skills/task-tracker/scripts/tasks.py show T-001

# Следующий свободный ID
python3 .claude/skills/task-tracker/scripts/tasks.py next-id
```

### Запись

```bash
# Обновить статус задачи
python3 .claude/skills/task-tracker/scripts/tasks.py update T-001 "✅ Готово"

# Добавить задачу в Active
python3 .claude/skills/task-tracker/scripts/tasks.py add "Название задачи" "docs/plans/plan.md"

# Добавить задачу в Backlog
python3 .claude/skills/task-tracker/scripts/tasks.py add-backlog "Название" "docs/plans/plan.md" "Примечание"

# Переместить в архив
python3 .claude/skills/task-tracker/scripts/tasks.py archive T-001
```

## Workflow: Показать задачи

Когда пользователь просит показать задачи:

1. Запусти `python3 .claude/skills/task-tracker/scripts/tasks.py active`
2. Получи JSON с задачами
3. Выведи пользователю в читаемом формате:
   - Задачи 🔄 В работе — выделить как текущие
   - Задачи ✅ Готово — отметить как завершённые
   - Показать общую сводку (сколько в работе, сколько завершено)
4. **Создай TodoWrite** со всеми задачами в статусе 🔄 — для отслеживания в UI

## Workflow: После сжатия контекста

**КРИТИЧНО.** Если ты замечаешь, что контекст был сжат и ты работал над задачей:

1. Запусти `python3 .claude/skills/task-tracker/scripts/tasks.py active`
2. Найди задачи в статусе 🔄
3. Пересоздай TodoWrite с этими задачами
4. Сообщи пользователю, какие задачи сейчас в работе
5. Спроси, над какой задачей продолжить

## Workflow: Создание плана

Когда создаётся новый план (режим Plan):

1. Создай файл плана в `docs/plans/YYYY-MM-DD-name.md`
2. Запусти: `python3 .claude/skills/task-tracker/scripts/tasks.py add "Описание задачи" "docs/plans/YYYY-MM-DD-name.md"`
3. Покажи пользователю ID новой задачи

## Workflow: Начало работы над задачей

Когда берёшь задачу в работу (режим Build):

1. Запусти: `python3 .claude/skills/task-tracker/scripts/tasks.py update T-XXX "🔄 В работе"`
2. Создай TodoWrite с подзадачами из плана

## Workflow: Завершение задачи

Когда задача выполнена:

1. Запусти: `python3 .claude/skills/task-tracker/scripts/tasks.py update T-XXX "✅ Готово"`
2. Обнови TodoWrite — отметь задачу как completed
3. Если план можно архивировать: `python3 .claude/skills/task-tracker/scripts/tasks.py archive T-XXX`

## Формат ID задач

- Формат: `T-XXX` (T-001, T-002, ...)
- ID автоматически инкрементируется
- Используй `next-id` чтобы узнать следующий свободный

## Статусы

| Эмодзи | Статус | Когда использовать |
|--------|--------|--------------------|
| 📝 | Планирование | План создан, работа не начата |
| 🔄 | В работе | Активная разработка |
| 👀 | На проверке | Code review / тестирование |
| ✅ | Готово | Выполнено |

При обновлении статуса можно добавить пояснение: `"✅ Готово (v0.38.0)"`, `"🔄 Фазы 1-2 готовы"`.

## Интеграция с Yttri через MCP

Если к IDE подключён MCP-сервер Yttri (`http://localhost:9315/mcp`), доступны дополнительные инструменты для работы с задачами **в приложении Yttri**:

### Доступные MCP tools (домен tasks)

| MCP Tool | Аналог tasks.py | Что делает |
|----------|-----------------|------------|
| `list_tasks(status?, limit?)` | `active` / `list` | Список задач Yttri. Фильтр: `todo`, `in_progress`, `done`, `all` |
| `get_task(uid)` | `show T-XXX` | Детали задачи по uid (title, description, status, priority, due_date, subtasks) |
| `create_task(title, description?, priority?, due_date?)` | `add` | Создать задачу в Yttri. Появится в UI Tasks |
| `update_task(uid, status?, title?, priority?)` | `update` | Обновить статус: `todo`, `in_progress`, `done` |
| `delete_task(uid)` | `archive` (близко) | Удалить задачу из Yttri |

### Две системы — два назначения

| | TASKS.md (`tasks.py`) | Yttri Tasks (MCP) |
|---|---|---|
| **Назначение** | Трекер задач разработки проекта (plan → build) | Пользовательские задачи в Yttri desktop |
| **ID** | `T-XXX` (T-001, T-213...) | UUID |
| **Хранение** | Markdown файл в репозитории | SQLite в Yttri |
| **Видимость** | Git, IDE | Yttri desktop UI |
| **Доступ** | Всегда (файл) | Только при запущенном Yttri |

### Когда использовать MCP tools

- Пользователь просит создать **пользовательскую задачу** в Yttri (не задачу разработки)
- Нужно посмотреть задачи из Yttri, не переключаясь в приложение
- Пользователь работает над функционалом и хочет видеть задачу в Yttri UI
- Пользователь явно говорит "создай задачу в Yttri" / "покажи мои задачи"

### Когда использовать tasks.py

- Управление задачами **разработки** проекта (план → реализация → ретроспектива)
- Работа с pipeline plan/build/review
- Обновление статусов задач для трейсабельности в репозитории
- После сжатия контекста (TASKS.md всегда доступен)

### Пример: параллельная работа

```
# 1. Создать задачу разработки в TASKS.md (трекинг плана)
python3 .claude/skills/task-tracker/scripts/tasks.py add "Рефакторинг auth модуля" "docs/plans/auth-refactor.md"

# 2. Одновременно создать задачу в Yttri (видна в UI)
# → MCP tool: create_task(title="Рефакторинг auth модуля", description="План: docs/plans/auth-refactor.md, T-216")
```

### Требования к подключению

1. Yttri desktop запущен
2. MCP-сервер включён (Settings → Integrations → MCP Server)
3. Домен `tasks` включён с доступом `read_write`
4. API-ключ создан и добавлен в конфигурацию IDE

## Правила

1. **Не редактируй TASKS.md вручную** — всегда используй скрипт `tasks.py`
2. **Всегда синхронизируй TodoWrite** с текущими задачами из TASKS.md
3. **После compaction** — первым делом перечитай задачи через `tasks.py active`
4. **Новый план = новая запись** в TASKS.md через `tasks.py add`
5. **Завершение = обновление статуса** через `tasks.py update`
6. **MCP tools — опциональный канал** для задач в Yttri UI; TASKS.md остаётся основным трекером разработки
