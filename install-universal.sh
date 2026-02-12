#!/usr/bin/env bash
set -e

# WFC Universal Installer
# Installs to Claude Code, Kiro, or both with smart symlinking

VERSION="0.1.0"
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}🏆 WFC Universal Installer v${VERSION}${RESET}"
echo -e "   World Fucking Class - Multi-Agent Framework"
echo ""

# Detect available platforms
CLAUDE_AVAILABLE=false
KIRO_AVAILABLE=false

if [ -d "$HOME/.claude" ]; then
    CLAUDE_AVAILABLE=true
    echo -e "${GREEN}✓${RESET} Claude Code detected at ~/.claude"
fi

if [ -d "$HOME/.kiro" ]; then
    KIRO_AVAILABLE=true
    echo -e "${GREEN}✓${RESET} Kiro detected at ~/.kiro"
fi

if [ "$CLAUDE_AVAILABLE" = false ] && [ "$KIRO_AVAILABLE" = false ]; then
    echo -e "${RED}✗${RESET} Neither Claude Code nor Kiro found"
    echo -e "   Install Claude Code: https://claude.ai/download"
    echo -e "   Install Kiro: https://kiro.dev"
    exit 1
fi

echo ""

# Ask user which platform(s) to install to
echo -e "${BOLD}Where should WFC be installed?${RESET}"
echo ""

if [ "$CLAUDE_AVAILABLE" = true ] && [ "$KIRO_AVAILABLE" = true ]; then
    echo "1) Claude Code only"
    echo "2) Kiro only"
    echo "3) Both (recommended - uses symlinks)"
    echo ""
    read -p "Choose (1-3): " CHOICE
    case $CHOICE in
        1) INSTALL_CLAUDE=true; INSTALL_KIRO=false ;;
        2) INSTALL_CLAUDE=false; INSTALL_KIRO=true ;;
        3) INSTALL_CLAUDE=true; INSTALL_KIRO=true ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
elif [ "$CLAUDE_AVAILABLE" = true ]; then
    INSTALL_CLAUDE=true
    INSTALL_KIRO=false
    echo "Installing to Claude Code (Kiro not detected)"
else
    INSTALL_CLAUDE=false
    INSTALL_KIRO=true
    echo "Installing to Kiro (Claude Code not detected)"
fi

echo ""

# Determine installation strategy
if [ "$INSTALL_CLAUDE" = true ] && [ "$INSTALL_KIRO" = true ]; then
    STRATEGY="symlink"
    echo -e "${BLUE}Strategy:${RESET} Install to ~/.wfc, symlink to both platforms"
    WFC_ROOT="$HOME/.wfc"
elif [ "$INSTALL_CLAUDE" = true ]; then
    STRATEGY="claude"
    WFC_ROOT="$HOME/.claude/skills/wfc"
else
    STRATEGY="kiro"
    WFC_ROOT="$HOME/.kiro/skills/wfc"
fi

echo -e "${BLUE}Installing to:${RESET} $WFC_ROOT"
echo ""

# Create installation directory
mkdir -p "$WFC_ROOT"

# Copy WFC files
echo -e "${BOLD}📦 Installing WFC...${RESET}"

