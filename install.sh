#!/bin/bash
set -e

# WFC (World Fucking Class) Installer
# Installs WFC skill framework into Claude Code environment

CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
WFC_INSTALL_DIR="${CLAUDE_SKILLS_DIR}/wfc"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 WFC Installer"
echo "================"
echo ""

# Check if Claude Code is installed
if [ ! -d "${HOME}/.claude" ]; then
    echo "❌ Claude Code directory not found at ${HOME}/.claude"
    echo "   Please install Claude Code first: https://claude.ai/download"
    exit 1
fi

# Create skills directory if it doesn't exist
mkdir -p "${CLAUDE_SKILLS_DIR}"

# Check if WFC is already installed
if [ -d "${WFC_INSTALL_DIR}" ]; then
    echo "⚠️  WFC is already installed at ${WFC_INSTALL_DIR}"
    read -p "   Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "   Removing existing installation..."
    rm -rf "${WFC_INSTALL_DIR}"
fi

# Copy WFC support files (personas, shared, wfc-tools, tests)
echo "📦 Installing WFC framework files..."
cp -R "${SCRIPT_DIR}/wfc" "${WFC_INSTALL_DIR}"

# Set up custom personas directory (gitignored)
mkdir -p "${WFC_INSTALL_DIR}/personas/custom"
cat > "${WFC_INSTALL_DIR}/personas/custom/.gitignore" << 'EOF'
# User-defined custom personas are not tracked
*.json
!.gitignore
EOF

# Make scripts executable
chmod +x "${WFC_INSTALL_DIR}/personas/update_models_to_aliases.py" 2>/dev/null || true

# Flatten skills for Claude Code discovery
# Claude Code expects skills at ~/.claude/skills/skill-name/SKILL.md
# Not ~/.claude/skills/wfc/skills/skill-name/SKILL.md
echo "🔧 Flattening skills for Claude Code discovery..."

skill_count=0
if [ -d "${WFC_INSTALL_DIR}/skills" ]; then
    for skill_dir in "${WFC_INSTALL_DIR}/skills"/*/ ; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            target_dir="${CLAUDE_SKILLS_DIR}/wfc-${skill_name}"

            echo "   → Installing wfc-${skill_name}"

            # Remove existing if present
            [ -d "$target_dir" ] && rm -rf "$target_dir"

            # Copy skill to flattened location
            cp -R "$skill_dir" "$target_dir"

            ((skill_count++))
        fi
    done

    # Remove nested skills directory (no longer needed)
    rm -rf "${WFC_INSTALL_DIR}/skills"
fi

echo "✅ WFC installed successfully!"
echo "   Framework: ${WFC_INSTALL_DIR}"
echo "   Skills: $skill_count installed (wfc-*)"
echo ""
echo "📋 Quick Start:"
echo "   1. WFC is now available in Claude Code"
echo "   2. Use /wfc-help to see available commands"
echo "   3. Try: /wfc-consensus-review TASK-001"
echo ""
echo "📚 Documentation:"
echo "   - Overview: ${SCRIPT_DIR}/README.md"
echo "   - Personas: ${SCRIPT_DIR}/docs/PERSONAS.md"
echo "   - Architecture: ${SCRIPT_DIR}/docs/ARCHITECTURE.md"
echo ""
echo "🎯 Current Personas: $(find "${WFC_INSTALL_DIR}/personas/panels" -name "*.json" 2>/dev/null | wc -l | xargs) expert reviewers across 9 panels"
echo ""
