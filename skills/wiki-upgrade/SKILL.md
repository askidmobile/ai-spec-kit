---
name: wiki-upgrade
description: Update the installed ai-spec-kit — git pull for symlink installs, reinstall for copies.
---


# Upgrade ai-spec-kit

Update the kit that provides these commands and skills.

## Instructions

1. **Locate the kit clone.** Installed skills are normally symlinks into it — resolve one:
   ```bash
   readlink ~/.claude/skills/wiki-compiler || readlink .claude/skills/wiki-compiler
   ```
   (For OpenCode/Codex check `~/.config/opencode/skills/` / `~/.codex/skills/` instead.)
   The kit directory is two levels up from the resolved path.

2. **Symlink install** — pull and show what changed:
   ```bash
   git -C {kit_dir} pull && git -C {kit_dir} log --oneline -5
   ```
   Symlinked commands and skills pick up the update immediately; suggest restarting
   the CLI session so already-loaded command definitions are refreshed.

3. **Copy install** (readlink prints nothing) — tell the user to `git pull` their clone
   of https://github.com/askidmobile/ai-spec-kit and re-run `./install.sh --force`
   with their original target/scope flags.
