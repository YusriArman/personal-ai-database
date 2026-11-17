---
type: reference
tags: [tools]
---
# Git Cheatsheet

Commands I keep forgetting.

## Undoing

- `git restore <file>` discards changes in the working tree.
- `git reset --soft HEAD~1` undoes the last commit and keeps the changes staged.
- `git revert <commit>` creates a new commit that reverses an old one.

## Habits

- You should commit small changes often.
- A commit message must say why, not what.

## Stashing

- `git stash` saves uncommitted changes and cleans the working tree.
- `git stash pop` brings them back.

## Rebasing

- `git rebase main` replays the current branch on top of main.
- Never rebase commits that have already been pushed and shared.
