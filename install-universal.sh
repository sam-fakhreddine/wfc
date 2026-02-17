#!/usr/bin/env bash
set -e

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
#   ./install-universal.sh              - Interactive (local clone)
#   ./install-universal.sh --ci         - Non-interactive CI mode
#   ./install-universal.sh --help       - Show help
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
#   - Reinstall options: refresh, change branding, or full reset
#   - Progressive disclosure (92% token reduction)
#   - Symlink support for multi-platform sync

VERSION="0.7.0"
REPO="sam-fakhreddine/wfc"
REPO_URL="https://github.com/${REPO}.git"

# Non-interactive mode flag
CI_MODE=false
if [ "$1" = "--ci" ] || [ "$1" = "--non-interactive" ]; then
    CI_MODE=true
fi

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'EOF'
WFC Universal Installer v0.6.0
==============================

USAGE:
    ./install.sh                 Interactive installation
    ./install.sh --help          Show this help
    ./install.sh --ci            Non-interactive CI mode

FEATURES:
    - Auto-detects Agent Skills platforms
    - Branding modes: SFW or NSFW
    - Reinstall options for existing installations
    - Multi-platform symlink support
    - Progressive disclosure (92% token reduction)

CI MODE:
    --ci flag enables non-interactive installation with these defaults:
    - Existing install: Refresh (keep settings)
    - Branding: NSFW (World Fucking Class)
    - Platform: All detected platforms (uses symlink strategy)

SUPPORTED PLATFORMS:
    - Claude Code     (~/.claude/skills)
    - Kiro (AWS)      (~/.kiro/skills)
    - OpenCode        (~/.opencode/skills)
    - Cursor          (~/.cursor/skills)
    - VS Code         (~/.vscode/skills)
    - OpenAI Codex    (~/.codex/skills)
    - Antigravity     (~/.antigravity/skills)
    - Goose           (~/.config/goose/skills)

REINSTALL OPTIONS:
    When existing installation detected:
    1. Refresh         - Update files, keep settings
    2. Change branding - Switch SFW/NSFW mode
    3. Full reinstall  - Reset all settings (with backup)
    4. Cancel          - Exit without changes

BRANDING MODES:
    SFW  (Safe For Work) - "Workflow Champion"
         Professional language, corporate-friendly

    NSFW (Default)       - "World Fucking Class"
         Original branding, no bullshit

DOCUMENTATION:
    Installation:  docs/workflow/UNIVERSAL_INSTALL.md
    Quick Start:   QUICKSTART.md

EOF
    exit 0
fi

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
RESET="\033[0m"

# ============================================================================
# REMOTE INSTALL: If running via curl pipe, clone repo first
# ============================================================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" 2>/dev/null )" 2>/dev/null && pwd 2>/dev/null )" || SCRIPT_DIR=""
REMOTE_INSTALL=false

if [ -z "$SCRIPT_DIR" ] || [ ! -d "$SCRIPT_DIR/wfc/skills" ]; then
    # Running via curl pipe or from outside repo - clone to /tmp
    REMOTE_INSTALL=true
    CLONE_DIR="/tmp/wfc-install-$$"

    echo -e "${BOLD}📡 Remote install - fetching WFC...${RESET}"

    if ! command -v git >/dev/null 2>&1; then
        echo -e "${RED}✗${RESET} git is required. Install git first."
        exit 1
    fi

    git clone --depth 1 "$REPO_URL" "$CLONE_DIR" 2>/dev/null
    SCRIPT_DIR="$CLONE_DIR"
    echo -e "${GREEN}✓${RESET} WFC fetched"
    echo ""

    # Cleanup on exit
    trap "rm -rf $CLONE_DIR" EXIT
