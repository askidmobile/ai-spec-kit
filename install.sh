#!/usr/bin/env bash
# ai-spec-kit — установка команд и скилов для AI CLI (Claude Code / OpenCode / Codex).
#
# Использование:
#   ./install.sh                         # интерактивно
#   ./install.sh --target=claude --scope=user
#   ./install.sh --target=claude,opencode --scope=project --project-dir=.
#   ./install.sh --target=codex --scope=user --copy
#
# Флаги:
#   --target=claude|opencode|codex (можно через запятую, или "all")
#   --scope=user|project
#   --project-dir=PATH     (для scope=project; по умолчанию текущая директория)
#   --copy                 (копировать вместо симлинков)
#   --force                (перезаписывать существующие файлы)
#   --dry-run              (показать что будет сделано, без изменений)
#   -h, --help

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- настройки по умолчанию ---
TARGET=""
SCOPE=""
PROJECT_DIR="$(pwd)"
USE_COPY=0
FORCE=0
DRY_RUN=0
INTERACTIVE=1

# --- утилиты ---
log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$*" >&2; }
err() { printf '\033[1;31mERR\033[0m %s\n' "$*" >&2; exit 1; }
run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '   [dry-run]'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

usage() {
  awk 'NR==1 && /^#!/ { next } /^#/{ sub(/^# ?/, ""); print; next } { exit }' "$0"
  exit 0
}

# --- парсинг аргументов ---
for arg in "$@"; do
  case "$arg" in
    --target=*)        TARGET="${arg#*=}"; INTERACTIVE=0 ;;
    --scope=*)         SCOPE="${arg#*=}"; INTERACTIVE=0 ;;
    --project-dir=*)   PROJECT_DIR="${arg#*=}" ;;
    --copy)            USE_COPY=1 ;;
    --force)           FORCE=1 ;;
    --dry-run)         DRY_RUN=1 ;;
    -h|--help)         usage ;;
    *) err "Неизвестный аргумент: $arg (см. --help)" ;;
  esac
done

# --- интерактивный режим ---
ask_choice() {
  local prompt="$1"; shift
  local options=("$@")
  local i=1
  printf '\n%s\n' "$prompt"
  for opt in "${options[@]}"; do
    printf '  %d) %s\n' "$i" "$opt"
    i=$((i+1))
  done
  local answer
  while true; do
    read -r -p "Выбор [1-$((${#options[@]}))]: " answer
    if [[ "$answer" =~ ^[0-9]+$ ]] && (( answer >= 1 && answer <= ${#options[@]} )); then
      echo "${options[$((answer-1))]}"
      return
    fi
    warn "Введите число от 1 до ${#options[@]}"
  done
}

if [[ $INTERACTIVE -eq 1 ]]; then
  log "ai-spec-kit installer"
  printf 'Путь к пакету: %s\n' "$KIT_DIR"

  choice=$(ask_choice "Для какого AI CLI устанавливать?" \
    "Claude Code" "OpenCode" "Codex" "Все три")
  case "$choice" in
    "Claude Code") TARGET="claude" ;;
    "OpenCode")    TARGET="opencode" ;;
    "Codex")       TARGET="codex" ;;
    "Все три")     TARGET="claude,opencode,codex" ;;
  esac

  choice=$(ask_choice "Scope установки?" \
    "User (глобально, для всех проектов)" \
    "Project (только в текущую папку)")
  case "$choice" in
    User*)    SCOPE="user" ;;
    Project*) SCOPE="project" ;;
  esac

  if [[ "$SCOPE" == "project" ]]; then
    read -r -p "Путь к проекту [$(pwd)]: " input
    PROJECT_DIR="${input:-$(pwd)}"
  fi

  choice=$(ask_choice "Как раскладывать файлы?" \
    "Симлинки (рекомендуется — обновления подхватываются автоматически)" \
    "Копирование (независимая копия)")
  [[ "$choice" == Копирование* ]] && USE_COPY=1
fi

# --- валидация ---
[[ -z "$TARGET" ]] && err "Не задан --target"
[[ -z "$SCOPE"  ]] && err "Не задан --scope"
[[ "$SCOPE" == "project" && ! -d "$PROJECT_DIR" ]] && err "Папка проекта не найдена: $PROJECT_DIR"

# Нормализация target
if [[ "$TARGET" == "all" ]]; then TARGET="claude,opencode,codex"; fi

