#!/usr/bin/env bash
# ai-spec-kit — install commands and skills for AI CLIs (Claude Code / OpenCode / Codex).
#
# Usage:
#   ./install.sh                         # interactive
#   ./install.sh --target=claude --scope=user
#   ./install.sh --target=claude,opencode --scope=project --project-dir=.
#   ./install.sh --target=codex --scope=user --copy
#
# Flags:
#   --target=claude|opencode|codex (comma-separated, or "all")
#   --scope=user|project
#   --project-dir=PATH     (for scope=project; defaults to the current directory)
#   --copy                 (copy instead of symlinking)
#   --force                (overwrite existing files)
#   --dry-run              (show what would be done without changing anything)
#   -h, --help

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- defaults ---
TARGET=""
SCOPE=""
PROJECT_DIR="$(pwd)"
USE_COPY=0
FORCE=0
DRY_RUN=0
INTERACTIVE=1

# --- helpers ---
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

# --- argument parsing ---
for arg in "$@"; do
  case "$arg" in
    --target=*)        TARGET="${arg#*=}"; INTERACTIVE=0 ;;
    --scope=*)         SCOPE="${arg#*=}"; INTERACTIVE=0 ;;
    --project-dir=*)   PROJECT_DIR="${arg#*=}" ;;
    --copy)            USE_COPY=1 ;;
    --force)           FORCE=1 ;;
    --dry-run)         DRY_RUN=1 ;;
    -h|--help)         usage ;;
    *) err "Unknown argument: $arg (see --help)" ;;
  esac
done

# --- interactive mode ---
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
    read -r -p "Choice [1-$((${#options[@]}))]: " answer
    if [[ "$answer" =~ ^[0-9]+$ ]] && (( answer >= 1 && answer <= ${#options[@]} )); then
      echo "${options[$((answer-1))]}"
      return
    fi
    warn "Enter a number between 1 and ${#options[@]}"
  done
}

if [[ $INTERACTIVE -eq 1 ]]; then
  log "ai-spec-kit installer"
  printf 'Kit path: %s\n' "$KIT_DIR"

  choice=$(ask_choice "Which AI CLI to install for?" \
    "Claude Code" "OpenCode" "Codex" "All three")
  case "$choice" in
    "Claude Code") TARGET="claude" ;;
    "OpenCode")    TARGET="opencode" ;;
    "Codex")       TARGET="codex" ;;
    "All three")   TARGET="claude,opencode,codex" ;;
  esac

  choice=$(ask_choice "Install scope?" \
    "User (global, for all projects)" \
    "Project (current folder only)")
  case "$choice" in
    User*)    SCOPE="user" ;;
    Project*) SCOPE="project" ;;
  esac

  if [[ "$SCOPE" == "project" ]]; then
    read -r -p "Project path [$(pwd)]: " input
    PROJECT_DIR="${input:-$(pwd)}"
  fi

  choice=$(ask_choice "How should the files be placed?" \
    "Symlinks (recommended — a git pull here updates all targets)" \
    "Copies (independent copy)")
  [[ "$choice" == Copies* ]] && USE_COPY=1
fi

# --- validation ---
[[ -z "$TARGET" ]] && err "Missing --target"
[[ -z "$SCOPE"  ]] && err "Missing --scope"
[[ "$SCOPE" == "project" && ! -d "$PROJECT_DIR" ]] && err "Project directory not found: $PROJECT_DIR"

# Normalize target
if [[ "$TARGET" == "all" ]]; then TARGET="claude,opencode,codex"; fi

# --- resolve directories for target and scope ---
# Sets the globals CMD_DIR and SKILL_DIR.
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
      # Codex has no native slash commands — install as prompts/skills under ~/.codex/
      if [[ "$SCOPE" == "user" ]]; then
        CMD_DIR="$HOME/.codex/prompts"
        SKILL_DIR="$HOME/.codex/skills"
      else
        CMD_DIR="$PROJECT_DIR/.codex/prompts"
        SKILL_DIR="$PROJECT_DIR/.codex/skills"
      fi
      ;;
    *) err "Unknown target: $tool" ;;
  esac
}

# --- place a single file ---
place() {
  local src="$1" dst="$2"
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      run rm -rf "$dst"
    else
      warn "skip (already exists): $dst — use --force to overwrite"
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

# --- main loop ---
IFS=',' read -ra TARGETS <<< "$TARGET"
for tool in "${TARGETS[@]}"; do
  tool="$(echo "$tool" | xargs)"
  log "Installing into: $tool ($SCOPE)"

  set_target_dirs "$tool"

  # Commands
  log "  commands → $CMD_DIR"
  shopt -s nullglob
  for f in "$KIT_DIR"/commands/*.md; do
    place "$f" "$CMD_DIR/$(basename "$f")"
  done

  # Skills (whole directories)
  log "  skills   → $SKILL_DIR"
  for d in "$KIT_DIR"/skills/*/; do
    name="$(basename "$d")"
    place "${d%/}" "$SKILL_DIR/$name"
  done
  shopt -u nullglob

  # Codex extra: a pointer in AGENTS.md
  if [[ "$tool" == "codex" ]]; then
    agents_md=""
    [[ "$SCOPE" == "user" ]] && agents_md="$HOME/.codex/AGENTS.md" || agents_md="$PROJECT_DIR/AGENTS.md"
    if ! grep -q "ai-spec-kit" "$agents_md" 2>/dev/null; then
      log "  ↳ appending a pointer to $agents_md"
      if [[ $DRY_RUN -eq 0 ]]; then
        {
          [[ -f "$agents_md" ]] && echo ""
          echo "## ai-spec-kit"
          echo ""
          echo "Available prompts: $CMD_DIR (create-brief, create-spec, create-spec-plan,"
          echo "create-spec-implement, create-spec-review, tasks, commit, wiki-*)."
          echo "Skills: $SKILL_DIR (task-tracker, wiki-compiler)."
        } >> "$agents_md"
      else
        printf '   [dry-run] append section to %s\n' "$agents_md"
      fi
    fi
  fi
done

log "Done."
[[ $DRY_RUN -eq 1 ]] && warn "This was a dry-run. Re-run without --dry-run to apply."
echo
echo "Next steps:"
echo "  • Open a project in Claude Code / OpenCode and try /create-brief, /create-spec, /tasks."
echo "  • Need TASKS.md? Copy templates/TASKS.md into your project root."
echo "  • For the wiki compiler — copy templates/wiki-compiler.example.json as .wiki-compiler.json."