fi

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
        echo -e "${YELLOW}⚠${RESET}  Optional dependencies not found: ${missing[*]}"

        if [[ " ${missing[*]} " =~ " uv " ]]; then
            echo -e "   Install uv: ${CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh${RESET}"
        fi
        echo ""
    fi

    # Check for quality tools (informational)
    local quality_tools=()
    command -v ruff >/dev/null 2>&1 && quality_tools+=("ruff")
    command -v black >/dev/null 2>&1 && quality_tools+=("black")
    command -v prettier >/dev/null 2>&1 && quality_tools+=("prettier")
    command -v eslint >/dev/null 2>&1 && quality_tools+=("eslint")
    command -v gofmt >/dev/null 2>&1 && quality_tools+=("gofmt")

    if [ ${#quality_tools[@]} -gt 0 ]; then
        echo -e "${GREEN}✓${RESET} Quality tools detected: ${quality_tools[*]}"
    fi
}

echo -e "${BOLD}🏆 WFC Universal Installer v${VERSION}${RESET}"
echo -e "   ${CYAN}Agent Skills Standard Compatible${RESET}"
echo ""

check_dependencies

# Check for existing installation
EXISTING_INSTALL=false
EXISTING_BRANDING=""
EXISTING_MODE=""

if [ -d "$HOME/.wfc" ]; then
    EXISTING_INSTALL=true
    if [ -f "$HOME/.wfc/.wfc_branding" ]; then
        EXISTING_MODE=$(grep "^mode=" "$HOME/.wfc/.wfc_branding" | cut -d'=' -f2)
        EXISTING_BRANDING=$(grep "^name=" "$HOME/.wfc/.wfc_branding" | cut -d'=' -f2)
    fi
fi

# Reinstall options if existing installation detected
if [ "$EXISTING_INSTALL" = true ]; then
    if [ "$CI_MODE" = true ]; then
        # CI mode: always refresh
        echo -e "${YELLOW}⚠${RESET}  CI mode: Refreshing existing installation..."
        KEEP_SETTINGS=true
        if [ -n "$EXISTING_MODE" ]; then
            WFC_MODE="$EXISTING_MODE"
            if [ "$WFC_MODE" = "sfw" ]; then
                WFC_NAME="Workflow Champion"
                WFC_TAGLINE="Professional Multi-Agent Framework"
            else
                WFC_NAME="World Fucking Class"
                WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"
            fi
        fi
    else
        # Interactive mode
        echo -e "${YELLOW}⚠${RESET}  Existing WFC installation detected"
        if [ -n "$EXISTING_BRANDING" ]; then
            echo -e "   Current: ${CYAN}$EXISTING_BRANDING${RESET} (${EXISTING_MODE})"
        fi
        echo ""
        echo -e "${BOLD}What would you like to do?${RESET}"
        echo ""
        echo -e "1) ${GREEN}Refresh installation${RESET} (keep current settings)"
        echo -e "   └─ Update files, preserve branding and config"
        echo ""
        echo -e "2) ${YELLOW}Change branding mode${RESET}"
        echo -e "   └─ Switch between SFW/NSFW, keep everything else"
        echo ""
        echo -e "3) ${RED}Full reinstall${RESET} (reset all settings)"
        echo -e "   └─ Clean install, reconfigure everything"
        echo ""
        echo -e "4) ${BLUE}Cancel${RESET}"
        echo -e "   └─ Exit without changes"
        echo ""
        read -p "Choose (1-4): " REINSTALL_CHOICE

        case $REINSTALL_CHOICE in
            1)
                # Refresh - keep existing settings
                echo -e "${GREEN}✓${RESET} Refreshing installation..."
                KEEP_SETTINGS=true
                if [ -n "$EXISTING_MODE" ]; then
                    WFC_MODE="$EXISTING_MODE"
                    if [ "$WFC_MODE" = "sfw" ]; then
                        WFC_NAME="Workflow Champion"
                        WFC_TAGLINE="Professional Multi-Agent Framework"
                    else
                        WFC_NAME="World Fucking Class"
                        WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"
                    fi
                fi
                ;;
            2)
                # Change branding
                echo -e "${GREEN}✓${RESET} Changing branding mode..."
                KEEP_SETTINGS=true
                CHANGE_BRANDING=true
                ;;
            3)
                # Full reinstall
                echo -e "${YELLOW}⚠${RESET}  Full reinstall - backing up current config..."
                BACKUP_DIR="$HOME/.wfc_backup_$(date +%Y%m%d_%H%M%S)"
                mkdir -p "$BACKUP_DIR"
                if [ -f "$HOME/.wfc/.wfc_branding" ]; then
                    cp "$HOME/.wfc/.wfc_branding" "$BACKUP_DIR/"
                fi
                # Backup user rules if they exist
                if [ -d "$HOME/.wfc/rules" ]; then
                    cp -r "$HOME/.wfc/rules" "$BACKUP_DIR/rules"
                    echo -e "   Backed up user rules"
                fi
                echo -e "${GREEN}✓${RESET} Backup saved to: ${CYAN}$BACKUP_DIR${RESET}"
                KEEP_SETTINGS=false
                ;;
            4)
                echo -e "${BLUE}Cancelled${RESET}"
                exit 0
                ;;
            *)
                echo -e "${RED}✗${RESET} Invalid choice"
                exit 1
                ;;
        esac
        echo ""
    fi
fi

