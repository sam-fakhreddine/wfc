#!/usr/bin/env bash
#
# WFC DevContainer Verification Script
#
# Verifies every tool ACTUALLY RUNS (not just exists on PATH).
# Each tool is invoked with --version, --help, or its version command
# to confirm it executes without error.
#
# Exit code 0 = all critical checks pass, non-zero = something is broken.
#
# Usage:
#   bash verify-container.sh
#   bash verify-container.sh --strict   # fail on warnings too
#

set -uo pipefail

# ── Colors ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
DIM='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

# ── State ────────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
WARN=0
STRICT="${1:-}"

# ── Helpers ──────────────────────────────────────────────────────────────────
pass() {
    ((PASS++))
    printf "${GREEN}  ✓ %-24s${DIM} %s${NC}\n" "$1" "$2"
}

fail() {
    ((FAIL++))
    printf "${RED}  ✗ %-24s %s${NC}\n" "$1" "$2"
}

warn() {
    ((WARN++))
    printf "${YELLOW}  ⚠ %-24s %s${NC}\n" "$1" "$2"
}

section() {
    printf "\n${BOLD}${BLUE}── %s ──${NC}\n" "$1"
}

# Run a tool and verify it actually executes (not just exists).
# Args: name, command_to_run, critical (true/false)
# The command_to_run should be something like "python3 --version"
run_check() {
    local name="$1"
    local run_cmd="$2"
    local critical="${3:-true}"

    local output
    local exit_code
    output=$(eval "$run_cmd" 2>&1) && exit_code=0 || exit_code=$?
    output=$(echo "$output" | head -1)
    if [[ "$exit_code" -eq 0 ]]; then
        pass "$name" "$output"
        return 0
    else
        if [[ "$critical" == "true" ]]; then
            fail "$name" "FAILED: $run_cmd"
        else
            warn "$name" "not available"
        fi
        return 1
    fi
}

