---
description: Commit and push in one go — reviews status and diff, writes a conventional commit message in the repo's style.
---

# Git Commit

Run the full automation for committing and pushing changes in git.

## Process

1. Check the repository status:
   ```bash
   git status
   ```

2. Show the changes:
   ```bash
   git diff
   ```

3. Show recent commits to understand the style:
   ```bash
   git log --oneline -5
   ```

4. Based on the changes, craft an informative commit message

5. Add the modified files:
   ```bash
   git add .
   ```

6. Create the commit with the message

7. Push the changes:
   ```bash
   git push
   ```

8. Show the final status

## Commit message rules

- First line <= 72 characters
- Imperative mood
- No period at the end of the first line
- Structure: `<type>: <short description>`

### Commit types

| Type | Description |
|------|-------------|
| `feat:` | new functionality |
| `fix:` | bug fix |
| `docs:` | documentation |
| `style:` | formatting |
| `refactor:` | refactor |
| `test:` | tests |
| `chore:` | other changes |
| `release:` | new version release |

## Message examples

- `feat: add report export button`
- `fix: resolve memory leak on modal close`
- `docs: update README with installation instructions`