# Branding mode selection (skip if keeping settings and not changing)
if [ "${KEEP_SETTINGS:-false}" = false ] || [ "${CHANGE_BRANDING:-false}" = true ]; then
    if [ "$CI_MODE" = true ]; then
        # CI mode: default to NSFW
        WFC_NAME="World Fucking Class"
        WFC_ACRONYM="WFC"
        WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"
        WFC_MODE="nsfw"
        echo -e "${GREEN}✓${RESET} CI mode: Using ${MAGENTA}World Fucking Class${RESET} (NSFW)"
    else
        echo -e "${BOLD}🎨 Choose branding mode:${RESET}"
        echo ""
        echo -e "1) ${BOLD}SFW${RESET} (Safe For Work)  → ${GREEN}Workflow Champion${RESET}"
        echo -e "   └─ Professional language, corporate-friendly"
        echo ""
        echo -e "2) ${BOLD}NSFW${RESET} (Default)        → ${MAGENTA}World Fucking Class${RESET}"
        echo -e "   └─ Original branding, no bullshit"
        echo ""
        read -p "Choose mode (1-2) [default: 2]: " BRANDING_CHOICE

        case $BRANDING_CHOICE in
            1)
                WFC_NAME="Workflow Champion"
                WFC_ACRONYM="WFC"
                WFC_TAGLINE="Professional Multi-Agent Framework"
                WFC_MODE="sfw"
                echo -e "${GREEN}✓${RESET} Selected: ${GREEN}Workflow Champion${RESET} (SFW)"
                ;;
            2|"")
                WFC_NAME="World Fucking Class"
                WFC_ACRONYM="WFC"
                WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"
                WFC_MODE="nsfw"
                echo -e "${GREEN}✓${RESET} Selected: ${MAGENTA}World Fucking Class${RESET} (NSFW)"
                ;;
            *)
                echo -e "${RED}✗${RESET} Invalid choice, defaulting to NSFW"
                WFC_NAME="World Fucking Class"
                WFC_ACRONYM="WFC"
                WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"
                WFC_MODE="nsfw"
                ;;
        esac
    fi
fi

echo ""
echo -e "${BOLD}🏆 Installing ${WFC_NAME}${RESET}"
echo -e "   ${WFC_TAGLINE}"
echo -e "   ${CYAN}Agent Skills Standard Compatible${RESET}"
echo ""

# Platform detection
declare -A PLATFORMS
declare -A PLATFORM_PATHS

# Detect all Agent Skills compatible platforms
echo -e "${BOLD}🔍 Detecting installed platforms...${RESET}"
echo ""

# Claude Code
if [ -d "$HOME/.claude" ]; then
    PLATFORMS[claude]=true
    PLATFORM_PATHS[claude]="$HOME/.claude/skills"
    echo -e "${GREEN}✓${RESET} Claude Code"
    echo -e "  └─ Skills: ${BLUE}~/.claude/skills/${RESET}"
fi

# Kiro (AWS)
if [ -d "$HOME/.kiro" ]; then
    PLATFORMS[kiro]=true
    PLATFORM_PATHS[kiro]="$HOME/.kiro/skills"
    echo -e "${GREEN}✓${RESET} Kiro (AWS)"
    echo -e "  └─ Skills: ${BLUE}~/.kiro/skills/${RESET}"
fi

# OpenCode
if [ -d "$HOME/.config/opencode" ] || [ -d "$HOME/.opencode" ]; then
    PLATFORMS[opencode]=true
    if [ -d "$HOME/.config/opencode" ]; then
        PLATFORM_PATHS[opencode]="$HOME/.config/opencode/skills"
    else
        PLATFORM_PATHS[opencode]="$HOME/.opencode/skills"
    fi
    echo -e "${GREEN}✓${RESET} OpenCode"
    echo -e "  └─ Skills: ${BLUE}${PLATFORM_PATHS[opencode]}${RESET}"
fi

# Cursor
if [ -d "$HOME/.cursor" ] || [ -d "$HOME/Library/Application Support/Cursor" ]; then
    PLATFORMS[cursor]=true
    if [ -d "$HOME/.cursor" ]; then
        PLATFORM_PATHS[cursor]="$HOME/.cursor/skills"
    else
        PLATFORM_PATHS[cursor]="$HOME/Library/Application Support/Cursor/skills"
    fi
    echo -e "${GREEN}✓${RESET} Cursor"
    echo -e "  └─ Skills: ${BLUE}${PLATFORM_PATHS[cursor]}${RESET}"
fi

# VS Code
if [ -d "$HOME/.vscode" ] || [ -d "$HOME/Library/Application Support/Code" ]; then
    PLATFORMS[vscode]=true
    if [ -d "$HOME/.vscode" ]; then
        PLATFORM_PATHS[vscode]="$HOME/.vscode/skills"
    else
        PLATFORM_PATHS[vscode]="$HOME/Library/Application Support/Code/User/skills"
    fi
    echo -e "${GREEN}✓${RESET} VS Code"
    echo -e "  └─ Skills: ${BLUE}${PLATFORM_PATHS[vscode]}${RESET}"
fi