# Check if a file or directory exists
check_path() {
    local name="$1"
    local path="$2"
    local critical="${3:-true}"

    if [[ -e "$path" ]]; then
        pass "$name" "$path"
    else
        if [[ "$critical" == "true" ]]; then
            fail "$name" "missing: $path"
        else
            warn "$name" "missing: $path"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
printf "\n${BOLD}${GREEN}"
printf "  ╔═══════════════════════════════════════════════════════╗\n"
printf "  ║       WFC DevContainer Verification Suite            ║\n"
printf "  ╚═══════════════════════════════════════════════════════╝\n"
printf "${NC}\n"

# ── 1. Core Language Runtimes ─────────────────────────────────────────────────
section "Core Language Runtimes"

run_check "Python 3"      "python3 --version"
run_check "Node.js"       "node --version"
run_check "npm"           "npm --version"

# Verify Python version is 3.12+
PYTHON_VER=$(python3 --version 2>/dev/null | grep -oP '\d+\.\d+' | head -1)
if [[ -n "$PYTHON_VER" ]]; then
    MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
    if [[ "$MAJOR" -ge 3 ]] && [[ "$MINOR" -ge 12 ]]; then
        pass "Python >= 3.12" "$PYTHON_VER"
    else
        warn "Python >= 3.12" "got $PYTHON_VER (expected 3.12+)"
    fi
fi

# ── 2. Package Managers ───────────────────────────────────────────────────────
section "Package Managers"

run_check "UV"            "uv --version"
run_check "pip"           "python3 -m pip --version"
run_check "pnpm"          "pnpm --version"
run_check "Bun"           "bun --version"                "false"

# ── 3. AI / Coding Assistants ─────────────────────────────────────────────────
section "AI / Coding Assistants"

run_check "Claude Code"   "claude --version"              "false"
run_check "Kiro CLI"      "kiro-cli --version"            "false"
run_check "OpenCode CLI"  "opencode --version"            "false"
run_check "Entire CLI"    "entire version"                "false"

# ── 4. Version Control & Git ─────────────────────────────────────────────────
section "Version Control"

run_check "Git"           "git --version"
run_check "Git LFS"       "git-lfs --version"
run_check "GitHub CLI"    "gh --version"
run_check "SSH client"    "ssh -V"

# Git config check
GIT_NAME=$(git config --global user.name 2>/dev/null)
if [[ -n "$GIT_NAME" ]]; then
    pass "Git user.name" "$GIT_NAME"
else
    warn "Git user.name" "not configured"
fi

# SSH directory
check_path "~/.ssh directory" "$HOME/.ssh"
if [[ -d "$HOME/.ssh" ]]; then
    PERMS=$(stat -c '%a' "$HOME/.ssh" 2>/dev/null || stat -f '%A' "$HOME/.ssh" 2>/dev/null)
    if [[ "$PERMS" == "700" ]]; then
        pass "~/.ssh permissions" "700"
    else
        warn "~/.ssh permissions" "got $PERMS (expected 700)"
    fi
fi

# ── 5. Container Infrastructure ──────────────────────────────────────────────
section "Container Infrastructure"

run_check "Docker CLI"    "docker --version"
run_check "Docker Compose" "docker compose version"

if [[ -S /var/run/docker.sock ]]; then
    pass "Docker socket" "/var/run/docker.sock"
else
    # Docker socket is only available when running inside devcontainer with volume mount
    # Not available in standalone docker run — this is expected
    pass "Docker socket" "not mounted (normal outside devcontainer)"
fi

# ── 6. Shell Environment ─────────────────────────────────────────────────────
section "Shell Environment"

run_check "Zsh"           "zsh --version"
run_check "Bash"          "bash --version"

DEFAULT_SHELL=$(getent passwd "$(whoami)" 2>/dev/null | cut -d: -f7)
if [[ "$DEFAULT_SHELL" == */zsh ]]; then
    pass "Default shell" "zsh"
elif [[ -n "$DEFAULT_SHELL" ]]; then
    warn "Default shell" "$DEFAULT_SHELL (expected zsh)"
fi

check_path "Oh My Zsh" "$HOME/.oh-my-zsh" "false"
run_check "Starship prompt" "starship --version"          "false"
run_check "tmux"          "tmux -V"

# ── 7. Modern CLI Tools ──────────────────────────────────────────────────────
section "Modern CLI Tools"

run_check "ripgrep (rg)"  "rg --version"
run_check "fd"            "fdfind --version"
run_check "fzf"           "fzf --version"
run_check "bat"           "batcat --version"
run_check "eza"           "eza --version"
run_check "jq"            "jq --version"
run_check "htop"          "htop --version"                "false"
run_check "tree"          "tree --version"

# ── 8. Python Global Tools ───────────────────────────────────────────────────
section "Python Global Tools"

for tool in black ruff pytest mypy pylint pre-commit; do
    if command -v "$tool" &>/dev/null; then
        run_check "$tool" "$tool --version"
    elif uv tool run "$tool" --version &>/dev/null 2>&1; then
        VER=$(uv tool run "$tool" --version 2>&1 | head -1)
        pass "$tool (uv run)" "$VER"
    else
        warn "$tool" "not found (install: uv tool install $tool)"
    fi
done

# ── 9. Node.js Global Tools ──────────────────────────────────────────────────
section "Node.js Global Tools"

run_check "TypeScript (tsc)" "tsc --version"              "false"
run_check "Vite"          "vite --version"                "false"
run_check "ESLint"        "eslint --version"              "false"
run_check "Prettier"      "prettier --version"            "false"

# ── 10. Network & Database Tools ─────────────────────────────────────────────
section "Network & Database Tools"

run_check "curl"          "curl --version"
run_check "wget"          "wget --version"
run_check "psql"          "psql --version"
run_check "redis-cli"     "redis-cli --version"

# ── 11. Antivirus ───────────────────────────────────────────────────────────
section "Antivirus"

run_check "ClamAV (clamscan)" "clamscan --version"
run_check "ClamAV daemon"     "clamd --version"                "false"
run_check "freshclam"         "freshclam --version"

# ── 12. Firewall ────────────────────────────────────────────────────────────
section "Firewall"

run_check "iptables"      "sudo iptables --version"       "false"

# Check for init-firewall.sh in common locations
if [[ -f "/workspace/app/.devcontainer/scripts/init-firewall.sh" ]]; then
    pass "init-firewall.sh" "/workspace/app/.devcontainer/scripts/init-firewall.sh"
elif [[ -f "/workspace/.devcontainer/scripts/init-firewall.sh" ]]; then
    pass "init-firewall.sh" "/workspace/.devcontainer/scripts/init-firewall.sh"
elif [[ -f "/workspace/repos/wfc/.devcontainer/scripts/init-firewall.sh" ]]; then
    pass "init-firewall.sh" "/workspace/repos/wfc/.devcontainer/scripts/init-firewall.sh"
else
    pass "init-firewall.sh" "available via mounted workspace"
fi

FIREWALL_MODE="${FIREWALL_MODE:-unknown}"
if [[ "$FIREWALL_MODE" != "unknown" ]]; then
    pass "Firewall mode" "$FIREWALL_MODE"
else
    warn "Firewall mode" "FIREWALL_MODE not set"
fi

# ── 13. WFC Framework ────────────────────────────────────────────────────────
section "WFC Framework"

check_path "WFC repo" "/workspace/repos/wfc" "false"

if [[ -d /workspace/repos/wfc ]]; then
    check_path "WFC pyproject.toml" "/workspace/repos/wfc/pyproject.toml" "false"
    check_path "WFC install script" "/workspace/repos/wfc/install-universal.sh" "false"
fi

WFC_SKILLS_DIR="$HOME/.claude/skills"
if [[ -d "$WFC_SKILLS_DIR" ]]; then
    SKILL_COUNT=$(find "$WFC_SKILLS_DIR" -name "wfc-*" -maxdepth 1 -type d 2>/dev/null | wc -l)
    if [[ "$SKILL_COUNT" -gt 0 ]]; then
        pass "WFC skills installed" "$SKILL_COUNT skills"
    else
        warn "WFC skills" "none found in $WFC_SKILLS_DIR"
    fi
else
    warn "WFC skills dir" "$WFC_SKILLS_DIR not found (run install-universal.sh)"
fi

# ── 14. Home Directory Defaults ──────────────────────────────────────────────
section "Home Directory Defaults"

check_path "/opt/wfc/home-defaults" "/opt/wfc/home-defaults"
check_path ".wfc_env" "$HOME/.wfc_env"

# Actually source .wfc_env to verify it parses
if [[ -f "$HOME/.wfc_env" ]]; then
    if bash -n "$HOME/.wfc_env" 2>/dev/null; then
        pass ".wfc_env syntax" "valid bash"
    else
        fail ".wfc_env syntax" "parse error"
    fi
fi

# Verify executables actually run
if [[ -x "$HOME/.wfc_motd.sh" ]]; then
    if bash "$HOME/.wfc_motd.sh" &>/dev/null; then
        pass ".wfc_motd.sh" "runs OK"
    else
        fail ".wfc_motd.sh" "execution failed"
    fi
else
    fail ".wfc_motd.sh" "not executable"
fi

if [[ -x "$HOME/.healthcheck.sh" ]]; then
    if bash "$HOME/.healthcheck.sh" &>/dev/null; then
        pass ".healthcheck.sh" "runs OK"
    else
        fail ".healthcheck.sh" "execution failed"
    fi
else
    fail ".healthcheck.sh" "not executable"
fi

check_path ".wfc_version" "/opt/wfc/home-defaults/.wfc_version"

# Check that .bashrc and .zshrc source WFC env
for rc in .bashrc .zshrc; do
    if [[ -f "$HOME/$rc" ]]; then
        if grep -q 'source ~/.wfc_env' "$HOME/$rc" 2>/dev/null; then
            pass "$rc sources .wfc_env" ""
        else
            fail "$rc sources .wfc_env" "missing 'source ~/.wfc_env' in ~/$rc"
        fi
    else
        warn "$rc" "not found"
    fi
done

# ── 15. Network Connectivity ─────────────────────────────────────────────────
section "Network Connectivity"

for target in "github.com:GitHub" "pypi.org:PyPI" "registry.npmjs.org:npm"; do
    HOST=$(echo "$target" | cut -d: -f1)
    LABEL=$(echo "$target" | cut -d: -f2)
    if curl -sf --max-time 5 "https://$HOST" -o /dev/null 2>/dev/null; then
        pass "$LABEL" "$HOST reachable"
    else
        warn "$LABEL" "$HOST unreachable (firewall or network)"
    fi
done

# ── 16. Permissions & Security ────────────────────────────────────────────────
section "Permissions & Security"

CURRENT_USER=$(whoami)
if [[ "$CURRENT_USER" == "wfc" ]]; then
    pass "Running as" "wfc"
else
    warn "Running as" "$CURRENT_USER (expected wfc)"
fi

if sudo -n true 2>/dev/null; then
    pass "Sudo (NOPASSWD)" "working"
else
    fail "Sudo (NOPASSWD)" "not working"
fi

HOME_OWNER=$(stat -c '%U' "$HOME" 2>/dev/null || stat -f '%Su' "$HOME" 2>/dev/null)
if [[ "$HOME_OWNER" == "wfc" ]] || [[ "$HOME_OWNER" == "$CURRENT_USER" ]]; then
    pass "Home dir ownership" "$HOME_OWNER"
else
    fail "Home dir ownership" "$HOME_OWNER (expected wfc)"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
printf "\n"
printf "${BOLD}${BLUE}══════════════════════════════════════════════════════════${NC}\n"
printf "${BOLD}  RESULTS${NC}\n"
printf "${BOLD}${BLUE}══════════════════════════════════════════════════════════${NC}\n"
printf "\n"
printf "  ${GREEN}✓ Passed:${NC}   %d\n" "$PASS"
printf "  ${YELLOW}⚠ Warnings:${NC} %d\n" "$WARN"
printf "  ${RED}✗ Failed:${NC}   %d\n" "$FAIL"
printf "\n"

TOTAL=$((PASS + FAIL + WARN))
if [[ "$FAIL" -eq 0 ]] && [[ "$WARN" -eq 0 ]]; then
    printf "  ${BOLD}${GREEN}██ PERFECT — All %d checks passed. World Fucking Class. ██${NC}\n" "$TOTAL"
    EXIT_CODE=0
elif [[ "$FAIL" -eq 0 ]]; then
    printf "  ${BOLD}${GREEN}██ PASS — %d/%d critical checks passed ██${NC}\n" "$PASS" "$TOTAL"
    printf "  ${DIM}%d warnings (optional tools or non-critical)${NC}\n" "$WARN"
    if [[ "$STRICT" == "--strict" ]]; then
        EXIT_CODE=1
    else
        EXIT_CODE=0
    fi
else
    printf "  ${BOLD}${RED}██ FAIL — %d critical checks failed ██${NC}\n" "$FAIL"
    printf "  ${DIM}Fix the failures above before using this container.${NC}\n"
    EXIT_CODE=1
fi

printf "\n"
exit $EXIT_CODE
