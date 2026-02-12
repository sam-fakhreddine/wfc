#!/usr/bin/env bash
set -e

# WFC Universal Installer - Agent Skills Standard Compatible
# Detects and installs to: Claude Code, Kiro, OpenCode, Cursor, VS Code, Codex, Antigravity
#
# Usage:
#   ./install-universal.sh          - Interactive installation
#   ./install-universal.sh --help   - Show this help message
#
# Features:
#   - Auto-detects installed Agent Skills platforms
#   - Supports 8+ platforms (Claude Code, Kiro, OpenCode, etc.)
#   - Branding modes: SFW (Workflow Champion) or NSFW (World Fucking Class)
#   - Reinstall options: refresh, change branding, or full reset
#   - Progressive disclosure (92% token reduction)
#   - Symlink support for multi-platform sync

VERSION="0.4.0"

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'EOF'
WFC Universal Installer v0.4.0
==============================

USAGE:
    ./install-universal.sh          Interactive installation
    ./install-universal.sh --help   Show this help

FEATURES:
    - Auto-detects Agent Skills platforms
    - Branding modes: SFW or NSFW
    - Reinstall options for existing installations
    - Multi-platform symlink support
    - Progressive disclosure (92% token reduction)

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
    Installation:  docs/UNIVERSAL_INSTALL.md
    Branding:      docs/BRANDING.md
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

echo -e "${BOLD}🏆 WFC Universal Installer v${VERSION}${RESET}"
echo -e "   ${CYAN}Agent Skills Standard Compatible${RESET}"
echo ""

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

# Branding mode selection (skip if keeping settings and not changing)
if [ "${KEEP_SETTINGS:-false}" = false ] || [ "${CHANGE_BRANDING:-false}" = true ]; then
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
    ((DETECTED_COUNT++))
done

echo ""

# Handle no platforms detected
if [ $DETECTED_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠${RESET}  No Agent Skills compatible platforms detected"
    echo ""
    echo -e "${BOLD}Install one of these platforms:${RESET}"
    echo -e "  • Claude Code:       ${CYAN}https://claude.ai/download${RESET}"
    echo -e "  • Kiro (AWS):        ${CYAN}https://kiro.dev${RESET}"
    echo -e "  • OpenCode:          ${CYAN}https://opencode.ai${RESET}"
    echo -e "  • Cursor:            ${CYAN}https://cursor.com${RESET}"
    echo -e "  • VS Code:           ${CYAN}https://code.visualstudio.com${RESET}"
    echo -e "  • OpenAI Codex:      ${CYAN}https://developers.openai.com/codex${RESET}"
    echo -e "  • Google Antigravity:${CYAN}https://antigravity.dev${RESET}"
    echo ""
    echo -e "Then re-run this installer."
    exit 1
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
        ((MENU_INDEX++))
    fi
done

# Add "All detected" option if more than one
if [ $DETECTED_COUNT -gt 1 ]; then
    echo -e "${MENU_INDEX}) ${BOLD}All detected platforms${RESET} (recommended - uses symlinks)"
    MENU_OPTIONS[$MENU_INDEX]="all"
    ALL_OPTION_INDEX=$MENU_INDEX
    ((MENU_INDEX++))
fi

# Add "Custom selection" option if more than two
if [ $DETECTED_COUNT -gt 2 ]; then
    echo -e "${MENU_INDEX}) Custom selection"
    MENU_OPTIONS[$MENU_INDEX]="custom"
    ((MENU_INDEX++))
fi

echo ""
read -p "Choose (1-$((MENU_INDEX-1))): " CHOICE

# Validate choice
if [ -z "$CHOICE" ] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -ge $MENU_INDEX ]; then
    echo -e "${RED}✗${RESET} Invalid choice"
    exit 1
fi

SELECTED_OPTION="${MENU_OPTIONS[$CHOICE]}"

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
            ((INDEX++))
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
        ((INSTALL_COUNT++))
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

# Determine installation root
if [ "$STRATEGY" = "symlink" ]; then
    WFC_ROOT="$HOME/.wfc"
    echo -e "${BLUE}Root directory:${RESET} $WFC_ROOT (source of truth)"
else
    # Direct install to single platform
    for platform in "${!INSTALL_TO[@]}"; do
        WFC_ROOT="${PLATFORM_PATHS[$platform]}/wfc"
    done
    echo -e "${BLUE}Installing to:${RESET} $WFC_ROOT"
fi

echo ""

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

# Core package (if exists)
if [ -d "$SCRIPT_DIR/wfc" ]; then
    echo "  • Copying core package..."
    cp -r "$SCRIPT_DIR/wfc"/* "$WFC_ROOT/" 2>/dev/null || true
fi

# Individual skills (from ~/.claude/skills or local directory)
echo "  • Installing skills..."

# Create skills directory
mkdir -p "$WFC_ROOT/skills"

# Find skills
SKILLS_FOUND=0

# Check local skills directory
if [ -d "$SCRIPT_DIR/skills" ]; then
    for skill_dir in "$SCRIPT_DIR/skills"/wfc-*; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            echo "    ├─ $skill_name"
            cp -r "$skill_dir" "$WFC_ROOT/skills/" 2>/dev/null || true
            ((SKILLS_FOUND++))
        fi
    done
fi

# Check ~/.claude/skills for already installed WFC skills
if [ -d "$HOME/.claude/skills" ]; then
    for skill_dir in "$HOME/.claude/skills"/wfc-*; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            if [ ! -d "$WFC_ROOT/skills/$skill_name" ]; then
                echo "    ├─ $skill_name (from ~/.claude/skills)"
                cp -r "$skill_dir" "$WFC_ROOT/skills/" 2>/dev/null || true
                ((SKILLS_FOUND++))
            fi
        fi
    done
fi

echo "  • Found $SKILLS_FOUND WFC skills"

# Copy shared resources
if [ -d "$SCRIPT_DIR/wfc/personas" ] || [ -d "$WFC_ROOT/personas" ]; then
    echo "  • Shared resources (personas, config)"
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

        # Link each skill
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
        if [ -d "$WFC_ROOT/personas" ]; then
            target="$platform_path/wfc"
            mkdir -p "$target"

            # Remove existing symlinks
            [ -L "$target/personas" ] && rm "$target/personas"
            [ -L "$target/shared" ] && rm "$target/shared"

            # Create symlinks
            ln -sf "$WFC_ROOT/personas" "$target/personas"
            [ -d "$WFC_ROOT/shared" ] && ln -sf "$WFC_ROOT/shared" "$target/shared"

            echo "  └─ Shared resources"
        fi

        echo ""
    done
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
echo "  • ${CYAN}/wfc-isthissmart${RESET}  - Critical thinking advisor"
echo "  • ${CYAN}/wfc-newskill${RESET}     - Create new WFC skills"

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
echo -e "  • Install:   ${CYAN}$SCRIPT_DIR/docs/UNIVERSAL_INSTALL.md${RESET}"
echo -e "  • Personas:  ${CYAN}$SCRIPT_DIR/docs/PERSONAS.md${RESET}"

echo ""
if [ "$WFC_MODE" = "sfw" ]; then
    echo -e "${GREEN}${BOLD}This is Workflow Champion.${RESET} 🏆"
else
    echo -e "${GREEN}${BOLD}This is World Fucking Class.${RESET} 🏆"
fi
echo -e "${CYAN}Universal. Compatible. Performance-optimized.${RESET}"
