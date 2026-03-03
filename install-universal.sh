#!/usr/bin/env bash
set -euo pipefail

# Require bash 4+ for associative arrays (declare -A)
if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    for candidate in /opt/homebrew/bin/bash /usr/local/bin/bash; do
        if [ -x "$candidate" ]; then
            exec "$candidate" "$0" "$@"
        fi
    done
    echo "Error: bash 4+ required. Install with: brew install bash"
    exit 1
fi

# WFC Universal Installer - Agent Skills Standard Compatible
# Detects and installs to: Claude Code, Kiro, OpenCode, Cursor, VS Code, Codex, Antigravity
#
# Usage:
#   ./install-universal.sh                    - Interactive (local clone)
#   ./install-universal.sh --ci               - Non-interactive CI mode
#   ./install-universal.sh --agent claude     - Install for specific platform
#   ./install-universal.sh --help             - Show help
#
# Remote install:
#   curl -fsSL https://raw.githubusercontent.com/sam-fakhreddine/wfc/main/install-universal.sh | bash
#
# Features:
#   - Auto-detects installed Agent Skills platforms
#   - Supports 8+ platforms (Claude Code, Kiro, OpenCode, etc.)
#   - Remote install via curl pipe (clones repo to /tmp)
#   - Branding modes: SFW (Workflow Champion) or NSFW (World Fucking Class)
#   - PostToolUse quality hooks (auto-lint, TDD, context monitor)
#   - Progressive disclosure (92% token reduction)
#   - Symlink support for multi-platform sync

VERSION="0.8.0"
REPO="sam-fakhreddine/wfc"
REPO_URL="https://github.com/${REPO}.git"

# ============================================================================
# Color support
# ============================================================================
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RESET="\033[0m"

# ============================================================================
# Helpers
# ============================================================================
print_ok()    { echo -e "  ${GREEN}✓${RESET} $1"; }
print_warn()  { echo -e "  ${YELLOW}!${RESET} $1"; }
print_error() { echo -e "  ${RED}✗${RESET} $1"; }

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}${BOLD}║        WFC Universal Installer           ║${RESET}"
    echo -e "${CYAN}${BOLD}║     Agent Skills Standard Compatible     ║${RESET}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════╝${RESET}"
    echo -e "  ${BOLD}Version:${RESET}  ${VERSION}"
    echo ""
}

get_platform_path() {
    case "$1" in
        claude)       echo "$HOME/.claude/skills" ;;
        kiro)         echo "$HOME/.kiro/skills" ;;
        opencode)
            if [ -d "$HOME/.config/opencode" ]; then
                echo "$HOME/.config/opencode/skills"
            else
                echo "$HOME/.opencode/skills"
            fi ;;
        cursor)
            if [ -d "$HOME/Library/Application Support/Cursor" ]; then
                echo "$HOME/Library/Application Support/Cursor/skills"
            else
                echo "$HOME/.cursor/skills"
            fi ;;
        vscode)
            if [ -d "$HOME/Library/Application Support/Code" ]; then
                echo "$HOME/Library/Application Support/Code/User/skills"
            else
                echo "$HOME/.vscode/skills"
            fi ;;
        codex)
            if [ -d "$HOME/.openai/codex" ]; then
                echo "$HOME/.openai/codex/skills"
            else
                echo "$HOME/.codex/skills"
            fi ;;
        antigravity)
            if [ -d "$HOME/.config/antigravity" ]; then
                echo "$HOME/.config/antigravity/skills"
            else
                echo "$HOME/.antigravity/skills"
            fi ;;
        goose)        echo "$HOME/.config/goose/skills" ;;
    esac
}

get_platform_name() {
    case "$1" in
        claude)       echo "Claude Code" ;;
        kiro)         echo "Kiro (AWS)" ;;
        opencode)     echo "OpenCode" ;;
        cursor)       echo "Cursor" ;;
        vscode)       echo "VS Code" ;;
        codex)        echo "OpenAI Codex" ;;
        antigravity)  echo "Google Antigravity" ;;
        goose)        echo "Goose" ;;
    esac
}

