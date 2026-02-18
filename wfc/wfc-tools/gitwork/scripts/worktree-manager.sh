#!/bin/bash

# WFC Worktree Manager
# Reliable worktree lifecycle: create, list, switch, cleanup, env sync
# NEVER call `git worktree add` directly — always use this script.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [[ -z "$GIT_ROOT" ]]; then
  echo -e "${RED}Error: Not inside a git repository${NC}"
  exit 1
fi

WORKTREE_DIR="$GIT_ROOT/.worktrees"

# --- Helpers ---

ensure_gitignore() {
  local gitignore="$GIT_ROOT/.gitignore"
  if ! grep -q "^\.worktrees$" "$gitignore" 2>/dev/null; then
    echo ".worktrees" >> "$gitignore"
    echo -e "  ${GREEN}+ Added .worktrees to .gitignore${NC}"
  fi
}

copy_env_files() {
  local dest="$1"
  local copied=0

  for f in "$GIT_ROOT"/.env*; do
    [[ -f "$f" ]] || continue
    local name=$(basename "$f")
    [[ "$name" == ".env.example" ]] && continue

    if [[ -f "$dest/$name" ]]; then
      cp "$dest/$name" "$dest/${name}.backup"
      echo -e "  ${YELLOW}Backed up existing $name${NC}"
    fi

    cp "$f" "$dest/$name"
    echo -e "  ${GREEN}+ $name${NC}"
    copied=$((copied + 1))
  done

  if [[ $copied -eq 0 ]]; then
    echo -e "  ${YELLOW}No .env files found in repo root${NC}"
  else
    echo -e "  ${GREEN}Copied $copied env file(s)${NC}"
  fi
}

copy_config_files() {
  local dest="$1"
  local copied=0

  # Copy project config files that worktrees need
  for config in ".tool-versions" ".node-version" ".python-version" ".nvmrc" ".ruby-version"; do
    if [[ -f "$GIT_ROOT/$config" && ! -f "$dest/$config" ]]; then
      cp "$GIT_ROOT/$config" "$dest/$config"
      echo -e "  ${GREEN}+ $config${NC}"
      copied=$((copied + 1))
    fi
  done

  if [[ $copied -gt 0 ]]; then
    echo -e "  ${GREEN}Copied $copied config file(s)${NC}"
  fi
}

install_deps() {
  local dest="$1"

  # Auto-install dependencies if lock files exist
  if [[ -f "$dest/uv.lock" ]] || [[ -f "$dest/pyproject.toml" ]]; then
    echo -e "  ${BLUE}Installing Python deps (uv)...${NC}"
    (cd "$dest" && uv pip install -e ".[all]" 2>/dev/null) || true
  fi

  if [[ -f "$dest/package-lock.json" ]]; then
    echo -e "  ${BLUE}Installing Node deps (npm)...${NC}"
    (cd "$dest" && npm install --silent 2>/dev/null) || true
  elif [[ -f "$dest/yarn.lock" ]]; then
    echo -e "  ${BLUE}Installing Node deps (yarn)...${NC}"
    (cd "$dest" && yarn install --silent 2>/dev/null) || true
  elif [[ -f "$dest/pnpm-lock.yaml" ]]; then
    echo -e "  ${BLUE}Installing Node deps (pnpm)...${NC}"
    (cd "$dest" && pnpm install --silent 2>/dev/null) || true
  elif [[ -f "$dest/bun.lock" ]] || [[ -f "$dest/bun.lockb" ]]; then
    echo -e "  ${BLUE}Installing Node deps (bun)...${NC}"
    (cd "$dest" && bun install 2>/dev/null) || true
  fi
}

# --- Commands ---

