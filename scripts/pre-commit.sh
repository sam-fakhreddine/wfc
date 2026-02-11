#!/bin/bash
# WFC Pre-commit Hook
# Validates all WFC skills before allowing commit

set -e

echo "🪝 WFC Pre-commit validation..."

# Check if skills-ref is available
SKILLS_REF_DIR="$HOME/repos/agentskills/skills-ref"
if [ ! -d "$SKILLS_REF_DIR" ]; then
    echo "⚠️  skills-ref not found at $SKILLS_REF_DIR"
    echo "⚠️  Skipping skill validation (install agentskills for validation)"
    exit 0
fi

# Activate skills-ref venv and validate
cd "$SKILLS_REF_DIR"
source .venv/bin/activate

FAILED_SKILLS=()

for skill in "$HOME/.claude/skills/wfc-"*; do
    if [ -d "$skill" ]; then
        skill_name=$(basename "$skill")
        if ! skills-ref validate "$skill" > /dev/null 2>&1; then
            FAILED_SKILLS+=("$skill_name")
        fi
    fi
done

if [ ${#FAILED_SKILLS[@]} -gt 0 ]; then
    echo "❌ Skill validation failed:"
    for skill in "${FAILED_SKILLS[@]}"; do
        echo "  - $skill"
    done
    echo ""
    echo "Fix with: make validate"
    exit 1
fi

echo "✅ All WFC skills validated"
exit 0