show_help() {
    cat << 'EOF'
WFC Universal Installer
=======================

USAGE:
    ./install.sh                        Interactive installation
    ./install.sh --help                 Show this help
    ./install.sh --ci                   Non-interactive CI mode
    ./install.sh --agent <name>         Install for a specific platform

AGENTS:
    claude, kiro, opencode, cursor, vscode, codex, antigravity, goose, all

EXAMPLES:
    ./install.sh --agent claude         Install for Claude Code only
    ./install.sh --agent all            Install for all detected platforms
    ./install.sh --agent claude --sfw   Install with SFW branding

FLAGS:
    --ci            Non-interactive (defaults: all platforms, NSFW branding)
    --agent NAME    Target a specific platform (non-interactive)
    --sfw           Use SFW branding ("Workflow Champion")
    --nsfw          Use NSFW branding ("World Fucking Class", default)
    -h, --help      Show this help

SUPPORTED PLATFORMS:
    Claude Code     ~/.claude/skills
    Kiro (AWS)      ~/.kiro/skills
    OpenCode        ~/.config/opencode/skills
    Cursor          ~/.cursor/skills
    VS Code         ~/.vscode/skills
    OpenAI Codex    ~/.codex/skills
    Antigravity     ~/.antigravity/skills
    Goose           ~/.config/goose/skills

EOF
    exit 0
}

# ============================================================================
# Parse arguments
# ============================================================================
CI_MODE=false
AGENT_FLAG=""
BRANDING_FLAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ci|--non-interactive)  CI_MODE=true; shift ;;
        --agent)                 AGENT_FLAG="$2"; shift 2 ;;
        --sfw)                   BRANDING_FLAG="sfw"; shift ;;
        --nsfw)                  BRANDING_FLAG="nsfw"; shift ;;
        -h|--help)               show_help ;;
        *)  echo "Unknown option: $1"; show_help ;;
    esac
done

# ============================================================================
# REMOTE INSTALL: If running via curl pipe, clone repo first
# ============================================================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" 2>/dev/null )" 2>/dev/null && pwd 2>/dev/null )" || SCRIPT_DIR=""
REMOTE_INSTALL=false

if [ -z "$SCRIPT_DIR" ] || [ ! -d "$SCRIPT_DIR/wfc/skills" ]; then
    REMOTE_INSTALL=true
    CLONE_DIR="/tmp/wfc-install-$$"

    echo -e "${BOLD}Remote install - fetching WFC...${RESET}"

    if ! command -v git >/dev/null 2>&1; then
        print_error "git is required. Install git first."
        exit 1
    fi

    git clone --depth 1 "$REPO_URL" "$CLONE_DIR" 2>/dev/null
    SCRIPT_DIR="$CLONE_DIR"
    print_ok "WFC fetched"
    echo ""

    trap 'rm -rf $CLONE_DIR' EXIT
fi

# ============================================================================
# SOURCE VALIDATION: Verify repo is complete before attempting install
# ============================================================================
validate_source() {
    local skills_src="$SCRIPT_DIR/wfc/skills"
    local missing=0

    if [ ! -d "$skills_src" ]; then
        print_error "Skills directory not found: $skills_src"
        echo -e "\n${RED}${BOLD}Source validation failed.${RESET} Is this a complete clone?"
        echo -e "  Try: ${CYAN}git clone https://github.com/sam-fakhreddine/wfc.git${RESET}\n"
        exit 1
    fi

    for skill_dir in "$skills_src"/wfc-*/; do
        [ -d "$skill_dir" ] || continue
        if [ ! -f "$skill_dir/SKILL.md" ]; then
            print_error "Missing: $(basename "$skill_dir")/SKILL.md"
            missing=$((missing + 1))
        fi
    done

    if [ "$missing" -gt 0 ]; then
        echo -e "\n${RED}${BOLD}Source validation failed.${RESET} $missing skill(s) missing SKILL.md."
        echo -e "  Try: ${CYAN}git pull origin develop${RESET}\n"
        exit 1
    fi

    local skill_count
    skill_count=$(find "$skills_src" -maxdepth 1 -type d -name "wfc-*" | wc -l | tr -d ' ')
    print_ok "Source validated ($skill_count skills found)"
}

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
check_dependencies() {
    local missing=()

    if ! command -v uv >/dev/null 2>&1; then
        missing+=("uv")
    fi
    if ! command -v git >/dev/null 2>&1; then
        missing+=("git")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        print_warn "Optional dependencies not found: ${missing[*]}"

        if [[ " ${missing[*]} " =~ " uv " ]]; then
            echo -e "   Install uv: ${CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${RESET}"
        fi
        echo ""
    fi
}

print_header
validate_source
check_dependencies

# Check for existing installation
EXISTING_INSTALL=false
EXISTING_BRANDING=""
EXISTING_MODE=""
KEEP_SETTINGS=false

