#!/usr/bin/env bash
# ai-spec-kit — remove commands and skills from selected AI CLIs.
#
# Usage:
#   ./uninstall.sh                       # interactive
#   ./uninstall.sh --target=claude --scope=user
#   ./uninstall.sh --target=opencode --scope=project --project-dir=.
#
# Only files that belong to the ai-spec-kit bundle are removed
# (matched by name). Other files in those directories are left alone.
#
# Flags: --target, --scope, --project-dir, --dry-run, -h/--help

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET=""
SCOPE=""
PROJECT_DIR="$(pwd)"
DRY_RUN=0
INTERACTIVE=1

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

for arg in "$@"; do
  case "$arg" in
    --target=*)      TARGET="${arg#*=}"; INTERACTIVE=0 ;;
    --scope=*)       SCOPE="${arg#*=}"; INTERACTIVE=0 ;;
    --project-dir=*) PROJECT_DIR="${arg#*=}" ;;
    --dry-run)       DRY_RUN=1 ;;
    -h|--help)       usage ;;
    *) err "Unknown argument: $arg" ;;
  esac
done

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
  log "ai-spec-kit uninstaller"
  choice=$(ask_choice "Uninstall from?" \
    "Claude Code" "OpenCode" "Codex" "All three")
  case "$choice" in
    "Claude Code") TARGET="claude" ;;
    "OpenCode")    TARGET="opencode" ;;
    "Codex")       TARGET="codex" ;;
    "All three")   TARGET="claude,opencode,codex" ;;
  esac

  choice=$(ask_choice "Scope?" \
    "User (~/)" "Project (current folder)")
  case "$choice" in
    User*)    SCOPE="user" ;;
    Project*) SCOPE="project" ;;
  esac

  if [[ "$SCOPE" == "project" ]]; then
    read -r -p "Project path [$(pwd)]: " input
    PROJECT_DIR="${input:-$(pwd)}"
  fi
fi

[[ -z "$TARGET" ]] && err "Missing --target"
[[ -z "$SCOPE"  ]] && err "Missing --scope"
[[ "$TARGET" == "all" ]] && TARGET="claude,opencode,codex"

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

# Remove only when the content (by name) matches the kit.
# A symlink into our KIT_DIR is removed unconditionally. A regular file —
# only if it was installed from the kit (same basename exists in KIT_DIR).
remove_if_ours() {
  local dst="$1" expected_src="$2"
  [[ -e "$dst" || -L "$dst" ]] || return 0

  if [[ -L "$dst" ]]; then
    local link_target
    link_target="$(readlink "$dst")"
    if [[ "$link_target" == "$expected_src" || "$link_target" == */ai-spec-kit/* ]]; then
      run rm -f "$dst"
    else
      warn "skip (symlink points outside ai-spec-kit): $dst"
    fi
  else
    # A copy — remove if the same basename exists in the kit
    if [[ -e "$expected_src" ]]; then
      run rm -rf "$dst"
    else
      warn "skip (not from the kit): $dst"
    fi
  fi
}

IFS=',' read -ra TARGETS <<< "$TARGET"
for tool in "${TARGETS[@]}"; do
  tool="$(echo "$tool" | xargs)"
  log "Removing from: $tool ($SCOPE)"
  set_target_dirs "$tool"

  shopt -s nullglob
  for f in "$KIT_DIR"/commands/*.md; do
    name="$(basename "$f")"
    remove_if_ours "$CMD_DIR/$name" "$f"
  done

  for d in "$KIT_DIR"/skills/*/; do
    name="$(basename "$d")"
    remove_if_ours "$SKILL_DIR/$name" "${d%/}"
  done
  shopt -u nullglob

  # Clean up empty directories
  for dir in "$CMD_DIR" "$SKILL_DIR"; do
    if [[ -d "$dir" ]] && [[ -z "$(ls -A "$dir" 2>/dev/null)" ]]; then
      run rmdir "$dir"
    fi
  done
done

log "Done."
[[ $DRY_RUN -eq 1 ]] && warn "This was a dry-run. Re-run without --dry-run to apply."
echo
echo "Note: the AGENTS.md entry (for Codex) has to be removed manually if needed."
