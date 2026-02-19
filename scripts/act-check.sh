#!/usr/bin/env bash
# scripts/act-check.sh — Run GitHub Actions workflows locally via act
# Usage: ./scripts/act-check.sh [--fast]
#
# --fast: runs only lint (ci.yml) + validate-skills (validate.yml)
#         completes in ~2 minutes vs ~10 minutes for full run
#
# Bypass: WFC_SKIP_ACT=1 git push  (skips hook, not this script)
# Secrets: create .act.secrets (gitignored) for local secret injection

set -euo pipefail

FAST_MODE=false
[[ "${1:-}" == "--fast" ]] && FAST_MODE=true

# macOS ships gtimeout (brew install coreutils), Linux ships timeout
TIMEOUT_CMD=$(command -v gtimeout 2>/dev/null || command -v timeout 2>/dev/null || true)
if [[ -z "$TIMEOUT_CMD" ]]; then
  echo "⚠  No timeout command found. Install via: brew install coreutils"
  echo "   Continuing without timeout protection (PROP-003 degraded)."
fi

# Fail fast if Docker is not running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Start Docker Desktop first."
  exit 1
fi

START=$(date +%s)

# Build optional flags
SECRET_FLAGS=()
if [[ -f ".act.secrets" ]]; then
  SECRET_FLAGS+=(--secret-file .act.secrets)
fi

run_act() {
  local workflow="$1"; shift
  echo "▶  Running $workflow locally via act..."
  if [[ -n "$TIMEOUT_CMD" ]]; then
    "$TIMEOUT_CMD" 900 act -W ".github/workflows/$workflow" "${SECRET_FLAGS[@]}" "$@"
  else
    act -W ".github/workflows/$workflow" "${SECRET_FLAGS[@]}" "$@"
  fi
}

if $FAST_MODE; then
  echo "⚡ Fast mode: lint + validate-skills only"
  run_act ci.yml -j lint
  run_act validate.yml -j validate-skills
else
  run_act ci.yml --matrix os:ubuntu-latest
  run_act validate.yml
fi

ELAPSED=$(( $(date +%s) - START ))
echo "✅ All local act checks passed in ${ELAPSED}s"