if [ -d "$HOME/.wfc" ]; then
    EXISTING_INSTALL=true
    if [ -f "$HOME/.wfc/.wfc_branding" ]; then
        EXISTING_MODE=$(grep "^mode=" "$HOME/.wfc/.wfc_branding" 2>/dev/null | cut -d'=' -f2) || true
        EXISTING_BRANDING=$(grep "^name=" "$HOME/.wfc/.wfc_branding" 2>/dev/null | cut -d'=' -f2) || true
    fi
fi

# Reinstall handling
if [ "$EXISTING_INSTALL" = true ]; then
    if [ "$CI_MODE" = true ] || [ -n "$AGENT_FLAG" ]; then
        # Non-interactive: always update, preserve settings
        print_ok "Existing install detected — updating files (settings preserved)"
        KEEP_SETTINGS=true
        if [ -n "$EXISTING_MODE" ]; then
            WFC_MODE="$EXISTING_MODE"
        fi
    else
        echo -e "${YELLOW}!${RESET}  Existing WFC installation detected"
        if [ -n "$EXISTING_BRANDING" ]; then
            echo -e "   Current: ${CYAN}$EXISTING_BRANDING${RESET} (${EXISTING_MODE})"
        fi
        echo ""
        echo -e "  1) ${GREEN}Update${RESET}     Update skills & hooks, keep branding and rules"
        echo -e "  2) ${RED}Reinstall${RESET}  Clean install with backup (choose branding again)"
        echo -e "  3) ${BLUE}Cancel${RESET}"
        echo ""
        read -rp "Choose [1-3]: " REINSTALL_CHOICE

        case ${REINSTALL_CHOICE:-1} in
            1)
                print_ok "Updating installation..."
                KEEP_SETTINGS=true
                if [ -n "$EXISTING_MODE" ]; then
                    WFC_MODE="$EXISTING_MODE"
                fi
                ;;
            2)
                BACKUP_DIR="$HOME/.wfc_backup_$(date +%Y%m%d_%H%M%S)"
                mkdir -p "$BACKUP_DIR"
                [ -f "$HOME/.wfc/.wfc_branding" ] && cp "$HOME/.wfc/.wfc_branding" "$BACKUP_DIR/"
                [ -d "$HOME/.wfc/rules" ] && cp -r "$HOME/.wfc/rules" "$BACKUP_DIR/rules"
                print_ok "Backup saved to: ${CYAN}$BACKUP_DIR${RESET}"
                KEEP_SETTINGS=false
                ;;
            3)
                echo -e "${BLUE}Cancelled${RESET}"
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
        echo ""
    fi
fi

# Resolve branding from existing settings or flags
set_branding() {
    local mode="${1:-nsfw}"
    WFC_MODE="$mode"
    if [ "$mode" = "sfw" ]; then
        WFC_NAME="Workflow Champion"
        WFC_TAGLINE="Professional Multi-Agent Framework"
    else
        WFC_NAME="World Fucking Class"
        WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"
    fi
}

# Branding mode selection (skip if keeping settings with known mode)
if [ "$KEEP_SETTINGS" = true ] && [ -n "${WFC_MODE:-}" ]; then
    set_branding "$WFC_MODE"
elif [ -n "$BRANDING_FLAG" ]; then
    set_branding "$BRANDING_FLAG"
elif [ "$CI_MODE" = true ] || [ -n "$AGENT_FLAG" ]; then
    set_branding "nsfw"
    print_ok "Using ${MAGENTA}World Fucking Class${RESET} (NSFW)"
else
    echo -e "${BOLD}Choose branding mode:${RESET}"
    echo ""
    echo -e "  1) ${BOLD}SFW${RESET}   ${GREEN}Workflow Champion${RESET}       Professional, corporate-friendly"
    echo -e "  2) ${BOLD}NSFW${RESET}  ${MAGENTA}World Fucking Class${RESET}   Original branding (default)"
    echo ""
    read -rp "Choose [1-2, default: 2]: " BRANDING_CHOICE

    case ${BRANDING_CHOICE:-2} in
        1)  set_branding "sfw";  print_ok "Selected: ${GREEN}Workflow Champion${RESET} (SFW)" ;;
        *)  set_branding "nsfw"; print_ok "Selected: ${MAGENTA}World Fucking Class${RESET} (NSFW)" ;;
    esac
fi

echo ""
echo -e "${BOLD}Installing ${WFC_NAME}${RESET}"
echo -e "   ${WFC_TAGLINE}"
echo ""