# OpenAI Codex
if [ -d "$HOME/.codex" ] || [ -d "$HOME/.openai/codex" ]; then
    PLATFORMS[codex]=true
    if [ -d "$HOME/.codex" ]; then
        PLATFORM_PATHS[codex]="$HOME/.codex/skills"
    else
        PLATFORM_PATHS[codex]="$HOME/.openai/codex/skills"
    fi
    echo -e "${GREEN}✓${RESET} OpenAI Codex"
    echo -e "  └─ Skills: ${BLUE}${PLATFORM_PATHS[codex]}${RESET}"
fi

# Google Antigravity
if [ -d "$HOME/.antigravity" ] || [ -d "$HOME/.config/antigravity" ]; then
    PLATFORMS[antigravity]=true
    if [ -d "$HOME/.antigravity" ]; then
        PLATFORM_PATHS[antigravity]="$HOME/.antigravity/skills"
    else
        PLATFORM_PATHS[antigravity]="$HOME/.config/antigravity/skills"
    fi
    echo -e "${GREEN}✓${RESET} Google Antigravity"
    echo -e "  └─ Skills: ${BLUE}${PLATFORM_PATHS[antigravity]}${RESET}"
fi

# Goose
if [ -d "$HOME/.config/goose" ]; then
    PLATFORMS[goose]=true
    PLATFORM_PATHS[goose]="$HOME/.config/goose/skills"
    echo -e "${GREEN}✓${RESET} Goose"
    echo -e "  └─ Skills: ${BLUE}~/.config/goose/skills/${RESET}"
fi

# Count detected platforms
DETECTED_COUNT=0
for platform in "${!PLATFORMS[@]}"; do
    DETECTED_COUNT=$((DETECTED_COUNT + 1))
done

echo ""

# Handle no platforms detected
if [ $DETECTED_COUNT -eq 0 ]; then
    if [ "$CI_MODE" = true ]; then
        echo -e "${CYAN}CI mode:${RESET} No platforms detected — auto-creating ~/.claude/skills"
        mkdir -p "$HOME/.claude/skills"
        PLATFORMS[claude]=true
        PLATFORM_PATHS[claude]="$HOME/.claude/skills"
        DETECTED_COUNT=1
    else
        echo -e "${YELLOW}⚠${RESET}  No Agent Skills compatible platforms detected"
        echo ""
        echo -e "${BOLD}Install one of these platforms:${RESET}"
        echo -e "  • Claude Code:       ${CYAN}https://claude.ai/download${RESET}"
        echo -e "  • Kiro (AWS):        ${CYAN}https://kiro.dev${RESET}"
        echo -e "  • OpenCode:          ${CYAN}https://opencode.ai${RESET}"
        echo -e "  • Cursor:            ${CYAN}https://cursor.com${RESET}"
        echo -e "  • VS Code:           ${CYAN}https://code.visualstudio.com/${RESET}"
        echo -e "  • OpenAI Codex:      ${CYAN}https://developers.openai.com/codex${RESET}"
        echo -e "  • Google Antigravity:${CYAN}https://antigravity.dev${RESET}"
        echo ""
        echo -e "Then re-run this installer."
        exit 1
    fi
fi

# Show summary
echo -e "${BOLD}📊 Detection Summary:${RESET}"
echo -e "   ${GREEN}$DETECTED_COUNT${RESET} platform(s) detected"
echo ""

# Build installation menu
echo -e "${BOLD}🎯 Where should WFC be installed?${RESET}"
echo ""

MENU_OPTIONS=()
MENU_PLATFORMS=()
MENU_INDEX=1

# Add individual platform options
for platform in claude kiro opencode cursor vscode codex antigravity goose; do
    if [ "${PLATFORMS[$platform]}" = true ]; then
        case $platform in
            claude) name="Claude Code" ;;
            kiro) name="Kiro (AWS)" ;;
            opencode) name="OpenCode" ;;
            cursor) name="Cursor" ;;
            vscode) name="VS Code" ;;
            codex) name="OpenAI Codex" ;;
            antigravity) name="Google Antigravity" ;;
            goose) name="Goose" ;;
        esac
        echo -e "${MENU_INDEX}) ${name} only"
        MENU_OPTIONS[$MENU_INDEX]="$platform"
        MENU_INDEX=$((MENU_INDEX + 1))
    fi
done

# Add "All detected" option if more than one
if [ $DETECTED_COUNT -gt 1 ]; then
    echo -e "${MENU_INDEX}) ${BOLD}All detected platforms${RESET} (recommended - uses symlinks)"
    MENU_OPTIONS[$MENU_INDEX]="all"
    ALL_OPTION_INDEX=$MENU_INDEX
    MENU_INDEX=$((MENU_INDEX + 1))
fi