cmd_create() {
  local branch_name="$1"
  local from_branch="${2:-develop}"

  if [[ -z "$branch_name" ]]; then
    echo -e "${RED}Usage: worktree-manager.sh create <branch-name> [from-branch]${NC}"
    exit 1
  fi

  local worktree_path="$WORKTREE_DIR/wfc-$branch_name"

  if [[ -d "$worktree_path" ]]; then
    echo -e "${YELLOW}Worktree already exists: $worktree_path${NC}"
    echo -e "Use 'switch $branch_name' to enter it."
    return 0
  fi

  echo -e "${BLUE}Creating worktree: wfc-$branch_name${NC}"
  echo "  Base: $from_branch"
  echo "  Path: $worktree_path"

  mkdir -p "$WORKTREE_DIR"
  ensure_gitignore

  # Fetch latest from remote (non-blocking)
  git fetch origin "$from_branch" 2>/dev/null || true

  # Create worktree with wfc/ branch prefix
  local wfc_branch="wfc/$branch_name"
  git worktree add "$worktree_path" -b "$wfc_branch" "origin/$from_branch" 2>/dev/null \
    || git worktree add "$worktree_path" -b "$wfc_branch" "$from_branch"

  echo -e "${BLUE}Syncing environment...${NC}"
  copy_env_files "$worktree_path"
  copy_config_files "$worktree_path"

  echo ""
  echo -e "${GREEN}Worktree ready!${NC}"
  echo -e "  cd $worktree_path"
  echo ""
}