# ============================================================================
# Platform detection
# ============================================================================
declare -A PLATFORMS
declare -A PLATFORM_PATHS

# Canonical platform order
PLATFORM_ORDER=(claude kiro opencode cursor vscode codex antigravity goose)

detect_platform() {
    local key="$1"
    case "$key" in
        claude)       [ -d "$HOME/.claude" ] ;;
        kiro)         [ -d "$HOME/.kiro" ] ;;
        opencode)     [ -d "$HOME/.config/opencode" ] || [ -d "$HOME/.opencode" ] ;;
        cursor)       [ -d "$HOME/.cursor" ] || [ -d "$HOME/Library/Application Support/Cursor" ] ;;
        vscode)       [ -d "$HOME/.vscode" ] || [ -d "$HOME/Library/Application Support/Code" ] ;;
        codex)        [ -d "$HOME/.codex" ] || [ -d "$HOME/.openai/codex" ] ;;
        antigravity)  [ -d "$HOME/.antigravity" ] || [ -d "$HOME/.config/antigravity" ] ;;
        goose)        [ -d "$HOME/.config/goose" ] ;;
        *)            return 1 ;;
    esac
}

echo -e "${BOLD}Detecting platforms...${RESET}"
echo ""

DETECTED_COUNT=0
for platform in "${PLATFORM_ORDER[@]}"; do
    if detect_platform "$platform"; then
        PLATFORMS[$platform]=true
        PLATFORM_PATHS[$platform]="$(get_platform_path "$platform")"
        DETECTED_COUNT=$((DETECTED_COUNT + 1))
        print_ok "$(get_platform_name "$platform")  ${BLUE}$(get_platform_path "$platform")${RESET}"
    fi
done

echo ""

# Handle no platforms detected
if [ $DETECTED_COUNT -eq 0 ]; then
    if [ "$CI_MODE" = true ] || [ "$AGENT_FLAG" = "claude" ]; then
        print_ok "No platforms detected — auto-creating ~/.claude/skills"
        mkdir -p "$HOME/.claude"
        PLATFORMS[claude]=true
        PLATFORM_PATHS[claude]="$HOME/.claude/skills"
        DETECTED_COUNT=1
    elif [ -n "$AGENT_FLAG" ]; then
        # --agent flag for a specific platform — create it
        print_ok "Creating target for $AGENT_FLAG"
        PLATFORMS[$AGENT_FLAG]=true
        PLATFORM_PATHS[$AGENT_FLAG]="$(get_platform_path "$AGENT_FLAG")"
        DETECTED_COUNT=1
    else
        print_warn "No Agent Skills compatible platforms detected"
        echo ""
        echo -e "${BOLD}Install one of these, then re-run:${RESET}"
        echo -e "  Claude Code       https://claude.ai/download"
        echo -e "  Kiro              https://kiro.dev"
        echo -e "  Cursor            https://cursor.com"
        echo -e "  VS Code           https://code.visualstudio.com"
        exit 1
    fi
fi

echo -e "  ${GREEN}$DETECTED_COUNT${RESET} platform(s) detected"
echo ""