# Add "Custom selection" option if more than two
if [ $DETECTED_COUNT -gt 2 ]; then
    echo -e "${MENU_INDEX}) Custom selection"
    MENU_OPTIONS[$MENU_INDEX]="custom"
    MENU_INDEX=$((MENU_INDEX + 1))
fi

echo ""

# CI mode: select all platforms automatically
if [ "$CI_MODE" = true ]; then
    if [ $DETECTED_COUNT -eq 1 ]; then
        # Single platform: select it directly
        for platform in "${!PLATFORMS[@]}"; do
            SELECTED_OPTION="$platform"
            case $platform in
                claude) name="Claude Code" ;;
                kiro) name="Kiro (AWS)" ;;
                opencode) name="OpenCode" ;;
                cursor) name="Cursor" ;;
                vscode) name="VS Code" ;;
                codex) name="OpenAI Codex" ;;
                antigravity) name="Google Antigravity" ;;
                goose) name="Goose" ;;
            esac
            echo -e "${CYAN}CI mode:${RESET} Installing to ${name}"
        done
    else
        # Multiple platforms: use "all" strategy
        echo -e "${CYAN}CI mode:${RESET} Installing to all detected platforms"
        SELECTED_OPTION="all"
    fi
else
    read -p "Choose (1-$((MENU_INDEX-1))): " CHOICE

    # Validate choice
    if [ -z "$CHOICE" ] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -ge $MENU_INDEX ]; then
        echo -e "${RED}✗${RESET} Invalid choice"
        exit 1
    fi

    SELECTED_OPTION="${MENU_OPTIONS[$CHOICE]}"
fi

# Process selection
declare -A INSTALL_TO

if [ "$SELECTED_OPTION" = "all" ]; then
    # Install to all detected platforms
    for platform in "${!PLATFORMS[@]}"; do
        INSTALL_TO[$platform]=true
    done
    STRATEGY="symlink"
    echo ""
    echo -e "${BLUE}Strategy:${RESET} Install to ~/.wfc, symlink to all platforms"
elif [ "$SELECTED_OPTION" = "custom" ]; then
    # Custom selection
    echo ""
    echo -e "${BOLD}Select platforms (space-separated numbers):${RESET}"
    INDEX=1
    declare -A CUSTOM_MAP
    for platform in claude kiro opencode cursor vscode codex antigravity goose; do
        if [ "${PLATFORMS[$platform]}" = true ]; then
            case $platform in
                claude) name="Claude Code" ;;
                kiro) name="Kiro (AWS)" ;;
                opencode) name="OpenCode" ;;
                cursor) name="Cursor" ;;
                vscode) name="VS Code" ;;
                codex) name="OpenAI Codex" ;;
                antigravity) name="Google Antigravity" ;;
                goose) name="Goose" ;;
            esac
            echo -e "${INDEX}) ${name}"
            CUSTOM_MAP[$INDEX]=$platform
            INDEX=$((INDEX + 1))
        fi
    done
    echo ""
    read -p "Enter numbers: " -a CUSTOM_CHOICES

    for choice in "${CUSTOM_CHOICES[@]}"; do
        if [ -n "${CUSTOM_MAP[$choice]}" ]; then
            INSTALL_TO[${CUSTOM_MAP[$choice]}]=true
        fi
    done

    # Determine strategy
    INSTALL_COUNT=0
    for platform in "${!INSTALL_TO[@]}"; do
        INSTALL_COUNT=$((INSTALL_COUNT + 1))
    done

    if [ $INSTALL_COUNT -gt 1 ]; then
        STRATEGY="symlink"
    else
        STRATEGY="direct"
    fi
else
    # Single platform installation
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

# Save branding mode config
cat > "$WFC_ROOT/.wfc_branding" <<EOF
# WFC Branding Configuration
# Generated by install-universal.sh v${VERSION}
mode=$WFC_MODE
name=$WFC_NAME
tagline=$WFC_TAGLINE
EOF

echo -e "${GREEN}✓${RESET} Saved branding mode: ${WFC_MODE}"

# Copy WFC files
echo -e "${BOLD}📦 Installing WFC...${RESET}"
echo ""

# Determine source directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ============================================================================
# CRITICAL FIX: Correct skill installation structure
# ============================================================================

echo "  • Installing skills..."

