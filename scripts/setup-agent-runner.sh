#!/usr/bin/env bash
# WFC Agent Runner Setup Script
#
# Provisions a self-hosted GitHub Actions runner for autonomous agent dispatch.
# Requirements: Linux (Ubuntu 22.04+), 4GB RAM minimum
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/your-org/wfc/main/scripts/setup-agent-runner.sh | bash
#   # OR
#   bash scripts/setup-agent-runner.sh
#
# After running:
#   1. Set ANTHROPIC_API_KEY as a repository secret
#   2. The runner registers with label "wfc-agent"
#   3. agent-dispatch.yml will auto-detect and use this runner

set -euo pipefail

echo "=========================================="
echo "WFC Agent Runner Setup"
echo "=========================================="

# Check prerequisites
check_prereq() {
    if ! command -v "$1" &> /dev/null; then
        echo "Missing: $1"
        return 1
    fi
    echo "Found: $1 ($(command -v "$1"))"
    return 0
}

echo ""
echo "Checking prerequisites..."
MISSING=0

check_prereq git || MISSING=1
check_prereq curl || MISSING=1
check_prereq jq || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "Install missing prerequisites:"
    echo "  sudo apt-get update && sudo apt-get install -y git curl jq"
    exit 1
fi

# Install GitHub CLI if missing
if ! command -v gh &> /dev/null; then
    echo ""
    echo "Installing GitHub CLI..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
        sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
        sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update && sudo apt-get install -y gh
fi
echo "Found: gh ($(gh --version | head -1))"

# Install Claude Code CLI if missing
if ! command -v claude &> /dev/null; then
    echo ""
    echo "Installing Claude Code CLI..."
    npm install -g @anthropic-ai/claude-code
fi
echo "Found: claude ($(claude --version 2>/dev/null || echo 'installed'))"

# Install UV if missing
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "Found: uv ($(uv --version))"

# Authenticate GitHub CLI
echo ""
echo "Checking GitHub CLI authentication..."
if ! gh auth status &> /dev/null; then
    echo "Please authenticate with GitHub:"
    echo "  gh auth login"
    echo ""
    echo "Then re-run this script."
    exit 1
fi
echo "GitHub CLI authenticated."

# Check ANTHROPIC_API_KEY
echo ""
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "WARNING: ANTHROPIC_API_KEY not set in environment."
    echo "Set it as a GitHub repository secret for agent-dispatch.yml to use."
    echo ""
    echo "  gh secret set ANTHROPIC_API_KEY"
    echo ""
else
    echo "ANTHROPIC_API_KEY is set."
fi

# Setup GitHub Actions runner
echo ""
echo "=========================================="
echo "GitHub Actions Runner Setup"
echo "=========================================="
echo ""
echo "To register a self-hosted runner with the 'wfc-agent' label:"
echo ""
echo "  1. Go to: https://github.com/<your-org>/<your-repo>/settings/actions/runners/new"
echo "  2. Follow the setup instructions for Linux"
echo "  3. When prompted for labels, add: wfc-agent"
echo "  4. Start the runner as a service:"
echo ""
echo "     sudo ./svc.sh install"
echo "     sudo ./svc.sh start"
echo ""

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Register self-hosted runner with label 'wfc-agent'"
echo "  2. Set ANTHROPIC_API_KEY as repository secret"
echo "  3. agent-dispatch.yml will automatically use this runner"
echo ""
echo "Test dispatch manually:"
echo "  gh workflow run agent-dispatch.yml"
