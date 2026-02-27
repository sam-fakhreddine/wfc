#!/usr/bin/env bash
# run-skill-validator.sh — Launch wfc-skill-validator-llm with z.ai or Anthropic endpoint.
#
# Usage:
#   bash scripts/run-skill-validator.sh                    # all skills, zai endpoint
#   bash scripts/run-skill-validator.sh --endpoint anthropic  # use Anthropic directly
#   bash scripts/run-skill-validator.sh --model glm-4.7   # override model
#   bash scripts/run-skill-validator.sh --dry-run         # cost estimate only
#   bash scripts/run-skill-validator.sh --stage discovery # single stage
#   bash scripts/run-skill-validator.sh path/to/skill     # single skill
#
# Env vars loaded from ~/.exportrc.sh:
#   ZAI_SKILLS_VALIDATOR      — z.ai API key
#   ANTHROPIC_SKILLS_VALIDATOR — Anthropic API key (fallback)
#   ANTHROPIC_ALTERNATE       — z.ai base URL (https://api.z.ai/api/anthropic)

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
ENDPOINT="zai"          # zai | anthropic
MODEL="glm-5"           # model when using zai
LOG_FILE="/tmp/wfc-validator-run.log"
EXTRA_ARGS=()
SINGLE_SKILL=""

# ── Parse args ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --endpoint)
      ENDPOINT="$2"; shift 2 ;;
    --model)
      MODEL="$2"; shift 2 ;;
    --log)
      LOG_FILE="$2"; shift 2 ;;
    --dry-run|--offline|--yes|-y)
      EXTRA_ARGS+=("$1"); shift ;;
    --stage|--stage=*)
      # --stage takes a value
      if [[ "$1" == --stage=* ]]; then
        EXTRA_ARGS+=("$1"); shift
      else
        EXTRA_ARGS+=("$1" "$2"); shift 2
      fi ;;
    -*)
      EXTRA_ARGS+=("$1"); shift ;;
    *)
      SINGLE_SKILL="$1"; shift ;;
  esac
done

# ── Load env ─────────────────────────────────────────────────────────────────
if [[ -f "$HOME/.exportrc.sh" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.exportrc.sh"
fi

# ── Configure endpoint ────────────────────────────────────────────────────────
if [[ "$ENDPOINT" == "zai" ]]; then
  export ANTHROPIC_ALTERNATE="${ANTHROPIC_ALTERNATE:-https://api.z.ai/api/anthropic}"
  export SKILLS_VALIDATOR_MODEL="$MODEL"
  echo "[validator] Endpoint: z.ai  (${ANTHROPIC_ALTERNATE})"
  echo "[validator] Model:    ${SKILLS_VALIDATOR_MODEL}"
else
  unset ANTHROPIC_ALTERNATE 2>/dev/null || true
  export SKILLS_VALIDATOR_MODEL="claude-sonnet-4-6"
  echo "[validator] Endpoint: Anthropic (direct)"
  echo "[validator] Model:    ${SKILLS_VALIDATOR_MODEL}"
fi

# ── Build CLI args ────────────────────────────────────────────────────────────
CLI_ARGS=()
if [[ -n "$SINGLE_SKILL" ]]; then
  CLI_ARGS+=("$SINGLE_SKILL")
else
  CLI_ARGS+=("--all" "--yes")
fi
CLI_ARGS+=("${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}")

# ── Resolve output root ───────────────────────────────────────────────────────
_REPO="${WFC_CORPUS_REPO:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo wfc)}"
_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
OUTPUT_ROOT="$HOME/.wfc/projects/${_REPO}/branches/${_BRANCH}/docs/skill-validation"

# ── Run ───────────────────────────────────────────────────────────────────────
echo "[validator] Log:      ${LOG_FILE}"
echo "[validator] Reports:  ${OUTPUT_ROOT}"
echo "[validator] Args:     ${CLI_ARGS[*]}"
echo "[validator] Starting  $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

uv run python -m wfc.scripts.orchestrators.skill_validator_llm.cli "${CLI_ARGS[@]}" 2>&1 | tee "$LOG_FILE"
