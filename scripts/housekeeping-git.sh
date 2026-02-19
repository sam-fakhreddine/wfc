#!/usr/bin/env bash
# scripts/housekeeping-git.sh
# Git helper — scan and action commands for the WFC workflow.
# Replaces bare git calls with project-aware, safety-guarded wrappers.
#
# SCAN commands (read-only):
#   branches                           List merged/gone/all local+remote branches
#   branch-age                         List branches sorted oldest→newest
#   worktrees                          List worktrees + prunable
#   status                             git status
#   log [n]                            Last N commits (default 10)
#   diff [ref]                         Staged+unstaged diff (or vs ref)
#   all                                Run all scan commands
#
# ACTION commands (mutating):
#   checkout <branch> [base]           Switch branch (create from base if new)
#   branch-delete <name> [--force]     Delete local branch (blocks protected)
#   stash [push [msg]|pop|drop|list]   Stash operations
#   add <file> [file...]               Stage specific files
#   add-all                            Stage all tracked+untracked changes
#   restore <file> [file...]           Discard unstaged changes (git restore)
#   rm <file> [file...]                Remove files from index (git rm)
#   commit <message>                   Commit staged changes
#   push [remote] [branch]             Push current branch (no force)
#   pr-create <title> <base> <body>    Create PR via gh CLI

set -euo pipefail

PROTECTED_PATTERN="^(main|develop)$"
CURRENT=$(git rev-parse --abbrev-ref HEAD)

_guard_protected() {
  local branch="$1"
  if [[ "$branch" =~ $PROTECTED_PATTERN ]]; then
    echo "ERROR: '${branch}' is a protected branch. Aborting." >&2
    exit 1
  fi
}

# ─── SCAN ─────────────────────────────────────────────────────────────────────

cmd_branches() {
  echo "=== Local branches merged into main ==="
  git branch --merged main | grep -v -E "^\*|main|develop" | sed 's/^[[:space:]]*//' || true

  echo ""
  echo "=== Remote branches merged into main ==="
  git branch -r --merged origin/main | grep -v -E "main|develop|HEAD" | sed 's/^[[:space:]]*//' || true

  echo ""
  echo "=== Local branches tracking deleted remotes ==="
  git branch -vv | grep ': gone]' | awk '{print $1}' || true

  echo ""
  echo "=== All local branches with tracking info ==="
  git branch -vv
}

cmd_branch_age() {
  echo "=== Branch ages (oldest first) ==="
  git for-each-ref \
    --sort=committerdate \
    --format='%(refname:short) | %(committerdate:relative) | %(committeremail)' \
    refs/heads/
}

cmd_worktrees() {
  echo "=== Worktree list ==="
  git worktree list --porcelain

  echo ""
  echo "=== Prunable worktrees ==="
  git worktree prune --dry-run 2>&1 || echo "(none)"
}

cmd_status() {
  git status
}

cmd_log() {
  local n="${1:-10}"
  git log --oneline -"$n"
}

cmd_diff() {
  local ref="${1:-}"
  if [ -n "$ref" ]; then
    git diff "$ref"
  else
    git diff HEAD
  fi
}

cmd_all() {
  echo "Current branch: ${CURRENT}"
  echo "Protected branches: main, develop"
  echo ""
  cmd_branches
  echo ""
  cmd_branch_age
  echo ""
  cmd_worktrees
}

# ─── ACTION ───────────────────────────────────────────────────────────────────

cmd_checkout() {
  local branch="${1:?Usage: checkout <branch> [base]}"
  local base="${2:-}"
  if [ -n "$base" ]; then
    git checkout -b "$branch" "$base"
  else
    git checkout "$branch"
  fi
}

cmd_branch_delete() {
  local branch="${1:?Usage: branch-delete <name> [--force]}"
  local force="${2:-}"
  _guard_protected "$branch"
  if [ "$branch" = "$CURRENT" ]; then
    echo "ERROR: Cannot delete the current branch '${branch}'." >&2
    exit 1
  fi
  if [ "$force" = "--force" ]; then
    git branch -D "$branch"
  else
    git branch -d "$branch"
  fi
}

cmd_stash() {
  local sub="${1:-list}"
  case "$sub" in
    push)
      local msg="${2:-wfc-stash}"
      git stash push --include-untracked -m "$msg"
      ;;
    pop)   git stash pop ;;
    drop)  git stash drop ;;
    list)  git stash list ;;
    *)
      echo "Usage: stash [push [msg]|pop|drop|list]" >&2
      exit 1
      ;;
  esac
}

cmd_add() {
  if [ $# -eq 0 ]; then
    echo "Usage: add <file> [file...]" >&2
    exit 1
  fi
  git add "$@"
}

cmd_add_all() {
  git add -A
}

cmd_restore() {
  if [ $# -eq 0 ]; then
    echo "Usage: restore <file> [file...]" >&2
    exit 1
  fi
  git restore "$@"
}

cmd_rm() {
  if [ $# -eq 0 ]; then
    echo "Usage: rm <file> [file...]" >&2
    exit 1
  fi
  git rm "$@"
}

cmd_commit() {
  local msg="${1:?Usage: commit <message>}"
  git commit -m "$msg"
}

cmd_push() {
  local remote="${1:-origin}"
  local branch="${2:-$CURRENT}"
  git push -u "$remote" "$branch"
}

cmd_pr_create() {
  local title="${1:?Usage: pr-create <title> <base> <body>}"
  local base="${2:?Usage: pr-create <title> <base> <body>}"
  local body="${3:?Usage: pr-create <title> <base> <body>}"
  gh pr create --title "$title" --base "$base" --body "$body"
}

# ─── Dispatch ─────────────────────────────────────────────────────────────────
case "${1:-all}" in
  # Scan
  branches)      cmd_branches ;;
  branch-age)    cmd_branch_age ;;
  worktrees)     cmd_worktrees ;;
  status)        cmd_status ;;
  log)           shift; cmd_log "$@" ;;
  diff)          shift; cmd_diff "$@" ;;
  all)           cmd_all ;;
  # Action
  checkout)      shift; cmd_checkout "$@" ;;
  branch-delete) shift; cmd_branch_delete "$@" ;;
  stash)         shift; cmd_stash "$@" ;;
  add)           shift; cmd_add "$@" ;;
  add-all)       cmd_add_all ;;
  restore)       shift; cmd_restore "$@" ;;
  rm)            shift; cmd_rm "$@" ;;
  commit)        shift; cmd_commit "$@" ;;
  push)          shift; cmd_push "$@" ;;
  pr-create)     shift; cmd_pr_create "$@" ;;
  *)
    echo "Usage: bash scripts/housekeeping-git.sh <command> [args]"
    echo ""
    echo "Scan:   branches | branch-age | worktrees | status | log [n] | diff [ref] | all"
    echo "Action: checkout | branch-delete | stash | add | add-all | restore | rm | commit | push | pr-create"
    exit 1
    ;;
esac
