#!/usr/bin/env bash
# generate-skills.sh — create Warp-compatible skill wrappers from command files.
#
# For each commands/<name>.md, emit skills/<name>/SKILL.md with Warp skill
# frontmatter (name + description). The body is the command's content verbatim
# so Warp agents get the same instructions Claude Code / OpenCode / Codex get
# via their native slash-command mechanism.
#
# Three commands are thin wrappers around core skills (project-brief,
# task-tracker, wiki-compiler) — for those we emit a delegate SKILL.md that
# tells the agent to invoke the core skill, avoiding content duplication.
#
# Re-run after editing commands/*.md to keep skills in sync:
#   ./scripts/generate-skills.sh

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CMD_DIR="$KIT_DIR/commands"
SKILL_ROOT="$KIT_DIR/skills"

# Commands that delegate to an existing core skill.
# Usage: delegate_for <name> -> echoes core skill name or empty.
delegate_for() {
  case "$1" in
    create-brief)  echo project-brief ;;
    tasks)         echo task-tracker ;;
    wiki-compile)  echo wiki-compiler ;;
    *)             echo "" ;;
  esac
}

# --- extract a YAML frontmatter value (simple key: value) ---
fm_value() {
  local file="$1" key="$2"
  awk -v k="$key" '
    /^---$/ { n++; next }
    n==1 && $0 ~ "^"k":" {
      sub("^"k":[[:space:]]*", "")
      gsub(/^"|"$/, "")
      printf "%s", $0
      exit
    }
  ' "$file"
}

# --- extract the body (everything after the closing ---) ---
fm_body() {
  local file="$1"
  awk 'BEGIN{n=0} /^---$/{n++; next} n>=2{print}' "$file"
}

shopt -s nullglob
for f in "$CMD_DIR"/*.md; do
  name="$(basename "$f" .md)"
  skill_dir="$SKILL_ROOT/$name"
  mkdir -p "$skill_dir"

  desc="$(fm_value "$f" description)"
  [[ -z "$desc" ]] && desc "Warp skill wrapper for $name"

  core="$(delegate_for "$name")"
  if [[ -n "$core" ]]; then
    # Thin wrapper: delegate to core skill
    arg_hint="$(fm_value "$f" argument-hint)"
    {
      echo "---"
      echo "name: $name"
      echo "description: $desc"
      echo "---"
      echo ""
      echo "# ${name}"
      echo ""
      echo "Invoke the **${core}** skill and run it for: \$ARGUMENTS"
      echo ""
      if [[ -n "$arg_hint" ]]; then
        echo "Arguments: ${arg_hint}"
        echo ""
      fi
      echo "> This is a Warp-compatible wrapper around the ${core} skill."
      echo "> In Claude Code / OpenCode / Codex the same workflow is the"
      echo "> \`/${name}\` slash command."
    } > "$skill_dir/SKILL.md"
  else
    # Full content: copy command body into SKILL.md
    {
      echo "---"
      echo "name: $name"
      echo "description: $desc"
      echo "---"
      echo ""
      fm_body "$f"
    } > "$skill_dir/SKILL.md"
  fi

  printf '  generated: skills/%s/SKILL.md\n' "$name"
done

echo "Done. $(ls -d "$SKILL_ROOT"/*/ | wc -l | tr -d ' ') skill directories total."