cmd_list() {
  echo -e "${BLUE}WFC Worktrees:${NC}"
  echo ""

  local count=0
  local current_dir=$(pwd)

  # Show main repo
  local main_branch=$(git -C "$GIT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  if [[ "$current_dir" == "$GIT_ROOT" ]]; then
    echo -e "  ${GREEN}* main-repo${NC} ($main_branch) ← you are here"
  else
    echo -e "    main-repo ($main_branch)"
  fi

  if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo ""
    echo -e "${YELLOW}No worktrees${NC}"
    return
  fi

  for wt in "$WORKTREE_DIR"/wfc-*; do
    [[ -d "$wt" && -e "$wt/.git" ]] || continue
    count=$((count + 1))
    local name=$(basename "$wt" | sed 's/^wfc-//')
    local branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
    local changes=$(git -C "$wt" status --short 2>/dev/null | wc -l | tr -d ' ')

    local marker="  "
    [[ "$current_dir" == "$wt" ]] && marker="${GREEN}* ${NC}"

    local status_info=""
    [[ "$changes" -gt 0 ]] && status_info=" ${YELLOW}[$changes uncommitted]${NC}"

    echo -e "  ${marker}${name} (${branch})${status_info}"
  done

  echo ""
  echo -e "${BLUE}Total: $count worktree(s)${NC}"
}

cmd_switch() {
  local name="$1"

  if [[ -z "$name" ]]; then
    cmd_list
    echo ""
    echo -e "${BLUE}Enter worktree name to switch to:${NC}"
    read -r name
  fi

  local worktree_path="$WORKTREE_DIR/wfc-$name"

  if [[ ! -d "$worktree_path" ]]; then
    echo -e "${RED}Worktree not found: $name${NC}"
    cmd_list
    exit 1
  fi

  echo -e "${GREEN}Switched to: $worktree_path${NC}"
  cd "$worktree_path"
  pwd
}

cmd_copy_env() {
  local name="$1"
  local dest

  if [[ -n "$name" ]]; then
    dest="$WORKTREE_DIR/wfc-$name"
  elif [[ "$(pwd)" == "$WORKTREE_DIR"/wfc-* ]]; then
    dest="$(pwd)"
    name=$(basename "$dest" | sed 's/^wfc-//')
  else
    echo -e "${RED}Usage: worktree-manager.sh copy-env <worktree-name>${NC}"
    exit 1
  fi

  if [[ ! -d "$dest" ]]; then
    echo -e "${RED}Worktree not found: $name${NC}"
    exit 1
  fi

  echo -e "${BLUE}Syncing env files to $name...${NC}"
  copy_env_files "$dest"
}

cmd_cleanup() {
  if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo -e "${GREEN}Nothing to clean up${NC}"
    return
  fi

  local current_dir=$(pwd)
  local removed=0

  echo -e "${BLUE}Cleaning up worktrees...${NC}"

  for wt in "$WORKTREE_DIR"/wfc-*; do
    [[ -d "$wt" && -e "$wt/.git" ]] || continue

    # Never remove current worktree
    if [[ "$current_dir" == "$wt" ]]; then
      echo -e "  ${YELLOW}Skip $(basename "$wt") (currently active)${NC}"
      continue
    fi

    local name=$(basename "$wt")
    local branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
    local changes=$(git -C "$wt" status --short 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$changes" -gt 0 ]]; then
      echo -e "  ${YELLOW}Skip $name ($changes uncommitted changes)${NC}"
      continue
    fi

    git worktree remove "$wt" --force 2>/dev/null || rm -rf "$wt"
    echo -e "  ${GREEN}Removed $name${NC}"
    removed=$((removed + 1))
  done

  # Prune stale worktree references
  git worktree prune 2>/dev/null || true

  # Remove empty .worktrees dir
  if [[ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKTREE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $removed worktree(s)${NC}"
}

cmd_status() {
  local name="$1"

  if [[ -z "$name" ]]; then
    # Status of all worktrees
    for wt in "$WORKTREE_DIR"/wfc-*; do
      [[ -d "$wt" && -e "$wt/.git" ]] || continue
      local wt_name=$(basename "$wt" | sed 's/^wfc-//')
      echo -e "${BLUE}$wt_name:${NC}"
      git -C "$wt" status --short 2>/dev/null || echo "  (no status)"
      echo ""
    done
    return
  fi

  local worktree_path="$WORKTREE_DIR/wfc-$name"
  if [[ ! -d "$worktree_path" ]]; then
    echo -e "${RED}Worktree not found: $name${NC}"
    exit 1
  fi

  echo -e "${BLUE}Status of $name:${NC}"
  git -C "$worktree_path" status 2>/dev/null
}

cmd_help() {
  cat << 'EOF'
WFC Worktree Manager

Usage: worktree-manager.sh <command> [options]

Commands:
  create <name> [base]   Create worktree (default base: develop)
                         Auto-copies .env files, config files
                         Creates wfc/<name> branch
  list | ls              List all worktrees with status
  switch | go <name>     Switch to worktree
  status [name]          Show git status (all or specific)
  copy-env | env <name>  Sync .env files from repo root
  cleanup | clean        Remove clean worktrees (skips dirty ones)
  help                   Show this message

What it does that raw `git worktree add` doesn't:
  - Copies .env, .env.local, .env.test (not .env.example)
  - Copies .tool-versions, .node-version, .python-version, .nvmrc
  - Ensures .worktrees is in .gitignore
  - Uses wfc/ branch naming convention
  - Defaults to develop as base branch
  - Skips cleanup of dirty worktrees (uncommitted changes)
  - Prunes stale git worktree references

Examples:
  worktree-manager.sh create TASK-001
  worktree-manager.sh create TASK-001 main
  worktree-manager.sh switch TASK-001
  worktree-manager.sh status TASK-001
  worktree-manager.sh copy-env TASK-001
  worktree-manager.sh cleanup
EOF
}

# --- Main ---

case "${1:-help}" in
  create)      cmd_create "$2" "$3" ;;
  list|ls)     cmd_list ;;
  switch|go)   cmd_switch "$2" ;;
  status)      cmd_status "$2" ;;
  copy-env|env) cmd_copy_env "$2" ;;
  cleanup|clean) cmd_cleanup ;;
  help|--help|-h) cmd_help ;;
  *)
    echo -e "${RED}Unknown command: $1${NC}"
    cmd_help
    exit 1
    ;;
esac