# ============================================================================
# Platform selection (interactive menu with path preview)
# ============================================================================
resolve_selection() {
    # --agent flag: skip menu entirely
    if [ -n "$AGENT_FLAG" ]; then
        if [ "$AGENT_FLAG" = "all" ]; then
            SELECTED_OPTION="all"
        else
            # Validate agent name
            local valid=false
            for p in "${PLATFORM_ORDER[@]}"; do
                if [ "$p" = "$AGENT_FLAG" ]; then valid=true; break; fi
            done
            if [ "$valid" = false ]; then
                print_error "Unknown agent: $AGENT_FLAG"
                echo "  Valid agents: ${PLATFORM_ORDER[*]} all"
                exit 1
            fi
            # Ensure platform entry exists
            PLATFORMS[$AGENT_FLAG]=true
            PLATFORM_PATHS[$AGENT_FLAG]="$(get_platform_path "$AGENT_FLAG")"
            SELECTED_OPTION="$AGENT_FLAG"
        fi
        return
    fi

    # CI mode: select all
    if [ "$CI_MODE" = true ]; then
        if [ $DETECTED_COUNT -eq 1 ]; then
            for platform in "${!PLATFORMS[@]}"; do
                SELECTED_OPTION="$platform"
            done
        else
            SELECTED_OPTION="all"
        fi
        print_ok "Installing to: $SELECTED_OPTION"
        return
    fi

    # Interactive menu with path preview
    echo -e "${BOLD}Where should WFC be installed?${RESET}"
    echo ""

    local -a MENU_OPTIONS=()
    local MENU_INDEX=1

    for platform in "${PLATFORM_ORDER[@]}"; do
        if [ "${PLATFORMS[$platform]:-}" = true ]; then
            local name path_display
            name="$(get_platform_name "$platform")"
            path_display="$(get_platform_path "$platform" | sed "s|$HOME|~|")"
            printf "  ${BOLD}%d)${RESET} %-20s ${BLUE}(%s)${RESET}\n" "$MENU_INDEX" "$name" "$path_display"
            MENU_OPTIONS[$MENU_INDEX]="$platform"
            MENU_INDEX=$((MENU_INDEX + 1))
        fi
    done

    if [ $DETECTED_COUNT -gt 1 ]; then
        printf "  ${BOLD}%d)${RESET} %-20s ${GREEN}(recommended — uses symlinks)${RESET}\n" "$MENU_INDEX" "All detected"
        MENU_OPTIONS[$MENU_INDEX]="all"
        MENU_INDEX=$((MENU_INDEX + 1))
    fi

    echo ""
    read -rp "Choose [1-$((MENU_INDEX-1))]: " CHOICE

    if [ -z "$CHOICE" ] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -ge "$MENU_INDEX" ]; then
        print_error "Invalid choice"
        exit 1
    fi

    SELECTED_OPTION="${MENU_OPTIONS[$CHOICE]}"
}

resolve_selection

# Process selection
declare -A INSTALL_TO

if [ "$SELECTED_OPTION" = "all" ]; then
    for platform in "${!PLATFORMS[@]}"; do
        INSTALL_TO[$platform]=true
    done
    STRATEGY="symlink"
    echo -e "  ${BLUE}Strategy:${RESET} Install to ~/.wfc, symlink to all platforms"
else
    INSTALL_TO[$SELECTED_OPTION]=true
    STRATEGY="direct"
fi

echo ""

# ============================================================================
# CRITICAL FIX: Correct directory structure for Agent Skills
# ============================================================================

# Determine installation root
if [ "$STRATEGY" = "symlink" ]; then
    # Multi-platform: use ~/.wfc as source of truth
    WFC_ROOT="$HOME/.wfc"
    echo -e "${BLUE}Root directory:${RESET} $WFC_ROOT (source of truth)"
else
    # Direct install to single platform
    # CRITICAL: For single platform, install DIRECTLY to platform skills dir
    # NOT nested under a wfc/ subdirectory
    for platform in "${!INSTALL_TO[@]}"; do
        # Install directly to platform path, NOT nested
        WFC_ROOT="${PLATFORM_PATHS[$platform]}"
    done
    echo -e "${BLUE}Installing to:${RESET} $WFC_ROOT"
fi

# Create installation directory
mkdir -p "$WFC_ROOT"

# Save branding mode config (only on fresh install or explicit change — never clobber on refresh)
if [ "${KEEP_SETTINGS:-false}" = false ] || [ "${CHANGE_BRANDING:-false}" = true ]; then
    cat > "$WFC_ROOT/.wfc_branding" <<EOF
# WFC Branding Configuration
# Generated by install-universal.sh v${VERSION}
mode=$WFC_MODE
name=$WFC_NAME
tagline=$WFC_TAGLINE
EOF
    echo -e "${GREEN}✓${RESET} Saved branding mode: ${WFC_MODE}"
else
    echo -e "${GREEN}✓${RESET} Branding preserved: ${WFC_MODE:-nsfw}"
fi

# Copy WFC files
if [ "${KEEP_SETTINGS:-false}" = true ]; then
    echo -e "${BOLD}📦 Refreshing WFC application files...${RESET}"
    echo -e "   ${YELLOW}Preserving:${RESET} .wfc_branding, .wfc/rules/ (user customizations)"
    echo -e "   ${GREEN}Refreshing:${RESET} wfc/skills/, wfc/scripts/hooks/, references/reviewers/, templates/"
else
    echo -e "${BOLD}📦 Installing WFC...${RESET}"
fi
echo ""

# Determine source directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ============================================================================
# CRITICAL FIX: Correct skill installation structure
# ============================================================================

