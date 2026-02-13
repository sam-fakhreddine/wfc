#!/bin/bash
# WFC Pre-commit Hook
# Validates all WFC skills before allowing commit

set -e

echo "🪝 WFC Pre-commit validation..."

# Run black format check
echo "  Checking black formatting..."
if command -v uv &> /dev/null; then
    if ! uv run black --check wfc/ tests/ scripts/ --quiet 2>/dev/null; then
        echo "❌ Black formatting check failed"
        echo "   Fix with: make format"
        exit 1
    fi
    echo "  ✅ Black formatting OK"
else
    echo "  ⚠️  uv not found, skipping black check"
fi

# Run ruff lint check
echo "  Checking ruff linting..."
if command -v uv &> /dev/null; then
    if ! uv run ruff check wfc/ --quiet 2>/dev/null; then
        echo "❌ Ruff lint check failed"
        echo "   Fix with: uv run ruff check --fix wfc/"
        exit 1
    fi
    echo "  ✅ Ruff lint OK"
else
    echo "  ⚠️  uv not found, skipping ruff check"
fi

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