# --- определение директорий по таргету и scope ---
# Устанавливает глобальные CMD_DIR и SKILL_DIR.
set_target_dirs() {
  local tool="$1"
  case "$tool" in
    claude)
      if [[ "$SCOPE" == "user" ]]; then
        CMD_DIR="$HOME/.claude/commands"
        SKILL_DIR="$HOME/.claude/skills"
      else
        CMD_DIR="$PROJECT_DIR/.claude/commands"
        SKILL_DIR="$PROJECT_DIR/.claude/skills"
      fi
      ;;
    opencode)
      if [[ "$SCOPE" == "user" ]]; then
        CMD_DIR="$HOME/.config/opencode/commands"
        SKILL_DIR="$HOME/.config/opencode/skills"
      else
        CMD_DIR="$PROJECT_DIR/.opencode/commands"
        SKILL_DIR="$PROJECT_DIR/.opencode/skills"
      fi
      ;;
    codex)
      # Codex не имеет slash-команд — раскладываем как prompts/skills под ~/.codex/
      if [[ "$SCOPE" == "user" ]]; then
        CMD_DIR="$HOME/.codex/prompts"
        SKILL_DIR="$HOME/.codex/skills"
      else
        CMD_DIR="$PROJECT_DIR/.codex/prompts"
        SKILL_DIR="$PROJECT_DIR/.codex/skills"
      fi
      ;;
    *) err "Неизвестный target: $tool" ;;
  esac
}

# --- размещение одного файла ---
place() {
  local src="$1" dst="$2"
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      run rm -rf "$dst"
    else
      warn "пропуск (уже существует): $dst — используй --force для перезаписи"
      return
    fi
  fi
  run mkdir -p "$(dirname "$dst")"
  if [[ $USE_COPY -eq 1 ]]; then
    if [[ -d "$src" ]]; then
      run cp -R "$src" "$dst"
    else
      run cp "$src" "$dst"
    fi
  else
    run ln -s "$src" "$dst"
  fi
}

# --- основной цикл ---
IFS=',' read -ra TARGETS <<< "$TARGET"
for tool in "${TARGETS[@]}"; do
  tool="$(echo "$tool" | xargs)"
  log "Устанавливаю в: $tool ($SCOPE)"

  set_target_dirs "$tool"

  # Команды
  log "  команды → $CMD_DIR"
  shopt -s nullglob
  for f in "$KIT_DIR"/commands/*.md; do
    place "$f" "$CMD_DIR/$(basename "$f")"
  done

  # Скилы (целиком директориями)
  log "  скилы   → $SKILL_DIR"
  for d in "$KIT_DIR"/skills/*/; do
    name="$(basename "$d")"
    place "${d%/}" "$SKILL_DIR/$name"
  done
  shopt -u nullglob

  # Для Codex дополнительно — подсказка в AGENTS.md
  if [[ "$tool" == "codex" ]]; then
    agents_md=""
    [[ "$SCOPE" == "user" ]] && agents_md="$HOME/.codex/AGENTS.md" || agents_md="$PROJECT_DIR/AGENTS.md"
    if ! grep -q "ai-spec-kit" "$agents_md" 2>/dev/null; then
      log "  ↳ дописываю ссылку в $agents_md"
      if [[ $DRY_RUN -eq 0 ]]; then
        {
          [[ -f "$agents_md" ]] && echo ""
          echo "## ai-spec-kit"
          echo ""
          echo "Доступные prompts: $CMD_DIR (create-brief, create-spec, create-spec-plan,"
          echo "create-spec-implement, create-spec-review, tasks, commit, wiki-*)."
          echo "Скилы: $SKILL_DIR (task-tracker, wiki-compiler)."
        } >> "$agents_md"
      else
        printf '   [dry-run] append section to %s\n' "$agents_md"
      fi
    fi
  fi
done

log "Готово."
[[ $DRY_RUN -eq 1 ]] && warn "Это был dry-run. Запусти без --dry-run для применения."
echo
echo "Дальше:"
echo "  • Открой проект в Claude Code / OpenCode и проверь /create-brief, /create-spec, /tasks."
echo "  • Если нужен TASKS.md — скопируй из templates/TASKS.md в корень проекта."
echo "  • Для wiki-compiler — скопируй templates/wiki-compiler.example.json как .wiki-compiler.json."