if [ "$STRATEGY" = "symlink" ]; then
    # Multi-platform: copy to ~/.wfc/skills first
    mkdir -p "$WFC_ROOT/skills"

    SKILLS_FOUND=0

    # Check local skills directory (in wfc/skills)
    if [ -d "$SCRIPT_DIR/wfc/skills" ]; then
        for skill_dir in "$SCRIPT_DIR/wfc/skills"/wfc-*; do
            if [ -d "$skill_dir" ]; then
                skill_name=$(basename "$skill_dir")
                echo "    ├─ $skill_name"
                # Remove old version if exists
                [ -d "$WFC_ROOT/skills/$skill_name" ] && rm -rf "$WFC_ROOT/skills/$skill_name"
                cp -r "$skill_dir" "$WFC_ROOT/skills/"
                SKILLS_FOUND=$((SKILLS_FOUND + 1))
            fi
        done
    fi

    # Check ~/.claude/skills for already installed WFC skills
    if [ -d "$HOME/.claude/skills" ]; then
        for skill_dir in "$HOME/.claude/skills"/wfc-*; do
            if [ -d "$skill_dir" ]; then
                skill_name=$(basename "$skill_dir")
                # Check if this is a meta-skill directory (contains sub-skills)
                if [ -d "$skill_dir/wkills" ]; then
                    # Meta-skill - install directly to skills root
                    target="$WFC_ROOT/skills/"
                    echo "    ├─ $skill_name (meta-skill from ~/.claude/skills)"
                    if [ ! -d "$target" ]; then
                        mkdir -p "$target"
                    fi
                    cp -r "$skill_dir"/* "$target/" 2>/dev/null || true
                    SKILLS_FOUND=$((SKILLS_FOUND + 1))
                else
                    # Regular skill - install in skills subdirectory
                    target="$WFC_ROOT/skills/"
                    if [ ! -d "$target/$skill_name" ]; then
                        mkdir -p "$target/$skill_name"
                        echo "    ├─ $skill_name"
                    else
                        echo "    ├─ $skill_name (already exists)"
                    fi
                fi
            fi
        done
    fi

    echo "  • Found $SKILLS_FOUND WFC skills"

    # Copy shared resources to ~/.wfc
    if [ -d "$SCRIPT_DIR/wfc/references/personas" ]; then
        echo "  • Copying shared resources..."
        mkdir -p "$WFC_ROOT/personas"
        cp -r "$SCRIPT_DIR/wfc/references/personas"/* "$WFC_ROOT/personas/"
    fi

    # Copy hooks infrastructure
    if [ -d "$SCRIPT_DIR/wfc/scripts/hooks" ]; then
        echo "  • Installing hook infrastructure..."
        mkdir -p "$WFC_ROOT/scripts/hooks"
        cp -r "$SCRIPT_DIR/wfc/scripts/hooks"/* "$WFC_ROOT/scripts/hooks/"
    fi

    # Copy templates
    if [ -d "$SCRIPT_DIR/wfc/assets/templates" ]; then
        echo "  • Installing templates..."
        mkdir -p "$WFC_ROOT/templates"
        cp -r "$SCRIPT_DIR/wfc/assets/templates"/* "$WFC_ROOT/templates/"
    fi

    # Preserve user rules (never overwrite)
    if [ -d "$WFC_ROOT/rules" ]; then
        echo "  • Preserving user rules (.wfc/rules/)"
    fi

else
    # Direct mode: install skills DIRECTLY to platform skills directory
    # CRITICAL: Skills must be at ~/.claude/skills/wfc-*/ NOT ~/.claude/skills/wfc/skills/wfc-*/

    SKILLS_FOUND=0

    # Check local skills directory (in wfc/skills)
    if [ -d "$SCRIPT_DIR/wfc/skills" ]; then
        for skill_dir in "$SCRIPT_DIR/wfc/skills"/wfc-*; do
            if [ -d "$skill_dir" ]; then
                skill_name=$(basename "$skill_dir")
                target="$WFC_ROOT/$skill_name"
                echo "    ├─ $skill_name"
                # Remove old version if exists
                [ -d "$target" ] && rm -rf "$target"
                cp -r "$skill_dir" "$target"
                SKILLS_FOUND=$((SKILLS_FOUND + 1))
            fi
        done
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

    # Copy shared resources
    if [ -d "$SCRIPT_DIR/wfc/references/personas" ]; then
        echo "  • Copying shared resources..."
        # Create wfc/ subdirectory for shared resources
        mkdir -p "$WFC_ROOT/wfc/personas"
        cp -r "$SCRIPT_DIR/wfc/references/personas"/* "$WFC_ROOT/wfc/personas/"
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

        echo -e "${CYAN}→ $name${RESET}"

        # Create platform skills directory
        mkdir -p "$platform_path"

        # Link each skill DIRECTLY to platform skills directory
        for skill in "$WFC_ROOT/skills"/wfc-*; do
            if [ -d "$skill" ]; then
                skill_name=$(basename "$skill")
                target="$platform_path/$skill_name"

                # Remove existing
                if [ -L "$target" ] || [ -d "$target" ]; then
                    rm -rf "$target"
                fi

                # Create symlink
                ln -s "$skill" "$target"
                echo "  ├─ $skill_name"
            fi
        done

        # Link shared resources
        target="$platform_path/wfc"
        mkdir -p "$target"

        # Remove existing symlinks
        [ -L "$target/personas" ] && rm "$target/personas"
        [ -L "$target/shared" ] && rm "$target/shared"
        [ -L "$target/scripts" ] && rm "$target/scripts"
        [ -L "$target/templates" ] && rm "$target/templates"

        # Create symlinks
        ln -sf "$WFC_ROOT/personas" "$target/personas"
        [ -d "$WFC_ROOT/shared" ] && ln -sf "$WFC_ROOT/shared" "$target/shared"
        [ -d "$WFC_ROOT/scripts" ] && ln -sf "$WFC_ROOT/scripts" "$target/scripts"
        [ -d "$WFC_ROOT/templates" ] && ln -sf "$WFC_ROOT/templates" "$target/templates"

        echo "  └─ Shared resources (personas, hooks, templates)"
        echo ""
    done
fi

# ============================================================================
# HOOK REGISTRATION: Install PostToolUse quality hooks for Claude Code
# ============================================================================
if [ "${INSTALL_TO[claude]}" = true ] || [ "${PLATFORMS[claude]}" = true ]; then
    echo -e "${BOLD}🪝 Registering PostToolUse quality hooks...${RESET}"
    echo ""

    HOOKS_SRC="$SCRIPT_DIR/wfc/scripts/hooks"
    HOOKS_DEST="$HOME/.wfc/scripts/hooks"

    if [ -d "$HOOKS_SRC" ]; then
        mkdir -p "$HOOKS_DEST"
        mkdir -p "$HOOKS_DEST/_checkers"

        # Copy hook scripts
        for hook_file in file_checker.py tdd_enforcer.py context_monitor.py _util.py register_hooks.py; do
            if [ -f "$HOOKS_SRC/$hook_file" ]; then
                cp "$HOOKS_SRC/$hook_file" "$HOOKS_DEST/$hook_file"
                echo "    ├─ $hook_file"
            fi
        done

        # Copy language checkers
        for checker_file in __init__.py python.py typescript.py go.py; do
            if [ -f "$HOOKS_SRC/_checkers/$checker_file" ]; then
                cp "$HOOKS_SRC/_checkers/$checker_file" "$HOOKS_DEST/_checkers/$checker_file"
                echo "    ├─ _checkers/$checker_file"
            fi
        done

        # Copy security hooks
        for sec_file in pretooluse_hook.py security_hook.py rule_engine.py config_loader.py hook_state.py __init__.py __main__.py; do
            if [ -f "$HOOKS_SRC/$sec_file" ]; then
                cp "$HOOKS_SRC/$sec_file" "$HOOKS_DEST/$sec_file"
            fi
        done

        # Copy patterns
        if [ -d "$HOOKS_SRC/patterns" ]; then
            mkdir -p "$HOOKS_DEST/patterns"
            cp "$HOOKS_SRC/patterns"/*.json "$HOOKS_DEST/patterns/" 2>/dev/null || true
        fi

        echo -e "${GREEN}  ✓${RESET} Quality hooks installed to ~/.wfc/scripts/hooks/"
    fi

    # Upsert WFC hooks into ~/.claude/settings.json (never clobbers existing settings)
    REGISTER_SCRIPT="$HOOKS_DEST/register_hooks.py"
    GLOBAL_SETTINGS="$HOME/.claude/settings.json"
    if [ -f "$REGISTER_SCRIPT" ]; then
        echo "  • Registering hooks in ~/.claude/settings.json (upsert)..."
        if command -v python3 >/dev/null 2>&1; then
            python3 "$REGISTER_SCRIPT" "$GLOBAL_SETTINGS"
            echo -e "${GREEN}  ✓${RESET} Hooks registered (existing settings preserved)"
        elif command -v python >/dev/null 2>&1; then
            python "$REGISTER_SCRIPT" "$GLOBAL_SETTINGS"
            echo -e "${GREEN}  ✓${RESET} Hooks registered (existing settings preserved)"
        else
            echo -e "${YELLOW}  ⚠${RESET} Python not found — run manually:"
            echo "      python3 $REGISTER_SCRIPT $GLOBAL_SETTINGS"
        fi
    fi

    echo ""
fi

# Success!
echo -e "${GREEN}${BOLD}✓ Installation complete!${RESET}"
echo ""

# Show installation summary
echo -e "${BOLD}📋 Installation Summary${RESET}"
echo ""

if [ "$STRATEGY" = "symlink" ]; then
    echo -e "${BLUE}Source:${RESET} $WFC_ROOT"
    echo ""
    echo -e "${BLUE}Symlinked to:${RESET}"
    for platform in "${!INSTALL_TO[@]}"; do
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
        echo -e "  • ${name}: ${PLATFORM_PATHS[$platform]}/wfc-*"
    done
    echo ""
    echo -e "${YELLOW}Note:${RESET} Updates to $WFC_ROOT automatically sync to all platforms"
else
    echo -e "${BLUE}Location:${RESET} $WFC_ROOT"
fi

echo ""
echo -e "${BOLD}🎯 Available Skills${RESET}"
echo ""
echo "  • ${CYAN}/wfc-review${RESET}       - Multi-agent consensus code review"
echo "  • ${CYAN}/wfc-implement${RESET}    - Parallel TDD implementation"
echo "  • ${CYAN}/wfc-plan${RESET}         - Structured task breakdown"
echo "  • ${CYAN}/wfc-test${RESET}         - Property-based test generation"
echo "  • ${CYAN}/wfc-security${RESET}     - STRIDE threat modeling"
echo "  • ${CYAN}/wfc-architecture${RESET} - C4 diagrams & ADRs"
echo "  • ${CYAN}/wfc-observe${RESET}      - Observability instrumentation"
echo "  • ${CYAN}/wfc-retro${RESET}        - AI-powered retrospectives"
echo "  • ${CYAN}/wfc-safeclaude${RESET}   - Safe command allowlist"
echo "  • ${CYAN}/wfc-safeguard${RESET}    - Real-time security hooks"
echo "  • ${CYAN}/wfc-rules${RESET}        - Custom enforcement rules"
echo "  • ${CYAN}/wfc-playground${RESET}   - Interactive HTML playgrounds"
echo "  • ${CYAN}/wfc-validate${RESET}     - Critical thinking advisor"
echo "  • ${CYAN}/wfc-pr-comments${RESET} - PR comment triage & fix"
echo "  • ${CYAN}/wfc-newskill${RESET}     - Create new WFC skills"
echo "  • ${CYAN}/wfc-init${RESET}        - Project initialization tool"
echo "  • ${CYAN}/wfc-vibe${RESET}         - Natural brainstorming mode"
echo "  • ${CYAN}/wfc-sync${RESET}        - Sync rules & discover patterns"
echo "  • ${CYAN}/wfc-agentic${RESET}     - GitHub Agentic Workflows (gh-aw)"
echo "  • ${CYAN}/wfc-ba${RESET}          - Business analysis & requirements"

echo ""
echo -e "${BOLD}🚀 Next Steps${RESET}"
echo ""

for platform in "${!INSTALL_TO[@]}"; do
    case $platform in
        claude)
            echo -e "  ${GREEN}Claude Code:${RESET}"
            echo -e "    claude"
            echo -e "    /wfc-review"
            echo ""
            ;;
        kiro)
            echo -e "  ${GREEN}Kiro:${RESET}"
            echo -e "    kiro"
            echo -e "    /wfc-review"
            echo ""
            ;;
        opencode)
            echo -e "  ${GREEN}OpenCode:${RESET}"
            echo -e "    opencode"
            echo -e "    /wfc-review"
            echo ""
            ;;
        cursor)
            echo -e "  ${GREEN}Cursor:${RESET}"
            echo -e "    Open Cursor"
            echo -e "    /wfc-review"
            echo ""
            ;;
        vscode)
            echo -e "  ${GREEN}VS Code:${RESET}"
            echo -e "    code ."
            echo -e "    /wfc-review"
            echo ""
            ;;
        codex)
            echo -e "  ${GREEN}OpenAI Codex:${RESET}"
            echo -e "    codex"
            echo -e "    /wfc-review"
            echo ""
            ;;
        antigravity)
            echo -e "  ${GREEN}Google Antigravity:${RESET}"
            echo -e "    antigravity"
            echo -e "    /wfc-review"
            echo ""
            ;;
        goose)
            echo -e "  ${GREEN}Goose:${RESET}"
            echo -e "    goose"
            echo -e "    /wfc-review"
            echo ""
            ;;
    esac
done

echo -e "${BOLD}📚 Documentation${RESET}"
echo ""
echo -e "  • README:    ${CYAN}https://github.com/sam-fakhreddine/wfc${RESET}"
echo -e "  • Install:   ${CYAN}$SCRIPT_DIR/docs/workflow/UNIVERSAL_INSTALL.md${RESET}"
echo -e "  • Personas:  ${CYAN}$SCRIPT_DIR/docs/quality/PERSONAS.md${RESET}"

echo ""
if [ "$WFC_MODE" = "sfw" ]; then
    echo -e "${GREEN}${BOLD}This is Workflow Champion.${RESET} 🏆"
else
    echo -e "${GREEN}${BOLD}This is World Fucking Class.${RESET} 🏆"
fi
echo -e "${CYAN}Universal. Compatible. Performance-optimized.${RESET}"
