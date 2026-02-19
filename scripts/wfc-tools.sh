#!/usr/bin/env bash
# scripts/wfc-tools.sh
# Single helper script replacing bare sed, ls, awk, find, etc.
# Cross-platform: macOS (BSD) and Linux (GNU). No eval, no glob hacks.
#
# Usage: bash scripts/wfc-tools.sh <command> [args...]
#
# Commands:
#   ls [path]                          List directory contents
#   find-files <glob> [path]           Find files by name pattern
#   find-empty [path] [ext]            Find empty files
#   find-large [path] [size_mb]        Find files larger than N MB (default: 1)
#   find-temp [path]                   Find temp/backup files (.tmp .bak .swp .orig)
#   find-tracked <glob>                Find git-tracked files by pattern
#   replace <old> <new> [path] [ext]   Bulk in-place replacement (cross-platform)
#   count <pattern> [path] [ext]       Count lines matching pattern across files
#   extract-col <col> [sep]            Extract column N from stdin (awk wrapper)
#   strip-trailing [path] [ext]        Strip trailing whitespace from files
#   show-large-files [path] [limit]    Show N largest files (default: 10)

set -euo pipefail

OS="$(uname)"

# ─── Cross-platform primitives ────────────────────────────────────────────────

# sed -i requires an empty-string suffix on macOS BSD sed, not on GNU sed.
_sed_inplace() {
  if [ "$OS" = "Darwin" ]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# ls color flag differs: -G on BSD/macOS, --color=auto on GNU/Linux.
_ls() {
  if [ "$OS" = "Darwin" ]; then
    ls -lA -G "$@"
  else
    ls -lA --color=auto "$@"
  fi
}

# _find <path> [find-expressions-including-action]
# Wraps find with consistent noise-dir exclusion via -prune.
# Callers MUST supply their own action (-print, -print0, -exec, etc.).
# No action is appended automatically — avoids conflicts with -print0/-exec.
_find() {
  local path="$1"
  shift
  find "$path" \
    \( \
      -path '*/.git/*' \
      -o -path '*/.venv/*' \
      -o -path '*/node_modules/*' \
      -o -path '*/__pycache__/*' \
      -o -path '*/.entire/*' \
    \) -prune \
    -o "$@"
}

# ─── Commands ─────────────────────────────────────────────────────────────────

cmd_ls() {
  local path="${1:-.}"
  _ls "$path"
}

cmd_find_files() {
  local glob="${1:?Usage: find-files <glob> [path]}"
  local path="${2:-.}"
  _find "$path" -name "$glob" -print | sort
}

cmd_find_empty() {
  local path="${1:-.}"
  local ext="${2:-py}"
  _find "$path" -name "*.${ext}" -empty -print | sort
}

cmd_find_large() {
  local path="${1:-.}"
  local size_mb="${2:-1}"
  _find "$path" -size "+${size_mb}M" -print | sort
}

cmd_find_temp() {
  local path="${1:-.}"
  _find "$path" \( -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*.orig" \) -print | sort
}

cmd_find_tracked() {
  local glob="${1:?Usage: find-tracked <glob>}"
  git ls-files "$glob"
}

# Bulk in-place replacement. Uses find+loop — no **/*.py glob, no eval.
cmd_replace() {
  local old="${1:?Usage: replace <old> <new> [path] [ext]}"
  local new="${2:?Usage: replace <old> <new> [path] [ext]}"
  local path="${3:-.}"
  local ext="${4:-py}"

  echo "Replacing: '${old}' → '${new}'"
  echo "Path: ${path}  Extension: *.${ext}"
  echo ""

  local count=0
  while IFS= read -r file; do
    if [ -f "$file" ] && grep -q "$old" "$file" 2>/dev/null; then
      _sed_inplace "s|${old}|${new}|g" "$file"
      echo "  updated: $file"
      count=$((count + 1))
    fi
  done < <(_find "$path" -name "*.${ext}" -print)

  echo ""
  echo "Done: ${count} file(s) updated."
}

cmd_count() {
  local pattern="${1:?Usage: count <pattern> [path] [ext]}"
  local path="${2:-.}"
  local ext="${3:-py}"

  local total=0
  while IFS= read -r file; do
    if [ -f "$file" ]; then
      local n
      n=$(grep -c "$pattern" "$file" 2>/dev/null || true)
      if [ "$n" -gt 0 ]; then
        echo "${file}: ${n}"
        total=$((total + n))
      fi
    fi
  done < <(_find "$path" -name "*.${ext}" -print)

  echo "---"
  echo "Total: ${total} matches"
}

# Reads stdin, prints column N. POSIX awk — works on both BSD and GNU.
cmd_extract_col() {
  local col="${1:?Usage: extract-col <col> [sep]}"
  local sep="${2:-}"
  if [ -n "$sep" ]; then
    awk -F"$sep" "{ print \$$col }"
  else
    awk "{ print \$$col }"
  fi
}

# Uses POSIX ERE [[:space:]] — no grep -P, works on BSD and GNU grep.
cmd_strip_trailing() {
  local path="${1:-.}"
  local ext="${2:-py}"
  local count=0

  while IFS= read -r file; do
    if [ -f "$file" ] && grep -qE '[[:space:]]+$' "$file" 2>/dev/null; then
      _sed_inplace 's/[[:space:]]*$//' "$file"
      echo "  stripped: $file"
      count=$((count + 1))
    fi
  done < <(_find "$path" -name "*.${ext}" -print)

  echo "Done: ${count} file(s) cleaned."
}

# Uses find -exec du -k to avoid xargs -print0 portability issues.
# du -k is POSIX and works on both BSD and GNU.
cmd_show_large_files() {
  local path="${1:-.}"
  local limit="${2:-10}"
  _find "$path" -type f -exec du -k {} + \
    | sort -rn \
    | head -"$limit" \
    | awk '{ printf "%8.1f KB  %s\n", $1, $2 }'
}

# ─── Dispatch ─────────────────────────────────────────────────────────────────
case "${1:-}" in
  ls)               shift; cmd_ls "$@" ;;
  find-files)       shift; cmd_find_files "$@" ;;
  find-empty)       shift; cmd_find_empty "$@" ;;
  find-large)       shift; cmd_find_large "$@" ;;
  find-temp)        shift; cmd_find_temp "$@" ;;
  find-tracked)     shift; cmd_find_tracked "$@" ;;
  replace)          shift; cmd_replace "$@" ;;
  count)            shift; cmd_count "$@" ;;
  extract-col)      shift; cmd_extract_col "$@" ;;
  strip-trailing)   shift; cmd_strip_trailing "$@" ;;
  show-large-files) shift; cmd_show_large_files "$@" ;;
  *)
    echo "Usage: bash scripts/wfc-tools.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  ls [path]                        List directory"
    echo "  find-files <glob> [path]         Find files by name"
    echo "  find-empty [path] [ext]          Find empty files"
    echo "  find-large [path] [size_mb]      Find files > N MB"
    echo "  find-temp [path]                 Find .tmp/.bak/.swp/.orig files"
    echo "  find-tracked <glob>              Find git-tracked files by pattern"
    echo "  replace <old> <new> [path] [ext] Bulk in-place replacement"
    echo "  count <pattern> [path] [ext]     Count pattern matches across files"
    echo "  extract-col <col> [sep]          Extract column from stdin"
    echo "  strip-trailing [path] [ext]      Strip trailing whitespace"
    echo "  show-large-files [path] [limit]  Show N largest files"
    echo ""
    echo "Platform: ${OS}"
    exit 1
    ;;
esac