# Core package
echo "  • Copying core package..."
cp -r wfc/* "$WFC_ROOT/" 2>/dev/null || true

# Individual skills
echo "  • Installing skills..."
mkdir -p "$WFC_ROOT/skills"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Find all WFC skills in ~/.claude/skills/
if [ -d "$HOME/.claude/skills" ]; then
    for skill_dir in "$HOME/.claude/skills"/wfc-*; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            echo "    - $skill_name"
            cp -r "$skill_dir" "$WFC_ROOT/skills/" 2>/dev/null || true
        fi
    done
fi

# Create symlinks if dual installation
if [ "$STRATEGY" = "symlink" ]; then
    echo ""
    echo -e "${BOLD}🔗 Creating symlinks...${RESET}"

    # Symlink for Claude Code
    if [ "$INSTALL_CLAUDE" = true ]; then
        mkdir -p "$HOME/.claude/skills"

        # Link each skill individually
        for skill in "$WFC_ROOT/skills"/wfc-*; do
            skill_name=$(basename "$skill")
            target="$HOME/.claude/skills/$skill_name"

            if [ -L "$target" ] || [ -d "$target" ]; then
                rm -rf "$target"
            fi

            ln -s "$skill" "$target"
            echo "  • $skill_name -> Claude Code"
        done

        # Link shared resources
        if [ -d "$WFC_ROOT/personas" ]; then
            target="$HOME/.claude/skills/wfc"
            mkdir -p "$target"
            ln -sf "$WFC_ROOT/personas" "$target/personas"
            ln -sf "$WFC_ROOT/shared" "$target/shared" 2>/dev/null || true
            echo "  • Shared resources -> Claude Code"
        fi
    fi

    # Symlink for Kiro
    if [ "$INSTALL_KIRO" = true ]; then
        mkdir -p "$HOME/.kiro/skills"

        # Link each skill individually
        for skill in "$WFC_ROOT/skills"/wfc-*; do
            skill_name=$(basename "$skill")
            target="$HOME/.kiro/skills/$skill_name"

            if [ -L "$target" ] || [ -d "$target" ]; then
                rm -rf "$target"
            fi

            ln -s "$skill" "$target"
            echo "  • $skill_name -> Kiro"
        done

        # Link shared resources
        if [ -d "$WFC_ROOT/personas" ]; then
            target="$HOME/.kiro/skills/wfc"
            mkdir -p "$target"
            ln -sf "$WFC_ROOT/personas" "$target/personas"
            ln -sf "$WFC_ROOT/shared" "$target/shared" 2>/dev/null || true
            echo "  • Shared resources -> Kiro"
        fi
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}✓ Installation complete!${RESET}"
echo ""

# Show what was installed
if [ "$STRATEGY" = "symlink" ]; then
    echo -e "${BOLD}Installation Summary:${RESET}"
    echo -e "  Source: ${BLUE}$WFC_ROOT${RESET}"
    [ "$INSTALL_CLAUDE" = true ] && echo -e "  Claude Code: ${BLUE}~/.claude/skills/wfc-*${RESET} (symlinked)"
    [ "$INSTALL_KIRO" = true ] && echo -e "  Kiro: ${BLUE}~/.kiro/skills/wfc-*${RESET} (symlinked)"
    echo ""
    echo -e "${YELLOW}Note:${RESET} Updates to ~/.wfc automatically sync to both platforms"
else
    echo -e "${BOLD}Installation Summary:${RESET}"
    echo -e "  Location: ${BLUE}$WFC_ROOT${RESET}"
fi

echo ""
echo -e "${BOLD}Available Skills:${RESET}"
echo "  • /wfc-review       - Multi-agent consensus code review"
echo "  • /wfc-implement    - Parallel TDD implementation"
echo "  • /wfc-plan         - Structured task breakdown"
echo "  • /wfc-test         - Property-based test generation"
echo "  • /wfc-security     - STRIDE threat modeling"
echo "  • /wfc-architecture - C4 diagrams & ADRs"
echo "  • /wfc-observe      - Observability instrumentation"
echo "  • /wfc-retro        - AI-powered retrospectives"
echo "  • /wfc-safeclaude   - Safe command allowlist"
echo "  • /wfc-isthissmart  - Critical thinking advisor"
echo "  • /wfc-newskill     - Create new WFC skills"

echo ""
echo -e "${BOLD}Quick Start:${RESET}"

if [ "$INSTALL_CLAUDE" = true ]; then
    echo "  Claude Code: /wfc-review"
fi

if [ "$INSTALL_KIRO" = true ]; then
    echo "  Kiro: /wfc-review"
fi

echo ""
echo -e "${BOLD}Documentation:${RESET}"
echo "  • README: https://github.com/sam-fakhreddine/wfc"
echo "  • Quick Start: $WFC_ROOT/../QUICKSTART.md"
echo "  • Personas: $WFC_ROOT/../docs/PERSONAS.md"

echo ""
echo -e "${GREEN}${BOLD}This is World Fucking Class.${RESET} 🏆"