if [ "$STRATEGY" = "symlink" ]; then
    # Multi-platform: install to ~/.wfc/skills first
    mkdir -p "$WFC_ROOT/skills"

    SKILLS_FOUND=0

    if [ -d "$SCRIPT_DIR/wfc/skills" ]; then
        for skill_dir in "$SCRIPT_DIR/wfc/skills"/wfc-*; do
            if [ -d "$skill_dir" ]; then
                skill_name=$(basename "$skill_dir")
                target="$WFC_ROOT/skills/$skill_name"
                # Remove existing copy or symlink before (re)installing
                [ -L "$target" ] && rm "$target"
                [ -d "$target" ] && rm -rf "$target"
                if [ "$REMOTE_INSTALL" = false ]; then
                    ln -sf "$skill_dir" "$target"
                else
                    cp -r "$skill_dir" "$WFC_ROOT/skills/"
                fi
                SKILLS_FOUND=$((SKILLS_FOUND + 1))
            fi
        done
        if [ "$SKILLS_FOUND" -eq 0 ]; then
            echo -e "  ${YELLOW}⚠${RESET}  No skills found in $SCRIPT_DIR/wfc/skills"
        elif [ "$REMOTE_INSTALL" = false ]; then
            echo -e "  ${GREEN}✓${RESET} $SKILLS_FOUND skills linked from repo (auto-updates on branch change)"
        else
            echo -e "  ${GREEN}✓${RESET} $SKILLS_FOUND skills installed"
        fi
    else
        echo -e "  ${YELLOW}⚠${RESET}  Skills source not found: $SCRIPT_DIR/wfc/skills"
    fi

    # Reviewers, hooks, templates
    if [ -d "$SCRIPT_DIR/wfc/references/reviewers" ]; then
        mkdir -p "$WFC_ROOT/references/reviewers"
        cp -r "$SCRIPT_DIR/wfc/references/reviewers"/* "$WFC_ROOT/references/reviewers/"
    fi
    if [ -d "$SCRIPT_DIR/wfc/scripts/hooks" ]; then
        mkdir -p "$WFC_ROOT/scripts/hooks"
        cp -r "$SCRIPT_DIR/wfc/scripts/hooks"/* "$WFC_ROOT/scripts/hooks/"
    fi
    if [ -d "$SCRIPT_DIR/wfc/assets/templates" ]; then
        mkdir -p "$WFC_ROOT/templates"
        cp -r "$SCRIPT_DIR/wfc/assets/templates"/* "$WFC_ROOT/templates/"
    fi
    [ -d "$WFC_ROOT/rules" ] && echo -e "  ${GREEN}✓${RESET} User rules preserved"

else
    # Direct mode: install skills DIRECTLY to platform skills directory

    SKILLS_FOUND=0

    if [ -d "$SCRIPT_DIR/wfc/skills" ]; then
        for skill_dir in "$SCRIPT_DIR/wfc/skills"/wfc-*; do
            if [ -d "$skill_dir" ]; then
                skill_name=$(basename "$skill_dir")
                target="$WFC_ROOT/$skill_name"
                [ -d "$target" ] && rm -rf "$target"
                cp -r "$skill_dir" "$target"
                SKILLS_FOUND=$((SKILLS_FOUND + 1))
            fi
        done
        echo -e "  ${GREEN}✓${RESET} $SKILLS_FOUND skills installed"
    fi

    # Check ~/.claude/skills for already installed WFC skills
    if [ -d "$HOME/.claude/skills" ]; then
        for skill_dir in "$HOME/.claude/skills"/wfc-*; do
            if [ -d "$skill_dir" ]; then
                skill_name=$(basename "$skill_dir")
                target="$WFC_ROOT/$skill_name"
                if [ ! -d "$target" ]; then
                    echo "    ├─ $skill_name (from ~/.claude/skills)"
                    cp -r "$skill_dir" "$target"
                    SKILLS_FOUND=$((SKILLS_FOUND + 1))
                fi
            fi
        done
    fi

    echo "  • Found $SKILLS_FOUND WFC skills"

    # Copy reviewers (5 fixed specialist reviewers)
    if [ -d "$SCRIPT_DIR/wfc/references/reviewers" ]; then
        echo "  • Installing reviewers..."
        mkdir -p "$WFC_ROOT/wfc/references/reviewers"
        cp -r "$SCRIPT_DIR/wfc/references/reviewers"/* "$WFC_ROOT/wfc/references/reviewers/"
    fi

    # Copy hooks infrastructure
    if [ -d "$SCRIPT_DIR/wfc/scripts/hooks" ]; then
        echo "  • Installing hook infrastructure..."
        mkdir -p "$WFC_ROOT/wfc/scripts/hooks"
        cp -r "$SCRIPT_DIR/wfc/scripts/hooks"/* "$WFC_ROOT/wfc/scripts/hooks/"
    fi

    # Copy templates
    if [ -d "$SCRIPT_DIR/wfc/assets/templates" ]; then
        echo "  • Installing templates..."
        mkdir -p "$WFC_ROOT/wfc/templates"
        cp -r "$SCRIPT_DIR/wfc/assets/templates"/* "$WFC_ROOT/wfc/templates/"
    fi

    # Preserve user rules (never overwrite)
    if [ -d "$WFC_ROOT/wfc/rules" ]; then
        echo "  • Preserving user rules (.wfc/rules/)"
    fi
fi

echo ""

# Create symlinks if multi-platform installation
if [ "$STRATEGY" = "symlink" ]; then
    echo -e "${BOLD}🔗 Creating symlinks...${RESET}"
    echo ""

    for platform in "${!INSTALL_TO[@]}"; do
        platform_path="${PLATFORM_PATHS[$platform]}"

        case $platform in
            claude) name="Claude Code" ;;
            kiro) name="Kiro" ;;
            opencode) name="OpenCode" ;;
            cursor) name="Cursor" ;;
            vscode) name="VS Code" ;;
            codex) name="OpenAI Codex" ;;
            antigravity) name="Google Antigravity" ;;
            goose) name="Goose" ;;
        esac

        # Create platform skills directory
        mkdir -p "$platform_path"

        # Link each skill DIRECTLY to platform skills directory
        LINKED=0
        for skill in "$WFC_ROOT/skills"/wfc-*; do
            if [ -d "$skill" ]; then
                skill_name=$(basename "$skill")
                target="$platform_path/$skill_name"
                [ -L "$target" ] || [ -d "$target" ] && rm -rf "$target"
                ln -s "$skill" "$target"
                LINKED=$((LINKED + 1))
            fi
        done

        # Link shared resources
        target="$platform_path/wfc"
        mkdir -p "$target"
        [ -L "$target/personas" ] && rm "$target/personas"
        [ -L "$target/shared" ] && rm "$target/shared"
        [ -L "$target/scripts" ] && rm "$target/scripts"
        [ -L "$target/templates" ] && rm "$target/templates"
        ln -sf "$WFC_ROOT/personas" "$target/personas"
        [ -d "$WFC_ROOT/shared" ] && ln -sf "$WFC_ROOT/shared" "$target/shared"
        [ -d "$WFC_ROOT/scripts" ] && ln -sf "$WFC_ROOT/scripts" "$target/scripts"
        [ -d "$WFC_ROOT/templates" ] && ln -sf "$WFC_ROOT/templates" "$target/templates"

        echo -e "  ${GREEN}✓${RESET} $name — $LINKED skills"
    done
fi

# ============================================================================
# HOOK REGISTRATION: Install PostToolUse quality hooks for Claude Code
# ============================================================================
if [ "${INSTALL_TO[claude]}" = true ] || [ "${PLATFORMS[claude]}" = true ]; then
    HOOKS_SRC="$SCRIPT_DIR/wfc/scripts/hooks"
    HOOKS_DEST="$HOME/.wfc/scripts/hooks"

    if [ -d "$HOOKS_SRC" ]; then
        mkdir -p "$HOOKS_DEST" "$HOOKS_DEST/_checkers"

        for hook_file in file_checker.py tdd_enforcer.py context_monitor.py _util.py register_hooks.py; do
            [ -f "$HOOKS_SRC/$hook_file" ] && cp "$HOOKS_SRC/$hook_file" "$HOOKS_DEST/$hook_file"
        done
        for checker_file in __init__.py python.py typescript.py go.py; do
            [ -f "$HOOKS_SRC/_checkers/$checker_file" ] && cp "$HOOKS_SRC/_checkers/$checker_file" "$HOOKS_DEST/_checkers/$checker_file"
        done
        for sec_file in pretooluse_hook.py security_hook.py rule_engine.py config_loader.py hook_state.py __init__.py __main__.py; do
            [ -f "$HOOKS_SRC/$sec_file" ] && cp "$HOOKS_SRC/$sec_file" "$HOOKS_DEST/$sec_file"
        done
        if [ -d "$HOOKS_SRC/patterns" ]; then
            mkdir -p "$HOOKS_DEST/patterns"
            cp "$HOOKS_SRC/patterns"/*.json "$HOOKS_DEST/patterns/" 2>/dev/null || true
        fi
    fi

    REGISTER_SCRIPT="$HOOKS_DEST/register_hooks.py"
    GLOBAL_SETTINGS="$HOME/.claude/settings.json"
    if [ -f "$REGISTER_SCRIPT" ]; then
        if command -v python3 >/dev/null 2>&1; then
            python3 "$REGISTER_SCRIPT" "$GLOBAL_SETTINGS"
            echo -e "  ${GREEN}✓${RESET} Hooks registered in ~/.claude/settings.json"
        elif command -v python >/dev/null 2>&1; then
            python "$REGISTER_SCRIPT" "$GLOBAL_SETTINGS"
            echo -e "  ${GREEN}✓${RESET} Hooks registered in ~/.claude/settings.json"
        else
            echo -e "  ${YELLOW}⚠${RESET} Python not found — run manually: python3 $REGISTER_SCRIPT $GLOBAL_SETTINGS"
        fi
    fi
fi

# ============================================================================
# Installation Summary
# ============================================================================
echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║          Installation Complete            ║${RESET}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════╝${RESET}"
echo ""

if [ "$STRATEGY" = "symlink" ]; then
    echo -e "  ${BOLD}Source:${RESET}     $WFC_ROOT"
    echo -e "  ${BOLD}Symlinked:${RESET}"
    for platform in "${PLATFORM_ORDER[@]}"; do
        [ "${INSTALL_TO[$platform]:-}" = true ] || continue
        local_path="$(get_platform_path "$platform" | sed "s|$HOME|~|")"
        printf "    %-20s %s\n" "$(get_platform_name "$platform")" "$local_path"
    done
else
    echo -e "  ${BOLD}Location:${RESET}   $WFC_ROOT"
fi

echo ""
echo -e "  ${BOLD}Skills:${RESET}     $SKILLS_FOUND installed"
echo -e "  ${BOLD}Branding:${RESET}   $WFC_NAME ($WFC_MODE)"
echo ""

# Compact skill list — top 8 most-used
echo -e "${BOLD}Key Skills${RESET}"
echo ""
echo -e "  ${CYAN}/wfc-review${RESET}       5-agent consensus code review"
echo -e "  ${CYAN}/wfc-build${RESET}        Quick feature with TDD"
echo -e "  ${CYAN}/wfc-plan${RESET}         Structured task breakdown"
echo -e "  ${CYAN}/wfc-implement${RESET}    Parallel TDD execution"
echo -e "  ${CYAN}/wfc-security${RESET}     STRIDE threat modeling"
echo -e "  ${CYAN}/wfc-test${RESET}         Property-based test generation"
echo -e "  ${CYAN}/wfc-lfg${RESET}          Full auto: plan → build → review → PR"
echo -e "  ${CYAN}/wfc-validate${RESET}     Critical thinking advisor"
echo ""

# Per-platform next steps
echo -e "${BOLD}Next Steps${RESET}"
echo ""

for platform in "${PLATFORM_ORDER[@]}"; do
    [ "${INSTALL_TO[$platform]:-}" = true ] || continue
    name="$(get_platform_name "$platform")"
    config_hint=""
    case $platform in
        claude)       config_hint="Restart Claude Code, then type: /wfc-review" ;;
        kiro)         config_hint="Add orchestrator to ~/.kiro/KIRO.md — see: examples/kiro/" ;;
        opencode)     config_hint="Add orchestrator to opencode config — see: examples/opencode/" ;;
        cursor)       config_hint="Add to .cursorrules — see: examples/cursor/" ;;
        vscode)       config_hint="Add to copilot-instructions.md — see: examples/vscode/" ;;
        codex)        config_hint="Add to Codex instructions — see: examples/codex/" ;;
        antigravity)  config_hint="Add to .agent/rules/ — see: examples/antigravity/" ;;
        goose)        config_hint="Add to Goose config — see: examples/goose/" ;;
    esac
    echo -e "  ${GREEN}${name}:${RESET} ${config_hint}"
done

echo ""
echo -e "  Docs:     ${CYAN}https://github.com/sam-fakhreddine/wfc${RESET}"
echo -e "  Examples: ${CYAN}examples/${RESET}  (per-platform config templates)"
echo ""

if [ "$WFC_MODE" = "sfw" ]; then
    echo -e "${GREEN}${BOLD}This is Workflow Champion.${RESET}"
else
    echo -e "${GREEN}${BOLD}This is World Fucking Class.${RESET}"
fi
